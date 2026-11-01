# Burst Rendering — Cloud GPU Offload

Offload non-realtime ComfyUI jobs (batch thumbnails, intros, slow-motion
stylization) to a DigitalOcean GPU droplet, freeing local VRAM for realtime
work.

## Architecture

```
FastAPI (local or DO) ── receives render job request
   │
   ▼
Redis queue (jobs:comfyui)
   │
   ▼
ComfyUI worker on DO GPU droplet (joined to tailnet)
   │
   ▼
Output → DO Spaces / MinIO
   │
   ▼
Local picks up result via webhook or polling
```

## Components

- `worker.py` — Queue consumer that pulls jobs from Redis, runs ComfyUI
  workflows, and uploads outputs to MinIO/Spaces
- FastAPI endpoint: `POST /api/v1/render/burst` (in `modules/backend-api`)
- Job format: workflow JSON + input references (images already in MinIO)
- Output: rendered images/video written to Spaces, metadata to Postgres

## Cost control

DO GPU droplets are billed per-hour. The worker includes auto-shutdown logic:

1. Worker starts, processes queued jobs
2. After N minutes idle (default: 15), worker calls the DO API to destroy
   its own droplet
3. Next job request spins up a fresh droplet via the DO API

This keeps costs near-zero when not rendering.

## Prerequisites

- [`broadcast-graphics`](../../../broadcast-graphics/setup/manual.md) complete (Redis + FastAPI running)
- [`infrastructure`](../../../infrastructure/setup/manual.md) complete (Tailscale networking, DO account)
- A DigitalOcean GPU droplet (or any cloud GPU with Docker + tailscale)

## Status

Scaffolded — architecture documented, ready for implementation after [`infrastructure`](../../../infrastructure/setup/manual.md).
Do NOT spin up a GPU droplet just to test — they cost USD per hour.

## Architecture

For **non-realtime** ComfyUI jobs — intro renders, batch thumbnails, slow-motion stylization —
offload to a cloud GPU rather than contending with the live path:

```
Local ComfyUI → job queue (Redis) → ComfyUI worker on a DO GPU droplet
                                  → output written to MinIO / DO Spaces
                                  → local picks up the result
```

`worker.py` in this folder is the worker side.

**Prerequisite: FastAPI and Redis must already be running.** This design has no queue of its own —
it borrows the one in [`storage-data`](../../../storage-data/setup/automated.md), stood up by
`make up`. Do not implement burst rendering before that exists.

Off by default. Nothing in the live path should ever wait on a burst job.

## Full deployment shape

The realistic step **before** Kubernetes:

```
FastAPI (local) — receives job request
   │
   ▼
Redis queue (jobs:comfyui)
   │
   ▼
ComfyUI worker on a DO GPU droplet (joined to the tailnet)
   │
   ▼
Output → DO Spaces / MinIO
   │
   ▼
Local picks up via webhook or polling
```

| Component | Detail |
|---|---|
| Worker | Slim ComfyUI install + queue consumer (`worker.py`) |
| Job format | Workflow JSON + inputs, uploaded to MinIO/Spaces; the worker pulls |
| Output | Image/video to Spaces; metadata to Postgres |
| Cost control | Workers auto-shutdown after N idle minutes via a DO API call |

The droplet joins the tailnet rather than exposing ports — see
[`infrastructure`](../../../infrastructure/setup/manual.md).

## Cost

**Do not spin up a GPU droplet "to play with it."** DO GPU droplets bill by the hour and are
expensive. Start one for a batch job, tear it down when the queue drains. The auto-shutdown above
is not an optimisation, it is the thing that stops an idle droplet quietly billing all weekend.

