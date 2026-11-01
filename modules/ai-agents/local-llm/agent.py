"""Async AI agent that subscribes to chat events on Redis, calls Ollama,
publishes responses back, and (optionally) routes audio to TTS.

Wire it into your pipeline by:
  1. Putting incoming chat messages on Redis channel `chat.incoming`
     as JSON: {"user": "...", "text": "..."}
  2. Subscribing to `agent.reply` on your overlay / OBS / TTS bridge.
  3. Loading a persona YAML from ./personas/.

Moderation runs inline, on both directions, per setup/manual.md's own
requirement ("An unmoderated agent on a live stream is a liability, not a
feature") — a regex-flagged incoming message never reaches generate(),
and a regex-flagged reply never reaches `agent.reply`. This uses
moderator.py's fast regex_check only, not its optional LLM second
opinion — an extra Ollama round-trip on every single message would fight
the latency budget this module's own docs call out. Run moderator.py
standalone (--use-llm) alongside this for the slower, more thorough check
and a `chat.moderation` audit trail; that responsibility is intentionally
kept separate from the inline gate here.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Any

import httpx
import redis.asyncio as aioredis
import yaml
from loguru import logger

from memory import Memory
from moderator import regex_check


# ─── Config ─────────────────────────────────────────────────────────────


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://hcp:hcp@127.0.0.1:5432/hcp",
)


def load_persona(path: str) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


# ─── LLM call ───────────────────────────────────────────────────────────


async def generate(
    client: httpx.AsyncClient,
    system_prompt: str,
    history: list[dict[str, str]],
    user_text: str,
) -> str:
    messages = [{"role": "system", "content": system_prompt}, *history,
                {"role": "user", "content": user_text}]
    r = await client.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=httpx.Timeout(60.0, connect=10.0),
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


# ─── Main loop ──────────────────────────────────────────────────────────


async def run(persona_path: str) -> None:
    persona = load_persona(persona_path)
    name: str = persona["name"]
    system_prompt: str = persona["system"]
    style_hint: str = persona.get("style", "")
    if style_hint:
        system_prompt = f"{system_prompt}\n\nStyle guidance:\n{style_hint}"

    logger.info("starting agent: {}", name)

    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    memory = Memory(DATABASE_URL)
    await memory.connect()
    http = httpx.AsyncClient()

    pubsub = redis.pubsub()
    await pubsub.subscribe("chat.incoming")

    stop = asyncio.Event()

    def _handle_signal(*_: Any) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(s, _handle_signal)
        except NotImplementedError:
            pass

    try:
        async for msg in pubsub.listen():
            if stop.is_set():
                break
            if msg.get("type") != "message":
                continue

            try:
                payload = json.loads(msg["data"])
            except (TypeError, json.JSONDecodeError):
                continue

            user = payload.get("user", "anon")
            text = (payload.get("text") or "").strip()
            if not text:
                continue

            incoming_flags = regex_check(text)
            if incoming_flags:
                logger.warning("[{}] incoming flagged, not replying: {} -> {}", name, user, incoming_flags)
                await redis.publish(
                    "chat.moderation",
                    json.dumps({"user": user, "text": text, "reasons": incoming_flags}),
                )
                continue

            try:
                recalled = await memory.recall(name, text, k=4)
                memory_block = ""
                if recalled:
                    memory_block = "Relevant past notes:\n" + "\n".join(
                        f"- ({r.role}) {r.content}" for r in recalled
                    )

                history: list[dict[str, str]] = []
                if memory_block:
                    history.append({"role": "system", "content": memory_block})

                reply = await generate(http, system_prompt, history, f"{user}: {text}")

                reply_flags = regex_check(reply)
                if reply_flags:
                    logger.error(
                        "[{}] generated reply flagged, NOT publishing: {} (to {})",
                        name, reply_flags, user,
                    )
                    await redis.publish(
                        "chat.moderation",
                        json.dumps(
                            {"user": name, "text": reply, "reasons": reply_flags, "source": "agent.reply"}
                        ),
                    )
                    continue

                await memory.store(name, "user", f"{user}: {text}")
                await memory.store(name, "assistant", reply)

                await redis.publish(
                    "agent.reply",
                    json.dumps({"persona": name, "to": user, "text": reply}),
                )
                logger.info("[{}] <- {}: {}", name, user, text[:60])
                logger.info("[{}] -> {}", name, reply[:80])
            except Exception as e:
                logger.exception("agent error: {}", e)
    finally:
        await pubsub.unsubscribe("chat.incoming")
        await pubsub.aclose()
        await redis.aclose()
        await http.aclose()
        await memory.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--persona",
        default=str(Path(__file__).parent / "personas" / "caddy.yaml"),
        help="path to persona YAML",
    )
    args = p.parse_args()
    asyncio.run(run(args.persona))
    return 0


if __name__ == "__main__":
    sys.exit(main())
