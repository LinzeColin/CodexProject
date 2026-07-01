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

    def test_current_state_records_write_gate_and_controlled_run_without_production_acceptance(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "S2PMT07_INTEGRATED_PRODUCTION_ACCEPTANCE_WRITE_GATE_BLOCKED_OWNER_DECISION_NO_PRODUCTION_ACCEPTANCE",
            current_state,
        )
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE", current_state)
        self.assertIn("status=blocked_write_gate_owner_decision_required_no_acceptance", current_state)
        self.assertIn("write_gate_precheck_ready=true", current_state)
        self.assertIn("acceptance_write_gate_allowed=false", current_state)
        self.assertIn("write_gate_state_hash=48bd21b374fb86b91ab1a684af5bc8f5d2d7a7be752b85d75fe9f8bb9f43bcd8", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json", current_state)
        self.assertIn("request_only=true", current_state)
        self.assertIn("state_hash=b406be2981f67b316df5ceba4469cc8fc3b96364a031c179bca9904f008bd9ea", current_state)
        self.assertIn("acceptance_write_gate_allowed_by_this_request=false", current_state)
        self.assertIn("runtime_enablement_allowed_by_this_request=false", current_state)
        self.assertIn("Owner packet remains `state_hash=de807ff8c395bfda9db6edb4aadacb1e1bdb0e076b4025ed3daca7a2402da289`", current_state)
        self.assertIn("status=pass_controlled_real_run_evidence_rechecked_no_new_send", current_state)
        self.assertIn("sent_mail_count=4/4", current_state)
        self.assertIn("newly_sent_mail_products=[]", current_state)
        self.assertIn("duplicate_smtp_send_avoided=true", current_state)
        self.assertIn("preflight_checks_passed=true", current_state)
        self.assertIn(
            "preflight_state_hash=6fc89cd8b1d83a2501c54aadd3e6ad04dcf209ec3898d7c0e65d8e65ae9ab4e5",
            current_state,
        )
        self.assertIn("failed_checks=[]", current_state)
        self.assertIn("owner_production_boundary_decision_missing", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", current_state)
        self.assertIn(
            "final bundle manifest validation remains `state_hash=558ec135fde8912868be73fe472c39bdd3a99f2038500eae15cb70baef470762`",
            current_state,
        )
        self.assertIn(
            "Final bundle readiness remains `state_hash=2e37a815934c84ffb08b79df572ec058081cfabb3fbbd4e8a2aba3630de36e4c`",
            current_state,
        )
        self.assertIn("integrated_production_accepted=false", current_state)
        self.assertIn("daily_operation_enabled=false", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("LaunchAgents disabled", current_state)
        self.assertIn("No Stage2/S3/integrated production acceptance is claimed", current_state)

    def test_owner_and_assurance_route_to_owner_decision_after_preflight(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        self.assertIn('task_id: "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION"', assurance)
        self.assertIn("next_task_id: `S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION`", owner_status)
        self.assertIn(
            "S2PMT07_INTEGRATED_PRODUCTION_ACCEPTANCE_WRITE_GATE_BLOCKED_OWNER_DECISION_NO_PRODUCTION_ACCEPTANCE",
            assurance,
        )
        self.assertIn("preflight checks passed", assurance)
        self.assertIn("owner decision packet ready", assurance)
        self.assertIn("acceptance write-gate precheck blocked correctly", assurance)
        self.assertIn("controlled foreground real-run acceptance recheck passed", assurance)
        self.assertIn("owner_production_boundary_decision.request.json", assurance)
        self.assertIn("open_pr_count=0", assurance)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", assurance)
        self.assertIn("LaunchAgents disabled", assurance)
        self.assertIn("owner production-boundary decision evidence", assurance)
        self.assertIn("final bundle manifest pass", assurance)
        self.assertIn("final bundle manifest pass", owner_status)
        self.assertIn("owner production-boundary decision", owner_status)
        self.assertIn("owner_production_boundary_decision.request.json", owner_status)
        self.assertIn("Final bundle ready 状态会保持", owner_status)
        self.assertIn("stage2_integrated_production_accepted: false", assurance)
        self.assertNotIn('task_id: "S2PMT07-S2PLT04-COMPLETION-REPORT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-S2PLT04-COMPLETION-REPORT`", owner_status)
        self.assertNotIn("next build, independently review, write, and validate FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json", owner_status)
        self.assertIn("production_boundary_preflight_ready", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE", generator)

    def test_current_pointer_and_user_center_match_owner_packet_and_controlled_run_state(self) -> None:
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")

        self.assertIn("current_iteration: ITER-20260701-ADP-S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE", current)
        self.assertIn(
            "current_gate: S2PMT07_INTEGRATED_PRODUCTION_ACCEPTANCE_WRITE_GATE_BLOCKED_OWNER_DECISION_NO_PRODUCTION_ACCEPTANCE",
            current,
        )
        self.assertIn("next_executable_task: S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION", current)
        self.assertIn("integrated_production_acceptance_preflight_passed: true", current)
        self.assertIn(
            "integrated_production_acceptance_preflight_state_hash: 6fc89cd8b1d83a2501c54aadd3e6ad04dcf209ec3898d7c0e65d8e65ae9ab4e5",
            current,
        )
        self.assertIn("integrated_production_acceptance_owner_decision_packet_ready: true", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_packet_state_hash: de807ff8c395bfda9db6edb4aadacb1e1bdb0e076b4025ed3daca7a2402da289",
            current,
        )
        self.assertIn("owner_authorized_controlled_real_run_acceptance_passed: true", current)
        self.assertIn("integrated_production_acceptance_write_gate_precheck_ready: true", current)
        self.assertIn("integrated_production_acceptance_write_gate_allowed: false", current)
        self.assertIn(
            "integrated_production_acceptance_write_gate_state_hash: 48bd21b374fb86b91ab1a684af5bc8f5d2d7a7be752b85d75fe9f8bb9f43bcd8",
            current,
        )
        self.assertIn("owner_authorized_controlled_real_run_duplicate_send_avoided: true", current)
        self.assertIn("owner_authorized_controlled_real_run_newly_sent_mail_products: []", current)
        self.assertIn("owner_authorized_controlled_real_run_post_smtp_flag: false", current)
        self.assertIn("owner_authorized_controlled_real_run_background_process_count_after: 0", current)
        self.assertIn("integrated_production_acceptance_owner_decision_request_ready: true", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_request_state_hash: b406be2981f67b316df5ceba4469cc8fc3b96364a031c179bca9904f008bd9ea",
            current,
        )
        self.assertIn(
            "integrated_production_acceptance_owner_decision_request_artifact: FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json",
            current,
        )
        self.assertIn("integrated_production_acceptance_owner_decision_request_only: true", current)
        self.assertIn("integrated_production_acceptance_owner_decision_request_write_gate_allowed: false", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_request_runtime_enablement_allowed: false",
            current,
        )
        self.assertIn("owner_production_boundary_decision_recorded: false", current)
        self.assertIn("final_bundle_present: true", current)
        self.assertIn("s2plt04_completed: true", current)
        self.assertIn("independent_final_review_passed: true", current)
        self.assertIn("final_commands_executed: true", current)
        self.assertIn("current_zero_proof_open_p0_findings: 0", current)
        self.assertIn("current_zero_proof_open_p1_findings: 0", current)
        self.assertIn("inherited_v7_1_baseline_p0_findings: 8", current)
        self.assertIn("inherited_v7_1_baseline_p1_findings: 37", current)
        self.assertIn("stage2_integrated_production_accepted: false", current)
        self.assertIn("Acceptance write gate 预检查已完成", decisions)
        self.assertIn("Owner 决策请求模板已准备", decisions)
        self.assertIn("owner_production_boundary_decision.request.json", decisions)
        self.assertIn("acceptance_write_gate_allowed=false", decisions)
        self.assertIn("受控真实运行验收已完成", decisions)
        self.assertIn("newly_sent_mail_products=[]", decisions)
        self.assertIn("Preflight 已通过", decisions)
        self.assertIn("owner production-boundary decision", decisions)
        self.assertIn("不得自动启用 SMTP/scheduler/Release/restore", decisions)
        self.assertIn("Acceptance write gate 预检查已准备", readme)
        self.assertIn("Owner 决策请求模板已公开", readme)
        self.assertIn("owner_production_boundary_decision.request.json", readme)
        self.assertIn("acceptance_write_gate_allowed=false", readme)
        self.assertIn("受控真实运行验收复核已通过", readme)
        self.assertIn("Production-boundary preflight 已通过", readme)
        self.assertIn("Stage2/S3 production accepted", readme)
        self.assertIn("受控真实运行验收", roadmap)
        self.assertIn("owner decision request 模板", roadmap)
        self.assertIn("acceptance write gate 预检查已准备", roadmap)
        self.assertIn("Production-boundary preflight 已通过", roadmap)
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
        self.assertIn("- current_task: `S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE`", summary)
        self.assertIn("- next_gate: `S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION`", summary)
        self.assertIn("Acceptance write-gate precheck ready", summary)
        self.assertIn("controlled foreground real-run acceptance recheck passed without duplicate send", summary)


if __name__ == "__main__":
    unittest.main()
