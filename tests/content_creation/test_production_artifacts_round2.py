"""R2 regressions: retired identity, explicit helper boundary and real display aspect."""

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "modules/content-creation"))
from production_artifacts.exports import ExportRunner, longform_sar  # noqa: E402
from production_artifacts.fixture_run import run as fixture_run  # noqa: E402
from production_artifacts.media import ProcessOwner  # noqa: E402
from production_artifacts.safety import Fault, SafeRoot  # noqa: E402
from production_artifacts.store import ProductionStore  # noqa: E402

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX process identity/descriptors and actual FFmpeg; portable boundary stays active",
)


@POSIX_ONLY
@pytest.mark.parametrize(
    "mode",
    [
        "cancel-retired",
        "timeout-retired",
        "retire-after-term",
        "concurrent-reaper",
        "concurrent-poll",
        "drop",
    ],
)
def test_signalling_authority_ends_at_reap_but_inherited_exclusion_is_separate(
    tmp_path, monkeypatch, mode
):
    root = tmp_path / "root"
    root.mkdir()
    runner = ExportRunner(ProductionStore(SafeRoot(root), "root-one"))
    lease = runner.lease()
    owner = ProcessOwner(sys.executable)
    owner.execution_fds = (lease,)
    cr, cw = os.pipe()
    rr, rw = os.pipe()
    lr, lw = os.pipe()
    output = os.open(root / "output", os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    script = r"""
import os,sys
control,ready,output,leader_release=map(int,sys.argv[1:5]);mode=sys.argv[5]
if os.fork():
 if mode in ('retire-after-term','concurrent-reaper','concurrent-poll'):os.read(leader_release,1)
 os._exit(0)
os.setsid()
if mode=='drop':
 for fd in range(2,1024):
  if fd not in (control,ready,output):
   try:os.close(fd)
   except OSError:pass
os.write(ready,b'R');os.read(control,1)
os.write(output,b'late-owned-write');os.write(ready,b'D');os._exit(0)
"""
    captured, signals, result = [], [], []
    reaped = threading.Event()
    release_reaper = threading.Event()
    original_popen = subprocess.Popen

    def launch(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        captured.append(child)
        if mode == "concurrent-reaper":
            original_wait = child._try_wait

            def blocked_wait(flags):
                result = original_wait(flags)
                if result[0] == child.pid:
                    reaped.set()  # Real waitpid returned; Popen still holds its lock.
                    assert release_reaper.wait(3)
                return result

            child._try_wait = blocked_wait
        elif mode == "concurrent-poll":
            original_poll = child._internal_poll
            original_status = child._handle_exitstatus

            def blocked_status(*args, **kwargs):
                reaped.set()  # Real _internal_poll waitpid returned under the lock.
                assert release_reaper.wait(3)
                return original_status(*args, **kwargs)

            def controlled_poll(*args, **kwargs):
                if threading.current_thread() is thread:
                    assert reaped.wait(3)  # Let the competing real poll reap first.
                return original_poll(*args, **kwargs)

            child._handle_exitstatus = blocked_status
            child._internal_poll = controlled_poll
        return child

    def observe_only(pgid, sig):
        # All numeric group calls are observations. Never deliver a signal to retired IDs.
        child = captured[0]
        signals.append((sig, child.returncode, reaped.is_set()))
        assert pgid == child.pid
        if mode == "retire-after-term" and sig == signal.SIGTERM:
            os.write(lw, b"G")

    monkeypatch.setattr(subprocess, "Popen", launch)
    monkeypatch.setattr(os, "killpg", observe_only)

    def run():
        try:
            done = owner.run(
                [sys.executable, "-B", "-c", script, str(cr), str(rw), str(output), str(lr), mode],
                pass_fds=(cr, rw, output, lr),
                timeout=0.5 if mode == "timeout-retired" else 10,
            )
            result.append(done.returncode)
        except Fault as error:
            result.append(error.code)

    thread = threading.Thread(target=run)
    reaper = None
    thread.start()
    try:
        assert select.select([rr], [], [], 3)[0] and os.read(rr, 1) == b"R"
        child = captured[0]
        if mode in {"concurrent-reaper", "concurrent-poll"}:

            def poll_until_reaped():
                while child.poll() is None:
                    time.sleep(0.001)

            reaper = threading.Thread(
                target=child.wait if mode == "concurrent-reaper" else poll_until_reaped
            )
            reaper.start()
            os.write(lw, b"G")
            assert reaped.wait(3)
            owner.cancel()
            time.sleep(0.1)
            assert signals == []  # Poll cannot acquire reaper lock; returncode still None.
            release_reaper.set()
        elif mode == "retire-after-term":
            owner.cancel()
        else:
            deadline = time.monotonic() + 3
            while child.returncode is None and time.monotonic() < deadline:
                time.sleep(0.005)  # Only production code reaps here.
            assert child.returncode == 0
            if mode == "cancel-retired":
                owner.cancel()
        os.close(lease)
        lease = None
        thread.join(6)
        assert not thread.is_alive()
        if mode == "drop":
            assert result == [0] and signals == []
        else:
            assert result == ["execution_unsettled"] and owner.execution_unsettled
            if mode == "retire-after-term":
                assert signals == [(signal.SIGTERM, None, False)]
            else:
                assert signals == []
        contender = runner.lease()
        if contender is not None:
            os.close(contender)
        assert (contender is None) == (mode != "drop")
        assert os.pread(output, 100, 0) == b""
        os.write(cw, b"G")
        assert select.select([rr], [], [], 3)[0] and os.read(rr, 1) == b"D"
        assert os.pread(output, 100, 0) == b"late-owned-write"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            released = runner.lease()
            if released is not None:
                os.close(released)
                break
            time.sleep(0.005)
        else:
            pytest.fail("descendant exited without releasing exclusion")
    finally:
        release_reaper.set()
        for fd in (cw, lw):
            try:
                os.write(fd, b"G")
            except BrokenPipeError:
                pass
        thread.join(6)
        if reaper:
            reaper.join(3)
        if lease is not None:
            os.close(lease)
        for fd in (cr, cw, rr, rw, lr, lw, output):
            os.close(fd)


@POSIX_ONLY
@pytest.mark.parametrize("policy", ["ignored", "handler"])
def test_unsupported_sigchld_policy_fails_before_launcher_or_process_side_effects(tmp_path, policy):
    script = r"""
import os,signal,sys
from production_artifacts.media import ProcessOwner
from production_artifacts.worker import launch_registry
from production_artifacts.safety import Fault
signal.signal(signal.SIGCHLD,signal.SIG_IGN if sys.argv[1]=='ignored' else lambda *a:None)
def audit(event,args):
 if event in ('open','os.mkdir','subprocess.Popen'):raise AssertionError('side effect '+event)
sys.addaudithook(audit)
for action in (lambda:ProcessOwner(sys.executable).run([sys.executable,'-c','pass']),lambda:launch_registry(-1)):
 try:action()
 except Fault as error:assert error.code=='platform_unavailable'
 else:raise AssertionError('unsupported reaper policy admitted')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, policy],
        capture_output=True,
        env={
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "modules/content-creation"),
        },
        timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not list(tmp_path.iterdir())


def aspect_probe(binary, path):
    result = subprocess.run(
        [
            binary,
            "-nostdin",
            "-hide_banner",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-vf",
            "sidedata=mode=delete,showinfo=checksum=0",
            "-frames:v",
            "1",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    text = result.stderr.decode()
    line = next(line for line in text.splitlines() if "Video:" in line)
    size = re.search(r"\b(\d{2,5})x(\d{2,5})\b", line)
    sar = re.search(r"\bsar:(\d+)/(\d+)\b", text)
    assert size and sar, text
    measured = Fraction(int(sar[1]), int(sar[2]))
    width, height = int(size[1]), int(size[2])
    return (width, height), measured, measured * width / height


def rejected_aspect_diagnostics(binary, source, output_root, evidence):
    """Bounded test-only observations; never changes worker admission or portable state."""
    import imageio_ffmpeg
    from production_artifacts.safety import hash_fd

    source_record = evidence["transcript"][1]["response"]["value"]["source"]
    expected = source_record["video"]
    from production_artifacts.models import Video

    expected_sar = longform_sar(Video.model_validate(expected))
    expected_dar = expected_sar * (expected["width"] // 2 * 2) / (expected["height"] // 2 * 2)
    observations = []
    candidates = [("source", source)] + [
        ("longform-" + path.name, path) for path in sorted(output_root.rglob("video.mp4*"))[:2]
    ]
    for label, path in candidates:
        root = SafeRoot(path.parent)
        fd = root.open(path.name)
        owner = ProcessOwner(binary)
        try:
            raw = owner.run(
                [
                    binary,
                    "-nostdin",
                    "-loglevel",
                    "info",
                    "-i",
                    f"/dev/fd/{fd}",
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0",
                    "-vf",
                    "sidedata=mode=delete,showinfo=checksum=0",
                    "-frames:v",
                    "1",
                    "-f",
                    "null",
                    "-",
                ],
                pass_fds=(fd,),
                timeout=20,
            )
            text = raw.stderr.decode(errors="replace")
            observation = dict(
                label=label,
                bytes=os.fstat(fd).st_size,
                sha256=hash_fd(fd),
                banner=[
                    line[:600]
                    for line in text.splitlines()
                    if line.startswith(("ffmpeg version", "configuration:", "libav"))
                ][:8],
                stream_lines=[
                    line[:500]
                    for line in text.splitlines()
                    if "Stream #0:" in line and ("Video:" in line or "Audio:" in line)
                ][:4],
                decoded_sar=re.findall(r"\bsar:(\d+)/(\d+)\b", text)[:4],
            )
            try:
                media = owner.inspect(fd)
                observation["media"] = media.model_dump(mode="json")
                observation["dar"] = str(media.video.display_aspect)
                observation["predicate_results"] = dict(
                    video_codec=media.video.codec == "h264",
                    pixel_format=media.video.pixel_format == "yuv420p",
                    audio_codec=media.audio.codec == "aac",
                    duration=abs(media.duration_seconds - source_record["duration_seconds"]) <= 0.3,
                    longform_dimensions=(media.video.width, media.video.height)
                    == (expected["width"] // 2 * 2, expected["height"] // 2 * 2),
                    longform_display_aspect=media.video.display_aspect == expected_dar,
                )
            except Fault as error:
                observation["probe_error"] = error.code
            observations.append(observation)
        finally:
            os.close(fd)
            root.close()
    report = dict(
        imageio_ffmpeg=imageio_ffmpeg.__version__,
        executable=Path(binary).name,
        executable_sha256=hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
        expected_source=source_record,
        expected_dar=str(expected_dar),
        phase=evidence["status"]["attempt"]["phase"],
        failures=evidence["status"]["attempt"]["failures"],
        observations=observations,
    )
    assert len(json.dumps(report).encode()) <= 16384
    return report


@POSIX_ONLY
@pytest.mark.parametrize("size", ["720x576", "721x577"])
def test_real_anamorphic_stdio_longform_preserves_display_aspect_after_even_rounding(
    tmp_path, monkeypatch, size
):
    monkeypatch.setenv(
        "PYTHONPATH", str(Path(__file__).resolve().parents[2] / "modules/content-creation")
    )
    owner = ProcessOwner()
    binary = owner.binary()
    source = tmp_path / "anamorphic.mp4"
    owner.run(
        [
            binary,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size={size}:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "12",
            "-vf",
            "format=yuv444p,setsar=16/15",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv444p",
            "-c:a",
            "aac",
            str(source),
        ]
    )
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    evidence = fixture_run(source, before, tmp_path / "exports", stdio=True)
    if evidence["status"]["attempt"]["phase"] != "complete":
        diagnostics = rejected_aspect_diagnostics(binary, source, tmp_path / "exports", evidence)
        sys.stderr.write(
            "ORCH04_CI04_DIAGNOSTICS " + json.dumps(diagnostics, sort_keys=True) + "\n"
        )
    assert evidence["status"]["attempt"]["phase"] == "complete", evidence["status"]
    assert any(
        row["artifact"]["destination"] == "youtube-longform" for row in evidence["artifacts"]
    )
    row = next(
        row for row in evidence["artifacts"] if row["artifact"]["destination"] == "youtube-longform"
    )
    source_size, source_sar, source_dar = aspect_probe(binary, source)
    out_size, out_sar, out_dar = aspect_probe(binary, Path(row["path"]))
    admitted_video = evidence["transcript"][1]["response"]["value"]["source"]["video"]
    from production_artifacts.models import Video

    expected_sar = longform_sar(Video.model_validate(admitted_video))
    assert out_sar == expected_sar
    intended_sar = source_dar * out_size[1] / out_size[0]
    assert abs(out_sar - intended_sar) * out_size[0] <= Fraction(1, 2)
    assert abs(1 / out_sar - 1 / intended_sar) * out_size[1] <= Fraction(1, 2)
    assert out_size == tuple(d // 2 * 2 for d in source_size)
    assert out_size[0] <= source_size[0] and out_size[1] <= source_size[1]
    video = row["artifact"]["media"]["video"]
    assert Fraction(video["sar_num"], video["sar_den"]) == out_sar
    elementary = tmp_path / "coded-longform.h264"
    owner.run(
        [
            binary,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-n",
            "-i",
            row["path"],
            "-map",
            "0:v:0",
            "-c:v",
            "copy",
            "-bsf:v",
            "h264_mp4toannexb",
            "-an",
            "-f",
            "h264",
            str(elementary),
        ]
    )
    coded_size, coded_sar, coded_dar = aspect_probe(binary, elementary)
    assert coded_size == out_size
    assert coded_sar == out_sar, "coded SPS and container-delivered aspect must agree"
    assert coded_dar == out_dar
    admitted = evidence["transcript"][1]["response"]["value"]["source"]["video"]
    assert Fraction(admitted["sar_num"], admitted["sar_den"]) == source_sar
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    assert evidence["status"]["attempt"]["phase"] == "complete"


@POSIX_ONLY
@pytest.mark.parametrize(
    "unsupported",
    [
        "runtime",
        "source-audit",
        "__init__",
        "_wait",
        "_internal_poll",
        "_try_wait",
        "_handle_exitstatus",
    ],
)
def test_unsupported_private_reaper_runtime_fails_before_launch(monkeypatch, unsupported):
    import production_artifacts.media as module

    def forbidden(*args, **kwargs):
        raise AssertionError("unsupported runtime reached process launch")

    with monkeypatch.context() as patch:
        if unsupported == "runtime":
            patch.setattr(module, "SUPPORTED_CPYTHON", frozenset())
        elif unsupported == "source-audit":
            patch.setattr(module, "_REAPERS_AUDITED", False)
        else:
            patch.setattr(module._POPEN, unsupported, None)
        patch.setattr(subprocess, "Popen", forbidden)
        with pytest.raises(Fault, match="platform_unavailable"):
            ProcessOwner(sys.executable).run([sys.executable, "-c", "pass"])


@POSIX_ONLY
@pytest.mark.parametrize("frame_sar", [None, "0/1", "1/0", "65536/1", "1/65536", "-1/1"])
def test_unknown_or_invalid_decoded_aspect_is_rejected_without_square_assumption(
    tmp_path, frame_sar
):
    path = tmp_path / "source.mp4"
    path.write_bytes(b"\0\0\0\x10ftypisom0000")
    header = b"Input #0, mov, from x:\nDuration: 00:00:12.00\nStream #0:0 Video: h264, yuv420p, 720x576 [SAR 16:15 DAR 4:3], 30 fps\nStream #0:1 Audio: aac, 48000 Hz, mono\n"

    class Probe(ProcessOwner):
        def run(self, argv, **kwargs):
            assert "-xerror" not in argv  # Reject before expensive full decode.
            measured = (
                b""
                if frame_sar is None
                else ("[Parsed_showinfo_0] n:0 fmt:yuv420p sar:" + frame_sar + " s:720x576\n").encode()
            )
            data = header + measured + b"frame=1\nprogress=end\n"
            kwargs["stderr_observer"](data)
            return subprocess.CompletedProcess(argv, 0, stderr=data)

    fd = os.open(path, os.O_RDONLY)
    try:
        with pytest.raises(Fault, match="invalid_media"):
            Probe(sys.executable).inspect(fd)
    finally:
        os.close(fd)


@POSIX_ONLY
def test_unexpected_sigchld_change_revokes_signal_authority_without_guessing(tmp_path, monkeypatch):
    cr, cw = os.pipe()
    rr, rw = os.pipe()
    owner = ProcessOwner(sys.executable)
    observed, result = [], []
    monkeypatch.setattr(os, "killpg", lambda *args: observed.append(args))

    def run():
        try:
            owner.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    "import os,sys;os.write(int(sys.argv[2]),b'R');os.read(int(sys.argv[1]),1)",
                    str(cr),
                    str(rw),
                ],
                pass_fds=(cr, rw),
                timeout=10,
            )
        except Fault as error:
            result.append(error.code)

    original = signal.getsignal(signal.SIGCHLD)
    thread = threading.Thread(target=run)
    thread.start()
    child = None
    try:
        assert select.select([rr], [], [], 3)[0] and os.read(rr, 1) == b"R"
        child = owner.child
        assert child is not None
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        owner.cancel()
        thread.join(6)
        assert not thread.is_alive() and result == ["execution_unsettled"]
        assert observed == []
    finally:
        signal.signal(signal.SIGCHLD, original)
        os.write(cw, b"G")
        thread.join(6)
        if child is not None:
            child.wait(timeout=3)
        for fd in (cr, cw, rr, rw):
            os.close(fd)


@POSIX_ONLY
@pytest.mark.parametrize(
    "size,bad_sar", [("720x576", "1/1"), ("721x577", "25187/23621"), ("721x577", "4038/3786")]
)
def test_actual_distorted_longform_is_rejected_while_valid_clips_survive(
    tmp_path, monkeypatch, size, bad_sar
):
    import importlib
    from production_artifacts.worker import Worker

    module = importlib.import_module("production_artifacts.fixture_run")
    owner = ProcessOwner()
    source = tmp_path / "anamorphic.mp4"
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
            f"testsrc=size={size}:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "12",
            "-vf",
            "format=yuv444p,setsar=16/15",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv444p",
            "-c:a",
            "aac",
            str(source),
        ]
    )
    sha = hashlib.sha256(source.read_bytes()).hexdigest()

    class DistortingOwner(ProcessOwner):
        def run(self, argv, **kwargs):
            argv = list(argv)
            if "-vf" in argv:
                index = argv.index("-vf") + 1
                if argv[index].startswith("scale=trunc(iw/2)"):
                    argv[index] += (
                        f",setsar=sar={bad_sar}:max=32767"  # Actual codec fault, not fake metadata.
                    )
            return super().run(argv, **kwargs)

    monkeypatch.setattr(
        module,
        "Worker",
        lambda store, inputs: Worker(store, inputs, ExportRunner(store, DistortingOwner)),
    )
    evidence = module.run(source, sha, tmp_path / "exports")
    attempt = evidence["status"]["attempt"]
    assert attempt["phase"] == "partial"
    diagnostics = rejected_aspect_diagnostics(
        owner.binary(), source, tmp_path / "exports", evidence
    )
    output_observations = [row for row in diagnostics["observations"] if row["label"] != "source"]
    assert output_observations
    assert all(
        row["predicate_results"]["longform_display_aspect"] is False for row in output_observations
    )
    assert diagnostics["expected_dar"] == ("4/3" if size == "720x576" else "20185/15144")
    if size == "721x577":
        ideal = Fraction(46144, 43275)
        wrong = Fraction(bad_sar)
        assert abs(wrong - ideal) * 720 < Fraction(1, 2)
        assert abs(1 / wrong - 1 / ideal) * 576 < Fraction(1, 2)
    assert attempt["failures"] == [dict(preset="youtube-longform-v1", error_code="invalid_media")]
    assert {row["artifact"]["destination"] for row in evidence["artifacts"]} == {
        "youtube-shorts",
        "tiktok",
    }
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sha


@POSIX_ONLY
def test_large_ancillary_sei_cannot_evict_decoded_aspect_measurement(tmp_path):
    from production_artifacts.media import validate_fd

    owner = ProcessOwner()
    source = tmp_path / "large-ancillary.mp4"
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
            "-bsf:v",
            "h264_metadata=sei_user_data=00112233445566778899aabbccddeeff+" + "x" * 70000,
            str(source),
        ]
    )
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    fd = os.open(source, os.O_RDONLY)
    try:
        measured = None
        failure = None
        try:
            measured = validate_fd(owner, fd, sha)
        except Fault as error:
            failure = error.code
        assert measured is not None, f"valid ancillary-data media rejected: {failure}"
        assert (measured.video.sar_num, measured.video.sar_den) == (1, 1)
    finally:
        os.close(fd)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sha


@POSIX_ONLY
def test_actual_audited_runtime_executes_owned_child_without_version_spoofing():
    owner = ProcessOwner(sys.executable)
    result, failure = None, None
    try:
        result = owner.run(
            [sys.executable, "-B", "-c", "import sys;assert sys.version_info[:2]>=(3,11)"]
        )
    except Fault as error:
        failure = error.code
    assert result is not None, f"actual runtime {sys.version} rejected: {failure}"
    assert result.returncode == 0


@POSIX_ONLY
@pytest.mark.parametrize("invalid", ["fingerprint", "unavailable"])
def test_unverified_reaper_source_is_rejected_before_effects(monkeypatch, invalid):
    import production_artifacts.media as module

    def forbidden(*args, **kwargs):
        raise AssertionError("unverified runtime reached child launch")

    with monkeypatch.context() as patch:
        if invalid == "fingerprint":
            patch.setitem(module._REAPER_SOURCE_SHA256, "__init__", "0" * 64)
        else:
            patch.setattr(
                module.inspect,
                "getsource",
                lambda _: (_ for _ in ()).throw(OSError("stdlib source unavailable")),
            )
        verified = module._has_audited_reapers()
        assert verified is False
        patch.setattr(module, "_REAPERS_AUDITED", verified)
        patch.setattr(subprocess, "Popen", forbidden)
        with pytest.raises(Fault, match="platform_unavailable"):
            ProcessOwner(sys.executable).run([sys.executable, "-B", "-c", "pass"])


@POSIX_ONLY
@pytest.mark.parametrize(
    "shape",
    [
        "with-empty-type-params",
        "without-type-params",
        "nonempty-type-params",
        "unknown-empty-field",
    ],
)
def test_reaper_fingerprint_normalizes_only_known_empty_ast_schema_fields(monkeypatch, shape):
    import production_artifacts.media as module

    original = module.ast.parse

    def shaped_parse(*args, **kwargs):
        tree = original(*args, **kwargs)
        for node in list(module.ast.walk(tree)):
            if isinstance(node, module.ast.FunctionDef):
                fields = tuple(field for field in node._fields if field != "type_params")
                if shape == "without-type-params":
                    node._fields = fields
                    if hasattr(node, "type_params"):
                        del node.type_params
                else:
                    node._fields = (*fields, "type_params")
                    node.type_params = (
                        []
                        if shape != "nonempty-type-params"
                        else [module.ast.Name(id="Unreviewed", ctx=module.ast.Load())]
                    )
                if shape == "unknown-empty-field":
                    node._fields = (*node._fields, "unreviewed_empty_field")
                    node.unreviewed_empty_field = []
        return tree

    with monkeypatch.context() as patch:
        patch.setattr(module.ast, "parse", shaped_parse)
        verified = module._has_audited_reapers()
    assert verified is (shape in {"with-empty-type-params", "without-type-params"})


@POSIX_ONLY
def test_compiled_altered_reaper_source_is_rejected_before_launch(tmp_path, monkeypatch):
    import importlib.util
    import textwrap
    import production_artifacts.media as module

    real = module.inspect.getsource(module._REAPERS["_internal_poll"])
    altered = textwrap.dedent(real).replace(
        "if self.returncode is None:", "if self.returncode is not None:", 1
    )
    assert altered != textwrap.dedent(real)
    path = tmp_path / "altered_reaper.py"
    path.write_text(altered)
    spec = importlib.util.spec_from_file_location("owned_altered_reaper", path)
    candidate = importlib.util.module_from_spec(spec)
    # The function's captured defaults need these names; its altered body is never run.
    candidate._waitpid = os.waitpid
    candidate._WNOHANG = os.WNOHANG
    import errno

    candidate.errno = errno
    spec.loader.exec_module(candidate)

    def forbidden(*args, **kwargs):
        raise AssertionError("altered reaper reached child launch")

    with monkeypatch.context() as patch:
        patch.setitem(module._REAPERS, "_internal_poll", candidate._internal_poll)
        verified = module._has_audited_reapers()
        assert verified is False
        patch.setattr(module, "_REAPERS_AUDITED", verified)
        patch.setattr(subprocess, "Popen", forbidden)
        with pytest.raises(Fault, match="platform_unavailable"):
            ProcessOwner(sys.executable).run([sys.executable, "-B", "-c", "pass"])


@pytest.mark.parametrize(
    "sar", [Fraction(7, 5), Fraction(7, 3), Fraction(5, 2), Fraction(22, 21), Fraction(251, 100), Fraction(3, 7), Fraction(1, 65535), Fraction(65535), Fraction(7, 6)]
)
def test_longform_canonical_ratio_is_closest_bounded_with_stable_ties(monkeypatch, sar):
    import production_artifacts.exports as module

    monkeypatch.setattr(module, "LONGFORM_SAR_LIMIT", 4)
    # Independent exhaustive oracle includes every allowed pair, not just near numerators.
    allowed = {Fraction(n, d) for n in range(1, 5) for d in range(1, 5)}
    expected = min(allowed, key=lambda q: (abs(q - sar), q.denominator, q.numerator))
    assert module._closest_longform_ratio(sar) == expected


def test_odd_ratio_has_one_canonical_codec_representation():
    from production_artifacts.models import Video

    video = Video(
        codec="h264",
        width=721,
        height=577,
        sar_num=16,
        sar_den=15,
        fps_num=30,
        fps_den=1,
        pixel_format="yuv444p",
    )
    result = longform_sar(video)
    assert result == Fraction(4037, 3786)
    assert result != Fraction(25187, 23621)  # Old MOV reader's closer ratio is not canonical.
    ideal = video.display_aspect * 576 / 720
    assert abs(result - ideal) * 720 == Fraction(72, 1820435)
    assert abs(1 / result - 1 / ideal) * 576 == Fraction(81, 2910677)


@pytest.mark.parametrize("size", [(7680, 2), (2, 4320)])
def test_unrepresentable_subpixel_geometry_is_rejected_on_either_axis(size):
    from production_artifacts.models import Video

    video = Video(
        codec="h264",
        width=size[0],
        height=size[1],
        sar_num=65535,
        sar_den=65527,
        fps_num=30,
        fps_den=1,
        pixel_format="yuv420p",
    )
    with pytest.raises(Fault, match="invalid_media"):
        longform_sar(video)


@pytest.mark.parametrize(
    "sar,expected", [(Fraction(7, 4), Fraction(2)), (Fraction(4, 7), Fraction(1, 2))]
)
def test_half_pixel_boundary_is_inclusive_and_deterministic(monkeypatch, sar, expected):
    import production_artifacts.exports as module
    from production_artifacts.models import Video

    monkeypatch.setattr(module, "LONGFORM_SAR_LIMIT", 4)
    video = Video(
        codec="h264",
        width=2,
        height=2,
        sar_num=sar.numerator,
        sar_den=sar.denominator,
        fps_num=30,
        fps_den=1,
        pixel_format="yuv420p",
    )
    actual = None
    try:
        actual = module.longform_sar(video)
    except Fault:
        pass
    assert actual == expected
    assert max(abs(expected - sar) * 2, abs(1 / expected - 1 / sar) * 2) == Fraction(1, 2)
