import unittest

from KMFA.tools import build_v015_s14_p2_design_system as builder
from KMFA.tools import v015_s14_p2_design_system as design


class TestV015S14P2DesignSystemGovernance(unittest.TestCase):
    def test_project_governance_tracks_only_s14_p2(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                design.RUN_PHASE_ID,
                design.TASK_ID,
                design.ACCEPTANCE_ID,
                "governance_model_count: 12",
                "active_formula_count: 370",
                "active_parameter_count: 1952",
                'current_parameter_range: "PARAM-KMFA-2320..2337"',
                "stage_execution_percentage: 67",
                "s14_p1_acceptance_status: \"PASSED\"",
                "s14_p2_started: true",
                "s14_p2_theme_count: 2",
                "s14_p2_contrast_fail_count: 0",
                "s14_p2_component_count: 11",
                "s14_p2_no_feedback_component_count: 0",
                "s14_p2_color_only_state_count: 0",
                "s14_p2_maximum_motion_duration_ms: 220",
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
        self.assertIn("FORM-KMFA-V015-S14-P2-DESIGN-SYSTEM-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s14_p2_design_system", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2320, 2338):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(design.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S14-P2", text, relative)
        design_md = (builder.PROJECT_ROOT / "DESIGN.md").read_text(encoding="utf-8")
        self.assertIn("七项横向顶部导航", design_md)
        self.assertIn("最长 220ms", design_md)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("可以直接打开", report)
        self.assertIn("所有状态同时有符号和中文", report)

    def test_private_release_and_later_stage_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"raw_business_content_read": false',
            '"live_source_read_count": 0',
            '"real_business_action_count": 0',
            '"s14_p2_started": true',
            '"s14_p3_started": false',
            '"s14_stage_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
