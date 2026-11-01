"""Hygiene checks that must hold before this repository is published; never authorizes a release.

    python3 scripts/testing/public_release_guard.py            # hygiene checks, exit 1 on a failure
    python3 scripts/testing/public_release_guard.py --release  # also fail on any owner-set placeholder

Read-only, offline and standard library only. It reads tracked files, so an ignored scratch file
cannot fail it. A value only the owner can supply is written ``[OWNER-SET: why]`` in the public
file that needs it; the default run lists those as PENDING and ``--release`` fails on them.

What it holds (docs/proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md, steps S01, S02, S04):

* no private registry row or target in the published crosswalk;
* no absolute home-directory path in a tracked text file;
* a root LICENSE whose SPDX id equals the ``license`` of every manifest that declares one;
* no tracked environment, key or certificate file.

It does not scan for secrets (use gitleaks, see the release checklist) and does not read history.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 1_500_000
SKIP_NAMES = {"package-lock.json", "Cargo.lock"}

REGISTRY_FILES = (
    "modules/marketing-crosswalk/crosswalk/modules.yml",
    "modules/marketing-crosswalk/crosswalk/targets.yml",
)
# A registry row or target key sits four spaces in; a comment or a subject-level entry does not match.
PRIVATE_ROW = re.compile(r"^ {4}(?:visibility:\s*private|kind:\s*internal-tool)\b")
HOME_PATH = re.compile(
    r"/Users/(?P<mac>[A-Za-z0-9._-]+)/"
    r"|[A-Za-z]:\\Users\\(?P<win>[A-Za-z0-9._-]+)\\"
    r"|/home/(?P<linux>[A-Za-z0-9._-]+)/"
)
# Account names that are placeholders or the well-known container and CI users, not a person.
GENERIC_HOMES = {
    "you", "user", "username", "name", "me", "example", "shared", "public", "default",
    "node", "runner", "ubuntu", "deploy", "app",
}
SECRET_FILE = re.compile(
    r"(^|/)(\.env|\.env\.(?!example$)[^/]*|id_rsa|id_ed25519|[^/]+\.(pem|key|p12|pfx|keystore))$",
    re.IGNORECASE,
)
OWNER_SET = re.compile(r"\[OWNER-SET\b[^\]]*\]")
# Prose that describes the marker puts it in code; the guard and its test must mention it to work at all.
CODE_SPAN = re.compile(r"`+[^`]*`+")
OWNER_SET_EXEMPT = {"scripts/testing/public_release_guard.py", "tests/docs/test_public_release_guard.py"}
CARGO_LICENSE = re.compile(r'^license\s*=\s*"([^"]+)"', re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    line: int
    text: str

    def render(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"{self.kind}: {where}: {self.text}"


def tracked_files(root: Path) -> list[str]:
    """Every tracked path. Fails loudly outside a git checkout rather than scanning nothing."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("not a git checkout: cannot list tracked files") from exc
    return sorted(rel for rel in out.decode("utf-8", "replace").split("\0") if rel)


def read_text(root: Path, rel: str) -> str | None:
    """Text of a tracked file, or None if it is missing, binary, a lockfile or too large."""
    path = root / rel
    if path.name in SKIP_NAMES or not path.is_file() or path.stat().st_size > MAX_BYTES:
        return None
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", "ignore")


def check_private_rows(root: Path, files: list[str]) -> list[Finding]:
    found = []
    for rel in REGISTRY_FILES:
        text = read_text(root, rel) if rel in files else None
        for number, line in enumerate((text or "").splitlines(), 1):
            if PRIVATE_ROW.match(line):
                found.append(Finding("private-row", rel, number, line.strip()))
    return found


def check_home_paths(root: Path, files: list[str]) -> list[Finding]:
    found = []
    for rel in files:
        text = read_text(root, rel)
        for number, line in enumerate((text or "").splitlines(), 1):
            for match in HOME_PATH.finditer(line):
                name = match["mac"] or match["win"] or match["linux"]
                if name.lower() not in GENERIC_HOMES:
                    found.append(Finding("home-path", rel, number, "absolute path to a personal account directory"))
                    break
    return found


def root_license(root: Path) -> str | None:
    """SPDX id of the root LICENSE, or None if it is absent or not a license this guard recognises."""
    path = root / "LICENSE"
    if not path.is_file():
        return None
    head = " ".join(path.read_text(encoding="utf-8", errors="ignore").split()[:12])
    if head.startswith("MIT License"):
        return "MIT"
    if "Apache License" in head and "Version 2.0" in head:
        return "Apache-2.0"
    return None


def manifest_license(root: Path, rel: str) -> str | None:
    text = read_text(root, rel)
    if text is None:
        return None
    if rel.endswith("Cargo.toml"):
        match = CARGO_LICENSE.search(text)
        return match.group(1) if match else None
    try:
        value = json.loads(text).get("license")
    except (ValueError, AttributeError):
        return None
    return value if isinstance(value, str) else None


def check_license(root: Path, files: list[str]) -> list[Finding]:
    spdx = root_license(root)
    if spdx is None:
        return [Finding("license", "LICENSE", 0, "missing, or not a license this guard recognises (MIT, Apache-2.0)")]
    found = []
    for rel in files:
        if not rel.endswith(("Cargo.toml", "package.json")):
            continue
        declared = manifest_license(root, rel)
        if declared is not None and declared != spdx:
            found.append(Finding("license", rel, 0, f"declares {declared!r}, root LICENSE is {spdx!r}"))
    return found


def check_secret_files(files: list[str]) -> list[Finding]:
    return [Finding("secret-file", rel, 0, "environment, key or certificate file is tracked")
            for rel in files if SECRET_FILE.search(rel)]


def pending_owner_set(root: Path, files: list[str]) -> list[Finding]:
    found = []
    for rel in files:
        if rel in OWNER_SET_EXEMPT:
            continue
        text = read_text(root, rel)
        for number, line in enumerate((text or "").splitlines(), 1):
            if OWNER_SET.search(CODE_SPAN.sub("", line)):
                found.append(Finding("owner-set", rel, number, line.strip()[:120]))
    return found


def run(root: Path) -> tuple[list[Finding], list[Finding]]:
    """(hygiene failures, owner-pending placeholders) for the tracked files under root."""
    files = tracked_files(root)
    failures = (
        check_private_rows(root, files) + check_home_paths(root, files)
        + check_license(root, files) + check_secret_files(files)
    )
    return failures, pending_owner_set(root, files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this checkout)")
    parser.add_argument("--release", action="store_true", help="also fail on any [OWNER-SET] placeholder")
    args = parser.parse_args(argv)
    try:
        failures, pending = run(args.root.resolve())
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    for finding in failures:
        sys.stdout.write(f"FAIL {finding.render()}\n")
    for finding in pending:
        sys.stdout.write(f"PENDING {finding.render()}\n")
    blocked = bool(failures) or (args.release and bool(pending))
    sys.stdout.write(
        f"{len(failures)} hygiene failure(s), {len(pending)} owner-set placeholder(s)"
        f"{' (release mode)' if args.release else ''}: {'NOT READY' if blocked else 'OK'}\n"
    )
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
