from __future__ import annotations

import importlib
import json
import unittest


class TestV014S10P1PostRemediationReportEntry(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.import_error = None
        try:
            phase = importlib.import_module("KMFA.tools.v014_s10_p1_post_remediation_report_entry")
            validator = importlib.import_module("KMFA.tools.check_v014_s10_p1_post_remediation_report_entry")
        except ModuleNotFoundError as exc:
            cls.import_error = exc
            return
        cls.payloads = phase.build_payloads()
        cls.manifest = validator.validate_payloads(cls.payloads)

    def setUp(self) -> None:
        if self.import_error is not None and self._testMethodName != "test_phase_implementation_is_available":
            self.skipTest("implementation availability is covered by the RED assertion")

    def test_phase_implementation_is_available(self) -> None:
        self.assertIsNone(
            self.import_error,
            "S10-P1 post-remediation report entry is not implemented",
        )

    def test_management_templates_match_the_roadmap_contract(self) -> None:
        summary = self.manifest["summary"]
        entries = self.manifest["report_entries"]

        self.assertEqual(self.manifest["stage_id"], "S10")
        self.assertEqual(self.manifest["roadmap_phase_id"], "S10-P1")
        self.assertEqual(summary["report_template_count"], 2)
        self.assertEqual(summary["management_section_count"], 11)
        self.assertEqual(summary["project_cost_section_count"], 4)
        self.assertEqual(summary["business_overview_section_count"], 7)
        self.assertEqual(
            entries[0]["visible_sections"],
            ["经营摘要", "项目毛利", "成本结构", "风险事项"],
        )
        self.assertEqual(
            entries[1]["visible_sections"],
            ["经营总览", "收入", "开票", "回款", "现金", "项目", "税务"],
        )

    def test_current_stage9_state_is_visible_without_running_s10_p2(self) -> None:
        summary = self.manifest["summary"]
        trust = self.manifest["trust_entry"]

        self.assertEqual(summary["cost_category_count"], 9)
        self.assertEqual(summary["human_readable_reconciliation_count"], 12)
        self.assertEqual(summary["queue_closed_or_excluded_count"], 69)
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(trust["current_data_quality_grade"], "Q4")
        self.assertEqual(trust["current_report_grade"], "D")
        self.assertEqual(trust["decision"], "NO_GO")
        self.assertTrue(trust["inherited_from_stage9_post_remediation_review"])
        self.assertFalse(trust["grade_calculation_performed_by_this_phase"])
        self.assertFalse(self.manifest["phase_boundaries"]["s10_p2_performed"])

    def test_missing_cash_is_not_zero_and_authority_is_not_overwritten(self) -> None:
        summary = self.manifest["summary"]

        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["forced_zero_materialization_count"], 0)
        self.assertEqual(summary["missing_cash_value_materialized_as_zero_count"], 0)
        self.assertEqual(summary["authority_system_overwrite_allowed_count"], 0)
        self.assertFalse(self.manifest["release_gate"]["formal_report_allowed"])
        self.assertFalse(self.manifest["release_gate"]["business_decision_basis_allowed"])

    def test_visible_content_is_management_readable_and_public_safe(self) -> None:
        visible = json.dumps(
            [
                {
                    "title": entry["visible_title"],
                    "sections": entry["visible_sections"],
                    "summary": entry["visible_management_summary"],
                    "status": entry["visible_trust_status"],
                }
                for entry in self.manifest["report_entries"]
            ],
            ensure_ascii=False,
        )

        for token in (
            "validator",
            "manifest",
            "metadata",
            "source_ref",
            "private_ref",
            "schema",
            "phase",
            "stage",
            "S10-P1",
        ):
            self.assertNotIn(token, visible)
        for token in ("项目成本专题报告", "经营总览报告", "Q4", "D", "NO_GO", "未放行"):
            self.assertIn(token, visible)

    def test_raw_snapshots_are_exact_and_downstream_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        boundaries = self.manifest["phase_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertFalse(boundaries["s10_p3_performed"])
        self.assertFalse(boundaries["stage10_review_performed"])
        self.assertFalse(boundaries["github_upload_performed"])
        self.assertFalse(boundaries["app_reinstall_performed"])
        self.assertFalse(boundaries["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
