# Realtime AI

**Labels:** `Content` `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

GPU-bound, low-latency inference. Everything here is local-first.

| Submodule              | Label | Purpose                              |
| ---------------------- | ----- | ------------------------------------ |
| `deepfacelive/`        | `Stream` | Face swap (replaces the face)     |
| `deep-live-cam/`       | `Stream` | Alternative face-swap tool        |
| `liveportrait/`        | `Stream` | Animate a portrait from webcam    |
| `ar-filters/`          | `Stream` | AR lens-style sprite overlays (Snapchat genre — doesn't touch the face) |
| `background-removal/`  | `Stream` | OBS plugin recipes + model picks + masked-region background repaint |
| `comfyui/`             | `Content` | Static + realtime ComfyUI workflows + inpainting backend |

## VRAM rule of thumb

- 6 GB: PNGTuber + background removal only.
- 8 GB: + one of {LivePortrait, Deep-Live-Cam (low-res), background removal}.
- 12 GB: + ComfyUI SDXL on the side (not realtime).
- 16 GB+: realtime LCM stylization OR face swap, not both.

## Latency budget

Webcam → AI → OBS sink should stay **under 200 ms** total. Anything more breaks lip-sync for the
host — they cannot talk on camera without noticing.

| Stage | Target |
|---|---|
| Webcam capture | 5–15 ms |
| Frame transfer to ComfyUI | 5–10 ms |
| Workflow inference | 50–150 ms |
| Output encode + virtual cam | 5–20 ms |
| OBS render | 16 ms (one frame @ 60 fps) |

**Inference is the only stage with real headroom.** If you exceed the budget, a face effect and
ComfyUI cannot both be on at once — pick one, or upgrade hardware. Lower the inference resolution
before you lower stream bitrate.

## Explicitly out of scope

Roadmap items, deliberately not implemented here:

- Full SDXL realtime — waits on faster hardware or distilled models
- Multi-step temporal consistency (realtime AnimateDiff) — research grade
- Remote GPU burst rendering — see [`comfyui/bursts/`](comfyui/bursts/README.md)

## What lives where on disk

- Model weights: `models/` (under MinIO, never git).
- Workflows: `comfyui/workflows/*.json` (committed).
- Bridges (webcam ↔ ComfyUI ↔ OBS): `comfyui/bridges/`.
- Burst worker (cloud GPU): `comfyui/bursts/` (off by default).

## Two different things called "face filter"

Worth settling before you pick a tool — they have different pipelines and different ethics.

| | Face swap / portrait animation | AR lens overlays |
|---|---|---|
| Tools | DeepFaceLive, Deep-Live-Cam, LivePortrait | [`ar-filters/`](ar-filters/README.md) |
| What it does | **Replaces or reshapes the face itself** | Composites a graphic *on top of* your face via face-mesh tracking |
| Consent required | **Yes** — only faces you hold rights to | No — it never touches the face |
| Pipeline | Heavier; see below | Lower latency, no ComfyUI round-trip |

If what you want is glasses, ears, or a mask, use `ar-filters/` — it is a separate and much
cheaper pipeline, and none of the consent constraints below apply to it.

## Face-effect tool selection

Pick **one** as primary. Running two face effects at once is the fastest way to blow the latency
budget above.

| Tool | OS | Quality | Latency | Notes |
|---|---|---|---|---|
| DeepFaceLive | Windows | High | 60–120 ms | Mature; 8 GB VRAM minimum |
| Deep-Live-Cam | Cross-platform | Medium | 80–150 ms | More portable; quality below DFL |
| LivePortrait | Cross-platform | High (expressive) | 100–200 ms | Animates a still image from your face motion — a different use case, not a swap |

Record the choice in [`deepfacelive/README.md`](deepfacelive/README.md) or
[`comfyui/liveportrait.md`](comfyui/liveportrait.md).

## Pipeline

```
Webcam (raw)
   │
   ▼
[ Face effect: DeepFaceLive | Deep-Live-Cam | LivePortrait ]
   │
   ▼
Virtual Camera (OS-specific)
   │
   ▼
OBS (consumes the virtual camera as a video source)
   │
   ▼
[ OBS Background Removal plugin — segmentation ]
   │
   ▼
Composited scene out
```

The face effect runs **before** OBS, and segmentation runs **inside** OBS. That ordering matters:
segmenting a swapped face is cheap, swapping a segmented face is not.

### Virtual camera by OS

| OS | Path |
|---|---|
| **Windows** | OBS Virtual Camera is the default; DeepFaceLive targets it directly |
| **Linux** | `v4l2loopback` — see below |
| **macOS** | Apple's privacy model makes this painful; OBS Virtual Camera is the safest path |

```bash
# Linux
sudo apt install v4l2loopback-dkms
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="AI Camera"
# then point your tool at /dev/video10
```

## Realtime ComfyUI architecture

Distinct from the face-effect pipeline above — this is ComfyUI itself in the live path.

```
Webcam (raw, e.g. /dev/video0 or a capture card)
   │
   ▼
ComfyUI frame loader node
   │
   ▼
[ Lightweight workflow: stylization | segmentation | ControlNet pass ]
   │
   ▼
Virtual camera (pyvirtualcam) OR NDI output
   │
   ▼
OBS source
```

`comfyui/bridges/webcam_bridge.py` implements the loader and output ends. Achievable framerates
per model are tabulated in [`comfyui/workflows/README.md`](comfyui/workflows/README.md) — read
that before choosing a workflow for live use.

Burst rendering (offloading heavy jobs to a cloud GPU rather than the live path) is
[`comfyui/bursts/`](comfyui/bursts/README.md), off by default.
