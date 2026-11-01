"""P-056 speech-timed avatar animation contracts."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/character-avatar"))

from stream_avatar.models import AvatarEvent, AvatarSettings, load_settings  # noqa: E402
from stream_avatar.runtime import AvatarRuntime  # noqa: E402


def settings() -> AvatarSettings:
    return AvatarSettings.model_validate(
        {
            "schema_version": 1,
            "on_air_session": "main",
            "event_ttl_seconds": 15,
            "vts_url": "ws://127.0.0.1:8001",
            "avatars": {"nova-vrm": {"talk_hotkey": "Talk", "idle_hotkey": "Idle"}},
        }
    )


def event(kind="started", number=1, **updates) -> AvatarEvent:
    data = {
        "schema_version": 1,
        "kind": kind,
        "event_id": f"event-{number}",
        "utterance_id": f"utterance-{number}",
        "session_id": "main",
        "generation": 0,
        "created_at": datetime.now(timezone.utc),
        "avatar_id": "nova-vrm",
    }
    data.update(updates)
    return AvatarEvent.model_validate(data)


class Adapter:
    def __init__(self):
        self.calls = []

    async def connect(self):
        self.calls.append(("connect",))

    async def talk(self, avatar_id):
        self.calls.append(("talk", avatar_id))

    async def idle(self, avatar_id):
        self.calls.append(("idle", avatar_id))

    async def close(self):
        self.calls.append(("close",))


def test_config_and_event_validation():
    loaded = load_settings(ROOT / "configs/local/stream-avatar.yaml")
    assert "nova-vrm" in loaded.avatars
    with pytest.raises(ValidationError):
        AvatarSettings.model_validate({**settings().model_dump(), "unknown": True})
    with pytest.raises(ValidationError):
        event("started", avatar_id=None)


def test_started_and_matching_finish_drive_talk_then_idle():
    async def scenario():
        adapter = Adapter()
        runtime = AvatarRuntime(settings(), adapter)
        await runtime.start()
        assert await runtime.handle(event())
        assert not await runtime.handle(event("finished", 2, utterance_id="different"))
        assert await runtime.handle(event("finished"))
        await runtime.close()
        assert adapter.calls == [
            ("connect",),
            ("talk", "nova-vrm"),
            ("idle", "nova-vrm"),
            ("close",),
        ]

    asyncio.run(scenario())


def test_pause_idles_and_old_off_air_stale_duplicate_events_do_nothing():
    async def scenario():
        adapter = Adapter()
        runtime = AvatarRuntime(settings(), adapter)
        await runtime.start()
        started = event()
        assert await runtime.handle(started)
        assert not await runtime.handle(started)
        assert not await runtime.handle(event(number=2, session_id="other"))
        assert not await runtime.handle(
            event(number=3, created_at=datetime.now(timezone.utc) - timedelta(seconds=30))
        )
        paused = event(
            "controlled",
            4,
            utterance_id=None,
            avatar_id=None,
            paused=True,
            generation=1,
        )
        assert await runtime.handle(paused)
        assert not await runtime.handle(paused)
        resumed = event(
            "controlled",
            6,
            utterance_id=None,
            avatar_id=None,
            paused=False,
            generation=2,
        )
        assert not await runtime.handle(resumed)
        assert not await runtime.handle(event(number=5, generation=0))
        await runtime.close()
        assert [call[0] for call in adapter.calls].count("talk") == 1
        assert [call[0] for call in adapter.calls].count("idle") == 1

    asyncio.run(scenario())


def test_unbound_avatar_and_failure_event_never_animate():
    async def scenario():
        adapter = Adapter()
        runtime = AvatarRuntime(settings(), adapter)
        await runtime.start()
        assert not await runtime.handle(event(avatar_id="missing"))
        assert not await runtime.handle(event("failed", 2, utterance_id=None, avatar_id=None))
        await runtime.close()
        assert adapter.calls == [("connect",), ("close",)]

    asyncio.run(scenario())
