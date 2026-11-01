"""Local-voice provider seam for the speech worker (P-068 section 4).

A `provider: local` voice is rendered by a registered engine adapter and cached by content.
Playback, cancellation and every runtime event stay with the native player, so nothing downstream
of the WAV changes. No engine adapter ships yet: `default_engines()` is empty, which is why a
local voice reports "not ready" until one is installed.
"""

from __future__ import annotations

import asyncio
import hashlib
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol

from loguru import logger

from .cache import RenderCache, cache_key
from .models import LocalVoice, Voice
from .runtime import SpeechAdapter


class LocalSpeechError(RuntimeError):
    """A local engine failed to produce usable audio."""

    failure_reason = "local_speech_failure"


class EngineUnavailable(LocalSpeechError):
    """The configured engine cannot render right now: no adapter, not installed, files missing."""

    failure_reason = "local_engine_unavailable"


@dataclass(frozen=True)
class ResolvedVoice:
    """A local voice with its repository-relative paths made absolute."""

    spec: LocalVoice
    model_path: Path
    speaker_ref: Path | None


class Engine(Protocol):
    """One local TTS engine.

    Adapters import their heavy libraries lazily, run synthesis in a child process so `stop` can
    end it mid-line, and must deliver a PCM WAV at `voice.spec.sample_rate`.
    """

    def check(self, voice: ResolvedVoice) -> None:
        """Raise EngineUnavailable unless this engine can render `voice` right now."""

    async def synthesize(self, text: str, voice: ResolvedVoice, output: Path) -> None: ...

    async def stop(self) -> None: ...


def default_engines() -> dict[str, Engine]:
    """Engine adapters shipped in this build. Empty until a P-068 engine slice adds one."""
    return {}


def _measure(output: Path, sample_rate: int) -> float:
    try:
        with wave.open(str(output), "rb") as audio:
            frames, rate = audio.getnframes(), audio.getframerate()
    except (OSError, EOFError, wave.Error) as exc:
        raise LocalSpeechError("local engine produced an unreadable WAV") from exc
    if frames == 0:
        raise LocalSpeechError("local engine produced empty audio")
    if rate != sample_rate:
        raise LocalSpeechError(f"local engine produced {rate} Hz, voice expects {sample_rate} Hz")
    return frames / rate


class LocalSynthesizer:
    def __init__(
        self, engines: Mapping[str, Engine], root: Path, cache: RenderCache | None = None
    ) -> None:
        self.engines = dict(engines)
        self.root = root
        self.cache = cache
        self.active: Engine | None = None
        self.last_hit = False  # whether the most recent synthesize() was served from the cache
        self.digests: dict[tuple[str, int, int], str] = {}

    def resolve(self, voice: LocalVoice) -> ResolvedVoice:
        speaker_ref = self.root / voice.speaker_ref if voice.speaker_ref else None
        return ResolvedVoice(voice, self.root / voice.model_path, speaker_ref)

    def _ready_engine(self, resolved: ResolvedVoice) -> Engine:
        voice = resolved.spec
        engine = self.engines.get(voice.engine)
        if engine is None:
            raise EngineUnavailable(f"no adapter for engine '{voice.engine}' in this build")
        if not resolved.model_path.exists():
            raise EngineUnavailable(f"model_path not found: {voice.model_path}")
        if resolved.speaker_ref is not None and not resolved.speaker_ref.is_file():
            raise EngineUnavailable(f"speaker_ref not found: {voice.speaker_ref}")
        engine.check(resolved)
        return engine

    def readiness(self, voice: LocalVoice) -> tuple[bool, str]:
        try:
            self._ready_engine(self.resolve(voice))
        except EngineUnavailable as exc:
            return False, str(exc)
        return True, "ready"

    def _digest(self, path: Path | None) -> str | None:
        """Hash of the reference recording, memoized until the file changes."""
        if path is None:
            return None
        stat = path.stat()
        memo = (str(path), stat.st_mtime_ns, stat.st_size)
        if memo not in self.digests:
            sha = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1 << 20), b""):
                    sha.update(block)
            self.digests[memo] = sha.hexdigest()
        return self.digests[memo]

    async def synthesize(self, text: str, voice: LocalVoice, output: Path) -> float:
        self.last_hit = False
        if not text.strip() or len(text) > 500 or "\0" in text:
            raise ValueError("invalid speech text")
        if output.exists():
            raise ValueError("speech output already exists")
        resolved = self.resolve(voice)
        engine = self._ready_engine(resolved)
        key = cache_key(text, voice, self._digest(resolved.speaker_ref))
        if self.cache is not None:
            cached = self.cache.fetch(key, output)
            if cached is not None:
                self.last_hit = True
                return cached
        self.active = engine
        try:
            await engine.synthesize(text, resolved, output)
            duration = _measure(output, voice.sample_rate)
        except asyncio.CancelledError:
            await engine.stop()
            output.unlink(missing_ok=True)
            raise
        except Exception as exc:
            output.unlink(missing_ok=True)
            if isinstance(exc, LocalSpeechError):
                raise
            raise LocalSpeechError(f"{voice.engine} failed ({type(exc).__name__})") from exc
        finally:
            self.active = None
        if self.cache is not None:
            try:
                self.cache.store(key, output)
            except OSError:
                logger.warning("render cache write failed; the line is spoken but not cached")
        return duration

    async def stop(self) -> None:
        if self.active is not None:
            await self.active.stop()


class RoutedSpeechAdapter:
    """Send local voices to the local provider and everything else to the native adapter.

    Playback and cancellation always belong to the native player, so the runtime emits the same
    started/finished/canceled events whichever provider rendered the WAV.
    """

    def __init__(self, native: SpeechAdapter, local: LocalSynthesizer) -> None:
        self.native = native
        self.local = local

    async def synthesize(self, text: str, voice: Voice, output: Path) -> float:
        if isinstance(voice, LocalVoice):
            return await self.local.synthesize(text, voice, output)
        return await self.native.synthesize(text, voice, output)

    async def play(self, path: Path) -> None:
        await self.native.play(path)

    async def stop(self) -> None:
        try:
            await self.local.stop()
        finally:
            await self.native.stop()
