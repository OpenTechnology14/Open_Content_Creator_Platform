"""Dependency isolation must not widen the reviewed CI command allowlist."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("verify_security", ROOT / "scripts/testing/verify.py")
verify = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verify
spec.loader.exec_module(verify)


def test_python_override_preserves_exact_test_arguments():
    command = [sys.executable, "-m", "pytest", "-p", "scripts.testing.no_skips"]
    gate = verify.Gate("security-relay/checks", "reviewed command", ROOT)
    assert verify.security_interpreter(gate, command, {"security-relay": "prepared/python"}) == ["prepared/python", *command[1:]]


def test_other_jobs_and_native_commands_cannot_take_security_overrides():
    overrides = {"security-relay": "prepared/python"}
    for name, command in [("security-relay-extra/checks", [sys.executable, "-m", "pytest"]),
                          ("security-relay/checks", ["cargo", "test"]),
                          ("lint-and-test/checks", [sys.executable, "-m", "pytest"])]:
        assert verify.security_interpreter(verify.Gate(name, "check", ROOT), command, overrides) == command
