"""Stream session metadata."""
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.deps import AuthDep, SessionDep

router = APIRouter()


class StreamStartRequest(BaseModel):
    title: str
    platforms: list[str] = []
    tags: list[str] = []


class Stream(BaseModel):
    id: UUID
    title: str
    started_at: datetime
    ended_at: datetime | None = None
    platforms: list[str] = []


@router.post("", response_model=Stream)
async def start_stream(req: StreamStartRequest, session: SessionDep, _: AuthDep) -> Stream:
    stream_id = uuid4()
    now = datetime.utcnow()
    await session.execute(
        text(
            "INSERT INTO streams (id, title, started_at, platforms) "
            "VALUES (:id, :title, :started_at, :platforms)"
        ),
        {"id": stream_id, "title": req.title, "started_at": now, "platforms": req.platforms},
    )
    await session.commit()
    return Stream(id=stream_id, title=req.title, started_at=now, platforms=req.platforms)


@router.post("/{stream_id}/stop", response_model=Stream)
async def stop_stream(stream_id: UUID, session: SessionDep, _: AuthDep) -> Stream:
    now = datetime.utcnow()
    await session.execute(
        text("UPDATE streams SET ended_at = :ended_at WHERE id = :id"),
        {"id": stream_id, "ended_at": now},
    )
    await session.commit()
    result = await session.execute(text("SELECT id, title, started_at, ended_at, platforms FROM streams WHERE id = :id"), {"id": stream_id})
    row = result.first()
    return Stream(
        id=row.id,
        title=row.title,
        started_at=row.started_at,
        ended_at=row.ended_at,
        platforms=row.platforms or [],
    )
