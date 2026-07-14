import unittest
from pathlib import Path

from KMFA.tools.check_v014_one_time_github_main_upload import (
    validate_v014_one_time_github_main_upload,
)


class V014OneTimeGithubMainUploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validate_v014_one_time_github_main_upload()

    def test_identity_and_source_review_are_locked(self) -> None:
        self.assertEqual(self.manifest["project_id"], "KMFA")
        self.assertEqual(self.manifest["stage_id"], "S01-S18")
        self.assertEqual(self.manifest["phase_id"], "V014_ONE_TIME_GITHUB_MAIN_UPLOAD")
        self.assertEqual(
            self.manifest["task_id"],
            "KMFA-V014-ONE-TIME-GITHUB-MAIN-UPLOAD-20260713",
        )
        self.assertEqual(
            self.manifest["acceptance_id"],
            "ACC-V014-ONE-TIME-GITHUB-MAIN-UPLOAD",
        )
        self.assertTrue(self.manifest["source_review"]["final_overall_review_validated"])
        self.assertEqual(self.manifest["source_review"]["current_stage_validator_pass_count"], 18)
        self.assertEqual(self.manifest["source_review"]["open_review_finding_count"], 0)

    def test_exactly_one_public_safe_main_push_is_bound_to_this_commit(self) -> None:
        upload = self.manifest["upload_closure"]
        self.assertEqual(self.manifest["status"], "uploaded_to_github_main_public_safe")
        self.assertEqual(self.manifest["target_ref"], "refs/heads/main")
        self.assertEqual(upload["upload_closure_commit"], "recorded_by_commit_containing_this_file")
        self.assertEqual(upload["push_count_authorized"], 1)
        self.assertTrue(upload["github_upload_performed_by_this_phase"])
        self.assertFalse(upload["force_push_allowed"])
        self.assertTrue(upload["post_push_remote_parity_required"])

    def test_business_and_app_gates_remain_closed(self) -> None:
        release = self.manifest["release_state"]
        self.assertEqual(release["current_data_quality_grade"], "Q4")
        self.assertEqual(release["current_report_grade"], "D")
        self.assertEqual(release["decision"], "NO_GO")
        self.assertEqual(release["difference_state"], "3-9-2-1")
        self.assertFalse(release["lineage_full_check_complete"])
        self.assertFalse(release["delivery_allowed"])
        self.assertFalse(release["official_report_release_allowed"])
        self.assertFalse(release["business_execution_allowed"])
        self.assertFalse(self.manifest["phase_boundaries"]["app_reinstall_performed"])
        self.assertEqual(self.manifest["next_phase"], "V014_APP_REINSTALL_AND_PARITY")

    def test_public_repository_and_raw_boundaries_are_all_false(self) -> None:
        for key, value in self.manifest["public_repo_safety"].items():
            with self.subTest(key=key):
                self.assertFalse(value)
        for key, value in self.manifest["raw_data_boundary"].items():
            with self.subTest(key=key):
                self.assertFalse(value)
        self.assertFalse(self.manifest["legacy_owner_plaintext_policy_applies_to_this_upload"])

    def test_governance_and_evidence_references_exist(self) -> None:
        for ref in self.manifest["source_refs"] + self.manifest["evidence_refs"]:
            with self.subTest(ref=ref):
                self.assertTrue(Path(ref).exists())


if __name__ == "__main__":
    unittest.main()
