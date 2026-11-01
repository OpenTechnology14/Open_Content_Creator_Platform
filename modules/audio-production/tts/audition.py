"""Blind voice audition: one script in several voices, unlabeled, level-matched, in random order.

P-068 section 6.1 and P-067 section 7.5 decide a voice by ear, and ears are biased by order,
loudness and labels. `build` removes all three: it copies each candidate to a neutral take-N.wav in
a shuffled order, attenuates the louder ones to the quietest one's level, and writes the answer
key. `reveal` takes your ranking, unmasks it and applies the section 6.1 pass rule. Standard
library only; candidates must be 16-bit PCM WAV.

    python3 modules/audio-production/tts/audition.py build --out audition --text-file script.txt \\
        --native nova-local --candidate local-clone=clone.wav --candidate dave=dave.wav
    python3 modules/audio-production/tts/audition.py reveal audition --rank 2 3 1 \\
        --subject local-clone

`--native LABEL[=VOICE]` renders `script.txt` now with the installed operating-system voice (the
incumbent, which the proposal says must be in the test). Anything else is a WAV you rendered
elsewhere; convert an MP3 or float WAV first: ffmpeg -i in.mp3 -c:a pcm_s16le out.wav
"""

from __future__ import annotations

import argparse
import array
import importlib.util
import json
import math
import random
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Callable

LABEL = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
MAX_WAV_BYTES = 100 * 1024 * 1024
MAX_NATIVE_TEXT = 500
LEVEL_TOLERANCE_DB = 1.0
FULL_SCALE = 32768
KEY_NAME = "key.reveal-after-ranking.json"
RESULT_NAME = "result.json"

Renderer = Callable[[str, Path, "str | None"], float]


class AuditionError(ValueError):
    """Bad input, worded so the operator can act on it."""


@dataclass(frozen=True)
class Clip:
    label: str
    source: Path
    channels: int
    sample_rate: int
    samples: array.array

    @property
    def seconds(self) -> float:
        return len(self.samples) / self.channels / self.sample_rate

    @cached_property
    def rms(self) -> float:
        return math.sqrt(sum(value * value for value in self.samples) / len(self.samples))

    @cached_property
    def rms_dbfs(self) -> float:
        return 20 * math.log10(self.rms / FULL_SCALE)

    @cached_property
    def peak_dbfs(self) -> float:
        peak = max(max(self.samples), -min(self.samples), 1)
        return 20 * math.log10(peak / FULL_SCALE)


def read_clip(label: str, path: Path) -> Clip:
    if not LABEL.match(label):
        raise AuditionError(f"label '{label}' must be 1-64 letters, digits, '.', '_' or '-'")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise AuditionError(f"{label}: cannot read {path}") from exc
    if size > MAX_WAV_BYTES:
        raise AuditionError(f"{label}: {path.name} is over {MAX_WAV_BYTES >> 20} MiB; an audition "
                            "clip is a paragraph, not a recording")
    convert = f"convert it with: ffmpeg -i {path.name} -c:a pcm_s16le out.wav"
    try:
        with wave.open(str(path), "rb") as audio:
            width, channels = audio.getsampwidth(), audio.getnchannels()
            rate, raw = audio.getframerate(), audio.readframes(audio.getnframes())
    except (wave.Error, EOFError) as exc:
        raise AuditionError(
            f"{label}: {path.name} is not a readable PCM WAV ({exc}); {convert}"
        ) from exc
    if width != 2:
        raise AuditionError(f"{label}: {path.name} is {width * 8}-bit; {convert}")
    samples = array.array("h")
    samples.frombytes(raw[: len(raw) - len(raw) % 2])
    if sys.byteorder == "big":
        samples.byteswap()
    if not samples or not any(samples):
        raise AuditionError(f"{label}: {path.name} is silent")
    return Clip(label, path, channels, rate, samples)


def write_clip(path: Path, clip: Clip, gain: float) -> None:
    samples = clip.samples
    if gain != 1.0:
        samples = array.array(
            "h", (max(-FULL_SCALE, min(FULL_SCALE - 1, round(v * gain))) for v in samples)
        )
    if sys.byteorder == "big":
        samples = array.array("h", samples)
        samples.byteswap()
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(clip.channels)
        audio.setsampwidth(2)
        audio.setframerate(clip.sample_rate)
        audio.writeframes(samples.tobytes())


def build(
    out: Path,
    clips: list[Clip],
    seed: int | None = None,
    match_level: bool = True,
) -> tuple[dict, list[str]]:
    """Write take-N.wav files and the key; return the key and any warnings (none name a voice)."""
    labels = [clip.label for clip in clips]
    if len(clips) < 2:
        raise AuditionError("an audition needs at least two candidates")
    if len(set(labels)) != len(labels):
        raise AuditionError("candidate labels must be unique")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise AuditionError(f"{out} already exists and is not empty; choose a new directory")

    quietest = min(clip.rms for clip in clips)
    gains = {clip.label: quietest / clip.rms if match_level else 1.0 for clip in clips}
    spread = max(clip.rms_dbfs for clip in clips) - min(clip.rms_dbfs for clip in clips)
    warnings: list[str] = []
    if not match_level and spread > LEVEL_TOLERANCE_DB:
        warnings.append(
            f"levels differ by {spread:.1f} dB and were not matched; louder voices are rated higher"
        )
    if len({(clip.sample_rate, clip.channels) for clip in clips}) > 1:
        warnings.append(
            "takes differ in sample rate or channel count, which can reveal a voice to anyone who "
            "inspects the files; convert them to one format for a stricter test"
        )

    seed = secrets.randbits(32) if seed is None else seed
    order = list(clips)
    random.Random(seed).shuffle(order)
    out.mkdir(parents=True, exist_ok=True)
    takes = []
    for number, clip in enumerate(order, start=1):
        name = f"take-{number}.wav"
        if gains[clip.label] == 1.0:
            shutil.copyfile(clip.source, out / name)
        else:
            write_clip(out / name, clip, gains[clip.label])
        takes.append(
            {
                "take": number,
                "file": name,
                "label": clip.label,
                "source": str(clip.source),
                "seconds": round(clip.seconds, 3),
                "sample_rate": clip.sample_rate,
                "rms_dbfs": round(clip.rms_dbfs, 2),
                "peak_dbfs": round(clip.peak_dbfs, 2),
                "gain_db": round(20 * math.log10(gains[clip.label]), 2),
            }
        )
    key = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "match_level": match_level,
        "level_spread_db": round(spread, 2),
        "takes": takes,
    }
    (out / KEY_NAME).write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    return key, warnings


def parse_ranking(tokens: list[str], count: int) -> dict[int, int]:
    """Best-to-worst take numbers; `a=b` ties. Returns take -> rank (competition ranking)."""
    ranks: dict[int, int] = {}
    position = 1
    for token in tokens:
        try:
            group = [int(part) for part in token.split("=")]
        except ValueError as exc:
            raise AuditionError(f"'{token}' is not a take number (2, or a tie like 1=3)") from exc
        for take in group:
            if take in ranks or not 1 <= take <= count:
                raise AuditionError(f"each take 1-{count} must appear exactly once in --rank")
            ranks[take] = position
        position += len(group)
    if len(ranks) != count:
        raise AuditionError(f"--rank must place all {count} takes")
    return ranks


def reveal(directory: Path, tokens: list[str], subject: str | None, incumbent: str) -> dict:
    try:
        takes = json.loads((directory / KEY_NAME).read_text(encoding="utf-8"))["takes"]
        takes = [{"take": int(item["take"]), "label": str(item["label"])} for item in takes]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AuditionError(f"{directory} has no readable {KEY_NAME}; run build first") from exc
    if (directory / RESULT_NAME).exists():
        raise AuditionError(f"{directory / RESULT_NAME} exists; a ranking is recorded once")
    ranks = parse_ranking(tokens, len(takes))
    by_label = {item["label"]: ranks[item["take"]] for item in takes}
    if subject is not None and subject not in by_label:
        raise AuditionError(f"--subject '{subject}' is not a candidate in this audition")
    result = {
        "schema_version": 1,
        "ranked_at": datetime.now(timezone.utc).isoformat(),
        "ranking": sorted(
            ({"rank": ranks[item["take"]], "take": item["take"], "label": item["label"]}
             for item in takes),
            key=lambda row: (row["rank"], row["take"]),
        ),
        "subject": subject,
        "incumbent": incumbent if incumbent in by_label else None,
    }
    if subject is not None:
        result["subject_first"] = by_label[subject] == 1
        if result["incumbent"] is not None:
            result["subject_below_incumbent"] = by_label[subject] > by_label[incumbent]
    with (directory / RESULT_NAME).open("x", encoding="utf-8") as target:
        target.write(json.dumps(result, indent=2) + "\n")
    return result


def native_renderer() -> Renderer:
    spec = importlib.util.spec_from_file_location(
        "render_reply", Path(__file__).with_name("render_reply.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def collect(args: argparse.Namespace, render: Renderer | None, scratch: Path) -> list[Clip]:
    clips = []
    for spec in args.candidate:
        label, separator, path = spec.partition("=")
        if not separator or not path:
            raise AuditionError(f"--candidate '{spec}' must look like LABEL=file.wav")
        clips.append(read_clip(label, Path(path)))
    for spec in args.native:
        label, _, voice = spec.partition("=")
        if args.text_file is None:
            raise AuditionError("--native needs --text-file with the script to speak")
        text = args.text_file.read_text(encoding="utf-8").strip()
        if len(text) > MAX_NATIVE_TEXT:
            raise AuditionError(
                f"the native renderer takes at most {MAX_NATIVE_TEXT} characters; shorten the "
                "script or render the operating-system voice yourself and pass it as --candidate"
            )
        output = scratch / f"native-{len(clips)}.wav"
        (render or native_renderer())(text, output, voice or None)
        clips.append(read_clip(label, output))
    return clips


def main(argv: list[str] | None = None, render: Renderer | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("build", help="create a blind audition directory")
    make.add_argument("--out", type=Path, required=True, help="new, empty directory")
    make.add_argument("--candidate", action="append", default=[], metavar="LABEL=WAV")
    make.add_argument("--native", action="append", default=[], metavar="LABEL[=VOICE]")
    make.add_argument("--text-file", type=Path, help="script for --native renders")
    make.add_argument("--seed", type=int, help="fix the shuffle (default: random, recorded)")
    make.add_argument("--no-match-level", action="store_true", help="copy files unchanged")
    show = commands.add_parser("reveal", help="unmask a ranking and apply the pass rule")
    show.add_argument("directory", type=Path)
    show.add_argument(
        "--rank", nargs="+", required=True, metavar="TAKE", help="best first; join ties: 1=3"
    )
    show.add_argument("--subject", help="the voice under test (e.g. the local clone)")
    show.add_argument("--incumbent", default="nova-local", help="the voice being replaced")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            with tempfile.TemporaryDirectory(prefix="audition-") as scratch:
                clips = collect(args, render, Path(scratch))
                _, warnings = build(args.out, clips, args.seed, not args.no_match_level)
            for warning in warnings:
                sys.stderr.write(f"warning: {warning}\n")
            for number in range(1, len(clips) + 1):
                sys.stdout.write(f"{args.out / f'take-{number}.wav'}\n")
            sys.stdout.write(
                f"\nListen without opening {KEY_NAME}, then:\n"
                f"  python3 {sys.argv[0]} reveal {args.out} --rank <best> ... <worst>\n"
            )
            return 0
        result = reveal(args.directory, args.rank, args.subject, args.incumbent)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    for row in result["ranking"]:
        sys.stdout.write(f"{row['rank']}. take-{row['take']}  {row['label']}\n")
    if result["subject"] is not None:
        verdict = "first" if result["subject_first"] else "not first"
        sys.stdout.write(f"\n{result['subject']} ranked {verdict} (ties for first count).\n")
        if result.get("subject_below_incumbent"):
            sys.stdout.write(
                f"It ranked below {result['incumbent']}: under P-068 section 6.1 local voice is "
                "abandoned for this account.\n"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
