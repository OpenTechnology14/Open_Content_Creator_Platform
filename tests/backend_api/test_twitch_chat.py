"""Twitch EventSub chat contracts without network or account credentials."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = str(ROOT / "modules/backend-api")
sys.path.insert(0, MODULE_ROOT)

from twitch_chat.models import TwitchSettings, load_settings  # noqa: E402
from twitch_chat.runtime import chat_event, subscription_request  # noqa: E402

sys.path.remove(MODULE_ROOT)


def settings() -> TwitchSettings:
    return load_settings(ROOT / "configs/local/twitch-chat.yaml")


def notification(text="hello", message_id="message-1"):
    return {
        "metadata": {
            "message_id": "envelope-1",
            "message_type": "notification",
            "message_timestamp": "2026-09-09T12:00:00Z",
            "subscription_type": "channel.chat.message",
        },
        "payload": {
            "subscription": {"type": "channel.chat.message"},
            "event": {
                "message_id": message_id,
                "chatter_user_name": "Viewer",
                "message": {"text": text},
            },
        },
    }


def test_subscription_is_scoped_to_configured_channel_and_socket():
    request = subscription_request(settings(), "socket-session")
    assert request["type"] == "channel.chat.message"
    assert request["condition"] == {
        "broadcaster_user_id": "000000000",
        "user_id": "000000000",
    }
    assert request["transport"] == {"method": "websocket", "session_id": "socket-session"}


def test_notification_becomes_bounded_host_content_with_source_timestamp_and_id():
    result = chat_event(settings(), notification(text="x" * 600, message_id="m" * 100))
    assert result is not None
    assert result["kind"] == "chat"
    assert result["session_id"] == "minecraft-main"
    assert len(result["text"]) == 500
    assert result["event_id"].startswith("twitch-")
    assert len(result["event_id"]) == 55
    assert result["occurred_at"] == "2026-09-09T12:00:00Z"


def test_non_chat_and_malformed_notifications_are_ignored():
    keepalive = notification()
    keepalive["metadata"]["message_type"] = "session_keepalive"
    assert chat_event(settings(), keepalive) is None
    malformed = notification()
    del malformed["payload"]["event"]["message"]
    assert chat_event(settings(), malformed) is None


def test_config_rejects_non_twitch_endpoints_and_unknown_fields():
    data = settings().model_dump()
    with pytest.raises(ValidationError):
        TwitchSettings.model_validate({**data, "websocket_url": "wss://example.com/ws"})
    with pytest.raises(ValidationError):
        TwitchSettings.model_validate({**data, "secret": "no"})
