from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_9" / "phase_9_1"


def load_stage9_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage9_regression_freeze")
    except ModuleNotFoundError:
        return None


class TestV024Stage9Phase91RegressionGuardrails(unittest.TestCase):
    def test_phase91_contract_defines_required_regression_rules(self) -> None:
        stage9 = load_stage9_module()
        self.assertIsNotNone(stage9, "stage_v024_stage9_regression_freeze module is required")
        self.assertTrue(hasattr(stage9, "build_v024_stage9_phase91_contract"))

        contract = stage9.build_v024_stage9_phase91_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 9")
        self.assertEqual(contract["stage_name"], "回归防线与交付冻结")
        self.assertEqual(contract["phase_id"], "9.1")
        self.assertEqual(contract["phase_name"], "回归规则")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["stage_8_github_main_uploaded_required"])
        self.assertEqual(contract["task_ids"], ["T9.1.1", "T9.1.2", "T9.1.3", "T9.1.4"])
        self.assertEqual(
            contract["required_guardrails"],
            [
                "old_ui_signature",
                "primary_entry_stack",
                "false_financial_zero",
                "mock_financial_data",
                "mechanical_copy",
                "dark_console_default",
            ],
        )
        self.assertFalse(contract["phase_9_2_started"])
        self.assertFalse(contract["phase_9_3_started"])
        self.assertFalse(contract["stage_9_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("Stage 9 Phase 9.2 delivery freeze", contract["explicitly_not_done"])

    def test_guardrail_evaluator_passes_against_current_runtime_files(self) -> None:
        stage9 = load_stage9_module()
        self.assertIsNotNone(stage9, "stage_v024_stage9_regression_freeze module is required")
        self.assertTrue(hasattr(stage9, "evaluate_v024_stage9_phase91_guardrails"))

        result = stage9.evaluate_v024_stage9_phase91_guardrails(ROOT).to_dict()

        self.assertEqual(result["schema"], "PFIV024Stage9Phase91GuardrailEvaluationV1")
        self.assertEqual(result["target_version"], "v0.2.4")
        self.assertEqual(result["primary_entry_count"], 10)
        self.assertEqual(result["mobile_primary_entry_count"], 10)
        self.assertEqual(result["primary_entry_labels"], stage9.PRIMARY_ENTRY_LABELS)
        self.assertEqual(result["legacy_alias_primary_entry_violations"], [])
        self.assertEqual(result["old_ui_signature_violations"], [])
        self.assertEqual(result["primary_entry_stack_violations"], [])
        self.assertEqual(result["false_financial_zero_violations"], [])
        self.assertEqual(result["mock_financial_data_violations"], [])
        self.assertTrue(result["old_ui_signature_test_passed"])
        self.assertTrue(result["primary_entry_stack_test_passed"])
        self.assertTrue(result["false_zero_test_passed"])
        self.assertTrue(result["mock_financial_data_test_passed"])
        self.assertTrue(result["mechanical_copy_guardrail_defined"])
        self.assertTrue(result["dark_console_default_guardrail_defined"])

    def test_phase91_evidence_pack_is_machine_readable(self) -> None:
        evidence_path = PHASE_DIR / "evidence.json"
        guardrail_path = PHASE_DIR / "regression_guardrails.json"
        terminal_path = PHASE_DIR / "terminal.log"
        changed_files_path = PHASE_DIR / "changed_files.txt"
        risk_path = PHASE_DIR / "risk_and_rollback.md"

        for path in (evidence_path, guardrail_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        guardrails = json.loads(guardrail_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage9Phase91RegressionGuardrailsEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3-repair")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["phase_id"], "9.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["stage_8_github_main_uploaded_verified"])
        self.assertFalse(evidence["phase_9_2_started"])
        self.assertFalse(evidence["phase_9_3_started"])
        self.assertFalse(evidence["stage_9_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)

        self.assertEqual(guardrails["schema"], "PFIV024Stage9Phase91GuardrailEvaluationV1")
        self.assertTrue(guardrails["all_guardrails_passed"])
        self.assertEqual(guardrails["old_ui_signature_violations"], [])
        self.assertEqual(guardrails["primary_entry_stack_violations"], [])
        self.assertEqual(guardrails["false_financial_zero_violations"], [])
        self.assertEqual(guardrails["mock_financial_data_violations"], [])


if __name__ == "__main__":
    unittest.main()
