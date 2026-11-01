"""The one schema every model/adapter entry must satisfy.

Before this module, three places hand-maintained model tables with no
checksum and no license field at all (`realtime-ai/comfyui/models.md`,
`sports-analytics/models/README.md`), and two more (`nature-generation`/
`cityscape-generation`'s adapter training configs) *required* a
`manifest_sha256` field that nothing ever validated — it was a documented
placeholder ellipsis, never a real value. This is the schema that closes
that gap: one dataclass, one validator, one "is this actually
distributable" answer computed from real fields instead of prose.

What this module does NOT do: verify that a corpus is actually rights-
clear, or that a license string is accurate. Those are human judgement
calls (see `docs/agent/MODULE-MATRIX.md`'s "Human judgement" row) — this
module enforces that the *fields exist and are well-formed*, which is the
part that was previously not enforced at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Substrings that mark a license as non-distributable, checked
# case-insensitively. Anything not matching one of these is treated as
# open — deliberately permissive, because the fallback for an unrecognized
# license string should be "flag it for a human to check", which
# `is_distributable()` handles by returning False when `license` is empty,
# not by trying to enumerate every open license that exists.
_NON_DISTRIBUTABLE_MARKERS = ("proprietary", "non-commercial", "noncommercial", "research-only", "internal-only")

REQUIRED_FIELDS = ("name", "kind", "version", "sha256", "size_bytes", "source_url", "license")

VALID_KINDS = ("checkpoint", "adapter", "controlnet", "vae", "embedding")


@dataclass
class ModelEntry:
    """One row in the registry. Mirrors the required fields future-state.md
    specified for this module: checksum, size, source, license, the corpus
    manifest hash for adapters, and required conditioning."""

    name: str
    kind: str
    version: str
    sha256: str
    size_bytes: int
    source_url: str
    license: str
    license_url: str | None = None
    corpus_manifest_sha256: str | None = None
    requires_controlnet: list[str] = field(default_factory=list)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ModelEntry:
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "source_url": self.source_url,
            "license": self.license,
            "license_url": self.license_url,
            "corpus_manifest_sha256": self.corpus_manifest_sha256,
            "requires_controlnet": self.requires_controlnet,
            "notes": self.notes,
        }


def validate_entry(entry: ModelEntry) -> list[str]:
    """Return a list of problems. Empty list means the entry is well-formed
    — not that the weight is safe to use, only that every required field is
    present and shaped correctly."""
    problems: list[str] = []

    for f in REQUIRED_FIELDS:
        value = getattr(entry, f, None)
        if value in (None, ""):
            problems.append(f"{entry.name or '<unnamed>'}: missing required field {f!r}")

    if entry.kind and entry.kind not in VALID_KINDS:
        problems.append(f"{entry.name}: kind {entry.kind!r} not in {VALID_KINDS}")

    if entry.sha256 and (len(entry.sha256) != 64 or not _is_hex(entry.sha256)):
        problems.append(f"{entry.name}: sha256 must be 64 hex characters, got {entry.sha256!r}")

    if entry.size_bytes is not None and entry.size_bytes <= 0:
        problems.append(f"{entry.name}: size_bytes must be positive, got {entry.size_bytes!r}")

    if entry.corpus_manifest_sha256 and (
        len(entry.corpus_manifest_sha256) != 64 or not _is_hex(entry.corpus_manifest_sha256)
    ):
        problems.append(
            f"{entry.name}: corpus_manifest_sha256 must be 64 hex characters, "
            f"got {entry.corpus_manifest_sha256!r}"
        )

    return problems


def is_distributable(entry: ModelEntry) -> bool:
    """Computed, not asserted. An adapter (has a corpus_manifest_sha256
    requirement by convention of `kind == "adapter"`) additionally needs
    that hash actually pinned — a blank field was the exact gap this module
    exists to close, per `nature-generation`/`cityscape-generation`'s
    adapter READMEs."""
    if not entry.license:
        return False
    if any(marker in entry.license.lower() for marker in _NON_DISTRIBUTABLE_MARKERS):
        return False
    if entry.kind == "adapter" and not entry.corpus_manifest_sha256:
        return False
    return True


def _is_hex(s: str) -> bool:
    try:
        int(s, 16)
        return True
    except ValueError:
        return False
