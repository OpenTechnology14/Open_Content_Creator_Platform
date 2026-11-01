"""Durable local revision review. Cross-module work uses JSON subprocess contracts."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import re
import struct
import time
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .process import call


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def atomic(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())
    schema_version: Literal[1]
    host_config: str
    speech_config: str
    max_phrase_words: int = Field(default=18, ge=1, le=50)
    max_phrase_seconds: float = Field(default=12, ge=1, le=30)
    max_candidates: int = Field(default=8, ge=1, le=8)
    render_timeout_seconds: float = Field(default=60, ge=1, le=120)
    model_timeout_seconds: float = Field(default=60, ge=1, le=120)
    ollama_url: str
    ollama_model: str = ""


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal[
        "status",
        "create",
        "revise",
        "preview",
        "cancel",
        "approve",
        "activate",
        "disable",
        "reject",
        "feedback",
        "audio",
        "export",
        "script_load",
        "script_play",
        "script_pause",
        "script_question",
        "script_answer",
        "script_resume",
        "script_stop",
    ]
    persona_id: str = Field(default="", pattern=r"^[a-zA-Z0-9_-]{0,64}$")
    revision_id: str = Field(default="", pattern=r"^[a-f0-9]{0,32}$")
    prompt: str = Field(default="", max_length=16000)
    feedback: str = Field(default="", max_length=2000)
    voice: str | None = Field(default=None, max_length=120)
    model: str = Field(default="", max_length=120)
    phrases: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    generate: bool = False
    asset_index: int = Field(default=0, ge=0, le=7)
    bindings: dict[str, str] = Field(default_factory=dict)
    stop_hotkey: str = Field(default="", max_length=200)
    acceptance_confirmed: bool = False
    # Explicit operator statement that local audio output is suitable for this session.
    monitor_confirmed: bool = False
    segments: list[str] = Field(default_factory=list, max_length=100)
    sources: str = Field(default="", max_length=20000)
    question: str = Field(default="", max_length=500)
    answer: str = Field(default="", max_length=500)


class Studio:
    def __init__(self, root: Path, library: Path, config: Path) -> None:
        self.root, self.library = root, library.resolve()
        self.settings = Settings.model_validate(yaml.safe_load(config.read_text()))
        self.library.mkdir(parents=True, exist_ok=True)
        self.path = self.library / "library.json"
        self.data = (
            json.loads(self.path.read_text())
            if self.path.exists()
            else {"schema_version": 1, "revisions": {}, "production": {}, "history": []}
        )
        if self.data.get("schema_version") != 1:
            raise ValueError("Unsupported phrase library schema")
        for revision in self.data["revisions"].values():
            if revision["status"] == "generating":
                revision.update(status="failed", error="Preview interrupted; revise and retry")
        self.task: asyncio.Task | None = None
        self.job_revision: str | None = None
        self.personas: dict = {}
        self.save()

    def save(self) -> None:
        atomic(self.path, self.data)

    async def author(self, data: dict) -> dict:
        return await call(
            self.root,
            "ai-agents",
            "stream_host.author",
            ["--config", str(self.root / self.settings.host_config)],
            data,
            self.settings.model_timeout_seconds + 5,
        )

    async def start(self) -> None:
        self.personas = await self.author({"action": "catalog"})
        from .script import ScriptPlayer

        self.script = ScriptPlayer(self)
        # The durable library is authoritative after an interrupted two-file export.
        try:
            self.export()
        except (ValueError, OSError, KeyError):
            atomic(self.library / "production.json", {"schema_version": 1, "profiles": {}})
            self.data["warning"] = (
                "Production assets changed; re-review or disable invalid selections"
            )

    def revision(self, ident: str) -> dict:
        if ident not in self.data["revisions"]:
            raise ValueError("Choose a saved revision")
        return self.data["revisions"][ident]

    def snapshot(self) -> dict:
        return {
            **self.data,
            "personas": self.personas,
            "library_path": str(self.library),
            "model": os.environ.get("OLLAMA_MODEL") or self.settings.ollama_model,
            "busy_revision": self.job_revision,
        }

    def check_phrases(self, phrases: list[dict], persona: dict) -> list[dict]:
        if not 1 <= len(phrases) <= self.settings.max_candidates:
            raise ValueError("Provide 1–8 phrases")
        host = yaml.safe_load((self.root / self.settings.host_config).read_text())
        blocked = host.get("blocked_terms", [])
        result = []
        for item in phrases:
            if set(item) != {"reaction", "text"}:
                raise ValueError("Each phrase needs only reaction and text")
            text = item["text"].strip()
            if item["reaction"] not in persona["catchphrases"]:
                raise ValueError("Reaction must be configured on the selected personality")
            if (
                not text
                or len(text) > 280
                or len(text.split()) > self.settings.max_phrase_words
                or re.search(r"https?://|\x00|free\s+v[-]?bucks|nitro\s+gift", text, re.I)
                or any(term.casefold() in text.casefold() for term in blocked)
            ):
                raise ValueError("Phrase violates configured length/content constraints")
            result.append({"reaction": item["reaction"], "text": text})
        return result

    async def create(self, request: Request) -> dict:
        parent = self.revision(request.revision_id) if request.action == "revise" else None
        persona_id = parent["persona_id"] if parent else request.persona_id
        persona = self.personas.get(persona_id)
        if not persona or persona["audio_policy"] != "gaming-reactive":
            raise ValueError("Choose a gaming Soundboard personality")
        if len(self.data["revisions"]) >= 64:
            raise ValueError(
                "Library revision limit reached; archive the library before continuing"
            )
        prepared = await self.author({"action": "prompt", "persona_id": persona_id, "feedback": ""})
        ident = uuid.uuid4().hex
        seeds = [
            {"reaction": reaction, "text": values[0]}
            for reaction, values in persona["catchphrases"].items()
        ][:8]
        voice_bindings = yaml.safe_load((self.root / self.settings.speech_config).read_text())[
            "voices"
        ]
        if persona["voice_id"] not in voice_bindings:
            raise ValueError("Personality has no approved voice binding")
        revision = {
            "id": ident,
            "persona_id": persona_id,
            "persona": persona,
            "context_hash": digest(persona),
            "parent_revision_id": parent["id"] if parent else None,
            "prompt": request.prompt or (parent["prompt"] if parent else prepared["prompt"]),
            "phrases": self.check_phrases(
                request.phrases or (parent["phrases"] if parent else seeds), persona
            ),
            "voice": request.voice
            if request.voice is not None
            else (parent["voice"] if parent else voice_bindings[persona["voice_id"]]),
            "model": os.environ.get("OLLAMA_MODEL")
            or request.model
            or (parent["model"] if parent else self.settings.ollama_model),
            "feedback": [{"text": request.feedback, "at": now()}] if request.feedback else [],
            "created_at": now(),
            "status": "draft",
            "assets": [],
            "error": "",
            "phrase_origin": "configured samples",
            "job_id": None,
        }
        if request.feedback:
            revision["prompt"] += "\nRevision feedback: " + request.feedback
        if len(revision["prompt"]) > 16000:
            raise ValueError("Prompt with feedback exceeds 16000 characters")
        self.data["revisions"][ident] = revision
        self.save()
        return revision

    async def render(self, revision: dict, generate: bool) -> None:
        started = time.monotonic()
        folder = self.library / revision["id"]
        try:
            folder.mkdir(exist_ok=False)
            if generate:
                result = await self.author(
                    {
                        "action": "generate",
                        "prompt": revision["prompt"],
                        "model": revision["model"],
                        "url": self.settings.ollama_url,
                        "timeout": self.settings.model_timeout_seconds,
                    }
                )
                revision["phrases"] = self.check_phrases(result["phrases"], revision["persona"])
                revision["phrase_origin"] = "Ollama"
            for index, phrase in enumerate(revision["phrases"]):
                path = folder / f"{index}.wav"
                await call(
                    self.root,
                    "audio-production",
                    "stream_speech.render",
                    ["render"],
                    {"text": phrase["text"], "voice": revision["voice"], "output": str(path)},
                    self.settings.render_timeout_seconds,
                )
                details = self.audio_details(path)
                if details["duration_seconds"] > self.settings.max_phrase_seconds:
                    raise ValueError("Phrase exceeds the configured audio duration")
                revision["assets"].append(
                    {**phrase, **details, "file": f"{revision['id']}/{index}.wav"}
                )
                revision["elapsed_seconds"] = round(time.monotonic() - started, 3)
                self.save()
            revision["status"] = "ready"
        except asyncio.CancelledError:
            revision.update(status="canceled", error="Preview canceled; revise to retry")
        except Exception as exc:
            revision.update(status="failed", error=str(exc)[:250])
        finally:
            revision["elapsed_seconds"] = round(time.monotonic() - started, 3)
            self.job_revision = None
            self.save()

    @staticmethod
    def audio_details(path: Path) -> dict:
        if path.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Audio exceeds 5 MiB")
        raw = path.read_bytes()
        with wave.open(str(path), "rb") as audio:
            if audio.getsampwidth() != 2 or audio.getnchannels() not in {1, 2}:
                raise ValueError("Expected 16-bit PCM mono/stereo WAV")
            samples = audio.readframes(audio.getnframes())
            duration = audio.getnframes() / audio.getframerate()
        peak = max((abs(x[0]) for x in struct.iter_unpack("<h", samples)), default=0)
        if peak == 0 or peak >= 32760 or duration <= 0:
            raise ValueError("Audio is silent, clipped or empty")
        return {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "duration_seconds": duration,
            "peak": round(peak / 32768, 5),
        }

    def asset_path(self, asset: dict) -> Path:
        path = (self.library / asset["file"]).resolve()
        if not path.is_relative_to(self.library) or path.is_symlink():
            raise ValueError("Invalid library file")
        if self.audio_details(path)["sha256"] != asset["sha256"]:
            raise ValueError("Audio changed since review; create a new revision")
        return path

    @staticmethod
    def review_hash(revision: dict) -> str:
        return digest(
            {
                key: revision[key]
                for key in (
                    "persona_id",
                    "context_hash",
                    "prompt",
                    "phrases",
                    "voice",
                    "model",
                    "assets",
                )
            }
        )

    def verify(self, revision: dict) -> None:
        if revision["status"] != "approved" or revision.get("approval_hash") != self.review_hash(
            revision
        ):
            raise ValueError("Approve this exact prompt/audio revision first")
        if digest(self.personas[revision["persona_id"]]) != revision["context_hash"]:
            raise ValueError("Personality context changed; create and review a new revision")
        for asset in revision["assets"]:
            self.asset_path(asset)

    def export(self) -> str:
        profiles = {}
        for persona_id, selected in self.data["production"].items():
            revision = self.revision(selected["revision_id"])
            self.verify(revision)
            profiles[persona_id] = {
                "revision_id": revision["id"],
                "game_id": revision["persona"]["game_id"],
                "voice_id": revision["persona"]["voice_id"],
                "stop_hotkey": selected["stop_hotkey"],
                "assets": [
                    {
                        **asset,
                        "file": str(self.asset_path(asset)),
                        "hotkey": selected["bindings"][str(index)],
                    }
                    for index, asset in enumerate(revision["assets"])
                ],
            }
        target = self.library / "production.json"
        atomic(target, {"schema_version": 1, "profiles": profiles})
        return str(target)

    async def handle(self, request: Request) -> dict:
        if request.action.startswith("script_"):
            return await self.script.handle(request)
        if request.action == "status":
            return self.snapshot()
        if request.action in {"create", "revise"}:
            revision = await self.create(request)
            return {"revision_id": revision["id"], **self.snapshot()}
        if request.action == "cancel":
            if self.task and self.job_revision == request.revision_id:
                await self.cancel_preview()
            return self.snapshot()
        if request.action == "export":
            return {"manifest": self.export(), **self.snapshot()}
        revision = self.revision(request.revision_id)
        if request.action == "preview":
            if self.task and not self.task.done():
                raise ValueError("Finish or cancel the current preview")
            if revision["status"] != "draft":
                raise ValueError("Create a new revision before rendering again")
            if request.generate and not (os.environ.get("OLLAMA_MODEL") or revision["model"]):
                raise ValueError("Choose an installed Ollama model and save the revision first")
            revision.update(status="generating", job_id=uuid.uuid4().hex)
            self.job_revision = revision["id"]
            self.save()
            self.task = asyncio.create_task(self.render(revision, request.generate))
        elif request.action == "feedback":
            if not request.feedback.strip():
                raise ValueError("Feedback is empty")
            if len(revision["feedback"]) >= 20:
                raise ValueError("Feedback limit reached")
            revision["feedback"].append({"text": request.feedback, "at": now()})
            self.save()
        elif request.action == "approve":
            if revision["status"] != "ready" or len(revision["assets"]) != len(revision["phrases"]):
                raise ValueError("Render and audition the complete revision first")
            if not request.acceptance_confirmed:
                raise ValueError("Confirm you reviewed the prompt, phrases and rendered audio")
            for asset in revision["assets"]:
                self.asset_path(asset)
            revision.update(
                status="approved", approved_at=now(), approval_hash=self.review_hash(revision)
            )
            self.save()
        elif request.action == "reject":
            if revision["status"] not in {"draft", "ready", "failed", "canceled"}:
                raise ValueError("Only unapproved, stopped revisions can be rejected")
            revision.update(status="rejected", rejected_at=now())
            self.save()
        elif request.action == "activate":
            self.verify(revision)
            if len(self.data["history"]) >= 1000:
                raise ValueError("Activation history limit reached; archive the library first")
            expected = {str(index) for index in range(len(revision["assets"]))}
            if (
                not request.acceptance_confirmed
                or set(request.bindings) != expected
                or not request.stop_hotkey.strip()
                or any(not value.strip() or len(value) > 200 for value in request.bindings.values())
            ):
                raise ValueError(
                    "Load/test each clip and stop control in OBS, then bind exact hotkey names"
                )
            if len(set(request.bindings.values())) != len(expected):
                raise ValueError("Each clip needs its own hotkey")
            if request.stop_hotkey in request.bindings.values():
                raise ValueError("Stop All must not share a clip's play hotkey")
            previous = self.data["production"].get(revision["persona_id"])
            selected = {
                "revision_id": revision["id"],
                "bindings": request.bindings,
                "stop_hotkey": request.stop_hotkey,
                "activated_at": now(),
            }
            self.data["production"][revision["persona_id"]] = selected
            try:
                self.export()
            except Exception:
                if previous:
                    self.data["production"][revision["persona_id"]] = previous
                else:
                    self.data["production"].pop(revision["persona_id"], None)
                raise
            self.data["history"].append(
                {"persona_id": revision["persona_id"], "previous": previous, "selected": selected}
            )
            self.save()
        elif request.action == "disable":
            previous = self.data["production"].pop(revision["persona_id"], None)
            try:
                self.export()
            except Exception:
                if previous:
                    self.data["production"][revision["persona_id"]] = previous
                raise
            self.save()
        elif request.action == "audio":
            if not request.monitor_confirmed:
                raise ValueError("Verify the audition output is isolated from the program mix")
            if request.asset_index >= len(revision["assets"]):
                raise ValueError("Sample is not ready")
            path = self.asset_path(revision["assets"][request.asset_index])
            return {"audio": base64.b64encode(path.read_bytes()).decode(), "mime": "audio/wav"}
        else:
            raise ValueError("Unsupported studio operation")
        return self.snapshot()

    async def cancel_preview(self) -> None:
        ident = self.job_revision
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        # A task canceled before its first turn never enters render's finally block.
        if ident and self.revision(ident)["status"] == "generating":
            self.revision(ident).update(
                status="canceled", error="Preview canceled; revise to retry"
            )
        self.job_revision = None
        self.save()

    async def close(self) -> None:
        await self.script.stop()
        await self.cancel_preview()
