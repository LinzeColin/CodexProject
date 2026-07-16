from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import workflow_security_audit as workflows  # noqa: E402


class WorkflowSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = workflows.load_policy()
        cls.expected_by_path = {
            item["path"]: item for item in cls.policy["workflows"]
        }
        cls.allowed_pins = {
            f"{item['repository']}@{item['commit_sha']}"
            for item in cls.policy["action_pins"]
        }
        requirements = cls.policy["requirements"]
        cls.forbidden_triggers = set(requirements["forbidden_triggers"])
        cls.forbidden_contexts = requirements["forbidden_direct_run_contexts"]

    def audit_text(self, path: str, text: str) -> list[str]:
        errors, _ = workflows.audit_workflow_text(
            text,
            self.expected_by_path[path],
            allowed_pins=self.allowed_pins,
            forbidden_triggers=self.forbidden_triggers,
            forbidden_direct_contexts=self.forbidden_contexts,
        )
        return errors

    def test_repository_meets_zero_violation_acceptance(self) -> None:
        summary = workflows.audit_repository()
        self.assertEqual(summary["status"], "PASS", summary["errors"])
        for field in {
            "unowned_workflow_count",
            "duplicate_role_count",
            "invalid_nested_workflow_count",
            "unpinned_actions",
            "unapproved_actions",
            "missing_timeouts",
            "missing_concurrency",
            "overbroad_permissions",
            "forbidden_triggers",
            "direct_context_violations",
            "high_privilege_violations",
        }:
            self.assertEqual(summary[field], 0, field)
        self.assertEqual(summary["transaction_ci_role_count"], 1)
        self.assertEqual(summary["settlement_role_count"], 1)

    def test_movable_action_tag_fails_closed(self) -> None:
        path = ".github/workflows/agent-loop-review-existing-pr.yml"
        text = (ROOT / path).read_text(encoding="utf-8")
        sha = "93cb6efe18208431cddfb8368fd83d5badbf9bfd"
        errors = self.audit_text(path, text.replace(sha, "v5", 1))
        self.assertTrue(any("not pinned to a full SHA" in error for error in errors), errors)

    def test_permission_drift_fails_closed(self) -> None:
        path = ".github/workflows/agent-loop-run-approved-taskpack.yml"
        text = (ROOT / path).read_text(encoding="utf-8")
        errors = self.audit_text(path, text.replace("contents: read", "contents: write", 1))
        self.assertTrue(any("permission matrix drift" in error for error in errors), errors)

    def test_direct_untrusted_shell_context_fails_but_environment_route_passes(self) -> None:
        path = ".github/workflows/agent-loop-run-approved-taskpack.yml"
        text = (ROOT / path).read_text(encoding="utf-8")
        unsafe = text.replace("run: |", "run: |\n          echo '${{ inputs.taskpack_path }}'", 1)
        errors = self.audit_text(path, unsafe)
        self.assertTrue(any("interpolated directly" in error for error in errors), errors)
        self.assertEqual(self.audit_text(path, text), [])

    def test_missing_timeout_and_concurrency_fail_closed(self) -> None:
        path = ".github/workflows/agent-loop-run-approved-taskpack.yml"
        text = (ROOT / path).read_text(encoding="utf-8")
        without_timeout = text.replace("    timeout-minutes: 5\n", "", 1)
        self.assertTrue(
            any("jobs missing timeout" in error for error in self.audit_text(path, without_timeout))
        )
        without_concurrency = text.replace(
            "concurrency:\n  group: agent-loop-taskpack-validation-${{ github.run_id }}\n  cancel-in-progress: false\n\n",
            "",
            1,
        )
        self.assertTrue(
            any("concurrency contract missing" in error for error in self.audit_text(path, without_concurrency))
        )

    def test_settlement_cannot_checkout_or_consume_actions(self) -> None:
        path = ".github/workflows/agent-loop-settlement.yml"
        text = (ROOT / path).read_text(encoding="utf-8")
        unsafe = text.replace(
            "      - name: Settle from trusted default-branch definition using live APIs only",
            "      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5\n"
            "      - name: Settle from trusted default-branch definition using live APIs only",
            1,
        )
        errors = self.audit_text(path, unsafe)
        self.assertTrue(any("high-privilege" in error for error in errors), errors)

    def test_duplicate_role_and_render_drift_fail(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["workflows"][1]["role"] = policy["workflows"][0]["role"]
        errors = workflows.validate_policy(policy)
        self.assertTrue(any("duplicate workflow role" in error for error in errors), errors)
        self.assertEqual(workflows.check_render()["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
