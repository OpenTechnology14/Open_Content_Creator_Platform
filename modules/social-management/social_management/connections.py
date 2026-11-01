"""Complete OAuth, verify the selected account, and store tokens outside public state."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

from .http import HttpTransport
from .models import Catalog, ConnectionRecord, OAuthSession
from .oauth import token_form
from .vault import ConnectionStore, TokenVault


def disconnect_connection(
    *, connection_id: str, vault: TokenVault, store: ConnectionStore
) -> ConnectionRecord:
    """Remove one account credential and its redacted public record."""
    records = {item.id: item for item in store.read()}
    record = records.get(connection_id)
    if record is None:
        raise ValueError("unknown connection")
    vault.delete(connection_id)
    store.delete(connection_id)
    return record


def _bearer(token: dict) -> dict[str, str]:
    access = token.get("access_token")
    if not isinstance(access, str) or not access:
        raise ValueError("provider token response has no access_token")
    return {"Authorization": f"Bearer {access}"}


def verify_account(
    catalog: Catalog, session: OAuthSession, token: dict, http: HttpTransport
) -> tuple[str, str, list[str]]:
    provider = next(item for item in catalog.providers if item.id == session.provider_id)
    headers = _bearer(token)
    if provider.adapter == "youtube":
        response = http.request(
            "GET",
            "https://www.googleapis.com/youtube/v3/channels?part=id%2Csnippet&mine=true",
            headers=headers,
        ).body
        items = response.get("items", [])
        if not items:
            raise ValueError("YouTube authorization returned no channel")
        account_id = items[0]["id"]
        account_name = items[0].get("snippet", {}).get("title", account_id)
    elif provider.adapter == "twitch":
        response = http.request("GET", "https://id.twitch.tv/oauth2/validate", headers=headers).body
        account_id = response.get("user_id")
        account_name = response.get("login")
        token["scope"] = response.get("scopes", token.get("scope", []))
    elif provider.adapter == "x":
        response = http.request("GET", "https://api.x.com/2/users/me", headers=headers).body.get(
            "data", {}
        )
        account_id = response.get("id")
        account_name = response.get("username") or response.get("name")
    elif provider.adapter == "discord":
        webhook = token.get("webhook", {})
        account_id = webhook.get("id")
        channel_id = webhook.get("channel_id")
        account_name = webhook.get("name") or (
            f"Discord channel {channel_id}" if channel_id else None
        )
        webhook_url = webhook.get("url")
        if not isinstance(webhook_url, str) or not webhook_url.startswith(
            ("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")
        ):
            raise ValueError("Discord authorization returned no valid incoming webhook")
    else:
        raise ValueError("provider adapter is not implemented")
    if not account_id or not account_name:
        raise ValueError("provider account verification returned incomplete identity")
    raw_scopes = token.get("scope", session.scopes)
    scopes = raw_scopes.split() if isinstance(raw_scopes, str) else list(raw_scopes)
    missing = set(session.scopes) - set(scopes)
    if missing:
        raise ValueError(f"provider did not grant required scopes: {', '.join(sorted(missing))}")
    return str(account_id), str(account_name), sorted(set(scopes))


def complete_connection(
    catalog: Catalog,
    session: OAuthSession,
    *,
    code: str,
    http: HttpTransport,
    vault: TokenVault,
    store: ConnectionStore,
    now: datetime | None = None,
) -> ConnectionRecord:
    url, form = token_form(catalog, session, code)
    token = http.request("POST", url, form=form).body
    _stamp_expiry(token, now)
    account_id, account_name, scopes = verify_account(catalog, session, token, http)
    suffix = hashlib.sha256(account_id.encode()).hexdigest()[:12]
    connection_id = f"{session.profile_id[:32]}-{session.provider_id}-{suffix}"
    timestamp = now or datetime.now(timezone.utc)
    record = ConnectionRecord(
        id=connection_id,
        profile_id=session.profile_id,
        provider_id=session.provider_id,
        account_id=account_id,
        account_name=account_name,
        scopes=scopes,
        connected_at=timestamp,
        verified_at=timestamp,
    )
    vault.set(connection_id, token)
    try:
        store.put(record)
    except Exception:
        vault.delete(connection_id)
        raise
    return record


def current_access_token(
    catalog: Catalog,
    *,
    provider_id: str,
    connection_id: str,
    vault: TokenVault,
    http: HttpTransport,
    now: datetime | None = None,
) -> str:
    """Refresh an expired access token and return one suitable for an immediate request."""
    token = vault.get(connection_id)
    current = now or datetime.now(timezone.utc)
    expires_at = token.get("_hcp_expires_at")
    if not expires_at or datetime.fromisoformat(expires_at) > current:
        return _required_access_token(token)
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise ValueError("connection expired and has no refresh token; reconnect the account")
    provider = next(item for item in catalog.providers if item.id == provider_id)
    if provider.oauth is None:
        raise ValueError("provider has no OAuth refresh contract")
    client_id = os.environ.get(provider.oauth.client_id_env)
    if not client_id:
        raise ValueError(f"missing {provider.oauth.client_id_env}")
    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if provider.oauth.client_secret_env:
        secret = os.environ.get(provider.oauth.client_secret_env)
        if not secret:
            raise ValueError(f"missing {provider.oauth.client_secret_env}")
        form["client_secret"] = secret
    refreshed = http.request("POST", provider.oauth.token_url, form=form).body
    refreshed.setdefault("refresh_token", refresh_token)
    refreshed.setdefault("scope", token.get("scope"))
    _stamp_expiry(refreshed, current)
    access = _required_access_token(refreshed)
    vault.set(connection_id, refreshed)
    return access


def _required_access_token(token: dict) -> str:
    access = token.get("access_token")
    if not isinstance(access, str) or not access:
        raise ValueError("provider token response has no access_token")
    return access


def _stamp_expiry(token: dict, now: datetime | None) -> None:
    current = now or datetime.now(timezone.utc)
    token["_hcp_obtained_at"] = current.isoformat()
    expires_in = token.get("expires_in")
    if isinstance(expires_in, (int, float)) and expires_in > 0:
        from datetime import timedelta

        token["_hcp_expires_at"] = (current + timedelta(seconds=expires_in - 30)).isoformat()
