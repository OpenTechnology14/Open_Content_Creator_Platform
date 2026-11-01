"""Run recognized local CI gates; list every unavailable or service-changing step."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
MINIMUM_GATES = 15


@dataclass(frozen=True)
class Gate:
    name: str
    command: str
    directory: Path


def read_gates(workflow: Path, root: Path) -> list[Gate]:
    """Expand run steps in CI order without executing setup actions or expressions."""
    document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
        raise ValueError("workflow has no jobs mapping")
    gates = []
    for job_name, job in document["jobs"].items():
        matrix = job.get("strategy", {}).get("matrix", {})
        if any(not isinstance(values, list) for values in matrix.values()):
            raise ValueError(f"unsupported matrix in {job_name}")
        if "include" in matrix or "exclude" in matrix:
            raise ValueError(f"unsupported matrix include/exclude in {job_name}")
        variants = itertools.product(*matrix.values()) if matrix else [()]
        for values in variants:
            bindings = dict(zip(matrix, values))

            def expand(text: str) -> str:
                for key, value in bindings.items():
                    text = re.sub(r"\$\{\{\s*matrix\." + re.escape(key) + r"\s*\}\}", str(value), text)
                if "${{" in text:
                    raise ValueError(f"unresolved workflow expression in {job_name}")
                return text

            for step in job.get("steps", []):
                if "run" not in step:
                    continue
                if step.get("if") or step.get("env") or job.get("env"):
                    raise ValueError(f"conditional/environment run step needs review in {job_name}")
                directory = (root / expand(step.get("working-directory", "."))).resolve()
                if not directory.is_relative_to(root.resolve()):
                    raise ValueError("working directory escapes repository")
                lines = expand(step["run"]).replace("\\\n", " ").splitlines()
                commands = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
                # Privileged installation blocks are classified as one skipped step.
                if any(line.startswith("sudo ") for line in commands):
                    commands = ["sudo installation block"]
                label = f"{job_name}/{step.get('name', 'run')}"
                if bindings:
                    label += f" [{','.join(f'{key}={value}' for key, value in bindings.items())}]"
                gates.extend(Gate(label, command, directory) for command in commands)
    return gates


def classify(gate: Gate, root: Path) -> tuple[list[str] | None, str]:
    """Allow known checks only; changes to CI cannot silently expand execution authority."""
    command = gate.command
    if command.startswith(("pip install ", "python -m pip install ", "sudo ")) or command == "npm ci":
        return None, "environment installation; prepare dependencies separately"
    if command == "cp .env.example .env":
        return None, "preserve local .env; compose checks use .env.example explicitly"
    if command == "make test-acceptance":
        return None, "live harness starts services; run separately with its acceptance prerequisites"
    if command == "pytest -q":
        return [sys.executable, "-m", "pytest", "-q"], ""
    if command in {
        'python -m pytest -p scripts.testing.no_skips -m "not live" tests/cloud_relay -q',
        'python -m pytest -p scripts.testing.no_skips -m "not live" tests/backend_api -q',
    }:
        return [sys.executable] + shlex.split(command)[1:], ""
    if command == 'python -m pytest -p scripts.testing.no_skips -m live tests/cloud_relay/test_tenant_isolation.py -q':
        return None, "owned Postgres live acceptance; run separately with native tools or Docker"
    if command == "python scripts/testing/generate_docs.py --check":
        return [sys.executable, "scripts/testing/generate_docs.py", "--check"], ""
    if command == "ruff check modules/ scripts/":
        return [sys.executable, "-m", "ruff", "check", "modules/", "scripts/"], ""
    if command in {"npm run build", "npm run check", "cargo check --locked", "cargo test --locked"}:
        return shlex.split(command), ""
    if re.fullmatch(r"cargo test --locked -p [a-z0-9-]+", command):
        return shlex.split(command), ""
    if command == "cargo test --locked --manifest-path apps/shared/setup-engine/Cargo.toml":
        return shlex.split(command), ""
    if command in {
        "docker compose build minio minio-bootstrap",
        "docker compose -f docker-compose.yml config -q",
        "docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml config -q",
    }:
        args = shlex.split(command)
        return args[:2] + ["--env-file", str(root / ".env.example")] + args[2:], ""
    raise ValueError(f"unrecognized CI command requires review: {command}")


def run_gate(gate: Gate, args: list[str], timeout: int) -> str:
    """Run a bounded check; kill its process group if the timeout expires."""
    import os
    import signal

    process = subprocess.Popen(args, cwd=gate.directory, start_new_session=True)
    try:
        return "PASS" if process.wait(timeout=timeout) == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False)
        process.wait()
        return "TIMEOUT"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="plan without running checks")
    parser.add_argument("--python-only", action="store_true", help="run Python gates; list native/compose checks as not run")
    parser.add_argument("--timeout", type=int, default=1800, help="maximum seconds per check")
    parser.add_argument("--relay-python", type=Path, help="prepared interpreter for relay security jobs")
    parser.add_argument("--backend-python", type=Path, help="prepared interpreter for backend security jobs")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("timeout must be positive")
    interpreters = {}
    for job, value in (("security-relay", args.relay_python), ("security-backend", args.backend_python)):
        if value is not None:
            path = value.absolute()
            if not path.is_file() or not re.fullmatch(r"python(?:3(?:\.\d+)?)?(?:\.exe)?", path.name):
                parser.error("security interpreter must be an existing Python executable")
            interpreters[job] = str(path)
    try:
        gates = read_gates(ROOT / ".github/workflows/ci.yml", ROOT)
        planned = [(gate, *classify(gate, ROOT)) for gate in gates]
        count = sum(command is not None for _, command, _ in planned)
        if count < MINIMUM_GATES:
            raise ValueError(f"tripwire: {count} check commands; expected at least {MINIMUM_GATES}")
    except (ValueError, OSError, yaml.YAMLError) as exc:
        sys.stderr.write(f"Verification plan rejected: {exc}\n")
        return 2
    results = []
    for gate, command, reason in planned:
        if command and args.python_only and command[0] != sys.executable:
            command, reason = None, "outside requested Python-only scope"
        if command:
            command = security_interpreter(gate, command, interpreters)
        if command and shutil.which(command[0]) is None:
            command, reason = None, "required executable unavailable"
        if not command:
            results.append((gate.name, "NOT RUN", reason))
        elif args.list:
            results.append((gate.name, "PLANNED", gate.command))
        else:
            sys.stdout.write(f"\nRUN {gate.name}: {gate.command}\n")
            sys.stdout.flush()
            try:
                status = run_gate(gate, command, args.timeout)
            except OSError as exc:
                status = "FAIL"
                reason = type(exc).__name__
            results.append((gate.name, status, reason))
    sys.stdout.write("\nVerification summary (local checks only)\n")
    for name, status, reason in results:
        sys.stdout.write(f"{status}: {name}" + (f" — {reason}" if reason else "") + "\n")
    skipped = sum(status == "NOT RUN" for _, status, _ in results)
    sys.stdout.write(f"{len(results)} CI commands accounted for; {skipped} not run.\n")
    return int(any(status in {"FAIL", "TIMEOUT"} for _, status, _ in results))


def security_interpreter(gate: Gate, command: list[str], interpreters: dict[str, str]) -> list[str]:
    """Override only a reviewed Python security job, never a CI-selected executable."""
    job = gate.name.split("/", 1)[0]
    if command[0] == sys.executable and job in {"security-relay", "security-backend"} and job in interpreters:
        return [interpreters[job], *command[1:]]
    return command


if __name__ == "__main__":
    raise SystemExit(main())
