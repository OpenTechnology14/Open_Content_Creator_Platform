"""Forward Twitch EventSub chat messages into one Stream Autopilot session."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from loguru import logger

from .models import load_settings
from .runtime import TwitchChatIngress

ROOT = Path(__file__).resolve().parents[3]


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


async def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config)
    if args.validate:
        credentials = bool(
            os.environ.get("TWITCH_CLIENT_ID") and os.environ.get("TWITCH_USER_ACCESS_TOKEN")
        )
        ids = settings.broadcaster_user_id.strip("0") != "" and settings.user_id.strip("0") != ""
        sys.stdout.write(
            json.dumps(
                {
                    "schema_version": 1,
                    "valid": credentials and ids,
                    "session_id": settings.session_id,
                    "required_scope": "user:read:chat",
                    "credentials_present": credentials,
                    "account_ids_configured": ids,
                }
            )
            + "\n"
        )
        return
    base = backend_url(os.environ.get("AUTOPILOT_BACKEND_URL", ""))
    key = os.environ.get("HCP_API_KEY", "")
    if not key or key in {"change-me", "change-me-to-a-long-random-string"}:
        raise ValueError("set HCP_API_KEY")
    async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=5)) as http:

        async def emit(event: dict) -> None:
            response = await http.post(
                base + "/events",
                headers={"X-API-Key": key},
                json={
                    "source": "stream-autopilot",
                    "kind": "input",
                    "stream_id": settings.session_id,
                    "data": event,
                },
            )
            response.raise_for_status()

        ingress = TwitchChatIngress(
            settings,
            os.environ.get("TWITCH_CLIENT_ID", ""),
            os.environ.get("TWITCH_USER_ACCESS_TOKEN", ""),
            http,
            emit,
        )
        await ingress.run()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/local/twitch-chat.yaml")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError, httpx.HTTPError) as exc:
        logger.error("Twitch chat stopped: {}; check account authorization", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
