import unittest

from KMFA.tools.check_v014_s09_p3_scope_reconciliation import (
    validate_v014_s09_p3_scope_reconciliation,
)
from KMFA.tools.v014_s09_p3_scope_reconciliation import generate


class TestV014S09P3ScopeReconciliation(unittest.TestCase):
    def test_locks_scope_reconciliation_without_review_rerun_or_upload(self) -> None:
        generate()
        result = validate_v014_s09_p3_scope_reconciliation()

        self.assertEqual(result["stage_id"], "S09")
        self.assertEqual(result["phase_id"], "S09-P3")
        self.assertEqual(result["phase_scope"], "v014_s09_p3_scope_reconciliation_only")
        self.assertEqual(result["reconciliation_record_count"], 12)
        self.assertEqual(result["domain_control_count"], 6)
        self.assertEqual(result["confirmed_resolution_count"], 0)
        self.assertEqual(result["pending_resolution_count"], 12)
        self.assertEqual(result["upstream_margin_record_count"], 4)
        self.assertEqual(result["source_difference_summary_count"], 12)
        self.assertEqual(result["required_reconciliation_domain_count"], 6)
        self.assertEqual(result["reconciliation_records_by_domain"]["authority_pdf_excel_vs_system_recomputed"], 8)
        self.assertEqual(result["reconciliation_records_by_domain"]["bank_collection_vs_receivable_aging"], 4)
        self.assertFalse(result["derived_metric_rerun_allowed"])
        self.assertFalse(result["formal_report_rerun_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["stage9_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertFalse(result["raw_inbox_read_performed"])
        self.assertFalse(result["raw_inbox_mutation_performed"])
        self.assertIn("Stage 9 review", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])
        self.assertIn("Stage 1-18", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
