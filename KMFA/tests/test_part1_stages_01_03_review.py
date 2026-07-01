import unittest

from KMFA.tools.check_part1_stages_01_03_review import (
    DEFAULT_MANIFEST,
    validate_part1_review,
)


class Part1Stages0103ReviewTests(unittest.TestCase):
    def test_part1_review_manifest_closes_stages_1_to_3_without_upload(self) -> None:
        counts = validate_part1_review(DEFAULT_MANIFEST)

        self.assertEqual(counts["stage_count"], 3)
        self.assertEqual(counts["phase_count"], 9)
        self.assertEqual(counts["required_stage_artifact_count"], 25)
        self.assertEqual(counts["required_baseline_ref_count"], 18)
        self.assertEqual(counts["part1_unit_tests"], 12)
        self.assertEqual(counts["full_kmfa_unit_tests"], 269)
        self.assertEqual(counts["open_review_finding_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)


if __name__ == "__main__":
    unittest.main()
