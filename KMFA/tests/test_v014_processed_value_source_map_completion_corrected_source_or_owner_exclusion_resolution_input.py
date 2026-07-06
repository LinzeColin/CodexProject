from __future__ import annotations

import unittest

from KMFA.tools import (
    v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input as generator,
)
from KMFA.tools.check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input import (
    validate,
)


class CorrectedSourceOrOwnerExclusionResolutionInputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_private_template_is_prepared_for_36_unlinked_blockers(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["private_resolution_item_count"], 36)
        self.assertEqual(summary["private_pending_queue_count"], 36)
        self.assertEqual(summary["unlinked_application_blocker_count"], 36)
        self.assertEqual(summary["source_non_actionable_group_decision_count"], 3)
        self.assertTrue(summary["private_template_written"])
        self.assertTrue(summary["private_pending_queue_written"])
        self.assertTrue(summary["private_diagnostic_written"])
        self.assertTrue(summary["private_report_written"])

    def test_matrix_keeps_resolution_and_reconciliation_blocked(self) -> None:
        matrix = self.manifest["matrix"]
        self.assertEqual(matrix["decision_check_count"], 7)
        self.assertEqual(matrix["decision_pass_count"], 3)
        self.assertEqual(matrix["decision_fail_count"], 4)
        self.assertFalse(matrix["owner_resolution_input_present"])
        self.assertFalse(matrix["all_36_unlinked_blockers_resolved"])
        self.assertFalse(matrix["resolution_application_allowed"])
        self.assertFalse(matrix["full_reconciliation_allowed"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["owner_resolution_input_present"])
        self.assertFalse(summary["all_36_unlinked_blockers_resolved"])
        self.assertFalse(summary["resolution_application_allowed"])
        self.assertFalse(summary["resolution_application_performed_by_this_phase"])
        self.assertFalse(summary["source_map_mutation_performed_by_this_phase"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_boundary_excludes_raw_inbox_access(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_template(self) -> None:
        manifest = validate(require_private_template=True)
        self.assertEqual(manifest["summary"]["private_resolution_item_count"], 36)
        self.assertFalse(manifest["summary"]["full_reconciliation_allowed"])


if __name__ == "__main__":
    unittest.main()
