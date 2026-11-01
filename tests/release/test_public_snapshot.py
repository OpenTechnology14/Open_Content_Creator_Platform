"""Privacy boundaries for one-way committed-source export."""

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/release/public_snapshot.py"
SPEC = importlib.util.spec_from_file_location("public_snapshot", SCRIPT)
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


def run(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    run(root, "init", "-q")
    run(root, "config", "user.name", "Fixture Maintainer")
    run(root, "config", "user.email", "fixture@example.invalid")
    (root / "README.md").write_text("# Example\n")
    (root / "LICENSE").write_text("MIT License\n")
    (root / "private").mkdir()
    (root / "private/accounts.md").write_text("private-identity-marker\n")
    (root / ".gitignore").write_text(".env\n")
    (root / ".env").write_text("private-identity-marker\n")
    run(root, "add", ".")
    run(root, "commit", "-qm", "fixture")
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({
        "private_repo": "example/private-source", "public_repo": "example/public-source",
        "deny_patterns": ["private-identity-marker"],
    }))
    return root, tmp_path / "public", policy


def test_exports_committed_code_not_working_state_private_files_or_history(source):
    root, output, policy = source
    (root / "README.md").write_text("private-identity-marker\n")
    report = snapshot.export_snapshot(root, output, policy, "HEAD")
    assert (output / "README.md").read_text() == "# Example\n"
    assert not (output / "private").exists()
    assert not (output / ".env").exists()
    assert not (output / ".git").exists()
    assert not report["history_exported"]
    assert "private-identity-marker" not in json.dumps(report)
    run(output, "init", "-q")
    run(output, "check-ignore", "private/accounts.md")
    assert "Public source edition" in (output / "PUBLIC_SOURCE.md").read_text()


@pytest.mark.parametrize("name,content", [
    ("notes.md", "private-identity-marker"),
    ("icon.bin", b"\x89PNG\x00private-identity-marker"),
    (".env.production", "synthetic only"),
    ("private-identity-marker.md", "synthetic only"),
    ("nested/private/notes.md", "synthetic only"),
])
def test_rejects_sensitive_text_binary_metadata_paths_and_secret_files(source, name, content):
    root, output, policy = source
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    run(root, "add", "-f", name)
    run(root, "commit", "-qm", "candidate")
    with pytest.raises(ValueError):
        snapshot.export_snapshot(root, output, policy, "HEAD")
    assert not output.exists()


def test_removes_marked_private_section_and_does_not_invent_public_pr_history(source):
    root, output, policy = source
    (root / "README.md").write_text(
        "# Example\n<!-- private-only:start -->\nprivate-identity-marker\n<!-- private-only:end -->\n"
        "[Review](https://github.com/example/private-source/pull/123)\n"
        "https://github.com/example/private-source\n"
    )
    run(root, "add", "README.md")
    run(root, "commit", "-qm", "candidate")
    snapshot.export_snapshot(root, output, policy, "HEAD")
    text = (output / "README.md").read_text()
    assert "private-identity-marker" not in text
    assert "/pull/123" not in text
    assert "private development evidence" in text
    assert "https://github.com/example/public-source" in text


def test_rejects_unbalanced_private_markers(source):
    root, output, policy = source
    (root / "README.md").write_text("<!-- private-only:start -->\n")
    run(root, "add", "README.md")
    run(root, "commit", "-qm", "candidate")
    with pytest.raises(ValueError, match="unbalanced"):
        snapshot.export_snapshot(root, output, policy, "HEAD")
    assert not output.exists()


@pytest.mark.parametrize("inside", [True, False])
def test_never_overwrites_existing_destination_or_exports_inside_source(source, inside):
    root, output, policy = source
    if inside:
        output = root / "nested-output"
    else:
        output.mkdir()
        (output / "retain").write_text("unchanged")
    with pytest.raises(ValueError):
        snapshot.export_snapshot(root, output, policy, "HEAD")
    if not inside:
        assert (output / "retain").read_text() == "unchanged"


def test_rejects_symlink_instead_of_reading_external_target(source):
    root, output, policy = source
    (root / "linked").symlink_to(policy)
    run(root, "add", "linked")
    run(root, "commit", "-qm", "candidate")
    with pytest.raises(ValueError, match="symlinks"):
        snapshot.export_snapshot(root, output, policy, "HEAD")
    assert not output.exists()


@pytest.mark.parametrize("change", ["identical", "invalid-name", "empty-deny-list"])
def test_rejects_incomplete_or_ambiguous_policy(source, change):
    root, output, policy = source
    data = json.loads(policy.read_text())
    if change == "identical":
        data["public_repo"] = data["private_repo"]
    elif change == "invalid-name":
        data["public_repo"] = "../../invalid"
    else:
        data["deny_patterns"] = []
    policy.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        snapshot.export_snapshot(root, output, policy, "HEAD")
    assert not output.exists()


@pytest.mark.parametrize("change", ["oversize", "missing-license", "submodule"])
def test_rejects_unreviewed_distribution_inputs(source, change):
    root, output, policy = source
    if change == "oversize":
        (root / "large.bin").write_bytes(b"0" * (5 * 1024 * 1024 + 1))
        run(root, "add", "large.bin")
    elif change == "missing-license":
        run(root, "rm", "LICENSE")
    else:
        commit = snapshot.git(root, "rev-parse", "HEAD").decode().strip()
        run(root, "update-index", "--add", "--cacheinfo", f"160000,{commit},submodule")
    run(root, "commit", "-qm", "candidate")
    with pytest.raises(ValueError):
        snapshot.export_snapshot(root, output, policy, "HEAD")
    assert not output.exists()


def test_cli_errors_never_echo_invalid_private_policy_values(source):
    root, output, policy = source
    policy.write_text('{"private-identity-marker":')
    result = subprocess.run(
        ["python3", str(SCRIPT), "--source", str(root), "--destination", str(output),
         "--policy", str(policy)], capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "private-identity-marker" not in result.stderr + result.stdout
    assert str(policy) not in result.stderr + result.stdout
    assert not output.exists()
