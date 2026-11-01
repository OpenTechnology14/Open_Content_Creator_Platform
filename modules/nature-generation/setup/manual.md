# nature-generation — manual setup

**Labels:** `Content` · Automated path: [automated.md](automated.md)

> **Tier 0 is real code as of 2026-09-01 (`P-041`)** — `grading/tone.py`, `presets.py`, `cli.py`.
> Tiers 1–4 are still unwritten; `CLAUDE.md` §11 keeps this module at `scaffolded` until they exist
> too. The dependencies below are real and installable today.

## Prerequisites

| Need | Where | Required for |
|---|---|---|
| MinIO running | [storage-data](../../storage-data/setup/automated.md) — `make up` | Tiers 1–4 |
| ComfyUI installed | [realtime-ai](../../realtime-ai/setup/manual.md) | Tiers 1–3 |
| NVIDIA GPU 12 GB+ | — | Tier 4; 8 GB works for 1–3 at SDXL |
| Photographs you hold rights to | you | Tiers 1, 3, 4 |

**Tier 0 needs none of these** beyond a Python environment. If tone work is all you want, go
straight to step 4.

## 1. Read the intake guide

[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) — buckets, provenance record, the rights
matrix, the format matrix, and the rule for deciding whether a photo belongs here or in
[cityscape](../../cityscape-generation/setup/manual.md).

Do this before uploading anything. Retro-fitting provenance is the expensive path.

## 2. Ingest

```bash
mc mb local/nature-corpus
```

Upload to `nature-corpus/raw/`, append a provenance line per image to `manifest.jsonl`. `raw/` is
append-only.

## 3. Curate

Move reviewed images to `curated/`. Nature-specific criteria — blown skies, single-location
dominance, single-season sets, pre-applied dehaze — are in
[`../corpus/README.md`](../corpus/README.md). Floor is ~30 varied images.

## 4. Tier 0 — grading (no AI)

```bash
pip install numpy pyyaml Pillow
cd modules/nature-generation
python3 -m grading.cli --input photo.jpg --vibrance 0.25 --exposure 0.3 --output out.png
# or write a preset YAML (schema: ../grading/README.md) and:
python3 -m grading.cli --input photo.jpg --preset my-preset.yaml --output out.png
```

Work in LAB or linear light, never gamma-encoded sRGB, or saturation changes will shift hue —
`grading/tone.py` already does this correctly (see `tests/nature_generation/test_tone.py` for the
checks proving it). Reach for **vibrance** before saturation.

This is the whole path for tone work. Do not escalate.

## 5. Tiers 1–3 — ComfyUI

```bash
cd modules/realtime-ai/comfyui/app && python main.py
```

Install IP-Adapter SDXL, ControlNet Depth, and SAM — see
[`../workflows/README.md`](../workflows/README.md). Load the tier's workflow.

**Run `relight-v1` after `sky-replace-v1`.** A dramatic new sky over flatly-lit foreground reads
as fake immediately; matching ground light to the new sky is the part that sells it.

## 6. Tier 4 — train an adapter

Write the config ([`../adapters/README.md`](../adapters/README.md)) including `manifest_sha256`.
Expect 1–3 hours for a LoRA on a 12 GB card. Apply at 0.6–0.8.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] An adapter at 0.7 changes palette and light without inventing structure.
- [ ] Foliage at 100% zoom still looks organic, not CGI-smooth — this domain's failure mode.
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

- **Saturation change also shifted hue** — applied in gamma-encoded sRGB. Convert to LAB.
- **Output looks CGI / plasticky** — over-structuring. Lower adapter strength, and check whether
  the corpus was pre-dehazed.
- **Repeated foliage texture** — corpus too small or too uniform. More images, more locations.
- **Sky replacement looks pasted on** — ground light does not match. Run relight after.
- **Highlights will not recover** — 8-bit source, already clipped. See the format matrix.
- **CUDA OOM at Tier 4** — reduce resolution or rank before reducing the corpus.
