import unittest

from KMFA.tools.check_v013_s01_p1_preflight import validate_s01_p1_preflight


class TestV013S01P1Preflight(unittest.TestCase):
    def test_current_state_preflight_keeps_no_go_blockers_visible(self) -> None:
        result = validate_s01_p1_preflight()

        self.assertEqual(result["stage_phase"], "S01-P1")
        self.assertEqual(result["actual_lineage_rows"], 0)
        self.assertEqual(result["pending_reconciliation_count"], 12)
        self.assertEqual(result["d_grade_report_count"], 2)
        self.assertFalse(result["delivery_allowed"])


if __name__ == "__main__":
    unittest.main()
