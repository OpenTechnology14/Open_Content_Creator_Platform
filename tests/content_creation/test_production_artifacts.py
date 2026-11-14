"""Behavioral contracts for the offline production namespace (no network)."""

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "modules/content-creation"))
from production_artifacts.models import RequestV1, ProductionSessionV1  # noqa: E402
from production_artifacts.store import ProductionStore  # noqa: E402
from production_artifacts.safety import Fault, SafeRoot  # noqa: E402

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX descriptor filesystem/media runtime; unsupported platform admission is tested separately",
)


def creation(operation_id="create-one"):
    return dict(
        operation_id=operation_id,
        source_profile_id="stream-main",
        content_profile_id="content-main",
        show_profile_id="opentech",
        content_root_id="root-one",
        target=dict(
            kind="opentechnologyapp",
            commit="a" * 40,
            tree_sha256="b" * 64,
            fixture_sha256="c" * 64,
            scenario_id="fixture",
        ),
    )


@pytest.fixture
def store(tmp_path):
    if os.name != "posix":
        pytest.skip(
            "POSIX durable store fixture; portable schema/import/admission tests remain active"
        )
    return ProductionStore(SafeRoot(tmp_path), "root-one")


def test_create_is_durable_idempotent_and_changed_operation_has_no_side_effects(store):
    first = store.create(creation())
    assert store.create(creation()) == first
    before = store.root.read("state.json")
    with pytest.raises(Fault, match="operation_conflict"):
        store.create({**creation(), "show_profile_id": "changed"})
    assert store.root.read("state.json") == before
    assert ProductionSessionV1.model_validate(first).revision == 1


@pytest.mark.parametrize(
    "bad", ["../escape", "/absolute", "//server/share", "https://host", r"C:\\file", "a/../b"]
)
@POSIX_ONLY
def test_private_root_rejects_paths_without_writes(tmp_path, bad):
    root = SafeRoot(tmp_path)
    with pytest.raises(Fault):
        root.open(bad)
    assert not list(tmp_path.iterdir())


@POSIX_ONLY
def test_root_and_ancestor_symlinks_are_rejected(tmp_path):
    (tmp_path / "real").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)
    with pytest.raises(Fault):
        SafeRoot(tmp_path / "link")
    root = SafeRoot(tmp_path)
    with pytest.raises(Fault):
        root.open("link/file")


def test_revision_conflict_has_no_side_effects(store):
    prod = store.create(creation())
    before = store.root.read("state.json")
    with pytest.raises(Fault, match="revision_conflict"):
        with store.transaction(prod["production_id"], 0):
            pytest.fail("stale revision admitted")
    assert before == store.root.read("state.json")


@pytest.mark.parametrize(
    "raw", ["[]", "null", '{"schema_version":2}', '{"schema_version":1,"x":NaN}']
)
def test_corrupt_or_future_state_is_preserved_and_not_reinitialized(store, raw):
    store.root.atomic("state.json", raw.encode())
    with pytest.raises(Fault):
        store.list()
    assert store.root.read("state.json") == raw.encode()


def test_strict_wire_rejects_unknown_fields_nonobjects_future_and_nan():
    from pydantic import ValidationError

    for value in [
        [],
        {"schema_version": 2},
        {
            "schema_version": 1,
            "request_id": "r",
            "command": "production.list",
            "payload": {},
            "extra": 1,
        },
    ]:
        with pytest.raises(ValidationError):
            RequestV1.model_validate(value)


def test_failed_atomic_commit_preserves_previous_state(store, monkeypatch):
    import os

    store.create(creation())
    before = store.root.read("state.json")

    def full(*args, **kwargs):
        raise OSError(28, "disk full")

    monkeypatch.setattr(os, "replace", full)
    with pytest.raises(OSError):
        store.create(creation("create-two"))
    assert store.root.read("state.json") == before


def test_wire_fixtures_roundtrip_and_schema_is_current():
    from production_artifacts.models import WIRE_MODELS, schema_bundle

    directory = (
        Path(__file__).resolve().parents[2] / "modules/content-creation/production_artifacts/wire"
    )
    assert json.loads((directory / "schema.json").read_text()) == schema_bundle()
    fixtures = json.loads((directory / "roundtrip.json").read_text())
    for name, value in fixtures.items():
        assert (
            WIRE_MODELS[name]
            .model_validate_json(json.dumps(value))
            .model_dump(mode="json", exclude_none=True)
            == value
        )
    assert hashlib.sha256((directory / "schema.json").read_bytes()).hexdigest()


@POSIX_ONLY
def test_faststart_relocates_chunk_offsets_without_reopening_path(tmp_path):
    import os
    import struct
    from production_artifacts.mp4 import faststart

    def atom(kind, data):
        return struct.pack(">I4s", 8 + len(data), kind) + data

    ftyp = atom(b"ftyp", b"isom0000")
    mdat = atom(b"mdat", b"actual-media-bytes")
    stco = atom(b"stco", struct.pack(">III", 0, 1, len(ftyp) + 8))
    moov = atom(b"moov", atom(b"trak", atom(b"mdia", atom(b"minf", atom(b"stbl", stco)))))
    original = tmp_path / "raw.mp4"
    original.write_bytes(ftyp + mdat + moov)
    out = tmp_path / "ready.mp4"
    with original.open("rb") as src, out.open("xb") as dst:
        faststart(src.fileno(), dst.fileno())
    data = out.read_bytes()
    assert data[20:24] == b"moov"
    index = data.index(b"stco") + 12
    offset = struct.unpack_from(">I", data, index)[0]
    assert data[offset : offset + 18] == b"actual-media-bytes"
    assert original.read_bytes() == ftyp + mdat + moov
    assert os.stat(out).st_size == os.stat(original).st_size


@POSIX_ONLY
def test_ancestor_replaced_during_commit_cannot_redirect_write(tmp_path, monkeypatch):
    import os

    root = SafeRoot(tmp_path)
    root.mkdir("inside")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "victim").write_bytes(b"untouched")
    real = os.replace

    def replace(src, dst, **kwargs):
        (tmp_path / "inside").rename(tmp_path / "retained")
        (tmp_path / "inside").symlink_to(outside, target_is_directory=True)
        return real(src, dst, **kwargs)

    monkeypatch.setattr(os, "replace", replace)
    root.atomic("inside/victim", b"new")
    assert (outside / "victim").read_bytes() == b"untouched"
    assert (tmp_path / "retained/victim").read_bytes() == b"new"


@POSIX_ONLY
def test_atomic_fsync_failure_preserves_previous_bytes(tmp_path, monkeypatch):
    import os

    root = SafeRoot(tmp_path)
    root.atomic("manifest.json", b"prior")

    def full(fd):
        raise OSError(28, "full at flush")

    monkeypatch.setattr(os, "fsync", full)
    with pytest.raises(OSError):
        root.atomic("manifest.json", b"new")
    assert root.read("manifest.json") == b"prior"


def test_portable_paths_unknown_versions_nonfinite_and_resource_bounds_rejected():
    from production_artifacts.models import ExportRequestV1, Media, Page
    from pydantic import ValidationError

    for value in [dict(limit=101), dict(cursor=-1), dict(limit=True)]:
        with pytest.raises(ValidationError):
            Page.model_validate(value)
    with pytest.raises(ValidationError):
        ExportRequestV1.model_validate(dict(production_id="../outside"))
    with pytest.raises(ValidationError):
        Media.model_validate(dict(duration_seconds=float("nan")))


@POSIX_ONLY
def test_real_three_destination_exports_decode_and_preserve_source(tmp_path):
    import os
    from production_artifacts.fixture_run import run
    from production_artifacts.media import ProcessOwner
    from production_artifacts.mp4 import atoms

    owner = ProcessOwner()
    source = tmp_path / "synthetic.mp4"
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
            "-movflags",
            "+faststart",
            str(source),
        ]
    )
    original = source.read_bytes()
    evidence = run(source, hashlib.sha256(original).hexdigest(), tmp_path / "production")
    assert evidence["status"]["attempt"]["phase"] == "complete"
    assert len(evidence["artifacts"]) == 3
    for inspection in evidence["artifacts"]:
        assert inspection["local_state"] == "validated"
        artifact = inspection["artifact"]
        with Path(inspection["path"]).open("rb") as media_file:
            top = list(atoms(media_file.fileno(), os.fstat(media_file.fileno()).st_size))
        assert top[1][2] == b"moov"
        assert artifact["media"]["audio"]["codec"] == "aac"
        assert artifact["media"]["audio"]["duration_seconds"] > 7.9
        assert artifact["media"]["video"]["pixel_format"] == "yuv420p"
        assert (
            hashlib.sha256(Path(inspection["path"]).read_bytes()).hexdigest() == artifact["sha256"]
        )
    assert source.read_bytes() == original


def test_metadata_rejects_remote_urls_and_control_bytes():
    from production_artifacts.models import Metadata
    from pydantic import ValidationError

    for title in ["https://signed-upload.example/token", "file:///private/secret", "a\x00b"]:
        with pytest.raises(ValidationError):
            Metadata(
                title=title,
                description="",
                start_seconds=0.0,
                end_seconds=12.0,
                preset_version="youtube-longform-v1",
                metadata_revision=1,
            )


@POSIX_ONLY
def test_atomic_symlink_and_fifo_state_cannot_be_opened(tmp_path):
    import os

    outside = tmp_path / "outside"
    outside.write_bytes(b"untouched")
    (tmp_path / "manifest.json").symlink_to(outside)
    root = SafeRoot(tmp_path)
    with pytest.raises(Fault):
        root.atomic("manifest.json", b"changed")
    assert outside.read_bytes() == b"untouched"
    os.mkfifo(tmp_path / "state.json")
    with pytest.raises(Fault):
        root.read("state.json")


def test_decoder_enforces_size_duplicates_object_and_finite_values():
    from production_artifacts.safety import decode

    for data in [b"[]", b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":"' + b"a" * (1024 * 1024) + b'"}']:
        with pytest.raises(Fault):
            decode(data)


@POSIX_ONLY
def test_relative_escape_to_existing_file_and_exclusive_write_are_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"private")
    inside = tmp_path / "inside"
    inside.mkdir()
    root = SafeRoot(inside)
    with pytest.raises(Fault):
        root.open("../outside")
    root.atomic("artifact.json", b"first", exclusive=True)
    with pytest.raises(FileExistsError):
        root.atomic("artifact.json", b"second", exclusive=True)
    assert root.read("artifact.json") == b"first"


def test_unknown_root_handle_cannot_create_production(store):
    before = list(store.root.path.iterdir())
    with pytest.raises(Fault, match="source_unavailable"):
        store.create({**creation(), "content_root_id": "forged-root"})
    assert list(store.root.path.iterdir()) == before


@POSIX_ONLY
def test_media_probe_bounds_precede_full_decode_and_full_decode_is_required(tmp_path):
    import os
    import subprocess
    from production_artifacts.media import ProcessOwner

    path = tmp_path / "source.mp4"
    path.write_bytes(b"\0\0\0\x10ftypisom0000")
    header = b"Input #0, mov, from x:\nDuration: 00:00:12.00\nStream #0:0 Video: h264, yuv420p, 1280x720, 30 fps\nStream #0:1 Audio: aac, 48000 Hz, mono\n[Parsed_showinfo_0] n:0 fmt:yuv420p sar:1/1 s:1280x720\nframe=1\nprogress=end\n"

    class Probe(ProcessOwner):
        def __init__(self, huge=False):
            super().__init__("/usr/bin/true")
            self.calls = []
            self.huge = huge

        def run(self, argv, **kwargs):
            self.calls.append(argv)
            if "-xerror" in argv:
                kwargs["stderr_observer"](header)
                return subprocess.CompletedProcess(argv, 0, stderr=b"Number of samples: 96000")
            data = header.replace(b"1280x720", b"90000x720") if self.huge else header
            kwargs["stderr_observer"](data)
            return subprocess.CompletedProcess(argv, 0, stderr=data)

    fd = os.open(path, os.O_RDONLY)
    try:
        probe = Probe()
        measured = probe.inspect(fd)
        assert len(probe.calls) == 2
        assert measured.audio.duration_seconds == 2.0
        huge = Probe(True)
        with pytest.raises(Fault, match="invalid_media"):
            huge.inspect(fd)
        assert len(huge.calls) == 1
    finally:
        os.close(fd)


@POSIX_ONLY
def test_playlist_bytes_are_rejected_before_any_codec_process(tmp_path):
    import os
    from production_artifacts.media import ProcessOwner

    path = tmp_path / "disguised.mp4"
    path.write_bytes(b"#EXTM3U\nfile:///private/file")

    class Forbidden(ProcessOwner):
        def binary(self):
            pytest.fail("unrecognized media reached executable lookup")

    fd = os.open(path, os.O_RDONLY)
    try:
        with pytest.raises(Fault, match="invalid_media"):
            Forbidden().inspect(fd)
    finally:
        os.close(fd)


@POSIX_ONLY
def test_faststart_cancellation_preserves_source_and_never_finishes(tmp_path):
    import struct
    from production_artifacts.mp4 import faststart

    def atom(kind, data):
        return struct.pack(">I4s", 8 + len(data), kind) + data

    raw = atom(b"ftyp", b"isom0000") + atom(b"mdat", b"content") + atom(b"moov", b"")
    path = tmp_path / "encoded.mp4"
    path.write_bytes(raw)
    with path.open("rb") as src, (tmp_path / "out.mp4").open("xb") as dst:
        with pytest.raises(Fault, match="cancelled"):
            faststart(src.fileno(), dst.fileno(), cancelled=lambda: True)
    assert path.read_bytes() == raw
