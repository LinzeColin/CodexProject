from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quantlab.integrations.permissions import authorize_system_action
from quantlab.integrations.system_orchestrator import orchestrate_child_system


class SystemPermissionsTest(unittest.TestCase):
    def test_eva_os_can_write_finance_ledger_scope(self) -> None:
        decision = authorize_system_action("EVA_OS", "finance_ledger", "ledger.write", action="write")

        self.assertTrue(decision["allowed"], decision)

    def test_finance_ledger_cannot_write_policy_scope(self) -> None:
        decision = authorize_system_action("finance_ledger", "policy_intelligence", "policy.write", action="write")

        self.assertFalse(decision["allowed"], decision)

    def test_industry_research_cannot_write_finance_ledger_scope(self) -> None:
        decision = authorize_system_action("industry_research", "finance_ledger", "ledger.write", action="write")

        self.assertFalse(decision["allowed"], decision)

    def test_undeclared_scope_is_denied_by_default(self) -> None:
        decision = authorize_system_action("EVA_OS", "finance_ledger", "broker.order.submit", action="write")

        self.assertFalse(decision["allowed"], decision)

    def test_execute_requires_approval_id(self) -> None:
        decision = authorize_system_action("EVA_OS", "finance_ledger", "ledger.write", action="write", execute=True)

        self.assertFalse(decision["allowed"], decision)
        self.assertIn("approval_id", decision["reason"])

    def test_orchestrator_execute_is_denied_for_cross_domain_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ResearchBus.sqlite"
            with patch.dict(
                os.environ,
                {
                    "EVA_ORCHESTRATOR_EXECUTE_ALLOWED": "1",
                    "EVA_ORCHESTRATOR_EXECUTE_CALLERS": "finance_ledger",
                },
                clear=False,
            ):
                with self.assertRaises(PermissionError):
                    orchestrate_child_system(
                        "GovernmentPolicySystem",
                        action="health",
                        execute=True,
                        db_path=db_path,
                        requester_system="finance_ledger",
                        approval_token="APPROVAL-UNIT-TEST",
                    )


if __name__ == "__main__":
    unittest.main()
