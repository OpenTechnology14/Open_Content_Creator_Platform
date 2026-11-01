"""Create a deterministic lineup without scheduling or launching broadcasts."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Annotated, Literal, Optional
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9_-]{1,64}$")]
AudioPolicy = Literal[
    "gaming-reactive", "opentech-scripted", "technical-scripted", "review-scripted"
]
# P-066: which delivery classes each profile kind may declare. Marketing and review programs are
# scripted on AI-VOICE and must never reach the Soundboard.
PROFILE_AUDIO_POLICIES = {
    "game": {"gaming-reactive"},
    "marketing": {"opentech-scripted", "technical-scripted"},
    "video-review": {"review-scripted"},
}
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BuildProject(Contract):
    """Operator-maintained production brief shared by teaching and working episodes."""

    id: Identifier
    game_id: Identifier
    title: str = Field(min_length=1, max_length=100)
    deliverable: str = Field(min_length=1, max_length=500)
    stage: Literal["idea", "prototype", "building", "testing", "released", "deferred"] = "idea"
    next_step: str = Field(min_length=1, max_length=500)
    monetization_route: str = Field(min_length=1, max_length=500)
    readiness_notes: list[str] = Field(min_length=1, max_length=10)


class SourcePolicy(Contract):
    """Bound the material a profile may consume; URLs and shell commands are not inputs."""

    kind: Literal["game-runtime", "marketing-crosswalk", "operator-media"]
    allowed_refs: list[Identifier] = Field(min_length=1, max_length=16)
    rights_confirmation_required: bool = False
    artifact_root: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_./-]{1,256}$")
    artifact_prefixes: dict[Identifier, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_artifact_policy(self) -> SourcePolicy:
        if self.kind == "marketing-crosswalk":
            if self.artifact_root is None or set(self.artifact_prefixes) != set(self.allowed_refs):
                raise ValueError("marketing sources need a root and prefixes for every source ref")
            if Path(self.artifact_root).is_absolute() or ".." in Path(self.artifact_root).parts:
                raise ValueError("marketing artifact root must be workspace-relative")
            if any(
                not values
                or len(values) > 8
                or any(not value or "/" in value or "\\" in value for value in values)
                for values in self.artifact_prefixes.values()
            ):
                raise ValueError("marketing artifact prefixes must be bounded filename prefixes")
        elif self.artifact_root is not None or self.artifact_prefixes:
            raise ValueError("only marketing-crosswalk sources may configure artifact paths")
        return self


class YouTubeWorkflow(Contract):
    """A destination plan. Upload remains disabled until a separate reviewed adapter exists."""

    workflow_id: Identifier
    channel_env: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,127}$")
    visibility: Literal["private", "unlisted"] = "private"
    approval_required: Literal[True] = True
    upload_enabled: Literal[False] = False


class StreamProfile(Contract):
    id: Identifier
    display_name: str = Field(min_length=1, max_length=100)
    kind: Literal["game", "marketing", "video-review"]
    subject_id: Identifier
    persona_id: Identifier
    agent_control: Literal["experimental", "commentary-only"]
    audio_policy: AudioPolicy
    source: SourcePolicy
    # For marketing profiles this is the registered Marketing Crosswalk module ID, not a
    # repository label such as "opentechblog". Keeping the module binding on the show profile
    # makes the source contract directly addressable by the planner and downstream handoff.
    marketing_module_id: Optional[Identifier] = None
    marketing_target: Optional[Identifier] = None
    youtube: Optional[YouTubeWorkflow] = None

    @model_validator(mode="after")
    def valid_profile_policy(self) -> StreamProfile:
        expected_source = {
            "game": "game-runtime",
            "marketing": "marketing-crosswalk",
            "video-review": "operator-media",
        }[self.kind]
        if self.source.kind != expected_source:
            raise ValueError("profile kind and source policy do not match")
        if self.audio_policy not in PROFILE_AUDIO_POLICIES[self.kind]:
            raise ValueError("profile kind and audio policy do not match")
        if self.kind == "game" and self.youtube is not None:
            raise ValueError("game profiles use the normal broadcast destination configuration")
        if self.kind != "game" and self.youtube is None:
            raise ValueError("non-game profiles need a scoped YouTube workflow")
        if self.kind == "video-review" and not self.source.rights_confirmation_required:
            raise ValueError("video-review profiles must require rights confirmation")
        if self.kind == "marketing":
            if not self.marketing_module_id or not self.marketing_target:
                raise ValueError("marketing profiles need a module ID and target")
            if self.source.allowed_refs != [self.marketing_module_id]:
                raise ValueError("marketing profiles must bind exactly one registered module")
        elif self.marketing_module_id is not None or self.marketing_target is not None:
            raise ValueError("only marketing profiles may declare a marketing module")
        return self


class Show(Contract):
    id: Identifier
    game_id: Optional[Identifier] = None
    subject_id: Optional[Identifier] = None
    persona_id: Identifier
    title: str = Field(min_length=1, max_length=100)
    hook: str = Field(min_length=1, max_length=500)
    interaction_prompt: str = Field(min_length=1, max_length=500)
    clip_prompts: list[str] = Field(min_length=1, max_length=8)
    segments: list[str] = Field(min_length=1, max_length=8)
    duration_minutes: int = Field(ge=15, le=240)
    format: Literal["gameplay", "tutorial", "workshop", "marketing", "video-review"] = "gameplay"
    project_id: Optional[Identifier] = None
    profile_id: Optional[Identifier] = None

    @model_validator(mode="after")
    def valid_subject(self) -> Show:
        if (self.game_id is None) == (self.subject_id is None):
            raise ValueError("show needs exactly one game_id or non-game subject_id")
        if self.format in ("marketing", "video-review") and self.subject_id is None:
            raise ValueError("non-game shows need subject_id")
        if self.format not in ("marketing", "video-review") and self.game_id is None:
            raise ValueError("game shows need game_id")
        return self

    @property
    def scope_id(self) -> str:
        return self.game_id or self.subject_id or ""


class Program(Contract):
    schema_version: Literal[1, 2]
    timezone: str
    cycle_anchor: date
    primary_start: time
    secondary_start: time
    flagships: dict[str, list[Identifier]]
    rotation: list[Identifier] = Field(min_length=1, max_length=128)
    shows: list[Show] = Field(min_length=1, max_length=128)
    projects: list[BuildProject] = Field(default_factory=list, max_length=64)
    profiles: list[StreamProfile] = Field(default_factory=list, max_length=64)

    @model_validator(mode="after")
    def valid_program(self) -> Program:
        ZoneInfo(self.timezone)
        if self.cycle_anchor.weekday() != 0:
            raise ValueError("cycle_anchor must be a Monday")
        if self.primary_start.tzinfo or self.secondary_start.tzinfo:
            raise ValueError("use local wall times; the program supplies the timezone")
        if self.primary_start == self.secondary_start:
            raise ValueError("daily slots must have different start times")
        ids = {show.id for show in self.shows}
        if len(ids) != len(self.shows):
            raise ValueError("duplicate show id")
        if len(self.flagships) != 2 or any(day not in WEEKDAYS for day in self.flagships):
            raise ValueError("configure exactly two distinct flagship weekdays")
        if any(not values for values in self.flagships.values()):
            raise ValueError("each flagship day needs at least one show")
        refs = self.rotation + [ref for values in self.flagships.values() for ref in values]
        if any(ref not in ids for ref in refs):
            raise ValueError("lineup references an unknown show")
        if set(refs) != ids:
            raise ValueError("every show must be reachable from the lineup")
        projects = {project.id: project for project in self.projects}
        if len(projects) != len(self.projects):
            raise ValueError("duplicate project id")
        profiles = {profile.id: profile for profile in self.profiles}
        if len(profiles) != len(self.profiles):
            raise ValueError("duplicate stream profile id")
        if self.schema_version == 2 and not profiles:
            raise ValueError("schema version 2 needs stream profiles")
        for show in self.shows:
            if show.format in ("tutorial", "workshop") and show.project_id is None:
                raise ValueError("tutorial and workshop shows need a shared project")
            if show.format in ("marketing", "video-review") and show.profile_id is None:
                raise ValueError("non-game shows need a stream profile")
            if show.project_id is not None:
                project = projects.get(show.project_id)
                if project is None or project.game_id != show.game_id:
                    raise ValueError("show references an unknown or wrong-game project")
                if project.stage == "deferred":
                    raise ValueError("deferred projects cannot enter the lineup")
            if show.profile_id is not None:
                profile = profiles.get(show.profile_id)
                if profile is None:
                    raise ValueError("show references an unknown stream profile")
                if profile.persona_id != show.persona_id or profile.subject_id != show.scope_id:
                    raise ValueError("show and stream profile scope do not match")
                expected_format = {
                    "game": ("gameplay", "tutorial", "workshop"),
                    "marketing": ("marketing",),
                    "video-review": ("video-review",),
                }[profile.kind]
                if show.format not in expected_format:
                    raise ValueError("show format and stream profile kind do not match")
        return self


def load_program(path: Path) -> Program:
    """Read operator-owned programming configuration."""
    return Program.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def calendar(program: Program, start: date, days: int = 28, daily_slots: int = 1) -> list[dict]:
    """Return one or two draft shows daily; primary lineup stays stable when adding slot two."""
    if not 1 <= days <= 90 or daily_slots not in (1, 2) or start < program.cycle_anchor:
        raise ValueError("use 1–90 days, 1–2 daily slots and start on/after cycle_anchor")
    zone = ZoneInfo(program.timezone)
    shows = {show.id: show for show in program.shows}
    profiles = {profile.id: profile for profile in program.profiles}
    # Count non-flagship primary days since the stable anchor, independent of requested range.
    elapsed = (start - program.cycle_anchor).days
    weeks, remainder = divmod(elapsed, 7)
    rotation_index = weeks * 5 + sum(
        WEEKDAYS[day] not in program.flagships for day in range(remainder)
    )
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        week = (day - program.cycle_anchor).days // 7
        choices = program.flagships.get(WEEKDAYS[day.weekday()])
        if choices:
            primary = choices[week % len(choices)]
        else:
            primary = program.rotation[rotation_index % len(program.rotation)]
            rotation_index += 1
        slots = [(program.primary_start, primary, bool(choices), "primary")]
        if daily_slots == 2:
            index = (day - program.cycle_anchor).days % len(program.shows)
            secondary = program.shows[index].id
            if secondary == primary:
                secondary = program.shows[(index + 1) % len(program.shows)].id
            slots.append((program.secondary_start, secondary, False, "secondary"))
        daily = []
        for wall_time, show_id, flagship, slot in slots:
            begins = datetime.combine(day, wall_time, zone)
            roundtrip = begins.astimezone(timezone.utc).astimezone(zone)
            if roundtrip.replace(tzinfo=None) != begins.replace(tzinfo=None):
                raise ValueError("slot falls in a nonexistent daylight-saving time")
            if begins.replace(fold=1).utcoffset() != begins.replace(fold=0).utcoffset():
                raise ValueError("choose an unambiguous time outside the daylight-saving overlap")
            show = shows[show_id]
            ends = (
                begins.astimezone(timezone.utc) + timedelta(minutes=show.duration_minutes)
            ).astimezone(zone)
            daily.append(
                {
                    "episode_id": f"{day.isoformat()}-{slot}",
                    "show_id": show.id,
                    "game_id": show.game_id,
                    "subject_id": show.scope_id,
                    "persona_id": show.persona_id,
                    "title": show.title,
                    "starts_at": begins.isoformat(),
                    "ends_at": ends.isoformat(),
                    "flagship": flagship,
                    "status": "draft",
                    "shorts_requested": True,
                    "format": show.format,
                    "project_id": show.project_id,
                    "marketing_module_id": (
                        profiles[show.profile_id].marketing_module_id
                        if show.profile_id is not None
                        else None
                    ),
                    "project_brief": next(
                        (
                            project.model_dump()
                            for project in program.projects
                            if project.id == show.project_id
                        ),
                        None,
                    ),
                    "profile": (
                        profiles[show.profile_id].model_dump(mode="json")
                        if show.profile_id is not None
                        else None
                    ),
                }
            )
        daily.sort(key=lambda item: item["starts_at"])
        result.extend(daily)
    for previous, following in zip(result, result[1:]):
        if datetime.fromisoformat(previous["ends_at"]) > datetime.fromisoformat(
            following["starts_at"]
        ):
            raise ValueError("show slots overlap; adjust start times or durations")
    return result
