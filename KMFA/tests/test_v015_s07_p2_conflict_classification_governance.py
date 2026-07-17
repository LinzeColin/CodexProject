from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s07_p2_conflict_classification as builder


PROJECT_ROOT = Path("KMFA")
FORMULA_ID = "FORM-KMFA-V015-S07-P2-CONFLICT-CLASSIFICATION-001"
PARAMETER_IDS = {f"PARAM-KMFA-{value}" for value in range(1990, 1999)}


class S07P2ConflictClassificationGovernanceTests(unittest.TestCase):
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
        self.assertIn("persistent_same_source_mismatch_is_system_error == true", formula)
        self.assertIn("automatic_source_selection_allowed == false", formula)
        self.assertIn("system_problem_assigned_to_user_count == 0", formula)
        self.assertIn("kmfa_v015_s07_p2_conflict_classification:", models)
        self.assertIn("kmfa_v015_s07_p2_conflict_classification:", metadata_models)

    def test_project_schemas_express_same_receipt_gated_state(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        acceptance = manifest["phase_acceptance_status"]
        final = acceptance == "PASSED"
        self.assertIn(acceptance, {"PENDING_FINAL_VALIDATION", "PASSED"})
        for text in (
            (PROJECT_ROOT / "docs/governance/project.yaml").read_text(encoding="utf-8"),
            (PROJECT_ROOT / "metadata/project/project.yaml").read_text(encoding="utf-8"),
        ):
            for token in (
                "V015_S07_P2_CONFLICT_CLASSIFICATION",
                'phase_execution_status: "EXECUTION_COMPLETE"',
                f'phase_acceptance_status: "{acceptance}"',
                f'evidence_validation_status: "{"PASS" if final else "PENDING"}"',
                'stage_lifecycle_status: "IN_PROGRESS"',
                'stage_acceptance_status: "PENDING"',
                "stage_execution_percentage: 67",
                "active_formula_count: 342",
                "active_parameter_count: 1613",
                'current_parameter_range: "PARAM-KMFA-1990..1998"',
                f'decision: "{"CONTINUE_TO_S07_P3_ONLY" if final else "REMAIN_IN_S07_P2_FINAL_VALIDATION"}"',
                's07_p1_acceptance_status: "PASSED"',
                "s07_p2_started: true",
                f's07_p2_acceptance_status: "{acceptance}"',
                f"s07_p3_entry_allowed: {str(final).lower()}",
                "s07_p3_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text)

    def test_traceability_version_assurance_and_human_records(self) -> None:
        governance = PROJECT_ROOT / "docs/governance"
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        final = manifest["phase_acceptance_status"] == "PASSED"
        traceability = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        row = next(line for line in traceability.splitlines() if line.startswith("REQ-KMFA-V015-S07-P2-CONFLICT-CLASSIFICATION,"))
        self.assertTrue(row.endswith(
            "completed_validated_local_only_s07p2_passed_s07p3_entry_only"
            if final else "completed_execution_pending_final_validation_s07p3_closed"
        ))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn('MOD-KMFA-COST-001: "1.5.0-dev-s07p2"', version)
        self.assertIn('kmfa_v015_s07_p2_conflict_classification: "1.5.0-dev-s07p2"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1613", assurance)
        self.assertIn("total_active_formulas: 342", assurance)
        model_spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn(f"FORM-KMFA-V015-S07-P2-CONFLICT-CLASSIFICATION-001（{'PASSED' if final else 'PENDING_FINAL_VALIDATION'}）", model_spec)
        for relative in ("HANDOFF.md", "功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("v1.5 S07-P2", text)
            self.assertIn("128", text)
            self.assertIn("6", text)

    def test_public_artifacts_match_receipt_gated_contract(self) -> None:
        builder.check_outputs()
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        final = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(manifest["phase_id"], "V015_S07_P2_CONFLICT_CLASSIFICATION")
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertEqual(manifest["private_conflict_candidate_count"], 6)
        self.assertEqual(manifest["private_conflict_auto_selected_count"], 0)
        self.assertEqual(manifest["system_problem_assigned_to_user_count"], 0)
        self.assertIs(manifest["s07_p3_entry_allowed"], final)
        self.assertEqual(matrix["task_execution_complete_count"], 3)
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
