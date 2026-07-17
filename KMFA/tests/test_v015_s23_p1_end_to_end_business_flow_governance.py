from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest

from KMFA.tools import build_v015_s23_p1_end_to_end_business_flow as builder


class EndToEndBusinessFlowGovernanceTests(unittest.TestCase):
    def test_registry_has_exact_twenty_active_parameters(self) -> None:
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 2986 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 3005]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == "MOD-KMFA-END-TO-END-ACCEPTANCE-001" and row["formula_id"] == "FORM-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-001" and row["status"] == "active" for row in selected))

    def test_registries_and_human_records_register_s23_p1(self) -> None:
        combined = "\n".join((builder.PROJECT_ROOT / relative).read_text(encoding="utf-8") for relative in ("metadata/model_registry.yaml", "docs/governance/model_registry.yaml", "docs/governance/formula_registry.yaml", "docs/governance/TRACEABILITY_MATRIX.csv"))
        for token in ("kmfa_v015_s23_p1_end_to_end_business_flow:", "MOD-KMFA-END-TO-END-ACCEPTANCE-001", "FORM-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-001", "PARAM-KMFA-2986", "PARAM-KMFA-3005"):
            self.assertIn(token, combined)
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md", "CHANGELOG.md", "README.md", "HANDOFF.md"):
            self.assertIn("S23-P1", (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"), relative)

    def test_governance_sync_matches_manifest_acceptance(self) -> None:
        accepted = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))["phase_acceptance_status"] == "PASSED"
        state = "S23_P1_PASSED" if accepted else "S23_P1_PENDING_FINAL_VALIDATION"
        result = subprocess.run([sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state], cwd=builder.REPO_ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_governance_counts_and_boundaries_are_visible(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in ("V015_S23_P1_END_TO_END_BUSINESS_FLOW", "active_formula_count: 405", "active_parameter_count: 2620", "PARAM-KMFA-2986..3005", "s23_p1_backend_view_count: 4", "s23_p1_project_difference_cents: 0", "s23_p1_export_format_count: 4", "s23_p1_cross_format_difference_integer: 0", "s23_p1_revision_unexplained_difference_count: 0", "s23_p2_started: false", "s23_p3_started: false", "github_upload_performed: false", "app_reinstall_performed: false"):
                self.assertIn(token, text, relative)

    def test_assurance_and_version_matrix_use_current_totals(self) -> None:
        assurance = (builder.PROJECT_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        versions = (builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 2620", assurance)
        self.assertIn("total_active_formulas: 405", assurance)
        self.assertIn('MOD-KMFA-END-TO-END-ACCEPTANCE-001: "1.5.0-dev-s23p1"', versions)
        self.assertIn('kmfa_v015_s23_p1_end_to_end_business_flow: "1.5.0-dev-s23p1"', versions)


if __name__ == "__main__":
    unittest.main()
