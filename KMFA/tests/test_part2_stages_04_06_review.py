import unittest

from KMFA.tools.check_part2_stages_04_06_review import (
    DEFAULT_MANIFEST,
    validate_part2_review,
)


class Part2Stages0406ReviewTests(unittest.TestCase):
    def test_part2_review_manifest_closes_stages_4_to_6_without_upload(self) -> None:
        counts = validate_part2_review(DEFAULT_MANIFEST)

        self.assertEqual(counts["stage_count"], 3)
        self.assertEqual(counts["phase_count"], 9)
        self.assertEqual(counts["required_stage_artifact_count"], 54)
        self.assertEqual(counts["required_baseline_ref_count"], 29)
        self.assertEqual(counts["part2_unit_tests"], 59)
        self.assertEqual(counts["full_kmfa_unit_tests"], 270)
        self.assertEqual(counts["open_review_finding_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)


if __name__ == "__main__":
    unittest.main()
