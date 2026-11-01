#!/usr/bin/env python3
"""Bounded, local PNG still jobs. Blender runs this fixed script with arguments after --."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import time
import uuid
from typing import Any

try:
    import bpy
except ImportError:  # available only in Blender; offline tests inject a backend
    bpy = None


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, manifest: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def make_plan(backend: Any, output: Path, selected: list[str], job_id: str) -> dict:
    """Inspect a loaded project; never derive filenames from untrusted scene labels."""
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise ValueError("invalid job ID")
    if not backend.data.filepath or not Path(backend.data.filepath).is_file():
        raise ValueError("Save the Blender project before submitting a job")
    available = [scene.name for scene in backend.data.scenes]
    if len(available) > 256:
        raise ValueError("Project scene inventory exceeds 256 names")
    if len(selected) > 16 or len(selected) != len(set(selected)):
        raise ValueError("Choose 1–16 distinct scenes")
    for name in [*available, *selected]:
        if not name or len(name) > 120 or any(ord(c) < 32 or 127 <= ord(c) <= 159 or c in "\u2028\u2029" for c in name):
            raise ValueError("Scene label exceeds limits")
    if any(name not in available for name in selected):
        raise ValueError("A selected scene is missing")
    for name in selected:
        render = backend.data.scenes[name].render
        width = render.resolution_x * render.resolution_percentage // 100
        height = render.resolution_y * render.resolution_percentage // 100
        if not 1 <= width <= 4096 or not 1 <= height <= 4096:
            raise ValueError("Still jobs support at most 4096 pixels per dimension")
    root = output.resolve()
    if not root.is_dir():
        raise ValueError("Choose an existing output folder")
    folder = root / ("blender-" + job_id)
    if folder.exists():
        raise ValueError("Job attempt already exists; use a new job ID")
    return {
        "schema_version": 1, "job_id": job_id, "attempt_id": job_id,
        "status": "planned", "project": str(Path(backend.data.filepath).resolve()),
        "project_sha256": file_hash(Path(backend.data.filepath)), "output": str(folder),
        "available_scenes": available, "selected_scenes": selected,
        "format": "PNG stills", "upload_enabled": False,
        "created_at": timestamp(), "updated_at": timestamp(),
        "scenes": [{"name": name, "status": "queued", "artifact": None, "error": ""} for name in selected],
    }


def render_job(backend: Any, plan: dict, metadata: Path | None = None) -> dict:
    """Continue past a per-scene failure while retaining verified successful artifacts."""
    if not plan["selected_scenes"]:
        raise ValueError("Select at least one scene before rendering")
    folder = Path(plan["output"])
    metadata = metadata or folder / "job.json"
    if metadata.exists():
        previous = json.loads(metadata.read_text())
        if previous.get("job_id") != plan["job_id"]:
            raise ValueError("Metadata belongs to another job")
        plan["parent_job_id"] = previous.get("parent_job_id")
    folder.mkdir(exist_ok=False)
    plan["status"] = "running"
    write_manifest(metadata, plan)
    previous_scene = backend.context.window.scene if backend.context.window else None
    started = time.monotonic()
    try:
        for index, item in enumerate(plan["scenes"]):
            scene = backend.data.scenes[item["name"]]
            old_path, old_format = scene.render.filepath, scene.render.image_settings.file_format
            target = folder / f"{index:02}.png"
            item["status"] = "running"
            plan["updated_at"] = timestamp()
            write_manifest(metadata, plan)
            try:
                if backend.context.window:
                    backend.context.window.scene = scene
                scene.render.filepath = str(target)
                scene.render.image_settings.file_format = "PNG"
                backend.ops.render.render(write_still=True, scene=scene.name)
                with target.open("rb") as image:
                    header = image.read(24)
                    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                        raise ValueError("Renderer did not produce a PNG")
                width, height = struct.unpack(">II", header[16:24])
                if not 1 <= width <= 32768 or not 1 <= height <= 32768:
                    raise ValueError("Rendered dimensions exceed limits")
                item["artifact"] = {"file": target.name, "size_bytes": target.stat().st_size, "sha256": file_hash(target), "width": width, "height": height}
                item["status"] = "complete"
            except Exception as exc:
                item["status"], item["error"] = "failed", type(exc).__name__
            finally:
                scene.render.filepath, scene.render.image_settings.file_format = old_path, old_format
                plan["updated_at"] = timestamp()
                write_manifest(metadata, plan)
    finally:
        if backend.context.window and previous_scene is not None:
            backend.context.window.scene = previous_scene
    plan["status"] = "complete" if all(item["status"] == "complete" for item in plan["scenes"]) else "failed"
    plan["elapsed_seconds"] = round(time.monotonic() - started, 3)
    plan["updated_at"] = timestamp()
    write_manifest(metadata, plan)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scene", action="append", default=[])
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--source-sha256")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    try:
        if bpy is None:
            raise ValueError("This job must run inside Blender")
        plan = make_plan(bpy, args.output, args.scene, args.job_id or uuid.uuid4().hex)
        if args.source_sha256 and plan["project_sha256"] != args.source_sha256:
            raise ValueError("Project changed before rendering; inspect it again")
        if not args.dry_run:
            plan = render_job(bpy, plan, args.metadata)
        sys.stdout.write("HCP_JOB " + json.dumps(plan, ensure_ascii=False) + "\n")
        return int(plan["status"] == "failed")
    except Exception as exc:
        sys.stderr.write(f"Blender job failed ({type(exc).__name__})\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
