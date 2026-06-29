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

    def test_current_state_summary_describes_s2plt02_real_proof_capture_readiness(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "S2PLT02_REAL_PROOF_CAPTURE_READINESS_BLOCKED_NO_AUTHORIZATION_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-READINESS", current_state)
        self.assertIn("safe_to_collect_terminal_proof=false", current_state)
        self.assertIn("real_proof_capture_authorized=false", current_state)
        self.assertIn("all_required_launchagents_disabled=true", current_state)
        self.assertIn("second_real_delivery_day_present=false", current_state)
        self.assertIn("terminal_delivery_proof_artifact_present=false", current_state)
        self.assertIn("real_scheduler_proven=false", current_state)
        self.assertIn("819b1c3911892ce861fd5ba5bdde0dc381e303076beea684f35eb94c75975463", current_state)
        self.assertIn("real_proof_capture_authorization_missing", current_state)
        self.assertIn("required_launchagents_disabled", current_state)
        self.assertIn("second_real_delivery_day_missing", current_state)
        self.assertIn("dry_run_second_day_not_terminal", current_state)
        self.assertIn("s2plt02_terminal_delivery_proof_artifact_missing", current_state)
        self.assertIn("real_scheduler_not_proven", current_state)
        self.assertIn("no production acceptance", current_state.lower())

    def test_owner_next_action_points_to_s2plt02_real_proof_capture_authorization(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        stale_option = "继续 S2PLT02 no-production readiness evidence work under V7.2 boundaries"
        self.assertIn('task_id: "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION"', assurance)
        self.assertIn("next_task_id: `S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION`", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT`", owner_status)
        for text in (assurance, owner_status):
            text_lower = text.lower()
            self.assertIn("S2PMT07", text)
            self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION", text)
            self.assertIn("ACC-S2PMT07-FINAL-REVIEW", text)
            self.assertIn("real smtp/scheduler", text_lower)
            self.assertIn("P0/P1 zero-proof", text)
            self.assertIn("owner authorization", text_lower)
            self.assertNotIn(stale_option, text)
        self.assertIn("adp_s2pmt07_blocked_next_task", generator)
        self.assertIn("real_proof_capture_is_next", generator)
        self.assertIn("current_v7_task_id", generator)

    def test_user_center_default_next_step_prioritizes_s2pmt07_final_review(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        default_next = decisions.split("## 默认下一步", 1)[1]
        first_action_row = next(
            line for line in default_next.splitlines() if line.startswith("| 1 |")
        )

        self.assertIn("S2PMT07", first_action_row)
        self.assertIn("独立终审", first_action_row)
        self.assertNotIn("候选池", first_action_row)
        self.assertNotIn("评分标准公开", first_action_row)
        self.assertIn("独立终审 reviewer assignment artifact", default_next)
        self.assertNotIn("| 无冲突的影子数据源证据 | 可以 |", roadmap)
        self.assertIn("S2PMT07 阻断期暂停新增影子数据源", roadmap)


if __name__ == "__main__":
    unittest.main()
