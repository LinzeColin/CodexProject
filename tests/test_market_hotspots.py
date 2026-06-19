import numpy as np
import pandas as pd

from quantlab.analysis import (
    HOTSPOT_CACHE_DIRECTORY_SUMMARY_SCHEMA,
    HOTSPOT_CACHE_STATUS_SCHEMA,
    HOTSPOT_PERSISTED_CACHE_SCHEMA,
    HOTSPOT_REFRESH_TTL_SECONDS,
    HOTSPOT_REQUEST_TRACE_SCHEMA,
    HOTSPOT_RUNTIME_SUMMARY_SCHEMA,
    build_hotspot_evidence_gate_rows,
    build_hotspot_history,
    default_hotspot_universe,
    hotspot_cache_directory_summary,
    hotspot_focus_rows,
    hotspot_persisted_cache_status,
    hotspot_request_trace_summary,
    hotspot_runtime_cache_key,
    hotspot_runtime_summary,
    hotspot_state,
    hotspot_summary,
    invalidate_hotspot_persisted_cache,
    load_hotspot_persisted_cache,
    write_hotspot_persisted_cache,
)


def _bars(close_values):
    index = pd.date_range("2026-01-01 09:30", periods=len(close_values), freq="h")
    close = np.array(close_values, dtype=float)
    return pd.DataFrame(
        {
            "datetime": index,
            "symbol": "TEST",
            "market": "US",
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 100000,
        }
    )


def test_default_hotspot_universe_covers_cross_asset_market_view():
    us = default_hotspot_universe("US")
    roles = {item.role for item in us}
    symbols = {item.symbol for item in us}

    assert HOTSPOT_REFRESH_TTL_SECONDS == 3600
    assert {"大盘宽基", "科技成长", "避险资产", "风险温度"}.issubset(roles)
    assert {"SPY", "QQQ", "GLD", "^VIX"}.issubset(symbols)


def test_build_hotspot_history_returns_time_slices_and_summary():
    instruments = default_hotspot_universe("US")[:2]
    frames = {
        instruments[0].symbol: _bars(np.linspace(100, 140, 90)),
        instruments[1].symbol: _bars(np.r_[np.linspace(120, 100, 45), np.linspace(100, 130, 45)]),
    }

    history = build_hotspot_history(frames, instruments, data_source="Sample", max_snapshots=12)
    latest = str(history["snapshot_time"].max())
    summary = hotspot_summary(history, latest)
    focus = hotspot_focus_rows(history, latest, n=1)

    assert not history.empty
    assert history["snapshot_time"].nunique() == 12
    assert {"instant_heat_score", "heat_score", "heat_score_delta", "hotspot_state", "bubble_size", "evidence_note"}.issubset(history.columns)
    assert summary.object_count == 2
    assert summary.average_heat_score > 0
    assert len(focus) == 1


def test_hotspot_runtime_summary_is_compact_and_uses_requested_count():
    instruments = default_hotspot_universe("US")[:6]
    frames = {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments[:5]}
    history = build_hotspot_history(frames, instruments, data_source="Sample", max_snapshots=24)
    request_key = hotspot_runtime_cache_key(
        data_source="Sample",
        market="US",
        interval="60min",
        instruments=instruments,
        display_start="2026-01-01",
        display_end="2026-01-05",
        max_snapshots=24,
    )

    summary = hotspot_runtime_summary(
        history,
        errors=[],
        data_source="Sample",
        market="US",
        interval="60min",
        requested_count=len(instruments),
        max_snapshots=24,
        request_key=request_key,
    )

    assert summary["schema"] == HOTSPOT_RUNTIME_SUMMARY_SCHEMA
    assert summary["status"] in {"Review", "Block"}
    assert summary["request_key"] == request_key
    assert summary["requested_count"] == 6
    assert summary["success_count"] == 5
    assert summary["coverage_rate"] == round(5 / 6, 4)
    assert summary["slice_count"] == 24
    assert summary["row_count"] == 24 * 5
    assert "raw price frames" in summary["token_policy"]
    assert "orders" in summary["safety_boundary"]


def test_hotspot_runtime_summary_marks_persisted_cache_hit():
    instruments = default_hotspot_universe("US")[:5]
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )

    summary = hotspot_runtime_summary(
        history,
        [],
        data_source="Sample",
        market="US",
        interval="60min",
        requested_count=len(instruments),
        max_snapshots=12,
        request_key="abc123",
        cache_source="persisted",
        persisted_cache_age_seconds=42.4,
    )

    assert summary["cache_hit"] is True
    assert summary["cache_source"] == "persisted"
    assert summary["persisted_cache_age_seconds"] == 42.4
    assert summary["cards"][3]["value"] == "Persisted Hit"
    assert "data/cache" in summary["token_policy"]


def test_hotspot_request_trace_summary_is_compact_and_flags_slow_failures():
    trace = [
        {"symbol": "FAST", "name": "Fast", "market": "US", "provider_symbol": "FAST", "status": "Pass", "elapsed_ms": 12.3, "row_count": 80},
        {"symbol": "SLOW", "name": "Slow", "market": "US", "provider_symbol": "SLOW", "status": "Pass", "elapsed_ms": 1234.5, "row_count": 80},
        {"symbol": "BAD", "name": "Bad", "market": "US", "provider_symbol": "BAD", "status": "Fail", "elapsed_ms": 50.0, "error": "network timeout with a long provider payload that should be truncated"},
    ]

    summary = hotspot_request_trace_summary(trace)

    assert summary["schema"] == HOTSPOT_REQUEST_TRACE_SCHEMA
    assert summary["status"] == "Review"
    assert summary["request_count"] == 3
    assert summary["success_count"] == 2
    assert summary["failed_count"] == 1
    assert summary["slowest"][0]["symbol"] == "SLOW"
    assert "raw price frames" in summary["token_policy"]


def test_hotspot_persisted_cache_round_trips_and_expires(tmp_path):
    instruments = default_hotspot_universe("US")[:5]
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )
    written_at = pd.Timestamp("2026-06-16T00:00:00Z")
    summary = hotspot_runtime_summary(
        history,
        [],
        data_source="Sample",
        market="US",
        interval="60min",
        requested_count=len(instruments),
        max_snapshots=12,
        request_key="abc123",
    )

    report = write_hotspot_persisted_cache(
        tmp_path,
        request_key="abc123",
        history=history,
        errors=[{"代码": "BAD", "名称": "Bad", "错误": "missing"}],
        summary=summary,
        now=written_at,
    )
    loaded = load_hotspot_persisted_cache(
        tmp_path,
        request_key="abc123",
        now=written_at + pd.Timedelta(seconds=120),
    )
    expired = load_hotspot_persisted_cache(
        tmp_path,
        request_key="abc123",
        now=written_at + pd.Timedelta(seconds=HOTSPOT_REFRESH_TTL_SECONDS + 1),
    )

    assert report["schema"] == HOTSPOT_PERSISTED_CACHE_SCHEMA
    assert report["status"] == "Written"
    assert loaded is not None
    assert loaded["status"] == "Hit"
    assert loaded["age_seconds"] == 120.0
    assert len(loaded["history"]) == len(history)
    assert loaded["errors"][0]["代码"] == "BAD"
    assert expired is None


def test_hotspot_cache_status_directory_summary_and_invalidate(tmp_path):
    instruments = default_hotspot_universe("US")[:5]
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )
    written_at = pd.Timestamp("2026-06-16T00:00:00Z")
    summary = hotspot_runtime_summary(
        history,
        [],
        data_source="Sample",
        market="US",
        interval="60min",
        requested_count=len(instruments),
        max_snapshots=12,
        request_key="abc123",
    )
    write_hotspot_persisted_cache(tmp_path, request_key="abc123", history=history, errors=[], summary=summary, now=written_at)

    status = hotspot_persisted_cache_status(tmp_path, request_key="abc123", now=written_at + pd.Timedelta(seconds=120))
    directory = hotspot_cache_directory_summary(tmp_path, now=written_at + pd.Timedelta(seconds=120))
    deleted = invalidate_hotspot_persisted_cache(tmp_path, request_key="abc123")
    missing = hotspot_persisted_cache_status(tmp_path, request_key="abc123", now=written_at + pd.Timedelta(seconds=121))

    assert status["schema"] == HOTSPOT_CACHE_STATUS_SCHEMA
    assert status["state"] == "hit"
    assert status["age_seconds"] == 120.0
    assert status["remaining_seconds"] == HOTSPOT_REFRESH_TTL_SECONDS - 120
    assert status["row_count"] == len(history)
    assert directory["schema"] == HOTSPOT_CACHE_DIRECTORY_SUMMARY_SCHEMA
    assert directory["file_count"] == 1
    assert directory["valid_count"] == 1
    assert deleted["status"] == "Deleted"
    assert deleted["bytes_removed"] > 0
    assert missing["state"] == "miss"


def test_hotspot_persisted_cache_preserves_compact_request_trace(tmp_path):
    instruments = default_hotspot_universe("US")[:5]
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )
    summary = hotspot_runtime_summary(history, [], data_source="Sample", market="US", interval="60min", request_key="abc123")
    trace = [{"symbol": "SPY", "name": "S&P 500 ETF", "market": "US", "provider_symbol": "SPY", "status": "Pass", "elapsed_ms": 18.2, "row_count": 96}]

    write_hotspot_persisted_cache(tmp_path, request_key="abc123", history=history, errors=[], summary=summary, request_trace=trace)
    loaded = load_hotspot_persisted_cache(tmp_path, request_key="abc123")

    assert loaded is not None
    assert loaded["request_trace"][0]["symbol"] == "SPY"
    assert loaded["request_trace"][0]["elapsed_ms"] == 18.2


def test_hotspot_cache_directory_summary_counts_expired_and_corrupt(tmp_path):
    instruments = default_hotspot_universe("US")[:5]
    history = build_hotspot_history(
        {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments},
        instruments,
        data_source="Sample",
        max_snapshots=12,
    )
    written_at = pd.Timestamp("2026-06-16T00:00:00Z")
    summary = hotspot_runtime_summary(history, [], data_source="Sample", market="US", interval="60min", request_key="expired")
    write_hotspot_persisted_cache(tmp_path, request_key="expired", history=history, errors=[], summary=summary, now=written_at)
    (tmp_path / "bad.json").write_text("{not-json", encoding="utf-8")

    directory = hotspot_cache_directory_summary(tmp_path, now=written_at + pd.Timedelta(seconds=HOTSPOT_REFRESH_TTL_SECONDS + 5))

    assert directory["file_count"] == 2
    assert directory["expired_count"] == 1
    assert directory["invalid_count"] == 1


def test_hotspot_evidence_gate_rows_accept_requested_count_for_short_data_gaps():
    instruments = default_hotspot_universe("US")[:6]
    frames = {instrument.symbol: _bars(np.linspace(100, 130, 96)) for instrument in instruments[:4]}
    history = build_hotspot_history(frames, instruments, data_source="Yahoo Finance", max_snapshots=12)

    rows = build_hotspot_evidence_gate_rows(
        history,
        [],
        data_source="Yahoo Finance",
        interval="60min",
        requested_count=len(instruments),
    )
    coverage = next(row for row in rows if row["检查项"] == "数据覆盖率")

    assert "请求 6 个" in coverage["说明"]
    assert coverage["状态"] == "Review"


def test_hotspot_runtime_cache_key_is_stable_across_selection_order():
    instruments = default_hotspot_universe("US")[:4]

    first = hotspot_runtime_cache_key(
        data_source="Sample",
        market="US",
        interval="60min",
        instruments=instruments,
        display_start="2026-01-01",
        display_end="2026-01-31",
        max_snapshots=96,
    )
    second = hotspot_runtime_cache_key(
        data_source="Sample",
        market="US",
        interval="60min",
        instruments=list(reversed(instruments)),
        display_start="2026-01-01",
        display_end="2026-01-31",
        max_snapshots=96,
    )
    changed = hotspot_runtime_cache_key(
        data_source="Sample",
        market="US",
        interval="1d",
        instruments=instruments,
        display_start="2026-01-01",
        display_end="2026-01-31",
        max_snapshots=96,
    )

    assert first == second
    assert first != changed
    assert len(first) == 16


def test_hotspot_display_window_does_not_recalculate_same_snapshot_context():
    instrument = default_hotspot_universe("US")[0]
    bars = _bars(np.r_[np.linspace(100, 80, 80), np.linspace(80, 130, 80)])
    target_snapshot = pd.Timestamp(bars["datetime"].iloc[-1]).isoformat()

    wide = build_hotspot_history(
        {instrument.symbol: bars},
        [instrument],
        data_source="Sample",
        max_snapshots=120,
        display_start=str(bars["datetime"].iloc[-40]),
        display_end=str(bars["datetime"].iloc[-1]),
    )
    narrow = build_hotspot_history(
        {instrument.symbol: bars},
        [instrument],
        data_source="Sample",
        max_snapshots=120,
        display_start=str(bars["datetime"].iloc[-10]),
        display_end=str(bars["datetime"].iloc[-1]),
    )

    wide_row = wide[wide["snapshot_time"].eq(target_snapshot)].iloc[0]
    narrow_row = narrow[narrow["snapshot_time"].eq(target_snapshot)].iloc[0]
    assert wide["snapshot_time"].min() < narrow["snapshot_time"].min()
    assert float(wide_row["instant_heat_score"]) == float(narrow_row["instant_heat_score"])
    assert float(wide_row["heat_score"]) == float(narrow_row["heat_score"])
    assert float(wide_row["heat_score_delta"]) == float(narrow_row["heat_score_delta"])
    assert float(wide_row["rsi14"]) == float(narrow_row["rsi14"])
    assert float(wide_row["drawdown20"]) == float(narrow_row["drawdown20"])


def test_hotspot_stable_heat_uses_fixed_recent_context_for_same_snapshot():
    instrument = default_hotspot_universe("US")[0]
    bars = _bars(
        np.r_[
            np.linspace(100, 72, 180),
            np.linspace(72, 138, 160),
            np.linspace(138, 92, 140),
            np.linspace(92, 168, 180),
        ]
    )
    target_snapshot = pd.Timestamp(bars["datetime"].iloc[-1]).isoformat()

    wide = build_hotspot_history(
        {instrument.symbol: bars},
        [instrument],
        data_source="Sample",
        max_snapshots=500,
        display_start=str(bars["datetime"].iloc[-360]),
        display_end=str(bars["datetime"].iloc[-1]),
    )
    narrow = build_hotspot_history(
        {instrument.symbol: bars},
        [instrument],
        data_source="Sample",
        max_snapshots=500,
        display_start=str(bars["datetime"].iloc[-3]),
        display_end=str(bars["datetime"].iloc[-1]),
    )

    wide_row = wide[wide["snapshot_time"].eq(target_snapshot)].iloc[0]
    narrow_row = narrow[narrow["snapshot_time"].eq(target_snapshot)].iloc[0]
    assert float(wide_row["instant_heat_score"]) == float(narrow_row["instant_heat_score"])
    assert float(wide_row["heat_score"]) == float(narrow_row["heat_score"])
    assert float(wide_row["heat_score_delta"]) == float(narrow_row["heat_score_delta"])


def test_hotspot_date_only_display_end_includes_full_intraday_session():
    instrument = default_hotspot_universe("US")[0]
    bars = _bars(np.linspace(100, 120, 80))
    latest_snapshot = pd.Timestamp(bars["datetime"].iloc[-1]).isoformat()

    history = build_hotspot_history(
        {instrument.symbol: bars},
        [instrument],
        data_source="Sample",
        max_snapshots=120,
        display_start=str(pd.Timestamp(bars["datetime"].iloc[-30]).date()),
        display_end=str(pd.Timestamp(bars["datetime"].iloc[-1]).date()),
    )

    assert str(history["snapshot_time"].max()) == latest_snapshot


def test_hotspot_stable_heat_limits_single_slice_jump():
    instrument = default_hotspot_universe("US")[0]
    bars = _bars(np.r_[np.linspace(100, 100, 35), np.linspace(100, 190, 10), np.linspace(190, 70, 10), np.linspace(70, 180, 20)])

    history = build_hotspot_history(
        {instrument.symbol: bars},
        [instrument],
        data_source="Sample",
        max_snapshots=80,
    )

    deltas = pd.to_numeric(history["heat_score_delta"], errors="coerce").abs().dropna()
    assert not deltas.empty
    assert float(deltas.max()) <= 12.0


def test_hotspot_history_aligns_misaligned_symbol_timestamps_to_same_cross_section():
    instruments = default_hotspot_universe("US")[:2]
    first = _bars(np.linspace(100, 130, 80))
    second = _bars(np.linspace(120, 90, 80))
    second["datetime"] = second["datetime"] + pd.Timedelta(minutes=30)
    selected_snapshot = pd.Timestamp(first["datetime"].iloc[-1]).isoformat()

    history = build_hotspot_history(
        {
            instruments[0].symbol: first,
            instruments[1].symbol: second,
        },
        instruments,
        data_source="Sample",
        max_snapshots=20,
    )
    current = history[history["snapshot_time"].eq(selected_snapshot)]

    assert set(current["symbol"]) == {instruments[0].symbol, instruments[1].symbol}
    assert set(current["bar_time"]) == {
        pd.Timestamp(first["datetime"].iloc[-1]).isoformat(),
        pd.Timestamp(second["datetime"].iloc[-2]).isoformat(),
    }


def test_hotspot_state_boundaries_are_stable():
    assert hotspot_state(80) == "强势扩散"
    assert hotspot_state(60) == "局部偏强"
    assert hotspot_state(50) == "中性轮动"
    assert hotspot_state(35) == "局部偏弱"
    assert hotspot_state(20) == "风险降温"
