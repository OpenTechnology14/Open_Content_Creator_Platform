# model-registry — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

There is nothing to install beyond two pure-Python dependencies. This is a plain importable
package plus a CLI, no service, no container.

## Prerequisites

```bash
pip install -r modules/model-registry/requirements.txt
```

MinIO running (see [storage-data](../../storage-data/setup/manual.md)) only if you want
`sync_to_minio`/`sync_from_minio` — the CLI's `validate`/`checksum`/`verify`/`status` commands work
entirely offline against the local `registry.yml`.

## Adding a real entry

1. Download the weight (`modules/realtime-ai/comfyui/models.md`, `modules/sports-analytics/models/README.md`,
   or a generation module's adapter README point at where).
2. Compute its checksum:
   ```bash
   cd modules/model-registry
   python3 -m model_registry.cli checksum /path/to/weight.safetensors
   ```
3. Add an entry to `registry.yml` with that hash, the file's size in bytes, the source URL, and the
   license the source actually states — see `README.md`'s schema table for every field. If it's an
   adapter, `corpus_manifest_sha256` is **required**, not optional — that's the field the generation
   modules' training configs already document.
4. `python3 -m model_registry.cli validate` — confirms the new entry is well-formed.
5. `python3 -m model_registry.cli status` — confirms it reports the `is_distributable` answer you
   expect. If it says `NOT distributable` and you expected otherwise, the license string or the
   missing `corpus_manifest_sha256` is why — both print in `status`'s output.

## Using it from a new script

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "model-registry"))
from model_registry import load_registry, validate_entry

entries = load_registry()
for e in entries:
    problems = validate_entry(e)
    if problems:
        print(problems)
```

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that does
not need MinIO or a real weight file at all.

**Automated — run these:**

- `make test` — `tests/model_registry/` covers the schema, checksum computation (verified against
  `hashlib` and against `shasum -a 256` by hand during development), and MinIO sync wiring against
  a mocked `asset_pipeline` client. No live server needed.

**Manual — nothing automates these:**

- [ ] `python3 -m model_registry.cli checksum <a real downloaded weight>` matches `shasum -a 256`
      run independently on the same file
- [ ] `sync_to_minio()` against a running MinIO actually lands `registry.yml` in the `models` bucket
- [ ] A second machine's `sync_from_minio()` reads back an identical file

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

- **`ModuleNotFoundError: No module named 'model_registry'`** or **`'asset_pipeline'`** — the
  `sys.path.insert` `parents[N]` index doesn't land on `modules/`. Count directories from your
  script up to `modules/` and use that number.
- **`RegistryError` on load** — an entry in `registry.yml` is missing a required field entirely
  (not just blank) — `ModelEntry(**data)` raises `TypeError` for a truly missing key, which
  `load_registry` wraps into `RegistryError` rather than a bare traceback.
- **`status` says `NOT distributable` unexpectedly** — check `validate`'s output first; a
  malformed `corpus_manifest_sha256` or an empty `license` field is the usual cause.
