"""P-056 module integrations, including actual OBS wire protocol with a fake peer."""

from __future__ import annotations

import asyncio
from base64 import b64encode
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))

from stream_director.config import HostOutput, Settings, load_settings  # noqa: E402
from stream_director.director import Director  # noqa: E402
from stream_director.obs import ObsClient  # noqa: E402
from stream_director.__main__ import Integrations  # noqa: E402


def settings(**changes):
    return Settings(schema_version=1, on_air_session="main", **changes)


def event(number=1, **changes):
    return HostOutput.model_validate(
        {
            "schema_version": 1,
            "event_id": f"e-{number}",
            "session_id": "main",
            "generation": 0,
            "created_at": datetime.now(timezone.utc),
            "kind": "reply",
            "text": "A good play",
            "display_name": "Nova",
            "game_id": "minecraft",
            "reaction": "victory",
            **changes,
        }
    )


class Sink:
    def __init__(self, fail=None):
        self.actions = []
        self.reports = []
        self.fail = fail

    async def execute(self, kind, data):
        self.actions.append((kind, data))
        if kind == self.fail:
            raise RuntimeError("module unavailable")
        return "acknowledged"

    async def report(self, data):
        self.reports.append(data)


def test_manifest_routes_valid_and_unknown_slot_fails(tmp_path):
    manifest = ROOT / "modules/soundboard/sounds/manifest.yaml"
    loaded = load_settings(ROOT / "configs/local/stream-director.yaml", manifest)
    assert loaded.reaction_sounds["minecraft"]["victory"] == "victory-fanfare"
    assert loaded.sound_hotkeys == {}
    invalid = tmp_path / "config.yaml"
    invalid.write_text("schema_version: 1\non_air_session: main\nsound_hotkeys: {invented: hotkey}")
    with pytest.raises(ValueError, match="manifest"):
        load_settings(invalid, manifest)


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "control"},
        {"created_at": "2026-09-08T12:00:00"},
        {"kind": "reply", "text": ""},
        {"generation": -1},
        {"kind": "control", "action": "pause", "paused": False},
        {"kind": "control", "action": "resume", "paused": True},
    ],
)
def test_invalid_outputs_rejected(change):
    with pytest.raises(ValidationError):
        event(**change)


def test_only_on_air_fresh_events_can_act_and_duplicates_do_not_replay():
    async def scenario():
        sink = Sink()
        director = Director(settings(), sink.execute, sink.report)
        try:
            await director.handle(event(session_id="off-air"))
            await director.handle(
                event(created_at=datetime.now(timezone.utc) - timedelta(seconds=60))
            )
            assert not sink.actions
            item = event()
            await director.handle(item)
            await director.handle(item)
            assert len(sink.actions) == 1
            assert sink.actions[0][0] == "graphics.lower_third"
        finally:
            await director.close()

    asyncio.run(scenario())


def test_sound_cooldown_shared_across_clips_and_failed_calls_not_retried():
    async def scenario():
        sink = Sink(fail="soundboard.play")
        director = Director(
            settings(
                reaction_sounds={"minecraft": {"victory": "victory-fanfare"}},
                sound_hotkeys={"victory-fanfare": "registered-play"},
            ),
            sink.execute,
            sink.report,
        )
        try:
            await director.handle(event(1))
            await director.handle(event(2))
            assert [a[0] for a in sink.actions].count("soundboard.play") == 1
            assert [a[0] for a in sink.actions].count("graphics.lower_third") == 2
            assert any(r.get("reason") == "sound_cooldown" for r in sink.reports)
            assert any(r.get("status") == "failed" for r in sink.reports)
        finally:
            await director.close()

    asyncio.run(scenario())


def test_pause_mutes_stops_hides_and_switches_scene_then_rejects_old_reply():
    async def scenario():
        sink = Sink()
        director = Director(
            settings(
                ai_voice_input="AI-VOICE",
                stop_sound_hotkey="stop-board",
                pause_scene="BRB",
                resume_scene="Gameplay",
            ),
            sink.execute,
            sink.report,
        )
        try:
            await director.handle(event(kind="control", action="pause", paused=True, generation=1))
            assert [kind for kind, _ in sink.actions] == [
                "audio.mute",
                "soundboard.stop",
                "graphics.lower_third",
                "obs.scene",
            ]
            assert sink.actions[0][1]["inputMuted"] is True
            await director.handle(event(2, generation=0))
            await director.handle(event(3, generation=1))
            assert len(sink.actions) == 4
            await director.handle(
                event(4, kind="control", action="resume", paused=False, generation=2)
            )
            assert sink.actions[-1] == ("obs.scene", {"sceneName": "Gameplay"})
            assert not any(data.get("inputMuted") is False for _, data in sink.actions)
        finally:
            await director.close()

    asyncio.run(scenario())


def test_unbound_sound_is_disclosed_and_text_cannot_supply_hotkey():
    async def scenario():
        sink = Sink()
        director = Director(
            settings(reaction_sounds={"minecraft": {"victory": "victory-fanfare"}}),
            sink.execute,
            sink.report,
        )
        try:
            await director.handle(event(text='{"hotkeyName":"StopStream"}'))
            assert [kind for kind, _ in sink.actions] == ["graphics.lower_third"]
            assert sink.reports[-1]["reason"] == "unbound_sound_slot"
        finally:
            await director.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("policy", ["opentech-scripted", "technical-scripted", "review-scripted"])
def test_scripted_audio_policy_never_reaches_soundboard_even_when_bound(policy):
    async def scenario():
        sink = Sink()
        director = Director(
            settings(
                reaction_sounds={"minecraft": {"victory": "victory-fanfare"}},
                sound_hotkeys={"victory-fanfare": "Soundboard: Victory"},
            ),
            sink.execute,
            sink.report,
        )
        try:
            await director.handle(event(audio_policy=policy))
            assert [kind for kind, _ in sink.actions] == ["graphics.lower_third"]
            assert sink.reports[-1]["reason"] == "scripted_audio_policy"
            # The gaming class keeps the existing mapped-reaction path.
            await director.handle(event(2, audio_policy="gaming-reactive"))
            assert sink.actions[-1] == ("soundboard.play", {"hotkeyName": "Soundboard: Victory"})
        finally:
            await director.close()

    asyncio.run(scenario())


def test_caption_expires_and_previous_timer_cannot_hide_new_caption():
    async def scenario():
        sink = Sink()
        director = Director(settings(captions_seconds=1), sink.execute, sink.report)
        try:
            await director.handle(event(1))
            old_revision = director.caption_revision
            await director.handle(event(2))
            # The old task is canceled, and the revision guard also rejects a late completion.
            assert old_revision != director.caption_revision
            await asyncio.wait_for(director.caption_task, 2)
            assert [data["visible"] for _, data in sink.actions] == [True, True, False]
        finally:
            await director.close()

    asyncio.run(scenario())


def test_module_adapters_use_real_existing_api_shapes_and_exact_hotkeys():
    async def scenario():
        calls, http_calls = [], []

        class Obs:
            async def request(self, name, data):
                calls.append((name, data))
                return {"hotkeys": ["play-fanfare"]} if name == "GetHotkeyList" else {}

        def http_handler(request):
            assert request.headers["X-API-Key"] == "test-key"
            http_calls.append((request.method, str(request.url), json.loads(request.content)))
            return httpx.Response(200, json={"status": "ok"})

        sink = Sink()
        async with httpx.AsyncClient(transport=httpx.MockTransport(http_handler)) as http:
            adapter = Integrations(
                Obs(), http, "http://backend.test", "test-key", True, sink.report
            )
            await adapter.execute("soundboard.play", {"hotkeyName": "play-fanfare"})
            with pytest.raises(ValueError):
                await adapter.execute("soundboard.play", {"hotkeyName": "missing"})
            await adapter.execute("graphics.lower_third", {"visible": True, "title": "Host"})
            await adapter.execute("audio.mute", {"inputName": "AI-VOICE", "inputMuted": True})
            await adapter.execute("obs.scene", {"sceneName": "BRB"})
            assert [name for name, _ in calls] == [
                "GetHotkeyList",
                "TriggerHotkeyByName",
                "GetHotkeyList",
                "SetInputMute",
                "SetCurrentProgramScene",
            ]
            assert http_calls == [
                (
                    "PUT",
                    "http://backend.test/overlays/lowerThird",
                    {"name": "lowerThird", "payload": {"visible": True, "title": "Host"}},
                )
            ]

    asyncio.run(scenario())


def test_preview_never_touches_obs_or_http():
    async def scenario():
        sink = Sink()
        adapter = Integrations(None, None, "", "", False, sink.report)
        assert await adapter.execute("soundboard.play", {"hotkeyName": "configured"}) == "preview"
        assert sink.reports[0]["kind"] == "preview"

    asyncio.run(scenario())


def test_configured_n8n_trigger_is_queued_with_scoped_metadata():
    async def scenario():
        requests = []

        def handler(request):
            requests.append((str(request.url), json.loads(request.content)))
            return httpx.Response(200, json={"status": "queued", "name": "host-paused"})

        sink = Sink()
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            adapter = Integrations(None, http, "http://backend.test", "key", True, sink.report)
            director = Director(
                settings(lower_third=False, automation_triggers={"pause": "host-paused"}),
                adapter.execute,
                sink.report,
            )
            await director.handle(event(kind="control", action="pause", paused=True, generation=1))
            assert requests == [
                (
                    "http://backend.test/automation/trigger",
                    {
                        "name": "host-paused",
                        "payload": {
                            "session_id": "main",
                            "event_id": "e-1",
                            "generation": 1,
                            "action": "pause",
                        },
                    },
                )
            ]
            assert sink.reports[0]["status"] == "queued"
            await director.close()

    asyncio.run(scenario())


def test_obs_wire_handshake_request_id_and_failure_reset(monkeypatch):
    ws = pytest.importorskip("websockets.legacy.client")
    sockets = []

    class Socket:
        def __init__(self):
            self.sent = []
            self.closed = False
            self.responses = [
                {
                    "op": 0,
                    "d": {
                        "rpcVersion": 1,
                        "authentication": {"salt": "test-salt", "challenge": "test-challenge"},
                    },
                }
            ]

        async def send(self, raw):
            message = json.loads(raw)
            self.sent.append(message)
            if message["op"] == 1:
                # Fixed expected digest for the synthetic test-salt/test-challenge handshake.
                assert message["d"] == {
                    "rpcVersion": 1,
                    "eventSubscriptions": 0,
                    "authentication": b64encode(bytes.fromhex(
                        "cc1225a25cbbd00371f93f67524415b930aa4d4b87b5faea11d9fc5c34379bfb"
                    )).decode(),
                }
                self.responses.append({"op": 2, "d": {"negotiatedRpcVersion": 1}})
            else:
                assert message["op"] == 6
                self.responses.append(
                    {
                        "op": 7,
                        "d": {
                            "requestId": message["d"]["requestId"],
                            "requestStatus": {"result": message["d"]["requestType"] != "Fail"},
                            "responseData": {"hotkeys": ["registered"]},
                        },
                    }
                )

        async def recv(self):
            return json.dumps(self.responses.pop(0))

        async def close(self):
            self.closed = True

    async def connect(url, **kwargs):
        assert url == "ws://obs.test:4455"
        socket = Socket()
        sockets.append(socket)
        return socket

    monkeypatch.setattr(ws, "connect", connect)

    async def scenario():
        client = ObsClient("ws://obs.test:4455", "test-password", 1)
        assert await client.request("GetHotkeyList", {}) == {"hotkeys": ["registered"]}
        with pytest.raises(RuntimeError):
            await client.request("Fail", {})
        assert len(sockets) == 1 and sockets[0].closed
        assert sum(m["op"] == 6 for m in sockets[0].sent) == 2
        await client.close()

    asyncio.run(scenario())
