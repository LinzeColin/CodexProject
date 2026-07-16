from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "agent_loop"))

from settlement_policy import SettlementPolicyError, decide  # noqa: E402


class SettlementPolicyTest(unittest.TestCase):
    def test_required_terminal_matrix(self) -> None:
        fixture = json.loads(
            (ROOT / "tests" / "agent_loop" / "fixtures" / "settlement_cases.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(fixture["cases"]), 16)
        for case in fixture["cases"]:
            with self.subTest(case=case["name"]):
                payload = {**fixture["defaults"], **case["overrides"]}
                actual = decide(payload)
                for key, value in case["expected"].items():
                    self.assertEqual(actual[key], value)

    def test_invalid_boolean_fails_closed(self) -> None:
        with self.assertRaises(SettlementPolicyError):
            decide({"workflow_conclusion": "success", "pr_state": "open", "issue_open": "false"})

    def test_untrusted_orphan_is_never_deleted(self) -> None:
        fixture = json.loads(
            (ROOT / "tests" / "agent_loop" / "fixtures" / "settlement_cases.json").read_text(
                encoding="utf-8"
            )
        )
        payload = {
            **fixture["defaults"],
            "orphan": True,
            "pr_state": "missing",
            "trusted_marker": False,
        }
        self.assertEqual(decide(payload)["action"], "BLOCK")
        self.assertFalse(decide(payload)["delete_branch"])


if __name__ == "__main__":
    unittest.main()
