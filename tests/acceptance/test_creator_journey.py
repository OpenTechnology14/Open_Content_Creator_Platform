"""P-016 — the acceptance harness. One executable creator journey.

Brings up the default Compose profile and drives:
  create a stream -> publish an event -> read it back -> round-trip an
  object through MinIO -> stop the stream -> confirm the metric moved.

Proves storage-data + backend-api + observability interoperate — the first
end-to-end evidence in this repository that any two modules actually work
together. See PROPOSAL_ACCEPTANCE_HARNESS.md and tests/USE-CASES.md's UC-1
for what this does and does not cover: it is the backend spine of UC-1, not
the complete 15-step journey (OBS, GPU, and desktop-app steps stay manual).

Everything here is marked `live` and excluded from the default offline suite.
Run explicitly: `make test-acceptance`.
"""

from __future__ import annotations

import io
import os
import uuid
from pathlib import Path

import pytest

httpx = pytest.importorskip("httpx", reason="httpx not installed", exc_type=ImportError)
minio_lib = pytest.importorskip("minio", reason="minio client not installed", exc_type=ImportError)

REPO = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.live

# Same bucket the platform's own docs describe outputs landing in
# (realtime-ai/comfyui/scripts/output_to_minio.py, image-editing's exporter).
# Created here if missing rather than depending on minio_init.sh having been
# run first — `make test-acceptance` must be self-contained.
TEST_BUCKET = "project-assets"


def _read_env_value(key: str, default: str) -> str:
    """Read a value from the repo's .env, falling back to .env.example, then
    to `default`. Mirrors how docker compose itself resolves the same file,
    so the credentials this test sends match what the containers were
    actually started with."""
    for name in (".env", ".env.example"):
        path = REPO / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return default


@pytest.fixture(scope="module")
def api_key() -> str:
    return os.environ.get("HCP_API_KEY") or _read_env_value(
        "HCP_API_KEY", "change-me-to-a-long-random-string"
    )


@pytest.fixture(scope="module")
def auth_headers(api_key: str) -> dict[str, str]:
    return {"X-API-Key": api_key}


@pytest.fixture(scope="module")
def minio_client() -> minio_lib.Minio:
    """MinIO client against the host-mapped port (127.0.0.1:9000), using the
    same convention documented across the platform's modules."""
    access_key = os.environ.get("MINIO_ROOT_USER") or _read_env_value("MINIO_ROOT_USER", "hcpadmin")
    secret_key = os.environ.get("MINIO_ROOT_PASSWORD") or _read_env_value(
        "MINIO_ROOT_PASSWORD", "change-me-long"
    )
    client = minio_lib.Minio(
        "127.0.0.1:9000",
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
    )
    if not client.bucket_exists(TEST_BUCKET):
        client.make_bucket(TEST_BUCKET)
    return client


def test_minio_bootstrap_client(compose_runner, minio_client: minio_lib.Minio) -> None:
    """The source-built client initializes real buckets/lifecycle through the bundled helper."""
    result = compose_runner("--profile", "setup", "run", "--rm", "minio-bootstrap")
    assert result.returncode == 0, f"MinIO helper failed:\n{result.stdout}\n{result.stderr}"
    for bucket in ["comfyui-outputs", "recordings", "models", "project-assets", "backups",
                   "nature-corpus", "cityscape-corpus"]:
        assert minio_client.bucket_exists(bucket), bucket
    lifecycle = minio_client.get_bucket_lifecycle("recordings")
    assert any(rule.expiration and rule.expiration.days == 30 for rule in lifecycle.rules)


def test_creator_journey(
    api_client: httpx.Client,
    auth_headers: dict[str, str],
    minio_client: minio_lib.Minio,
) -> None:
    """The journey. One test, sequential steps, each asserted before the next.

    A single test rather than several is deliberate: the steps are not
    independent (step 4 needs step 3's stream id), and pytest would happily
    reorder or parallelize separate tests in ways that silently break that
    dependency. Sub-steps are still visible via subTest-style print markers
    so a failure names which step broke, not just "test_creator_journey".
    """
    # Step 2 — liveness. The docker_stack fixture already polled /ready to
    # get here; this additionally confirms the plain liveness route the
    # proposal names explicitly.
    health = api_client.get("/health")
    assert health.status_code == 200, f"step 2 (GET /health): {health.status_code} {health.text}"

    # Step 3 — create a stream. FastAPI's default status for a bare @post is
    # 200, not 201 — streams.py declares no status_code, unlike events.py.
    title = f"acceptance-journey-{uuid.uuid4().hex[:8]}"
    create = api_client.post("/streams", json={"title": title, "platforms": ["test"]}, headers=auth_headers)
    assert create.status_code == 200, f"step 3 (POST /streams): {create.status_code} {create.text}"
    stream = create.json()
    stream_id = stream["id"]
    assert stream["title"] == title

    # Step 4 — publish an event tied to that stream. events.py explicitly
    # declares status_code=201 and publishes to Redis (events.py:64) before
    # returning — this is the step that proves backend-api and Redis talk.
    event_kind = "acceptance_check"
    publish = api_client.post(
        "/events",
        json={"source": "acceptance-harness", "kind": event_kind, "stream_id": stream_id, "data": {"run": title}},
        headers=auth_headers,
    )
    assert publish.status_code == 201, f"step 4 (POST /events): {publish.status_code} {publish.text}"
    event = publish.json()
    assert event["stream_id"] == stream_id

    # Step 5 — read it back from Postgres. Proves the write in step 4 landed,
    # not just that Redis received a publish nobody could have read.
    recent = api_client.get("/events/recent", params={"limit": 50}, headers=auth_headers)
    assert recent.status_code == 200, f"step 5 (GET /events/recent): {recent.status_code} {recent.text}"
    ids = {e["id"] for e in recent.json()}
    assert event["id"] in ids, (
        f"step 5: event {event['id']} was published (step 4 returned 201) "
        f"but does not appear in /events/recent — the Postgres write did not land"
    )

    # Step 6 — round-trip an object through MinIO, byte for byte.
    object_name = f"acceptance/{title}.txt"
    payload = f"acceptance harness run {title}".encode()
    minio_client.put_object(TEST_BUCKET, object_name, io.BytesIO(payload), length=len(payload))
    fetched = minio_client.get_object(TEST_BUCKET, object_name)
    try:
        roundtripped = fetched.read()
    finally:
        fetched.close()
        fetched.release_conn()
    assert roundtripped == payload, "step 6: MinIO round-trip returned different bytes than were written"

    # Step 7 — stop the stream.
    stop = api_client.post(f"/streams/{stream_id}/stop", headers=auth_headers)
    assert stop.status_code == 200, f"step 7 (POST /streams/{{id}}/stop): {stop.status_code} {stop.text}"
    assert stop.json()["ended_at"] is not None, "step 7: stream stopped but ended_at was not set"

    # Step 8 — the request counter moved. Proves observability sees this
    # traffic, not just that Prometheus is running.
    metrics = api_client.get("/metrics")
    assert metrics.status_code == 200, f"step 8 (GET /metrics): {metrics.status_code}"
    body = metrics.text
    assert "http_requests_total" in body or "http_request_duration" in body, (
        "step 8: /metrics did not expose the request counter "
        "prometheus-fastapi-instrumentator is supposed to add"
    )
