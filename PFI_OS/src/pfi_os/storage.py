from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable


def read_json_state(
    path: Path | str,
    default: Any,
    expected_type: type | tuple[type, ...] | None = None,
    *,
    fail_closed: bool = True,
) -> Any:
    state_path = Path(path)
    if not state_path.exists():
        return default
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        if fail_closed:
            raise ValueError(f"JSON 状态文件损坏，已阻止覆盖：{state_path}") from exc
        return default
    if expected_type is not None and not isinstance(payload, expected_type):
        if fail_closed:
            raise ValueError(f"JSON 状态文件格式不正确，已阻止覆盖：{state_path}")
        return default
    return payload


def atomic_write_json(path: Path | str, payload: Any, *, sort_keys: bool = False, default: Callable[[Any], Any] | None = None) -> Path:
    state_path = Path(path)
    atomic_write_text(state_path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=sort_keys, default=default))
    return state_path


def atomic_write_text(path: Path | str, content: str) -> Path:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{state_path.name}.", suffix=".tmp", dir=str(state_path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, state_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return state_path


def locked_json_update(
    path: Path | str,
    default: Any,
    updater: Callable[[Any], Any],
    *,
    expected_type: type | tuple[type, ...] | None = None,
    sort_keys: bool = False,
) -> Path:
    state_path = Path(path)
    with file_lock(lock_path_for(state_path)):
        current = read_json_state(state_path, default, expected_type=expected_type)
        updated = updater(current)
        atomic_write_json(state_path, updated, sort_keys=sort_keys)
    return state_path


def lock_path_for(path: Path | str) -> Path:
    state_path = Path(path)
    return state_path.with_name(f"{state_path.name}.lock")


@contextmanager
def file_lock(path: Path | str):
    import fcntl

    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
