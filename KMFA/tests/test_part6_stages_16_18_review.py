import unittest

from KMFA.tools.check_part6_stages_16_18_review import (
    DEFAULT_MANIFEST,
    validate_part6_review,
)


class Part6Stages1618ReviewTests(unittest.TestCase):
    def test_part6_review_manifest_closes_stages_16_to_18_without_upload_or_delivery(self) -> None:
        counts = validate_part6_review(DEFAULT_MANIFEST)

        self.assertEqual(counts["stage_count"], 3)
        self.assertEqual(counts["phase_count"], 9)
        self.assertEqual(counts["required_stage_artifact_count"], 48)
        self.assertEqual(counts["required_baseline_ref_count"], 74)
        self.assertEqual(counts["part6_unit_tests"], 62)
        self.assertEqual(counts["full_kmfa_unit_tests"], 274)
        self.assertEqual(counts["open_review_finding_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)
        self.assertEqual(counts["delivery_allowed_count"], 0)


if __name__ == "__main__":
    unittest.main()
