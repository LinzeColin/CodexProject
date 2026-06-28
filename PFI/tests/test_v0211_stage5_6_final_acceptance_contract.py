from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

import pfi_v02.stage_v0211_ui_recovery as recovery
from pfi_v02.stage_v021_runtime_api import (
    build_v021_operational_trends,
    save_v021_holdings_payload,
)


class V0211Stage5Stage6FinalAcceptanceContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.js = (self.root / "web" / "app" / "shell.js").read_text(encoding="utf-8")
        self.html = (self.root / "web" / "index.html").read_text(encoding="utf-8")

    def test_stage5_contract_locks_real_chart_and_final_acceptance_scope(self) -> None:
        contract = recovery.build_v0211_stage5_contract()

        self.assertEqual(contract["schema"], "PFIV0211ProductUIRecoveryStage5ContractV1")
        self.assertEqual(contract["stage"], "S5 真实图表与最终验收")
        self.assertEqual(contract["task_id"], "V0211-S5-T01")
        self.assertTrue(contract["current_stage_only"])
        self.assertEqual(set(contract["chart_surfaces"]), {"accounts", "investment", "consumption"})
        self.assertEqual(contract["chart_runtime_contract"]["endpoint"], "/api/trends")
        self.assertIn("SQLite operational database", contract["chart_runtime_contract"]["allowed_sources"])
        self.assertIn("MetaDatabase/PFI/alipay_daily", contract["chart_runtime_contract"]["allowed_sources"])
        self.assertIn("所有一级入口、二级入口和主要按钮真实可点", "\n".join(contract["behavior_e2e_required"]))
        self.assertIn("使用 demo/sample/synthetic/fixture/mock/fake", "\n".join(contract["stop_conditions"]))

    def test_stage6_project_review_contract_is_second_phase_closeout_not_extra_fake_stage(self) -> None:
        contract = recovery.build_v0211_stage6_project_review_contract()

        self.assertEqual(contract["schema"], "PFIV0211ProjectReviewCloseoutStage6AliasV1")
        self.assertEqual(contract["owner_stage_label"], "Stage 6 项目级复审验收")
        self.assertEqual(contract["machine_stage_completed"], "S5")
        self.assertIn("Stage 5 完成后执行", contract["entry_condition"])
        self.assertIn("跨板块复审", "\n".join(contract["review_scope"]))
        self.assertIn("GitHub main 同步", "\n".join(contract["closeout_required"]))
        self.assertIn("刷新本机 PFI.app 入口", "\n".join(contract["closeout_required"]))
        self.assertIn("清理非必要缓存", "\n".join(contract["closeout_required"]))

    def test_operational_trends_are_derived_from_sqlite_and_real_metadatabase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "stage5-real-charts.sqlite"
            save_v021_holdings_payload(
                {
                    "rows": [
                        {
                            "snapshotId": "owner-stage5-real-chart",
                            "instrumentId": "PFI_STAGE5",
                            "displayName": "真实图表验收持仓",
                            "quantity": 4,
                            "averageCost": 20,
                            "marketPrice": 25,
                            "currency": "CNY",
                            "account": "主账户",
                            "updatedAt": "2026-06-29",
                            "note": "Stage 5 临时图表验证",
                        }
                    ]
                },
                db_path=db_path,
            )

            payload = build_v021_operational_trends(db_path=db_path)

        accounts = payload["trends"]["accounts"]
        investment = payload["trends"]["investment"]
        consumption = payload["trends"]["consumption"]
        self.assertEqual(accounts["source"], "SQLite 运行读模型")
        self.assertEqual(investment["source"], "SQLite 运行读模型")
        self.assertEqual(investment["periods"], ["成本基准", "当前"])
        market_value = next(item for item in investment["series"] if item["id"] == "market_value_cny")
        unrealized = next(item for item in investment["series"] if item["id"] == "unrealized_pnl_cny")
        self.assertEqual(market_value["values"], [80.0, 100.0])
        self.assertEqual(unrealized["values"], [0.0, 20.0])
        self.assertEqual(consumption["source"], "MetaDatabase 真实支付宝流水")
        self.assertEqual(consumption["periods"], ["最近30天", "本月"])
        self.assertGreater(payload["readModel"]["consumption"]["transaction_count"], 0)
        self.assertNotIn("demo", str(payload).lower())
        self.assertNotIn("mock", str(payload).lower())

    def test_formal_web_shell_does_not_ship_hardcoded_chart_or_synthetic_acceptance_paths(self) -> None:
        web_source = "\n".join((self.html, self.js))

        self.assertIn('runtimeApiJson("/api/trends"', self.js)
        self.assertIn("runtimeTrendState", self.js)
        self.assertNotRegex(self.js, re.compile(r"chart:\s*\[[^\]]*[0-9]"))
        self.assertNotIn("UNIFIED_TREND_PERIODS", self.js)
        self.assertNotIn("legacyChartToTrend", self.js)
        self.assertNotIn("本地缓存趋势", self.js)
        for forbidden in ("stage6_synthetic_e2e", "source_fixture_matrix", "fixture", "合成端到端", "合成券商", "合成导入账本"):
            self.assertNotIn(forbidden, web_source)

    def test_stage5_and_stage6_human_records_exist_and_match_delivery_scope(self) -> None:
        stage5_doc = self.root / "docs" / "pfi_v0211" / "STAGE5_REAL_CHARTS_FINAL_ACCEPTANCE.md"
        stage6_doc = self.root / "docs" / "pfi_v0211" / "STAGE6_PROJECT_REVIEW_CLOSEOUT.md"
        for path in (stage5_doc, stage6_doc):
            self.assertTrue(path.exists(), path)

        stage5 = stage5_doc.read_text(encoding="utf-8")
        stage6 = stage6_doc.read_text(encoding="utf-8")
        self.assertIn("账户、投资、消费趋势图读取真实数据层或显示中文空状态", stage5)
        self.assertIn("/api/trends", stage5)
        self.assertIn("不是关键词测试", stage5)
        self.assertIn("跨板块复审", stage6)
        self.assertIn("GitHub main", stage6)
        for name in ("README.md", "开发记录.md", "功能清单.md", "模型参数文件.md", "HANDOFF.md"):
            text = (self.root / name).read_text(encoding="utf-8")
            self.assertIn("v0.2.1.1 Stage 5", text, name)
            self.assertIn("Stage 6 项目级复审验收", text, name)


if __name__ == "__main__":
    unittest.main()
