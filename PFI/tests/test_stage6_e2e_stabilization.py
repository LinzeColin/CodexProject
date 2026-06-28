from __future__ import annotations

import unittest
from pathlib import Path

from pfi_os.application.homepage_summary import empty_homepage_summary
from pfi_v02.stage6_e2e_stabilization import (
    STAGE6_E2E_SOURCE_IDS,
    STAGE6_TOTAL_GATE_COUNT,
    build_stage6_e2e_stabilization_model,
)


class Stage6E2EStabilizationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = build_stage6_e2e_stabilization_model()

    def test_phase_statuses_total_gates_and_taskpack_audit_pass(self) -> None:
        self.assertEqual(self.model["schema"], "PFIV02Stage6E2EStabilizationV1")
        self.assertEqual(self.model["phase_6a"]["status"], "PASS")
        self.assertEqual(self.model["phase_6b"]["status"], "PASS")
        self.assertEqual(self.model["phase_6c"]["status"], "PASS")

        total_gate = self.model["total_acceptance_gate"]
        taskpack_audit = self.model["taskpack_acceptance_audit"]
        self.assertEqual(len(total_gate), STAGE6_TOTAL_GATE_COUNT)
        self.assertTrue(all(item["status"] == "PASS" for item in total_gate))
        self.assertTrue(all(item["status"] == "PASS" for item in taskpack_audit))

    def test_source_fixture_matrix_covers_core_sources_and_non_csv_contracts(self) -> None:
        rows = self.model["phase_6a"]["source_fixture_matrix"]
        by_source = {row["source_id"]: row for row in rows}

        self.assertEqual(set(by_source), set(STAGE6_E2E_SOURCE_IDS))
        for source_id in ("alipay_daily", "alipay_fund", "moomoo_au", "cn_broker", "abc_bullion", "cba_bank", "wechat_pay"):
            self.assertIn(source_id, by_source)
            self.assertTrue(by_source[source_id]["read_only"])
            self.assertFalse(by_source[source_id]["requires_trading_password"])
        for source_id in ("alipay_fund", "cn_broker", "abc_bullion"):
            self.assertTrue(by_source[source_id]["non_csv_primary"])
            self.assertNotEqual(by_source[source_id]["primary_acquisition"], ("CSV",))
        self.assertIn("cba_csv_v1", by_source["cba_bank"]["parser_contracts"])

    def test_homepage_loop_closes_accounts_investment_consumption_health_and_recommendations(self) -> None:
        homepage = self.model["phase_6a"]["homepage_loop"]

        self.assertEqual(homepage["status"], "PASS")
        self.assertEqual(set(homepage["required_outputs"]), {"accounts", "investment", "consumption", "data_health", "recommendations"})
        self.assertTrue(all(homepage["required_outputs"].values()))
        self.assertIn("数据健康", homepage["owner_readable_cards"])
        self.assertTrue({"同步全部", "处理待复核", "查看建议", "生成报告"}.issubset(set(homepage["quick_actions"])))
        self.assertGreater(homepage["top_recommendation_count"], 0)

    def test_ledger_loop_classifies_transfers_investments_refunds_fees_valuation_and_repayment(self) -> None:
        ledger = self.model["phase_6a"]["ledger_loop"]
        by_check = {item["check_id"]: item for item in ledger["checks"]}

        self.assertEqual(ledger["status"], "PASS")
        self.assertGreater(ledger["stage3_traceable_transaction_count"], 0)
        for check_id in ("transfer", "investment_buy", "consumption", "refund", "fee", "valuation", "fund_redemption", "bullion_buy", "credit_repayment"):
            self.assertIn(check_id, by_check)
            self.assertEqual(by_check[check_id]["status"], "PASS")
            self.assertTrue(by_check[check_id]["evidence_ref"])
            self.assertTrue(by_check[check_id]["parser_version"])

        self.assertFalse(by_check["transfer"]["affects_consumption"])
        self.assertFalse(by_check["investment_buy"]["affects_consumption"])
        self.assertTrue(by_check["investment_buy"]["affects_investment"])
        self.assertFalse(by_check["refund"]["affects_consumption"])
        self.assertEqual(by_check["fund_redemption"]["event_type"], "FUND")
        self.assertTrue(by_check["fund_redemption"]["affects_investment"])
        self.assertEqual(by_check["bullion_buy"]["event_type"], "BUY_ASSET")
        self.assertTrue(by_check["bullion_buy"]["affects_investment"])
        self.assertEqual(by_check["credit_repayment"]["event_type"], "TRANSFER")
        self.assertFalse(by_check["credit_repayment"]["affects_consumption"])

    def test_recommendation_loop_requires_evidence_lifecycle_and_supported_decisions(self) -> None:
        recommendation = self.model["phase_6a"]["recommendation_loop"]

        self.assertEqual(recommendation["status"], "PASS")
        self.assertGreaterEqual(recommendation["generated_count"], 8)
        self.assertLess(len(recommendation["displayed_top_ids"]), recommendation["lifecycle_row_count"])
        self.assertTrue(recommendation["all_generated_have_evidence"])
        self.assertEqual(
            set(recommendation["supported_decisions"]),
            {"accept", "reject", "snooze", "review", "effect_measured"},
        )
        decisions = {item["decision_record"]["decision"] for item in recommendation["decision_results"]}
        self.assertEqual(decisions, set(recommendation["supported_decisions"]))

    def test_regression_governance_and_delivery_rollback_are_documented(self) -> None:
        regression = self.model["phase_6b"]
        delivery = self.model["phase_6c"]

        self.assertIn("cd QBVS", regression["existing_smoke"]["command"])
        self.assertIn("test_stage6_e2e_stabilization", regression["new_focused_tests"]["command"])
        self.assertIn("lean_governance.py ci --changed-only --base-ref origin/main", regression["changed_scope_governance"]["command"])
        self.assertIn("PFI/docs/governance", regression["no_broad_refactor"]["allowed_scope"])
        self.assertIn("Alpha", regression["no_broad_refactor"]["forbidden_scope"])

        self.assertGreaterEqual(len(delivery["rollback_plan"]), 6)
        self.assertTrue(any("Alpha repository" in item for item in delivery["follow_up_list"]))
        self.assertTrue(any("Real account data" in item for item in delivery["follow_up_list"]))
        self.assertTrue(any("PDF/ZIP" in item for item in delivery["follow_up_list"]))
        self.assertTrue(any("CDR/Open Banking" in item for item in delivery["follow_up_list"]))

    def test_compatibility_preserves_entries_qbvs_and_forbidden_first_level_entries(self) -> None:
        compatibility = self.model["compatibility"]

        self.assertEqual(compatibility["primary_entry_count"], 8)
        self.assertEqual(
            tuple(compatibility["primary_entries"]),
            ("首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与上传", "建议与复盘", "报告与洞察"),
        )
        self.assertEqual(tuple(compatibility["v01_compatibility_entries"]), ("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"))
        self.assertEqual(compatibility["legacy_compatibility_entry"]["target_location"], "独立系统：CodexProject/QBVS")
        self.assertFalse(compatibility["alpha_first_level_entry_added"])
        self.assertFalse(compatibility["ralpha_first_level_entry_added"])
        self.assertFalse(compatibility["system_development_first_level_entry_added"])
        self.assertTrue(compatibility["qbvs_independent_system"])
        self.assertFalse(compatibility["qbvs_owned_by_pfi"])
        self.assertTrue(compatibility["qbvs_runtime_moved_out_of_pfi"])
        self.assertFalse(compatibility["product_surface_forbidden_external_dependency"])

    def test_homepage_summary_exposes_stage6_without_losing_prior_stage_payloads(self) -> None:
        summary = empty_homepage_summary()

        self.assertEqual(summary["stage6_dashboard"]["schema"], "PFIV02Stage6E2EStabilizationV1")
        self.assertEqual(summary["stage5_dashboard"]["schema"], "PFIV02Stage5AdviceReportAlphaExportV1")
        self.assertEqual(summary["stage4_dashboard"]["schema"], "PFIV02Stage4AnalysisMVPV1")
        self.assertEqual(summary["stage3_dashboard"]["schema"], "PFIV02Stage3ReadableMVPV1")
        self.assertIn("第 6 阶段", summary["evidence_drawer"]["title"])
        self.assertIn("第 5 阶段", summary["evidence_drawer"]["title"])
        self.assertIn("第 4 阶段", summary["evidence_drawer"]["title"])

    def test_web_shell_exposes_stage6_views_without_extra_first_level_entries(self) -> None:
        root = Path(__file__).resolve().parents[1]
        html = (root / "web" / "index.html").read_text(encoding="utf-8")
        js = (root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn('data-primary-workspaces="10"', html)
        self.assertEqual(html.count('data-primary-entry="true"'), 10)
        self.assertNotIn('data-v01-workspaces="6"', html)
        self.assertNotIn('data-v01-entry="true"', html)
        self.assertIn('"stage6_dashboard"', html)
        self.assertIn("项目级复审", js)
        self.assertIn("真实数据闭环", js)
        for label in ("端到端验收", "合成端到端", "stage6_synthetic_e2e", "source_fixture_matrix", "fixture"):
            self.assertNotIn(label, js)
        self.assertNotIn('data-workspace="alpha"', html.lower())
        self.assertNotIn('data-workspace="ralpha"', html.lower())
        self.assertNotIn('data-workspace="system"', html.lower())

    def test_new_stage6_files_do_not_reference_forbidden_external_project_name(self) -> None:
        root = Path(__file__).resolve().parents[1]
        forbidden = "Serenity" + "-Alipay"
        checked = (
            root / "src" / "pfi_v02" / "stage6_e2e_stabilization.py",
            root / "tests" / "test_stage6_e2e_stabilization.py",
        )

        for path in checked:
            self.assertNotIn(forbidden, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
