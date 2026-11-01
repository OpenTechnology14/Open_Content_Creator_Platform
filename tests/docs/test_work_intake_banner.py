"""Audit ledgers, test plans and parking-lot documents say where a finding goes.

A document that records findings is not a queue. It carries the intake marker and a banner that points to the
three places work and decisions actually live: the proposal queue, the decision and run lanes, and the
future-documents registry. `REQUIRED` is the contract: a document that adopts the banner must be listed here, and
a listed document must keep it. The link tests in `test_docs_integrity.py` do not read root `TESTING.md` or
`tests/*.md`, so the banner's links are resolved here.

Offline and read-only (P-074, R3).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MARKER = "<!-- PROPOSAL_WORK_INTAKE -->"
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Every link the banner must carry, by the path it ends with.
TARGETS = ("PROPOSALS.md", "todo/README.md", "FUTURE_DOCS.md")

REQUIRED = [
    "docs/architecture/future.md",
    "docs/architecture/future-state.md",
    "docs/AUDIT.md",
    "docs/GAP_AUDIT.md",
    "docs/API_ROUTE_AUDIT_LEDGER.md",
    "docs/FULL_APPLICATION_AUDIT_MATRIX.md",
    "docs/CONTINUOUS_IMPROVEMENT.md",
    "docs/IMPLEMENTATION_NOTES.md",
    "docs/PRESSURE_TEST_LOAD.md",
    "TESTING.md",
    "tests/ACCEPTANCE-CHECKLIST.md",
    "tests/USE-CASES.md",
]


def _marker_index(lines: list[str]) -> int | None:
    """Index of the marker line outside a fenced code block, or None. A proposal may quote the banner in a fence."""
    in_fence = False
    for number, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line == MARKER:
            return number
    return None


def _banner(rel: str) -> list[str]:
    """The marker line and the blockquote that follows it, or an empty list."""
    lines = (REPO / rel).read_text(encoding="utf-8").splitlines()
    start = _marker_index(lines)
    if start is None:
        return []
    block = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith(">"):
            break
        block.append(line)
    return block


@pytest.mark.parametrize("rel", REQUIRED)
def test_required_document_carries_the_banner(rel):
    assert (REPO / rel).is_file(), f"{rel} is listed but does not exist"
    block = _banner(rel)
    assert block, f"{rel} has lost its {MARKER} banner"
    assert len(block) > 1 and block[1].startswith("> **Work intake:**"), \
        f"{rel}: the marker must be followed by a '> **Work intake:**' blockquote"


@pytest.mark.parametrize("rel", REQUIRED)
def test_banner_links_resolve_to_the_queue_the_lanes_and_the_registry(rel):
    hrefs = LINK.findall("\n".join(_banner(rel)))
    for target in TARGETS:
        assert any(href.split("#")[0].endswith(target) for href in hrefs), f"{rel}: banner does not link {target}"
    broken = [href for href in hrefs if not (REPO / rel).parent.joinpath(href.split("#")[0]).resolve().exists()]
    assert not broken, f"{rel}: banner links to missing {broken}"


def test_every_document_with_the_marker_is_listed():
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "*.md"], cwd=REPO, capture_output=True, check=True,
    ).stdout.decode("utf-8", "replace").split("\0")
    carrying = sorted(
        rel for rel in filter(None, tracked)
        if (REPO / rel).is_file()
        and _marker_index((REPO / rel).read_text(encoding="utf-8", errors="ignore").splitlines()) is not None
    )
    unlisted = sorted(set(carrying) - set(REQUIRED))
    assert not unlisted, f"carries the marker but is not in REQUIRED: {unlisted} (add it, so the banner stays guarded)"
