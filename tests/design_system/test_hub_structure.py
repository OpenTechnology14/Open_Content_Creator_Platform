"""The hub is one thing in several places: its files, a README table, a registry row, a consumers list, the agent
instructions, and three copies of the voice registers. These tests fail when any of them stop agreeing."""
from __future__ import annotations

import re

import pytest
import yaml

from helpers import HUB, REPO, load

T = load()
FILES = ("README.md", "components.md", "voice-and-tone.md", "iconography.md", "accessibility.md",
         "crosswalk/consumers.md", "proposals/TEMPLATE.md", "tokens.yaml")
MARKDOWN = tuple(f for f in FILES if f.endswith(".md"))
REGISTRY = REPO / "modules" / "marketing-crosswalk" / "crosswalk" / "modules.yml"
STATE_WORDS = {"present": "**present**", "absent": "**absent**", "local-draft": "**drafted on a local branch only**"}


def text(relative: str) -> str:
    return (HUB / relative).read_text(encoding="utf-8")


def row() -> dict:
    rows = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["modules"]
    return next(r for r in rows if r["module"] == "design-system")


@pytest.mark.parametrize("relative", FILES)
def test_the_specified_files_exist(relative):
    assert (HUB / relative).is_file(), f"design-system/{relative} is missing"


def test_the_hub_holds_only_specification_and_data():
    """The request: the spec layer has no implementation code. Only markdown and YAML live here."""
    stray = sorted(str(p.relative_to(HUB)) for p in HUB.rglob("*") if p.is_file() and p.suffix not in (".md", ".yaml"))
    assert not stray, f"implementation or binary files in the hub: {stray}"
    assert "```" not in text("components.md"), "components.md is a specification: no code blocks"


@pytest.mark.parametrize("relative", MARKDOWN)
def test_every_document_declares_its_status(relative):
    head = text(relative)[:600]
    assert "**Status:**" in head, f"{relative}: no status banner"
    if relative != "proposals/TEMPLATE.md":
        assert "drafted — awaiting owner review" in head or "approved" in head, f"{relative}: status is neither drafted nor approved"


def test_the_readme_lists_every_file_and_exactly_the_decisions_in_tokens_yaml():
    readme = text("README.md")
    for relative in FILES[1:]:
        assert relative in readme, f"README does not list {relative}"
    in_table = set(re.findall(r"^\| (D-\d+) \|", readme, re.M))
    assert in_table == set(T["decisions"]), f"README decisions {sorted(in_table)} vs tokens.yaml {sorted(T['decisions'])}"


def test_every_decision_cited_anywhere_in_the_hub_exists():
    cited = set()
    for relative in MARKDOWN:
        cited |= set(re.findall(r"\bD-\d+\b", text(relative)))
    unknown = cited - set(T["decisions"])
    assert not unknown, f"cited but not defined in tokens.yaml: {sorted(unknown)}"


def test_the_registry_row_describes_the_hub():
    r = row()
    assert r["kind"] == "design-system-hub" and r["status"] == "drafted" and r["target"] == "hybrid-creator-platform"
    assert r.get("visibility") is None, "the hub is public to the platform: it is never a private row"
    for key, path in r["files"].items():
        if key != "target_repo":
            assert (REPO / path).is_file(), f"files.{key}: {path} does not exist"


def test_the_registry_counts_recompute():
    counts = row()["counts"]
    assert counts["subjects"] == 0
    assert counts["doc_files"] == len(list(HUB.rglob("*.md")))
    assert counts["data_files"] == len(list(HUB.rglob("*.yaml")))
    assert counts["color_tokens"] == len(T["color"])
    assert counts["type_tokens"] == len(T["type"])
    assert counts["decisions"] == len(T["decisions"])
    assert counts["known_contrast_failures"] == len(T["contrast"]["known_failures"])


def test_the_consumers_list_and_the_registry_agree():
    consumers_md = text("crosswalk/consumers.md")
    listed = set(re.findall(r"`([A-Za-z-]+):((?:docs|Docs)/design/DESIGN-SYSTEM-POINTER\.md)`", consumers_md))
    registry = {(c["name"], c["pointer_doc"]) for c in row()["consumers"]}
    assert listed == registry, f"consumers.md {sorted(listed)} vs registry {sorted(registry)}"
    for consumer in row()["consumers"]:
        needle = f"`{consumer['name']}:{consumer['pointer_doc']}`"
        line = next(text_line for text_line in consumers_md.splitlines() if needle in text_line)
        assert STATE_WORDS[consumer["pointer_state"]] in line, f"{consumer['name']}: state {consumer['pointer_state']!r} is not what the table says"


REGISTERS = ("young, energetic, expressive", "young, energetic, latin-accented", "deep, warm, measured, narrative")
REGISTER_COPIES = ("design-system/voice-and-tone.md", ".claude/skills/design/SKILL.md", "docs/design/BUILD-PROMPTING-DIGEST.md")


@pytest.mark.parametrize("path", REGISTER_COPIES)
def test_the_three_registers_read_the_same_everywhere(path):
    flat = re.sub(r"[*_`]", "", (REPO / path).read_text(encoding="utf-8")).lower()
    missing = [r for r in REGISTERS if r not in flat]
    assert not missing, f"{path} no longer says: {missing}"


@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md"])
def test_agent_instructions_point_at_the_hub(name):
    body = (REPO / name).read_text(encoding="utf-8")
    assert "## 15. Design system" in body
    section = body.split("## 15. Design system", 1)[1]
    for relative in FILES:
        assert f"design-system/{relative}" in section, f"{name} §15 does not point at design-system/{relative}"
    assert "approved" in section, f"{name} §15 must state the adoption rule"


def test_the_docs_index_links_the_hub():
    assert "../design-system/README.md" in (REPO / "docs" / "README.md").read_text(encoding="utf-8")


def test_the_design_skill_and_digest_point_at_the_hub():
    for path in (".claude/skills/design/SKILL.md", "docs/design/BUILD-PROMPTING-DIGEST.md"):
        assert "design-system/" in (REPO / path).read_text(encoding="utf-8"), path

def test_the_contrast_numbers_quoted_in_accessibility_md_are_the_computed_ones():
    """accessibility.md repeats the failures on purpose so a human can read them; the repeat is verified."""
    doc = text("accessibility.md")
    for failure in T["contrast"]["known_failures"]:
        assert f"{failure['ratio']:.2f}" in doc, f"accessibility.md does not quote {failure['pair']} ({failure['theme']}): {failure['ratio']:.2f}"
    for observed in T["contrast"]["observed_pairs"]:
        assert f"{observed['ratio']:.2f}" in doc, f"accessibility.md does not quote {observed['id']}: {observed['ratio']:.2f}"
