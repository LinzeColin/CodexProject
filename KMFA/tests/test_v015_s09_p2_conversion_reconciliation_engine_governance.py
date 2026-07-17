from __future__ import annotations

import unittest

from KMFA.tools import build_v015_s09_p2_conversion_reconciliation_engine as builder


class ConversionReconciliationGovernanceTests(unittest.TestCase):
    def test_project_state_tracks_only_s09_p2(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE",
                "KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE-20260715",
                "ACC-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE",
                "stage_execution_percentage: 67",
                "s09_p2_started: true",
                "s09_p3_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text)

    def test_required_human_governance_surfaces_are_current(self) -> None:
        for relative in (
            "AGENTS.md",
            "HANDOFF.md",
            "README.md",
            "CHANGELOG.md",
            "功能清单.md",
            "开发记录.md",
            "模型参数文件.md",
            "docs/governance/DEVELOPMENT_LEDGER.md",
            "docs/governance/STATUS.md",
            "docs/governance/OWNER_STATUS.md",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S09-P2", text, relative)
        self.assertIn("整数分", (builder.PROJECT_ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("不静默", (builder.PROJECT_ROOT / "HANDOFF.md").read_text(encoding="utf-8"))

    def test_model_formula_parameter_and_feature_registration(self) -> None:
        surfaces = {
            "metadata/model_registry.yaml": "kmfa_v015_s09_p2_conversion_reconciliation_engine",
            "docs/governance/model_registry.yaml": "kmfa_v015_s09_p2_conversion_reconciliation_engine",
            "docs/governance/formula_registry.yaml": "FORM-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-001",
            "docs/governance/parameter_registry.csv": "PARAM-KMFA-2064",
            "docs/governance/TRACEABILITY_MATRIX.csv": "REQ-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE",
            "功能清单.md": "FEAT-KMFA-283",
        }
        for relative, token in surfaces.items():
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(token, text, relative)

    def test_roadmap_has_s09_p2_task_state_and_keeps_later_work_closed(self) -> None:
        text = (builder.PROJECT_ROOT / "docs/governance/roadmap.yaml").read_text(encoding="utf-8")
        for task_id in ("S09P2T01", "S09P2T02", "S09P2T03"):
            self.assertIn(f'task_id: "{task_id}"', text)
        self.assertIn("s09_p2_started: true", text)
        self.assertIn("s09_p3_started: false", text)
        self.assertIn("s09_stage_review_entry_allowed: false", text)


if __name__ == "__main__":
    unittest.main()
