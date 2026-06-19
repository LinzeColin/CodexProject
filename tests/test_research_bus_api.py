from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from quantlab.integrations.research_bus_api import (
    bus_api_requests_frame,
    bus_chat_inputs_frame,
    bus_heartbeats_frame,
    classify_chat_input,
    confirm_holding_update_candidate,
    heartbeat_system,
    pending_bus_requests_frame,
    process_chat_dropbox,
    process_pending_bus_requests,
    research_bus_health_summary,
    submit_bus_request,
    submit_chat_input,
    submit_webhook_payload,
    workflow_inputs_frame,
)
from quantlab.integrations.research_bus import bus_validation_task_frame, holding_update_candidates_frame


AI_RESEARCH_ROOT = Path(os.environ.get("EVA_AI_RESEARCH_ROOT", "")).expanduser() if os.environ.get("EVA_AI_RESEARCH_ROOT") else Path.home() / "Documents" / "EVA_OS_Workspace" / "systems" / "industry_research"


def _load_ai_research_bridge():
    bridge_path = AI_RESEARCH_ROOT / "src" / "integrations" / "research_bus_bridge.py"
    if not bridge_path.exists():
        raise unittest.SkipTest(f"AI-Research-System bridge not found: {bridge_path}")
    if str(AI_RESEARCH_ROOT) not in sys.path:
        sys.path.insert(0, str(AI_RESEARCH_ROOT))
    spec = importlib.util.spec_from_file_location("ai_research_bus_bridge_for_quantlab_test", bridge_path)
    if spec is None or spec.loader is None:
        raise unittest.SkipTest(f"Cannot load AI-Research-System bridge: {bridge_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResearchBusApiTest(unittest.TestCase):
    def test_chat_input_creates_validation_task_and_api_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"

            result = submit_chat_input("请验证 600000 的 RSI 均线策略是否有效", source_system="AI-Research-Chat", db_path=db_path)
            chats = bus_chat_inputs_frame(db_path)
            requests = pending_bus_requests_frame(db_path=db_path, target_system="ResearchBus")
            tasks = bus_validation_task_frame(db_path)

            self.assertEqual(result["classification"], "validation_task")
            self.assertEqual(result["created_validation_tasks"], 1)
            self.assertEqual(len(chats), 1)
            self.assertEqual(len(requests), 1)
            self.assertIn("600000.SH", set(tasks["symbol"]))

    def test_workflow_inputs_frame_combines_chat_and_direct_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            chat = submit_chat_input("请验证 600000 的 RSI 策略", source_system="AI-Research-Chat", author="user", db_path=db_path)
            request = submit_bus_request("sync_holdings", {"source": "unit_test"}, source_system="UnitTest", db_path=db_path)

            frame = workflow_inputs_frame(db_path)

            self.assertEqual(set(frame["input_type"]), {"chat", "api_request"})
            by_id = {row["workflow_input_id"]: row for row in frame.to_dict("records")}
            self.assertEqual(by_id[chat["input_id"]]["classification"], "validation_task")
            self.assertEqual(by_id[chat["input_id"]]["linked_request_id"], chat["linked_request_id"])
            self.assertEqual(by_id[request.request_id]["classification"], "sync_holdings")
            self.assertEqual(by_id[request.request_id]["channel"], "api")

    def test_chat_status_follows_linked_request_without_overwriting_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            validation_chat = submit_chat_input("请验证 600000 的 RSI 策略", source_system="AI-Research-Chat", db_path=db_path)
            holding_chat = submit_chat_input("这是今天的支付宝持仓截图，含 600000.SH", source_system="AI-Research-Chat", db_path=db_path)

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            chats = bus_chat_inputs_frame(db_path)
            by_id = {row["input_id"]: row for row in chats.to_dict("records")}

            self.assertEqual(result["failed"], 0)
            self.assertEqual(by_id[validation_chat["input_id"]]["status"], "Completed")
            self.assertEqual(by_id[holding_chat["input_id"]]["status"], "PendingReview")

    def test_malformed_bus_request_payload_is_rejected_without_queueing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"

            with self.assertRaises(ValueError):
                submit_bus_request("sync_holdings", ["not", "an", "object"], source_system="UnitTest", db_path=db_path)  # type: ignore[arg-type]

            requests = bus_api_requests_frame(db_path)
            self.assertTrue(requests.empty)

    def test_pull_holding_symbol_mappings_request_returns_shared_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_bus_request(
                "sync_holding_symbol_mappings",
                {},
                source_system="UnitTest",
                target_system="ResearchBus",
                db_path=db_path,
            )
            sync_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            pull = submit_bus_request(
                "pull_holding_symbol_mappings",
                {"limit": 5},
                source_system="UnitTest",
                target_system="ResearchBus",
                db_path=db_path,
            )
            pull_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                response = json.loads(
                    conn.execute(
                        "SELECT response_json FROM bus_api_requests WHERE request_id=?",
                        (pull.request_id,),
                    ).fetchone()[0]
                )

            self.assertEqual(sync_result["processed"], 1)
            self.assertEqual(pull_result["processed"], 1)
            self.assertEqual(response["status"], "Pulled")
            self.assertIn("holding_symbol_mappings", response)

    def test_holding_update_chat_input_creates_review_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            chat = submit_chat_input(
                "这是今天的支付宝持仓截图，含 600000.SH，请同步到量化系统和行研系统。",
                source_system="AI-Research-Chat",
                attachments=[{"path": Path(tmp) / "holding.png", "media_type": "image/png"}],
                db_path=db_path,
            )

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidates = holding_update_candidates_frame(db_path)
            chats = bus_chat_inputs_frame(db_path)
            with sqlite3.connect(db_path) as conn:
                formal_holding_count = conn.execute("SELECT COUNT(*) FROM holdings_master").fetchone()[0]

            self.assertEqual(chat["classification"], "holding_update")
            self.assertEqual(result["processed"], 1)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates.iloc[0]["status"], "PendingReview")
            self.assertEqual(candidates.iloc[0]["candidate_type"], "holding_attachment")
            self.assertIn("600000.SH", candidates.iloc[0]["extracted_symbols_json"])
            self.assertEqual(chats.iloc[0]["status"], "PendingReview")
            self.assertEqual(formal_holding_count, 0)

    def test_confirm_structured_holding_candidate_applies_to_formal_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            holding_import_path = root / "confirmed_holding_candidates.csv"
            transaction_import_path = root / "confirmed_portfolio_transactions.csv"
            book_path = root / "HoldingsBook.json"
            submit_bus_request(
                "holding_update_candidate",
                {
                    "content_text": "结构化持仓候选",
                    "holdings": [
                        {
                            "symbol": "600000.SH",
                            "name": "浦发银行",
                            "market": "CN",
                            "position_value": 12000,
                            "quantity": 1000,
                            "updated_at": "2026-06-05",
                        }
                    ],
                    "portfolio_transactions": [
                        {
                            "trade_date": "2026-06-05",
                            "order_time": "14:30:00",
                            "symbol": "600000.SH",
                            "name": "浦发银行",
                            "market": "CN",
                            "side": "买入",
                            "order_amount": 12000,
                            "status": "交易成功",
                        }
                    ],
                },
                source_system="AI-Research-Chat",
                target_system="ResearchBus",
                db_path=db_path,
            )
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidate_id = process_result["results"][0]["response"]["candidate_id"]

            confirm_result = confirm_holding_update_candidate(
                candidate_id,
                db_path=db_path,
                holding_import_path=holding_import_path,
                transaction_import_path=transaction_import_path,
                holdings_book_path=book_path,
            )
            candidates = holding_update_candidates_frame(db_path)
            with sqlite3.connect(db_path) as conn:
                holding = conn.execute("SELECT symbol, name, position_value FROM holdings_master").fetchone()
                transaction = conn.execute("SELECT symbol, name, order_amount, quality_status FROM portfolio_transactions").fetchone()

            self.assertEqual(confirm_result["status"], "Applied")
            self.assertEqual(confirm_result["confirmed_holding_count"], 1)
            self.assertEqual(confirm_result["confirmed_transaction_count"], 1)
            self.assertTrue(book_path.exists())
            self.assertTrue(holding_import_path.exists())
            self.assertTrue(transaction_import_path.exists())
            self.assertEqual(candidates.iloc[0]["status"], "Applied")
            self.assertEqual(holding, ("600000.SH", "浦发银行", 12000.0))
            self.assertEqual(transaction, ("600000.SH", "浦发银行", 12000.0, "Confirmed"))

    def test_confirm_unstructured_holding_candidate_does_not_modify_formal_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            submit_chat_input(
                "这是今天的支付宝持仓截图",
                source_system="AI-Research-Chat",
                attachments=[{"path": root / "holding.png", "media_type": "image/png"}],
                db_path=db_path,
            )
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidate_id = process_result["results"][0]["response"]["candidate_id"]

            confirm_result = confirm_holding_update_candidate(candidate_id, db_path=db_path, holdings_book_path=root / "HoldingsBook.json")
            candidates = holding_update_candidates_frame(db_path)
            with sqlite3.connect(db_path) as conn:
                formal_holding_count = conn.execute("SELECT COUNT(*) FROM holdings_master").fetchone()[0]

            self.assertEqual(confirm_result["status"], "NeedsStructuredData")
            self.assertEqual(candidates.iloc[0]["status"], "NeedsStructuredData")
            self.assertEqual(formal_holding_count, 0)

    def test_holding_csv_attachment_auto_parses_and_confirms_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            csv_path = root / "holdings.csv"
            csv_path.write_text(
                "symbol,name,market,position_value,quantity,updated_at\n"
                "600000.SH,浦发银行,CN,12000,1000,2026-06-05\n",
                encoding="utf-8",
            )
            chat = submit_chat_input(
                "这是今天的持仓 CSV，请同步到量化系统和行研系统。",
                source_system="AI-Research-Chat",
                attachments=[{"path": csv_path, "media_type": "text/csv"}],
                db_path=db_path,
            )
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidate_id = process_result["results"][0]["response"]["candidate_id"]
            with sqlite3.connect(db_path) as conn:
                payload = json.loads(conn.execute("SELECT payload_json FROM holding_update_candidates WHERE candidate_id=?", (candidate_id,)).fetchone()[0])

            confirm_result = confirm_holding_update_candidate(candidate_id, db_path=db_path, holdings_book_path=root / "HoldingsBook.json")

            self.assertEqual(chat["classification"], "holding_update")
            self.assertEqual(payload["attachment_parser_reports"][0]["status"], "Parsed")
            self.assertEqual(payload["holdings"][0]["symbol"], "600000.SH")
            self.assertEqual(confirm_result["status"], "Applied")
            self.assertEqual(confirm_result["confirmed_holding_count"], 1)

    def test_dropbox_json_relative_attachment_auto_parses_transaction_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            inbox = root / "inbox"
            inbox.mkdir()
            attachment_dir = inbox / "attachments"
            attachment_dir.mkdir()
            attachment_path = attachment_dir / "trade.json"
            attachment_path.write_text(
                json.dumps(
                    {
                        "portfolio_transactions": [
                            {
                                "trade_date": "2026-06-05",
                                "order_time": "14:30:00",
                                "symbol": "600000.SH",
                                "name": "浦发银行",
                                "market": "CN",
                                "side": "买入",
                                "order_amount": 12000,
                                "status": "交易成功",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (inbox / "request.json").write_text(
                json.dumps(
                    {
                        "text": "这是今天的持仓交易文件，请同步到量化系统和行研系统。",
                        "source_system": "AI-Research-Chat",
                        "attachments": [{"path": "attachments/trade.json", "media_type": "application/json"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            dropbox_result = process_chat_dropbox(inbox, db_path=db_path, min_age_seconds=0)
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidate_id = process_result["results"][0]["response"]["candidate_id"]
            with sqlite3.connect(db_path) as conn:
                payload = json.loads(conn.execute("SELECT payload_json FROM holding_update_candidates WHERE candidate_id=?", (candidate_id,)).fetchone()[0])

            confirm_result = confirm_holding_update_candidate(
                candidate_id,
                db_path=db_path,
                transaction_import_path=root / "confirmed_portfolio_transactions.csv",
            )

            self.assertEqual(dropbox_result["processed_count"], 1)
            self.assertEqual(payload["attachment_parser_reports"][0]["status"], "Parsed")
            self.assertEqual(payload["portfolio_transactions"][0]["symbol"], "600000.SH")
            self.assertEqual(confirm_result["status"], "Applied")
            self.assertEqual(confirm_result["confirmed_transaction_count"], 1)

    def test_image_attachment_without_ocr_runtime_stays_review_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            image_path = root / "holding.png"
            image_path.write_bytes(b"not a real image")
            with patch(
                "quantlab.integrations.research_bus_api._image_ocr_runtime_status",
                return_value={"available": False, "pillow_available": True, "pytesseract_available": False, "tesseract_path": ""},
            ):
                submit_chat_input(
                    "这是今天的支付宝持仓截图，含 600000.SH",
                    source_system="AI-Research-Chat",
                    attachments=[{"path": image_path, "media_type": "image/png"}],
                    db_path=db_path,
                )
                process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidate_id = process_result["results"][0]["response"]["candidate_id"]
            with sqlite3.connect(db_path) as conn:
                payload = json.loads(conn.execute("SELECT payload_json FROM holding_update_candidates WHERE candidate_id=?", (candidate_id,)).fetchone()[0])

            confirm_result = confirm_holding_update_candidate(candidate_id, db_path=db_path, holdings_book_path=root / "HoldingsBook.json")

            self.assertEqual(payload["attachment_parser_reports"][0]["status"], "NeedsRuntime")
            self.assertEqual(payload["attachment_parser_reports"][0]["parser"], "image_ocr")
            self.assertEqual(confirm_result["status"], "NeedsStructuredData")

    def test_image_ocr_json_text_auto_parses_and_confirms_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            image_path = root / "holding.png"
            image_path.write_bytes(b"fake image bytes; OCR is mocked")
            ocr_json = json.dumps(
                {
                    "holdings": [
                        {
                            "symbol": "600000.SH",
                            "name": "浦发银行",
                            "market": "CN",
                            "position_value": 12000,
                            "quantity": 1000,
                            "updated_at": "2026-06-05",
                        }
                    ]
                },
                ensure_ascii=False,
            )
            with patch(
                "quantlab.integrations.research_bus_api._image_ocr_runtime_status",
                return_value={"available": True, "pillow_available": True, "pytesseract_available": True, "tesseract_path": "/usr/bin/tesseract"},
            ), patch("quantlab.integrations.research_bus_api._ocr_image_text", return_value=ocr_json):
                submit_chat_input(
                    "这是今天的支付宝持仓截图",
                    source_system="AI-Research-Chat",
                    attachments=[{"path": image_path, "media_type": "image/png"}],
                    db_path=db_path,
                )
                process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            candidate_id = process_result["results"][0]["response"]["candidate_id"]
            with sqlite3.connect(db_path) as conn:
                payload = json.loads(conn.execute("SELECT payload_json FROM holding_update_candidates WHERE candidate_id=?", (candidate_id,)).fetchone()[0])

            confirm_result = confirm_holding_update_candidate(candidate_id, db_path=db_path, holdings_book_path=root / "HoldingsBook.json")

            self.assertEqual(payload["attachment_parser_reports"][0]["status"], "Parsed")
            self.assertEqual(payload["attachment_parser_reports"][0]["parser"], "image_ocr")
            self.assertEqual(payload["holdings"][0]["symbol"], "600000.SH")
            self.assertEqual(confirm_result["status"], "Applied")
            self.assertEqual(confirm_result["confirmed_holding_count"], 1)

    def test_process_independent_validation_request_records_shards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_bus_request(
                "independent_validation_dry_run",
                {"synthetic_rows": 1_000_000_000, "rows_per_shard": 250_000_000},
                source_system="IndependentValidationChat",
                target_system="ResearchBus",
                db_path=db_path,
            )

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            requests = bus_api_requests_frame(db_path)
            with sqlite3.connect(db_path) as conn:
                shard_count = conn.execute("SELECT COUNT(*) FROM independent_validation_shards").fetchone()[0]

            self.assertEqual(result["processed"], 1)
            self.assertEqual(int(shard_count), 4)
            self.assertEqual(requests.iloc[0]["status"], "Completed")

    def test_chat_input_can_trigger_billion_row_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_chat_input("请运行十亿行独立验证，每片1亿行", source_system="IndependentValidationChat", db_path=db_path)

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT total_rows, shard_count FROM independent_validation_runs").fetchone()

            self.assertEqual(result["processed"], 1)
            self.assertEqual(run[0], 1_000_000_000)
            self.assertEqual(run[1], 10)

    def test_chat_input_can_trigger_checksum_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_chat_input("请运行十亿行独立验证 checksum 校验，每片1亿行", source_system="IndependentValidationChat", db_path=db_path)

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT status, mode, total_rows, shard_count FROM independent_validation_runs").fetchone()
                shard_statuses = [row[0] for row in conn.execute("SELECT status FROM independent_validation_shards").fetchall()]

            self.assertEqual(result["processed"], 1)
            self.assertEqual(run[0], "Completed")
            self.assertEqual(run[1], "checksum")
            self.assertEqual(run[2], 1_000_000_000)
            self.assertEqual(run[3], 10)
            self.assertTrue(all(status == "Completed" for status in shard_statuses))

    def test_chat_input_can_trigger_million_row_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_chat_input("请运行百万行独立验证，每片10万行", source_system="IndependentValidationChat", db_path=db_path)

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT total_rows, shard_count FROM independent_validation_runs").fetchone()

            self.assertEqual(result["processed"], 1)
            self.assertEqual(run[0], 1_000_000)
            self.assertEqual(run[1], 10)

    def test_chat_input_can_trigger_ten_million_checksum_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_chat_input("请运行千万行独立验证 checksum 校验，每片100万行", source_system="IndependentValidationChat", db_path=db_path)

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT status, mode, total_rows, shard_count FROM independent_validation_runs").fetchone()

            self.assertEqual(result["processed"], 1)
            self.assertEqual(run[0], "Completed")
            self.assertEqual(run[1], "checksum")
            self.assertEqual(run[2], 10_000_000)
            self.assertEqual(run[3], 10)

    def test_ai_research_chat_input_can_round_trip_independent_validation_results(self) -> None:
        ai_bridge = _load_ai_research_bridge()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            bridge_dir = root / "ai_bridge"
            ai_bridge.BRIDGE_DIR = bridge_dir

            payload = ai_bridge.submit_chat_input(
                "请运行千万行独立验证 checksum 校验，每片100万行",
                source_system="AI-Research-Chat",
                db_path=db_path,
            )
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            sync_result = ai_bridge.sync_research_bus(db_path, report_limit=0, result_limit=10)

            with sqlite3.connect(db_path) as conn:
                request_status = conn.execute(
                    "SELECT status FROM bus_api_requests WHERE request_id=?",
                    (payload["linked_request_id"],),
                ).fetchone()[0]
                run = conn.execute(
                    "SELECT status, mode, total_rows, shard_count FROM independent_validation_runs"
                ).fetchone()

            runs_payload = json.loads(Path(sync_result["independent_validation_runs_path"]).read_text(encoding="utf-8"))
            pulled_run = runs_payload["independent_validation_runs"][0]
            self.assertEqual(payload["classification"], "independent_validation")
            self.assertEqual(process_result["processed"], 1)
            self.assertEqual(request_status, "Completed")
            self.assertEqual(run, ("Completed", "checksum", 10_000_000, 10))
            self.assertEqual(sync_result["independent_validation_run_count"], 1)
            self.assertEqual(pulled_run["mode"], "checksum")
            self.assertEqual(pulled_run["total_rows"], 10_000_000)

    def test_ai_research_holding_attachment_can_round_trip_to_candidate_queue(self) -> None:
        ai_bridge = _load_ai_research_bridge()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            ai_bridge.BRIDGE_DIR = root / "ai_bridge"

            payload = ai_bridge.submit_chat_input(
                "这是今天的支付宝持仓截图，含 600000.SH，请同步到量化系统和行研系统。",
                source_system="AI-Research-Chat",
                attachments=[{"path": root / "holding.png", "media_type": "image/png", "source": "unit_test"}],
                db_path=db_path,
            )
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)
            sync_result = ai_bridge.sync_research_bus(db_path, report_limit=0, result_limit=10)

            candidates_payload = json.loads(Path(sync_result["holding_update_candidates_path"]).read_text(encoding="utf-8"))
            candidate = candidates_payload["holding_update_candidates"][0]
            self.assertEqual(payload["classification"], "holding_update")
            self.assertEqual(process_result["processed"], 1)
            self.assertEqual(sync_result["holding_update_candidate_count"], 1)
            self.assertEqual(candidate["status"], "PendingReview")
            self.assertEqual(candidate["candidate_type"], "holding_attachment")
            self.assertIn("600000.SH", candidate["extracted_symbols_json"])

    def test_webhook_payload_can_trigger_hundred_million_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            submit_webhook_payload(
                {"text": "run hundred million rows independent validation, rows_per_shard 10 million"},
                source_system="Shortcut",
                db_path=db_path,
            )

            result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT total_rows, shard_count FROM independent_validation_runs").fetchone()

            self.assertEqual(result["processed"], 1)
            self.assertEqual(run[0], 100_000_000)
            self.assertEqual(run[1], 10)

    def test_chat_dropbox_can_trigger_billion_scale_independent_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            inbox = root / "inbox"
            inbox.mkdir()
            (inbox / "big_data.md").write_text("请运行亿万级独立验证，每片1亿行", encoding="utf-8")

            dropbox_result = process_chat_dropbox(inbox, db_path=db_path, min_age_seconds=0)
            process_result = process_pending_bus_requests(system_name="ResearchBus", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                run = conn.execute("SELECT total_rows, shard_count FROM independent_validation_runs").fetchone()

            self.assertEqual(dropbox_result["processed_count"], 1)
            self.assertEqual(process_result["processed"], 1)
            self.assertEqual(run[0], 1_000_000_000)
            self.assertEqual(run[1], 10)

    def test_heartbeat_and_classification_are_queryable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            heartbeat_system("AI-Research-System", status="Ready", capabilities=["publish_reports"], db_path=db_path)
            frame = bus_heartbeats_frame(db_path)

            self.assertEqual(frame.iloc[0]["system_name"], "AI-Research-System")
            self.assertEqual(classify_chat_input("同步所有系统"), "sync_request")
            self.assertEqual(classify_chat_input("更新持仓 AAPL 市值"), "holding_update")
            self.assertEqual(classify_chat_input("优化报告中心显示逻辑"), "system_update")

    def test_chat_dropbox_processes_text_file_and_moves_to_processed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            inbox = root / "inbox"
            inbox.mkdir()
            (inbox / "request.txt").write_text("请验证 AAPL 的 RSI 策略", encoding="utf-8")

            result = process_chat_dropbox(inbox, db_path=db_path, min_age_seconds=0)
            tasks = bus_validation_task_frame(db_path)

            self.assertEqual(result["processed_count"], 1)
            self.assertEqual(result["failed_count"], 0)
            self.assertFalse((inbox / "request.txt").exists())
            self.assertTrue((inbox / "processed" / "request.txt").exists())
            self.assertIn("AAPL", set(tasks["symbol"]))

    def test_chat_dropbox_retry_with_same_file_name_keeps_previous_processed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            inbox = root / "inbox"
            inbox.mkdir()
            request_path = inbox / "request.txt"
            request_path.write_text("请验证 AAPL 的 RSI 策略", encoding="utf-8")
            first_result = process_chat_dropbox(inbox, db_path=db_path, min_age_seconds=0)
            request_path.write_text("请验证 MSFT 的 MACD 策略", encoding="utf-8")

            second_result = process_chat_dropbox(inbox, db_path=db_path, min_age_seconds=0)
            processed_files = sorted(path.name for path in (inbox / "processed").iterdir() if path.is_file())
            tasks = bus_validation_task_frame(db_path)

            self.assertEqual(first_result["processed_count"], 1)
            self.assertEqual(second_result["processed_count"], 1)
            self.assertEqual(len(processed_files), 2)
            self.assertIn("request.txt", processed_files)
            self.assertIn("AAPL", set(tasks["symbol"]))
            self.assertIn("MSFT", set(tasks["symbol"]))

    def test_chat_dropbox_processes_json_system_update_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            inbox = root / "inbox"
            inbox.mkdir()
            (inbox / "update.json").write_text(
                json.dumps({"text": "优化策略库编辑流程", "source_system": "AI-Research-Chat", "author": "user"}, ensure_ascii=False),
                encoding="utf-8",
            )

            result = process_chat_dropbox(inbox, db_path=db_path, min_age_seconds=0)
            requests = pending_bus_requests_frame(db_path=db_path, target_system="ResearchBus")

            self.assertEqual(result["processed_count"], 1)
            self.assertEqual(requests.iloc[0]["request_type"], "system_update_request")
            self.assertEqual(bus_chat_inputs_frame(db_path).iloc[0]["classification"], "system_update")

    def test_webhook_payload_can_submit_chat_and_raw_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"

            chat_result = submit_webhook_payload({"text": "请验证 MSFT 的 MACD 信号", "source_system": "Shortcut"}, db_path=db_path)
            request_result = submit_webhook_payload(
                {"request_type": "sync_holdings", "payload": {"source": "webhook"}, "source_system": "Shortcut"},
                db_path=db_path,
            )
            pending = pending_bus_requests_frame(db_path=db_path, target_system="ResearchBus")

            self.assertEqual(chat_result["kind"], "chat")
            self.assertEqual(request_result["kind"], "request")
            self.assertIn("validation_task_from_chat", set(pending["request_type"]))
            self.assertIn("sync_holdings", set(pending["request_type"]))

    def test_research_bus_health_summary_reports_pending_and_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ResearchBus.sqlite"
            inbox = root / "inbox"
            inbox.mkdir()
            (inbox / "note.txt").write_text("同步所有系统", encoding="utf-8")
            submit_bus_request("sync_all", {}, db_path=db_path)
            heartbeat_system("AI-Research-System", status="Ready", db_path=db_path)

            summary = research_bus_health_summary(db_path=db_path, inbox_dir=inbox, heartbeat_max_age_seconds=180)

            self.assertEqual(summary["status"], "Ready")
            self.assertEqual(summary["pending_request_count"], 1)
            self.assertEqual(summary["chat_inbox_pending_files"], 1)
            self.assertEqual(summary["heartbeat_stale_count"], 0)


if __name__ == "__main__":
    unittest.main()
