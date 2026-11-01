"""Run a local JSONL rehearsal or connect to the authenticated backend event bus."""

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

from .models import HostEvent, load_config
from .responders import OllamaResponder, RehearsalResponder
from .runtime import HostRuntime

ROOT = Path(__file__).resolve().parents[3]
MAX_LINE = 16384


class SetupError(ValueError):
    """Operator-facing diagnostic written by us, never copied from model/viewer input."""


def endpoint(value: str, name: str) -> str:
    """Validate configured HTTP endpoints without echoing secrets in diagnostics."""
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise SetupError(f"{name} must be an HTTP(S) URL without credentials, query or fragment")
    return value.rstrip("/")


def websocket_url(base: str) -> str:
    """Build the existing backend /ws endpoint; credentials travel only in headers."""
    parsed = urlsplit(base)
    return urlunsplit(
        (
            "wss" if parsed.scheme == "https" else "ws",
            parsed.netloc,
            parsed.path.rstrip("/") + "/ws",
            "topics=events.stream-autopilot.input",
            "",
        )
    )


async def stdout_event(event: dict) -> None:
    """JSONL is the explicit CLI output contract, not application logging."""
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


async def replay(runtime: HostRuntime, path: Path) -> None:
    """Read bounded JSONL records. File replay drains between records for deterministic demos."""
    with path.open(encoding="utf-8") as stream:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                break
            if len(line) > MAX_LINE:
                raise ValueError("input record exceeds 16 KiB")
            if line.strip():
                await runtime.submit(HostEvent.model_validate_json(line))
                await runtime.drain()


async def backend_loop(runtime: HostRuntime, base: str, key: str) -> None:
    """Read authenticated backend events; fail closed on disconnect (no stale replay)."""
    from websockets.legacy.client import connect

    async with connect(
        websocket_url(base),
        extra_headers={"X-API-Key": key},
        max_size=MAX_LINE,
        max_queue=16,
        open_timeout=10,
        close_timeout=2,
    ) as socket:
        logger.info("stream host connected to backend; sessions={}", len(runtime.sessions))
        async for raw in socket:
            try:
                envelope = json.loads(raw)
                if envelope.get("channel") != "events.stream-autopilot.input":
                    continue
                payload = envelope["data"]["data"]
                # Rehearsal files can omit timestamps; network producers must preserve age.
                if not isinstance(payload, dict) or "occurred_at" not in payload:
                    raise ValueError("network events require occurred_at")
                event = HostEvent.model_validate(payload)
            except (ValidationError, ValueError, TypeError, KeyError, AttributeError):
                logger.warning("discarded malformed host event")
                continue
            await runtime.submit(event)


async def run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    selected = os.environ.get("AUTOPILOT_SESSION_ID")
    if selected:
        if selected not in config.sessions:
            raise SetupError("selected production session is not enabled in host config")
        config = config.model_copy(update={"sessions": {selected: config.sessions[selected]}})
    if args.validate:
        await stdout_event(
            {
                "schema_version": 1,
                "valid": True,
                "sessions": list(config.sessions),
                "personas": list(config.personas),
                "gameplay_enabled": False,
                "bindings": {
                    key: {"persona_id": item.persona_id,
                          "voice_id": config.resolve_persona(item.persona_id).voice_id,
                          "avatar_id": config.resolve_persona(item.persona_id).avatar_id}
                    for key, item in config.sessions.items()
                },
            }
        )
        return
    base = None
    key = None
    if args.backend:
        base = endpoint(os.environ.get("AUTOPILOT_BACKEND_URL", ""), "AUTOPILOT_BACKEND_URL")
        key = os.environ.get("HCP_API_KEY")
        if not key or key in {"change-me", "change-me-to-a-long-random-string"}:
            raise SetupError("set HCP_API_KEY to the backend's configured key")
    async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5)) as http:
        if args.rehearsal:
            responder = RehearsalResponder()
            logger.info("SCRIPTED REHEARSAL: no LLM inference or gameplay")
        else:
            url = endpoint(os.environ.get("OLLAMA_HOST", ""), "OLLAMA_HOST")
            model = os.environ.get("OLLAMA_MODEL", "")
            if not model:
                raise SetupError("set OLLAMA_MODEL to an installed local model")
            responder = OllamaResponder(http, url, model)

        failed = False

        async def emit(event: dict) -> None:
            nonlocal failed
            if event["kind"] == "error":
                failed = True
            if base:
                result = await http.post(
                    base + "/events",
                    headers={"X-API-Key": key},
                    json={"source": "stream-host", "kind": event["kind"], "data": event},
                )
                result.raise_for_status()
            else:
                await stdout_event(event)

        runtime = HostRuntime(config, responder, emit)
        await runtime.start()
        try:
            if args.backend:
                await backend_loop(runtime, base, key)
            else:
                await replay(runtime, args.input)
        finally:
            await runtime.close()
        if failed and not args.backend:
            raise RuntimeError("one or more rehearsal replies failed")


def main() -> int:
    from websockets.exceptions import WebSocketException

    parser = argparse.ArgumentParser(description="Stream Autopilot conversational host (P-056)")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/local/stream-autopilot.yaml")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true", help="validate configuration only")
    mode.add_argument("--input", type=Path, help="replay a local JSONL input file")
    mode.add_argument("--backend", action="store_true", help="consume authenticated backend events")
    parser.add_argument(
        "--rehearsal", action="store_true", help="explicit scripted replies, no LLM"
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130
    except SetupError as exc:
        logger.error("host setup: {}", exc)
        return 1
    except (OSError, ValueError, RuntimeError, httpx.HTTPError, WebSocketException) as exc:
        # ValidationError can contain viewer data. Never dump it or credential-bearing URLs.
        logger.error("host stopped: {}; check configuration and dependencies", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
