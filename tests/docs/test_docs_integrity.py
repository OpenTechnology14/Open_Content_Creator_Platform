"""Documentation integrity — the checks that were run ad-hoc all session.

A verification step only counts if it is a command. These were being retyped as
throwaway snippets, which means they were one forgetful session away from never
running again. They are part of `make test` now.

All offline: no network, no services.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
MODULES = REPO / "modules"
DESIGN_SYSTEM = REPO / "design-system"

LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
EXTERNAL = ("http://", "https://", "#", "mailto:")


def _markdown_files() -> list[Path]:
    """Every tracked markdown file. Generated drafts under out/ are excluded.

    Filtered against `git ls-files`, not just walked with rglob — a gitignored
    local install anywhere under modules/ (a cloned tool, a venv, a node_modules)
    ships its own .md files with links that resolve relative to *its* repo, not
    this one, and rglob alone picked those up and failed them. Real bug, found
    2026-09-02 (P-043) by actually having such an install on disk for the first
    time (modules/realtime-ai/comfyui/app/, gitignored but rglob doesn't know
    that) — the docstring already claimed "tracked", the code just never
    checked.
    """
    found: list[Path] = []
    for root in (DOCS, MODULES):
        found += [p for p in root.rglob("*.md") if "/out/" not in str(p)]
    found += list(DESIGN_SYSTEM.rglob("*.md"))
    found += [REPO / "README.md", REPO / "CLAUDE.md", REPO / "tests" / "README.md"]
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.splitlines()
    )
    return sorted(
        p for p in found if p.is_file() and str(p.relative_to(REPO)) in tracked
    )


@pytest.mark.parametrize("doc", _markdown_files(), ids=lambda p: str(p.relative_to(REPO)))
def test_relative_links_resolve(doc: Path) -> None:
    """A broken relative link is a doc that silently lies about where something is."""
    broken = []
    for _text, href in LINK.findall(doc.read_text(encoding="utf-8")):
        if href.startswith(EXTERNAL):
            continue
        target = (doc.parent / href.split("#")[0]).resolve()
        if not target.exists():
            broken.append(href)
    assert not broken, f"{doc.relative_to(REPO)} links to missing: {broken}"


def test_every_doc_is_in_the_index() -> None:
    """DM-DOCS-INDEX: a doc that is not in the index is a doc nobody opens.

    Proposal documents are exempt — they are indexed by the queue, not here, and
    `test_every_proposal_has_a_queue_row` covers them instead.
    """
    index = (DOCS / "README.md").read_text(encoding="utf-8")
    missing = []
    for doc in sorted(DOCS.rglob("*.md")):
        rel = doc.relative_to(DOCS)
        if doc.name == "README.md" and doc.parent == DOCS:
            continue
        if rel.parts[0] == "proposals":
            continue
        if str(rel) not in index and doc.name not in index:
            missing.append(str(rel))
    assert not missing, f"not listed in docs/README.md: {missing}"


def test_every_proposal_has_a_queue_row() -> None:
    """A proposal document that no row points at is not queued work."""
    queue = (DOCS / "PROPOSALS.md").read_text(encoding="utf-8")
    unqueued = [
        p.name
        for p in sorted((DOCS / "proposals").glob("*.md"))
        if p.name != "TEMPLATE_PROPOSAL.md" and p.name not in queue
    ]
    assert not unqueued, f"proposal docs with no queue row: {unqueued}"


def test_every_module_has_both_setup_docs() -> None:
    """A module without both setup docs cannot be stood up or honestly described."""
    missing = []
    for module in sorted(p for p in MODULES.iterdir() if p.is_dir()):
        for name in ("manual.md", "automated.md"):
            if not (module / "setup" / name).is_file():
                missing.append(f"{module.name}/setup/{name}")
    assert not missing, f"missing setup docs: {missing}"


def test_every_module_readme_declares_labels() -> None:
    """Labels decide which product a module belongs to; an unlabelled one is invisible."""
    unlabelled = []
    for module in sorted(p for p in MODULES.iterdir() if p.is_dir()):
        readme = module / "README.md"
        if not readme.is_file():
            unlabelled.append(f"{module.name} (no README)")
            continue
        body = readme.read_text(encoding="utf-8")
        if not re.search(r"\*\*Labels:\*\*.*`(Content|Stream)`", body):
            unlabelled.append(module.name)
    assert not unlabelled, f"modules without a Labels line: {unlabelled}"


def test_every_module_appears_in_module_indexes() -> None:
    """DM-MODULE: module reference indexes go stale together when a module is added."""
    names = sorted(p.name for p in MODULES.iterdir() if p.is_dir())
    for matrix in (
        "MODULE-MATRIX.md",
        "MODULE-ITEM-MATRIX.md",
        "SUBFEATURE-CHECKLIST.md",
    ):
        body = (DOCS / "agent" / matrix).read_text(encoding="utf-8")
        missing = [n for n in names if n not in body]
        assert not missing, f"{matrix} does not list: {missing}"


def test_module_status_table_covers_every_module() -> None:
    """CLAUDE.md §11 gates every marketing claim; a module missing from it is ungated."""
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    section = claude[claude.index("## 11."):]
    section = section[: section.index("## 12.")]
    missing = [p.name for p in MODULES.iterdir() if p.is_dir() and p.name not in section]
    assert not missing, f"CLAUDE.md §11 has no status row for: {missing}"


@pytest.mark.parametrize(
    "doc",
    sorted((DOCS / "agent").glob("*.md")) + [DOCS / "SETUP-TECHNIQUE-NOTES.md", DOCS / "PROPOSALS.md"],
    ids=lambda p: p.name,
)
def test_living_docs_declare_status_and_enforcement(doc: Path) -> None:
    """A reference doc that does not say whether it binds anyone is decoration."""
    body = doc.read_text(encoding="utf-8")
    assert "**Status:**" in body, f"{doc.name} has no Status header"
    assert "**Last reviewed:**" in body, f"{doc.name} has no Last reviewed date"
    if doc.name != "README.md":
        assert "Enforcement" in body, (
            f"{doc.name} does not state its enforcement (reference / advisory / required)"
        )


# ── Manual setup docs carry the verification a human must finish ────────────
CHECKLIST = REPO / "tests" / "ACCEPTANCE-CHECKLIST.md"


@pytest.mark.parametrize(
    "manual",
    sorted(MODULES.glob("*/setup/manual.md")),
    ids=lambda p: p.parts[-3],
)
def test_manual_setup_doc_has_both_verification_halves(manual: Path) -> None:
    """Setup is not finished at "installed" — it is finished at "verified".

    Both halves are required. The automated half is cheap and catches problems
    that do not need the module installed; the manual half is the part no script
    can do, and it is the whole reason these docs exist.
    """
    body = manual.read_text(encoding="utf-8")
    module = manual.parts[-3]
    assert "## Verification" in body, f"{module}: no Verification section"
    assert "**Automated — run these:**" in body, f"{module}: no automated half"
    assert "**Manual — nothing automates these:**" in body, f"{module}: no manual half"
    assert "### Last step — full feature test run" in body, (
        f"{module}: no full-feature-test-run step. That is the last step of every module."
    )
    assert "ACCEPTANCE-CHECKLIST.md" in body, (
        f"{module}: last step does not point at the acceptance checklist"
    )


@pytest.mark.parametrize(
    "manual",
    sorted(MODULES.glob("*/setup/manual.md")),
    ids=lambda p: p.parts[-3],
)
def test_manual_half_is_a_checklist(manual: Path) -> None:
    """The manual half is something a human ticks off, not prose to skim."""
    body = manual.read_text(encoding="utf-8")
    half = body.split("**Manual — nothing automates these:**", 1)[1]
    half = half.split("### Last step", 1)[0]
    assert "- [ ]" in half, (
        f"{manual.parts[-3]}: manual half has no checkboxes — it should be tickable"
    )


def test_acceptance_checklist_covers_every_module() -> None:
    """A module absent from the checklist can never be called done."""
    body = CHECKLIST.read_text(encoding="utf-8")
    missing = [
        p.name for p in sorted(MODULES.iterdir())
        if p.is_dir() and f"`{p.name}`" not in body
    ]
    assert not missing, f"tests/ACCEPTANCE-CHECKLIST.md has no section naming: {missing}"


def test_every_checklist_line_is_annotated() -> None:
    """An unannotated line has never been assessed — the file says so itself."""
    body = CHECKLIST.read_text(encoding="utf-8")
    section = body.split("## Foundations", 1)[1].split("## Current state", 1)[0]
    markers = ("**auto**", "**live**", "**manual**", "**blocked**")
    unannotated = [
        line.strip()
        for line in section.splitlines()
        if line.startswith("- ") and not any(m in line for m in markers)
    ]
    assert not unannotated, f"checklist lines with no proof marker: {unannotated}"


# ── Backticked paths: the class the markdown-link check misses ──────────────
# Two dead `docs/guides/archive/...` references survived a full link check
# because they were written as `path` rather than [text](path).
BACKTICKED_PATH = re.compile(
    r"`((?:docs|modules|scripts|tests|apps|cloud|plugins|design-system)/[A-Za-z0-9_./-]+\.[a-z]{2,4})`"
)


def _prose_docs() -> list[Path]:
    """Docs that describe what exists. Proposals are excluded — describing a file
    that does not exist yet is exactly what a proposal is for."""
    return [
        f
        for f in _markdown_files()
        if "proposals" not in f.parts and "/out/" not in str(f)
    ]


@pytest.mark.parametrize("doc", _prose_docs(), ids=lambda p: str(p.relative_to(REPO)))
def test_backticked_repo_paths_exist(doc: Path) -> None:
    """A backticked repo path that does not exist is a lie the link check misses."""
    # A path explicitly marked as not-yet-existing is honest, not a lie.
    FUTURE = ("will live", "when implemented", "not built", "does not exist",
              "proposed", "deferred", "missing", "absent", "no longer")
    dead = []
    for line in doc.read_text(encoding="utf-8").splitlines():
        if any(marker in line.lower() for marker in FUTURE):
            continue
        dead += [m for m in BACKTICKED_PATH.findall(line) if not (REPO / m).exists()]
    assert not dead, (
        f"{doc.relative_to(REPO)} references non-existent paths: {dead}. "
        "If the file is proposed rather than present, say so in prose or move the "
        "claim into a proposal."
    )


def test_agents_and_claude_stay_paired() -> None:
    """DM-CONTEXT: the two carry the same conventions for different agents.

    They drifted once — AGENTS.md kept the retired guide model in §4 and §11 for a
    full restructure, so an agent reading it was told to use a system that no
    longer existed.
    """
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")

    for num, nxt, label in (("4", "5", "Modules, Labels, and Setup"),
                            ("11", "12", "Module Status")):
        c = claude[claude.index(f"## {num}."):claude.index(f"## {nxt}.")]
        a = agents[agents.index(f"## {num}."):agents.index(f"## {nxt}.")]
        assert c == a, (
            f"CLAUDE.md and AGENTS.md §{num} ({label}) have drifted. "
            "These sections must stay identical — DM-CONTEXT."
        )

    # Neither may teach the retired guide series.
    for name, body in (("CLAUDE.md", claude), ("AGENTS.md", agents)):
        stale = re.findall(r"Guide [0-9]", body)
        assert not stale, f"{name} still references the retired guide series: {set(stale)}"


@pytest.mark.parametrize(
    "doc",
    [f for f in _markdown_files() if "modules" in f.parts],
    ids=lambda p: str(p.relative_to(REPO)),
)
def test_module_docs_do_not_teach_the_retired_guide_series(doc: Path) -> None:
    """The guide series is retired. A doc still pointing at it sends a reader nowhere.

    28 submodule docs kept these through a full restructure because the first
    sweep only checked top-level module READMEs.
    """
    body = doc.read_text(encoding="utf-8")
    stale = [
        line.strip()
        for line in body.splitlines()
        if re.search(r"\bGuide [0-9]", line) and "retired" not in line.lower()
    ]
    assert not stale, (
        f"{doc.relative_to(REPO)} references the retired guide series: {stale}. "
        "Point at the module's setup docs instead."
    )


def _module_source_files() -> list[Path]:
    """Non-markdown files under modules/, plus root-level config files,
    that can carry a stray "Guide N" reference — comments in scripts and
    configs, not just prose docs.

    root docker-compose.yml/docker-compose.digitalocean.yml joined
    2026-09-01 (P-033) after `docker-compose.yml` turned up three; root
    .env.example joined the same day (P-035) after it turned up four more
    — the original P-031/P-032 sweep only checked modules/, so any
    root-level file was never in scope at all. Each root-level addition
    here has actually had a violation found in it so far; that is worth
    noting in case it means this list still isn't exhaustive.
    docs/setup-timeline.html stays tracked separately (P-031) since fixing
    it is a real reorganisation, not a text substitution.
    """
    exts = (".py", ".yml", ".yaml", ".json", ".xml")
    module_files = (
        p for p in MODULES.rglob("*")
        if p.is_file() and p.suffix in exts and "/out/" not in str(p)
    )
    root_files = (
        p for p in (
            REPO / "docker-compose.yml",
            REPO / "docker-compose.digitalocean.yml",
            REPO / ".env.example",
        )
        if p.is_file()
    )
    return sorted((*module_files, *root_files))


@pytest.mark.parametrize(
    "src", _module_source_files(), ids=lambda p: str(p.relative_to(REPO))
)
def test_module_source_files_do_not_reference_the_retired_guide_series(src: Path) -> None:
    """Same rule as the markdown test above, for comments in code and config.

    14 files were found doing this on 2026-09-01 — scripts, YAML, and JSON
    workflow metadata — because the original sweep (P-029) only checked
    .md files. Extensions here are exactly the ones that check missed.
    """
    body = src.read_text(encoding="utf-8", errors="ignore")
    stale = [
        line.strip()
        for line in body.splitlines()
        if re.search(r"\bGuide [0-9]", line) and "retired" not in line.lower()
    ]
    assert not stale, (
        f"{src.relative_to(REPO)} references the retired guide series: {stale}. "
        "Point at the module's setup docs instead."
    )


USE_CASES = REPO / "tests" / "USE-CASES.md"


def test_use_cases_cover_every_module() -> None:
    """A module in no use case has never been shown to compose with anything.

    The point of the use cases is the union covering all 17 - a new module that
    joins no workflow is one nobody has thought about end to end.
    """
    body = USE_CASES.read_text(encoding="utf-8")
    missing = [
        p.name for p in sorted(MODULES.iterdir())
        if p.is_dir() and f"`{p.name}`" not in body
    ]
    assert not missing, f"tests/USE-CASES.md names no step for: {missing}"


def test_use_case_steps_are_annotated() -> None:
    """Every step needs a proof marker, same rule as the checklist."""
    body = USE_CASES.read_text(encoding="utf-8")
    markers = ("**auto", "**live**", "**manual**", "**blocked**")
    bad = [
        line.strip()
        for line in body.splitlines()
        # step rows look like: | 3 | ... | `module` | proof |
        if re.match(r"^\| \d+ \|", line) and not any(m in line for m in markers)
    ]
    assert not bad, f"use-case steps with no proof marker: {bad}"
