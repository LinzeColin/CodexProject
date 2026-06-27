from __future__ import annotations

from pathlib import Path
import unittest

from pfi_v02.stage_v022_database_governance import (
    V022_STAGE0_SOURCE_PACK,
    V022_STAGE0_TASKS,
    build_v022_stage0_agent_review,
    build_v022_stage0_contract,
)


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage0DatabaseGovernance(unittest.TestCase):
    def test_stage0_contract_locks_database_governance_scope(self) -> None:
        contract = build_v022_stage0_contract()

        self.assertEqual(contract["version"], "v0.2.2")
        self.assertEqual(contract["stage"], "Stage 0")
        self.assertEqual(contract["scope"]["domain"], "database_governance_and_e2e_logic")
        self.assertEqual(contract["scope"]["html_template_policy"], "reference_only_not_stage0_ui_change")
        self.assertEqual(contract["roadmap_shape"]["format"], "Stage -> Phase -> Task")
        self.assertEqual(contract["roadmap_shape"]["stage_range"], "Stage 0-13")
        self.assertIn("PFI/web/index.html", contract["scope"]["forbidden_stage0_changes"])
        self.assertIn("PFI/web/app/shell.js", contract["scope"]["forbidden_stage0_changes"])
        self.assertIn("PFI/config/pfi_parameters.yaml", contract["scope"]["forbidden_stage0_changes"])
        self.assertIn("PFI/config/parameter_changelog.md", contract["scope"]["allowed_stage0_changes"])

    def test_stage0_task_ids_match_stage_phase_task_roadmap(self) -> None:
        contract = build_v022_stage0_contract()
        task_ids = tuple(task["task_id"] for task in V022_STAGE0_TASKS)

        self.assertEqual(contract["task_ids"], ("S0-P1-T1", "S0-P1-T2", "S0-P1-T3", "S0-P2-T1", "S0-P2-T2"))
        self.assertEqual(task_ids, contract["task_ids"])
        self.assertEqual(contract["roadmap_shape"]["stage0_task_count"], 5)
        self.assertIn("PFI/config/pfi_parameters.yaml", contract["current_inventory"]["stage0_core_file_list"])
        self.assertIn("PFI/web/index.html", contract["current_inventory"]["stage0_core_file_list"])
        self.assertIn("PFI/tests/test_pfi_parameters_consistency.py", contract["current_inventory"]["stage0_core_file_list"])

    def test_downloaded_task_pack_sources_are_recorded_with_hashes(self) -> None:
        files = {item["file"]: item for item in V022_STAGE0_SOURCE_PACK}

        self.assertIn("PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md", files)
        self.assertIn("PFI_v0.2.2_E2E_logic_optimization_package (1).zip", files)
        self.assertIn("PFI_v0.2.2_Roadmap_Acceptance_Stop_Validation_zh.md", files)
        self.assertIn("PFI_v0.2.2_Codex_Task_Pack_zh.md", files)
        self.assertIn("PFI_v0.2.2_UIUX_Logic_Review_Template.html", files)
        self.assertEqual(files["PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md"]["role"], "stage_phase_task_roadmap")
        self.assertEqual(files["PFI_v0.2.2_UIUX_Logic_Review_Template.html"]["role"], "future_logic_review_reference_only")
        for item in V022_STAGE0_SOURCE_PACK:
            self.assertRegex(str(item["sha256"]), r"^[0-9a-f]{64}$")

    def test_current_inventory_lists_hardcoded_thresholds_and_conflicts(self) -> None:
        contract = build_v022_stage0_contract()
        inventory = contract["current_inventory"]
        thresholds = inventory["known_thresholds"]
        conflicts = {item["topic"]: item for item in contract["baseline_conflicts"]}

        self.assertEqual(inventory["current_cashflow_windows"], (30, 90, 180))
        self.assertEqual(inventory["v022_required_cashflow_windows"], (7, 21, 30, 60, 90, 180, 360))
        self.assertEqual(thresholds["low_confidence_review_threshold"], 0.70)
        self.assertEqual(thresholds["large_spend_aud_threshold"], 500)
        self.assertEqual(thresholds["night_window_v022_required"], "22:00-06:00")
        self.assertIn("currency_and_fx", conflicts)
        self.assertIn("interconnection", conflicts)
        self.assertIn("runtime_diff", conflicts)

    def test_stage0_baseline_report_is_chinese_and_names_no_frontend_change(self) -> None:
        report = (ROOT / "docs" / "pfi_v022" / "STAGE0_BASELINE_REPORT.md").read_text(encoding="utf-8")

        self.assertIn("v0.2.2 Stage 0 Baseline Report", report)
        self.assertIn("数据库治理", report)
        self.assertIn("不修改 `PFI/web/index.html`", report)
        self.assertIn("不修改 `PFI/web/app/shell.js`", report)
        self.assertIn("S0-P1-T1", report)
        self.assertIn("S0-P2-T2", report)
        self.assertIn("现金流窗口", report)
        self.assertIn("7/21/30/60/90/180/360", report)
        self.assertIn("Agent 1", report)
        self.assertIn("Agent 3", report)

    def test_stage0_does_not_create_future_ui_review_page(self) -> None:
        self.assertFalse((ROOT / "web" / "pfi_v022_logic_review.html").exists())

    def test_parameter_changelog_exists_and_tracks_required_fields(self) -> None:
        changelog = (ROOT / "config" / "parameter_changelog.md").read_text(encoding="utf-8")

        self.assertIn("task_name", changelog)
        self.assertIn("parameter_version", changelog)
        self.assertIn("旧值", changelog)
        self.assertIn("新值", changelog)
        self.assertIn("原因", changelog)
        self.assertIn("影响范围", changelog)

    def test_three_base_files_record_v022_stage0_readiness(self) -> None:
        for file_name in ("模型参数文件.md", "功能清单.md", "开发记录.md"):
            text = (ROOT / file_name).read_text(encoding="utf-8")
            self.assertIn("v0.2.2", text)
            self.assertIn("Stage 0", text)
            self.assertIn("数据库治理", text)
            self.assertIn("PFI v0.2.2 E2E 逻辑优化", text)
        parameter_file = (ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        self.assertIn("task_name: `PFI v0.2.2 E2E 逻辑优化`", parameter_file)
        self.assertIn("parameter_version: `v0.2.2`", parameter_file)

    def test_agent_review_marks_stage0_non_blocking(self) -> None:
        review = build_v022_stage0_agent_review()

        self.assertFalse(review["blocking"])
        self.assertEqual(review["agent_1_financial_logic"]["status"], "通过")
        self.assertEqual(review["agent_3_parameter_governance"]["status"], "通过")


if __name__ == "__main__":
    unittest.main()
