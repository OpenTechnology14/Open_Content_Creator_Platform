"""Every top-level document under docs/ says what it is and when it was last reviewed, or is exempt on the record.

A reader opening a ledger or a guide cannot tell from the text whether it is current. The header answers that in its first
lines: ``> **Status:** Living · **Last reviewed:** 2026-10-19 · **Owner:** OpenTechnology14``. The guard checks presence and a
plausible date, not freshness: a date is only worth what the review behind it was, and nothing here proves a review happened.

A date is written only where ``git log`` supports it: the last commit that changed the document's own claims, not the initial
import, the intake-banner insertion or a one-line hygiene edit. A document with no such commit is listed in ``EXEMPT`` with the
reason, and stays there until someone reviews it; an exemption that has become stale fails, so the list cannot outlive the gap.

Offline and read-only (P-074, R5).
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOCS = sorted((REPO / "docs").glob("*.md"))
HEAD_LINES = 15
# `**Reviewed:**` is accepted because two existing documents already use it; new headers say `**Last reviewed:**`.
REVIEWED = re.compile(r"\*\*(?:Last reviewed|Reviewed):\*\*\s*(\d{4}-\d{2}-\d{2})")

NO_REVIEW = (
    "no commit since the initial import changes its claims (an intake banner is not a claim), so no review is recorded; "
    "the owner decides whether it gets one (HYB-REDESIGN-D08)"
)
EXEMPT = {
    "CONTINUOUS_IMPROVEMENT.md": NO_REVIEW,
    "IMPLEMENTATION_NOTES.md": NO_REVIEW,
    "PRESSURE_TEST_LOAD.md": NO_REVIEW,
    # It has a status and the date it was written, 2026-07-13, which is the initial import and not a review.
    "REPOSITORY_ALIGNMENT.md": NO_REVIEW,
}


def _head(path: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[:HEAD_LINES])


def _ids(paths):
    return [p.name for p in paths]


def test_there_are_documents_to_check():
    assert len(DOCS) >= 20, "docs/*.md moved or the glob stopped matching"


@pytest.mark.parametrize("doc", [d for d in DOCS if d.name not in EXEMPT], ids=_ids([d for d in DOCS if d.name not in EXEMPT]))
def test_a_document_declares_its_status_and_review_date(doc):
    head = _head(doc)
    assert "**Status:**" in head, (
        f"docs/{doc.name} has no '> **Status:** … · **Last reviewed:** YYYY-MM-DD' header in its first {HEAD_LINES} lines. "
        "Add one dated by the last commit that changed its content (git log), or list it in EXEMPT with the reason."
    )
    match = REVIEWED.search(head)
    assert match, f"docs/{doc.name}: the status header has no '**Last reviewed:** YYYY-MM-DD'"
    reviewed = datetime.date.fromisoformat(match.group(1))
    assert reviewed <= datetime.date.today() + datetime.timedelta(days=1), f"docs/{doc.name}: reviewed {reviewed} is in the future"


@pytest.mark.parametrize("name", sorted(EXEMPT))
def test_an_exemption_is_still_needed_and_still_explained(name):
    path = REPO / "docs" / name
    assert path.exists(), f"docs/{name} is exempt but no longer exists: delete it from EXEMPT"
    assert EXEMPT[name].strip(), f"docs/{name}: an exemption needs its reason"
    assert not REVIEWED.search(_head(path)), (
        f"docs/{name} now carries a review date: delete it from EXEMPT so the guard covers it"
    )
