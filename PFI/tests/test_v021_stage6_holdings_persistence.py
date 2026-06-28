from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from pfi_v02.stage_v021_frontend_contract import (
    STAGE6_TASK_IDS,
    build_v021_stage6_contract,
)
from pfi_v02.stage_v021_holdings_persistence import (
    V021HoldingsPersistenceService,
    V021HoldingSnapshot,
    build_v021_demo_holding_snapshots,
    seed_v021_demo_holdings,
)


class V021Stage6HoldingsPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.css = (self.root / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.web_source = "\n".join((self.html, self.js, self.css))

    def test_stage6_contract_covers_sqlite_service_and_frontend_route(self) -> None:
        contract = build_v021_stage6_contract()

        self.assertEqual(contract["schema"], "PFIV021FrontendOptimizationStage6ContractV1")
        self.assertEqual(tuple(contract["task_ids"]), STAGE6_TASK_IDS)
        self.assertEqual(contract["frontend_contract"]["route"], "/investment?tab=holdings")
        self.assertEqual(contract["frontend_contract"]["draft_storage_key"], "pfi-v021-unsubmitted-holdings-draft")
        self.assertEqual(
            contract["sqlite_contract"]["tables"],
            ("v021_holding_snapshots", "v021_position_adjustments"),
        )
        self.assertEqual(contract["service_contract"]["class"], "V021HoldingsPersistenceService")
        for method_name in contract["service_contract"]["required_methods"]:
            self.assertTrue(hasattr(V021HoldingsPersistenceService, method_name), method_name)

    def test_frontend_exposes_holding_editor_markers_and_persistence_logic(self) -> None:
        contract = build_v021_stage6_contract()["frontend_contract"]

        for marker in contract["html_markers"]:
            if "strategy-lab" in marker:
                continue
            self.assertIn(marker, self.web_source)
        self.assertIn('data-command-route="/market-research/strategy-lab"', self.web_source)
        for required in (
            '"/holdings": "/investment?tab=holdings"',
            'routeAlias: "/investment?tab=holdings"',
            "const HOLDINGS_DRAFT_STORAGE_KEY",
            "function refreshHoldingsFromBackend",
            "function saveUnsubmittedHoldingsDraft",
            "function saveHoldingsToBackend",
            "function renderHoldingsPersistencePanel",
            "function saveHoldingsEdits",
            "function softDeleteHoldingRow",
            "runtimeApiJson(\"/api/holdings\"",
            "已写入 SQLite 数据库",
            "未提交草稿",
        ):
            self.assertIn(required, self.web_source)
        for forbidden in ("HOLDINGS_STORAGE_KEY", "localStorage.setItem(HOLDINGS_STORAGE_KEY", "已保存到本机"):
            self.assertNotIn(forbidden, self.web_source)

    def test_frontend_has_readable_responsive_holding_styles(self) -> None:
        for required in (
            ".holdings-persistence-panel",
            ".holdings-persistence-head",
            ".holdings-summary",
            ".holdings-table-wrap",
            ".holdings-table",
            ".holdings-table input",
            ".holdings-actions",
            "@media (max-width: 780px)",
        ):
            self.assertIn(required, self.css)
        for forbidden in (
            'data-action="trade"',
            'data-action="pay"',
            'data-action="broker-submit"',
            "broker-submit",
            "live_trade_submission_authorized=true",
        ):
            self.assertNotIn(forbidden, self.web_source)
        for forbidden_copy in ("不做实盘自动下单", "只做研究", "不连接券商", "不提交订单"):
            self.assertNotIn(forbidden_copy, self.web_source)

    def test_sqlite_service_persists_snapshots_across_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "private" / "operational" / "pfi.sqlite"
            service = V021HoldingsPersistenceService(db_path)

            summary = seed_v021_demo_holdings(service)
            self.assertEqual(summary["schema"], "PFIV021HoldingsPersistenceV1")
            self.assertEqual(summary["snapshot_count"], 3)
            self.assertIn("v021_holding_snapshots", summary["tables"])
            self.assertIn("v021_position_adjustments", summary["tables"])

            snapshot = service.get_snapshot("v021-snap-spy")
            self.assertIsNotNone(snapshot)
            updated = replace(snapshot, quantity=12.5, market_price=551.25)
            service.upsert_snapshot(updated)
            adjustment = service.create_adjustment(
                snapshot_id=updated.snapshot_id,
                portfolio_id=updated.portfolio_id,
                instrument_id=updated.instrument_id,
                adjustment_type="UPDATE",
                changes={"quantity": updated.quantity, "market_price": updated.market_price},
                reason="Stage 6 单测更新持仓",
            )

            reopened = V021HoldingsPersistenceService(db_path)
            persisted = reopened.get_snapshot("v021-snap-spy")
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.quantity, 12.5)
            self.assertEqual(persisted.market_price, 551.25)
            self.assertEqual(reopened.get_adjustment(adjustment.adjustment_id).changes["quantity"], 12.5)

    def test_service_supports_create_read_update_and_soft_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = V021HoldingsPersistenceService(Path(tmp) / "pfi.sqlite")
            snapshot = V021HoldingSnapshot(
                snapshot_id="v021-snap-test",
                portfolio_id="manual",
                instrument_id="TEST",
                display_name="测试持仓",
                quantity=2.0,
                average_cost=10.0,
                market_price=12.0,
                currency="CNY",
                source_id="stage6_unit_test",
                as_of="2026-06-27",
            )

            service.upsert_snapshot(snapshot)
            created = service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="ADD",
                changes={"quantity": 2.0},
                reason="新增测试持仓",
            )
            updated = service.update_adjustment(created.adjustment_id, status="closed", reason="已复核")
            self.assertEqual(updated.status, "closed")
            self.assertEqual(updated.reason, "已复核")

            delete_event = service.soft_delete_snapshot(snapshot.snapshot_id, reason="软删除测试")
            self.assertEqual(delete_event.adjustment_type, "SOFT_DELETE")
            self.assertEqual(service.list_snapshots(), [])
            self.assertEqual(len(service.list_snapshots(include_deleted=True)), 1)

            service.soft_delete_adjustment(created.adjustment_id)
            active_adjustments = service.list_adjustments()
            all_adjustments = service.list_adjustments(include_deleted=True)
            self.assertEqual([item.adjustment_type for item in active_adjustments], ["SOFT_DELETE"])
            self.assertGreaterEqual(len(all_adjustments), 2)

    def test_demo_snapshot_values_are_non_negative_and_review_only(self) -> None:
        snapshots = build_v021_demo_holding_snapshots()

        self.assertGreaterEqual(len(snapshots), 3)
        for snapshot in snapshots:
            snapshot.validate()
            self.assertGreaterEqual(snapshot.market_value, 0)
            self.assertEqual(snapshot.source_id, "manual_review")


if __name__ == "__main__":
    unittest.main()
