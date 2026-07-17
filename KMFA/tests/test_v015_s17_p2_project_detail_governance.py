from __future__ import annotations

import unittest

from KMFA.tools import build_v015_s17_p2_project_detail as builder
from KMFA.tools import v015_s17_p2_project_detail as subject


class ProjectDetailGovernanceTests(unittest.TestCase):
    def test_project_governance_tracks_only_s17_p2(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                subject.RUN_PHASE_ID,
                subject.TASK_ID,
                subject.ACCEPTANCE_ID,
                "governance_model_count: 13",
                "active_formula_count: 382",
                "active_parameter_count: 2160",
                'current_parameter_range: "PARAM-KMFA-2526..2545"',
                "stage_execution_percentage: 67",
                's17_p1_acceptance_status: "PASSED"',
                "s17_p2_started: true",
                "s17_p2_detail_tab_count: 5",
                "s17_p2_cost_category_count: 10",
                "s17_p2_cost_trend_period_count: 4",
                "s17_p2_document_count: 6",
                "s17_p2_source_group_count: 5",
                "s17_p2_money_tolerance_cents: 0",
                "s17_p2_engine_difference_cents: 0",
                "s17_p2_chart_table_difference_cents: 0",
                "s17_p2_section_overlap_count: 0",
                "s17_p2_return_context_preserved: true",
                "s17_p2_browser_flow_count: 9",
                "s17_p2_visual_evidence_count: 5",
                "s17_p2_public_check_count: 72",
                "s17_p3_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S17-P2-PROJECT-DETAIL-001", formula)
        self.assertIn("money_tolerance_cents == 0", formula)
        self.assertIn("chart_table_difference_cents == 0", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s17_p2_project_detail", text)
            self.assertIn("MOD-KMFA-PROJECT-PORTFOLIO-001", text)
        for number in range(2526, 2546):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S17-P2", text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        self.assertIn("项目目前赚钱", report)
        self.assertIn("一分钱不差", guide)

    def test_private_release_and_later_phase_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"fact_layer_write_count": 0',
            '"s17_p1_started": true',
            '"s17_p2_started": true',
            '"s17_p3_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)

    def test_traceability_and_version_matrix_expose_current_formula_profile(self) -> None:
        trace = (builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S17-P2-PROJECT-DETAIL", trace)
        self.assertIn("PARAM-KMFA-2526;PARAM-KMFA-2527", trace)
        self.assertIn('MOD-KMFA-PROJECT-PORTFOLIO-001: "1.5.0-dev-s17p2"', version)
        self.assertIn('kmfa_v015_s17_p2_project_detail: "1.5.0-dev-s17p2"', version)


if __name__ == "__main__":
    unittest.main()
