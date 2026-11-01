"""Readiness is observed evidence, not an installer completion flag."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


readiness = load("readiness", "scripts/setup/module_readiness.py")
setup = load("selective_setup", "scripts/setup/modules.py")


def test_missing_environment_is_not_ready(tmp_path):
    result = readiness.check_packages(tmp_path, "audio-production", [])
    assert result["status"] == "missing"


def test_package_mismatch_is_not_a_pass(monkeypatch, tmp_path):
    executable = setup.interpreter(
        tmp_path / ".venv-modules/audio-production", setup.os.name == "nt"
    )
    executable.parent.mkdir(parents=True)
    executable.touch()

    def run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, json.dumps([{"package": "loguru", "version": "0.1", "matches": False}]), ""
        )

    monkeypatch.setattr(readiness.subprocess, "run", run)
    assert readiness.check_packages(tmp_path, "audio-production", [])["status"] == "missing"


def test_dependency_conflict_is_not_a_pass(monkeypatch, tmp_path):
    executable = setup.interpreter(
        tmp_path / ".venv-modules/audio-production", setup.os.name == "nt"
    )
    executable.parent.mkdir(parents=True)
    executable.touch()

    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1 if "check" in command else 0, "[]", "")

    monkeypatch.setattr(readiness.subprocess, "run", run)
    assert readiness.check_packages(tmp_path, "audio-production", [])["status"] == "failed"


def test_app_presence_does_not_verify_a_module(monkeypatch):
    monkeypatch.setattr(readiness.shutil, "which", lambda _: "/test/obs")
    item = {
        "id": "creator-experience",
        "requirements": [],
        "tools": [{"label": "OBS", "commands": ["obs"]}],
        "remaining": "Record a real scene",
        "manual": "manual.md",
    }
    result = readiness.doctor(ROOT, {"modules": [item]})
    assert result["modules"][0]["checks"][0]["status"] == "passed"
    assert result["modules"][0]["capability_status"] == "not_verified"


def test_unavailable_app_is_not_claimed_uninstalled(monkeypatch):
    monkeypatch.setattr(readiness.shutil, "which", lambda _: None)
    assert (
        readiness.check_tool({"label": "Blender", "commands": ["blender"]})["status"] == "not_found"
    )


def test_installer_lock_blocks_a_second_caller_and_releases(monkeypatch, tmp_path):
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.delenv("HCP_MODULE_DATA_ROOT", raising=False)
    with setup.installation_lock():
        with pytest.raises(RuntimeError, match="Another module installation"):
            with setup.installation_lock():
                pytest.fail("Second installer entered")
    with setup.installation_lock():
        pass


def test_shared_desktop_data_directory_keeps_manual_install_report(monkeypatch, tmp_path):
    selection = setup.plan(setup.catalog(), ["soundboard"])
    monkeypatch.setenv("HCP_MODULE_DATA_ROOT", str(tmp_path / "shared data"))
    report = setup.install(selection)
    assert report["status"] == "action_required"
    assert len(list((tmp_path / "shared data/output/module-setup").glob("*/report.json"))) == 1
