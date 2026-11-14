"""Finite, test-only Windows execution experiment; normal CI selection is preserved.

Children write directly to durable files, avoiding an undrained subprocess pipe.
Only bounded, parameter-free progress is streamed. Timeout/log-limit is FAILURE,
and cleanup uses the current Popen handle, never a persisted PID or process group.
The separate Actions step deadline also covers interpreter/supervisor startup.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

SELECTION = (
    "tests/ai_agents/test_stream_host.py",
    "tests/audio_production/test_host_speech.py",
    "tests/automation_control/test_stream_director.py",
    "tests/automation_control/test_gameplay_handoff.py",
    "tests/automation_control/test_show_planner.py",
    "tests/content_creation",
    "tests/setup",
)
MAX_LOG_BYTES = 8 * 1024 * 1024
MAX_PROGRESS = 2048
OUTPUT = Path("output/orch04-windows-diagnostics")


def safe_progress(line: bytes) -> str | None:
    """Do not stream arbitrary assertions, environment, URLs or parameter values."""
    text = line.decode("utf-8", "replace")
    match = re.search(r"\b(tests/[\w./-]{1,160}::[\w:.]{1,160})", text)
    if match:
        return match[1]
    if text.startswith("ORCH04_NATIVE_CHILD_RESULT "):
        try:
            data = json.loads(text.removeprefix("ORCH04_NATIVE_CHILD_RESULT "))
            mode = data["mode"]
            code = data["returncode"]
            if not re.fullmatch(r"[a-zA-Z0-9.-]{1,40}", mode) or type(code) is not int:
                return None
            return f"native {mode} returncode={code} unsigned32={code & 0xFFFFFFFF:#010x}"
        except (ValueError, KeyError, TypeError):
            return None
    if "collected " in text:
        match = re.search(r"collected (\d+) items?", text)
        if match:
            return match[0]
    return None


def durable_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def run_stage(
    root: Path,
    output: Path,
    name: str,
    arguments: list[str],
    seconds: float,
    *,
    max_log_bytes: int = MAX_LOG_BYTES,
) -> dict:
    """Run one trusted diagnostic/test command; retain nonzero and timeout facts."""
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    log = output / (name + ".log")
    command = [sys.executable, "-u", *arguments]
    durable_json(output / (name + "-start.json"), {"command": command, "deadline": seconds})
    print("ORCH04_STAGE_START " + name, flush=True)
    reason = "exited"
    progress_count = 0
    pending = b""
    with log.open("xb") as sink, log.open("rb") as reader:
        child = subprocess.Popen(
            command, cwd=root, stdin=subprocess.DEVNULL, stdout=sink, stderr=subprocess.STDOUT
        )
        try:
            while True:
                block = reader.read(4096)
                if block:
                    for line in (pending + block).splitlines(keepends=True):
                        if not line.endswith((b"\n", b"\r")):
                            pending = line[-2048:]
                            continue
                        pending = b""
                        value = safe_progress(line)
                        if value:
                            durable_json(
                                output / "last-progress.json",
                                {
                                    "stage": name,
                                    "progress": value,
                                    "seconds": time.monotonic() - started,
                                },
                            )
                            if progress_count < MAX_PROGRESS:
                                print("ORCH04_PROGRESS " + value, flush=True)
                                progress_count += 1
                if log.stat().st_size > max_log_bytes:
                    reason = "log_limit"
                    break
                code = child.poll()
                if code is not None:
                    # Consume remaining regular-file output before recording completion.
                    if block:
                        continue
                    break
                if time.monotonic() - started >= seconds:
                    reason = "timeout"
                    break
                time.sleep(0.05)
        finally:
            if child.poll() is None:
                child.kill()  # Windows: TerminateProcess on THIS current Popen handle.
            code = child.wait(timeout=5)
    result = dict(
        stage=name,
        command=command,
        returncode=code,
        unsigned_32bit=code & 0xFFFFFFFF,
        reason=reason,
        elapsed_seconds=time.monotonic() - started,
        log_bytes=log.stat().st_size,
        success=reason == "exited" and code == 0,
    )
    durable_json(output / (name + "-result.json"), result)
    print("ORCH04_STAGE_END " + name + " " + json.dumps(result), flush=True)
    return result


def main() -> int:
    if os.name != "nt":
        raise SystemExit("Actual Windows execution required; no platform simulation")
    root = Path(__file__).resolve().parents[2]
    output = root / OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    durable_json(
        output / "runtime.json",
        dict(
            python=sys.version,
            executable=sys.executable,
            machine=platform.machine(),
            platform=sys.platform,
        ),
    )
    stages = [
        ("interpreter", ["-c", "import sys; print(sys.version,flush=True)"], 15),
        ("pytest-import", ["-c", "import pytest; print(pytest.__version__,flush=True)"], 30),
        (
            "diagnostic-import",
            [
                "-c",
                "import scripts.testing.production_artifacts_diagnostics; print('imported',flush=True)",
            ],
            30,
        ),
        (
            "native-arm-disarm",
            [
                "-c",
                "import sys,time; from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic; print('before-arm',flush=True); d=SessionDiagnostic(sys.stderr,1); d.start(); print('armed',flush=True); d.close(); print('disarmed',flush=True); time.sleep(1.1); print('alive',flush=True)",
            ],
            15,
        ),
        (
            "focused-normal",
            [
                "-X",
                "faulthandler",
                "-m",
                "pytest",
                "-p",
                "scripts.testing.production_artifacts_diagnostics",
                *SELECTION,
                "-o",
                "addopts=",
                "--strict-markers",
                "-m",
                "not live",
                "-vv",
                "-s",
                "--setup-show",
                "--trace-config",
                "--tb=short",
                "-o",
                "faulthandler_timeout=30",
                "--junitxml=" + str(output / "focused.xml"),
            ],
            360,
        ),
    ]
    results = []
    for name, arguments, seconds in stages:
        results.append(run_stage(root, output, name, arguments, seconds))
        durable_json(output / "summary.json", results)
    return 0 if all(row["success"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
