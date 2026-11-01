# model-registry — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

**No service to stand up.** `pip install -r requirements.txt` is the entire install step. The CLI
(`python3 -m model_registry.cli ...`) is the automated path for everything that doesn't require a
human to actually download a weight, read its license, or decide it's rights-clear.

## What "automated" covers here

- `validate` — checks every entry in `registry.yml` is well-formed. Run in CI-equivalent form via
  `make test` (`tests/model_registry/test_schema.py`).
- `checksum` — computes a real SHA-256 from a local file. Deterministic, scriptable, exactly what
  replaces "trust the number someone typed into a table."
- `verify` — checks a downloaded file matches its registry entry before you trust it.
- `status` — the computed distributability answer, so a human doesn't have to re-derive it from
  the license string and the corpus-manifest field by hand every time.
- `sync_to_minio`/`sync_from_minio` — push/pull the registry file through `asset_pipeline`, once
  MinIO is up.

## What automation cannot cover

- **Downloading a weight.** License-gated, multi-GB, and the exact class of action `CLAUDE.md`
  §10 keeps out of git — same reason `realtime-ai`'s ComfyUI checkpoints are manual.
- **Deciding a license permits redistribution.** `is_distributable()` computes an answer from the
  `license` field's text, but reading a model card and writing that field correctly the first time
  is a human judgement call, not something this module verifies against the actual upstream terms.
- **Confirming a corpus is rights-clear.** The registry enforces that `corpus_manifest_sha256` is
  *present* for an adapter — it cannot enforce that the pinned corpus manifest is actually made of
  images the owner has rights to, which is the same "Human judgement: Image rights and provenance"
  line `docs/agent/MODULE-MATRIX.md` already names for the generation modules.

Populating `registry.yml` with real entries for the weights the three old tables reference
(`realtime-ai/comfyui/models.md`, `sports-analytics/models/README.md`) is owner work — this module
built the tool, not the ledger.
