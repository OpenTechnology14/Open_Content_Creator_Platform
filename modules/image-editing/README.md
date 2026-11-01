# Image Editing

**Labels:** `Content` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

AI-powered image and video editing using Krita + ComfyUI inpainting. Desktop plus a Creator Extend Mobile tap-to-edit path.

## Architecture

```
Desktop: Krita → AI Diffusion plugin → ComfyUI (localhost:8188)
Mobile:  Creator Extend app → FastAPI → ComfyUI (local GPU)
```

Both paths use the same ComfyUI backend and inpainting workflows. The desktop
path provides full layer-based editing in Krita. The mobile path provides
tap-to-select area editing via the Creator Extend app, similar to ComfyUI's
own mask editor.

## Submodules

| Folder       | Purpose                                                    |
| ------------ | ---------------------------------------------------------- |
| `krita/`     | Krita workspace presets, Python automation scripts          |
| `workflows/` | ComfyUI inpainting/outpainting/upscale workflow JSON files |
| `mobile/`    | FastAPI endpoints + specs for mobile editing UI            |

## Desktop: Krita + AI Diffusion

- **Krita** (free, open source) — full-featured image editor, layers, masks, brushes
- **Krita AI Diffusion** plugin (MIT) — connects to ComfyUI for generative fill, inpaint, outpaint, upscale
- Supports Flux 2, SDXL, SD 1.5, Illustrious models
- Works on NVIDIA (CUDA), AMD (ROCm/DirectML), Apple Silicon (MPS)

## Mobile: Creator Extend

- Tap/draw mask on image or video frame
- Send image + mask + prompt to ComfyUI via FastAPI
- Similar to ComfyUI's mask editor: paint areas, choose operations
- Video support: scrub to frame, select region, edit just that area
- Results saved to MinIO, synced back to device

## Required models (not committed)

See `modules/realtime-ai/comfyui/models.md` for the full model inventory.
Inpainting-specific models:

| Model                    | Purpose                      | VRAM   |
| ------------------------ | ---------------------------- | ------ |
| SDXL Inpainting          | High-quality region editing  | 10+ GB |
| Flux Fill (dev/schnell)  | Best quality generative fill | 12+ GB |
| SD 1.5 Inpainting        | Lightweight, fast editing    | 4+ GB  |
| RMBG-1.4 / SAM          | Auto-mask / subject select   | 2+ GB  |
| 4x-UltraSharp            | Detail-preserving upscale    | 2+ GB  |

## What lives where on disk

- Inpainting workflows: `workflows/*.json` (committed)
- Krita presets/workspace: `krita/presets/` (committed)
- Krita automation: `krita/scripts/` (committed)
- Mobile API spec: `mobile/` (committed)
- Model weights: MinIO `models/` bucket (never git)
- Edited outputs: MinIO `outputs/` bucket

## Two paths

| Path | What it is |
|---|---|
| **Desktop** | Full layer-based editing in Krita with the AI Diffusion plugin — masks, layers, history, batch operations, export to MinIO. See [`setup/manual.md`](setup/manual.md). |
| **Mobile** | Tap-to-select area editing, like ComfyUI's own mask editor: select an area on an image or video frame, type a prompt, and the edit runs **on your desktop GPU**. Spec at [`mobile/README.md`](mobile/README.md). |

The mobile path is a remote control, not a second inference stack — the GPU work stays on the
workstation either way, which is what keeps `CLAUDE.md` §2's local-first rule intact.

## Boundary with the generation modules

[`nature-generation`](../nature-generation/README.md) and
[`cityscape-generation`](../cityscape-generation/README.md) also do inpaint-based structural
edits. The split is about who drives:

| | this module | nature / cityscape generation |
|---|---|---|
| Driven by | A human, interactively, on one image | A corpus and a learned style, in batch |
| Interface | Krita plugin, mobile tap-to-edit | Config + CLI |
| Scope of an edit | The region you masked | Every image matching a selector |

Fix one photograph here. Make two hundred photographs agree with each other there. All three drive
the same ComfyUI backend, and `workflows/inpaint-fill-v1.json` may gain a third consumer — see
[`workflows/README.md`](workflows/README.md).

## Config docs

- [`krita/README.md`](krita/README.md) — plugin operations and the export scripts
- [`workflows/README.md`](workflows/README.md) — committed inpaint/video workflows
- [`mobile/README.md`](mobile/README.md) — the app-side tap-to-edit spec

