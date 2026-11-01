"""Fixed module entry points with bounded results and cancellation of native child trees."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
from pathlib import Path


async def call(
    root: Path, module: str, entry: str, args: list[str], data: dict, timeout: float = 60
) -> dict:
    """Run a repository-owned entry point. All variable content travels as JSON stdin."""
    options = (
        {"start_new_session": True}
        if os.name != "nt"
        else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        entry,
        *args,
        env={**os.environ, "PYTHONPATH": str(root / "modules" / module), "PYTHONUTF8": "1"},
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        limit=262144,
        **options,
    )
    try:

        async def exchange() -> bytes:
            process.stdin.write(json.dumps(data).encode())
            await process.stdin.drain()
            process.stdin.close()
            output = b""
            while chunk := await process.stdout.read(65536):
                output += chunk
                if len(output) > 262144:
                    raise ValueError("worker output exceeds limit")
            await process.wait()
            if process.returncode:
                raise RuntimeError(f"{entry} failed; check installed voice/model and input")
            return output

        return json.loads(await asyncio.wait_for(exchange(), timeout))
    finally:
        if process.returncode is None:
            if os.name == "nt":
                killer = await asyncio.create_subprocess_exec(
                    "taskkill",
                    "/PID",
                    str(process.pid),
                    "/T",
                    "/F",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await killer.wait()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            await process.wait()
