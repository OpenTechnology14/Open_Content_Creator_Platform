# nature-generation — automated setup

**Labels:** `Content` · Manual path: [manual.md](manual.md)

**Tier 0 is real, tested code as of 2026-09-01 (`P-041`)** — see below. Tiers 1–4 have no code and
no automated setup; `CLAUDE.md` §11 keeps this module at `scaffolded` until they exist too.

## What its dependencies give you

Every dependency *is* automated, which is most of the setup:

```bash
make up      # postgres, redis, minio — the corpus and adapter store
```

`scripts/setup/minio_init.sh` already creates `nature-corpus` — this line previously said the
bucket would be added "when implemented", which was false; it's been in the script's `BUCKETS`
array since before this module had any code at all (found and corrected across several docs
during `P-017`; this was a copy not caught by that pass). ComfyUI is manual by nature (local GPU,
`CLAUDE.md` §2) — see [realtime-ai](../../realtime-ai/setup/automated.md).

## What automation looks like, by tier

| Tier | Automatable? | What it does |
|---|---|---|
| **0** grading | **Built** | `grading/cli.py` — read a preset or flags, apply the operation, write the file. No models, no GPU, no ComfyUI. `tests/nature_generation/` proves it's exactly reproducible (`test_tier0_operations_are_deterministic`), not just claims to be |
| **1–3** ComfyUI | Partly, unwritten | Queue a committed workflow over HTTP with substituted inputs, poll, push to MinIO. `realtime-ai/comfyui/scripts/output_to_minio.py` already does the last step |
| **4** training | No | An hours-long GPU job with a human deciding when the look is right. Scriptable to *launch*, not to *judge* |

**Tier 0 first, and now done.** The only tier needing nothing else installed, and the only one
whose correctness a test can assert — `tests/nature_generation/` does exactly that (25 cases).

## Intake is not automatable

Provenance is a human judgement — whether you hold rights to an image is not something a script
can determine, and [`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) makes an unmanifested
image ineligible. A script can compute `sha256` and stage files; it cannot fill in `rights`.
