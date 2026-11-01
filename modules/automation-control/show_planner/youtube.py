"""Compile an approval-gated YouTube handoff without uploading or publishing media."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .planner import Program, load_program

ROOT = Path(__file__).resolve().parents[3]


def compile_youtube_plan(
    program: Program,
    *,
    profile_id: str,
    source_ref: str,
    media_path: Path,
    title: str,
    source_artifact_path: Optional[Path] = None,
    rights_confirmed: bool = False,
    approved: bool = False,
    workspace_root: Path = ROOT,
) -> dict:
    """Return a fixed, local-file-only handoff for a future YouTube upload adapter."""
    profile = next((item for item in program.profiles if item.id == profile_id), None)
    if profile is None or profile.youtube is None:
        raise ValueError("profile does not define a YouTube workflow")
    if source_ref not in profile.source.allowed_refs:
        raise ValueError("source is outside the profile allowlist")
    if profile.source.rights_confirmation_required and not rights_confirmed:
        raise ValueError("rights confirmation is required for this profile")
    artifact = None
    if profile.source.kind == "marketing-crosswalk":
        if source_artifact_path is None or profile.source.artifact_root is None:
            raise ValueError("marketing profile requires a Crosswalk source artifact")
        artifact = source_artifact_path.expanduser().resolve()
        allowed_root = (workspace_root.resolve() / profile.source.artifact_root).resolve()
        if (
            not artifact.is_file()
            or artifact.suffix.lower() != ".md"
            or not artifact.is_relative_to(allowed_root)
            or not any(
                artifact.name.startswith(prefix)
                for prefix in profile.source.artifact_prefixes[source_ref]
            )
        ):
            raise ValueError("source artifact is outside the configured Crosswalk scope")
    elif source_artifact_path is not None:
        raise ValueError("source artifact applies only to a marketing profile")
    media = media_path.expanduser().resolve()
    if not media.is_file():
        raise ValueError("media must be an existing local file")
    clean_title = title.strip()
    if not 1 <= len(clean_title) <= 100:
        raise ValueError("title must contain 1–100 characters")
    workflow = profile.youtube
    return {
        "schema_version": 1,
        "profile_id": profile.id,
        "profile_name": profile.display_name,
        "profile_kind": profile.kind,
        "persona_id": profile.persona_id,
        "audio_policy": profile.audio_policy,
        "marketing_module": (
            {
                "id": profile.marketing_module_id,
                "target": profile.marketing_target,
            }
            if profile.marketing_module_id is not None
            else None
        ),
        "source": {
            "kind": profile.source.kind,
            # For marketing-crosswalk profiles, `ref` is the registered module ID.
            "ref": source_ref,
            "media_path": str(media),
            "rights_confirmed": rights_confirmed,
            "artifact_path": str(artifact) if artifact is not None else None,
        },
        "destination": {
            "platform": "youtube",
            "workflow_id": workflow.workflow_id,
            "channel_env": workflow.channel_env,
            "visibility": workflow.visibility,
        },
        "title": clean_title,
        "approval": {"required": True, "approved": approved},
        "upload_enabled": False,
        "status": "approved-draft" if approved else "awaiting-approval",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/local/stream-programming.yaml"
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--media", required=True, type=Path)
    parser.add_argument("--source-artifact", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--rights-confirmed", action="store_true")
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    try:
        plan = compile_youtube_plan(
            load_program(args.config),
            profile_id=args.profile,
            source_ref=args.source,
            media_path=args.media,
            title=args.title,
            source_artifact_path=args.source_artifact,
            rights_confirmed=args.rights_confirmed,
            approved=args.approved,
        )
        sys.stdout.write(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
        return 0
    except (OSError, ValueError, ValidationError) as exc:
        sys.stderr.write(f"YouTube plan failed: {type(exc).__name__}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
