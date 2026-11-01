# cityscape-generation — automated setup

**Labels:** `Content` · Manual path: [manual.md](manual.md)

**Tier 0 is real, tested code as of 2026-09-01 (`P-041`)** — see below. Tiers 1–4 have no code and
no automated setup; `CLAUDE.md` §11 keeps this module at `scaffolded` until they exist too.

## What its dependencies give you

```bash
make up      # postgres, redis, minio — the corpus and adapter store
```

`scripts/setup/minio_init.sh` already creates `cityscape-corpus` — this line previously said the
bucket would be added "when this module is implemented", which was false; it's been in the
script's `BUCKETS` array since before this module had any code at all (found and corrected across
several docs during `P-017`; this was a copy not caught by that pass). ComfyUI is manual by nature
— see [realtime-ai](../../realtime-ai/setup/automated.md).

## What automation looks like, by tier

| Tier | Automatable? | What it does |
|---|---|---|
| **0** tone | **Built** | `grading/cli.py` — read a preset or flags, apply the operation, write the file. `tests/cityscape_generation/` proves it's exactly reproducible |
| **0** geometry | **Built** | `grading/geometry.py` — lens distortion and perspective correction are known transforms solved exactly (a homography via DLT, not a guess). **Automatic** keystone detection (`perspective: {vertical: auto}` in the preset schema) is explicitly not built — that's real vanishing-point computer vision, not a Tier 0 "no AI" operation; it raises `NotImplementedError` rather than silently no-op-ing. Only manual numeric keystone values work today |
| **1–3** ComfyUI | Partly, unwritten | Queue a committed workflow over HTTP, poll, push to MinIO. `output_to_minio.py` covers the last step |
| **4** training | No | Hours-long GPU job with a human judging the look |

**Tier 0 geometry is the highest-value automation in either generation module, and it's built.**
Perspective correction has an exact answer, applies to nearly every urban frame, and is a
prerequisite for a clean corpus — an uncorrected corpus teaches the adapter your lens. What's
still manual is supplying the correction *parameters* (auto-detection from the image itself is
not built); applying them once known is automatic.

## Intake is not automatable

Provenance and **privacy screening** are human judgements. A script can compute `sha256` and stage
files; it cannot decide whether a face is recognisable or whether you hold rights. Cityscape
carries more privacy exposure than nature — see
[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) §5.
