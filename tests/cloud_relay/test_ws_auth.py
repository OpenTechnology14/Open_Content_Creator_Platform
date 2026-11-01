"""Offline checks for the cloud relay's `/ws` handshake (P-053, WP-6).

Real bug found and fixed by writing these: `main.py`'s WebSocket route
handler had no `websocket: WebSocket` type annotation. FastAPI's routing
(unlike bare Starlette) needs that annotation to recognize the parameter —
without it, every connection closed immediately after `accept()`, before
`handle_websocket`'s own body ever ran. Confirmed by direct reproduction
against the pre-fix code (`git stash` + rerun) before fixing it. Nothing
had ever exercised this path — the relay's own module docstring calls it
"the core of the cloud service."

Uses `TestClient(app)` without the `with ... as client:` form (same trick
tests/backend_api/test_routes.py already uses) so the app's `lifespan()`
(which calls `init_db()`, needing a real Postgres) never runs — all four
handshake failure paths return/close before touching the DB or Redis,
verified by reading routers/relay.py directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
APP_DIR = REPO / "cloud" / "relay-api"

sys.path.insert(0, str(APP_DIR))

try:
    from app.main import app as fastapi_app
    from app.middleware.auth import create_token
    from app.models import SubscriptionTier
    from app.routers import relay as relay_module
    from starlette.testclient import TestClient
except ModuleNotFoundError as exc:  # pragma: no cover
    pytest.skip(f"cloud relay dependencies not installed: {exc}", allow_module_level=True)


@pytest.fixture()
def client():
    return TestClient(fastapi_app)


def send_auth(ws, token: str, device_id: str):
    ws.send_json({"Auth": {
        "jwt": token,
        "device_id": device_id,
        "device_name": f"Device {device_id}",
        "product": "StreamExtend",
    }})


def test_ws_route_has_a_typed_websocket_parameter():
    """Direct regression test for the actual bug — not just its symptom.
    A future refactor that drops the annotation again should fail here
    even before anyone notices every connection silently closing."""
    # Read main.py's source directly rather than introspecting Starlette's
    # internal route objects, which don't preserve the original annotation
    # in an easily-queryable form.
    main_source = (APP_DIR / "app" / "main.py").read_text(encoding="utf-8")
    assert "async def websocket_relay(websocket: WebSocket)" in main_source, (
        "the /ws route handler's `websocket` parameter lost its `WebSocket` "
        "type annotation — FastAPI's routing needs it, or every real "
        "connection closes immediately after accept() (see this test's "
        "module docstring)"
    )


def test_ws_rejects_non_json_first_message(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_text("not json")
        assert ws.receive_json() == {"AuthError": {"reason": "Invalid JSON"}}


def test_ws_rejects_first_message_missing_auth_key(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"not_auth": True})
        assert ws.receive_json() == {"AuthError": {"reason": "First message must be Auth"}}


def test_ws_rejects_invalid_jwt(client):
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, "not-a-real-jwt", "dev-1")
        data = ws.receive_json()
        assert "AuthError" in data


def test_ws_rejects_after_auth_timeout(client, monkeypatch):
    monkeypatch.setattr(relay_module, "AUTH_TIMEOUT_S", 0.05)
    with client.websocket_connect("/ws") as ws:
        import time

        time.sleep(0.2)
        data = ws.receive_json()
        assert data == {
            "AuthError": {"reason": "Auth timeout — send Auth message within 10 seconds"}
        }


def test_ws_accepts_a_valid_token(client):
    token = create_token("tenant-ws-test", SubscriptionTier.FREE, device_id="dev-1")
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, token, "dev-1")
        data = ws.receive_json()
        assert "AuthOk" in data
        assert data["AuthOk"]["subscription"]["tenant_id"] == "tenant-ws-test"


def test_ws_requires_and_binds_the_authenticated_device_id(client):
    token = create_token("tenant-ws-device", SubscriptionTier.CONNECT, device_id="dev-1")
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"Auth": {"jwt": token}})
        assert ws.receive_json() == {"AuthError": {"reason": "Auth device_id is required"}}
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, token, "dev-2")
        assert ws.receive_json() == {
            "AuthError": {"reason": "Token is registered to a different device"}
        }
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, token, "dev-1")
        assert "AuthOk" in ws.receive_json()
        ws.send_json({"Command": {
            "id": "cmd-1", "source_device_id": "spoofed", "target_device_id": "dev-2",
            "target": "obs", "action": "toggle_stream", "payload": {},
        }})
        assert ws.receive_json() == {"AuthError": {
            "reason": "Command source_device_id does not match the authenticated device"
        }}


def test_ws_rejects_oversized_post_auth_message(client):
    token = create_token("tenant-ws-size", SubscriptionTier.CONNECT, device_id="dev-1")
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, token, "dev-1")
        assert "AuthOk" in ws.receive_json()
        ws.send_json({"DevicePresence": {
            "device_id": "dev-1",
            "device_name": "x" * relay_module.MAX_WS_MESSAGE_BYTES,
            "product": "StreamExtend",
        }})
        assert ws.receive_json() == {
            "AuthError": {"reason": "Relay message exceeds 32 KiB"}
        }


@pytest.mark.parametrize(
    "message, reason",
    [
        ({"Unknown": {}}, "Unknown relay message type"),
        ({"DevicePresence": {"device_id": "dev-1", "device_name": "Studio", "product": "bad"}},
         "DevicePresence product is invalid"),
        ({"Command": {"id": "1"}}, "Command source_device_id is invalid"),
    ],
)
def test_ws_rejects_malformed_relay_messages(client, message, reason):
    token = create_token("tenant-ws-validation", SubscriptionTier.CONNECT, device_id="dev-1")
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, token, "dev-1")
        assert "AuthOk" in ws.receive_json()
        ws.send_json(message)
        assert ws.receive_json() == {"AuthError": {"reason": reason}}


def test_device_presence_requires_connect_tier_and_relays_within_tenant(client):
    free_token = create_token("tenant-ws-free", SubscriptionTier.FREE, device_id="free")
    with client.websocket_connect("/ws") as ws:
        send_auth(ws, free_token, "free")
        assert "AuthOk" in ws.receive_json()
        ws.send_json({"DevicePresence": {
            "device_id": "free", "device_name": "Free", "product": "StreamExtend",
        }})
        assert ws.receive_json() == {
            "AuthError": {"reason": "Subscription upgrade required for this feature"}
        }

    first_token = create_token("tenant-ws-presence", SubscriptionTier.CONNECT, device_id="dev-1")
    second_token = create_token("tenant-ws-presence", SubscriptionTier.CONNECT, device_id="dev-2")
    with client.websocket_connect("/ws") as first:
        send_auth(first, first_token, "dev-1")
        assert "AuthOk" in first.receive_json()
        with client.websocket_connect("/ws") as second:
            send_auth(second, second_token, "dev-2")
            assert "AuthOk" in second.receive_json()
            presence = {"DevicePresence": {
                "device_id": "dev-2", "device_name": "Studio PC", "product": "StreamExtend",
            }}
            second.send_json(presence)
            assert first.receive_json() == presence
