"""Bounded owned FFmpeg subprocesses; probe and full decode use the same open bytes."""

from __future__ import annotations

import ast
from collections import deque
from collections.abc import Callable
import hashlib
import inspect
from fractions import Fraction
import os
from pathlib import Path
import re
import signal
import select
import subprocess
import sys
import threading
import textwrap
import time

from .models import Audio, Media, Video
from .geometry import GeometryScan, GEOMETRY_FILTER
from .safety import Fault, hash_fd, identity
from .platform_support import require_posix

# Signalling depends on these audited CPython reapers sharing _waitpid_lock. This
# is a fixed-worker prerequisite, not a promise made by the generic Python API.
SUPPORTED_CPYTHON = frozenset({(3, 11, 18), (3, 12, 10), (3, 12, 13)})
# Official tagged CPython sources have identical normalized ASTs for these POSIX
# methods. Pin semantics as well as version; unavailable/modified source denies launch.
_REAPER_SOURCE_SHA256 = {
    "__init__": "294e6ebe70ca1ec6713e6e53c8a1d3a3c8b7d6edf82a5f17e8773cba5788ccdb",
    "_internal_poll": "be6f3d11eb1037d4781a2a97009fc2278a64a59546d899126691d772ff7c35a6",
    "_wait": "f0cb675bfa1a8e4b7a230b1cff9ff9f61d4a21ef7a5bc3a3f42b1dfbbc1fb733",
    "_try_wait": "65ca88b0f768be9e6b7a526c5c05486b11963976337e6d6d15fc2e9125599a21",
    "_handle_exitstatus": "916381f9760f848a9775921d8f2ba31e45f052b6220ed8c26367a6117d74bccf",
}
_POPEN = subprocess.Popen
_REAPERS = {
    name: getattr(_POPEN, name, None)
    for name in ("__init__", "_internal_poll", "_wait", "_try_wait", "_handle_exitstatus")
}


def _has_audited_reapers() -> bool:
    """Read only stdlib source at import, before any approved root/registry admission."""
    try:
        for name, expected in _REAPER_SOURCE_SHA256.items():
            method = _REAPERS[name]
            node = ast.parse(textwrap.dedent(inspect.getsource(method))).body[0]
            if not isinstance(node, ast.FunctionDef):
                return False
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:]  # Documentation is not reaping semantics.
            for item in ast.walk(node):
                if hasattr(item, "type_params") and item.type_params == []:
                    # CPython3.12 added this empty AST metadata field. Ignore only its
                    # empty form so identical3.11/3.12 executable bodies hash equally.
                    item._fields = tuple(field for field in item._fields if field != "type_params")
            actual = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
            if actual != expected:
                return False
        return True
    except (OSError, TypeError, SyntaxError, IndexError, KeyError):
        return False


_REAPERS_AUDITED = (
    os.name == "posix"
    and sys.implementation.name == "cpython"
    and sys.version_info[:3] in SUPPORTED_CPYTHON
    and _has_audited_reapers()
)


def require_process_policy() -> None:
    """The launcher must also forbid raw/foreign reapers and native auto-reap flags."""
    require_posix()
    if (
        sys.implementation.name != "cpython"
        or sys.version_info[:3] not in SUPPORTED_CPYTHON
        or not _REAPERS_AUDITED
        or signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL
        or any(
            not callable(method) or getattr(_POPEN, name, None) is not method
            for name, method in _REAPERS.items()
        )
    ):
        raise Fault("platform_unavailable")


class ProcessOwner:
    """Unreaped leader reservation authorizes signalling; descriptors exclude execution."""

    def __init__(self, executable: str | None = None):
        self.executable = executable
        self.cancelled = threading.Event()
        self.mutex = threading.Lock()
        self.child: subprocess.Popen | None = None
        self.execution_fds: tuple[int, ...] = ()
        self.execution_unsettled = False

    def binary(self) -> str:
        require_process_policy()
        if self.executable is None:
            try:
                import imageio_ffmpeg

                self.executable = imageio_ffmpeg.get_ffmpeg_exe()
            except (ImportError, RuntimeError) as error:
                raise Fault("dependency_unavailable") from error
        if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
            raise Fault("dependency_unavailable")
        return self.executable

    def cancel(self) -> None:
        self.cancelled.set()

    def run(
        self,
        argv: list[str],
        *,
        pass_fds: tuple[int, ...] = (),
        timeout: float = 300,
        stderr_observer: Callable[[bytes], None] | None = None,
        **unused: object,
    ) -> subprocess.CompletedProcess:
        require_process_policy()
        if self.execution_unsettled:
            raise Fault("execution_unsettled")
        if self.cancelled.is_set():
            raise Fault("cancelled")
        lines: deque[bytes] = deque(maxlen=128)
        witness_read, witness_write = os.pipe()
        child = None
        try:
            # The inherited lease excludes another worker even after this Python process
            # dies. The witness stays open through inherited descendants, so a live owner
            # also waits for the whole execution lifetime before terminal admission.
            child = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                start_new_session=True,
                bufsize=0,
                pass_fds=tuple(dict.fromkeys((*pass_fds, *self.execution_fds, witness_write))),
                env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
                cwd="/",
            )
        finally:
            os.close(witness_write)
            if child is None:
                os.close(witness_read)
        with self.mutex:
            self.child = child
        assert child.stderr is not None
        stderr_fd = child.stderr.fileno()
        os.set_blocking(stderr_fd, False)
        os.set_blocking(witness_read, False)
        readers = {stderr_fd, witness_read}
        settled = False
        deadline = time.monotonic() + timeout
        stop_at = None
        killed = False
        reason = None
        self.execution_unsettled = False

        def signal_owned(sig: int) -> None:
            # A concurrent Popen wait/poll may have reaped without installing returncode
            # yet. Unknown lock ownership is NOT live ownership: skip rather than wait
            # or poll recursively. With the pinned reapers excluded and default SIGCHLD,
            # returncode=None reserves this unreaped leader through the entire syscall.
            if not child._waitpid_lock.acquire(False):
                return
            try:
                if (
                    child.returncode is not None
                    or signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL
                ):
                    return
                try:
                    os.killpg(child.pid, sig)
                except ProcessLookupError:
                    pass
            finally:
                child._waitpid_lock.release()

        def observe(block: bytes) -> None:
            nonlocal reason, stop_at
            lines.append(block)
            if stderr_observer is not None and reason is None:
                try:
                    stderr_observer(block)
                except Exception:
                    # Parser failure uses the same owned stop/wait/witness path. Never
                    # abandon a live codec or let parsing bypass signalling ownership.
                    reason = "invalid_media"
                    signal_owned(signal.SIGTERM)
                    stop_at = time.monotonic() + 2

        try:
            while child.poll() is None or not settled:
                moment = time.monotonic()
                if reason is None and (self.cancelled.is_set() or moment > deadline):
                    reason = "cancelled" if self.cancelled.is_set() else "process_timeout"
                    signal_owned(signal.SIGTERM)
                    stop_at = moment + 2
                if stop_at is not None and moment >= stop_at:
                    if not killed:
                        signal_owned(signal.SIGKILL)
                        killed = True
                        stop_at = moment + 2
                    else:
                        # An escaped descendant may still hold media FDs. Its inherited
                        # lease continues excluding new work; do not invent terminal state.
                        self.execution_unsettled = True
                        raise Fault("execution_unsettled")
                ready, _, _ = select.select(list(readers), [], [], 0.02)
                for fd in ready:
                    try:
                        block = os.read(fd, 1024)
                    except BlockingIOError:
                        continue
                    if not block:
                        readers.remove(fd)
                        if fd == witness_read:
                            settled = True
                    elif fd == stderr_fd:
                        observe(block)
            child.wait(timeout=2)
            # Drain final diagnostics without a blocking reader thread or unbounded log.
            while stderr_fd in readers:
                try:
                    block = os.read(stderr_fd, 1024)
                except BlockingIOError:
                    break
                if not block:
                    break
                observe(block)
            if reason:
                raise Fault(reason)
            if child.returncode:
                raise Fault("media_failed")
            return subprocess.CompletedProcess(
                argv, child.returncode, stderr=b"".join(lines), stdout=b""
            )
        finally:
            os.close(witness_read)
            child.stderr.close()
            with self.mutex:
                self.child = None

    def inspect(self, fd: int, *, full: bool = True) -> Media:
        require_posix()
        before = identity(fd)
        if before[2] <= 0 or before[2] > 1024**4:
            raise Fault("media_limit")
        header = os.pread(fd, 16, 0)
        if len(header) >= 8 and header[4:8] == b"ftyp":
            demuxer = "mov"
        elif header.startswith(b"\x1a\x45\xdf\xa3"):
            demuxer = "matroska"
        else:
            raise Fault("invalid_media")
        binary = self.binary()
        path = f"/dev/fd/{fd}"
        # One coherent unrotated domain. Transform-bearing inputs are unavailable,
        # not silently normalized. Strip ONLY irrelevant unregistered SEI side data.
        probe_geometry = GeometryScan()
        os.lseek(fd, 0, os.SEEK_SET)
        result = self.run(
            [
                binary,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "info",
                "-protocol_whitelist",
                "file,pipe,fd",
                "-probesize",
                "5000000",
                "-analyzeduration",
                "5000000",
                "-f",
                demuxer,
                "-noautorotate",
                "-i",
                path,
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-vf",
                GEOMETRY_FILTER,
                "-frames:v",
                "1",
                "-nostats",
                "-progress",
                "pipe:2",
                "-fps_mode",
                "passthrough",
                "-f",
                "null",
                "-",
            ],
            pass_fds=(fd,),
            timeout=20,
            stderr_observer=probe_geometry.feed,
        )
        width, height, measured_sar, pixel_format = probe_geometry.finish()
        text = result.stderr.decode("utf-8", errors="replace")
        try:
            duration = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", text)
            video = re.search(r"Stream #0:\d+[^\n]*Video: (\w+)[^\n]*", text).group()
            audio = re.search(r"Stream #0:\d+[^\n]*Audio: (\w+)[^\n]*", text).group()
            fps = Fraction(re.search(r"([\d.]+) fps", video).group(1)).limit_denominator(1001)
            seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3])
            channels = 1 if "mono" in audio else 2 if "stereo" in audio else 0
            container = re.search(r"Input #0, ([^,]+)", text).group(1)
            media = Media(
                container="mp4" if container in {"mov", "mp4"} else container,
                video=Video(
                    codec=re.search(r"Video: (\w+)", video)[1],
                    width=width,
                    height=height,
                    sar_num=measured_sar.numerator,
                    sar_den=measured_sar.denominator,
                    fps_num=fps.numerator,
                    fps_den=fps.denominator,
                    pixel_format=pixel_format,
                ),
                audio=Audio(
                    codec=re.search(r"Audio: (\w+)", audio)[1],
                    sample_rate=int(re.search(r"(\d+) Hz", audio)[1]),
                    channels=channels,
                    duration_seconds=seconds,
                ),
                duration_seconds=seconds,
            )
            if media.video.fps_num / media.video.fps_den > 120:
                raise ValueError("fps limit")
        except (AttributeError, TypeError, ValueError) as error:
            raise Fault("invalid_media") from error
        if full:
            os.lseek(fd, 0, os.SEEK_SET)
            full_geometry = GeometryScan(probe_geometry.geometry)
            decoded = self.run(
                [
                    binary,
                    "-nostdin",
                    "-hide_banner",
                    "-loglevel",
                    "info",
                    "-xerror",
                    "-protocol_whitelist",
                    "file,pipe,fd",
                    "-f",
                    demuxer,
                    "-noautorotate",
                    "-i",
                    path,
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0",
                    "-vf",
                    GEOMETRY_FILTER,
                    "-nostats",
                    "-progress",
                    "pipe:2",
                    "-fps_mode",
                    "passthrough",
                    "-af",
                    "astats=metadata=0:reset=0",
                    "-f",
                    "null",
                    "-",
                ],
                pass_fds=(fd,),
                timeout=min(1800, 30 + seconds * 3),
                stderr_observer=full_geometry.feed,
            )
            full_geometry.finish()
            measured = re.findall(rb"Number of samples: ([0-9.]+)", decoded.stderr)
            if not measured:
                raise Fault("invalid_media")
            measured_audio = Audio(
                **{
                    **media.audio.model_dump(),
                    "duration_seconds": float(measured[-1]) / media.audio.sample_rate,
                }
            )
            media = media.model_copy(update={"audio": measured_audio})
        if before != identity(fd):
            raise Fault("source_changed")
        return media


def validate_fd(owner: ProcessOwner, fd: int, expected: str) -> Media:
    """Hash on both sides of decode. A descriptor pins identity, not mutable bytes."""
    require_posix()
    before = identity(fd)
    if hash_fd(fd) != expected:
        raise Fault("source_changed")
    media = owner.inspect(fd)
    if before != identity(fd) or hash_fd(fd) != expected:
        raise Fault("source_changed")
    return media


def descriptor_path(fd: int) -> Path:
    return Path(f"/dev/fd/{fd}")
