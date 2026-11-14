"""Bounded faststart relocation without reopening a mutable path (FFmpeg MP4 only)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
import os
import struct
from .safety import Fault
from .platform_support import require_posix

MAX_MOOV = 16 * 1024 * 1024


def atoms(fd: int, length: int) -> Iterator[tuple[int, int, bytes]]:
    require_posix()
    offset = 0
    while offset < length:
        header = os.pread(fd, 8, offset)
        if len(header) != 8:
            raise Fault("invalid_media")
        size, kind = struct.unpack(">I4s", header)
        if size < 8 or offset + size > length:
            raise Fault("invalid_media")
        yield offset, size, kind
        offset += size


def relocate_moov(data: bytes, delta: int) -> bytes:
    result = bytearray(data)

    def walk(start: int, end: int) -> None:
        while start < end:
            if end - start < 8:
                raise Fault("invalid_media")
            size, kind = struct.unpack_from(">I4s", result, start)
            if size < 8 or start + size > end:
                raise Fault("invalid_media")
            if kind in {b"moov", b"trak", b"mdia", b"minf", b"stbl"}:
                walk(start + 8, start + size)
            elif kind in {b"stco", b"co64"}:
                if size < 16:
                    raise Fault("invalid_media")
                count = struct.unpack_from(">I", result, start + 12)[0]
                width, fmt = (4, ">I") if kind == b"stco" else (8, ">Q")
                if 16 + count * width != size:
                    raise Fault("invalid_media")
                for index in range(count):
                    offset = start + 16 + index * width
                    value = struct.unpack_from(fmt, result, offset)[0] + delta
                    if value >= 2 ** (width * 8):
                        raise Fault("media_limit")
                    struct.pack_into(fmt, result, offset, value)
            start += size

    walk(0, len(result))
    return bytes(result)


def write_all(fd: int, data: bytes) -> None:
    require_posix()
    view = memoryview(data)
    while view:
        size = os.write(fd, view)
        if size <= 0:
            raise Fault("disk_unavailable")
        view = view[size:]


def faststart(
    source_fd: int, output_fd: int, *, cancelled: Callable[[], bool] | None = None
) -> None:
    """Source is our newly encoded seekable MP4; destination must be exclusively created."""
    require_posix()
    length = os.fstat(source_fd).st_size
    top = []
    for atom in atoms(source_fd, length):
        top.append(atom)
        if len(top) > 16:
            raise Fault("media_limit")
    if (
        len(top) > 16
        or not top
        or top[0][2] != b"ftyp"
        or top[-1][2] != b"moov"
        or sum(kind == b"mdat" for _, _, kind in top) != 1
        or any(kind not in {b"ftyp", b"free", b"mdat", b"moov"} for _, _, kind in top)
        or top[-1][1] > MAX_MOOV
    ):
        raise Fault("invalid_media")
    offset, size, _ = top[-1]
    moov = relocate_moov(os.pread(source_fd, size, offset), size)
    for index, (offset, size, kind) in enumerate(top[:-1]):
        copied = 0
        while copied < size:
            if cancelled is not None and cancelled():
                raise Fault("cancelled")
            block = os.pread(source_fd, min(1024 * 1024, size - copied), offset + copied)
            if not block:
                raise Fault("invalid_media")
            write_all(output_fd, block)
            copied += len(block)
        if index == 0:
            write_all(output_fd, moov)
    os.fsync(output_fd)
