# Krita + AI Diffusion Setup

Desktop AI image editing. Krita provides the canvas, layers, and selection
tools. The AI Diffusion plugin connects to your existing ComfyUI instance
for generative fill, inpainting, outpainting, and upscaling.

## Install Krita

- **All platforms:** https://krita.org/en/download/
- Version 5.2+ required (Qt6 build recommended)
- macOS: `brew install --cask krita`
- Linux: `sudo apt install krita` or Flatpak

## Install AI Diffusion Plugin

1. Open Krita → Settings → Manage Resources → Open Resource Folder
2. Download latest release from https://github.com/Acly/krita-ai-diffusion/releases
3. Extract into Krita's `pykrita/` folder
4. Restart Krita → Settings → Configure Krita → Python Plugin Manager
5. Enable "AI Image Diffusion"

Or install via Krita's built-in plugin manager if available.

## Connect to ComfyUI

The plugin uses ComfyUI as its backend. If ComfyUI is already running
(from [`realtime-ai`](../../realtime-ai/setup/manual.md)), the plugin auto-connects:

1. Open Krita → Settings → AI Diffusion
2. Server URL: `http://127.0.0.1:8188`
3. Click "Connect" — should show green status

If ComfyUI is not running, the plugin can install and manage its own
instance, but using the shared one avoids duplicate model downloads.

## Required ComfyUI Custom Nodes

The AI Diffusion plugin will prompt you to install these via ComfyUI
Manager if missing:

- `ComfyUI_IPAdapter_plus` — style transfer
- `comfyui_controlnet_aux` — preprocessors (Canny, Depth, etc.)
- `ComfyUI-GGUF` — quantized model support
- `ComfyUI_UltimateSDUpscale` — tiled upscaling

## Workspace Presets

**`presets/` is empty today** (verified 2026-09-01, `P-037`) — this section previously named two
specific files, `ai-editing.kws` and `batch-review.kws`, that don't exist. The intent still stands:
a Krita workspace layout (AI panel docked, layer list visible, minimal toolbar; a second for
side-by-side output review) would go here, exported via Krita's own **Window → Workspace → Create
Workspace**, then **Settings → Manage Resources → Import** on another machine. Nobody has built or
exported one yet.

`apply_style.py`'s `STYLE_PRESETS` (anime/watercolor/oil/pixel/cinematic) are a separate, unrelated
thing despite the shared "preset" name — they're IPAdapter weight/denoise tuning values baked into
that script, not files in this folder. See that script's own docstring for the distinction, and
its noted limitation: without a per-style reference image, presets differentiate by generic
strength tuning only, not by a distinct visual look.

## Key Operations

| Adobe Photoshop Feature | Krita + AI Diffusion |
| ----------------------- | -------------------- |
| Generative Fill         | Select area → AI Generate (fill) |
| Generative Expand       | Extend canvas → AI Generate (outpaint) |
| Remove Tool             | Paint mask → AI Generate (remove) |
| Content-Aware Fill      | Select → AI Inpaint |
| Neural Filters          | AI Refine (style/detail) |
| Super Resolution        | AI Upscale (2x/4x) |
| Sky Replacement         | Quick-select sky → AI Generate |
| Object Selection        | SAM auto-select → Edit |

All operations output to a new layer (non-destructive).

## Automation Scripts

`scripts/` contains Krita Python scripts for batch operations:

- `batch_upscale.py` — Upscale all images in a folder via ComfyUI
- `export_to_minio.py` — Save current document layers to MinIO
- `apply_style.py` — Apply a style preset to the current selection

## Core operations

All five run through the AI Diffusion panel against your ComfyUI instance.

| Operation | How |
|---|---|
| **Generative fill** | Select an area (rectangle, lasso, magic wand) → type what should fill it → Generate. Result arrives as a new layer. |
| **Remove object** | Paint over it with the mask brush → leave the prompt empty or type "clean background" → Generate. |
| **Outpaint** | Image → Canvas Size, expand in the desired direction → select the new empty area → prompt describing the extension → Generate. |
| **Upscale** | AI Diffusion → Upscale mode → 2x or 4x → Generate. Detail-preserving super-resolution. |
| **Auto-select + edit** | AI Diffusion → Selection mode → click an object; SAM segments it → type the replacement → Generate. Only the selected object changes. |

Results always land as a **new layer** — nothing is destructive, so an unwanted generation is a
layer delete rather than an undo chain.

Auto-select needs the SAM checkpoint; see [`../setup/manual.md`](../setup/manual.md).

## Scripts

| Script | Purpose |
|---|---|
| `modules/image-editing/krita/scripts/apply_style.py` | Style application |
| `modules/image-editing/krita/scripts/batch_upscale.py` | Batch upscaling |
| `modules/image-editing/krita/scripts/export_to_minio.py` | Push results to the `project-assets` bucket |

