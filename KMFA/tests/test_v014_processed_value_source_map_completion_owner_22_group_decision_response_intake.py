from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_22_group_decision_response_intake as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake import validate


class Owner22GroupDecisionResponseIntakeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_delegated_default_response_is_intaken(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["delegated_default_decision_applied_by_this_phase"])
        self.assertTrue(summary["owner_22_group_response_intaken"])
        self.assertEqual(summary["owner_22_group_count"], 22)
        self.assertEqual(summary["owner_22_group_response_row_count"], 113)
        self.assertEqual(summary["decision_code_counts"]["CONFIRM_GROUP_CANDIDATE_RANK"], 19)
        self.assertEqual(summary["decision_code_counts"]["KEEP_PENDING"], 2)
        self.assertEqual(summary["decision_code_counts"]["REQUEST_MORE_DIAGNOSTICS"], 1)
        self.assertTrue(summary["owner_response_complete"])
        self.assertTrue(summary["all_group_decisions_valid"])

    def test_application_blockers_stay_explicit(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["application_blocker_queue_count"], 113)
        self.assertEqual(summary["linked_application_blocker_count"], 77)
        self.assertEqual(summary["unlinked_application_blocker_count"], 36)
        self.assertEqual(summary["actionable_group_decision_count"], 19)
        self.assertEqual(summary["non_actionable_group_decision_count"], 3)
        self.assertEqual(summary["actionable_linked_application_blocker_count"], 77)
        self.assertEqual(summary["non_actionable_linked_application_blocker_count"], 0)

    def test_decision_matrix_keeps_downstream_gates_closed(self) -> None:
        matrix = self.manifest["decision_matrix"]
        self.assertEqual(matrix["decision_check_count"], 8)
        self.assertEqual(matrix["decision_pass_count"], 4)
        self.assertEqual(matrix["decision_fail_count"], 4)
        self.assertTrue(matrix["owner_response_complete"])
        self.assertTrue(matrix["all_group_decisions_valid"])
        self.assertFalse(matrix["resolution_application_allowed"])
        self.assertFalse(matrix["full_reconciliation_allowed"])

    def test_downstream_and_raw_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["owner_group_decision_applied"])
        self.assertFalse(summary["owner_22_group_partial_authorization_record_ready"])
        self.assertFalse(summary["owner_22_group_partial_authorization_record_written"])
        self.assertFalse(summary["resolution_application_allowed"])
        self.assertFalse(summary["resolution_application_performed_by_this_phase"])
        self.assertFalse(summary["source_map_mutation_performed_by_this_phase"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_response(self) -> None:
        manifest = validate(require_private_response=True)
        self.assertEqual(manifest["summary"]["owner_22_group_count"], 22)
        self.assertEqual(manifest["summary"]["actionable_group_decision_count"], 19)
        self.assertEqual(manifest["summary"]["unlinked_application_blocker_count"], 36)


if __name__ == "__main__":
    unittest.main()
