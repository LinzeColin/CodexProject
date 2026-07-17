from __future__ import annotations

import csv
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s06_p1_authoritative_source_registration as builder
from KMFA.tools import v015_s06_p1_authoritative_source_registration as kernel


FORMULA_ID = "FORM-KMFA-V015-S06-P1-AUTHORITATIVE-SOURCE-REGISTRATION-001"
PARAMETER_IDS = {f"PARAM-KMFA-{value}" for value in range(1948, 1957)}
PROJECT_ROOT = Path("KMFA")


class V015S06P1GovernanceTests(unittest.TestCase):
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
        self.assertTrue(all(row["fact_level"] == "EXTRACTED" and row["status"] == "active" for row in rows))
        self.assertEqual(formula.count(f'formula_id: "{FORMULA_ID}"'), 1)
        self.assertIn("private_candidate_count == 157", formula)
        self.assertIn("raw_mutation_performed == false", formula)
        self.assertIn("kmfa_v015_s06_p1_authoritative_source_registration:", models)
        self.assertIn("kmfa_v015_s06_p1_authoritative_source_registration:", metadata_models)

    def test_project_schemas_express_the_same_pending_gate(self) -> None:
        governance = (PROJECT_ROOT / "docs/governance/project.yaml").read_text(encoding="utf-8")
        metadata = (PROJECT_ROOT / "metadata/project/project.yaml").read_text(encoding="utf-8")
        self.assertIn('current_phase_id: "V015_S06_P2_GOLDEN_BASELINE_LOCK"', governance)
        self.assertIn('current_phase: "V015_S06_P2_GOLDEN_BASELINE_LOCK"', metadata)
        common = (
            'phase_acceptance_status: "BLOCKED_BY_MISSING_SIGNOFF"',
            'stage_lifecycle_status: "IN_PROGRESS"', 'stage_acceptance_status: "PENDING"',
            'stage_execution_percentage: 33', 'active_formula_count: 338',
            'active_parameter_count: 1580', 's06_p1_authority_source_count: 9',
            's06_p1_started: true', 's06_p1_acceptance_status: "PASSED"',
            's06_p1_private_candidate_count: 157', 's06_p1_template_class_count: 6',
            's06_p1_raw_mutation_performed: false',
            's06_p2_started: true', 's06_p2_candidate_count: 157',
        )
        for text in (governance, metadata):
            for token in common:
                self.assertIn(token, text)

    def test_traceability_version_assurance_and_primary_records(self) -> None:
        governance = PROJECT_ROOT / "docs/governance"
        self.assertIn("REQ-KMFA-V015-S06-P1", (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn('kmfa_v015_s06_p1_authoritative_source_registration: "1.5.0-dev-s06p1"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1580", assurance)
        self.assertIn("total_active_formulas: 338", assurance)
        for relative in ("HANDOFF.md", "开发记录.md", "功能清单.md", "模型参数文件.md"):
            self.assertIn("v1.5 S06-P1", (PROJECT_ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
