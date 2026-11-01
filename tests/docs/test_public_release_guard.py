"""The public-release guard holds the hygiene the release checklist asks for, on the real tree and on
synthetic repositories that each break exactly one rule.

Offline. The synthetic repositories are created with `git init` under tmp_path and never committed to.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "testing"))

import public_release_guard as guard  # noqa: E402

MIT = "MIT License\n\nCopyright (c) 2026 Example\n\nPermission is hereby granted, free of charge\n"
REGISTRY = "modules/marketing-crosswalk/crosswalk/modules.yml"
TARGETS = "modules/marketing-crosswalk/crosswalk/targets.yml"
# Built from parts so this file never contains a personal path or an unresolved marker itself.
HOME = "/" + "Users" + "/" + "jdoe" + "/project"
MARKER = "[" + "OWNER" + "-SET: choose a contact]"


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for rel, body in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def _kinds(findings) -> set[str]:
    return {f.kind for f in findings}


def test_the_real_repository_passes_every_hygiene_check():
    failures, _pending = guard.run(REPO)
    assert failures == [], "\n".join(f.render() for f in failures)


def test_a_clean_repository_is_ok(tmp_path):
    root = _repo(tmp_path, {"LICENSE": MIT, "README.md": "hello\n", ".env.example": "A=b\n"})
    assert guard.run(root) == ([], [])
    assert guard.main(["--root", str(root)]) == 0


@pytest.mark.parametrize("rel, body", [
    (REGISTRY, "modules:\n  - module: x\n    visibility: private\n"),
    (REGISTRY, "modules:\n  - module: x\n    kind: internal-tool\n"),
    (TARGETS, "targets:\n  t:\n    visibility: private\n"),
])
def test_a_private_row_or_target_is_a_failure(tmp_path, rel, body):
    root = _repo(tmp_path, {"LICENSE": MIT, rel: body})
    assert _kinds(guard.run(root)[0]) == {"private-row"}


def test_a_commented_or_subject_level_flag_is_not_a_private_row(tmp_path):
    root = _repo(tmp_path, {
        "LICENSE": MIT,
        REGISTRY: "modules:\n  # visibility: private\n  - module: x\n",
        "modules/marketing-crosswalk/crosswalk/subjects/x.yml": "subjects:\n  - id: a\n    visibility: private\n",
    })
    assert guard.run(root)[0] == []


def test_a_personal_home_path_is_a_failure_and_generic_ones_are_not(tmp_path):
    root = _repo(tmp_path, {"LICENSE": MIT, "docs/a.md": f"see {HOME}/x\n", "docs/b.md": "/home/node/.n8n and /Users/you/x\n"})
    failures = guard.run(root)[0]
    assert [(f.kind, f.path, f.line) for f in failures] == [("home-path", "docs/a.md", 1)]
    assert "jdoe" not in failures[0].render(), "a finding must not repeat the account name"


def test_a_windows_home_path_is_a_failure(tmp_path):
    root = _repo(tmp_path, {"LICENSE": MIT, "docs/a.md": "C:\\" + "Users" + "\\jdoe\\x\n"})
    assert _kinds(guard.run(root)[0]) == {"home-path"}


def test_a_missing_root_license_is_a_failure(tmp_path):
    root = _repo(tmp_path, {"README.md": "x\n"})
    assert _kinds(guard.run(root)[0]) == {"license"}


def test_an_unrecognised_root_license_is_a_failure(tmp_path):
    root = _repo(tmp_path, {"LICENSE": "Some custom terms\n"})
    assert _kinds(guard.run(root)[0]) == {"license"}


@pytest.mark.parametrize("rel, body", [
    ("apps/x/src-tauri/Cargo.toml", '[package]\nname = "x"\nlicense = "BSL-1.1"\n'),
    ("apps/x/package.json", '{"name": "x", "license": "Apache-2.0"}\n'),
])
def test_a_manifest_that_disagrees_with_the_root_license_is_a_failure(tmp_path, rel, body):
    root = _repo(tmp_path, {"LICENSE": MIT, rel: body})
    failures = guard.run(root)[0]
    assert _kinds(failures) == {"license"} and failures[0].path == rel


def test_manifests_that_agree_or_declare_nothing_pass(tmp_path):
    root = _repo(tmp_path, {
        "LICENSE": MIT,
        "a/Cargo.toml": '[package]\nname = "a"\nlicense = "MIT"\n',
        "b/Cargo.toml": '[package]\nname = "b"\n',
        "c/package.json": '{"name": "c", "license": "MIT"}\n',
        "d/package.json": '{"name": "d"}\n',
    })
    assert guard.run(root)[0] == []


@pytest.mark.parametrize("name", [".env", ".env.local", "secrets/server.pem", "deploy/id_rsa", "tls/site.key"])
def test_a_tracked_environment_or_key_file_is_a_failure(tmp_path, name):
    root = _repo(tmp_path, {"LICENSE": MIT, name: "x\n"})
    assert _kinds(guard.run(root)[0]) == {"secret-file"}


def test_owner_set_is_pending_by_default_and_fails_in_release_mode(tmp_path):
    root = _repo(tmp_path, {"LICENSE": MIT, "CODE_OF_CONDUCT.md": f"report to {MARKER}\n"})
    failures, pending = guard.run(root)
    assert failures == [] and [(p.kind, p.path, p.line) for p in pending] == [("owner-set", "CODE_OF_CONDUCT.md", 1)]
    assert guard.main(["--root", str(root)]) == 0
    assert guard.main(["--root", str(root), "--release"]) == 1


def test_a_document_that_describes_the_marker_in_code_is_not_pending(tmp_path):
    root = _repo(tmp_path, {"LICENSE": MIT, "docs/a.md": f"An unset value is written `{MARKER}` in the file.\n"})
    assert guard.run(root) == ([], [])


def test_the_guard_and_its_test_may_mention_the_marker(tmp_path):
    root = _repo(tmp_path, {
        "LICENSE": MIT,
        "scripts/testing/public_release_guard.py": f"# {MARKER}\n",
        "tests/docs/test_public_release_guard.py": f"# {MARKER}\n",
    })
    assert guard.run(root) == ([], [])


def test_outside_a_git_checkout_it_fails_loudly(tmp_path, capsys):
    assert guard.main(["--root", str(tmp_path)]) == 2
    assert "not a git checkout" in capsys.readouterr().err


def test_untracked_files_are_never_scanned(tmp_path):
    root = _repo(tmp_path, {"LICENSE": MIT})
    (root / "scratch.md").write_text(f"{HOME}\n", encoding="utf-8")
    assert guard.run(root)[0] == []
