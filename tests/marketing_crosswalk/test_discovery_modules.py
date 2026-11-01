"""Discovery-only registry rows (myfeed, ironfall, animalhouse, gist and the design-system hub).

These rows exist so a session can FIND a project, not so the platform can market it. Three things
must stay true, and each is enforced here rather than left to review:

* nothing generates for them (`subjects: []`), and a `visibility: private` row refuses outright;
* **no private row ships**: the published registry holds none (the release checklist's privacy item);
* the row, its subjects-file mirror and its `status` agree with the counts that justify them.

Offline: the real registry is parsed from disk, the loader rules run on synthetic crosswalks.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
MODULE_ROOT = REPO / "modules" / "marketing-crosswalk"
CROSSWALK = MODULE_ROOT / "crosswalk"
sys.path.insert(0, str(MODULE_ROOT))

from generator import cli  # noqa: E402
from generator.crosswalk import Crosswalk, _validate_visibility, load, validate  # noqa: E402

PUBLIC = ("myfeed", "ironfall", "animalhouse", "gist")
DISCOVERY = PUBLIC               # project rows: a project that is not part of this platform
HUB = ("design-system",)          # a folder of this repository; status is review state, not the project-count rule
ROWS = DISCOVERY + HUB
MIRRORED = ("status", "last_verified", "notes", "discovery_keywords",
            "not_to_be_confused_with", "counts", "files")
MIN_DOCS = 10  # the "maintained docs" bar for `drafted`; schema.md § Discovery-only modules


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _rows() -> dict[str, dict]:
    return {r["module"]: r for r in _yaml(CROSSWALK / "modules.yml")["modules"]}


def _subjects(module: str) -> dict:
    return _yaml(CROSSWALK / "subjects" / f"{module}.yml")


def _expected_status(counts: dict) -> str:
    code, docs = counts["code_files"], counts["doc_files"]
    if code > 0 and docs >= MIN_DOCS:
        return "drafted"
    return "outlined" if code > 0 or docs > 0 else "planned"


# ── shape of the five rows ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ROWS)
def test_row_is_a_complete_discovery_only_record(name):
    row = _rows()[name]
    for key in ("kind", "target", "subjects", "description", "onboarded", "status",
                "last_verified", "notes", "discovery_keywords", "not_to_be_confused_with",
                "counts", "files"):
        assert row.get(key), f"{name}: row is missing {key}"
    assert row["counts"]["subjects"] == 0 and _subjects(name)["subjects"] == [], \
        "a discovery-only module must not generate anything"
    assert isinstance(row["counts"]["basis"], str) and "2026-" in row["counts"]["basis"], \
        "counts must say what was counted, where and when"
    promotion = _subjects(name)["promotion"]
    assert promotion["blocked_on"] and isinstance(promotion["steps"], list)
    assert _subjects(name)["product"] == "none"


@pytest.mark.parametrize("name", ROWS)
def test_subjects_file_mirrors_the_row(name):
    """The row is canonical; the subjects-file copy exists for the person who opens that file."""
    row, mirror = _rows()[name], _subjects(name)["discovery"]
    assert {k: mirror[k] for k in MIRRORED} == {k: row[k] for k in MIRRORED}


@pytest.mark.parametrize("name", DISCOVERY)
def test_status_follows_the_counts_not_a_hunch(name):
    row = _rows()[name]
    assert row["status"] == _expected_status(row["counts"]), \
        f"{name}: status {row['status']!r} disagrees with counts {row['counts']}"


@pytest.mark.parametrize("name", ROWS)
def test_dates_are_real_and_ordered(name):
    row = _rows()[name]
    onboarded, verified = row["onboarded"], row["last_verified"]
    assert isinstance(onboarded, datetime.date) and isinstance(verified, datetime.date)
    assert onboarded <= verified <= datetime.date.today()


def test_status_rule_edges():
    assert _expected_status({"code_files": 5, "doc_files": 10}) == "drafted"
    assert _expected_status({"code_files": 5, "doc_files": 9}) == "outlined"
    assert _expected_status({"code_files": 0, "doc_files": 40}) == "outlined"
    assert _expected_status({"code_files": 0, "doc_files": 4}) == "outlined"
    assert _expected_status({"code_files": 0, "doc_files": 0}) == "planned"


# ── keywords are greppable and collisions are disambiguated ───────────────────────────────────

VARIANTS = {
    "myfeed": {"myfeed", "my feed", "my-feed"},
    "ironfall": {"ironfall", "iron fall", "iron-fall"},
    "animalhouse": {"animalhouse", "animal house", "animal-house"},
    "gist": {"gist", "gist app", "gist-app"},
    "design-system": {"design-system", "design system", "designsystem"},
}


@pytest.mark.parametrize("name", ROWS)
def test_keywords_cover_the_spellings_a_person_would_type(name):
    keywords = [str(k).strip().lower() for k in _rows()[name]["discovery_keywords"]]
    assert VARIANTS[name] <= set(keywords)
    assert len(keywords) == len(set(keywords)), "duplicate keyword"


@pytest.mark.parametrize("name", ROWS)
def test_a_keyword_shared_with_another_module_is_disambiguated(name):
    """A grep that hits two modules must tell the reader which is which (the 'AI' misroutes)."""
    rows = _rows()
    mine = {str(k).strip().lower() for k in rows[name]["discovery_keywords"]}
    confusables = " ".join(rows[name]["not_to_be_confused_with"]).lower()
    for other, row in rows.items():
        if other == name:
            continue
        theirs = {str(k).strip().lower() for k in row.get("discovery_keywords") or []}
        overlap = {m for m in mine for t in theirs if m == t or (len(min(m, t, key=len)) > 4 and (m in t or t in m))}
        if overlap:
            assert other.lower() in confusables, \
                f"{name} shares {sorted(overlap)[:3]} with {other} but never says how they differ"


# ── private rows ──────────────────────────────────────────────────────────────────────────────


def test_no_private_row_ships():
    """A private row is for a local, uncommitted registry. The published one holds none."""
    rows = _rows()
    assert [n for n, r in rows.items() if r.get("visibility") == "private"] == []
    assert [n for n, r in rows.items() if r.get("kind") == "internal-tool"] == []
    targets = _yaml(CROSSWALK / "targets.yml")["targets"]
    assert [k for k, t in targets.items() if t.get("visibility") == "private"] == []


def test_the_real_registry_has_no_visibility_findings():
    assert _validate_visibility(load(MODULE_ROOT, REPO)) == []


# ── loader rules, on synthetic crosswalks ─────────────────────────────────────────────────────

PUB_TARGET = {"repo": "o/pub", "path_env": "PUB_PATH", "default_path": "../pub", "docs": {}}
PRIV_TARGET = {"repo": "none", "path_env": "PRIV_PATH", "default_path": "../priv", "docs": {},
               "visibility": "private", "optional": True}


def _cw(tmp_path, modules, targets, subjects=None, meta=None, present=("pub",)):
    for key in present:
        (tmp_path / key).mkdir(exist_ok=True)
    names = [m["module"] for m in modules]
    return Crosswalk(
        root=REPO, module_root=MODULE_ROOT, targets=targets, products={},
        icps={n: {} for n in names}, channels={n: {} for n in names}, assets={}, engine_order=[],
        modules=modules,
        subjects={n: (subjects or {}).get(n, []) for n in names},
        module_meta={n: (meta or {}).get(n, {}) for n in names},
        target_paths={k: tmp_path / k for k in targets},
    )


def _pub(name="pub_mod", **extra):
    return {"module": name, "target": "pub", "subjects": f"subjects/{name}.yml", **extra}


def _priv(name="secret_tool", **extra):
    return {"module": name, "target": "priv", "visibility": "private",
            "subjects": f"subjects/{name}.yml", **extra}


def _problems(cw):
    return [f.problem for f in validate(cw)]


def test_an_absent_optional_target_is_not_an_error(tmp_path):
    cw = _cw(tmp_path, [_pub(), _priv()], {"pub": PUB_TARGET, "priv": PRIV_TARGET})
    assert _problems(cw) == []


def test_an_absent_required_target_is_still_an_error(tmp_path):
    cw = _cw(tmp_path, [_pub()], {"pub": PUB_TARGET}, present=())
    assert any("target repository not found" in p for p in _problems(cw))


def test_optional_does_not_excuse_declared_docs(tmp_path):
    """`optional` only skips a checkout that is absent; it never weakens a present one."""
    target = {**PUB_TARGET, "optional": True, "docs": {"d": {"path": "NOPE.md", "anchors": {}}}}
    cw = _cw(tmp_path, [_pub()], {"pub": target})
    assert any("NOPE.md" in f.where + f.problem for f in validate(cw))


def test_a_private_module_must_use_a_private_target(tmp_path):
    cw = _cw(tmp_path, [_priv(target="pub")], {"pub": PUB_TARGET})
    assert any("not `visibility: private`" in p for p in _problems(cw))


def test_a_public_module_must_not_use_a_private_target(tmp_path):
    cw = _cw(tmp_path, [_pub(target="priv")], {"priv": PRIV_TARGET}, present=())
    assert any("public module targets a private target" in p for p in _problems(cw))


def test_a_private_module_cannot_declare_subjects(tmp_path):
    cw = _cw(tmp_path, [_priv()], {"priv": PRIV_TARGET}, present=(),
             subjects={"secret_tool": [{"id": "s", "name": "S"}]})
    assert any("could generate content" in p for p in _problems(cw))


@pytest.mark.parametrize("where", ["entry", "subjects", "meta"])
def test_a_public_module_naming_a_private_id_is_an_error(tmp_path, where):
    entry = _pub(notes="see secret_tool for the real thing" if where == "entry" else "ok")
    subjects = {"pub_mod": [{"id": "s", "name": "uses Secret_Tool"}]} if where == "subjects" else None
    meta = {"pub_mod": {"discovery": {"notes": "via secret_tool"}}} if where == "meta" else None
    cw = _cw(tmp_path, [entry, _priv()], {"pub": PUB_TARGET, "priv": PRIV_TARGET},
             subjects=subjects, meta=meta)
    assert any("private module id 'secret_tool'" in p for p in _problems(cw))


def test_private_rows_may_name_each_other_and_public_modules(tmp_path):
    rows = [_pub(), _priv(notes="sibling of other_tool; not pub_mod"), _priv("other_tool", notes="not secret_tool")]
    assert _problems(_cw(tmp_path, rows, {"pub": PUB_TARGET, "priv": PRIV_TARGET})) == []


def test_a_topic_shared_with_a_private_module_is_not_a_leak(tmp_path):
    """Only ids are matched: public subjects may legitimately share a private module's topic."""
    subjects = {"pub_mod": [{"id": "secret", "name": "Secret Tool — a public template",
                             "status_evidence": {"file": "templates/secret-tool/README.md"}}]}
    cw = _cw(tmp_path, [_pub(), _priv()], {"pub": PUB_TARGET, "priv": PRIV_TARGET}, subjects=subjects)
    assert _validate_visibility(cw) == []


# ── the CLI refuses before it does anything ───────────────────────────────────────────────────


def test_generate_refuses_a_private_module_before_validating(tmp_path, monkeypatch):
    """Exit 2 (not the 1 that validation against an absent target would give) proves the ordering."""
    cw = _cw(tmp_path, [_pub(), _priv()], {"pub": PUB_TARGET, "priv": PRIV_TARGET}, present=())
    monkeypatch.setattr(cli, "_load", lambda args: cw)
    out = tmp_path / "out"
    assert cli.main(["generate", "--module", "secret_tool", "--out", str(out)]) == 2 and not out.exists()


def test_schema_documents_every_key_this_adds():
    text = (CROSSWALK / "schema.md").read_text(encoding="utf-8")
    for needle in ("Discovery-only modules", "`visibility: private`", "`optional`", "`promotion`",
                   "design-system-hub", "`consumers`"):
        assert needle in text, f"schema.md does not document {needle}"
