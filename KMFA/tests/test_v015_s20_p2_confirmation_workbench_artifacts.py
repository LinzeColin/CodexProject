from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s20_p2_confirmation_workbench as builder


class ConfirmationWorkbenchArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_problem_list_is_business_only_and_sorted(self) -> None:
        value = self.load(builder.ISSUE_LIST_PATH)
        self.assertEqual((value["business_issue_count"], value["default_issue_count"]), (6, 5))
        self.assertEqual(value["governance_log_count_in_main_list"], 0)
        self.assertEqual(value["sort_order"], ["impact_desc", "urgency_desc", "source_asc", "owner_asc"])
        self.assertTrue(value["default_requires_user_action_only"])

    def test_detail_and_control_event_contracts_close_the_boundaries(self) -> None:
        detail = self.load(builder.DETAIL_PATH)
        control = self.load(builder.CONTROL_EVENT_PATH)
        self.assertEqual((detail["detail_count"], detail["side_by_side_field_group_count"]), (5, 2))
        self.assertFalse(detail["technical_details_default_expanded"])
        self.assertFalse(detail["raw_value_edit_allowed"])
        self.assertEqual((control["allowed_action_role_count"], control["control_event_type_count"]), (2, 2))
        self.assertTrue(control["append_only"])
        self.assertTrue(control["hash_chain_required"])
        self.assertTrue(control["idempotency_required"])
        self.assertTrue(control["impact_preview_required"])
        for key in (
            "high_impact_without_preview_success_count", "undo_without_preview_success_count",
            "raw_source_mutation_count", "fact_layer_mutation_count",
            "s20_p3_recalculation_count", "report_refresh_count",
        ):
            self.assertEqual(control[key], 0, key)

    def test_checks_browser_human_and_manifest_evidence(self) -> None:
        checks = self.load(builder.PUBLIC_CHECKS_PATH)
        browser = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual((checks["check_count"], checks["pass_count"], checks["fail_count"]), (55, 55, 0))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"]), (7, 6))
        self.assertEqual(browser["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)
        manifest = self.load(builder.MANIFEST_PATH)
        final, run_id, head = builder.final_binding(builder.receipts())
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 57 if final else 56)
        self.assertEqual((manifest["validation_run_id"], manifest["validation_head"]), (run_id, head))
        self.assertFalse(manifest["s20_p3_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
