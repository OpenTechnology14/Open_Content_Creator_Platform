"""Local channel routing and revision-bound concept decisions; no provider or model calls."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
from typing import Iterator, Literal
import uuid

from pydantic import Field, field_validator, model_validator
import yaml

from .models import Catalog, ConnectionRecord, Contract, Identifier

SourceKind = Literal["marketing-subject", "blog-post", "owned-recording", "game-brief"]
Decision = Literal["approve", "reject", "revise"]
DEFAULT_CHANNELS = Path(__file__).resolve().parents[3] / "configs/local/social-channels.yaml"


class Channel(Contract):
    id: Identifier
    name: str = Field(min_length=1, max_length=100)
    purpose: Literal["walkthroughs", "original-content", "gaming"]
    profile_id: Identifier
    source_kinds: list[SourceKind] = Field(min_length=1, max_length=4)
    description: str = Field(min_length=1, max_length=500)


class ChannelCatalog(Contract):
    schema_version: Literal[1]
    channels: list[Channel] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def unique_channels(self) -> ChannelCatalog:
        if len({channel.id for channel in self.channels}) != len(self.channels):
            raise ValueError("channel IDs must be unique")
        return self


class SourceReference(Contract):
    kind: SourceKind
    repository: str = Field(pattern=r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?$")
    revision: str = Field(pattern=r"^[a-f0-9]{7,64}$")
    path: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=1000)

    @field_validator("path")
    @classmethod
    def relative_source(cls, value: str) -> str:
        if (
            PurePosixPath(value).is_absolute()
            or ".." in value.split("/")
            or "\\" in value
            or ":" in value
            or any(ord(c) < 32 for c in value)
        ):
            raise ValueError("source path must be a relative repository or recording reference")
        return value


class ConceptDraft(Contract):
    channel_id: Identifier
    title: str = Field(min_length=1, max_length=160)
    audience: str = Field(min_length=1, max_length=500)
    hook: str = Field(min_length=1, max_length=1000)
    original_contribution: str = Field(min_length=1, max_length=2000)
    outline: list[str] = Field(min_length=1, max_length=20)
    format: Literal["long-form", "short", "live"]
    sources: list[SourceReference] = Field(min_length=1, max_length=20)
    rights_note: str = Field(min_length=1, max_length=2000)
    effort: Literal["small", "medium", "large"]

    @field_validator("outline")
    @classmethod
    def bounded_outline(cls, value: list[str]) -> list[str]:
        if any(not line.strip() or len(line) > 1000 for line in value):
            raise ValueError("outline items must contain 1–1000 characters")
        return value


def load_channels(catalog: Catalog, path: Path = DEFAULT_CHANNELS) -> ChannelCatalog:
    """Load operator configuration and validate social-profile capabilities."""
    result = ChannelCatalog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    profiles = {item.id: item for item in catalog.profiles}
    for channel in result.channels:
        profile = profiles.get(channel.profile_id)
        if profile is None or not any(
            d.provider_id == "youtube" and "post-video" in d.capabilities
            for d in profile.destinations
        ):
            raise ValueError("every channel needs a social profile with YouTube video capability")
    return result


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class EditorialStore:
    """Private SQLite state. Every state change and its history commit together."""

    def __init__(self, path: Path, channels: ChannelCatalog) -> None:
        self.path = path
        self.channels = {item.id: item for item in channels.channels}

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Open privately before SQLite can create a world-readable database.
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        self.path.chmod(0o600)
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("unsupported editorial database version")
            db.execute(
                "CREATE TABLE IF NOT EXISTS concepts (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS events "
                "(sequence INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS bindings "
                "(channel TEXT PRIMARY KEY, connection TEXT NOT NULL, "
                "fingerprint TEXT NOT NULL UNIQUE)"
            )
            db.execute("CREATE TABLE IF NOT EXISTS paused (channel TEXT PRIMARY KEY)")
            db.execute("PRAGMA user_version=1")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _channel(self, channel_id: str) -> Channel:
        if channel_id not in self.channels:
            raise ValueError("unknown channel")
        return self.channels[channel_id]

    def _validate(self, draft: ConceptDraft) -> str:
        channel = self._channel(draft.channel_id)
        if not {source.kind for source in draft.sources} <= set(channel.source_kinds):
            raise ValueError("source kind is not allowed for this channel")
        return _fingerprint(channel.model_dump_json())

    @staticmethod
    def _record(db: sqlite3.Connection, concept_id: str, revision: int | None = None) -> dict:
        row = db.execute("SELECT payload FROM concepts WHERE id=?", (concept_id,)).fetchone()
        if row is None:
            raise ValueError("unknown concept")
        record = json.loads(row[0])
        if revision is not None and revision != record["revision"]:
            raise ValueError("stale revision; read the current concept before changing it")
        return record

    @staticmethod
    def _event(db: sqlite3.Connection, action: str, **details: object) -> None:
        db.execute(
            "INSERT INTO events(payload) VALUES (?)",
            (json.dumps({"at": _stamp(), "action": action, **details}),),
        )

    @staticmethod
    def _save(db: sqlite3.Connection, record: dict) -> None:
        db.execute(
            "INSERT OR REPLACE INTO concepts(id,payload) VALUES (?,?)",
            (record["id"], json.dumps(record)),
        )

    def submit(self, draft: ConceptDraft) -> dict:
        channel_revision = self._validate(draft)
        record = {
            "schema_version": 1,
            "id": f"concept-{uuid.uuid4().hex[:20]}",
            "revision": 1,
            "state": "awaiting-approval",
            "draft": draft.model_dump(),
            "channel_revision": channel_revision,
            "updated_at": _stamp(),
        }
        with self._transaction() as db:
            self._save(db, record)
            self._event(db, "submit", record=record)
        return record

    def edit(self, concept_id: str, revision: int, draft: ConceptDraft) -> dict:
        channel_revision = self._validate(draft)
        with self._transaction() as db:
            record = self._record(db, concept_id, revision)
            record.update(
                revision=revision + 1,
                state="awaiting-approval",
                draft=draft.model_dump(),
                channel_revision=channel_revision,
                updated_at=_stamp(),
            )
            self._save(db, record)
            self._event(db, "edit", record=record)
        return record

    def decide(
        self,
        concept_id: str,
        revision: int,
        decision: Decision,
        *,
        actor: str,
        reason: str,
        confirmation: str,
    ) -> dict:
        if confirmation != f"{concept_id}@{revision}":
            raise ValueError("decision requires the exact concept ID@revision confirmation")
        if decision not in ("approve", "reject", "revise"):
            raise ValueError("unknown decision")
        if not actor.strip() or len(actor) > 100 or not reason.strip() or len(reason) > 2000:
            raise ValueError("actor and owner decision text are required and bounded")
        with self._transaction() as db:
            record = self._record(db, concept_id, revision)
            current = self._validate(ConceptDraft.model_validate(record["draft"]))
            if decision == "approve" and current != record["channel_revision"]:
                raise ValueError("channel configuration changed; resubmit the concept for review")
            record.update(
                revision=revision + 1,
                updated_at=_stamp(),
                state={"approve": "approved", "reject": "rejected", "revise": "changes-requested"}[
                    decision
                ],
            )
            self._save(db, record)
            self._event(
                db,
                decision,
                concept_id=concept_id,
                revision=record["revision"],
                reviewed_revision=revision,
                actor=actor,
                reason=reason,
            )
        return record

    def bind(self, channel_id: str, connection: ConnectionRecord) -> None:
        channel = self._channel(channel_id)
        if connection.provider_id != "youtube" or connection.profile_id != channel.profile_id:
            raise ValueError("connection must be YouTube and match this channel's social profile")
        fingerprint = _fingerprint(connection.account_id)
        with self._transaction() as db:
            other = db.execute(
                "SELECT channel FROM bindings WHERE fingerprint=? AND channel!=?",
                (fingerprint, channel_id),
            ).fetchone()
            if other:
                raise ValueError("this YouTube account is already bound to another channel")
            db.execute(
                "INSERT OR REPLACE INTO bindings VALUES (?,?,?)",
                (channel_id, connection.id, fingerprint),
            )
            self._event(db, "bind", channel_id=channel_id, connection_id=connection.id)

    def unbind(self, channel_id: str) -> None:
        self._channel(channel_id)
        with self._transaction() as db:
            db.execute("DELETE FROM bindings WHERE channel=?", (channel_id,))
            self._event(db, "unbind", channel_id=channel_id)

    def pause(self, channel_id: str, paused: bool) -> None:
        self._channel(channel_id)
        with self._transaction() as db:
            if paused:
                db.execute("INSERT OR IGNORE INTO paused VALUES (?)", (channel_id,))
            else:
                db.execute("DELETE FROM paused WHERE channel=?", (channel_id,))
            self._event(db, "pause" if paused else "resume", channel_id=channel_id)

    def report(self, connections: list[ConnectionRecord]) -> dict:
        records = {record.id: record for record in connections}
        with self._transaction() as db:
            bindings = {row["channel"]: row for row in db.execute("SELECT * FROM bindings")}
            paused = {row[0] for row in db.execute("SELECT channel FROM paused")}
            concepts = [
                json.loads(row[0]) for row in db.execute("SELECT payload FROM concepts ORDER BY id")
            ]
        channels = []
        for channel in self.channels.values():
            binding = bindings.get(channel.id)
            connection = records.get(binding["connection"]) if binding else None
            ready = bool(
                connection
                and connection.profile_id == channel.profile_id
                and connection.provider_id == "youtube"
                and _fingerprint(connection.account_id) == binding["fingerprint"]
            )
            channels.append(
                {
                    **channel.model_dump(),
                    "paused": channel.id in paused,
                    "connection_state": "locally-bound"
                    if ready
                    else "reconnect-required"
                    if binding
                    else "unbound",
                }
            )
        for record in concepts:
            channel = self.channels.get(record["draft"]["channel_id"])
            record["configuration_current"] = bool(
                channel and _fingerprint(channel.model_dump_json()) == record["channel_revision"]
            )
        return {
            "schema_version": 1,
            "generated_at": _stamp(),
            "channels": channels,
            "concepts": concepts,
            "publication": "separate-final-approval-required",
            "analytics": "not-connected",
        }

    def history(self, concept_id: str) -> list[dict]:
        with self._transaction() as db:
            self._record(db, concept_id)
            events = [
                json.loads(row[0])
                for row in db.execute("SELECT payload FROM events ORDER BY sequence")
            ]
        return [
            event
            for event in events
            if event.get("concept_id") == concept_id
            or event.get("record", {}).get("id") == concept_id
        ]

    def brief(self, concept_id: str, revision: int) -> dict:
        with self._transaction() as db:
            record = self._record(db, concept_id, revision)
            draft = ConceptDraft.model_validate(record["draft"])
            if record["state"] != "approved":
                raise ValueError("production brief requires an approved concept")
            if self._validate(draft) != record["channel_revision"]:
                raise ValueError("channel configuration changed; resubmit the concept for review")
            if db.execute("SELECT 1 FROM paused WHERE channel=?", (draft.channel_id,)).fetchone():
                raise ValueError("channel is paused")
            return {
                "schema_version": 1,
                "concept": record,
                "profile_id": self._channel(draft.channel_id).profile_id,
                "publication_approved": False,
                "instructions": [
                    "Produce a local draft for finished-video review.",
                    "Recheck concept ID/revision before starting or resuming work.",
                    "Source references and rights notes need editorial verification.",
                    "Use Social Management's separate final publishing gate.",
                ],
            }
