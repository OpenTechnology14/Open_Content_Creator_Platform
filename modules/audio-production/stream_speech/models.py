"""Validated speech input and operator-owned playback settings."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import yaml
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,128}$")]
UtteranceIdentifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,256}$")]

CLONING_ENGINES = frozenset({"chatterbox", "f5-tts", "xtts-v2"})


def _repo_relative(value: str) -> str:
    if (
        not value
        or "\0" in value
        or "\\" in value
        or value.startswith("/")
        or (len(value) > 1 and value[1] == ":")
    ):
        raise ValueError("must be a relative path written with forward slashes")
    if ".." in value.split("/"):
        raise ValueError("must not contain '..'")
    return value


RelativePath = Annotated[str, Field(max_length=260), AfterValidator(_repo_relative)]


class LocalVoice(BaseModel):
    """A voice rendered by a local TTS engine instead of the operating system (P-068).

    Paths are repository-relative so one config works on every workstation. `revision` is folded
    into the render-cache key: change it when the weights or engine settings change, because the
    weights themselves are far too large to hash on every line.
    """

    # `model_path` is the config key P-068 specifies; pydantic reserves the `model_` prefix.
    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())
    provider: Literal["local"]
    engine: Literal["chatterbox", "f5-tts", "xtts-v2", "kokoro"]
    model_path: RelativePath
    speaker_ref: Optional[RelativePath] = None
    sample_rate: int = Field(default=48000, ge=8000, le=96000)
    revision: str = Field(default="", max_length=64, pattern=r"^[a-zA-Z0-9._-]*$")

    @model_validator(mode="after")
    def reference_matches_engine(self) -> LocalVoice:
        if self.engine in CLONING_ENGINES and self.speaker_ref is None:
            raise ValueError(f"{self.engine} clones from a reference recording; set speaker_ref")
        if self.engine not in CLONING_ENGINES and self.speaker_ref is not None:
            raise ValueError(f"{self.engine} has pre-built voices only; remove speaker_ref")
        return self


# None is the operating-system default voice, a string names an operating-system voice.
Voice = Union[None, str, LocalVoice]


class SpeechSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    on_air_session: Identifier
    queue_capacity: int = Field(default=2, ge=1, le=8)
    event_ttl_seconds: float = Field(default=15, ge=1, le=60)
    output_directory: Path
    retain_wav: bool = False
    reply_source: Literal["stream-host", "stream-director"] = "stream-host"
    voices: dict[Identifier, Voice] = Field(min_length=1, max_length=32)
    render_cache_directory: Optional[Path] = None


class SpeechEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    schema_version: Literal[1]
    kind: Literal["reply", "control"]
    event_id: Identifier
    session_id: Identifier
    generation: int = Field(ge=0)
    created_at: datetime
    utterance_id: Optional[UtteranceIdentifier] = None
    text: str = Field(default="", max_length=500)
    voice_id: Optional[Identifier] = None
    avatar_id: Optional[Identifier] = None
    action: Optional[Literal["pause", "resume", "persona"]] = None
    paused: Optional[bool] = None

    @model_validator(mode="after")
    def complete_event(self) -> SpeechEvent:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must include timezone")
        if self.kind == "reply":
            if (
                not self.utterance_id
                or not self.text.strip()
                or not self.voice_id
                or not self.avatar_id
            ):
                raise ValueError("reply requires utterance, text, voice and avatar")
        elif self.action is None or self.paused is None:
            raise ValueError("control requires action and paused state")
        if self.action == "pause" and self.paused is not True:
            raise ValueError("pause must set paused")
        if self.action == "resume" and self.paused is not False:
            raise ValueError("resume must clear paused")
        return self


def load_settings(path: Path) -> SpeechSettings:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SpeechSettings.model_validate(value)
