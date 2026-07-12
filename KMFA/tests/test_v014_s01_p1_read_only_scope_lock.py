import unittest

from KMFA.tools.check_v014_s01_p1_read_only_scope_lock import (
    validate_v014_s01_p1_read_only_scope_lock,
)


class TestV014S01P1ReadOnlyScopeLock(unittest.TestCase):
    def test_v14_s01_p1_locks_read_only_scope_without_raw_or_upload(self) -> None:
        result = validate_v014_s01_p1_read_only_scope_lock()

        self.assertEqual(result["schema_version"], "kmfa.v014_s01_p1_read_only_scope_lock.v1")
        self.assertEqual(result["version"], "0.1.4")
        self.assertEqual(result["stage_phase"], "S01-P1")
        self.assertEqual(result["status"], "completed_validated_local_only_no_go_upload_deferred")
        self.assertEqual(result["scope_lock"]["phase_scope"], "read_only_plan_and_scope_lock")
        self.assertFalse(result["scope_lock"]["business_code_modified"])
        self.assertFalse(result["scope_lock"]["github_upload_this_phase"])
        self.assertEqual(result["scope_lock"]["next_phase"], "S01-P2")
        self.assertFalse(result["scope_lock"]["next_phase_started"])
        self.assertIn("main_worktree/CodexProject/kmfa", result["path_policy"]["canonical_worktree_path"])
        self.assertFalse(result["path_policy"]["standalone_or_old_path_used"])
        self.assertEqual(result["v14_gates"]["raw_data_root"], "/Users/linzezhang/Downloads/KMFA_MetaData")
        self.assertEqual(result["v14_gates"]["html_audit_pass"], 54)
        self.assertEqual(result["v14_gates"]["html_audit_warn"], 0)
        self.assertEqual(result["v14_gates"]["html_audit_fail"], 0)
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_filenames_committed"])
        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["formal_report_allowed"])
        self.assertFalse(result["release_state"]["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
