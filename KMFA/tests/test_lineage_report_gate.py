import unittest

from KMFA.tools.check_lineage_report_gate import validate_lineage_report_gate


class LineageReportGateTests(unittest.TestCase):
    def test_current_lineage_report_gate_blocks_release_and_backup_is_no_go_only(self) -> None:
        summary = validate_lineage_report_gate()

        self.assertEqual(summary["lineage_summary"]["field_actual_lineage_record_count"], 0)
        self.assertEqual(summary["lineage_summary"]["metric_actual_lineage_record_count"], 0)
        self.assertEqual(summary["lineage_summary"]["report_actual_lineage_record_count"], 0)
        self.assertEqual(summary["report_grade_summary"]["report_grade_distribution"], {"D": 2})
        self.assertEqual(summary["reconciliation_summary"]["pending_resolution_count"], 12)
        self.assertEqual(summary["report_export_summary"]["formal_report_allowed_count"], 0)


if __name__ == "__main__":
    unittest.main()
