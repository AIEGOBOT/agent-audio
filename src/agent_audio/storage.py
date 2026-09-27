"""Filesystem primitives for non-destructive user-local installation."""

from __future__ import annotations

import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def reject_link(path: Path) -> None:
    """Reject symlinks and Windows junctions, including dangling links."""
    if not os.path.lexists(path):
        return
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise RuntimeError(f"Refusing to follow a link or reparse point: {path}")


def read_optional(path: Path) -> bytes | None:
    reject_link(path)
    return path.read_bytes() if path.exists() else None


@contextmanager
def file_lock(path: Path) -> Iterator[None]:
    """Coordinate Agent Audio writers; never remove someone else's lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".agent-audio.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(
            f"Another install may be using {path}; lock exists: {lock}"
        ) from exc
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(fd)
        lock.unlink()


def atomic_write(path: Path, expected: bytes | None, updated: bytes) -> None:
    """Back up each edit and replace atomically. Caller holds file_lock.

    External editors do not participate in that lock; comparisons detect their
    edits made before the final replacement check.
    """
    if read_optional(path) != expected:
        raise RuntimeError(f"Configuration changed during installation: {path}")
    if expected == updated:
        return
    if expected is not None:
        fd, _ = tempfile.mkstemp(
            prefix=path.name + ".agent-audio-", suffix=".bak", dir=path.parent
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())
    fd, temporary = tempfile.mkstemp(prefix=".agent-audio-", dir=path.parent)
    temp = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        if expected is not None:
            os.chmod(temp, stat.S_IMODE(path.stat().st_mode))
        if read_optional(path) != expected:
            raise RuntimeError(f"Configuration changed during installation: {path}")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
