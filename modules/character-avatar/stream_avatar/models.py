"""Validated speech timing events and avatar hotkey bindings."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Cue = Literal["wave", "nod", "shrug", "look_left", "look_right", "happy", "surprised", "neutral"]

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,256}$")]


class AvatarBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    talk_hotkey: str = Field(min_length=1, max_length=200)
    idle_hotkey: str = Field(min_length=1, max_length=200)
    vts_model_id: str | None = Field(default=None, min_length=1, max_length=128)
    cues: dict[Cue, str] = Field(default_factory=dict, max_length=8)

    @model_validator(mode="after")
    def body_only(self):
        if any(
            not value or len(value) > 200 or value in {self.talk_hotkey, self.idle_hotkey}
            for value in self.cues.values()
        ):
            raise ValueError("body cues need distinct, bounded body-only hotkey IDs")
        return self


class AvatarSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    on_air_session: Identifier
    event_ttl_seconds: float = Field(default=15, ge=1, le=60)
    vts_url: str = Field(pattern=r"^wss?://[^/?#]+(?::[0-9]+)?$")
    avatars: dict[Identifier, AvatarBinding] = Field(min_length=1, max_length=16)
    full_body_enabled: bool = False
    speech_cues: list[Cue] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def complete_body_bindings(self):
        if self.full_body_enabled:
            required = {
                "wave",
                "nod",
                "shrug",
                "look_left",
                "look_right",
                "happy",
                "surprised",
                "neutral",
            }
            if any(
                not value.vts_model_id or set(value.cues) != required
                for value in self.avatars.values()
            ):
                raise ValueError("bind the owned current model and all full-body cues")
        elif self.speech_cues:
            raise ValueError("automatic body cues require full_body_enabled")
        return self


class AvatarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    schema_version: Literal[1]
    kind: Literal["started", "finished", "canceled", "failed", "controlled"]
    event_id: Identifier
    session_id: Identifier
    generation: int = Field(ge=0)
    created_at: datetime
    utterance_id: Optional[Identifier] = None
    avatar_id: Optional[Identifier] = None
    paused: Optional[bool] = None

    @model_validator(mode="after")
    def required_fields(self) -> AvatarEvent:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must include timezone")
        if self.kind in {"started", "finished", "canceled"} and (
            not self.utterance_id or not self.avatar_id
        ):
            raise ValueError("playback event requires utterance and avatar")
        if self.kind == "controlled" and self.paused is None:
            raise ValueError("controlled event requires paused")
        return self


def load_settings(path: Path) -> AvatarSettings:
    return AvatarSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


class AvatarCueEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    kind: Literal["cue"]
    event_id: Identifier
    session_id: Identifier
    avatar_id: Identifier
    cue: Cue
    created_at: datetime

    @model_validator(mode="after")
    def aware(self):
        if self.created_at.tzinfo is None:
            raise ValueError("cue time must include timezone")
        return self
