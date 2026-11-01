"""Select automatic/manual highlights or render a reviewed plan from a local recording."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import ClipPlan, ShortsJob
from .selector import select_clips


def read_json(path: Path) -> dict:
    """Bound operator artifact size before parsing it."""
    with path.open(encoding="utf-8") as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("input exceeds 16 MiB")
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    select = sub.add_parser(
        "select", help="print a clip plan from interactions and manual sections"
    )
    select.add_argument("--job", type=Path, required=True)
    render = sub.add_parser("render", help="render a clip plan to a NEW local output directory")
    render.add_argument("--plan", type=Path, required=True)
    render.add_argument("--source", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    review = sub.add_parser("review", help="write a local video scrub/selection page")
    review.add_argument("--plan", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    produce = sub.add_parser(
        "produce", help="select and render Shorts automatically for one recording"
    )
    produce.add_argument("--job", type=Path, required=True)
    produce.add_argument("--source", type=Path, required=True)
    produce.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "select":
            output = select_clips(ShortsJob.model_validate(read_json(args.job))).model_dump()
        elif args.command == "review":
            from .review import write_review

            write_review(ClipPlan.model_validate(read_json(args.plan)), args.output)
            output = {"review": str(args.output.resolve()), "published": False}
        else:
            from .render import render_plan

            plan = (
                select_clips(ShortsJob.model_validate(read_json(args.job)))
                if args.command == "produce"
                else ClipPlan.model_validate(read_json(args.plan))
            )
            output = render_plan(plan, args.source, args.output)
        sys.stdout.write(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:
        # Do not echo paths, source contents or command diagnostics into platform chat/logs.
        sys.stderr.write(f"Shorts {args.command} failed: {type(exc).__name__}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
