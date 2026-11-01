# workflows — nature

Committed ComfyUI workflow JSON, one per tier. Same conventions as
[`realtime-ai/comfyui/workflows`](../../realtime-ai/comfyui/workflows/README.md): a leading `Note`
node documenting inputs and outputs, a version tag in the filename, no absolute paths.

## Index

**Nothing is on disk yet**, and this table says so — the sibling index in `realtime-ai` spent
months listing workflows that did not exist.

| Tier | File | Operation | Key nodes | Built? |
|---|---|---|---|---|
| 1 | `restyle-reference-v1.json` | Match a corpus image's look | IP-Adapter | no |
| 2 | `sky-replace-v1.json` | Replace sky, match scene light | SAM + inpaint | no |
| 2 | `outpaint-extend-v1.json` | Widen a scene | Outpaint | no |
| 2 | `relight-v1.json` | Change apparent time of day | ControlNet depth + inpaint | no |
| 3 | `generate-nature-v1.json` | New scene from an adapter | txt2img + LoRA | no |

Tier 0 has no workflow — it is not a ComfyUI operation. See [`../grading/`](../grading/README.md).

## Sky replacement is the flagship

It is the operation nature work needs most and the one diffusion handles best here: the sky is a
large, low-frequency region with no hard geometry, so a wrong pixel is invisible. Pair it with a
sky-only adapter if the corpus is large enough
([`../corpus/README.md`](../corpus/README.md)).

The hard part is not the sky — it is **matching the light on the ground to the new sky**. A
brilliant sunset over flatly-lit foreground reads as fake instantly. `relight-v1` exists to run
after `sky-replace-v1`, not instead of it.

## No lineart here

Unlike [cityscape](../../cityscape-generation/workflows/README.md), nature workflows do not need
ControlNet lineart — there are no straight edges to preserve. Depth is useful for terrain
occlusion and relighting; lineart on foliage actively hurts, freezing texture that should vary.

## Cross-module reuse

Tier 2 overlaps with [`image-editing/workflows`](../../image-editing/workflows/README.md), which
already ships `inpaint-fill-v1.json` with **two** consumers. Decide deliberately when Tier 2 is
built whether to reuse it — making its signature a contract across more modules — or ship a
nature-specific variant. Do not let it happen by default.

## Required models

Beyond the base checkpoints in
[`realtime-ai/comfyui/models.md`](../../realtime-ai/comfyui/models.md):

| Slot | Model | Purpose |
|---|---|---|
| IP-Adapter | IP-Adapter SDXL | Tier 1 |
| ControlNet | Depth SDXL | Relight, terrain occlusion |
| Segmentation | SAM ViT-H | Sky selection (already listed for image-editing) |
| LoRA | your nature adapters | [`../adapters/`](../adapters/README.md) |

Weights are never committed — MinIO `models/`.
