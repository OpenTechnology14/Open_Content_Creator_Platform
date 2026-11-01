"""Lightweight chat moderation.

Flags messages with simple regex/keyword rules and a (optional) LLM second
opinion. The decision is exposed via Redis (`chat.moderation`) so other
components (overlay, agent, notifier) can act on it.

Default behavior is FLAG, never auto-ban. Bans must be confirmed by a human
through StreamDeck / overlay UI.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass

import httpx
import redis.asyncio as aioredis
from loguru import logger


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODERATOR_MODEL", "llama3.1:8b")
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


SLUR_PATTERNS = [
    # Intentionally empty — populate with your own list, optionally loaded
    # from a config file. Avoid committing a slur list to the repo.
]
SPAM_PATTERNS = [
    re.compile(r"(?i)\b(?:free\s+v[-]?bucks|nitro\s+gift|click\s+here)\b"),
    re.compile(r"https?://\S+\.(?:ru|tk|click|zip)\b"),
]


@dataclass
class Verdict:
    flag: bool
    reasons: list[str]
    raw_text: str
    user: str


def regex_check(text: str) -> list[str]:
    reasons: list[str] = []
    for p in SLUR_PATTERNS:
        if p.search(text):
            reasons.append("slur")
            break
    for p in SPAM_PATTERNS:
        if p.search(text):
            reasons.append("spam")
            break
    return reasons


async def llm_check(http: httpx.AsyncClient, text: str) -> list[str]:
    prompt = (
        "Classify the following chat message. Respond with a single word: "
        "OK, FLAG, or BAN.\n\nMessage: " + text
    )
    try:
        r = await http.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=10.0,
        )
        r.raise_for_status()
        verdict = r.json().get("response", "").strip().upper()
        if verdict.startswith("FLAG") or verdict.startswith("BAN"):
            return ["llm:" + verdict.lower()]
    except Exception as e:
        logger.warning("llm moderation failed: {}", e)
    return []


async def run(use_llm: bool) -> None:
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    http = httpx.AsyncClient()
    pubsub = redis.pubsub()
    await pubsub.subscribe("chat.incoming")

    try:
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                payload = json.loads(msg["data"])
            except (TypeError, json.JSONDecodeError):
                continue
            text = payload.get("text", "")
            user = payload.get("user", "anon")
            if not text:
                continue
            reasons = regex_check(text)
            if not reasons and use_llm:
                reasons = await llm_check(http, text)
            verdict = Verdict(
                flag=bool(reasons), reasons=reasons, raw_text=text, user=user
            )
            if verdict.flag:
                await redis.publish(
                    "chat.moderation",
                    json.dumps(
                        {"user": user, "text": text, "reasons": reasons}
                    ),
                )
                logger.warning("flagged: {} -> {}", user, reasons)
    finally:
        await pubsub.unsubscribe("chat.incoming")
        await pubsub.aclose()
        await redis.aclose()
        await http.aclose()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--use-llm", action="store_true",
                   help="enable LLM second-opinion (Ollama)")
    args = p.parse_args()
    asyncio.run(run(use_llm=args.use_llm))
    return 0


if __name__ == "__main__":
    sys.exit(main())
