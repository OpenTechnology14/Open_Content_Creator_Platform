"""Generated policy/data must drift-fail, preserve restrictions and stay within the checkout."""

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/testing"))
spec = importlib.util.spec_from_file_location("generate_docs", ROOT / "scripts/testing/generate_docs.py")
generation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generation)


def fixture_root(tmp_path):
    relative_paths = ["CLAUDE.md", "docs/PROPOSALS.md", "docs/todo/README.md", "docs/PROJECT_CROSSWALK.md", "docs/agent/DOC-UPDATE-MATRIX.md"]
    relative_paths.extend(str(path.relative_to(ROOT)) for path in (ROOT / "modules").glob("*/README.md"))
    relative_paths.extend(str(path.relative_to(ROOT)) for path in (ROOT / "modules").glob("*/setup/*.md"))
    for relative in relative_paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((ROOT / relative).read_text())
    return tmp_path


def test_generated_crosswalk_only_claims_explicit_references(tmp_path):
    root = fixture_root(tmp_path)
    readme = root / "modules/storage-data/README.md"
    readme.write_text(readme.read_text() + "\nVerified reference: P-001.\n")
    generation.synchronize(root, True)
    crosswalk = (root / "docs/PROJECT_CROSSWALK.md").read_text()
    generated = crosswalk.split(generation.REFERENCE_START, 1)[1]
    assert "Explicit references" in generated
    assert "[P-001](PROPOSALS.md)" in generated
    assert generation.synchronize(root, False) == []


def test_current_generated_files_match_canonical_sources():
    assert generation.synchronize(ROOT, False) == [], "run generate_docs.py --write and inspect the diff"


def test_hand_edit_of_any_policy_section_is_detected(tmp_path):
    root = fixture_root(tmp_path)
    generation.synchronize(root, True)
    agent = root / "AGENTS.md"
    agent.write_text(agent.read_text().replace("Do **not** expose any service", "Expose any service"))
    assert "AGENTS.md" in generation.synchronize(root, False)
    # Check mode must preserve the hand-edited file for review, not silently repair it.
    assert "Expose any service" in agent.read_text()


def test_changed_queue_or_rule_source_invalidates_registry(tmp_path):
    root = fixture_root(tmp_path)
    generation.synchronize(root, True)
    queue = root / "docs/PROPOSALS.md"
    queue.write_text(queue.read_text() + "\nA reviewed new note.\n")
    assert "docs/agent-registries/documentation.json" in generation.synchronize(root, False)


def test_claude_review_role_survives_codex_identity_conversion():
    source = (ROOT / "CLAUDE.md").read_text()
    result = generation.agent_text(source)
    assert "This file gives Codex (" in result
    assert "HF/OpenCode drafts, Claude reviews" in result
    assert "**No fix-until-green.**" in result
    assert "A wrong capability is a security defect" in result


def test_generation_is_deterministic(tmp_path):
    root = fixture_root(tmp_path)
    first = generation.outputs(root)
    assert first == generation.outputs(root)
    generation.synchronize(root, True)
    assert generation.synchronize(root, False) == []


def test_generated_target_symlink_cannot_escape_checkout(tmp_path):
    root = fixture_root(tmp_path / "repo")
    outside = tmp_path / "outside.md"
    outside.write_text("keep this file")
    (root / "AGENTS.md").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        generation.synchronize(root, True)
    assert outside.read_text() == "keep this file"


def test_missing_module_and_rule_inventories_are_not_clean_snapshots():
    with pytest.raises(ValueError, match="tripwire"):
        generation.update_rules("| `DM-ONE` | x | y | z |")
    with pytest.raises(ValueError, match="tripwire"):
        generation.module_statuses("## 11. Module Status\n| one | Content | scaffolded |\n## 12. Quick Reference")
