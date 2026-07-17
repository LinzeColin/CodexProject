from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest

from KMFA.tools import build_v015_s22_p1_notifications as builder


class NotificationGovernanceTests(unittest.TestCase):
    def test_registry_has_exact_twenty_active_parameters(self) -> None:
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 2906 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2925]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == "MOD-KMFA-NOTIFICATION-001" and row["formula_id"] == "FORM-KMFA-V015-S22-P1-NOTIFICATIONS-001" and row["status"] == "active" for row in selected))

    def test_registries_and_human_records_register_s22_p1(self) -> None:
        registry = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        formal = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        trace = (builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        for token in ("kmfa_v015_s22_p1_notifications:", "MOD-KMFA-NOTIFICATION-001", "FORM-KMFA-V015-S22-P1-NOTIFICATIONS-001", "PARAM-KMFA-2906", "PARAM-KMFA-2925"):
            self.assertIn(token, registry + formal + formula)
        self.assertIn("REQ-KMFA-V015-S22-P1-NOTIFICATIONS", trace)
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md", "CHANGELOG.md", "README.md", "HANDOFF.md", "AGENTS.md"):
            self.assertIn("S22-P1", (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"), relative)

    def test_governance_sync_matches_manifest_acceptance(self) -> None:
        accepted = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))["phase_acceptance_status"] == "PASSED"
        state = "S22_P1_PASSED" if accepted else "S22_P1_PENDING_FINAL_VALIDATION"
        result = subprocess.run([sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state], cwd=builder.REPO_ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_governance_counts_and_boundaries_are_visible(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "V015_S22_P1_NOTIFICATIONS", "active_formula_count: 401", "active_parameter_count: 2540", "PARAM-KMFA-2906..2925",
                "s22_p1_rule_catalog_count: 7", "s22_p1_enabled_confirmed_rule_count: 6", "s22_p1_unconfirmed_rule_enabled_count: 0",
                "s22_p1_public_check_count: 65", "s22_p1_duplicate_dispatch_count: 0", "s22_p1_raw_external_release_count: 0",
                "s22_p2_started: false", "s22_p3_started: false", "github_upload_performed: false", "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_assurance_and_version_matrix_use_current_totals(self) -> None:
        assurance = (builder.PROJECT_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        versions = (builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 2540", assurance); self.assertIn("total_active_formulas: 401", assurance)
        self.assertIn('MOD-KMFA-NOTIFICATION-001: "1.5.0-dev-s22p1"', versions)
        self.assertIn('kmfa_v015_s22_p1_notifications: "1.5.0-dev-s22p1"', versions)


if __name__ == "__main__":
    unittest.main()
