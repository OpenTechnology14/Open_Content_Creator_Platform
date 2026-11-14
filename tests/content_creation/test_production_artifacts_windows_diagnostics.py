"""Portable mechanism tests; actual Windows results come from the isolated workflow."""

import json
from pathlib import Path
import shlex
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.testing.windows_contract_diagnostics import (  # noqa: E402
    SELECTION,
    run_stage,
    safe_progress,
)


def test_diagnostic_selection_preserves_the_full_normal_focused_command():
    workflow = yaml.safe_load((ROOT / ".github/workflows/stream-autopilot.yml").read_text())
    step = next(
        s
        for s in workflow["jobs"]["native-rehearsal"]["steps"]
        if s.get("name") == "Focused contracts"
    )
    argv = shlex.split(step["run"])
    assert (
        tuple(argv[argv.index("scripts.testing.production_artifacts_diagnostics") + 1 :])
        == SELECTION
    )
    diagnostic = yaml.safe_load(
        (ROOT / ".github/workflows/orch04-windows-diagnostics.yml").read_text()
    )
    job = diagnostic["jobs"]["windows-contract-diagnosis"]
    assert job["timeout-minutes"] == 15 and job["runs-on"] == "windows-latest"
    assert any(
        s.get("if") == "always()" and s.get("uses") == "actions/upload-artifact@v4"
        for s in job["steps"]
    )
    assert not any(s.get("continue-on-error") for s in job["steps"])


def test_owned_deadline_fails_and_settles_child_with_durable_start_and_result(tmp_path):
    result = run_stage(
        tmp_path, tmp_path / "output", "hang", ["-c", "import time; time.sleep(0.8)"], 0.05
    )
    assert result["reason"] == "timeout" and not result["success"]
    assert result["returncode"] != 0 and result["elapsed_seconds"] < 0.6
    assert json.loads((tmp_path / "output/hang-start.json").read_text())["deadline"] == 0.05
    assert json.loads((tmp_path / "output/hang-result.json").read_text()) == result


@pytest.mark.parametrize("code", [0, 3])
def test_normal_exit_preserves_returncode_and_failure_without_fake_timeout(tmp_path, code):
    result = run_stage(
        tmp_path, tmp_path / "output", "exit", ["-c", f"raise SystemExit({code})"], 3
    )
    assert result["reason"] == "exited" and result["returncode"] == code
    assert result["success"] is (code == 0)


def test_log_budget_is_failure_even_when_child_already_exited_zero(tmp_path):
    result = run_stage(
        tmp_path,
        tmp_path / "output",
        "flood",
        ["-c", "import os; os.write(1,b'x'*16384)"],
        3,
        max_log_bytes=512,
    )
    assert result["reason"] == "log_limit" and not result["success"]


def test_progress_excludes_parameters_urls_and_keeps_full_native_returncode(tmp_path, capsys):
    code = (
        "print('tests/content_creation/test_owned.py::test_case[private-value] PASSED',flush=True)"
    )
    result = run_stage(tmp_path, tmp_path / "output", "progress", ["-c", code], 3)
    streamed = capsys.readouterr().out
    assert result["success"]
    assert "ORCH04_PROGRESS tests/content_creation/test_owned.py::test_case" in streamed
    # Command is retained as fixed diagnostic provenance; parameter-free progress is separate.
    assert (
        "private-value"
        not in json.loads((tmp_path / "output/last-progress.json").read_text())["progress"]
    )
    assert safe_progress(b"https://credential.invalid/private") is None
    row = dict(mode="held-GIL", returncode=0x10001)
    assert safe_progress(("ORCH04_NATIVE_CHILD_RESULT " + json.dumps(row)).encode()) == (
        "native held-GIL returncode=65537 unsigned32=0x00010001"
    )


def test_overlong_and_malformed_progress_do_not_become_stdout_authority():
    assert safe_progress(b"ORCH04_NATIVE_CHILD_RESULT not-json") is None
    assert (
        safe_progress(b'ORCH04_NATIVE_CHILD_RESULT {"mode":"https://private","returncode":1}')
        is None
    )
    assert safe_progress(b'ORCH04_NATIVE_CHILD_RESULT {"mode":"closed","returncode":"1"}') is None
    assert safe_progress(b"unrestricted " + b"x" * 10000) is None


def test_streamed_progress_is_bounded_but_latest_stage_stays_durable(tmp_path, capsys):
    code = "for i in range(2050): print('tests/owned.py::test_case'+str(i),flush=True)"
    result = run_stage(tmp_path, tmp_path / "output", "many", ["-c", code], 15)
    assert result["success"]
    assert capsys.readouterr().out.count("ORCH04_PROGRESS ") == 2048
    latest = json.loads((tmp_path / "output/last-progress.json").read_text())
    assert latest["progress"] == "tests/owned.py::test_case2049"


def test_large_wire_payload_keeps_full_input_and_bounded_collected_test_ids():
    import test_production_artifacts_jobs as jobs

    mark = next(
        m
        for m in jobs.test_malformed_wire_never_creates_production.pytestmark
        if m.name == "parametrize"
    )
    payloads = mark.args[1]
    assert len(payloads) == 6 and payloads[-1] == b"x" * (1024 * 1024 + 1)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "tests/content_creation/test_production_artifacts_jobs.py::test_malformed_wire_never_creates_production",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    nodes = [
        s
        for s in result.stdout.splitlines()
        if "::test_malformed_wire_never_creates_production[" in s
    ]
    assert len(nodes) == 6
    longest = max(map(len, nodes))
    assert longest < 256, longest
    assert any(s.endswith("[oversized]") for s in nodes)
