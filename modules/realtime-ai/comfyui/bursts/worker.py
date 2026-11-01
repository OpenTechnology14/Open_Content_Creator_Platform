#!/usr/bin/env python3
"""Burst render worker — consumes ComfyUI jobs from Redis and uploads results.

Runs on a cloud GPU droplet (DigitalOcean or similar). Connects to Redis
over Tailscale, pulls workflow + inputs, runs ComfyUI locally, and uploads
results to MinIO/DO Spaces.

Usage:
    python worker.py
    python worker.py --idle-timeout 900  # shutdown after 15 min idle
    python worker.py --queue jobs:comfyui --no-auto-shutdown

Requirements:
    pip install redis requests -r ../../../asset-pipeline/requirements.txt
    ComfyUI installed and runnable on this machine
    Tailscale connected to the same tailnet as the main platform

Environment variables (from .env):
    REDIS_URL          — redis://hcp-redis.tailnet.ts.net:6379/0
    MINIO_ENDPOINT     — hcp-minio.tailnet.ts.net:9000  (or DO Spaces)
    MINIO_ACCESS_KEY
    MINIO_SECRET_KEY
    COMFYUI_URL        — http://127.0.0.1:8188  (local on the worker)
    DO_API_TOKEN       — for auto-shutdown (optional)
    DO_DROPLET_ID      — this droplet's ID (optional, for auto-shutdown)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "asset-pipeline"))
from asset_pipeline import ensure_bucket, get_client, upload_bytes  # noqa: E402

log = logging.getLogger("burst_worker")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "comfyui-outputs")

DEFAULT_QUEUE = "jobs:comfyui"
DEFAULT_IDLE_TIMEOUT = 900  # 15 minutes


def get_redis():
    """Connect to Redis."""
    import redis
    return redis.from_url(REDIS_URL, decode_responses=True)


def run_comfyui_workflow(workflow: dict) -> list[str]:
    """Submit a workflow to the local ComfyUI and wait for output filenames."""
    import requests

    client_id = str(uuid.uuid4())
    resp = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
    )
    resp.raise_for_status()
    prompt_id = resp.json()["prompt_id"]

    # Poll for completion
    deadline = time.time() + 600  # 10 min max per job
    while time.time() < deadline:
        hist = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
        if prompt_id in hist:
            filenames = []
            for node_out in hist[prompt_id].get("outputs", {}).values():
                for img in node_out.get("images", []):
                    filenames.append(img["filename"])
            return filenames
        time.sleep(2)

    raise TimeoutError(f"ComfyUI did not finish {prompt_id} in 600s")


def upload_results(client, filenames: list[str], job_id: str) -> list[str]:
    """Download results from ComfyUI output dir and upload to MinIO."""
    import requests

    keys = []
    for fname in filenames:
        resp = requests.get(
            f"{COMFYUI_URL}/view",
            params={"filename": fname, "type": "output"},
        )
        resp.raise_for_status()
        key = f"burst/{job_id}/{fname}"
        upload_bytes(client, MINIO_BUCKET, key, resp.content, content_type="image/png")
        keys.append(key)
    return keys


def auto_shutdown():
    """Destroy this droplet via the DO API to save costs."""
    import requests

    token = os.getenv("DO_API_TOKEN")
    droplet_id = os.getenv("DO_DROPLET_ID")
    if not token or not droplet_id:
        log.warning("Auto-shutdown skipped — DO_API_TOKEN or DO_DROPLET_ID not set")
        return

    log.info("Auto-shutdown: destroying droplet %s", droplet_id)
    requests.delete(
        f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


def main(queue: str, idle_timeout: int, no_auto_shutdown: bool) -> None:
    """Main worker loop."""
    r = get_redis()
    client = get_client()
    # Fixed 2026-09-01 (P-017): this worker previously never called
    # ensure_bucket, unlike output_to_minio.py and export_to_minio.py which
    # both always had. It would hard-fail on the first upload against a
    # fresh MinIO instance / DO Spaces bucket with no prior setup step.
    ensure_bucket(client, MINIO_BUCKET)

    log.info("Burst worker started. Queue: %s, idle timeout: %ds", queue, idle_timeout)

    last_job_time = time.time()

    while True:
        # Blocking pop with 5s timeout
        result = r.brpop(queue, timeout=5)

        if result is None:
            # No job — check idle timeout
            idle_seconds = time.time() - last_job_time
            if idle_seconds > idle_timeout:
                log.info("Idle for %ds — shutting down.", int(idle_seconds))
                if not no_auto_shutdown:
                    auto_shutdown()
                sys.exit(0)
            continue

        _, raw = result
        last_job_time = time.time()

        try:
            job = json.loads(raw)
            job_id = job.get("id", str(uuid.uuid4()))
            workflow = job["workflow"]

            log.info("Processing job %s ...", job_id)
            filenames = run_comfyui_workflow(workflow)
            keys = upload_results(client, filenames, job_id)

            # Publish completion event
            r.publish("jobs:comfyui:done", json.dumps({
                "id": job_id,
                "status": "complete",
                "outputs": keys,
            }))
            log.info("Job %s complete — %d output(s)", job_id, len(keys))

        except Exception as e:
            log.error("Job failed: %s", e)
            r.publish("jobs:comfyui:done", json.dumps({
                "id": job_id,
                "status": "error",
                "error": str(e),
            }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Burst render worker for ComfyUI")
    parser.add_argument("--queue", default=DEFAULT_QUEUE, help="Redis queue name")
    parser.add_argument("--idle-timeout", type=int, default=DEFAULT_IDLE_TIMEOUT,
                        help="Seconds idle before auto-shutdown (default: 900)")
    parser.add_argument("--no-auto-shutdown", action="store_true",
                        help="Disable auto-shutdown (for local testing)")
    args = parser.parse_args()
    main(args.queue, args.idle_timeout, args.no_auto_shutdown)
