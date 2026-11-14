"""Synthetic-only development smoke. Requires an explicit source path and expected hash."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import queue
import subprocess
import sys
import threading

from .safety import SafeRoot, canonical
from .platform_support import require_posix
from .sources import InputHandle
from .store import ProductionStore
from .worker import Worker


def run(source: Path, expected_sha256: str, output: Path, *, stdio: bool = False) -> dict:
    """Exercise every public command against a fresh task-owned root, retaining evidence."""
    require_posix()
    source = source.absolute()
    output.mkdir(parents=True, exist_ok=False)
    root = SafeRoot(output)
    source_root = SafeRoot(source.parent)
    handle = InputHandle.admit(
        source_root,
        source.name,
        expected_sha256,
        source_profile_id="stream-main",
        content_profile_id="content-main",
        origin="fixture",
    )
    worker = (
        None if stdio else Worker(ProductionStore(root, "fixture-root"), {"fixture-input": handle})
    )
    transcript = []
    events = []
    child = None
    replies = queue.Queue(maxsize=256)
    if stdio:
        registry = dict(
            schema_version=1,
            root_id="fixture-root",
            root_path=str(output),
            inputs={
                "fixture-input": dict(
                    parent=str(source.parent),
                    relative_path=source.name,
                    sha256=expected_sha256,
                    source_profile_id="stream-main",
                    content_profile_id="content-main",
                    origin="fixture",
                )
            },
        )
        registry_path = output / ".launcher-registry.json"
        descriptor = os.open(registry_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(descriptor, canonical(registry))
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "production_artifacts",
                    "--registry-fd",
                    str(descriptor),
                ],
                pass_fds=(descriptor,),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        finally:
            os.close(descriptor)

        def read_replies():
            while line := child.stdout.readline(1024 * 1024 + 2):
                replies.put(json.loads(line), timeout=5)

        threading.Thread(target=read_replies, daemon=True).start()

    def request(command: str, payload: dict) -> dict:
        envelope = dict(
            schema_version=1,
            request_id=f"req-{len(transcript):04d}",
            command=command,
            payload=payload,
        )
        if child:
            child.stdin.write(canonical(envelope) + b"\n")
            child.stdin.flush()
            while True:
                response = replies.get(timeout=180)
                if response.get("event") == "job.event.v1":
                    events.append(response["value"])
                elif response.get("request_id") == envelope["request_id"]:
                    break
                else:
                    raise RuntimeError("unexpected correlation")
        else:
            response = worker.handle(canonical(envelope))
        transcript.append(dict(command=command, response=response))
        if not response["ok"]:
            raise RuntimeError(response["error"]["code"])
        return response["value"]

    before = hashlib.sha256(source.read_bytes()).hexdigest()
    prod = request(
        "production.create",
        dict(
            operation_id="fixture-create",
            source_profile_id="stream-main",
            content_profile_id="content-main",
            show_profile_id="opentech",
            content_root_id="fixture-root",
            target=dict(
                kind="opentechnologyapp",
                commit="a" * 40,
                tree_sha256="b" * 64,
                fixture_sha256="c" * 64,
                scenario_id="synthetic-export-only",
            ),
        ),
    )
    imported = request(
        "source.register",
        dict(
            production_id=prod["production_id"],
            expected_revision=1,
            operation_id="fixture-source",
            input_id="fixture-input",
            source_sha256=expected_sha256,
            source_profile_id="stream-main",
            content_profile_id="content-main",
            origin="fixture",
        ),
    )
    source_dto = imported["source"]
    plan = request(
        "plan.register",
        dict(
            production_id=prod["production_id"],
            expected_revision=imported["revision"],
            operation_id="fixture-plan",
            source_id=source_dto["source_id"],
            title="Synthetic export fixture",
            description="Local test pattern and sine tone; not an App walkthrough.",
            metadata_revision=1,
            job=dict(
                schema_version=1,
                recording_id=source_dto["source_id"],
                session_id=prod["production_id"],
                game_id="walkthrough",
                show_id="opentech",
                duration_seconds=source_dto["duration_seconds"],
                automatic=False,
                manual_sections=[dict(start_seconds=2.0, end_seconds=10.0)],
                edit=dict(enabled=False),
            ),
        ),
    )
    started = request(
        "export.start",
        dict(
            production_id=prod["production_id"],
            expected_revision=plan["revision"],
            operation_id="fixture-export",
            source_id=source_dto["source_id"],
            source_sha256=expected_sha256,
            presets=["youtube-longform-v1", "youtube-shorts-v1", "tiktok-local-v1"],
            clip_plan_ref=plan["clip_plan_ref"],
            metadata_revision=1,
        ),
    )
    deadline = time.monotonic() + 180
    while True:
        status = request(
            "job.get", dict(production_id=prod["production_id"], job_id=started["job_id"])
        )
        if status["attempt"]["phase"] in {
            "complete",
            "partial",
            "failed",
            "cancelled",
            "interrupted",
        }:
            break
        if time.monotonic() > deadline:
            raise RuntimeError("smoke timed out")
        time.sleep(0.1)
    artifacts = []
    for artifact in status["attempt"]["artifacts"]:
        inspection = request(
            "artifact.inspect",
            dict(production_id=prod["production_id"], artifact_id=artifact["artifact_id"]),
        )
        artifacts.append(dict(path=str(output / artifact["relative_path"]), **inspection))
    evidence = dict(
        source_sha256_before=before,
        source_sha256_after=hashlib.sha256(source.read_bytes()).hexdigest(),
        status=status,
        artifacts=artifacts,
        transcript=transcript,
        events=events,
        transport="stdio" if stdio else "direct",
    )
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    handle.close()
    if child:
        child.stdin.close()
        child.wait(timeout=8)
        child.stdout.close()
        if child.returncode:
            raise RuntimeError("worker failed")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stdio", action="store_true", help="exercise the fixed worker process")
    args = parser.parse_args()
    result = run(args.source, args.sha256, args.output, stdio=args.stdio)
    os.write(
        1,
        canonical(dict(phase=result["status"]["attempt"]["phase"], artifacts=result["artifacts"]))
        + b"\n",
    )
    if (
        result["status"]["attempt"]["phase"] != "complete"
        or result["source_sha256_before"] != result["source_sha256_after"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
