from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s10_stage_review as builder


MODEL_ID = "MOD-KMFA-V015-S02-P2-TRACEABILITY-001"
FORMULA_ID = "FORM-KMFA-V015-S10-STAGE-REVIEW-001"


class V015S10StageReviewGovernanceTests(unittest.TestCase):
    def test_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 2119 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2125
        ]
        self.assertEqual(len(selected), 7)
        self.assertTrue(all(row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID and row["status"] == "active" for row in selected))
        self.assertIn(FORMULA_ID, formula)
        self.assertIn("predecessor_receipt_count == 57", formula)
        self.assertIn("live_check_pass_count == 36", formula)
        self.assertIn("cross_phase_contract_pass_count == 24", formula)
        self.assertIn("kmfa_v015_s10_stage_review:", model)
        self.assertIn("kmfa_v015_s10_stage_review:", metadata_model)

    def test_traceability_version_and_assurance(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        self.assertIn("REQ-KMFA-V015-S10-STAGE-REVIEW", (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"))
        self.assertIn(f'{MODEL_ID}: "{builder.VERSION}"', (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8"))
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1740", assurance)
        self.assertIn("total_active_formulas: 356", assurance)


if __name__ == "__main__":
    unittest.main()
