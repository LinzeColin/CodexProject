from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
ADP_ROOT = REPO_ROOT / "arxiv-daily-push"


def _quoted_yaml_value(text: str, key: str) -> str:
    match = re.search(rf'(?m)^{re.escape(key)}:\s*"([^"]+)"\s*$', text)
    if not match:
        raise AssertionError(f"{key} is missing from VERSION_MATRIX.yaml")
    return match.group(1)


class GovernanceCurrentStateTests(unittest.TestCase):
    def test_development_ledger_current_state_matches_version_matrix(self) -> None:
        version_matrix = (ADP_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")

        current_iteration = _quoted_yaml_value(version_matrix, "current_iteration")
        current_phase = _quoted_yaml_value(version_matrix, "current_phase")
        current_gate = _quoted_yaml_value(version_matrix, "current_gate")
        expected_task = re.sub(r"^ITER-\d{8}-ADP-", "", current_iteration)
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(f"- Current phase: {current_phase}", current_state)
        self.assertIn(f"- Current gate: {current_gate}", current_state)
        self.assertIn(f"- Current task: `{expected_task}`", current_state)
        self.assertIn(f"### `{current_iteration}`", ledger)

    def test_current_state_records_final_bundle_complete_without_production_acceptance(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn("S2PMT07_POST_FINAL_BUNDLE_CURRENT_STATE_SYNC_READY_NO_PRODUCTION_ACCEPTANCE", current_state)
        self.assertIn("S2PMT07-POST-FINAL-BUNDLE-CURRENT-STATE-SYNC", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", current_state)
        self.assertIn("manifest_validation_state_hash=558ec135fde8912868be73fe472c39bdd3a99f2038500eae15cb70baef470762", current_state)
        self.assertIn("final_bundle_readiness_state_hash=2e37a815934c84ffb08b79df572ec058081cfabb3fbbd4e8a2aba3630de36e4c", current_state)
        self.assertIn("final_bundle_prerequisite_plan_state_hash=a05ed0633ecf8dbd0b1fd93e82b2ad568886544465b5be488ac043f7849ce87b", current_state)
        self.assertIn("missing_items=[]", current_state)
        self.assertIn("next_executable_task=null", current_state)
        self.assertIn("integrated_production_accepted=false", current_state)
        self.assertIn("daily_operation_enabled=false", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("LaunchAgents disabled", current_state)
        self.assertIn("No Stage2/S3/integrated production acceptance is claimed", current_state)

    def test_owner_and_assurance_route_to_production_boundary_preflight(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        self.assertIn('task_id: "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT"', assurance)
        self.assertIn("next_task_id: `S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT`", owner_status)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", assurance)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", owner_status)
        self.assertIn("missing_items=[]", assurance)
        self.assertIn("missing_items=[]", owner_status)
        self.assertIn("current_zero_proof_open_p0_findings: 0", assurance)
        self.assertIn("current_zero_proof_open_p1_findings: 0", assurance)
        self.assertIn("inherited_v7_1_baseline_p0_findings: 8", assurance)
        self.assertIn("inherited_v7_1_baseline_p1_findings: 37", assurance)
        self.assertIn("stage2_integrated_production_accepted: false", assurance)
        self.assertIn("production_acceptance_claimed: false", assurance)
        self.assertNotIn('task_id: "S2PMT07-S2PLT04-COMPLETION-REPORT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-S2PLT04-COMPLETION-REPORT`", owner_status)
        self.assertNotIn("next build, independently review, write, and validate FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json", owner_status)
        self.assertIn("POST_FINAL_BUNDLE_CURRENT_STATE_SYNC", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT", generator)

    def test_current_pointer_and_user_center_match_final_bundle_state(self) -> None:
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")

        self.assertIn("final_bundle_present: true", current)
        self.assertIn("s2plt04_completed: true", current)
        self.assertIn("independent_final_review_passed: true", current)
        self.assertIn("final_commands_executed: true", current)
        self.assertIn("current_zero_proof_open_p0_findings: 0", current)
        self.assertIn("current_zero_proof_open_p1_findings: 0", current)
        self.assertIn("inherited_v7_1_baseline_p0_findings: 8", current)
        self.assertIn("inherited_v7_1_baseline_p1_findings: 37", current)
        self.assertIn("stage2_integrated_production_accepted: false", current)
        self.assertIn("最终验收包 manifest 已通过", decisions)
        self.assertIn("生产验收边界预检", decisions)
        self.assertIn("不是再写 S2PLT04", decisions)
        self.assertIn("Final bundle artifact chain 已通过", readme)
        self.assertIn("Stage2/S3 production accepted", readme)
        self.assertIn("Final bundle artifact chain 已收口", roadmap)
        self.assertIn("INTEGRATED_PRODUCTION_ACCEPTED", roadmap)

    def test_three_base_model_parameter_summary_matches_governance_counts(self) -> None:
        model_spec = (ADP_ROOT / "docs/governance/MODEL_SPEC.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        model_params = (ADP_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        summary = model_params.split("\n## 2026-", 1)[0]

        model_count = re.search(r"(?m)^- model_count: `?(\d+)`?$", model_spec)
        active_formulas = re.search(r"(?m)^- active_formulas: `(\d+)`$", owner_status)
        active_parameters = re.search(r"(?m)^- active_parameters: `(\d+)`$", owner_status)
        if not model_count or not active_formulas or not active_parameters:
            raise AssertionError("governance model/formula/parameter counts are missing")

        self.assertIn(f"- active_model_count: `{model_count.group(1)}`", summary)
        self.assertIn(f"- active_formula_count: `{active_formulas.group(1)}`", summary)
        self.assertIn(f"- active_parameter_count: `{active_parameters.group(1)}`", summary)
        self.assertIn("- current_task: `S2PMT07-POST-FINAL-BUNDLE-CURRENT-STATE-SYNC`", summary)
        self.assertIn("- next_gate: `S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT`", summary)


if __name__ == "__main__":
    unittest.main()
