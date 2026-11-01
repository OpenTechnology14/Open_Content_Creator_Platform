"""Drive talk/idle from actual audio playback timing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from .models import AvatarCueEvent, AvatarEvent, AvatarSettings


class AvatarAdapter(Protocol):
    async def connect(self) -> None: ...

    async def talk(self, avatar_id: str) -> None: ...

    async def idle(self, avatar_id: str) -> None: ...

    async def close(self) -> None: ...

    async def cue(self, avatar_id: str, cue: str) -> None: ...


class AvatarRuntime:
    def __init__(self, settings: AvatarSettings, adapter: AvatarAdapter) -> None:
        self.settings = settings
        self.adapter = adapter
        self.generation = -1
        self.active_utterance: str | None = None
        self.active_avatar: str | None = None
        self.seen: set[tuple[str, str | None]] = set()
        self.paused = True
        self.cue_floor = datetime.min.replace(tzinfo=timezone.utc)
        self.seen_cues: set[str] = set()
        self.cue_rotation = 0

    async def start(self) -> None:
        await self.adapter.connect()

    def _stale(self, event: AvatarEvent) -> bool:
        age = (datetime.now(timezone.utc) - event.created_at).total_seconds()
        return age > self.settings.event_ttl_seconds or age < -5

    async def handle(self, event: AvatarEvent) -> bool:
        if (
            event.session_id != self.settings.on_air_session
            or self._stale(event)
            or event.generation < self.generation
        ):
            return False
        key = (event.kind, event.utterance_id or event.event_id)
        if key in self.seen:
            return False
        self.seen.add(key)
        if len(self.seen) > 2048:
            self.seen.clear()
            self.seen.add(key)
        self.generation = event.generation

        if event.kind == "started":
            if event.avatar_id not in self.settings.avatars:
                return False
            if self.active_avatar and self.active_avatar != event.avatar_id:
                await self.adapter.idle(self.active_avatar)
            self.paused = False
            self.cue_floor = event.created_at
            await self.adapter.talk(event.avatar_id)
            if self.settings.full_body_enabled and self.settings.speech_cues:
                cue = self.settings.speech_cues[self.cue_rotation % len(self.settings.speech_cues)]
                self.cue_rotation += 1
                await self.adapter.cue(event.avatar_id, cue)
            self.active_avatar = event.avatar_id
            self.active_utterance = event.utterance_id
            return True
        if event.kind in {"finished", "canceled"}:
            if event.utterance_id != self.active_utterance or not self.active_avatar:
                return False
            await self.adapter.idle(self.active_avatar)
            self.active_avatar = None
            self.active_utterance = None
            return True
        if event.kind == "controlled":
            self.paused = bool(event.paused)
            self.cue_floor = event.created_at
        if event.kind == "controlled" and event.paused and self.active_avatar:
            await self.adapter.idle(self.active_avatar)
            self.active_avatar = None
            self.active_utterance = None
            return True
        return False

    async def handle_cue(self, event: AvatarCueEvent) -> bool:
        age = (datetime.now(timezone.utc) - event.created_at).total_seconds()
        if (
            not self.settings.full_body_enabled
            or self.paused
            or event.session_id != self.settings.on_air_session
            or age > self.settings.event_ttl_seconds
            or age < -5
            or event.created_at < self.cue_floor
            or event.event_id in self.seen_cues
            or event.avatar_id not in self.settings.avatars
            or (self.active_avatar and event.avatar_id != self.active_avatar)
        ):
            return False
        self.seen_cues.add(event.event_id)
        if len(self.seen_cues) > 512:
            self.seen_cues = {event.event_id}
        await self.adapter.cue(event.avatar_id, event.cue)
        return True

    async def close(self) -> None:
        if self.active_avatar:
            await self.adapter.idle(self.active_avatar)
        self.active_avatar = None
        self.active_utterance = None
        await self.adapter.close()
