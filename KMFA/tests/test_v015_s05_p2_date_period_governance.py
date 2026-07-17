from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s05_p2_date_period as builder


MODEL_ID = "MOD-KMFA-COST-001"
FORMULA_ID = "FORM-KMFA-V015-S05-P2-DATE-PERIOD-001"


class V015S05P2DatePeriodGovernanceTests(unittest.TestCase):
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
            and 1924 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 1932
        ]
        self.assertEqual(len(selected), 9)
        self.assertTrue(all(row["status"] == "active" for row in selected))
        self.assertTrue(all(row["model_id"] == MODEL_ID for row in selected))
        self.assertTrue(all(row["formula_id"] == FORMULA_ID for row in selected))
        self.assertIn("kmfa_v015_s05_p2_date_period:", model)
        self.assertIn("kmfa_v015_s05_p2_date_period:", metadata_model)
        self.assertIn(FORMULA_ID, formula)
        self.assertIn("business_timezone_required == true", formula)
        self.assertIn("period_overlap_merge_allowed == false", formula)
        self.assertIn("unregistered_rule_calculation_allowed == false", formula)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        versions = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S05-P2-DATE-PERIOD", trace)
        self.assertIn(builder.kernel.TASK_ID, trace)
        self.assertIn(f'{MODEL_ID}: "1.5.0-dev-s05p2"', versions)
        self.assertIn('kmfa_v015_s05_p2_date_period: "1.5.0-dev-s05p2"', versions)
        self.assertIn("total_active_parameters: 1547", assurance)
        self.assertIn("total_active_formulas: 334", assurance)

    def test_manifest_is_truthful_and_phase_bounded_in_both_receipt_states(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        status = manifest["phase_acceptance_status"]
        self.assertIn(status, {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertEqual(manifest["date_case_pass_count"], 12)
        self.assertEqual(manifest["period_case_pass_count"], 10)
        self.assertEqual(manifest["attribution_case_pass_count"], 9)
        self.assertTrue(manifest["business_timezone_required"])
        self.assertFalse(manifest["ambiguous_date_guessing_allowed"])
        self.assertFalse(manifest["period_overlap_merge_allowed"])
        self.assertFalse(manifest["unregistered_rule_calculation_allowed"])
        self.assertFalse(manifest["formal_report_generated"])
        self.assertEqual(manifest["s05_p3_entry_allowed"], status == "PASSED")
        self.assertFalse(manifest["s05_p3_started"])
        self.assertFalse(manifest["s05_stage_review_entry_allowed"])
        self.assertEqual(manifest["decision"], "CONTINUE_TO_S05_P3_ONLY" if status == "PASSED" else "REMAIN_IN_S05_P2")
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
