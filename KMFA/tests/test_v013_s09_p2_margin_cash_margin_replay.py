import unittest

from KMFA.tools.check_v013_s09_p2_margin_cash_margin_replay import (
    validate_v013_s09_p2_margin_cash_margin_replay,
)
from KMFA.tools.v013_s09_p2_margin_cash_margin_replay import generate


class TestV013S09P2MarginCashMarginReplay(unittest.TestCase):
    def test_replay_locks_margin_cash_margin_without_reconciliation_review_or_upload(self) -> None:
        generate()
        result = validate_v013_s09_p2_margin_cash_margin_replay()

        self.assertEqual(result["stage_id"], "S09")
        self.assertEqual(result["phase_id"], "S09-P2")
        self.assertEqual(result["phase_scope"], "v013_s09_p2_margin_cash_margin_replay_only")
        self.assertEqual(result["required_margin_metric_count"], 4)
        self.assertEqual(result["project_cost_fact_record_count"], 4)
        self.assertEqual(result["margin_record_count"], 4)
        self.assertEqual(result["difference_summary_count"], 12)
        self.assertEqual(result["authority_field_group_count"], 8)
        self.assertEqual(result["upstream_manual_review_queue_count"], 3)
        self.assertEqual(result["upstream_unresolved_difference_count"], 1)
        self.assertEqual(result["zero_delta_fail_count"], 1)
        self.assertEqual(result["blocked_quality_result_count"], 2)
        self.assertEqual(result["authority_system_overwrite_allowed_count"], 0)
        self.assertEqual(result["public_amount_values_committed_count"], 0)
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["s09_p3_performed"])
        self.assertFalse(result["stage9_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("S09-P3", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
