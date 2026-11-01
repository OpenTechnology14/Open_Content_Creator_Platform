# asset-pipeline

**Labels:** `Content` `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (none — it's an importable library)

One storage contract for every script/service that reads or writes MinIO/S3 objects. Before this
module (2026-09-01, P-017), three places in the repo each hand-rolled their own client — two on
the `minio` SDK, one on `boto3` — with slightly different env var handling, and one of them
([`realtime-ai/comfyui/bursts/worker.py`](../realtime-ai/comfyui/bursts/worker.py)) never ensured
its bucket existed at all, a real bug that would hard-fail against a fresh MinIO instance.

## What it is

`asset_pipeline/` — a plain importable Python package, not a service, not something you `pip
install`. Consumers add its parent directory to `sys.path` and import it directly, the same way
[`tests/backend_api/test_routes.py`](../../tests/backend_api/test_routes.py) already imports the
FastAPI app by path. See any migrated consumer for the exact pattern.

Five functions: `get_client()`, `ensure_bucket()`, `upload_file()`, `upload_bytes()`,
`download_file()`, `list_objects()`. All wrap `S3Error` into one `AssetClientError` so callers
only need to catch one exception type.

## Consumers

| File | Was | Now |
|---|---|---|
| [`realtime-ai/comfyui/scripts/output_to_minio.py`](../realtime-ai/comfyui/scripts/output_to_minio.py) | `minio` SDK, hand-rolled | migrated |
| [`realtime-ai/comfyui/bursts/worker.py`](../realtime-ai/comfyui/bursts/worker.py) | `boto3`, no bucket-ensure (bug) | migrated, bug fixed |
| [`image-editing/krita/scripts/export_to_minio.py`](../image-editing/krita/scripts/export_to_minio.py) | `boto3`, hand-rolled | migrated |
| [`backend-api/fastapi/app/deps.py`](../backend-api/fastapi/app/deps.py) | `minio` SDK, hand-rolled | **not migrated** — see below |
| [`plugins/blender-addon/operators/__init__.py`](../../plugins/blender-addon/operators/__init__.py) | `boto3`, hand-rolled | **not migrated** — see below |

### Why two consumers are intentional exceptions, not oversights

- **`backend-api/fastapi/app/deps.py`** — `MinioDep`/`get_minio()` build a client for FastAPI's
  dependency injection, but as of 2026-09-01 no router actually calls it — there's no upload or
  download logic to consolidate yet, just unused wiring. It also runs in a Docker build whose
  context is `modules/backend-api/fastapi/` alone, so pulling in this module would need a build
  context change (`docker-compose.yml` + `Dockerfile`) that can't be verified without a Docker
  build, which this environment doesn't have. Migrate it when a router actually uses `MinioDep`
  for real upload/download work — that's the point at which duplication would actually start.
- **`plugins/blender-addon/operators/__init__.py`** — runs inside Blender's embedded Python
  interpreter, which can't import a sibling repo package without a build/vendoring step this repo
  has no infrastructure for. It keeps its own `boto3` client, config sourced from Blender add-on
  preferences (not env vars) rather than duplicating a contract nothing else in that process reads.

## Env vars

Every migrated consumer already agreed on these before this module existed — nothing here changes
a deployment's `.env`:

| Var | Default | Meaning |
|---|---|---|
| `MINIO_ENDPOINT` | `localhost:9000` | host:port — a `http://`/`https://` prefix is stripped automatically |
| `MINIO_ACCESS_KEY` | `minioadmin` | |
| `MINIO_SECRET_KEY` | `minioadmin` | |
| `MINIO_SECURE` | `false` | `"true"` for TLS |

Bucket names stay per-consumer (`comfyui-outputs`, `artwork`, etc.) — `get_client()` doesn't pick
one, callers do.
