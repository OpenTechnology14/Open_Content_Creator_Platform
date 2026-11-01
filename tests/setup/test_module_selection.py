"""Selection is explicit, isolated and never equates installation with service readiness."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("module_setup", ROOT / "scripts/setup/modules.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def test_catalog_covers_every_module_and_resolves_profiles():
    data = setup.catalog()
    expected = {p.name for p in (ROOT / "modules").iterdir() if (p / "setup/manual.md").exists()}
    assert set(data["modules"]) == expected
    for profile in data["profiles"]:
        assert setup.plan(data, [], profile)["modules"]


def test_only_selected_modules_and_dependencies_are_planned():
    data = setup.catalog()
    result = setup.plan(data, ["broadcast-graphics"])
    assert [item["id"] for item in result["modules"]] == [
        "storage-data",
        "backend-api",
        "broadcast-graphics",
    ]
    assert result["modules"][0]["added_dependency"] is True
    assert result["modules"][-1]["added_dependency"] is False
    assert [item["id"] for item in setup.plan(data, ["soundboard"])["modules"]] == ["soundboard"]


@pytest.mark.parametrize("selected,profile", [([], None), (["not-a-module"], None), ([], "typo")])
def test_invalid_or_empty_selection_is_rejected(selected, profile):
    with pytest.raises(ValueError):
        setup.plan(setup.catalog(), selected, profile)


def test_dependency_cycles_are_rejected():
    data = setup.catalog()
    data["modules"]["storage-data"]["depends_on"] = ["backend-api"]
    with pytest.raises(ValueError, match="cycle"):
        setup.plan(data, ["backend-api"])


def test_manual_module_does_not_run_installer(monkeypatch, tmp_path):
    selection = setup.plan(setup.catalog(), ["soundboard"])
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup.platform, "platform", lambda: "test-host")
    monkeypatch.setattr(setup.subprocess, "run", lambda *a, **k: pytest.fail("Unexpected install"))
    report = setup.install(selection)
    assert report["status"] == "action_required"
    assert report["modules"][0]["dependencies"] == "manual_only"
    assert report["modules"][0]["capability_status"] == "not_verified"
    assert not (tmp_path / ".venv-modules").exists()


def test_failed_module_does_not_block_next_module(monkeypatch, tmp_path):
    selection = setup.plan(setup.catalog(), ["audio-production", "content-creation"])
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup.platform, "platform", lambda: "test-host")
    for name in ("audio-production", "content-creation"):
        executable = setup.interpreter(tmp_path / ".venv-modules" / name, setup.os.name == "nt")
        executable.parent.mkdir(parents=True)
        executable.touch()
    calls = []

    def run(command, **kwargs):
        assert "shell" not in kwargs
        calls.append(command)
        if "audio-production" in command[0]:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(setup.subprocess, "run", run)
    report = setup.install(selection)
    assert report["status"] == "failed"
    assert [item["dependencies"] for item in report["modules"]] == ["failed", "installed"]
    assert all(item["capability_status"] == "not_verified" for item in report["modules"])
    assert any(
        "pip" in call
        and str(tmp_path / "modules/content-creation/stream_shorts/requirements.txt") in call
        for call in calls
    )


def test_interpreter_layout_is_platform_specific(tmp_path):
    assert setup.interpreter(tmp_path, True) == tmp_path / "Scripts/python.exe"
    assert setup.interpreter(tmp_path, False) == tmp_path / "bin/python"
