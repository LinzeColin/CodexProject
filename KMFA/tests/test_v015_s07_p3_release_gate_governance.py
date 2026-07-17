from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s07_p3_release_gate as builder


PROJECT_ROOT = Path("KMFA")
FORMULA_ID = "FORM-KMFA-V015-S07-P3-RELEASE-GATE-001"
PARAMETER_IDS = {f"PARAM-KMFA-{value}" for value in range(1999, 2008)}


class S07P3ReleaseGateGovernanceTests(unittest.TestCase):
    def test_registry_bindings_and_counts(self) -> None:
        governance = PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        models = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_models = (PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if row["parameter_id"] in PARAMETER_IDS]
        self.assertEqual({row["parameter_id"] for row in rows}, PARAMETER_IDS)
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(row["model_id"] == "MOD-KMFA-COST-001" for row in rows))
        self.assertTrue(all(row["formula_id"] == FORMULA_ID for row in rows))
        self.assertTrue(all(row["status"] == "active" and row["fact_level"] == "EXTRACTED" for row in rows))
        self.assertEqual(formula.count(f'formula_id: "{FORMULA_ID}"'), 1)
        for token in (
            "human_status_label_count == 3", "ui_technical_abbreviation_count == 0",
            "status_only_closure_rejected == true", "private_regression_pass_rate_bps == 10000",
            "synthetic_regression_failure_merge_allowed == false",
            "current_formal_report_release_allowed == false",
        ):
            self.assertIn(token, formula)
        self.assertIn("kmfa_v015_s07_p3_release_gate:", models)
        self.assertIn("kmfa_v015_s07_p3_release_gate:", metadata_models)

    def test_project_schemas_express_same_receipt_gated_state(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        acceptance = manifest["phase_acceptance_status"]
        final = acceptance == "PASSED"
        self.assertIn(acceptance, {"PENDING_FINAL_VALIDATION", "PASSED"})
        for index, text in enumerate((
            (PROJECT_ROOT / "docs/governance/project.yaml").read_text(encoding="utf-8"),
            (PROJECT_ROOT / "metadata/project/project.yaml").read_text(encoding="utf-8"),
        )):
            self.assertIn(
                'current_phase_id: "V015_S07_P3_RELEASE_GATE"' if index == 0
                else 'current_phase: "V015_S07_P3_RELEASE_GATE"',
                text,
            )
            for token in (
                'phase_execution_status: "EXECUTION_COMPLETE"',
                f'phase_acceptance_status: "{acceptance}"',
                f'evidence_validation_status: "{"PASS" if final else "PENDING"}"',
                'stage_lifecycle_status: "IN_PROGRESS"', 'stage_acceptance_status: "PENDING"',
                "stage_execution_percentage: 100", "active_formula_count: 343",
                "active_parameter_count: 1622", 'current_parameter_range: "PARAM-KMFA-1999..2007"',
                f'decision: "{"CONTINUE_TO_S07_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S07_P3_FINAL_VALIDATION"}"',
                's07_p2_acceptance_status: "PASSED"', "s07_p3_started: true",
                f's07_p3_acceptance_status: "{acceptance}"',
                f"s07_stage_review_entry_allowed: {str(final).lower()}",
                "s07_stage_review_started: false", "s08_p1_entry_allowed: false",
                "formal_report_generated: false", "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text)

    def test_traceability_version_assurance_and_human_records(self) -> None:
        governance = PROJECT_ROOT / "docs/governance"
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        final = manifest["phase_acceptance_status"] == "PASSED"
        traceability = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        row = next(line for line in traceability.splitlines() if line.startswith("REQ-KMFA-V015-S07-P3-RELEASE-GATE,"))
        self.assertTrue(row.endswith(
            "completed_validated_local_only_s07p3_passed_s07_stage_review_entry_only"
            if final else "completed_execution_pending_final_validation_s07_review_closed"
        ))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn('MOD-KMFA-COST-001: "1.5.0-dev-s07p3"', version)
        self.assertIn('kmfa_v015_s07_p3_release_gate: "1.5.0-dev-s07p3"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1622", assurance)
        self.assertIn("total_active_formulas: 343", assurance)
        model_spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn(f"FORM-KMFA-V015-S07-P3-RELEASE-GATE-001（{'PASSED' if final else 'PENDING_FINAL_VALIDATION'}）", model_spec)
        for relative in ("HANDOFF.md", "功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("v1.5 S07-P3", text)
            self.assertIn("128", text)
            self.assertIn("6", text)

    def test_public_artifacts_match_receipt_gated_contract(self) -> None:
        builder.check_outputs()
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        regression = json.loads(builder.REGRESSION_PATH.read_text(encoding="utf-8"))
        final = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(manifest["phase_id"], "V015_S07_P3_RELEASE_GATE")
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["current_report_display_label_zh"], "暂不可使用")
        self.assertIs(manifest["current_formal_report_release_allowed"], False)
        self.assertEqual(regression["private_regression_pass_rate_bps"], 10000)
        self.assertIs(manifest["s07_stage_review_entry_allowed"], final)
        self.assertEqual(matrix["task_execution_complete_count"], 3)
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
