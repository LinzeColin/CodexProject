from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s05_p1_amount_precision as builder


MODEL_ID = "MOD-KMFA-COST-001"
FORMULA_ID = "FORM-KMFA-V015-S05-P1-AMOUNT-PRECISION-001"


class V015S05P1AmountPrecisionGovernanceTests(unittest.TestCase):
    def test_model_formula_and_parameter_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 1916 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 1923]
        self.assertEqual(len(selected), 8)
        self.assertTrue(all(row["status"] == "active" for row in selected))
        self.assertTrue(all(row["model_id"] == MODEL_ID for row in selected))
        self.assertTrue(all(row["formula_id"] == FORMULA_ID for row in selected))
        self.assertIn("kmfa_v015_s05_p1_amount_precision:", model)
        self.assertIn("kmfa_v015_s05_p1_amount_precision:", metadata_model)
        self.assertIn(FORMULA_ID, formula)
        self.assertIn("float_money_allowed == false", formula)
        self.assertIn("implicit_intermediate_rounding_allowed == false", formula)
        self.assertIn("unregistered_unit_calculation_allowed == false", formula)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        versions = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S05-P1-AMOUNT-PRECISION", trace)
        self.assertIn(builder.kernel.TASK_ID, trace)
        self.assertIn(f'{MODEL_ID}: "1.5.0-dev-s05p1"', versions)
        self.assertIn('kmfa_v015_s05_p1_amount_precision: "1.5.0-dev-s05p1"', versions)
        self.assertIn("total_active_parameters: 1538", assurance)
        self.assertIn("total_active_formulas: 333", assurance)

    def test_manifest_is_truthful_and_phase_bounded_in_both_receipt_states(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        status = manifest["phase_acceptance_status"]
        self.assertIn(status, {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["stage_execution_percentage"], 33)
        self.assertEqual(manifest["cent_delta_detection_count"], 1)
        self.assertEqual(manifest["amount_case_pass_count"], 6)
        self.assertEqual(manifest["rounding_case_pass_count"], 8)
        self.assertEqual(manifest["unit_case_pass_count"], 7)
        self.assertFalse(manifest["float_money_allowed"])
        self.assertFalse(manifest["implicit_intermediate_rounding_allowed"])
        self.assertFalse(manifest["unknown_unit_calculation_allowed"])
        self.assertFalse(manifest["formal_report_generated"])
        self.assertEqual(manifest["s05_p2_entry_allowed"], status == "PASSED")
        self.assertFalse(manifest["s05_p2_started"])
        self.assertFalse(manifest["s05_p3_entry_allowed"])
        self.assertFalse(manifest["s05_stage_review_entry_allowed"])
        self.assertEqual(manifest["decision"], "CONTINUE_TO_S05_P2_ONLY" if status == "PASSED" else "REMAIN_IN_S05_P1")
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
