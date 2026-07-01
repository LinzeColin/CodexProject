import unittest

from KMFA.tools.check_part3_stages_07_09_review import (
    DEFAULT_MANIFEST,
    validate_part3_review,
)


class Part3Stages0709ReviewTests(unittest.TestCase):
    def test_part3_review_manifest_closes_stages_7_to_9_without_upload(self) -> None:
        counts = validate_part3_review(DEFAULT_MANIFEST)

        self.assertEqual(counts["stage_count"], 3)
        self.assertEqual(counts["phase_count"], 9)
        self.assertEqual(counts["required_stage_artifact_count"], 49)
        self.assertEqual(counts["required_baseline_ref_count"], 64)
        self.assertEqual(counts["part3_unit_tests"], 32)
        self.assertEqual(counts["full_kmfa_unit_tests"], 271)
        self.assertEqual(counts["open_review_finding_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)


if __name__ == "__main__":
    unittest.main()
