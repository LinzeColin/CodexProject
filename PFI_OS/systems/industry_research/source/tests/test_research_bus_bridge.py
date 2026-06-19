from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from src.integrations import research_bus_bridge


class ResearchBusBridgeTest(unittest.TestCase):
    def test_ai_research_bridge_publishes_reports_and_pulls_pfi_os_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_root = root / "行研报告"
            artifact_root = root / "artifacts"
            bridge_dir = root / "bridge"
            report_root.mkdir()
            artifact_root.mkdir()
            (report_root / "半导体策略_04062026.md").write_text(
                "半导体研究：688001 需要验证趋势信号和政策催化后的回撤。",
                encoding="utf-8",
            )
            db_path = root / "ResearchBus.sqlite"
            research_bus_bridge.initialize_research_bus(db_path)
            with closing(sqlite3.connect(db_path)) as conn, conn:
                conn.execute(
                    """
                    INSERT INTO pfi_os_results(
                        result_id, report_path, metadata_path, strategy_id, symbol, market,
                        total_return, annualized_return, max_drawdown, sharpe, research_status,
                        decision_quality_score, data_quality_status, cross_validation_status,
                        created_at, updated_at, payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "result_1",
                        "/tmp/report.docx",
                        "/tmp/metadata.json",
                        "demo_strategy",
                        "AAPL",
                        "US",
                        0.12,
                        0.05,
                        -0.08,
                        1.2,
                        "ContinueResearch",
                        80,
                        "Pass",
                        "Pass",
                        "2026-06-04T10:00:00",
                        "2026-06-04T10:00:00",
                        "{}",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO validation_tasks(
                        task_id, source_system, source_report_id, source_report_path, source_paragraph,
                        research_topic, symbol, market, signal_to_validate, sample_period,
                        cost_assumption, benchmark, status, validation_report_path, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "task_1",
                        "AI-Research-System",
                        "report_1",
                        "/tmp/report.md",
                        "验证趋势信号",
                        "半导体验证",
                        "688001.SH",
                        "CN",
                        "验证趋势信号",
                        "默认区间",
                        "默认成本",
                        "沪深300",
                        "待验证",
                        "",
                        "2026-06-04T10:00:00",
                        "2026-06-04T10:00:00",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO independent_validation_runs(
                        run_id, source_system, status, mode, manifest_path, total_rows, shard_count,
                        started_at, completed_at, output_path, payload_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "ivr_1",
                        "IndependentValidation",
                        "Planned",
                        "dry_run",
                        "",
                        1000000000,
                        10,
                        "2026-06-04T10:00:00",
                        "2026-06-04T10:00:01",
                        "/tmp/IndependentValidationRun.json",
                        "{}",
                        "2026-06-04T10:00:01",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO consumer_behavior_state(
                        state_id, source_system, db_path, run_count, transaction_count, ledger_count,
                        latest_run_id, latest_generated_at, total_amount, manual_review_count,
                        summary_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "consumerState_1",
                        "ConsumptionAnalysisSystem",
                        "/tmp/consumption.sqlite",
                        2,
                        10,
                        12,
                        "run_2",
                        "2026-06-04T10:00:00",
                        1234.5,
                        1,
                        "{}",
                        "2026-06-04T10:00:01",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO holdings_master(
                        holding_id, source_system, account, symbol, name, market, asset_type,
                        quantity, cost_basis, position_value, unrealized_pnl, weight, as_of,
                        source_path, payload_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "holding_1",
                        "支付宝视频候选持仓",
                        "支付宝基金账户",
                        "",
                        "国泰黄金ETF联接A",
                        "CN",
                        "fund",
                        0,
                        0,
                        11386.53,
                        -257.95,
                        0.123,
                        "2026-06-04T22:24:00+10:00",
                        "/tmp/video.mp4",
                        "{}",
                        "2026-06-04T22:24:00+10:00",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO holding_symbol_mappings(
                        mapping_id, source_system, holding_name, holding_market, original_symbol,
                        proxy_symbol, proxy_name, proxy_market, status, confidence, reason,
                        source, payload_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "mapping_1",
                        "PFIOS",
                        "国泰黄金ETF联接A",
                        "CN",
                        "",
                        "518880",
                        "黄金ETF代理",
                        "CN",
                        "ProxyMapped",
                        "ProxyHigh",
                        "名称包含黄金，使用 A 股黄金 ETF 作为行情代理。",
                        "HoldingSymbolMap",
                        "{}",
                        "2026-06-04T22:24:00+10:00",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO portfolio_transactions(
                        transaction_id, source_system, account, trade_date, order_time, timezone,
                        symbol, name, market, asset_type, side, order_type, order_amount,
                        confirmed_amount, confirmed_units, confirmed_nav, fee, status,
                        quality_status, source_path, evidence_frame, notes, payload_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "txn_1",
                        "支付宝视频候选交易",
                        "支付宝基金账户",
                        "2026-06-04",
                        "14:48:55",
                        "Asia/Shanghai",
                        "",
                        "易方达石油化工ETF联接A",
                        "CN",
                        "fund",
                        "买入",
                        "manual",
                        500,
                        0,
                        0,
                        0,
                        0,
                        "交易进行中",
                        "PendingConfirmation",
                        "/tmp/video.mp4",
                        "frame_0021-frame_0025",
                        "",
                        "{}",
                        "2026-06-04T22:24:00+10:00",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO holding_update_candidates(
                        candidate_id, source_system, account, candidate_type, status, quality_status,
                        content_text, attachments_json, extracted_symbols_json, source_request_id,
                        source_chat_input_id, payload_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "candidate_1",
                        "AI-Research-Chat",
                        "支付宝基金账户",
                        "holding_attachment",
                        "PendingReview",
                        "Candidate",
                        "这是今天的持仓截图",
                        json.dumps([{"path": "/tmp/holding.png", "media_type": "image/png"}], ensure_ascii=False),
                        "[]",
                        "request_1",
                        "chat_1",
                        "{}",
                        "2026-06-04T22:24:00+10:00",
                        "2026-06-04T22:24:00+10:00",
                    ),
                )

            with patch.object(research_bus_bridge, "REPORTS_HOME", report_root), patch.object(
                research_bus_bridge, "ARTIFACTS_HOME", artifact_root
            ), patch.object(research_bus_bridge, "BRIDGE_DIR", bridge_dir):
                payload = research_bus_bridge.sync_research_bus(db_path, report_limit=10, result_limit=10)

            self.assertEqual(payload["published_reports"], 1)
            self.assertEqual(payload["pfi_os_result_count"], 1)
            self.assertGreaterEqual(payload["validation_task_count"], 1)
            self.assertEqual(payload["independent_validation_run_count"], 1)
            self.assertEqual(payload["consumer_behavior_state_count"], 1)
            self.assertEqual(payload["holdings_master_count"], 1)
            self.assertEqual(payload["holding_symbol_mapping_count"], 1)
            self.assertEqual(payload["portfolio_transaction_count"], 1)
            self.assertEqual(payload["holding_update_candidate_count"], 1)
            self.assertTrue(Path(payload["pfi_os_results_path"]).exists())
            self.assertTrue(Path(payload["validation_tasks_path"]).exists())
            self.assertTrue(Path(payload["independent_validation_runs_path"]).exists())
            self.assertTrue(Path(payload["consumer_behavior_state_path"]).exists())
            self.assertTrue(Path(payload["holdings_master_path"]).exists())
            self.assertTrue(Path(payload["holding_symbol_mappings_path"]).exists())
            self.assertTrue(Path(payload["portfolio_transactions_path"]).exists())
            self.assertTrue(Path(payload["holding_update_candidates_path"]).exists())
            pulled = json.loads(Path(payload["pfi_os_results_path"]).read_text(encoding="utf-8"))
            self.assertEqual(pulled["results"][0]["strategy_id"], "demo_strategy")
            holdings = json.loads(Path(payload["holdings_master_path"]).read_text(encoding="utf-8"))
            mappings = json.loads(Path(payload["holding_symbol_mappings_path"]).read_text(encoding="utf-8"))
            transactions = json.loads(Path(payload["portfolio_transactions_path"]).read_text(encoding="utf-8"))
            candidates = json.loads(Path(payload["holding_update_candidates_path"]).read_text(encoding="utf-8"))
            self.assertEqual(holdings["holdings"][0]["name"], "国泰黄金ETF联接A")
            self.assertEqual(mappings["holding_symbol_mappings"][0]["proxy_symbol"], "518880")
            self.assertEqual(transactions["portfolio_transactions"][0]["quality_status"], "PendingConfirmation")
            self.assertEqual(candidates["holding_update_candidates"][0]["status"], "PendingReview")

    def test_ai_research_can_submit_and_process_bus_api_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            research_bus_bridge.initialize_research_bus(db_path)
            request = research_bus_bridge.submit_bus_request(
                "pull_holding_symbol_mappings",
                {"limit": 5},
                source_system="UnitTest",
                target_system="AI-Research-System",
                db_path=db_path,
            )

            result = research_bus_bridge.process_pending_research_bus_requests(db_path, system_name="AI-Research-System")

            self.assertEqual(request["status"], "Pending")
            self.assertEqual(result["processed"], 1)
            with closing(sqlite3.connect(db_path)) as conn, conn:
                status = conn.execute("SELECT status FROM bus_api_requests WHERE request_id=?", (request["request_id"],)).fetchone()[0]
                heartbeat = conn.execute("SELECT status FROM bus_heartbeats WHERE system_name='AI-Research-System'").fetchone()[0]
            self.assertEqual(status, "Completed")
            self.assertEqual(heartbeat, "Ready")

    def test_ai_research_chat_input_records_shared_api_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            payload = research_bus_bridge.submit_chat_input(
                "同步 PFIOS 和行研系统状态",
                source_system="AI-Research-Chat",
                db_path=db_path,
            )

            self.assertEqual(payload["classification"], "sync_request")
            with closing(sqlite3.connect(db_path)) as conn, conn:
                request_type = conn.execute("SELECT request_type FROM bus_api_requests WHERE request_id=?", (payload["linked_request_id"],)).fetchone()[0]
                chat_count = conn.execute("SELECT COUNT(*) FROM bus_chat_inputs").fetchone()[0]
            self.assertEqual(request_type, "sync_all")
            self.assertEqual(chat_count, 1)

    def test_ai_research_chat_input_preserves_attachments_for_bus_processing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            payload = research_bus_bridge.submit_chat_input(
                "这是今天的持仓截图，请同步到量化系统和行研系统",
                source_system="AI-Research-Chat",
                attachments=[
                    {
                        "path": Path(tmp) / "holding.png",
                        "name": "holding.png",
                        "media_type": "image/png",
                        "source": "chat_upload",
                        "size_bytes": 2048,
                    }
                ],
                db_path=db_path,
            )

            with closing(sqlite3.connect(db_path)) as conn, conn:
                row = conn.execute(
                    "SELECT attachments_json, payload_json FROM bus_chat_inputs WHERE input_id=?",
                    (payload["input_id"],),
                ).fetchone()
                request_payload = conn.execute(
                    "SELECT payload_json FROM bus_api_requests WHERE request_id=?",
                    (payload["linked_request_id"],),
                ).fetchone()[0]

            attachments = json.loads(row[0])
            chat_payload = json.loads(row[1])
            request_payload = json.loads(request_payload)
            self.assertEqual(attachments[0]["name"], "holding.png")
            self.assertEqual(attachments[0]["extra"]["size_bytes"], 2048)
            self.assertEqual(chat_payload["attachments"][0]["media_type"], "image/png")
            self.assertEqual(request_payload["attachments"][0]["source"], "chat_upload")

    def test_ai_research_chat_input_routes_checksum_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            payload = research_bus_bridge.submit_chat_input(
                "请运行千万行独立验证 checksum 校验，每片100万行",
                source_system="AI-Research-Chat",
                db_path=db_path,
            )

            self.assertEqual(payload["classification"], "independent_validation")
            self.assertEqual(payload["request_type"], "independent_validation_checksum")
            with closing(sqlite3.connect(db_path)) as conn, conn:
                request_payload = conn.execute(
                    "SELECT payload_json FROM bus_api_requests WHERE request_id=?",
                    (payload["linked_request_id"],),
                ).fetchone()[0]
            parsed = json.loads(request_payload)
            self.assertEqual(parsed["synthetic_rows"], 10_000_000)
            self.assertEqual(parsed["rows_per_shard"], 1_000_000)

    def test_ai_research_chat_input_routes_english_hundred_million_scale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            payload = research_bus_bridge.submit_chat_input(
                "run hundred million rows independent validation, rows_per_shard 10 million",
                source_system="AI-Research-Chat",
                db_path=db_path,
            )

            self.assertEqual(payload["classification"], "independent_validation")
            self.assertEqual(payload["request_type"], "independent_validation_dry_run")
            with closing(sqlite3.connect(db_path)) as conn, conn:
                request_payload = conn.execute(
                    "SELECT payload_json FROM bus_api_requests WHERE request_id=?",
                    (payload["linked_request_id"],),
                ).fetchone()[0]
            parsed = json.loads(request_payload)
            self.assertEqual(parsed["synthetic_rows"], 100_000_000)
            self.assertEqual(parsed["rows_per_shard"], 10_000_000)


if __name__ == "__main__":
    unittest.main()
