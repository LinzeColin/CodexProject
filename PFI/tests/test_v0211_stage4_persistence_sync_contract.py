from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pfi_v02.stage_v0211_ui_recovery as recovery
from pfi_v02.stage_v021_runtime_api import (
    build_v021_holdings_report,
    build_v021_holdings_sync_read_model,
    load_v021_holdings_payload,
    save_v021_holdings_payload,
)


class V0211Stage4PersistenceSyncContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.web_source = "\n".join((self.html, self.js))

    def test_contract_locks_stage4_scope_and_stop_conditions(self) -> None:
        contract = recovery.build_v0211_stage4_contract()

        self.assertEqual(contract["schema"], "PFIV0211ProductUIRecoveryStage4ContractV1")
        self.assertEqual(contract["stage"], "S4 持久化与同步")
        self.assertEqual(contract["task_id"], "V0211-S4-T01")
        self.assertEqual(contract["current_stage_only"], True)
        self.assertIn("持仓修改写入本地 SQLite", "\n".join(contract["delivery_focus"]))
        self.assertIn("不跳过 SQLite 查询验收", "\n".join(contract["forbidden_work"]))
        self.assertEqual(
            tuple(contract["sqlite_contract"]["tables"]),
            ("v021_holding_snapshots", "v021_position_adjustments"),
        )
        self.assertEqual(contract["sqlite_contract"]["write_endpoint"], "/api/holdings")
        self.assertEqual(contract["sqlite_contract"]["read_model_endpoint"], "/api/read-model")
        self.assertIn("页面编辑 -> 保存 -> SQLite 查询 -> 重启服务 -> 页面读取通过", "\n".join(contract["acceptance_gate"]))

    def test_backend_save_query_reopen_and_sync_read_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "pfi-stage4.sqlite"
            row = {
                "snapshotId": "owner-stage4-manual-input",
                "instrumentId": "PFI_STAGE4",
                "displayName": "人工输入持仓",
                "quantity": 3,
                "averageCost": 10,
                "marketPrice": 11,
                "currency": "CNY",
                "account": "主账户",
                "updatedAt": "2026-06-29",
                "note": "Stage 4 临时持久化验证",
            }

            saved = save_v021_holdings_payload({"rows": [row]}, db_path=db_path)

            self.assertEqual(saved["summary"]["schema"], "PFIV021HoldingsPersistenceV1")
            self.assertEqual(saved["summary"]["snapshot_count"], 1)
            self.assertEqual(saved["summary"]["adjustment_count"], 1)
            with sqlite3.connect(db_path) as conn:
                snapshot = conn.execute(
                    "SELECT instrument_id, quantity, average_cost, market_price, portfolio_id, as_of, metadata_json "
                    "FROM v021_holding_snapshots WHERE snapshot_id = ?",
                    ("owner-stage4-manual-input",),
                ).fetchone()
                adjustment_count = conn.execute("SELECT count(*) FROM v021_position_adjustments").fetchone()[0]
            self.assertEqual(snapshot[:6], ("PFI_STAGE4", 3.0, 10.0, 11.0, "主账户", "2026-06-29"))
            self.assertIn("Stage 4 临时持久化验证", snapshot[6])
            self.assertEqual(adjustment_count, 1)

            reopened = load_v021_holdings_payload(db_path=db_path)
            self.assertEqual(reopened["rows"][0]["instrumentId"], "PFI_STAGE4")
            self.assertEqual(reopened["rows"][0]["account"], "主账户")
            self.assertEqual(reopened["rows"][0]["note"], "Stage 4 临时持久化验证")

            sync_model = build_v021_holdings_sync_read_model(db_path=db_path)
            report = build_v021_holdings_report(db_path=db_path)
            self.assertEqual(sync_model["home"]["investment_market_value_cny"], 33.0)
            self.assertEqual(sync_model["investment"]["market_value_cny"], 33.0)
            self.assertEqual(sync_model["report"]["market_value_cny"], 33.0)
            self.assertEqual(report["report"]["holding_count"], 1)
            self.assertTrue(sync_model["consistency"]["home_investment_report_market_value_same"])

    def test_frontend_contains_required_fields_and_no_browser_production_save(self) -> None:
        for visible_field in ("标的", "名称", "数量", "成本", "价格", "币种", "账户", "更新时间", "备注"):
            self.assertIn(visible_field, self.html)

        for required in (
            'data-holding-field="portfolioId"',
            'data-holding-field="asOf"',
            'data-holding-field="note"',
            'runtimeApiJson("/api/holdings"',
            'runtimeApiJson("/api/read-model"',
            "runtimeStage4SyncState",
            "WORKSPACES.insights.cards",
            "保存后刷新仍保留",
            "已写入 SQLite 数据库",
        ):
            self.assertIn(required, self.web_source)

        save_start = self.js.index("async function saveHoldingsEdits()")
        save_end = self.js.index("async function saveHoldingsToBackend", save_start)
        save_source = self.js[save_start:save_end]
        self.assertNotIn("localStorage.setItem", save_source)
        self.assertNotIn("sessionStorage", save_source)
        self.assertNotIn("indexedDB", save_source)
        self.assertIn("saveHoldingsToBackend(rows)", save_source)
        self.assertIn("await refreshRuntimeTrends({ rerender: true })", save_source)

    def test_empty_official_store_stays_real_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "empty.sqlite"

            payload = load_v021_holdings_payload(db_path=db_path)
            sync_model = build_v021_holdings_sync_read_model(db_path=db_path)
            report = build_v021_holdings_report(db_path=db_path)

            self.assertEqual(payload["summary"]["snapshot_count"], 0)
            self.assertEqual(sync_model["home"]["investment_market_value_cny"], 0)
            self.assertEqual(sync_model["report"]["holding_count"], 0)
            self.assertEqual(report["report"]["empty_state"], "暂无真实持仓，报告不生成模拟收益。")


if __name__ == "__main__":
    unittest.main()
