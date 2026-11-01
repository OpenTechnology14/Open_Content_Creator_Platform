# Recipe 4 — AI-Generated Environment

Use ComfyUI to generate a custom background image, then use it as a
static background via the OBS Background Removal plugin — with a
touch-up path so you don't have to fully re-render the image every time
you want to change one small thing about it.

## Prerequisites

- [`realtime-ai`](../../setup/manual.md) (ComfyUI) complete and reachable at `http://127.0.0.1:8188`
- OBS Background Removal plugin installed (see this module's parent README)
- Recipe #1 (Static Image Background) set up — you have an Image source
  in OBS pointed at a background file

## Step 1 — Generate the base background

The workflows README documents `background-replace-v1.json` (auto-mask
subject, replace bg via RMBG-1.4 + SDXL) for this step — **but that file
doesn't exist yet**, only `inpaint-fill-v1.json` and
`video-frame-edit-v1.json` are actually built (see that README's index).
Until it's built, generate the base background manually in ComfyUI: load
a plain text-to-image SDXL workflow, no subject/mask involved since
you're generating an empty environment, not editing a photo of yourself.
Prompt example:

```
cozy streaming studio, warm lighting, bookshelves, 4k
```

Save the output as your OBS background file, e.g. `studio_bg.png`, and
point your Recipe #1 Image source at it. Step 2 below (masked-region
repaint) does not depend on `background-replace-v1.json` — it only needs
an existing background image, generated however you like.

## Step 2 — Touch up a region without a full re-render

Regenerating the whole background on every small change gives you a
different composition, different lighting, and misaligned framing each
time — not what you want for a one-off fix like "swap the plant for a
lamp." Instead, mask just that region and repaint it in place:

```bash
python3 modules/realtime-ai/background-removal/repaint_region.py \
    --background studio_bg.png \
    --mask plant_corner_mask.png \
    --prompt "a warm reading lamp on a side table"
```

- The mask is a PNG the same size as the background: **white = repaint
  this area, black = keep unchanged.** Paint it in any image editor, or
  use ComfyUI's own MaskEditor (right-click a LoadImage node → Open in
  MaskEditor) and export the mask.
- By default this **overwrites `studio_bg.png` in place** — the same
  file your OBS source already points at. Pass `--output` instead if you
  want to preview the result in a separate file first.
- OBS does not watch the file for changes. After a repaint, right-click
  the Image source → Properties → reselect the file path (or toggle it
  off/on) to force a refresh.

## Step 3 — Iterate

Repeat Step 2 for each region you want to change. Each run only touches
the masked pixels, so unrelated parts of the background (and anything
you've already fine-tuned) stay untouched.

## Status

Working, pending validation on a real stream setup — the underlying
`inpaint-fill-v1.json` workflow and `repaint_region.py` script exist and
are runnable; this recipe hasn't yet been confirmed end-to-end with a
live OBS source refresh cycle on hardware.
