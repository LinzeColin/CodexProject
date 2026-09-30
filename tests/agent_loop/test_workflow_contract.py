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

    def test_agent_loop_workflows_are_retired(self) -> None:
        """Agent Loop 4 个 workflow 于 2026-09-30 随 Owner 决定退役；不得悄悄复活。"""
        self.assertEqual(list((ROOT / ".github" / "workflows").glob("agent-loop-*.yml")), [])

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


if __name__ == "__main__":
    unittest.main()
