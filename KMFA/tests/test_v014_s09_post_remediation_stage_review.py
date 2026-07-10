import unittest

from KMFA.tools.check_v014_s09_post_remediation_stage_review import (
    validate_v014_s09_post_remediation_stage_review,
)
from KMFA.tools.v014_s09_post_remediation_stage_review import normalize_stage_status_records


class TestV014S09PostRemediationStageReview(unittest.TestCase):
    def test_status_normalization_adds_only_required_governance_fields(self) -> None:
        records = [
            {
                "event_id": "EVENT-1",
                "event_time": "2026-07-10T00:00:00+10:00",
                "phase_id": "V014_EVENT_PHASE",
                "status": "completed",
            },
            {
                "record_type": "stage_phase_status",
                "phase_id": "V014_STATUS_PHASE",
                "status": "completed",
                "updated_at": "2026-07-10T00:00:00+10:00",
            },
            {
                "record_type": "stage_phase_status",
                "phase_id": "V014_COMPLETE_PHASE",
                "status": "completed",
                "updated_at": "2026-07-10T00:00:00+10:00",
                "fact_level": "EXTRACTED",
            },
        ]

        normalized, changed_count = normalize_stage_status_records(records)

        self.assertEqual(changed_count, 2)
        self.assertEqual(normalized[0]["record_type"], "v014_phase_event")
        self.assertEqual(normalized[0]["updated_at"], records[0]["event_time"])
        self.assertEqual(normalized[0]["fact_level"], "EXTRACTED")
        self.assertEqual(normalized[1]["fact_level"], "EXTRACTED")
        self.assertEqual(normalized[2], records[2])

    def test_post_remediation_review_closes_findings_without_opening_release(self) -> None:
        result = validate_v014_s09_post_remediation_stage_review(require_private_evidence=True)

        self.assertEqual(result["stage_id"], "S09")
        self.assertEqual(result["review_scope"], "v014_s09_post_remediation_stage_review_only")
        self.assertEqual(result["phase_results"], {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"})
        self.assertEqual(result["cost_category_count"], 9)
        self.assertEqual(result["cost_component_materialization_count"], 8)
        self.assertEqual(result["authority_system_overwrite_allowed_count"], 0)
        self.assertEqual(result["reconciliation_record_count"], 12)
        self.assertEqual(result["human_readable_reconciliation_count"], 12)
        self.assertEqual(result["queue_closed_or_excluded_count"], 69)
        self.assertEqual(result["open_final_difference_accepted_count"], 3)
        self.assertEqual(result["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(result["zero_delta_reconciliation_count"], 2)
        self.assertEqual(result["incomplete_reconciliation_count"], 1)
        self.assertEqual(result["fixed_review_finding_count"], 11)
        self.assertEqual(result["open_review_finding_count"], 0)
        self.assertEqual(result["full_regression_test_count"], 1200)
        self.assertEqual(result["full_regression_failure_count"], 0)
        self.assertEqual(result["full_regression_result"], "OK")
        self.assertEqual(result["decision"], "NO_GO")
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertFalse(result["s10_p1_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])
        self.assertFalse(result["business_execution_performed"])
        self.assertTrue(result["raw_snapshot_exact_match"])


if __name__ == "__main__":
    unittest.main()
