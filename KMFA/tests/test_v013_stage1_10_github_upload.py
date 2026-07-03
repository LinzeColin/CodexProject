import unittest

from KMFA.tools.check_v013_stage1_10_github_upload import (
    validate_v013_stage1_10_github_upload,
)


class TestV013Stage110GithubUpload(unittest.TestCase):
    def test_upload_gate_is_public_safe_and_ready_for_main_push(self) -> None:
        result = validate_v013_stage1_10_github_upload()

        self.assertEqual(result["schema_version"], "kmfa.v013_stage1_10_github_upload_manifest.v1")
        self.assertEqual(result["project_id"], "KMFA")
        self.assertEqual(result["upload_id"], "KMFA-V013-STAGE1-10-GITHUB-UPLOAD-20260703")
        self.assertEqual(result["target"], "LinzeColin/CodexProject main")
        self.assertEqual(result["source_scope"], "v0.1.3 Stage 1-10 batch overall review")
        self.assertEqual(result["status"], "ready_to_push_github_main_public_safe")
        self.assertTrue(result["git_integration"]["rebased_onto_origin_main"])
        self.assertTrue(result["git_integration"]["origin_main_is_ancestor_of_upload_head"])
        self.assertEqual(result["review_state"]["stage_count"], 10)
        self.assertEqual(result["review_state"]["open_batch_finding_count"], 0)
        self.assertFalse(result["review_state"]["github_upload_performed_before_this_gate"])
        self.assertFalse(result["decision_state"]["delivery_allowed"])
        self.assertFalse(result["decision_state"]["formal_report_allowed"])
        self.assertFalse(result["decision_state"]["business_execution_allowed"])
        self.assertFalse(result["public_repo_safety"]["raw_business_data_uploaded"])
        self.assertFalse(result["public_repo_safety"]["credentials_committed"])
        self.assertIn("push", result["validation_summary"])
        self.assertIn("post_push_parity", result["validation_summary"])


if __name__ == "__main__":
    unittest.main()
