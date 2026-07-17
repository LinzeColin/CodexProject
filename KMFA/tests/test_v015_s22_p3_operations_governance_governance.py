from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest

from KMFA.tools import build_v015_s22_p3_operations_governance as builder


class OperationsGovernanceGovernanceTests(unittest.TestCase):
    def test_registry_has_exact_twenty_active_parameters(self) -> None:
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row
            for row in rows
            if row.get("parameter_id", "").startswith("PARAM-KMFA-")
            and 2946 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2965
        ]
        self.assertEqual(len(selected), 20)
        self.assertTrue(
            all(
                row["model_id"] == "MOD-KMFA-OPERATIONS-001"
                and row["formula_id"]
                == "FORM-KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE-001"
                and row["status"] == "active"
                for row in selected
            )
        )

    def test_registries_and_human_records_register_s22_p3(self) -> None:
        registry = (
            builder.PROJECT_ROOT / "metadata/model_registry.yaml"
        ).read_text(encoding="utf-8")
        formal = (
            builder.PROJECT_ROOT / "docs/governance/model_registry.yaml"
        ).read_text(encoding="utf-8")
        formula = (
            builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml"
        ).read_text(encoding="utf-8")
        trace = (
            builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv"
        ).read_text(encoding="utf-8")
        for token in (
            "kmfa_v015_s22_p3_operations_governance:",
            "MOD-KMFA-OPERATIONS-001",
            "FORM-KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE-001",
            "PARAM-KMFA-2946",
            "PARAM-KMFA-2965",
        ):
            self.assertIn(token, registry + formal + formula)
        self.assertIn("REQ-KMFA-V015-S22-P3-OPERATIONS-GOVERNANCE", trace)
        for relative in (
            "功能清单.md",
            "开发记录.md",
            "模型参数文件.md",
            "CHANGELOG.md",
            "README.md",
            "HANDOFF.md",
            "AGENTS.md",
        ):
            self.assertIn(
                "S22-P3",
                (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"),
                relative,
            )

    def test_governance_sync_matches_manifest_acceptance(self) -> None:
        accepted = (
            json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))[
                "phase_acceptance_status"
            ]
            == "PASSED"
        )
        state = "S22_P3_PASSED" if accepted else "S22_P3_PENDING_FINAL_VALIDATION"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "KMFA/tools/v015_roadmap_governance_sync.py",
                "--check",
                "--validation-state",
                state,
            ],
            cwd=builder.REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_governance_counts_and_boundaries_are_visible(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "V015_S22_P3_OPERATIONS_GOVERNANCE",
                "active_formula_count: 403",
                "active_parameter_count: 2580",
                "PARAM-KMFA-2946..2965",
                "s22_p3_service_count: 6",
                "s22_p3_monitored_service_count: 6",
                "s22_p3_unmonitored_service_count: 0",
                "s22_p3_restore_difference_count: 0",
                "s22_p3_restore_permission_difference_count: 0",
                "s22_p3_migration_surface_count: 4",
                "s22_p3_migration_idempotent_noop_count: 1",
                "s22_p3_migration_rollback_difference_count: 0",
                "s22_p3_irreversible_without_approval_accept_count: 0",
                "s22_p3_public_check_count: 62",
                "s22_p3_raw_external_release_count: 0",
                "s22_stage_review_started: false",
                "s23_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_assurance_and_version_matrix_use_current_totals(self) -> None:
        assurance = (
            builder.PROJECT_ROOT / "docs/governance/ASSURANCE_STATUS.yaml"
        ).read_text(encoding="utf-8")
        versions = (
            builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 2580", assurance)
        self.assertIn("total_active_formulas: 403", assurance)
        self.assertIn(
            'MOD-KMFA-OPERATIONS-001: "1.5.0-dev-s22p3"',
            versions,
        )
        self.assertIn(
            'kmfa_v015_s22_p3_operations_governance: "1.5.0-dev-s22p3"',
            versions,
        )


if __name__ == "__main__":
    unittest.main()
