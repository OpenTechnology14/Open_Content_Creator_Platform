"""One storage contract for every script/service that talks to MinIO/S3.

Before this module, four places in the repo each hand-rolled their own
MinIO/S3 client: two used the `minio` SDK, two used `boto3`; env var
defaults, bucket-creation logic, and error handling all differed slightly.
`output_to_minio.py` had none of the differences that mattered (bucket
creation), but `worker.py` had actually skipped it — a real bug that only
showed up against a fresh MinIO instance. This package is the fix: one
client factory, one set of helpers, used the same way everywhere.

Import it via a `sys.path` insert pointing at this directory's parent —
see any migrated consumer (e.g. `modules/realtime-ai/comfyui/scripts/
output_to_minio.py`) for the exact pattern. There is no `pip install`
step; this is a plain importable package, not a published one, matching
how `tests/backend_api/test_routes.py` already imports `app.main` by
path rather than as an installed dependency.
"""

from asset_pipeline.client import (
    AssetClientError,
    download_file,
    ensure_bucket,
    get_client,
    list_objects,
    upload_bytes,
    upload_file,
)

__all__ = [
    "AssetClientError",
    "download_file",
    "ensure_bucket",
    "get_client",
    "list_objects",
    "upload_bytes",
    "upload_file",
]
