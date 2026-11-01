"""MARKETING.md is a crosswalk artifact: what it repeats is checked against the registry.

The playbook deliberately repeats registry data (ICPs, the persona chain, the shipped list, the
engine order) because a human-readable plan is missing without it. Duplication is only safe when it
is verified, so these tests fail the moment either side drifts. The YAML and configs always win.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = ROOT / "modules/marketing-crosswalk/crosswalk"
PLAYBOOK = ROOT / "MARKETING.md"
PRODUCT_MODULES = ("stream-extend", "content-extend")


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def _registry() -> dict:
    return {row["module"]: row for row in _yaml(CROSSWALK / "modules.yml")["modules"]}


def _subjects(module: str) -> dict:
    return _yaml(CROSSWALK / "subjects" / f"{module}.yml")


def _sections(text: str) -> list[tuple[str, str, str]]:
    """(number, heading line, body) for every numbered ## / ### section."""
    found = list(re.finditer(r"(?m)^#{2,3} (\d+[a-z]?)\. .*$", text))
    return [
        (m.group(1), m.group(0), text[m.end(): found[i + 1].start() if i + 1 < len(found) else len(text)])
        for i, m in enumerate(found)
    ]


def _section(text: str, number: str) -> str:
    return next(body for n, _, body in _sections(text) if n == number)


def _table_rows(body: str, columns: int) -> list[list[str]]:
    rows = []
    for line in body.splitlines():
        if line.startswith("|") and not set(line) <= set("|-: "):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == columns:
                rows.append(cells)
    return rows


@pytest.fixture(scope="module")
def text() -> str:
    return PLAYBOOK.read_text(encoding="utf-8")


def test_numbered_headings_are_exactly_the_registered_anchors(text):
    """`validate` checks each registered anchor exists; this also forbids an unregistered section."""
    doc = _yaml(CROSSWALK / "targets.yml")["targets"]["hybrid-creator-platform"]["docs"]["marketing_playbook"]
    assert doc["path"] == "MARKETING.md"
    assert list(doc["anchors"].values()) == [heading for _, heading, _ in _sections(text)]


def test_product_rows_and_subjects_point_at_the_playbook():
    registry = _registry()
    for module in PRODUCT_MODULES:
        row = registry[module]
        assert row["files"]["marketing_doc"] == "MARKETING.md"
        assert "marketing playbook" in row["discovery_keywords"]
        assert _subjects(module)["discovery"]["files"]["marketing_doc"] == "MARKETING.md"
    assert PLAYBOOK.is_file()


def test_every_numbered_section_names_registered_modules(text):
    registry = set(_registry())
    for number, _, body in _sections(text):
        match = re.search(r"(?ms)^\*\*Registry:\*\*(.*?)(?:\n\s*\n|\Z)", body)
        assert match, f"§{number} has no **Registry:** paragraph"
        paragraph = match.group(1)
        assert set(re.findall(r"`([a-z][a-z-]*)`", paragraph)) & registry, f"§{number} names no registered module"
        for link in re.findall(r"\]\(([^)]*subjects/[a-z-]+\.yml)\)", paragraph):
            assert (ROOT / link).is_file(), f"§{number} links to a missing subjects file: {link}"


def test_shipped_list_matches_subjects(text):
    claimed = set(re.findall(r"`([a-z-]+)`", re.search(r"\*\*Shipped subjects \(checked by tests\):\*\* (.+)", text).group(1)))
    actual = {s["id"] for m in PRODUCT_MODULES for s in _subjects(m)["subjects"] if s["status"] == "shipped"}
    assert claimed == actual


def test_icp_tables_match_subjects(text):
    parts = re.split(r"\n\*\*(Stream Extend|Creator Extend)\*\*\n", _section(text, "2"))
    tables = dict(zip(parts[1::2], parts[2::2]))
    for module, label in (("stream-extend", "Stream Extend"), ("content-extend", "Creator Extend")):
        rows = [r for r in _table_rows(tables[label], 5) if r[0].isdigit()]
        expected = sorted(_subjects(module)["icps"].items(), key=lambda kv: kv[1]["rank"])
        assert [r[1].strip("`") for r in rows] == [key for key, _ in expected], module
        for row, (key, icp) in zip(rows, expected):
            assert row[0] == str(icp["rank"]), (module, key)
            assert _norm(row[2]) == _norm(icp["who"]), (module, key)
            assert _norm(row[3]) == _norm(icp["why_they_switch"]), (module, key)
            assert _norm(row[4]) == _norm(icp["where"]), (module, key)


def test_persona_chain_matches_stream_programming(text):
    program = _yaml(ROOT / "configs/local/stream-programming.yaml")
    profiles = {p["id"]: p for p in program["profiles"]}
    shows = {s["id"]: s for s in program["shows"]}
    rows = [r for r in _table_rows(_section(text, "3g"), 5) if r[0].strip("`") in PRODUCT_MODULES]
    assert {r[0].strip("`") for r in rows} == set(PRODUCT_MODULES)
    for module, profile_id, persona, show_id, policy in (tuple(c.strip("`") for c in r) for r in rows):
        profile, show = profiles[profile_id], shows[show_id]
        assert profile["kind"] == "marketing" and profile["marketing_module_id"] == module
        assert profile["persona_id"] == persona and profile["audio_policy"] == policy
        assert show["profile_id"] == profile_id and show["persona_id"] == persona
        # §3g says nothing runs on its own: uploads stay off and approval stays on.
        assert profile["youtube"]["upload_enabled"] is False
        assert profile["youtube"]["approval_required"] is True


def test_engine_order_and_claim_levels_match_the_asset_catalogue(text):
    catalogue = _yaml(CROSSWALK / "assets.yml")
    body = _section(text, "4")
    order = re.findall(r"`([a-z-]+)`", re.search(r"\*\*Engine order:\*\* (.+)", body).group(1))
    assert order == catalogue["engine_order"]
    rows = [r for r in _table_rows(body, 5) if r[0].isdigit()]
    assert [r[1].strip("`") for r in rows] == catalogue["engine_order"]
    for _, asset, level, *_ in rows:
        assert level == catalogue["assets"][asset.strip("`")]["claim_level"], asset
    beyond = re.search(r"(?s)Beyond the five:(.*?)\.(?:\s|$)", body).group(1)  # the first sentence only
    for asset in re.findall(r"`([a-z-]+)`", beyond):
        assert asset in catalogue["assets"], asset
