"""Every open owner decision carries one plain-English question beside its explanation.

The owner reads these tables to decide, not to audit. The explanation stays as long as it needs to be; the
question is additive and sits at the end of the explanation cell, so a reader can always find the ask:

    ... the full explanation ... **Question:** Use MIT as the license?

A question is one short sentence a person can answer yes or no, or close to it. It is written for the owner, so it
carries no identifiers, no code spans and no section marks; the row already names its source.

Where the rule applies (an open row is one whose state is not resolved, decided, done or dropped):

* the lane docs: every `CT-A`, `CT-D`, `ST-D` and `PL-D` row, and a "Decision for the owner" paragraph;
* the decision-gate tables of P-074 (`HYB-REDESIGN-D01` to `D10`) and P-075 (`OSS-D01` to `D16`);
* the design-system hub's `D-1` to `D-9`, in the README and as `ask` in `tokens.yaml`;
* every `Pending` queue row, and the decision tables of the proposals those rows link.

Offline and read-only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
MARKER = "**Question:**"
MAX_WORDS = 25
# An identifier is not plain English: P-067, CT-D01, OSS-D04, D-1. Hyphenated lower-case words are fine.
ID_LIKE = re.compile(r"\b[A-Z]{1,12}(?:-[A-Z]+)*-[A-Z]?\d+\b")
FORBIDDEN_CHARS = "`|§*"
CLOSED_STATES = ("resolved", "decided", "done", "dropped")
# The rule, as the owner gave it, written the same way wherever decisions are made. A row that merely carries a
# question does not state the rule, so this literal is what the documents below must hold.
RULE = "`**Question:** <one short sentence>`"

LANES = [
    "docs/todo/README.md",
    "docs/todo/CONTENT_CREATE_TODO.md",
    "docs/todo/STREAM_DECISIONS_AND_TODO.md",
]
LANE_ROW = re.compile(r"^(?:CT-[AD]|ST-D|PL-D)\d+$")
GATE_TABLES = {
    "docs/proposals/PROPOSAL_REDESIGN_FROM_OPENTECHAPP_PATTERN.md": ("HYB-REDESIGN-D", 10),
    "docs/proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md": ("OSS-D", 16),
}
DECISION_SECTION = re.compile(r"(?im)^(#{2,3}) .*(?:unresolved decisions|decision points|open questions|decision gates).*$")
BOLD_NUMBERED = re.compile(r"^\*\*[QD]\d+\*\*$")


def read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def cells_of(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def tables(text: str):
    """Yield (header cells, [(line number, cells)]) for each markdown table; rows hold no pipe inside a cell."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("|") and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
            header, rows, j = cells_of(lines[i]), [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append((j + 1, cells_of(lines[j])))
                j += 1
            yield header, rows
            i = j
        else:
            i += 1


def question_in(cells: list[str]) -> str | None:
    """The sentence after the marker, only if the marker is the last thing in exactly one cell."""
    found = [cell for cell in cells if MARKER in cell]
    if len(found) != 1 or found[0].count(MARKER) != 1:
        return None
    tail = found[0].split(MARKER, 1)[1].strip()
    return tail or None


def problems(sentence: str) -> list[str]:
    """Why a question is not a short plain-English sentence. Empty when it is."""
    found = []
    if not sentence.endswith("?") or sentence.count("?") != 1:
        found.append("must be exactly one sentence ending in a question mark")
    if len(sentence.split()) > MAX_WORDS:
        found.append(f"is {len(sentence.split())} words; keep it under {MAX_WORDS}")
    if any(ch in sentence for ch in FORBIDDEN_CHARS):
        found.append("holds a code span, table pipe, section mark or emphasis")
    if "](" in sentence:
        found.append("holds a link")
    if ID_LIKE.search(sentence):
        found.append(f"holds the identifier {ID_LIKE.search(sentence).group(0)!r}; say it in words")
    if not sentence[:1].isupper():
        found.append("must start with a capital letter")
    return found


def _check(where: str, cells: list[str], failures: list[str]) -> str | None:
    sentence = question_in(cells)
    if sentence is None:
        failures.append(f"{where}: no single trailing {MARKER} line")
        return None
    failures += [f"{where}: question {why}" for why in problems(sentence)]
    return sentence


def lane_rows():
    """(relative path, line number, ID, cells) for every open decision row in the lane docs."""
    for relative in LANES:
        for header, rows in tables(read(relative)):
            if not header or header[0] != "ID" or header[-1] != "State":
                continue
            for number, cells in rows:
                if not LANE_ROW.match(cells[0]):
                    continue
                state = re.sub(r"[*`_]", "", cells[-1]).strip().lower()
                if not state.startswith(CLOSED_STATES):
                    yield relative, number, cells[0], cells


def test_the_sentence_rules_catch_what_they_describe():
    assert problems("Use MIT as the license?") == []
    assert problems("Use MIT, or Apache-2.0, as the license?") == []
    assert problems("Rename rook-tactician and lux-commentator to nova-prefixed names?") == []
    assert problems("Use MIT.")
    assert problems("Use MIT? Or Apache?")
    assert problems("use MIT as the license?")
    assert problems("Use the `MIT` license?")
    assert problems("Accept P-067 as written?")
    assert problems("Answer OSS-D01 now?")
    assert problems("Is this plain " + "word " * 25 + "?")  # over the length cap, with a single question mark
    assert problems("Is this plain " + "word " * 10 + "?") == []
    assert problems("See [the plan](x.md) now?")


def test_the_lane_docs_were_read():
    ids = {cells[0] for _r, _n, _i, cells in lane_rows()}
    assert {"CT-A01", "CT-D01", "ST-D01", "PL-D01", "PL-D15", "PL-D16"} <= ids
    assert len(ids) >= 50, f"only {len(ids)} open decision rows found: the table parser stopped reading something"
    assert "PL-D08" not in ids, "a row whose state starts with 'Resolved' is closed and needs no question"


def test_every_open_lane_decision_carries_a_question():
    failures: list[str] = []
    for relative, number, row_id, cells in lane_rows():
        _check(f"{relative}:{number} {row_id}", cells, failures)
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("relative", LANES)
def test_a_decision_for_the_owner_paragraph_carries_a_question(relative):
    paragraphs = re.split(r"\n\s*\n", read(relative))
    asked = [p for p in paragraphs if p.lstrip().startswith("**Decision for the owner")]
    for paragraph in asked:
        assert paragraph.count(MARKER) == 1, f"{relative}: a 'Decision for the owner' paragraph has no {MARKER} line"
        tail = paragraph.split(MARKER, 1)[1].strip()
        assert not problems(tail), f"{relative}: {problems(tail)}"


@pytest.mark.parametrize("relative", sorted(GATE_TABLES))
def test_every_decision_gate_carries_a_question(relative):
    prefix, count = GATE_TABLES[relative]
    failures: list[str] = []
    seen = set()
    for header, rows in tables(read(relative)):
        if header[:2] != ["Gate", "Question"]:
            continue
        for number, cells in rows:
            gate = cells[0].strip("`")
            if not gate.startswith(prefix):
                continue
            seen.add(gate)
            _check(f"{relative}:{number} {gate}", cells, failures)
    assert seen == {f"{prefix}{n:02d}" for n in range(1, count + 1)}, f"{relative}: gates found {sorted(seen)}"
    assert not failures, "\n".join(failures)


def test_every_hub_decision_has_an_ask_and_the_readme_repeats_it():
    decisions = yaml.safe_load(read("design-system/tokens.yaml"))["decisions"]
    in_readme: dict[str, str] = {}
    failures: list[str] = []
    for header, rows in tables(read("design-system/README.md")):
        if header[:1] == ["ID"]:
            for number, cells in rows:
                if re.fullmatch(r"D-\d+", cells[0]):
                    in_readme[cells[0]] = _check(f"design-system/README.md:{number} {cells[0]}", cells, failures) or ""
    assert set(in_readme) == set(decisions), f"README decisions {sorted(in_readme)} vs tokens.yaml {sorted(decisions)}"
    for key, decision in decisions.items():
        ask = decision.get("ask", "")
        failures += [f"tokens.yaml {key}: ask {why}" for why in problems(ask)] if ask else [f"tokens.yaml {key}: no ask"]
        if in_readme[key] != ask:
            failures.append(f"{key}: the README question and tokens.yaml ask differ; tokens.yaml is the source")
    assert not failures, "\n".join(failures)


def _pending_rows():
    text = read("docs/PROPOSALS.md")
    section = re.search(r"(?ms)^## Pending\s*$(.*?)(?=^## )", text)
    assert section, "docs/PROPOSALS.md has no Pending section"
    for line in section.group(1).splitlines():
        if re.match(r"^\| P-\d+ \|", line):
            yield cells_of(line)


def test_every_pending_proposal_asks_whether_to_accept_it():
    failures: list[str] = []
    for cells in _pending_rows():
        _check(f"docs/PROPOSALS.md {cells[0]}", cells, failures)
    assert not failures, "\n".join(failures)


def test_the_decision_tables_of_pending_proposals_carry_questions():
    failures: list[str] = []
    for cells in _pending_rows():
        link = re.search(r"\]\((proposals/[^)#]+\.md)\)", cells[1])
        if not link:
            continue
        relative = f"docs/{link.group(1)}"
        text = read(relative)
        numbered = 0
        for _header, rows in tables(text):
            for number, row in rows:
                if BOLD_NUMBERED.match(row[0]) and not any("~~" in cell for cell in row):
                    numbered += 1
                    _check(f"{relative}:{number} {row[0]}", row, failures)
        for section in DECISION_SECTION.finditer(text):
            level = len(section.group(1))
            end = re.search(rf"(?m)^#{{1,{level}}} ", text[section.end():])
            body = text[section.end(): section.end() + end.start()] if end else text[section.end():]
            has_rows = any(rows for _h, rows in tables(body))
            if has_rows and not numbered and MARKER not in body:
                failures.append(f"{relative}: its decision section {section.group(0).strip()!r} has no {MARKER} line")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("relative", [
    "CLAUDE.md",
    "AGENTS.md",
    "docs/PROPOSAL_CREATION_SOP.md",
    "docs/proposals/TEMPLATE_PROPOSAL.md",
    "docs/todo/README.md",
])
def test_the_rule_is_written_down_where_decisions_are_made(relative):
    assert RULE in read(relative), f"{relative} must state the rule: every owner decision carries {RULE} beside its explanation"
