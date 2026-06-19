from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quantlab.data.lake import build_data_lake_manifest, write_data_lake_manifest
from quantlab.data.market_events import write_market_event_log
from quantlab.data.store import DataStore


def test_data_lake_manifest_indexes_market_event_jsonl_and_replay_cursor(tmp_path: Path) -> None:
    write_market_event_log(
        _bars(),
        symbol="SPY",
        market="US",
        interval="1d",
        source="sample",
        as_of="2026-06-13",
        output_dir=tmp_path / "data" / "marketEvents",
        project_root=tmp_path,
    )

    payload = build_data_lake_manifest(project_root=tmp_path, as_of="2026-06-13")

    assert payload["schema"] == "EVAOSReproducibleDataLakeManifestV1"
    assert payload["lake_status"] == "Pass"
    assert payload["asset_count"] == 1
    assert payload["partition_count"] == 1
    assert payload["replay_cursor_count"] == 1
    assert payload["latest_alias_count"] == 4
    assert payload["assets"][0]["dataset"] == "market_events"
    assert payload["assets"][0]["row_count"] == 3
    assert payload["assets"][0]["checksum_sha256"]
    assert payload["replay_cursors"][0]["event_count"] == 3
    assert payload["replay_cursors"][0]["next_after"] == "2026-01-05T00:00:00"
    assert payload["missing_data_log"][0]["dataset"] == "bar_cache"


def test_data_lake_manifest_indexes_structured_bar_cache(tmp_path: Path) -> None:
    store = DataStore(root=tmp_path / "data" / "cache", format="csv")
    store.save_bars(_bars(), symbol="SPY", market="US", interval="1d")

    payload = build_data_lake_manifest(project_root=tmp_path, as_of="2026-06-13", include_market_events=False)

    assert payload["lake_status"] == "Pass"
    assert payload["asset_count"] == 1
    assert payload["assets"][0]["dataset"] == "bar_cache"
    assert payload["assets"][0]["schema"] == "QuantLabOHLCV"
    assert payload["assets"][0]["row_count"] == 3
    assert payload["replay_cursors"][0]["dataset"] == "bar_cache"


def test_write_data_lake_manifest_outputs_files_and_latest_pointers(tmp_path: Path) -> None:
    write_market_event_log(
        _bars(),
        symbol="SPY",
        market="US",
        interval="1d",
        source="sample",
        as_of="2026-06-13",
        output_dir=tmp_path / "data" / "marketEvents",
        project_root=tmp_path,
    )

    payload = write_data_lake_manifest(project_root=tmp_path, as_of="2026-06-13", output_dir=tmp_path / "out")

    outputs = payload["outputs"]
    saved = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
    cursors = json.loads(Path(outputs["replay_cursors_json"]).read_text(encoding="utf-8"))

    assert Path(outputs["json"]).name == "DataLakeManifest_13062026.json"
    assert saved["asset_count"] == 1
    assert cursors["schema"] == "EVAOSDataLakeReplayCursorV1"
    assert Path(outputs["assets_csv"]).read_text(encoding="utf-8").startswith("asset_id,dataset,asset_type")
    assert "# Reproducible Data Lake" in Path(outputs["markdown"]).read_text(encoding="utf-8")
    assert Path(outputs["latest_json"]).exists()
    assert Path(outputs["latest_replay_cursors_json"]).exists()


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
