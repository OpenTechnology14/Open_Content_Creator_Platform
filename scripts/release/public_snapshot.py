"""Export committed source without private records, Git history or workstation state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


EXCLUDED = {"private", ".git", ".agent-workflows.json", ".gitleaksignore"}
SECRET_PATH = re.compile(
    r"(^|/)(\.env(?:\.(?!example$)[^/]*)?|id_rsa|id_ed25519|[^/]+\.(pem|key|p12|pfx))$",
    re.IGNORECASE,
)
PRIVATE_BLOCK = re.compile(
    r"^<!-- private-only:start -->\r?\n.*?^<!-- private-only:end -->[ \t]*$", re.S | re.M,
)
PRIVATE_MARKER = re.compile(r"^<!-- private-only:(?:start|end) -->[ \t]*$", re.M)


def git(source: Path, *args: str) -> bytes:
    """Read Git objects without invoking a shell or reading ignored working files."""
    return subprocess.run(
        ["git", "-C", str(source), *args], check=True, capture_output=True,
    ).stdout


def export_snapshot(source: Path, destination: Path, policy_path: Path, ref: str) -> dict:
    """Validate a committed tree fully before writing a new, history-free directory."""
    source = source.resolve()
    destination = destination.resolve()
    root = Path(git(source, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if destination == root or root in destination.parents:
        raise ValueError("destination must be outside the source checkout")
    if destination.exists():
        raise ValueError("destination already exists; choose a new directory")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    public_repo = policy["public_repo"]
    private_repo = policy["private_repo"]
    if not all(re.fullmatch(r"[\w.-]+/[\w.-]+", item) for item in (public_repo, private_repo)):
        raise ValueError("invalid repository name in private export policy")
    if public_repo == private_repo:
        raise ValueError("public and private repositories must differ")
    denied = [re.compile(pattern) for pattern in policy["deny_patterns"]]
    if not denied:
        raise ValueError("a reviewed personal-data deny list is required")
    commit = git(root, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
    commit = commit.decode().strip()
    records = git(root, "ls-tree", "-rz", "--full-tree", commit).split(b"\0")
    files: dict[str, tuple[bytes, bool]] = {}
    excluded = 0
    for raw in records:
        if not raw:
            continue
        metadata, name = raw.split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        relative = name.decode("utf-8")
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("unsafe tree path")
        if path.parts[0] in EXCLUDED:
            excluded += 1
            continue
        if any(part.lower() in {".git", "private"} for part in path.parts):
            raise ValueError("nested private or Git path cannot be exported")
        if SECRET_PATH.search(relative):
            raise ValueError("credential-like file cannot be exported")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("symlinks and submodules require separate public review")
        data = git(root, "cat-file", "blob", blob)
        if len(data) > 5 * 1024 * 1024:
            raise ValueError("file exceeds public source size limit")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is not None:
            text = PRIVATE_BLOCK.sub("", text)
            if PRIVATE_MARKER.search(text):
                raise ValueError("unbalanced private-only markers")
            # Private PRs, Actions runs and commits have no public counterparts.
            history_url = r"https://github\.com/" + re.escape(private_repo)
            history_url += r"/(?:pull|issues|actions|commit|compare)(?:/[^\s)<>]+)?"
            text = re.sub(
                r"\[([^\]]+)\]\(" + history_url + r"\)",
                r"\1 (private development evidence; not distributed)", text,
            )
            text = re.sub(history_url, "private development evidence (not distributed)", text)
            text = text.replace(private_repo, public_repo)
            for old, new in policy.get("replacements", {}).items():
                text = text.replace(old, new)
            data = text.encode("utf-8")
        # Latin-1 preserves every byte for checking binary metadata as well as text.
        inspection = relative + "\n" + data.decode("utf-8", errors="replace")
        binary_inspection = data.decode("latin-1")
        if any(pattern.search(inspection) or pattern.search(binary_inspection) for pattern in denied):
            raise ValueError("personal-data deny-list match; inspect the private source locally")
        files[relative] = (data, mode == "100755")
    if "README.md" not in files or "LICENSE" not in files:
        raise ValueError("source snapshot must retain its README and license")
    ignore, _ = files.get(".gitignore", (b"", False))
    files[".gitignore"] = (
        ignore.rstrip() + b"\n\n# Private operating records are never public source.\n/private/\n",
        False,
    )
    files["PUBLIC_SOURCE.md"] = (
        b"# Public source edition\n\n"
        b"Open Content Creator Platform is a pre-release source preview. This repository starts "
        b"with fresh history: no prior development PRs, issues, Actions logs, account matrix or "
        b"private operating records are copied. Historical development evidence described in "
        b"the docs is not a public PR archive or evidence that this repository ran those checks.\n\n"
        b"The source includes the social channel/concept controls and account setup guides. "
        b"Native/provider acceptance and production-release gates remain open. No installers, "
        b"model weights or credentials are distributed. Existing app IDs and local data paths "
        b"retain their compatibility names; the product is Open Content Creator Platform.\n\n"
        b"Keep local accounts and secrets outside Git. Use the account setup template with "
        b"a private inventory and password-manager references. See scripts/release/README.md "
        b"for the reviewed snapshot process and README.md for setup and license boundaries.\n",
        False,
    )
    # No output exists until the entire candidate passed the structural/privacy checks.
    destination.mkdir(parents=True, mode=0o700)
    for relative, (data, executable) in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if executable else 0o644)
    return {
        "schema_version": 1,
        "files_exported": len(files),
        "files_excluded": excluded,
        "history_exported": False,
        "provider_state_exported": False,
        "public_repo": public_repo,
        "files": {
            path: hashlib.sha256(value[0]).hexdigest() for path, value in sorted(files.items())
        },
    }


def main() -> int:
    """Run an export; secret scanning and public publishing are separate explicit steps."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.cwd())
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True, help="private reviewed JSON policy")
    args = parser.parse_args()
    try:
        report = export_snapshot(args.source, args.destination, args.policy, args.ref)
    except (ValueError, OSError, KeyError, TypeError, re.error, subprocess.CalledProcessError) as exc:
        # Policy/paths may be private: errors must never echo credentials or source contents.
        message = (
            str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError)
            else "invalid export inputs or unreadable source"
        )
        sys.stderr.write(f"Export failed: {message}\n")
        return 1
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
