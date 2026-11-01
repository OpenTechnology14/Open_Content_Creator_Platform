"""A lane row is a derived index of the queue, so it must not outlive the state it was derived from.

`docs/todo/` says "the source wins": when a row and its proposal disagree, the row is the one that is wrong. `proposal_report.py`
checks the queue against the lane map by proposal id. These checks cover the rows themselves, each of which was found stale
once and fixed by hand:

* an *Awaiting acceptance* row names a proposal the queue no longer shows as `Pending` (`CT-A06`, with P-061 In progress);
* a decision asks the owner to accept or retire a proposal that is already accepted (`PL-D09`, with P-005 In progress);
* an "also <ID>" pointer leads to a row about something else (`PL-D07` pointed at `CT-D13`, the lesson status words, for the
  product naming decision, which is `CT-D12`);
* the design-system hub says the repository has no root `LICENSE` after one was added (D-9).

Offline and read-only.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LANES = [
    "docs/todo/README.md",
    "docs/todo/CONTENT_CREATE_TODO.md",
    "docs/todo/STREAM_DECISIONS_AND_TODO.md",
]
MARKER = "**Question:**"
CLOSED = ("resolved", "decided", "done", "dropped")
ROW_ID = re.compile(r"^(?:CT|ST|PL)-[AD]\d+$")
PROPOSAL = re.compile(r"\bP-\d{3}\b")


def read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def cells_of(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def lane_rows() -> dict[str, dict]:
    """Every lane decision or acceptance row by id: its cells, its line, and whether it is still open."""
    found: dict[str, dict] = {}
    for relative in LANES:
        lines = read(relative).splitlines()
        for number, line in enumerate(lines, 1):
            if not line.startswith("| "):
                continue
            cells = cells_of(line)
            if not ROW_ID.match(cells[0]):
                continue
            state = re.sub(r"[*`_]", "", cells[-1]).strip().lower()
            found[cells[0]] = {"file": relative, "line": number, "cells": cells, "open": not state.startswith(CLOSED)}
    return found


def queue_states() -> dict[str, str]:
    """Proposal id -> the first words of its queue status, lower case and without markup."""
    states = {}
    for line in read("docs/PROPOSALS.md").splitlines():
        match = re.match(r"^\| (P-\d+) \|", line)
        if match:
            # The first occurrence is the live queue; the historical notes further down repeat ids with older states.
            states.setdefault(match.group(1), re.sub(r"[*`]", "", cells_of(line)[2]).strip().lower())
    return states


def test_the_rows_and_the_queue_were_read():
    rows, states = lane_rows(), queue_states()
    assert {"CT-A01", "CT-D12", "PL-D07", "PL-D09"} <= set(rows)
    assert states["P-061"].startswith("in progress") and len(states) >= 60


def test_an_awaiting_acceptance_row_names_a_pending_proposal():
    states, failures = queue_states(), []
    for row_id, row in lane_rows().items():
        if not row_id.startswith(("CT-A", "ST-A")) or not row["open"]:
            continue
        proposal = PROPOSAL.search(row["cells"][1])
        if not proposal:
            failures.append(f"{row['file']}:{row['line']} {row_id}: no proposal id in {row['cells'][1][:50]!r}")
        elif not states.get(proposal.group(0), "").startswith("pending"):
            failures.append(
                f"{row['file']}:{row['line']} {row_id}: awaits acceptance, but the queue shows {proposal.group(0)} as "
                f"{states.get(proposal.group(0), 'absent')[:40]!r}. Move the row to the Resolved log with the date it was accepted."
            )
    assert not failures, "\n".join(failures)


def test_a_decision_to_accept_or_retire_names_only_proposals_that_wait():
    states, failures = queue_states(), []
    for row_id, row in lane_rows().items():
        if not row_id.startswith(("CT-D", "ST-D", "PL-D")) or not row["open"]:
            continue
        decision = row["cells"][1].split(MARKER)[0]
        if not (re.search(r"\baccept\b", decision, re.I) and re.search(r"\bretire\b", decision, re.I)):
            continue
        for proposal in sorted(set(PROPOSAL.findall(decision))):
            if not states.get(proposal, "").startswith(("pending", "deferred")):
                failures.append(
                    f"{row['file']}:{row['line']} {row_id}: asks to accept or retire {proposal}, "
                    f"but the queue shows it as {states.get(proposal, 'absent')[:40]!r}"
                )
    assert not failures, "\n".join(failures)


def test_an_also_pointer_leads_to_a_row_about_the_same_proposal():
    rows, failures = lane_rows(), []
    for row_id, row in rows.items():
        source = row["cells"][2] if len(row["cells"]) > 3 else ""
        for target in re.findall(r"\balso ((?:CT|ST|PL)-[AD]\d+)\b", source):
            if target not in rows:
                failures.append(f"{row_id} points at {target}, which has no row")
                continue
            mine = set(PROPOSAL.findall(" ".join(row["cells"][1:3])))
            theirs = set(PROPOSAL.findall(" ".join(rows[target]["cells"][1:3])))
            if not mine & theirs:
                failures.append(
                    f"{row['file']}:{row['line']} {row_id} says 'also {target}', but {target} is about "
                    f"{sorted(theirs) or 'no proposal'} and {row_id} about {sorted(mine) or 'no proposal'}"
                )
    assert not failures, "\n".join(failures)


def test_the_hub_does_not_say_the_repository_has_no_root_license():
    assert (REPO / "LICENSE").exists(), "this check holds only while a root LICENSE exists"
    claim = re.compile(r"\bno root[\s`*]*licen[sc]e", re.I)
    stale = []
    for path in sorted((REPO / "design-system").rglob("*")):
        if path.suffix in {".md", ".yaml"} and claim.search(path.read_text(encoding="utf-8")):
            stale.append(str(path.relative_to(REPO)))
    assert not stale, f"{stale} still say there is no root LICENSE; the repository has had one since P-075"
