from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from quantlab.integrations.research_bus import initialize_research_bus
from quantlab.integrations.research_bus_audit import REQUIRED_AI_AUTOMATION_FILES, REQUIRED_AI_BRIDGE_FILES, run_research_bus_interop_audit


def test_research_bus_interop_audit_passes_complete_temp_bus(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "ResearchBus.sqlite"
        ai_root = root / "AI-Research-System"
        bridge_dir = ai_root / "data" / "report_artifacts" / "research_bus_bridge"
        bridge_dir.mkdir(parents=True)
        for name in REQUIRED_AI_BRIDGE_FILES:
            (bridge_dir / name).write_text(json.dumps({"schema": "ResearchBusV1"}), encoding="utf-8")
        for relative in REQUIRED_AI_AUTOMATION_FILES:
            automation_path = ai_root / relative
            automation_path.parent.mkdir(parents=True, exist_ok=True)
            automation_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        inbox = root / "chatInbox"
        inbox.mkdir()
        monkeypatch.setattr("quantlab.integrations.research_bus_audit.CHAT_DROPBOX_DIR", inbox)
        initialize_research_bus(db_path)
        _seed_complete_bus(db_path)

        payload = run_research_bus_interop_audit(db_path, ai_research_root=ai_root, output_path=root / "audit.json")

        assert payload["status"] == "Pass"
        assert payload["summary"]["fail"] == 0
        assert payload["summary"]["warn"] == 0
        assert (root / "audit.json").exists()
        assert {item["requirement"] for item in payload["items"]} >= {
            "共享 SQLite 数据库",
            "本地母子系统注册表",
            "子系统产物索引",
            "双向 API 和消息队列",
            "行研报告解析为待验证任务",
            "QuantLab 回测结论回写行研系统",
            "独立验证系统任意入口运行",
            "独立验证两级架构与本机 worker pool",
        }


def test_research_bus_interop_audit_warns_when_runtime_records_are_missing(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "ResearchBus.sqlite"
        ai_root = root / "AI-Research-System"
        inbox = root / "chatInbox"
        inbox.mkdir()
        monkeypatch.setattr("quantlab.integrations.research_bus_audit.CHAT_DROPBOX_DIR", inbox)
        initialize_research_bus(db_path)

        payload = run_research_bus_interop_audit(db_path, ai_research_root=ai_root, output_path=None)

        assert payload["status"] == "Warn"
        warnings = {item["requirement"] for item in payload["items"] if item["status"] == "Warn"}
        assert "任意聊天框输入同步" in warnings
        assert "行研报告解析为待验证任务" in warnings
        assert "QuantLab 回测结论回写行研系统" in warnings


def test_research_bus_interop_audit_uses_immutable_readonly_fallback(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "ResearchBus.sqlite"
        ai_root = root / "AI-Research-System"
        bridge_dir = ai_root / "data" / "report_artifacts" / "research_bus_bridge"
        bridge_dir.mkdir(parents=True)
        for name in REQUIRED_AI_BRIDGE_FILES:
            (bridge_dir / name).write_text(json.dumps({"schema": "ResearchBusV1"}), encoding="utf-8")
        for relative in REQUIRED_AI_AUTOMATION_FILES:
            automation_path = ai_root / relative
            automation_path.parent.mkdir(parents=True, exist_ok=True)
            automation_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        inbox = root / "chatInbox"
        inbox.mkdir()
        monkeypatch.setattr("quantlab.integrations.research_bus_audit.CHAT_DROPBOX_DIR", inbox)
        initialize_research_bus(db_path)
        _seed_complete_bus(db_path)
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        real_connect = sqlite3.connect

        def readonly_locked_connect(database, *args, **kwargs):
            if str(database) == f"file:{db_path}?mode=ro":
                raise sqlite3.OperationalError("unable to open database file")
            return real_connect(database, *args, **kwargs)

        monkeypatch.setattr(sqlite3, "connect", readonly_locked_connect)

        payload = run_research_bus_interop_audit(db_path, ai_research_root=ai_root, output_path=None)

        assert payload["status"] == "Pass"
        assert payload["summary"]["fail"] == 0


def test_research_bus_interop_audit_fails_missing_database():
    with tempfile.TemporaryDirectory() as tmp:
        missing_db = Path(tmp) / "missing.sqlite"

        payload = run_research_bus_interop_audit(missing_db, output_path=None)

        assert payload["status"] == "Fail"
        assert payload["items"][0]["requirement"] == "共享 SQLite 数据库"


def _seed_complete_bus(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO research_reports(
                report_id, source_system, report_type, title, report_date, period, path,
                content_hash, summary, symbols_json, topics_json, created_at, updated_at
            )
            VALUES ('report_1', 'AI-Research-System', 'daily', 'report', '2026-06-05',
                    'daily', '/tmp/report.md', 'hash', 'summary', '["AAPL"]', '[]',
                    '2026-06-05T09:00:00', '2026-06-05T09:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO validation_tasks(
                task_id, source_system, source_report_id, source_report_path, source_paragraph,
                research_topic, symbol, market, signal_to_validate, sample_period, cost_assumption,
                benchmark, status, validation_report_path, created_at, updated_at
            )
            VALUES ('task_1', 'AI-Research-System', 'report_1', '/tmp/report.md',
                    '验证 RSI', 'RSI 验证', 'AAPL', 'US', 'RSI', '默认区间',
                    '默认成本', '标普500', '待验证', '', '2026-06-05T09:00:00',
                    '2026-06-05T09:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO quantlab_results(
                result_id, report_path, metadata_path, strategy_id, symbol, market,
                total_return, annualized_return, max_drawdown, sharpe, research_status,
                decision_quality_score, data_quality_status, cross_validation_status,
                created_at, updated_at, payload_json
            )
            VALUES ('result_1', '/tmp/report.docx', '/tmp/meta.json', 'demo', 'AAPL',
                    'US', 0.1, 0.05, -0.1, 1.0, 'ContinueResearch', 80, 'Pass',
                    'Pass', '2026-06-05T09:00:00', '2026-06-05T09:00:00', '{}')
            """
        )
        conn.execute(
            """
            INSERT INTO holdings_master(
                holding_id, source_system, account, symbol, name, market, asset_type,
                quantity, cost_basis, position_value, unrealized_pnl, weight, as_of,
                source_path, payload_json, updated_at
            )
            VALUES ('holding_1', 'UnitTest', 'Default', 'AAPL', 'Apple', 'US', 'equity',
                    1, 100, 110, 10, 1, '2026-06-05', '', '{}', '2026-06-05T09:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO holding_symbol_mappings(
                mapping_id, source_system, holding_name, holding_market, original_symbol,
                proxy_symbol, proxy_name, proxy_market, status, confidence, reason,
                source, payload_json, updated_at
            )
            VALUES ('mapping_1', 'QuantLab', 'Apple', 'US', 'AAPL', 'AAPL', 'Apple',
                    'US', 'ConfirmedSymbol', 'ConfirmedSymbol', '持仓记录已包含行情代码',
                    'HoldingBook', '{}', '2026-06-05T09:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO portfolio_transactions(
                transaction_id, source_system, account, trade_date, order_time, timezone,
                symbol, name, market, asset_type, side, order_type, order_amount,
                confirmed_amount, confirmed_units, confirmed_nav, fee, status,
                quality_status, source_path, evidence_frame, notes, payload_json, updated_at
            )
            VALUES ('txn_1', 'UnitTest', 'Default', '2026-06-05', '14:30:00',
                    'Asia/Shanghai', 'AAPL', 'Apple', 'US', 'equity', '买入',
                    'manual', 100, 100, 1, 100, 0, 'Confirmed', 'Confirmed',
                    '', '', '', '{}', '2026-06-05T09:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO consumer_behavior_state(
                state_id, source_system, db_path, run_count, transaction_count, ledger_count,
                latest_run_id, latest_generated_at, total_amount, manual_review_count,
                summary_json, updated_at
            )
            VALUES ('consumer_1', 'ConsumptionAnalysisSystem', '/tmp/consumer.sqlite',
                    1, 1, 1, 'run_1', '2026-06-05T09:00:00', 100, 0, '{}',
                    '2026-06-05T09:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO independent_validation_runs(
                run_id, source_system, status, mode, manifest_path, total_rows, shard_count,
                started_at, completed_at, output_path, payload_json, updated_at
            )
            VALUES ('run_1', 'IndependentValidation', 'Completed', 'checksum',
                    '/tmp/manifest.json', 1000000, 10, '2026-06-05T09:00:00',
                    '2026-06-05T09:00:01', '/tmp/run.json',
                    '{"execution_tier":"local_worker_pool","worker_count":4}',
                    '2026-06-05T09:00:01')
            """
        )
        for system_name, role in [
            ("QuantLab", "MotherSystem"),
            ("AI-Research-System", "ChildSystem"),
            ("finance_ledger", "WorkspaceChildSystem"),
            ("industry_research", "WorkspaceChildSystem"),
            ("policy_intelligence", "WorkspaceChildSystem"),
            ("FIFA-Research-System", "ChildSystem"),
            ("GovernmentPolicySystem", "ChildSystem"),
            ("IndependentValidation", "WorkerPoolChildSystem"),
        ]:
            conn.execute(
                """
                INSERT INTO system_registry(
                    system_name, role, root_path, standalone_command_json, health_command_json,
                    sync_command_json, capabilities_json, outputs_json, status, last_seen_at,
                    payload_json, updated_at
                )
                VALUES (?, ?, '/tmp', '[]', '[]', '[]', '[]', '[]', 'Ready',
                        '2026-06-05T09:00:00', '{}', '2026-06-05T09:00:00')
                """,
                (system_name, role),
            )
        for system_name in [
            "FIFA-Research-System",
            "GovernmentPolicySystem",
            "finance_ledger",
            "industry_research",
            "policy_intelligence",
        ]:
            conn.execute(
                """
                INSERT INTO system_artifacts(
                    artifact_id, system_name, artifact_type, title, path, content_hash,
                    size_bytes, modified_at, payload_json, created_at, updated_at
                )
                VALUES (?, ?, 'json_state', ?, ?, 'hash', 10, '2026-06-05T09:00:00',
                        '{}', '2026-06-05T09:00:00', '2026-06-05T09:00:00')
                """,
                (f"artifact_{system_name}", system_name, f"{system_name}.json", f"/tmp/{system_name}.json"),
            )
        conn.execute(
            """
            INSERT INTO bus_api_requests(
                request_id, source_system, target_system, request_type, status, priority,
                payload_json, response_json, error_message, created_at, updated_at, processed_at
            )
            VALUES ('request_1', 'AI-Research-Chat', 'ResearchBus',
                    'independent_validation_checksum', 'Completed', 5, '{}', '{}', '',
                    '2026-06-05T09:00:00', '2026-06-05T09:00:01', '2026-06-05T09:00:01')
            """
        )
        conn.execute(
            """
            INSERT INTO bus_chat_inputs(
                input_id, source_system, author, channel, content_text, attachments_json,
                classification, linked_request_id, status, payload_json, created_at, processed_at
            )
            VALUES ('chat_1', 'AI-Research-Chat', 'user', 'chat',
                    '请运行百万行独立验证', '[]', 'independent_validation', 'request_1',
                    'Completed', '{}', '2026-06-05T09:00:00', '2026-06-05T09:00:01')
            """
        )
        conn.execute(
            """
            INSERT INTO bus_heartbeats(system_name, status, capabilities_json, payload_json, last_seen_at)
            VALUES ('ResearchBus', 'Ready', '[]', '{}', '2026-06-05T09:00:00'),
                   ('AI-Research-System', 'Ready', '[]', '{}', '2026-06-05T09:00:00')
            """
        )
        conn.commit()
