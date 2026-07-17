import unittest

from KMFA.tools import build_v015_s13_p1_indicator_registry as builder
from KMFA.tools import v015_s13_p1_indicator_registry as kernel


class TestV015S13P1IndicatorRegistryGovernance(unittest.TestCase):
    def test_project_governance_preserves_accepted_s13_p1(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "s13_p1_started: true",
                's13_p1_acceptance_status: "PASSED"',
                "s13_p1_indicator_count: 8",
                "s13_p1_indicator_domain_count: 8",
                "s13_p1_parameter_version_count: 8",
                "s13_p1_function_contract_count: 5",
                "s13_p1_result_status_count: 6",
                "s13_p1_public_check_count: 78",
                "s13_p1_public_check_failed_count: 0",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S13-P1-INDICATOR-REGISTRY-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s13_p1_indicator_registry", text)
            self.assertIn("MOD-KMFA-COST-001", text)
        for number in range(2240, 2254):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_are_present_and_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(kernel.RUN_PHASE_ID, text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("八类指标", report)
        self.assertIn("不会被静默忽略", report)

    def test_release_and_private_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertIn('"raw_root_access_count": 0', manifest)
        self.assertIn('"live_source_read_count": 0', manifest)
        self.assertIn('"health_score_computed": false', manifest)
        self.assertIn('"action_priority_computed": false', manifest)
        self.assertIn('"github_upload_performed": false', manifest)
        self.assertIn('"app_reinstall_performed": false', manifest)


if __name__ == "__main__":
    unittest.main()
