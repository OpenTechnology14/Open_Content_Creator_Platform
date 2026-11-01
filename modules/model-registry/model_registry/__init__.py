"""One schema, one checksum tool, one distributability answer for every
model weight and adapter in the repo — closing the gap where three
independent hand-maintained tables (`realtime-ai/comfyui/models.md`,
`sports-analytics/models/README.md`, and the generation modules' adapter
training configs) each asked for provenance but nothing checked it.

Import via a `sys.path` insert pointing at this directory's parent, the
same pattern `modules/asset-pipeline` established (see any of that
module's migrated consumers for the exact snippet). No `pip install` step.
"""

from model_registry.checksum import compute_sha256, verify_local_file
from model_registry.registry import (
    RegistryError,
    load_registry,
    save_registry,
    sync_from_minio,
    sync_to_minio,
)
from model_registry.schema import ModelEntry, is_distributable, validate_entry

__all__ = [
    "ModelEntry",
    "RegistryError",
    "compute_sha256",
    "is_distributable",
    "load_registry",
    "save_registry",
    "sync_from_minio",
    "sync_to_minio",
    "validate_entry",
    "verify_local_file",
]
