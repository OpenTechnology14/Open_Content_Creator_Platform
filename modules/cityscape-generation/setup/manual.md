# cityscape-generation — manual setup

**Labels:** `Content` · Automated path: [automated.md](automated.md)

> **Tier 0 is real code as of 2026-09-01 (`P-041`)** — `grading/tone.py`, `geometry.py`,
> `presets.py`, `cli.py`. Tiers 1–4 are still unwritten; `CLAUDE.md` §11 keeps this module at
> `scaffolded` until they exist too. Dependencies below are real and installable today.

## Prerequisites

| Need | Where | Required for |
|---|---|---|
| MinIO running | [storage-data](../../storage-data/setup/automated.md) — `make up` | Tiers 1–4 |
| ComfyUI installed | [realtime-ai](../../realtime-ai/setup/manual.md) | Tiers 1–3 |
| **ControlNet Lineart SDXL** | model download | **Tiers 2–3 — not optional** |
| NVIDIA GPU 12 GB+ | — | Tier 4; 8 GB works for 1–3 |
| Photographs you hold rights to | you | Tiers 1, 3, 4 |

**Tier 0 needs none of these** beyond a Python environment.

## 1. Read the intake guide

[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) — buckets, provenance, rights matrix,
format matrix, and the mixed-scene rule for deciding between this module and
[nature](../../nature-generation/setup/manual.md). **Anything with a hard straight edge belongs
here**, even a mostly-landscape frame.

## 2. Ingest

```bash
mc mb local/cityscape-corpus
```

Upload to `cityscape-corpus/raw/`, one provenance line per image. `raw/` is append-only.

## 3. Correct geometry, then curate

**Do this before promoting to `curated/`.** Correct lens distortion and perspective at Tier 0
first — an uncorrected corpus teaches the adapter your lens rather than the architecture.

Then screen for privacy (faces, plates, interiors — [`../corpus/README.md`](../corpus/README.md))
and split into `curated/day/` and `curated/night/`. **Night is a separate adapter**, not a darker
version of day: different dynamic range, mixed-temperature sources, different noise, different
subject.

Floor is ~30 curated per sub-domain, so a day+night corpus wants ~60.

## 4. Tier 0 — grading and geometry (no AI)

```bash
pip install numpy pyyaml Pillow
cd modules/cityscape-generation
python3 -m grading.cli --input photo.jpg --barrel -0.02 --rotate 1.5 --vibrance 0.2 --output out.png
# or a preset YAML (schema: ../grading/README.md):
python3 -m grading.cli --input photo.jpg --preset my-preset.yaml --output out.png
```

Order matters: **lens distortion → perspective → rotation → crop → tone.** Tone first regrades
pixels you then discard; perspective after crop runs out of frame. `grading/geometry.py`'s
`apply_geometry()` already enforces this order — see `tests/cityscape_generation/test_geometry.py`
for the check proving it.

**Automatic keystone detection is not built.** The preset schema's `perspective: {vertical: auto}`
raises `NotImplementedError` rather than silently doing nothing — pass explicit numeric
`vertical`/`horizontal` values (a fraction of half the frame dimension) instead.

For mixed street lighting, correct shadows and highlights to *different* temperatures — a single
global white balance cannot fix sodium and LED in one frame. **Also not built yet:** `apply_preset()`
raises `NotImplementedError` on a `white_balance.shadows`/`.highlights` split; only a flat
`{temp, tint}` white balance works today. See [`../grading/README.md`](../grading/README.md).

## 5. Tiers 1–3 — ComfyUI

```bash
cd modules/realtime-ai/comfyui/app && python main.py
```

Install IP-Adapter SDXL, **ControlNet Lineart SDXL**, ControlNet Depth SDXL, and SAM.

**Weight lineart at 0.7–1.0.** Without it, straight edges bend and window grids melt — the output
is unusable, not merely worse. Reduce only if results look traced rather than generated.

**Generate above your target resolution and downscale.** Window grids and brickwork survive
downscaling; they do not survive upscaling.

**Do not try to generate legible signage.** Mask it out, compose around it, or accept illegible
text — see [`../workflows/README.md`](../workflows/README.md).

## 6. Tier 4 — train an adapter

Write the config ([`../adapters/README.md`](../adapters/README.md)) with `manifest_sha256` and
`requires_controlnet: [lineart]`. Expect 1–3 hours for a LoRA on a 12 GB card. Apply at 0.6–0.8 —
cityscape tolerates high strength worse than nature, because a viewer recognises a real building
rendered wrong.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] Corrected verticals are actually vertical — check against the frame edge, not by eye.
- [ ] A generated skyline holds straight building edges at 100% zoom.
- [ ] Window grids are regular, not melted.
- [ ] Night output keeps its black point without chroma noise in the flats.
- [ ] Outputs land in MinIO `project-assets`.

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

- **Buildings bend** — lineart ControlNet missing, or weighted too low. This is the first thing to check.
- **Window grids melted** — generated at target resolution. Generate higher and downscale.
- **Signage is text-shaped noise** — expected. Mask, compose around, or accept it.
- **Output resembles a specific real building** — adapter strength too high, or corpus too uniform.
- **Night frames washed out** — day and night in one adapter. Split the corpus.
- **Colour casts fought each other** — single global white balance on mixed sources. Correct shadows and highlights separately.
- **Saturation shifted hue** — applied in gamma-encoded sRGB. Convert to LAB.
