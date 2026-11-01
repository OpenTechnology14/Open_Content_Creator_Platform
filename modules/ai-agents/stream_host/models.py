"""Versioned configuration and input contracts, independent of transport."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
ShortText = Annotated[str, Field(min_length=1, max_length=500)]
# P-066 delivery classes. Only `gaming-reactive` may reach the Soundboard; every scripted class
# speaks through the AI voice bus. The class belongs to the persona, never to the phrase text.
AudioPolicy = Literal[
    "gaming-reactive", "opentech-scripted", "technical-scripted", "review-scripted"
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Persona(Contract):
    game_id: Identifier
    display_name: ShortText
    system: str = Field(min_length=1, max_length=4000)
    voice_id: Identifier
    avatar_id: Identifier
    catchphrases: dict[Identifier, list[ShortText]] = Field(default_factory=dict)
    audio_policy: AudioPolicy = "gaming-reactive"

    @model_validator(mode="after")
    def bounded_phrases(self) -> Persona:
        if len(self.catchphrases) > 32 or any(
            not phrases or len(phrases) > 8 for phrases in self.catchphrases.values()
        ):
            raise ValueError("use at most 32 reaction types with 1–8 phrases each")
        return self


class SessionConfig(Contract):
    persona_id: Identifier
    # A label for deployment inventory; it does not launch or contact a VM.
    host_id: Identifier = "local"


class MainPersonality(Contract):
    display_name: ShortText
    system: str = Field(min_length=1, max_length=2000)
    voice_id: Identifier
    avatar_id: Identifier
    catchphrases: dict[Identifier, list[ShortText]] = Field(default_factory=dict)


class HostConfig(Contract):
    schema_version: Literal[1]
    main_personality: Optional[MainPersonality] = None
    personas: dict[Identifier, Persona]
    sessions: dict[Identifier, SessionConfig]
    queue_capacity: int = Field(default=16, ge=1, le=128)
    event_ttl_seconds: int = Field(default=15, ge=1, le=120)
    reply_timeout_seconds: float = Field(default=20, gt=0, le=120)
    catchphrase_cooldown_seconds: int = Field(default=180, ge=0, le=3600)
    max_reply_characters: int = Field(default=280, ge=40, le=500)
    history_turns: int = Field(default=4, ge=0, le=12)
    # Literal substrings, not user-supplied regexes. This is a basic filter only.
    blocked_terms: list[ShortText] = Field(default_factory=list, max_length=128)

    @model_validator(mode="before")
    @classmethod
    def inherit_identity(cls, data: object) -> object:
        """Fill game-mode identity fields from the core without mutating caller config."""
        if not isinstance(data, dict) or not isinstance(data.get("main_personality"), dict):
            return data
        core = data["main_personality"]
        if not isinstance(data.get("personas"), dict):
            return data
        profiles = {}
        for key, value in data["personas"].items():
            if not isinstance(value, dict):
                profiles[key] = value
                continue
            profile = dict(value)
            for field in ("display_name", "voice_id", "avatar_id"):
                if field in core:
                    profile.setdefault(field, core[field])
            profiles[key] = profile
        return {**data, "personas": profiles}

    @model_validator(mode="after")
    def references_exist(self) -> HostConfig:
        if not 1 <= len(self.personas) <= 32 or not 1 <= len(self.sessions) <= 8:
            raise ValueError("configure 1–32 personas and 1–8 sessions")
        if any(s.persona_id not in self.personas for s in self.sessions.values()):
            raise ValueError("session references an unknown persona")
        for key in self.personas:
            self.resolve_persona(key)
        return self

    def resolve_persona(self, persona_id: str) -> Persona:
        """Keep the main identity fixed while composing game-specific instructions/phrases."""
        persona = self.personas[persona_id]
        core = self.main_personality
        if core is None:
            return persona
        return Persona.model_validate(
            {
                **persona.model_dump(),
                "display_name": core.display_name,
                "voice_id": core.voice_id,
                "avatar_id": core.avatar_id,
                "system": f"{core.system}\nGame-specific variation:\n{persona.system}",
                "catchphrases": {**core.catchphrases, **persona.catchphrases},
            }
        )


class HostEvent(Contract):
    schema_version: Literal[1] = 1
    event_id: Identifier
    session_id: Identifier
    kind: Literal["chat", "game", "pause", "resume", "persona"]
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    text: str = Field(default="", max_length=500)
    user: str = Field(default="viewer", min_length=1, max_length=80)
    # Optional keeps Pydantic introspection usable in the legacy Python 3.9 offline harness.
    # The supported worker runtime remains Python 3.11+.
    reaction: Optional[Identifier] = None
    persona_id: Optional[Identifier] = None

    @model_validator(mode="after")
    def valid_payload(self) -> HostEvent:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        if self.kind == "chat" and not self.text.strip():
            raise ValueError("chat requires nonempty text")
        if self.kind == "game" and self.reaction is None:
            raise ValueError("game requires reaction")
        if self.kind == "persona" and self.persona_id is None:
            raise ValueError("persona change requires persona_id")
        return self


def load_config(path: Path) -> HostConfig:
    """Load operator-owned YAML and reject unknown fields or dangling references."""
    return HostConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
