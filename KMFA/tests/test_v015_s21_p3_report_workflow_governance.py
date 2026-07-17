from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest

from KMFA.tools import build_v015_s21_p3_report_workflow as builder


class ReportWorkflowGovernanceTests(unittest.TestCase):
    def test_registry_has_exact_twenty_active_parameters(self) -> None:
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row for row in rows
            if row.get("parameter_id", "").startswith("PARAM-KMFA-")
            and 2866 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2885
        ]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == "MOD-KMFA-CASH-REPORT-001" for row in selected))
        self.assertTrue(all(
            row["formula_id"] == "FORM-KMFA-V015-S21-P3-REPORT-WORKFLOW-001"
            and row["status"] == "active"
            for row in selected
        ))

    def test_registries_and_human_records_register_s21_p3(self) -> None:
        registry = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        trace = (builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        for token in (
            "kmfa_v015_s21_p3_report_workflow:", "FORM-KMFA-V015-S21-P3-REPORT-WORKFLOW-001",
            "PARAM-KMFA-2866", "PARAM-KMFA-2885",
        ):
            self.assertIn(token, registry)
        self.assertIn("FORM-KMFA-V015-S21-P3-REPORT-WORKFLOW-001", formula)
        self.assertIn("REQ-KMFA-V015-S21-P3-REPORT-WORKFLOW", trace)
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md", "CHANGELOG.md", "README.md", "HANDOFF.md", "AGENTS.md"):
            self.assertIn("S21-P3", (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"), relative)

    def test_governance_sync_matches_manifest_acceptance(self) -> None:
        accepted = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))["phase_acceptance_status"] == "PASSED"
        state = "S21_P3_PASSED" if accepted else "S21_P3_PENDING_FINAL_VALIDATION"
        result = subprocess.run(
            [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
            cwd=builder.REPO_ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_governance_counts_and_boundaries_are_visible(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "V015_S21_P3_REPORT_WORKFLOW", "active_formula_count: 399", "active_parameter_count: 2500",
                "PARAM-KMFA-2866..2885", "s21_p3_workflow_action_count: 5",
                "s21_p3_quality_gate_check_count: 15", "s21_p3_unexplained_difference_count: 0",
                "s21_p3_report_center_filter_count: 6", "s21_p3_internal_publication_count: 1",
                "s21_p3_public_link_count: 0", "s21_stage_review_started: false",
                "s22_entry_allowed: false", "github_upload_performed: false", "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)


if __name__ == "__main__":
    unittest.main()
