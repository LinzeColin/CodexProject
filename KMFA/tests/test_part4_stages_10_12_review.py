import unittest

from KMFA.tools.check_part4_stages_10_12_review import (
    DEFAULT_MANIFEST,
    validate_part4_review,
)


class Part4Stages1012ReviewTests(unittest.TestCase):
    def test_part4_review_manifest_closes_stages_10_to_12_without_upload(self) -> None:
        counts = validate_part4_review(DEFAULT_MANIFEST)

        self.assertEqual(counts["stage_count"], 3)
        self.assertEqual(counts["phase_count"], 9)
        self.assertEqual(counts["required_stage_artifact_count"], 52)
        self.assertEqual(counts["required_baseline_ref_count"], 55)
        self.assertEqual(counts["part4_unit_tests"], 53)
        self.assertEqual(counts["full_kmfa_unit_tests"], 272)
        self.assertEqual(counts["open_review_finding_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)


if __name__ == "__main__":
    unittest.main()
