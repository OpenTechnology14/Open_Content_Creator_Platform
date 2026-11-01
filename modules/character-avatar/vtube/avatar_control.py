"""Agent -> avatar control bridge.

This is the seam `README.md` and `setup/manual.md` both name but never
wired: "the AI agent decides an expression or mouth state, and this module
applies it to the avatar." `ai-agents/local-llm/agent.py` publishes every
reply to the Redis channel `agent.reply` as
`{"persona": ..., "to": ..., "text": ...}`. This module subscribes to that
same channel and, for each reply, triggers a "talking" VTube Studio hotkey,
holds it for a duration estimated from the reply's length, then triggers an
"idle" hotkey.

Which hotkey fires per persona is configured in `avatar_mapping.yaml`, not
hardcoded — a persona with no entry there falls back to `default`.

Wire it into your pipeline by:
  1. Setting up VTube Studio's hotkeys (Settings -> Hotkeys) with the same
     names/IDs this module's `avatar_mapping.yaml` references.
  2. Running `python avatar_control.py` alongside `ai-agents/local-llm/agent.py`.

Import ordering note: `redis.asyncio` and `vts_client` (which imports
`websockets`) are imported lazily, inside `run()`, not at module level.
This keeps the pure functions below importable — and testable offline —
without either dependency installed, the same reason `ai-agents/agent.py`
keeps `asyncpg` behind `memory.py` rather than importing it directly.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

DEFAULT_MAPPING_PATH = Path(__file__).parent / "avatar_mapping.yaml"
WORDS_PER_MINUTE = 170
MIN_TALK_SECONDS = 0.6
MAX_TALK_SECONDS = 8.0


# ─── Pure functions ─────────────────────────────────────────────────────


def parse_agent_reply(raw: str) -> dict[str, Any] | None:
    """Parse one `agent.reply` Redis payload. Returns None (skip, don't
    crash) on anything malformed or incomplete — mirrors agent.py's own
    handling of its `chat.incoming` messages."""
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if not payload.get("persona") or not payload.get("text"):
        return None
    return payload


def load_avatar_mapping(path: str | Path = DEFAULT_MAPPING_PATH) -> dict[str, Any]:
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    default = data.get("default") if isinstance(data, dict) else None
    if not isinstance(default, dict) or "talk_hotkey" not in default or "idle_hotkey" not in default:
        raise ValueError(f"{path}: 'default' section must set talk_hotkey and idle_hotkey")
    return data


def hotkey_for_persona(persona: str, mapping: dict[str, Any], key: str) -> str:
    """`key` is 'talk_hotkey' or 'idle_hotkey'. A persona missing from
    `personas:` (or the whole section missing) falls back to `default`."""
    personas = mapping.get("personas") or {}
    override = personas.get(persona) or {}
    return override.get(key) or mapping["default"][key]


def estimate_talk_seconds(
    text: str,
    wpm: int = WORDS_PER_MINUTE,
    min_seconds: float = MIN_TALK_SECONDS,
    max_seconds: float = MAX_TALK_SECONDS,
) -> float:
    words = len(text.split())
    if words == 0:
        return min_seconds
    seconds = (words / wpm) * 60.0
    return max(min_seconds, min(max_seconds, seconds))


# ─── Bridge loop ────────────────────────────────────────────────────────


async def run(mapping_path: str | Path = DEFAULT_MAPPING_PATH, redis_url: str | None = None) -> None:
    import redis.asyncio as aioredis

    sys.path.insert(0, str(Path(__file__).parent))
    from vts_client import VTSClient  # noqa: E402

    mapping = load_avatar_mapping(mapping_path)
    redis_url = redis_url or os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

    vts = VTSClient()
    await vts.connect()

    redis = aioredis.from_url(redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("agent.reply")

    try:
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue

            payload = parse_agent_reply(msg["data"])
            if payload is None:
                continue

            persona = payload["persona"]
            talk_hotkey = hotkey_for_persona(persona, mapping, "talk_hotkey")
            idle_hotkey = hotkey_for_persona(persona, mapping, "idle_hotkey")
            duration = estimate_talk_seconds(payload["text"])

            await vts.trigger_hotkey(talk_hotkey)
            logger.info("avatar: [{}] talking ({:.1f}s)", persona, duration)
            await asyncio.sleep(duration)
            await vts.trigger_hotkey(idle_hotkey)
    finally:
        await pubsub.unsubscribe("agent.reply")
        await pubsub.aclose()
        await redis.aclose()
        await vts.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Agent -> avatar control bridge")
    p.add_argument("--mapping", default=str(DEFAULT_MAPPING_PATH), help="path to avatar_mapping.yaml")
    args = p.parse_args()
    asyncio.run(run(args.mapping))
    return 0


if __name__ == "__main__":
    sys.exit(main())
