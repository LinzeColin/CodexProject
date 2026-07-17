import unittest

from KMFA.tools import build_v015_s13_p3_action_priority as builder
from KMFA.tools import v015_s13_p3_action_priority as action


class TestV015S13P3ActionPriorityGovernance(unittest.TestCase):
    def test_project_governance_tracks_only_s13_p3(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                action.RUN_PHASE_ID,
                action.TASK_ID,
                action.ACCEPTANCE_ID,
                "governance_model_count: 12",
                "active_formula_count: 367",
                "active_parameter_count: 1904",
                'current_parameter_range: "PARAM-KMFA-2272..2289"',
                "s13_p3_started: true",
                "s13_stage_review_started: false",
                "s13_p3_ranking_factor_count: 6",
                "s13_p3_focus_max_items: 5",
                "s13_p3_automatic_execution_count: 0",
                "s13_p3_recommendation_fact_write_count: 0",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S13-P3-ACTION-PRIORITY-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s13_p3_action_priority", text)
            self.assertIn("MOD-KMFA-ACTION-001", text)
        for number in range(2272, 2290):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_are_present_and_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(action.RUN_PHASE_ID, text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("不会替人执行", report)
        self.assertIn("结果和校准建议分开", report)

    def test_release_private_and_execution_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertIn('"raw_root_access_count": 0', manifest)
        self.assertIn('"live_source_read_count": 0', manifest)
        self.assertIn('"real_business_action_priority_computed": false', manifest)
        self.assertIn('"automatic_execution_count": 0', manifest)
        self.assertIn('"recommendation_fact_write_count": 0', manifest)
        self.assertIn('"github_upload_performed": false', manifest)
        self.assertIn('"app_reinstall_performed": false', manifest)


if __name__ == "__main__":
    unittest.main()
