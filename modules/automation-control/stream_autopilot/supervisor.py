"""Fail-closed session lifecycle with durable recovery and idempotent operations."""

from __future__ import annotations

import asyncio
import os
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import (
    Action,
    CapabilityCheck,
    OperationRecord,
    SessionPolicy,
    SessionSnapshot,
    SupervisorConfig,
    SupervisorSnapshot,
)


class SessionDriver(Protocol):
    """Implement local effects; viewer content never reaches this boundary."""

    async def preflight(self, session_id: str, policy: SessionPolicy) -> list[CapabilityCheck]: ...

    async def preview(self, session_id: str, policy: SessionPolicy) -> None: ...

    async def run(self, session_id: str, policy: SessionPolicy) -> None: ...

    async def pause(self, session_id: str, policy: SessionPolicy) -> None:
        """Silence AI output and release any game input before returning."""
        ...

    async def stop(self, session_id: str, policy: SessionPolicy) -> None:
        """Stop this session's resources and release any game input."""
        ...


class TransitionRejected(ValueError):
    """The requested state change is invalid; the current runtime state stays authoritative."""


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, config: SupervisorConfig) -> SupervisorSnapshot:
        if self.path.is_file():
            snapshot = SupervisorSnapshot.model_validate_json(self.path.read_text(encoding="utf-8"))
        else:
            snapshot = SupervisorSnapshot(
                sessions={key: SessionSnapshot(session_id=key) for key in config.sessions}
            )
        if set(snapshot.sessions) != set(config.sessions):
            raise ValueError("saved supervisor sessions do not match configured sessions")
        # A process restart cannot prove old workers, audio, input or OBS state.
        for session in snapshot.sessions.values():
            if session.lifecycle in {"preflight", "running", "paused", "degraded"}:
                session.previous_lifecycle = session.lifecycle
                session.lifecycle = "preview" if session.ready else "stopped"
                session.ready = False
                session.checks = []
                session.resume_required = True
                session.last_error = "runtime restarted; verify preview before resuming"
                session.revision += 1
                session.updated_at = datetime.now(timezone.utc)
        return snapshot

    def save(self, snapshot: SupervisorSnapshot) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(snapshot.model_dump_json(indent=2) + "\n", encoding="utf-8")
        if os.name != "nt":
            temporary.chmod(0o600)
        temporary.replace(self.path)


class SessionSupervisor:
    """Own lifecycle state while injected drivers own concrete local effects."""

    def __init__(self, config: SupervisorConfig, driver: SessionDriver, state_path: Path) -> None:
        self.config = config
        self.driver = driver
        self.store = StateStore(state_path)
        self.snapshot = self.store.load(config)
        self.operations = OrderedDict(
            (record.operation_id, record) for record in self.snapshot.operations
        )
        self.lock = asyncio.Lock()
        self.store.save(self.snapshot)

    def status(self, session_id: str | None = None) -> dict:
        if session_id is not None:
            return self._session(session_id).model_dump(mode="json")
        return self.snapshot.model_dump(mode="json")

    def _session(self, session_id: str) -> SessionSnapshot:
        if session_id not in self.config.sessions:
            raise ValueError("unknown session")
        if not self.config.sessions[session_id].enabled:
            raise ValueError("session is disabled")
        return self.snapshot.sessions[session_id]

    def _remember(self, operation_id: str, session_id: str, action: Action) -> None:
        session = self._session(session_id)
        record = OperationRecord(
            operation_id=operation_id,
            session_id=session_id,
            action=action,
            revision=session.revision,
            result=session.model_copy(deep=True),
        )
        self.operations[operation_id] = record
        while len(self.operations) > self.config.operation_history:
            self.operations.popitem(last=False)
        self.snapshot.operations = list(self.operations.values())

    def _existing(self, operation_id: str, session_id: str, action: Action) -> dict | None:
        previous = self.operations.get(operation_id)
        if previous is None:
            return None
        if previous.session_id != session_id or previous.action != action:
            raise ValueError("operation id was already used for a different request")
        if previous.result is not None:
            return previous.result.model_dump(mode="json")
        return self.status(session_id)

    def _set(
        self,
        session: SessionSnapshot,
        lifecycle: str,
        *,
        error: str | None = None,
        resume_required: bool = False,
    ) -> None:
        session.previous_lifecycle = session.lifecycle
        session.lifecycle = lifecycle
        session.last_error = error
        session.resume_required = resume_required
        session.revision += 1
        session.updated_at = datetime.now(timezone.utc)

    async def apply(self, session_id: str, action: Action, operation_id: str) -> dict:
        """Apply one operator action with a caller-supplied idempotency key."""
        if (
            not operation_id
            or len(operation_id) > 64
            or not all(character.isalnum() or character in "_-" for character in operation_id)
        ):
            raise ValueError(
                "operation id must contain 1-64 letters, numbers, underscores or hyphens"
            )
        async with self.lock:
            existing = self._existing(operation_id, session_id, action)
            if existing is not None:
                return existing
            session = self._session(session_id)
            policy = self.config.sessions[session_id]
            try:
                await self._transition(session_id, session, policy, action)
            except asyncio.CancelledError:
                self._set(
                    session,
                    "degraded",
                    error="operation interrupted; reconcile effects before resume",
                )
                self.store.save(self.snapshot)
                raise
            except TransitionRejected:
                raise
            except Exception as exc:
                self._set(session, "degraded", error=f"{action} failed: {type(exc).__name__}")
            self._remember(operation_id, session_id, action)
            self.store.save(self.snapshot)
            return self.status(session_id)

    async def _transition(
        self,
        session_id: str,
        session: SessionSnapshot,
        policy: SessionPolicy,
        action: Action,
    ) -> None:
        if action == "preflight":
            self._set(session, "preflight")
            checks = await self.driver.preflight(session_id, policy)
            ids = [check.id for check in checks]
            if len(ids) != len(set(ids)):
                raise ValueError("preflight returned duplicate capability ids")
            session.checks = checks
            required = [check for check in checks if check.required]
            session.ready = bool(required) and all(check.status == "ready" for check in required)
            if not session.ready:
                self._set(session, "degraded", error="required capabilities are unavailable")
            return
        if action == "preview":
            if not session.ready or session.lifecycle not in {"preflight", "preview", "degraded"}:
                raise TransitionRejected("complete a successful preflight before preview")
            await self.driver.preview(session_id, policy)
            self._set(session, "preview")
            return
        if action == "run":
            if session.lifecycle != "preview" or session.resume_required:
                raise TransitionRejected("verify preview before starting the session")
            if not policy.broadcast_start_authorized and not policy.local_run_authorized:
                raise TransitionRejected("broadcast start is disabled in operator configuration")
            running = sum(item.lifecycle == "running" for item in self.snapshot.sessions.values())
            if running >= self.config.max_concurrent_running:
                raise TransitionRejected("running-session budget is exhausted")
            await self.driver.run(session_id, policy)
            self._set(session, "running")
            return
        if action == "pause":
            if session.lifecycle not in {"preview", "running"}:
                raise TransitionRejected("only preview or running sessions can pause")
            await asyncio.wait_for(
                self.driver.pause(session_id, policy),
                timeout=self.config.emergency_timeout_seconds,
            )
            self._set(session, "paused")
            return
        if action == "resume":
            if session.lifecycle != "paused":
                raise TransitionRejected("only a paused session can resume")
            await self.driver.preview(session_id, policy)
            self._set(session, "preview")
            return
        if action in {"stop", "emergency_stop"}:
            await asyncio.wait_for(
                self.driver.stop(session_id, policy),
                timeout=self.config.emergency_timeout_seconds if action == "emergency_stop" else 10,
            )
            session.ready = False
            session.checks = []
            self._set(session, "stopped")
            return
        raise TransitionRejected("unsupported lifecycle action")
