from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class WorkflowContractTest(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_required_ci_is_read_only_and_unfiltered(self) -> None:
        workflow = self.read(".github/workflows/project-governance.yml")
        top_permissions = workflow.split("permissions:", 1)[1].split("concurrency:", 1)[0]
        self.assertEqual(top_permissions.strip(), "contents: read")
        self.assertIn("pull_request:", workflow)
        self.assertIn("governance:", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIsNone(re.search(r"^\s+paths(?:-ignore)?:", workflow, re.MULTILINE))

    def test_settlement_is_api_only_and_separate_from_ci(self) -> None:
        workflow = self.read(".github/workflows/agent-loop-settlement.yml")
        self.assertIn('workflows: ["Project Governance"]', workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("workflow_run:", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn("AUTOMATION_C_TRANSACTION_V1", workflow)
        self.assertIn("branch tip drifted; exact deletion refused", workflow)
        self.assertIn("governance_run_id", workflow)
        self.assertIn("AUTOMATION_C_MAX_AGE_MINUTES", workflow)
        self.assertIn("ref_used_by_open_pr", workflow)
        self.assertIn("CLOSE_ACCIDENTAL_ISSUE", workflow)
        self.assertNotIn('method="POST"', workflow)
        for forbidden in (
            "actions/checkout@",
            "download-artifact",
            "upload-artifact",
            "restore-cache",
            "gh issue",
        ):
            self.assertNotIn(forbidden, workflow)

    def test_agent_runtime_has_no_issue_state_machine(self) -> None:
        runtime_files = list((ROOT / ".github" / "workflows").glob("agent-loop-*.yml"))
        runtime_files += list((ROOT / "scripts" / "agent_loop").glob("*.py"))
        for path in runtime_files:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("gh issue", text)
                self.assertIsNone(re.search(r"^\s{2}issues:\s*$", text, re.MULTILINE))
                for retired_state in ("agent:running", "agent:done", "agent:blocked"):
                    self.assertNotIn(retired_state, text)
        self.assertFalse((ROOT / ".github" / "ISSUE_TEMPLATE" / "codex-task.yml").exists())
        self.assertFalse((ROOT / "scripts" / "agent_loop" / "build_prefilled_issue_url.py").exists())

    def test_compatibility_workflow_is_validation_only(self) -> None:
        workflow = self.read(".github/workflows/agent-loop-run-approved-taskpack.yml")
        self.assertIn("contents: read", workflow)
        self.assertIn("mutation: none", workflow)
        for forbidden in ("contents: write", "pull-requests: write", "issues:", "gh pr create", "gh pr merge"):
            self.assertNotIn(forbidden, workflow)

    def test_review_roles_have_no_issue_permission(self) -> None:
        for name in (
            "agent-loop-review-existing-pr.yml",
            "agent-loop-retrospective.yml",
        ):
            with self.subTest(name=name):
                workflow = self.read(f".github/workflows/{name}")
                self.assertNotIn("issues: write", workflow)
                self.assertIn("persist-credentials: false", workflow)


if __name__ == "__main__":
    unittest.main()
