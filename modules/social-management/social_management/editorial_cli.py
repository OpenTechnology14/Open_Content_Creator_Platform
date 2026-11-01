"""AgentWorkflows-facing editorial controls. All operations are local."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from pydantic import ValidationError
import yaml

from .editorial import DEFAULT_CHANNELS, ConceptDraft, EditorialStore, load_channels
from .profiles import ProfileStore
from .registry import load_catalog
from .vault import ConnectionStore


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("portfolio", help="Local channel and concept approval controls")
    parser.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    parser.add_argument("--channels", type=Path, default=DEFAULT_CHANNELS)
    commands = parser.add_subparsers(dest="portfolio_command", required=True)
    commands.add_parser("channels", help="Show logical channels and local binding readiness")
    report = commands.add_parser("report", help="Read current editorial status for Agent reporting")
    report.add_argument("--format", choices=["json", "markdown"], default="json")
    submit = commands.add_parser("submit", help="Submit a source-backed concept for owner review")
    submit.add_argument("draft", type=Path)
    edit = commands.add_parser("edit", help="Replace a concept draft and invalidate prior approval")
    edit.add_argument("concept_id")
    edit.add_argument("draft", type=Path)
    edit.add_argument("--revision", type=int, required=True)
    decide = commands.add_parser("decide", help="Apply an explicit owner decision to one revision")
    decide.add_argument("concept_id")
    decide.add_argument("decision", choices=["approve", "reject", "revise"])
    decide.add_argument("--revision", type=int, required=True)
    decide.add_argument("--confirm", required=True, help="Exact concept-id@revision reviewed")
    decide.add_argument("--actor", required=True)
    decide.add_argument(
        "--reason", required=True, help="The owner's decision, not an inferred answer"
    )
    brief = commands.add_parser("brief", help="Read an approved production brief; never publish")
    brief.add_argument("concept_id")
    brief.add_argument("--revision", type=int, required=True)
    history = commands.add_parser("history", help="Read a concept's revisions and decision history")
    history.add_argument("concept_id")
    bind = commands.add_parser(
        "bind", help="Bind a channel to an existing local YouTube connection"
    )
    bind.add_argument("channel_id")
    bind.add_argument("connection_id")
    for name in ("unbind", "pause", "resume"):
        command = commands.add_parser(name, help=f"{name.capitalize()} one logical channel")
        command.add_argument("channel_id")


def _markdown(value: dict) -> str:
    # Escape all source-authored text. Reports are inert, not shell commands or HTML controls.
    def safe(text: str) -> str:
        return "".join(c if c.isalnum() or c in " .,:;!?()-/@" else f"&#{ord(c)};" for c in text)

    lines = [
        "# Social content report",
        "",
        f"Checked: {value['generated_at']}",
        "",
        "Publication: separate final approval required. Analytics: not connected.",
        "",
        "## Channels",
        "",
    ]
    for channel in value["channels"]:
        lines.append(
            f"- {safe(channel['name'])}: {channel['connection_state']}; "
            f"{'paused' if channel['paused'] else 'open for editorial work'}."
        )
    lines.extend(["", "## Concepts", ""])
    for item in value["concepts"]:
        draft = item["draft"]
        lines.extend(
            [
                f"- {item['id']}@{item['revision']} — {safe(draft['title'])}",
                f"  Channel: {safe(draft['channel_id'])}; {item['state']}; "
                f"configuration {'current' if item['configuration_current'] else 'changed'}.",
                f"  Hook: {safe(draft['hook'])}",
            ]
        )
    if not value["concepts"]:
        lines.append("No concepts submitted.")
    lines.extend(
        [
            "",
            "Use the current concept ID and revision when giving a decision. "
            "A report snapshot is not approval or a live control surface.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    try:
        base = load_catalog(args.catalog) if args.catalog else load_catalog()
        catalog = ProfileStore(args.state_dir / "profiles.json", base).catalog()
        store = EditorialStore(
            args.state_dir / "editorial.sqlite3", load_channels(catalog, args.channels)
        )
        connections = ConnectionStore(args.state_dir / "connections.json").read()
        command = args.portfolio_command
        if command in ("channels", "report"):
            report = store.report(connections)
            result = report["channels"] if command == "channels" else report
            if command == "report" and args.format == "markdown":
                sys.stdout.write(_markdown(report))
                return 0
        elif command in ("submit", "edit"):
            if args.draft.stat().st_size > 128_000:
                raise ValueError("concept file exceeds 128 KB")
            draft = ConceptDraft.model_validate_json(args.draft.read_text(encoding="utf-8"))
            result = (
                store.submit(draft)
                if command == "submit"
                else store.edit(args.concept_id, args.revision, draft)
            )
        elif command == "decide":
            result = store.decide(
                args.concept_id,
                args.revision,
                args.decision,
                actor=args.actor,
                reason=args.reason,
                confirmation=args.confirm,
            )
        elif command == "brief":
            result = store.brief(args.concept_id, args.revision)
        elif command == "history":
            result = store.history(args.concept_id)
        elif command == "bind":
            connection = next((item for item in connections if item.id == args.connection_id), None)
            if connection is None:
                raise ValueError("unknown connection; connect the account through Social first")
            store.bind(args.channel_id, connection)
            result = {"channel_id": args.channel_id, "state": "locally-bound"}
        elif command == "unbind":
            store.unbind(args.channel_id)
            result = {"channel_id": args.channel_id, "state": "unbound"}
        else:
            store.pause(args.channel_id, command == "pause")
            result = {"channel_id": args.channel_id, "paused": command == "pause"}
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
        return 0
    except yaml.YAMLError:
        error = "invalid channel YAML"
    except ValidationError as exc:
        # Pydantic's default rendering includes input values; keep those out of diagnostics.
        error = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    except (ValueError, OSError, sqlite3.Error) as exc:
        error = str(exc)
    sys.stderr.write(json.dumps({"error": error}) + "\n")
    return 2
