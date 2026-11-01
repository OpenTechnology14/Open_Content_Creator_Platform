"""Bounded per-session conversations; no game input or OBS control authority."""

from __future__ import annotations

import asyncio
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable, Protocol

from loguru import logger

from .models import HostConfig, HostEvent, Persona

Emit = Callable[[dict], Awaitable[None]]


class Responder(Protocol):
    async def reply(self, persona: Persona, history: list[dict[str, str]], text: str) -> str:
        """Return text; implementations must cooperate with cancellation."""
        ...


@dataclass
class Session:
    persona_id: str
    queue: asyncio.Queue
    generation: int = 0
    paused: bool = False
    history: list[dict[str, str]] = field(default_factory=list)
    last_phrases: dict[str, float] = field(default_factory=dict)
    phrase_index: dict[str, int] = field(default_factory=dict)
    seen: OrderedDict = field(default_factory=OrderedDict)
    active: asyncio.Task | None = None
    worker: asyncio.Task | None = None


class HostRuntime:
    def __init__(self, config: HostConfig, responder: Responder, emit: Emit) -> None:
        self.config = config
        self.responder = responder
        self.emit = emit
        self.sessions = {
            key: Session(value.persona_id, asyncio.Queue(config.queue_capacity))
            for key, value in config.sessions.items()
        }
        self.closed = False

    async def start(self) -> None:
        """Start one bounded worker per configured session."""
        if self.closed:
            raise RuntimeError("runtime is closed")
        for key, session in self.sessions.items():
            if session.worker is None:
                session.worker = asyncio.create_task(self._work(key, session))

    def _blocked(self, text: str) -> bool:
        folded = text.casefold()
        return any(term.casefold() in folded for term in self.config.blocked_terms) or bool(
            re.search(r"https?://|\b(?:free\s+v[-]?bucks|nitro\s+gift)\b", folded)
        )

    def _expired(self, event: HostEvent) -> bool:
        age = (datetime.now(timezone.utc) - event.occurred_at).total_seconds()
        return age > self.config.event_ttl_seconds or age < -5

    async def _notice(self, event: HostEvent, kind: str, reason: str) -> None:
        await self.emit(
            {
                "schema_version": 1,
                "kind": kind,
                "event_id": event.event_id,
                "session_id": event.session_id,
                "reason": reason,
            }
        )

    async def submit(self, event: HostEvent) -> bool:
        """Accept chat/game content or operator controls. Never read controls from chat text."""
        if self.closed:
            raise RuntimeError("runtime is closed")
        session = self.sessions.get(event.session_id)
        if session is None:
            await self._notice(event, "dropped", "unknown_session")
            return False
        if self._expired(event):
            await self._notice(event, "dropped", "expired_or_future")
            return False
        now = time.monotonic()
        while session.seen and next(iter(session.seen.values())) <= now:
            session.seen.popitem(last=False)
        if event.event_id in session.seen:
            await self._notice(event, "dropped", "duplicate")
            return False
        # Capacity bound as well as time bound; never retain viewer content here.
        session.seen[event.event_id] = now + self.config.event_ttl_seconds + 5
        if len(session.seen) > 1024:
            session.seen.popitem(last=False)

        if event.kind in {"pause", "resume", "persona"}:
            if event.kind == "persona" and event.persona_id not in self.config.personas:
                await self._notice(event, "dropped", "unknown_persona")
                return False
            session.generation += 1
            if session.active is not None:
                session.active.cancel()
            self._clear_queue(session)
            if event.kind == "persona":
                session.persona_id = event.persona_id
                session.history.clear()
                session.last_phrases.clear()
                session.phrase_index.clear()
            else:
                session.paused = event.kind == "pause"
            await self.emit(
                {
                    "schema_version": 1,
                    "kind": "control",
                    "event_id": event.event_id,
                    "session_id": event.session_id,
                    "generation": session.generation,
                    "persona_id": session.persona_id,
                    "paused": session.paused,
                    "action": event.kind,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return True
        if session.paused:
            await self._notice(event, "dropped", "paused")
            return False
        if self._blocked(event.text):
            await self._notice(event, "dropped", "content_filter")
            return False
        try:
            session.queue.put_nowait((session.generation, event))
        except asyncio.QueueFull:
            await self._notice(event, "dropped", "queue_full")
            return False
        return True

    @staticmethod
    def _clear_queue(session: Session) -> None:
        while not session.queue.empty():
            session.queue.get_nowait()
            session.queue.task_done()

    async def _work(self, key: str, session: Session) -> None:
        while True:
            generation, event = await session.queue.get()
            try:
                session.active = asyncio.create_task(self._respond(session, generation, event))
                await session.active
            except asyncio.CancelledError:
                if self.closed:
                    raise
            except Exception as exc:
                # Do not log chat, model output, URLs or credential-bearing exceptions.
                logger.warning(
                    "host dependency failure: session={} type={}", key, type(exc).__name__
                )
                try:
                    await self._notice(event, "error", "reply_or_delivery_failed")
                except Exception:
                    logger.warning("host error delivery failed: session={}", key)
            finally:
                session.active = None
                session.queue.task_done()

    async def _respond(self, session: Session, generation: int, event: HostEvent) -> None:
        if generation != session.generation or session.paused:
            return
        if self._expired(event):
            await self._notice(event, "dropped", "expired_in_queue")
            return
        persona = self.config.resolve_persona(session.persona_id)
        phrase = None
        if event.kind == "game":
            phrases = persona.catchphrases.get(event.reaction, [])
            if not phrases:
                await self._notice(event, "dropped", "unknown_reaction")
                return
            index = session.phrase_index.get(event.reaction, 0)
            phrase = phrases[index % len(phrases)]
            last = session.last_phrases.get(phrase)
            if (
                last is not None
                and time.monotonic() - last < self.config.catchphrase_cooldown_seconds
            ):
                await self._notice(event, "dropped", "catchphrase_cooldown")
                return
            reply = phrase
        else:
            reply = await asyncio.wait_for(
                self.responder.reply(persona, list(session.history), event.text),
                timeout=self.config.reply_timeout_seconds,
            )
        if generation != session.generation or session.paused or self.closed:
            return
        if self._expired(event):
            await self._notice(event, "dropped", "expired_during_reply")
            return
        if not isinstance(reply, str) or not reply.strip() or self._blocked(reply):
            await self._notice(event, "dropped", "output_filter")
            return
        # Check full output BEFORE truncation so a forbidden suffix is not hidden.
        reply = reply.strip()[: self.config.max_reply_characters]
        await self.emit(
            {
                "schema_version": 1,
                "kind": "reply",
                "event_id": event.event_id,
                "utterance_id": f"{event.session_id}-{generation}-{event.event_id}",
                "session_id": event.session_id,
                "generation": generation,
                "game_id": persona.game_id,
                "persona_id": session.persona_id,
                "display_name": persona.display_name,
                "voice_id": persona.voice_id,
                "avatar_id": persona.avatar_id,
                "audio_policy": persona.audio_policy,
                "text": reply,
                "reaction": event.reaction,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        if generation != session.generation:
            return
        if phrase is not None:
            session.last_phrases[phrase] = time.monotonic()
            session.phrase_index[event.reaction] = session.phrase_index.get(event.reaction, 0) + 1
        elif self.config.history_turns:
            session.history.extend(
                [
                    {"role": "user", "content": event.text},
                    {"role": "assistant", "content": reply},
                ]
            )
            del session.history[: -self.config.history_turns * 2]

    async def drain(self) -> None:
        """Wait for admitted content to finish (used for file replay and orderly shutdown)."""
        await asyncio.gather(*(s.queue.join() for s in self.sessions.values()))

    async def close(self) -> None:
        """Cancel in-flight replies and discard queued content without speaking it later."""
        self.closed = True
        tasks = []
        for session in self.sessions.values():
            session.generation += 1
            self._clear_queue(session)
            for task in (session.active, session.worker):
                if task is not None:
                    task.cancel()
                    tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
