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
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertEqual([result["status"] for result in payload["command_results"]], ["pass", "pass"])

    def test_verify_acceptance_bundle_root_tool_fails_closed_until_bundle_complete(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/verify_acceptance_bundle.py", "--require-zero", "P0", "P1"],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["required_zero"], ["P0", "P1"])
        self.assertEqual(payload["missing_required_zero"], [])
        self.assertTrue(payload["zero_checks"]["P0"])
        self.assertTrue(payload["zero_checks"]["P1"])
        self.assertEqual(payload["bundle_status"], "blocked")
        self.assertIn("final_acceptance_bundle_manifest_missing", payload["blocking_reasons"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])


if __name__ == "__main__":
    unittest.main()
