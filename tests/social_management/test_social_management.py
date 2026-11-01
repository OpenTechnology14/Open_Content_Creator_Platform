from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import yaml

MODULE = Path(__file__).resolve().parents[2] / "modules" / "social-management"
sys.path.insert(0, str(MODULE))

from social_management.connections import (  # noqa: E402
    complete_connection,
    current_access_token,
    disconnect_connection,
)
from social_management.http import Response  # noqa: E402
from social_management.jobs import execute_job, plan_job  # noqa: E402
from social_management.models import OAuthSession  # noqa: E402
from social_management.oauth import begin_authorization, consume_session  # noqa: E402
from social_management.profiles import ProfileStore  # noqa: E402
from social_management.registry import load_catalog, profile_options, provider_options  # noqa: E402
from social_management.ui import LoopbackThreadingHTTPServer, PAGE  # noqa: E402
from social_management.vault import ConnectionStore, MemoryVault  # noqa: E402


class FakeHttp:
    def __init__(self, responses: list[Response]) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, str, dict]] = []

    def request(self, method: str, url: str, **kwargs) -> Response:
        self.requests.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError(f"unexpected request: {method} {url}")
        return self.responses.pop(0)


def test_catalog_exposes_profiles_brands_and_honest_provider_states() -> None:
    catalog = load_catalog()
    profiles = {item["value"]: item for item in profile_options(catalog)}
    assert set(profiles) == {
        "stream-main",
        "content-main",
        "opentech-marketing",
        "video-review",
        "agent-labs",
    }
    assert profiles["opentech-marketing"]["default_brand_id"] == "opentechapp"
    assert {brand["value"] for brand in profiles["opentech-marketing"]["brands"]} == {
        "opentechapp",
        "hybrid-platform",
        "stream-extend",
        "creator-extend",
    }
    destinations = {item["value"]: item for item in provider_options(catalog, "content-main")}
    assert destinations["youtube"]["connection_status"] == "available"
    assert destinations["discord"]["connection_status"] == "available"
    assert destinations["tiktok"]["connection_status"] == "registration-required"
    stream_destinations = {item["value"]: item for item in provider_options(catalog, "stream-main")}
    assert stream_destinations["kick"]["connection_status"] == "planned"
    assert stream_destinations["restream"]["connection_status"] == "planned"
    assert '<select id="profile">' in PAGE
    assert '<select id="brand">' in PAGE


def test_loopback_server_binds_without_hostname_resolution() -> None:
    server = LoopbackThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    try:
        assert server.server_name == "127.0.0.1"
        assert server.server_port > 0
    finally:
        server.server_close()


def test_show_profiles_are_mapped_to_social_profiles() -> None:
    catalog = load_catalog()
    stream_programming = yaml.safe_load(
        (MODULE.parents[1] / "configs/local/stream-programming.yaml").read_text()
    )
    expected = {
        "flight-simulator-agent",
        "beamng-agent",
        "roblox-agent",
        "opentech-marketing",
        "marketing-stream-extend",
        "marketing-content-extend",
        "marketing-ai-learning",
        "marketing-ai-control-layer",
        "marketing-chatbot-routing",
        "video-review",
    }
    actual = {name for profile in catalog.profiles for name in profile.show_profile_ids}
    configured = {item["id"] for item in stream_programming["profiles"]}
    assert expected <= actual
    assert actual <= configured


def test_custom_profile_is_private_validated_and_joins_dropdown(tmp_path: Path) -> None:
    from social_management.models import Destination, SocialProfile

    store = ProfileStore(tmp_path / "state" / "profiles.json", load_catalog())
    store.put(
        SocialProfile(
            id="minecraft-tutorials",
            display_name="Minecraft Tutorials",
            kind="hybrid",
            brand_ids=["stream-extend", "creator-extend"],
            default_brand_id="stream-extend",
            destinations=[
                Destination(
                    provider_id="youtube",
                    capabilities=["account-read", "live-stream", "post-video"],
                    account_label="Tutorial channel",
                )
            ],
        )
    )
    options = {item["value"] for item in profile_options(store.catalog())}
    assert "minecraft-tutorials" in options
    if os.name != "nt":
        assert store.path.stat().st_mode & 0o777 == 0o600
    invalid = store.read()[0].model_copy(
        update={
            "destinations": [
                Destination(provider_id="youtube", capabilities=["post-image"], account_label="Bad")
            ]
        }
    )
    with pytest.raises(ValueError, match="not declared"):
        store.put(invalid)
    assert store.read()[0].destinations[0].capabilities == [
        "account-read",
        "live-stream",
        "post-video",
    ]


def test_pkce_authorization_is_scoped_and_private(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOCIAL_YOUTUBE_CLIENT_ID", "public-client")
    catalog = load_catalog()
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    url, session_path = begin_authorization(
        catalog,
        profile_id="stream-main",
        provider_id="youtube",
        capability="live-stream",
        redirect_uri="http://127.0.0.1:8765/oauth/callback",
        session_dir=tmp_path / "sessions",
        now=now,
    )
    query = parse_qs(urlparse(url).query)
    assert query["client_id"] == ["public-client"]
    assert query["code_challenge_method"] == ["S256"]
    assert "https://www.googleapis.com/auth/youtube" in query["scope"][0]
    payload = json.loads(session_path.read_text())
    assert payload["code_verifier"] not in url
    if os.name != "nt":
        assert session_path.stat().st_mode & 0o777 == 0o600
        assert session_path.parent.stat().st_mode & 0o777 == 0o700


def test_oauth_session_rejects_state_mismatch_and_expiry(tmp_path: Path) -> None:
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    session = OAuthSession(
        provider_id="x",
        profile_id="content-main",
        capability="post-text",
        redirect_uri="http://127.0.0.1:8765/oauth/callback",
        state="s" * 32,
        code_verifier="v" * 43,
        scopes=["tweet.write"],
        created_at=now,
    )
    path = tmp_path / "session.json"
    path.write_text(session.model_dump_json())
    with pytest.raises(ValueError, match="state mismatch"):
        consume_session(path, returned_state="z" * 32, now=now)
    with pytest.raises(ValueError, match="expired"):
        consume_session(path, returned_state="s" * 32, now=now + timedelta(minutes=11))
    assert path.exists()


def test_complete_x_connection_keeps_token_out_of_public_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOCIAL_X_CLIENT_ID", "x-client")
    catalog = load_catalog()
    session = OAuthSession(
        provider_id="x",
        profile_id="content-main",
        capability="post-text",
        redirect_uri="http://127.0.0.1:8765/oauth/callback",
        state="s" * 32,
        code_verifier="v" * 43,
        scopes=["offline.access", "tweet.read", "tweet.write", "users.read"],
        created_at=datetime.now(timezone.utc),
    )
    http = FakeHttp(
        [
            Response(
                200,
                {
                    "access_token": "secret-token",
                    "refresh_token": "secret-refresh",
                    "scope": "offline.access tweet.read tweet.write users.read",
                },
                {},
            ),
            Response(200, {"data": {"id": "42", "name": "Open Tech", "username": "open_tech"}}, {}),
        ]
    )
    vault = MemoryVault()
    store = ConnectionStore(tmp_path / "state" / "connections.json")
    record = complete_connection(
        catalog, session, code="authorization-code", http=http, vault=vault, store=store
    )
    assert record.account_name == "open_tech"
    assert vault.get(record.id)["refresh_token"] == "secret-refresh"
    public = store.path.read_text()
    assert "secret-token" not in public and "secret-refresh" not in public
    assert "open_tech" in public
    if os.name != "nt":
        assert store.path.stat().st_mode & 0o777 == 0o600


def test_disconnect_removes_both_public_record_and_private_token(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOCIAL_X_CLIENT_ID", "x-client")
    catalog = load_catalog()
    session = OAuthSession(
        provider_id="x",
        profile_id="content-main",
        capability="post-text",
        redirect_uri="http://127.0.0.1:8765/oauth/callback",
        state="s" * 32,
        code_verifier="v" * 43,
        scopes=["offline.access", "tweet.read", "tweet.write", "users.read"],
        created_at=datetime.now(timezone.utc),
    )
    http = FakeHttp(
        [
            Response(
                200,
                {
                    "access_token": "secret-token",
                    "scope": "offline.access tweet.read tweet.write users.read",
                },
                {},
            ),
            Response(200, {"data": {"id": "42", "username": "open_tech"}}, {}),
        ]
    )
    vault = MemoryVault()
    store = ConnectionStore(tmp_path / "state" / "connections.json")
    record = complete_connection(
        catalog, session, code="authorization-code", http=http, vault=vault, store=store
    )
    removed = disconnect_connection(connection_id=record.id, vault=vault, store=store)
    assert removed.id == record.id
    assert store.read() == []
    with pytest.raises(ValueError, match="missing"):
        vault.get(record.id)


def test_discord_connection_keeps_webhook_in_vault(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOCIAL_DISCORD_CLIENT_ID", "discord-client")
    monkeypatch.setenv("SOCIAL_DISCORD_CLIENT_SECRET", "discord-secret")
    catalog = load_catalog()
    session = OAuthSession(
        provider_id="discord",
        profile_id="content-main",
        capability="post-text",
        redirect_uri="http://127.0.0.1:8765/oauth/callback",
        state="s" * 32,
        scopes=["identify", "webhook.incoming"],
        created_at=datetime.now(timezone.utc),
    )
    http = FakeHttp(
        [
            Response(
                200,
                {
                    "access_token": "discord-access",
                    "refresh_token": "discord-refresh",
                    "scope": "identify webhook.incoming",
                    "webhook": {
                        "id": "123456",
                        "channel_id": "987654",
                        "name": "OpenTech announcements",
                        "url": "https://discord.com/api/webhooks/123456/private-token",
                    },
                },
                {},
            )
        ]
    )
    vault = MemoryVault()
    store = ConnectionStore(tmp_path / "state" / "connections.json")
    record = complete_connection(
        catalog, session, code="authorization-code", http=http, vault=vault, store=store
    )
    assert record.account_name == "OpenTech announcements"
    assert vault.get(record.id)["webhook"]["url"].endswith("/private-token")
    assert "private-token" not in store.path.read_text()


def test_expired_token_refreshes_in_the_vault(monkeypatch) -> None:
    monkeypatch.setenv("SOCIAL_X_CLIENT_ID", "x-client")
    vault = MemoryVault()
    vault.set(
        "connection-1",
        {
            "access_token": "expired",
            "refresh_token": "refresh-secret",
            "scope": "tweet.write users.read",
            "_hcp_expires_at": "2026-09-10T11:00:00+00:00",
        },
    )
    http = FakeHttp([Response(200, {"access_token": "current", "expires_in": 7200}, {})])
    access = current_access_token(
        load_catalog(),
        provider_id="x",
        connection_id="connection-1",
        vault=vault,
        http=http,
        now=datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert access == "current"
    assert vault.get("connection-1")["refresh_token"] == "refresh-secret"
    assert http.requests[0][2]["form"]["grant_type"] == "refresh_token"


def test_x_publish_requires_approval_and_exact_confirmation(tmp_path: Path) -> None:
    catalog = load_catalog()
    now = datetime.now(timezone.utc)
    from social_management.models import ConnectionRecord

    connection = ConnectionRecord(
        id="content-main-x-123",
        profile_id="content-main",
        provider_id="x",
        account_id="42",
        account_name="open_tech",
        scopes=["offline.access", "tweet.read", "tweet.write", "users.read"],
        connected_at=now,
        verified_at=now,
    )
    job = plan_job(
        catalog,
        connection,
        capability="post-text",
        brand_id="creator-extend",
        text="New build",
        approved=False,
    )
    vault = MemoryVault()
    vault.set(connection.id, {"access_token": "secret"})
    with pytest.raises(ValueError, match="approved job"):
        execute_job(
            catalog, job, confirmation=job.id, connection=connection, vault=vault, http=FakeHttp([])
        )
    approved = job.model_copy(update={"approved": True})
    http = FakeHttp([Response(201, {"data": {"id": "remote-7"}}, {})])
    result = execute_job(
        catalog, approved, confirmation=approved.id, connection=connection, vault=vault, http=http
    )
    assert result == {"provider_id": "x", "remote_id": "remote-7"}
    assert http.requests[0][2]["json_body"] == {"text": "New build"}


def test_discord_publish_uses_webhook_without_mentions() -> None:
    catalog = load_catalog()
    now = datetime.now(timezone.utc)
    from social_management.models import ConnectionRecord

    connection = ConnectionRecord(
        id="content-main-discord-123",
        profile_id="content-main",
        provider_id="discord",
        account_id="123",
        account_name="announcements",
        scopes=["identify", "webhook.incoming"],
        connected_at=now,
        verified_at=now,
    )
    job = plan_job(
        catalog,
        connection,
        capability="post-text",
        brand_id="creator-extend",
        text="New video is ready",
        approved=True,
    )
    vault = MemoryVault()
    vault.set(
        connection.id,
        {
            "access_token": "unused",
            "webhook": {"url": "https://discord.com/api/webhooks/123/private"},
        },
    )
    http = FakeHttp([Response(200, {"id": "message-9"}, {})])
    result = execute_job(
        catalog, job, confirmation=job.id, connection=connection, vault=vault, http=http
    )
    assert result == {"provider_id": "discord", "remote_id": "message-9"}
    assert http.requests[0][1].endswith("/123/private?wait=true")
    assert http.requests[0][2]["json_body"] == {
        "content": "New video is ready",
        "allowed_mentions": {"parse": []},
    }


def test_twitch_live_target_is_ephemeral(monkeypatch) -> None:
    monkeypatch.setenv("SOCIAL_TWITCH_CLIENT_ID", "twitch-client")
    catalog = load_catalog()
    now = datetime.now(timezone.utc)
    from social_management.models import ConnectionRecord

    connection = ConnectionRecord(
        id="stream-main-twitch-123",
        profile_id="stream-main",
        provider_id="twitch",
        account_id="99",
        account_name="channel",
        scopes=["channel:read:stream_key", "user:read:email"],
        connected_at=now,
        verified_at=now,
    )
    job = plan_job(
        catalog, connection, capability="live-stream", brand_id="stream-extend", approved=True
    )
    vault = MemoryVault()
    vault.set(connection.id, {"access_token": "secret"})
    http = FakeHttp([Response(200, {"data": [{"stream_key": "live-secret"}]}, {})])
    result = execute_job(
        catalog, job, confirmation=job.id, connection=connection, vault=vault, http=http
    )
    assert result["ingest_url"] == "rtmp://live.twitch.tv/app/live-secret"
    assert "broadcaster_id=99" in http.requests[0][1]


def test_youtube_live_creates_and_binds_ephemeral_destination() -> None:
    catalog = load_catalog()
    now = datetime.now(timezone.utc)
    from social_management.models import ConnectionRecord

    connection = ConnectionRecord(
        id="stream-main-youtube-123",
        profile_id="stream-main",
        provider_id="youtube",
        account_id="channel-7",
        account_name="Main channel",
        scopes=[
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.readonly",
        ],
        connected_at=now,
        verified_at=now,
    )
    job = plan_job(
        catalog,
        connection,
        capability="live-stream",
        brand_id="stream-extend",
        text="Test live",
        approved=True,
    )
    vault = MemoryVault()
    vault.set(connection.id, {"access_token": "secret"})
    http = FakeHttp(
        [
            Response(200, {"id": "broadcast-1"}, {}),
            Response(
                200,
                {
                    "id": "stream-1",
                    "cdn": {
                        "ingestionInfo": {
                            "ingestionAddress": "rtmp://youtube.test/app",
                            "streamName": "private-key",
                        }
                    },
                },
                {},
            ),
            Response(200, {"id": "broadcast-1"}, {}),
        ]
    )
    result = execute_job(
        catalog,
        job,
        confirmation=job.id,
        connection=connection,
        vault=vault,
        http=http,
    )
    assert result == {
        "provider_id": "youtube",
        "remote_id": "broadcast-1",
        "ingest_url": "rtmp://youtube.test/app/private-key",
    }
    assert "/liveBroadcasts/bind?" in http.requests[2][1]


def test_youtube_private_video_uses_resumable_upload(tmp_path: Path) -> None:
    catalog = load_catalog()
    now = datetime.now(timezone.utc)
    from social_management.models import ConnectionRecord

    connection = ConnectionRecord(
        id="content-main-youtube-123",
        profile_id="content-main",
        provider_id="youtube",
        account_id="channel-7",
        account_name="Main channel",
        scopes=[
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.upload",
        ],
        connected_at=now,
        verified_at=now,
    )
    media = tmp_path / "short.mp4"
    media.write_bytes(b"video-bytes")
    job = plan_job(
        catalog,
        connection,
        capability="post-video",
        brand_id="creator-extend",
        text="Private short",
        media_path=media,
        approved=True,
    )
    vault = MemoryVault()
    vault.set(connection.id, {"access_token": "secret"})
    http = FakeHttp(
        [
            Response(200, {}, {"Location": "https://upload.youtube.test/session"}),
            Response(200, {"id": "video-1"}, {}),
        ]
    )
    result = execute_job(
        catalog,
        job,
        confirmation=job.id,
        connection=connection,
        vault=vault,
        http=http,
    )
    assert result == {"provider_id": "youtube", "remote_id": "video-1"}
    assert http.requests[0][2]["json_body"]["status"]["privacyStatus"] == "private"
    assert http.requests[1][2]["raw"] == b"video-bytes"


def test_catalog_only_provider_cannot_begin_authorization(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not implemented"):
        begin_authorization(
            load_catalog(),
            profile_id="content-main",
            provider_id="tiktok",
            capability="post-video",
            redirect_uri="http://127.0.0.1:8765/oauth/callback",
            session_dir=tmp_path,
        )
