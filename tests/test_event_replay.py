from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quantlab.data.lake import write_data_lake_manifest
from quantlab.data.market_events import write_market_event_log
from quantlab.data.replay import build_event_replay, write_event_replay


def test_event_replay_builds_deterministic_batch_from_data_lake_cursor(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    payload = build_event_replay(project_root=tmp_path, as_of="2026-06-13", limit=2)

    assert payload["schema"] == "EVAOSEventReplayBatchV1"
    assert payload["replay_status"] == "Pass"
    assert payload["cursor_count"] == 1
    assert payload["asset_count"] == 1
    assert payload["source_event_count"] == 3
    assert payload["event_count"] == 2
    assert payload["records"][0]["event_time"] == "2026-01-01T00:00:00"
    assert payload["records"][1]["event_time"] == "2026-01-02T00:00:00"
    assert payload["records"][0]["replay_index"] == 1
    assert payload["next_after"] == "2026-01-02T00:00:00"
    assert json.loads(payload["records"][0]["payload_json"])["close"] == 100.5


def test_event_replay_start_after_filters_cursor_window(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    payload = build_event_replay(
        project_root=tmp_path,
        as_of="2026-06-13",
        market="US",
        symbol="SPY",
        interval="1d",
        start_after="2026-01-02T00:00:00",
    )

    assert payload["replay_status"] == "Pass"
    assert payload["event_count"] == 1
    assert payload["records"][0]["event_time"] == "2026-01-05T00:00:00"
    assert payload["next_after"] == "2026-01-05T00:00:00"


def test_write_event_replay_outputs_files_and_latest_pointers(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    payload = write_event_replay(project_root=tmp_path, as_of="2026-06-13", output_dir=tmp_path / "out", limit=1)

    outputs = payload["outputs"]
    saved = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))

    assert Path(outputs["json"]).name.startswith("EventReplay_")
    assert Path(outputs["json"]).name.endswith("_13062026.json")
    assert saved["event_count"] == 1
    assert Path(outputs["csv"]).read_text(encoding="utf-8").startswith("replay_index,cursor_id,asset_id")
    assert "# Event Replay" in Path(outputs["markdown"]).read_text(encoding="utf-8")
    assert Path(outputs["latest_json"]).exists()
    assert Path(outputs["latest_csv"]).exists()
    assert Path(outputs["latest_markdown"]).exists()


def test_event_replay_returns_empty_when_cursor_filter_does_not_match(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    payload = build_event_replay(project_root=tmp_path, as_of="2026-06-13", cursor_id="missing")

    assert payload["replay_status"] == "Empty"
    assert payload["event_count"] == 0
    assert payload["missing_data_log"][0]["dataset"] == "replay_cursor"


def _write_fixture(root: Path) -> None:
    write_market_event_log(
        _bars(),
        symbol="SPY",
        market="US",
        interval="1d",
        source="sample",
        as_of="2026-06-13",
        output_dir=root / "data" / "marketEvents",
        project_root=root,
    )
    write_data_lake_manifest(project_root=root, as_of="2026-06-13", output_dir=root / "data" / "dataLake")


def _bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": ["2026-01-05", "2026-01-02", "2026-01-01"],
            "open": [102.0, 101.0, 100.0],
            "high": [103.0, 102.0, 101.0],
            "low": [101.0, 100.0, 99.0],
            "close": [102.5, 101.5, 100.5],
            "volume": [1200, 1100, 1000],
        }
    )
