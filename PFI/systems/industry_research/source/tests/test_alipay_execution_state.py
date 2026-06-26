from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.accounting.alipay_ledger import (
    POSITION_FIELDS,
    UpdateSummary,
    alipay_execution_state,
    build_account_summary,
    confirm_current_positions,
    format_update_summary,
)
from src.data_io import read_csv, write_csv


class AlipayExecutionStateTest(unittest.TestCase):
    def test_needs_confirmation_blocks_execution_even_when_update_exists(self) -> None:
        summary = UpdateSummary(
            start_date="2026-06-04",
            end_date="2026-06-04",
            updated_dates=["2026-06-04"],
            missing_dates=[],
            log_rows=[
                {
                    "date": "2026-06-04",
                    "updated_at": "2026-06-04T22:58:32+10:00",
                    "status": "needs_confirmation",
                    "source_type": "video",
                    "source_path": "/tmp/alipay.mp4",
                }
            ],
        )

        state = alipay_execution_state(summary, "2026-06-04")

        self.assertEqual(state["status"], "needs_confirmation")
        self.assertTrue(state["execution_blocked"])
        self.assertFalse(state["execution_confirmed"])
        self.assertIn("候选数据", state["block_reason"])
        rendered = format_update_summary(summary)
        self.assertIn("status=needs_confirmation", rendered)
        self.assertIn("execution=blocked", rendered)

    def test_confirmed_update_allows_execution_calculation(self) -> None:
        summary = UpdateSummary(
            start_date="2026-06-04",
            end_date="2026-06-04",
            updated_dates=["2026-06-04"],
            missing_dates=[],
            log_rows=[
                {
                    "date": "2026-06-04",
                    "updated_at": "2026-06-04T21:00:00+10:00",
                    "status": "confirmed",
                    "source_type": "csv",
                    "source_path": "/tmp/alipay.csv",
                }
            ],
        )

        state = alipay_execution_state(summary, "2026-06-04")

        self.assertEqual(state["status"], "confirmed")
        self.assertFalse(state["execution_blocked"])
        self.assertTrue(state["execution_confirmed"])

    def test_video_visible_positions_are_candidate_account_source(self) -> None:
        summary = build_account_summary(
            positions=[
                {
                    "date": "2026-06-05",
                    "name": "测试基金",
                    "amount": "1000",
                    "holding_return_amount": "10",
                    "holding_return_pct": "1%",
                    "daily_return_amount": "2",
                    "status": "video_visible",
                }
            ],
            pending_orders=[],
            as_of="2026-06-05",
        )

        self.assertEqual(summary["source_status"], "video_candidate")
        self.assertEqual(summary["source_label"], "支付宝视频候选持仓")

    def test_confirm_current_positions_blocks_unverified_rows_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, stack = self._patch_alipay_paths(Path(tmp))
            with stack:
                self._write_positions(
                    [
                        self._position_row("2026-06-05", "可见基金", "video_visible"),
                        self._position_row("2026-06-05", "沿用基金", "carried_forward_unverified"),
                    ]
                )

                with self.assertRaisesRegex(ValueError, "low-confidence rows"):
                    confirm_current_positions("2026-06-05")

    def test_confirm_current_positions_can_unlock_after_explicit_manual_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths, stack = self._patch_alipay_paths(Path(tmp))
            with stack:
                self._write_positions(
                    [
                        self._position_row("2026-06-05", "可见基金", "video_visible"),
                        self._position_row("2026-06-05", "沿用基金", "carried_forward_unverified"),
                    ]
                )

                result = confirm_current_positions(
                    "2026-06-05",
                    source_path="/tmp/manual-confirmation.png",
                    notes="人工复核支付宝持仓页金额一致",
                    allow_unverified=True,
                )

                rows = read_csv(paths.current_positions)
                statuses = {row["status"] for row in rows}
                sources = {row["source"] for row in rows}
                log_rows = read_csv(paths.daily_update_log)

        self.assertEqual(result["confirmed_positions"], 2)
        self.assertEqual(statuses, {"confirmed_manual"})
        self.assertEqual(sources, {"alipay_manual_confirmed"})
        self.assertEqual(log_rows[-1]["status"], "confirmed")
        self.assertEqual(log_rows[-1]["positions_count"], "2")

    def _write_positions(self, rows: list[dict[str, str]]) -> None:
        from src.accounting import alipay_ledger

        write_csv(alipay_ledger.CURRENT_POSITIONS, rows)

    def _position_row(self, row_date: str, name: str, status: str) -> dict[str, str]:
        row = {field: "" for field in POSITION_FIELDS}
        row.update(
            {
                "date": row_date,
                "source": "alipay_video",
                "name": name,
                "asset_type": "fund",
                "amount": "1000",
                "holding_return_amount": "10",
                "holding_return_pct": "1%",
                "daily_return_amount": "2",
                "status": status,
                "notes": "unit-test",
            }
        )
        return row

    def _patch_alipay_paths(self, root: Path):
        from contextlib import ExitStack
        from types import SimpleNamespace

        paths = SimpleNamespace(
            current_positions=root / "current_positions.csv",
            trade_ledger=root / "trade_ledger.csv",
            pending_orders=root / "pending_orders.csv",
            daily_update_log=root / "daily_update_log.csv",
            import_log=root / "import_log.csv",
        )
        root.mkdir(parents=True, exist_ok=True)
        write_csv(paths.current_positions, [])
        write_csv(paths.trade_ledger, [])
        write_csv(paths.pending_orders, [])
        write_csv(paths.daily_update_log, [])
        write_csv(paths.import_log, [])
        stack = ExitStack()
        stack.enter_context(patch("src.accounting.alipay_ledger.ALIPAY_DIR", root))
        stack.enter_context(patch("src.accounting.alipay_ledger.CURRENT_POSITIONS", paths.current_positions))
        stack.enter_context(patch("src.accounting.alipay_ledger.TRADE_LEDGER", paths.trade_ledger))
        stack.enter_context(patch("src.accounting.alipay_ledger.PENDING_ORDERS", paths.pending_orders))
        stack.enter_context(patch("src.accounting.alipay_ledger.DAILY_UPDATE_LOG", paths.daily_update_log))
        stack.enter_context(patch("src.accounting.alipay_ledger.IMPORT_LOG", paths.import_log))
        return paths, stack


if __name__ == "__main__":
    unittest.main()
