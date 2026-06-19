from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

from quantlab.integrations import (
    canonical_holdings_frame,
    holdings_exposure_frame,
    holdings_quality_frame,
    holdings_sync_history_frame,
    load_holdings_book,
    load_pending_orders_frame,
    sync_holdings_book,
    upsert_manual_holding,
)
from quantlab.integrations.holdings_book import HoldingSourceSpec, default_alipay_ledger_dirs


def test_sync_holdings_book_keeps_latest_confirmed_holding_and_saves_book():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_a = root / "consumer"
        source_b = root / "quantlab"
        source_a.mkdir()
        source_b.mkdir()
        pd.DataFrame(
            [
                {"symbol": "AAPL", "name": "Apple Old", "market": "US", "position_value": 10000, "updated_at": "2026-06-01"},
                {"symbol": "MSFT", "name": "Microsoft", "market": "US", "position_value": 5000, "updated_at": "2026-06-01"},
            ]
        ).to_csv(source_a / "holdings.csv", index=False)
        pd.DataFrame(
            [
                {"symbol": "AAPL", "name": "Apple New", "market": "US", "position_value": 12000, "updated_at": "2026-06-03"},
            ]
        ).to_csv(source_b / "holdings.csv", index=False)
        book_path = root / "HoldingsBook.json"
        specs = [
            HoldingSourceSpec("消费行为分析系统", (source_a,), "test source a"),
            HoldingSourceSpec("量化回测系统导入", (source_b,), "test source b"),
        ]

        result = sync_holdings_book(specs=specs, book_path=book_path)
        saved = load_holdings_book(book_path)

        assert result.raw_row_count == 3
        assert result.canonical_row_count == 2
        assert list(saved["symbol"]) == ["AAPL", "MSFT"]
        assert saved.iloc[0]["name"] == "Apple New"
        assert round(float(saved["weight"].sum()), 6) == 1.0


def test_sync_holdings_book_does_not_clear_existing_book_when_sources_are_empty():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source"
        empty = root / "empty"
        source.mkdir()
        empty.mkdir()
        book_path = root / "HoldingsBook.json"
        pd.DataFrame([{"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 12000, "updated_at": "2026-06-03"}]).to_csv(source / "holdings.csv", index=False)

        sync_holdings_book(specs=[HoldingSourceSpec("量化回测系统导入", (source,), "source")], book_path=book_path)
        result = sync_holdings_book(specs=[HoldingSourceSpec("量化回测系统导入", (empty,), "empty")], book_path=book_path)
        saved = load_holdings_book(book_path)

        assert result.raw_row_count == 0
        assert result.canonical_row_count == 1
        assert saved.iloc[0]["symbol"] == "AAPL"
        assert "已保留现有正式持仓" in "；".join(result.warnings)


def test_manual_holding_survives_external_sync():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source"
        source.mkdir()
        book_path = root / "HoldingsBook.json"
        upsert_manual_holding({"symbol": "510300", "name": "沪深300ETF", "market": "CN", "position_value": 8000}, book_path=book_path)
        pd.DataFrame([{"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 12000, "updated_at": "2026-06-03"}]).to_csv(source / "holdings.csv", index=False)

        result = sync_holdings_book(specs=[HoldingSourceSpec("量化回测系统导入", (source,), "source")], book_path=book_path)
        saved = load_holdings_book(book_path)

        assert result.canonical_row_count == 2
        assert set(saved["symbol"]) == {"510300", "AAPL"}


def test_corrupt_holdings_book_blocks_overwrite():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source"
        source.mkdir()
        book_path = root / "HoldingsBook.json"
        book_path.write_text("{bad json", encoding="utf-8")
        pd.DataFrame([{"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 12000}]).to_csv(source / "holdings.csv", index=False)

        with pytest.raises(ValueError):
            sync_holdings_book(specs=[HoldingSourceSpec("量化回测系统导入", (source,), "source")], book_path=book_path)

        assert book_path.read_text(encoding="utf-8") == "{bad json"


def test_duplicate_source_paths_and_pending_files_are_ignored():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source"
        source.mkdir()
        pd.DataFrame([{"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 12000}]).to_csv(source / "holdings.csv", index=False)
        pd.DataFrame([{"name": "待确认基金", "amount": 5000, "status": "付款成功，确认中"}]).to_csv(source / "pending_orders.csv", index=False)
        specs = [HoldingSourceSpec("量化回测系统导入", (source, source), "source")]

        result = sync_holdings_book(specs=specs, book_path=root / "HoldingsBook.json")
        saved = load_holdings_book(root / "HoldingsBook.json")

        assert result.source_file_count == 1
        assert result.raw_row_count == 1
        assert list(saved["symbol"]) == ["AAPL"]


def test_default_alipay_dirs_require_explicit_external_private_path(monkeypatch):
    monkeypatch.delenv("QUANTLAB_ALIPAY_LEDGER_DIR", raising=False)

    dirs = default_alipay_ledger_dirs()

    assert len(dirs) == 1
    assert "AI-Research-System" not in str(dirs[0])


def test_canonical_holdings_filters_zero_pending_like_rows():
    frame = pd.DataFrame(
        [
            {"source_system": "支付宝持仓账本", "symbol": "", "name": "待确认基金", "market": "CN", "position_value": 0, "quantity": 0, "weight": 0},
            {"source_system": "手动录入", "symbol": "510300", "name": "沪深300ETF", "market": "CN", "position_value": 8000, "quantity": 100, "weight": 0},
        ]
    )

    canonical = canonical_holdings_frame(frame)

    assert len(canonical) == 1
    assert canonical.iloc[0]["symbol"] == "510300"


def test_holdings_quality_and_exposure_frames_are_user_readable():
    frame = pd.DataFrame(
        [
            {"source_system": "手动录入", "symbol": "510300", "name": "沪深300ETF", "market": "CN", "position_value": 8000, "quantity": 100, "weight": 0.8, "updated_at": "2026-06-03", "source_file": "Manual", "cost_basis": 0, "unrealized_pnl": 0, "source_modified_time": "2026-06-03"},
            {"source_system": "手动录入", "symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 2000, "quantity": 10, "weight": 0.2, "updated_at": "2026-06-03", "source_file": "Manual", "cost_basis": 0, "unrealized_pnl": 0, "source_modified_time": "2026-06-03"},
        ]
    )

    quality = holdings_quality_frame(frame)
    exposure = holdings_exposure_frame(frame)

    assert set(quality["检查项"]) >= {"持仓数量", "市值字段", "集中度"}
    assert set(exposure["维度"]) == {"市场", "来源"}


def test_holdings_exposure_uses_weight_when_position_value_is_missing():
    frame = pd.DataFrame(
        [
            {"source_system": "手动录入", "symbol": "510300", "name": "沪深300ETF", "market": "CN", "position_value": 0, "quantity": 0, "weight": 0.8, "updated_at": "2026-06-03", "source_file": "Manual", "cost_basis": 0, "unrealized_pnl": 0, "source_modified_time": "2026-06-03"},
            {"source_system": "手动录入", "symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 0, "quantity": 0, "weight": 0.2, "updated_at": "2026-06-03", "source_file": "Manual", "cost_basis": 0, "unrealized_pnl": 0, "source_modified_time": "2026-06-03"},
        ]
    )

    exposure = holdings_exposure_frame(frame)

    cn = exposure[(exposure["维度"] == "市场") & (exposure["类别"] == "CN")].iloc[0]
    assert cn["市值"] == 0.0
    assert round(float(cn["权重"]), 2) == 0.80


def test_holdings_quality_accepts_timezone_aware_updated_at():
    frame = pd.DataFrame(
        [
            {"source_system": "手动录入", "symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 2000, "quantity": 10, "weight": 1.0, "updated_at": "2026-06-03T10:00:00+08:00", "source_file": "Manual", "cost_basis": 0, "unrealized_pnl": 0, "source_modified_time": "2026-06-03"},
        ]
    )

    quality = holdings_quality_frame(frame)

    assert "更新时间" in set(quality["检查项"])


def test_pending_orders_are_loaded_separately_from_alipay_ledger():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        pd.DataFrame(
            [
                {"trade_date": "2026-06-03", "name": "测试基金", "side": "买入", "order_amount": 300, "status": "付款成功，基金份额确认中"},
            ]
        ).to_csv(root / "pending_orders.csv", index=False)

        pending = load_pending_orders_frame(alipay_dirs=(root,))

        assert len(pending) == 1
        assert "source_file" in pending.columns


def test_holdings_sync_history_accepts_schema_wrapped_history():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        history_path = root / "HoldingsImportHistory.json"
        history_path.write_text(
            '{"schema":"QuantLabHoldingsImportHistoryV1","history":[{"synced_at":"2026-06-04T22:16:41","raw_row_count":0,"canonical_row_count":28,"source_file_count":1}]}',
            encoding="utf-8",
        )

        history = holdings_sync_history_frame(history_path)

        assert len(history) == 1
        assert int(history.iloc[0]["canonical_row_count"]) == 28
        assert "book_path" in history.columns
