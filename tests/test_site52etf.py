from urllib.error import URLError
from unittest.mock import patch
import subprocess

import numpy as np
import pandas as pd

from quantlab.analysis import build_hotspot_history, default_hotspot_universe
from quantlab.integrations.site52etf import (
    SITE52ETF_COMPARISON_SCHEMA,
    SITE52ETF_PUBLIC_SNAPSHOT_SCHEMA,
    build_site52etf_hotspot_comparison,
    build_site52etf_public_snapshot,
    fetch_52etf_public_snapshot,
    load_site52etf_public_snapshot_latest,
    parse_52etf_public_page,
    site52etf_comparison_rows,
    site52etf_summary_rows,
    write_site52etf_public_snapshot,
)


SAMPLE_PAGE = """
<html>
  <body>
    <h1>大盘云图</h1>
    <nav>A股全图 上证A股 深证A股 沪深300 中证A500 创业板 科创板</nav>
    <section>上涨 平盘 下跌 成交额 比昨日 放量</section>
    <p>面积代表流通市值</p>
    <p>颜色代表涨跌幅度</p>
    <p>每8秒更新数据</p>
    <p>双击色块查看K线</p>
    <p>全屏观看效果更好</p>
    <p>按键盘方向键复盘</p>
  </body>
</html>
"""


def test_parse_52etf_public_page_extracts_market_cloud_contract():
    snapshot = parse_52etf_public_page(SAMPLE_PAGE, fetched_at="2026-06-13T00:00:00+00:00")

    assert snapshot.status == "Available"
    assert snapshot.evidence_status == "Pass"
    assert "沪深300" in snapshot.boards
    assert "成交额" in snapshot.metrics
    assert "每8秒更新数据" in snapshot.operating_notes
    assert "not as a broker" in snapshot.risk_note


def test_fetch_52etf_public_snapshot_fails_closed_when_unavailable():
    def failing_fetch(_url, _timeout):
        raise URLError("network down")

    snapshot = fetch_52etf_public_snapshot(fetch_html=failing_fetch)

    assert snapshot.status == "Unavailable"
    assert snapshot.evidence_status == "Review"
    assert "network down" in snapshot.error
    rows = site52etf_summary_rows(snapshot)
    assert any(row["项目"] == "可用性" and row["状态"] == "Unavailable" for row in rows)


def test_fetch_52etf_public_snapshot_uses_curl_fallback_after_urlopen_failure():
    completed = subprocess.CompletedProcess(args=["curl"], returncode=0, stdout=SAMPLE_PAGE, stderr="")

    with patch("quantlab.integrations.site52etf.urlopen", side_effect=URLError("certificate verify failed")):
        with patch("quantlab.integrations.site52etf.subprocess.run", return_value=completed) as run:
            snapshot = fetch_52etf_public_snapshot()

    assert snapshot.status == "Available"
    assert snapshot.evidence_status == "Pass"
    assert "沪深300" in snapshot.boards
    assert run.call_args.args[0][0] == "/usr/bin/curl"
    assert "--max-time" in run.call_args.args[0]


def test_build_52etf_public_snapshot_stays_compact_and_read_only():
    payload = build_site52etf_public_snapshot(html_text=SAMPLE_PAGE, fetched_at="2026-06-13T00:00:00+00:00")

    assert payload["schema"] == SITE52ETF_PUBLIC_SNAPSHOT_SCHEMA
    assert payload["status"] == "Available"
    assert payload["artifact_status"] == "Pass"
    assert payload["refresh_cadence_seconds"] == 8
    assert payload["interactions"]["double_click_kline"] is True
    assert payload["interactions"]["keyboard_replay"] is True
    assert payload["board_count"] >= 6
    assert "raw HTML is not stored" in payload["token_policy"]
    assert "No broker calls" in payload["safety_boundary"]
    assert "html" not in payload
    assert any(gate["gate"] == "ReadOnlyBoundary" and gate["status"] == "Pass" for gate in payload["evidence_gate"])


def test_write_and_load_52etf_public_snapshot_latest_feeds_hotspot_comparison(tmp_path):
    output_dir = tmp_path / "site52etf"
    payload = write_site52etf_public_snapshot(
        project_root=tmp_path,
        output_dir=output_dir,
        html_text=SAMPLE_PAGE,
        fetched_at="2026-06-13T00:00:00+00:00",
    )
    loaded = load_site52etf_public_snapshot_latest(project_root=tmp_path, latest_path=output_dir / "Site52ETFPublicSnapshot_latest.json")
    instruments = default_hotspot_universe("CN")
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96), symbol=instrument.symbol, market="CN") for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )

    assert payload["outputs"]["latest_json"] == "site52etf/Site52ETFPublicSnapshot_latest.json"
    assert loaded is not None
    assert loaded["schema"] == SITE52ETF_PUBLIC_SNAPSHOT_SCHEMA
    assert (output_dir / "Site52ETFPublicSnapshot_latest.json").exists()
    assert not (output_dir / "Site52ETFPublicSnapshot_latest.json").read_text(encoding="utf-8").lower().count("<html")
    comparison = build_site52etf_hotspot_comparison(loaded, history, market="CN")
    assert comparison["status"] == "Pass"
    assert comparison["source_status"] == "Available"


def test_52etf_hotspot_comparison_maps_cn_boards_to_eva_objects():
    snapshot = parse_52etf_public_page(SAMPLE_PAGE, fetched_at="2026-06-13T00:00:00+00:00")
    instruments = default_hotspot_universe("CN")
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96), symbol=instrument.symbol, market="CN") for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )

    comparison = build_site52etf_hotspot_comparison(snapshot, history, market="CN")
    rows = site52etf_comparison_rows(comparison)

    assert comparison["schema"] == SITE52ETF_COMPARISON_SCHEMA
    assert comparison["status"] == "Pass"
    assert comparison["market_status"] == "Pass"
    assert comparison["matched_board_count"] >= 3
    assert any(item["board"] == "沪深300" for item in comparison["matched_boards"])
    assert any(row["项目"] == "板块映射" for row in rows)


def test_52etf_hotspot_comparison_reviews_non_cn_market():
    snapshot = parse_52etf_public_page(SAMPLE_PAGE, fetched_at="2026-06-13T00:00:00+00:00")
    instruments = default_hotspot_universe("US")[:4]
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96), symbol=instrument.symbol, market="US") for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )

    comparison = build_site52etf_hotspot_comparison(snapshot, history, market="US")

    assert comparison["status"] == "Review"
    assert comparison["market_status"] == "Review"
    assert "A-share" in comparison["comparison_note"]


def _bars(close_values, *, symbol: str, market: str):
    index = pd.date_range("2026-01-01 09:30", periods=len(close_values), freq="h")
    close = np.array(close_values, dtype=float)
    return pd.DataFrame(
        {
            "datetime": index,
            "symbol": symbol,
            "market": market,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 100000,
        }
    )
