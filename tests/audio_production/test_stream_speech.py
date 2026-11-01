"""P-056 bounded, cancellable speech playback contracts."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/audio-production"))

from stream_speech.models import SpeechEvent, SpeechSettings, load_settings  # noqa: E402
from stream_speech.runtime import SpeechRuntime  # noqa: E402


def settings(tmp_path: Path, **updates) -> SpeechSettings:
    data = {
        "schema_version": 1,
        "on_air_session": "main",
        "queue_capacity": 2,
        "event_ttl_seconds": 15,
        "output_directory": tmp_path,
        "retain_wav": False,
        "voices": {"nova-local": None},
    }
    data.update(updates)
    return SpeechSettings.model_validate(data)


def reply(number: int = 1, **updates) -> SpeechEvent:
    data = {
        "schema_version": 1,
        "kind": "reply",
        "event_id": f"event-{number}",
        "utterance_id": f"utterance-{number}",
        "session_id": "main",
        "generation": 0,
        "created_at": datetime.now(timezone.utc),
        "text": "Hello from Nova",
        "voice_id": "nova-local",
        "avatar_id": "nova-vrm",
    }
    data.update(updates)
    return SpeechEvent.model_validate(data)


def control(number: int, action: str, paused: bool, generation: int) -> SpeechEvent:
    return SpeechEvent.model_validate(
        {
            "schema_version": 1,
            "kind": "control",
            "event_id": f"control-{number}",
            "session_id": "main",
            "generation": generation,
            "created_at": datetime.now(timezone.utc),
            "action": action,
            "paused": paused,
        }
    )


class Adapter:
    def __init__(self, hold: bool = False) -> None:
        self.calls = []
        self.hold = hold
        self.release = asyncio.Event()

    async def synthesize(self, text, voice, output):
        self.calls.append(("synthesize", text, voice, output.name))
        output.write_bytes(b"wave")
        return 1.25

    async def play(self, path):
        self.calls.append(("play", path.name))
        if self.hold:
            await self.release.wait()

    async def stop(self):
        self.calls.append(("stop",))
        self.release.set()


def test_settings_and_events_reject_unknown_or_incomplete_values(tmp_path):
    loaded = load_settings(ROOT / "configs/local/stream-speech.yaml")
    assert loaded.on_air_session == "minecraft-main"
    with pytest.raises(ValidationError):
        settings(tmp_path, invented=True)
    with pytest.raises(ValidationError):
        reply(text="")
    with pytest.raises(ValidationError):
        control(1, "pause", False, 1)
    assert len(reply(2, utterance_id="u" * 200).utterance_id) == 200


def test_reply_uses_bound_voice_emits_real_timing_and_removes_wav(tmp_path):
    async def scenario():
        events = []

        async def emit(value):
            events.append(value)

        adapter = Adapter()
        runtime = SpeechRuntime(settings(tmp_path), adapter, emit)
        await runtime.start()
        assert await runtime.submit(reply())
        await runtime.drain()
        await runtime.close()
        assert [event["kind"] for event in events] == ["started", "finished"]
        assert events[0]["duration_seconds"] == 1.25
        assert [call[0] for call in adapter.calls] == ["synthesize", "play", "stop"]
        assert list(tmp_path.iterdir()) == []

    asyncio.run(scenario())


def test_pause_cancels_active_playback_and_old_generation_never_speaks(tmp_path):
    async def scenario():
        events = []

        async def emit(value):
            events.append(value)

        adapter = Adapter(hold=True)
        runtime = SpeechRuntime(settings(tmp_path), adapter, emit)
        await runtime.start()
        assert await runtime.submit(reply())
        for _ in range(20):
            if any(call[0] == "play" for call in adapter.calls):
                break
            await asyncio.sleep(0.01)
        assert await runtime.submit(control(1, "pause", True, 1))
        assert not await runtime.submit(reply(2, generation=0))
        assert not await runtime.submit(reply(3, generation=1))
        await runtime.close()
        assert ("stop",) in adapter.calls
        assert any(event["kind"] == "controlled" for event in events)
        assert [call[0] for call in adapter.calls].count("play") == 1

    asyncio.run(scenario())


def test_new_generation_cancels_active_old_reply_before_queueing(tmp_path):
    async def scenario():
        events = []

        async def emit(value):
            events.append(value)

        adapter = Adapter(hold=True)
        runtime = SpeechRuntime(settings(tmp_path), adapter, emit)
        await runtime.start()
        assert await runtime.submit(reply())
        for _ in range(20):
            if any(call[0] == "play" for call in adapter.calls):
                break
            await asyncio.sleep(0.01)
        assert await runtime.submit(reply(2, generation=1))
        adapter.release.set()
        await runtime.drain()
        await runtime.close()
        assert [call[0] for call in adapter.calls].count("play") == 2
        assert not any(
            event["kind"] == "finished" and event["utterance_id"] == "utterance-1"
            for event in events
        )

    asyncio.run(scenario())


def test_off_air_stale_duplicate_queue_and_unbound_voice_fail_closed(tmp_path):
    async def scenario():
        events = []

        async def emit(value):
            events.append(value)

        adapter = Adapter(hold=True)
        runtime = SpeechRuntime(settings(tmp_path, queue_capacity=1), adapter, emit)
        await runtime.start()
        assert not await runtime.submit(reply(session_id="other"))
        assert not await runtime.submit(
            reply(2, created_at=datetime.now(timezone.utc) - timedelta(seconds=30))
        )
        first = reply(3)
        assert await runtime.submit(first)
        assert not await runtime.submit(first)
        for _ in range(20):
            if any(call[0] == "play" for call in adapter.calls):
                break
            await asyncio.sleep(0.01)
        assert await runtime.submit(reply(4))
        assert not await runtime.submit(reply(5))
        adapter.release.set()
        await runtime.drain()
        await runtime.submit(reply(6, voice_id="missing"))
        await runtime.drain()
        await runtime.close()
        reasons = {event.get("reason") for event in events}
        assert {
            "off_air_or_stale",
            "duplicate_or_old_generation",
            "queue_full",
            "unbound_voice",
        } <= reasons

    asyncio.run(scenario())
