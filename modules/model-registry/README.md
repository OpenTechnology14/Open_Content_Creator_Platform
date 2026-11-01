# model-registry

**Labels:** `Content` `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (CLI only)

One schema, one checksum tool, and one computed "is this actually distributable" answer for every
model weight and adapter in the repo. Before this module (2026-09-01, P-018), three places
hand-maintained their own model table — [`realtime-ai/comfyui/models.md`](../realtime-ai/comfyui/models.md),
[`sports-analytics/models/README.md`](../sports-analytics/models/README.md), and the generation
modules' adapter training configs — and none of them had a real checksum or license field. The
generation modules' adapter configs *required* a pinned `manifest_sha256`, but nothing checked it
was ever filled in with a real value rather than the documented placeholder ellipsis.

## What it owns

Per [`docs/architecture/future-state.md`](../../docs/architecture/future-state.md)'s original
boundary: an entry per model or adapter with checksum, size, source, license, the corpus manifest
hash that produced an adapter, and the conditioning it requires at inference
(`requires_controlnet`). It computes "is this distributable" from those fields instead of leaving
it as prose. **It does not own inference, does not own the corpus itself, and does not duplicate
[`asset-pipeline`](../asset-pipeline/README.md)** — it stores the registry file through that
module's shared MinIO client, not a second one.

## The schema

One `ModelEntry` per weight, defined in [`model_registry/schema.py`](model_registry/schema.py):

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | Unique key |
| `kind` | yes | `checkpoint` \| `adapter` \| `controlnet` \| `vae` \| `embedding` |
| `version` | yes | |
| `sha256` | yes | 64 hex chars — validated, not just present |
| `size_bytes` | yes | |
| `source_url` | yes | |
| `license` | yes | Free text; a handful of substrings (`proprietary`, `non-commercial`, …) mark an entry non-distributable |
| `license_url` | no | |
| `corpus_manifest_sha256` | **required if `kind == "adapter"`** | The exact field the generation modules already document and nothing enforced |
| `requires_controlnet` | no | List — cityscape-style adapters need this |
| `notes` | no | |

`model_registry.validate_entry()` checks shape (required fields present, `sha256` and
`corpus_manifest_sha256` are well-formed hex). `model_registry.is_distributable()` computes the
distributability answer — it does **not** verify a corpus is actually rights-clear or that a
license string is accurate; those stay human judgement calls
([`docs/agent/MODULE-MATRIX.md`](../../docs/agent/MODULE-MATRIX.md)'s "Human judgement" row). What
was missing before this module wasn't *judgement* — it was *anywhere to record the judgement's
inputs at all*.

## `registry.yml`

Committed, small (metadata only — **never weights**, per `CLAUDE.md` §10's 5 MB binary limit), and
**deliberately empty today**. No entry in it has a fabricated checksum: every weight the three old
tables reference needs a real `model_registry.cli checksum` run against the actual downloaded file
before it gets a real entry. See `setup/manual.md` for the add-an-entry workflow.

## What it is

`model_registry/` — a plain importable Python package plus a CLI, not a service. No `pip install`
step of its own; consumers add its parent directory to `sys.path`, the same pattern
[`asset-pipeline`](../asset-pipeline/README.md) established. Run the CLI from
`modules/model-registry/`:

```bash
python3 -m model_registry.cli validate
python3 -m model_registry.cli checksum /path/to/weight.safetensors
python3 -m model_registry.cli verify sdxl-base-1.0 /path/to/weight.safetensors
python3 -m model_registry.cli status
```

`sync_to_minio()`/`sync_from_minio()` push/pull the registry file through `asset_pipeline`'s
`upload_file`/`download_file`, so a droplet or a second workstation can read the same ledger
without a git checkout.
