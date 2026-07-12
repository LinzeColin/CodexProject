from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_private_corrected_source_or_owner_resolution_intake import (
    validate,
)


class PrivateCorrectedSourceOrOwnerResolutionIntakeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_intake_contract_is_prepared_without_authorized_input(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertFalse(summary["owner_approved_resolution_input_present"])
        self.assertFalse(summary["corrected_private_source_package_present"])
        self.assertTrue(summary["owner_approved_resolution_intake_template_prepared"])
        self.assertEqual(summary["template_track_count"], 5)
        self.assertEqual(summary["private_decision_queue_count"], 113)
        self.assertEqual(summary["blocked_private_decision_count"], 113)
        self.assertEqual(summary["requires_corrected_source_or_owner_exclusion_count"], 36)
        self.assertEqual(summary["requires_private_disambiguation_count"], 77)

    def test_matrix_keeps_resolution_and_reconciliation_blocked(self) -> None:
        matrix = self.manifest["intake_matrix"]
        self.assertEqual(matrix["intake_check_count"], 5)
        self.assertEqual(matrix["intake_pass_count"], 1)
        self.assertEqual(matrix["intake_fail_count"], 4)
        self.assertFalse(matrix["owner_approved_resolution_input_present"])
        self.assertFalse(matrix["corrected_private_source_package_present"])
        self.assertFalse(matrix["resolution_application_allowed"])
        self.assertFalse(matrix["full_reconciliation_allowed"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["resolution_application_allowed"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["full_raw_to_processed_reconciliation_performed_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["processed_data_reconciliation_performed"])
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
        self.assertEqual(manifest["summary"]["private_pending_queue_count"], 113)
        self.assertFalse(manifest["summary"]["full_reconciliation_allowed"])


if __name__ == "__main__":
    unittest.main()
