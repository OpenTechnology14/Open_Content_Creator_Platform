"""Derive proposal counts, assignments and lane coverage from the canonical queue."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]


def state_of(text: str) -> str:
    """Normalize existing queue vocabulary without changing its authorization text."""
    clean = text.replace("*", "").replace("`", "").strip().lower()
    if clean.startswith("accepted (in use)"):
        return "standing"
    for prefix, state in (
        ("done", "done"), ("in progress", "in_progress"), ("accepted", "accepted"),
        ("pending", "pending"), ("deferred", "deferred"),
        ("code", "acceptance_open"), ("partially", "acceptance_open"),
    ):
        if clean.startswith(prefix):
            return state
    raise ValueError(f"unknown proposal state: {text}")


def report(queue: str, lane_index: str) -> dict:
    """Reject duplicate/unassigned proposals and report derived lane discrepancies."""
    rows = []
    seen = set()
    section = None
    testing_group = None
    headings = {
        "Accepted": "accepted", "In progress": "in_progress", "Testing": "testing",
        "Pending": "pending", "Deferred": "deferred", "Done": "done",
        "Accepted (in use) — standing practice": "standing",
    }
    for line in queue.splitlines():
        if line.startswith("## "):
            section = headings.get(line[3:].strip())
            testing_group = None
        elif section == "testing" and line.startswith("### "):
            testing_group = {
                "Mainly acceptance": "mainly_acceptance",
                "Testing with remaining features or delivery": "remaining_work",
            }.get(line[4:].strip())
        if not re.match(r"^\| P-\d+ \|", line):
            continue
        fields = line.split("|")
        if len(fields) < 7:
            raise ValueError("malformed proposal row")
        proposal_id = fields[1].strip()
        if proposal_id in seen:
            raise ValueError(f"duplicate proposal: {proposal_id}")
        seen.add(proposal_id)
        assignment = re.search(r"`(gpt-[a-z0-9.-]+)`\s*/\s*`([a-z]+)`", fields[5])
        if not assignment:
            raise ValueError(f"missing model/effort: {proposal_id}")
        state = state_of(fields[3])
        if section == "testing" and state != "in_progress":
            raise ValueError(f"Testing rows must remain In progress: {proposal_id}")
        rows.append({
            "id": proposal_id, "title": fields[2].strip(), "status": fields[3].strip(),
            "state": state, "model": assignment[1], "effort": assignment[2],
            "work_focus": section or state,
            "testing_group": testing_group if section == "testing" else None,
        })
    if not rows:
        raise ValueError("proposal queue is empty")
    counts = Counter(row["state"] for row in rows)
    work_counts = Counter(row["work_focus"] for row in rows)
    testing_counts = Counter(
        row["testing_group"] or "unclassified" for row in rows if row["work_focus"] == "testing"
    )
    unfinished = [row for row in rows if row["state"] not in {"done", "standing"}]
    lane_ids = set(re.findall(r"^\| (P-\d+)\b", lane_index, re.MULTILINE))
    expected = {row["id"] for row in unfinished}
    models = {}
    for row in unfinished:
        models.setdefault(row["model"], []).append(row["id"])
    return {
        "schema_version": 1, "total": len(rows), "unfinished": len(unfinished),
        "counts": dict(sorted(counts.items())), "unfinished_by_model": models,
        "work_counts": dict(sorted(work_counts.items())),
        "testing_counts": dict(sorted(testing_counts.items())),
        "lane_missing": sorted(expected - lane_ids), "lane_extra": sorted(lane_ids - expected),
        "proposals": rows,
        "authorization_note": "Canonical status text and owner instructions control scope; model labels do not grant authority.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if unfinished queue and lane map disagree")
    parser.add_argument("--summary", action="store_true", help="omit individual proposal rows")
    args = parser.parse_args(argv)
    try:
        data = report(
            (ROOT / "docs/PROPOSALS.md").read_text(encoding="utf-8"),
            (ROOT / "docs/todo/README.md").read_text(encoding="utf-8"),
        )
    except (ValueError, OSError) as exc:
        sys.stderr.write(f"Proposal report failed: {exc}\n")
        return 2
    if args.summary:
        data.pop("proposals")
    sys.stdout.write(json.dumps(data, indent=2) + "\n")
    return int(args.check and bool(data["lane_missing"] or data["lane_extra"]))


if __name__ == "__main__":
    raise SystemExit(main())
