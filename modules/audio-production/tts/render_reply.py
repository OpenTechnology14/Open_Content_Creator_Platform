"""Render a saved stream-host reply to local speech without playing or broadcasting it."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from loguru import logger


def read_reply(path: Path, session_id: str) -> str:
    """Validate one reply or backend EventOut envelope and require an explicit session."""
    if path.stat().st_size > 16384:
        raise ValueError("reply file exceeds 16 KiB")
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and value.get("source") == "stream-host":
        value = value.get("data")
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("unsupported reply schema")
    if value.get("kind") != "reply" or value.get("session_id") != session_id:
        raise ValueError("expected a reply for the selected session")
    text = value.get("text")
    if not isinstance(text, str) or not text.strip() or len(text) > 500 or "\x00" in text:
        raise ValueError("invalid speech text")
    return text


def render(text: str, output: Path, voice: str | None = None) -> float:
    """Use installed macOS/Windows voices; viewer content is data, never script code."""
    executable = shutil.which("powershell.exe" if sys.platform == "win32" else "say")
    if sys.platform not in {"darwin", "win32"} or executable is None:
        raise RuntimeError("speech export needs macOS say or Windows PowerShell with System.Speech")
    if not text.strip() or len(text) > 500 or "\x00" in text:
        raise ValueError("invalid speech text")
    if output.exists():
        raise ValueError("output already exists; choose a new file")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="host-tts-", dir=output.parent) as temporary:
        wav = Path(temporary) / "reply.wav"
        if sys.platform == "win32":
            # Only repository-owned code goes in -Command. JSON values are read from stdin,
            # never interpolated into PowerShell, and Speak treats text as plain text, not SSML.
            script = Path(__file__).with_name("windows_speech.ps1").read_text(encoding="utf-8")
            command = [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]
            payload = json.dumps({"text": text, "voice": voice, "output": str(wav.resolve())})
        else:
            command = [
                executable,
                "--file-format=WAVE",
                "--data-format=LEI16@22050",
                "-o",
                str(wav),
            ]
            if voice:
                command.extend(["-v", voice])
            payload = text
        subprocess.run(
            command,
            input=payload,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
            timeout=45,
        )
        with wave.open(str(wav), "rb") as audio:
            if audio.getnframes() == 0:
                raise ValueError("speech renderer produced empty audio")
            duration = audio.getnframes() / audio.getframerate()
        # Exclusive creation also prevents overwriting if a second render races this one.
        with output.open("xb") as target:
            target.write(wav.read_bytes())
        return duration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reply", type=Path, required=True, help="single saved reply JSON")
    parser.add_argument("--session", required=True, help="expected session ID")
    parser.add_argument("--output", type=Path, required=True, help="new WAV file")
    parser.add_argument("--voice", help="installed system voice name (defaults to system voice)")
    args = parser.parse_args()
    try:
        duration = render(read_reply(args.reply, args.session), args.output, args.voice)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        logger.error("speech render failed: {}", type(exc).__name__)
        return 1
    sys.stdout.write(
        json.dumps({"output": str(args.output.resolve()), "duration_seconds": round(duration, 3)})
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
