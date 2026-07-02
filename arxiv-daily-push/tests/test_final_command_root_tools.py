from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FinalCommandRootToolTests(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        return {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(REPO_ROOT / "arxiv-daily-push" / "src"),
        }

    def test_validate_task_pack_root_tool_passes_without_production_side_effects(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/validate_task_pack.py", "--root", "."],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["contract_id"], "ADP-PRODUCT-CONTRACT-V7.2")
        self.assertEqual(payload["task_id"], "S2PMT07")
        self.assertTrue(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertEqual([result["status"] for result in payload["command_results"]], ["pass", "pass"])

    def test_verify_acceptance_bundle_root_tool_accepts_final_command_prerequisites(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/verify_acceptance_bundle.py", "--require-zero", "P0", "P1"],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["required_zero"], ["P0", "P1"])
        self.assertEqual(payload["missing_required_zero"], [])
        self.assertTrue(payload["zero_checks"]["P0"])
        self.assertTrue(payload["zero_checks"]["P1"])
        self.assertEqual(payload["bundle_status"], "pass")
        self.assertTrue(payload["bundle_complete"])
        self.assertFalse(payload["final_command_prerequisite_ready"])
        self.assertIsNone(payload["next_required_step"])
        self.assertIsNone(payload["next_executable_task"])
        self.assertEqual(payload["s2plt04_completion_report_status"], "pass")
        self.assertEqual(payload["blocking_reasons"], [])
        self.assertFalse(payload["daily_operation_authorization_ready"])
        self.assertEqual(
            payload["daily_operation_blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )
        self.assertEqual(
            payload["daily_operation_next_required_step"],
            "OBTAIN_EXPLICIT_OWNER_PERSISTENT_DAILY_OPERATION_AUTHORIZATION",
        )
        self.assertEqual(
            payload["daily_operation_next_executable_task"],
            "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
        )
        self.assertEqual(
            payload["daily_operation_persistent_authorization_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json",
        )
        self.assertEqual(
            payload["daily_operation_gate_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json",
        )
        self.assertTrue(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])

    def test_verify_daily_operation_readiness_root_tool_fails_closed_without_authorization(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/verify_daily_operation_readiness.py"],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertEqual(
            payload["blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )
        self.assertEqual(
            payload["next_required_step"],
            "OBTAIN_EXPLICIT_OWNER_PERSISTENT_DAILY_OPERATION_AUTHORIZATION",
        )
        self.assertEqual(
            payload["authorization_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json",
        )
        self.assertEqual(payload["validation_errors"], [])


if __name__ == "__main__":
    unittest.main()
