import unittest

from KMFA.tools.check_lineage_completeness import validate_lineage_completeness_review


class LineageCompletenessReviewTests(unittest.TestCase):
    def test_current_lineage_gate_blocks_delivery_without_private_data(self) -> None:
        counts = validate_lineage_completeness_review()

        self.assertEqual(counts["field_lineage_records"], 1)
        self.assertEqual(counts["metric_lineage_records"], 1)
        self.assertEqual(counts["report_lineage_records"], 1)
        self.assertEqual(counts["manual_rerun_steps"], 8)


if __name__ == "__main__":
    unittest.main()
