import unittest

from KMFA.tools import build_v015_s13_p2_business_health_model as builder
from KMFA.tools import v015_s13_p2_business_health_model as health


class TestV015S13P2BusinessHealthModelGovernance(unittest.TestCase):
    def test_project_governance_preserves_accepted_s13_p2(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "s13_p2_started: true",
                's13_p2_acceptance_status: "PASSED"',
                "s13_p2_health_dimension_count: 6",
                "s13_p2_health_weight_total_bps: 10000",
                "s13_p2_scenario_count: 3",
                "s13_p2_fact_layer_write_count: 0",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameter_registries_are_bound(self) -> None:
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        parameters = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S13-P2-BUSINESS-HEALTH-MODEL-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s13_p2_business_health_model", text)
            self.assertIn("MOD-KMFA-HEALTH-001", text)
        for number in range(2254, 2272):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_are_present_and_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(health.RUN_PHASE_ID, text, relative)
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("六部分", report)
        self.assertIn("不改写事实", report)

    def test_release_and_private_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertIn('"raw_root_access_count": 0', manifest)
        self.assertIn('"live_source_read_count": 0', manifest)
        self.assertIn('"real_business_health_score_computed": false', manifest)
        self.assertIn('"action_priority_computed": false', manifest)
        self.assertIn('"github_upload_performed": false', manifest)
        self.assertIn('"app_reinstall_performed": false', manifest)


if __name__ == "__main__":
    unittest.main()
