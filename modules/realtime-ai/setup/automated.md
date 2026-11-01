# realtime-ai — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

**There is no automated setup script for this module.** Everything here runs on the local GPU,
outside Compose, by design — `CLAUDE.md` §2 requires the latency-sensitive path to stay local.

## What exists

| Piece | State |
|---|---|
| `comfyui/scripts/output_to_minio.py` | Real — watches an output dir and uploads to MinIO |
| `comfyui/bridges/webcam_bridge.py` | Real — ~220 lines |
| `comfyui/bursts/worker.py` | Real — ~200 lines |
| `ar-filters/face_mesh_filter.py` | Real — ~195 lines |
| `background-removal/repaint_region.py` | Real — ~180 lines |

Running any of them is a manual `python` invocation; there is no launcher, no service, and no
Make target.

## Known documentation gap

`comfyui/workflows/README.md` indexes nine workflows. On disk there are three:
`00-starter.json` (a stub — `"nodes": []`), `realtime-lcm-stylize-v1.json`, and
`realtime-segmentation-v1.json`. Six indexed workflows do not exist anywhere in the repo:
`auto-select-sam-v1`, `background-replace-v1`, `inpaint-remove-v1`, `outpaint-expand-v1`,
`upscale-4x-v1`, `video-range-edit-v1`. Two others (`inpaint-fill-v1`, `video-frame-edit-v1`)
live under `modules/image-editing/workflows/`, not where the index says.

The retired Guide 4 additionally called for five content workflows (`thumbnail-1280x720`,
`title-card-1920x1080`, `lower-third-png-sequence`, `sports-overlay-style`,
`stylized-portrait-test`) — **none exist**.

Do not assume a workflow exists because it is indexed. Check the directory.

## What automation would take

A `make comfyui` target could create the venv, install requirements, and clone ComfyUI-Manager.
The model downloads cannot be automated in-repo — weights must never be committed
(`CLAUDE.md` §10) and each has its own license gate.

## Mobile control (the app path)

Stream Extend is specified to provide a mobile dashboard for this pipeline: toggle face effects,
switch segmentation models, adjust latency compensation, and watch VRAM — without alt-tabbing off
a live stream.

**Specified, not shipped** — `CLAUDE.md` §11 has this module at `scaffolded`. Everything in
[manual.md](manual.md) works without it.

## Monitoring this pipeline

The one piece of automation that *is* real: `observability`'s `source-health-exporter` polls
virtual cameras and AI service health, and the `ai-pipelines` Grafana dashboard covers ComfyUI /
DeepFaceLive fps, latency, and VRAM. Bring it up with `make up` — see
[observability](../../observability/setup/automated.md).

