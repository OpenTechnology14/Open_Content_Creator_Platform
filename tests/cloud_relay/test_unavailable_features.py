"""Unimplemented provider/commerce paths must not issue privileges or false success."""
import asyncio
import uuid

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.middleware.auth import create_token, decode_token  # noqa: E402
from app.models import SubscriptionTier  # noqa: E402
from app.routers import auth, notifications, tenants  # noqa: E402


@pytest.mark.parametrize("route,tier,params,body", [
    ("/api/v1/auth/verify-purchase", SubscriptionTier.FREE, {},
     {"receipt": "synthetic", "store": "apple", "product": "stream_extend"}),
    ("/api/v1/auth/subscribe", SubscriptionTier.FREE, {"tier": "team"}, None),
    ("/api/v1/auth/self-hosted-key", SubscriptionTier.FREE, {}, {"name": "test"}),
    ("/api/v1/notifications/send", SubscriptionTier.CONNECT, {}, {"title": "test", "body": "test"}),
    ("/api/v1/notifications/register-device", SubscriptionTier.CONNECT,
     {"device_id": "test", "push_token": "synthetic", "platform": "ios"}, None),
    ("/api/v1/tenants/me/team/invite", SubscriptionTier.TEAM,
     {"email": "test@example.invalid", "role": "member"}, None),
])
def test_provider_stubs_fail_before_token_or_database_side_effects(monkeypatch, route, tier, params, body):
    def forbidden(*_args, **_kwargs):
        pytest.fail("unavailable provider attempted a token/database side effect")
    monkeypatch.setattr(auth, "create_token", forbidden)
    for module in [notifications, tenants]:
        monkeypatch.setattr(module, "TenantConnection", forbidden, raising=False)
    token = create_token(str(uuid.uuid4()), tier)
    result = TestClient(app).post(route, params=params, json=body,
                                  headers={"Authorization": f"Bearer {token}"})
    assert result.status_code == 501, result.text
    assert result.json()["detail"]["code"] == "feature_not_available"


def test_unimplemented_push_helpers_cannot_report_success():
    for helper in [notifications._send_apns, notifications._send_fcm]:
        with pytest.raises(NotImplementedError):
            asyncio.run(helper("synthetic-token", "test", "test", None))


def test_refresh_preserves_existing_tier_and_tenant():
    tenant = str(uuid.uuid4())
    token = create_token(tenant, SubscriptionTier.FREE)
    response = TestClient(app).post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    refreshed = decode_token(response.json()["jwt"])
    assert refreshed.tier == SubscriptionTier.FREE
    assert refreshed.tenant_id == tenant
