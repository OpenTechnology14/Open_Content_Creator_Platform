# LivePortrait — Webcam-Driven Portrait Animation

LivePortrait animates a still portrait image using your webcam face motion.
Different from face-swap (DeepFaceLive/Deep-Live-Cam) — instead of replacing
your face, it transfers your expressions onto a drawn/painted character.

## Use cases

- Vtuber-style avatar driven by webcam (higher quality than PNGTuber)
- Animated character co-host without needing Live2D rigging
- AI-generated character with realtime facial tracking

## Install

```bash
git clone https://github.com/KwaiVGI/LivePortrait.git
cd LivePortrait
pip install -r requirements.txt
```

Or use the ComfyUI integration:
```bash
cd modules/realtime-ai/comfyui/app/custom_nodes
git clone https://github.com/kijai/ComfyUI-LivePortraitKJ.git
```

## Hardware requirements

- NVIDIA GPU with ≥ 8 GB VRAM
- 100–200 ms latency (usable but noticeable)
- Webcam (720p minimum; 1080p recommended)

## Pipeline

```
Webcam → LivePortrait (expression extraction) → Rendered portrait → Virtual Camera → OBS
```

## Notes

- The source portrait should be front-facing, well-lit, high-resolution
- Works with AI-generated portraits (Stable Diffusion, FLUX, etc.)
- Quality degrades with extreme head angles (> 30° from center)
- Can run alongside background removal but NOT alongside face-swap (VRAM conflict)

## Decision: LivePortrait vs DeepFaceLive vs PNGTuber

| Feature | LivePortrait | DeepFaceLive | PNGTuber |
|---------|-------------|--------------|----------|
| Identity | Character | Your face (or swap) | Character |
| Expression | Full facial tracking | Full facial tracking | Mouth open/close only |
| Setup effort | Medium | Medium-High | Low |
| VRAM | 8 GB | 8 GB | 0 (CPU) |
| Quality | High | High | Low |

Document your choice in the module README.
