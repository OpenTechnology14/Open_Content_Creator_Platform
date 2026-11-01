"""OAuth authorization-code sessions with PKCE and private local state."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from .models import Capability, Catalog, OAuthSession


def scopes_for(catalog: Catalog, provider_id: str, capability: Capability) -> list[str]:
    provider = next((item for item in catalog.providers if item.id == provider_id), None)
    if provider is None:
        raise ValueError("unknown provider")
    requested = {"account-read", capability}
    scopes: list[str] = []
    for name in requested:
        for scope in provider.capability_scopes.get(name, []):
            if scope not in scopes:
                scopes.append(scope)
    if capability not in provider.capability_scopes:
        raise ValueError("provider does not declare this capability")
    return sorted(scopes)


def begin_authorization(
    catalog: Catalog,
    *,
    profile_id: str,
    provider_id: str,
    capability: Capability,
    redirect_uri: str,
    session_dir: Path,
    now: datetime | None = None,
) -> tuple[str, Path]:
    profile = next((item for item in catalog.profiles if item.id == profile_id), None)
    if profile is None:
        raise ValueError("unknown social profile")
    destination = next(
        (item for item in profile.destinations if item.provider_id == provider_id), None
    )
    if destination is None or capability not in destination.capabilities:
        raise ValueError("capability is not enabled for this profile destination")
    provider = next(item for item in catalog.providers if item.id == provider_id)
    if provider.connection_status != "available" or provider.oauth is None:
        raise ValueError("provider connection is not implemented yet")
    client_id = os.environ.get(provider.oauth.client_id_env)
    if not client_id:
        raise ValueError(f"missing {provider.oauth.client_id_env}")

    verifier = secrets.token_urlsafe(64)[:96] if provider.oauth.use_pkce else None
    challenge = None
    if verifier:
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    session = OAuthSession(
        provider_id=provider_id,
        profile_id=profile_id,
        capability=capability,
        redirect_uri=redirect_uri,
        state=secrets.token_urlsafe(48),
        code_verifier=verifier,
        scopes=scopes_for(catalog, provider_id, capability),
        created_at=now or datetime.now(timezone.utc),
    )
    session_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        session_dir.chmod(0o700)
    except OSError:
        pass
    path = session_dir / f"{session.state}.json"
    path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(session.scopes),
        "state": session.state,
        **provider.oauth.extra_authorize_params,
    }
    if challenge:
        params.update({"code_challenge": challenge, "code_challenge_method": "S256"})
    return f"{provider.oauth.authorize_url}?{urlencode(params)}", path


def consume_session(
    session_path: Path,
    *,
    returned_state: str,
    now: datetime | None = None,
    max_age: timedelta = timedelta(minutes=10),
) -> OAuthSession:
    session = OAuthSession.model_validate_json(session_path.read_text(encoding="utf-8"))
    current = now or datetime.now(timezone.utc)
    created = session.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if not secrets.compare_digest(session.state, returned_state):
        raise ValueError("OAuth state mismatch")
    if current - created > max_age:
        raise ValueError("OAuth session expired")
    session_path.unlink()
    return session


def token_form(catalog: Catalog, session: OAuthSession, code: str) -> tuple[str, dict[str, str]]:
    provider = next(item for item in catalog.providers if item.id == session.provider_id)
    assert provider.oauth is not None
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": os.environ[provider.oauth.client_id_env],
        "redirect_uri": session.redirect_uri,
    }
    if session.code_verifier:
        form["code_verifier"] = session.code_verifier
    if provider.oauth.client_secret_env:
        secret = os.environ.get(provider.oauth.client_secret_env)
        if not secret:
            raise ValueError(f"missing {provider.oauth.client_secret_env}")
        form["client_secret"] = secret
    return provider.oauth.token_url, form
