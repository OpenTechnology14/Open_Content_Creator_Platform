"""Owned cue bindings cannot bypass speech generation, pause, model or hotkey guards."""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/character-avatar"))
from stream_avatar.models import AvatarSettings, AvatarCueEvent, AvatarEvent  # noqa: E402
from stream_avatar.runtime import AvatarRuntime  # noqa: E402
from stream_avatar.vts import VtsAvatarAdapter  # noqa: E402

CUES = ["wave", "nod", "shrug", "look_left", "look_right", "happy", "surprised", "neutral"]


def settings():
    return AvatarSettings.model_validate(
        {
            "schema_version": 1,
            "on_air_session": "show",
            "vts_url": "ws://127.0.0.1:8001",
            "full_body_enabled": True,
            "speech_cues": ["nod"],
            "avatars": {
                "owned": {
                    "talk_hotkey": "talk",
                    "idle_hotkey": "idle",
                    "vts_model_id": "model-1",
                    "cues": {cue: "key-" + cue for cue in CUES},
                }
            },
        }
    )


class Adapter:
    def __init__(self):
        self.actions = []

    async def connect(self):
        pass

    async def talk(self, avatar):
        self.actions.append(("talk", avatar))

    async def idle(self, avatar):
        self.actions.append(("idle", avatar))

    async def cue(self, avatar, cue):
        self.actions.append((cue, avatar))

    async def close(self):
        pass


def cue(**updates):
    return AvatarCueEvent.model_validate(
        {
            "schema_version": 1,
            "kind": "cue",
            "event_id": "cue-1",
            "session_id": "show",
            "avatar_id": "owned",
            "cue": "wave",
            "created_at": datetime.now(timezone.utc),
            **updates,
        }
    )


def test_cues_require_complete_distinct_owned_bindings():
    value = settings().model_dump()
    value["avatars"]["owned"]["cues"].pop("nod")
    with pytest.raises(ValueError):
        AvatarSettings.model_validate(value)
    value = settings().model_dump()
    value["avatars"]["owned"]["cues"]["wave"] = "talk"
    with pytest.raises(ValueError):
        AvatarSettings.model_validate(value)


def test_cues_keep_speech_generation_and_utterance_identity():
    async def scenario():
        adapter = Adapter()
        runtime = AvatarRuntime(settings(), adapter)
        assert not await runtime.handle_cue(cue())  # Not resumed/started yet.
        started = AvatarEvent.model_validate(
            {
                "schema_version": 1,
                "kind": "started",
                "event_id": "s1",
                "session_id": "show",
                "generation": 7,
                "created_at": datetime.now(timezone.utc),
                "utterance_id": "u1",
                "avatar_id": "owned",
            }
        )
        await runtime.handle(started)
        assert adapter.actions == [("talk", "owned"), ("nod", "owned")]
        request = cue()
        assert await runtime.handle_cue(request)
        assert not await runtime.handle_cue(request)
        assert runtime.generation == 7 and runtime.active_utterance == "u1"
        assert not await runtime.handle_cue(
            cue(event_id="old", created_at=datetime.now(timezone.utc) - timedelta(seconds=20))
        )
        assert not await runtime.handle_cue(cue(event_id="other", session_id="other"))
        await runtime.handle(
            AvatarEvent.model_validate(
                {
                    "schema_version": 1,
                    "kind": "controlled",
                    "event_id": "pause",
                    "session_id": "show",
                    "generation": 8,
                    "created_at": datetime.now(timezone.utc),
                    "paused": True,
                }
            )
        )
        assert not await runtime.handle_cue(cue(event_id="paused"))

    asyncio.run(scenario())


def test_wrong_model_and_non_animation_hotkey_never_trigger():
    async def scenario():
        adapter = VtsAvatarAdapter(settings())

        class Client:
            calls = []
            model = "different"
            kind = "ChangeVTSModel"

            async def get_current_model(self):
                return {"data": {"modelLoaded": True, "modelID": self.model}}

            async def _send(self, kind):
                return {"data": {"availableHotkeys": [{"hotkeyID": "key-wave", "type": self.kind}]}}

            async def trigger_hotkey(self, key):
                self.calls.append(key)
                return {"messageType": "HotkeyTriggerResponse"}

        adapter.client = Client()
        with pytest.raises(RuntimeError):
            await adapter.cue("owned", "wave")
        adapter.client.model = "model-1"
        with pytest.raises(RuntimeError):
            await adapter.cue("owned", "wave")
        assert adapter.client.calls == []
        adapter.client.kind = "TriggerAnimation"
        await adapter.cue("owned", "wave")
        assert adapter.client.calls == ["key-wave"]

    asyncio.run(scenario())
