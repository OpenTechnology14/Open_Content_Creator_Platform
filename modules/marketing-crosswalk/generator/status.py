"""Subject status, verified against evidence in the target repository.

An earlier version of this module read implementation status from this repo's
CLAUDE.md §11 guide table. That was the wrong source: the subjects are the target
app's project templates, and their status is established by lines in the target
repo — a template README that says "Target architecture", or the engineering
crosswalk's verdict on an upstream.

So each subject declares both a status and the evidence for it, and the evidence is
re-read on every run. A template whose README stops saying "Target architecture" is a
status change the generator must surface, not paper over.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Ordered least-to-most trustworthy for making a public claim.
STATUS_ORDER = ["scaffolded", "unverified", "target-architecture", "shipped"]

STATUS_MEANING = {
    "scaffolded": "directory, README, and config exist, but it is not working, tested, or documented",
    "unverified": "upstream's own docs say not to believe capability claims without checking",
    "target-architecture": "the template's README describes the target, not what runs today",
    "shipped": "works as described",
}


class StatusError(RuntimeError):
    """Raised when a subject's declared status cannot be verified."""


@dataclass(frozen=True)
class EvidenceResult:
    subject: str
    status: str
    file: str
    contains: str
    verified: bool
    detail: Optional[str] = None


def verify_evidence(subject: dict, target_root: Path) -> EvidenceResult:
    """Re-read the line that establishes a subject's status."""
    status = subject.get("status")
    if status not in STATUS_ORDER:
        raise StatusError(
            f"subject {subject.get('id')!r} declares status {status!r}; "
            f"expected one of {STATUS_ORDER}"
        )

    evidence = subject.get("status_evidence") or {}
    rel, needle = evidence.get("file"), evidence.get("contains")
    if not rel or not needle:
        raise StatusError(
            f"subject {subject['id']!r} declares status {status!r} with no "
            "status_evidence.file / .contains — an unevidenced status cannot gate a claim"
        )

    path = target_root / rel
    if not path.is_file():
        return EvidenceResult(subject["id"], status, rel, needle, False,
                              "evidence file does not exist in the target repo")

    if needle not in path.read_text(encoding="utf-8"):
        return EvidenceResult(subject["id"], status, rel, needle, False,
                              "evidence text is no longer present — the status may have changed")

    return EvidenceResult(subject["id"], status, rel, needle, True)


def satisfies(status: str, claim_level: str) -> bool:
    """Whether `status` is high enough to publish a `claim_level` asset."""
    if claim_level == "roadmap":
        return True
    if claim_level == "shipped":
        return status == "shipped"
    raise StatusError(f"unknown claim_level {claim_level!r}")


def coverage_gaps(subject: dict) -> List[str]:
    """Which BLOG_MARKETING_CONNECTION.md §2 cells are empty for this subject."""
    return [key for key, value in (subject.get("coverage") or {}).items() if value is False]
