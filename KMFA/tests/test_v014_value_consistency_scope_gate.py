import unittest

from KMFA.tools.check_v014_value_consistency_scope_gate import (
    validate_v014_value_consistency_scope_gate,
)
from KMFA.tools.v014_value_consistency_scope_gate import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_ID,
    generate,
)


class V014ValueConsistencyScopeGateTests(unittest.TestCase):
    def test_generate_preview_locks_scope_without_claiming_value_match(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:30+10:00", write=False)

        self.assertEqual(manifest["phase_id"], PHASE_ID)
        self.assertEqual(manifest["task_id"], TASK_ID)
        self.assertEqual(manifest["acceptance_ids"], [ACCEPTANCE_ID])

        summary = manifest["value_consistency_summary"]
        self.assertTrue(summary["authoritative_raw_baseline_locked"])
        self.assertTrue(summary["value_consistency_scope_locked"])
        self.assertTrue(summary["raw_inbox_mutation_guard_locked"])
        self.assertTrue(summary["difference_report_required_on_repeated_mismatch"])
        self.assertFalse(summary["raw_value_matching_performed"])
        self.assertFalse(summary["processed_data_reconciliation_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])

        scope_matrix = manifest["scope_matrix"]
        self.assertEqual(scope_matrix["lane_count"], 6)
        self.assertEqual({lane["lane_id"] for lane in scope_matrix["lanes"]}, {"VC-L01", "VC-L02", "VC-L03", "VC-L04", "VC-L05", "VC-L06"})

        difference_contract = manifest["difference_report_contract"]
        self.assertTrue(difference_contract["final_goal_closeout_must_include_difference_report_if_triggered"])
        self.assertEqual(difference_contract["minimum_independent_validation_passes"], 3)
        self.assertFalse(difference_contract["raw_inbox_mutation_allowed"])

        go_no_go = manifest["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertFalse(go_no_go["raw_value_matching_performed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])

    def test_validate_committed_gate_with_private_diagnostic(self) -> None:
        validated = validate_v014_value_consistency_scope_gate(require_private_diagnostic=True)

        self.assertEqual(validated["phase_id"], PHASE_ID)
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")
        self.assertTrue(validated["value_consistency_summary"]["value_consistency_scope_locked"])
        self.assertTrue(validated["value_consistency_summary"]["difference_report_required_on_repeated_mismatch"])
        self.assertFalse(validated["value_consistency_summary"]["business_value_consistency_verified"])
        self.assertFalse(validated["github_upload_performed"])


if __name__ == "__main__":
    unittest.main()
