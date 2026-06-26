from __future__ import annotations

import unittest

from src.advice.engine import build_trading_advice


class AdviceEngineAccountGateTest(unittest.TestCase):
    def test_missing_alipay_update_zeroes_buy_candidate(self) -> None:
        rows = build_trading_advice(
            factors=[self._factor(momentum=-0.02)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.05)],
            holdings=[self._holding(amount=1000, return_pct=-0.04, weight=0.02)],
            pending_orders=[],
            account_summary={
                "total_holding_amount": 100000,
                "alipay_update_status": "missing",
                "alipay_update_missing": True,
                "alipay_missing_dates": ["2026-06-04"],
            },
        )

        self.assertEqual(rows[0]["Position"], "账户待更新-买入候选")
        self.assertEqual(rows[0]["Volume"], 0.0)
        self.assertIn("本次Volume归零", rows[0]["risk_note"])
        self.assertIn("2026-06-04", rows[0]["entry_condition"])

    def test_missing_alipay_update_zeroes_sell_candidate(self) -> None:
        rows = build_trading_advice(
            factors=[self._factor(momentum=0.025)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.05)],
            holdings=[self._holding(amount=12000, return_pct=0.09, weight=0.12)],
            pending_orders=[],
            account_summary={
                "total_holding_amount": 100000,
                "alipay_update_status": "missing",
                "alipay_update_missing": True,
                "alipay_missing_dates": ["2026-06-04"],
            },
        )

        self.assertEqual(rows[0]["Position"], "账户待更新-卖出候选")
        self.assertEqual(rows[0]["Volume"], 0.0)
        self.assertIn("卖出", rows[0]["exit_condition"])

    def test_current_alipay_update_keeps_executable_volume(self) -> None:
        rows = build_trading_advice(
            factors=[self._factor(momentum=-0.02)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.05)],
            holdings=[self._holding(amount=1000, return_pct=-0.04, weight=0.02)],
            pending_orders=[],
            account_summary={
                "total_holding_amount": 100000,
                "alipay_update_status": "updated",
                "alipay_update_missing": False,
            },
        )

        self.assertEqual(rows[0]["Position"], "建议买入-下跌承接")
        self.assertGreater(rows[0]["Volume"], 0.0)
        self.assertIn("跌幅项", rows[0]["volume_basis"])

    def test_buy_volume_changes_with_holding_return_weight_and_volume_risk(self) -> None:
        low_risk_rows = build_trading_advice(
            factors=[self._factor(momentum=-0.035, volume_ratio=0.9)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.06)],
            holdings=[self._holding(amount=1000, return_pct=-0.10, weight=0.02)],
            pending_orders=[],
            account_summary={"total_holding_amount": 100000, "alipay_update_missing": False},
        )
        high_risk_rows = build_trading_advice(
            factors=[self._factor(momentum=-0.035, volume_ratio=1.9)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.06)],
            holdings=[self._holding(amount=11000, return_pct=-0.01, weight=0.11)],
            pending_orders=[],
            account_summary={"total_holding_amount": 100000, "alipay_update_missing": False},
        )

        self.assertGreater(low_risk_rows[0]["Volume"], high_risk_rows[0]["Volume"])
        self.assertIn("放量扣减2.000%", high_risk_rows[0]["volume_basis"])

    def test_sell_volume_changes_with_profit_concentration_and_breakout_risk(self) -> None:
        profit_rows = build_trading_advice(
            factors=[self._factor(momentum=0.03, volume_ratio=1.0)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.06)],
            holdings=[self._holding(amount=14000, return_pct=0.10, weight=0.14)],
            pending_orders=[],
            account_summary={"total_holding_amount": 100000, "alipay_update_missing": False},
        )
        breakout_rows = build_trading_advice(
            factors=[self._factor(momentum=0.04, volume_ratio=1.8)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.06)],
            holdings=[self._holding(amount=5000, return_pct=0.025, weight=0.05)],
            pending_orders=[],
            account_summary={"total_holding_amount": 100000, "alipay_update_missing": False},
        )

        self.assertGreater(profit_rows[0]["Volume"], breakout_rows[0]["Volume"])
        self.assertIn("突破扣减1.500%", breakout_rows[0]["volume_basis"])

    def test_user_tradable_index_objects_are_not_forced_to_background(self) -> None:
        rows = build_trading_advice(
            factors=[
                {
                    "symbol": "SH.000688",
                    "name": "科创50",
                    "momentum_5d": -0.02,
                    "volume_ratio_5d": 1.0,
                    "pe": 25,
                },
                {
                    "symbol": "SZ.399986",
                    "name": "中证银行",
                    "momentum_5d": 0.02,
                    "volume_ratio_5d": 1.0,
                    "pe": 8,
                },
                {
                    "symbol": "SH.000001",
                    "name": "上证指数",
                    "momentum_5d": -0.02,
                    "volume_ratio_5d": 1.0,
                    "pe": 12,
                },
            ],
            events=[],
            signals=[],
            positions=[
                self._position(signal="buy", weight=0.05, symbol="SH.000688", name="科创50", asset_class="Index"),
                self._position(signal="buy", weight=0.05, symbol="SZ.399986", name="中证银行", asset_class="Index"),
                self._position(signal="buy", weight=0.05, symbol="SH.000001", name="上证指数", asset_class="Index"),
            ],
            holdings=[
                self._holding(amount=5000, return_pct=0.04, weight=0.08, symbol="SZ.399986", name="中证银行"),
            ],
            pending_orders=[],
            account_summary={
                "total_holding_amount": 100000,
                "alipay_update_status": "updated",
                "alipay_update_missing": False,
            },
        )

        by_name = {row["Name"]: row for row in rows}
        self.assertEqual(by_name["科创50"]["Position"], "建议买入-下跌承接")
        self.assertEqual(by_name["中证银行"]["Position"], "建议卖出-上涨减仓")
        self.assertEqual(by_name["上证指数"]["Position"], "观望-指数背景")

    def test_unconfirmed_alipay_update_still_zeroes_executable_volume(self) -> None:
        rows = build_trading_advice(
            factors=[self._factor(momentum=-0.02)],
            events=[],
            signals=[],
            positions=[self._position(signal="buy", weight=0.05)],
            holdings=[self._holding(amount=1000, return_pct=-0.04, weight=0.02)],
            pending_orders=[],
            account_summary={
                "total_holding_amount": 100000,
                "alipay_update_status": "needs_confirmation",
                "alipay_update_missing": False,
                "alipay_execution_blocked": True,
                "alipay_execution_block_reason": "当日资料为视频/截图/OCR候选数据，仍需官方CSV或人工确认后才能用于执行金额",
            },
        )

        self.assertEqual(rows[0]["Position"], "账户待更新-买入候选")
        self.assertEqual(rows[0]["Volume"], 0.0)
        self.assertIn("未更新或未确认", rows[0]["entry_condition"])

    def _factor(self, momentum: float, volume_ratio: float = 1.0) -> dict[str, object]:
        return {
            "symbol": "159995",
            "name": "芯片ETF华夏",
            "momentum_5d": momentum,
            "volume_ratio_5d": volume_ratio,
            "pe": 20,
        }

    def _position(
        self,
        signal: str,
        weight: float,
        symbol: str = "159995",
        name: str = "芯片ETF华夏",
        asset_class: str = "ETF",
    ) -> dict[str, object]:
        return {
            "symbol": symbol,
            "name": name,
            "industry": "半导体",
            "internal_signal": signal,
            "risk_adjusted_weight": weight,
            "asset_class": asset_class,
            "reason": "unit-test",
        }

    def _holding(
        self,
        amount: float,
        return_pct: float,
        weight: float,
        symbol: str = "159995",
        name: str = "芯片ETF华夏",
    ) -> dict[str, str]:
        return {
            "symbol": symbol,
            "name": name,
            "amount": str(amount),
            "holding_return_pct": str(return_pct),
            "weight": str(weight),
        }


if __name__ == "__main__":
    unittest.main()
