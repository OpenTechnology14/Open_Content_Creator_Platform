"""Collect private release evidence from a clean checkout; never authorize a release."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time

# The collector and verifier are versioned together. Do not load Python from a
# different checkout merely to inspect its CI plan.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_COMMANDS = {"docker compose build minio minio-bootstrap"}


def git(root: Path, *args: str) -> str:
    """Read Git metadata without printing paths, remote URLs or file contents."""
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError("Git metadata unavailable")
    return result.stdout.strip()


def source_metadata(root: Path) -> dict:
    """Reject dirty, nested and credential-bearing source trees before any check."""
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("checkout must be a repository root")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("checkout is dirty; commit the reviewed work or use a fresh clone")
    if (root / ".env").exists():
        raise ValueError("checkout contains .env; use a fresh clone without local credentials")
    return {
        "commit": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "clean": True,
    }


def digest(path: Path) -> str:
    """Hash a file with bounded memory."""
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def artifact_metadata(path: Path) -> dict:
    """Hash only explicitly selected public installers, not arbitrary user files."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact must be a regular file, not a symlink")
    if path.suffix.lower() not in {".dmg", ".exe", ".msi", ".appimage", ".deb", ".rpm"}:
        raise ValueError("artifact must be a desktop installer")
    if any(character in path.name for character in "\r\n"):
        raise ValueError("artifact basename must not contain line breaks")
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": digest(path),
            "provenance": "operator-supplied; build/source association not verified"}


def python_tooling() -> dict:
    """Record only predefined public package versions, not environment variables."""
    versions = {}
    for name in ("pytest", "ruff", "PyYAML"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def run_check(command: list[str], directory: Path, timeout: int) -> dict:
    """Record outcome and duration without collecting potentially private tool output."""
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        code = process.wait(timeout=timeout)
        status = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        process.wait()
        code, status = None, "TIMEOUT"
    return {"status": status, "exit_code": code,
            "elapsed_seconds": round(time.monotonic() - started, 3)}


def plan_checks(root: Path, python_only: bool) -> list[tuple[dict, list[str] | None, Path]]:
    """Reuse CI's reviewed allowlist; account for every skipped step explicitly."""
    gates = verify.read_gates(root / ".github/workflows/ci.yml", root)
    classified = [(gate, *verify.classify(gate, root)) for gate in gates]
    if sum(command is not None for _, command, _ in classified) < verify.MINIMUM_GATES:
        raise ValueError("CI plan has fewer checks than the verifier tripwire permits")
    checks = []
    for gate, command, reason in classified:
        if gate.command in EXCLUDED_COMMANDS:
            command, reason = None, "container image build; run separately with Docker"
        if command and python_only and command[0] != sys.executable:
            command, reason = None, "outside requested Python-only scope"
        if command and shutil.which(command[0]) is None:
            command, reason = None, "required executable unavailable"
        entry = {"name": gate.name, "command": gate.command,
                 "directory": gate.directory.relative_to(root).as_posix(),
                 "status": "PLANNED" if command else "NOT RUN"}
        if reason:
            entry["reason"] = reason
        checks.append((entry, command, gate.directory))
    return checks


def collect(root: Path, output: Path, artifacts: list[Path], python_only: bool,
            timeout: int) -> dict:
    """Write a bounded evidence bundle outside the clean source checkout."""
    source = source_metadata(root)
    if output.is_relative_to(root) or output.exists():
        raise ValueError("output must be a new directory outside the checkout")
    planned = plan_checks(root, python_only)
    installers = [artifact_metadata(path) for path in artifacts]
    if len({item["name"] for item in installers}) != len(installers):
        raise ValueError("artifact basenames must be unique")
    report = {
        "schema_version": 1,
        "claim": "private local check evidence; not release approval",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "collector_sha256": digest(Path(__file__)),
        "verifier_sha256": digest(Path(verify.__file__)),
        "host": {"os": platform.system(), "release": platform.release(),
                 "architecture": platform.machine(), "python": platform.python_version()},
        "python_tooling": python_tooling(),
        "checks": [],
        "artifacts": installers,
        "release_gates": [
            {"name": name, "status": "NOT RUN", "reason": reason}
            for name, reason in [
                ("license and governance", "owner/legal sign-off required; D-01 remains separate"),
                ("supported targets", "D-02 support decision and native evidence on every target"),
                ("secret scanning", "full-history and working-tree scanner evidence required separately"),
                ("SBOM and dependency review", "generate an SBOM and review third-party licenses separately"),
                ("artifact provenance and signing", "supplied hashes do not prove source association or signatures"),
                ("native and live acceptance", "OBS, ComfyUI, clean-host install, outage and rollback runs required"),
            ]
        ],
    }
    for entry, command, directory in planned:
        if command:
            sys.stdout.write(f"RUN {entry['name']}\n")
            sys.stdout.flush()
            try:
                entry.update(run_check(command, directory, timeout))
            except OSError:
                entry.update(status="FAIL", reason="check could not be started")
        report["checks"].append(entry)
    try:
        after = source_metadata(root)
        unchanged = after == source
    except ValueError:
        unchanged = False
    report["source_unchanged"] = unchanged
    if not unchanged:
        report["source"]["clean"] = False
    report["local_checks_passed"] = unchanged and all(
        item["status"] == "PASS" for item in report["checks"]
        if item["status"] != "NOT RUN"
    )
    report["release_ready"] = False
    output.mkdir(parents=True, exist_ok=False)
    (output / "evidence.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [f"{digest(output / 'evidence.json')}  evidence.json"]
    lines.extend(f"{item['sha256']}  {item['name']}" for item in installers)
    (output / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=ROOT, help="clean repository root")
    parser.add_argument("--output", type=Path, help="new evidence directory outside the checkout")
    parser.add_argument("--artifact", type=Path, action="append", default=[], help="explicit installer to hash")
    parser.add_argument("--python-only", action="store_true", help="record native checks as not run")
    parser.add_argument("--list", action="store_true", help="inspect CI plan without executing it")
    parser.add_argument("--timeout", type=int, default=1800, help="maximum seconds per check")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("timeout must be positive")
    root = args.checkout.resolve()
    try:
        if args.list:
            for entry, _, _ in plan_checks(root, args.python_only):
                sys.stdout.write(f"{entry['status']}: {entry['name']} — {entry['command']}\n")
            return 0
        if args.output is None:
            parser.error("--output is required unless --list is used")
        report = collect(root, args.output.resolve(), args.artifact, args.python_only, args.timeout)
    except (ValueError, OSError, verify.yaml.YAMLError) as exc:
        # Do not render exception text from filesystem/process errors.
        message = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        sys.stderr.write(f"Evidence collection rejected: {message}\n")
        return 2
    for entry in report["checks"] + report["release_gates"]:
        sys.stdout.write(f"{entry['status']}: {entry['name']}\n")
    sys.stdout.write("Private evidence written; release_ready=false. See evidence.json for skipped gates.\n")
    return 0 if report["local_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
