from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGE9_DIR = ROOT / "reports" / "pfi_v024" / "stage_9"
REVIEW_DIR = STAGE9_DIR / "whole_stage_review"
EXPECTED_PHASE_IDS = ["9.1", "9.2", "9.3"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_stage9_module():
    return importlib.import_module("pfi_v02.stage_v024_stage9_regression_freeze")


class TestV024Stage9WholeReviewContract(unittest.TestCase):
    def test_whole_stage_review_contract_is_bounded_and_non_upload(self) -> None:
        stage9 = load_stage9_module()
        self.assertTrue(hasattr(stage9, "build_v024_stage9_whole_review_contract"))

        contract = stage9.build_v024_stage9_whole_review_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 9")
        self.assertEqual(contract["stage_name"], "回归防线与交付冻结")
        self.assertEqual(contract["review_id"], "stage_9_whole_review")
        self.assertEqual(contract["current_run_unit"], "Stage 9 whole-stage review")
        self.assertTrue(contract["current_run_only"])
        self.assertEqual(contract["reviewed_phase_ids"], EXPECTED_PHASE_IDS)
        self.assertTrue(contract["phase_9_1_required"])
        self.assertTrue(contract["phase_9_2_required"])
        self.assertTrue(contract["phase_9_3_required"])
        self.assertTrue(contract["phase_9_3_user_confirmation_required"])
        self.assertEqual(contract["user_confirmation_source"], "chat_reply_1")
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["future_version_started"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])
        self.assertIn("future version work", contract["explicitly_not_done"])

    def test_whole_stage_review_artifacts_exist_and_show_pass_after_user_confirmation(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "STAGE9_WHOLE_STAGE_REVIEW.md",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "risk_and_rollback.md",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        self.assertEqual(evidence["schema"], "PFIV024Stage9WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["review_id"], "stage_9_whole_review")
        self.assertEqual(evidence["current_run_unit"], "Stage 9 whole-stage review")
        self.assertTrue(evidence["current_run_only"])
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_9_candidate_complete"])
        self.assertTrue(evidence["stage_9_whole_review_complete"])
        self.assertTrue(evidence["phase_9_3_user_confirmed"])
        self.assertEqual(evidence["user_confirmation_source"], "chat_reply_1")
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["future_version_started"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])

    def test_review_binds_guardrails_delivery_freeze_and_user_acceptance(self) -> None:
        phase91 = read_json(STAGE9_DIR / "phase_9_1" / "evidence.json")
        guardrails = read_json(STAGE9_DIR / "phase_9_1" / "regression_guardrails.json")
        phase92 = read_json(STAGE9_DIR / "phase_9_2" / "evidence.json")
        final_index = read_json(STAGE9_DIR / "phase_9_2" / "final_evidence_index.json")
        phase93 = read_json(STAGE9_DIR / "phase_9_3" / "evidence.json")
        review = read_json(REVIEW_DIR / "evidence.json")

        self.assertEqual(review["reviewed_phase_ids"], EXPECTED_PHASE_IDS)
        self.assertEqual(review["phase_statuses"], {
            "phase_9_1": "candidate_pass",
            "phase_9_2": "candidate_pass",
            "phase_9_3": "user_confirmed",
        })
        self.assertEqual(phase91["status"], "candidate_pass")
        self.assertEqual(phase92["status"], "candidate_pass")
        self.assertEqual(phase93["status"], "waiting_for_user_acceptance")
        self.assertTrue(guardrails["all_guardrails_passed"])
        self.assertEqual(guardrails["old_ui_signature_violations"], [])
        self.assertEqual(guardrails["primary_entry_stack_violations"], [])
        self.assertEqual(guardrails["false_financial_zero_violations"], [])
        self.assertEqual(guardrails["mock_financial_data_violations"], [])
        self.assertEqual(final_index["status"], "candidate_pass")
        self.assertTrue(final_index["stage_8_github_main_uploaded_verified"])
        self.assertTrue(final_index["stage_9_phase_9_1_guardrails_passed"])
        self.assertFalse(final_index["github_main_uploaded"])

    def test_stop_conditions_and_review_findings_are_fixed_before_upload(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        stop_conditions = evidence["stop_condition_audit"]
        findings = evidence["review_findings"]

        self.assertEqual(stop_conditions["old_ui_signature_regression"], "absent")
        self.assertEqual(stop_conditions["primary_entry_stack_regression"], "absent")
        self.assertEqual(stop_conditions["false_financial_zero_visible"], "absent")
        self.assertEqual(stop_conditions["forbidden_financial_data_added"], "absent")
        self.assertEqual(stop_conditions["manual_acceptance_missing"], "absent")
        self.assertEqual(stop_conditions["final_evidence_index_missing"], "absent")
        self.assertEqual(stop_conditions["stage_9_upload_executed_early"], "absent")
        self.assertEqual(stop_conditions["future_version_started"], "absent")

        self.assertGreaterEqual(len(findings), 3)
        for finding in findings:
            self.assertIn(finding["severity"], {"P1", "P2", "P3"})
            self.assertEqual(finding["status"], "fixed")
            self.assertTrue(finding["fix"])
            self.assertTrue(finding["verification"])

        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["pytest stage9 whole review red run"], "expected_fail")
        self.assertEqual(command_status["pytest stage9 whole review contract"], "pass")
        self.assertEqual(command_status["pytest stage9 phase regression"], "pass")
        self.assertEqual(command_status["pytest stage8 upload boundary"], "pass")
        self.assertEqual(command_status["python py_compile stage9 contract"], "pass")
        self.assertEqual(command_status["json evidence checks"], "pass")
        self.assertEqual(command_status["changed files reconciliation"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

        self.assertIn("GitHub main upload", evidence["remaining_gates"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])
        self.assertNotIn("future version work", evidence["remaining_gates"])

    def test_docs_and_status_files_reflect_whole_review_without_upload(self) -> None:
        stage_doc = (ROOT / "docs" / "pfi_v024" / "STAGE9_REGRESSION_FREEZE.md").read_text(encoding="utf-8")
        review_doc = (ROOT / "docs" / "pfi_v024" / "STAGE9_WHOLE_STAGE_REVIEW.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")

        self.assertIn("Stage 9 Whole-stage Review", stage_doc)
        self.assertIn("Stage 9 whole-stage review pass", stage_doc)
        self.assertIn("Stage 9 whole-stage review - 复审并解决暴露问题", run_contract)
        self.assertIn("Stage 9 whole-stage review pass", readme)
        self.assertIn("Stage 9 whole-stage review pass", handoff)
        self.assertIn("GitHub main upload 仍未执行", review_doc)
        self.assertIn("future version 未开始", review_doc)
        self.assertNotIn("GitHub main uploaded", stage_doc)
        self.assertNotIn("future version started", stage_doc)


if __name__ == "__main__":
    unittest.main()
