"""Exercise addon lifecycle error paths without claiming native Blender UI acceptance."""

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def operator(monkeypatch):
    class Operator:
        def report(self, severity, message):
            self.reports.append((severity, message))

    bpy = SimpleNamespace(
        types=SimpleNamespace(Operator=Operator),
        props=SimpleNamespace(StringProperty=lambda **kwargs: None),
    )
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    path = Path(__file__).resolve().parents[2] / "plugins/blender-addon/operators/__init__.py"
    spec = importlib.util.spec_from_file_location("hcp_test_blender_operators", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instance = module.CE_OT_BatchRender()
    instance.reports = []
    return instance


@pytest.mark.parametrize("damage", ["missing-log", "invalid-json", "invalid-schema"])
def test_finished_worker_with_damaged_files_reports_failure_and_releases_timer(
    operator, tmp_path, damage
):
    removed = []
    context = SimpleNamespace(window_manager=SimpleNamespace(event_timer_remove=removed.append))
    operator._timer = object()
    operator._process = SimpleNamespace(poll=lambda: 0, returncode=0)
    operator._log_path = tmp_path / "process.log"
    operator._metadata = tmp_path / "job.json"
    if damage != "missing-log":
        operator._log_path.write_bytes(b"")
    operator._metadata.write_text({
        "missing-log": '{"status":"failed"}',
        "invalid-json": '{"status":',
        "invalid-schema": '[]',
    }[damage])
    assert operator.modal(context, SimpleNamespace(type="TIMER")) == {"CANCELLED"}
    assert removed == [operator._timer]
    assert any("ERROR" in severity for severity, _ in operator.reports)
