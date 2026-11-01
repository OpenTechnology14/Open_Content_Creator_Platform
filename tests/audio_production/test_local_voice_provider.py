"""P-068 slice 1: the local-voice provider seam, the render cache and unchanged playback events.

No real engine exists yet, so a fake engine that writes a real WAV stands in for one. These tests
prove the seam, not any engine: they say nothing about quality, latency or a cloned voice.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import re
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/audio-production"))

from stream_speech import __main__ as worker  # noqa: E402
from stream_speech.cache import RenderCache, cache_key  # noqa: E402
from stream_speech.models import LocalVoice, SpeechEvent, SpeechSettings, load_settings  # noqa: E402
from stream_speech.providers import (  # noqa: E402
    EngineUnavailable,
    LocalSpeechError,
    LocalSynthesizer,
    RoutedSpeechAdapter,
)
from stream_speech.runtime import SpeechRuntime  # noqa: E402

LOCAL = {
    "provider": "local",
    "engine": "chatterbox",
    "model_path": "models/tts/chatterbox",
    "speaker_ref": "models/tts/refs/owner-measured.wav",
}
VOICE = LocalVoice.model_validate(LOCAL)


def write_wav(path: Path, frames: int = 4800, rate: int = 48000) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\x01\x00" * frames)


class FakeEngine:
    def __init__(self, frames: int = 4800, rate: int = 48000, error=None, hold: bool = False):
        self.frames, self.rate, self.error, self.hold = frames, rate, error, hold
        self.unavailable = None
        self.calls: list[str] = []
        self.stopped = 0
        self.started = asyncio.Event() if hold else None

    def check(self, voice):
        if self.unavailable:
            raise EngineUnavailable(self.unavailable)

    async def synthesize(self, text, voice, output):
        self.calls.append(text)
        if self.error is not None:
            raise self.error
        write_wav(output, self.frames, self.rate)
        if self.hold:
            self.started.set()
            await asyncio.Event().wait()

    async def stop(self):
        self.stopped += 1


class FakeNative:
    """The native adapter's contract: record calls, write a WAV, play until released."""

    def __init__(self, hold: bool = False) -> None:
        self.calls: list[tuple] = []
        self.hold = hold
        self.release = asyncio.Event()

    async def synthesize(self, text, voice, output):
        self.calls.append(("synthesize", text, voice))
        write_wav(output, 2205, 22050)
        return 0.1

    async def play(self, path):
        self.calls.append(("play", path.name))
        if self.hold:
            await self.release.wait()

    async def stop(self):
        self.calls.append(("stop",))
        self.release.set()


@pytest.fixture()
def repo(tmp_path):
    """A stand-in repository root holding the model directory and reference recording."""
    (tmp_path / "models/tts/chatterbox").mkdir(parents=True)
    reference = tmp_path / "models/tts/refs/owner-measured.wav"
    reference.parent.mkdir(parents=True)
    write_wav(reference, 960)
    return tmp_path


def settings(tmp_path: Path, **updates) -> SpeechSettings:
    data = {
        "schema_version": 1,
        "on_air_session": "main",
        "output_directory": tmp_path / "out",
        "voices": {"nova-local": None, "nova-opentech": LOCAL},
    }
    data.update(updates)
    return SpeechSettings.model_validate(data)


def reply(number: int, voice_id: str, text: str = "Hello from Nova") -> SpeechEvent:
    return SpeechEvent.model_validate(
        {
            "schema_version": 1,
            "kind": "reply",
            "event_id": f"event-{number}",
            "utterance_id": f"utterance-{number}",
            "session_id": "main",
            "generation": 0,
            "created_at": datetime.now(timezone.utc),
            "text": text,
            "voice_id": voice_id,
            "avatar_id": "nova-vrm",
        }
    )


# ── schema ────────────────────────────────────────────────────────────────────────────────────


def test_shipped_config_and_operating_system_voices_are_unchanged(tmp_path):
    loaded = load_settings(ROOT / "configs/local/stream-speech.yaml")
    assert loaded.voices == {"nova-local": None}
    assert loaded.render_cache_directory is None
    assert settings(tmp_path, voices={"a": None, "b": "Samantha"}).voices["b"] == "Samantha"


def test_local_voice_takes_the_shape_the_proposal_specifies(tmp_path):
    voice = settings(tmp_path).voices["nova-opentech"]
    assert isinstance(voice, LocalVoice)
    assert (voice.engine, voice.sample_rate, voice.revision) == ("chatterbox", 48000, "")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"speaker_ref": "/etc/passwd"}, "relative path"),
        ({"speaker_ref": "C:/voices/me.wav"}, "relative path"),
        ({"speaker_ref": "models\\tts\\me.wav"}, "forward slashes"),
        ({"model_path": "../outside"}, "'..'"),
        ({"model_path": "models/../../outside"}, "'..'"),
        ({"model_path": ""}, "relative path"),
        ({"speaker_ref": None}, "set speaker_ref"),
        ({"engine": "kokoro"}, "pre-built voices only"),
        ({"engine": "elevenlabs"}, "engine"),
        ({"sample_rate": 100}, "sample_rate"),
        ({"revision": "two words"}, "revision"),
        ({"invented": True}, "invented"),
    ],
)
def test_local_voice_rejects_unsafe_or_inconsistent_values(changes, message):
    with pytest.raises(ValidationError, match=re.escape(message)):
        LocalVoice.model_validate({**LOCAL, **changes})


def test_kokoro_needs_no_reference_recording():
    voice = LocalVoice.model_validate(
        {"provider": "local", "engine": "kokoro", "model_path": "models/tts/kokoro"}
    )
    assert voice.speaker_ref is None


def test_readme_local_voice_example_is_valid_config(tmp_path):
    readme = (ROOT / "modules/audio-production/stream_speech/README.md").read_text("utf-8")
    block = re.search(r"## Local voices.*?```yaml\n(.*?)```", readme, re.S).group(1)
    example = yaml.safe_load(block)
    loaded = settings(tmp_path, **example)
    assert any(isinstance(voice, LocalVoice) for voice in loaded.voices.values())
    assert loaded.render_cache_directory is not None


# ── cache ─────────────────────────────────────────────────────────────────────────────────────


def test_cache_key_covers_text_voice_and_reference_content():
    base = cache_key("Hello", VOICE, "ref-digest")
    assert re.fullmatch(r"[0-9a-f]{64}", base)
    assert cache_key("Hello", VOICE, "ref-digest") == base
    assert cache_key("Hello.", VOICE, "ref-digest") != base
    assert cache_key("Hello", VOICE, "other-digest") != base
    for field, value in {
        "engine": "xtts-v2",
        "model_path": "models/tts/other",
        "speaker_ref": "models/tts/refs/other.wav",
        "sample_rate": 24000,
        "revision": "2026-10",
    }.items():
        changed = LocalVoice.model_validate({**LOCAL, field: value})
        assert cache_key("Hello", changed, "ref-digest") != base, field
    reordered = LocalVoice.model_validate(dict(reversed(list(LOCAL.items()))))
    assert cache_key("Hello", reordered, "ref-digest") == base


def test_cache_round_trip_and_damaged_entries_are_misses(tmp_path):
    cache = RenderCache(tmp_path / "cache")
    source = tmp_path / "source.wav"
    write_wav(source, 24000)
    assert cache.fetch("a" * 64, tmp_path / "unused.wav") is None

    cache.store("k1", source)
    served = tmp_path / "served.wav"
    assert cache.fetch("k1", served) == 0.5
    assert served.read_bytes() == source.read_bytes()

    wav, meta = cache.directory / "k1.wav", cache.directory / "k1.json"
    wav.write_bytes(wav.read_bytes()[:-100])
    assert cache.fetch("k1", tmp_path / "again.wav") is None
    cache.store("k1", source)
    meta.write_text("{not json", encoding="utf-8")
    assert cache.fetch("k1", tmp_path / "again.wav") is None
    meta.unlink()
    assert cache.fetch("k1", tmp_path / "again.wav") is None
    cache.store("k1", source)
    assert cache.fetch("k1", tmp_path / "healed.wav") == 0.5


def test_cache_store_publishes_only_complete_entries(tmp_path):
    cache = RenderCache(tmp_path / "cache")
    source = tmp_path / "source.wav"
    write_wav(source)
    cache.store("k1", source)
    assert sorted(path.name for path in cache.directory.iterdir()) == ["k1.json", "k1.wav"]
    assert json.loads((cache.directory / "k1.json").read_text())["bytes"] == source.stat().st_size

    with pytest.raises(OSError):
        cache.store("k2", tmp_path / "missing.wav")
    assert sorted(path.name for path in cache.directory.iterdir()) == ["k1.json", "k1.wav"]


# ── synthesizer ───────────────────────────────────────────────────────────────────────────────


def test_readiness_names_the_first_thing_that_is_missing(tmp_path, repo):
    nothing = LocalSynthesizer({}, repo)
    assert nothing.readiness(VOICE) == (False, "no adapter for engine 'chatterbox' in this build")

    engine = FakeEngine()
    bare = LocalSynthesizer({"chatterbox": engine}, tmp_path / "empty")
    assert bare.readiness(VOICE) == (False, "model_path not found: models/tts/chatterbox")

    (tmp_path / "half/models/tts/chatterbox").mkdir(parents=True)
    half = LocalSynthesizer({"chatterbox": engine}, tmp_path / "half")
    assert half.readiness(VOICE) == (
        False,
        "speaker_ref not found: models/tts/refs/owner-measured.wav",
    )

    ready = LocalSynthesizer({"chatterbox": engine}, repo)
    assert ready.readiness(VOICE) == (True, "ready")
    engine.unavailable = "chatterbox is not installed"
    assert ready.readiness(VOICE) == (False, "chatterbox is not installed")


def test_unavailable_engine_raises_with_a_specific_failure_reason(tmp_path, repo):
    synth = LocalSynthesizer({}, repo)
    with pytest.raises(EngineUnavailable) as raised:
        asyncio.run(synth.synthesize("Hello", VOICE, tmp_path / "out.wav"))
    assert raised.value.failure_reason == "local_engine_unavailable"


def test_a_line_is_rendered_once_then_served_from_the_cache(tmp_path, repo):
    engine = FakeEngine()
    synth = LocalSynthesizer({"chatterbox": engine}, repo, RenderCache(tmp_path / "cache"))

    async def scenario():
        first = await synth.synthesize("Hello", VOICE, tmp_path / "one.wav")
        second = await synth.synthesize("Hello", VOICE, tmp_path / "two.wav")
        assert (first, second) == (0.1, 0.1)
        assert engine.calls == ["Hello"]
        assert (tmp_path / "one.wav").read_bytes() == (tmp_path / "two.wav").read_bytes()

        await synth.synthesize("Hello again", VOICE, tmp_path / "three.wav")
        revised = LocalVoice.model_validate({**LOCAL, "revision": "new-weights"})
        await synth.synthesize("Hello", revised, tmp_path / "four.wav")
        assert engine.calls == ["Hello", "Hello again", "Hello"]

        write_wav(repo / LOCAL["speaker_ref"], 1920)
        await synth.synthesize("Hello", VOICE, tmp_path / "five.wav")
        assert engine.calls == ["Hello", "Hello again", "Hello", "Hello"]

    asyncio.run(scenario())


def test_without_a_cache_every_line_is_rendered(tmp_path, repo):
    engine = FakeEngine()
    synth = LocalSynthesizer({"chatterbox": engine}, repo)

    async def scenario():
        await synth.synthesize("Hello", VOICE, tmp_path / "one.wav")
        await synth.synthesize("Hello", VOICE, tmp_path / "two.wav")

    asyncio.run(scenario())
    assert engine.calls == ["Hello", "Hello"]


@pytest.mark.parametrize(
    ("engine", "message"),
    [
        (FakeEngine(error=RuntimeError("boom")), "chatterbox failed (RuntimeError)"),
        (FakeEngine(frames=0), "empty audio"),
        (FakeEngine(rate=24000), "24000 Hz, voice expects 48000 Hz"),
    ],
)
def test_engine_failures_become_local_errors_and_leave_no_audio(tmp_path, repo, engine, message):
    synth = LocalSynthesizer({"chatterbox": engine}, repo, RenderCache(tmp_path / "cache"))
    output = tmp_path / "out.wav"
    with pytest.raises(LocalSpeechError, match=re.escape(message)) as raised:
        asyncio.run(synth.synthesize("Hello", VOICE, output))
    assert raised.value.failure_reason == "local_speech_failure"
    assert not output.exists()
    assert not (tmp_path / "cache").exists()


def test_an_engine_that_writes_garbage_is_reported_as_unreadable(tmp_path, repo):
    class Garbage(FakeEngine):
        async def synthesize(self, text, voice, output):
            output.write_bytes(b"not a wav")

    synth = LocalSynthesizer({"chatterbox": Garbage()}, repo)
    with pytest.raises(LocalSpeechError, match="unreadable"):
        asyncio.run(synth.synthesize("Hello", VOICE, tmp_path / "out.wav"))


def test_text_and_output_are_checked_like_the_native_adapter(tmp_path, repo):
    synth = LocalSynthesizer({"chatterbox": FakeEngine()}, repo)
    taken = tmp_path / "taken.wav"
    taken.write_bytes(b"x")

    async def attempt(text, output):
        return await synth.synthesize(text, VOICE, output)

    for text in ("", "   ", "x" * 501, "bad\0text"):
        with pytest.raises(ValueError, match="invalid speech text"):
            asyncio.run(attempt(text, tmp_path / "fresh.wav"))
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(attempt("Hello", taken))


def test_cancellation_stops_the_engine_and_removes_partial_audio(tmp_path, repo):
    engine = FakeEngine(hold=True)
    synth = LocalSynthesizer({"chatterbox": engine}, repo)
    output = tmp_path / "out.wav"

    async def scenario():
        task = asyncio.create_task(synth.synthesize("Hello", VOICE, output))
        await engine.started.wait()
        assert output.exists() and synth.active is engine
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert engine.stopped == 1
    assert not output.exists()
    assert synth.active is None


def test_a_cache_write_failure_does_not_fail_the_line(tmp_path, repo, monkeypatch):
    def refuse(self, key, source):
        raise OSError("disk full")

    monkeypatch.setattr(RenderCache, "store", refuse)
    synth = LocalSynthesizer({"chatterbox": FakeEngine()}, repo, RenderCache(tmp_path / "cache"))
    assert asyncio.run(synth.synthesize("Hello", VOICE, tmp_path / "out.wav")) == 0.1


# ── router and runtime events ─────────────────────────────────────────────────────────────────


def test_router_leaves_native_voices_exactly_as_they_were(tmp_path, repo):
    native = FakeNative()
    engine = FakeEngine()
    router = RoutedSpeechAdapter(native, LocalSynthesizer({"chatterbox": engine}, repo))

    async def scenario():
        await router.synthesize("Hi", None, tmp_path / "a.wav")
        await router.synthesize("Hi", "Samantha", tmp_path / "b.wav")
        await router.play(tmp_path / "b.wav")

    asyncio.run(scenario())
    assert native.calls == [
        ("synthesize", "Hi", None),
        ("synthesize", "Hi", "Samantha"),
        ("play", "b.wav"),
    ]
    assert engine.calls == []


def test_router_still_stops_the_native_player_when_the_local_stop_fails(repo):
    class Broken:
        active = None

        async def stop(self):
            raise RuntimeError("engine hung")

    native = FakeNative()
    router = RoutedSpeechAdapter(native, Broken())
    with pytest.raises(RuntimeError, match="engine hung"):
        asyncio.run(router.stop())
    assert native.calls == [("stop",)]


def run_replies(tmp_path, repo, replies, engines, native=None, cache=True, **setting_updates):
    """Drive the real runtime through the router; return the events it emitted."""
    events: list[dict] = []

    async def emit(value):
        events.append(value)

    native = native or FakeNative()
    cache_dir = RenderCache(tmp_path / "cache") if cache else None
    router = RoutedSpeechAdapter(native, LocalSynthesizer(engines, repo, cache_dir))

    async def scenario():
        runtime = SpeechRuntime(settings(tmp_path, **setting_updates), router, emit)
        await runtime.start()
        for event in replies:
            assert await runtime.submit(event)
            await runtime.drain()
        await runtime.close()

    asyncio.run(scenario())
    return events, native


def test_a_local_voice_emits_the_same_events_as_a_native_voice(tmp_path, repo):
    local_events, native = run_replies(
        tmp_path, repo, [reply(1, "nova-opentech")], {"chatterbox": FakeEngine()}
    )
    native_events, _ = run_replies(tmp_path, repo, [reply(1, "nova-local")], {})

    assert [event["kind"] for event in local_events] == ["started", "finished"]
    assert [event["kind"] for event in native_events] == ["started", "finished"]
    assert [set(event) for event in local_events] == [set(event) for event in native_events]
    assert local_events[0]["duration_seconds"] == 0.1
    assert ("play", "utterance-1.wav") in native.calls
    assert list((tmp_path / "out").iterdir()) == []


def test_pre_rendered_lines_play_from_the_cache_with_the_same_events(tmp_path, repo):
    engine = FakeEngine()
    first, _ = run_replies(tmp_path, repo, [reply(1, "nova-opentech")], {"chatterbox": engine})
    second, _ = run_replies(tmp_path, repo, [reply(2, "nova-opentech")], {"chatterbox": engine})
    assert engine.calls == ["Hello from Nova"]
    assert [event["kind"] for event in second] == [event["kind"] for event in first]
    assert second[0]["duration_seconds"] == first[0]["duration_seconds"]


def test_a_render_that_outlives_the_event_still_fills_the_cache(tmp_path, repo):
    class Slow(FakeEngine):
        async def synthesize(self, text, voice, output):
            await asyncio.sleep(1.1)
            await super().synthesize(text, voice, output)

    engine = Slow()
    engines = {"chatterbox": engine}
    first, _ = run_replies(
        tmp_path, repo, [reply(1, "nova-opentech")], engines, event_ttl_seconds=1
    )
    second, _ = run_replies(
        tmp_path, repo, [reply(2, "nova-opentech")], engines, event_ttl_seconds=1
    )
    assert [(event["kind"], event.get("reason")) for event in first] == [
        ("canceled", "stale_before_playback")
    ]
    assert [event["kind"] for event in second] == ["started", "finished"]
    assert engine.calls == ["Hello from Nova"]


def test_an_unavailable_engine_fails_loudly_and_the_worker_carries_on(tmp_path, repo):
    events, native = run_replies(
        tmp_path, repo, [reply(1, "nova-opentech"), reply(2, "nova-local")], {}
    )
    assert [(event["kind"], event.get("reason")) for event in events] == [
        ("failed", "local_engine_unavailable"),
        ("started", None),
        ("finished", None),
    ]
    assert [call[0] for call in native.calls].count("play") == 1


def test_pausing_during_local_playback_cancels_it_without_a_finish_event(tmp_path, repo):
    events: list[dict] = []

    async def emit(value):
        events.append(value)

    native = FakeNative(hold=True)
    router = RoutedSpeechAdapter(
        native, LocalSynthesizer({"chatterbox": FakeEngine()}, repo, RenderCache(tmp_path / "c"))
    )

    async def scenario():
        runtime = SpeechRuntime(settings(tmp_path), router, emit)
        await runtime.start()
        assert await runtime.submit(reply(1, "nova-opentech"))
        while not any(event["kind"] == "started" for event in events):
            await asyncio.sleep(0)
        pause = SpeechEvent.model_validate(
            {
                "schema_version": 1,
                "kind": "control",
                "event_id": "control-1",
                "session_id": "main",
                "generation": 1,
                "created_at": datetime.now(timezone.utc),
                "action": "pause",
                "paused": True,
            }
        )
        await runtime.submit(pause)
        await runtime.close()

    asyncio.run(scenario())
    kinds = [event["kind"] for event in events]
    assert "started" in kinds and "controlled" in kinds and "finished" not in kinds


# ── worker CLI and the Stream Extend bundle ───────────────────────────────────────────────────


def test_validate_reports_each_voice_provider_without_failing_for_unready_local_voices(
    tmp_path, monkeypatch, capsys
):
    class Native:
        def check(self):
            return None

        @staticmethod
        def dependencies():
            return ["say", "afplay"]

    monkeypatch.setattr(worker, "NativeSpeechAdapter", Native)
    config = tmp_path / "speech.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "on_air_session": "main",
                "output_directory": str(tmp_path / "out"),
                "render_cache_directory": str(tmp_path / "cache"),
                "voices": {"nova-local": None, "nova-opentech": LOCAL},
            }
        ),
        encoding="utf-8",
    )

    asyncio.run(
        worker.run(argparse.Namespace(config=config, validate=True, backend=False, input=None))
    )

    report = json.loads(capsys.readouterr().out)
    # The Autopilot preflight requires exactly this; an unready local voice must not break it.
    assert report["valid"] is True
    assert report["voices"] == ["nova-local", "nova-opentech"]
    assert report["native_commands"] == ["say", "afplay"]
    assert report["voice_providers"]["nova-local"] == {
        "provider": "native",
        "ready": True,
        "detail": "operating system",
    }
    local = report["voice_providers"]["nova-opentech"]
    assert (local["provider"], local["engine"], local["ready"]) == ("local", "chatterbox", False)
    assert "no adapter" in local["detail"]


def test_embedded_voice_studio_files_import_only_embedded_siblings():
    """Stream Extend writes a fixed list of stream_speech files into its runtime directory.

    An embedded file that imports a sibling missing from that list works in the repository and
    breaks inside the app, and the Rust file-count test cannot see it.
    """
    rust = (ROOT / "apps/stream-extend/src-tauri/src/voice_studio.rs").read_text("utf-8")
    pattern = r'include_str!\("(?:\.\./)+modules/audio-production/stream_speech/(\w+)\.py"\)'
    embedded = set(re.findall(pattern, rust))
    assert {"__init__", "models", "runtime", "native", "render"} <= embedded
    for name in embedded:
        source = (ROOT / f"modules/audio-production/stream_speech/{name}.py").read_text("utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                needed = {node.module} if node.module else {alias.name for alias in node.names}
                assert needed <= embedded, f"{name}.py imports {needed - embedded}"
    assert not embedded & {"providers", "cache", "prerender", "__main__"}
