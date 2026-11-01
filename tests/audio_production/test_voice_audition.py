"""P-068 section 6.1 blind audition rig: neutral takes, matched levels, a hidden key, one ranking."""

from __future__ import annotations

import array
import importlib.util
import json
import math
import re
import shutil
import struct
import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "audition", ROOT / "modules/audio-production/tts/audition.py"
)
audition = importlib.util.module_from_spec(spec)
sys.modules["audition"] = audition
spec.loader.exec_module(audition)

RATE = 8000


def tone(path: Path, seconds=0.5, amplitude=0.5, rate=RATE, channels=1, width=2) -> Path:
    data = bytearray()
    for index in range(int(seconds * rate)):
        value = int(amplitude * 32767 * math.sin(2 * math.pi * 220 * index / rate))
        for _ in range(channels):
            if width == 2:
                data += struct.pack("<h", value)
            else:
                data += (value * 256).to_bytes(3, "little", signed=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(width)
        audio.setframerate(rate)
        audio.writeframes(bytes(data))
    return path


def samples_of(path: Path) -> array.array:
    with wave.open(str(path), "rb") as audio:
        values = array.array("h")
        values.frombytes(audio.readframes(audio.getnframes()))
    return values


def rms_db(path: Path) -> float:
    values = samples_of(path)
    return 20 * math.log10(math.sqrt(sum(v * v for v in values) / len(values)) / 32768)


def clips(tmp_path: Path, **amplitudes):
    """One clip per label; durations differ so a take's length identifies its voice."""
    result = []
    for number, (label, amplitude) in enumerate(amplitudes.items()):
        path = tone(tmp_path / f"{label}.wav", seconds=0.4 + 0.2 * number, amplitude=amplitude)
        result.append(audition.read_clip(label, path))
    return result


def read_key(directory: Path) -> dict:
    return json.loads((directory / audition.KEY_NAME).read_text(encoding="utf-8"))


# ── build ─────────────────────────────────────────────────────────────────────────────────────


def test_takes_are_neutrally_named_and_the_key_maps_each_back(tmp_path):
    made = clips(tmp_path, clone=0.5, dave=0.5, incumbent=0.5)
    out = tmp_path / "audition"
    key, _ = audition.build(out, made, seed=3)

    assert sorted(path.name for path in out.iterdir()) == [
        audition.KEY_NAME,
        "take-1.wav",
        "take-2.wav",
        "take-3.wav",
    ]
    by_seconds = {round(clip.seconds, 3): clip.label for clip in made}
    for item in key["takes"]:
        with wave.open(str(out / item["file"]), "rb") as audio:
            seconds = round(audio.getnframes() / audio.getframerate(), 3)
        assert by_seconds[seconds] == item["label"]
    assert not any(label in name for label in by_seconds.values() for name in map(str, out.iterdir()))


def test_the_shuffle_follows_the_seed_and_really_shuffles(tmp_path):
    made = clips(tmp_path, a=0.5, b=0.5, c=0.5)

    def order(seed, tag):
        key, _ = audition.build(tmp_path / f"out-{tag}", made, seed)
        return [item["label"] for item in key["takes"]]

    assert order(7, "first") == order(7, "second")
    assert len({tuple(order(seed, f"seed-{seed}")) for seed in range(12)}) >= 3


def test_levels_are_matched_by_attenuating_the_louder_clips_only(tmp_path):
    made = clips(tmp_path, loud=0.8, middle=0.4, quiet=0.1)
    out = tmp_path / "audition"
    key, warnings = audition.build(out, made, seed=1)

    levels = [rms_db(out / item["file"]) for item in key["takes"]]
    assert max(levels) - min(levels) < 0.05
    assert key["level_spread_db"] > 15 and warnings == []
    for item in key["takes"]:
        source = next(clip for clip in made if clip.label == item["label"])
        assert item["gain_db"] <= 0
        assert max(map(abs, samples_of(out / item["file"]))) <= max(map(abs, source.samples))
        if item["label"] == "quiet":
            assert item["gain_db"] == 0
            assert (out / item["file"]).read_bytes() == source.source.read_bytes()


def test_unmatched_build_copies_files_unchanged_and_warns_about_the_level_gap(tmp_path):
    made = clips(tmp_path, loud=0.8, quiet=0.1)
    out = tmp_path / "audition"
    key, warnings = audition.build(out, made, seed=1, match_level=False)

    for item in key["takes"]:
        source = next(clip for clip in made if clip.label == item["label"]).source
        assert (out / item["file"]).read_bytes() == source.read_bytes()
    assert len(warnings) == 1 and "levels differ by" in warnings[0] and "not matched" in warnings[0]
    assert "loud" not in warnings[0].replace("louder", "") and "quiet" not in warnings[0]

    (tmp_path / "even").mkdir()
    even = clips(tmp_path / "even", a=0.5, b=0.5)
    _, quiet = audition.build(tmp_path / "audition-even", even, seed=1, match_level=False)
    assert quiet == []


def test_unattenuated_takes_are_the_source_file_byte_for_byte(tmp_path):
    plain = tone(tmp_path / "plain.wav", amplitude=0.1)
    raw = plain.read_bytes()
    extra = b"LIST" + struct.pack("<I", 4) + b"INFO"
    tagged = tmp_path / "tagged.wav"
    tagged.write_bytes(
        raw[:4] + struct.pack("<I", len(raw) - 8 + len(extra)) + raw[8:36] + extra + raw[36:]
    )
    loud = tone(tmp_path / "loud.wav", amplitude=0.8)
    for match_level in (True, False):
        out = tmp_path / f"audition-{match_level}"
        made = [audition.read_clip("tagged", tagged), audition.read_clip("loud", loud)]
        key, _ = audition.build(out, made, seed=1, match_level=match_level)
        take = next(item for item in key["takes"] if item["label"] == "tagged")
        assert (out / take["file"]).read_bytes() == tagged.read_bytes()


def test_mixed_formats_warn_without_naming_any_voice(tmp_path):
    first = audition.read_clip("secret-one", tone(tmp_path / "a.wav", rate=8000))
    second = audition.read_clip("secret-two", tone(tmp_path / "b.wav", rate=16000))
    _, warnings = audition.build(tmp_path / "audition", [first, second], seed=1)

    assert len(warnings) == 1 and "sample rate" in warnings[0]
    assert "secret" not in warnings[0]


@pytest.mark.parametrize(
    ("scenario", "message"),
    [
        ("single", "at least two"),
        ("duplicate", "unique"),
        ("badlabel", "label 'two words'"),
        ("24bit", "24-bit"),
        ("notwav", "not a readable PCM WAV"),
        ("silent", "silent"),
        ("oversize", "over"),
        ("missing", "cannot read"),
        ("occupied", "not empty"),
    ],
)
def test_bad_input_is_refused_before_any_output_exists(tmp_path, monkeypatch, scenario, message):
    good = tone(tmp_path / "good.wav")
    other = tone(tmp_path / "other.wav")
    out = tmp_path / "audition"
    read = audition.read_clip

    def run():
        if scenario == "single":
            return audition.build(out, [read("a", good)])
        if scenario == "duplicate":
            return audition.build(out, [read("a", good), read("a", other)])
        if scenario == "badlabel":
            return read("two words", good)
        if scenario == "24bit":
            return read("a", tone(tmp_path / "wide.wav", width=3))
        if scenario == "notwav":
            (tmp_path / "x.mp3").write_bytes(b"ID3 not a wav")
            return read("a", tmp_path / "x.mp3")
        if scenario == "silent":
            return read("a", tone(tmp_path / "quiet.wav", amplitude=0))
        if scenario == "oversize":
            monkeypatch.setattr(audition, "MAX_WAV_BYTES", 100)
            return read("a", good)
        if scenario == "missing":
            return read("a", tmp_path / "nope.wav")
        out.mkdir()
        (out / "keep.txt").write_text("mine")
        return audition.build(out, [read("a", good), read("b", other)])

    with pytest.raises(audition.AuditionError, match=message):
        run()
    if scenario != "occupied":
        assert not out.exists()
    else:
        assert [path.name for path in out.iterdir()] == ["keep.txt"]


# ── reveal ────────────────────────────────────────────────────────────────────────────────────


def test_ranking_parser_uses_competition_ranks_for_ties():
    assert audition.parse_ranking(["3", "1=2"], 3) == {3: 1, 1: 2, 2: 2}
    assert audition.parse_ranking(["1", "2=3", "4"], 4) == {1: 1, 2: 2, 3: 2, 4: 4}
    for bad in (
        ["1", "1", "2"],
        ["1", "2", "3", "1"],
        ["1", "4"],
        ["1", "2"],
        ["1", "x", "3"],
        ["1=", "2", "3"],
        [],
    ):
        with pytest.raises(audition.AuditionError):
            audition.parse_ranking(bad, 3)


def build_three(tmp_path, name="audition"):
    made = clips(tmp_path, clone=0.5, dave=0.5, **{"nova-local": 0.5})
    out = tmp_path / name
    key, _ = audition.build(out, made, seed=11)
    return out, {item["label"]: item["take"] for item in key["takes"]}


def test_reveal_unmasks_the_ranking_and_applies_the_pass_rule(tmp_path):
    out, take = build_three(tmp_path)
    result = audition.reveal(
        out, [str(take["clone"]), str(take["dave"]), str(take["nova-local"])], "clone", "nova-local"
    )
    assert [row["label"] for row in result["ranking"]] == ["clone", "dave", "nova-local"]
    assert result["subject_first"] is True and result["subject_below_incumbent"] is False
    assert json.loads((out / audition.RESULT_NAME).read_text()) == result

    below, take = build_three(tmp_path, "second")
    result = audition.reveal(
        below, [str(take["nova-local"]), str(take["dave"]), str(take["clone"])], "clone", "nova-local"
    )
    assert result["subject_first"] is False and result["subject_below_incumbent"] is True

    middle, take = build_three(tmp_path, "middle")
    result = audition.reveal(
        middle, [str(take["dave"]), str(take["clone"]), str(take["nova-local"])], "clone", "nova-local"
    )
    assert result["subject_first"] is False and result["subject_below_incumbent"] is False

    tied, take = build_three(tmp_path, "third")
    result = audition.reveal(
        tied, [f"{take['dave']}={take['clone']}", str(take["nova-local"])], "clone", "nova-local"
    )
    assert result["subject_first"] is True and result["subject_below_incumbent"] is False


def test_a_ranking_is_recorded_once(tmp_path):
    out, take = build_three(tmp_path)
    order = [str(take[label]) for label in ("clone", "dave", "nova-local")]
    audition.reveal(out, order, None, "nova-local")
    with pytest.raises(audition.AuditionError, match="recorded once"):
        audition.reveal(out, order, None, "nova-local")


def test_a_failed_reveal_does_not_use_up_the_recording(tmp_path):
    out, take = build_three(tmp_path)
    order = [str(take[label]) for label in ("clone", "dave", "nova-local")]
    with pytest.raises(audition.AuditionError):
        audition.reveal(out, order[:2], "clone", "nova-local")
    with pytest.raises(audition.AuditionError, match="not a candidate"):
        audition.reveal(out, order, "elevenlabs", "nova-local")
    assert not (out / audition.RESULT_NAME).exists()
    assert audition.reveal(out, order, "clone", "nova-local")["subject_first"] is True


def test_reveal_needs_a_readable_key(tmp_path):
    with pytest.raises(audition.AuditionError, match="run build first"):
        audition.reveal(tmp_path, ["1", "2"], None, "nova-local")
    (tmp_path / audition.KEY_NAME).write_text('{"takes": [{"nope": 1}]}')
    with pytest.raises(audition.AuditionError, match="run build first"):
        audition.reveal(tmp_path, ["1", "2"], None, "nova-local")


def test_readme_commands_use_flags_the_tool_really_has(capsys):
    readme = (ROOT / "modules/audio-production/tts/README.md").read_text(encoding="utf-8")
    block = re.search(r"## Blind voice audition.*?```bash\n(.*?)```", readme, re.S).group(1)
    build_part, reveal_part = block.split("audition.py reveal")
    for command, part in (("build", build_part), ("reveal", reveal_part)):
        with pytest.raises(SystemExit):
            audition.main([command, "--help"])
        help_text = capsys.readouterr().out
        flags = set(re.findall(r"--[a-z][a-z-]*", part))
        assert flags and all(flag in help_text for flag in flags), (command, flags)


# ── command line ──────────────────────────────────────────────────────────────────────────────


def test_build_prints_take_paths_and_never_a_label(tmp_path, capsys):
    paths = [
        f"zz-{name}={tone(tmp_path / f'{name}.wav', amplitude=amp)}"
        for name, amp in (("clone", 0.6), ("dave", 0.2))
    ]
    code = audition.main(
        ["build", "--out", str(tmp_path / "a"), "--seed", "5"]
        + [arg for path in paths for arg in ("--candidate", path)]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "take-1.wav" in captured.out and "take-2.wav" in captured.out
    assert "zz-" not in captured.out + captured.err


def test_build_errors_exit_one_with_a_message_and_write_nothing(tmp_path, capsys):
    code = audition.main(["build", "--out", str(tmp_path / "a"), "--candidate", "only=missing.wav"])
    assert code == 1
    assert capsys.readouterr().err.startswith("error: ")
    assert not (tmp_path / "a").exists()


def test_native_voices_are_rendered_from_the_script_file(tmp_path, capsys):
    calls = []

    def render(text, output, voice):
        calls.append((text, voice))
        tone(output, seconds=0.3 + 0.1 * len(calls))
        return 0.3

    script = tmp_path / "script.txt"
    script.write_text("  Read this paragraph.  \n", encoding="utf-8")
    code = audition.main(
        ["build", "--out", str(tmp_path / "a"), "--text-file", str(script),
         "--native", "nova-local", "--native", "second=Albert",
         "--candidate", f"clone={tone(tmp_path / 'clone.wav')}", "--seed", "2"],
        render=render,
    )
    assert code == 0
    assert calls == [("Read this paragraph.", None), ("Read this paragraph.", "Albert")]
    assert sorted(item["label"] for item in read_key(tmp_path / "a")["takes"]) == [
        "clone", "nova-local", "second",
    ]


@pytest.mark.parametrize(
    ("text", "extra", "message"),
    [
        ("Hello", ["--native", "x"], "--text-file"),
        ("a" * 501, ["--native", "x"], "at most 500 characters"),
        ("   ", ["--native", "x"], "invalid speech text"),
    ],
)
def test_native_render_problems_are_operator_errors(tmp_path, capsys, text, extra, message):
    def render(text, output, voice):
        if not text.strip():
            raise ValueError("invalid speech text")
        tone(output)

    script = tmp_path / "script.txt"
    script.write_text(text, encoding="utf-8")
    args = ["build", "--out", str(tmp_path / "a"), "--candidate", f"c={tone(tmp_path / 'c.wav')}"]
    if message != "--text-file":
        args += ["--text-file", str(script)]
    code = audition.main(args + extra, render=render)
    assert code == 1
    assert message in capsys.readouterr().err


def test_a_renderer_that_cannot_run_is_reported_not_raised(tmp_path, capsys):
    def render(text, output, voice):
        raise RuntimeError("speech export needs macOS say or Windows PowerShell")

    script = tmp_path / "script.txt"
    script.write_text("Hello", encoding="utf-8")
    code = audition.main(
        ["build", "--out", str(tmp_path / "a"), "--text-file", str(script), "--native", "x",
         "--candidate", f"c={tone(tmp_path / 'c.wav')}"],
        render=render,
    )
    assert code == 1 and "speech export needs" in capsys.readouterr().err


def test_reveal_command_prints_the_ranking_and_the_abandon_rule(tmp_path, capsys):
    out, take = build_three(tmp_path)
    capsys.readouterr()
    code = audition.main(
        ["reveal", str(out), "--rank", str(take["nova-local"]), str(take["dave"]),
         str(take["clone"]), "--subject", "clone"]
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert printed.splitlines()[0] == f"1. take-{take['nova-local']}  nova-local"
    assert "clone ranked not first" in printed and "section 6.1" in printed


@pytest.mark.skipif(
    sys.platform != "darwin" or shutil.which("say") is None, reason="needs macOS say"
)
def test_real_operating_system_voices_end_to_end(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("The quick brown fox jumps over the lazy dog.", encoding="utf-8")
    code = audition.main(
        ["build", "--out", str(tmp_path / "a"), "--text-file", str(script),
         "--native", "nova-local", "--native", "second=Albert", "--seed", "4"]
    )
    assert code == 0
    key = read_key(tmp_path / "a")
    assert sorted(item["label"] for item in key["takes"]) == ["nova-local", "second"]
    levels = [rms_db(tmp_path / "a" / item["file"]) for item in key["takes"]]
    assert abs(levels[0] - levels[1]) < 0.1
