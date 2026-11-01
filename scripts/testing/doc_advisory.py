"""List the documentation-update rules a change fires, from the files it touches. Advises; never blocks.

    python3 scripts/testing/doc_advisory.py              # working tree against origin/main
    python3 scripts/testing/doc_advisory.py --base REF   # against another ref
    python3 scripts/testing/doc_advisory.py --json       # the same, as JSON

It reads the generated registry (docs/agent-registries/documentation.json), whose rules come from
docs/agent/DOC-UPDATE-MATRIX.md and carry the glob patterns of its "Path triggers" table. It maps paths,
not meaning: a rule with no patterns (a judgement about content) never fires here and stays on the author.
Read-only, offline and standard library only. It exits 0 whether or not a rule fired; exit 2 means it could
not run (not a git checkout, an unknown base, an unreadable registry).
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
REGISTRY = "docs/agent-registries/documentation.json"
DEFAULT_BASES = ("origin/main", "main")


class AdvisoryError(Exception):
    """The advisory could not run; distinct from "nothing fired"."""


@dataclass(frozen=True)
class Pattern:
    include: bool
    status: str  # "" any, "A" added only, "D" removed only
    regex: re.Pattern[str]

    def matches(self, status: str, path: str) -> bool:
        return bool(self.regex.match(path)) and (not self.status or self.status == status)


def glob_regex(glob: str) -> re.Pattern[str]:
    """`*` stays inside one path segment, `**` crosses directories, `**/` may match no directory at all."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def parse_pattern(text: str) -> Pattern:
    """`+glob` added only, `-glob` removed only, `!glob` excluded, `glob` any change."""
    if text[:1] == "!":
        return Pattern(False, "", glob_regex(text[1:]))
    if text[:1] == "+":
        return Pattern(True, "A", glob_regex(text[1:]))
    if text[:1] == "-":
        return Pattern(True, "D", glob_regex(text[1:]))
    return Pattern(True, "", glob_regex(text))


def rule_matches(patterns: list[str], changed: list[tuple[str, str]]) -> list[str]:
    """Paths among `changed` (status, path) that match an include pattern and no exclude pattern."""
    parsed = [parse_pattern(pattern) for pattern in patterns]
    includes = [p for p in parsed if p.include]
    excludes = [p for p in parsed if not p.include]
    return sorted({
        path for status, path in changed
        if any(p.matches(status, path) for p in includes) and not any(p.regex.match(path) for p in excludes)
    })


def git(root: Path, *args: str) -> str:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AdvisoryError(f"git {args[0]} failed: not a git checkout, or an unknown ref") from exc
    return done.stdout.decode("utf-8", "replace")


def resolve_base(root: Path, base: str | None) -> str:
    for candidate in ([base] if base else list(DEFAULT_BASES)):
        try:
            git(root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
            return candidate
        except AdvisoryError:
            continue
    raise AdvisoryError(f"base ref not found: {base or ' or '.join(DEFAULT_BASES)} (pass --base REF)")


def changed_files(root: Path, base: str) -> list[tuple[str, str]]:
    """(status, path) for the working tree against the merge-base with `base`; untracked files count as added."""
    fork = git(root, "merge-base", base, "HEAD").strip()
    fields = git(root, "diff", "--name-status", "--no-renames", "-z", fork).split("\0")
    changed = {path: status[0] for status, path in zip(fields[0::2], fields[1::2]) if status}
    for path in filter(None, git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")):
        changed.setdefault(path, "A")
    return sorted((status, path) for path, status in changed.items())


def load_rules(root: Path) -> list[dict]:
    try:
        return json.loads((root / REGISTRY).read_text(encoding="utf-8"))["documentation_update_rules"]
    except (OSError, ValueError, KeyError) as exc:
        raise AdvisoryError(f"cannot read {REGISTRY}: run generate_docs.py --write") from exc


def advise(root: Path, base: str | None) -> dict:
    resolved = resolve_base(root, base)
    changed = changed_files(root, resolved)
    rules = load_rules(root)
    fired = []
    for rule in rules:
        matched = rule_matches(rule.get("paths") or [], changed)
        if matched:
            fired.append({
                "rule": rule["id"].strip("`"),
                "trigger": rule["trigger"],
                "files": matched,
                "re_read": [item.strip() for item in rule["references"].split("<br>")],
            })
    judgement = sorted(rule["id"].strip("`") for rule in rules if not rule.get("paths"))
    return {"base": resolved, "changed": len(changed), "fired": fired, "never_fires_here": judgement}


def render(result: dict) -> str:
    lines = [f"Doc-update advisory: working tree against {result['base']}, {result['changed']} changed file(s)"]
    for item in result["fired"]:
        shown = item["files"][:4]
        more = f" and {len(item['files']) - 4} more" if len(item["files"]) > 4 else ""
        lines += ["", f"{item['rule']} — {item['trigger']}", f"  because of: {', '.join(shown)}{more}", "  re-read:"]
        lines += [f"    {entry}" for entry in item["re_read"]]
    if not result["fired"]:
        lines.append("No path-triggered rule fired.")
    judged = ", ".join(result["never_fires_here"])
    lines += ["", f"{len(result['fired'])} rule(s) fired. Advisory only: it maps paths, not meaning, so {judged or 'no rule'}"
                  " rest on the author. See docs/agent/DOC-UPDATE-MATRIX.md."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this checkout)")
    parser.add_argument("--base", help="ref to compare against (default: origin/main, then main)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)
    try:
        result = advise(args.root.resolve(), args.base)
    except AdvisoryError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2) + "\n" if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
