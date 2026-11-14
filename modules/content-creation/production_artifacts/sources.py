"""Explicit trusted input handles and independent immutable source snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import shutil

from .media import ProcessOwner, validate_fd
from .platform_support import require_posix
from .models import FinalizedSourceV1, SourceRegister, Validation, Media
from .safety import Fault, SafeRoot, identity
from .store import ProductionStore, dump, new_id, now


@dataclass
class InputHandle:
    """Launcher-only private registration. Never deserialized from worker requests."""

    root: SafeRoot
    relative_path: str
    fd: int
    expected_identity: tuple[int, ...]
    expected_sha256: str
    source_profile_id: str
    content_profile_id: str
    origin: str

    @classmethod
    def admit(
        cls,
        root: SafeRoot,
        relative_path: str,
        expected_sha256: str,
        *,
        source_profile_id: str,
        content_profile_id: str,
        origin: str,
    ) -> InputHandle:
        require_posix()
        fd = root.open(relative_path)
        return cls(
            root,
            relative_path,
            fd,
            identity(fd),
            expected_sha256,
            source_profile_id,
            content_profile_id,
            origin,
        )

    def check(self) -> None:
        try:
            current = self.root.open(self.relative_path)
            try:
                if (
                    identity(current) != self.expected_identity
                    or identity(self.fd) != self.expected_identity
                ):
                    raise Fault("source_changed")
            finally:
                os.close(current)
        except FileNotFoundError as error:
            raise Fault("source_unavailable") from error

    def close(self) -> None:
        os.close(self.fd)


def reserve(root: SafeRoot, source_bytes: int, output_bytes: int = 0) -> None:
    require_posix()
    estimate = source_bytes + output_bytes
    margin = max(1024**3, (estimate + 9) // 10)
    try:
        free = shutil.disk_usage(root.fd).free
    except OSError as error:
        raise Fault("disk_unavailable") from error
    if free < estimate + margin:
        raise Fault("disk_space")


def verify_published_snapshot(
    root: SafeRoot,
    directory: str,
    relative_path: str,
    copied: int,
    chain: tuple[tuple[int, int], ...],
    expected_bytes: int,
    expected_sha256: str,
    owner: ProcessOwner,
    stamp: tuple[int, ...] | None = None,
) -> tuple[Media | None, tuple[int, ...]]:
    """Bind final root path to the validated descriptor, never to the temporary name.

    Decode through the final no-follow path. The quick second call under ledger CAS
    checks the exact post-validation identity/stamp and all ancestors again.
    """
    try:
        if root.directory_chain(directory) != chain:
            raise Fault("source_changed")
        final = root.open(relative_path)
        try:
            current = identity(final)
            if current != identity(copied) or current[2] != expected_bytes:
                raise Fault("source_changed")
            if stamp is not None:
                if current != stamp:
                    raise Fault("source_changed")
                media = None
            else:
                media = validate_fd(owner, final, expected_sha256)
            if identity(final) != current or root.directory_chain(directory) != chain:
                raise Fault("source_changed")
            # Reopen after decode: a retained FD alone cannot prove the name still binds it.
            rebound = root.open(relative_path)
            try:
                if identity(rebound) != current:
                    raise Fault("source_changed")
            finally:
                os.close(rebound)
            return media, current
        finally:
            os.close(final)
    except (OSError, Fault) as error:
        raise Fault("source_changed") from error


def register_finalized_source(
    store: ProductionStore,
    inputs: dict[str, InputHandle],
    payload: dict,
    owner: ProcessOwner | None = None,
) -> dict:
    require_posix()
    request = SourceRegister.model_validate(payload)
    with store.locked() as state:
        replay = store.replay(state, request.operation_id, payload)
        if replay is not None:
            return replay
        prod = store.production(state, request.production_id)
        if prod.revision != request.expected_revision:
            raise Fault("revision_conflict")
        if (
            prod.source_profile_id != request.source_profile_id
            or prod.content_profile_id != request.content_profile_id
        ):
            raise Fault("profile_conflict")
        handle = inputs.get(request.input_id)
        if handle is None:
            raise Fault("source_unavailable")
        if (
            request.source_profile_id != handle.source_profile_id
            or request.content_profile_id != handle.content_profile_id
            or request.origin != handle.origin
        ):
            raise Fault("profile_conflict")
        if request.source_sha256 != handle.expected_sha256:
            raise Fault("source_changed")
    handle.check()
    process = owner or ProcessOwner()
    process.binary()  # fail before creating folders when dependency is missing
    reserve(store.root, os.fstat(handle.fd).st_size)
    before = identity(handle.fd)
    # Validate original before admission and hold its descriptor through the exclusive copy.
    media = validate_fd(process, handle.fd, request.source_sha256)
    source_id = new_id("source")
    extension = {"mp4": "mp4", "mov": "mov", "matroska": "mkv", "webm": "webm"}[media.container]
    directory = f"{prod.content_profile_id}/{prod.production_id}/source/{source_id}"
    store.root.mkdir(directory)
    relative_path = directory + "/recording." + extension
    temporary = directory + "/snapshot.pending"
    publication_chain = store.root.directory_chain(directory)
    with store.root.parent(temporary) as (directory_fd, name):
        copied = os.open(
            name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd
        )
        try:
            sha = hashlib.sha256()
            offset = 0
            while block := os.pread(handle.fd, 1024 * 1024, offset):
                if process.cancelled.is_set():
                    raise Fault("cancelled")
                sha.update(block)
                view = memoryview(block)
                while view:
                    written = os.write(copied, view)
                    if written <= 0:
                        raise Fault("disk_unavailable")
                    view = view[written:]
                offset += len(block)
            os.fsync(copied)
            if sha.hexdigest() != request.source_sha256 or before != identity(handle.fd):
                raise Fault("source_changed")
            handle.check()
            snapshot_media = validate_fd(process, copied, request.source_sha256)
            if media != snapshot_media:
                raise Fault("source_changed")
            handle.check()
            if before != identity(handle.fd):
                raise Fault("source_changed")
            # Publication is provisional: the name can race. Final admission below must
            # prove it still identifies our validated independent copied descriptor.
            os.link(
                name,
                "recording." + extension,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
            # Keep the pending name as immutable orphan evidence. Do not unlink a name
            # another actor may have replaced. Successful admission binds both to our copy.
            os.fchmod(copied, 0o400)
            os.fsync(copied)
            os.fsync(directory_fd)
            published_media, published_stamp = verify_published_snapshot(
                store.root,
                directory,
                relative_path,
                copied,
                publication_chain,
                offset,
                request.source_sha256,
                process,
            )
            if published_media != snapshot_media:
                raise Fault("source_changed")
            source = FinalizedSourceV1(
                source_id=source_id,
                production_id=prod.production_id,
                origin=request.origin,
                inbox_record_id=request.inbox_record_id,
                source_profile_id=prod.source_profile_id,
                content_profile_id=prod.content_profile_id,
                root_id=store.root_id,
                relative_path=relative_path,
                sha256=request.source_sha256,
                bytes=offset,
                validation=Validation(validated_at=now()),
                provenance=request.provenance,
                **dump(snapshot_media),
            )
            store.root.atomic(
                directory + "/source.json",
                json.dumps(dump(source)).encode(),
                exclusive=True,
            )
            with store.locked() as state:
                replay = store.replay(state, request.operation_id, payload)
                if replay is not None:
                    return replay
                prod = store.production(state, request.production_id)
                if prod.revision != request.expected_revision:
                    raise Fault("revision_conflict")
                verify_published_snapshot(
                    store.root,
                    directory,
                    relative_path,
                    copied,
                    publication_chain,
                    offset,
                    request.source_sha256,
                    process,
                    published_stamp,
                )
                state.sources[source_id] = source
                updated = store.bump(state, prod, source_ids=[*prod.source_ids, source_id])
                result = dict(source=dump(source), revision=updated.revision)
                store.remember(state, request.operation_id, payload, result)
                store.save(state, prod.production_id)
                return result
        finally:
            os.close(copied)
