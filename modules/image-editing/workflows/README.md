# Image Editing Workflows

ComfyUI workflow JSON files for inpainting, outpainting, object removal,
upscaling, and video frame editing. These are consumed by both the desktop
Krita integration and the mobile Creator Extend app.

## Index

| File                          | Purpose                              | Required models                    | Custom nodes           |
| ----------------------------- | ------------------------------------ | ---------------------------------- | ---------------------- |
| `inpaint-fill-v1.json`        | Generative fill (replace region)    | SDXL Inpainting or Flux Fill       | —                      |
| `inpaint-remove-v1.json`      | Remove object, reconstruct bg      | SDXL Inpainting                    | —                      |
| `outpaint-expand-v1.json`     | Extend canvas with AI content      | SDXL Inpainting                    | —                      |
| `upscale-4x-v1.json`          | Detail-preserving 4x upscale       | 4x-UltraSharp + SDXL              | UltimateSDUpscale      |
| `auto-select-sam-v1.json`     | Point → segment mask (SAM)         | SAM ViT-H or SAM-HQ               | ComfyUI-SAM            |
| `background-replace-v1.json`  | Auto-mask subject, replace bg      | RMBG-2.0 + SDXL                   | RMBG node              |
| `video-frame-edit-v1.json`    | Edit single video frame            | SDXL Inpainting                    | VideoHelperSuite       |
| `video-range-edit-v1.json`    | Edit frame range with propagation  | SDXL Inpainting + RAFT            | VideoHelperSuite, RAFT |

## Status

All eight rows in the index above are on disk. **Five GPU-run verified 2026-09-02 (`P-043`,
Apple M1 Pro / Metal):** `inpaint-fill-v1.json`, `inpaint-remove-v1.json`,
`outpaint-expand-v1.json`, `upscale-4x-v1.json`, `background-replace-v1.json` — each actually
loaded into a real ComfyUI and run to a saved image. Real bugs found and fixed in the process,
not just confirmed working as originally written:

- All four SDXL-Inpainting-checkpoint workflows referenced a single-file checkpoint
  (`sd_xl_base_1.0_inpainting_0.1.safetensors`) that does not exist at the documented source —
  see "SDXL Inpainting" below for what it actually is and the real fix (three loader nodes, not
  one).
- `upscale-4x-v1.json`'s `UltimateSDUpscale` node was missing two inputs
  (`tiled_decode`, `batch_size`) the currently-installed node pack requires — fixed.
- `background-replace-v1.json` named `RMBG-1.4`, a model this node pack's currently-installed
  version doesn't offer at all (superseded by `RMBG-2.0`) — fixed. It also omitted the optional
  `invert_output` input, which this node pack's `process_image()` reads via a raw dict lookup
  instead of `.get()` — crashes if absent rather than using its own documented default. Fixed by
  setting it (and `refine_foreground`) explicitly rather than relying on an implicit default that,
  in this pack, doesn't actually apply when called via the raw API.

**One confirmed blocked, for a real reason, not a naming fix:** `auto-select-sam-v1.json`'s node
names and model names are all correct — the actual blocker is that `storyicon/comfyui_segment_anything`'s
vendored GroundingDINO/BERT code is broken against current `transformers` releases in two separate
places (`BertModel.get_head_mask` removed; a `get_extended_attention_mask` argument-type
mismatch). Confirmed via real execution, not by reading the changelog — the first error matches
[an open upstream issue](https://github.com/storyicon/comfyui_segment_anything/issues/111); the
second reproduced even after pinning `transformers==4.57.6`, the version that issue's own thread
names as a fix (for a different pack). This needs an actively-maintained fork or a compatibility
patch upstream — not something to chase further here.

**One still a template, and now more specifically diagnosed than "placeholder":**
`video-range-edit-v1.json`. `VideoHelperSuite`'s two nodes (`VHS_LoadVideo`, `VHS_VideoCombine`)
are confirmed real and correctly named. The flow-warp step is not fixable by renaming the
placeholder class — `ComfyUI-Buff-Nodes`' `RaftOpticalFlowNode` (correctly identified) returns
`RETURN_TYPES = ("IMAGE",)`, a rendered flow **visualization**, not a usable flow field; there is
no mask-warp node anywhere in that pack. A different pack
([`seanlynch/comfyui-optical-flow`](https://github.com/seanlynch/comfyui-optical-flow)) does
expose a real `ApplyOpticalFlow` node, but its flow type isn't interchangeable with Buff-Nodes'
output — building this workflow for real means either replacing the flow-computation step too
(not just the warp step), or writing a small bridging node. That's design work, not a bug fix;
left for whoever picks this up next rather than half-built here.

`tests/realtime_ai/test_workflows.py` still confirms every node has a `class_type` and every
node reference resolves for all eight files — structural checks that hold regardless of GPU-run
status. `inpaint-fill-v1.json` is consumed by
`modules/realtime-ai/background-removal/repaint_region.py` for masked background touch-ups (see
that module's `recipes/ai-environment.md`) — its node "1" (the checkpoint loader) is never
referenced by that script, so the loader-node change above doesn't affect it.

## Workflow Design Conventions

1. **First node is always LoadImage** (or LoadVideo for video workflows)
   with a mask input. The API injects these at runtime.
2. **Prompt node uses positive + negative** — the API injects the user's
   text prompt into positive; negative has sensible defaults.
3. **Output is SaveImage** (or SaveVideo) — the API reads the output path.
4. **All model references use relative paths** so workflows load on any machine.

## Model Downloads

Inpainting models are separate from the base models in [`realtime-ai`](../../realtime-ai/setup/manual.md).

### SDXL Inpainting

**Not a single-file checkpoint.** `diffusers/stable-diffusion-xl-1.0-inpainting-0.1` on Hugging
Face ships in diffusers multi-folder format (`unet/`, `vae/`, `text_encoder/`, `text_encoder_2/`)
— there is no `sd_xl_base_1.0_inpainting_0.1.safetensors` at the repo root. A prior version of
this doc named that file; it 404s (confirmed 2026-09-02, GPU-run verification, `P-043`). Download
the four fp16 weight files it actually has, into ComfyUI's own per-type model folders (not
`models/checkpoints/`):

```
BASE=https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1/resolve/main
DEST=modules/realtime-ai/comfyui/app/models
wget -O "$DEST/unet/sdxl-inpainting-0.1-unet.fp16.safetensors" "$BASE/unet/diffusion_pytorch_model.fp16.safetensors"
wget -O "$DEST/vae/sdxl-inpainting-0.1-vae.fp16.safetensors" "$BASE/vae/diffusion_pytorch_model.fp16.safetensors"
wget -O "$DEST/text_encoders/sdxl-inpainting-0.1-clip_l.fp16.safetensors" "$BASE/text_encoder/model.fp16.safetensors"
wget -O "$DEST/text_encoders/sdxl-inpainting-0.1-clip_g.fp16.safetensors" "$BASE/text_encoder_2/model.fp16.safetensors"
```

Load with three separate nodes instead of `CheckpointLoaderSimple` — `UNETLoader` (`unet_name` =
the file above), `DualCLIPLoader` (`clip_name1`/`clip_name2` = the two text encoder files,
`type: sdxl`), `VAELoader` (`vae_name` = the vae file). All five workflows below that use this
checkpoint are wired this way — GPU-run verified 2026-09-02, `P-043`. (ComfyUI's `DiffusersLoader`
node can load the diffusers folder directly in one node and was also confirmed working, but is
marked deprecated in the installed ComfyUI version — the three-loader form is the one that won't
break on a future upgrade.)

### Flux Fill (for best quality generative fill)
```
# Requires Flux dev or schnell base
# See https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev
```

### SAM (Segment Anything Model)

No manual download needed — `storyicon/comfyui_segment_anything`'s `SAMModelLoader` and
`GroundingDinoModelLoader` fetch their own weights into `models/sams/` and
`models/grounding-dino/` on first use (confirmed by source inspection, `P-043`; a prior version of
this doc named a manual `wget` to `models/sam/`, which was never how this pack actually works).
Moot in practice today — see Status above for why this workflow doesn't run regardless.

### RMBG-2.0 (Background Removal)
```
# Auto-installed via ComfyUI Manager when first used, into models/RMBG/
```
`1038lab/ComfyUI-RMBG`'s currently-installed version doesn't offer `RMBG-1.4` as a model choice at
all (superseded by `RMBG-2.0`, `INSPYRENET`, `BEN`, `BEN2` — confirmed by source, `P-043`).

## Testing a Workflow

```bash
# Start ComfyUI
cd modules/realtime-ai/comfyui/app && python main.py

# Load workflow: top-right menu → Load → pick JSON
# Set input image via LoadImage node
# Draw mask via right-click → Open in MaskEditor
# Queue Prompt → verify output
```

---

## Inpainting + video workflow index

Verified against this directory and `modules/realtime-ai/comfyui/workflows/` on 2026-09-01.

| Workflow | Operation | Input | Output | On disk? |
|---|---|---|---|---|
| `inpaint-fill-v1.json` | Generative fill | Image + mask + prompt | Edited image | **yes** — GPU-run verified |
| `video-frame-edit-v1.json` | Single frame edit | Video + frame + mask | Edited video | **yes** |
| `inpaint-remove-v1.json` | Object removal | Image + mask | Clean image | **yes** — GPU-run verified |
| `outpaint-expand-v1.json` | Canvas expansion | Image + direction + prompt | Expanded image | **yes** — GPU-run verified |
| `upscale-4x-v1.json` | Super resolution | Image | 4× upscaled image | **yes** — GPU-run verified |
| `auto-select-sam-v1.json` | Auto segmentation | Image + region prompt* | Mask | **yes** — blocked on an upstream library bug, see Status |
| `background-replace-v1.json` | Background swap | Image + prompt | New background | **yes** — GPU-run verified |
| `video-range-edit-v1.json` | Frame range edit | Video + range + mask | Edited clip | **yes** — template, needs design work, see Status |

\* `auto-select-sam-v1.json` takes a text region description (e.g. "the mug"), not a literal click
coordinate — see its `_meta.status` for why.

All eight are on disk; five are GPU-run verified working, one is blocked on a real upstream bug,
one needs real design work (see Status above). The Krita AI Diffusion plugin performs the
equivalent operations through its own graphs regardless, so neither remaining gap blocks
**interactive** editing — only scripted/API use of these two specific files.

### Cross-module reuse

`inpaint-fill-v1.json` is not only used here — `realtime-ai/background-removal/repaint_region.py`
calls it to touch up a masked region of a live OBS background without a full regenerate. See
[`../../realtime-ai/background-removal/README.md`](../../realtime-ai/background-removal/README.md)
and its `recipes/ai-environment.md`.

Changing this workflow's inputs or outputs breaks that path. It has two consumers, not one.

**More are pending.** Both generation modules do Tier 2 inpaint work:
[`nature-generation`](../../nature-generation/workflows/README.md) (sky replace, relight) and
[`cityscape-generation`](../../cityscape-generation/workflows/README.md) (facade repair, sign
removal). When those tiers are built, decide deliberately whether each reuses this file — making
its signature a contract across more modules — or ships its own variant.

Cityscape probably needs its own: its structural workflows carry ControlNet lineart conditioning
that this file does not. Nature could plausibly reuse. Each decision is recorded in that module's
workflow index; do not let it happen by default.

## Video frame editing

ComfyUI handles video through the **VideoHelperSuite** custom node pack. The desktop flow:

1. Load the video with the `LoadVideo` node
2. Extract the frame to edit
3. Apply the mask + inpainting workflow
4. Re-insert the edited frame
5. Export

`video-frame-edit-v1.json` implements this for a single frame. `video-range-edit-v1.json`
implements the range variant — RAFT optical flow propagates the frame-1 mask across the batch —
but is an unverified template like the rest of P-028's additions; its flow-warp node names a
placeholder `class_type` pending confirmation of which RAFT pack ships the real one.

