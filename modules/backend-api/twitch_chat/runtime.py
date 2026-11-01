"""EventSub WebSocket connection, subscription, reconnect and backend handoff."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import Awaitable, Callable

import httpx

from .models import TwitchSettings

Emit = Callable[[dict], Awaitable[None]]
MAX_MESSAGE = 64 * 1024


def subscription_request(settings: TwitchSettings, session_id: str) -> dict:
    return {
        "type": "channel.chat.message",
        "version": "1",
        "condition": {
            "broadcaster_user_id": settings.broadcaster_user_id,
            "user_id": settings.user_id,
        },
        "transport": {"method": "websocket", "session_id": session_id},
    }


def chat_event(settings: TwitchSettings, envelope: dict) -> dict | None:
    metadata = envelope.get("metadata", {})
    payload = envelope.get("payload", {})
    subscription = payload.get("subscription", {})
    event = payload.get("event", {})
    if (
        metadata.get("message_type") != "notification"
        or metadata.get("subscription_type") != "channel.chat.message"
        or subscription.get("type") != "channel.chat.message"
    ):
        return None
    text = event.get("message", {}).get("text")
    user = event.get("chatter_user_name")
    message_id = event.get("message_id") or metadata.get("message_id")
    timestamp = metadata.get("message_timestamp")
    if not all(isinstance(value, str) and value for value in (text, user, message_id, timestamp)):
        return None
    safe_id = message_id
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", safe_id):
        safe_id = "twitch-" + hashlib.sha256(safe_id.encode()).hexdigest()[:48]
    return {
        "schema_version": 1,
        "event_id": safe_id,
        "session_id": settings.session_id,
        "kind": "chat",
        "occurred_at": timestamp,
        "text": text[:500],
        "user": user[:80],
    }


class TwitchChatIngress:
    def __init__(
        self,
        settings: TwitchSettings,
        client_id: str,
        user_token: str,
        http: httpx.AsyncClient,
        emit: Emit,
    ) -> None:
        if not client_id or not user_token:
            raise ValueError("Twitch client ID and user access token are required")
        self.settings = settings
        self.client_id = client_id
        self.user_token = user_token
        self.http = http
        self.emit = emit

    async def _subscribe(self, session_id: str) -> None:
        response = await self.http.post(
            self.settings.helix_url + "/eventsub/subscriptions",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Client-Id": self.client_id,
                "Content-Type": "application/json",
            },
            json=subscription_request(self.settings, session_id),
        )
        response.raise_for_status()

    @staticmethod
    def _welcome(raw: str) -> tuple[str, float]:
        envelope = json.loads(raw)
        if envelope.get("metadata", {}).get("message_type") != "session_welcome":
            raise ValueError("Twitch did not send a welcome message")
        session = envelope["payload"]["session"]
        session_id = session["id"]
        timeout = float(session.get("keepalive_timeout_seconds") or 10)
        if not isinstance(session_id, str) or not session_id or not 10 <= timeout <= 600:
            raise ValueError("invalid Twitch welcome message")
        return session_id, timeout

    async def connection(self, url: str, subscribe: bool) -> None:
        from websockets.legacy.client import connect

        socket = await connect(
            url, max_size=MAX_MESSAGE, max_queue=32, open_timeout=10, close_timeout=2
        )
        try:
            session_id, keepalive = self._welcome(await asyncio.wait_for(socket.recv(), 10))
            if subscribe:
                await self._subscribe(session_id)
            while True:
                raw = await asyncio.wait_for(socket.recv(), keepalive + 5)
                envelope = json.loads(raw)
                message_type = envelope.get("metadata", {}).get("message_type")
                if message_type == "notification":
                    event = chat_event(self.settings, envelope)
                    if event is not None:
                        await self.emit(event)
                elif message_type == "session_reconnect":
                    reconnect_url = (
                        envelope.get("payload", {}).get("session", {}).get("reconnect_url")
                    )
                    if not isinstance(reconnect_url, str) or not reconnect_url.startswith(
                        "wss://eventsub.wss.twitch.tv/"
                    ):
                        raise ValueError("invalid Twitch reconnect URL")
                    replacement = await connect(
                        reconnect_url,
                        max_size=MAX_MESSAGE,
                        max_queue=32,
                        open_timeout=10,
                        close_timeout=2,
                    )
                    _, keepalive = self._welcome(await asyncio.wait_for(replacement.recv(), 10))
                    await socket.close()
                    socket = replacement
                elif message_type == "revocation":
                    raise RuntimeError("Twitch revoked the chat subscription")
        finally:
            await socket.close()

    async def run(self) -> None:
        from websockets.exceptions import WebSocketException

        delay = self.settings.reconnect_min_seconds
        while True:
            try:
                await self.connection(self.settings.websocket_url, subscribe=True)
                delay = self.settings.reconnect_min_seconds
            except asyncio.CancelledError:
                raise
            except (OSError, ValueError, RuntimeError, httpx.HTTPError, WebSocketException):
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.settings.reconnect_max_seconds)
