"""One bounded durable root ledger; CAS and operation results commit together."""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import os
import threading
import time
import uuid
from collections.abc import Iterator

from pydantic import Field, ValidationError
from .models import (
    Contract,
    Create,
    ExportAttemptV1,
    FinalizedSourceV1,
    PlanRecord,
    ProductionSessionV1,
)
from .safety import Fault, SafeRoot, canonical, decode, digest
from .platform_support import fcntl, require_posix

TERMINAL = {"complete", "partial", "failed", "cancelled", "interrupted"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def new_id(prefix: str) -> str:
    return prefix + "-" + uuid.uuid4().hex


def dump(model: Contract) -> dict:
    return model.model_dump(mode="json", exclude_none=True)


class Operation(Contract):
    payload_sha256: str
    value: dict


class State(Contract):
    schema_version: int = Field(default=1, ge=1, le=1)
    productions: dict[str, ProductionSessionV1] = Field(default_factory=dict, max_length=100)
    sources: dict[str, FinalizedSourceV1] = Field(default_factory=dict, max_length=1000)
    plans: dict[str, PlanRecord] = Field(default_factory=dict, max_length=1000)
    attempts: dict[str, ExportAttemptV1] = Field(default_factory=dict, max_length=1000)
    operations: dict[str, Operation] = Field(default_factory=dict, max_length=2000)


class ProductionStore:
    """Root is a trusted launcher capability, never constructed from a request."""

    def __init__(self, root: SafeRoot, root_id: str):
        require_posix()
        self.root, self.root_id = root, root_id
        self.mutex = threading.RLock()

    @contextlib.contextmanager
    def locked(self) -> Iterator[State]:
        require_posix()
        if not self.mutex.acquire(timeout=2):
            raise Fault("worker_busy")
        try:
            fd = self.root.open(".lock", os.O_CREAT | os.O_RDWR)
            try:
                deadline = time.monotonic() + 2
                while True:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            raise Fault("worker_busy")
                        time.sleep(0.01)
                try:
                    raw = self.root.read("state.json")
                except FileNotFoundError:
                    state = State()
                else:
                    try:
                        state = State.model_validate(decode(raw))
                        self.validate_links(state)
                    except (ValidationError, ValueError, KeyError) as error:
                        raise Fault("corrupt_state") from error
                yield state
            finally:
                os.close(fd)
        finally:
            self.mutex.release()

    def validate_links(self, state: State) -> None:
        for key, prod in state.productions.items():
            if key != prod.production_id or prod.content_root_id != self.root_id:
                raise Fault("corrupt_state")
            for source_id in prod.source_ids:
                source = state.sources[source_id]
                if (
                    source.production_id != key
                    or source.source_id != source_id
                    or source.source_profile_id != prod.source_profile_id
                    or source.content_profile_id != prod.content_profile_id
                ):
                    raise Fault("corrupt_state")
            for attempt_id in prod.export_attempt_ids:
                attempt = state.attempts[attempt_id]
                if attempt.production_id != key or attempt.attempt_id != attempt_id:
                    raise Fault("corrupt_state")

        for key, source in state.sources.items():
            owner = state.productions.get(source.production_id)
            if (
                owner is None
                or key != source.source_id
                or key not in owner.source_ids
                or source.root_id != self.root_id
            ):
                raise Fault("corrupt_state")
        for key, attempt in state.attempts.items():
            owner = state.productions.get(attempt.production_id)
            source = state.sources.get(attempt.source_id)
            if (
                owner is None
                or source is None
                or key != attempt.attempt_id
                or key not in owner.export_attempt_ids
                or source.production_id != owner.production_id
                or source.sha256 != attempt.source_sha256
                or any(
                    a.attempt_id != key or a.source_id != attempt.source_id
                    for a in attempt.artifacts
                )
            ):
                raise Fault("corrupt_state")
        for key, plan in state.plans.items():
            plan_body = plan.model_dump(mode="json", exclude={"schema_version", "id", "sha256"})
            if digest(plan_body) != plan.sha256:
                raise Fault("corrupt_state")
            if (
                key != plan.id
                or plan.production_id not in state.productions
                or plan.source_id not in state.sources
                or state.sources[plan.source_id].production_id != plan.production_id
            ):
                raise Fault("corrupt_state")
            clip = plan.clip_plan
            if (
                clip.recording_id != plan.source_id
                or clip.session_id != plan.production_id
                or clip.show_id != state.productions[plan.production_id].show_profile_id
                or abs(clip.duration_seconds - state.sources[plan.source_id].duration_seconds)
                > 0.01
            ):
                raise Fault("corrupt_state")

    def save(self, state: State, production_id: str | None = None) -> None:
        # Validate again: model_copy and mutable lists do not perform assignment validation.
        state = State.model_validate(dump(state))
        self.validate_links(state)
        if production_id:
            prod = state.productions[production_id]
            portable = dict(
                schema_version=1,
                production=dump(prod),
                sources=[dump(state.sources[s]) for s in prod.source_ids],
                plans=[dump(p) for p in state.plans.values() if p.production_id == production_id],
                attempts=[dump(state.attempts[a]) for a in prod.export_attempt_ids],
            )
            # Derived portable snapshot is committed first. Native must use worker admission;
            # a crash can leave this one revision ahead of the authoritative private ledger.
            self.root.atomic(
                f"{prod.content_profile_id}/{production_id}/manifest.json", canonical(portable)
            )
        data = canonical(dump(state))
        if len(data) > 1024 * 1024:
            raise Fault("limit_exceeded")
        self.root.atomic("state.json", data)

    @contextlib.contextmanager
    def transaction(
        self, production_id: str, expected_revision: int
    ) -> Iterator[tuple[State, ProductionSessionV1]]:
        with self.locked() as state:
            prod = self.production(state, production_id)
            if prod.revision != expected_revision:
                raise Fault("revision_conflict")
            yield state, prod

    @staticmethod
    def production(state: State, production_id: str) -> ProductionSessionV1:
        if production_id not in state.productions:
            raise Fault("production_unavailable")
        return state.productions[production_id]

    @staticmethod
    def replay(state: State, operation_id: str, payload: dict) -> dict | None:
        if operation_id in state.operations:
            operation = state.operations[operation_id]
            if operation.payload_sha256 != digest(payload):
                raise Fault("operation_conflict")
            return operation.value
        return None

    @staticmethod
    def remember(state: State, operation_id: str, payload: dict, result: dict) -> None:
        state.operations[operation_id] = Operation(payload_sha256=digest(payload), value=result)

    @staticmethod
    def bump(state: State, prod: ProductionSessionV1, **changes: object) -> ProductionSessionV1:
        updated = ProductionSessionV1.model_validate(
            {**dump(prod), **changes, "revision": prod.revision + 1}
        )
        state.productions[prod.production_id] = updated
        return updated

    def create(self, payload: dict) -> dict:
        request = Create.model_validate(payload)
        if request.content_root_id != self.root_id:
            raise Fault("source_unavailable")
        with self.locked() as state:
            result = self.replay(state, request.operation_id, payload)
            if result is not None:
                return result
            prod = ProductionSessionV1(
                production_id=new_id("prod"),
                revision=1,
                created_at=now(),
                **request.model_dump(exclude={"operation_id"}),
            )
            state.productions[prod.production_id] = prod
            result = dump(prod)
            self.remember(state, request.operation_id, payload, result)
            self.save(state, prod.production_id)
            return result

    def get(self, production_id: str) -> dict:
        with self.locked() as state:
            prod = self.production(state, production_id)
            return dict(
                production=dump(prod),
                sources=[dump(state.sources[s]) for s in prod.source_ids],
                plans=[dump(p) for p in state.plans.values() if p.production_id == production_id],
                attempts=[dump(state.attempts[a]) for a in prod.export_attempt_ids],
                account_state="unavailable",
                publication_state="unavailable",
            )

    def list(self, cursor: int = 0, limit: int = 100) -> dict:
        with self.locked() as state:
            records = sorted(
                state.productions.values(), key=lambda p: (p.created_at, p.production_id)
            )
            end = cursor + limit
            return dict(
                items=[dump(p) for p in records[cursor:end]],
                next_cursor=end if end < len(records) else None,
            )

    def recover(self) -> None:
        """Caller MUST hold the export lease. No persisted PID is read or signalled."""
        with self.locked() as state:
            changed = set()
            for key, attempt in list(state.attempts.items()):
                if attempt.phase not in TERMINAL:
                    state.attempts[key] = ExportAttemptV1.model_validate(
                        {
                            **dump(attempt),
                            "phase": "interrupted",
                            "ended_at": now(),
                            "error_code": "worker_restarted",
                            "sequence": attempt.sequence + 1,
                        }
                    )
                    changed.add(attempt.production_id)
            for production_id in changed:
                self.bump(state, state.productions[production_id])
                self.save(state, production_id)
