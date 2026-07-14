from __future__ import annotations

import importlib
import json
import unittest


class TestV014S10P2PostRemediationTrustGradeLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.import_error = None
        try:
            phase = importlib.import_module("KMFA.tools.v014_s10_p2_post_remediation_trust_grade_lock")
            validator = importlib.import_module("KMFA.tools.check_v014_s10_p2_post_remediation_trust_grade_lock")
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
            "S10-P2 post-remediation trust grade lock is not implemented",
        )

    def test_abcd_rules_cover_all_roadmap_dimensions(self) -> None:
        rules = self.manifest["grade_rules"]["report_grades"]

        self.assertEqual([rule["grade"] for rule in rules], ["A", "B", "C", "D"])
        self.assertEqual(
            self.manifest["grade_rules"]["driver_dimensions"],
            ["data_quality", "difference_status", "human_confirmation", "timeliness"],
        )
        self.assertEqual(rules[0]["minimum_quality_grade"], "Q5")
        self.assertTrue(rules[0]["zero_delta_required"])
        self.assertEqual(rules[1]["minimum_quality_grade"], "Q4")
        self.assertTrue(rules[1]["limitations_required"])
        self.assertTrue(rules[2]["preview_only"])
        self.assertEqual(rules[3]["release_permission"], "blocked_decision_use")

    def test_current_state_is_recomputed_and_locked_to_d(self) -> None:
        summary = self.manifest["summary"]

        self.assertEqual(summary["report_grade_record_count"], 2)
        self.assertEqual(summary["grade_distribution"], {"D": 2})
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["maximum_report_grade_before_hard_blocks"], "B")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["grade_recalculation_performed_by_this_phase"])
        self.assertFalse(summary["automatic_grade_promotion_performed"])

    def test_difference_confirmation_and_timeliness_inputs_are_explicit(self) -> None:
        inputs = self.manifest["grade_inputs"]

        self.assertEqual(inputs["open_final_difference_accepted_count"], 3)
        self.assertEqual(inputs["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(inputs["incomplete_reconciliation_count"], 1)
        self.assertFalse(inputs["zero_delta_passed"])
        self.assertEqual(inputs["human_confirmation_status"], "partial_not_release_sufficient")
        self.assertEqual(inputs["timeliness_status"], "current_no_stale_signal")
        self.assertFalse(inputs["stale_input_detected"])
        self.assertFalse(inputs["full_business_value_consistency_verified"])

    def test_each_report_record_has_complete_version_binding_and_hard_blocks(self) -> None:
        records = self.manifest["grade_records"]

        self.assertEqual(len(records), 2)
        self.assertEqual(self.manifest["summary"]["record_version_binding_count"], 2)
        for record in records:
            self.assertEqual(record["computed_report_grade"], "D")
            self.assertEqual(record["maximum_report_grade_before_hard_blocks"], "B")
            self.assertEqual(record["release_permission"], "blocked_decision_use")
            self.assertEqual(len(record["hard_blocks"]), 6)
            for key in (
                "report_record_version",
                "report_entry_version",
                "template_version",
                "formula_version",
                "mapping_version",
                "field_mapping_version",
                "grade_policy_version",
                "release_gate_version",
            ):
                self.assertTrue(record[key], f"missing version field: {key}")
            self.assertFalse(record["complete_trusted_report_display_allowed"])
            self.assertFalse(record["formal_report_allowed"])
            self.assertFalse(record["business_decision_basis_allowed"])

    def test_management_explanation_is_public_safe_and_not_falsely_trusted(self) -> None:
        visible = json.dumps(self.manifest["management_explanation"], ensure_ascii=False)

        for token in (
            "validator",
            "manifest",
            "metadata",
            "source_ref",
            "private_ref",
            "schema",
            "phase",
            "stage",
            "S10-P2",
        ):
            self.assertNotIn(token, visible)
        for token in ("D级", "未放行", "关键现金数据缺失", "九项非零差异", "一项比较未完成"):
            self.assertIn(token, visible)

    def test_raw_snapshots_and_downstream_boundaries_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        boundaries = self.manifest["phase_boundaries"]

        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(boundaries["s10_p2_performed"])
        self.assertFalse(boundaries["s10_p3_performed"])
        self.assertFalse(boundaries["stage10_review_performed"])
        self.assertFalse(boundaries["github_upload_performed"])
        self.assertFalse(boundaries["app_reinstall_performed"])
        self.assertFalse(boundaries["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
