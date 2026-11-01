"""Check a voice-clone source recording against the P-068 section 5.4 protocol.

A clone copies everything in its sample, room and artifacts included, so a poor recording is the
failure no engine can fix. This measures what can be measured objectively: format, length,
clipping, level, noise floor, digital silence left by edits or gating, DC offset, level drift
between sections and an unmistakable bandwidth cliff. Room reflections, register and varied
content stay with your ears. Standard library only.

    python3 modules/audio-production/tts/check_voice_sample.py recording.wav [--json] [--strict]

Exit 0 when ready (warnings allowed unless --strict), 1 when not ready, 2 when unreadable. The
thresholds below are starting values for the first real recording, not measurements of a good
one; the report prints every number so you can judge them. Leave a few seconds of room tone at
the start: the noise-floor estimate needs pauses.
"""

from __future__ import annotations

import argparse
import array
import json
import math
import struct
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from operator import mul
from pathlib import Path
from typing import BinaryIO

REQUIRED_RATE = 48000
ABSOLUTE_MIN_SECONDS = 6.0  # the documented XTTS v2 minimum
PROTOCOL_MIN_SECONDS = 180.0
PROTOCOL_MAX_SECONDS = 600.0
CLIP_RUN = 3  # consecutive full-scale samples that make clipping rather than a peak
PEAK_WARN_DBFS = -1.0
SPEECH_FAIL_BELOW_DBFS = -45.0
SPEECH_WARN_BELOW_DBFS = -35.0
SPEECH_WARN_ABOVE_DBFS = -9.0
SNR_FAIL_BELOW_DB = 30.0
SNR_WARN_BELOW_DB = 40.0
DC_WARN_PERCENT = 0.5
DRIFT_WARN_DB = 6.0

WINDOW_SECONDS = 0.1
BLOCK_SECONDS = 30.0
ACTIVE_ABOVE_NOISE_DB = 15.0
MIN_BLOCK_ACTIVE_WINDOWS = 10
SILENCE_SLICE_SECONDS = 0.01
SILENCE_MIN_SLICES = 3  # three whole 10 ms slices: reliably found from 40 ms of digital silence
SPECTRUM_SIZE = 2048
SPECTRUM_STEP_SECONDS = 2.5
MAX_SPECTRUM_WINDOWS = 32
MIN_SPECTRUM_WINDOWS = 4
CLIFF_SCAN_FROM_HZ = 3000.0
CLIFF_MAX_HZ = 17000.0
CLIFF_NEAR_HZ = 600.0
CLIFF_FAR_HZ = 900.0
CLIFF_DROP_DB = 30.0
CLIFF_CEILING_DB = 25.0


class SampleError(ValueError):
    """The file cannot be analysed at all; the message says why."""


@dataclass(frozen=True)
class Layout:
    tag: int  # 1 integer PCM, 3 IEEE float
    channels: int
    rate: int
    bits: int
    data_start: int
    data_bytes: int

    @property
    def frame_bytes(self) -> int:
        return self.channels * (self.bits // 8)

    @property
    def encoding(self) -> str:
        return f"{self.bits}-bit {'float' if self.tag == 3 else 'PCM'}"


def read_layout(handle: BinaryIO, file_size: int) -> Layout:
    head = handle.read(12)
    if len(head) < 12 or head[:4] != b"RIFF" or head[8:12] != b"WAVE":
        raise SampleError("not a RIFF/WAVE file (an MP3 or M4A renamed .wav looks like this)")
    fmt = None
    position = 12
    while position + 8 <= file_size:
        handle.seek(position)
        header = handle.read(8)
        if len(header) < 8:
            break
        chunk, size = header[:4], struct.unpack("<I", header[4:])[0]
        body = position + 8
        if chunk == b"fmt ":
            raw = handle.read(min(size, 40))
            if len(raw) < 16:
                raise SampleError("truncated fmt chunk")
            tag, channels, rate, _, _, bits = struct.unpack("<HHIIHH", raw[:16])
            if tag == 0xFFFE and len(raw) >= 26:
                tag = struct.unpack("<H", raw[24:26])[0]
            fmt = (tag, channels, rate, bits)
        elif chunk == b"data":
            if fmt is None:
                raise SampleError("data chunk before fmt chunk")
            available = file_size - body
            data_bytes = size if 0 < size <= available else available
            tag, channels, rate, bits = fmt
            if tag not in (1, 3):
                raise SampleError(f"compressed WAV (format tag {tag}); export uncompressed PCM")
            if (tag, bits) not in ((1, 16), (1, 24), (1, 32), (3, 32), (3, 64)):
                raise SampleError(f"{bits}-bit {'float' if tag == 3 else 'PCM'} is not supported")
            if channels < 1 or rate < 8000:
                raise SampleError("implausible channel count or sample rate")
            return Layout(tag, channels, rate, bits, body, data_bytes)
        position = body + size + (size & 1)
    raise SampleError("no audio data found")


def decode(raw: bytes, layout: Layout) -> tuple[array.array, float, float]:
    """Interleaved samples, the value meaning full scale, and the level counted as clipped."""
    bits = layout.bits
    if layout.tag == 3:
        samples = array.array("f" if bits == 32 else "d")
        samples.frombytes(raw)
        full, clip = 1.0, 1.0
    elif bits == 16:
        samples = array.array("h")
        samples.frombytes(raw)
        full, clip = 32768.0, 32767.0
    elif bits == 24:
        padded = bytearray(len(raw) // 3 * 4)
        padded[1::4], padded[2::4], padded[3::4] = raw[0::3], raw[1::3], raw[2::3]
        samples = array.array("i")
        samples.frombytes(bytes(padded))
        full, clip = 2.0**31, float((1 << 31) - 256)
    else:
        samples = array.array("i")
        samples.frombytes(raw)
        full, clip = 2.0**31, float((1 << 31) - 1)
    if sys.byteorder == "big":
        samples.byteswap()
    return samples, full, clip


def clipped_stats(channel: array.array, clip: float, carry: int) -> tuple[int, int, int]:
    """(runs of CLIP_RUN or more clipped samples, clipped samples, run length carried on)."""
    runs = clipped = 0
    for value in channel:
        if value >= clip or value <= -clip:
            carry += 1
            clipped += 1
            if carry == CLIP_RUN:
                runs += 1
        else:
            carry = 0
    return runs, clipped, carry


@lru_cache(maxsize=2)
def fft_tables(n: int) -> tuple[list[int], list[float], list[float], list[float]]:
    bits = n.bit_length() - 1
    reverse = [int(format(i, f"0{bits}b")[::-1], 2) for i in range(n)]
    cos = [math.cos(2 * math.pi * k / n) for k in range(n // 2)]
    sin = [-math.sin(2 * math.pi * k / n) for k in range(n // 2)]
    hann = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    return reverse, cos, sin, hann


def power_spectrum(frame: array.array) -> list[float]:
    """Hann-windowed power spectrum of n real samples (n a power of two): n/2 + 1 bins."""
    n = len(frame)
    reverse, cos, sin, hann = fft_tables(n)
    re = [frame[reverse[i]] * hann[reverse[i]] for i in range(n)]
    im = [0.0] * n
    size = 2
    while size <= n:
        half, step = size // 2, n // size
        for start in range(0, n, size):
            k = 0
            for j in range(start, start + half):
                c, s = cos[k], sin[k]
                tr = re[j + half] * c - im[j + half] * s
                ti = re[j + half] * s + im[j + half] * c
                re[j + half], im[j + half] = re[j] - tr, im[j] - ti
                re[j], im[j] = re[j] + tr, im[j] + ti
                k += step
        size *= 2
    return [re[k] * re[k] + im[k] * im[k] for k in range(n // 2 + 1)]


def find_cliff(power: list[float], rate: int) -> float | None:
    """Frequency in Hz of a brick-wall low-pass in the average spectrum, or None.

    Speech rolls off gradually. A drop of CLIFF_DROP_DB within a few hundred hertz, below
    CLIFF_MAX_HZ, that stays down is what MP3/AAC encoders and low-rate sources leave behind.
    """
    bin_hz = rate / SPECTRUM_SIZE
    level = [10 * math.log10(max(p, 1e-30)) for p in power]
    smooth = []
    for k in range(len(level)):
        around = level[max(0, k - 4) : k + 5]
        smooth.append(sum(around) / len(around))

    def bins(hz: float) -> int:
        return int(hz / bin_hz)

    near, far, reach = bins(CLIFF_NEAR_HZ), bins(CLIFF_FAR_HZ), bins(6000.0)
    last = min(bins(CLIFF_MAX_HZ), bins(rate * 0.45))
    for c in range(bins(CLIFF_SCAN_FROM_HZ), last + 1):
        if c + far + 8 >= len(smooth):
            break
        above = smooth[c + near : c + far]
        ceiling = max(smooth[c + near : min(len(smooth) - 4, c + reach)])
        if smooth[c] - sum(above) / len(above) >= CLIFF_DROP_DB and (
            smooth[c] - ceiling >= CLIFF_CEILING_DB
        ):
            return c * bin_hz + CLIFF_NEAR_HZ  # the look-ahead zone starts at the edge
    return None


def db(power: float) -> float:
    return 10 * math.log10(max(power, 1e-12))


@dataclass(frozen=True)
class Measurements:
    rate: int
    channels: int
    encoding: str
    seconds: float
    peak_dbfs: float
    clipped_runs: int
    clipped_samples: int
    speech_rms_dbfs: float | None
    noise_floor_dbfs: float
    snr_db: float | None
    dc_offset_percent: float
    digital_silence_runs: int
    level_range_db: float | None
    bandwidth_cliff_khz: float | None
    bandwidth_checked: bool
    active_seconds: float


def measure(path: Path) -> Measurements:
    size = path.stat().st_size
    with path.open("rb") as handle:
        layout = read_layout(handle, size)
        handle.seek(layout.data_start)
        frame_bytes = layout.frame_bytes
        frames_total = layout.data_bytes // frame_bytes
        rate, channels = layout.rate, layout.channels
        window = max(1, round(WINDOW_SECONDS * rate))
        sliver = max(1, round(SILENCE_SLICE_SECONDS * rate))
        block_frames = window * max(1, round(BLOCK_SECONDS / WINDOW_SECONDS))
        step = max(SPECTRUM_SIZE, round(SPECTRUM_STEP_SECONDS * rate))

        powers: list[float] = []
        segments: list[tuple[float, array.array]] = []
        peak = 0.0
        clipped_runs = clipped_samples = 0
        carry = [0] * channels
        dc_sum, dc_count = 0.0, 0
        zero_run, seen_sound, silent_runs = 0, False, 0
        done = 0
        while done < frames_total:
            raw = handle.read(min(block_frames, frames_total - done) * frame_bytes)
            frames = len(raw) // frame_bytes
            if frames == 0:
                break
            samples, full, clip = decode(raw[: frames * frame_bytes], layout)
            for c in range(channels):
                channel = samples[c::channels]
                top = max(max(channel), -min(channel))
                peak = max(peak, top / full)
                if top >= clip:
                    runs, hot, carry[c] = clipped_stats(channel, clip, carry[c])
                    clipped_runs += runs
                    clipped_samples += hot
                else:
                    carry[c] = 0
            first = samples[0::channels]
            dc_sum += sum(first)
            dc_count += len(first)
            for s in range(len(first) // sliver):
                if any(first[s * sliver : (s + 1) * sliver]):
                    if seen_sound and zero_run >= SILENCE_MIN_SLICES:
                        silent_runs += 1
                    zero_run, seen_sound = 0, True
                else:
                    zero_run += 1
            for i in range(0, len(first) - window + 1, window):
                piece = first[i : i + window]
                powers.append(sum(map(mul, piece, piece)) / window / (full * full))
            start = -(-done // step) * step
            for position in range(start, done + frames - SPECTRUM_SIZE + 1, step):
                piece = first[position - done : position - done + SPECTRUM_SIZE]
                level = sum(map(mul, piece, piece)) / SPECTRUM_SIZE / (full * full)
                segments.append((level, array.array("d", (v / full for v in piece))))
            done += frames

    if not powers:
        raise SampleError("the recording is shorter than 0.1 s")
    floor = max(sorted(powers)[int(0.1 * (len(powers) - 1))], 1e-12)
    gate = floor * 10 ** (ACTIVE_ABOVE_NOISE_DB / 10)
    active = [(i, p) for i, p in enumerate(powers) if p >= gate]
    speech = sum(p for _, p in active) / len(active) if active else None

    per_block = max(1, round(BLOCK_SECONDS / WINDOW_SECONDS))
    levels = []
    for begin in range(0, len(powers), per_block):
        inside = [p for i, p in active if begin <= i < begin + per_block]
        if len(inside) >= MIN_BLOCK_ACTIVE_WINDOWS:
            levels.append(db(sum(inside) / len(inside)))

    loud = [frame for level, frame in segments if level >= gate]
    cliff = None
    checked = len(loud) >= MIN_SPECTRUM_WINDOWS
    if checked:
        stride = max(1, len(loud) // MAX_SPECTRUM_WINDOWS)
        chosen = loud[::stride][:MAX_SPECTRUM_WINDOWS]
        total = [0.0] * (SPECTRUM_SIZE // 2 + 1)
        for frame in chosen:
            for k, value in enumerate(power_spectrum(frame)):
                total[k] += value
        found = find_cliff([v / len(chosen) for v in total], rate)
        cliff = None if found is None else found / 1000

    return Measurements(
        rate=rate,
        channels=channels,
        encoding=layout.encoding,
        seconds=round(frames_total / rate, 3),
        peak_dbfs=round(20 * math.log10(max(peak, 1e-6)), 2),
        clipped_runs=clipped_runs,
        clipped_samples=clipped_samples,
        speech_rms_dbfs=None if speech is None else round(db(speech), 2),
        noise_floor_dbfs=round(db(floor), 2),
        snr_db=None if speech is None else round(db(speech) - db(floor), 2),
        dc_offset_percent=round(dc_sum / dc_count / full * 100, 3),
        digital_silence_runs=silent_runs,
        level_range_db=round(max(levels) - min(levels), 2) if len(levels) >= 2 else None,
        bandwidth_cliff_khz=None if cliff is None else round(cliff, 1),
        bandwidth_checked=checked,
        active_seconds=round(len(active) * WINDOW_SECONDS, 1),
    )


@dataclass(frozen=True)
class Finding:
    check: str
    status: str  # pass | warn | fail | skip
    detail: str


def grade(m: Measurements) -> list[Finding]:
    """Turn measurements into findings. Pure, so every boundary can be tested directly."""
    found: list[Finding] = []

    def add(check: str, status: str, detail: str) -> None:
        found.append(Finding(check, status, detail))

    shape = f"{m.rate} Hz, {m.channels} ch, {m.encoding}"
    if m.rate != REQUIRED_RATE:
        add("format", "fail", f"{shape}; the protocol requires {REQUIRED_RATE} Hz")
    elif m.channels not in (1, 2):
        add("format", "fail", f"{shape}; use mono or stereo")
    else:
        add("format", "pass", shape)

    minutes = f"{m.seconds / 60:.1f} min"
    if m.seconds < ABSOLUTE_MIN_SECONDS:
        add("length", "fail", f"{m.seconds:.1f} s; the minimum is {ABSOLUTE_MIN_SECONDS:.0f} s")
    elif m.seconds < PROTOCOL_MIN_SECONDS:
        add("length", "warn", f"{minutes}; the protocol asks for 3-10 min")
    elif m.seconds > PROTOCOL_MAX_SECONDS:
        add("length", "warn", f"{minutes}; the protocol asks for 3-10 min")
    else:
        add("length", "pass", minutes)

    if m.clipped_runs:
        add(
            "clipping",
            "fail",
            f"{m.clipped_runs} clipped stretches ({m.clipped_samples} samples); lower the gain",
        )
    elif m.peak_dbfs > PEAK_WARN_DBFS:
        add("clipping", "warn", f"peak {m.peak_dbfs:.1f} dBFS leaves no headroom")
    else:
        add("clipping", "pass", f"peak {m.peak_dbfs:.1f} dBFS")

    if m.speech_rms_dbfs is None:
        add("level", "fail", "no speech found above the noise floor")
    elif m.speech_rms_dbfs < SPEECH_FAIL_BELOW_DBFS:
        add("level", "fail", f"speech at {m.speech_rms_dbfs:.1f} dBFS is far too quiet")
    elif m.speech_rms_dbfs < SPEECH_WARN_BELOW_DBFS:
        add("level", "warn", f"speech at {m.speech_rms_dbfs:.1f} dBFS is quiet; more gain helps")
    elif m.speech_rms_dbfs > SPEECH_WARN_ABOVE_DBFS:
        add("level", "warn", f"speech at {m.speech_rms_dbfs:.1f} dBFS is hot; clipping risk")
    else:
        add("level", "pass", f"speech {m.speech_rms_dbfs:.1f} dBFS")

    floor = f"noise floor {m.noise_floor_dbfs:.1f} dBFS"
    if m.snr_db is None:
        add("noise", "skip", f"{floor}; no speech to compare against")
    elif m.snr_db < SNR_FAIL_BELOW_DB:
        add("noise", "fail", f"{m.snr_db:.1f} dB over the {floor}; too noisy")
    elif m.snr_db < SNR_WARN_BELOW_DB:
        add("noise", "warn", f"{m.snr_db:.1f} dB over the {floor}; quieter is better")
    else:
        add("noise", "pass", f"{m.snr_db:.1f} dB over the {floor}")

    if m.digital_silence_runs:
        add(
            "silence",
            "warn",
            f"{m.digital_silence_runs} stretches of digital silence (40 ms+): edits or gating",
        )
    else:
        add("silence", "pass", "no digital silence inside the recording")

    if abs(m.dc_offset_percent) > DC_WARN_PERCENT:
        add("dc", "warn", f"DC offset {m.dc_offset_percent:.2f}% of full scale")
    else:
        add("dc", "pass", f"DC offset {m.dc_offset_percent:.2f}%")

    if m.level_range_db is None:
        add("drift", "skip", "needs two 30 s sections of speech to compare")
    elif m.level_range_db > DRIFT_WARN_DB:
        add(
            "drift",
            "warn",
            f"speech level varies by {m.level_range_db:.1f} dB between sections: mic or gain moved",
        )
    else:
        add("drift", "pass", f"speech level varies by {m.level_range_db:.1f} dB between sections")

    if not m.bandwidth_checked:
        add("bandwidth", "skip", "not enough speech for a spectrum")
    elif m.bandwidth_cliff_khz is not None:
        add(
            "bandwidth",
            "warn",
            f"sharp cutoff near {m.bandwidth_cliff_khz:.1f} kHz: typical of MP3/AAC or a "
            "low-rate source; record again from the original",
        )
    else:
        add("bandwidth", "pass", "no sharp cutoff below 17 kHz (cannot prove a lossless source)")
    return found


def verdict(findings: list[Finding]) -> str:
    statuses = {finding.status for finding in findings}
    return "fail" if "fail" in statuses else "warn" if "warn" in statuses else "pass"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("recording", type=Path)
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--strict", action="store_true", help="treat warnings as not ready")
    args = parser.parse_args(argv)
    try:
        measured = measure(args.recording)
    except (SampleError, OSError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    findings = grade(measured)
    outcome = verdict(findings)
    ready = outcome == "pass" or (outcome == "warn" and not args.strict)
    if args.json:
        sys.stdout.write(
            json.dumps(
                {
                    "file": str(args.recording),
                    "verdict": outcome,
                    "ready": ready,
                    "measurements": asdict(measured),
                    "findings": [asdict(finding) for finding in findings],
                },
                indent=2,
            )
            + "\n"
        )
        return 0 if ready else 1
    sys.stdout.write(f"voice sample: {args.recording}\n")
    for finding in findings:
        sys.stdout.write(f"  {finding.status.upper():5} {finding.check:10} {finding.detail}\n")
    counts = {s: sum(f.status == s for f in findings) for s in ("fail", "warn")}
    sys.stdout.write(f"\nverdict: {'READY' if ready else 'NOT READY'}")
    sys.stdout.write(f" ({counts['fail']} failed, {counts['warn']} warnings)\n")
    if ready:
        sys.stdout.write(
            "Room reflections, register and varied content are still yours to judge by ear. "
            "Keep the file under models/tts/ (gitignored).\n"
        )
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
