"""P-066 director exclusivity, failure and runtime configuration contracts."""

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))

from stream_director.config import HostOutput, Settings  # noqa: E402
from stream_director.director import Director  # noqa: E402
from stream_autopilot.production import load_runtime_settings, ProductionDriver  # noqa: E402


def manifest(tmp_path):
    audio = tmp_path / "accepted.wav"
    audio.write_bytes(b"test-audio")
    path = tmp_path / "production.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profiles": {
                    "nova-builder": {
                        "revision_id": "reviewed",
                        "game_id": "minecraft",
                        "voice_id": "nova-local",
                        "stop_hotkey": "stop-all",
                        "assets": [
                            {
                                "reaction": "victory",
                                "text": "Accepted phrase",
                                "file": str(audio),
                                "sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
                                "duration_seconds": 1,
                                "peak": 0.1,
                                "hotkey": "accepted-hotkey",
                            }
                        ],
                    }
                },
            }
        )
    )
    return path


def event(**kwargs):
    return HostOutput.model_validate(
        {
            "schema_version": 1,
            "kind": "reply",
            "event_id": "one",
            "session_id": "main",
            "generation": 0,
            "created_at": datetime.now(timezone.utc),
            "game_id": "minecraft",
            "persona_id": "nova-builder",
            "voice_id": "nova-local",
            "avatar_id": "nova",
            "utterance_id": "main:0:one",
            "text": "Live fallback",
            "reaction": "victory",
            "audio_policy": "gaming-reactive",
            **kwargs,
        }
    )


@pytest.mark.parametrize(
    "case,expected",
    [
        ("accepted", "soundboard.play"),
        ("unbound", "speech.reply"),
        ("missing", "speech.reply"),
        ("tampered", "speech.reply"),
        ("uncertain", "soundboard.play"),
        ("scripted", "speech.reply"),
        ("wrong_persona", "speech.reply"),
        ("drop", None),
    ],
)
def test_one_audio_route_per_event_and_no_retry_after_uncertain_dispatch(tmp_path, case, expected):
    async def scenario():
        path = manifest(tmp_path)
        if case == "missing":
            (tmp_path / "accepted.wav").unlink()
        if case == "tampered":
            (tmp_path / "accepted.wav").write_bytes(b"changed")
        actions, reports = [], []

        async def execute(kind, data):
            actions.append((kind, data))
            if kind == "soundboard.available":
                return "unbound" if case in {"unbound", "drop"} else "available"
            if kind == "soundboard.play" and case == "uncertain":
                raise TimeoutError("may already be playing")
            return "acknowledged"

        async def report(data):
            reports.append(data)

        director = Director(
            Settings(
                schema_version=1,
                on_air_session="main",
                phrase_manifest=path,
                lower_third=False,
                phrase_fallback="drop" if case == "drop" else "live_voice",
            ),
            execute,
            report,
        )
        message = event(audio_policy="technical-scripted") if case == "scripted" else event()
        if case == "wrong_persona":
            message = event(persona_id="other")
        await director.handle(message)
        await director.handle(message)
        audio = [kind for kind, _ in actions if kind in {"soundboard.play", "speech.reply"}]
        assert audio == ([expected] if expected else [])
        if case == "uncertain":
            assert any(r.get("reason") == "clip_dispatch_uncertain" for r in reports)
        await director.close()

    asyncio.run(scenario())


def test_pause_stops_clips_and_rejects_off_air_old_generation(tmp_path):
    async def scenario():
        actions = []

        async def execute(kind, data):
            actions.append((kind, data))
            return "available" if kind == "soundboard.available" else "acknowledged"

        async def report(data):
            pass

        director = Director(
            Settings(
                schema_version=1,
                on_air_session="main",
                phrase_manifest=manifest(tmp_path),
                lower_third=False,
            ),
            execute,
            report,
        )
        await director.handle(event(session_id="off-air"))
        assert not actions
        await director.handle(event(kind="control", action="pause", paused=True, generation=2))
        await director.handle(event(event_id="old", generation=1))
        await director.handle(event(event_id="paused", generation=2))
        assert actions == [("soundboard.stop", {"hotkeyName": "stop-all"})]
        await director.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "source,apply,valid",
    [
        ("stream-host", True, False),
        ("stream-director", False, False),
        ("stream-director", True, True),
    ],
)
def test_production_driver_requires_exclusive_speech_source(tmp_path, source, apply, valid):
    runtime = yaml.safe_load((ROOT / "configs/local/stream-runtime.yaml").read_text())
    director = yaml.safe_load((ROOT / runtime["director_config"]).read_text())
    speech = yaml.safe_load((ROOT / runtime["speech_config"]).read_text())
    director["phrase_manifest"] = str(manifest(tmp_path))
    speech["reply_source"] = source
    dpath, spath = tmp_path / "director.yaml", tmp_path / "speech.yaml"
    dpath.write_text(yaml.safe_dump(director))
    spath.write_text(yaml.safe_dump(speech))
    runtime.update(director_config=str(dpath), speech_config=str(spath), director_apply=apply)
    path = tmp_path / "runtime.yaml"
    path.write_text(yaml.safe_dump(runtime))
    if valid:
        assert load_runtime_settings(path).director_apply
    else:
        with pytest.raises(ValueError, match="Phrase routing"):
            load_runtime_settings(path)


def test_supervisor_stop_reaches_obs_after_director_is_gone(monkeypatch):
    async def scenario():
        from stream_director import obs
        from stream_director import __main__ as main

        calls = []

        class Client:
            def __init__(self, *args):
                pass

            async def request(self, method, data):
                calls.append((method, data))

            async def close(self):
                pass

        monkeypatch.setattr(obs, "ObsClient", Client)
        monkeypatch.setattr(main, "obs_url", lambda: "ws://test")
        driver = ProductionDriver(load_runtime_settings(ROOT / "configs/local/stream-runtime.yaml"))
        driver.phrase_stop_hotkeys = ["approved-stop"]
        await driver._stop_phrases()
        assert calls == [("TriggerHotkeyByName", {"hotkeyName": "approved-stop"})]
        driver.phrase_stop_hotkeys = []
        await driver.close()

    asyncio.run(scenario())
