from __future__ import annotations

import unittest

from KMFA.tools import build_v015_s17_p3_project_workflow as builder
from KMFA.tools import v015_s17_p3_project_workflow as subject


class ProjectWorkflowGovernanceTests(unittest.TestCase):
    def test_project_governance_tracks_only_s17_p3(self) -> None:
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
                "active_formula_count: 383",
                "active_parameter_count: 2180",
                'current_parameter_range: "PARAM-KMFA-2546..2565"',
                "stage_execution_percentage: 100",
                's17_p2_acceptance_status: "PASSED"',
                "s17_p3_started: true",
                "s17_p3_candidate_count: 3",
                "s17_p3_auto_allocation_min_confidence_bps: 9000",
                "s17_p3_low_confidence_bps: 5200",
                "s17_p3_source_data_write_count: 0",
                "s17_p3_fact_layer_write_count: 0",
                "s17_p3_reversible: true",
                "s17_p3_variance_source_count: 2",
                "s17_p3_event_count: 5",
                "s17_p3_money_tolerance_cents: 0",
                "s17_p3_projection_difference_cents: 0",
                "s17_p3_report_format_count: 3",
                "s17_p3_workbook_sheet_count: 5",
                "s17_p3_browser_flow_count: 10",
                "s17_p3_visual_evidence_count: 6",
                "s17_p3_public_check_count: 69",
                "s17_stage_review_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S17-P3-PROJECT-WORKFLOW-001", formula)
        self.assertIn("auto_allocation_min_confidence_bps == 9000", formula)
        self.assertIn("money_tolerance_cents == 0", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s17_p3_project_workflow", text)
            self.assertIn("MOD-KMFA-PROJECT-PORTFOLIO-001", text)
        for number in range(2546, 2566):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md", "CHANGELOG.md", "docs/governance/DEVELOPMENT_LEDGER.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S17-P3", text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        self.assertIn("用户能做什么", report)
        self.assertIn("不修改源数据", report)
        self.assertIn("低可信候选会被拒绝", guide)

    def test_private_release_and_review_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"live_source_read_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"fact_layer_write_count": 0',
            '"s17_p3_started": true',
            '"s17_overall_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)

    def test_traceability_spec_and_version_matrix_expose_current_profile(self) -> None:
        trace = (builder.PROJECT_ROOT / "docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        spec = (builder.PROJECT_ROOT / "docs/governance/MODEL_SPEC.md").read_text(encoding="utf-8")
        version = (builder.PROJECT_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S17-P3-PROJECT-WORKFLOW", trace)
        self.assertIn("PARAM-KMFA-2546;PARAM-KMFA-2547", trace)
        self.assertIn("FORM-KMFA-V015-S17-P3-PROJECT-WORKFLOW-001", spec)
        self.assertIn('MOD-KMFA-PROJECT-PORTFOLIO-001: "1.5.0-dev-s17p3"', version)
        self.assertIn('kmfa_v015_s17_p3_project_workflow: "1.5.0-dev-s17p3"', version)


if __name__ == "__main__":
    unittest.main()
