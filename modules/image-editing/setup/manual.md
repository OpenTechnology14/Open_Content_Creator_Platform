# image-editing — manual setup

**Labels:** `Content` · Automated path: [automated.md](automated.md)

Krita + AI Diffusion inpainting, SAM auto-select, and tap-to-edit from a phone — all driving the
same ComfyUI backend.

## Prerequisites

ComfyUI installed and running — see [realtime-ai](../../realtime-ai/setup/manual.md). MinIO
running if you want `export_to_minio.py` — see
[storage-data](../../storage-data/setup/manual.md).

## Step 1 — Install Krita (5.2+)

| Platform | Install |
|---|---|
| macOS | `brew install --cask krita` or https://krita.org |
| Windows | https://krita.org/en/download/ |
| Linux | `sudo apt install krita`, Flatpak, or AppImage |

## Step 2 — Install the AI Diffusion plugin

1. Download the latest release from https://github.com/Acly/krita-ai-diffusion/releases
2. Krita → Settings → Manage Resources → Open Resource Folder
3. Extract the archive into the `pykrita/` subfolder
4. Restart Krita
5. Settings → Configure Krita → Python Plugin Manager → enable **AI Image Diffusion**

## Step 3 — Connect to ComfyUI

```bash
cd modules/realtime-ai/comfyui/app && python main.py
```

In Krita: Settings → AI Diffusion → Server URL `http://127.0.0.1:8188` → **Connect**. Green means
connected. The plugin will offer to install its required custom nodes through ComfyUI Manager on
first use.

## Step 4 — Inpainting models

Standard checkpoints can inpaint, but dedicated inpainting models are noticeably better at mask
boundaries.

```bash
cd modules/realtime-ai/comfyui/app/models/checkpoints
wget https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1/resolve/main/sd_xl_base_1.0_inpainting_0.1.safetensors
```

For auto-selection (tap a point → segment the object):

```bash
mkdir -p ../sam && cd ../sam
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
```

Record new entries in `modules/realtime-ai/comfyui/models.md`. **Never commit weights**
(`CLAUDE.md` §10).

## Scripts

- `krita/scripts/apply_style.py` — style application
- `krita/scripts/batch_upscale.py` — batch upscaling
- `krita/scripts/export_to_minio.py` — push results to the `project-assets` bucket

## Workflows

Real and committed: `workflows/inpaint-fill-v1.json`, `workflows/video-frame-edit-v1.json`.
Five others are indexed in the realtime-ai workflows README but **do not exist** — see
[automated.md](automated.md).

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] Krita's AI Diffusion panel shows a green connection to ComfyUI
- [ ] A masked region inpaints and the seam is not visible at 100% zoom
- [ ] `export_to_minio.py` lands a file in the bucket

### Last step — full feature test run

With setup complete, run this module's section of
[`../../../tests/ACCEPTANCE-CHECKLIST.md`](../../../tests/ACCEPTANCE-CHECKLIST.md) end to end.

**This does not block the next module.** A failing line is a finding against *this* module, not a
gate on starting another. The full checklist is a **release gate** — the platform is done when
every section passes, and not before.

Record what you ran in this module's row in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).
[`../../../docs/agent/VERIFICATION-MATRIX.md`](../../../docs/agent/VERIFICATION-MATRIX.md) requires
the command and its result — **"not run" is an acceptable answer; silence is not.**

If you find a manual step here that could be automated, automate it and delete the step. Driving
the manual count down is the measure of progress, not adding more of them.
## Troubleshooting

- **Plugin missing from the Python Plugin Manager** — extracted to the wrong folder; it must be
  `pykrita/`, not the resource root.
- **Connect fails** — ComfyUI is not running, or is bound to a different host than `127.0.0.1`.
- **Inpaint result ignores the mask** — a non-inpainting checkpoint is selected.
- **Workflow will not load** — six workflows are unverified templates, not GPU-run yet (P-028); the
  error usually names a `class_type` your installed custom node pack doesn't have. See
  [`../workflows/README.md`](../workflows/README.md)'s Status section and the failing file's own
  `_meta.status`/`_meta.required_nodes` for which pack and version it was written against.

Creator Extend has [per-run image, prompt and seed controls](../../content-creation/setup/workflow-inputs.md) for its bundled workflows. Required ComfyUI models/nodes remain separate installs.
