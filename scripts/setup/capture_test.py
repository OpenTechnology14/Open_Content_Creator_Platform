"""Run a short, local capture-card signal and recording probe.

This command deliberately accepts only device IDs produced by capture_devices.py. It never opens
an arbitrary executable or path and it never changes the device format permanently.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

FRAME_RE = re.compile(r"frame=\s*(\d+)")
TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")


def _name(device_id: str, kind: str) -> str:
    prefix = f"dshow:{kind}:"
    if device_id.startswith(prefix) and len(device_id) > len(prefix):
        value = device_id[len(prefix) :]
        if len(value) <= 512 and not any(ord(char) < 32 or char in {'"', '\\'} for char in value):
            return value
    raise ValueError(f"Choose a {kind} device from the latest local scan")


def _index(device_id: str, kind: str) -> str:
    prefix = f"avfoundation:{kind}:"
    value = device_id[len(prefix) :] if device_id.startswith(prefix) else ""
    if value.isdigit():
        return value
    raise ValueError(f"Choose a {kind} device from the latest local scan")


def build_command(
    executable: str, system: str, video_id: str, audio_id: str | None, output: str
) -> list[str]:
    """Build the fixed FFmpeg capture command for one scanned device selection."""
    if system == "Windows":
        video = _name(video_id, "video")
        audio = _name(audio_id, "audio") if audio_id else None
        source = f'video="{video}"' + (f':audio="{audio}"' if audio else "")
        return [
            executable,
            "-hide_banner",
            "-loglevel",
            "info",
            "-f",
            "dshow",
            "-video_size",
            "1280x720",
            "-framerate",
            "30",
            "-i",
            source,
            "-t",
            "3",
            "-y",
            output,
        ]
    if system == "Darwin":
        video = _index(video_id, "video")
        audio = _index(audio_id, "audio") if audio_id else "none"
        return [
            executable,
            "-hide_banner",
            "-loglevel",
            "info",
            "-f",
            "avfoundation",
            "-framerate",
            "30",
            "-video_size",
            "1280x720",
            "-i",
            f"{video}:{audio}",
            "-t",
            "3",
            "-y",
            output,
        ]
    raise ValueError(f"Capture testing is not implemented for {system}")


def _streams_and_frames(stderr: str) -> tuple[bool, bool, int, float | None]:
    video = bool(re.search(r"Stream #.*Video:", stderr, re.IGNORECASE))
    audio = bool(re.search(r"Stream #.*Audio:", stderr, re.IGNORECASE))
    frames = [int(value) for value in FRAME_RE.findall(stderr)]
    times = [value for value in TIME_RE.findall(stderr)]
    duration = None
    if times:
        hours, minutes, seconds = times[-1]
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return video, audio, max(frames, default=0), duration


def probe(
    video_id: str,
    audio_id: str | None = None,
    *,
    system: str | None = None,
    executable: str | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    """Run a three-second probe and return separate signal/recording evidence."""
    system = system or platform.system()
    executable = executable or shutil.which("ffmpeg")
    checked_at = int(time.time())
    base: dict[str, Any] = {
        "schema_version": 1,
        "checked_at": checked_at,
        "platform": system,
        "duration_requested_seconds": 3,
        "stages": {"detected": True, "signal": False, "recorded": False, "accepted": False},
        "video_id": video_id,
        "audio_id": audio_id,
        "scope": "Bounded local probe; it does not change device formats or bypass HDCP.",
    }
    if not executable:
        base.update({"status": "action_required", "error": "FFmpeg was not found."})
        return base
    try:
        with tempfile.TemporaryDirectory(prefix="hcp-capture-test-") as directory:
            output = str(Path(directory) / "capture.mkv")
            command = build_command(executable, system, video_id, audio_id, output)
            result = runner(command, capture_output=True, text=True, timeout=20, check=False)
            stderr = f"{result.stdout}\n{result.stderr}"
            video, audio, frames, duration = _streams_and_frames(stderr)
            recorded = result.returncode == 0 and Path(output).is_file() and Path(output).stat().st_size > 0
            signal = frames > 0
            base.update(
                {
                    "status": "accepted" if recorded else ("signal" if signal else "action_required"),
                    "stages": {"detected": True, "signal": signal, "recorded": recorded, "accepted": recorded},
                    "video_stream": video,
                    "audio_stream": audio,
                    "frames_observed": frames,
                    "duration_observed_seconds": duration,
                    "recording_bytes": Path(output).stat().st_size if recorded else 0,
                }
            )
            if not recorded:
                base["error"] = "FFmpeg did not complete a bounded recording; check HDMI, USB, permissions and device mode."
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        base.update({"status": "action_required", "error": str(error)})
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--audio-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = probe(args.video_id, args.audio_id)
    print(json.dumps(report) if args.json else json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
