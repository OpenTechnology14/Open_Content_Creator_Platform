"""Descriptor-relative POSIX filesystem operations; no path-following writes."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import uuid
from collections.abc import Iterator

from .platform_support import require_posix

MAX_JSON = 1024 * 1024


class Fault(Exception):
    """Allowlisted error code only: paths/diagnostics never cross the protocol."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(data: bytes) -> dict:
    if len(data) > MAX_JSON:
        raise Fault("limit_exceeded")

    def unique(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise Fault("invalid_request")
            result[key] = value
        return result

    try:
        value = json.loads(
            data,
            parse_constant=lambda _: (_ for _ in ()).throw(Fault("invalid_request")),
            object_pairs_hook=unique,
        )
        if not isinstance(value, dict):
            raise Fault("invalid_request")
        return value
    except (ValueError, RecursionError) as error:
        raise Fault("invalid_request") from error


def parts(path: str) -> tuple[str, ...]:
    if (
        not path
        or "\\" in path
        or ":" in path
        or path.startswith("/")
        or any(x in {"", ".", ".."} for x in path.split("/"))
        or len(path) > 1024
    ):
        raise Fault("unsafe_path")
    return PurePosixPath(path).parts


def identity(fd: int) -> tuple[int, ...]:
    require_posix()
    s = os.fstat(fd)
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def hash_fd(fd: int) -> str:
    require_posix()
    sha = hashlib.sha256()
    offset = 0
    while data := os.pread(fd, 1024 * 1024, offset):
        sha.update(data)
        offset += len(data)
    return sha.hexdigest()


class SafeRoot:
    """Trusted launcher opens an existing root, rejecting every symlink ancestor.

    Windows needs a native handle implementation; fail closed here rather than pretending
    resolve()+open provides Windows reparse-point/race guarantees.
    """

    def __init__(self, path: Path):
        require_posix()
        if not path.is_absolute() or ".." in path.parts or "\\" in str(path):
            raise Fault("unsafe_path")
        absolute = path
        # macOS /tmp is a system symlink. Callers must pass its canonical /private/tmp root.
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for name in absolute.parts[1:]:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
        except OSError as error:
            os.close(fd)
            raise Fault("unsafe_path") from error
        self.fd = fd
        self.path = absolute

    def close(self) -> None:
        if getattr(self, "fd", -1) >= 0:
            os.close(self.fd)
            self.fd = -1

    def __del__(self) -> None:
        self.close()

    @contextlib.contextmanager
    def parent(self, path: str, create: bool = False) -> Iterator[tuple[int, str]]:
        names = parts(path)
        fd = os.dup(self.fd)
        try:
            for name in names[:-1]:
                if create:
                    try:
                        os.mkdir(name, mode=0o700, dir_fd=fd)
                        os.fsync(fd)
                    except FileExistsError:
                        pass
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            yield fd, names[-1]
        except OSError as error:
            if error.errno in {20, 40, 62}:
                raise Fault("source_unavailable") from error
            raise
        finally:
            os.close(fd)

    def directory_chain(self, path: str) -> tuple[tuple[int, int], ...]:
        """Retain every ancestor identity, without following any directory symlink."""
        require_posix()
        fd = os.dup(self.fd)
        result = []
        try:
            st = os.fstat(fd)
            result.append((st.st_dev, st.st_ino))
            for name in parts(path):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
                st = os.fstat(fd)
                result.append((st.st_dev, st.st_ino))
            return tuple(result)
        finally:
            os.close(fd)

    def open(self, path: str, flags: int = os.O_RDONLY) -> int:
        with self.parent(path) as (fd, name):
            result = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
            if not stat.S_ISREG(os.fstat(result).st_mode):
                os.close(result)
                raise Fault("unsafe_path")
            return result

    def read(self, path: str) -> bytes:
        fd = self.open(path)
        try:
            if os.fstat(fd).st_size > MAX_JSON:
                raise Fault("limit_exceeded")
            return os.read(fd, MAX_JSON + 1)
        finally:
            os.close(fd)

    def atomic(self, path: str, data: bytes, exclusive: bool = False) -> None:
        with self.parent(path, create=True) as (fd, name):
            try:
                existing = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISLNK(existing.st_mode):
                    raise Fault("unsafe_path")
            except FileNotFoundError:
                pass
            temporary = ".pending-" + uuid.uuid4().hex
            handle = os.open(
                temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
            )
            try:
                with os.fdopen(handle, "wb") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                if exclusive:
                    os.link(temporary, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
                    os.unlink(temporary, dir_fd=fd)
                else:
                    os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
                os.fsync(fd)
            finally:
                try:
                    os.unlink(temporary, dir_fd=fd)
                except FileNotFoundError:
                    pass

    def mkdir(self, path: str) -> None:
        with self.parent(path, create=True) as (fd, name):
            os.mkdir(name, mode=0o700, dir_fd=fd)
            os.fsync(fd)

    @contextlib.contextmanager
    def directory(self, path: str) -> Iterator[int]:
        with self.parent(path) as (fd, name):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            yield child
        finally:
            os.close(child)
