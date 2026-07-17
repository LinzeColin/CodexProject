from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s09_p3_human_readable_audit as builder
from KMFA.tools import v015_s09_p3_human_readable_audit as kernel


class HumanReadableAuditArtifactTests(unittest.TestCase):
    @staticmethod
    def _json(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_generated_outputs_are_current(self) -> None:
        builder.check_outputs()

    def test_all_expected_outputs_exist(self) -> None:
        self.assertTrue(all(path.is_file() for path in builder.expected_outputs()))

    def test_rule_manual_and_review_cover_all_rules(self) -> None:
        manual = self._json(builder.RULE_MANUAL_PATH)
        review = self._json(builder.RULE_REVIEW_PATH)
        self.assertEqual(len(manual["rules"]), 10)
        self.assertEqual((review["transformation_rule_count"], review["difference_rule_count"]), (2, 8))
        self.assertEqual(review["review_status"], "PASS")
        self.assertFalse(review["external_human_signoff_claimed"])

    def test_human_manual_uses_friendly_names_not_contract_codes(self) -> None:
        text = (builder.HUMAN_ROOT / "rule_manual_zh.md").read_text(encoding="utf-8")
        for token in ("CONVERSION-RULE", "TRANSFORM_ACCOUNTING", "DIFFERENCE_UNBILLED", "schema_version"):
            self.assertNotIn(token, text)
        for phrase in ("发生了什么", "经营影响", "财务怎么审", "老板摘要"):
            self.assertIn(phrase, text)

    def test_report_sample_has_one_decision_relevant_item_and_no_debug(self) -> None:
        report = self._json(builder.REPORT_SAMPLE_PATH)
        self.assertEqual((report["input_difference_count"], report["included_difference_count"]), (2, 1))
        self.assertEqual(report["excluded_non_decision_difference_count"], 1)
        self.assertEqual(report["technical_term_occurrence_count"], 0)
        self.assertEqual(report["debug_field_count"], 0)
        self.assertEqual(set(report["items"][0]), set(kernel.REPORT_ITEM_FIELDS))

    def test_report_title_is_business_language(self) -> None:
        report = self._json(builder.REPORT_SAMPLE_PATH)
        title = report["items"][0]["title_zh"]
        self.assertEqual(title, "经营提醒：未开票")
        self.assertNotRegex(title, r"[A-Z_]{3,}")

    def test_closure_evidence_covers_six_ordered_feedback_steps(self) -> None:
        closure = self._json(builder.CLOSURE_E2E_PATH)
        self.assertEqual(closure["required_step_count"], 6)
        self.assertEqual(closure["event_count"], 6)
        self.assertEqual(closure["feedback_count"], 6)
        self.assertEqual(closure["event_types"], list(kernel.CLOSURE_STEPS))
        self.assertTrue(closure["closure_complete"])
        self.assertTrue(closure["refresh_state_persisted"])
        self.assertTrue(closure["history_queryable"])
        self.assertTrue(closure["report_version_advanced"])

    def test_closure_negative_gates_are_recorded(self) -> None:
        closure = self._json(builder.CLOSURE_E2E_PATH)
        self.assertTrue(closure["missing_feedback_rejected"])
        self.assertTrue(closure["out_of_order_rejected"])
        self.assertFalse(closure["source_or_fact_mutation_performed"])

    def test_task_matrix_tracks_exact_three_taskpack_tasks(self) -> None:
        matrix = self._json(builder.TASK_MATRIX_PATH)
        manifest = self._json(builder.MANIFEST_PATH)
        self.assertEqual(matrix["task_count"], 3)
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S09P3T01", "S09P3T02", "S09P3T03"])
        self.assertEqual(matrix["phase_acceptance_status"], manifest["phase_acceptance_status"])

    def test_manifest_stops_at_expected_phase_gate(self) -> None:
        manifest = self._json(builder.MANIFEST_PATH)
        final = manifest["phase_acceptance_status"] == "PASSED"
        self.assertIn(manifest["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["overall_accepted_phase_count"], 25 if final else 24)
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(
            manifest["decision"],
            "CONTINUE_TO_S09_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S09_P3_FINAL_VALIDATION",
        )
        self.assertEqual(manifest["s09_stage_review_entry_allowed"], final)
        self.assertFalse(manifest["s09_stage_review_started"])
        self.assertFalse(manifest["s10_p1_entry_allowed"])

    def test_public_outputs_have_no_local_or_raw_path(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in builder.expected_outputs())
        for token in ("/Users/", "/Volumes/", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".pdf"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
