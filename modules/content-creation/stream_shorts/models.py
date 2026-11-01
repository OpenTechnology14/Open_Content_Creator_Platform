"""Recording-relative contracts; no platform credentials or raw chat text are needed."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Interaction(Contract):
    event_id: Identifier
    session_id: Identifier
    offset_seconds: float = Field(ge=0)
    user_key: Identifier
    kind: Literal["chat", "reaction", "poll_vote"] = "chat"
    eligible: bool = True
    is_bot: bool = False


class Section(Contract):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    label: str = Field(default="Selected moment", min_length=1, max_length=120)

    @model_validator(mode="after")
    def valid_range(self) -> Section:
        if not 0 < self.end_seconds - self.start_seconds <= 60:
            raise ValueError("sections must be longer than zero and at most 60 seconds")
        return self


class CaptionCue(Contract):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(min_length=1, max_length=240)

    @model_validator(mode="after")
    def valid_range(self) -> CaptionCue:
        if not 0 < self.end_seconds - self.start_seconds <= 20:
            raise ValueError("captions must be longer than zero and at most 20 seconds")
        return self


class PunchInCue(Contract):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    scale: float = Field(default=1.18, ge=1.05, le=1.5)
    focus_x: float = Field(default=0.5, ge=0, le=1)
    focus_y: float = Field(default=0.5, ge=0, le=1)
    event_id: Optional[Identifier] = None

    @model_validator(mode="after")
    def valid_range(self) -> PunchInCue:
        if not 0 < self.end_seconds - self.start_seconds <= 8:
            raise ValueError("punch-ins must be longer than zero and at most 8 seconds")
        return self


class EditStyle(Contract):
    background_color: str = Field(default="#101827", pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field(default="#B7F7DA", pattern=r"^#[0-9a-fA-F]{6}$")
    brand_title: str = Field(default="NOVA", min_length=1, max_length=48)
    watermark: str = Field(default="@nova", min_length=1, max_length=48)
    captions_enabled: bool = True
    normalize_audio: bool = True
    target_lufs: float = Field(default=-16, ge=-24, le=-10)


class EditSpec(Contract):
    enabled: bool = False
    style: EditStyle = Field(default_factory=EditStyle)
    captions: list[CaptionCue] = Field(default_factory=list, max_length=1000)
    punch_ins: list[PunchInCue] = Field(default_factory=list, max_length=200)


class ShortsJob(Contract):
    schema_version: Literal[1]
    recording_id: Identifier
    session_id: Identifier
    game_id: Identifier
    show_id: Identifier
    # Local media path is supplied separately by the operator to the render command.
    duration_seconds: float = Field(gt=0, le=86400)
    interactions: list[Interaction] = Field(default_factory=list, max_length=50000)
    manual_sections: list[Section] = Field(default_factory=list, max_length=20)
    excluded_sections: list[Section] = Field(default_factory=list, max_length=100)
    automatic: bool = True
    max_clips: int = Field(default=3, ge=1, le=20)
    clip_seconds: float = Field(default=30, ge=5, le=60)
    pre_roll_seconds: float = Field(default=8, ge=0, le=30)
    per_viewer_cap: int = Field(default=3, ge=1, le=10)
    edit: EditSpec = Field(default_factory=EditSpec)

    @model_validator(mode="after")
    def within_recording(self) -> ShortsJob:
        if self.pre_roll_seconds >= self.clip_seconds:
            raise ValueError("pre-roll must be shorter than automatic clips")
        for section in self.manual_sections + self.excluded_sections:
            if section.end_seconds > self.duration_seconds:
                raise ValueError("section extends beyond recording")
        if any(cue.end_seconds > self.duration_seconds for cue in self.edit.captions):
            raise ValueError("caption extends beyond recording")
        if any(cue.end_seconds > self.duration_seconds for cue in self.edit.punch_ins):
            raise ValueError("punch-in extends beyond recording")
        for section in self.manual_sections:
            if any(
                section.start_seconds < excluded.end_seconds
                and excluded.start_seconds < section.end_seconds
                for excluded in self.excluded_sections
            ):
                raise ValueError("manual section overlaps an excluded section")
        return self


class Clip(Section):
    clip_id: Identifier
    origin: Literal["manual", "interaction", "fallback"]
    score: float = Field(ge=0)
    unique_viewers: int = Field(ge=0)


class ClipPlan(Contract):
    schema_version: Literal[1] = 1
    recording_id: Identifier
    session_id: Identifier
    game_id: Identifier
    show_id: Identifier
    duration_seconds: float = Field(gt=0)
    ignored_events: int = Field(ge=0)
    clips: list[Clip]
    edit: EditSpec = Field(default_factory=EditSpec)

    @model_validator(mode="after")
    def valid_clips(self) -> ClipPlan:
        if len(self.clips) > 40 or len({clip.clip_id for clip in self.clips}) != len(self.clips):
            raise ValueError("clip IDs must be unique; at most 40 clips")
        if any(clip.end_seconds > self.duration_seconds for clip in self.clips):
            raise ValueError("clip extends beyond recording")
        if any(cue.end_seconds > self.duration_seconds for cue in self.edit.captions):
            raise ValueError("caption extends beyond recording")
        if any(cue.end_seconds > self.duration_seconds for cue in self.edit.punch_ins):
            raise ValueError("punch-in extends beyond recording")
        return self
