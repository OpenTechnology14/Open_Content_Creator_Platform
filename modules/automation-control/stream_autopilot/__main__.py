"""Inspect or rehearse the Stream Autopilot lifecycle without starting a broadcast."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import asyncio
import json
import sys
import tempfile
import uuid
from pathlib import Path

from pydantic import ValidationError

from .models import CapabilityCheck, load_config
from .production import ProductionDriver, load_runtime_settings
from .supervisor import SessionSupervisor

ROOT = Path(__file__).resolve().parents[3]


class RehearsalDriver:
    """Explicit no-effects driver used to exercise recovery and controls offline."""

    def __init__(self) -> None:
        self.actions: list[str] = []

    async def preflight(self, session_id, policy):
        self.actions.append("preflight")
        return [
            CapabilityCheck(
                id="lifecycle-contract",
                status="ready",
                detail="Offline rehearsal loaded; no OBS, audio, model or game was contacted.",
            )
        ]

    async def preview(self, session_id, policy):
        self.actions.append("preview")

    async def run(self, session_id, policy):
        self.actions.append("run")

    async def pause(self, session_id, policy):
        self.actions.append("pause")

    async def stop(self, session_id, policy):
        self.actions.append("stop")


async def rehearse(config_path: Path, state_path: Path, session_id: str | None) -> dict:
    config = load_config(config_path)
    selected = session_id or next(key for key, value in config.sessions.items() if value.enabled)
    driver = RehearsalDriver()
    supervisor = SessionSupervisor(config, driver, state_path)
    for action in ("preflight", "preview", "pause", "resume", "stop"):
        await supervisor.apply(selected, action, uuid.uuid4().hex)
    return {
        "schema_version": 1,
        "rehearsal": True,
        "broadcast_started": False,
        "session_id": selected,
        "driver_actions": driver.actions,
        "status": supervisor.status(selected),
    }


async def inspect_production(
    config_path: Path, runtime_path: Path, session_id: str | None = None
) -> dict:
    """Read current production readiness without starting or stopping any effect owner."""
    config = load_config(config_path)
    settings = load_runtime_settings(runtime_path)
    selected = session_id or settings.on_air_session
    policy = config.sessions.get(selected)
    if policy is None or not policy.enabled:
        raise ValueError("choose an enabled configured session")
    driver = ProductionDriver(settings)
    try:
        checks = await driver.preflight(selected, policy)
        return {
            "schema_version": 1,
            "inspection": True,
            "session_id": selected,
            "ready": all(check.status == "ready" for check in checks if check.required),
            "checks": [check.model_dump(mode="json") for check in checks],
            "broadcast_started": False,
            "workers_started": False,
            "scope": "Validation and backend readiness only; no live-state, clip, game or broadcast action.",
        }
    finally:
        # close() is an effect-owner shutdown and can trigger OBS Stop All hotkeys.
        # This inspection never owns effects; release only its HTTP client.
        await driver.http.aclose()


@contextmanager
def production_lock(state_path: Path):
    """Hold a local OS lock for the entire effect owner, including shutdown."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    path = state_path.with_suffix(".owner.lock")
    stream = path.open("a+b")
    try:
        if sys.platform == "win32":
            import msvcrt

            if path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        stream.close()


async def serve(config_path: Path, runtime_path: Path, state_path: Path) -> None:
    with production_lock(state_path):
        await _serve_owned(config_path, runtime_path, state_path)


async def _serve_owned(config_path: Path, runtime_path: Path, state_path: Path) -> None:
    """Own production effects and correlate bounded local operator requests."""
    supervisor_config = load_config(config_path)
    settings = load_runtime_settings(runtime_path)
    if (
        settings.on_air_session not in supervisor_config.sessions
        or not supervisor_config.sessions[settings.on_air_session].enabled
    ):
        raise ValueError("runtime must own an enabled configured session")
    driver = ProductionDriver(settings)
    supervisor = SessionSupervisor(supervisor_config, driver, state_path)
    active: dict[str, asyncio.Task] = {}
    output_lock = asyncio.Lock()

    async def respond(request: dict, response: dict) -> None:
        response["operation_id"] = (
            request.get("operation_id") if isinstance(request.get("operation_id"), str) else None
        )
        response["session_id"] = settings.on_air_session
        response["avatar_enabled"] = settings.avatar_enabled
        response["broadcast_control_enabled"] = settings.control_broadcast
        response["policy"] = supervisor_config.sessions[settings.on_air_session].model_dump(
            mode="json"
        )
        response["worker_states"] = {
            name: "running" if process.returncode is None else "exited"
            for name, process in driver.processes.items()
        }
        async with output_lock:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

    async def apply(request: dict) -> None:
        try:
            action = request["action"]
            if action.startswith("cue_"):
                status = supervisor.status(settings.on_air_session)
                if status["lifecycle"] not in {"preview", "running"}:
                    raise ValueError("local preview is required for cues")
                cue = await driver.cue(settings.on_air_session, action[4:], request["operation_id"])
                await respond(request, {"ok": True, "status": status, "cue": cue})
            else:
                result = await supervisor.apply(
                    settings.on_air_session, action, request["operation_id"]
                )
                await respond(request, {"ok": True, "status": result})
        except asyncio.CancelledError:
            await respond(
                request,
                {
                    "ok": False,
                    "error": "interrupted",
                    "status": supervisor.status(settings.on_air_session),
                },
            )
            raise
        except (TypeError, ValueError):
            await respond(
                request,
                {
                    "ok": False,
                    "error": "transition_rejected",
                    "status": supervisor.status(settings.on_air_session),
                },
            )

    try:
        while True:
            line = await asyncio.to_thread(sys.stdin.readline, 4097)
            if not line:
                break
            request: dict = {}
            try:
                if len(line.encode("utf-8")) > 4096:
                    await respond(request, {"ok": False, "error": "frame_too_large"})
                    break  # Never interpret the tail of an oversized frame as another command.
                request = json.loads(line)
                if not isinstance(request, dict) or set(request) != {
                    "session_id",
                    "action",
                    "operation_id",
                }:
                    raise ValueError("invalid command fields")
                operation = request["operation_id"]
                if (
                    not isinstance(operation, str)
                    or not 1 <= len(operation) <= 64
                    or not all(c.isascii() and (c.isalnum() or c in "_-") for c in operation)
                ):
                    raise ValueError("invalid operation")
                if request["session_id"] not in {None, settings.on_air_session}:
                    raise ValueError("runtime owns a different session")
                action = request["action"]
                if action == "status":
                    await respond(
                        request, {"ok": True, "status": supervisor.status(settings.on_air_session)}
                    )
                    continue
                if action not in {
                    "cue_wave",
                    "cue_nod",
                    "cue_shrug",
                    "cue_look_left",
                    "cue_look_right",
                    "cue_happy",
                    "cue_surprised",
                    "cue_neutral",
                    "preflight",
                    "preview",
                    "run",
                    "pause",
                    "resume",
                    "stop",
                    "emergency_stop",
                }:
                    raise ValueError("invalid action")
                pending = active.get(settings.on_air_session)
                if pending and not pending.done():
                    if action not in {"emergency_stop", "stop"}:
                        await respond(request, {"ok": False, "error": "busy"})
                        continue
                    pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)
                active[settings.on_air_session] = asyncio.create_task(apply(request))
            except (json.JSONDecodeError, TypeError, ValueError):
                await respond(
                    request if isinstance(request, dict) else {},
                    {"ok": False, "error": "invalid_request"},
                )
    finally:
        for task in active.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*active.values(), return_exceptions=True)
        await driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/local/stream-supervisor.yaml"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status", help="validate policy and show configured sessions")
    status.add_argument("--state", type=Path)
    rehearsal = sub.add_parser("rehearse", help="exercise lifecycle with no external effects")
    rehearsal.add_argument("--session")
    rehearsal.add_argument("--state", type=Path)
    inspection = sub.add_parser("preflight", help="inspect production readiness without effects")
    inspection.add_argument("--session")
    inspection.add_argument(
        "--runtime-config", type=Path, default=ROOT / "configs/local/stream-runtime.yaml"
    )
    service = sub.add_parser("serve", help="run production workers under local lifecycle control")
    service.add_argument(
        "--runtime-config", type=Path, default=ROOT / "configs/local/stream-runtime.yaml"
    )
    service.add_argument(
        "--state", type=Path, default=Path.home() / ".hcp/stream-autopilot-state.json"
    )
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.command == "status":
            if args.state:
                result = SessionSupervisor(config, RehearsalDriver(), args.state).status()
            else:
                result = {
                    "schema_version": 1,
                    "valid": True,
                    "max_concurrent_running": config.max_concurrent_running,
                    "sessions": {
                        key: value.model_dump(mode="json") for key, value in config.sessions.items()
                    },
                }
        elif args.command == "preflight":
            result = asyncio.run(inspect_production(args.config, args.runtime_config, args.session))
        elif args.command == "rehearse":
            state = args.state
            if state is None:
                state = Path(tempfile.mkdtemp(prefix="hcp-autopilot-")) / "state.json"
            result = asyncio.run(rehearse(args.config, state, args.session))
        else:
            asyncio.run(serve(args.config, args.runtime_config, args.state))
            return 0
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
        return 0
    except (OSError, ValueError, RuntimeError, ValidationError) as exc:
        sys.stderr.write(f"Autopilot supervisor failed: {type(exc).__name__}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
