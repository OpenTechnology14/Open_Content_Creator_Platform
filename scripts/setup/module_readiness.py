"""Read-only dependency evidence for the module setup UI; never marks whole modules ready."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

# Runs inside the selected module environment, isolated from the caller's Python paths.
PROBE = r"""
import json, sys
from importlib.metadata import version, PackageNotFoundError
from pip._vendor.packaging.requirements import Requirement
results=[]
for line in json.load(sys.stdin):
    req=Requirement(line)
    if req.marker and not req.marker.evaluate():
        continue
    try:
        installed=version(req.name)
        results.append({"package":req.name,"version":installed,"matches":installed in req.specifier})
    except PackageNotFoundError:
        results.append({"package":req.name,"version":None,"matches":False})
print(json.dumps(results))
"""


def check_packages(
    root: Path, module: str, requirements: list[str], environment_root: Path | None = None
) -> dict:
    """Check required versions and installed dependency consistency in the module's own venv."""
    executable = (
        (environment_root or root)
        / ".venv-modules"
        / module
        / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if not executable.is_file():
        return {
            "name": "Python dependencies",
            "status": "missing",
            "detail": "Install this module's Python dependencies first.",
        }
    declarations = []
    for requirement in requirements:
        for raw in (root / requirement).read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if line:
                declarations.append(line)
    try:
        result = subprocess.run(
            [str(executable), "-I", "-c", PROBE],
            input=json.dumps(declarations),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=15,
        )
        packages = json.loads(result.stdout)
        if not all(item["matches"] for item in packages):
            return {
                "name": "Python dependencies",
                "status": "missing",
                "detail": "Some required packages are missing or have different versions.",
                "packages": packages,
            }
        result = subprocess.run(
            [str(executable), "-I", "-m", "pip", "check"], capture_output=True, timeout=15
        )
        return {
            "name": "Python dependencies",
            "status": "passed" if result.returncode == 0 else "failed",
            "detail": "Required versions and dependency consistency checked."
            if result.returncode == 0
            else "Dependency conflicts detected; reinstall or review this environment.",
            "packages": packages,
        }
    except (OSError, ValueError, subprocess.SubprocessError):
        return {
            "name": "Python dependencies",
            "status": "failed",
            "detail": "Could not inspect this module environment; repair it and retry.",
        }


def check_tool(tool: dict) -> dict:
    """Presence is evidence of installation, never of a functioning device or integration."""
    key = "windows_paths" if os.name == "nt" else "macos_paths"
    found = any(shutil.which(command) for command in tool.get("commands", []))
    found = found or any(
        Path(os.path.expandvars(path)).expanduser().exists() for path in tool.get(key, [])
    )
    return {
        "name": tool["label"],
        "status": "passed" if found else "not_found",
        "detail": "Application found; live operation still needs verification."
        if found
        else "Not found in standard locations or PATH; it may be installed elsewhere.",
    }


def doctor(root: Path, selection: dict, environment_root: Path | None = None) -> dict:
    """Collect fresh local evidence only for selected modules and declared dependencies."""
    results = []
    for item in selection["modules"]:
        checks = []
        if item["requirements"]:
            checks.append(check_packages(root, item["id"], item["requirements"], environment_root))
        checks.extend(check_tool(tool) for tool in item.get("tools", []))
        results.append(
            {
                "id": item["id"],
                "capability_status": "not_verified",
                "checks": checks,
                "remaining": item["remaining"],
                "manual": item["manual"],
            }
        )
    return {
        "schema_version": 1,
        "checked_at": int(time.time()),
        "modules": results,
        "scope": "Dependency checks only. Models, devices, services and full module readiness require their own acceptance.",
    }
