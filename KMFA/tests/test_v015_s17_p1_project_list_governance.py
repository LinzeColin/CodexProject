import unittest

from KMFA.tools import build_v015_s17_p1_project_list as builder
from KMFA.tools import v015_s17_p1_project_list as subject


class ProjectListGovernanceTests(unittest.TestCase):
    def test_project_governance_tracks_only_s17_p1(self) -> None:
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
                "active_formula_count: 381",
                "active_parameter_count: 2140",
                'current_parameter_range: "PARAM-KMFA-2506..2525"',
                "stage_execution_percentage: 33",
                's16_stage_review_acceptance_status: "PASSED"',
                "s17_p1_started: true",
                "s17_p1_catalog_project_count: 18",
                "s17_p1_company_count: 3",
                "s17_p1_default_visible_column_count: 8",
                "s17_p1_filter_dimension_count: 7",
                "s17_p1_group_option_count: 6",
                "s17_p1_sort_option_count: 5",
                "s17_p1_hidden_composite_score_count: 0",
                "s17_p1_minimum_batch_project_count: 2",
                "s17_p1_maximum_batch_project_count: 6",
                "s17_p1_export_source_required: true",
                "s17_p1_fact_layer_write_count: 0",
                "s17_p1_browser_flow_count: 8",
                "s17_p1_visual_evidence_count: 4",
                "s17_p1_public_check_count: 58",
                "s17_p2_started: false",
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
        self.assertIn("FORM-KMFA-V015-S17-P1-PROJECT-LIST-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s17_p1_project_list", text)
            self.assertIn("MOD-KMFA-PROJECT-PORTFOLIO-001", text)
        for number in range(2506, 2526):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S17-P1", text, relative)
        self.assertIn("默认只显示", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("不连接真实公司资料", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_release_and_later_phase_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"fact_layer_write_count": 0',
            '"s17_p1_started": true',
            '"s17_p2_started": false',
            '"s17_p3_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
