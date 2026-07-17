import unittest

from KMFA.tools import build_v015_s15_p2_identity_roles as builder
from KMFA.tools import v015_s15_p2_identity_roles as subject


class TestV015S15P2IdentityRolesGovernance(unittest.TestCase):
    def test_project_governance_tracks_only_s15_p2(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                subject.RUN_PHASE_ID,
                subject.TASK_ID,
                subject.ACCEPTANCE_ID,
                "governance_model_count: 12",
                "active_formula_count: 374",
                "active_parameter_count: 2018",
                'current_parameter_range: "PARAM-KMFA-2386..2403"',
                "stage_execution_percentage: 67",
                "s15_p2_started: true",
                "s15_p2_public_user_count: 2",
                "s15_p2_role_hat_count: 4",
                "s15_p2_resource_domain_count: 5",
                "s15_p2_default_deny_enabled: true",
                "s15_p2_same_role_self_approval_allowed: false",
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
        self.assertIn("FORM-KMFA-V015-S15-P2-IDENTITY-ROLES-001", formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s15_p2_identity_roles", text)
            self.assertIn("MOD-KMFA-QUALITY-GATE-001", text)
        for number in range(2386, 2404):
            self.assertIn(f"PARAM-KMFA-{number}", parameters)

    def test_human_records_explain_the_change_in_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S15-P2", text, relative)
        self.assertIn("同一个人", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("不会真的发布报告", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_release_and_later_stage_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"s15_p3_started": false',
            '"s15_stage_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
