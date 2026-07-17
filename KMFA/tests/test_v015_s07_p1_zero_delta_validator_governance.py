from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s07_p1_zero_delta_validator as builder


PROJECT_ROOT = Path("KMFA")
FORMULA_ID = "FORM-KMFA-V015-S07-P1-ZERO-DELTA-VALIDATOR-001"
PARAMETER_IDS = {f"PARAM-KMFA-{value}" for value in range(1981, 1990)}


class S07P1ZeroDeltaGovernanceTests(unittest.TestCase):
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
        self.assertIn("money_tolerance_cents == 0", formula)
        self.assertIn("minimum_fail_difference_cents == 1", formula)
        self.assertIn("open_items_may_be_treated_as_resolved == false", formula)
        self.assertIn("kmfa_v015_s07_p1_zero_delta_validator:", models)
        self.assertIn("kmfa_v015_s07_p1_zero_delta_validator:", metadata_models)

    def test_project_schemas_express_same_receipt_gated_state(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        acceptance = manifest["phase_acceptance_status"]
        final = acceptance == "PASSED"
        self.assertIn(acceptance, {"PENDING_FINAL_VALIDATION", "PASSED"})
        values = (
            (PROJECT_ROOT / "docs/governance/project.yaml").read_text(encoding="utf-8"),
            (PROJECT_ROOT / "metadata/project/project.yaml").read_text(encoding="utf-8"),
        )
        for text in values:
            for token in (
                "V015_S07_P1_ZERO_DELTA_VALIDATOR",
                'phase_execution_status: "EXECUTION_COMPLETE"',
                f'phase_acceptance_status: "{acceptance}"',
                f'evidence_validation_status: "{"PASS" if final else "PENDING"}"',
                'stage_lifecycle_status: "IN_PROGRESS"',
                'stage_acceptance_status: "PENDING"',
                "stage_execution_percentage: 33",
                "active_formula_count: 341",
                "active_parameter_count: 1604",
                'current_parameter_range: "PARAM-KMFA-1981..1989"',
                f'decision: "{"CONTINUE_TO_S07_P2_ONLY" if final else "REMAIN_IN_S07_P1_FINAL_VALIDATION"}"',
                "s07_p1_started: true",
                f's07_p1_acceptance_status: "{acceptance}"',
                f"s07_p2_entry_allowed: {str(final).lower()}",
                "s07_p2_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text)

    def test_traceability_version_assurance_and_human_records(self) -> None:
        governance = PROJECT_ROOT / "docs/governance"
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        final = manifest["phase_acceptance_status"] == "PASSED"
        traceability = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        trace_row = next(line for line in traceability.splitlines() if line.startswith("REQ-KMFA-V015-S07-P1-ZERO-DELTA-VALIDATOR,"))
        self.assertTrue(trace_row.endswith(
            "completed_validated_local_only_s07p1_passed_s07p2_entry_only"
            if final else "completed_execution_pending_final_validation_s07p2_closed"
        ))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn('MOD-KMFA-COST-001: "1.5.0-dev-s07p1"', version)
        self.assertIn('kmfa_v015_s07_p1_zero_delta_validator: "1.5.0-dev-s07p1"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1604", assurance)
        self.assertIn("total_active_formulas: 341", assurance)
        delivery = (governance / "delivery_tasks.yaml").read_text(encoding="utf-8")
        self.assertIn(f'acceptance_status: "{"PASSED" if final else "PENDING_FINAL_VALIDATION"}"', delivery.split('  - task_id: "KMFA-V015-S06-STAGE-REVIEW', 1)[0])
        model_spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn(f"FORM-KMFA-V015-S07-P1-ZERO-DELTA-VALIDATOR-001（{'PASSED' if final else 'PENDING_FINAL_VALIDATION'}）", model_spec)
        for relative in ("HANDOFF.md", "功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("v1.5 S07-P1", text)
            self.assertIn("128", text)

    def test_public_artifacts_match_receipt_gated_contract(self) -> None:
        builder.check_outputs()
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_id"], "V015_S07_P1_ZERO_DELTA_VALIDATOR")
        acceptance = manifest["phase_acceptance_status"]
        final = acceptance == "PASSED"
        self.assertIn(acceptance, {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["stage_execution_percentage"], 33)
        self.assertEqual(manifest["money_tolerance_cents"], 0)
        self.assertTrue(manifest["one_cent_difference_detected"])
        self.assertTrue(manifest["private_zero_difference"])
        self.assertEqual(manifest["open_unconfirmed_item_count"], 128)
        self.assertFalse(manifest["open_items_may_be_treated_as_resolved"])
        self.assertIs(manifest["s07_p2_entry_allowed"], final)
        self.assertEqual(matrix["task_execution_complete_count"], 3)
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
