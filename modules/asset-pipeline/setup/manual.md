# asset-pipeline — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

There is nothing to install. This is a plain Python package other modules import by path — no
service, no container, no `pip install` step of its own.

## Prerequisites

A running MinIO instance to actually upload/download against — see
[storage-data](../../storage-data/setup/manual.md). The package imports fine without one; only
network calls need it reachable.

## Using it from a new script

```python
import sys
from pathlib import Path

# Point at modules/, then into asset-pipeline/ — adjust the parents[N]
# index to however many directories separate your script from modules/.
sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "asset-pipeline"))
from asset_pipeline import ensure_bucket, get_client, upload_file

client = get_client()               # reads MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY/MINIO_SECURE
ensure_bucket(client, "my-bucket")  # idempotent — safe on every run
upload_file(client, "my-bucket", "key.png", "/local/path/key.png")
```

Install its two dependencies into whatever Python environment your script runs under:

```bash
pip install -r modules/asset-pipeline/requirements.txt
```

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that does
not need a MinIO instance at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite; `tests/asset_pipeline/` mocks the MinIO SDK, no live
  server needed

**Manual — nothing automates these:**

- [ ] `python3 modules/realtime-ai/comfyui/scripts/output_to_minio.py --watch <dir>` connects to a
      running MinIO and uploads a test file dropped into `<dir>`
- [ ] `python3 modules/image-editing/krita/scripts/export_to_minio.py --file <img> --bucket artwork`
      lands the file in MinIO's console
- [ ] The Krita-embedded `export_current_document()` path works from inside Krita itself (the
      standalone CLI path above doesn't exercise the `from krita import Krita` branch)

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

- **`ModuleNotFoundError: No module named 'asset_pipeline'`** — the `sys.path.insert` line's
  `parents[N]` index doesn't land on `modules/`. Count directories from your script up to
  `modules/` and use that number.
- **`AssetClientError` on every call** — MinIO isn't reachable at `MINIO_ENDPOINT`, or the
  credentials are wrong. `docker compose up minio` if it isn't running.
