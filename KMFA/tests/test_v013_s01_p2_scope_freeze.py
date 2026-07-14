import unittest

from KMFA.tools.check_v013_s01_p2_scope_freeze import validate_s01_p2_scope_freeze


class TestV013S01P2ScopeFreeze(unittest.TestCase):
    def test_scope_freeze_locks_no_go_boundaries(self) -> None:
        result = validate_s01_p2_scope_freeze()

        self.assertEqual(result["stage_phase"], "S01-P2")
        self.assertEqual(result["phase_scope"], "scope_freeze_only")
        self.assertEqual(result["inherited_blockers"]["actual_lineage_rows"], 0)
        self.assertEqual(result["inherited_blockers"]["pending_reconciliation_count"], 12)
        self.assertEqual(result["inherited_blockers"]["d_grade_report_count"], 2)
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["stage_review_scope_included"])
        self.assertFalse(result["github_upload_this_phase"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertFalse(result["external_v013_roadmap_available"])
        self.assertEqual(result["raw_data_boundary"]["local_raw_data_dir"], "/Users/linzezhang/Downloads/KMFA_MetaData")
        self.assertFalse(result["raw_data_boundary"]["codex_modify_allowed"])
        self.assertFalse(result["raw_data_boundary"]["github_commit_allowed"])


if __name__ == "__main__":
    unittest.main()
