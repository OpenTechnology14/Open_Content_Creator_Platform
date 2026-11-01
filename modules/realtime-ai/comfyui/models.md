# ComfyUI models

Models are **not** committed. Download them once on first install, push to
MinIO `models/` for backup, and let your local `ComfyUI/models/checkpoints/`
folder mirror the bucket.

This table has no checksum or license column — it's a shopping list, not provenance. For a real
checksum and license record per downloaded weight, use
[`model-registry`](../../model-registry/README.md)'s `registry.yml` instead.

| Slot         | Recommended (size)               | Notes                              |
| ------------ | -------------------------------- | ---------------------------------- |
| checkpoint   | SDXL base 1.0 (~7 GB)            | High-quality stills                |
| checkpoint   | SDXL Turbo (~7 GB)               | Single-step generation             |
| checkpoint   | SD 1.5 (~4 GB)                   | Realtime LCM stylization candidate |
| LoRA         | LCM-LoRA SDXL (~50 MB)           | Pair with SDXL for fast inference  |
| LoRA         | LCM-LoRA SD1.5 (~50 MB)          | Pair with SD1.5 for realtime       |
| ControlNet   | Depth / Canny / Lineart SDXL     | Pose-locked stylization            |
| VAE          | SDXL VAE                         | Fixes washed-out colors            |
| upscaler     | 4x-UltraSharp                    | Pre-encode upscales                |

## Inpainting models (see [`image-editing`](../../image-editing/README.md))

| Slot         | Recommended (size)               | Notes                              |
| ------------ | -------------------------------- | ---------------------------------- |
| checkpoint   | SDXL Inpainting 0.1 (~7 GB)     | Best general inpainting            |
| checkpoint   | SD 1.5 Inpainting (~4 GB)       | Lightweight, fast edits            |
| checkpoint   | Flux Fill dev (~12 GB)           | Highest quality generative fill    |
| SAM          | SAM ViT-H (~2.5 GB)             | Auto-select / segment anything     |
| SAM          | SAM-HQ or MobileSAM (~400 MB)   | Faster auto-select, less accurate  |
| segmentation | RMBG-1.4 (~170 MB)              | Background removal / subject mask  |

## Ethics

Avoid:

- Reproducing copyrighted character LoRAs of real public figures.
- Anything trained on private/non-consensual datasets.

See [../setup/manual.md](../setup/manual.md) and
[../../image-editing/setup/manual.md](../../image-editing/setup/manual.md)
for the download workflows.

## Nature generation (see [`nature-generation`](../../nature-generation/README.md))

| Slot       | Recommended                  | Notes                                        |
| ---------- | ---------------------------- | -------------------------------------------- |
| IP-Adapter | IP-Adapter SDXL              | Tier 1 reference-conditioned restyle          |
| ControlNet | Depth SDXL                   | Relight and terrain occlusion                 |
| LoRA       | your nature adapters         | Tier 4 output — MinIO `models/nature/`        |

Lineart is deliberately **not** listed: there are no straight edges to preserve, and conditioning
foliage on lineart freezes texture that should vary.

## Cityscape generation (see [`cityscape-generation`](../../cityscape-generation/README.md))

| Slot       | Recommended                  | Notes                                        |
| ---------- | ---------------------------- | -------------------------------------------- |
| IP-Adapter | IP-Adapter SDXL              | Tier 1 reference-conditioned restyle          |
| ControlNet | **Lineart SDXL**             | **Required** at Tiers 2–3 — without it straight edges bend, window grids melt, signage becomes pseudo-text |
| ControlNet | Depth SDXL                   | Occlusion order; complementary to lineart, not a substitute |
| LoRA       | your cityscape adapters      | Tier 4 output — MinIO `models/cityscape/`. Day and night are separate adapters |

SAM ViT-H is already listed above for image-editing; both generation modules reuse it for region
selection rather than adding a second segmentation model.

Corpus intake for both: [`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md).
