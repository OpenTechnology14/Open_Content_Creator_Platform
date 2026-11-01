"""The entry gate is a pointer, not a copy.

CLAUDE.md section 17 sends every agent to the public AgentWorkflows library for the work types and the
"register, then start" gate, at one pinned revision. The four skills that begin work repeat the pointer. This
repository keeps no list of Kinds of its own: a copy would drift, which is the problem the library's single list
exists to end.

Offline and read-only. It checks that the pointer is internally consistent, not that the pinned revision still exists.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = ["code-creation", "docs", "design", "audits"]
LIBRARY = re.compile(r"github\.com/OpenTechnology14/AgentWorkflows/blob/([0-9a-f]{40})/workflows/(WORK_TYPES|ENTRY_GATE)\.md")
# A distinctive Kind from the library's list. If it appears here, someone copied the list.
COPY_MARKER = "proposal remainder"


def read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def section_17(name: str = "CLAUDE.md") -> str:
    text = read(name)
    assert "## 17. Work registration" in text, f"{name} has no section 17"
    return text.split("## 17. Work registration", 1)[1]


@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md"])
def test_section_17_links_both_library_workflows_at_one_pinned_revision(name):
    found = LIBRARY.findall(section_17(name))
    assert {workflow for _rev, workflow in found} == {"WORK_TYPES", "ENTRY_GATE"}, f"{name}: link both workflows"
    assert len({rev for rev, _workflow in found}) == 1, f"{name}: the two links must pin the same revision"
    assert found[0][0] in section_17(name).replace("blob/" + found[0][0], ""), f"{name}: state the pinned revision in words too"


@pytest.mark.parametrize("skill", SKILLS)
def test_each_skill_that_starts_work_carries_the_pointer(skill):
    text = read(f".claude/skills/{skill}/SKILL.md")
    assert "**Register first.**" in text, f"{skill}: no 'Register first' paragraph"
    assert "`CLAUDE.md` section 17" in text, f"{skill}: it must cite CLAUDE.md section 17"


def test_the_prompt_kit_preamble_carries_the_pointer():
    assert "Register the task with its one Kind" in read("docs/design/BUILD-PROMPTING-DIGEST.md")


@pytest.mark.parametrize("relative", [
    "CLAUDE.md", "AGENTS.md", "docs/design/BUILD-PROMPTING-DIGEST.md", "docs/PROPOSAL_CREATION_SOP.md",
    *[f".claude/skills/{s}/SKILL.md" for s in SKILLS],
])
def test_no_local_copy_of_the_kind_list(relative):
    assert COPY_MARKER not in read(relative).lower(), (
        f"{relative} lists the library's Kinds. Link the library's work types instead of copying them."
    )
