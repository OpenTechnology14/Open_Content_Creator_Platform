# asset-pipeline — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

**There is no automated setup, and there is nothing to automate.** This module is a plain
importable Python package (`asset_pipeline/`), not a service — nothing to build, start, or
containerize. `pip install -r requirements.txt` is the entire install step, and consumers do that
themselves as part of their own setup (see each migrated consumer's own `Requirements:` docstring
line).

## What "done" looks like here

Three of the five MinIO/S3 client implementations that existed in this repo before 2026-09-01
(P-017) now import this package instead of hand-rolling their own:
`realtime-ai/comfyui/scripts/output_to_minio.py`, `realtime-ai/comfyui/bursts/worker.py`,
`image-editing/krita/scripts/export_to_minio.py`. `tests/asset_pipeline/test_consumers_migrated.py`
enforces this — it fails if any of the three ever reintroduces a direct `boto3` import or drops
the `asset_pipeline` import.

## What's deliberately not consolidated

Two consumers keep their own client — see `README.md`'s "Why two consumers are intentional
exceptions" section for the full reasoning:

- `backend-api/fastapi/app/deps.py` — no router uses `MinioDep` for real upload/download work yet,
  so there's no duplication to remove; migrating it also needs a Docker build-context change this
  environment can't verify.
- `plugins/blender-addon/operators/__init__.py` — runs inside Blender's embedded interpreter,
  which can't import a sibling repo package without vendoring infrastructure this repo doesn't have.

Both are correctly-scoped exclusions, not gaps — re-scope only if a router starts doing real
uploads (first case) or the repo grows an addon-packaging/vendoring step (second case).
