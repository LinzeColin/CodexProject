import unittest

from KMFA.tools.check_part5_stages_13_15_review import (
    DEFAULT_MANIFEST,
    validate_part5_review,
)


class Part5Stages1315ReviewTests(unittest.TestCase):
    def test_part5_review_manifest_closes_stages_13_to_15_without_upload(self) -> None:
        counts = validate_part5_review(DEFAULT_MANIFEST)

        self.assertEqual(counts["stage_count"], 3)
        self.assertEqual(counts["phase_count"], 9)
        self.assertEqual(counts["required_stage_artifact_count"], 49)
        self.assertEqual(counts["required_baseline_ref_count"], 69)
        self.assertEqual(counts["part5_unit_tests"], 56)
        self.assertEqual(counts["full_kmfa_unit_tests"], 273)
        self.assertEqual(counts["open_review_finding_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)


if __name__ == "__main__":
    unittest.main()
