"""Adversarial source/job persistence contracts; fake codecs never count as media acceptance."""

import concurrent.futures
import hashlib
import os
from pathlib import Path
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "modules/content-creation"))
from production_artifacts.exports import ExportRunner, register_plan  # noqa: E402
from production_artifacts.media import ProcessOwner  # noqa: E402
from production_artifacts.models import ArtifactV1, Audio, Media, Video  # noqa: E402
from production_artifacts.safety import Fault, SafeRoot, canonical, digest, hash_fd  # noqa: E402
from production_artifacts.sources import InputHandle, register_finalized_source  # noqa: E402
from production_artifacts.store import ProductionStore  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from production_artifacts.worker import Worker  # noqa: E402
from test_production_artifacts import creation  # noqa: E402

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX descriptor/process ownership runtime; unsupported platform admission is tested separately",
)

MEDIA = Media(
    container="mp4",
    video=Video(
        codec="h264",
        width=1280,
        height=720,
        sar_num=1,
        sar_den=1,
        fps_num=30,
        fps_den=1,
        pixel_format="yuv420p",
    ),
    audio=Audio(codec="aac", sample_rate=48000, channels=1, duration_seconds=12.0),
    duration_seconds=12.0,
)


class FakeMedia(ProcessOwner):
    def binary(self):
        return "/usr/bin/true"

    def inspect(self, fd, **kwargs):
        return MEDIA


@pytest.fixture
def prepared(tmp_path):
    if os.name != "posix":
        pytest.skip(
            "POSIX immutable source/job fixture; Windows unsupported admission has positive portable tests"
        )
    root = tmp_path / "outputs"
    root.mkdir()
    original = tmp_path / "original.mp4"
    original.write_bytes(b"fixture media" * 100)
    sha = hashlib.sha256(original.read_bytes()).hexdigest()
    inputs = {
        "input-one": InputHandle.admit(
            SafeRoot(tmp_path),
            original.name,
            sha,
            source_profile_id="stream-main",
            content_profile_id="content-main",
            origin="fixture",
        )
    }
    store = ProductionStore(SafeRoot(root), "root-one")
    prod = store.create(creation())
    payload = dict(
        production_id=prod["production_id"],
        expected_revision=1,
        operation_id="source-one",
        input_id="input-one",
        source_sha256=sha,
        source_profile_id="stream-main",
        content_profile_id="content-main",
        origin="fixture",
    )
    yield store, inputs, prod, payload, original
    for handle in inputs.values():
        handle.close()


def seed(prepared):
    store, inputs, prod, payload, original = prepared
    registered = register_finalized_source(store, inputs, payload, FakeMedia())
    source = registered["source"]
    plan_payload = dict(
        production_id=prod["production_id"],
        expected_revision=2,
        operation_id="plan-one",
        source_id=source["source_id"],
        title="Literal title",
        description="Literal description",
        metadata_revision=1,
        job=dict(
            schema_version=1,
            recording_id=source["source_id"],
            session_id=prod["production_id"],
            game_id="walkthrough",
            show_id="opentech",
            duration_seconds=12.0,
            automatic=False,
            manual_sections=[dict(start_seconds=2.0, end_seconds=10.0)],
            edit=dict(enabled=False),
        ),
    )
    plan = register_plan(store, plan_payload)
    request = dict(
        production_id=prod["production_id"],
        expected_revision=3,
        operation_id="export-one",
        source_id=source["source_id"],
        source_sha256=source["sha256"],
        presets=["youtube-longform-v1", "youtube-shorts-v1", "tiktok-local-v1"],
        clip_plan_ref=plan["clip_plan_ref"],
        metadata_revision=1,
    )
    return store, source, plan_payload, request, original


def finish(runner):
    runner.thread.join(timeout=5)
    assert not runner.thread.is_alive()


def fake_render(runner, attempt, source, record, plan, preset, fd, owner):
    path = f"artifacts/{attempt.attempt_id}/{preset}.mp4"
    runner.store.root.atomic(path, b"validated-output", exclusive=True)
    metadata = dict(title=record.title)
    runner.store.root.atomic(path + ".json", canonical(metadata), exclusive=True)
    return ArtifactV1(
        artifact_id="artifact-" + preset,
        attempt_id=attempt.attempt_id,
        source_id=source.source_id,
        destination={
            "youtube-longform-v1": "youtube-longform",
            "youtube-shorts-v1": "youtube-shorts",
            "tiktok-local-v1": "tiktok",
        }[preset],
        relative_path=path,
        metadata_path=path + ".json",
        metadata_sha256=digest(metadata),
        sha256=hashlib.sha256(b"validated-output").hexdigest(),
        bytes=16,
        media=MEDIA,
        preset_version=preset,
    )


def runner_with_render(store, monkeypatch):
    runner = ExportRunner(store, FakeMedia)
    monkeypatch.setattr(runner, "render", lambda *args: fake_render(runner, *args))
    return runner


def test_snapshot_is_independent_portable_idempotent_and_original_unchanged(prepared):
    store, inputs, prod, payload, original = prepared
    before = original.read_bytes()
    result = register_finalized_source(store, inputs, payload, FakeMedia())
    assert register_finalized_source(store, inputs, payload, FakeMedia()) == result
    snapshot = store.root.path / result["source"]["relative_path"]
    assert snapshot.read_bytes() == before
    assert snapshot.stat().st_ino != original.stat().st_ino
    assert original.read_bytes() == before
    portable = (
        store.root.path / "content-main" / prod["production_id"] / "manifest.json"
    ).read_text()
    assert str(original.parent) not in portable
    original.unlink()
    fd = store.root.open(result["source"]["relative_path"])
    try:
        assert hash_fd(fd) == payload["source_sha256"]
    finally:
        os.close(fd)


@pytest.mark.parametrize(
    "change,code",
    [
        ({"source_profile_id": "other"}, "profile_conflict"),
        ({"content_profile_id": "other"}, "profile_conflict"),
        ({"source_sha256": "0" * 64}, "source_changed"),
        ({"expected_revision": 2}, "revision_conflict"),
        ({"input_id": "missing"}, "source_unavailable"),
    ],
)
def test_bad_source_admission_leaves_no_snapshot(prepared, change, code):
    store, inputs, prod, payload, original = prepared
    before = store.root.read("state.json")
    with pytest.raises(Fault, match=code):
        register_finalized_source(store, inputs, {**payload, **change}, FakeMedia())
    assert store.root.read("state.json") == before
    assert not list(store.root.path.rglob("recording.mp4"))


def test_managed_and_request_paths_cannot_be_admitted(prepared):
    store, inputs, prod, payload, original = prepared
    worker = Worker(store, inputs)
    for change in [
        {"origin": "managed"},
        {"root_path": str(original.parent)},
        {"path": str(original)},
    ]:
        response = worker.handle(
            canonical(
                dict(
                    schema_version=1,
                    request_id="bad",
                    command="source.register",
                    payload={**payload, **change},
                )
            )
        )
        assert response["ok"] is False
        assert response["error"]["code"] == "invalid_request"
    assert not list(store.root.path.rglob("recording.mp4"))


@pytest.mark.parametrize("stage", ["before-open", "hash", "copy", "decode"])
def test_replacement_at_each_source_boundary_is_rejected(prepared, monkeypatch, stage):
    store, inputs, prod, payload, original = prepared

    def replace():
        replacement = original.with_suffix(".replacement")
        replacement.write_bytes(b"X" * original.stat().st_size)
        stamp = original.stat().st_mtime_ns
        os.utime(replacement, ns=(stamp, stamp))
        os.replace(replacement, original)

    if stage == "before-open":
        replace()
    elif stage in {"hash", "copy"}:
        real = os.pread
        count = 0

        def pread(fd, size, offset):
            nonlocal count
            count += 1
            block = real(fd, size, offset)
            if count == (1 if stage == "hash" else 3):
                replace()
            return block

        monkeypatch.setattr(os, "pread", pread)
    else:
        real = FakeMedia.inspect

        def inspect(self, fd, **kwargs):
            result = real(self, fd, **kwargs)
            replace()
            return result

        monkeypatch.setattr(FakeMedia, "inspect", inspect)
    with pytest.raises(Fault, match="source_changed"):
        register_finalized_source(store, inputs, payload, FakeMedia())
    assert store.get(prod["production_id"])["sources"] == []


def test_in_place_mutation_during_decode_is_rejected(prepared, monkeypatch):
    store, inputs, prod, payload, original = prepared

    def mutate(self, fd, **kwargs):
        original.write_bytes(b"changed" * 200)
        return MEDIA

    monkeypatch.setattr(FakeMedia, "inspect", mutate)
    with pytest.raises(Fault, match="source_changed"):
        register_finalized_source(store, inputs, payload, FakeMedia())


def test_source_symlink_replacement_fails_closed(prepared):
    store, inputs, prod, payload, original = prepared
    moved = original.with_suffix(".moved")
    original.rename(moved)
    original.symlink_to(moved)
    with pytest.raises((Fault, OSError)):
        register_finalized_source(store, inputs, payload, FakeMedia())
    assert not list(store.root.path.rglob("recording.mp4"))


def test_missing_dependency_and_disk_estimate_block_before_snapshot(prepared, monkeypatch):
    import production_artifacts.sources as sources

    store, inputs, prod, payload, original = prepared
    with pytest.raises(Fault, match="dependency_unavailable"):
        register_finalized_source(store, inputs, payload, ProcessOwner("/missing-ffmpeg"))
    monkeypatch.setattr(sources.shutil, "disk_usage", lambda _: type("Usage", (), {"free": 0})())
    with pytest.raises(Fault, match="disk_space"):
        register_finalized_source(store, inputs, payload, FakeMedia())
    assert not list(store.root.path.rglob("recording.mp4"))


@pytest.mark.parametrize(
    "change",
    [
        {"automatic": True},
        {"game_id": "fakegame"},
        {"edit": {"enabled": True}},
        {"recording_id": "other"},
        {"show_id": "other"},
        {"manual_sections": [{"start_seconds": 1.0, "end_seconds": 9.0}]},
    ],
)
def test_plan_pins_source_show_and_exact_manual_plain_range(prepared, change):
    store, source, payload, request, original = seed(prepared)
    before = store.root.read("state.json")
    payload.update(operation_id="new-plan", expected_revision=3, job={**payload["job"], **change})
    if any(key in change for key in {"automatic", "game_id", "edit"}):
        with pytest.raises(ValidationError):
            register_plan(store, payload)
    else:
        with pytest.raises(Fault, match="plan_conflict"):
            register_plan(store, payload)
    assert before == store.root.read("state.json")


def test_export_duplicate_conflict_and_retry_preserve_prior_files(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    before = original.read_bytes()
    runner = runner_with_render(store, monkeypatch)
    result = runner.start(request)
    finish(runner)
    successful = runner.status(request["production_id"], result["job_id"])
    assert successful["attempt"]["phase"] == "complete"
    paths = {
        a["relative_path"]: (store.root.path / a["relative_path"]).read_bytes()
        for a in successful["attempt"]["artifacts"]
    }
    ledger = store.root.read("state.json")
    assert runner.start(request) == result
    with pytest.raises(Fault, match="operation_conflict"):
        runner.start({**request, "metadata_revision": 2})
    assert ledger == store.root.read("state.json")
    revision = store.get(request["production_id"])["production"]["revision"]
    second = runner.start({**request, "operation_id": "retry-one", "expected_revision": revision})
    finish(runner)
    assert second["attempt_id"] != result["attempt_id"]
    assert original.read_bytes() == before
    for path, data in paths.items():
        assert (store.root.path / path).read_bytes() == data
    assert runner.status(request["production_id"], result["job_id"]) == successful


def test_partial_failure_preserves_validated_sibling_and_truthful_states(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)

    def partial(*args):
        if args[4] == "youtube-shorts-v1":
            raise OSError(28, "full disk during render")
        return fake_render(runner, *args)

    monkeypatch.setattr(runner, "render", partial)
    result = runner.start(request)
    finish(runner)
    status = runner.status(request["production_id"], result["job_id"])
    assert status["attempt"]["phase"] == "partial"
    assert len(status["attempt"]["artifacts"]) == 2
    assert status["attempt"]["failures"][0]["error_code"] == "disk_unavailable"
    assert status["account_state"] == "unavailable"
    assert all(a["editorial_state"] == "review-needed" for a in status["attempt"]["artifacts"])


def test_status_and_cancel_responsive_and_only_owned_process_is_signalled(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    entered = threading.Event()

    def slow(*args):
        owner = args[-1]
        entered.set()
        assert owner.cancelled.wait(3)
        raise Fault("cancelled")

    monkeypatch.setattr(runner, "render", slow)
    result = runner.start(request)
    assert entered.wait(2)
    started = time.monotonic()
    assert (
        runner.status(request["production_id"], result["job_id"])["attempt"]["phase"] == "rendering"
    )
    runner.cancel(request["production_id"], result["job_id"])
    assert time.monotonic() - started < 0.5
    finish(runner)
    assert (
        runner.status(request["production_id"], result["job_id"])["attempt"]["phase"] == "cancelled"
    )
    with pytest.raises(Fault, match="job_unavailable"):
        runner.cancel(request["production_id"], "foreign-job")


def test_interprocess_lease_blocks_duplicate_render_without_recovery(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    lease = runner.lease()
    assert lease is not None
    try:
        other = ExportRunner(ProductionStore(SafeRoot(store.root.path), "root-one"), FakeMedia)
        before = store.root.read("state.json")
        with pytest.raises(Fault, match="export_busy"):
            other.start(request)
        assert before == store.root.read("state.json")
    finally:
        os.close(lease)


def test_concurrent_claims_get_one_attempt(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = runner_with_render(store, monkeypatch)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: runner.start(request), range(2)))
    finish(runner)
    assert results[0] == results[1]
    assert len(store.get(request["production_id"])["attempts"]) == 1


def test_restart_interrupts_active_attempt_never_kills_or_replays(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    real_start = threading.Thread.start
    monkeypatch.setattr(threading.Thread, "start", lambda _: None)
    result = runner.start(request)
    # Simulate a dead process: release its lease by closing the fd in the captured args.
    os.close(runner.thread._args[-1])
    monkeypatch.setattr(threading.Thread, "start", real_start)
    monkeypatch.setattr(os, "killpg", lambda *args: pytest.fail("persisted PID was signalled"))
    recovered = ExportRunner(store, FakeMedia)
    status = recovered.status(request["production_id"], result["job_id"])
    assert status["attempt"]["phase"] == "interrupted"
    assert status["attempt"]["error_code"] == "worker_restarted"
    before = store.root.read("state.json")
    assert recovered.start(request) == result
    assert before == store.root.read("state.json")


def test_missing_and_changed_snapshot_block_export(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    snapshot = store.root.path / source["relative_path"]
    snapshot.chmod(0o600)
    snapshot.write_bytes(b"wrong same or different size")
    runner = runner_with_render(store, monkeypatch)
    result = runner.start(request)
    finish(runner)
    status = runner.status(request["production_id"], result["job_id"])
    assert status["attempt"]["phase"] == "failed"
    assert status["attempt"]["error_code"] == "source_changed"
    assert not (store.root.path / "artifacts").exists()


def test_manifest_commit_failure_never_claims_complete_and_restart_retains_success(
    prepared, monkeypatch
):
    store, source, payload, request, original = seed(prepared)
    runner = runner_with_render(store, monkeypatch)
    real_save = store.save

    def fail_terminal(state, production_id=None):
        if any(a.phase in {"complete", "partial", "failed"} for a in state.attempts.values()):
            raise OSError(28, "disk full during manifest commit")
        return real_save(state, production_id)

    monkeypatch.setattr(store, "save", fail_terminal)
    result = runner.start(request)
    finish(runner)
    status = runner.status(request["production_id"], result["job_id"])
    assert status["attempt"]["phase"] == "interrupted"
    assert status["persistence_error"] == "persistence_failed"
    assert len(status["attempt"]["artifacts"]) == 3
    monkeypatch.setattr(store, "save", real_save)
    recovered = ExportRunner(store, FakeMedia)
    status = recovered.status(request["production_id"], result["job_id"])
    assert status["attempt"]["phase"] == "interrupted"
    assert len(status["attempt"]["artifacts"]) == 3


def test_terminal_attempt_cannot_reopen(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = runner_with_render(store, monkeypatch)
    result = runner.start(request)
    finish(runner)
    with store.locked() as state:
        attempt = state.attempts[result["attempt_id"]]
    before = store.root.read("state.json")
    with pytest.raises(Fault, match="terminal_attempt"):
        runner.update(attempt, time.monotonic(), phase="rendering")
    assert before == store.root.read("state.json")


def test_inspection_checks_media_and_metadata_without_changing_history(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = runner_with_render(store, monkeypatch)
    result = runner.start(request)
    finish(runner)
    artifact = runner.status(request["production_id"], result["job_id"])["attempt"]["artifacts"][0]
    before = store.root.read("state.json")
    assert (
        runner.inspect_artifact(request["production_id"], artifact["artifact_id"])["local_state"]
        == "validated"
    )
    (store.root.path / artifact["metadata_path"]).write_text("{}")
    assert (
        runner.inspect_artifact(request["production_id"], artifact["artifact_id"])["local_state"]
        == "changed"
    )
    (store.root.path / artifact["relative_path"]).unlink()
    assert (
        runner.inspect_artifact(request["production_id"], artifact["artifact_id"])["local_state"]
        == "missing"
    )
    assert before == store.root.read("state.json")


def test_wire_cancel_is_revision_checked_and_durable_idempotent(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = runner_with_render(store, monkeypatch)
    result = runner.start(request)
    finish(runner)
    worker = Worker(store, {}, runner)
    revision = store.get(request["production_id"])["production"]["revision"]

    def cancel(rev, operation):
        return worker.handle(
            canonical(
                dict(
                    schema_version=1,
                    request_id="cancel",
                    command="job.cancel",
                    payload=dict(
                        production_id=request["production_id"],
                        job_id=result["job_id"],
                        expected_revision=rev,
                        operation_id=operation,
                    ),
                )
            )
        )

    assert cancel(revision - 1, "cancel-stale")["error"]["code"] == "revision_conflict"
    first = cancel(revision, "cancel-one")
    assert first["ok"] is True
    before = store.root.read("state.json")
    assert cancel(revision, "cancel-one") == first
    assert store.root.read("state.json") == before
    assert cancel(revision - 1, "cancel-one")["error"]["code"] == "operation_conflict"


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b"null",
        b'{"schema_version":2}',
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b"x" * (1024 * 1024 + 1),
    ],
    ids=["array", "null", "unknown-version", "duplicate-key", "nonfinite", "oversized"],
)
def test_malformed_wire_never_creates_production(prepared, raw):
    store, inputs, prod, payload, original = prepared
    worker = Worker(store, inputs)
    before = store.root.read("state.json")
    assert worker.handle(raw)["ok"] is False
    assert before == store.root.read("state.json")


def test_trusted_input_profiles_and_origin_cannot_be_relabelled(prepared):
    store, inputs, prod, payload, original = prepared
    handle = inputs["input-one"]
    handle.content_profile_id = "different-trusted-content"
    with pytest.raises(Fault, match="profile_conflict"):
        register_finalized_source(store, inputs, payload, FakeMedia())
    assert not list(store.root.path.rglob("recording.mp4"))


@POSIX_ONLY
def test_real_process_cancel_and_deadline_reap_only_live_owned_group():
    owner = ProcessOwner(sys.executable)
    result = []

    def work():
        try:
            owner.run([sys.executable, "-B", "-c", "import time; time.sleep(20)"], timeout=5)
        except Fault as error:
            result.append(error.code)

    thread = threading.Thread(target=work)
    thread.start()
    deadline = time.monotonic() + 2
    while owner.child is None and time.monotonic() < deadline:
        time.sleep(0.005)
    assert owner.child is not None
    child = owner.child
    owner.cancel()
    thread.join(3)
    assert result == ["cancelled"]
    assert child.poll() is not None
    with pytest.raises(Fault, match="process_timeout"):
        ProcessOwner(sys.executable).run(
            [sys.executable, "-B", "-c", "import time; time.sleep(20)"], timeout=0.05
        )


def test_existing_output_is_never_overwritten(prepared, monkeypatch):
    from stream_shorts.models import ClipPlan

    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    monkeypatch.setattr(threading.Thread, "start", lambda _: None)
    result = runner.start(request)
    os.close(runner.thread._args[-1])
    with store.locked() as state:
        attempt = state.attempts[result["attempt_id"]]
        source_model = state.sources[source["source_id"]]
        plan_record = state.plans[request["clip_plan_ref"]["id"]]
    prefix = (
        f"content-main/{request['production_id']}/youtube/long-form/attempts/{result['attempt_id']}"
    )
    store.root.mkdir(prefix)
    store.root.atomic(prefix + "/video.mp4", b"prior-output", exclusive=True)
    fd = store.root.open(source["relative_path"])
    try:
        with pytest.raises(FileExistsError):
            runner.render(
                attempt,
                source_model,
                plan_record,
                ClipPlan.model_validate(plan_record.clip_plan.model_dump()),
                "youtube-longform-v1",
                fd,
                FakeMedia(),
            )
    finally:
        os.close(fd)
    assert store.root.read(prefix + "/video.mp4") == b"prior-output"


def test_export_stale_revision_and_wrong_source_plan_rejected_without_attempt(prepared):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    before = store.root.read("state.json")
    for change, code in [
        ({"expected_revision": 2}, "revision_conflict"),
        ({"source_sha256": "0" * 64}, "source_unavailable"),
        ({"clip_plan_ref": {"id": "missing", "sha256": "0" * 64}}, "plan_conflict"),
        ({"metadata_revision": 2}, "plan_conflict"),
    ]:
        with pytest.raises(Fault, match=code):
            runner.start({**request, **change})
    assert before == store.root.read("state.json")


@POSIX_ONLY
def test_fd_hash_validation_and_postdecode_replacement_are_checked(tmp_path):
    from production_artifacts.media import validate_fd

    source = tmp_path / "source"
    source.write_bytes(b"accepted")
    fd = os.open(source, os.O_RDONLY)
    try:
        with pytest.raises(Fault, match="source_changed"):
            validate_fd(FakeMedia(), fd, "0" * 64)

        class Mutator(FakeMedia):
            def inspect(self, fd, **kwargs):
                source.write_bytes(b"mutated!")
                return MEDIA

        expected = hashlib.sha256(source.read_bytes()).hexdigest()
        with pytest.raises(Fault, match="source_changed"):
            validate_fd(Mutator(), fd, expected)
    finally:
        os.close(fd)


def test_snapshot_missing_does_not_create_destination_files(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    (store.root.path / source["relative_path"]).unlink()
    runner = runner_with_render(store, monkeypatch)
    result = runner.start(request)
    finish(runner)
    status = runner.status(request["production_id"], result["job_id"])
    assert status["attempt"]["phase"] == "failed"
    assert status["attempt"]["error_code"] == "source_unavailable"
    assert status["attempt"]["artifacts"] == []
    assert not (store.root.path / "artifacts").exists()


def test_source_copy_disk_full_leaves_no_admitted_source(prepared, monkeypatch):
    store, inputs, prod, payload, original = prepared
    real_write = os.write

    def full(fd, data):
        if bytes(data).startswith(b"fixture media"):
            raise OSError(28, "disk full mid-copy")
        return real_write(fd, data)

    monkeypatch.setattr(os, "write", full)
    with pytest.raises(OSError):
        register_finalized_source(store, inputs, payload, FakeMedia())
    assert store.get(prod["production_id"])["sources"] == []
    assert hashlib.sha256(original.read_bytes()).hexdigest() == payload["source_sha256"]


def test_diagnostic_import_does_not_hold_status_lock(prepared, monkeypatch):
    store, inputs, prod, payload, original = prepared
    entered, release = threading.Event(), threading.Event()

    class Slow(FakeMedia):
        def inspect(self, fd, **kwargs):
            entered.set()
            assert release.wait(3)
            return MEDIA

    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        importing = pool.submit(register_finalized_source, store, inputs, payload, Slow())
        assert entered.wait(1)
        try:
            reading = pool.submit(store.get, prod["production_id"])
            assert reading.result(timeout=0.5)["production"]["revision"] == 1
        finally:
            release.set()
        assert importing.result(timeout=2)["revision"] == 2


def test_input_expected_hash_is_pinned_by_launcher(prepared):
    store, inputs, prod, payload, original = prepared
    inputs["input-one"].expected_sha256 = "0" * 64
    with pytest.raises(Fault, match="source_changed"):
        register_finalized_source(store, inputs, payload, FakeMedia())
    assert store.get(prod["production_id"])["sources"] == []


@POSIX_ONLY
def test_missing_executable_is_rejected_before_launch():
    with pytest.raises(Fault, match="dependency_unavailable"):
        ProcessOwner("/missing-executable").binary()


@POSIX_ONLY
def test_owned_process_deadline_is_enforced():
    with pytest.raises(Fault, match="process_timeout"):
        ProcessOwner(sys.executable).run(
            [sys.executable, "-B", "-c", "import time; time.sleep(.2)"], timeout=0.01
        )


def test_valid_plan_id_with_altered_hash_is_not_admitted(prepared):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    with pytest.raises(Fault, match="plan_conflict"):
        runner.start({**request, "clip_plan_ref": {**request["clip_plan_ref"], "sha256": "0" * 64}})
    assert store.get(request["production_id"])["attempts"] == []


def test_progress_event_ring_and_sequence_are_bounded(prepared, monkeypatch):
    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    monkeypatch.setattr(threading.Thread, "start", lambda _: None)
    result = runner.start(request)
    os.close(runner.thread._args[-1])
    with store.locked() as state:
        attempt = state.attempts[result["attempt_id"]]
    for number in range(80):
        attempt = runner.update(attempt, time.monotonic(), phase="rendering")
    assert len(runner.events) == 64
    assert runner.events[-1]["sequence"] == 80
    assert len(canonical(runner.events[-1])) <= 16384
    assert runner.events[-1]["process_epoch"] == runner.epoch


def test_output_preset_dimensions_are_verified_before_admission(prepared, monkeypatch):
    from stream_shorts.models import ClipPlan
    from production_artifacts.models import Video

    store, source, payload, request, original = seed(prepared)
    owner = ProcessOwner()
    actual = original.with_name("real-tiny.mp4")
    owner.run(
        [
            owner.binary(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=160x90:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "0.2",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(actual),
        ]
    )
    runner = ExportRunner(store, FakeMedia)
    real_start = threading.Thread.start
    monkeypatch.setattr(threading.Thread, "start", lambda _: None)
    result = runner.start(request)
    os.close(runner.thread._args[-1])
    monkeypatch.setattr(threading.Thread, "start", real_start)
    with store.locked() as state:
        attempt = state.attempts[result["attempt_id"]]
        source_model = state.sources[source["source_id"]].model_copy(
            update={"sha256": hashlib.sha256(actual.read_bytes()).hexdigest()}
        )
        plan = state.plans[request["clip_plan_ref"]["id"]]

    class WrongDimensions(ProcessOwner):
        def inspect(self, fd, **kwargs):
            return MEDIA.model_copy(
                update={
                    "video": Video(
                        codec="h264",
                        width=2,
                        height=2,
                        sar_num=1,
                        sar_den=1,
                        fps_num=30,
                        fps_den=1,
                        pixel_format="yuv420p",
                    )
                }
            )

    fd = os.open(actual, os.O_RDONLY)
    try:
        with pytest.raises(Fault, match="invalid_media"):
            runner.render(
                attempt,
                source_model,
                plan,
                ClipPlan.model_validate(plan.clip_plan.model_dump()),
                "youtube-longform-v1",
                fd,
                WrongDimensions(),
            )
    finally:
        os.close(fd)
    assert not list(store.root.path.rglob("artifact.json"))


def test_changed_stored_plan_is_not_used_with_old_approved_hash(prepared):
    import json

    store, source, payload, request, original = seed(prepared)
    state = json.loads(store.root.read("state.json"))
    state["plans"][request["clip_plan_ref"]["id"]]["clip_plan"]["clips"][0]["label"] = "tampered"
    store.root.atomic("state.json", canonical(state))
    before = store.root.read("state.json")
    with pytest.raises(Fault, match="corrupt_state"):
        store.get(request["production_id"])
    assert store.root.read("state.json") == before


def test_store_interprocess_lock_has_bounded_busy_result(prepared, monkeypatch):
    import production_artifacts.store as module

    store, inputs, prod, payload, original = prepared
    real_flock = module.fcntl.flock

    def held(fd, operation):
        if operation & module.fcntl.LOCK_NB:
            raise BlockingIOError("other process holds lock")
        return real_flock(fd, operation)

    ticks = iter([0, 3, 4, 5, 6, 7, 8, 9, 10])
    monkeypatch.setattr(module.fcntl, "flock", held)
    monkeypatch.setattr(module.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(module.time, "sleep", lambda _: pytest.fail("waited after lock deadline"))
    with pytest.raises(Fault, match="worker_busy"):
        store.list()


def test_orphan_records_in_corrupt_ledger_are_preserved_and_rejected(prepared):
    import json

    store, source, payload, request, original = seed(prepared)
    state = json.loads(store.root.read("state.json"))
    # Valid schema, invalid membership: it must not disappear from checks merely because
    # a production's list no longer references it.
    state["productions"][request["production_id"]]["source_ids"] = []
    state["plans"] = {}
    store.root.atomic("state.json", canonical(state))
    before = store.root.read("state.json")
    with pytest.raises(Fault, match="corrupt_state"):
        store.list()
    assert store.root.read("state.json") == before
