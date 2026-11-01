"""Play current Stream Autopilot replies through the local operating-system voice."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
from loguru import logger
from pydantic import ValidationError

from .cache import RenderCache
from .models import LocalVoice, SpeechEvent, SpeechSettings, load_settings
from .native import NativeSpeechAdapter
from .prerender import prerender, read_lines
from .providers import LocalSynthesizer, RoutedSpeechAdapter, default_engines
from .runtime import SpeechRuntime

ROOT = Path(__file__).resolve().parents[3]
TOPICS = {"events.stream-host.reply", "events.stream-host.control"}
MAX_LINE = 16_384


def endpoint(value: str) -> str:
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


def websocket_url(base: str, topics: set[str] | None = None) -> str:
    parsed = urlsplit(base)
    return urlunsplit(
        (
            "wss" if parsed.scheme == "https" else "ws",
            parsed.netloc,
            parsed.path.rstrip("/") + "/ws",
            "topics=" + ",".join(sorted(topics or TOPICS)),
            "",
        )
    )


async def stdout_event(event: dict) -> None:
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


async def replay(runtime: SpeechRuntime, path: Path) -> None:
    with path.open(encoding="utf-8") as stream:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                break
            if len(line) > MAX_LINE:
                raise ValueError("speech input exceeds 16 KiB")
            if line.strip():
                await runtime.submit(SpeechEvent.model_validate_json(line))
    await runtime.drain()


async def backend_loop(runtime: SpeechRuntime, base: str, key: str) -> None:
    from websockets.legacy.client import connect

    topics = {f"events.{runtime.settings.reply_source}.reply", "events.stream-host.control"}
    async with connect(
        websocket_url(base, topics),
        extra_headers={"X-API-Key": key},
        max_size=MAX_LINE,
        max_queue=8,
        open_timeout=5,
        close_timeout=1,
    ) as socket:
        async for raw in socket:
            try:
                envelope = json.loads(raw)
                if envelope.get("channel") not in topics:
                    continue
                event = SpeechEvent.model_validate(envelope["data"]["data"])
                source = runtime.settings.reply_source if event.kind == "reply" else "stream-host"
                if envelope["channel"] != f"events.{source}." + event.kind:
                    continue
            except (ValidationError, ValueError, KeyError, TypeError, AttributeError):
                logger.warning("speech worker ignored malformed host envelope")
                continue
            await runtime.submit(event)


def describe_voices(settings: SpeechSettings, local: LocalSynthesizer) -> dict[str, dict]:
    """Which provider backs each voice and whether it can render now.

    Reported, not enforced: a local engine that is not installed yet (pre-recorded narration) must
    not turn `valid` false and fail the live-stream preflight that runs this command.
    """
    report: dict[str, dict] = {}
    for voice_id, voice in settings.voices.items():
        if isinstance(voice, LocalVoice):
            ready, detail = local.readiness(voice)
            report[voice_id] = {
                "provider": "local",
                "engine": voice.engine,
                "ready": ready,
                "detail": detail,
            }
        else:
            report[voice_id] = {"provider": "native", "ready": True, "detail": "operating system"}
    return report


async def run(args: argparse.Namespace) -> int:
    settings = load_settings(args.config)
    native = NativeSpeechAdapter()
    directory = settings.render_cache_directory
    local = LocalSynthesizer(default_engines(), ROOT, RenderCache(directory) if directory else None)
    adapter = RoutedSpeechAdapter(native, local)
    if args.validate:
        native.check()
        await stdout_event(
            {
                "schema_version": 1,
                "valid": True,
                "on_air_session": settings.on_air_session,
                "voices": list(settings.voices),
                "native_commands": native.dependencies(),
                "voice_providers": describe_voices(settings, local),
            }
        )
        return 0

    if args.prerender is not None:
        lines = read_lines(args.prerender, settings)
        if any(not isinstance(settings.voices[line.voice_id], LocalVoice) for line in lines):
            native.check()
        summary = await prerender(lines, settings, adapter, local, stdout_event)
        await stdout_event(summary)
        return 1 if summary["failed"] else 0

    base = endpoint(os.environ.get("AUTOPILOT_BACKEND_URL", "")) if args.backend else ""
    key = os.environ.get("HCP_API_KEY", "")
    if base and (not key or key in {"change-me", "change-me-to-a-long-random-string"}):
        raise ValueError("set HCP_API_KEY to the configured backend key")

    async with httpx.AsyncClient(timeout=5) as http:

        async def emit(event: dict) -> None:
            if not base:
                await stdout_event(event)
                return
            response = await http.post(
                base + "/events",
                headers={"X-API-Key": key},
                json={"source": "stream-speech", "kind": event["kind"], "data": event},
            )
            response.raise_for_status()

        runtime = SpeechRuntime(settings, adapter, emit)
        await runtime.start()
        try:
            if args.backend:
                await backend_loop(runtime, base, key)
            else:
                await replay(runtime, args.input)
        finally:
            await runtime.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/local/stream-speech.yaml")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--input", type=Path, help="bounded host reply/control JSONL")
    mode.add_argument("--backend", action="store_true")
    mode.add_argument(
        "--prerender", type=Path, help="render JSONL script lines ahead of time and time them"
    )
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError, httpx.HTTPError) as exc:
        # Live modes name only the exception type, because viewer text can reach their errors. A
        # pre-render script is operator-written and its errors never echo a line's text.
        detail = str(exc) if args.prerender is not None else type(exc).__name__
        logger.error("speech worker stopped: {}; check local voice and routing", detail)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
