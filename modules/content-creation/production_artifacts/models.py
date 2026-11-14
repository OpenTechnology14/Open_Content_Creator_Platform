"""Candidate strict schema1 local export wire contract; independent review pending. No capture or publication authority."""

from __future__ import annotations

from typing import Annotated, Literal
from fractions import Fraction
import re
from pydantic import AfterValidator, BeforeValidator, BaseModel, ConfigDict, Field, model_validator

ID = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
RelativePath = Annotated[
    str, Field(pattern=r"^[a-zA-Z0-9_-]+(?:[./][a-zA-Z0-9_-]+)*$", max_length=512)
]


PORTABLE_FORBIDDEN = (
    r"(?:[a-zA-Z][a-zA-Z0-9+.-]*://|(?:[fF][iI][lL][eE]|[mM][aA][iI][lL][tT][oO]|[dD][aA][tT][aA]):|"
    r"[\x00-\x08\x0b\x0c\x0e-\x1f])"
)


def portable_text(value: str) -> str:
    if re.search(PORTABLE_FORBIDDEN, value):
        raise ValueError("portable metadata cannot contain URLs or control data")
    return value


Title = Annotated[
    str,
    Field(
        min_length=1,
        max_length=120,
        json_schema_extra={"format": "portable-text-v1", "not": {"pattern": PORTABLE_FORBIDDEN}},
    ),
    AfterValidator(portable_text),
]
Description = Annotated[
    str,
    Field(
        max_length=5000,
        json_schema_extra={"format": "portable-text-v1", "not": {"pattern": PORTABLE_FORBIDDEN}},
    ),
    AfterValidator(portable_text),
]


def false_only(value: object) -> bool:
    if value is not False:
        raise ValueError("the plain export preset requires literal false")
    return False


FalseValue = Annotated[Literal[False], BeforeValidator(false_only)]
Revision = Annotated[int, Field(ge=1, le=2147483647)]
Timestamp = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")]
Preset = Literal["youtube-longform-v1", "youtube-shorts-v1", "tiktok-local-v1"]
ErrorCode = Literal[
    "artifact_unavailable",
    "cancelled",
    "corrupt_state",
    "dependency_unavailable",
    "disk_space",
    "disk_unavailable",
    "export_busy",
    "execution_unsettled",
    "invalid_media",
    "invalid_registry",
    "invalid_request",
    "job_not_owned",
    "job_unavailable",
    "limit_exceeded",
    "media_failed",
    "media_limit",
    "operation_conflict",
    "persistence_failed",
    "plan_conflict",
    "platform_unavailable",
    "process_timeout",
    "production_unavailable",
    "profile_conflict",
    "revision_conflict",
    "source_changed",
    "source_unavailable",
    "terminal_attempt",
    "unsafe_path",
    "worker_busy",
    "worker_restarted",
]
Phase = Literal[
    "queued",
    "validating",
    "rendering",
    "validating-output",
    "complete",
    "partial",
    "failed",
    "cancelled",
    "interrupted",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, strict=True)


class Reference(Contract):
    id: ID
    sha256: SHA


class ConceptReference(Reference):
    revision: Revision


class Target(Contract):
    kind: Literal["opentechnologyapp"]
    commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    tree_sha256: SHA
    fixture_sha256: SHA
    scenario_id: ID


class Create(Contract):
    operation_id: ID
    source_profile_id: ID
    content_profile_id: ID
    show_profile_id: ID
    content_root_id: ID
    target: Target
    concept_ref: ConceptReference | None = None
    script_sha256: SHA | None = None


class ProductionSessionV1(Contract):
    schema_version: Literal[1] = 1
    production_id: ID
    revision: Revision
    created_at: Timestamp
    source_profile_id: ID
    content_profile_id: ID
    show_profile_id: ID
    content_root_id: ID
    target: Target
    concept_ref: ConceptReference | None = None
    script_sha256: SHA | None = None
    source_ids: list[ID] = Field(default_factory=list, max_length=100)
    export_attempt_ids: list[ID] = Field(default_factory=list, max_length=100)


class Video(Contract):
    codec: ID
    width: int = Field(ge=2, le=7680)
    height: int = Field(ge=2, le=4320)
    sar_num: int = Field(ge=1, le=65535)
    sar_den: int = Field(ge=1, le=65535)
    fps_num: int = Field(ge=1, le=240000)
    fps_den: int = Field(ge=1, le=10000)
    pixel_format: ID

    @property
    def display_aspect(self) -> Fraction:
        """Exact derived DAR; never infer square pixels from storage dimensions."""
        return Fraction(self.width * self.sar_num, self.height * self.sar_den)


class Audio(Contract):
    codec: ID
    sample_rate: int = Field(ge=8000, le=192000)
    channels: int = Field(ge=1, le=8)
    duration_seconds: float = Field(gt=0, le=86400)


class Media(Contract):
    container: Literal["mp4", "matroska", "mov", "webm"]
    video: Video
    audio: Audio
    duration_seconds: float = Field(gt=0, le=86400)


class Validation(Contract):
    validator_version: Literal["ffmpeg-full-v1"] = "ffmpeg-full-v1"
    full_decode: Literal[True] = True
    validated_at: Timestamp


class Provenance(Contract):
    fixture_recipe_sha256: SHA | None = None


class FinalizedSourceV1(Media):
    schema_version: Literal[1] = 1
    source_id: ID
    production_id: ID
    origin: Literal["manual", "fixture"]
    inbox_record_id: ID | None = None
    source_profile_id: ID
    content_profile_id: ID
    root_id: ID
    relative_path: RelativePath
    sha256: SHA
    bytes: int = Field(gt=0, le=1024**4)
    validation: Validation
    provenance: Provenance = Field(default_factory=Provenance)


class SourceRegister(Contract):
    production_id: ID
    expected_revision: Revision
    operation_id: ID
    input_id: ID
    source_sha256: SHA
    source_profile_id: ID
    content_profile_id: ID
    origin: Literal["manual", "fixture"]
    inbox_record_id: ID | None = None
    provenance: Provenance = Field(default_factory=Provenance)


class PlainEditV1(Contract):
    enabled: FalseValue = False


class ExportSectionV1(Contract):
    start_seconds: float = Field(ge=0, le=86400)
    end_seconds: float = Field(gt=0, le=86400)
    label: Title = "Selected moment"

    @model_validator(mode="after")
    def bounded_range(self) -> ExportSectionV1:
        if not 0 < self.end_seconds - self.start_seconds <= 60:
            raise ValueError("invalid manual range")
        return self


class ExportJobV1(Contract):
    schema_version: Literal[1]
    recording_id: ID
    session_id: ID
    game_id: Literal["walkthrough"]
    show_id: ID
    duration_seconds: float = Field(gt=0, le=86400)
    automatic: FalseValue = False
    manual_sections: list[ExportSectionV1] = Field(min_length=1, max_length=1)
    edit: PlainEditV1 = Field(default_factory=PlainEditV1)


class ExportClipV1(ExportSectionV1):
    clip_id: Literal["clip-001"]
    origin: Literal["manual"]
    score: float = Field(ge=0, le=0)
    unique_viewers: int = Field(ge=0, le=0)


class ExportClipPlanV1(Contract):
    schema_version: Literal[1] = 1
    recording_id: ID
    session_id: ID
    game_id: Literal["walkthrough"]
    show_id: ID
    duration_seconds: float = Field(gt=0, le=86400)
    ignored_events: int = Field(ge=0, le=0)
    clips: list[ExportClipV1] = Field(min_length=1, max_length=1)
    edit: PlainEditV1 = Field(default_factory=PlainEditV1)

    @model_validator(mode="after")
    def exact_plain_range(self) -> ExportClipPlanV1:
        clip = self.clips[0]
        if (
            clip.start_seconds != 2
            or clip.end_seconds != 10
            or clip.end_seconds > self.duration_seconds
        ):
            raise ValueError("initial plain preset uses manual 2..10 seconds")
        return self


class PlanRegister(Contract):
    production_id: ID
    expected_revision: Revision
    operation_id: ID
    source_id: ID
    job: ExportJobV1


class ExportRequestV1(Contract):
    production_id: ID
    expected_revision: Revision
    source_id: ID
    source_sha256: SHA
    operation_id: ID
    presets: list[Preset] = Field(min_length=1, max_length=3)
    clip_plan_ref: Reference
    metadata_revision: Revision

    @model_validator(mode="after")
    def unique_presets(self) -> ExportRequestV1:
        if len(set(self.presets)) != len(self.presets):
            raise ValueError("duplicate preset")
        return self


class Metadata(Contract):
    schema_version: Literal[1] = 1
    title: Title
    description: Description
    start_seconds: float = Field(ge=0, le=86400)
    end_seconds: float = Field(gt=0, le=86400)
    timebase: Literal["source-seconds"] = "source-seconds"
    preset_version: Preset
    metadata_revision: Revision


class PlanRecord(Contract):
    schema_version: Literal[1] = 1
    id: ID
    sha256: SHA
    production_id: ID
    source_id: ID
    clip_plan: ExportClipPlanV1
    title: Title
    description: Description
    metadata_revision: Revision


class PlanPayload(PlanRegister):
    title: Title
    description: Description
    metadata_revision: Revision


class ArtifactV1(Contract):
    schema_version: Literal[1] = 1
    artifact_id: ID
    attempt_id: ID
    source_id: ID
    destination: Literal["youtube-longform", "youtube-shorts", "tiktok"]
    relative_path: RelativePath
    metadata_path: RelativePath
    metadata_sha256: SHA
    sha256: SHA
    bytes: int = Field(gt=0, le=1024**4)
    media: Media
    preset_version: Preset
    editorial_state: Literal["review-needed"] = "review-needed"
    local_state: Literal["validated"] = "validated"


class Failure(Contract):
    preset: Preset
    error_code: ErrorCode


class ExportAttemptV1(Contract):
    schema_version: Literal[1] = 1
    attempt_id: ID
    job_id: ID
    production_id: ID
    source_id: ID
    source_sha256: SHA
    plan_sha256: SHA
    preset_version: Literal["local-presets-v1"] = "local-presets-v1"
    metadata_revision: Revision
    requested_output_ids: list[Preset] = Field(min_length=1, max_length=3)
    phase: Phase
    started_at: Timestamp
    ended_at: Timestamp | None = None
    artifacts: list[ArtifactV1] = Field(default_factory=list, max_length=3)
    failures: list[Failure] = Field(default_factory=list, max_length=3)
    process_epoch: ID
    generation: int = Field(ge=1)
    sequence: int = Field(ge=0)
    error_code: ErrorCode | None = None


class Progress(Contract):
    completed: int = Field(ge=0, le=3)
    total: int = Field(ge=1, le=3)
    unit: Literal["outputs"] = "outputs"

    @model_validator(mode="after")
    def bounded(self) -> Progress:
        if self.completed > self.total:
            raise ValueError("progress exceeds total")
        return self


class JobEventV1(Contract):
    schema_version: Literal[1] = 1
    event_id: ID
    production_id: ID
    job_id: ID
    attempt_id: ID
    process_epoch: ID
    generation: int = Field(ge=1)
    sequence: int = Field(ge=1)
    kind: Literal["job.event.v1"] = "job.event.v1"
    phase: Phase
    elapsed_ms: int = Field(ge=0)
    progress: Progress
    error_code: ErrorCode | None = None


class RequestV1(Contract):
    schema_version: Literal[1]
    request_id: ID
    command: Literal[
        "production.create",
        "production.list",
        "production.get",
        "source.register",
        "plan.register",
        "export.start",
        "job.get",
        "job.cancel",
        "artifact.inspect",
    ]
    payload: dict


class Get(Contract):
    production_id: ID


class JobGet(Get):
    job_id: ID


class JobCancel(JobGet):
    expected_revision: Revision
    operation_id: ID


class ArtifactGet(Get):
    artifact_id: ID


class Page(Contract):
    cursor: int = Field(default=0, ge=0, le=1000)
    limit: int = Field(default=100, ge=1, le=100)


WIRE_MODELS = {
    c.__name__: c
    for c in [
        ProductionSessionV1,
        Video,
        FinalizedSourceV1,
        ExportRequestV1,
        ExportAttemptV1,
        ArtifactV1,
        JobEventV1,
        RequestV1,
        Create,
        SourceRegister,
        PlanPayload,
        PlanRecord,
        ExportJobV1,
        PlainEditV1,
        ExportSectionV1,
        ExportClipV1,
        ExportClipPlanV1,
        Metadata,
        Get,
        JobGet,
        JobCancel,
        ArtifactGet,
        Page,
    ]
}


def schema_bundle() -> dict:
    """Generate deterministic schemas consumed by the later Rust/TS slice."""
    return {name: model.model_json_schema() for name, model in WIRE_MODELS.items()}


class ErrorV1(Contract):
    code: ErrorCode
    retryable: bool


class ReplyV1(Contract):
    request_id: ID | None
    ok: bool
    revision: Revision | None = None
    value: dict | None = None
    error: ErrorV1 | None = None

    @model_validator(mode="after")
    def envelope(self) -> ReplyV1:
        if self.ok != (self.value is not None) or self.ok == (self.error is not None):
            raise ValueError("reply must contain exactly a value or error")
        return self


WIRE_MODELS.update({"ReplyV1": ReplyV1, "ErrorV1": ErrorV1})
