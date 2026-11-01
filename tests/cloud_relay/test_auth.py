"""Offline checks for the cloud relay's JWT auth, admin-token, and
per-tenant rate limiting (P-053, WP-6).

None of this needs a live Postgres — `create_token`/`decode_token`/
`get_current_tenant`/`require_admin_token`/`check_rate_limit` are all pure
or dependency-only logic. Skips cleanly if the relay's own dependencies
(fastapi, jose, pydantic-settings, ...) aren't installed, matching
tests/backend_api/test_routes.py's own pattern — CI's fast Python job
doesn't install them today.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
APP_DIR = REPO / "cloud" / "relay-api"

sys.path.insert(0, str(APP_DIR))

try:
    from app.middleware.auth import (
        create_token,
        decode_token,
        _admin_token_matches,
    )
    from app.middleware.rate_limit import check_rate_limit
    from app.models import SubscriptionTier
    from fastapi import HTTPException
except ModuleNotFoundError as exc:  # pragma: no cover
    pytest.skip(f"cloud relay dependencies not installed: {exc}", allow_module_level=True)


# ── create_token / decode_token round-trip ──────────────────────────

def test_create_and_decode_token_round_trips():
    token = create_token("tenant-1", SubscriptionTier.PRO, device_id="dev-1")
    data = decode_token(token)
    assert data.tenant_id == "tenant-1"
    assert data.tier == SubscriptionTier.PRO
    assert data.device_id == "dev-1"


def test_decode_token_rejects_garbage():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not-a-real-jwt")
    assert exc_info.value.status_code == 401


def test_decode_token_rejects_wrong_secret():
    import jose.jwt as jose_jwt

    forged = jose_jwt.encode(
        {"tenant_id": "x", "tier": "free", "device_id": "", "exp": 9_999_999_999, "iat": 0},
        "a-different-secret-entirely",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(forged)
    assert exc_info.value.status_code == 401


def test_decode_token_rejects_expired():
    import jose.jwt as jose_jwt
    from app.config import settings

    expired = jose_jwt.encode(
        {"tenant_id": "x", "tier": "free", "device_id": "", "exp": 1, "iat": 0},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    # decode_token itself doesn't check exp (get_current_tenant does, and
    # that needs an HTTPBearer credentials object) — jose's own decode
    # does enforce it though, since exp=1 is far in the past.
    with pytest.raises(HTTPException):
        decode_token(expired)


# ── require_admin_token ───────────────────────────────────────────

def test_admin_token_matches_the_real_value(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_token", "real-secret")
    assert _admin_token_matches("real-secret")
    assert not _admin_token_matches("wrong")


def test_admin_token_never_matches_when_unset(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_token", None)
    assert not _admin_token_matches("anything")
    assert not _admin_token_matches("")


def test_require_admin_token_uses_constant_time_comparison():
    """Regression pattern matching test_routes.py's
    test_require_api_key_uses_constant_time_comparison — inspect the
    source, not just behavior, so a future refactor back to `==` fails
    loudly even if it happens to still pass the accept/reject cases."""
    import inspect

    from app.middleware import auth as auth_module

    source = inspect.getsource(auth_module._admin_token_matches)
    # Strip comments so the assertion can't match this test file's own
    # explanatory comment instead of the real code.
    code_lines = [line for line in source.splitlines() if not line.strip().startswith("#")]
    assert "hmac.compare_digest(" in "\n".join(code_lines)


# ── check_rate_limit ───────────────────────────────────────────────

def test_check_rate_limit_allows_up_to_the_configured_limit(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_rate_limit_per_minute", 5)
    tenant = "tenant-rate-1"
    for _ in range(5):
        check_rate_limit(tenant, now=1000.0)  # should not raise


def test_check_rate_limit_rejects_over_the_limit(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_rate_limit_per_minute", 3)
    tenant = "tenant-rate-2"
    for _ in range(3):
        check_rate_limit(tenant, now=2000.0)
    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(tenant, now=2000.0)
    assert exc_info.value.status_code == 429


def test_check_rate_limit_refills_over_time(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_rate_limit_per_minute", 60)
    tenant = "tenant-rate-3"
    for _ in range(60):
        check_rate_limit(tenant, now=3000.0)
    with pytest.raises(HTTPException):
        check_rate_limit(tenant, now=3000.0)
    # A full minute later, the bucket should be full again.
    check_rate_limit(tenant, now=3060.0)  # should not raise


def test_check_rate_limit_tracks_tenants_independently(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_rate_limit_per_minute", 1)
    check_rate_limit("tenant-a", now=4000.0)
    with pytest.raises(HTTPException):
        check_rate_limit("tenant-a", now=4000.0)
    check_rate_limit("tenant-b", now=4000.0)  # different tenant, untouched bucket
