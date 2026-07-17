from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s19_p2_policy_eligibility as builder


class PolicyEligibilityArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_registry_is_versioned_and_stale_rules_are_blocked(self) -> None:
        value = self.load(builder.POLICY_REGISTRY_PATH)
        self.assertEqual(value["policy_count"], 6)
        self.assertEqual(value["current_policy_count"], 5)
        self.assertEqual(value["blocked_policy_count"], 1)
        self.assertEqual(value["official_source_count"], 6)
        self.assertEqual(value["versioned_rule_count"], 6)
        self.assertEqual(value["expired_policy_deterministic_conclusion_count"], 0)

    def test_readiness_has_six_categories_and_no_eligibility_conclusion(self) -> None:
        value = self.load(builder.READINESS_PATH)
        self.assertEqual(value["category_count"], 6)
        self.assertEqual(value["evidence_item_count"], 12)
        self.assertEqual((value["available_evidence_count"], value["missing_evidence_count"], value["review_evidence_count"]), (7, 3, 2))
        self.assertEqual(value["formal_eligibility_conclusion_count"], 0)
        self.assertEqual(value["fabricated_evidence_count"], 0)
        self.assertEqual(value["material_packaging_assistance_count"], 0)

    def test_task_contract_requires_source_and_owner(self) -> None:
        value = self.load(builder.TASK_CONTRACT_PATH)
        self.assertEqual(value["task_count"], 6)
        self.assertEqual(value["owner_due_target_count"], 6)
        self.assertEqual((value["missing_source_task_count"], value["source_review_task_count"], value["ready_task_count"]), (3, 2, 1))
        self.assertEqual(value["source_gate_enabled_count"], 6)
        self.assertEqual(value["fabrication_or_packaging_allowed_count"], 0)

    def test_browser_and_human_evidence_exist(self) -> None:
        value = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual(value["browser_flow_count"], 8)
        self.assertEqual(value["visual_evidence_count"], 6)
        self.assertEqual(value["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)

    def test_manifest_uses_receipt_bound_acceptance(self) -> None:
        value = self.load(builder.MANIFEST_PATH)
        final, run_id, validation_head = builder.final_binding(builder.receipts())
        self.assertEqual(value["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(value["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(value["overall_accepted_phase_count"], 54 if final else 53)
        self.assertTrue(value["s19_p2_started"])
        self.assertEqual(value["s19_p2_completed"], final)
        self.assertEqual(value["s19_p3_entry_allowed"], final)
        self.assertFalse(value["s19_p3_started"])
        self.assertEqual(value["validation_run_id"], run_id)
        self.assertEqual(value["validation_head"], validation_head)
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
