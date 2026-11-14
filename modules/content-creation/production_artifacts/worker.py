"""Fixed, bounded stdio worker. Registry configuration belongs to the native launcher."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import threading
from pydantic import ValidationError

from .exports import ExportRunner, register_plan
from .media import require_process_policy
from .platform_support import require_posix
from .models import ArtifactGet, Get, JobGet, Page, RequestV1
from .safety import MAX_JSON, Fault, SafeRoot, canonical, decode
from .sources import InputHandle, register_finalized_source
from .store import ProductionStore


class Worker:
    def __init__(
        self,
        store: ProductionStore,
        inputs: dict[str, InputHandle],
        runner: ExportRunner | None = None,
    ):
        self.store, self.inputs = store, inputs
        self.runner = runner or ExportRunner(store)
        self.import_owner = None

    def handle(self, raw: bytes) -> dict:
        request_id = None
        try:
            if len(raw) > MAX_JSON:
                raise Fault("limit_exceeded")
            request = RequestV1.model_validate(decode(raw))
            request_id = request.request_id
            payload = request.payload
            if request.command == "production.create":
                value = self.store.create(payload)
            elif request.command == "production.list":
                page = Page.model_validate(payload)
                self.runner.recover_if_available()
                value = self.store.list(**page.model_dump())
            elif request.command == "production.get":
                query = Get.model_validate(payload)
                self.runner.recover_if_available()
                value = self.store.get(query.production_id)
            elif request.command == "source.register":
                from .media import ProcessOwner

                self.import_owner = ProcessOwner()
                try:
                    value = register_finalized_source(
                        self.store, self.inputs, payload, self.import_owner
                    )
                finally:
                    self.import_owner = None
            elif request.command == "plan.register":
                value = register_plan(self.store, payload)
            elif request.command == "export.start":
                value = self.runner.start(payload)
            elif request.command == "job.get":
                value = self.runner.status(**JobGet.model_validate(payload).model_dump())
            elif request.command == "job.cancel":
                value = self.runner.cancel_request(payload)
            else:
                value = self.runner.inspect_artifact(
                    **ArtifactGet.model_validate(payload).model_dump()
                )
            reply = dict(request_id=request_id, ok=True, value=value)
            revision = value.get("revision")
            if revision is not None:
                reply["revision"] = revision
            if len(canonical(reply)) > MAX_JSON:
                raise Fault("limit_exceeded")
            return reply
        except (Fault, ValidationError, OSError, ValueError, RecursionError) as error:
            code = (
                error.code
                if isinstance(error, Fault)
                else "disk_unavailable"
                if isinstance(error, OSError)
                else "invalid_request"
            )
            return dict(
                request_id=request_id,
                ok=False,
                error=dict(
                    code=code,
                    retryable=code
                    in {"export_busy", "worker_busy", "disk_space", "dependency_unavailable"},
                ),
            )


def launch_registry(fd: int) -> Worker:
    """Inherited private descriptor only; request payloads cannot register roots/inputs.

    The native launcher must protect this registry and validate origin/pack/capture state.
    This function supplies filesystem isolation, never evidence of native authorization.
    """
    require_posix()
    require_process_policy()
    raw = os.read(fd, MAX_JSON + 1)
    registry = decode(raw)
    if (
        set(registry) != {"schema_version", "root_id", "root_path", "inputs"}
        or registry["schema_version"] != 1
    ):
        raise Fault("invalid_registry")
    if not isinstance(registry["inputs"], dict) or len(registry["inputs"]) > 100:
        raise Fault("invalid_registry")
    from pydantic import TypeAdapter
    from .models import ID, SHA

    TypeAdapter(ID).validate_python(registry["root_id"], strict=True)
    root = SafeRoot(Path(registry["root_path"]))
    inputs = {}
    for key, entry in registry["inputs"].items():
        TypeAdapter(ID).validate_python(key, strict=True)
        if not isinstance(entry, dict) or set(entry) != {
            "parent",
            "relative_path",
            "sha256",
            "source_profile_id",
            "content_profile_id",
            "origin",
        }:
            raise Fault("invalid_registry")
        TypeAdapter(SHA).validate_python(entry["sha256"], strict=True)
        for field in ["source_profile_id", "content_profile_id"]:
            TypeAdapter(ID).validate_python(entry[field], strict=True)
        if entry["origin"] not in {"manual", "fixture"}:
            raise Fault("invalid_registry")
        inputs[key] = InputHandle.admit(
            SafeRoot(Path(entry["parent"])),
            entry["relative_path"],
            entry["sha256"],
            source_profile_id=entry["source_profile_id"],
            content_profile_id=entry["content_profile_id"],
            origin=entry["origin"],
        )
    return Worker(ProductionStore(root, registry["root_id"]), inputs)


def serve(worker: Worker) -> None:
    """Bounded diagnostics lane leaves the reader available for status and cancellation."""
    import queue

    replies: queue.Queue[dict | None] = queue.Queue(maxsize=8)
    diagnostics: queue.Queue[bytes | None] = queue.Queue(maxsize=1)
    broken = threading.Event()
    finished = threading.Event()

    def enqueue(value: dict) -> None:
        try:
            replies.put(value, timeout=1)
        except queue.Full:
            broken.set()

    def write() -> None:
        try:
            while (reply := replies.get()) is not None:
                sys.stdout.buffer.write(canonical(reply) + b"\n")
                sys.stdout.buffer.flush()
        except (BrokenPipeError, OSError):
            broken.set()
            if worker.runner.owner:
                worker.runner.owner.cancel()

    def expensive() -> None:
        while not finished.is_set():
            try:
                raw = diagnostics.get(timeout=0.1)
            except queue.Empty:
                continue
            if raw is None:
                return
            enqueue(worker.handle(raw))

    def events() -> None:
        while not finished.wait(0.1):
            with worker.runner.event_lock:
                pending = worker.runner.events[:]
                worker.runner.events.clear()
            for event in pending:
                # Snapshot polling recovers dropped events; no unbounded replay log.
                try:
                    replies.put_nowait(dict(event="job.event.v1", value=event))
                except queue.Full:
                    break

    writer = threading.Thread(target=write, daemon=True)
    helpers = [
        threading.Thread(target=expensive, daemon=True),
        threading.Thread(target=events, daemon=True),
    ]
    writer.start()
    for helper in helpers:
        helper.start()
    try:
        while not broken.is_set():
            raw = sys.stdin.buffer.readline(MAX_JSON + 2)
            if not raw:
                break
            if len(raw) > MAX_JSON:
                enqueue(
                    dict(
                        request_id=None,
                        ok=False,
                        error=dict(code="limit_exceeded", retryable=False),
                    )
                )
                break
            try:
                command = decode(raw).get("command")
            except Fault:
                command = None
            if command in {"source.register", "artifact.inspect"}:
                try:
                    diagnostics.put_nowait(raw)
                except queue.Full:
                    request_id = decode(raw).get("request_id")
                    # Validate correlation even on the busy path; never echo arbitrary data.
                    from pydantic import TypeAdapter
                    from .models import ID

                    try:
                        request_id = TypeAdapter(ID).validate_python(request_id, strict=True)
                    except ValidationError:
                        request_id = None
                    enqueue(
                        dict(
                            request_id=request_id,
                            ok=False,
                            error=dict(code="worker_busy", retryable=True),
                        )
                    )
            else:
                enqueue(worker.handle(raw))
    finally:
        finished.set()
        if worker.import_owner:
            worker.import_owner.cancel()
        if worker.runner.owner:
            worker.runner.owner.cancel()
        if worker.runner.thread:
            worker.runner.thread.join(timeout=5)
        for helper in helpers:
            helper.join(timeout=5)
        if not broken.is_set():
            enqueue(None)
            writer.join(timeout=1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline production worker (trusted launcher only)"
    )
    parser.add_argument(
        "--registry-fd",
        type=int,
        required=True,
        help="inherited descriptor for private launcher registry, never a webview path",
    )
    args = parser.parse_args()
    try:
        worker = launch_registry(args.registry_fd)
        serve(worker)
    except Fault as error:
        sys.stderr.write(f"production worker initialization failed: {error.code}\n")
        raise SystemExit(2) from None
    except (OSError, ValueError, TypeError, ValidationError):
        sys.stderr.write("production worker initialization failed\n")
        raise SystemExit(2) from None
