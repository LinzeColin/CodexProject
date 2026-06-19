from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quantlab.data.market_events import (
    bars_to_market_events,
    build_market_event_log,
    read_market_events_jsonl,
    upsert_market_events_jsonl,
    write_market_event_log,
)


def test_bars_to_market_events_are_sorted_and_stable() -> None:
    bars = _bars()

    first = bars_to_market_events(bars, symbol="SPY", market="US", interval="1d", source="sample")
    second = bars_to_market_events(bars, symbol="SPY", market="US", interval="1d", source="sample")

    assert [event["event_time"] for event in first] == sorted(event["event_time"] for event in first)
    assert [event["event_id"] for event in first] == [event["event_id"] for event in second]
    assert first[0]["event_type"] == "BarClosed"
    assert first[0]["quality_status"] == "Pass"
    assert first[0]["payload"]["close"] == 100.5


def test_build_market_event_log_fail_closes_empty_input() -> None:
    payload = build_market_event_log(pd.DataFrame(), symbol="SPY", market="US", interval="1d", source="sample")

    assert payload["schema"] == "EVAOSMarketEventLogV1"
    assert payload["event_log_status"] == "Empty"
    assert payload["event_count"] == 0
    assert payload["quality_report"]["quality_status"] == "Empty"


def test_write_market_event_log_outputs_json_jsonl_csv_and_markdown(tmp_path: Path) -> None:
    payload = write_market_event_log(
        _bars(),
        symbol="SPY",
        market="US",
        interval="1d",
        source="sample",
        as_of="2026-06-13",
        output_dir=tmp_path,
        project_root=tmp_path,
    )

    outputs = payload["outputs"]
    saved = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
    events = read_market_events_jsonl(outputs["jsonl"])

    assert Path(outputs["json"]).name == "MarketEventLog_SPY_1d_13062026.json"
    assert saved["event_count"] == 3
    assert len(events) == 3
    assert Path(outputs["csv"]).read_text(encoding="utf-8").startswith("event_id,event_time,event_type")
    assert "# Market Event Layer" in Path(outputs["markdown"]).read_text(encoding="utf-8")
    assert Path(outputs["latest_json"]).exists()
    assert Path(outputs["latest_jsonl"]).exists()


def test_upsert_market_events_jsonl_dedupes_by_event_id(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    events = bars_to_market_events(_bars(), symbol="SPY", market="US", interval="1d", source="sample")

    upsert_market_events_jsonl(path, events[:2])
    upsert_market_events_jsonl(path, events)

    saved = read_market_events_jsonl(path)
    assert len(saved) == 3
    assert saved[-1]["event_time"] == "2026-01-05T00:00:00"
    assert (tmp_path / "events.jsonl.lock").exists()


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
