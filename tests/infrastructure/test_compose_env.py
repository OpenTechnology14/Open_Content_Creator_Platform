"""Offline checks for infrastructure's env-var contract (P-035).

No Docker required. `docs/AUDIT.md` and `modules/infrastructure/setup/
manual.md` both used to claim "six Compose-referenced values are absent
from .env.example" — stale by the time this was written; every `${VAR}`
docker-compose.yml/docker-compose.digitalocean.yml reference already had
a matching .env.example entry. This is the test that makes that claim
checkable instead of asserted.

deploy-do.sh's DROPLET-resolution tests run the real script end to end
with fake `ssh`/`rsync` stubs on PATH (the script already supports
SSH=/RSYNC= overrides for exactly this) rather than grepping a fragment
of its source and re-evaluating it — the latter would silently stop
testing anything real the moment the script's wording changed.
"""

from __future__ import annotations

import re
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = REPO / ".env.example"
DEPLOY_SCRIPT = REPO / "scripts" / "deploy" / "deploy-do.sh"
COMPOSE_FILES = [
    REPO / "docker-compose.yml",
    REPO / "docker-compose.digitalocean.yml",
]


def _compose_vars(path: Path) -> set[str]:
    body = path.read_text(encoding="utf-8")
    return set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*)", body))


def _env_example_vars() -> set[str]:
    body = ENV_EXAMPLE.read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Z_][A-Z0-9_]*)=", body, re.MULTILINE))


@pytest.mark.parametrize("compose_file", COMPOSE_FILES, ids=lambda p: p.name)
def test_every_compose_var_is_in_env_example(compose_file: Path) -> None:
    needed = _compose_vars(compose_file)
    assert needed, f"found no ${{VAR}} references in {compose_file.name} — check the regex"

    available = _env_example_vars()
    missing = needed - available
    assert not missing, (
        f"{compose_file.name} references {missing}, which .env.example never declares — "
        f"a clean clone would hit an unset-variable warning or a hard Compose failure "
        f"(':?' vars) with no clue what to add"
    )


@pytest.fixture
def fake_ssh_rsync(tmp_path):
    """Fake `ssh` and `rsync` that just record their invocation and exit 0
    — enough for deploy-do.sh to run to completion without touching a
    real network, so its DROPLET-resolution logic runs for real.

    Also copies the real script into an isolated fake repo (with its own
    scripts/deploy/ layout, so SCRIPT_DIR/REPO_ROOT resolve inside
    tmp_path) rather than running the real one in place — this repo's own
    root .env (real dev config, or CI's copy of .env.example) already sets
    DO_DROPLET_IP= empty, which the script correctly sources and which
    would silently clobber whatever this test injects via subprocess env.
    The fake repo's .env is fully test-controlled instead.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "calls.log"

    for name in ("ssh", "rsync"):
        script = bin_dir / name
        script.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log_file}"\nexit 0\n')
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    fake_repo = tmp_path / "repo"
    fake_deploy_dir = fake_repo / "scripts" / "deploy"
    fake_deploy_dir.mkdir(parents=True)
    fake_script = fake_deploy_dir / "deploy-do.sh"
    fake_script.write_text(DEPLOY_SCRIPT.read_text(encoding="utf-8"))
    fake_script.chmod(fake_script.stat().st_mode | stat.S_IEXEC)

    return bin_dir, log_file, fake_script, fake_repo


def _run_deploy(bin_dir: Path, script: Path, repo_root: Path, extra_env: dict) -> subprocess.CompletedProcess:
    env_lines = "\n".join(f"{k}={v}" for k, v in extra_env.items())
    (repo_root / ".env").write_text(env_lines + "\n", encoding="utf-8")
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    return subprocess.run(
        ["bash", str(script)],
        capture_output=True, text=True, timeout=10, cwd=repo_root, env=env,
    )


def test_deploy_script_falls_back_to_do_droplet_ip(fake_ssh_rsync) -> None:
    """Regression: .env.example declared DO_DROPLET_IP and DO_SSH_USER, but
    deploy-do.sh never read either — filling them into .env did nothing,
    DROPLET still had to be passed explicitly on every invocation."""
    bin_dir, log_file, script, repo_root = fake_ssh_rsync
    result = _run_deploy(
        bin_dir, script, repo_root, {"DO_DROPLET_IP": "203.0.113.5", "DO_SSH_USER": "deploy"}
    )
    assert result.returncode == 0, result.stderr
    calls = log_file.read_text()
    assert "deploy@203.0.113.5" in calls, f"resolved host never reached ssh/rsync: {calls!r}"


def test_deploy_script_explicit_droplet_wins_over_env_fallback(fake_ssh_rsync) -> None:
    bin_dir, log_file, script, repo_root = fake_ssh_rsync
    result = _run_deploy(
        bin_dir, script, repo_root,
        {"DROPLET": "explicit-host.ts.net", "DO_DROPLET_IP": "203.0.113.5", "DO_SSH_USER": "deploy"},
    )
    assert result.returncode == 0, result.stderr
    calls = log_file.read_text()
    assert "explicit-host.ts.net" in calls
    assert "deploy@203.0.113.5" not in calls


def test_deploy_script_fails_loudly_with_no_droplet_and_no_ip(fake_ssh_rsync) -> None:
    bin_dir, _, script, repo_root = fake_ssh_rsync
    result = _run_deploy(bin_dir, script, repo_root, {})
    assert result.returncode != 0
    assert "DROPLET" in result.stderr
