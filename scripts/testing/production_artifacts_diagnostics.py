"""CI05 test-only trace with native self-exit independent of logging and Python's GIL.

Windows activation remains Windows+Actions. Win64 timer callback ABI adaptation is an
explicit inference, requiring independent review and actual Windows child/CI proof.
POSIX native alarm support exists only for owned controlled mechanism tests; never the
production worker. Neither backend changes child reaping or faulthandler's own timer.
"""

from __future__ import annotations

import ctypes
import faulthandler
import math
import os
import platform
import queue
import signal
import sys
import tempfile
import threading
from typing import TextIO

import pytest

MAX_MARKERS = 2048
SESSION_SECONDS = 300
MAX_RECORD_BYTES = 512
MAX_TRACE_BYTES = 32768


def _windows_x64_abi(pointer_size: int, machine: str) -> bool:
    return pointer_size == 8 and machine.lower() in {"amd64", "x86_64"}


class _NativeDeadline:
    """Only this process can be terminated; no caller process ID or foreign handle."""

    def __init__(self):
        self.timer = None
        self.kernel = None
        self.posix = False

    def arm(self, seconds: float) -> None:
        if not math.isfinite(seconds) or not 0 < seconds <= SESSION_SECONDS:
            raise RuntimeError("unsupported diagnostic deadline")
        if os.name == "nt":
            if not _windows_x64_abi(ctypes.sizeof(ctypes.c_void_p), platform.machine()):
                raise RuntimeError("diagnostic requires Windows x64 ABI")
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetCurrentProcess.argtypes = []
            kernel.GetCurrentProcess.restype = ctypes.c_void_p
            kernel.CreateTimerQueueTimer.argtypes = [
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_ulong,
            ]
            kernel.CreateTimerQueueTimer.restype = ctypes.c_int
            kernel.DeleteTimerQueueTimer.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ]
            kernel.DeleteTimerQueueTimer.restype = ctypes.c_int
            kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            kernel.TerminateProcess.restype = ctypes.c_int
            self.kernel = kernel  # Retain DLL/export references for the complete lifetime.
            timer = ctypes.c_void_p()
            # Native address, NOT a Python/ctypes callback trampoline. On the restricted
            # x64 ABI RCX carries our self pseudo-handle; timer callback RDX's TRUE low
            # byte makes TerminateProcess's UINT nonzero (upper bits unspecified).
            # This is an audited ABI INFERENCE, not a documented identical signature.
            callback = ctypes.cast(kernel.TerminateProcess, ctypes.c_void_p)
            if not kernel.CreateTimerQueueTimer(
                ctypes.byref(timer),
                None,
                callback,
                kernel.GetCurrentProcess(),
                math.ceil(seconds * 1000),
                0,
                0x20,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            self.timer = timer
        elif os.name == "posix":
            # Controlled-child mechanism proof only. Never replace an existing alarm,
            # custom handler, blocked signal, or faulthandler/pytest configuration.
            if (
                signal.getsignal(signal.SIGALRM) != signal.SIG_DFL
                or signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0)
                or signal.SIGALRM in signal.pthread_sigmask(signal.SIG_BLOCK, set())
            ):
                raise RuntimeError("diagnostic native alarm unavailable")
            signal.setitimer(signal.ITIMER_REAL, seconds)
            self.posix = True
        else:
            raise RuntimeError("diagnostic native deadline unavailable")

    def cancel(self) -> bool:
        if self.posix:
            mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)
                if signal.SIGALRM in signal.sigpending():
                    return False
                self.posix = False
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        if self.timer is not None:
            # Main thread only. INVALID_HANDLE_VALUE waits for callback completion.
            # Failure/ERROR_IO_PENDING never means disarmed; caller exits nonzero.
            if not self.kernel.DeleteTimerQueueTimer(None, self.timer, ctypes.c_void_p(-1)):
                return False
            self.timer = None
        return True


class SessionDiagnostic:
    def __init__(self, stream: TextIO, seconds: float = SESSION_SECONDS):
        self.stream = stream
        self.seconds = seconds
        self.stopped = threading.Event()
        self.thread: threading.Thread | None = None
        self.writer: threading.Thread | None = None
        self.records: queue.Queue[bytes] = queue.Queue(maxsize=8)
        self.markers = 0
        self.phase = "startup"
        self.hard = _NativeDeadline()
        self.closed = False

    def _enqueue(self, data: bytes) -> None:
        try:
            self.records.put_nowait(data)
        except queue.Full:
            pass  # Diagnostics are best effort; control and exit never wait for output.

    def mark(self, phase: str, node: str = "") -> None:
        self.phase = (phase + " " + node.split("[", 1)[0])[:320]
        if self.markers < MAX_MARKERS:
            self.markers += 1
            self._enqueue(
                ("ORCH04_SESSION " + self.phase + "\n").encode("utf-8", "replace")[
                    :MAX_RECORD_BYTES
                ]
            )

    def start(self) -> None:
        try:
            self.hard.arm(self.seconds)  # FIRST: no potentially blocking logging before this.
        except Exception:
            os._exit(2)  # Fail diagnostic setup without trying to print to an unsafe sink.

        def write() -> None:
            while not self.stopped.is_set() or not self.records.empty():
                try:
                    record = self.records.get(timeout=0.01)
                except queue.Empty:
                    continue
                try:
                    self.stream.write(record.decode("utf-8", "replace"))
                    self.stream.flush()
                except Exception:
                    return  # Closed/broken sink never prevents native self-exit.

        def trace() -> None:
            # Soft trace is optional. Hard native deadline cannot wait for this thread,
            # its GIL, a buffered stream lock, tempfile I/O or traceback output.
            if not self.stopped.wait(self.seconds - min(1.0, self.seconds / 2)):
                try:
                    with tempfile.TemporaryFile() as output:
                        faulthandler.dump_traceback(file=output, all_threads=True)
                        output.seek(0)
                        data = output.read(MAX_TRACE_BYTES)
                except Exception:
                    data = b"trace unavailable\n"
                self._enqueue(
                    ("ORCH04_SESSION_TIMEOUT " + self.phase + "\n").encode()[:MAX_RECORD_BYTES]
                    + data
                )

        self.writer = threading.Thread(target=write, name="pytest-orch04-log", daemon=True)
        self.thread = threading.Thread(target=trace, name="pytest-orch04-trace", daemon=True)
        self.writer.start()
        self.thread.start()
        self.mark("startup")

    def close(self) -> None:
        if self.closed:
            return
        self.mark("disarm-request")
        self.stopped.set()
        for thread in (self.writer, self.thread):
            if thread is not None:
                thread.join(timeout=0.1)
                if thread.is_alive():
                    os._exit(1)  # Never cancel protection then hang in buffered finalization.
        if not self.hard.cancel():
            os._exit(1)
        self.closed = True  # Only after confirmed cancellation/completion.
        self.phase = "disarmed"


_diagnostic: SessionDiagnostic | None = None


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args) -> None:
    global _diagnostic
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true":
        return
    capture = early_config.pluginmanager.get_plugin("capturemanager")
    if capture is not None:
        with capture.global_and_fixture_disabled():
            stream = os.fdopen(os.dup(sys.stderr.fileno()), "w", buffering=1)
    else:
        stream = os.fdopen(os.dup(sys.stderr.fileno()), "w", buffering=1)
    _diagnostic = SessionDiagnostic(stream)
    _diagnostic.start()


def _mark(phase: str, node: str = "") -> None:
    if _diagnostic is not None:
        _diagnostic.mark(phase, node)


def pytest_sessionstart(session) -> None:
    _mark("collection-start")


def pytest_collectstart(collector) -> None:
    _mark("collect", collector.nodeid)


def pytest_collection_finish(session) -> None:
    _mark("collection-finished")


def pytest_runtest_logstart(nodeid, location) -> None:
    _mark("test-start", nodeid)


def pytest_runtest_logreport(report) -> None:
    _mark("test-" + report.when + "-" + report.outcome, report.nodeid)


def pytest_sessionfinish(session, exitstatus) -> None:
    _mark("session-finish-" + str(exitstatus))


def pytest_unconfigure(config) -> None:
    global _diagnostic
    if _diagnostic is not None:
        _diagnostic.close()
        _diagnostic.stream.close()
        _diagnostic = None
