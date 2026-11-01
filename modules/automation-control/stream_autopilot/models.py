"""Validated operator policy and persisted lifecycle contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
Lifecycle = Literal["stopped", "preflight", "preview", "running", "paused", "degraded"]
Action = Literal["preflight", "preview", "run", "pause", "resume", "stop", "emergency_stop"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CapabilityCheck(Contract):
    id: Identifier
    status: Literal["ready", "missing", "degraded"]
    required: bool = True
    detail: str = Field(min_length=1, max_length=500)


class SessionPolicy(Contract):
    persona_id: Identifier
    game_id: Identifier
    mode: Literal["cohost", "autonomous"] = "cohost"
    enabled: bool = True
    broadcast_start_authorized: bool = False
    local_run_authorized: bool = False
    gameplay_enabled: bool = False

    @model_validator(mode="after")
    def safe_gameplay(self) -> SessionPolicy:
        if self.mode == "autonomous" and not self.gameplay_enabled:
            raise ValueError("autonomous mode requires an explicitly enabled gameplay adapter")
        return self


class SupervisorConfig(Contract):
    schema_version: Literal[1]
    max_concurrent_running: int = Field(default=1, ge=1, le=8)
    emergency_timeout_seconds: float = Field(default=0.25, gt=0, le=5)
    operation_history: int = Field(default=64, ge=8, le=256)
    sessions: dict[Identifier, SessionPolicy] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def valid_budget(self) -> SupervisorConfig:
        enabled = sum(session.enabled for session in self.sessions.values())
        if not enabled:
            raise ValueError("enable at least one session")
        if self.max_concurrent_running > enabled:
            raise ValueError("running-session budget exceeds enabled sessions")
        return self


class SessionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: Identifier
    lifecycle: Lifecycle = "stopped"
    previous_lifecycle: Optional[Lifecycle] = None
    revision: int = Field(default=0, ge=0)
    checks: list[CapabilityCheck] = Field(default_factory=list, max_length=64)
    ready: bool = False
    resume_required: bool = False
    last_error: Optional[str] = Field(default=None, max_length=500)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OperationRecord(Contract):
    operation_id: Identifier
    session_id: Identifier
    action: Action
    revision: int = Field(ge=0)
    # Optional permits loading the first local development snapshot written before exact
    # idempotent-result replay was added.
    result: Optional[SessionSnapshot] = None


class SupervisorSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    sessions: dict[Identifier, SessionSnapshot]
    operations: list[OperationRecord] = Field(default_factory=list, max_length=256)


def load_config(path: Path) -> SupervisorConfig:
    """Read the lifecycle policy without accepting unknown fields."""
    return SupervisorConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
