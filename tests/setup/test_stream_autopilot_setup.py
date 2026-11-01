"""Portable rehearsal failures must be visible and must preserve existing artifacts."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "autopilot_setup", ROOT / "scripts/setup/stream_autopilot.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def test_environment_handles_repository_with_spaces(monkeypatch, tmp_path):
    root = tmp_path / "my creator platform"
    monkeypatch.setattr(setup, "ROOT", root)
    env = setup.environment()
    assert env["PYTHONPATH"].split(os.pathsep) == [
        str(root / "modules" / name)
        for name in ("ai-agents", "automation-control", "content-creation")
    ]
    assert env["PYTHONUTF8"] == "1"


def test_missing_prerequisites_record_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(setup, "doctor", lambda: {"ready": False})
    destination = tmp_path / "rehearsal"
    with pytest.raises(RuntimeError):
        setup.smoke(destination)
    report = json.loads((destination / "report.json").read_text())
    assert report["status"] == "failed"
    assert report["published"] is False
    with pytest.raises(FileExistsError):
        setup.smoke(destination)


def test_child_process_failure_records_stage(monkeypatch, tmp_path):
    monkeypatch.setattr(setup, "doctor", lambda: {"ready": True})

    def fail(command, **kwargs):
        assert "shell" not in kwargs
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(setup.subprocess, "run", fail)
    destination = tmp_path / "rehearsal"
    with pytest.raises(subprocess.CalledProcessError):
        setup.smoke(destination)
    report = json.loads((destination / "report.json").read_text())
    assert report["status"] == "failed"
    assert report["steps"][0]["name"] == "host-validation"
    assert report["steps"][0]["status"] == "failed"


def test_smoke_source_runs_safe_supervisor_before_host_rehearsal():
    source = (ROOT / "scripts/setup/stream_autopilot.py").read_text(encoding="utf-8")
    supervisor = source.index('step("supervisor-rehearsal"')
    host = source.index('events = step(\n            "host-rehearsal"')
    assert supervisor < host
    assert 'supervisor_report["broadcast_started"]' in source
