"""Social Management command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .connections import disconnect_connection
from . import editorial_cli
from .http import HttpTransport
from .jobs import execute_job, plan_job
from .models import Destination, PublishJob, SocialProfile
from .profiles import ProfileStore
from .registry import load_catalog, profile_options, provider_options
from .ui import serve
from .vault import ConnectionStore, KeyringVault


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage creator identities and social accounts")
    parser.add_argument("--catalog", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    editorial_cli.add_parser(sub)
    profiles = sub.add_parser("profiles", help="Print profile and brand dropdown options")
    profiles.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    providers = sub.add_parser("providers", help="Print destinations for one profile")
    providers.add_argument("profile_id")
    providers.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    add_profile = sub.add_parser("profile-add", help="Create or update a local profile")
    add_profile.add_argument("--id", required=True)
    add_profile.add_argument("--name", required=True)
    add_profile.add_argument("--kind", choices=["stream", "content", "hybrid"], required=True)
    add_profile.add_argument("--brand", action="append", required=True)
    add_profile.add_argument("--default-brand", required=True)
    add_profile.add_argument("--show-profile", action="append", default=[])
    add_profile.add_argument(
        "--destination", action="append", required=True, help="provider=capability,capability"
    )
    add_profile.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    remove_profile = sub.add_parser("profile-remove", help="Remove a local profile")
    remove_profile.add_argument("profile_id")
    remove_profile.add_argument("--confirm", required=True)
    remove_profile.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    connections = sub.add_parser("connections", help="Print redacted connected-account metadata")
    connections.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    plan = sub.add_parser("plan", help="Write a reviewable publication/live job")
    plan.add_argument("--connection", required=True)
    plan.add_argument(
        "--capability",
        required=True,
        choices=["post-text", "post-image", "post-video", "live-stream"],
    )
    plan.add_argument("--brand", required=True)
    plan.add_argument("--text")
    plan.add_argument("--media", type=Path)
    plan.add_argument("--visibility", choices=["private", "unlisted", "public"], default="private")
    plan.add_argument("--ai-generated", action="store_true")
    plan.add_argument("--approve", action="store_true")
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    publish = sub.add_parser("publish", help="Execute one approved job")
    publish.add_argument("job", type=Path)
    publish.add_argument("--confirm", required=True)
    publish.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    disconnect = sub.add_parser("disconnect", help="Remove one local account connection")
    disconnect.add_argument("connection_id")
    disconnect.add_argument("--confirm", required=True)
    disconnect.add_argument(
        "--state-dir", type=Path, default=Path.home() / ".hybrid-creator-platform" / "social"
    )
    ui = sub.add_parser("serve", help="Open the loopback-only account picker")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument("--no-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "portfolio":
        return editorial_cli.run(args)
    base_catalog = load_catalog(args.catalog) if args.catalog else load_catalog()
    state_dir = getattr(args, "state_dir", Path.home() / ".hybrid-creator-platform" / "social")
    profile_store = ProfileStore(state_dir / "profiles.json", base_catalog)
    catalog = profile_store.catalog()
    if args.command == "profiles":
        _write_json(profile_options(catalog))
    elif args.command == "providers":
        _write_json(provider_options(catalog, args.profile_id))
    elif args.command == "profile-add":
        destinations = [_parse_destination(value) for value in args.destination]
        profile = SocialProfile(
            id=args.id,
            display_name=args.name,
            kind=args.kind,
            brand_ids=args.brand,
            default_brand_id=args.default_brand,
            show_profile_ids=args.show_profile,
            destinations=destinations,
        )
        profile_store.put(profile)
        _write_json({"saved": profile.id})
    elif args.command == "profile-remove":
        if args.confirm != args.profile_id:
            raise ValueError("profile removal requires the exact profile ID")
        if any(
            item.profile_id == args.profile_id
            for item in ConnectionStore(args.state_dir / "connections.json").read()
        ):
            raise ValueError("disconnect this profile's accounts before removing it")
        profile_store.delete(args.profile_id)
        _write_json({"removed": args.profile_id})
    elif args.command == "connections":
        records = ConnectionStore(args.state_dir / "connections.json").read()
        _write_json([item.model_dump(mode="json") for item in records])
    elif args.command == "plan":
        records = {
            item.id: item for item in ConnectionStore(args.state_dir / "connections.json").read()
        }
        if args.connection not in records:
            raise ValueError("unknown connection")
        job = plan_job(
            catalog,
            records[args.connection],
            capability=args.capability,
            brand_id=args.brand,
            text=args.text,
            media_path=args.media,
            visibility=args.visibility,
            approved=args.approve,
            ai_generated=args.ai_generated,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(job.model_dump_json(indent=2), encoding="utf-8")
        args.output.chmod(0o600)
        _write_json({"job_id": job.id, "approved": job.approved, "path": str(args.output)})
    elif args.command == "publish":
        job = PublishJob.model_validate_json(args.job.read_text(encoding="utf-8"))
        store = ConnectionStore(args.state_dir / "connections.json")
        connections = {item.id: item for item in store.read()}
        if job.connection_id not in connections:
            raise ValueError("job connection is no longer available")
        result = execute_job(
            catalog,
            job,
            confirmation=args.confirm,
            connection=connections[job.connection_id],
            vault=KeyringVault(),
            http=HttpTransport(),
        )
        _write_json(result)
    elif args.command == "disconnect":
        if args.confirm != args.connection_id:
            raise ValueError("disconnect requires the exact connection ID")
        store = ConnectionStore(args.state_dir / "connections.json")
        disconnect_connection(
            connection_id=args.connection_id, vault=KeyringVault(), store=store
        )
        _write_json({"disconnected": args.connection_id})
    elif args.command == "serve":
        try:
            serve(port=args.port, open_browser=not args.no_browser)
        except KeyboardInterrupt:
            return 0
    return 0


def _write_json(value: object) -> None:
    sys.stdout.write(json.dumps(value, indent=2) + "\n")


def _parse_destination(value: str) -> Destination:
    provider_id, separator, capability_text = value.partition("=")
    capabilities = [item.strip() for item in capability_text.split(",") if item.strip()]
    if not separator or not capabilities:
        raise ValueError("destination must use provider=capability,capability")
    if "account-read" not in capabilities:
        capabilities.insert(0, "account-read")
    return Destination(
        provider_id=provider_id,
        capabilities=capabilities,
        account_label=f"{provider_id} account",
    )
