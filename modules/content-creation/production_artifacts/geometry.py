"""Bounded, incremental fixed-codec measurements; never infer geometry from headers."""

from __future__ import annotations

from fractions import Fraction
import re

from .safety import Fault

MAX_LINE = 4096
MAX_FRAMES = 86400 * 120  # Existing duration/fps envelope; decode deadline also applies.
GEOMETRY_FILTER = "sidedata=mode=delete:type=SEI_UNREGISTERED,showinfo=checksum=0"


class GeometryScan:
    """Every frame must have one constant geometry and the final mux count must agree.

    noautorotate is required on the input. Preserve transform side data: this candidate
    explicitly rejects ALL display/spherical transforms, including valid quarter turns.
    The observer consumes the entire stream before its bounded diagnostic tail evicts it.
    """

    def __init__(self, expected: tuple[int, int, Fraction, str] | None = None):
        self.geometry = expected
        self.frames = 0
        self.pending = bytearray()
        self.reported = None
        self.ended = False

    def feed(self, block: bytes) -> None:
        for part in re.split(rb"([\r\n])", block):
            if part in {b"\r", b"\n"}:
                self._line(bytes(self.pending))
                self.pending.clear()
            else:
                if len(self.pending) + len(part) > MAX_LINE:
                    raise Fault("invalid_media")
                self.pending.extend(part)

    def _line(self, line: bytes) -> None:
        lowered = line.lower()
        if b"displaymatrix" in lowered or b"spherical" in lowered:
            raise Fault("invalid_media")
        if b"Parsed_showinfo_" in line and re.search(rb"\b(?:n|sar|s):", line):
            frame = re.search(
                rb"\bn:\s*(\d+)\b.*?\bfmt:(\w+)\b.*?\bsar:(\d+)/(\d+)\b s:(\d+)x(\d+)\b",
                line,
            )
            if frame is None or int(frame[1]) != self.frames or self.frames >= MAX_FRAMES:
                raise Fault("invalid_media")
            width, height, num, den = int(frame[5]), int(frame[6]), int(frame[3]), int(frame[4])
            if not (
                2 <= width <= 7680
                and 2 <= height <= 4320
                and 1 <= num <= 65535
                and 1 <= den <= 65535
            ):
                raise Fault("invalid_media")
            current = (width, height, Fraction(num, den), frame[2].decode("ascii"))
            if self.geometry is not None and current != self.geometry:
                raise Fault("invalid_media")
            self.geometry = current
            self.frames += 1
        elif line.startswith(b"frame="):
            if b" fps=" in line:  # Human-readable final stats, not -progress output.
                return
            count = re.fullmatch(rb"frame=\s*(\d+)", line)
            if count is None or int(count[1]) > MAX_FRAMES:
                raise Fault("invalid_media")
            self.reported = int(count[1])
        elif line == b"progress=end":
            self.ended = True

    def finish(self) -> tuple[int, int, Fraction, str]:
        if self.pending or not self.frames or not self.ended or self.reported != self.frames:
            raise Fault("invalid_media")
        assert self.geometry is not None
        return self.geometry
