"""Offline tests for status_evidence.target (P-064): a subject's status can be verified against
a different repo than the one its content is delivered to. Local temp dirs only."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "modules" / "marketing-crosswalk"))

from generator.crosswalk import Crosswalk, validate  # noqa: E402
from generator.status import StatusError  # noqa: E402


def _crosswalk(tmp_path: Path, evidence: dict) -> Crosswalk:
    blog, src = tmp_path / "blog", tmp_path / "src"
    for root in (blog, src):
        root.mkdir()
    (src / "syllabus.md").write_text("| 1 | Model usage | Outlined |\n", encoding="utf-8")
    subject = {
        "id": "lesson", "name": "Lesson", "status": "scaffolded",
        "status_evidence": evidence, "icps": [], "channels": [], "assets": [],
    }
    return Crosswalk(
        root=REPO, module_root=REPO / "modules" / "marketing-crosswalk",
        targets={"blog": {"docs": {}}, "src": {"docs": {}}}, products={},
        icps={"m": {}}, channels={"m": {}}, assets={}, engine_order=[],
        modules=[{"module": "m", "target": "blog", "subjects": "subjects/m.yml"}],
        subjects={"m": [subject]}, module_meta={"m": {}},
        target_paths={"blog": blog, "src": src},
    )


def test_evidence_is_read_from_the_named_target_not_the_delivery_target(tmp_path):
    cw = _crosswalk(tmp_path, {"target": "src", "file": "syllabus.md",
                               "contains": "| 1 | Model usage | Outlined |"})
    assert cw.evidence_root("m", cw.subjects["m"][0]) == tmp_path / "src"
    assert not [f for f in validate(cw) if "lesson" in f.where]


def test_evidence_without_target_still_uses_the_module_target(tmp_path):
    cw = _crosswalk(tmp_path, {"file": "syllabus.md", "contains": "Outlined"})
    assert cw.evidence_root("m", cw.subjects["m"][0]) == tmp_path / "blog"
    assert any("evidence file does not exist" in f.problem for f in validate(cw))


def test_drift_in_the_named_target_fails_validation(tmp_path):
    cw = _crosswalk(tmp_path, {"target": "src", "file": "syllabus.md", "contains": "| Aired |"})
    assert any("no longer present" in f.problem for f in validate(cw))


def test_unknown_evidence_target_is_an_error_not_a_silent_fallback(tmp_path):
    cw = _crosswalk(tmp_path, {"target": "nope", "file": "syllabus.md", "contains": "x"})
    with pytest.raises(StatusError):
        cw.evidence_root("m", cw.subjects["m"][0])
    assert any("nope" in f.problem for f in validate(cw))
