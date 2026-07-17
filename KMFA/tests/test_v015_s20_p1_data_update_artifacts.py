from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s20_p1_data_update as builder


class DataUpdateArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_three_step_preview_and_confirmation_contract(self) -> None:
        value = self.load(builder.WORKFLOW_PATH)
        self.assertEqual((value["step_count"], value["source_option_count"], value["entity_option_count"]), (3, 3, 3))
        self.assertEqual((value["scope_option_count"], value["supported_extension_count"]), (4, 8))
        self.assertEqual((value["preview_field_count"], value["auto_detected_field_count"]), (5, 1))
        self.assertTrue(value["explicit_confirmation_required"])
        self.assertTrue(value["back_allowed_before_commit"])
        self.assertTrue(value["cancel_allowed_before_commit"])
        self.assertFalse(value["raw_write_allowed"])

    def test_progress_is_recoverable_and_not_fabricated(self) -> None:
        value = self.load(builder.RECOVERY_PATH)
        self.assertEqual((value["progress_stage_count"], value["actual_completed_stage_count"], value["not_executed_stage_count"]), (7, 5, 2))
        self.assertTrue(value["refresh_preview_restored"])
        self.assertEqual(value["resume_status"], "COMPLETED")
        self.assertTrue(value["resumed_from_checkpoint"])
        self.assertFalse(value["partial_commit_visible"])
        self.assertFalse(value["recalculation_executed"])
        self.assertFalse(value["report_refresh_executed"])
        self.assertEqual(value["progress_fabrication_count"], 0)

    def test_checks_browser_human_and_manifest_evidence(self) -> None:
        checks = self.load(builder.PUBLIC_CHECKS_PATH)
        browser = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual((checks["check_count"], checks["pass_count"], checks["fail_count"]), (59, 59, 0))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"]), (7, 4))
        self.assertEqual(browser["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)
        manifest = self.load(builder.MANIFEST_PATH)
        final, run_id, head = builder.final_binding(builder.receipts())
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 56 if final else 55)
        self.assertEqual((manifest["validation_run_id"], manifest["validation_head"]), (run_id, head))
        self.assertEqual(manifest["progress_fabrication_count"], 0)
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
