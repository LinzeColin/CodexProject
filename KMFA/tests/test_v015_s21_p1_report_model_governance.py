from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s21_p1_report_model as builder
from KMFA.tools import v015_roadmap_governance_sync as sync


class ReportModelGovernanceTests(unittest.TestCase):
    def test_pending_and_passed_state_are_registered(self) -> None:
        pending = sync.resolve_validation_state("S21_P1_PENDING_FINAL_VALIDATION")
        passed = sync.resolve_validation_state("S21_P1_PASSED")
        self.assertEqual((pending["phase_acceptance_status"], pending["s21_p2_entry_allowed"]), ("PENDING_FINAL_VALIDATION", False))
        self.assertEqual((passed["phase_acceptance_status"], passed["s21_p2_entry_allowed"]), ("PASSED", True))
        self.assertFalse(passed["s21_p2_started"])

    def test_current_governance_matches_manifest_state(self) -> None:
        manifest = __import__("json").loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        state = "S21_P1_PASSED" if manifest["phase_acceptance_status"] == "PASSED" else "S21_P1_PENDING_FINAL_VALIDATION"
        sync.run(check=True, validation_state=state)

    def test_formula_model_and_version_profiles_are_registered(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        models = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        versions = (builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S21-P1-REPORT-MODEL-001", formula)
        self.assertIn("kmfa_v015_s21_p1_report_model:", models)
        self.assertIn('kmfa_v015_s21_p1_report_model: "1.5.0-dev-s21p1"', versions)

    def test_twenty_parameters_are_active_and_bound(self) -> None:
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 2826 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2845]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == "MOD-KMFA-CASH-REPORT-001" for row in selected))
        self.assertTrue(all(row["formula_id"] == "FORM-KMFA-V015-S21-P1-REPORT-MODEL-001" and row["status"] == "active" for row in selected))

    def test_traceability_and_release_boundary_are_explicit(self) -> None:
        trace = (builder.PROJECT_ROOT / "docs/governance/traceability_matrix.csv").read_text(encoding="utf-8")
        project = (builder.PROJECT_ROOT / "docs/governance/project.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S21-P1-REPORT-MODEL", trace)
        self.assertIn("github_upload_performed: false", project)
        self.assertIn("app_reinstall_performed: false", project)


if __name__ == "__main__":
    unittest.main()
