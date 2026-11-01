"""Operator-owned bindings, separate from model/viewer content."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Name = Annotated[str, Field(min_length=1, max_length=200)]
Id = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    on_air_session: Id
    reaction_sounds: dict[Id, dict[Id, Id]] = Field(default_factory=dict)
    sound_hotkeys: dict[Id, Name] = Field(default_factory=dict)
    automation_triggers: dict[Literal["pause", "resume", "persona"], Id] = Field(
        default_factory=dict
    )
    stop_sound_hotkey: Optional[Name] = None
    pause_scene: Optional[Name] = None
    resume_scene: Optional[Name] = None
    ai_voice_input: Optional[Name] = None
    lower_third: bool = True
    captions_seconds: float = Field(default=8, ge=1, le=30)
    sound_cooldown_seconds: float = Field(default=20, ge=1, le=600)
    event_ttl_seconds: float = Field(default=15, ge=1, le=60)
    request_timeout_seconds: float = Field(default=3, ge=0.1, le=10)
    phrase_manifest: Optional[Path] = None
    phrase_fallback: Literal["live_voice", "drop"] = "live_voice"


class HostOutput(BaseModel):
    # Ignore descriptive host metadata, never treat it as an action request.
    model_config = ConfigDict(extra="ignore")
    schema_version: Literal[1]
    kind: Literal["reply", "control"]
    event_id: Id
    session_id: Id
    generation: int = Field(ge=0)
    created_at: datetime
    text: str = Field(default="", max_length=500)
    display_name: str = Field(default="", max_length=500)
    game_id: Optional[Id] = None
    reaction: Optional[Id] = None
    persona_id: Optional[Id] = None
    voice_id: Optional[Id] = None
    avatar_id: Optional[Id] = None
    utterance_id: Optional[str] = Field(default=None, max_length=256)
    # The host's P-066 delivery class. It can only withhold the Soundboard, never select a clip;
    # an absent value keeps legacy host output on the existing gaming path.
    audio_policy: Optional[
        Literal["gaming-reactive", "opentech-scripted", "technical-scripted", "review-scripted"]
    ] = None
    action: Optional[Literal["pause", "resume", "persona"]] = None
    paused: Optional[bool] = None

    @model_validator(mode="after")
    def require_fields(self) -> HostOutput:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must include timezone")
        if self.kind == "reply" and (not self.text.strip() or not self.game_id):
            raise ValueError("reply requires text and game_id")
        if self.kind == "control" and (self.action is None or self.paused is None):
            raise ValueError("control requires action and paused")
        if self.action == "pause" and self.paused is not True:
            raise ValueError("pause must set paused")
        if self.action == "resume" and self.paused is not False:
            raise ValueError("resume must clear paused")
        return self


def load_settings(path: Path, manifest: Path) -> Settings:
    """Verify selected sound slots against soundboard's existing asset registry."""
    config = Settings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if config.phrase_manifest is not None and not config.phrase_manifest.is_absolute():
        config.phrase_manifest = (path.parent / config.phrase_manifest).resolve()
    from .phrases import load
    load(config.phrase_manifest)
    entries = yaml.safe_load(manifest.read_text(encoding="utf-8"))["sounds"]
    slots = {entry["slot"] for entry in entries}
    selected = set(config.sound_hotkeys)
    selected.update(slot for routes in config.reaction_sounds.values() for slot in routes.values())
    if not selected <= slots:
        raise ValueError("director references a sound slot absent from soundboard's manifest")
    return config
