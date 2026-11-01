"""Map scoped host events to configured module actions without model tool authority."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Awaitable, Callable

from .config import HostOutput, Settings
from .phrases import intact, load

Execute = Callable[[str, dict], Awaitable[str]]
Report = Callable[[dict], Awaitable[None]]


class Director:
    def __init__(self, settings: Settings, execute: Execute, report: Report) -> None:
        self.settings, self.execute, self.report = settings, execute, report
        self.generation = -1
        self.paused = False
        self.seen = OrderedDict()
        self.last_sound = float("-inf")
        self.caption_task = None
        self.caption_revision = 0
        self.lock = asyncio.Lock()
        self.phrase_profiles = load(settings.phrase_manifest)
        self.phrase_indices: dict[tuple[str, str], int] = {}

    async def _action(self, kind: str, data: dict) -> str:
        try:
            status = await asyncio.wait_for(
                self.execute(kind, data), self.settings.request_timeout_seconds + 1
            )
        except Exception as exc:
            await self.report(
                {
                    "kind": "action_result",
                    "action": kind,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "session_id": self.settings.on_air_session,
                }
            )
            return "failed"
        else:
            await self.report(
                {
                    "kind": "action_result",
                    "action": kind,
                    "status": status,
                    "session_id": self.settings.on_air_session,
                }
            )
            return status

    def _stale(self, event: HostOutput) -> bool:
        age = (datetime.now(timezone.utc) - event.created_at).total_seconds()
        return age > self.settings.event_ttl_seconds or age < -5

    async def handle(self, event: HostOutput) -> None:
        """Process one authenticated host event; only on-air session may change shared OBS."""
        async with self.lock:
            if event.session_id != self.settings.on_air_session or self._stale(event):
                await self.report({"kind": "ignored", "reason": "off_air_or_stale"})
                return
            key = (event.kind, event.event_id, event.generation)
            now = time.monotonic()
            while self.seen and next(iter(self.seen.values())) <= now:
                self.seen.popitem(last=False)
            if key in self.seen or event.generation < self.generation:
                await self.report({"kind": "ignored", "reason": "duplicate_or_old_generation"})
                return
            self.seen[key] = now + self.settings.event_ttl_seconds + 5
            if len(self.seen) > 1024:
                self.seen.popitem(last=False)
            self.generation = event.generation
            if event.kind == "control":
                self.paused = event.paused
                self._cancel_caption()
                # Pausing first silences the configured AI voice input inside OBS.
                if self.paused:
                    if self.settings.ai_voice_input:
                        await self._action(
                            "audio.mute",
                            {"inputName": self.settings.ai_voice_input, "inputMuted": True},
                        )
                    if self.settings.stop_sound_hotkey:
                        await self._action(
                            "soundboard.stop", {"hotkeyName": self.settings.stop_sound_hotkey}
                        )
                if self.paused or event.action == "persona":
                    for hotkey in {profile.stop_hotkey for profile in self.phrase_profiles.values()}:
                        await self._action("soundboard.stop", {"hotkeyName": hotkey})
                if self.settings.lower_third:
                    await self._action("graphics.lower_third", {"visible": False})
                scene = self.settings.pause_scene if self.paused else self.settings.resume_scene
                if scene and event.action in {"pause", "resume"}:
                    await self._action("obs.scene", {"sceneName": scene})
                trigger = self.settings.automation_triggers.get(event.action)
                if trigger:
                    await self._action(
                        "automation.trigger",
                        {
                            "name": trigger,
                            "payload": {
                                "session_id": event.session_id,
                                "event_id": event.event_id,
                                "generation": event.generation,
                                "action": event.action,
                            },
                        },
                    )
                # Resume deliberately leaves audio muted: existing external TTS playback could
                # be stale. The operator unmutes after verifying the voice bus is ready.
                return
            if self.paused:
                await self.report({"kind": "ignored", "reason": "paused"})
                return
            if self.settings.phrase_manifest is not None:
                await self._route_phrase(event)
                return
            if self.settings.lower_third:
                self._cancel_caption()
                await self._action(
                    "graphics.lower_third",
                    {
                        "visible": True,
                        "title": event.display_name[:100],
                        "subtitle": event.text[:280],
                    },
                )
                revision = self.caption_revision
                self.caption_task = asyncio.create_task(self._hide_caption(revision))
            if self._stale(event):
                return
            slot = self.settings.reaction_sounds.get(event.game_id, {}).get(event.reaction)
            if slot and event.audio_policy not in (None, "gaming-reactive"):
                # Scripted personalities speak on AI-VOICE only, even if a slot is mapped.
                await self.report(
                    {"kind": "skipped", "reason": "scripted_audio_policy", "slot": slot}
                )
            elif slot:
                hotkey = self.settings.sound_hotkeys.get(slot)
                if not hotkey:
                    await self.report(
                        {"kind": "skipped", "reason": "unbound_sound_slot", "slot": slot}
                    )
                elif time.monotonic() - self.last_sound < self.settings.sound_cooldown_seconds:
                    await self.report({"kind": "skipped", "reason": "sound_cooldown", "slot": slot})
                else:
                    # Reserve before dispatch: an ambiguous OBS timeout must not spam replay.
                    self.last_sound = time.monotonic()
                    await self._action("soundboard.play", {"hotkeyName": hotkey})

    async def _route_phrase(self, event: HostOutput) -> None:
        profile = self.phrase_profiles.get(event.persona_id)
        reason = "no_phrase"
        assets = []
        if (event.audio_policy == "gaming-reactive" and profile
                and profile.game_id == event.game_id and profile.voice_id == event.voice_id):
            assets = [asset for asset in profile.assets if asset.reaction == event.reaction]
        if assets:
            key = (event.persona_id, event.reaction)
            index = self.phrase_indices.get(key, 0)
            asset = assets[index % len(assets)]
            reason = "missing_or_changed_asset"
            if intact(asset):
                try:
                    available = await asyncio.wait_for(
                        self.execute("soundboard.available", {"hotkeyName": asset.hotkey}),
                        self.settings.request_timeout_seconds,
                    )
                except Exception:
                    available = "unavailable"
                reason = "unbound_hotkey"
                if available == "available":
                    if self._stale(event):
                        return
                    if time.monotonic() - self.last_sound < self.settings.sound_cooldown_seconds:
                        await self.report({"kind": "skipped", "reason": "sound_cooldown"})
                        return
                    self.last_sound = time.monotonic()
                    self.phrase_indices[key] = index + 1
                    await self._caption(event, asset.text)
                    if self._stale(event):
                        return
                    status = await self._action("soundboard.play", {"hotkeyName": asset.hotkey})
                    # Success or uncertain failure: never also speak the same reaction.
                    await self.report({"kind": "routed", "reason": "clip_dispatched" if status == "acknowledged" else "clip_dispatch_uncertain",
                                       "status": status, "session_id": event.session_id,
                                       "generation": event.generation, "event_id": event.event_id,
                                       "revision_id": profile.revision_id})
                    return
        if (event.reaction and event.audio_policy == "gaming-reactive"
                and self.settings.phrase_fallback == "drop"):
            await self.report({"kind": "skipped", "reason": reason, "event_id": event.event_id})
            return
        if not event.utterance_id or not event.voice_id or not event.avatar_id:
            await self.report({"kind": "skipped", "reason": "missing_speech_identity"})
            return
        await self._caption(event, event.text)
        if not self._stale(event):
            await self._action("speech.reply", event.model_dump(mode="json"))
            await self.report({"kind": "routed", "reason": "fallback_live_voice" if event.reaction else "live_voice",
                               "fallback_reason": reason, "session_id": event.session_id,
                               "generation": event.generation, "event_id": event.event_id})

    async def _caption(self, event: HostOutput, text: str) -> None:
        if self.settings.lower_third:
            self._cancel_caption()
            await self._action("graphics.lower_third", {"visible": True,
                               "title": event.display_name[:100], "subtitle": text[:280]})
            self.caption_task = asyncio.create_task(self._hide_caption(self.caption_revision))

    def _cancel_caption(self) -> None:
        self.caption_revision += 1
        if self.caption_task is not None:
            self.caption_task.cancel()

    async def _hide_caption(self, revision: int) -> None:
        await asyncio.sleep(self.settings.captions_seconds)
        async with self.lock:
            if revision == self.caption_revision:
                await self._action("graphics.lower_third", {"visible": False})

    async def close(self) -> None:
        self._cancel_caption()
        if self.caption_task is not None:
            await asyncio.gather(self.caption_task, return_exceptions=True)
