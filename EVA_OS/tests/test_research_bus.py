from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from quantlab.integrations.research_bus import (
    bus_quantlab_results_frame,
    bus_validation_task_frame,
    extract_symbols,
    export_research_bus_snapshot,
    holding_symbol_mappings_frame,
    parse_report_file,
    portfolio_transactions_frame,
    _ocr_runtime_available,
    push_bus_validation_tasks_to_quantlab_queue,
    sync_holding_symbol_mappings_to_bus,
    sync_holdings_to_bus,
    sync_industry_reports_to_bus,
    sync_portfolio_transactions_to_bus,
    sync_quantlab_results_to_bus,
)
from quantlab.research.validation_queue import load_validation_tasks


class ResearchBusTest(unittest.TestCase):
    def test_industry_report_sync_generates_validation_tasks_and_queue_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_root = root / "行研报告"
            report_root.mkdir()
            report_path = report_root / "银行策略_04062026.md"
            report_path.write_text(
                "银行行业研究：600000 需要验证 RSI 和均线趋势信号，观察政策催化后回撤是否可控。",
                encoding="utf-8",
            )
            db_path = root / "ResearchBus.sqlite"
            queue_path = root / "ValidationTasks.json"

            result = sync_industry_reports_to_bus(report_root, db_path)
            tasks = bus_validation_task_frame(db_path)
            pushed = push_bus_validation_tasks_to_quantlab_queue(db_path, queue_path)
            queue = load_validation_tasks(queue_path)

            self.assertEqual(result.reports, 1)
            self.assertGreaterEqual(result.validation_tasks, 1)
            self.assertGreaterEqual(len(tasks), 1)
            self.assertIn("600000.SH", set(tasks["symbol"]))
            self.assertGreaterEqual(pushed, 1)
            self.assertEqual(len(queue), pushed)

    def test_extract_symbols_does_not_treat_market_suffix_as_us_ticker(self) -> None:
        symbols = extract_symbols("这是今天的支付宝持仓截图，含 600000.SH 和 AAPL。")

        self.assertIn("600000.SH", symbols)
        self.assertIn("AAPL", symbols)
        self.assertNotIn("SH", symbols)

    def test_quantlab_results_are_written_to_bus_and_ai_outbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_root = root / "量化回测分析"
            run_dir = report_root / "2026-06-04"
            run_dir.mkdir(parents=True)
            metadata_path = run_dir / "RunMetadata_AAPL.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "metrics": {
                            "total_return": 0.1234,
                            "annualized_return": 0.052,
                            "sharpe": 1.1,
                            "max_drawdown": -0.08,
                            "trade_count": 4,
                            "ending_equity": 11234,
                        },
                        "metadata": {
                            "strategy": {"strategy_id": "demo_strategy"},
                            "backtest": {"symbol": "AAPL", "market": "US", "initial_cash": 10000},
                        },
                        "decision_quality": {"status": "ContinueResearch", "score": 82},
                        "risk_gate": {"status": "ContinueResearch"},
                        "data_quality": {"status": "Pass"},
                        "cross_validation": {"status": "Pass"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            db_path = root / "ResearchBus.sqlite"
            ai_root = root / "AI-Research-System"

            result = sync_quantlab_results_to_bus(report_root, db_path, ai_research_root=ai_root)
            frame = bus_quantlab_results_frame(db_path)
            outbox = ai_root / "data" / "report_artifacts" / "quantlab_bridge" / "QuantLabResults.json"

            self.assertEqual(result.quantlab_results, 1)
            self.assertTrue(outbox.exists())
            self.assertEqual(frame.iloc[0]["strategy_id"], "demo_strategy")
            self.assertEqual(frame.iloc[0]["symbol"], "AAPL")

    def test_holdings_sync_writes_master_table_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            holdings = pd.DataFrame(
                [
                    {
                        "source_system": "量化回测系统导入",
                        "source_file": "holdings.csv",
                        "symbol": "AAPL",
                        "name": "Apple",
                        "market": "US",
                        "quantity": 10,
                        "cost_basis": 150,
                        "position_value": 2000,
                        "unrealized_pnl": 100,
                        "weight": 1.0,
                        "updated_at": "2026-06-04",
                        "source_modified_time": "2026-06-04T10:00:00",
                    }
                ]
            )

            result = sync_holdings_to_bus(holdings, db_path)
            snapshot = export_research_bus_snapshot(db_path, root / "snapshot.json")

            with sqlite3.connect(db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM holdings_master").fetchone()[0]

            self.assertEqual(result.holdings, 1)
            self.assertEqual(count, 1)
            self.assertTrue(snapshot.exists())

    def test_holding_symbol_mappings_sync_writes_shared_proxy_table_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            holdings = pd.DataFrame(
                [
                    {"symbol": "", "name": "国泰黄金ETF联接A", "market": "CN", "position_value": 1000},
                    {"symbol": "AAPL", "name": "Apple", "market": "US", "position_value": 2000},
                    {"symbol": "", "name": "未知主动基金", "market": "CN", "position_value": 500},
                ]
            )

            result = sync_holding_symbol_mappings_to_bus(holdings, db_path)
            frame = holding_symbol_mappings_frame(db_path)
            snapshot = json.loads(export_research_bus_snapshot(db_path, root / "snapshot.json").read_text(encoding="utf-8"))

            self.assertEqual(result.holding_symbol_mappings, 3)
            self.assertEqual(len(frame), 3)
            self.assertIn("518880", set(frame["proxy_symbol"]))
            self.assertIn("ConfirmedSymbol", set(frame["status"]))
            self.assertIn("holding_symbol_mappings", snapshot["tables"])
            with sqlite3.connect(db_path) as conn:
                payload = conn.execute("SELECT summary_json FROM system_state WHERE system_name='HoldingSymbolMappings'").fetchone()[0]
            state = json.loads(payload)
            self.assertEqual(state["entity_registry_schema"], "QuantLabEntityRegistryV1")
            self.assertEqual(state["entity_status_counts"]["MissingSymbol"], 1)
            self.assertEqual(state["entity_status_counts"]["ProxyMapped"], 1)
            self.assertEqual(state["entity_status_counts"]["TradableSymbol"], 1)

    def test_portfolio_transactions_sync_writes_shared_table_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            transactions = pd.DataFrame(
                [
                    {
                        "source_system": "支付宝视频候选交易",
                        "account": "支付宝基金账户",
                        "trade_date": "2026-06-04",
                        "order_time": "14:48:55",
                        "timezone": "Asia/Shanghai",
                        "name": "易方达石油化工ETF联接A",
                        "market": "CN",
                        "asset_type": "fund",
                        "side": "买入",
                        "order_type": "manual",
                        "order_amount": "500.00元",
                        "status": "交易进行中",
                        "quality_status": "PendingConfirmation",
                        "source_path": "/tmp/video.mp4",
                        "evidence_frame": "frame_0021-frame_0025",
                    }
                ]
            )

            result = sync_portfolio_transactions_to_bus(transactions, db_path)
            frame = portfolio_transactions_frame(db_path)
            snapshot = json.loads(export_research_bus_snapshot(db_path, root / "snapshot.json").read_text(encoding="utf-8"))

            self.assertEqual(result.portfolio_transactions, 1)
            self.assertEqual(len(frame), 1)
            self.assertEqual(frame.iloc[0]["name"], "易方达石油化工ETF联接A")
            self.assertEqual(float(frame.iloc[0]["order_amount"]), 500.0)
            self.assertEqual(frame.iloc[0]["quality_status"], "PendingConfirmation")
            self.assertIn("portfolio_transactions", snapshot["tables"])

    def test_pdf_parser_uses_pypdf_text_extraction_when_available(self) -> None:
        class FakePage:
            def extract_text(self) -> str:
                return "600000 需要验证 RSI 信号"

        class FakeReader:
            def __init__(self, _: str) -> None:
                self.pages = [FakePage()]

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "report.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            fake_module = SimpleNamespace(PdfReader=FakeReader)

            with patch.dict(sys.modules, {"pypdf": fake_module}):
                parsed = parse_report_file(pdf_path)

            self.assertIn("600000", parsed["text"])
            self.assertEqual(parsed["parser_warning"], "")

    def test_pdf_parser_warns_when_text_and_ocr_are_unavailable(self) -> None:
        class EmptyPage:
            def extract_text(self) -> str:
                return ""

        class EmptyReader:
            def __init__(self, _: str) -> None:
                self.pages = [EmptyPage()]

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "scan.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            fake_module = SimpleNamespace(PdfReader=EmptyReader)

            with patch.dict(sys.modules, {"pypdf": fake_module}), patch(
                "quantlab.integrations.research_bus._ocr_runtime_available",
                return_value=False,
            ):
                parsed = parse_report_file(pdf_path)

            self.assertEqual(parsed["text"], "")
            self.assertIn("OCR 引擎未配置", parsed["parser_warning"])

    def test_ocr_runtime_probe_returns_boolean(self) -> None:
        self.assertIsInstance(_ocr_runtime_available(), bool)


if __name__ == "__main__":
    unittest.main()
