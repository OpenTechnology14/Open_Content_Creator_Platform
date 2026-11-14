"""Actual source-DAR pixels and output-independent test diagnostic termination."""

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/content-creation"))
from production_artifacts.exports import vertical_fit  # noqa: E402
from production_artifacts.models import Video  # noqa: E402
from production_artifacts.media import ProcessOwner  # noqa: E402
from production_artifacts.safety import Fault  # noqa: E402
from production_artifacts.fixture_run import run as fixture_run  # noqa: E402

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="Real POSIX media export; diagnostic/parser/fit tests execute portably",
)


def video(width=720, height=576, sar=Fraction(16, 15)):
    return Video(
        codec="h264",
        width=width,
        height=height,
        sar_num=sar.numerator,
        sar_den=sar.denominator,
        fps_num=30,
        fps_den=1,
        pixel_format="yuv420p",
    )


@pytest.mark.parametrize(
    "source,expected",
    [
        (video(1280, 720, Fraction(1)), (720, 404, 0, 438)),
        (video(), (720, 540, 0, 370)),
        (video(721, 577), (720, 540, 0, 370)),
        (video(360, 640, Fraction(1)), (720, 1280, 0, 0)),
        (video(180, 640, Fraction(1)), (360, 1280, 180, 0)),
        (video(720, 542, Fraction(1)), (720, 542, 0, 368)),
        (video(271, 720, Fraction(1)), (482, 1280, 118, 0)),
        (video(720, 546, Fraction(1001, 1000)), (720, 546, 0, 366)),
    ],
)
def test_vertical_fit_uses_original_dar_even_nearest_lower_tie_and_center(source, expected):
    try:
        fitted = vertical_fit(source)
    except Exception:
        fitted = "unexpected-fit-error"
    assert fitted == expected
    w, h, x, y = expected
    assert all(n % 2 == 0 for n in expected)
    assert x >= 0 and y >= 0 and x + w <= 720 and y + h <= 1280
    assert abs(x - Fraction(720 - w, 2)) <= 1 and abs(y - Fraction(1280 - h, 2)) <= 1
    ideal = Fraction(720) / source.display_aspect if w == 720 else 1280 * source.display_aspect
    assert abs((h if w == 720 else w) - ideal) <= 1


@pytest.mark.parametrize("sar", [Fraction(65535), Fraction(1, 65535)])
def test_unrepresentable_vertical_projection_rejects_instead_of_stretching(sar):
    with pytest.raises(Fault, match="invalid_media"):
        vertical_fit(video(7680, 2, sar) if sar > 1 else video(2, 4320, sar))


def measure_pixels(binary, path, expected):
    raw = subprocess.run(
        [
            binary,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "3",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "-",
        ],
        capture_output=True,
        timeout=20,
    )
    assert raw.returncode == 0 and len(raw.stdout) == 720 * 1280 * 3
    data = raw.stdout

    def pixel(x, y):
        return tuple(data[(y * 720 + x) * 3 : (y * 720 + x) * 3 + 3])

    # Center row/column avoid corner markers; padding is dark and source center white.
    ys = [y for y in range(1280) if min(pixel(360, y)) > 200]
    xs = [x for x in range(720) if min(pixel(x, 640)) > 200]
    measured = (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, min(xs), min(ys))
    assert measured == expected
    w, h, x, y = expected
    # Four independent corner colors prove the complete source is fitted, not cropped.
    positions = [
        (x + w // 32, y + h // 32),
        (x + w - w // 32 - 1, y + h // 32),
        (x + w // 32, y + h - h // 32 - 1),
        (x + w - w // 32 - 1, y + h - h // 32 - 1),
    ]
    colors = [pixel(*position) for position in positions]
    assert colors[0][0] > 180 and max(colors[0][1:]) < 80
    assert colors[1][1] > 180 and max(colors[1][0], colors[1][2]) < 80
    assert colors[2][2] > 180 and max(colors[2][:2]) < 80
    assert min(colors[3][:2]) > 180 and colors[3][2] < 80
    return dict(box=measured, corners=colors, frame_sha256=hashlib.sha256(data).hexdigest())


@POSIX_ONLY
@pytest.mark.parametrize(
    "size,sar,expected",
    [
        ("1280x720", "1/1", (720, 404, 0, 438)),
        ("720x576", "16/15", (720, 540, 0, 370)),
        ("721x577", "16/15", (720, 540, 0, 370)),
    ],
)
def test_real_plain_vertical_pixels_preserve_source_dar_full_content_and_placement(
    tmp_path, size, sar, expected, monkeypatch
):
    monkeypatch.setenv("PYTHONPATH", str(ROOT / "modules/content-creation"))
    owner = ProcessOwner()
    binary = owner.binary()
    source = tmp_path / "source.mp4"
    filters = (
        "format=yuv444p,drawbox=x=0:y=0:w=iw:h=ih:c=white:t=fill,"
        "drawbox=x=0:y=0:w=iw/8:h=ih/8:c=red:t=fill,"
        "drawbox=x=iw-iw/8:y=0:w=iw/8:h=ih/8:c=0x00ff00:t=fill,"
        "drawbox=x=0:y=ih-ih/8:w=iw/8:h=ih/8:c=blue:t=fill,"
        "drawbox=x=iw-iw/8:y=ih-ih/8:w=iw/8:h=ih/8:c=yellow:t=fill,setsar=" + sar
    )
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
            "testsrc=size=" + size + ":rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=48000",
            "-t",
            "12",
            "-vf",
            filters,
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
    evidence = fixture_run(source, sha, tmp_path / "exports", stdio=True)
    assert evidence["status"]["attempt"]["phase"] == "complete"
    observations = []
    for row in evidence["artifacts"]:
        if row["artifact"]["destination"] != "youtube-longform":
            observations.append(
                dict(
                    destination=row["artifact"]["destination"],
                    **measure_pixels(binary, row["path"], expected),
                )
            )
    assert len(observations) == 2
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
    (tmp_path / "pixel-proof.json").write_text(json.dumps(observations, indent=2))


CHILD = r"""
import os,sys,time,threading,ctypes
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
mode=sys.argv[1]
stream=sys.stderr
if mode=='full-pipe':
    try:
        os.set_blocking(2,False)
        for _ in range(2048):
            try:
                if not os.write(2,b'x'*4096):break
            except BlockingIOError:break
        else:os._exit(97)
        os.set_blocking(2,True)
    except Exception:os._exit(97)
if mode in {'held-writer','close-blocked'}:
    lock=threading.Lock();lock.acquire()
    threading.Timer(2,lock.release).start()
    class Held:
        def write(self,x):lock.acquire();lock.release()
        def flush(self):pass
    stream=Held()
if mode=='held-GIL':
    class Held:
        def write(self,x):
            os.write(1,b'GIL-HELD\n')
            if os.name=='nt':
                lib=ctypes.PyDLL('kernel32');lib.Sleep.argtypes=[ctypes.c_ulong];lib.Sleep.restype=None;lib.Sleep(1000)
            else:
                lib=ctypes.PyDLL(None);lib.usleep.argtypes=[ctypes.c_uint];lib.usleep.restype=ctypes.c_int;lib.usleep(1000000)
        def flush(self):pass
    stream=Held()
if mode=='closed':
    stream=open(os.devnull,'w');stream.close()
if mode=='broken':
    class Broken:
        def write(self,x):raise BrokenPipeError('owned broken sink')
        def flush(self):raise BrokenPipeError('owned broken sink')
    stream=Broken()
print('READY '+str(time.monotonic()),flush=True)
d=SessionDiagnostic(stream,0.2)
d.start();d.mark('collection','owned-test[redacted]')
for _ in range(2048):d.mark('teardown','x'*300)
if mode=='full-pipe':print('MARKS_RETURNED',flush=True)
if mode=='close-blocked':d.close();print('DISARMED',flush=True)
time.sleep(3)
"""


def windows_self_exit(code):
    # TRUE's low byte is the claimed ABI fact; unspecified upper bits are retained.
    # Ambiguous NT failure-severity values fail closed even if their low byte is 1.
    return code is not None and code & 255 == 1 and code & 0xC0000000 != 0xC0000000


def native_exit(code):
    return windows_self_exit(code) if os.name == "nt" else code == -signal.SIGALRM


def record_native_result(tmp_path, capsys, mode, code):
    row = dict(
        mode=mode,
        platform=sys.platform,
        returncode=code,
        unsigned_32bit=code & 0xFFFFFFFF,
        hex_32bit=f"0x{code & 0xFFFFFFFF:08x}",
        windows_low_byte=code & 255,
        expected_self_exit=native_exit(code),
    )
    (tmp_path / "native-result.json").write_text(json.dumps(row, indent=2))
    if os.name == "nt" and os.environ.get("GITHUB_ACTIONS") == "true":
        # Finite, fixture-only evidence survives successful pytest capture. Logging
        # remains optional to the separate session protection/termination mechanism.
        with capsys.disabled():
            print("ORCH04_NATIVE_CHILD_RESULT " + json.dumps(row), file=sys.stderr, flush=True)


@pytest.mark.parametrize(
    "code,expected",
    [
        (1, True),
        (0x10001, True),
        (0, False),
        (2, False),
        (97, False),
        (0xC0000001, False),
        (0xC0000005, False),
        (0xC0000409, False),
        (-1, False),
    ],
)
def test_windows_exit_comparison_rejects_setup_refusal_and_native_failure_status(code, expected):
    assert windows_self_exit(code) is expected


@pytest.mark.parametrize(
    "mode", ["full-pipe", "held-writer", "held-GIL", "closed", "broken", "unread", "close-blocked"]
)
def test_native_deadline_exits_without_draining_or_python_writer_progress(tmp_path, mode, capsys):
    p = subprocess.Popen(
        [sys.executable, "-B", "-c", CHILD, mode],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    start = time.monotonic()
    exited = False
    try:
        try:
            p.wait(timeout=3)
            finished_at = time.monotonic()
            exited = True
            record_native_result(tmp_path, capsys, mode, p.returncode)
        except subprocess.TimeoutExpired:
            pass
        # THIS assertion is evaluated before ANY stderr drain. No timeout counts as proof.
        assert exited and (
            native_exit(p.returncode) or (mode == "close-blocked" and p.returncode == 1)
        ), (mode, p.returncode, time.monotonic() - start)
    finally:
        # Only release/read our owned pipes; old behavior can then settle without signalling.
        try:
            out, _ = p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()  # Only this harness-owned, unreaped child; never a group/persisted ID.
            out, _ = p.communicate(timeout=2)
    assert out.startswith(b"READY ")
    armed_at = float(out.splitlines()[0].split()[1])
    assert finished_at - armed_at < 1.0
    assert b"DISARMED" not in out
    if mode == "full-pipe":
        assert b"MARKS_RETURNED" in out
    if mode == "held-GIL":
        assert b"GIL-HELD" in out
    witness = dict(
        mode=mode,
        settled_before_stderr_drain=exited,
        gil_held=b"GIL-HELD" in out,
        marks_returned=b"MARKS_RETURNED" in out,
    )
    (tmp_path / "native-witness.json").write_text(json.dumps(witness, indent=2))
    if os.name == "nt" and os.environ.get("GITHUB_ACTIONS") == "true":
        with capsys.disabled():
            print("ORCH04_NATIVE_CHILD_WITNESS " + json.dumps(witness), file=sys.stderr, flush=True)


@pytest.mark.parametrize("phase", ["collection", "test-teardown"])
def test_readable_session_trace_and_native_exit(tmp_path, phase, capsys):
    code = """import sys,time
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
d=SessionDiagnostic(sys.stderr,0.2);d.start();d.mark(sys.argv[1],'owned-case[private-param]');time.sleep(3)
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code, phase],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    record_native_result(tmp_path, capsys, phase, p.returncode)
    assert native_exit(p.returncode)
    assert b"ORCH04_SESSION_TIMEOUT" in p.stderr and b"<string>" in p.stderr
    assert b"private-param" not in p.stderr


@pytest.mark.parametrize("delay", [0.01, 0.1, 0.18])
def test_native_disarm_never_returns_success_with_a_later_callback(tmp_path, delay, capsys):
    code = """import sys,time
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
d=SessionDiagnostic(sys.stderr,0.2);d.start();time.sleep(float(sys.argv[1]));d.close();print('DISARMED',flush=True);time.sleep(0.25);print('ALIVE',flush=True)
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code, str(delay)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    record_native_result(tmp_path, capsys, "disarm-" + str(delay), p.returncode)
    if b"DISARMED" in p.stdout:
        assert p.returncode == 0 and b"ALIVE" in p.stdout
    else:
        assert native_exit(p.returncode) or p.returncode == 1


def test_protection_is_armed_before_any_startup_logging():
    from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
    import io

    d = SessionDiagnostic(io.StringIO())
    order = []
    d.hard.arm = lambda seconds: order.append("armed")
    d.hard.cancel = lambda: True
    actual = d.mark

    def mark(*args):
        assert order == ["armed"]
        return actual(*args)

    d.mark = mark
    d.start()
    d.close()


@pytest.mark.parametrize(
    "pointer_size,machine,expected",
    [
        (8, "AMD64", True),
        (8, "x86_64", True),
        (8, "ARM64", False),
        (4, "AMD64", False),
        (4, "i386", False),
    ],
)
def test_native_windows_abi_policy_is_exact_not_just_pointer_width(pointer_size, machine, expected):
    from scripts.testing.production_artifacts_diagnostics import _windows_x64_abi

    assert _windows_x64_abi(pointer_size, machine) is expected


@pytest.mark.parametrize(
    "mode", ["creation-failure", "cancellation-failure", "configured-faulthandler"]
)
def test_native_setup_and_cancellation_failures_never_claim_disarmed(tmp_path, mode):
    code = """import sys,time,os,faulthandler
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
mode=sys.argv[1]
class Forbidden:
 def write(self,x):os._exit(97)
 def flush(self):os._exit(97)
d=SessionDiagnostic(Forbidden() if mode=='creation-failure' else sys.stderr,0.5)
if mode=='creation-failure':
 def failed(seconds):raise OSError('controlled native timer creation failure')
 d.hard.arm=failed
if mode=='configured-faulthandler':faulthandler.dump_traceback_later(0.15,file=sys.stderr,exit=True)
d.start()
if mode=='cancellation-failure':d.hard.cancel=lambda:False
d.close();print('DISARMED',flush=True);time.sleep(0.7)
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code, mode],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    if mode == "creation-failure":
        assert p.returncode == 2 and b"DISARMED" not in p.stdout
    elif mode == "cancellation-failure":
        assert p.returncode == 1 and b"DISARMED" not in p.stdout
    else:
        assert p.returncode == 1 and b"Timeout" in p.stderr and b"DISARMED" in p.stdout


@pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX alarm policy only; Windows native timer children execute separately",
)
@pytest.mark.parametrize("policy", ["handler", "timer", "blocked"])
def test_existing_posix_alarm_policy_is_preserved_by_refused_mechanism(tmp_path, policy):
    code = """import os,sys,signal,ctypes
from scripts.testing.production_artifacts_diagnostics import _NativeDeadline
if os.name=='nt':
 # No POSIX mechanism is exercised or inferred on Windows; exact ABI is tested separately.
 from scripts.testing.production_artifacts_diagnostics import _windows_x64_abi
 import platform
 assert _windows_x64_abi(ctypes.sizeof(ctypes.c_void_p),platform.machine())
else:
 policy=sys.argv[1]
 if policy=='handler':signal.signal(signal.SIGALRM,signal.SIG_IGN)
 if policy=='timer':signal.setitimer(signal.ITIMER_REAL,10)
 if policy=='blocked':signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
 handler=signal.getsignal(signal.SIGALRM);mask=signal.pthread_sigmask(signal.SIG_BLOCK,set())
 try:_NativeDeadline().arm(0.1)
 except RuntimeError:pass
 else:raise AssertionError('foreign alarm policy replaced')
 assert signal.getsignal(signal.SIGALRM)==handler
 assert signal.pthread_sigmask(signal.SIG_BLOCK,set())==mask
 if policy=='timer':assert signal.getitimer(signal.ITIMER_REAL)[0]>9
 else:assert signal.getitimer(signal.ITIMER_REAL)==(0,0)
print('policy-preserved')
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code, policy],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    assert p.returncode == 0 and b"policy-preserved" in p.stdout, p.stdout + p.stderr


@pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX pending-alarm cancellation; Windows native timer races execute separately",
)
def test_pending_posix_alarm_is_not_falsely_reported_disarmed(tmp_path):
    code = """import os,signal,time
from scripts.testing.production_artifacts_diagnostics import _NativeDeadline
if os.name=='posix':
 d=_NativeDeadline();d.arm(0.03)
 signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
 time.sleep(0.06)
 assert signal.SIGALRM in signal.sigpending()
 assert d.cancel() is False
 os._exit(0)
else:
 # Actual Windows timer disarm/races execute in other controlled child cases.
 os._exit(0)
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    assert p.returncode == 0, p.stdout + p.stderr


@pytest.mark.parametrize("seconds", ["0", "-1", "nan", "inf", "301"])
def test_invalid_native_deadline_is_refused_in_owned_child(seconds, tmp_path):
    code = """import sys
from scripts.testing.production_artifacts_diagnostics import _NativeDeadline
d=_NativeDeadline()
try:d.arm(float(sys.argv[1]))
except RuntimeError:print('REFUSED')
else:d.cancel();print('UNEXPECTED_ADMISSION')
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code, seconds],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    assert p.returncode == 0 and p.stdout.strip() == b"REFUSED", p.stdout + p.stderr


def test_unicode_marker_bytes_and_pending_queue_are_bounded():
    import io
    from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic

    d = SessionDiagnostic(io.StringIO())
    for _ in range(40):
        d.mark("λ" * 1000, "owner[private]")
    assert d.records.qsize() <= 8
    assert max(map(len, d.records.queue)) <= 512


def test_trace_output_is_best_effort_and_byte_bounded(tmp_path):
    code = """import sys,time,os,faulthandler
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
def oversized(file,**kwargs):os.write(file.fileno(),b'x'*131072)
faulthandler.dump_traceback=oversized
d=SessionDiagnostic(sys.stderr,0.3);d.start();time.sleep(3)
"""
    p = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        timeout=3,
    )
    assert native_exit(p.returncode)
    assert b"ORCH04_SESSION_TIMEOUT" in p.stderr and len(p.stderr) <= 32768 + 1024


@POSIX_ONLY
@pytest.mark.parametrize("fault", ["outer-SAR", "missing-filter"])
def test_vertical_format_and_fixed_graph_faults_preserve_only_valid_longform(
    tmp_path, monkeypatch, fault
):
    import importlib
    from production_artifacts.exports import ExportRunner
    from production_artifacts.worker import Worker

    module = importlib.import_module("production_artifacts.fixture_run")
    exports = importlib.import_module("production_artifacts.exports")
    owner = ProcessOwner()
    source = tmp_path / "source.mp4"
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
            "color=white:size=320x180:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=48000",
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
            str(source),
        ]
    )
    sha = hashlib.sha256(source.read_bytes()).hexdigest()

    class Faulty(ProcessOwner):
        def run(self, argv, **kwargs):
            argv = list(argv)
            if "-filter_complex" in argv and fault == "outer-SAR":
                n = argv.index("-filter_complex") + 1
                argv[n] = argv[n].replace(",fps=30[outv]", ",setsar=2/1,fps=30[outv]")
            return super().run(argv, **kwargs)

    real = exports.render_plan

    def missing_graph(*args, **kwargs):
        command = kwargs["command_runner"]

        def omitted(argv, **options):
            argv = list(argv)
            n = argv.index("-filter_complex")
            del argv[n : n + 2]
            return command(argv, **options)

        kwargs["command_runner"] = omitted
        return real(*args, **kwargs)

    if fault == "missing-filter":
        monkeypatch.setattr(exports, "render_plan", missing_graph)
    monkeypatch.setattr(
        module, "Worker", lambda store, inputs: Worker(store, inputs, ExportRunner(store, Faulty))
    )
    evidence = module.run(source, sha, tmp_path / "outputs")
    assert evidence["status"]["attempt"]["phase"] == "partial"
    assert (
        len(evidence["artifacts"]) == 1
        and evidence["artifacts"][0]["artifact"]["destination"] == "youtube-longform"
    )
    expected = "invalid_media" if fault == "outer-SAR" else "plan_conflict"
    assert {row["error_code"] for row in evidence["status"]["attempt"]["failures"]} == {expected}
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
