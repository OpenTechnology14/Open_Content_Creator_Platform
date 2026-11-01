"""Overlay state APIs consumed by NodeCG / Browser Sources."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.deps import AuthDep, RedisDep

router = APIRouter(tags=["overlays"])


class OverlayState(BaseModel):
    name: str
    payload: dict[str, Any]


def _key(name: str) -> str:
    return f"overlay:{name}"


@router.get("/{name}")
async def get_overlay(name: str, redis: RedisDep) -> OverlayState:
    raw = await redis.get(_key(name))
    if raw is None:
        return OverlayState(name=name, payload={})
    return OverlayState(name=name, payload=json.loads(raw))


@router.put("/{name}")
async def put_overlay(
    name: str,
    state: OverlayState,
    redis: RedisDep,
    _: AuthDep,
) -> dict[str, str]:
    if state.name != name:
        raise HTTPException(status_code=400, detail="name in path and body must match")
    await redis.set(_key(name), json.dumps(state.payload))
    # Publish so NodeCG / WS subscribers pick it up immediately.
    await redis.publish(f"overlay.{name}", json.dumps(state.payload))
    return {"status": "ok"}


@router.delete("/{name}")
async def delete_overlay(name: str, redis: RedisDep, _: AuthDep) -> dict[str, str]:
    await redis.delete(_key(name))
    await redis.publish(f"overlay.{name}", json.dumps({}))
    return {"status": "ok"}
