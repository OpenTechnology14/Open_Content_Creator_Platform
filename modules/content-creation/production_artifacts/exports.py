"""One leased export per root, asynchronous status/cancel and immutable attempts."""

from __future__ import annotations

import json
from fractions import Fraction
import os
from pathlib import Path
import threading
import time
import tempfile
from pydantic import ValidationError

from stream_shorts.models import ClipPlan, ShortsJob
from stream_shorts.selector import select_clips
from stream_shorts.render import render_plan
from .media import ProcessOwner, validate_fd
from .platform_support import fcntl, require_posix
from .models import (
    ArtifactV1,
    ExportJobV1,
    ExportClipV1,
    ExportClipPlanV1,
    ExportAttemptV1,
    ExportRequestV1,
    JobEventV1,
    Metadata,
    PlanPayload,
    PlanRecord,
    Progress,
    JobCancel,
    Video,
)
from .safety import Fault, canonical, digest, hash_fd, identity
from .sources import reserve
from .store import ProductionStore, TERMINAL, dump, new_id, now

DESTINATIONS = {
    "youtube-longform-v1": ("youtube/long-form", "youtube-longform"),
    "youtube-shorts-v1": ("youtube/shorts", "youtube-shorts"),
    "tiktok-local-v1": ("tiktok", "tiktok"),
}

LONGFORM_SAR_LIMIT = 4096


def _closest_longform_ratio(ideal: Fraction) -> Fraction:
    """Closest positive ratio with both components bounded; stable reduced-form ties."""
    result = ideal
    if max(ideal.numerator, ideal.denominator) > LONGFORM_SAR_LIMIT:
        best = None
        for denominator in range(1, LONGFORM_SAR_LIMIT + 1):
            lower = ideal.numerator * denominator // ideal.denominator
            for numerator in {
                max(1, min(LONGFORM_SAR_LIMIT, lower)),
                max(1, min(LONGFORM_SAR_LIMIT, lower + 1)),
            }:
                candidate = Fraction(numerator, denominator)
                rank = (abs(candidate - ideal), candidate.denominator, candidate.numerator)
                if best is None or rank < best:
                    best, result = rank, candidate
    return result


def longform_sar(video: Video) -> Fraction:
    """Canonical x264/MOV precision; at most half a display pixel on either axis.

    The intended ratio comes from original DAR and chosen even dimensions. This
    pre-encoding projection budget never admits an arbitrary measured output.
    """
    width, height = video.width // 2 * 2, video.height // 2 * 2
    ideal = video.display_aspect * height / width
    result = _closest_longform_ratio(ideal)
    if abs(result - ideal) * width > Fraction(1, 2) or abs(
        1 / result - 1 / ideal
    ) * height > Fraction(1, 2):
        raise Fault("invalid_media")
    return result


def vertical_fit(video: Video) -> tuple[int, int, int, int]:
    """Full source DAR, square pixels, nearest even fit (lower tie), no crop.

    The nonlimiting dimension may move at most one output pixel. Even pad offsets
    keep 4:2:0 chroma aligned and move the exact center by at most one pixel.
    """
    dar = video.display_aspect
    wide = dar >= Fraction(720, 1280)
    ideal = Fraction(720, 1) / dar if wide else 1280 * dar
    bound = 1280 if wide else 720
    lower = ideal.numerator // (2 * ideal.denominator) * 2
    choices = [n for n in (lower, lower + 2) if 2 <= n <= bound]
    # Positive validated DAR and the limiting edge guarantee a candidate in [2, bound].
    chosen = min(choices, key=lambda n: (abs(n - ideal), n))
    if abs(chosen - ideal) > 1:
        raise Fault("invalid_media")
    width, height = (720, chosen) if wide else (chosen, 1280)
    return width, height, (720 - width) // 4 * 2, (1280 - height) // 4 * 2


def build_export_plan(
    payload: dict | ExportJobV1, prod: object, source: object
) -> ExportClipPlanV1:
    """Reuse selector; initial contract is one exact manual 2..10 second clip."""
    job = ExportJobV1.model_validate(payload)
    if (
        job.recording_id != source.source_id
        or job.session_id != prod.production_id
        or job.show_id != prod.show_profile_id
        or job.game_id != "walkthrough"
        or job.automatic
        or job.edit.enabled
        or abs(job.duration_seconds - source.duration_seconds) > 0.01
        or len(job.manual_sections) != 1
        or job.manual_sections[0].start_seconds != 2
        or job.manual_sections[0].end_seconds != 10
    ):
        raise Fault("plan_conflict")
    plan = select_clips(ShortsJob.model_validate(dump(job)))
    if len(plan.clips) != 1 or plan.clips[0].origin != "manual":
        raise Fault("plan_conflict")
    return ExportClipPlanV1(
        schema_version=1,
        recording_id=plan.recording_id,
        session_id=plan.session_id,
        game_id=plan.game_id,
        show_id=plan.show_id,
        duration_seconds=plan.duration_seconds,
        ignored_events=0,
        clips=[ExportClipV1.model_validate(clip.model_dump()) for clip in plan.clips],
    )


def register_plan(store: ProductionStore, payload: dict) -> dict:
    request = PlanPayload.model_validate(payload)
    with store.locked() as state:
        replay = store.replay(state, request.operation_id, payload)
        if replay is not None:
            return replay
        prod = store.production(state, request.production_id)
        if prod.revision != request.expected_revision:
            raise Fault("revision_conflict")
        source = state.sources.get(request.source_id)
        if source is None or source.production_id != prod.production_id:
            raise Fault("source_unavailable")
        plan = build_export_plan(request.job, prod, source)
        # Stored hash binds plan AND literal metadata, not only timing.
        body = dict(
            production_id=prod.production_id,
            source_id=source.source_id,
            clip_plan=plan.model_dump(mode="json"),
            title=request.title,
            description=request.description,
            metadata_revision=request.metadata_revision,
        )
        record = PlanRecord(id=new_id("plan"), sha256=digest(body), **body)
        state.plans[record.id] = record
        revision = store.bump(state, prod).revision
        result = dict(clip_plan_ref={"id": record.id, "sha256": record.sha256}, revision=revision)
        store.remember(state, request.operation_id, payload, result)
        store.save(state, prod.production_id)
        return result


class ExportRunner:
    def __init__(self, store: ProductionStore, owner_factory=ProcessOwner):
        require_posix()
        self.store, self.owner_factory = store, owner_factory
        self.mutex = threading.RLock()
        self.owner: ProcessOwner | None = None
        self.thread: threading.Thread | None = None
        self.job_id: str | None = None
        self.epoch = new_id("epoch")
        self.events: list[dict] = []
        self.event_lock = threading.Lock()
        self.commit_error: str | None = None
        self.recovery_pending = True
        self.recover_if_available()

    def recover_if_available(self) -> bool:
        """Reconcile only after every inherited execution descriptor releases exclusion."""
        with self.mutex:
            if self.thread is not None and self.thread.is_alive():
                return False
            lease = self.lease()
            if lease is None:
                self.recovery_pending = True
                return False
            try:
                self.store.recover()
                self.recovery_pending = False
                if self.commit_error == "execution_unsettled":
                    self.commit_error = None
                return True
            finally:
                os.close(lease)

    def lease(self) -> int | None:
        require_posix()
        fd = os.open(
            ".export-lease",
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
            0o600,
            dir_fd=self.store.root.fd,
        )
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            os.close(fd)
            return None
        except BaseException:
            os.close(fd)
            raise

    def start(self, payload: dict) -> dict:
        request = ExportRequestV1.model_validate(payload)
        with self.mutex, self.store.locked() as state:
            replay = self.store.replay(state, request.operation_id, payload)
            if replay is not None:
                return replay
            prod = self.store.production(state, request.production_id)
            if prod.revision != request.expected_revision:
                raise Fault("revision_conflict")
            source = state.sources.get(request.source_id)
            plan = state.plans.get(request.clip_plan_ref.id)
            if (
                source is None
                or source.production_id != prod.production_id
                or source.sha256 != request.source_sha256
            ):
                raise Fault("source_unavailable")
            if (
                plan is None
                or plan.production_id != prod.production_id
                or plan.source_id != source.source_id
                or plan.sha256 != request.clip_plan_ref.sha256
                or plan.metadata_revision != request.metadata_revision
            ):
                raise Fault("plan_conflict")
            if self.thread is not None and self.thread.is_alive():
                raise Fault("export_busy")
            lease = self.lease()
            if lease is None:
                raise Fault("export_busy")
            try:
                # Observations reconcile abandoned work. Admission must not change the
                # ledger before replay/CAS checks, or reopen an unreconciled attempt.
                if any(attempt.phase not in TERMINAL for attempt in state.attempts.values()):
                    raise Fault("export_busy")
                owner = self.owner_factory()
                owner.execution_fds = (lease,)
                owner.binary()
                # Bounded conservative H264 allowance: 30Mbps full master + two 10Mbps clips.
                estimate = int(source.duration_seconds * 30_000_000 / 8 + 2 * 8 * 10_000_000 / 8)
                reserve(self.store.root, source.bytes, estimate * 2)
                attempt = ExportAttemptV1(
                    attempt_id=new_id("attempt"),
                    job_id=new_id("job"),
                    production_id=prod.production_id,
                    source_id=source.source_id,
                    source_sha256=source.sha256,
                    plan_sha256=plan.sha256,
                    metadata_revision=plan.metadata_revision,
                    requested_output_ids=request.presets,
                    phase="queued",
                    started_at=now(),
                    process_epoch=self.epoch,
                    generation=1,
                    sequence=0,
                )
                state.attempts[attempt.attempt_id] = attempt
                revision = self.store.bump(
                    state, prod, export_attempt_ids=[*prod.export_attempt_ids, attempt.attempt_id]
                ).revision
                result = dict(
                    job_id=attempt.job_id,
                    attempt_id=attempt.attempt_id,
                    phase="queued",
                    revision=revision,
                )
                self.store.remember(state, request.operation_id, payload, result)
                self.store.save(state, prod.production_id)
            except BaseException:
                os.close(lease)
                raise
            self.owner, self.job_id = owner, attempt.job_id
            self.commit_error = None
            self.thread = threading.Thread(
                target=self.execute, args=(attempt, source, plan, owner, lease), daemon=True
            )
            try:
                self.thread.start()
            except BaseException as error:
                owner.execution_fds = ()
                self.owner, self.job_id, self.thread = None, None, None
                os.close(lease)
                if isinstance(error, RuntimeError):
                    raise Fault("worker_busy") from error
                raise
            return result

    def update(
        self, attempt: ExportAttemptV1, started: float, **changes: object
    ) -> ExportAttemptV1:
        with self.store.locked() as state:
            previous = state.attempts[attempt.attempt_id]
            if previous.phase in TERMINAL:
                raise Fault("terminal_attempt")
            updated = ExportAttemptV1.model_validate(
                {**dump(attempt), **changes, "sequence": previous.sequence + 1}
            )
            if updated.phase in TERMINAL:
                updated = updated.model_copy(update={"ended_at": now()})
            state.attempts[attempt.attempt_id] = updated
            self.store.bump(state, state.productions[attempt.production_id])
            self.store.save(state, attempt.production_id)
        event = JobEventV1(
            event_id=new_id("event"),
            production_id=attempt.production_id,
            job_id=attempt.job_id,
            attempt_id=attempt.attempt_id,
            process_epoch=self.epoch,
            generation=updated.generation,
            sequence=updated.sequence,
            phase=updated.phase,
            elapsed_ms=int((time.monotonic() - started) * 1000),
            progress=Progress(
                completed=len(updated.artifacts), total=len(updated.requested_output_ids)
            ),
            error_code=updated.error_code,
        )
        serialized = dump(event)
        if len(canonical(serialized)) > 16384:
            raise Fault("limit_exceeded")
        with self.event_lock:
            self.events.append(serialized)
            del self.events[:-64]
        return updated

    def execute(
        self,
        attempt: ExportAttemptV1,
        source: object,
        record: PlanRecord,
        owner: ProcessOwner,
        lease: int,
    ) -> None:
        start = time.monotonic()
        fd = None
        try:
            attempt = self.update(attempt, start, phase="validating")
            fd = self.store.root.open(source.relative_path)
            validate_fd(owner, fd, source.sha256)
            plan = ClipPlan.model_validate(dump(record.clip_plan))
            for preset in attempt.requested_output_ids:
                if owner.cancelled.is_set():
                    raise Fault("cancelled")
                try:
                    attempt = self.update(attempt, start, phase="rendering")
                    artifact = self.render(attempt, source, record, plan, preset, fd, owner)
                    attempt = self.update(
                        attempt,
                        start,
                        phase="validating-output",
                        artifacts=[*attempt.artifacts, artifact],
                    )
                except (Fault, OSError, ValueError) as error:
                    code = (
                        error.code
                        if isinstance(error, Fault)
                        else "source_unavailable"
                        if isinstance(error, FileNotFoundError)
                        else "disk_unavailable"
                        if isinstance(error, OSError)
                        else "media_failed"
                    )
                    if owner.execution_unsettled:
                        raise Fault("execution_unsettled") from error
                    if code == "cancelled":
                        raise Fault("cancelled") from error
                    attempt = self.update(
                        attempt,
                        start,
                        failures=[*attempt.failures, {"preset": preset, "error_code": code}],
                    )
            validate_fd(owner, fd, source.sha256)
            attempt = self.update(
                attempt,
                start,
                phase="partial"
                if attempt.artifacts and attempt.failures
                else "failed"
                if attempt.failures
                else "complete",
            )
        except (Fault, OSError, ValueError) as error:
            code = (
                error.code
                if isinstance(error, Fault)
                else "source_unavailable"
                if isinstance(error, FileNotFoundError)
                else "disk_unavailable"
                if isinstance(error, OSError)
                else "media_failed"
            )
            try:
                if owner.execution_unsettled:
                    self.commit_error = "execution_unsettled"
                    return
                self.update(
                    attempt,
                    start,
                    phase="cancelled"
                    if code == "cancelled"
                    else "partial"
                    if attempt.artifacts
                    else "failed",
                    error_code=code,
                )
            except (OSError, Fault, ValidationError):
                # Durable ledger remains nonterminal: restart marks interrupted. Never invent
                # a terminal success when fsync/rename failed; status includes persistence fault.
                self.commit_error = "persistence_failed"
        finally:
            if fd is not None:
                os.close(fd)
            owner.execution_fds = ()
            os.close(lease)

    def render(
        self,
        attempt: ExportAttemptV1,
        source: object,
        record: PlanRecord,
        plan: ClipPlan,
        preset: str,
        input_fd: int,
        owner: ProcessOwner,
    ) -> ArtifactV1:
        destination, label = DESTINATIONS[preset]
        with self.store.locked() as state:
            prod = state.productions[attempt.production_id]
        prefix = f"{prod.content_profile_id}/{prod.production_id}/{destination}/attempts/{attempt.attempt_id}"
        # Each output owns a new directory, preserving all prior attempts, even on failure.
        self.store.root.mkdir(prefix)
        filename = "video.mp4" if preset == "youtube-longform-v1" else "clip-001.mp4"
        initial = identity(input_fd)
        if hash_fd(input_fd) != source.sha256:
            raise Fault("source_changed")
        with self.store.root.directory(prefix) as directory_fd:

            def command_runner(argv: list[str], **kwargs: object) -> object:
                if preset != "youtube-longform-v1":
                    # Adapt only this fixed plain production preset; legacy CLI layout
                    # and edit behavior stay unchanged. No caller supplies filter text.
                    if "-filter_complex" not in argv:
                        raise Fault("plan_conflict")
                    width, height, x, y = vertical_fit(source.video)
                    argv = list(argv)
                    argv[argv.index("-filter_complex") + 1] = (
                        f"[0:v]scale={width}:{height},setsar=1,"
                        f"pad=720:1280:{x}:{y}:color=0x101827,fps=30[outv]"
                    )
                # Precreate output exclusively, then encode through its descriptor. ffmpeg never
                # follows a caller-controlled output path, even if an ancestor is renamed.
                output = os.open(
                    filename + ".encoded",
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory_fd,
                )
                try:
                    os.lseek(input_fd, 0, os.SEEK_SET)
                    argv = [
                        *argv[:-1],
                        "-threads",
                        "2",
                        "-maxrate",
                        "30M",
                        "-bufsize",
                        "60M",
                        "-f",
                        "mp4",
                        f"/dev/fd/{output}",
                    ]
                    argv = ["-y" if arg == "-n" else arg for arg in argv]
                    if "-movflags" in argv:
                        index = argv.index("-movflags")
                        del argv[index : index + 2]
                    argv[0] = owner.binary()
                    index = argv.index("-i")
                    argv[index:index] = ["-protocol_whitelist", "file,pipe,fd"]
                    result = owner.run(argv, pass_fds=(input_fd, output, directory_fd), timeout=600)
                    os.fsync(output)
                    final = os.open(
                        filename,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=directory_fd,
                    )
                    try:
                        from .mp4 import faststart

                        faststart(output, final, cancelled=owner.cancelled.is_set)
                    finally:
                        os.close(final)
                    return result
                finally:
                    os.close(output)

            def inspector(path: Path) -> dict:
                if str(path) == f"/dev/fd/{input_fd}":
                    media = owner.inspect(input_fd, full=False)
                else:
                    output = os.open(
                        filename + ".encoded", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd
                    )
                    try:
                        media = owner.inspect(output)
                    finally:
                        os.close(output)
                return dict(
                    size=(media.video.width, media.video.height), duration=media.duration_seconds
                )

            if preset != "youtube-longform-v1":
                # Legacy renderer manifest stays in an isolated scratch subdirectory and is
                # removed from portable authority (contains descriptor paths, no secrets).
                with tempfile.TemporaryDirectory(prefix="production-render-") as scratch:
                    render_plan(
                        plan,
                        Path("recording.mp4"),
                        Path(scratch) / "renderer",
                        source_fd=input_fd,
                        command_runner=command_runner,
                        media_inspector=inspector,
                    )
                start_seconds, end_seconds = 2.0, 10.0
            else:
                sar = longform_sar(source.video)
                command_runner(
                    [
                        owner.binary(),
                        "-nostdin",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-n",
                        "-i",
                        f"/dev/fd/{input_fd}",
                        "-map",
                        "0:v:0",
                        "-map",
                        "0:a:0",
                        "-vf",
                        "scale=trunc(iw/2)*2:trunc(ih/2)*2,"
                        f"setsar=sar={sar.numerator}/{sar.denominator}:max={LONGFORM_SAR_LIMIT}",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-crf",
                        "23",
                        "-pix_fmt",
                        "yuv420p",
                        "-threads",
                        "2",
                        "-maxrate",
                        "30M",
                        "-bufsize",
                        "60M",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "128k",
                        "-movflags",
                        "+faststart",
                        filename,
                    ]
                )
                start_seconds, end_seconds = 0.0, source.duration_seconds
            if initial != identity(input_fd) or hash_fd(input_fd) != source.sha256:
                raise Fault("source_changed")
            output = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
            try:
                sha = hash_fd(output)
                media = validate_fd(owner, output, sha)
                if (
                    media.video.codec != "h264"
                    or media.video.pixel_format != "yuv420p"
                    or media.audio.codec != "aac"
                    or abs(media.duration_seconds - (end_seconds - start_seconds)) > 0.3
                    or (
                        preset != "youtube-longform-v1"
                        and (
                            (
                                media.video.width,
                                media.video.height,
                                media.video.fps_num / media.video.fps_den,
                            )
                            != (720, 1280, 30)
                            or media.video.sar_num != media.video.sar_den
                        )
                    )
                    or (
                        preset == "youtube-longform-v1"
                        and (
                            (media.video.width, media.video.height)
                            != (source.video.width // 2 * 2, source.video.height // 2 * 2)
                            or Fraction(media.video.sar_num, media.video.sar_den)
                            != longform_sar(source.video)
                        )
                    )
                ):
                    raise Fault("invalid_media")
                metadata = Metadata(
                    title=record.title,
                    description=record.description,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    preset_version=preset,
                    metadata_revision=record.metadata_revision,
                )
                metadata_bytes = canonical(dump(metadata))
                self.store.root.atomic(prefix + "/metadata.json", metadata_bytes, exclusive=True)
                artifact = ArtifactV1(
                    artifact_id=new_id("artifact"),
                    attempt_id=attempt.attempt_id,
                    source_id=source.source_id,
                    destination=label,
                    relative_path=prefix + "/" + filename,
                    metadata_path=prefix + "/metadata.json",
                    metadata_sha256=digest(dump(metadata)),
                    sha256=sha,
                    bytes=os.fstat(output).st_size,
                    media=media,
                    preset_version=preset,
                )
                self.store.root.atomic(
                    prefix + "/artifact.json", canonical(dump(artifact)), exclusive=True
                )
                os.fsync(directory_fd)
                current = self.store.root.open(prefix + "/" + filename)
                try:
                    if identity(current) != identity(output) or hash_fd(current) != sha:
                        raise Fault("source_changed")
                finally:
                    os.close(current)
                return artifact
            finally:
                os.close(output)

    def status(self, production_id: str, job_id: str) -> dict:
        self.recover_if_available()
        with self.store.locked() as state:
            self.store.production(state, production_id)
            for attempt in state.attempts.values():
                if attempt.production_id == production_id and attempt.job_id == job_id:
                    view = dump(attempt)
                    if self.commit_error == "persistence_failed" and self.job_id == job_id:
                        view.update(phase="interrupted", error_code="persistence_failed")
                    return dict(
                        attempt=view,
                        recovery_required=(attempt.phase not in TERMINAL and self.recovery_pending)
                        or self.commit_error == "execution_unsettled",
                        persistence_error=self.commit_error,
                        account_state="unavailable",
                        publication_state="unavailable",
                    )
        raise Fault("job_unavailable")

    def cancel_request(self, payload: dict) -> dict:
        request = JobCancel.model_validate(payload)
        with self.mutex, self.store.locked() as state:
            replay = self.store.replay(state, request.operation_id, payload)
            if replay is not None:
                return replay
            prod = self.store.production(state, request.production_id)
            if prod.revision != request.expected_revision:
                raise Fault("revision_conflict")
            attempts = [
                a
                for a in state.attempts.values()
                if a.job_id == request.job_id and a.production_id == request.production_id
            ]
            if len(attempts) != 1:
                raise Fault("job_unavailable")
            attempt = attempts[0]
            if attempt.phase not in TERMINAL:
                if self.job_id != request.job_id or self.owner is None:
                    raise Fault("job_not_owned")
            result = dict(
                job_id=request.job_id,
                attempt_id=attempt.attempt_id,
                cancel_requested=attempt.phase not in TERMINAL,
                revision=prod.revision + 1,
            )
            self.store.bump(state, prod)
            self.store.remember(state, request.operation_id, payload, result)
            self.store.save(state, prod.production_id)
            if attempt.phase not in TERMINAL:
                self.owner.cancel()
            return result

    def cancel(self, production_id: str, job_id: str) -> dict:
        with self.mutex:
            result = self.status(production_id, job_id)
            if result["attempt"]["phase"] not in TERMINAL:
                if self.job_id != job_id or self.owner is None:
                    raise Fault("job_not_owned")
                self.owner.cancel()
            return result

    def inspect_artifact(self, production_id: str, artifact_id: str) -> dict:
        with self.store.locked() as state:
            self.store.production(state, production_id)
            artifacts = [
                a
                for attempt in state.attempts.values()
                if attempt.production_id == production_id
                for a in attempt.artifacts
                if a.artifact_id == artifact_id
            ]
        if len(artifacts) != 1:
            raise Fault("artifact_unavailable")
        artifact = artifacts[0]
        local_state = "validated"
        try:
            fd = self.store.root.open(artifact.relative_path)
            try:
                validate_fd(self.owner_factory(), fd, artifact.sha256)
                current = self.store.root.open(artifact.relative_path)
                try:
                    if identity(current) != identity(fd):
                        raise Fault("source_changed")
                finally:
                    os.close(current)
                if (
                    hash_fd(fd) != artifact.sha256
                    or digest(json.loads(self.store.root.read(artifact.metadata_path)))
                    != artifact.metadata_sha256
                ):
                    raise Fault("source_changed")
            finally:
                os.close(fd)
        except FileNotFoundError:
            local_state = "missing"
        except (Fault, OSError, ValueError):
            local_state = "changed"
        return dict(
            artifact=dump(artifact),
            local_state=local_state,
            editorial_state="review-needed",
            account_state="unavailable",
            publication_state="unavailable",
        )
