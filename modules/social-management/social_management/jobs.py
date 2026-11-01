"""Approval-gated publishing and live destination preparation."""

from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from .connections import current_access_token
from .http import HttpTransport
from .models import Capability, Catalog, ConnectionRecord, PublishJob
from .vault import TokenVault


def plan_job(
    catalog: Catalog,
    connection: ConnectionRecord,
    *,
    capability: Capability,
    brand_id: str,
    text: str | None = None,
    media_path: Path | None = None,
    visibility: str = "private",
    approved: bool = False,
    ai_generated: bool = False,
    now: datetime | None = None,
) -> PublishJob:
    profile = next((item for item in catalog.profiles if item.id == connection.profile_id), None)
    if profile is None or brand_id not in profile.brand_ids:
        raise ValueError("connection profile or brand is not in the catalog")
    destination = next(
        (item for item in profile.destinations if item.provider_id == connection.provider_id), None
    )
    if destination is None or capability not in destination.capabilities:
        raise ValueError("capability is not enabled for this profile destination")
    provider = next(item for item in catalog.providers if item.id == connection.provider_id)
    if provider.connection_status != "available":
        raise ValueError("provider adapter is not available")
    required = set(provider.capability_scopes[capability])
    if not required <= set(connection.scopes):
        raise ValueError("connection does not have the scopes required for this job")
    if media_path is not None and (not media_path.is_file() or media_path.stat().st_size == 0):
        raise ValueError("media_path must be a non-empty local file")
    return PublishJob(
        id=f"job-{uuid.uuid4().hex[:20]}",
        profile_id=profile.id,
        provider_id=connection.provider_id,
        connection_id=connection.id,
        brand_id=brand_id,
        capability=capability,
        text=text,
        media_path=media_path,
        visibility=visibility,
        approved=approved,
        ai_generated=ai_generated,
        created_at=now or datetime.now(timezone.utc),
    )


def execute_job(
    catalog: Catalog,
    job: PublishJob,
    *,
    confirmation: str,
    connection: ConnectionRecord,
    vault: TokenVault,
    http: HttpTransport,
) -> dict:
    if not job.approved or confirmation != job.id:
        raise ValueError("publishing requires an approved job and its exact confirmation ID")
    if connection.id != job.connection_id or connection.provider_id != job.provider_id:
        raise ValueError("job connection does not match the verified connection record")
    provider = next(item for item in catalog.providers if item.id == job.provider_id)
    if provider.adapter == "discord" and job.capability == "post-text":
        token = vault.get(job.connection_id)
        webhook_url = token.get("webhook", {}).get("url")
        if not isinstance(webhook_url, str) or not webhook_url.startswith(
            ("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")
        ):
            raise ValueError("Discord connection has no valid incoming webhook")
        separator = "&" if "?" in webhook_url else "?"
        result = http.request(
            "POST",
            f"{webhook_url}{separator}wait=true",
            json_body={"content": job.text, "allowed_mentions": {"parse": []}},
        ).body
        return {"provider_id": "discord", "remote_id": result.get("id")}
    access_token = current_access_token(
        catalog,
        provider_id=job.provider_id,
        connection_id=job.connection_id,
        vault=vault,
        http=http,
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    if provider.adapter == "x" and job.capability == "post-text":
        result = http.request(
            "POST", "https://api.x.com/2/tweets", headers=headers, json_body={"text": job.text}
        ).body
        return {"provider_id": "x", "remote_id": result.get("data", {}).get("id")}
    if provider.adapter == "twitch" and job.capability == "live-stream":
        result = http.request(
            "GET",
            f"https://api.twitch.tv/helix/streams/key?{urlencode({'broadcaster_id': connection.account_id})}",
            headers={**headers, "Client-Id": _client_id(catalog, "twitch")},
        ).body
        key = result.get("data", [{}])[0].get("stream_key")
        if not key:
            raise ValueError("Twitch returned no stream key")
        return {"provider_id": "twitch", "ingest_url": f"rtmp://live.twitch.tv/app/{key}"}
    if provider.adapter == "youtube" and job.capability == "live-stream":
        return _prepare_youtube_live(job, headers, http)
    if provider.adapter == "youtube" and job.capability == "post-video":
        return _upload_youtube_video(job, headers, http)
    raise ValueError("this provider capability has no executable adapter")


def _client_id(catalog: Catalog, provider_id: str) -> str:
    import os

    provider = next(item for item in catalog.providers if item.id == provider_id)
    assert provider.oauth is not None
    value = os.environ.get(provider.oauth.client_id_env)
    if not value:
        raise ValueError(f"missing {provider.oauth.client_id_env}")
    return value


def _prepare_youtube_live(job: PublishJob, headers: dict[str, str], http: HttpTransport) -> dict:
    start = datetime.now(timezone.utc) + timedelta(minutes=5)
    title = job.text or "Open Content Creator Platform live stream"
    broadcast = http.request(
        "POST",
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet,status",
        headers=headers,
        json_body={
            "snippet": {"title": title[:100], "scheduledStartTime": start.isoformat()},
            "status": {"privacyStatus": job.visibility},
        },
    ).body
    stream = http.request(
        "POST",
        "https://www.googleapis.com/youtube/v3/liveStreams?part=snippet,cdn",
        headers=headers,
        json_body={
            "snippet": {"title": title[:100]},
            "cdn": {"ingestionType": "rtmp", "resolution": "variable", "frameRate": "variable"},
        },
    ).body
    broadcast_id, stream_id = broadcast.get("id"), stream.get("id")
    if not broadcast_id or not stream_id:
        raise ValueError("YouTube did not create the live resources")
    http.request(
        "POST",
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?{urlencode({'id': broadcast_id, 'streamId': stream_id, 'part': 'id,contentDetails'})}",
        headers=headers,
    )
    info = stream.get("cdn", {}).get("ingestionInfo", {})
    address, name = info.get("ingestionAddress"), info.get("streamName")
    if not address or not name:
        raise ValueError("YouTube did not return an ingest destination")
    return {"provider_id": "youtube", "remote_id": broadcast_id, "ingest_url": f"{address}/{name}"}


def _upload_youtube_video(job: PublishJob, headers: dict[str, str], http: HttpTransport) -> dict:
    assert job.media_path is not None
    content_type = mimetypes.guess_type(job.media_path.name)[0] or "application/octet-stream"
    metadata = {
        "snippet": {"title": (job.text or job.media_path.stem)[:100]},
        "status": {"privacyStatus": job.visibility},
    }
    init = http.request(
        "POST",
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            **headers,
            "X-Upload-Content-Length": str(job.media_path.stat().st_size),
            "X-Upload-Content-Type": content_type,
        },
        json_body=metadata,
    )
    location = next(
        (value for key, value in init.headers.items() if key.lower() == "location"), None
    )
    if not location:
        raise ValueError("YouTube did not return a resumable upload URL")
    result = http.request(
        "PUT", location, headers={"Content-Type": content_type}, raw=job.media_path.read_bytes()
    ).body
    return {"provider_id": "youtube", "remote_id": result.get("id")}
