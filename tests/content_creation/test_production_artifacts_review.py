"""Maintained R1 regressions: real publication boundaries and strict portable contracts."""

import hashlib
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "modules/content-creation"))
from production_artifacts.media import ProcessOwner  # noqa: E402
from production_artifacts.safety import Fault, SafeRoot, canonical  # noqa: E402
from production_artifacts.sources import InputHandle, register_finalized_source  # noqa: E402
from production_artifacts.store import ProductionStore  # noqa: E402
from production_artifacts.worker import Worker  # noqa: E402
from test_production_artifacts import creation  # noqa: E402
from test_production_artifacts_jobs import FakeMedia, prepared as prepared_fixture, seed  # noqa: E402,F401

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX descriptor publication and codec execution; portable ABI tests run on all hosts",
)


@pytest.fixture(name="prepared")
def source_job_fixture(tmp_path):
    yield from prepared_fixture.__wrapped__(tmp_path)


def generate_source(path):
    owner = ProcessOwner()
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
            "12",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )


@POSIX_ONLY
@pytest.mark.parametrize("real_codec", [False, True])
@pytest.mark.parametrize(
    "attack",
    [
        "regular",
        "symlink",
        "directory",
        "directory-symlink",
        "directory-rebind",
        "ancestor",
        "final-swap",
    ],
)
def test_source_publication_admits_only_validated_inode_at_original_root(
    tmp_path, monkeypatch, real_codec, attack
):
    root = tmp_path / "root"
    root.mkdir()
    source = tmp_path / "original.mp4"
    if real_codec:
        generate_source(source)
    else:
        source.write_bytes(b"fixture media" * 100)
    original = source.read_bytes()
    sha = hashlib.sha256(original).hexdigest()
    store = ProductionStore(SafeRoot(root), "root-one")
    prod = store.create(creation())
    handle = InputHandle.admit(
        SafeRoot(tmp_path),
        source.name,
        sha,
        source_profile_id="stream-main",
        content_profile_id="content-main",
        origin="fixture",
    )
    real_link = os.link
    hit = []

    def replace_at_publish(src, dst, *args, **kwargs):
        if src != "snapshot.pending":
            return real_link(src, dst, *args, **kwargs)
        hit.append(True)
        fd = kwargs["src_dir_fd"]
        directory = next(root.rglob("snapshot.pending")).parent
        if attack in {"regular", "symlink"}:
            os.rename(src, "validated-detached", src_dir_fd=fd, dst_dir_fd=fd)
            if attack == "regular":
                bad = os.open(src, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=fd)
                os.write(bad, b"not validated media")
                os.close(bad)
            else:
                os.symlink(source, src, dir_fd=fd)
        elif attack in {"directory", "directory-symlink", "directory-rebind", "ancestor"}:
            changed = directory.parent if attack == "ancestor" else directory
            detached = changed.with_name(changed.name + "-detached")
            changed.rename(detached)
            if attack == "directory-symlink":
                changed.symlink_to(detached, target_is_directory=True)
            else:
                changed.mkdir()
        result = real_link(src, dst, *args, **kwargs)
        if attack == "directory-rebind":
            real_link(directory.with_name(directory.name + "-detached") / dst, directory / dst)
        if attack == "final-swap":
            os.rename(dst, "published-detached", src_dir_fd=fd, dst_dir_fd=fd)
            bad = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=fd)
            os.write(bad, b"not validated media")
            os.close(bad)
        return result

    monkeypatch.setattr(os, "link", replace_at_publish)
    try:
        with pytest.raises((Fault, OSError)):
            register_finalized_source(
                store,
                {"input": handle},
                dict(
                    production_id=prod["production_id"],
                    expected_revision=1,
                    operation_id="source",
                    input_id="input",
                    source_sha256=sha,
                    source_profile_id="stream-main",
                    content_profile_id="content-main",
                    origin="fixture",
                ),
                ProcessOwner() if real_codec else FakeMedia(),
            )
        assert hit and store.get(prod["production_id"])["sources"] == []
        assert source.read_bytes() == original
        assert list(root.rglob("*detached*"))  # retained evidence, no cleanup of replaced names
    finally:
        handle.close()


@pytest.mark.parametrize(
    "change",
    [
        {"duration_seconds": "12"},
        {"automatic": "false"},
        {"automatic": 0},
        {"manual_sections": [{"start_seconds": "2", "end_seconds": "10", "label": "range"}]},
        {
            "manual_sections": [
                {
                    "start_seconds": 2.0,
                    "end_seconds": 10.0,
                    "label": "https://example.invalid/synthetic",
                }
            ]
        },
        {"edit": {"enabled": "false"}},
        {"edit": {"enabled": 0}},
        {"edit": {"enabled": False, "style": {"watermark": "https://example.invalid/synthetic"}}},
        {"edit": {"enabled": False, "captions": []}},
        {"schema_version": 2},
        {"unknown": True},
    ],
)
def test_nested_job_rejects_coercions_urls_and_unused_fields_without_writes(prepared, change):
    store, source, payload, request, original = seed(prepared)
    payload.update(operation_id="bad-plan", expected_revision=3, job={**payload["job"], **change})
    before = store.root.read("state.json")
    result = Worker(store, {}).handle(
        canonical(
            dict(schema_version=1, request_id="bad", command="plan.register", payload=payload)
        )
    )
    assert result["ok"] is False
    assert before == store.root.read("state.json")


class StdioClient:
    def __init__(self, root, pause=None):
        import json
        import queue
        import subprocess
        import threading
        import uuid

        self.root = root
        self.queue = queue.Queue()
        self.number = 0
        registry = root / ("registry-" + uuid.uuid4().hex + ".json")
        registry.write_bytes(
            canonical(dict(schema_version=1, root_id="root-one", root_path=str(root), inputs={}))
        )
        fd = os.open(registry, os.O_RDONLY)
        # Hook only the real codec launch in this owned worker to make SIGKILL deterministic.
        harness = """
import json,os,signal,sys
import production_artifacts.media as media
from production_artifacts.worker import main
real=media.subprocess.Popen
mode=sys.argv[1];marker=sys.argv[2];hit=False
args=sys.argv[3:]
def launch(argv,**kwargs):
    global hit
    child=real(argv,**kwargs)
    match=('-c:v' in argv) if mode=='render' else ('-xerror' in argv)
    if mode!='none' and match and not hit:
        hit=True;os.kill(child.pid,signal.SIGSTOP)
        with open(marker+'.pending','x') as output:
            json.dump({'pid':child.pid,'worker':os.getpid()},output)
            output.flush();os.fsync(output.fileno())
        os.rename(marker+'.pending',marker)
    return child
media.subprocess.Popen=launch
sys.argv=['production_artifacts',*args]
main()
"""
        self.marker = root / ("paused-" + uuid.uuid4().hex + ".json")
        self.stderr = (root / ("stderr-" + uuid.uuid4().hex + ".log")).open("wb")
        try:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    harness,
                    pause or "none",
                    str(self.marker),
                    "--registry-fd",
                    str(fd),
                ],
                pass_fds=(fd,),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.stderr,
                env={
                    **os.environ,
                    "PYTHONPATH": str(
                        Path(__file__).resolve().parents[2] / "modules/content-creation"
                    ),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
        finally:
            os.close(fd)

        def read():
            for line in self.process.stdout:
                self.queue.put(json.loads(line))

        threading.Thread(target=read, daemon=True).start()

    def call(self, command, payload):
        self.number += 1
        rid = "request-" + str(self.number)
        self.process.stdin.write(
            canonical(dict(schema_version=1, request_id=rid, command=command, payload=payload))
            + b"\n"
        )
        self.process.stdin.flush()
        while True:
            result = self.queue.get(timeout=20)
            if result.get("request_id") == rid:
                return result

    def close(self):
        if not self.process.stdin.closed:
            self.process.stdin.close()
        if self.process.poll() is None:
            self.process.wait(timeout=8)
        self.process.stdout.close()
        self.stderr.close()


@POSIX_ONLY
@pytest.mark.parametrize("stage", ["render", "probe"])
def test_real_worker_death_excludes_old_codec_until_exit_and_then_recovers(tmp_path, stage):
    import json
    import signal
    import time
    from production_artifacts.exports import register_plan

    root = tmp_path / "root"
    root.mkdir()
    source = tmp_path / "source.mp4"
    generate_source(source)
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    store = ProductionStore(SafeRoot(root), "root-one")
    prod = store.create(creation())
    handle = InputHandle.admit(
        SafeRoot(tmp_path),
        source.name,
        sha,
        source_profile_id="stream-main",
        content_profile_id="content-main",
        origin="fixture",
    )
    try:
        src = register_finalized_source(
            store,
            {"input": handle},
            dict(
                production_id=prod["production_id"],
                expected_revision=1,
                operation_id="source",
                input_id="input",
                source_sha256=sha,
                source_profile_id="stream-main",
                content_profile_id="content-main",
                origin="fixture",
            ),
        )["source"]
    finally:
        handle.close()
    plan = register_plan(
        store,
        dict(
            production_id=prod["production_id"],
            expected_revision=2,
            operation_id="plan",
            source_id=src["source_id"],
            title="Fixture",
            description="",
            metadata_revision=1,
            job=dict(
                schema_version=1,
                recording_id=src["source_id"],
                session_id=prod["production_id"],
                game_id="walkthrough",
                show_id="opentech",
                duration_seconds=12.0,
                automatic=False,
                manual_sections=[dict(start_seconds=2.0, end_seconds=10.0)],
                edit=dict(enabled=False),
            ),
        ),
    )

    def start(client, operation):
        current = client.call("production.get", dict(production_id=prod["production_id"]))["value"][
            "production"
        ]
        return client.call(
            "export.start",
            dict(
                production_id=prod["production_id"],
                expected_revision=current["revision"],
                operation_id=operation,
                source_id=src["source_id"],
                source_sha256=sha,
                presets=["youtube-longform-v1"],
                clip_plan_ref=plan["clip_plan_ref"],
                metadata_revision=1,
            ),
        )

    first = StdioClient(root, stage)
    second = None
    codec = None
    try:
        accepted = start(first, "first")
        assert accepted["ok"], accepted
        deadline = time.monotonic() + 10
        while not first.marker.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        marker = json.loads(first.marker.read_text())
        codec = marker["pid"]
        assert marker["worker"] == first.process.pid
        first.process.kill()
        first.process.wait(timeout=5)
        second = StdioClient(root)
        status = second.call(
            "job.get", dict(production_id=prod["production_id"], job_id=accepted["value"]["job_id"])
        )
        assert status["value"]["attempt"]["phase"] not in {
            "interrupted",
            "failed",
            "cancelled",
            "complete",
        }
        assert status["value"]["recovery_required"] is True
        denied = start(second, "while-old-codec-lives")
        assert denied["ok"] is False and denied["error"]["code"] == "export_busy"
        os.kill(codec, signal.SIGCONT)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            status = second.call(
                "job.get",
                dict(production_id=prod["production_id"], job_id=accepted["value"]["job_id"]),
            )
            if status["value"]["attempt"]["phase"] == "interrupted":
                break
            time.sleep(0.02)
        assert status["value"]["attempt"]["phase"] == "interrupted"
        assert status["value"]["recovery_required"] is False
        old_files = {str(p): p.read_bytes() for p in root.rglob("*.encoded")}
        retried = start(second, "explicit-retry")
        assert retried["ok"], retried
        assert retried["value"]["attempt_id"] != accepted["value"]["attempt_id"]
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            end = second.call(
                "job.get",
                dict(production_id=prod["production_id"], job_id=retried["value"]["job_id"]),
            )
            if end["value"]["attempt"]["phase"] == "complete":
                break
            time.sleep(0.02)
        assert end["value"]["attempt"]["phase"] == "complete"
        assert all(Path(path).read_bytes() == data for path, data in old_files.items())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
    finally:
        # Only fresh observed children of this owned harness are released, never persisted PIDs.
        if codec:
            try:
                os.kill(codec, signal.SIGCONT)
            except ProcessLookupError:
                pass
        first.close()
        if second:
            second.close()


@POSIX_ONLY
def test_descendant_keeps_exclusion_and_owner_waits_without_descriptor_leak(tmp_path):
    import select
    import threading
    import time
    from production_artifacts.exports import ExportRunner

    root = tmp_path / "root"
    root.mkdir()
    runner = ExportRunner(ProductionStore(SafeRoot(root), "root-one"))
    lease = runner.lease()
    assert lease is not None
    owner = ProcessOwner(sys.executable)
    owner.execution_fds = (lease,)
    control_read, control_write = os.pipe()
    ready_read, ready_write = os.pipe()
    output = os.open(tmp_path / "written", os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
    result = []
    script = """
import os,sys
if os.fork():os._exit(0)
os.write(int(sys.argv[2]),b'R')
os.read(int(sys.argv[1]),1)
os.write(int(sys.argv[3]),b'finished')
os._exit(0)
"""

    def run():
        result.append(
            owner.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    script,
                    str(control_read),
                    str(ready_write),
                    str(output),
                ],
                pass_fds=(control_read, ready_write, output),
                timeout=5,
            )
        )

    thread = threading.Thread(target=run)
    thread.start()
    try:
        assert select.select([ready_read], [], [], 3)[0]
        assert os.read(ready_read, 1) == b"R"
        os.close(lease)
        lease = None
        deadline = time.monotonic() + 2
        while (
            owner.child is not None and owner.child.poll() is None and time.monotonic() < deadline
        ):
            time.sleep(0.005)
        thread.join(0.1)
        assert thread.is_alive()  # direct child exited; inherited descendant still owns FDs
        contender = runner.lease()
        if contender is not None:
            os.close(contender)
        assert contender is None
        os.write(control_write, b"G")
        thread.join(5)
        assert not thread.is_alive() and result[0].returncode == 0
        assert os.pread(output, 8, 0) == b"finished"
        released = runner.lease()
        assert released is not None
        os.close(released)
    finally:
        if thread.is_alive():
            os.write(control_write, b"G")
            owner.cancel()
            thread.join(5)
        if lease is not None:
            os.close(lease)
        for fd in [control_read, control_write, ready_read, ready_write, output]:
            os.close(fd)


@POSIX_ONLY
@pytest.mark.parametrize("cancel", [False, True])
def test_cancel_or_timeout_releases_inherited_lease_and_owned_descriptors(tmp_path, cancel):
    import threading
    import time
    from production_artifacts.exports import ExportRunner

    root = tmp_path / "root"
    root.mkdir()
    runner = ExportRunner(ProductionStore(SafeRoot(root), "root-one"))
    lease = runner.lease()
    assert lease is not None
    owner = ProcessOwner(sys.executable)
    owner.execution_fds = (lease,)
    result = []

    def run():
        try:
            owner.run(
                [sys.executable, "-B", "-c", "import time;time.sleep(20)"],
                timeout=2 if cancel else 0.05,
            )
        except Fault as error:
            result.append(error.code)

    thread = threading.Thread(target=run)
    thread.start()
    try:
        deadline = time.monotonic() + 2
        while owner.child is None and time.monotonic() < deadline:
            time.sleep(0.005)
        assert owner.child is not None
        if cancel:
            owner.cancel()
        thread.join(5)
        assert not thread.is_alive()
        assert result == ["cancelled" if cancel else "process_timeout"]
        assert owner.child is None
        os.close(lease)
        lease = None
        released = runner.lease()
        assert released is not None
        os.close(released)
    finally:
        if thread.is_alive():
            owner.cancel()
            thread.join(5)
        if lease is not None:
            os.close(lease)


@POSIX_ONLY
def test_escaped_descendant_is_unsettled_excluded_and_eventually_releases(tmp_path):
    import select
    import threading
    import time
    from production_artifacts.exports import ExportRunner

    root = tmp_path / "root"
    root.mkdir()
    runner = ExportRunner(ProductionStore(SafeRoot(root), "root-one"))
    lease = runner.lease()
    assert lease is not None
    owner = ProcessOwner(sys.executable)
    owner.execution_fds = (lease,)
    control_read, control_write = os.pipe()
    ready_read, ready_write = os.pipe()
    script = """
import os,sys
if os.fork():os._exit(0)
os.setsid()
os.write(int(sys.argv[2]),b'R')
os.read(int(sys.argv[1]),1)
os._exit(0)
"""
    result = []

    def run():
        try:
            owner.run(
                [sys.executable, "-B", "-c", script, str(control_read), str(ready_write)],
                pass_fds=(control_read, ready_write),
                timeout=0.05,
            )
        except Fault as error:
            result.append(error.code)

    thread = threading.Thread(target=run)
    thread.start()
    try:
        assert select.select([ready_read], [], [], 3)[0] and os.read(ready_read, 1) == b"R"
        thread.join(7)
        assert not thread.is_alive() and result == ["execution_unsettled"]
        assert owner.execution_unsettled
        os.close(lease)
        lease = None
        busy = runner.lease()
        if busy is not None:
            os.close(busy)
        assert busy is None
        with pytest.raises(Fault, match="execution_unsettled"):
            owner.run([sys.executable, "-B", "-c", "raise SystemExit(99)"])
        os.write(control_write, b"G")
        deadline = time.monotonic() + 3
        released = None
        while time.monotonic() < deadline:
            released = runner.lease()
            if released is not None:
                break
            time.sleep(0.01)
        assert released is not None
        os.close(released)
    finally:
        if thread.is_alive():
            owner.cancel()
        try:
            os.write(control_write, b"G")
        except BrokenPipeError:
            pass
        thread.join(5)
        if lease is not None:
            os.close(lease)
        for fd in [control_read, control_write, ready_read, ready_write]:
            os.close(fd)


@POSIX_ONLY
def test_execution_lease_closes_when_flock_fails(tmp_path, monkeypatch):
    from production_artifacts.exports import ExportRunner
    import production_artifacts.exports as module

    root = tmp_path / "root"
    root.mkdir()
    runner = ExportRunner(ProductionStore(SafeRoot(root), "root-one"))
    opened = []
    real_open = os.open

    def track(path, *args, **kwargs):
        fd = real_open(path, *args, **kwargs)
        if path == ".export-lease":
            opened.append(fd)
        return fd

    def fail(*args):
        raise OSError("flock failed")

    monkeypatch.setattr(module.os, "open", track)
    monkeypatch.setattr(module.fcntl, "flock", fail)
    try:
        with pytest.raises(OSError, match="flock failed"):
            runner.lease()
        assert opened
        with pytest.raises(OSError):
            os.fstat(opened[-1])
    finally:
        for fd in opened:
            try:
                os.close(fd)
            except OSError:
                pass


def test_execution_lease_closes_when_thread_start_fails(prepared, monkeypatch):
    import threading
    from production_artifacts.exports import ExportRunner

    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)

    def fail(*args):
        raise RuntimeError("thread unavailable")

    monkeypatch.setattr(threading.Thread, "start", fail)
    try:
        try:
            runner.start(request)
        except (Fault, RuntimeError):
            pass
        contender = runner.lease()
        if contender is not None:
            os.close(contender)
        assert contender is not None
        job = store.get(request["production_id"])["attempts"][-1]
        assert (
            runner.status(request["production_id"], job["job_id"])["attempt"]["phase"]
            == "interrupted"
        )
    finally:
        if runner.thread is not None and not runner.thread.is_alive():
            try:
                os.close(runner.thread._args[-1])
            except OSError:
                pass


def test_changed_operation_cannot_trigger_recovery_side_effects(prepared, monkeypatch):
    import threading
    from production_artifacts.exports import ExportRunner

    store, source, payload, request, original = seed(prepared)
    runner = ExportRunner(store, FakeMedia)
    monkeypatch.setattr(threading.Thread, "start", lambda _: None)
    accepted = runner.start(request)
    os.close(runner.thread._args[-1])  # Model owner death with no live codec.
    before = store.root.read("state.json")
    try:
        with pytest.raises(Fault, match="operation_conflict"):
            runner.start({**request, "metadata_revision": 2})
        assert store.root.read("state.json") == before
        assert runner.start(request) == accepted
        with pytest.raises(Fault, match="revision_conflict"):
            runner.start({**request, "operation_id": "stale-retry"})
        assert store.root.read("state.json") == before
        with pytest.raises(Fault, match="export_busy"):
            runner.start({**request, "operation_id": "fresh-retry",
                          "expected_revision": accepted["revision"]})
        assert store.root.read("state.json") == before
        worker = Worker(store, {}, runner)
        for command in ("production.get", "production.list"):
            result = worker.handle(canonical(dict(schema_version=1, request_id="bad-query",
                                                  command=command, payload={"unknown": True})))
            assert result["error"]["code"] == "invalid_request"
            assert store.root.read("state.json") == before
    finally:
        assert runner.status(request["production_id"], accepted["job_id"])["attempt"]["phase"] == "interrupted"
