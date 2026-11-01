"""Required security jobs must fail when optional dependencies skip their checks."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("no_skips", ROOT / "scripts/testing/no_skips.py")
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


def session(stats):
    reporter = SimpleNamespace(stats=stats, write_line=lambda *_args, **_kwargs: None)
    return SimpleNamespace(config=SimpleNamespace(pluginmanager=SimpleNamespace(
        get_plugin=lambda *_: reporter)), exitstatus=0)


def test_security_dependency_skips_fail_the_lane():
    value = session({"skipped": [object()]})
    plugin.pytest_sessionfinish(value, 0)
    assert value.exitstatus == 1


def test_explicit_scope_deselection_is_not_a_missing_dependency_skip():
    value = session({"deselected": [object()], "passed": [object()]})
    plugin.pytest_sessionfinish(value, 0)
    assert value.exitstatus == 0
