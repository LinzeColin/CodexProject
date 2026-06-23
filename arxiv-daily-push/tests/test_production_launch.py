from __future__ import annotations

import unittest
from pathlib import Path

from arxiv_daily_push.production_launch import build_production_launch_readiness, validate_production_launch_readiness

ROOT = Path(__file__).resolve().parents[2]

def pr_info() -> dict:
    return {"state": "MERGED", "merged": True, "draft": False, "base": "main", "head_sha": "abc123"}

class ProductionLaunchTests(unittest.TestCase):
    def test_launch_ready_without_release_target_ref(self) -> None:
        report = build_production_launch_readiness(
            ROOT,
            generated_at="2026-07-01T04:00:00+10:00",
            pr_info=pr_info(),
            expected_head_sha="abc123",
            default_branch_ref="git://repo/main@abc123",
            runner_ref="github-actions://runner/ubuntu-latest",
            smtp_secret_ref="github-secrets://actions/smtp",
            workflow_vars_ref="github-vars://actions/workflow-vars",
            trial_start_workflow_ref="github-actions://workflow/trial-start",
            confirm_launch=True,
        )
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["production_launch_ready"])
        self.assertNotIn("release_target_ref", report["evidence_refs"])
        self.assertFalse(validate_production_launch_readiness(report))

    def test_launch_blocks_without_confirm(self) -> None:
        report = build_production_launch_readiness(ROOT, generated_at="2026-07-01T04:00:00+10:00", pr_info=pr_info(), expected_head_sha="abc123")
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_launch_ready"])
        self.assertTrue(report["blocking_reasons"])

if __name__ == "__main__":
    unittest.main()
