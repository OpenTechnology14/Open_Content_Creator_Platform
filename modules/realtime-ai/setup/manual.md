# realtime-ai — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

Face filters, background removal, and ComfyUI stylization on the local GPU, wired into OBS.

> **Ethics — read first.** Face-swap tooling depicts a real person's likeness. Use only your own
> face or one you have explicit consent to use, disclose synthetic likeness on stream, and never
> impersonate a real person. This is a hard constraint, not a suggestion.

## Prerequisites

OBS configured — see [creator-experience](../../creator-experience/setup/manual.md). An NVIDIA
GPU with ≥ 8 GB VRAM for realtime paths; more for SDXL.

## Pick the right tool

| Want | Use |
|---|---|
| Replace your face with another likeness | Face swap (DeepFaceLive / Deep-Live-Cam) |
| Glasses, masks, overlays tracking your face | AR lens filters (`ar-filters/face_mesh_filter.py`) |
| Remove or replace the background | OBS Background Removal plugin, or `background-removal/` |
| Restyle the whole frame | ComfyUI realtime (LCM) |

## OBS Background Removal plugin

Install the plugin, add it as a filter on your camera source, and pick a model. Lighter models
cost less GPU but hold edges worse — start light and only move up if the matte is unusable.
`background-removal/repaint_region.py` handles masked repaint beyond what the plugin does.

## ComfyUI

### Linux / WSL

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git modules/realtime-ai/comfyui/app
cd modules/realtime-ai/comfyui/app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121   # CUDA 12.1
```

### Windows

Use the official portable build: https://github.com/comfyanonymous/ComfyUI/releases

### ComfyUI Manager (non-negotiable)

```bash
cd modules/realtime-ai/comfyui/app/custom_nodes
git clone https://github.com/Comfy-Org/ComfyUI-Manager.git
```

The project moved from `ltdrdata/ComfyUI-Manager` to `Comfy-Org/ComfyUI-Manager` — the old URL
redirects (confirmed 2026-09-02, `P-043`) so an existing clone still works, but use the new one
for a fresh install. Restart ComfyUI. The Manager installs community nodes without cloning each by
hand.

## Models

Into `modules/realtime-ai/comfyui/app/models/checkpoints/`. **Never commit weights**
(`CLAUDE.md` §10). Track download links in `modules/realtime-ai/comfyui/models.md` — that table has
no checksum column (2026-09-01 correction; it previously claimed one). Real checksums belong in
[`model-registry`](../../model-registry/README.md)'s `registry.yml`: run
`python3 -m model_registry.cli checksum <file>` after downloading and add an entry there.

| Model | Purpose | VRAM |
|---|---|---|
| SDXL Base 1.0 | General generation | 10+ GB |
| SDXL Turbo | Fast / realtime | 8+ GB |
| SD 1.5 | Lightweight, many LoRAs | 4+ GB |
| RealVisXL | Photorealism | 10+ GB |
| ControlNet (Canny, Depth) | Constrained generation | varies |

Pick **one** SDXL and **one** SD 1.5 checkpoint to start.

## Realtime into OBS

Committed workflows that actually exist:

- `workflows/realtime-lcm-stylize-v1.json` — LCM stylization, the recommended starter
- `workflows/realtime-segmentation-v1.json` — segmentation only, highest fps

`comfyui/bridges/webcam_bridge.py` moves frames between the webcam, ComfyUI, and a virtual camera
OBS can capture.

> **Check before you rely on a workflow.** The workflows README indexes six files that do not
> exist, and `00-starter.json` is an empty stub. See [automated.md](automated.md) for the list.

### Latency budget

Every stage adds delay: capture → inference → virtual camera → OBS compositing → encode. Budget
it end to end, not per stage. If the encoder starts reporting overload, the GPU is contended
between inference and NVENC — lower the inference resolution before lowering stream bitrate.

## Deliverables

Commit workflow JSON. Never commit models, weights, or captured footage.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] ComfyUI serves at `127.0.0.1:8188` and the LCM workflow runs end to end
- [ ] The virtual camera appears as a source in OBS
- [ ] `output_to_minio.py` uploads a generated image to the `comfyui-outputs` bucket
- [ ] Stream holds target fps with the effect live

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

- **CUDA out of memory** — SDXL at full resolution alongside NVENC will not fit on 8 GB. Use
  SDXL Turbo or SD 1.5.
- **Virtual camera missing in OBS** — the virtual camera driver is not installed, or OBS was
  started before the bridge.
- **Workflow fails to load** — the file may be one of the six indexed-but-missing ones.
