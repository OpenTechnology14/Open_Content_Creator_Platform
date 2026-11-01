"""Cancellable macOS and Windows speech synthesis/playback adapter."""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import wave
from pathlib import Path


class NativeSpeechAdapter:
    def __init__(self) -> None:
        self.process: asyncio.subprocess.Process | None = None

    @staticmethod
    def dependencies() -> list[str]:
        if sys.platform == "darwin":
            return ["say", "afplay"]
        if sys.platform == "win32":
            return ["powershell.exe"]
        return []

    def check(self) -> None:
        required = self.dependencies()
        if not required or any(shutil.which(command) is None for command in required):
            raise RuntimeError("native speech playback is unavailable on this system")

    async def _run(self, command: list[str], stdin: str | None = None) -> None:
        self.process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, _ = await self.process.communicate(None if stdin is None else stdin.encode())
            if self.process.returncode != 0:
                raise RuntimeError("native speech command failed")
        except asyncio.CancelledError:
            await self.stop()
            raise
        finally:
            self.process = None

    async def synthesize(self, text: str, voice: str | None, output: Path) -> float:
        self.check()
        if not text.strip() or len(text) > 500 or "\0" in text:
            raise ValueError("invalid speech text")
        if output.exists():
            raise ValueError("speech output already exists")
        if sys.platform == "darwin":
            command = [
                shutil.which("say") or "say",
                "--file-format=WAVE",
                "--data-format=LEI16@22050",
                "-o",
                str(output),
            ]
            if voice:
                command.extend(["-v", voice])
            stdin = text
        else:
            script = (Path(__file__).parents[1] / "tts/windows_speech.ps1").read_text(
                encoding="utf-8"
            )
            command = [
                shutil.which("powershell.exe") or "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ]
            stdin = json.dumps({"text": text, "voice": voice, "output": str(output.resolve())})
        await self._run(command, stdin)
        with wave.open(str(output), "rb") as audio:
            if audio.getnframes() == 0:
                raise RuntimeError("native speech produced empty audio")
            return audio.getnframes() / audio.getframerate()

    async def play(self, path: Path) -> None:
        self.check()
        if sys.platform == "darwin":
            await self._run([shutil.which("afplay") or "afplay", str(path)])
        else:
            script = Path(__file__).with_name("windows_playback.ps1").read_text(encoding="utf-8")
            await self._run(
                [
                    shutil.which("powershell.exe") or "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    script,
                ],
                json.dumps({"path": str(path.resolve())}),
            )

    async def stop(self) -> None:
        process = self.process
        if process is not None and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), 0.2)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
