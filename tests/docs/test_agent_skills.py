"""Agent skills are instructions other tools read by path, so they get the same "a doc that lies"
protection as the rest of docs/: valid frontmatter, real paths, resolvable links, a pointer from
CLAUDE.md and its generated AGENTS.md mirror, and the voice guardrail from P-067 section 7.3.

Offline and read-only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO / ".claude" / "skills"
SKILLS = sorted(SKILL_DIR.glob("*/SKILL.md"))
DIGEST = REPO / "docs" / "design" / "BUILD-PROMPTING-DIGEST.md"
HUB = REPO / "design-system"
SURFACES = [*SKILLS, DIGEST, REPO / "CLAUDE.md", REPO / "AGENTS.md",
            *sorted(HUB.rglob("*.md")), HUB / "tokens.yaml"]

LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
EXTERNAL = ("http://", "https://", "#", "mailto:")
BACKTICKED_PATH = re.compile(
    r"`((?:docs|modules|scripts|tests|apps|cloud|plugins|design-system)/[A-Za-z0-9_./-]+\.[a-z]{2,4})`"
)
# A line that says a path is absent is honest, not a lie (same markers as test_docs_integrity).
FUTURE = ("will live", "when implemented", "not built", "does not exist", "proposed", "deferred",
          "missing", "absent", "no longer")
# Shipped by the static-audit pull request; the audits skill tells the reader to check before running.
# test_pending_paths_are_still_pending fails once they exist, so this list cannot outlive the wait.
PENDING = {"scripts/audit_test_coverage.py", "scripts/audit_dead_exports.py"}
# Frontmatter keys. `when_to_use` is read by Claude Code, which appends it to `description` in its skill
# listing and caps the pair; other tools read the file by path and ignore it, so `description` must stand alone.
REQUIRED_KEYS = {"name", "description", "when_to_use"}
OPTIONAL_KEYS = {"paths"}
LISTING_CAP = 1536


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.name}: no frontmatter"
    return yaml.safe_load(text.split("---\n", 2)[1])


def _ids(paths):
    return [str(p.relative_to(REPO)) for p in paths]


def test_there_are_skills():
    assert SKILLS, "glob found no skills: the directory moved or the filenames changed"


@pytest.mark.parametrize("skill", SKILLS, ids=_ids(SKILLS))
def test_frontmatter_is_valid(skill):
    meta = _frontmatter(skill)
    assert REQUIRED_KEYS <= set(meta) <= REQUIRED_KEYS | OPTIONAL_KEYS, \
        f"frontmatter keys {sorted(meta)}: need {sorted(REQUIRED_KEYS)}, may add {sorted(OPTIONAL_KEYS)}"
    assert meta["name"] == skill.parent.name, "name must equal the directory name"
    assert re.fullmatch(r"[a-z][a-z0-9-]{0,63}", meta["name"])
    assert 40 <= len(meta["description"]) <= 1024, "description must say when to use the skill, within 1024 chars"
    assert isinstance(meta["when_to_use"], str) and meta["when_to_use"].strip(), "when_to_use must be a non-empty string"
    assert len(meta["description"]) + len(meta["when_to_use"]) <= LISTING_CAP, \
        f"description + when_to_use is over Claude Code's {LISTING_CAP}-character listing cap"
    assert skill.read_text(encoding="utf-8").split("---\n", 2)[2].strip(), "empty body"


@pytest.mark.parametrize("skill", SKILLS, ids=_ids(SKILLS))
def test_backticked_repo_paths_exist(skill):
    dead = []
    for line in skill.read_text(encoding="utf-8").splitlines():
        if any(marker in line.lower() for marker in FUTURE):
            continue
        dead += [m for m in BACKTICKED_PATH.findall(line) if m not in PENDING and not (REPO / m).exists()]
    assert not dead, f"{skill.relative_to(REPO)} cites paths that do not exist: {sorted(set(dead))}"


@pytest.mark.parametrize("skill", SKILLS, ids=_ids(SKILLS))
def test_relative_links_resolve(skill):
    broken = [href for _t, href in LINK.findall(skill.read_text(encoding="utf-8"))
              if not href.startswith(EXTERNAL) and not (skill.parent / href.split("#")[0]).resolve().exists()]
    assert not broken, f"{skill.relative_to(REPO)} links to missing: {broken}"


def test_pending_paths_are_still_pending():
    existing = sorted(p for p in PENDING if (REPO / p).exists())
    assert not existing, f"{existing} now exist: delete them from PENDING so the skills are checked against them"


def _section_14(name: str) -> str:
    text = (REPO / name).read_text(encoding="utf-8")
    assert "## 14. Agent skills" in text, f"{name} has no section 14"
    return text.split("## 14. Agent skills", 1)[1]


@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md"])
def test_every_skill_is_pointed_at(name):
    section = _section_14(name)
    # A table row, not a passing mention: the pointer is only useful if the skill is listed with its trigger.
    missing = [s.parent.name for s in SKILLS if not re.search(rf"(?m)^\| `{re.escape(s.parent.name)}` \|", section)]
    assert not missing, f"{name} section 14 has no table row for: {missing}"


def test_digest_links_every_skill():
    text = DIGEST.read_text(encoding="utf-8")
    missing = [s.parent.name for s in SKILLS if f".claude/skills/{s.parent.name}/SKILL.md" not in text]
    assert not missing, f"BUILD-PROMPTING-DIGEST.md does not link: {missing}"


# P-067 section 7.3: the real people the owner cited are selection references only and must never
# appear in a prompt, voice name, config comment or marketing copy. Skills, the digest and the agent
# instruction files are all prompts. The needles are assembled so this file does not carry the names.
FORBIDDEN = [("ishow", "speed"), ("i show", " speed"), ("morgan", " freeman"), ("morgan", "-freeman")]


@pytest.mark.parametrize("surface", SURFACES, ids=_ids(SURFACES))
def test_voice_references_are_described_never_named(surface):
    text = surface.read_text(encoding="utf-8").lower()
    hits = ["".join(parts) for parts in FORBIDDEN if "".join(parts) in text]
    assert not hits, (
        f"{surface.relative_to(REPO)} names a real person as a voice reference. Describe the register instead "
        "(docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md section 7.3)."
    )
