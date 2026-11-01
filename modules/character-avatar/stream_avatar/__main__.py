"""Animate the local VTube Studio avatar from Stream Autopilot speech timing events."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from loguru import logger
from pydantic import ValidationError

from .models import AvatarCueEvent, AvatarEvent, load_settings
from .runtime import AvatarRuntime
from .vts import VtsAvatarAdapter

ROOT = Path(__file__).resolve().parents[3]
TOPICS = {
    "events.stream-speech.started",
    "events.stream-speech.finished",
    "events.stream-speech.canceled",
    "events.stream-speech.controlled",
    "events.stream-avatar.cue",
}
MAX_LINE = 16_384


def backend_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("AUTOPILOT_BACKEND_URL must be a credential-free HTTP(S) URL")
    return value.rstrip("/")


def websocket_url(base: str) -> str:
    parsed = urlsplit(base)
    return urlunsplit(
        (
            "wss" if parsed.scheme == "https" else "ws",
            parsed.netloc,
            parsed.path.rstrip("/") + "/ws",
            "topics=" + ",".join(sorted(TOPICS)),
            "",
        )
    )


async def replay(runtime: AvatarRuntime, path: Path) -> None:
    with path.open(encoding="utf-8") as stream:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                return
            if len(line) > MAX_LINE:
                raise ValueError("avatar input exceeds 16 KiB")
            if line.strip():
                await runtime.handle(AvatarEvent.model_validate_json(line))


async def live(runtime: AvatarRuntime, base: str, key: str) -> None:
    from websockets.legacy.client import connect

    async with connect(
        websocket_url(base),
        extra_headers={"X-API-Key": key},
        max_size=MAX_LINE,
        max_queue=8,
        open_timeout=5,
        close_timeout=1,
    ) as socket:
        async for raw in socket:
            try:
                envelope = json.loads(raw)
                if envelope.get("channel") not in TOPICS:
                    continue
                payload = envelope["data"]["data"]
                if envelope["channel"] == "events.stream-avatar.cue":
                    await runtime.handle_cue(AvatarCueEvent.model_validate(payload))
                    continue
                event = AvatarEvent.model_validate(payload)
                if envelope["channel"] != "events.stream-speech." + event.kind:
                    continue
            except (ValidationError, ValueError, KeyError, TypeError, AttributeError):
                logger.warning("avatar worker ignored malformed speech envelope")
                continue
            await runtime.handle(event)


async def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config)
    if args.validate:
        sys.stdout.write(
            json.dumps(
                {
                    "schema_version": 1,
                    "valid": True,
                    "on_air_session": settings.on_air_session,
                    "avatars": list(settings.avatars),
                    "connected": False,
                }
            )
            + "\n"
        )
        return
    base = backend_url(os.environ.get("AUTOPILOT_BACKEND_URL", "")) if args.backend else ""
    key = os.environ.get("HCP_API_KEY", "")
    if base and (not key or key in {"change-me", "change-me-to-a-long-random-string"}):
        raise ValueError("set HCP_API_KEY to the configured backend key")
    if args.idle:
        from pathlib import Path as LocalPath
        from vtube.vts_client import VTSConfig

        if not LocalPath(VTSConfig().token_path).is_file():
            raise ValueError("existing VTS authorization is required for an idle reset")
        adapter = VtsAvatarAdapter(settings, allow_token_request=False)
        await adapter.connect()
        try:
            for avatar in settings.avatars:
                await adapter.idle(avatar)
        finally:
            await adapter.close()
        return
    runtime = AvatarRuntime(settings, VtsAvatarAdapter(settings))
    await runtime.start()
    try:
        if args.backend:
            await live(runtime, base, key)
        else:
            await replay(runtime, args.input)
    finally:
        await runtime.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/local/stream-avatar.yaml")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--input", type=Path)
    mode.add_argument("--backend", action="store_true")
    mode.add_argument("--idle", action="store_true")
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        logger.error(
            "avatar worker stopped: {}; check VTube Studio and hotkeys", type(exc).__name__
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
