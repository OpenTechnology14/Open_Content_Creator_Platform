"""Bounded speech lifecycle with generation-safe cancellation."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Protocol

from .models import SpeechEvent, SpeechSettings, Voice

Emit = Callable[[dict], Awaitable[None]]


class SpeechAdapter(Protocol):
    async def synthesize(self, text: str, voice: Voice, output: Path) -> float: ...

    async def play(self, path: Path) -> None: ...

    async def stop(self) -> None: ...


class SpeechRuntime:
    """Speak only current, on-air replies and cancel promptly on operator controls."""

    def __init__(self, settings: SpeechSettings, adapter: SpeechAdapter, emit: Emit) -> None:
        self.settings = settings
        self.adapter = adapter
        self.emit = emit
        self.queue: asyncio.Queue[SpeechEvent] = asyncio.Queue(settings.queue_capacity)
        self.generation = -1
        self.paused = False
        self.seen: OrderedDict[str, float] = OrderedDict()
        self.worker: asyncio.Task | None = None
        self.active: asyncio.Task | None = None
        self.closed = False

    async def start(self) -> None:
        if self.closed:
            raise RuntimeError("speech runtime is closed")
        if self.worker is None:
            self.worker = asyncio.create_task(self._work())

    def _stale(self, event: SpeechEvent) -> bool:
        age = (datetime.now(timezone.utc) - event.created_at).total_seconds()
        return age > self.settings.event_ttl_seconds or age < -5

    async def _emit(self, kind: str, event: SpeechEvent, **data) -> None:
        await self.emit(
            {
                "schema_version": 1,
                "kind": kind,
                "event_id": event.event_id,
                "utterance_id": event.utterance_id,
                "session_id": event.session_id,
                "generation": event.generation,
                "avatar_id": event.avatar_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **data,
            }
        )

    def _clear_queue(self) -> None:
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()

    async def _cancel_active(self) -> None:
        if self.active is not None:
            self.active.cancel()
            await asyncio.gather(self.active, return_exceptions=True)
        await self.adapter.stop()

    async def submit(self, event: SpeechEvent) -> bool:
        if self.closed:
            raise RuntimeError("speech runtime is closed")
        if event.session_id != self.settings.on_air_session or self._stale(event):
            await self._emit("ignored", event, reason="off_air_or_stale")
            return False
        now = time.monotonic()
        while self.seen and next(iter(self.seen.values())) <= now:
            self.seen.popitem(last=False)
        key = event.utterance_id or f"control-{event.event_id}"
        if key in self.seen or event.generation < self.generation:
            await self._emit("ignored", event, reason="duplicate_or_old_generation")
            return False
        self.seen[key] = now + self.settings.event_ttl_seconds + 5
        if len(self.seen) > 1024:
            self.seen.popitem(last=False)

        if event.kind == "control":
            self.generation = event.generation
            self.paused = bool(event.paused)
            self._clear_queue()
            await self._cancel_active()
            await self._emit("controlled", event, action=event.action, paused=self.paused)
            return True
        if self.paused:
            await self._emit("ignored", event, reason="paused")
            return False
        if event.generation > self.generation:
            had_generation = self.generation >= 0
            self.generation = event.generation
            if had_generation:
                self._clear_queue()
                await self._cancel_active()
        else:
            self.generation = max(self.generation, event.generation)
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            await self._emit("ignored", event, reason="queue_full")
            return False
        return True

    async def _speak(self, event: SpeechEvent) -> None:
        self.settings.output_directory.mkdir(parents=True, exist_ok=True)
        output = self.settings.output_directory / f"{event.utterance_id}.wav"
        try:
            voice = self.settings.voices.get(event.voice_id)
            if event.voice_id not in self.settings.voices:
                await self._emit("failed", event, reason="unbound_voice")
                return
            duration = await self.adapter.synthesize(event.text, voice, output)
            if self.paused or event.generation != self.generation or self._stale(event):
                await self._emit("canceled", event, reason="stale_before_playback")
                return
            await self._emit("started", event, duration_seconds=round(duration, 3))
            await self.adapter.play(output)
            if not self.paused and event.generation == self.generation:
                await self._emit("finished", event, duration_seconds=round(duration, 3))
        finally:
            if not self.settings.retain_wav:
                output.unlink(missing_ok=True)

    async def _work(self) -> None:
        while True:
            event = await self.queue.get()
            try:
                self.active = asyncio.create_task(self._speak(event))
                await self.active
            except asyncio.CancelledError:
                if self.closed:
                    raise
            except Exception as exc:
                reason = getattr(exc, "failure_reason", "native_speech_failure")
                await self._emit("failed", event, reason=reason)
            finally:
                self.active = None
                self.queue.task_done()

    async def drain(self) -> None:
        await self.queue.join()

    async def close(self) -> None:
        self.closed = True
        self._clear_queue()
        await self._cancel_active()
        if self.worker is not None:
            self.worker.cancel()
            await asyncio.gather(self.worker, return_exceptions=True)
