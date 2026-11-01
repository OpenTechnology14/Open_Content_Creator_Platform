"""Command-line entry point for the marketing crosswalk.

    python3 -m generator.cli validate
    python3 -m generator.cli coverage [--module task-management]
    python3 -m generator.cli generate --subject pm_requests [--asset blog-brief] [--apply]

The Content Platform (this repository) generates content for the modules registered in
crosswalk/modules.yml. Dry-run is the default everywhere. `--apply` writes drafts into the
target repository's draft directory and never edits a hand-written marketing doc in place;
moving a draft into MARKETING.md is a human's decision, not this tool's.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from . import coverage as coverage_mod
from . import crosswalk as cx
from . import render as render_mod

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(levelname)s: %(message)s",
)
log = logging.getLogger("marketing-crosswalk")

MODULE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = MODULE_ROOT.parent.parent


def _load(args: argparse.Namespace) -> cx.Crosswalk:
    return cx.load(MODULE_ROOT, REPO_ROOT, target_path=args.target_path)


def _split(values: Optional[List[str]]) -> List[str]:
    """Accept both --asset a --asset b and --asset a,b."""
    out: List[str] = []
    for value in values or []:
        out.extend(part.strip() for part in value.split(",") if part.strip())
    return out


def _module_of(cw: cx.Crosswalk, requested: Optional[str]) -> str:
    if requested:
        cw.module(requested)  # raises with the known list if unregistered
        return requested
    if len(cw.modules) == 1:
        return cw.modules[0]["module"]
    known = ", ".join(m["module"] for m in cw.modules)
    raise cx.CrosswalkError(f"--module is required; registered modules: {known}")


def cmd_validate(args: argparse.Namespace) -> int:
    cw = _load(args)
    findings = cx.validate(cw)

    subject_total = sum(len(v) for v in cw.subjects.values())
    log.info("registry: %d module(s), %d subject(s), %d asset(s), %d ICP(s)",
             len(cw.modules), subject_total, len(cw.assets),
             sum(len(v) for v in cw.icps.values()))
    for entry in cw.modules:
        log.info("  %s -> %s at %s", entry["module"],
                 cw.targets[entry["target"]]["repo"], cw.target_paths.get(entry["target"]))

    if not findings:
        anchors = sum(
            len(doc.get("anchors", {}))
            for entry in cw.modules
            for doc in cw.targets[entry["target"]]["docs"].values()
        )
        log.info("verified: %d marketing-doc anchor(s) and %d status claim(s) still hold",
                 anchors, subject_total)
        log.info("OK — crosswalk matches both repositories")
        return 0

    log.error("%d finding(s):", len(findings))
    for finding in findings:
        print(finding.render(), file=sys.stderr)
    return 1 if cw.errors else 0


def cmd_coverage(args: argparse.Namespace) -> int:
    cw = _load(args)
    cx.validate(cw)
    if cw.errors and not args.force:
        log.error("%d validation error(s) — run `validate` first, or pass --force", len(cw.errors))
        return 1

    module = _module_of(cw, args.module)
    print(coverage_mod.format_report(cw, coverage_mod.build(cw, module), module))
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    cw = _load(args)
    cx.validate(cw)
    if cw.errors:
        log.error("%d validation error(s) — fix those first", len(cw.errors))
        for finding in cw.errors:
            print(finding.render(), file=sys.stderr)
        return 1

    pairs, failures = render_mod.selftest(cw)
    log.info("rendered %d subject/asset pair(s) in memory, ignoring claim gating "
             "(nothing written)", pairs)
    if failures:
        log.error("%d template failure(s):", len(failures))
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    log.info("OK — every template renders with no unfilled placeholders and no private links")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    cw = _load(args)
    if args.module and cw.module(args.module).get("visibility") == "private":
        log.error("module %s is private: it is registered for discovery only and never "
                  "generates content", args.module)
        return 2
    cx.validate(cw)
    if cw.errors and not args.force:
        log.error("%d validation error(s) — refusing to generate. Run `validate`, or pass --force.",
                  len(cw.errors))
        for finding in cw.errors:
            print(finding.render(), file=sys.stderr)
        return 1

    module = _module_of(cw, args.module)
    wanted = _split(args.subject)
    subjects = [cw.subject(module, s) for s in wanted] if wanted else cw.subjects.get(module, [])
    if not subjects:
        log.error("no subjects selected for module %s", module)
        return 1

    out_dir = Path(args.out).resolve() if args.out else (MODULE_ROOT / "out")
    if args.apply:
        target = cw.targets[cw.target_for(module)]
        out_dir = cw.target_paths[cw.target_for(module)] / target["draft_dir"]

    wanted_assets = _split(args.asset)
    written, blocked, failed = [], [], []

    for subject in subjects:
        for asset in render_mod.assets_for(cw, subject, wanted_assets):
            try:
                body = render_mod.render(cw, module, subject, asset)
            except render_mod.ClaimBlocked as exc:
                blocked.append((subject["id"], asset, str(exc)))
                continue
            except render_mod.RenderError as exc:
                failed.append((subject["id"], asset, str(exc)))
                continue

            path = out_dir / render_mod.draft_filename(module, subject, asset)
            if not args.dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
            written.append(path)

    log.info("%s %d draft(s) to %s", "would write" if args.dry_run else "wrote",
             len(written), out_dir)
    for path in written:
        log.info("  %s", path.name)

    if blocked:
        log.warning("%d asset(s) blocked by verified status:", len(blocked))
        for subject_id, asset, reason in blocked:
            print(f"\n  BLOCKED  {subject_id} → {asset}\n    " + reason.replace("\n", "\n    "),
                  file=sys.stderr)

    if failed:
        log.error("%d asset(s) failed to render:", len(failed))
        for subject_id, asset, reason in failed:
            print(f"  FAILED   {subject_id} → {asset}: {reason}", file=sys.stderr)
        return 1

    if args.apply and not args.dry_run:
        log.info("drafts written into %s — review and move them into the marketing docs by hand",
                 cw.targets[cw.target_for(module)]["repo"])

    return 1 if (blocked and args.strict) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="marketing-crosswalk",
        description="Generate marketing content from the Content Platform for the modules "
                    "registered in crosswalk/modules.yml.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--target-path", help="local checkout of the target repo "
                                              "(overrides $OPENTECHAPP_REPO_PATH)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="check the crosswalk against both repositories")
    p_validate.set_defaults(func=cmd_validate)

    p_coverage = sub.add_parser("coverage", help="content coverage, ledger gaps, blocked claims")
    p_coverage.add_argument("--module", help="registered module (default: the only one)")
    p_coverage.add_argument("--force", action="store_true", help="report even with validation errors")
    p_coverage.set_defaults(func=cmd_coverage)

    p_selftest = sub.add_parser(
        "selftest",
        help="render every template in memory, ignoring claim gating; writes nothing")
    p_selftest.set_defaults(func=cmd_selftest)

    p_generate = sub.add_parser("generate", help="render channel assets for a module's subjects")
    p_generate.add_argument("--module", help="registered module (default: the only one)")
    p_generate.add_argument("--subject", action="append",
                            help="subject id (repeatable or comma-separated)")
    p_generate.add_argument("--asset", action="append",
                            help="asset name (repeatable or comma-separated)")
    p_generate.add_argument("--out", help="output directory (default: modules/marketing-crosswalk/out)")
    p_generate.add_argument("--apply", action="store_true",
                            help="write into the target repo's draft dir instead of out/")
    p_generate.add_argument("--dry-run", action="store_true",
                            help="list what would be written, write nothing")
    p_generate.add_argument("--strict", action="store_true",
                            help="exit non-zero if any asset is blocked")
    p_generate.add_argument("--force", action="store_true",
                            help="generate even with validation errors")
    p_generate.set_defaults(func=cmd_generate)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (cx.CrosswalkError, render_mod.RenderError) as exc:
        log.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
