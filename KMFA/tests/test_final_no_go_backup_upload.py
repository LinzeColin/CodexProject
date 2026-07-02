import unittest

from KMFA.tools.check_final_no_go_backup_upload import validate_final_no_go_backup_upload


class FinalNoGoBackupUploadTests(unittest.TestCase):
    def test_final_backup_is_no_go_governance_only(self) -> None:
        manifest = validate_final_no_go_backup_upload()

        self.assertEqual(manifest["decision_state"]["go_no_go"], "NO_GO")
        self.assertFalse(manifest["decision_state"]["delivery_allowed"])
        self.assertFalse(manifest["decision_state"]["release_claim_allowed"])
        self.assertTrue(manifest["backup_policy"]["no_go_governance_backup_only"])
        self.assertFalse(manifest["backup_policy"]["delivery_claim_allowed"])
        self.assertFalse(manifest["public_repo_safety"]["raw_business_data_uploaded"])


if __name__ == "__main__":
    unittest.main()
