"""R3: one no-transform geometry across the whole decoded timeline; no header inference."""

from collections import Counter
from fractions import Fraction
import hashlib
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "modules/content-creation"))
from production_artifacts.geometry import GeometryScan, MAX_LINE  # noqa: E402
from production_artifacts.media import ProcessOwner  # noqa: E402
from production_artifacts.safety import Fault, SafeRoot  # noqa: E402
from production_artifacts.sources import InputHandle, register_finalized_source  # noqa: E402
from production_artifacts.store import ProductionStore  # noqa: E402
from test_production_artifacts import creation  # noqa: E402

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix", reason="Real POSIX descriptor/codec execution; parser tests stay portable"
)


def fault_code(action):
    try:
        action()
    except Fault as error:
        return error.code
    except Exception:
        return "unexpected_exception"
    return None


def frame(n=0, size="720x576", sar="1/1", fmt="yuv420p"):
    return f"[Parsed_showinfo_1 @ 0x123] n: {n} pts: 0 fmt:{fmt} sar:{sar} s:{size} i:P\n".encode()


def end(count):
    return f"frame={count}\nprogress=end\n".encode()


def test_incremental_parser_matches_frames_across_every_byte_boundary():
    data = frame() + frame(1) + end(2)
    for cut in range(len(data) + 1):
        scan = GeometryScan()
        scan.feed(data[:cut])
        scan.feed(data[cut:])
        assert scan.finish() == (720, 576, Fraction(1), "yuv420p")
        assert scan.frames == 2 and not scan.pending


@pytest.mark.parametrize("change", ["size", "sar", "format", "matrix", "spherical"])
def test_late_changes_beyond_diagnostic_tail_are_rejected(change):
    scan = GeometryScan()
    scan.feed(frame())
    for _ in range(3000):
        scan.feed(b"irrelevant bounded diagnostic " + b"x" * 64 + b"\n")
    assert len(scan.pending) == 0
    changed = {
        "size": frame(1, size="640x480"),
        "sar": frame(1, sar="16/15"),
        "format": frame(1, fmt="yuv444p"),
        "matrix": b"[Parsed_showinfo_1 @ 0x123] side data - 3x3 displaymatrix: rotation of -90.00 degrees\n",
        "spherical": b"[Parsed_showinfo_1 @ 0x123] side data - spherical mapping\n",
    }[change]
    with pytest.raises(Fault, match="invalid_media"):
        scan.feed(changed)


@pytest.mark.parametrize(
    "bad",
    [
        b"[Parsed_showinfo_1 @ 0x123] n:0 fmt:yuv420p s:720x576\n",  # missing SAR
        b"[Parsed_showinfo_1 @ 0x123] n:0 fmt:yuv420p sar:1/1\n",  # missing dimensions
        frame().replace(b"sar:1/1", b"sar:0/1"),
        frame().replace(b"sar:1/1", b"sar:1/0"),
        b"frame=10368001\n",
        frame().replace(b"sar:1/1", b"sar:65536/1"),
        frame().replace(b"sar:1/1", b"sar:1/65536"),
        frame(size="1x576"),
        frame(size="720x1"),
        frame(size="720x5000"),
        frame().replace(b"720x576", b"90000x576"),
        frame().replace(b"n: 0", b"n: 2"),
        b"[Parsed_showinfo_1 @ 0x123] n:0 " + b"x" * MAX_LINE,
    ],
)
def test_missing_malformed_or_oversized_per_frame_measurement_rejects(bad):
    assert fault_code(lambda: GeometryScan().feed(bad)) == "invalid_media"


@pytest.mark.parametrize(
    "data",
    [
        b"",
        frame(),
        frame()[:-1],
        end(1),
        frame() + end(2),
        frame() + b"frame=1\nprogress=en",
        frame() + b"frame=invalid\nprogress=end\n",
        frame() + b"frame=1\n",
        frame() + end(1) + frame(1)[:-1],
    ],
)
def test_incomplete_or_missing_full_timeline_measurements_reject(data):
    def complete():
        scan = GeometryScan()
        scan.feed(data)
        scan.finish()

    assert fault_code(complete) == "invalid_media"


def test_frame_limit_fails_closed_without_unbounded_count_or_buffer(monkeypatch):
    import production_artifacts.geometry as module

    monkeypatch.setattr(module, "MAX_FRAMES", 1)
    scan = GeometryScan()
    scan.feed(frame())
    with pytest.raises(Fault, match="invalid_media"):
        scan.feed(frame(1))
    assert scan.frames == 1 and len(scan.pending) <= MAX_LINE


def codec(args):
    owner = ProcessOwner()
    owner.run([owner.binary(), "-nostdin", "-hide_banner", "-loglevel", "error", *args])


@pytest.fixture(scope="module")
def base_media(tmp_path_factory):
    if os.name != "posix":
        pytest.skip("Real POSIX media fixture; portable parser cases execute on Windows")
    root = tmp_path_factory.mktemp("geometry-media")
    path = root / "base.mp4"
    codec(
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=720x576:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=48000",
            "-t",
            "12",
            "-vf",
            "setsar=16/15",
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
    return path


def reject_publication(tmp_path, source):
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    root = tmp_path / "root"
    root.mkdir()
    store = ProductionStore(SafeRoot(root), "root-one")
    production = store.create(creation())
    before = store.root.read("state.json")
    handle = InputHandle.admit(
        SafeRoot(source.parent),
        source.name,
        sha,
        source_profile_id="stream-main",
        content_profile_id="content-main",
        origin="fixture",
    )
    try:
        caught = None
        try:
            register_finalized_source(
                store,
                {"input": handle},
                dict(
                    production_id=production["production_id"],
                    expected_revision=1,
                    operation_id="register",
                    input_id="input",
                    source_sha256=sha,
                    source_profile_id="stream-main",
                    content_profile_id="content-main",
                    origin="fixture",
                ),
            )
        except Fault as error:
            caught = error.code
        assert caught == "invalid_media"
        assert store.root.read("state.json") == before
        assert store.get(production["production_id"])["sources"] == []
        assert not list(root.rglob("source.json"))
        assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
    finally:
        handle.close()


@POSIX_ONLY
@pytest.mark.parametrize(
    "matrix",
    [
        (0, 65536, 0, -65536, 0, 0, 0, 0, 1 << 30),  # valid quarter turn, intentionally unsupported
        (-65536, 0, 0, 0, -65536, 0, 0, 0, 1 << 30),
        (0, -65536, 0, 65536, 0, 0, 0, 0, 1 << 30),
        (65536, 0, 0, 0, -65536, 0, 0, 0, 1 << 30),  # reflection
        (46341, 46341, 0, -46341, 46341, 0, 0, 0, 1 << 30),  # non-quarter turn
    ],
)
@pytest.mark.parametrize("square_pixels", [False, True])
def test_real_display_transforms_are_explicitly_unavailable_before_publication(
    tmp_path, base_media, matrix, square_pixels
):
    source = tmp_path / "matrix.mp4"
    if square_pixels:
        codec(
            [
                "-i",
                str(base_media),
                "-c",
                "copy",
                "-bsf:v",
                "h264_metadata=sample_aspect_ratio=1/1",
                "-aspect",
                "5:4",
                str(source),
            ]
        )
        data = bytearray(source.read_bytes())
    else:
        data = bytearray(base_media.read_bytes())
    offset = data.index(b"tkhd") - 4
    assert data[offset + 8] == 0
    struct.pack_into(">9i", data, offset + 48, *matrix)
    source.write_bytes(data)
    # Independent fixed-codec observation confirms retained matrix-bearing frames under noautorotate.
    binary = ProcessOwner().binary()
    raw = subprocess.run(
        [
            binary,
            "-nostdin",
            "-hide_banner",
            "-noautorotate",
            "-i",
            str(source),
            "-vf",
            "sidedata=mode=delete:type=SEI_UNREGISTERED,showinfo=checksum=0",
            "-frames:v",
            "2",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        timeout=15,
    )
    assert raw.returncode == 0 and b"side data - 3x3 displaymatrix" in raw.stderr
    assert b"s:720x576" in raw.stderr
    reject_publication(tmp_path, source)


def make_variable(tmp_path, first_frames, first_size="160x90", second_size="128x96", sar="1/1"):
    raw = tmp_path / "variable.h264"
    parts = []
    for index, (count, size) in enumerate(
        [(first_frames, first_size), (360 - first_frames, second_size)]
    ):
        path = tmp_path / f"part-{index}.h264"
        codec(
            [
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size={size}:rate=30",
                "-frames:v",
                str(count),
                "-vf",
                "setsar=" + sar,
                "-c:v",
                "libx264",
                "-bf",
                "0",
                "-threads",
                "2",
                "-pix_fmt",
                "yuv420p",
                "-f",
                "h264",
                str(path),
            ]
        )
        parts.append(path.read_bytes())
    raw.write_bytes(b"".join(parts))
    source = tmp_path / "variable.mp4"
    codec(
        [
            "-fflags",
            "+genpts",
            "-r",
            "30",
            "-i",
            str(raw),
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=48000",
            "-t",
            "12",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(source),
        ]
    )
    result = subprocess.run(
        [
            ProcessOwner().binary(),
            "-nostdin",
            "-hide_banner",
            "-noautorotate",
            "-i",
            str(source),
            "-vf",
            "showinfo=checksum=0",
            "-an",
            "-fps_mode",
            "passthrough",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        timeout=20,
    )
    geometries = re.findall(rb"sar:(\d+/\d+) s:(\d+x\d+)", result.stderr)
    counts = Counter(geometries)
    assert result.returncode == 0 and set(counts) == {
        (sar.encode(), first_size.encode()),
        (sar.encode(), second_size.encode()),
    }
    assert geometries[0][1] == first_size.encode() and geometries[-1][1] == second_size.encode()
    return source


@POSIX_ONLY
@pytest.mark.parametrize("first_frames", [2, 358])
def test_real_early_and_near_end_dimension_changes_reject_without_source_admission(
    tmp_path, first_frames
):
    reject_publication(tmp_path, make_variable(tmp_path, first_frames))


@POSIX_ONLY
@pytest.mark.parametrize("parser_failure", ["fault", "unexpected", "cancel", "timeout"])
def test_streaming_failure_uses_owned_shutdown_and_releases_process_descriptors(
    tmp_path, parser_failure
):
    owner = ProcessOwner(sys.executable)
    real_run = subprocess.Popen
    children = []
    # Observe actual owned handle at launch; never adopt or signal a persisted numeric ID.
    import production_artifacts.media as module
    from unittest.mock import patch

    def launch(*args, **kwargs):
        child = real_run(*args, **kwargs)
        children.append(child)
        return child

    def observer(block):
        if parser_failure == "fault":
            raise Fault("invalid_media")
        if parser_failure == "unexpected":
            raise RuntimeError("controlled parser failure")
        if parser_failure == "cancel":
            owner.cancel()

    read_control, write_control = os.pipe()
    code = "import os,sys;os.write(2,b'owned parser input\\n');os.read(int(sys.argv[1]),1)"
    expected = (
        "process_timeout"
        if parser_failure == "timeout"
        else "cancelled"
        if parser_failure == "cancel"
        else "invalid_media"
    )
    try:
        with patch.object(module.subprocess, "Popen", launch):
            # Preserve audited class methods; the launch facade retains the actual owned handle.
            result = fault_code(
                lambda: owner.run(
                    [sys.executable, "-B", "-c", code, str(read_control)],
                    pass_fds=(read_control,),
                    stderr_observer=observer,
                    timeout=0.1 if parser_failure == "timeout" else 3,
                )
            )
            assert result == expected
        assert owner.child is None and not owner.execution_unsettled
        assert children and children[0].returncode is not None and children[0].stderr.closed
    finally:
        # Even a deliberately broken parser guard cannot strand this owned test child.
        if children and children[0].returncode is None:
            os.write(write_control, b"release")
            children[0].wait(timeout=3)
        os.close(read_control)
        os.close(write_control)


@POSIX_ONLY
def test_real_inband_orientation_survives_filter_without_autorotate(tmp_path, base_media):
    source = tmp_path / "sei-matrix.mp4"
    codec(
        [
            "-i",
            str(base_media),
            "-c",
            "copy",
            "-frames:v",
            "1",
            "-bsf:v",
            "h264_metadata=display_orientation=insert:rotate=90",
            str(source),
        ]
    )
    binary = ProcessOwner().binary()
    evidence = subprocess.run(
        [
            binary,
            "-nostdin",
            "-hide_banner",
            "-noautorotate",
            "-i",
            str(source),
            "-vf",
            "sidedata=mode=delete:type=SEI_UNREGISTERED,showinfo=checksum=0",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        timeout=15,
    )
    assert evidence.returncode == 0 and b"side data - 3x3 displaymatrix" in evidence.stderr
    assert b"s:720x576" in evidence.stderr
    reject_publication(tmp_path, source)


@POSIX_ONLY
def test_probe_geometry_uses_dimensions_and_sar_from_same_frame(tmp_path):
    path = tmp_path / "probe.mp4"
    path.write_bytes(b"\0\0\0\x10ftypisom0000")

    class Probe(ProcessOwner):
        def run(self, argv, **kwargs):
            data = (
                b"Input #0, mov, from x:\nDuration: 00:00:12.00\n"
                b"Stream #0:0 Video: h264, yuv444p, 720x576, 30 fps\n"
                b"Stream #0:1 Audio: aac, 48000 Hz, mono\n"
            )
            kwargs["stderr_observer"](frame(size="640x480", sar="16/15") + end(1))
            return subprocess.CompletedProcess(argv, 0, stderr=data)

    fd = os.open(path, os.O_RDONLY)
    try:
        media = Probe(sys.executable).inspect(fd, full=False)
        assert (
            media.video.width,
            media.video.height,
            media.video.display_aspect,
            media.video.pixel_format,
        ) == (640, 480, Fraction(64, 45), "yuv420p")
    finally:
        os.close(fd)


@POSIX_ONLY
@pytest.mark.parametrize(
    "full_data", [b"", frame() + end(2), frame()[:-1], frame(size="640x480") + end(1)]
)
def test_full_decode_requires_complete_streamed_geometry_not_successful_audio_only(
    tmp_path, full_data
):
    path = tmp_path / "probe.mp4"
    path.write_bytes(b"\0\0\0\x10ftypisom0000")

    class Probe(ProcessOwner):
        def run(self, argv, **kwargs):
            if "-xerror" in argv:
                kwargs["stderr_observer"](full_data)
                return subprocess.CompletedProcess(argv, 0, stderr=b"Number of samples: 576000")
            data = (
                b"Input #0, mov, from x:\nDuration: 00:00:12.00\n"
                b"Stream #0:0 Video: h264, yuv420p, 720x576, 30 fps\n"
                b"Stream #0:1 Audio: aac, 48000 Hz, mono\n"
            )
            kwargs["stderr_observer"](frame() + end(1))
            return subprocess.CompletedProcess(argv, 0, stderr=data)

    fd = os.open(path, os.O_RDONLY)
    try:
        with pytest.raises(Fault, match="invalid_media"):
            Probe(sys.executable).inspect(fd)
    finally:
        os.close(fd)


@POSIX_ONLY
def test_real_variable_geometry_output_is_not_admitted_and_valid_siblings_survive(
    tmp_path, base_media, monkeypatch
):
    import importlib
    from production_artifacts.exports import ExportRunner
    from production_artifacts.worker import Worker

    variable = make_variable(tmp_path, 358, "720x576", "640x480", "16/15")
    original = hashlib.sha256(base_media.read_bytes()).hexdigest()
    injected = []

    class InjectingOwner(ProcessOwner):
        def run(self, argv, **kwargs):
            result = super().run(argv, **kwargs)
            if "-vf" in argv and argv[argv.index("-vf") + 1].startswith("scale=trunc(iw/2)"):
                # Exact newly owned encoded descriptor, not caller-controlled output path.
                output = int(str(argv[-1]).rsplit("/", 1)[1])
                os.ftruncate(output, 0)
                data = variable.read_bytes()
                assert os.pwrite(output, data, 0) == len(data)
                injected.append(True)
            return result

    module = importlib.import_module("production_artifacts.fixture_run")
    monkeypatch.setattr(
        module,
        "Worker",
        lambda store, inputs: Worker(store, inputs, ExportRunner(store, InjectingOwner)),
    )
    evidence = module.run(base_media, original, tmp_path / "exports")
    attempt = evidence["status"]["attempt"]
    assert injected and attempt["phase"] == "partial"
    assert attempt["failures"] == [dict(preset="youtube-longform-v1", error_code="invalid_media")]
    assert {row["artifact"]["destination"] for row in evidence["artifacts"]} == {
        "youtube-shorts",
        "tiktok",
    }
    assert hashlib.sha256(base_media.read_bytes()).hexdigest() == original
