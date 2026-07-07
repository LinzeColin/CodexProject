import json
import unittest

from KMFA.tools import v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_audit as phase
from KMFA.tools.check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_audit import (
    validate,
)


class ResidualDifferenceOwnerAgentDiagnosticBlockerAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = phase.generate(generated_at="2026-07-07T00:00:00+10:00", write_governance_event=False)

    def test_summary_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["prior_diagnostic_blocker_observation_count"], 1)
        self.assertEqual(summary["diagnostic_blocker_observation_count"], 2)
        self.assertFalse(summary["diagnostic_blocked_audit_threshold_met"])
        self.assertEqual(summary["diagnostic_response_blocker_count"], 72)
        self.assertEqual(summary["source_private_readiness_blocker_queue_item_count"], 72)
        self.assertEqual(summary["valid_diagnostic_response_count"], 0)
        self.assertEqual(summary["actionable_resolution_count"], 0)
        self.assertEqual(summary["open_residual_difference_count"], 72)

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "source_map_correction_ready",
            "source_map_correction_written_by_this_phase",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_ready",
            "full_raw_to_processed_value_comparison_complete",
            "business_value_consistency_verified",
            "formal_report_allowed",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_matrix_all_pass(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["blocker_audit_check_count"], 10)
        self.assertEqual(matrix["blocker_audit_check_pass_count"], 10)
        self.assertEqual(matrix["blocker_audit_check_fail_count"], 0)

    def test_private_outputs_are_ignored(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["private_audit_diagnostic_gitignored"])
        self.assertTrue(phase.PRIVATE_AUDIT_DIAGNOSTIC_PATH.exists())

    def test_public_evidence_has_no_forbidden_private_markers(self) -> None:
        forbidden = [
            "/Users/linzezhang/Downloads",
            "KMFA_MetaData",
            ".codex_private_runtime",
            "raw_file_name",
            "sheet_name",
            "raw_value",
            "target_slot_id",
            "value_fingerprint",
            ".xlsx",
            ".zip",
            ".pdf",
        ]
        for path in (
            phase.SUMMARY_PATH,
            phase.MANIFEST_PATH,
            phase.GO_NO_GO_PATH,
            phase.MATRIX_PATH,
            phase.REPORT_PATH,
            phase.GO_NO_GO_RECORD_PATH,
            phase.TEST_RESULTS_PATH,
        ):
            text = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{marker} leaked into {path}")

    def test_validator_passes_with_private_diagnostic(self) -> None:
        validate(require_private_diagnostic=True)

    def test_summary_json_is_parseable(self) -> None:
        parsed = json.loads(phase.SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(parsed["phase_id"], phase.PHASE_ID)


if __name__ == "__main__":
    unittest.main()
