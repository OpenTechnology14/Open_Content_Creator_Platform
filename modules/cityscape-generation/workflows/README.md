# workflows — cityscape

Committed ComfyUI workflow JSON, one per tier. Conventions as in
[`realtime-ai/comfyui/workflows`](../../realtime-ai/comfyui/workflows/README.md).

## Index

**Nothing is on disk yet**, and this table says so.

| Tier | File | Operation | Key nodes | Built? |
|---|---|---|---|---|
| 1 | `restyle-reference-v1.json` | Match a corpus image's look | IP-Adapter | no |
| 2 | `facade-repair-v1.json` | Fix or replace a facade region | Inpaint + **lineart** | no |
| 2 | `outpaint-extend-v1.json` | Widen a scene | Outpaint + **lineart** | no |
| 2 | `relight-v1.json` | Day↔night, change lighting | ControlNet depth + inpaint | no |
| 2 | `sign-remove-v1.json` | Remove signage rather than regenerate it | Inpaint | no |
| 3 | `generate-cityscape-v1.json` | New scene from an adapter | txt2img + LoRA + **lineart** | no |

Tier 0 has no workflow — perspective and tone are not ComfyUI operations. See
[`../grading/`](../grading/README.md).

## Lineart is required, not optional

Every structural workflow above carries ControlNet lineart, and the nature equivalents do not.
This is the single largest difference between the two modules.

Without lineart conditioning, diffusion bends straight edges, misaligns window grids, and produces
unreadable pseudo-text on signage. The output is not lower quality — it is unusable. Weight it
high (0.7–1.0) and only reduce if the result looks traced rather than generated.

Depth is complementary, not a substitute: depth preserves *occlusion order*, lineart preserves
*edges*. Buildings need both; a depth-only graph still bends.

## Resolution strategy

**Generate above target and downscale.** Repeating small structures — window grids, balcony rails,
brickwork — survive downscaling and do not survive upscaling. A 1536px generation downscaled to
1024 holds grids that a native 1024 generation melts.

## Signage: removal, not generation

`sign-remove-v1` exists because the alternative does not work. Models produce text-shaped noise,
and no amount of prompting yields legible signage. Three honest options:

1. Mask signage out and inpaint it away
2. Compose to avoid readable text
3. Accept illegible text as a stylistic choice

Do not add a fourth by trying to prompt around it.

## Cross-module reuse

Tier 2 overlaps with [`image-editing/workflows`](../../image-editing/workflows/README.md), whose
`inpaint-fill-v1.json` already has **two** consumers. The cityscape variants need lineart
conditioning that file does not carry, so a **separate variant is likely correct here** — unlike
nature, where reuse is plausible. Decide when Tier 2 is built; record the decision.

## Required models

| Slot | Model | Purpose |
|---|---|---|
| IP-Adapter | IP-Adapter SDXL | Tier 1 |
| ControlNet | **Lineart SDXL** | **Required** — Tiers 2–3 |
| ControlNet | Depth SDXL | Occlusion, relight |
| Segmentation | SAM ViT-H | Region selection (already listed for image-editing) |
| LoRA | your cityscape adapters | [`../adapters/`](../adapters/README.md) |

Weights are never committed — MinIO `models/`.
