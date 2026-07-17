import unittest

from KMFA.tools import build_v015_s14_p1_information_architecture as builder
from KMFA.tools import v015_s14_p1_information_architecture as architecture


class TestV015S14P1InformationArchitectureGovernance(unittest.TestCase):
    def test_project_governance_tracks_only_s14_p1(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                architecture.RUN_PHASE_ID,
                architecture.TASK_ID,
                architecture.ACCEPTANCE_ID,
                "governance_model_count: 12",
                "active_formula_count: 369",
                "active_parameter_count: 1934",
                'current_parameter_range: "PARAM-KMFA-2302..2319"',
                "stage_execution_percentage: 33",
                "s14_p1_started: true",
                "s14_p1_primary_navigation_count: 7",
                "s14_p1_page_node_count: 18",
                "s14_p1_dead_end_count: 0",
                "s14_p1_parent_cycle_count: 0",
                "s14_p1_stacked_sidebar_used: false",
                "s14_p1_default_visible_technical_term_count: 0",
                "s14_p2_started: false",
                "s14_p3_started: false",
                "s14_stage_review_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S14-P1-INFORMATION-ARCHITECTURE-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s14_p1_information_architecture", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2302, 2320):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(architecture.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S14-P1", text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("顶部固定七个入口", report)
        self.assertIn("返回上一任务", report)

    def test_private_release_and_later_stage_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"raw_business_content_read": false',
            '"live_source_read_count": 0',
            '"real_business_action_count": 0',
            '"s14_p2_started": false',
            '"s14_p3_started": false',
            '"s14_stage_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
