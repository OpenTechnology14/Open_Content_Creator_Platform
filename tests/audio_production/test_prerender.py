"""P-068 slice 4: pre-rendering a script and timing it, with a scripted clock and fake engines.

Local engines take tens of seconds per line, so a real run proves nothing a test can pin down; a fake
clock that the fake engine advances makes the percentile and pass-condition logic exact. The one
real measurement (the incumbent OS voice) lives in the proposal's implementation record.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import wave
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/audio-production"))

from stream_speech import __main__ as worker  # noqa: E402
from stream_speech import prerender as pre  # noqa: E402
from stream_speech.cache import RenderCache  # noqa: E402
from stream_speech.models import SpeechSettings  # noqa: E402
from stream_speech.providers import EngineUnavailable, LocalSynthesizer, RoutedSpeechAdapter  # noqa: E402

LOCAL = {
    "provider": "local",
    "engine": "chatterbox",
    "model_path": "models/tts/chatterbox",
    "speaker_ref": "models/tts/refs/owner-measured.wav",
}


def write_wav(path: Path, frames: int = 24000, rate: int = 48000) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\x01\x00" * frames)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class TimedEngine:
    """Spends scripted seconds on the fake clock, then writes a half-second WAV."""

    def __init__(self, clock: Clock, seconds=(10.0,), unavailable: str | None = None):
        self.clock, self.seconds, self.unavailable = clock, list(seconds), unavailable
        self.calls: list[str] = []

    def check(self, voice):
        if self.unavailable:
            raise EngineUnavailable(self.unavailable)

    async def synthesize(self, text, voice, output):
        self.clock.now += self.seconds[len(self.calls) % len(self.seconds)]
        self.calls.append(text)
        write_wav(output)

    async def stop(self):
        return None


class TimedNative:
    def __init__(self, clock: Clock, seconds: float = 2.0) -> None:
        self.clock, self.seconds = clock, seconds
        self.calls: list[str] = []

    async def synthesize(self, text, voice, output):
        self.clock.now += self.seconds
        self.calls.append(text)
        write_wav(output, 4800, 48000)
        return 0.1

    async def play(self, path):
        return None

    async def stop(self):
        return None


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / "models/tts/chatterbox").mkdir(parents=True)
    reference = tmp_path / "models/tts/refs/owner-measured.wav"
    reference.parent.mkdir(parents=True)
    write_wav(reference, 960)
    return tmp_path


def settings(tmp_path: Path, cache: bool = True) -> SpeechSettings:
    data = {
        "schema_version": 1,
        "on_air_session": "main",
        "output_directory": tmp_path / "out",
        "voices": {"nova-local": None, "nova-opentech": LOCAL},
    }
    if cache:
        data["render_cache_directory"] = tmp_path / "cache"
    return SpeechSettings.model_validate(data)


def lines(*items) -> list[pre.PrerenderLine]:
    return [pre.PrerenderLine(voice_id=voice, text=text) for voice, text in items]


def run_prerender(tmp_path, repo, batch, engines, clock, native=None, cache=True):
    config = settings(tmp_path, cache)
    local = LocalSynthesizer(
        engines, repo, RenderCache(config.render_cache_directory) if cache else None
    )
    adapter = RoutedSpeechAdapter(native or TimedNative(clock), local)
    records: list[dict] = []

    async def emit(record):
        records.append(record)

    summary = asyncio.run(pre.prerender(batch, config, adapter, local, emit, clock))
    return records, summary


# ── percentile and the pass condition ────────────────────────────────────────────────────────


def test_percentile_is_nearest_rank():
    values = [float(n) for n in range(20, 0, -1)]
    assert pre.percentile(values, 50) == 10
    assert pre.percentile(values, 95) == 19
    assert pre.percentile(values, 100) == 20
    assert pre.percentile([7.0], 95) == 7.0


def test_only_renders_are_timed_and_a_cache_hit_costs_nothing(tmp_path, repo):
    clock = Clock()
    engine = TimedEngine(clock, seconds=(10.0, 20.0))
    batch = lines(("nova-opentech", "One."), ("nova-opentech", "One."), ("nova-opentech", "Two."))
    records, summary = run_prerender(tmp_path, repo, batch, {"chatterbox": engine}, clock)

    assert [record["status"] for record in records] == ["rendered", "cached", "rendered"]
    assert [record["render_seconds"] for record in records] == [10.0, 0.0, 20.0]
    assert [record["audio_seconds"] for record in records] == [0.5, 0.5, 0.5]
    voice = summary["by_voice"]["nova-opentech"]
    assert (summary["rendered"], summary["cached"], summary["failed"]) == (2, 1, 0)
    assert voice["render_seconds"] == {"count": 2, "p50": 10.0, "p95": 20.0, "max": 20.0}
    assert voice["real_time_factor"] == 30.0  # 30 s of rendering for 1 s of rendered audio
    assert engine.calls == ["One.", "Two."]


@pytest.mark.parametrize(
    ("times", "samples", "met"),
    [
        ([70.0] * 19, 19, None),  # too few renders for a p95 to mean anything
        ([10.0] * 19 + [200.0], 20, True),  # one outlier does not move the 95th percentile
        ([10.0] * 18 + [70.0, 70.0], 20, False),  # two slow lines do
        ([60.0] * 20, 20, False),  # the limit is "under 60 s"
        ([59.9] * 20, 20, True),
    ],
)
def test_the_sixty_second_pass_condition_needs_twenty_samples(tmp_path, repo, times, samples, met):
    clock = Clock()
    engine = TimedEngine(clock, seconds=times)
    batch = lines(*[("nova-opentech", f"Line {n}.") for n in range(len(times))])
    _, summary = run_prerender(tmp_path, repo, batch, {"chatterbox": engine}, clock)
    limit = summary["by_voice"]["nova-opentech"]["p95_under_limit"]
    assert limit == {"limit_seconds": 60.0, "samples": samples, "met": met}


def test_native_lines_are_timed_but_have_no_pass_condition_and_no_cache(tmp_path, repo):
    clock = Clock()
    native = TimedNative(clock, seconds=3.0)
    batch = lines(("nova-local", "Same."), ("nova-local", "Same."))
    records, summary = run_prerender(tmp_path, repo, batch, {}, clock, native=native)

    assert [record["status"] for record in records] == ["rendered", "rendered"]
    assert native.calls == ["Same.", "Same."]
    voice = summary["by_voice"]["nova-local"]
    assert voice["provider"] == "native" and voice["cached"] == 0
    assert voice["render_seconds"]["p50"] == 3.0
    assert "p95_under_limit" not in voice


def test_a_failed_line_is_reported_and_the_batch_carries_on(tmp_path, repo):
    clock = Clock()
    batch = lines(("nova-opentech", "Local."), ("nova-local", "Native."))
    records, summary = run_prerender(tmp_path, repo, batch, {}, clock)

    assert records[0]["status"] == "failed" and records[0]["reason"] == "local_engine_unavailable"
    assert "render_seconds" not in records[0]
    assert records[1]["status"] == "rendered"
    assert (summary["rendered"], summary["failed"]) == (1, 1)
    assert summary["by_voice"]["nova-opentech"]["failed"] == 1
    assert "render_seconds" not in summary["by_voice"]["nova-opentech"]


def test_records_identify_a_line_without_echoing_its_text(tmp_path, repo):
    clock = Clock()
    text = "Confidential narration about the quarterly numbers."
    records, _ = run_prerender(
        tmp_path, repo, lines(("nova-local", text)), {}, clock, native=TimedNative(clock)
    )
    assert text not in json.dumps(records)
    assert records[0]["characters"] == len(text)
    assert records[0]["text_sha256"] == hashlib.sha256(text.encode()).hexdigest()[:16]
    assert records[0]["index"] == 1 and records[0]["voice_id"] == "nova-local"


def test_each_scratch_wav_is_gone_before_the_next_line_renders(tmp_path, repo, monkeypatch):
    """A 2000-line script must not pile its audio up on disk until the end of the run."""
    made: list[Path] = []
    real = TimedNative.synthesize

    async def spy(self, text, voice, output):
        assert all(not earlier.exists() for earlier in made)
        made.append(output)
        return await real(self, text, voice, output)

    monkeypatch.setattr(TimedNative, "synthesize", spy)
    clock = Clock()
    run_prerender(tmp_path, repo, lines(*[("nova-local", f"Line {n}.") for n in range(4)]), {}, clock)
    assert len(made) == 4 and not made[0].parent.exists()


# ── reading the script ───────────────────────────────────────────────────────────────────────


def write_lines(tmp_path: Path, *raw: str) -> Path:
    path = tmp_path / "lines.jsonl"
    path.write_text("\n".join(raw) + "\n", encoding="utf-8")
    return path


def good(voice="nova-local", text="Hello there."):
    return json.dumps({"voice_id": voice, "text": text})


def test_a_valid_script_is_read_and_blank_lines_are_skipped(tmp_path):
    path = write_lines(tmp_path, good(), "", good("nova-opentech", "Second."))
    batch = pre.read_lines(path, settings(tmp_path))
    assert [(line.voice_id, line.text) for line in batch] == [
        ("nova-local", "Hello there."),
        ("nova-opentech", "Second."),
    ]


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ([good(), "{not json"], "line 2 is invalid"),
        ([good(), json.dumps({"voice_id": "nova-local", "text": "x", "extra": 1})], "line 2 is invalid"),
        ([good(), json.dumps({"voice_id": "nova-local", "text": ""})], "line 2 is invalid"),
        ([good(), json.dumps({"voice_id": "nova-local", "text": "x" * 501})], "line 2 is invalid"),
        ([good(), json.dumps({"voice_id": "nova-local", "text": "   "})], "line 2 has no speakable"),
        ([good(), json.dumps({"voice_id": "nova-local", "text": "a\u0000b"})], "line 2 has no speakable"),
        ([good(), good("elevenlabs")], "line 2: voice 'elevenlabs' is not configured"),
        ([], "empty"),
    ],
)
def test_a_bad_script_is_refused_with_the_line_number(tmp_path, raw, message):
    with pytest.raises(ValueError, match=message):
        pre.read_lines(write_lines(tmp_path, *raw), settings(tmp_path))


def test_error_messages_never_contain_the_line_text(tmp_path):
    secret = "q3 secret numbers"  # short enough to survive pydantic's truncation of echoed input
    too_long = json.dumps({"voice_id": "nova-local", "text": secret + "x" * 500})
    with pytest.raises(ValueError, match="line 1 is invalid") as raised:
        pre.read_lines(write_lines(tmp_path, too_long), settings(tmp_path))
    assert secret not in str(raised.value) and secret not in repr(raised.value.__cause__.errors()[0]["loc"])


def test_limits_on_size_and_line_count(tmp_path, monkeypatch):
    monkeypatch.setattr(pre, "MAX_LINES", 3)
    with pytest.raises(ValueError, match="more than 3 lines"):
        pre.read_lines(write_lines(tmp_path, *[good()] * 4), settings(tmp_path))
    monkeypatch.setattr(pre, "MAX_FILE_BYTES", 10)
    with pytest.raises(ValueError, match="exceeds 4 MiB"):
        pre.read_lines(write_lines(tmp_path, good()), settings(tmp_path))


def test_local_lines_need_a_cache_or_the_render_is_thrown_away(tmp_path):
    path = write_lines(tmp_path, good("nova-opentech"))
    with pytest.raises(ValueError, match="render_cache_directory"):
        pre.read_lines(path, settings(tmp_path, cache=False))
    assert pre.read_lines(write_lines(tmp_path, good()), settings(tmp_path, cache=False))


# ── the command ──────────────────────────────────────────────────────────────────────────────


def config_file(tmp_path: Path, cache: bool = True) -> Path:
    data = {
        "schema_version": 1,
        "on_air_session": "main",
        "output_directory": str(tmp_path / "out"),
        "voices": {"nova-local": None, "nova-opentech": LOCAL},
    }
    if cache:
        data["render_cache_directory"] = str(tmp_path / "cache")
    path = tmp_path / "speech.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def run_command(tmp_path, monkeypatch, capsys, raw, engines=None, native_ok=True, cache=True):
    clock = Clock()

    class Native(TimedNative):
        def __init__(self):
            super().__init__(clock)

        def check(self):
            if not native_ok:
                raise RuntimeError("native speech playback is unavailable on this system")

        @staticmethod
        def dependencies():
            return []

    monkeypatch.setattr(worker, "NativeSpeechAdapter", Native)
    monkeypatch.setattr(worker, "default_engines", lambda: engines or {})
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    (tmp_path / "models/tts/chatterbox").mkdir(parents=True, exist_ok=True)
    reference = tmp_path / "models/tts/refs/owner-measured.wav"
    reference.parent.mkdir(parents=True, exist_ok=True)
    write_wav(reference, 960)
    args = argparse.Namespace(
        config=config_file(tmp_path, cache),
        validate=False,
        backend=False,
        input=None,
        prerender=write_lines(tmp_path, *raw),
    )
    code = asyncio.run(worker.run(args))
    out = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    return code, out


def test_the_command_streams_one_record_per_line_then_a_summary(tmp_path, monkeypatch, capsys):
    engine = TimedEngine(Clock(), seconds=(1.0,))
    code, out = run_command(
        tmp_path, monkeypatch, capsys,
        [good("nova-opentech", "A."), good("nova-local", "B."), good("nova-opentech", "A.")],
        engines={"chatterbox": engine},
    )
    assert code == 0
    assert [record["kind"] for record in out] == ["prerendered"] * 3 + ["prerender_summary"]
    assert [record["status"] for record in out[:3]] == ["rendered", "rendered", "cached"]
    assert out[-1]["lines"] == 3 and out[-1]["failed"] == 0


def test_a_failed_line_makes_the_exit_status_one_after_the_whole_script_ran(
    tmp_path, monkeypatch, capsys
):
    code, out = run_command(
        tmp_path, monkeypatch, capsys, [good("nova-opentech", "A."), good("nova-local", "B.")]
    )
    assert code == 1
    assert [record.get("status") for record in out[:2]] == ["failed", "rendered"]


def test_a_bad_script_stops_before_anything_renders(tmp_path, monkeypatch, capsys):
    engine = TimedEngine(Clock())
    with pytest.raises(ValueError, match="line 2 is invalid"):
        run_command(
            tmp_path, monkeypatch, capsys, [good("nova-opentech", "A."), "{broken"],
            engines={"chatterbox": engine},
        )
    assert engine.calls == [] and capsys.readouterr().out == ""


def test_native_speech_is_required_only_when_a_native_voice_is_used(tmp_path, monkeypatch, capsys):
    engine = TimedEngine(Clock())
    code, out = run_command(
        tmp_path, monkeypatch, capsys, [good("nova-opentech", "A.")],
        engines={"chatterbox": engine}, native_ok=False,
    )
    assert code == 0 and out[-1]["rendered"] == 1
    with pytest.raises(RuntimeError, match="unavailable"):
        run_command(tmp_path, monkeypatch, capsys, [good("nova-local", "B.")], native_ok=False)


def test_main_reports_a_bad_script_as_exit_one_and_says_which_line(tmp_path, monkeypatch):
    bad = write_lines(tmp_path, good(), "{broken")
    monkeypatch.setattr(sys, "argv", ["stream_speech", "--config", str(config_file(tmp_path)),
                                      "--prerender", str(bad)])
    messages: list[str] = []
    handler = worker.logger.add(messages.append, format="{message}")
    try:
        assert worker.main() == 1
    finally:
        worker.logger.remove(handler)
    assert any("line 2 is invalid" in message for message in messages)


def test_live_modes_still_name_only_the_exception_type(tmp_path, monkeypatch):
    config = config_file(tmp_path)
    monkeypatch.setattr(sys, "argv", ["stream_speech", "--config", str(config),
                                      "--input", str(tmp_path / "missing.jsonl")])

    class Native:
        def check(self):
            return None

        @staticmethod
        def dependencies():
            return []

        async def stop(self):
            return None

    monkeypatch.setattr(worker, "NativeSpeechAdapter", Native)
    messages: list[str] = []
    handler = worker.logger.add(messages.append, format="{message}")
    try:
        assert worker.main() == 1
    finally:
        worker.logger.remove(handler)
    assert messages and "missing.jsonl" not in messages[0] and "FileNotFoundError" in messages[0]


def test_readme_example_is_a_valid_script_and_its_flag_exists(tmp_path, monkeypatch, capsys):
    readme = (ROOT / "modules/audio-production/stream_speech/README.md").read_text("utf-8")
    section = readme.split("## Pre-rendering")[1].split("\n## ")[0]
    sample = re.search(r"```json\n(.*?)```", section, re.S).group(1)
    batch = pre.read_lines(write_lines(tmp_path, *sample.strip().splitlines()), settings(tmp_path))
    assert batch
    flag = re.search(r"python3 -m stream_speech (--[a-z-]+)", section).group(1)
    monkeypatch.setattr(sys, "argv", ["stream_speech", "--help"])
    with pytest.raises(SystemExit):
        worker.main()
    assert flag in capsys.readouterr().out
