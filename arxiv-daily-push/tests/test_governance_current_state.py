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

    def test_current_state_summary_describes_s2plt02_controlled_launchd_timeout_and_blockers(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn("S2PLT03_TERMINAL_RESILIENCE_PROOF_READY_NO_PRODUCTION_ACCEPTANCE", current_state)
        self.assertIn("S2PLT03-TERMINAL-RESILIENCE-PROOF", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json", current_state)
        self.assertIn("artifact_validation_state_hash=caac74172d784c536fc9a9444aff70264de723536ba873026c709da3e30cfb10", current_state)
        self.assertIn("acceptance_hash=dc1ba0e62e10bdfc3d45660ba2b6e5a33c4d383fdf2e11c6b529d0928e8e57ce", current_state)
        self.assertIn("next_executable_task=S2PLT04_COMPLETION_REPORT", current_state)
        self.assertIn("sha256=7413b69865d3529a4217f6e543da1bcb326fbeea16b8b75af304590ab91ef192", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("No Stage2/S3/integrated production acceptance is claimed", current_state)
        self.assertIn("Previous scheduler proof capture remains visible", current_state)
        self.assertIn("S2PLT02-REAL-SCHEDULER-PROOF-CAPTURE-PASS", current_state)
        self.assertIn("real_scheduler_proven=true", current_state)
        self.assertIn("scheduler_proof_ready=true", current_state)
        self.assertIn("ADP-S2PLT02-REAL-SCHEDULER-PROOF-CAPTURE-PASS-20260701.json", current_state)
        self.assertIn("Previous controlled real 20260701 run remains visible", current_state)
        self.assertIn("real_smtp_sent=true", current_state)
        self.assertIn("sent_mail_count=4", current_state)
        self.assertIn("PHASE_S2PLT03_TERMINAL_RESILIENCE_PROOF.md", ledger)

    def test_owner_next_action_points_to_s2plt04_completion_report(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        stale_option = "继续 S2PLT02 no-production readiness evidence work under V7.2 boundaries"
        self.assertIn('task_id: "S2PMT07-S2PLT04-COMPLETION-REPORT"', assurance)
        self.assertIn("next_task_id: `S2PMT07-S2PLT04-COMPLETION-REPORT`", owner_status)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", assurance)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", owner_status)
        self.assertIn("do not re-run S2PLT02 SMTP/scheduler capture", assurance)
        self.assertIn("do not re-run S2PLT02 SMTP/scheduler capture", owner_status)
        self.assertNotIn("next collect S2PLT02 terminal delivery proof", assurance)
        self.assertNotIn("next collect S2PLT02 terminal delivery proof", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT`", owner_status)
        for text in (assurance, owner_status):
            text_lower = text.lower()
            self.assertIn("S2PMT07", text)
            self.assertIn("validated independent reviewer assignment", text)
            self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", text)
            self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json", text)
            self.assertIn("S2PMT07-S2PLT04-COMPLETION-REPORT", text)
            self.assertIn("ACC-S2PMT07-FINAL-REVIEW", text)
            self.assertTrue("real" in text_lower or "真实" in text)
            self.assertIn("smtp", text_lower)
            self.assertIn("scheduler", text_lower)
            self.assertIn("P0/P1 zero-proof", text)
            self.assertIn("resilience", text_lower)
            self.assertNotIn(stale_option, text)
        for no_write_ref in (
            "S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR",
            "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION",
            "S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN",
            "S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY",
            "S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR",
            "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT",
            "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI",
            "S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY",
            "S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC",
            "S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN",
        ):
            self.assertIn(no_write_ref, assurance)
        assurance_lower = assurance.lower()
        self.assertIn("live authorization", assurance_lower)
        self.assertIn("input inventory", assurance_lower)
        self.assertIn("capture plan", assurance_lower)
        self.assertIn("manifest", assurance_lower)
        self.assertIn("normalized manifest", assurance_lower)
        self.assertIn("dry-run", assurance_lower)
        self.assertIn("adp_s2pmt07_blocked_next_task", generator)
        self.assertIn("terminal_delivery_proof_is_next", generator)
        self.assertIn("terminal_resilience_proof_is_next", generator)
        self.assertIn("s2plt02_terminal_delivery_accepted", generator)
        self.assertIn("current_v7_task_id", generator)

    def test_user_center_default_next_step_prioritizes_s2plt04_completion_report(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        latest_block = decisions.split("## 2026-07-01 13:16:19+10:00 Australia/Sydney", 1)[1].split("\n## ", 1)[0]

        self.assertIn("S2PLT03 terminal resilience proof artifact 已通过", latest_block)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json", latest_block)
        self.assertIn("默认下一步 `S2PLT04_COMPLETION_REPORT`", latest_block)
        self.assertIn("S2PLT04 evidence audit 已通过", latest_block)
        self.assertIn("不重复发送", latest_block)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", latest_block)
        self.assertIn("S2PLT02 terminal delivery proof 已通过", decisions)
        self.assertIn("默认下一步 `S2PLT04_COMPLETION_REPORT`", decisions)
        self.assertIn("独立最终复审人分配已验证", decisions)
        self.assertIn("validate-final-reviewer-assignment", decisions)
        self.assertIn("b5b117307bd61f168ae6a422b24c865227f4824191348b851081af66730ed2c2", decisions)
        self.assertIn("S2PLT02 terminal proof 输入仍不完整", decisions)
        self.assertIn("S2PLT02 terminal proof 捕获计划仍 blocked", decisions)
        self.assertIn("S2PLT02 capture-window CLI 已可复现但仍 blocked", decisions)
        self.assertIn("S2PLT02 real delivery manifest 输入门刚补齐", decisions)
        self.assertIn("S2PLT02 real delivery manifest 规范化输入已补齐", decisions)
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_INPUT_INVENTORY.md", decisions)
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN.md", decisions)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_INPUT_VALIDATOR.md", decisions)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION.md", decisions)
        self.assertNotIn("候选池", latest_block)
        self.assertNotIn("评分标准公开", latest_block)
        self.assertNotIn("独立终审 reviewer assignment artifact 准备", latest_block)
        self.assertIn("no-production attestation、independent reviewer assignment validator pass、P0/P1 zero-proof、S2PLT01 terminal acceptance 已是可用输入", decisions)
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
