"""Generic event ingestion. Anything timeline-worthy goes here.

Example sources: golf tracer shot detected, OBS scene change, chat moderation
hit, agent response sent. Events are persisted and fanned out via Redis.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.deps import AuthDep, RedisDep, SessionDep

router = APIRouter(tags=["events"])


class EventIn(BaseModel):
    source: str = Field(..., examples=["golf-tracer", "obs", "agent"])
    kind: str = Field(..., examples=["shot_detected", "scene_changed", "reply"])
    stream_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class EventOut(EventIn):
    id: str
    received_at: datetime


@router.post("", response_model=EventOut, status_code=201)
async def ingest_event(
    event: EventIn,
    session: SessionDep,
    redis: RedisDep,
    _: AuthDep,
) -> EventOut:
    event_id = str(uuid.uuid4())
    received = datetime.now(timezone.utc)

    await session.execute(
        text(
            """
            INSERT INTO events (id, stream_id, source, kind, data, received_at)
            VALUES (:id, :stream_id, :source, :kind, CAST(:data AS jsonb), :received_at)
            """
        ),
        {
            "id": event_id,
            "stream_id": event.stream_id,
            "source": event.source,
            "kind": event.kind,
            "data": json.dumps(event.data),
            "received_at": received,
        },
    )
    await session.commit()

    # Fanout to anyone subscribed. Channel pattern: events.<source>.<kind>
    channel = f"events.{event.source}.{event.kind}"
    await redis.publish(
        channel,
        json.dumps(
            {
                "id": event_id,
                "stream_id": event.stream_id,
                "source": event.source,
                "kind": event.kind,
                "data": event.data,
                "received_at": received.isoformat(),
            }
        ),
    )

    return EventOut(
        id=event_id,
        received_at=received,
        **event.model_dump(),
    )


@router.get("/recent")
async def recent_events(
    session: SessionDep,
    _: AuthDep,
    limit: int = 50,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    result = await session.execute(
        text(
            """
            SELECT id, stream_id, source, kind, data, received_at
            FROM events ORDER BY received_at DESC LIMIT :limit
            """
        ),
        {"limit": limit},
    )
    return [dict(row._mapping) for row in result]
