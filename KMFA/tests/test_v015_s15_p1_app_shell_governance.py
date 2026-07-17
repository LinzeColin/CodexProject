import unittest

from KMFA.tools import build_v015_s15_p1_app_shell as builder
from KMFA.tools import v015_s15_p1_app_shell as shell


class TestV015S15P1AppShellGovernance(unittest.TestCase):
    def test_project_governance_tracks_only_s15_p1(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                shell.RUN_PHASE_ID,
                shell.TASK_ID,
                shell.ACCEPTANCE_ID,
                "governance_model_count: 12",
                "active_formula_count: 373",
                "active_parameter_count: 2000",
                'current_parameter_range: "PARAM-KMFA-2368..2385"',
                "stage_execution_percentage: 33",
                "s15_p1_started: true",
                "s15_p1_deep_link_route_count: 18",
                "s15_p1_context_dimension_count: 4",
                "s15_p1_company_isolation_guard_count: 3",
                "s15_p1_cross_company_leak_count: 0",
                "s15_p1_fault_boundary_count: 4",
                "s15_p2_started: false",
                "s15_p3_started: false",
                "s15_stage_review_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S15-P1-APP-SHELL-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s15_p1_app_shell", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2368, 2386):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(shell.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S15-P1", text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("18 个业务页面", report)
        self.assertIn("不会白屏", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_release_and_later_stage_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"live_source_read_count": 0',
            '"external_network_request_count": 0',
            '"real_business_action_count": 0',
            '"s15_p2_started": false',
            '"s15_p3_started": false',
            '"s15_stage_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
