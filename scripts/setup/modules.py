"""List, plan and selectively install module Python dependencies on Mac or Windows."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import venv
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def catalog() -> dict:
    """Read the repository-owned installation manifest; reject missing references."""
    data = json.loads(
        (ROOT / "configs/local/module-install-catalog.json").read_text(encoding="utf-8")
    )
    if data["schema_version"] != 1:
        raise ValueError("Unsupported catalog schema")
    for name, item in data["modules"].items():
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in name):
            raise ValueError("Invalid module name")
        for path in [*item["requirements"], item["manual"], item["automated"]]:
            resolved = (ROOT / path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
                raise ValueError("Catalog references a missing or external file")
        if any(dep not in data["modules"] for dep in item["depends_on"]):
            raise ValueError("Unknown dependency")
    return data


def plan(data: dict, selected: list[str], profile: str | None = None) -> dict:
    """Expand only declared dependencies; a plan performs no installation or service calls."""
    requested = list(dict.fromkeys([*data["profiles"].get(profile, []), *selected]))
    if profile and profile not in data["profiles"]:
        raise ValueError("Unknown profile")
    if not requested:
        raise ValueError("Choose --modules or --profile; there is no install-everything default")
    ordered, visiting = [], set()

    def visit(name: str) -> None:
        if name not in data["modules"]:
            raise ValueError(f"Unknown module: {name}")
        if name in visiting:
            raise ValueError("Module dependency cycle")
        if name in ordered:
            return
        visiting.add(name)
        for dependency in data["modules"][name]["depends_on"]:
            visit(dependency)
        visiting.remove(name)
        ordered.append(name)

    for name in requested:
        visit(name)
    return {
        "schema_version": 1,
        "requested": requested,
        "host": platform.system(),
        "scope": "Selected Python dependencies only; services and capabilities are not verified",
        "modules": [
            {"id": name, "added_dependency": name not in requested, **data["modules"][name]}
            for name in ordered
        ],
    }


def interpreter(directory: Path, windows: bool) -> Path:
    """Virtual environments are per module and per device, never copied between systems."""
    return directory / ("Scripts/python.exe" if windows else "bin/python")


def data_root() -> Path:
    """Desktop bundles keep environments outside their versioned installer resources."""
    return Path(os.environ.get("HCP_MODULE_DATA_ROOT", str(ROOT)))


@contextmanager
def installation_lock():
    """One installer per data directory, including across the two desktop apps."""
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".module-install.lock").open("a+b") as lock:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("Another module installation is running; wait and retry") from exc
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def install(selection: dict, report_directory: Path | None = None) -> dict:
    """Serialize installs across CLI and desktop callers without blocking other checks."""
    with installation_lock():
        return _install(selection, report_directory)


def _install(selection: dict, report_directory: Path | None = None) -> dict:
    """Install selected requirements in isolated environments and retain per-module results."""
    state = data_root() / "output/module-setup"
    state.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    run_dir = report_directory or state / stamp
    run_dir.mkdir()
    result = {
        "status": "running",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "selection": selection,
        "modules": [],
    }
    path = run_dir / "report.json"

    def save() -> None:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    save()
    for item in selection["modules"]:
        entry = {
            "id": item["id"],
            "capability_status": "not_verified",
            "remaining": item["remaining"],
            "manual": item["manual"],
            "dependencies": "manual_only" if not item["requirements"] else "installing",
        }
        result["modules"].append(entry)
        save()
        if not item["requirements"]:
            continue
        destination = data_root() / ".venv-modules" / item["id"]
        executable = interpreter(destination, os.name == "nt")
        try:
            sys.stdout.write(f"Installing {item['id']} Python dependencies...\n")
            sys.stdout.flush()
            if not destination.exists():
                venv.EnvBuilder(with_pip=True).create(destination)
            if not executable.is_file():
                raise RuntimeError("Existing module environment has no interpreter")
            command = [str(executable), "-m", "pip", "install"]
            for requirement in item["requirements"]:
                command.extend(["-r", str(ROOT / requirement)])
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            with (run_dir / f"{item['id']}.log").open("w", encoding="utf-8") as log:
                subprocess.run(
                    [str(executable), "-c", "import sys; assert sys.version_info >= (3,11)"],
                    check=True,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=30,
                    env=env,
                )
                subprocess.run(
                    command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=1800, env=env
                )
            entry["dependencies"] = "installed"
            entry["interpreter"] = str(executable)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            entry["dependencies"] = "failed"
            entry["error_type"] = type(exc).__name__
        finally:
            save()
    result["status"] = (
        "failed"
        if any(x["dependencies"] == "failed" for x in result["modules"])
        else "action_required"
    )
    save()
    sys.stdout.write(
        f"Setup report: {path}\nDependencies installed are not proof that a module is ready. Follow the report's manual guides.\n"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="show all modules and optional starter profiles")
    for command in ("plan", "install", "doctor"):
        child = sub.add_parser(
            command,
            help="preview selection"
            if command == "plan"
            else "install only selected Python dependencies",
        )
        child.add_argument("--modules", nargs="+", default=[], help="module IDs from list")
        child.add_argument("--profile", help="starter profile; optional modules are additive")
        if command == "install":
            child.add_argument("--report-directory", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        data = catalog()
        if args.command == "list":
            for name, item in data["modules"].items():
                mode = "Python deps + manual steps" if item["requirements"] else "manual setup"
                sys.stdout.write(f"{name}: {mode}\n  {item['remaining']}\n")
            sys.stdout.write("Profiles: " + ", ".join(data["profiles"]) + "\n")
        else:
            selection = plan(data, args.modules, args.profile)
            if args.command == "plan":
                sys.stdout.write(json.dumps(selection, indent=2) + "\n")
            elif args.command == "doctor":
                from module_readiness import doctor

                sys.stdout.write(json.dumps(doctor(ROOT, selection, data_root()), indent=2) + "\n")
            else:
                if sys.version_info < (3, 11) or sys.platform not in {"win32", "darwin"}:
                    raise ValueError("Install requires Python 3.11+ on Windows or macOS")
                return 1 if install(selection, args.report_directory)["status"] == "failed" else 0
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        sys.stderr.write(f"Module setup failed: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
