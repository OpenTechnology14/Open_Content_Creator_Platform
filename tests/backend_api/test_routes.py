"""Offline route-table checks for the FastAPI backend.

No service required — FastAPI builds its route table at import time, so this
inspects `app.routes` directly. Catches double-prefix and other routing bugs
without a running server.

This module requires Python 3.11+ (`str | None` union syntax, matching
CLAUDE.md §5 and the Dockerfile's `python:3.11-slim`). Skipped, not failed,
on an older interpreter — CI runs 3.11.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
APP_DIR = REPO / "modules" / "backend-api" / "fastapi"

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="app code uses 3.11+ syntax (str | None); CLAUDE.md §5 pins 3.11+",
)


@pytest.fixture(scope="module")
def app():
    """Import the FastAPI app with its own directory on sys.path.

    The app package is `app.*`, matching how uvicorn runs it inside the
    Dockerfile (`WORKDIR /app`, `CMD uvicorn app.main:app`).
    """
    sys.path.insert(0, str(APP_DIR))
    try:
        from app.main import app as fastapi_app  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        pytest.skip(f"backend-api dependencies not installed: {exc}")
    else:
        yield fastapi_app
    finally:
        sys.path.remove(str(APP_DIR))


def _paths(app) -> set[str]:
    return {r.path for r in app.routes if hasattr(r, "path")}


def test_no_router_double_prefixes_itself(app) -> None:
    """Regression: events/automation/overlays each declared their own prefix
    on `APIRouter(prefix=...)` AND main.py included them with the same
    prefix again, so the live paths were /events/events, not /events.
    `ws` had the same class of bug from the other direction: no router-level
    prefix, but the endpoint decorator hardcoded "/ws" *and* main.py applied
    prefix="/ws" — live path was /ws/ws, not /ws (found 2026-09-01, while
    adding WS auth for P-026 — nothing had exercised the path string before).

    Every router except the ones legitimately mounted at "" must appear
    exactly once in its own path, not twice.
    """
    doubled = [
        p for p in _paths(app)
        for segment in ("events", "automation", "overlays", "ws")
        if p.count(f"/{segment}") >= 2
    ]
    assert not doubled, f"double-prefixed routes: {sorted(set(doubled))}"


def test_documented_routes_exist(app) -> None:
    """The exact routes P-016's proposal and tests/USE-CASES.md cite by path."""
    paths = _paths(app)
    expected = {
        "/health",
        "/ready",
        "/metrics",
        "/streams",
        "/streams/{stream_id}/stop",
        "/events",
        "/events/recent",
        "/automation/trigger",
        "/automation/status",
        "/overlays/{name}",
        "/ws",
    }
    missing = expected - paths
    assert not missing, f"routes referenced in docs but not served: {missing}"


# ── WebSocket auth (P-026 hardening) ─────────────────────────────────────
# /ws fans out the same event/overlay data the REST writes require an API
# key for, but had no auth at all. These only exercise the *rejection*
# path — the accepted path subscribes to Redis pub/sub, which needs a real
# Redis and is exactly what tests/acceptance covers instead.

def test_ws_rejects_missing_api_key(app) -> None:
    from starlette.testclient import TestClient  # noqa: PLC0415
    from starlette.websockets import WebSocketDisconnect  # noqa: PLC0415

    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws?topics=x"):
            pass
    assert exc_info.value.code == 1008


def test_ws_rejects_wrong_api_key(app) -> None:
    from starlette.testclient import TestClient  # noqa: PLC0415
    from starlette.websockets import WebSocketDisconnect  # noqa: PLC0415

    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws?topics=x&api_key=definitely-wrong"):
            pass
    assert exc_info.value.code == 1008


def test_require_api_key_uses_constant_time_comparison(app) -> None:
    """Regression: the original check used `x_api_key != settings.api_key`,
    a naive equality compare whose short-circuit-on-first-mismatch timing
    leaks how many leading characters of a guess are correct. Assert the
    fix (hmac.compare_digest) is actually what's wired in, not just that
    correct/wrong keys still behave correctly — a plain `==` passes the
    same functional assertions while reintroducing the timing leak."""
    import inspect  # noqa: PLC0415
    import re  # noqa: PLC0415

    from app.deps import require_api_key  # noqa: PLC0415

    src = inspect.getsource(require_api_key.__globals__["_keys_match"])
    # Strip comments first — the explanatory comment above the real check
    # also contains the words "hmac.compare_digest", so a plain substring
    # search on raw source passes even after the call itself is deleted.
    code_only = re.sub(r"#.*", "", src)
    assert "hmac.compare_digest(" in code_only, (
        "require_api_key's comparison no longer calls hmac.compare_digest — "
        "this reintroduces a timing side-channel on the API key check"
    )


def test_require_api_key_accepts_and_rejects(app) -> None:
    from fastapi import HTTPException  # noqa: PLC0415

    from app.deps import require_api_key, settings  # noqa: PLC0415

    with pytest.raises(HTTPException) as exc_info:
        require_api_key(x_api_key=None)
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException):
        require_api_key(x_api_key="definitely-wrong")

    require_api_key(x_api_key=settings.api_key)  # does not raise
