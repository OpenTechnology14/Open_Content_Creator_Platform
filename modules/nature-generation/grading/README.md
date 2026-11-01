# grading — Tier 0 (nature)

Deterministic tone and colour. **No AI, no GPU, no ComfyUI**, and no corpus — this tier needs
nothing from [`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md).

It is separate from the rest of the module because it is the only tier that is exact, reversible,
and instant. A tone curve is a function; keep it one.

## Operations

| Operation | Parameter | Colour space |
|---|---|---|
| Vibrance | scalar | LAB — saturation weighted away from already-saturated pixels |
| Saturation | scalar, 0–2 | LAB or HSV, **never** gamma-encoded sRGB |
| Exposure | stops, −3…+3 | Linear light |
| White balance | temp / tint | Linear light |
| Contrast | S-curve | Gamma-encoded is fine here |
| Per-channel curves | RGB | Where a "look" actually lives |
| Highlight / shadow recovery | scalar | Needs headroom — see the format matrix in the intake guide |

**Vibrance, not saturation, is usually what someone means.** Global saturation pushes an already-
saturated sky to neon while barely touching muted foliage; vibrance lifts the muted parts and
leaves the sky alone. Reach for it first.

## Why this is not a diffusion job

Running a saturation change through Tiers 1–3 is slower (seconds vs milliseconds),
non-reproducible (a sample, not a function), lossy (the model re-renders the whole frame), and
unbounded (nothing guarantees it changes only saturation).

## Presets

Committed here as YAML. A preset is the deterministic half of a look; the adapter is the
generative half. Pair them by name.

```yaml
preset: overcast-lift
pairs_with: nature-overcast-v1     # adapter in ../adapters/
vibrance: 0.25
exposure: +0.3
white_balance: {temp: -200, tint: +4}
curves:
  rgb: [[0, 8], [64, 72], [192, 200], [255, 250]]
```

## Nature-specific cautions

- **Do not lift shadows hard on foliage.** It exposes sensor noise in exactly the high-frequency
  detail this domain is judged on.
- **Watch the sky when raising vibrance.** Blue channel clips before the others, and a clipped
  sky cannot be recovered later.
- **Dehaze and clarity are structural, not tonal.** They over-structure foliage — this domain's
  characteristic failure. If you want them, apply lightly and check at 100%.

## Bit depth

Grade from the highest depth available. Clipped highlights in an 8-bit JPEG are gone — see the
format matrix in [`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) §3.

## Status

**Built** (2026-09-01, `P-041`) — `tone.py`, `presets.py`, `cli.py`, `tests/nature_generation/`
(25 cases, including a determinism check proving the "exact function" claim above rather than
just asserting it). Was the cheapest tier to implement first — pure CPU, and the only one whose
correctness a test can assert rather than an eye — and now is.
