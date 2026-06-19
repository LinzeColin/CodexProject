from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from quantlab.storage import atomic_write_json, locked_json_update, read_json_state


def test_json_state_fail_closes_on_corrupt_file(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON 状态文件损坏"):
        read_json_state(path, [], expected_type=list)

    assert path.read_text(encoding="utf-8") == "{bad json"


def test_json_state_fail_closes_on_unexpected_type(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON 状态文件格式不正确"):
        read_json_state(path, [], expected_type=list)


def test_atomic_json_write_supports_non_native_values(tmp_path: Path):
    path = tmp_path / "state.json"
    atomic_write_json(path, {"created_at": datetime(2026, 6, 4, tzinfo=timezone.utc)}, default=str)

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["created_at"].startswith("2026-06-04")


def test_locked_json_update_writes_under_lock(tmp_path: Path):
    path = tmp_path / "state.json"

    locked_json_update(path, [], lambda payload: payload + [{"item": 1}], expected_type=list)
    locked_json_update(path, [], lambda payload: payload + [{"item": 2}], expected_type=list)

    assert json.loads(path.read_text(encoding="utf-8")) == [{"item": 1}, {"item": 2}]
    assert (tmp_path / "state.json.lock").exists()
