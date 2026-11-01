"""
WebSocket relay router.

The core of the cloud service — relays messages between a tenant's
desktop app and mobile app (or between multiple devices).

Architecture:
- Each tenant has a "room" (Redis pub/sub channel)
- When device A sends a message, it's published to the tenant's channel
- All other devices subscribed to that channel receive it
- The relay itself is stateless — Redis handles fan-out

This means the relay can scale horizontally: multiple relay instances
behind a load balancer, all sharing the same Redis.
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

from ..middleware.auth import decode_token, require_admin_token
from ..models import SubscriptionTier

router = APIRouter()

# In-memory connection tracking (per-instance)
# Key: tenant_id, Value: set of WebSocket connections
_connections: Dict[str, Set[WebSocket]] = {}

# Module-level so tests can monkeypatch it short instead of actually
# sleeping 10s to exercise the auth-timeout path.
AUTH_TIMEOUT_S = 10.0
MAX_WS_MESSAGE_BYTES = 32 * 1024

_RELAY_MESSAGE_KEYS = {
    "Command", "CommandResult", "DevicePresence", "SyncPush", "SyncPull",
    "SyncData", "Notification", "MetricsBatch", "Ping", "Pong",
}


def _validate_relay_message(msg, authenticated_device_id: str) -> str | None:
    """Return a client-safe error for malformed post-auth relay messages."""
    if msg in ("Ping", "Pong"):
        return None
    if not isinstance(msg, dict) or len(msg) != 1:
        return "Relay message must contain exactly one message type"
    kind, body = next(iter(msg.items()))
    if kind not in _RELAY_MESSAGE_KEYS:
        return "Unknown relay message type"
    if kind in {"Ping", "Pong"}:
        return None
    if not isinstance(body, dict):
        return f"{kind} body must be an object"
    if kind == "DevicePresence":
        device_id = body.get("device_id")
        device_name = body.get("device_name")
        product = body.get("product")
        if not _printable_string(device_id, 128):
            return "DevicePresence device_id is invalid"
        if device_id != authenticated_device_id:
            return "DevicePresence device_id does not match the authenticated device"
        if not _printable_string(device_name, 80):
            return "DevicePresence device_name is invalid"
        if product not in {"StreamExtend", "CreatorExtend"}:
            return "DevicePresence product is invalid"
    elif kind == "Command":
        for field in ("id", "source_device_id", "target_device_id", "target", "action"):
            if not _printable_string(body.get(field), 128):
                return f"Command {field} is invalid"
        if body["source_device_id"] != authenticated_device_id:
            return "Command source_device_id does not match the authenticated device"
        if "payload" not in body:
            return "Command payload is required"
    elif kind == "CommandResult":
        if not _printable_string(body.get("id"), 128):
            return "CommandResult id is invalid"
        if not isinstance(body.get("success"), bool) or "data" not in body:
            return "CommandResult body is invalid"
    return None


def _printable_string(value, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and value.isprintable()
    )


async def _receive_json_message(websocket: WebSocket):
    raw = await websocket.receive_text()
    if len(raw.encode("utf-8")) > MAX_WS_MESSAGE_BYTES:
        raise ValueError("Relay message exceeds 32 KiB")
    return json.loads(raw)


async def handle_websocket(websocket: WebSocket):
    """Main WebSocket handler.

    Protocol:
    1. Client connects
    2. Client sends Auth message: {"Auth": {"jwt": "..."}}
    3. Server validates JWT, responds with AuthOk or AuthError
    4. Bidirectional message relay begins
    """
    await websocket.accept()

    tenant_id = None
    authenticated_device_id = None
    tier = SubscriptionTier.FREE

    try:
        # Step 1: Wait for auth message
        msg = await asyncio.wait_for(_receive_json_message(websocket), timeout=AUTH_TIMEOUT_S)

        # Parse auth
        if not isinstance(msg, dict):
            await websocket.send_json({
                "AuthError": {"reason": "First message must be Auth"}
            })
            await websocket.close()
            return
        if "Auth" in msg and isinstance(msg["Auth"], dict):
            auth_body = msg["Auth"]
            jwt_token = auth_body.get("jwt", "")
        elif "auth" in msg and isinstance(msg["auth"], dict):
            auth_body = msg["auth"]
            jwt_token = auth_body.get("jwt", "")
        else:
            await websocket.send_json({
                "AuthError": {"reason": "First message must be Auth"}
            })
            await websocket.close()
            return

        authenticated_device_id = auth_body.get("device_id")
        if not _printable_string(authenticated_device_id, 128):
            await websocket.send_json({
                "AuthError": {"reason": "Auth device_id is required"}
            })
            await websocket.close()
            return

        # Validate JWT
        try:
            token_data = decode_token(jwt_token)
            tenant_id = token_data.tenant_id
            tier = token_data.tier
            if token_data.device_id and token_data.device_id != authenticated_device_id:
                raise ValueError("Token is registered to a different device")
        except Exception as e:
            await websocket.send_json({
                "AuthError": {"reason": str(e)}
            })
            await websocket.close()
            return

        # Check connection limit
        existing = _connections.get(tenant_id, set())
        from ..config import settings
        if len(existing) >= settings.ws_max_connections_per_tenant:
            await websocket.send_json({
                "AuthError": {
                    "reason": f"Too many connections (max {settings.ws_max_connections_per_tenant})"
                }
            })
            await websocket.close()
            return

        # Auth successful
        await websocket.send_json({
            "AuthOk": {
                "subscription": {
                    "tier": tier.value,
                    "active": True,
                    "tenant_id": tenant_id,
                    "expires_at": None,
                }
            }
        })

        # Register connection
        if tenant_id not in _connections:
            _connections[tenant_id] = set()
        _connections[tenant_id].add(websocket)

        # Step 2: Message relay loop
        while True:
            msg = await _receive_json_message(websocket)

            # Handle Ping/Pong
            if msg == "Ping" or (isinstance(msg, dict) and msg.get("Ping") is not None):
                await websocket.send_json("Pong")
                continue

            validation_error = _validate_relay_message(msg, authenticated_device_id)
            if validation_error:
                await websocket.send_json({"AuthError": {"reason": validation_error}})
                continue

            # Feature gating based on tier
            if not _check_tier_for_message(msg, tier):
                await websocket.send_json({
                    "AuthError": {
                        "reason": "Subscription upgrade required for this feature"
                    }
                })
                continue

            # Relay to all other connections for this tenant
            await _broadcast(tenant_id, msg, exclude=websocket)

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        await websocket.send_json({
            "AuthError": {"reason": "Auth timeout — send Auth message within 10 seconds"}
        })
    except json.JSONDecodeError:
        await websocket.send_json({
            "AuthError": {"reason": "Invalid JSON"}
        })
    except ValueError as e:
        await websocket.send_json({"AuthError": {"reason": str(e)}})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if tenant_id and tenant_id in _connections:
            _connections[tenant_id].discard(websocket)
            if not _connections[tenant_id]:
                del _connections[tenant_id]

        try:
            await websocket.close()
        except Exception:
            pass


async def _broadcast(tenant_id: str, message: dict, exclude: WebSocket = None):
    """Broadcast a message to all devices for a tenant."""
    connections = _connections.get(tenant_id, set())
    dead = set()

    for conn in connections:
        if conn is exclude:
            continue
        try:
            await conn.send_json(message)
        except Exception:
            dead.add(conn)

    # Clean up dead connections
    for conn in dead:
        _connections.get(tenant_id, set()).discard(conn)


def _check_tier_for_message(msg: dict, tier: SubscriptionTier) -> bool:
    """Check if the message type is allowed for the given tier."""
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.CONNECT: 1,
        SubscriptionTier.PRO: 2,
        SubscriptionTier.TEAM: 3,
    }

    current = tier_order.get(tier, 0)

    # Remote control requires Connect+
    if "Command" in msg or "CommandResult" in msg or "DevicePresence" in msg:
        return current >= 1

    # Sync requires Pro+
    if "SyncPush" in msg or "SyncPull" in msg:
        return current >= 2

    # Metrics requires Pro+
    if "MetricsBatch" in msg:
        return current >= 2

    # Notifications require Connect+
    if "Notification" in msg:
        return current >= 1

    return True


@router.get("/connections", dependencies=[Depends(require_admin_token)])
async def get_connection_count():
    """Admin: get current WebSocket connection stats."""
    return {
        "tenants": len(_connections),
        "connections": sum(len(conns) for conns in _connections.values()),
    }
