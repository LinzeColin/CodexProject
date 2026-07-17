from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s05_p3_field_standardization as builder


MODEL_ID = "MOD-KMFA-COST-001"
FORMULA_ID = "FORM-KMFA-V015-S05-P3-FIELD-STANDARDIZATION-001"


class V015S05P3FieldStandardizationGovernanceTests(unittest.TestCase):
    def test_model_formula_and_parameter_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 1933 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 1941
        ]
        self.assertEqual(len(selected), 9)
        self.assertTrue(all(row["status"] == "active" for row in selected))
        self.assertTrue(all(row["model_id"] == MODEL_ID for row in selected))
        self.assertTrue(all(row["formula_id"] == FORMULA_ID for row in selected))
        self.assertIn("kmfa_v015_s05_p3_field_standardization:", model)
        self.assertIn("kmfa_v015_s05_p3_field_standardization:", metadata_model)
        self.assertIn(FORMULA_ID, formula)
        self.assertIn("blank_to_zero_allowed == false", formula)
        self.assertIn("low_confidence_auto_map_allowed == false", formula)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        versions = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S05-P3-FIELD-STANDARDIZATION", trace)
        self.assertIn(builder.kernel.TASK_ID, trace)
        self.assertIn('kmfa_v015_s05_p3_field_standardization: "1.5.0-dev-s05p3"', versions)
        parameter_match = __import__("re").search(r"total_active_parameters:\s*(\d+)", assurance)
        formula_match = __import__("re").search(r"total_active_formulas:\s*(\d+)", assurance)
        self.assertIsNotNone(parameter_match)
        self.assertIsNotNone(formula_match)
        self.assertGreaterEqual(int(parameter_match.group(1)), 1556)
        self.assertGreaterEqual(int(formula_match.group(1)), 335)

    def test_manifest_is_truthful_and_phase_bounded_in_both_receipt_states(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        status = manifest["phase_acceptance_status"]
        self.assertIn(status, {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["field_definition_count"], 24)
        self.assertEqual(manifest["critical_field_count"], 16)
        self.assertEqual(manifest["mapping_case_pass_count"], 12)
        self.assertEqual(manifest["value_semantic_case_pass_count"], 12)
        self.assertFalse(manifest["low_confidence_auto_map_allowed"])
        self.assertFalse(manifest["blank_to_zero_allowed"])
        self.assertEqual(manifest["s05_stage_review_entry_allowed"], status == "PASSED")
        self.assertFalse(manifest["s05_stage_review_started"])
        self.assertFalse(manifest["s05_stage_review_performed"])
        self.assertFalse(manifest["s06_entry_allowed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
