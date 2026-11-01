"""Keep proposal model assignments complete and consistent with their documents."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
ASSIGNMENT = re.compile(
    r"`(?P<model>[\w./-]+)` / `(?P<effort>low|medium|high|xhigh|max|ultra)` — .+"
)


def _proposal_rows() -> dict[str, list[str]]:
    rows = {}
    for line in (DOCS / "PROPOSALS.md").read_text().splitlines():
        if re.match(r"\| P-\d+ \|", line):
            cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            assert cells[0] not in rows, f"Duplicate proposal: {cells[0]}"
            rows[cells[0]] = cells
    assert rows, "No proposal rows found"
    return rows


def test_every_proposal_has_an_explicit_agent_model() -> None:
    """All states, including historical and deferred work, retain a work assignment."""
    queue = (DOCS / "PROPOSALS.md").read_text()
    assert "| Agent model / effort |" in queue
    declared = set(re.findall(r"^\| `(gpt-[\w.-]+)` \|", queue, re.MULTILINE))
    assert declared, "The selection policy declares no models"
    for proposal, cells in _proposal_rows().items():
        assert len(cells) == 6, f"{proposal}: expected a model column, got {len(cells)} cells"
        assignment = ASSIGNMENT.fullmatch(cells[4])
        assert assignment, f"{proposal}: missing model, effort or rationale"
        assert assignment["model"] in declared, f"{proposal}: model absent from selection policy"


def test_proposal_documents_match_the_queue_model() -> None:
    """Detailed proposals must expose the same assignment their queue row selects."""
    rows = _proposal_rows()
    for doc in sorted((DOCS / "proposals").glob("PROPOSAL_*.md")):
        body = doc.read_text()
        identity = re.search(r"\*\*Queue row:\*\*\s*`?(P-\d+)`?", body)
        assert identity, f"{doc.name}: missing queue ID"
        row = rows[identity[1]]
        assert len(row) == 6, f"{identity[1]}: missing model column"
        model = re.search(r"\*\*Agent model / effort:\*\*\s*(.+)", body)
        assert model, f"{doc.name}: missing agent model"
        assert model[1] == row[4], f"{doc.name}: model assignment differs from {identity[1]}"


def test_setup_subitems_have_model_assignments() -> None:
    """The existing P-063 work queue exposes a model for each numbered setup item."""
    proposal = (DOCS / "proposals" / "PROPOSAL_IN_APP_SETUP.md").read_text()
    section = proposal.split("### In-app automation work queue", 1)[1]
    section = section.split("### Acceptance and measurement", 1)[0]
    items = []
    for line in section.splitlines():
        if re.match(r"\| \d+ \|", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            assert len(cells) == 5, f"Setup item {cells[0]}: missing model column"
            assert ASSIGNMENT.fullmatch(cells[3]), f"Setup item {cells[0]}: invalid model"
            items.append(cells[0])
    assert items, "No setup subitems found"


def test_proposal_template_requires_model_selection() -> None:
    template = (DOCS / "proposals" / "TEMPLATE_PROPOSAL.md").read_text()
    assert "**Agent model / effort:**" in template
    assert "best available model" in template
    assert "PROPOSALS.md#agent-model-selection" in template


def test_proposal_template_and_sop_ask_for_verified_against_unchanged_files_and_first_slice() -> None:
    """P-074 R7: the form asks for what the proposal was read against, what it leaves alone and its first slice."""
    template = (DOCS / "proposals" / "TEMPLATE_PROPOSAL.md").read_text(encoding="utf-8")
    sop = (DOCS / "PROPOSAL_CREATION_SOP.md").read_text(encoding="utf-8")
    for phrase in ("**Verified against:**", "**Files intentionally unchanged.**", "**First implementation slice.**"):
        assert phrase in template, f"TEMPLATE_PROPOSAL.md no longer asks for {phrase}"
    for phrase in ("**Verified against**", "**intentionally unchanged**", "**first implementation"):
        assert phrase in sop, f"PROPOSAL_CREATION_SOP.md no longer requires {phrase}"
