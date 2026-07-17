from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s04_p2_lineage_version_impact as builder


class V015S04P2LineageVersionGovernanceTests(unittest.TestCase):
    def test_model_formula_and_parameter_registry_bindings(self) -> None:
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 1892 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 1900
        ]
        self.assertEqual(len(selected), 9)
        self.assertTrue(all(row["status"] == "active" for row in selected))
        self.assertTrue(
            all(row["model_id"] == "MOD-KMFA-V015-S02-P2-TRACEABILITY-001" for row in selected)
        )
        self.assertTrue(
            all(row["formula_id"] == "FORM-KMFA-V015-S04-P2-LINEAGE-VERSION-001" for row in selected)
        )
        self.assertIn("kmfa_v015_s04_p2_lineage_version:", model)
        self.assertIn("runtime_enablement: true", model)
        self.assertIn("production_business_lineage_claimed: false", model)
        self.assertIn("FORM-KMFA-V015-S04-P2-LINEAGE-VERSION-001", formula)
        self.assertIn("actual_business_lineage_record_count == 0", formula)
        self.assertIn("missing_historical_input_result == NOT_REBUILDABLE", formula)

    def test_traceability_and_version_matrix_are_current(self) -> None:
        trace = (builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        versions = (builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S04-P2-LINEAGE-VERSION", trace)
        self.assertIn("KMFA-V015-S04-P2-LINEAGE-VERSION-20260714", trace)
        self.assertIn('MOD-KMFA-V015-S02-P2-TRACEABILITY-001: "1.5.0-dev-s04p2"', versions)
        self.assertIn('kmfa_v015_s04_p2_lineage_version: "1.5.0-dev-s04p2"', versions)

    def test_manifest_is_truthful_and_phase_bounded_in_both_receipt_states(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        status = manifest["phase_acceptance_status"]
        self.assertIn(status, {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertEqual(manifest["actual_business_lineage_record_count"], 0)
        self.assertEqual(manifest["lineage_coverage_bps"], 10_000)
        self.assertFalse(manifest["formal_report_allowed"])
        self.assertEqual(manifest["s04_p3_entry_allowed"], status == "PASSED")
        self.assertEqual(
            manifest["decision"],
            "CONTINUE_TO_S04_P3_ONLY" if status == "PASSED" else "REMAIN_IN_S04_P2",
        )
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
