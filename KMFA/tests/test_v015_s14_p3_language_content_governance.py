import unittest

from KMFA.tools import build_v015_s14_p3_language_content as builder
from KMFA.tools import v015_s14_p3_language_content as language


class TestV015S14P3LanguageContentGovernance(unittest.TestCase):
    def test_project_governance_tracks_only_s14_p3(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                language.RUN_PHASE_ID,
                language.TASK_ID,
                language.ACCEPTANCE_ID,
                "governance_model_count: 12",
                "active_formula_count: 371",
                "active_parameter_count: 1970",
                'current_parameter_range: "PARAM-KMFA-2338..2355"',
                "stage_execution_percentage: 100",
                's14_p1_acceptance_status: "PASSED"',
                's14_p2_acceptance_status: "PASSED"',
                "s14_p3_entry_allowed: false",
                "s14_p3_started: true",
                "s14_stage_review_started: false",
                "s14_p3_dictionary_entry_count: 14",
                "s14_p3_format_case_count: 10",
                "s14_p3_content_rule_screen_count: 6",
                "s14_p3_ten_second_failure_count: 0",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S14-P3-LANGUAGE-CONTENT-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s14_p3_language_content", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2338, 2356):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(language.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S14-P3", text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("普通中文", report)
        self.assertIn("页面、报告和导出", report)
        self.assertIn("六类页面", report)

    def test_private_release_and_later_stage_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"raw_business_content_read": false',
            '"live_source_read_count": 0',
            '"real_business_action_count": 0',
            '"s14_p3_started": true',
            '"s14_stage_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
