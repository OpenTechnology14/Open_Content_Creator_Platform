"""Render a script's lines ahead of time and report how long each one took (P-068 section 6.2).

Local voices are for pre-recorded narration, never live: every line is rendered into the cache
before a run, so playback is instant and each line's real duration is known before pacing is
chosen (P-067 section 7.4). The report gives per-line durations and, per voice, the p50 and p95
render time that section 6.2 asks for instead of a mean, which hides the outlier that stalls a
batch. Run it with `python -m stream_speech --prerender lines.jsonl`.
"""

from __future__ import annotations

import hashlib
import math
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Awaitable, Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .models import Identifier, LocalVoice, SpeechSettings
from .providers import LocalSynthesizer, RoutedSpeechAdapter

MAX_LINES = 2000
MAX_FILE_BYTES = 4 * 1024 * 1024
P95_LIMIT_SECONDS = 60.0  # section 6.2's pass condition for batch use
MIN_SAMPLES = 20  # section 6.2 asks for twenty paragraphs before a p95 means anything

Emit = Callable[[dict], Awaitable[None]]


class PrerenderLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    voice_id: Identifier
    text: str = Field(min_length=1, max_length=500)


def read_lines(path: Path, settings: SpeechSettings) -> list[PrerenderLine]:
    """Validate the whole file before anything renders, so a typo on line 40 costs nothing."""
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("lines file exceeds 4 MiB")
    lines: list[PrerenderLine] = []
    with path.open(encoding="utf-8") as stream:
        for number, raw in enumerate(stream, start=1):
            if not raw.strip():
                continue
            try:
                line = PrerenderLine.model_validate_json(raw)
            except ValidationError as exc:
                problems = exc.error_count()
                raise ValueError(f"line {number} is invalid ({problems} problems)") from exc
            if not line.text.strip() or "\0" in line.text:
                raise ValueError(f"line {number} has no speakable text")
            if line.voice_id not in settings.voices:
                raise ValueError(f"line {number}: voice '{line.voice_id}' is not configured")
            lines.append(line)
            if len(lines) > MAX_LINES:
                raise ValueError(f"more than {MAX_LINES} lines")
    if not lines:
        raise ValueError("the lines file is empty")
    local = any(isinstance(settings.voices[line.voice_id], LocalVoice) for line in lines)
    if local and settings.render_cache_directory is None:
        raise ValueError("set render_cache_directory so pre-rendered lines survive the run")
    return lines


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


async def prerender(
    lines: list[PrerenderLine],
    settings: SpeechSettings,
    adapter: RoutedSpeechAdapter,
    local: LocalSynthesizer,
    emit: Emit,
    clock: Callable[[], float] = time.monotonic,
) -> dict:
    """Render every line, emit one record per line and return the summary record."""
    stats: dict[str, dict] = defaultdict(
        lambda: {"rendered": 0, "cached": 0, "failed": 0, "times": [], "rendered_audio": 0.0}
    )
    with tempfile.TemporaryDirectory(prefix="prerender-") as scratch:
        for index, line in enumerate(lines, start=1):
            voice = settings.voices[line.voice_id]
            provider = "local" if isinstance(voice, LocalVoice) else "native"
            record = {
                "schema_version": 1,
                "kind": "prerendered",
                "index": index,
                "voice_id": line.voice_id,
                "provider": provider,
                "characters": len(line.text),
                "text_sha256": hashlib.sha256(line.text.encode("utf-8")).hexdigest()[:16],
            }
            output = Path(scratch) / f"{index}.wav"
            entry = stats[line.voice_id]
            entry["provider"] = provider
            started = clock()
            try:
                audio = await adapter.synthesize(line.text, voice, output)
            except Exception as exc:
                entry["failed"] += 1
                reason = getattr(exc, "failure_reason", "native_speech_failure")
                record |= {"status": "failed", "reason": reason}
            else:
                seconds = clock() - started
                hit = provider == "local" and local.last_hit
                entry["cached" if hit else "rendered"] += 1
                if not hit:
                    entry["times"].append(seconds)
                    entry["rendered_audio"] += audio
                record |= {
                    "status": "cached" if hit else "rendered",
                    "render_seconds": round(seconds, 3),
                    "audio_seconds": round(audio, 3),
                }
            finally:
                output.unlink(missing_ok=True)
            await emit(record)
    return summarize(len(lines), stats)


def summarize(count: int, stats: dict[str, dict]) -> dict:
    by_voice = {}
    for voice_id, entry in stats.items():
        times = entry["times"]
        report: dict = {key: entry[key] for key in ("provider", "rendered", "cached", "failed")}
        if times:
            report["render_seconds"] = {
                "count": len(times),
                "p50": round(percentile(times, 50), 3),
                "p95": round(percentile(times, 95), 3),
                "max": round(max(times), 3),
            }
            if entry["rendered_audio"] > 0:
                report["real_time_factor"] = round(sum(times) / entry["rendered_audio"], 3)
            if entry["provider"] == "local":
                p95 = report["render_seconds"]["p95"]
                report["p95_under_limit"] = {
                    "limit_seconds": P95_LIMIT_SECONDS,
                    "samples": len(times),
                    "met": p95 < P95_LIMIT_SECONDS if len(times) >= MIN_SAMPLES else None,
                }
        by_voice[voice_id] = report
    totals = {
        key: sum(report[key] for report in by_voice.values())
        for key in ("rendered", "cached", "failed")
    }
    return {
        "schema_version": 1,
        "kind": "prerender_summary",
        "lines": count,
        **totals,
        "by_voice": by_voice,
    }
