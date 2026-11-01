# ComfyUI workflows

Each `.json` here is a versioned, committable workflow. Conventions:

- File name: `NN-shortname.json` (NN sorts in load order).
- One workflow per file. No "scratch" or "experiment" JSON — those go in
  your local ComfyUI install only.
- Replace any absolute paths with `models/<file>` so the workflow loads
  on someone else's machine.
- If a workflow depends on a custom node, document it at the top of the
  file's metadata comment AND in this README.

## Index

| File                         | Purpose                                  | Required models              | Custom nodes |
| ---------------------------- | ---------------------------------------- | ---------------------------- | ------------ |
| `00-starter.json`            | Empty stub — copy when adding workflows  | —                            | —            |

### Image Editing Workflows ([`image-editing`](../../../image-editing/setup/manual.md))

Inpainting/editing workflows live in `modules/image-editing/workflows/` but
use the same ComfyUI instance. See that folder's README for model requirements.

| File (in image-editing/workflows/)  | Purpose                          | Required models              | Custom nodes         |
| ----------------------------------- | -------------------------------- | ---------------------------- | -------------------- |
| `inpaint-fill-v1.json`              | Generative fill (replace region) | SDXL Inpainting              | —                    |
| `inpaint-remove-v1.json`            | Remove object, reconstruct bg   | SDXL Inpainting              | —                    |
| `outpaint-expand-v1.json`           | Extend canvas with AI content   | SDXL Inpainting              | —                    |
| `upscale-4x-v1.json`               | Detail-preserving 4x upscale    | 4x-UltraSharp + SDXL        | UltimateSDUpscale    |
| `auto-select-sam-v1.json`           | Point → segment mask            | SAM ViT-H                   | ComfyUI-SAM          |
| `background-replace-v1.json`        | Auto-mask subject, replace bg   | RMBG-1.4 + SDXL             | RMBG node            |
| `video-frame-edit-v1.json`          | Edit single video frame         | SDXL Inpainting              | VideoHelperSuite     |
| `video-range-edit-v1.json`          | Edit frame range w/ propagation | SDXL Inpainting + RAFT      | VideoHelperSuite     |

Add new rows when you commit a workflow.

## Loading

ComfyUI → top-right menu → Load → pick the JSON. To make a workflow the
default for a stream, save it as `default.json` locally (don't commit).

---

## Versioning conventions

Every committed workflow JSON should carry:

- A leading **Note** node (from ComfyUI Manager) explaining inputs and outputs
- A version tag in the filename: `thumbnail-1280x720-v1.json`
- Its test inputs and expected outputs documented in this README

Workflows are the actual deliverable of the content-creation phase — they are committed; the
models they reference are not.

## Realtime framerate expectations

You will **not** get full-fidelity SDXL diffusion at 60 fps on consumer hardware. Measured
ballparks:

| Model | RTX 3060 (12 GB) | RTX 4070 (12 GB) | RTX 4090 (24 GB) |
|---|---|---|---|
| SD 1.5 + LCM-LoRA | 8–15 fps | 15–25 fps | 30+ fps |
| SDXL Turbo (1-step) | 5–10 fps | 10–15 fps | 20–30 fps |
| Full SDXL (20 steps) | <1 fps | 1–2 fps | 3–5 fps |
| Segmentation only (SAM / RMBG) | 20–30 fps | 30+ fps | 60+ fps |

For OBS use, target **LCM stylization** or **segmentation / ControlNet passes** — never full
diffusion. `realtime-lcm-stylize-v1.json` and `realtime-segmentation-v1.json` are the two
committed workflows that respect this.

## ReActor / face nodes — caveat

ReActor enables face swap inside a workflow. It is subject to the same consent constraint as any
face effect: **only swap to faces you hold rights to use**, and disclose synthetic likeness. If
you do not need it, do not install it.

## Index accuracy

This index has historically listed workflows that are not on disk. Verified state:

| Documented | Actually on disk |
|---|---|
| `00-starter.json` | present — but an **empty stub** (`"nodes": []`) |
| `realtime-lcm-stylize-v1.json` | present |
| `realtime-segmentation-v1.json` | present |
| `inpaint-fill-v1.json` | present, under `modules/image-editing/workflows/` |
| `video-frame-edit-v1.json` | present, under `modules/image-editing/workflows/` |
| `auto-select-sam-v1.json` | present (2026-09-01), under `modules/image-editing/workflows/` — **template only, not run against a real ComfyUI instance**; see its `_meta.status` |
| `background-replace-v1.json` | present (2026-09-01), under `modules/image-editing/workflows/` — **template only, not run** |
| `inpaint-remove-v1.json` | present (2026-09-01), under `modules/image-editing/workflows/` — **template only, not run** |
| `outpaint-expand-v1.json` | present (2026-09-01), under `modules/image-editing/workflows/` — **template only, not run** |
| `upscale-4x-v1.json` | present (2026-09-01), under `modules/image-editing/workflows/` — **template only, not run** |
| `video-range-edit-v1.json` | present (2026-09-01), under `modules/image-editing/workflows/` — **template only, not run**; its RAFT mask-warp step names a placeholder node class — see the file's own `_meta` |

Check this table before assuming a workflow exists. **"Present" here means the node graph is
committed and offline-structurally-checked (`tests/realtime_ai/test_workflows.py` — every
`class_type` present, every node reference resolves, every `_meta` block documents its
models/nodes) — it does not mean anyone has loaded it into a real ComfyUI and run inference.**
That needs a GPU this repo's CI does not have; per `docs/PROPOSALS.md` P-028, real-run
verification is explicitly left as owner work. Six of these were scaffolded from documented,
web-verified node names (2026-09-01) rather than hand-tested — expect to fix custom-node-name
mismatches on first real load, especially `video-range-edit-v1.json`'s flow-warp step. The five
content workflows once planned for this folder (`thumbnail-1280x720`, `title-card-1920x1080`,
`lower-third-png-sequence`, `sports-overlay-style`, `stylized-portrait-test`) were never written.

