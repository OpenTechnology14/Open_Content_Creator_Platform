"""WebSocket endpoint with Redis pub/sub backing.

Clients connect to /ws?topics=overlay.scoreboard,events.golf-tracer.shot_detected
and receive a JSON envelope every time a matching channel fires.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from loguru import logger

from app.deps import WsAuthDep, get_redis_client

router = APIRouter(tags=["ws"])


@router.websocket("")
async def ws_endpoint(
    websocket: WebSocket,
    authorized: WsAuthDep,
    topics: str = Query("", description="comma-separated channel/pattern list"),
) -> None:
    if not authorized:
        # Close, don't just refuse to accept: a bare refusal leaves some
        # clients retrying forever against what looks like a routing
        # problem rather than an auth one. 1008 = policy violation, the
        # WS close code for "you're not allowed here."
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid api key")
        return

    await websocket.accept()
    patterns = [t.strip() for t in topics.split(",") if t.strip()]
    if not patterns:
        await websocket.send_json({"error": "no topics provided"})
        await websocket.close()
        return

    redis = await get_redis_client()
    pubsub = redis.pubsub()
    try:
        await pubsub.psubscribe(*patterns)
        logger.info("ws subscribed: {}", patterns)

        # Two coroutines: relay Redis -> client, and drain client pings.
        async def relay() -> None:
            async for msg in pubsub.listen():
                if msg.get("type") not in {"pmessage", "message"}:
                    continue
                channel = msg.get("channel")
                data: Any = msg.get("data")
                if isinstance(data, (bytes, bytearray)):
                    data = data.decode("utf-8", errors="replace")
                if isinstance(channel, (bytes, bytearray)):
                    channel = channel.decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(data) if isinstance(data, str) else data
                except json.JSONDecodeError:
                    parsed = data
                await websocket.send_json({"channel": channel, "data": parsed})

        async def drain() -> None:
            while True:
                # We don't expect inbound traffic but want to detect disconnects.
                await websocket.receive_text()

        relay_task = asyncio.create_task(relay())
        drain_task = asyncio.create_task(drain())
        done, pending = await asyncio.wait(
            {relay_task, drain_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()
    except WebSocketDisconnect:
        logger.info("ws disconnected: {}", patterns)
    finally:
        await pubsub.punsubscribe(*patterns)
        await pubsub.aclose()
