from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s04_p3_audit_recovery as builder


MODEL_ID = "MOD-KMFA-V015-S02-P2-TRACEABILITY-001"
FORMULA_ID = "FORM-KMFA-V015-S04-P3-AUDIT-RECOVERY-001"


class V015S04P3AuditRecoveryGovernanceTests(unittest.TestCase):
    def test_model_formula_and_parameter_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(
            encoding="utf-8"
        )
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row
            for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 1901 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 1909
        ]
        self.assertEqual(len(selected), 9)
        self.assertTrue(all(row["status"] == "active" for row in selected))
        self.assertTrue(all(row["model_id"] == MODEL_ID for row in selected))
        self.assertTrue(all(row["formula_id"] == FORMULA_ID for row in selected))
        self.assertIn("kmfa_v015_s04_p3_audit_recovery:", model)
        self.assertIn("kmfa_v015_s04_p3_audit_recovery:", metadata_model)
        self.assertEqual(model.count(f'  - model_id: "{MODEL_ID}"'), 1)
        self.assertIn(FORMULA_ID, formula)
        self.assertIn("event_chain_valid == true", formula)
        self.assertIn("critical_break_publication_allowed == false", formula)
        self.assertIn("actual_business_lineage_record_count == 0", formula)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        versions = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S04-P3-AUDIT-RECOVERY", trace)
        self.assertIn(builder.kernel.TASK_ID, trace)
        self.assertIn(f'{MODEL_ID}: "1.5.0-dev-s04p3"', versions)
        self.assertIn('kmfa_v015_s04_p3_audit_recovery: "1.5.0-dev-s04p3"', versions)
        self.assertIn("total_active_parameters: 1524", assurance)
        self.assertIn("total_active_formulas: 331", assurance)

    def test_manifest_is_truthful_and_phase_bounded_in_both_receipt_states(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        status = manifest["phase_acceptance_status"]
        self.assertIn(status, {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["required_action_type_count"], 6)
        self.assertEqual(manifest["synthetic_event_count"], 7)
        self.assertEqual(manifest["approved_snapshot_recovery_case_count"], 3)
        self.assertEqual(manifest["required_health_finding_type_count"], 4)
        self.assertEqual(manifest["actual_business_lineage_record_count"], 0)
        self.assertFalse(manifest["formal_report_allowed"])
        self.assertEqual(manifest["s04_stage_review_entry_allowed"], status == "PASSED")
        self.assertFalse(manifest["s04_stage_review_started"])
        self.assertFalse(manifest["s04_stage_review_performed"])
        self.assertFalse(manifest["s05_entry_allowed"])
        self.assertEqual(
            manifest["decision"],
            "CONTINUE_TO_S04_STAGE_REVIEW_ONLY" if status == "PASSED" else "REMAIN_IN_S04_P3",
        )
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
