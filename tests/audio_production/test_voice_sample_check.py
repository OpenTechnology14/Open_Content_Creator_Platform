"""P-068 section 5.4 clone-source recording checker: measured against signals with known answers.

The recordings are synthetic (a voice-like complex tone over a room-tone floor), so every number
has a known truth. They prove the measurements and the grading, not that any threshold suits a real
microphone: the thresholds are starting values until the first real recording exists.
"""

from __future__ import annotations

import array
import cmath
import dataclasses
import importlib.util
import json
import math
import random
import re
import shutil
import struct
import subprocess
import sys
import wave
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_voice_sample", ROOT / "modules/audio-production/tts/check_voice_sample.py"
)
chk = importlib.util.module_from_spec(spec)
sys.modules["check_voice_sample"] = chk
spec.loader.exec_module(chk)

RATE = 48000


# ── synthetic recordings ──────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=None)
def comb(cutoff_hz: float, rms: float, offset: int, seed: int, tilt: float = 40.0) -> tuple:
    """Periodic partials on exact FFT bins, so a band limit is exact by construction."""
    n = chk.SPECTRUM_SIZE
    rng = random.Random(seed)
    bins = [k for k in range(8, int(cutoff_hz / (RATE / n))) if k % 3 == offset]
    phase = {k: rng.uniform(0, 2 * math.pi) for k in bins}
    unit = [
        sum(math.sin(2 * math.pi * k * i / n + phase[k]) / (1 + k / tilt) for k in bins)
        for i in range(n)
    ]
    gain = rms / math.sqrt(sum(v * v for v in unit) / n)
    return tuple(v * gain for v in unit)


def voice(seconds, speech_db=-20.0, noise_db=-70.0, cutoff=23000.0) -> list[float]:
    """One second of speech then half a second of room tone, repeated. A fresh list each call."""
    return list(synth(seconds, speech_db, noise_db, cutoff))


@lru_cache(maxsize=None)
def synth(seconds, speech_db, noise_db, cutoff) -> tuple:
    n = chk.SPECTRUM_SIZE
    speech = comb(cutoff, 10 ** (speech_db / 20), 0, 1)
    room = comb(cutoff, 10 ** (noise_db / 20), 1, 2, 1e9)
    total, out = int(seconds * RATE), []
    while len(out) < total:
        for duration, speaking in ((1.0, True), (0.5, False)):
            base = len(out)
            for i in range(min(int(duration * RATE), total - base)):
                value = room[(base + i) % n]
                out.append(value + speech[(base + i) % n] if speaking else value)
    return tuple(out)


def frames(x, width, channels, tag) -> bytes:
    if tag == 3:
        code = "f" if width == 4 else "d"
        return b"".join(struct.pack("<" + code, v) * channels for v in x)
    top = 1 << (8 * width - 1)
    out = bytearray()
    for v in x:
        value = max(-top, min(top - 1, round(v * top)))
        out += value.to_bytes(width, "little", signed=True) * channels
    return bytes(out)


def write_wav(path: Path, x, *, width=2, channels=1, rate=RATE, tag=1) -> Path:
    if tag == 1:
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(channels)
            audio.setsampwidth(width)
            audio.setframerate(rate)
            audio.writeframes(frames(x, width, channels, tag))
        return path
    return write_raw(path, frames(x, width, channels, tag), tag=tag, bits=width * 8,
                     channels=channels, rate=rate)


def write_raw(path: Path, data: bytes, *, tag=1, bits=16, channels=1, rate=RATE,
              extensible=False, extra=b"", data_size=None, odd_pad=False) -> Path:
    block = channels * bits // 8
    fmt = struct.pack("<HHIIHH", 0xFFFE if extensible else tag, channels, rate,
                      rate * block, block, bits)
    if extensible:
        guid = struct.pack("<H", tag) + bytes.fromhex("000000001000800000aa00389b71")
        fmt += struct.pack("<HHI", 22, bits, 0) + guid
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + extra
    size = len(data) if data_size is None else data_size
    body += b"data" + struct.pack("<I", size) + data + (b"\0" if odd_pad else b"")
    path.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    return path


@pytest.fixture()
def dense(monkeypatch):
    """Short test clips need denser spectrum sampling than a real 3-minute recording does."""
    monkeypatch.setattr(chk, "SPECTRUM_STEP_SECONDS", 0.25)


# ── the FFT ───────────────────────────────────────────────────────────────────────────────────


def test_fft_agrees_with_a_naive_dft():
    n = 64
    rng = random.Random(1)
    frame = array.array("d", [rng.uniform(-1, 1) for _ in range(n)])
    _, _, _, hann = chk.fft_tables(n)
    fast = chk.power_spectrum(frame)
    for k, got in enumerate(fast):
        want = abs(sum(frame[i] * hann[i] * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))) ** 2
        assert got == pytest.approx(want, rel=1e-9, abs=1e-12)


def test_a_pure_tone_peaks_in_its_own_bin():
    n = chk.SPECTRUM_SIZE
    tone = array.array("d", (math.sin(2 * math.pi * 100 * i / n) for i in range(n)))
    spectrum = chk.power_spectrum(tone)
    assert max(range(len(spectrum)), key=spectrum.__getitem__) == 100


# ── measurements ──────────────────────────────────────────────────────────────────────────────


def test_levels_noise_floor_and_snr_recover_the_known_values(tmp_path, dense):
    m = chk.measure(write_wav(tmp_path / "a.wav", voice(12)))
    assert m.speech_rms_dbfs == pytest.approx(-20.0, abs=0.5)
    assert m.noise_floor_dbfs == pytest.approx(-70.0, abs=0.5)
    assert m.snr_db == pytest.approx(50.0, abs=1.0)
    assert (m.clipped_runs, m.digital_silence_runs) == (0, 0)
    assert m.dc_offset_percent == pytest.approx(0.0, abs=0.05)
    assert (m.rate, m.channels, m.seconds) == (RATE, 1, 12.0)
    assert m.bandwidth_checked and m.bandwidth_cliff_khz is None
    assert m.active_seconds == pytest.approx(8.0, abs=1.0)


@pytest.mark.parametrize(
    ("width", "channels", "tag", "label"),
    [
        (2, 2, 1, "16-bit PCM"),
        (3, 1, 1, "24-bit PCM"),
        (3, 2, 1, "24-bit PCM"),
        (4, 1, 1, "32-bit PCM"),
        (4, 2, 3, "32-bit float"),
        (8, 1, 3, "64-bit float"),
    ],
)
def test_every_supported_encoding_measures_the_same_signal(tmp_path, width, channels, tag, label):
    x = voice(4)
    reference = chk.measure(write_wav(tmp_path / "ref.wav", x))
    m = chk.measure(write_wav(tmp_path / "x.wav", x, width=width, channels=channels, tag=tag))
    assert m.encoding == label and m.channels == channels
    assert m.speech_rms_dbfs == pytest.approx(reference.speech_rms_dbfs, abs=0.1)
    assert m.noise_floor_dbfs == pytest.approx(reference.noise_floor_dbfs, abs=0.2)
    assert m.peak_dbfs == pytest.approx(reference.peak_dbfs, abs=0.1)


def test_extensible_wav_headers_are_understood(tmp_path):
    x = voice(4)
    plain = chk.measure(write_wav(tmp_path / "plain.wav", x, width=3))
    data = frames(x, 3, 1, 1)
    m = chk.measure(write_raw(tmp_path / "ext.wav", data, bits=24, extensible=True))
    assert m.encoding == "24-bit PCM"
    assert m.speech_rms_dbfs == pytest.approx(plain.speech_rms_dbfs, abs=0.05)
    floaty = chk.measure(write_raw(tmp_path / "f.wav", frames(x, 4, 1, 3), tag=3, bits=32,
                                   extensible=True))
    assert floaty.encoding == "32-bit float"


def test_clipping_is_a_run_of_full_scale_samples_not_a_single_peak(tmp_path):
    hard = [max(-1.0, min(1.0, v * 8)) for v in voice(4)]
    clipped = chk.measure(write_wav(tmp_path / "hard.wav", hard))
    assert clipped.clipped_runs > 10 and clipped.peak_dbfs > -0.1

    x = voice(4)
    for position in range(1000, 40000, 5000):  # isolated single hot samples
        x[position] = 1.0
    isolated = chk.measure(write_wav(tmp_path / "isolated.wav", x))
    assert isolated.clipped_runs == 0 and isolated.clipped_samples >= 8


def test_a_clipped_stretch_is_counted_once_across_a_block_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(chk, "BLOCK_SECONDS", 1.0)  # blocks end at 48000-sample multiples
    runs = {}
    for name, start, length in (("two", 47999, 2), ("four", 47998, 4), ("six", 47997, 6)):
        x = voice(3)
        x[start : start + length] = [1.0] * length
        runs[name] = chk.measure(write_wav(tmp_path / f"{name}.wav", x)).clipped_runs
    # neither half of "four" reaches three samples; "six" must not be counted once per block
    assert runs == {"two": 0, "four": 1, "six": 1}


def test_negative_full_scale_runs_count_as_clipping_too(tmp_path):
    x = voice(4)
    x[20000:20005] = [-1.0] * 5
    assert chk.measure(write_wav(tmp_path / "neg.wav", x)).clipped_runs == 1


def test_clipping_on_the_second_channel_is_found(tmp_path):
    x = voice(4)
    left = frames(x, 2, 1, 1)
    hot = [1.0 if 20000 <= i < 20010 else v for i, v in enumerate(x)]
    right = frames(hot, 2, 1, 1)
    interleaved = b"".join(left[i : i + 2] + right[i : i + 2] for i in range(0, len(left), 2))
    m = chk.measure(write_raw(tmp_path / "s.wav", interleaved, channels=2))
    assert m.clipped_runs == 1


def test_digital_silence_inside_the_recording_is_counted_but_not_at_the_ends(tmp_path, monkeypatch):
    x = voice(6)
    x[:2400] = [0.0] * 2400  # leading
    x[-2400:] = [0.0] * 2400  # trailing
    ends = chk.measure(write_wav(tmp_path / "ends.wav", x))
    assert ends.digital_silence_runs == 0

    x[100000:104800] = [0.0] * 4800  # 100 ms edit
    x[200000:200960] = [0.0] * 960  # 20 ms: below the detection floor
    x[250000:254800] = [0.0] * 4800
    inside = chk.measure(write_wav(tmp_path / "inside.wav", x))
    assert inside.digital_silence_runs == 2

    monkeypatch.setattr(chk, "BLOCK_SECONDS", 1.0)
    straddle = voice(3)
    straddle[47000:49000] = [0.0] * 2000
    assert chk.measure(write_wav(tmp_path / "straddle.wav", straddle)).digital_silence_runs == 1


@pytest.mark.parametrize("offset", [0.01, -0.01])
def test_dc_offset_is_measured_with_its_sign(tmp_path, offset):
    m = chk.measure(write_wav(tmp_path / "dc.wav", [v + offset for v in voice(4)]))
    assert m.dc_offset_percent == pytest.approx(offset * 100, abs=0.1)


def test_level_drift_between_sections(tmp_path, monkeypatch):
    monkeypatch.setattr(chk, "BLOCK_SECONDS", 4.0)
    drifting = voice(8, speech_db=-20) + voice(8, speech_db=-32)
    steady = voice(16, speech_db=-20)
    assert chk.measure(write_wav(tmp_path / "d.wav", drifting)).level_range_db == pytest.approx(
        12.0, abs=1.0
    )
    assert chk.measure(write_wav(tmp_path / "s.wav", steady)).level_range_db < 1.0
    assert chk.measure(write_wav(tmp_path / "one.wav", voice(3))).level_range_db is None


@pytest.mark.parametrize(("cutoff", "edge"), [(15900, 15.9), (11000, 11.0), (8000, 8.0)])
def test_a_brick_wall_low_pass_is_found_at_its_edge(tmp_path, dense, cutoff, edge):
    m = chk.measure(write_wav(tmp_path / "bl.wav", voice(12, cutoff=cutoff)))
    assert m.bandwidth_cliff_khz == pytest.approx(edge, abs=0.3)


def test_full_band_and_a_recording_without_speech_are_not_flagged(tmp_path, monkeypatch):
    full = chk.measure(write_wav(tmp_path / "f.wav", voice(12)))
    assert full.bandwidth_checked is False and full.bandwidth_cliff_khz is None  # 2.5 s step: 3 loud
    monkeypatch.setattr(chk, "SPECTRUM_STEP_SECONDS", 0.25)
    assert chk.measure(write_wav(tmp_path / "g.wav", voice(12))).bandwidth_cliff_khz is None
    rng = random.Random(4)
    hiss = chk.measure(write_wav(tmp_path / "hiss.wav", [rng.gauss(0, 1e-3) for _ in range(RATE * 3)]))
    assert hiss.speech_rms_dbfs is None and hiss.snr_db is None
    assert hiss.bandwidth_checked is False


# ── headers ───────────────────────────────────────────────────────────────────────────────────


def test_unreadable_files_say_why(tmp_path):
    mp3 = tmp_path / "x.wav"
    mp3.write_bytes(b"ID3\x03\x00 this is an mp3")
    with pytest.raises(chk.SampleError, match="not a RIFF/WAVE"):
        chk.measure(mp3)
    data = frames(voice(1), 2, 1, 1)
    with pytest.raises(chk.SampleError, match="compressed WAV .format tag 85"):
        chk.measure(write_raw(tmp_path / "mp3tag.wav", data, tag=0x55))
    with pytest.raises(chk.SampleError, match="8-bit PCM is not supported"):
        chk.measure(write_raw(tmp_path / "eight.wav", b"\x80" * 9600, bits=8))
    empty = tmp_path / "empty.wav"
    empty.write_bytes(b"RIFF\x04\x00\x00\x00WAVE")
    with pytest.raises(chk.SampleError, match="no audio data"):
        chk.measure(empty)
    with pytest.raises(chk.SampleError, match="shorter than 0.1 s"):
        chk.measure(write_raw(tmp_path / "tiny.wav", frames([0.1] * 100, 2, 1, 1)))
    with pytest.raises(OSError):
        chk.measure(tmp_path / "missing.wav")


def test_odd_real_world_headers_still_measure(tmp_path):
    x = voice(4)
    data = frames(x, 2, 1, 1)
    reference = chk.measure(write_raw(tmp_path / "ref.wav", data))
    for name, kwargs in {
        "list-chunk": {"extra": b"LIST" + struct.pack("<I", 5) + b"INFOx" + b"\0"},
        "streaming-zero-size": {"data_size": 0},
        "size-larger-than-file": {"data_size": len(data) + 5000},
        "odd-padding": {"odd_pad": True},
    }.items():
        m = chk.measure(write_raw(tmp_path / f"{name}.wav", data, **kwargs))
        assert m.seconds == reference.seconds and m.speech_rms_dbfs == reference.speech_rms_dbfs, name


# ── grading ───────────────────────────────────────────────────────────────────────────────────

GOOD = chk.Measurements(
    rate=48000, channels=1, encoding="24-bit PCM", seconds=300.0, peak_dbfs=-6.0, clipped_runs=0,
    clipped_samples=0, speech_rms_dbfs=-20.0, noise_floor_dbfs=-65.0, snr_db=45.0,
    dc_offset_percent=0.0, digital_silence_runs=0, level_range_db=2.0, bandwidth_cliff_khz=None,
    bandwidth_checked=True, active_seconds=200.0,
)


def status(check: str, **changes) -> str:
    findings = chk.grade(dataclasses.replace(GOOD, **changes))
    return next(f.status for f in findings if f.check == check)


def test_a_good_recording_passes_every_check():
    findings = chk.grade(GOOD)
    assert [f.check for f in findings] == [
        "format", "length", "clipping", "level", "noise", "silence", "dc", "drift", "bandwidth",
    ]
    assert {f.status for f in findings} == {"pass"} and chk.verdict(findings) == "pass"


@pytest.mark.parametrize(
    ("check", "changes", "expected"),
    [
        ("format", {"rate": 44100}, "fail"),
        ("format", {"rate": 24000}, "fail"),
        ("format", {"channels": 3}, "fail"),
        ("format", {"channels": 2}, "pass"),
        ("length", {"seconds": 5.9}, "fail"),
        ("length", {"seconds": 6.0}, "warn"),
        ("length", {"seconds": 179.9}, "warn"),
        ("length", {"seconds": 180.0}, "pass"),
        ("length", {"seconds": 600.0}, "pass"),
        ("length", {"seconds": 600.1}, "warn"),
        ("clipping", {"clipped_runs": 1, "clipped_samples": 3}, "fail"),
        ("clipping", {"peak_dbfs": -0.9}, "warn"),
        ("clipping", {"peak_dbfs": -1.0}, "pass"),
        ("level", {"speech_rms_dbfs": None, "snr_db": None}, "fail"),
        ("level", {"speech_rms_dbfs": -45.1}, "fail"),
        ("level", {"speech_rms_dbfs": -45.0}, "warn"),
        ("level", {"speech_rms_dbfs": -35.1}, "warn"),
        ("level", {"speech_rms_dbfs": -35.0}, "pass"),
        ("level", {"speech_rms_dbfs": -9.0}, "pass"),
        ("level", {"speech_rms_dbfs": -8.9}, "warn"),
        ("noise", {"snr_db": 29.9}, "fail"),
        ("noise", {"snr_db": 30.0}, "warn"),
        ("noise", {"snr_db": 39.9}, "warn"),
        ("noise", {"snr_db": 40.0}, "pass"),
        ("noise", {"snr_db": None}, "skip"),
        ("silence", {"digital_silence_runs": 1}, "warn"),
        ("dc", {"dc_offset_percent": 0.5}, "pass"),
        ("dc", {"dc_offset_percent": 0.51}, "warn"),
        ("dc", {"dc_offset_percent": -0.6}, "warn"),
        ("drift", {"level_range_db": None}, "skip"),
        ("drift", {"level_range_db": 6.0}, "pass"),
        ("drift", {"level_range_db": 6.1}, "warn"),
        ("bandwidth", {"bandwidth_checked": False}, "skip"),
        ("bandwidth", {"bandwidth_cliff_khz": 15.9}, "warn"),
    ],
)
def test_every_threshold_boundary(check, changes, expected):
    assert status(check, **changes) == expected


def test_the_verdict_is_the_worst_finding_and_skips_do_not_count():
    assert chk.verdict(chk.grade(dataclasses.replace(GOOD, level_range_db=None))) == "pass"
    assert chk.verdict(chk.grade(dataclasses.replace(GOOD, snr_db=35.0))) == "warn"
    assert chk.verdict(chk.grade(dataclasses.replace(GOOD, snr_db=35.0, rate=44100))) == "fail"


# ── command line ──────────────────────────────────────────────────────────────────────────────


def test_a_clean_recording_is_ready(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(chk, "SPECTRUM_STEP_SECONDS", 0.25)
    monkeypatch.setattr(chk, "PROTOCOL_MIN_SECONDS", 5.0)
    path = write_wav(tmp_path / "a.wav", voice(12))
    assert chk.main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "verdict: READY (0 failed, 0 warnings)" in out and "FAIL" not in out
    assert out.splitlines()[1].split()[:2] == ["PASS", "format"]


def test_warnings_are_ready_unless_strict(tmp_path, capsys):
    path = write_wav(tmp_path / "a.wav", voice(12))  # 12 s: shorter than the protocol's 3 minutes
    assert chk.main([str(path)]) == 0
    assert "WARN  length" in capsys.readouterr().out
    assert chk.main([str(path), "--strict"]) == 1
    assert "NOT READY" in capsys.readouterr().out


def test_a_failing_recording_is_not_ready_and_says_what_to_fix(tmp_path, capsys):
    path = write_wav(tmp_path / "hot.wav", [max(-1.0, min(1.0, v * 8)) for v in voice(12)])
    assert chk.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "FAIL  clipping" in out and "lower the gain" in out and "verdict: NOT READY" in out


def test_json_output_carries_the_measurements_and_findings(tmp_path, capsys):
    path = write_wav(tmp_path / "a.wav", voice(12))
    assert chk.main([str(path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ready"] is True and report["verdict"] == "warn"
    assert report["measurements"]["rate"] == 48000
    assert {f["check"] for f in report["findings"]} >= {"format", "length", "noise"}


def test_unreadable_input_exits_two_with_a_message(tmp_path, capsys):
    bad = tmp_path / "x.wav"
    bad.write_bytes(b"not audio")
    assert chk.main([str(bad)]) == 2
    assert capsys.readouterr().err.startswith("error: not a RIFF/WAVE")
    assert chk.main([str(tmp_path / "missing.wav")]) == 2


def test_readme_command_uses_flags_the_tool_really_has(capsys):
    readme = (ROOT / "modules/audio-production/tts/README.md").read_text(encoding="utf-8")
    block = re.search(r"## Checking a clone-source recording.*?```bash\n(.*?)```", readme, re.S)
    with pytest.raises(SystemExit):
        chk.main(["--help"])
    help_text = capsys.readouterr().out
    flags = set(re.findall(r"--[a-z][a-z-]*", block.group(1)))
    assert flags and all(flag in help_text for flag in flags)


@pytest.mark.skipif(sys.platform != "darwin" or shutil.which("say") is None, reason="needs macOS say")
def test_real_synthesised_speech_is_measured_without_error(tmp_path):
    out = tmp_path / "say.wav"
    subprocess.run(
        ["say", "--file-format=WAVE", "--data-format=LEI16@22050", "-o", str(out),
         "The quick brown fox jumps over the lazy dog. " * 6],
        check=True, timeout=60,
    )
    m = chk.measure(out)
    assert m.rate == 22050 and m.speech_rms_dbfs is not None and m.clipped_runs == 0
    assert status_for(m, "format") == "fail"


def status_for(m, check):
    return next(f.status for f in chk.grade(m) if f.check == check)


@pytest.mark.skipif(
    sys.platform != "darwin" or shutil.which("afconvert") is None or shutil.which("say") is None,
    reason="needs macOS say and afconvert",
)
def test_real_aac_round_trips_are_flagged_at_low_bitrates_only(tmp_path, monkeypatch):
    """A real lossy codec, not a synthetic wall: OS speech plus full-band room noise through AAC.

    Bounds are loose on purpose: the encoder belongs to the operating system.
    """
    monkeypatch.setattr(chk, "SPECTRUM_STEP_SECONDS", 0.5)
    text = "Open the draft, then check the three numbers on the dashboard. " * 14
    speech = tmp_path / "speech.wav"
    subprocess.run(["say", "--file-format=WAVE", "--data-format=LEI16@48000", "-o", str(speech),
                    text], check=True, timeout=120)
    with wave.open(str(speech)) as audio:
        samples = array.array("h")
        samples.frombytes(audio.readframes(audio.getnframes()))
    rng = random.Random(5)
    noise = 10 ** (-58 / 20) * 32768
    noisy = array.array(
        "h", (max(-32768, min(32767, round(v + rng.gauss(0, noise)))) for v in samples)
    )
    clean = write_raw(tmp_path / "clean.wav", noisy.tobytes())

    def through_aac(kbps):
        encoded, decoded = tmp_path / f"{kbps}.m4a", tmp_path / f"{kbps}.wav"
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", str(kbps * 1000),
                        str(clean), str(encoded)], check=True, timeout=120)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@48000", str(encoded),
                        str(decoded)], check=True, timeout=120)
        return chk.measure(decoded)

    assert chk.measure(clean).bandwidth_cliff_khz is None
    low = through_aac(32)
    assert low.bandwidth_cliff_khz is not None and 6.0 < low.bandwidth_cliff_khz < 13.0
    assert status_for(low, "bandwidth") == "warn"
    assert through_aac(192).bandwidth_cliff_khz is None
