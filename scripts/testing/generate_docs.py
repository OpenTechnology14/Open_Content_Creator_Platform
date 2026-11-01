"""Generate/check agent instructions and canonical documentation data; no service actions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from proposal_report import report

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_START = "<!-- BEGIN GENERATED MODULE PROPOSAL REFERENCES -->"
REFERENCE_END = "<!-- END GENERATED MODULE PROPOSAL REFERENCES -->"
MARKER = "<!-- Generated from CLAUDE.md by scripts/testing/generate_docs.py; edit the source, then regenerate. -->\n"
PATH_TRIGGERS = "\n## Path triggers"


def agent_text(source: str) -> str:
    """Convert self-identification only; preserve all policy and third-party Claude references."""
    if not source.startswith("# CLAUDE.md — Open Content Creator Platform\n"):
        raise ValueError("unexpected canonical instruction header")
    body = source.replace("# CLAUDE.md —", "# AGENTS.md —", 1)
    body = body.replace("This file gives Claude (", "This file gives Codex (", 1)
    body = body.replace("├── CLAUDE.md", "├── AGENTS.md", 1)
    body = body.replace("## 9. Working With Claude in This Repo", "## 9. Working With Codex in This Repo", 1)
    return MARKER + body


def update_rules(source: str) -> list[dict]:
    """Snapshot the readable rules without inventing semantic change detection."""
    rows = []
    seen = set()
    for line in source.partition(PATH_TRIGGERS)[0].splitlines():
        if not re.match(r"^\| `DM-[A-Z-]+` \|", line):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) != 4 or cells[0] in seen:
            raise ValueError("malformed or duplicate documentation update rule")
        seen.add(cells[0])
        rows.append(dict(zip(["id", "trigger", "references", "rationale"], cells)))
    if len(rows) < 10:
        raise ValueError("documentation rule tripwire: fewer than 10 rules")
    return rows


def path_triggers(source: str, known: set[str]) -> dict[str, list[str]]:
    """Read the `## Path triggers` table: rule ID to glob patterns for scripts/testing/doc_advisory.py.

    The patterns are data, not detection: a rule without a row never fires in the advisory. A row for an
    unknown or repeated rule, an empty row, or a row with no include pattern is an error, not a silent skip.
    """
    _, found, tail = source.partition(PATH_TRIGGERS)
    triggers: dict[str, list[str]] = {}
    if not found:
        return triggers
    for line in tail.split("\n## ", 1)[0].splitlines():
        if not re.match(r"^\| `DM-[A-Z-]+` \|", line):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        rule = cells[0].strip("`")
        patterns = re.findall(r"`([^`]+)`", cells[1]) if len(cells) == 2 else []
        if rule not in known or rule in triggers or not patterns:
            raise ValueError(f"malformed, unknown or duplicate path trigger: {cells[0]}")
        if all(pattern[0] == "!" for pattern in patterns):
            raise ValueError(f"path trigger for {rule} has no include pattern")
        triggers[rule] = patterns
    return triggers


def module_statuses(source: str) -> list[dict[str, str]]:
    """Read the canonical module table; reject malformed/missing inventory."""
    section = source.split("## 11. Module Status", 1)[1].split("## 12.", 1)[0]
    rows = []
    seen = set()
    for line in section.splitlines():
        match = re.fullmatch(r"\| ([a-z][a-z0-9-]+) \| (.+) \| (scaffolded|implemented|production) \|", line)
        if not match:
            continue
        if match[1] in seen:
            raise ValueError("duplicate module status")
        seen.add(match[1])
        rows.append({"module": match[1], "labels": match[2], "status": match[3]})
    if len(rows) < 21:
        raise ValueError("module inventory tripwire: fewer than 21 modules")
    return rows


def outputs(root: Path) -> dict[Path, str]:
    """Build all content before writing; use canonical sources and stable normalized text."""
    paths = ["CLAUDE.md", "docs/PROPOSALS.md", "docs/todo/README.md", "docs/agent/DOC-UPDATE-MATRIX.md"]
    sources = {path: (root / path).read_text(encoding="utf-8") for path in paths}
    proposal_data = report(sources[paths[1]], sources[paths[2]])
    if proposal_data["lane_missing"] or proposal_data["lane_extra"]:
        raise ValueError("unfinished queue and lane IDs disagree")
    modules = module_statuses(sources[paths[0]])
    known = {row["id"] for row in proposal_data["proposals"]}
    references = []
    table = [REFERENCE_START, "", "## Generated module-owned proposal references", "",
             "Explicit references in module README/setup documents; these are discovery links,",
             "not inferred implementation ownership or evidence of completion.", "",
             "| Module | Explicit proposal references |", "|---|---|"]
    for module in modules:
        found = set()
        for suffix in ["README.md", "setup/manual.md", "setup/automated.md"]:
            relative = f"modules/{module['module']}/{suffix}"
            text = (root / relative).read_text(encoding="utf-8")
            sources[relative] = text
            found.update(re.findall(r"\bP-\d{3}\b", text))
        unknown = found - known
        if unknown:
            raise ValueError(f"unregistered module proposal references: {sorted(unknown)}")
        references.append({"module": module["module"], "proposals": sorted(found)})
        links = ", ".join(f"[{item}](PROPOSALS.md)" for item in sorted(found)) or "—"
        table.append(f"| [{module['module']}](../modules/{module['module']}/README.md) | {links} |")
    table.extend(["", REFERENCE_END])
    crosswalk = (root / "docs/PROJECT_CROSSWALK.md").read_text(encoding="utf-8")
    block = "\n".join(table)
    if REFERENCE_START in crosswalk:
        if REFERENCE_END not in crosswalk:
            raise ValueError("unterminated generated reference block")
        crosswalk = crosswalk.split(REFERENCE_START, 1)[0] + block + crosswalk.split(REFERENCE_END, 1)[1]
    else:
        crosswalk = crosswalk.rstrip() + "\n\n" + block + "\n"
    sources["docs/PROJECT_CROSSWALK.md"] = crosswalk
    rules = update_rules(sources[paths[3]])
    triggers = path_triggers(sources[paths[3]], {rule["id"].strip("`") for rule in rules})
    for rule in rules:
        rule["paths"] = triggers.get(rule["id"].strip("`"), [])
    data = {
        "schema_version": 1,
        "source_sha256": {path: hashlib.sha256(text.encode()).hexdigest() for path, text in sources.items()},
        "proposals": proposal_data,
        "module_statuses": modules,
        "module_proposal_references": references,
        "documentation_update_rules": rules,
    }
    return {
        root / "AGENTS.md": agent_text(sources[paths[0]]),
        root / "docs/PROJECT_CROSSWALK.md": crosswalk,
        root / "docs/agent-registries/documentation.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    }


def synchronize(root: Path, write: bool) -> list[str]:
    """Return drift paths; overwrite only explicit generated targets when --write is selected."""
    generated = outputs(root)
    for path in generated:
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("generated target escapes repository")
    drift = []
    for path, text in generated.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == text:
            continue
        drift.append(str(path.relative_to(root)))
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".generated-tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(path)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        drift = synchronize(ROOT, args.write)
    except (ValueError, OSError, KeyError, IndexError) as exc:
        sys.stderr.write(f"Documentation generation failed: {exc}\n")
        return 2
    if drift:
        sys.stdout.write(("Updated: " if args.write else "Stale generated documents: ") + ", ".join(drift) + "\n")
    else:
        sys.stdout.write("Generated documentation matches canonical sources.\n")
    return int(bool(drift) and not args.write)


if __name__ == "__main__":
    raise SystemExit(main())
