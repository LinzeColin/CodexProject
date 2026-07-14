from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_22_group_decision_checklist as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_22_group_decision_checklist import validate


class Owner22GroupDecisionChecklistTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_private_chinese_checklist_is_prepared_without_owner_confirmation(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["owner_22_group_count"], 22)
        self.assertEqual(summary["owner_22_group_response_row_count"], 113)
        self.assertEqual(summary["owner_22_group_linked_application_blocker_count"], 77)
        self.assertEqual(summary["owner_22_group_unlinked_application_blocker_count"], 36)
        self.assertTrue(summary["private_22_group_checklist_prepared"])
        self.assertTrue(summary["private_22_group_response_template_prepared"])
        self.assertFalse(summary["owner_group_decision_confirmed"])

    def test_recommended_decision_counts_are_aggregate_only(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["recommended_confirm_group_candidate_rank_count"], 19)
        self.assertEqual(summary["recommended_keep_pending_count"], 2)
        self.assertEqual(summary["recommended_request_more_diagnostics_count"], 1)
        self.assertEqual(summary["allowed_decision_code_count"], 5)

    def test_decision_matrix_keeps_application_blocked(self) -> None:
        matrix = self.manifest["decision_matrix"]
        self.assertEqual(matrix["decision_check_count"], 8)
        self.assertEqual(matrix["decision_pass_count"], 4)
        self.assertEqual(matrix["decision_fail_count"], 4)
        self.assertTrue(matrix["owner_22_group_decision_checklist_prepared"])
        self.assertFalse(matrix["owner_group_decision_confirmed"])
        self.assertFalse(matrix["owner_approved_resolution_input_present"])
        self.assertFalse(matrix["resolution_application_allowed"])
        self.assertFalse(matrix["full_reconciliation_allowed"])

    def test_downstream_and_raw_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["resolution_application_allowed"])
        self.assertFalse(summary["resolution_application_performed_by_this_phase"])
        self.assertFalse(summary["source_map_mutation_performed_by_this_phase"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_checklist(self) -> None:
        manifest = validate(require_private_checklist=True)
        self.assertEqual(manifest["summary"]["owner_22_group_count"], 22)
        self.assertEqual(manifest["summary"]["owner_22_group_response_row_count"], 113)
        self.assertFalse(manifest["summary"]["owner_group_decision_confirmed"])


if __name__ == "__main__":
    unittest.main()
