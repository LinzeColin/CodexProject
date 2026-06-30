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

    def test_current_state_summary_describes_s2plt02_terminal_delivery_proof_next(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_READY_NO_WRITE_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION", current_state)
        self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY", current_state)
        self.assertIn("S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER", current_state)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF", current_state)
        self.assertIn("ready inputs", current_state)
        self.assertIn("missing inputs", current_state)
        self.assertIn("SECOND_REAL_DELIVERY_DAY", current_state)
        self.assertIn("EIGHT_REAL_EMAILS", current_state)
        self.assertIn("REAL_SCHEDULER_PROOF", current_state)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", current_state)
        self.assertIn("CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY", current_state)
        self.assertIn("delivery_manifest_ready=true", current_state)
        self.assertIn("blocked_missing_explicit_no_production_flags", current_state)
        self.assertIn("ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json", current_state)
        self.assertIn("a795bd90778b5a0bbbd217d286f696936954af47a1a547ed689f907b677d9fa2", current_state)
        self.assertIn("91bf1a4477c621a75fceed90efecdb620341cfc97d5a751c127cc5ffbd6a0d99", current_state)
        self.assertIn("c56a7a1a5e9cb8a81ba0b05aa848c05e1577ce7558bae1700ea4563652c2d93c", current_state)
        self.assertIn("artifact_written=false", current_state)
        self.assertIn("scheduler_install_enabled=false", current_state)
        self.assertIn("daily_operation_enabled=false", current_state)
        self.assertIn("2026-06-29", current_state)
        self.assertIn("2026-06-30", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("terminal_delivery_credit=false", current_state)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", current_state)
        self.assertIn("1f5abf4e3def35129bc6a360722b10087880dfb49f904d6f9b267cb796d7f8f1", current_state)
        self.assertIn("s2plt02_terminal_delivery_proof_artifact_missing", current_state)
        self.assertIn("no production acceptance", current_state.lower())

    def test_owner_next_action_points_to_s2plt02_terminal_delivery_proof(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        stale_option = "继续 S2PLT02 no-production readiness evidence work under V7.2 boundaries"
        self.assertIn('task_id: "S2PLT02-TERMINAL-DELIVERY-PROOF"', assurance)
        self.assertIn("next_task_id: `S2PLT02-TERMINAL-DELIVERY-PROOF`", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT`", owner_status)
        for text in (assurance, owner_status):
            text_lower = text.lower()
            self.assertIn("S2PMT07", text)
            self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR", text)
            self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION", text)
            self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN", text)
            self.assertIn("S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY", text)
            self.assertIn("S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR", text)
            self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT", text)
            self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF", text)
            self.assertIn("ACC-S2PMT07-FINAL-REVIEW", text)
            self.assertIn("real", text_lower)
            self.assertIn("smtp", text_lower)
            self.assertIn("scheduler", text_lower)
            self.assertIn("P0/P1 zero-proof", text)
            self.assertIn("live authorization", text_lower)
            self.assertIn("input inventory", text_lower)
            self.assertIn("capture plan", text_lower)
            self.assertIn("manifest", text_lower)
            self.assertIn("normalized manifest", text_lower)
            self.assertIn("dry-run", text_lower)
            self.assertNotIn(stale_option, text)
        self.assertIn("adp_s2pmt07_blocked_next_task", generator)
        self.assertIn("terminal_delivery_proof_is_next", generator)
        self.assertIn("current_v7_task_id", generator)

    def test_user_center_default_next_step_prioritizes_s2plt02_terminal_proof(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        default_next = decisions.split("## 默认下一步", 1)[1]
        first_action_row = next(
            line for line in default_next.splitlines() if line.startswith("| 1 |")
        )

        self.assertIn("S2PLT02 终态交付 proof", first_action_row)
        self.assertIn("capture plan", first_action_row)
        self.assertIn("validate-s2plt02-real-delivery-manifest", first_action_row)
        self.assertIn("CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY", first_action_row)
        self.assertIn("dry-run/scheduler-disabled", first_action_row)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json", default_next)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", default_next)
        self.assertIn("受控真实捕获窗口", default_next)
        self.assertIn("真实 launchd scheduler proof", default_next)
        self.assertIn("S2PLT02 terminal proof 输入仍不完整", decisions)
        self.assertIn("S2PLT02 terminal proof 捕获计划仍 blocked", decisions)
        self.assertIn("S2PLT02 real delivery manifest 输入门刚补齐", decisions)
        self.assertIn("S2PLT02 real delivery manifest 规范化输入已补齐", decisions)
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_INPUT_INVENTORY.md", decisions)
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN.md", decisions)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_INPUT_VALIDATOR.md", decisions)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION.md", decisions)
        self.assertNotIn("候选池", first_action_row)
        self.assertNotIn("评分标准公开", first_action_row)
        self.assertNotIn("独立终审 reviewer assignment artifact 准备", default_next)
        self.assertIn("no-production attestation、independent reviewer assignment、P0/P1 zero-proof、S2PLT01 terminal acceptance 已是可用输入", decisions)
        self.assertNotIn("| 无冲突的影子数据源证据 | 可以 |", roadmap)
        self.assertIn("S2PMT07 阻断期暂停新增影子数据源", roadmap)

    def test_three_base_model_parameter_summary_matches_governance_counts(self) -> None:
        model_spec = (ADP_ROOT / "docs/governance/MODEL_SPEC.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        model_params = (ADP_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        summary = model_params.split("\n## 2026-", 1)[0]

        model_count = re.search(r"(?m)^- model_count: (\d+)$", model_spec)
        active_formulas = re.search(r"(?m)^- active_formulas: `(\d+)`$", owner_status)
        active_parameters = re.search(r"(?m)^- active_parameters: `(\d+)`$", owner_status)
        if not model_count or not active_formulas or not active_parameters:
            raise AssertionError("governance model/formula/parameter counts are missing")

        self.assertIn(f"- active_model_count: `{model_count.group(1)}`", summary)
        self.assertIn(f"- active_formula_count: `{active_formulas.group(1)}`", summary)
        self.assertIn(f"- active_parameter_count: `{active_parameters.group(1)}`", summary)
        self.assertNotIn("- active_model_count: `120`", summary)
        self.assertNotIn("- active_formula_count: `122`", summary)
        self.assertNotIn("- active_parameter_count: `1073`", summary)


if __name__ == "__main__":
    unittest.main()
