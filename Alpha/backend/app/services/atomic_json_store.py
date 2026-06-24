from __future__ import annotations

import json
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


_LOCKS_GUARD = threading.Lock()
_PROCESS_LOCKS: dict[Path, threading.RLock] = {}


def read_json(path: str | Path, *, default: Any) -> Any:
    p = Path(path)
    with locked_file(p):
        if not p.exists():
            return default
        return json.loads(p.read_text(encoding="utf-8"))


def write_json_atomic(path: str | Path, payload: Any) -> None:
    p = Path(path)
    with locked_file(p):
        _write_json_atomic_unlocked(p, payload)


@contextmanager
def json_transaction(path: str | Path, *, default: Any) -> Iterator["JsonTransaction"]:
    p = Path(path)
    with locked_file(p):
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            data = default
        transaction = JsonTransaction(path=p, data=data)
        yield transaction
        if transaction.dirty:
            _write_json_atomic_unlocked(p, transaction.data)


class JsonTransaction:
    def __init__(self, *, path: Path, data: Any) -> None:
        self.path = path
        self.data = data
        self.dirty = False

    def write(self, data: Any) -> None:
        self.data = data
        self.dirty = True


@contextmanager
def locked_file(path: Path) -> Iterator[None]:
    lock_path = path.with_name(f"{path.name}.lock")
    process_lock = _process_lock(lock_path)
    with process_lock:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            _lock_handle(handle)
            try:
                yield
            finally:
                _unlock_handle(handle)


def _process_lock(path: Path) -> threading.RLock:
    resolved = path.resolve()
    with _LOCKS_GUARD:
        lock = _PROCESS_LOCKS.get(resolved)
        if lock is None:
            lock = threading.RLock()
            _PROCESS_LOCKS[resolved] = lock
        return lock


def _write_json_atomic_unlocked(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _fsync_parent(path.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _fsync_parent(path: Path) -> None:
    if sys.platform == "win32":
        return
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


if sys.platform == "win32":
    import msvcrt

    def _lock_handle(handle: Any) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_handle(handle: Any) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock_handle(handle: Any) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _unlock_handle(handle: Any) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
