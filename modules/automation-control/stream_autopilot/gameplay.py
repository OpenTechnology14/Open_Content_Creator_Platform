"""Bounded private-world Minecraft transport; viewer text is never a game command."""

from __future__ import annotations

import argparse
import subprocess
import asyncio
import ipaddress
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PACKAGE = Path(__file__).parent / "minecraft"


def tool(name: str) -> str | None:
    """Discover a normal workstation install without a caller-selected executable."""
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            / "nodejs"
            / (name + (".exe" if name == "node" else ".cmd"))
        ]
    else:
        candidates = [Path(prefix) / name for prefix in ("/opt/homebrew/bin", "/usr/local/bin")]
    return next((str(path) for path in candidates if path.is_file()), None)


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action: Literal["forward", "back", "jump"]
    duration_ms: int = Field(ge=50, le=1000)


class GameConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal[1]
    enabled: bool
    permission_confirmed: bool
    permission_statement: str = Field(max_length=500)
    world_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    host: str
    port: int = Field(ge=1, le=65535)
    username: str = Field(pattern=r"^hcp_[a-zA-Z0-9_]{1,12}$")
    game_version: str | None = Field(pattern=r"^\d+\.\d+(\.\d+)?$")
    task: Task

    @model_validator(mode="after")
    def private_permission(self):
        host = "127.0.0.1" if self.host == "localhost" else self.host
        ip = ipaddress.ip_address(host)
        private = ip.is_loopback or (
            ip.version == 4
            and any(
                ip in network
                for network in (
                    ipaddress.ip_network("10.0.0.0/8"),
                    ipaddress.ip_network("172.16.0.0/12"),
                    ipaddress.ip_network("192.168.0.0/16"),
                )
            )
        )
        if not private:
            raise ValueError("only a literal private/loopback server is supported")
        if self.enabled and (
            not self.permission_confirmed
            or len(self.permission_statement.strip()) < 10
            or self.world_id == "unbound"
        ):
            raise ValueError("declare the permitted owned test world before enabling")
        return self


def load_game(path: Path) -> GameConfig:
    if path.stat().st_size > 65536:
        raise ValueError("game configuration exceeds 64 KiB")
    return GameConfig.model_validate_json(path.read_text(encoding="utf-8"))


class MinecraftPeer:
    """Own one protocol client and fence movement against stop/takeover epochs."""

    def __init__(self, config: Path):
        self.path = config
        self.config = load_game(config)
        self.process: asyncio.subprocess.Process | None = None
        self.pending: dict[str, asyncio.Future] = {}
        self.reader: asyncio.Task | None = None
        self.write_lock = asyncio.Lock()
        self.epoch = 0

    async def open(self) -> None:
        if not self.config.enabled or not self.config.permission_confirmed:
            raise ValueError("private-world gameplay has not been permitted")
        node = tool("node")
        if not node:
            raise ValueError("install Node.js 22+ and the pinned game package")
        # The game SDK needs no backend, OBS, platform or avatar credential.
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TMP", "TEMP"}
        }
        self.process = await asyncio.create_subprocess_exec(
            node,
            str(PACKAGE / "index.mjs"),
            "--config",
            str(self.path),
            "--stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=environment,
        )
        self.reader = asyncio.create_task(self._read())
        await self.request("connect", timeout=12)

    async def _read(self) -> None:
        try:
            while self.process and self.process.stdout:
                line = await self.process.stdout.readline()
                if not line or len(line) > 8192:
                    break
                value = json.loads(line)
                future = self.pending.get(value.get("operation_id"))
                if future and not future.done():
                    future.set_result(value)
        except (ValueError, OSError):
            pass
        finally:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(RuntimeError("game adapter disconnected"))

    async def request(self, action: str, timeout: float = 2) -> dict:
        if action not in {"connect", "observe", "task", "release", "close"}:
            raise ValueError("unknown game action")
        if not self.process or not self.process.stdin or self.process.returncode is not None:
            raise RuntimeError("game adapter is unavailable")
        if len(self.pending) >= 4:
            raise RuntimeError("game command budget is exhausted")
        operation = uuid.uuid4().hex
        future = asyncio.get_running_loop().create_future()
        self.pending[operation] = future
        frame = {"action": action, "epoch": self.epoch, "operation_id": operation}
        try:
            async with self.write_lock:
                self.process.stdin.write((json.dumps(frame) + "\n").encode())
                await self.process.stdin.drain()
            result = await asyncio.wait_for(future, timeout)
            if result.get("epoch") != self.epoch or not result.get("ok"):
                raise RuntimeError("game action was rejected or interrupted")
            return result
        finally:
            self.pending.pop(operation, None)

    async def perform(self) -> dict:
        self.epoch += 1
        return await self.request("task", 2)

    async def release(self) -> dict:
        self.epoch += 1
        return await self.request("release", 0.2)

    async def close(self) -> None:
        if self.process and self.process.returncode is None:
            try:
                self.epoch += 1
                await self.request("close", 0.3)
                await asyncio.wait_for(self.process.wait(), 1)
            except (RuntimeError, OSError, asyncio.TimeoutError):
                self.process.kill()
                await self.process.wait()
        if self.reader:
            self.reader.cancel()
            await asyncio.gather(self.reader, return_exceptions=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--install-dependencies", action="store_true")
    args = parser.parse_args()
    try:
        config = load_game(args.config)
        if args.install_dependencies:
            npm = tool("npm")
            if not npm:
                raise ValueError("install Node.js 22+ first")
            result = subprocess.run(
                [npm, "ci", "--ignore-scripts", "--prefix", str(PACKAGE)],
                capture_output=True,
                timeout=180,
                check=False,
            )
            sys.stdout.write(
                json.dumps({"installed": result.returncode == 0, "gameplay_started": False}) + "\n"
            )
            return int(result.returncode != 0)
        if not args.validate:
            parser.error(
                "choose --validate or --install-dependencies; effects use the production owner"
            )

        node = tool("node")
        if not config.enabled or not node:
            sys.stdout.write(
                json.dumps(
                    {
                        "valid": False,
                        "connected": False,
                        "reason": "adapter_disabled_or_node_missing",
                    }
                )
                + "\n"
            )
            return 0
        result = subprocess.run(
            [node, str(PACKAGE / "index.mjs"), "--config", str(args.config), "--validate"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        report = json.loads(result.stdout)
        sys.stdout.write(json.dumps(report) + "\n")
        return int(result.returncode != 0)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"Gameplay check failed: {type(exc).__name__}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
