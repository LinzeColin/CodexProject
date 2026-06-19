from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quantlab.data.lake import write_data_lake_manifest
from quantlab.data.market_events import write_market_event_log
from quantlab.data.replay import write_event_replay
from quantlab.research.vectorized import (
    VECTORIZED_RESEARCH_SCHEMA,
    build_vectorized_research,
    event_replay_to_ohlcv,
    write_vectorized_research,
)


def test_event_replay_to_ohlcv_builds_stable_symbol_time_frame(tmp_path: Path) -> None:
    replay = _write_replay_fixture(tmp_path)
    payload = json.loads(Path(replay["outputs"]["latest_json"]).read_text(encoding="utf-8"))
    payload["project_root"] = "/old/private/path/that/must/not/be_used"

    frame, missing = event_replay_to_ohlcv(payload, symbol="SPY", market="US", interval="1d")

    assert missing == []
    assert list(frame["symbol"].unique()) == ["SPY"]
    assert frame["datetime"].is_monotonic_increasing
    assert frame.iloc[0]["close"] == 100.5
    assert "payload_json" not in frame.columns


def test_vectorized_research_runs_parameter_scan_from_replay(tmp_path: Path) -> None:
    replay = _write_replay_fixture(tmp_path)

    payload = build_vectorized_research(
        project_root=tmp_path,
        replay_path=Path(replay["outputs"]["latest_json"]),
        symbol="SPY",
        market="US",
        interval="1d",
        param_grid={"short_window": [2, 3], "long_window": [4, 5]},
        as_of="2026-06-16",
    )

    assert payload["schema"] == VECTORIZED_RESEARCH_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["row_count"] == 7
    assert payload["selected_symbol"] == "SPY"
    assert payload["parameter_run_count"] == 4
    assert payload["scan_run_count"] == 4
    assert payload["best_run"]["strategy_id"] == "ma_crossover"
    assert "broker" in payload["safety_boundary"]


def test_write_vectorized_research_outputs_latest_files(tmp_path: Path) -> None:
    replay = _write_replay_fixture(tmp_path)

    payload = write_vectorized_research(
        project_root=tmp_path,
        replay_path=Path(replay["outputs"]["latest_json"]),
        output_dir=tmp_path / "vectorized",
        symbol="SPY",
        param_grid={"short_window": [2], "long_window": [4]},
        as_of="2026-06-16",
    )

    outputs = payload["outputs"]
    assert outputs["json"] == "vectorized/VectorizedResearch_SPY_20260616.json"
    assert (tmp_path / outputs["json"]).exists()
    assert (tmp_path / outputs["latest_json"]).exists()
    assert (tmp_path / outputs["latest_csv"]).read_text(encoding="utf-8").startswith("run_id,strategy_id")
    assert "# Vectorized Research" in (tmp_path / outputs["latest_markdown"]).read_text(encoding="utf-8")


def test_vectorized_research_fails_closed_for_bad_grid(tmp_path: Path) -> None:
    replay = _write_replay_fixture(tmp_path)

    payload = build_vectorized_research(
        project_root=tmp_path,
        replay_path=Path(replay["outputs"]["latest_json"]),
        symbol="SPY",
        param_grid={"short_window": [5], "long_window": [4]},
    )

    assert payload["status"] == "Blocked"
    assert payload["missing_data_log"][0]["dataset"] == "parameter_scan"


def _write_replay_fixture(root: Path) -> dict:
    write_market_event_log(
        _bars(),
        symbol="SPY",
        market="US",
        interval="1d",
        source="sample",
        as_of="2026-06-16",
        output_dir=root / "data" / "marketEvents",
        project_root=root,
    )
    write_data_lake_manifest(project_root=root, as_of="2026-06-16", output_dir=root / "data" / "dataLake")
    return write_event_replay(project_root=root, as_of="2026-06-16", output_dir=root / "data" / "replay")


def _bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": ["2026-01-01", "2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09"],
            "open": [100.0, 101.0, 102.0, 103.0, 102.5, 104.0, 105.0],
            "high": [101.0, 102.0, 103.0, 104.0, 103.0, 105.0, 106.0],
            "low": [99.0, 100.0, 101.0, 102.0, 101.5, 103.0, 104.0],
            "close": [100.5, 101.5, 102.5, 102.0, 104.5, 105.5, 106.0],
            "volume": [1000, 1100, 1200, 1300, 1250, 1400, 1500],
        }
    )
