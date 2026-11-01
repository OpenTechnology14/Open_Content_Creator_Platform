# Background Removal Recipes

Step-by-step OBS setups for common background workflows. Each recipe assumes
the OBS Background Removal plugin is installed (see [`realtime-ai`](../../setup/manual.md)).

## Recipes

### 1. Static Image Background (`static-bg.md`)
Replace your real background with a single PNG image.
- Simplest setup, lowest GPU cost
- Works with any segmentation model
- Great for branded backgrounds

### 2. Blurred Room (`blurred-room.md`)
Keep your real room visible but blurred (like Zoom/Teams blur).
- Duplicate the webcam source, apply Gaussian blur filter, layer behind segmented source
- No need for a replacement image
- Professional look with minimal setup

### 3. Animated Loop (`animated-loop.md`)
Use a short MP4/WebM video as your background.
- Low GPU cost (video decode is cheap)
- Subtle motion adds life without distraction
- Loop a 10–30 second clip

### 4. AI-Generated Environment (`ai-environment.md`)
Use ComfyUI to generate a custom background image, then touch up regions
of it in place (via `../repaint_region.py`) without a full re-render.
- Requires [`realtime-ai`](../../setup/manual.md) (ComfyUI) complete
- Generate once, use as static background; repaint masked regions to iterate
- Prompt: "cozy streaming studio, warm lighting, bookshelves, 4k"

## Status

Recipe #4 (`ai-environment.md`) is written and runnable. Recipes #1–3
are still scaffolded — markdown files to be added as each is validated.
