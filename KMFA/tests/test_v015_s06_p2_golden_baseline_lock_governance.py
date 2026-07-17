from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s06_p2_golden_baseline_lock as builder
from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel


PROJECT_ROOT = Path("KMFA")
FORMULA_ID = "FORM-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK-001"
PARAMETER_IDS = {f"PARAM-KMFA-{value}" for value in range(1957, 1966)}


class V015S06P2GovernanceTests(unittest.TestCase):
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
        self.assertIn("human_signoff_valid == true", formula)
        self.assertIn("accepted_field_count == 92", formula)
        self.assertIn("rejected_candidate_count == 65", formula)
        self.assertIn("history_overwrite_allowed == false", formula)
        self.assertIn("kmfa_v015_s06_p2_golden_baseline_lock:", models)
        self.assertIn("kmfa_v015_s06_p2_golden_baseline_lock:", metadata_models)

    def test_project_schemas_express_same_locked_pending_validation_gate(self) -> None:
        governance = (PROJECT_ROOT / "docs/governance/project.yaml").read_text(encoding="utf-8")
        metadata = (PROJECT_ROOT / "metadata/project/project.yaml").read_text(encoding="utf-8")
        common = (
            kernel.RUN_PHASE_ID,
            'phase_execution_status: "EXECUTION_COMPLETE"',
            'phase_acceptance_status: "PENDING_FINAL_VALIDATION"',
            'evidence_validation_status: "PENDING"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            'stage_execution_percentage: 33',
            'active_formula_count: 338',
            'active_parameter_count: 1580',
            'current_parameter_range: "PARAM-KMFA-1957..1965"',
            'decision: "REMAIN_IN_S06_P2_PENDING_FINAL_VALIDATION"',
            's06_p1_acceptance_status: "PASSED"',
            's06_p2_started: true',
            's06_p2_candidate_count: 157',
            's06_p2_pending_candidate_count: 0',
            's06_p2_accepted_field_count: 92',
            's06_p2_rejected_candidate_count: 65',
            's06_p2_project_summary_count: 8',
            's06_p2_golden_version_count: 1',
            's06_p2_human_signoff_valid: true',
            's06_p3_entry_allowed: false',
        )
        for text in (governance, metadata):
            for token in common:
                self.assertIn(token, text)

    def test_traceability_version_assurance_and_primary_records(self) -> None:
        governance = PROJECT_ROOT / "docs/governance"
        self.assertIn("REQ-KMFA-V015-S06-P2-GOLDEN-BASELINE-LOCK", (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn('MOD-KMFA-COST-001: "1.5.0-dev-s06p2"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1580", assurance)
        self.assertIn("total_active_formulas: 338", assurance)
        for relative in ("HANDOFF.md", "开发记录.md", "功能清单.md", "模型参数文件.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("v1.5 S06-P2", text)
            self.assertIn("PENDING_FINAL_VALIDATION", text)
            self.assertIn("127.0.0.1", text)

    def test_public_locked_artifacts_are_exact_and_private_free(self) -> None:
        builder.check_outputs()
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        contract = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["golden_version_count"], 1)
        self.assertEqual(manifest["accepted_field_count"], 92)
        self.assertEqual(manifest["project_summary_count"], 8)
        self.assertFalse(manifest["s06_p3_entry_allowed"])
        self.assertTrue(manifest["private_review_ui_available"])
        self.assertEqual(manifest["private_review_host_policy"], "127.0.0.1_ONLY")
        self.assertEqual(manifest["private_review_external_asset_count"], 0)
        self.assertEqual(manifest["source_group_count"], 9)
        self.assertTrue(manifest["private_review_source_filter_available"])
        self.assertTrue(manifest["private_review_stable_source_order"])
        self.assertFalse(manifest["private_review_automatic_inference"])
        rendered = json.dumps({"manifest": manifest, "contract": contract}, ensure_ascii=False)
        for forbidden in ('"private_raw_root":', '"private_package_path":', '"source_locator":', '"confirmer_identity":'):
            self.assertNotIn(forbidden, rendered)
        self.assertEqual(contract["public_raw_value_count"], 0)


if __name__ == "__main__":
    unittest.main()
