# grading — Tier 0 (cityscape)

Deterministic tone, **geometry**, and colour. No AI, no GPU, no ComfyUI, no corpus.

This tier carries more weight in cityscape than in nature, because two of the most common urban
photo problems — converging verticals and mixed-temperature lighting — have **exact** solutions.
Sending them through diffusion invents new architecture to fix a lens.

## Operations

### Tone (shared with nature)

| Operation | Parameter | Colour space |
|---|---|---|
| Vibrance | scalar | LAB — usually what someone means by "more saturated" |
| Saturation | scalar, 0–2 | LAB or HSV, **never** gamma-encoded sRGB |
| Exposure | stops | Linear light |
| Contrast | S-curve | Gamma-encoded fine |
| Per-channel curves | RGB | Where a look lives |

### Geometry — cityscape only

| Operation | Parameter | Note |
|---|---|---|
| **Perspective correction** | vertical / horizontal keystone | Straightens converging verticals. Exact, and the single highest-value Tier 0 op here |
| **Lens distortion** | barrel / pincushion coefficient | Correct before anything else; every later operation inherits it |
| Rotation | degrees | Horizon and vertical alignment |
| Crop | rect | Perspective correction loses edge pixels — crop after, not before |

Order matters: **distortion → perspective → rotation → crop → tone.** Doing tone first means
regrading pixels you then throw away; doing perspective after crop means you run out of frame.

### Colour — cityscape only

| Operation | Note |
|---|---|
| **Mixed-source white balance** | Sodium, mercury, LED, and neon in one frame. A single global temperature cannot fix it |
| Per-range colour correction | Correct shadows and highlights to different temperatures — the practical answer to mixed sources |

## Why this is not a diffusion job

Beyond the general argument (slower, non-reproducible, lossy, unbounded), cityscape has a specific
one: **perspective correction is a known transform.** A homography has an exact answer. Asking a
generative model to straighten a building means asking it to redraw the building, and it will
redraw the windows differently.

## Presets

```yaml
preset: night-neon-cool
pairs_with: cityscape-neon-night-v1     # adapter in ../adapters/
lens_distortion: {barrel: -0.02}
perspective: {vertical: auto}
white_balance:
  shadows: {temp: -400}
  highlights: {temp: +150}
vibrance: 0.2
curves:
  rgb: [[0, 4], [48, 40], [200, 210], [255, 252]]
```

## Cityscape-specific cautions

- **Correct distortion before curation, not after.** An uncorrected corpus teaches the adapter
  your lens.
- **Do not push clarity on facades.** It haloes every window edge, and edges are what this domain
  is judged on.
- **Night: protect the black point.** Lifting shadows on a high-ISO night frame surfaces chroma
  noise in exactly the flat areas a viewer scans.
- **Neon clips one channel first.** Check the individual channel histograms, not luminance.

## Status

**Built** (2026-09-01, `P-041`) — `tone.py`, `geometry.py`, `presets.py`, `cli.py`,
`tests/cityscape_generation/` (44 cases). Automatic keystone detection
(`perspective: {vertical: auto}`) and the shadows/highlights mixed-source white balance split are
explicit exceptions — both raise `NotImplementedError` rather than being silently unimplemented;
see each function's own docstring. Was the cheapest tier to implement first, and the one this
domain benefits from most — and now is.
