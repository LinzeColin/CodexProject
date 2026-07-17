import unittest

from KMFA.tools import build_v015_s16_p1_homepage as builder
from KMFA.tools import v015_s16_p1_homepage as subject


class HomepageGovernanceTests(unittest.TestCase):
    def test_project_governance_tracks_only_s16_p1(self) -> None:
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
                "governance_model_count: 12",
                "active_formula_count: 377",
                "active_parameter_count: 2066",
                'current_parameter_range: "PARAM-KMFA-2434..2451"',
                "stage_execution_percentage: 33",
                "s16_p1_started: true",
                "s16_p1_summary_metric_count: 5",
                "s16_p1_source_bound_metric_count: 5",
                "s16_p1_cutoff_bound_metric_count: 5",
                "s16_p1_completeness_bound_metric_count: 5",
                "s16_p1_partial_missing_metric_count: 1",
                "s16_p1_missing_as_zero_count: 0",
                "s16_p1_focus_item_count: 5",
                "s16_p1_primary_action_count: 5",
                "s16_p1_automatic_execution_count: 0",
                "s16_p1_trend_series_count: 3",
                "s16_p1_trend_table_alternative_count: 3",
                "s16_p1_project_portfolio_count: 4",
                "s16_p1_public_check_count: 50",
                "s16_p2_started: false",
                "s16_p3_started: false",
                "s17_entry_allowed: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S16-P1-HOMEPAGE-FIRST-SCREEN-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s16_p1_homepage_first_screen", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2434, 2452):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S16-P1", text, relative)
        self.assertIn("5 个数字", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("不连接真实公司数据", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_release_and_later_stage_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"s16_p1_started": true',
            '"s16_p2_started": false',
            '"s16_p3_started": false',
            '"s16_stage_review_entry_allowed": false',
            '"s17_entry_allowed": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
