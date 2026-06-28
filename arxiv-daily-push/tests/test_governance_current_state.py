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

    def test_s2pmt07_current_state_summary_describes_assignment_placeholder_gate(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_PLACEHOLDER_GATE_READY_NO_ASSIGNMENT_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-PLACEHOLDER-GATE", current_state)
        self.assertIn("validate_independent_final_reviewer_assignment_artifact", current_state)
        self.assertIn("REPLACE_WITH", current_state)
        self.assertIn("independent_final_reviewer_assignment.json", current_state)
        self.assertIn("assignment_artifact_present=false", current_state)
        self.assertIn("independent_final_reviewer_assigned=false", current_state)
        self.assertIn("independent_final_reviewer_assignment_missing", current_state)
        self.assertIn("P0=8", current_state)
        self.assertIn("P1=37", current_state)
        self.assertIn("directory-level final bundle artifact validation", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/templates/", current_state)
        self.assertIn("no_production_side_effects.json", current_state)
        self.assertIn("only one sub-artifact", current_state)
        self.assertIn("top-level final bundle readiness remain blocked", current_state)
        self.assertIn("independent review pass", current_state)
        self.assertNotIn("M4 watermark proof record", current_state)
        self.assertNotIn("m4_watermark_correct=true", current_state)

    def test_owner_next_action_points_to_s2pmt07_not_stale_s2plt02(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        stale_option = "继续 S2PLT02 no-production readiness evidence work under V7.2 boundaries"
        for text in (assurance, owner_status):
            self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT", text)
            self.assertIn("ACC-S2PMT07-FINAL-REVIEW", text)
            self.assertIn("independent final reviewer assignment", text)
            self.assertNotIn(stale_option, text)
            self.assertNotIn("ACC-S2PLT02-2D", text)
        self.assertIn("adp_s2pmt07_blocked_next_task", generator)
        self.assertIn("adp_s2pmt07_gate_is_current", generator)
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
