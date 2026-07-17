import unittest

from KMFA.tools import build_v015_s16_p3_homepage_usability as builder
from KMFA.tools import v015_s16_p3_homepage_usability as subject


class HomepageUsabilityGovernanceTests(unittest.TestCase):
    def test_project_governance_tracks_only_s16_p3(self) -> None:
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
                "active_formula_count: 379",
                "active_parameter_count: 2102",
                'current_parameter_range: "PARAM-KMFA-2470..2487"',
                "stage_execution_percentage: 100",
                's16_p2_acceptance_status: "PASSED"',
                "s16_p3_started: true",
                "s16_p3_ten_second_case_count: 6",
                "s16_p3_ten_second_case_pass_count: 6",
                "s16_p3_ten_second_success_bps: 10000",
                "s16_p3_ten_second_threshold_bps: 8000",
                "s16_p3_priority_preview_count: 3",
                "s16_p3_critical_task_count: 3",
                "s16_p3_max_critical_task_clicks: 1",
                "s16_p3_dead_end_count: 0",
                "s16_p3_fault_state_count: 3",
                "s16_p3_blank_page_count: 0",
                "s16_p3_fake_business_value_count: 0",
                "s16_p3_browser_flow_count: 8",
                "s16_p3_visual_evidence_count: 5",
                "s16_p3_public_check_count: 55",
                "s16_stage_review_started: false",
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
        self.assertIn("FORM-KMFA-V015-S16-P3-HOMEPAGE-USABILITY-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s16_p3_homepage_usability", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2470, 2488):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S16-P3", text, relative)
        self.assertIn("前三项重点", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("不连接真实公司数据", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_release_and_later_phase_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"fact_layer_write_count": 0',
            '"s16_p3_started": true',
            '"s16_stage_review_started": false',
            '"s17_entry_allowed": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
