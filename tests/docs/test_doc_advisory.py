"""The doc-update advisory maps changed paths to the rules in DOC-UPDATE-MATRIX.md, and only advises.

Covers the glob semantics, the registry the rules come from, the generator that reads the matrix's
"Path triggers" table, and a synthetic git repository per behaviour. Offline (P-074, R4).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "testing"))

import doc_advisory as advisory  # noqa: E402

_spec = importlib.util.spec_from_file_location("generate_docs", REPO / "scripts" / "testing" / "generate_docs.py")
generation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generation)

JUDGEMENT = {"DM-STATUS", "DM-MODEL", "DM-ACCEPTANCE", "DM-VERIFY", "DM-DEVIATION"}


def _ids(rules: list[dict]) -> set[str]:
    return {rule["id"].strip("`") for rule in rules}


# ── glob semantics ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("glob, path, expected", [
    ("modules/*/README.md", "modules/a/README.md", True),
    ("modules/*/README.md", "modules/a/b/README.md", False),
    ("modules/**/workflows/*.json", "modules/a/workflows/x.json", True),
    ("modules/**/workflows/*.json", "modules/a/b/workflows/x.json", True),
    ("modules/**/workflows/*.json", "modules/workflows/x.json", True),
    ("modules/**/workflows/*.json", "modules/a/workflows/sub/x.json", False),
    ("docs/**/*.md", "docs/a.md", True),
    ("docs/**/*.md", "docs/x/y.md", True),
    ("docs/**/*.md", "docs/x/y.txt", False),
    ("design-system/**", "design-system/a.md", True),
    ("design-system/**", "design-system/x/y.yaml", True),
    ("design-system/**", "other/design-system/a.md", False),
    ("CLAUDE.md", "CLAUDE.md", True),
    ("CLAUDE.md", "docs/CLAUDE.md", False),
    ("a?c.md", "abc.md", True),
    ("a?c.md", "a/c.md", False),
    ("docker-compose.yml", "docker-composexyml", False),
])
def test_glob_semantics(glob, path, expected):
    assert bool(advisory.glob_regex(glob).match(path)) is expected


def test_prefixes_restrict_by_change_kind_and_exclusions_win():
    changed = [("A", "docs/new.md"), ("M", "docs/old.md"), ("D", "docs/gone.md"), ("A", "docs/proposals/PROPOSAL_X.md")]
    assert advisory.rule_matches(["+docs/**/*.md", "!docs/proposals/**"], changed) == ["docs/new.md"]
    assert advisory.rule_matches(["-docs/**/*.md"], changed) == ["docs/gone.md"]
    assert advisory.rule_matches(["docs/**/*.md"], changed) == [
        "docs/gone.md", "docs/new.md", "docs/old.md", "docs/proposals/PROPOSAL_X.md"]
    assert advisory.rule_matches([], changed) == []


# ── the real registry ─────────────────────────────────────────────────────────────────────────

def test_the_real_registry_maps_every_rule_but_the_judgement_ones():
    rules = advisory.load_rules(REPO)
    assert {rule["id"].strip("`") for rule in rules if not rule["paths"]} == JUDGEMENT
    for rule in rules:
        parsed = [advisory.parse_pattern(pattern) for pattern in rule["paths"]]
        assert not rule["paths"] or any(p.include for p in parsed), f"{rule['id']} has no include pattern"


def test_the_matrix_names_the_rules_that_never_fire_in_the_advisory():
    text = (REPO / "docs" / "agent" / "DOC-UPDATE-MATRIX.md").read_text(encoding="utf-8")
    section = text.split("## Path triggers", 1)[1].split("\n## ", 1)[0]
    for rule in JUDGEMENT:
        assert f"`{rule}`" in section.split("| Rule | Paths |")[0], f"{rule} is not named as a judgement rule"


# ── the generator's side ──────────────────────────────────────────────────────────────────────

KNOWN = {"DM-ONE", "DM-TWO"}


def _table(*rows: str) -> str:
    return "\n## Path triggers\n\n| Rule | Paths |\n|---|---|\n" + "\n".join(rows) + "\n"


def test_path_triggers_are_read_by_rule_id():
    source = "intro\n" + _table("| `DM-ONE` | `a/**`<br>`!a/skip/**` |", "| `DM-TWO` | `+b.md` |")
    assert generation.path_triggers(source, KNOWN) == {"DM-ONE": ["a/**", "!a/skip/**"], "DM-TWO": ["+b.md"]}


def test_no_table_means_no_triggers():
    assert generation.path_triggers("| `DM-ONE` | x | y | z |", KNOWN) == {}


@pytest.mark.parametrize("rows", [
    ["| `DM-NOPE` | `a` |"],                       # unknown rule
    ["| `DM-ONE` | `a` |", "| `DM-ONE` | `b` |"],   # repeated rule
    ["| `DM-ONE` | nothing in backticks |"],        # no pattern
    ["| `DM-ONE` | `!a` |"],                        # exclude only
])
def test_a_malformed_trigger_row_is_an_error(rows):
    with pytest.raises(ValueError):
        generation.path_triggers(_table(*rows), KNOWN)


def test_a_removal_pattern_counts_as_an_include():
    assert generation.path_triggers(_table("| `DM-ONE` | `-a`<br>`!b` |"), KNOWN) == {"DM-ONE": ["-a", "!b"]}


def test_the_second_table_is_not_mistaken_for_a_rule():
    rows = "\n".join(f"| `DM-R{chr(65 + i)}` | t | r | w |" for i in range(10))
    source = rows + "\n\n" + _table("| `DM-RB` | `a` |")
    assert len(generation.update_rules(source)) == 10


# ── synthetic repositories ────────────────────────────────────────────────────────────────────

RULES = [
    {"id": "`DM-CONTEXT`", "trigger": "change to `CLAUDE.md`", "references": "regenerate `AGENTS.md`", "rationale": "x",
     "paths": ["CLAUDE.md"]},
    {"id": "`DM-DOCS-INDEX`", "trigger": "a **new file** under `docs/`", "references": "`docs/README.md`<br>second", "rationale": "x",
     "paths": ["+docs/**/*.md", "!docs/proposals/**"]},
    {"id": "`DM-PROPOSAL-OPEN`", "trigger": "a proposal is **added**", "references": "`docs/todo/README.md`", "rationale": "x",
     "paths": ["+docs/proposals/PROPOSAL_*.md"]},
    {"id": "`DM-WORKFLOW`", "trigger": "a workflow json added or removed", "references": "the README", "rationale": "x",
     "paths": ["+modules/**/workflows/*.json", "-modules/**/workflows/*.json"]},
    {"id": "`DM-STATUS`", "trigger": "a judgement", "references": "somewhere", "rationale": "x", "paths": []},
]


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=root, check=True,
                   capture_output=True)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "docs" / "agent-registries").mkdir(parents=True)
    (tmp_path / "docs" / "agent-registries" / "documentation.json").write_text(
        json.dumps({"documentation_update_rules": RULES}), encoding="utf-8")
    for rel in ("CLAUDE.md", "docs/README.md", "modules/a/workflows/old.json"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("base\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "checkout", "-q", "-b", "feature")
    return tmp_path


def _fired(root: Path) -> dict[str, list[str]]:
    return {item["rule"]: item["files"] for item in advisory.advise(root, "main")["fired"]}


def test_an_unchanged_tree_fires_nothing(repo):
    assert _fired(repo) == {}
    assert advisory.main(["--root", str(repo), "--base", "main"]) == 0


def test_a_changed_instruction_file_fires_its_rule(repo):
    (repo / "CLAUDE.md").write_text("changed\n", encoding="utf-8")
    assert _fired(repo) == {"DM-CONTEXT": ["CLAUDE.md"]}


def test_committed_and_untracked_changes_both_count(repo):
    (repo / "CLAUDE.md").write_text("changed\n", encoding="utf-8")
    _git(repo, "commit", "-qam", "edit")
    (repo / "docs" / "new.md").write_text("new\n", encoding="utf-8")        # untracked
    assert _fired(repo) == {"DM-CONTEXT": ["CLAUDE.md"], "DM-DOCS-INDEX": ["docs/new.md"]}


def test_a_new_proposal_fires_the_proposal_rule_but_not_the_docs_index_rule(repo):
    (repo / "docs" / "proposals").mkdir()
    (repo / "docs" / "proposals" / "PROPOSAL_X.md").write_text("p\n", encoding="utf-8")
    assert _fired(repo) == {"DM-PROPOSAL-OPEN": ["docs/proposals/PROPOSAL_X.md"]}


def test_an_edited_existing_doc_does_not_fire_the_new_file_rule(repo):
    (repo / "docs" / "README.md").write_text("edited\n", encoding="utf-8")
    assert _fired(repo) == {}


def test_a_workflow_added_or_removed_fires_but_one_edited_does_not(repo):
    (repo / "modules" / "a" / "workflows" / "old.json").write_text("edited\n", encoding="utf-8")
    assert "DM-WORKFLOW" not in _fired(repo)
    (repo / "modules" / "a" / "workflows" / "old.json").unlink()
    assert _fired(repo) == {"DM-WORKFLOW": ["modules/a/workflows/old.json"]}


def test_a_judgement_rule_never_fires_and_is_named_in_the_output(repo):
    (repo / "CLAUDE.md").write_text("changed\n", encoding="utf-8")
    result = advisory.advise(repo, "main")
    assert "DM-STATUS" in result["never_fires_here"] and "DM-STATUS" not in {i["rule"] for i in result["fired"]}
    assert "DM-STATUS" in advisory.render(result)


def test_text_and_json_output(repo, capsys):
    (repo / "CLAUDE.md").write_text("changed\n", encoding="utf-8")
    assert advisory.main(["--root", str(repo), "--base", "main"]) == 0
    text = capsys.readouterr().out
    assert "DM-CONTEXT" in text and "because of: CLAUDE.md" in text and "Advisory only" in text
    assert advisory.main(["--root", str(repo), "--base", "main", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["fired"][0]["rule"] == "DM-CONTEXT" and data["base"] == "main"


def test_it_always_exits_zero_when_it_runs_even_if_rules_fired(repo):
    (repo / "CLAUDE.md").write_text("changed\n", encoding="utf-8")
    assert advisory.main(["--root", str(repo), "--base", "main"]) == 0


def test_an_unknown_base_is_an_error_not_an_empty_answer(repo, capsys):
    assert advisory.main(["--root", str(repo), "--base", "no-such-ref"]) == 2
    assert "base ref not found" in capsys.readouterr().err


def test_outside_a_git_checkout_it_fails_loudly(tmp_path, capsys):
    assert advisory.main(["--root", str(tmp_path)]) == 2
    assert capsys.readouterr().err.strip()


def test_a_missing_registry_is_an_error(repo, capsys):
    (repo / "docs" / "agent-registries" / "documentation.json").unlink()
    assert advisory.main(["--root", str(repo), "--base", "main"]) == 2
    assert "generate_docs.py --write" in capsys.readouterr().err


def test_rule_ids_in_the_output_carry_no_backticks(repo):
    (repo / "CLAUDE.md").write_text("changed\n", encoding="utf-8")
    lines = advisory.render(advisory.advise(repo, "main")).splitlines()
    assert any(line.startswith("DM-CONTEXT — ") for line in lines)
