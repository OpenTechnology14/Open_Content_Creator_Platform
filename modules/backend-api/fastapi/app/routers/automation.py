"""Endpoints called by n8n flows (and any other automation runner).

These are intentionally coarse: they exist so an n8n node can call one URL
to trigger a sequence rather than orchestrating each step itself.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.deps import AuthDep, RedisDep

router = APIRouter(tags=["automation"])


class TriggerIn(BaseModel):
    name: str
    payload: dict[str, Any] = {}


@router.post("/trigger")
async def trigger(payload: TriggerIn, redis: RedisDep, _: AuthDep) -> dict[str, str]:
    """Fire an automation trigger by name. n8n listens on `automation.<name>`."""
    if not payload.name or "." in payload.name or "/" in payload.name:
        raise HTTPException(status_code=400, detail="invalid trigger name")
    await redis.publish(
        f"automation.{payload.name}",
        json.dumps(payload.payload),
    )
    return {"status": "queued", "name": payload.name}


@router.get("/status")
async def status(redis: RedisDep, _: AuthDep) -> dict[str, Any]:
    """Lightweight liveness for automation plane."""
    info = await redis.info("server")
    return {
        "redis_uptime_s": int(info.get("uptime_in_seconds", 0)),
        "ok": True,
    }
