from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_launch import (
    PRODUCTION_LAUNCH_MODEL_ID,
    build_production_launch_readiness,
    validate_production_launch_readiness,
)


ROOT = Path(__file__).resolve().parents[2]


def merged_pr_info() -> dict:
    return {
        "state": "closed",
        "merged": True,
        "draft": False,
        "mergeable": None,
        "base": "main",
        "head": "codex/arxiv-daily-push-phase1-20260621",
        "head_sha": "abc123",
        "changed_files": 179,
    }


def current_blocked_pr_info() -> dict:
    return {
        "state": "open",
        "merged": False,
        "draft": True,
        "mergeable": False,
        "base": "main",
        "head": "codex/arxiv-daily-push-phase1-20260621",
        "head_sha": "fc5a100",
        "changed_files": 179,
    }


def refs() -> dict[str, str]:
    return {
        "default_branch_ref": "git://LinzeColin/CodexProject/main@abc123",
        "runner_ref": "github-runner://arxiv-daily-push/private-runner-01",
        "smtp_secret_ref": "github-secrets://LinzeColin/CodexProject/actions/ADP_SMTP",
        "release_target_ref": "github-vars://LinzeColin/CodexProject/actions/ADP_RELEASE_TARGET",
        "workflow_vars_ref": "github-vars://LinzeColin/CodexProject/actions/ADP_ALLOW_PROBES",
        "trial_start_workflow_ref": "github-actions://LinzeColin/CodexProject/.github/workflows/arxiv-daily-push-trial-start.yml@main",
    }


def launch_kwargs(**overrides) -> dict:
    kwargs = {
        "generated_at": "2026-07-01T04:30:00+10:00",
        "pr_info": merged_pr_info(),
        "expected_head_sha": "abc123",
        "confirm_launch": True,
    }
    kwargs.update(refs())
    kwargs.update(overrides)
    return kwargs


class ProductionLaunchTests(unittest.TestCase):
    def test_launch_readiness_passes_when_pr_merged_and_refs_exist(self) -> None:
        report = build_production_launch_readiness(ROOT, **launch_kwargs())

        self.assertEqual(report["model_id"], PRODUCTION_LAUNCH_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["production_launch_ready"])
        self.assertFalse(report["side_effects_performed"])
        self.assertFalse(report["secret_values_logged"])
        self.assertFalse(report["codex_auth_read"])
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(validate_production_launch_readiness(report))

    def test_launch_readiness_blocks_current_draft_unmerged_pr(self) -> None:
        report = build_production_launch_readiness(
            ROOT,
            **launch_kwargs(
                pr_info=current_blocked_pr_info(),
                expected_head_sha="fc5a100",
                confirm_launch=False,
                runner_ref="runner-01",
            ),
        )

        reasons = " ".join(report["blocking_reasons"])
        self.assertEqual(report["status"], "blocked")
        self.assertIn("confirm_launch must be true", reasons)
        self.assertIn("PR must not be draft", reasons)
        self.assertIn("PR must be merged", reasons)
        self.assertIn("runner_ref must be a durable ref", reasons)
        self.assertFalse(validate_production_launch_readiness(report))

    def test_launch_readiness_blocks_head_sha_mismatch(self) -> None:
        report = build_production_launch_readiness(ROOT, **launch_kwargs(expected_head_sha="different"))

        self.assertEqual(report["status"], "blocked")
        self.assertIn("does not match expected different", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_production_launch_readiness(report))

    def test_cli_plan_production_launch_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pr_path = Path(tmp) / "pr-info.json"
            pr_path.write_text(json.dumps(merged_pr_info(), ensure_ascii=False), encoding="utf-8")

            buffer = io.StringIO()
            args = [
                "plan-production-launch",
                "--path",
                str(ROOT),
                "--pr-info",
                str(pr_path),
                "--generated-at",
                "2026-07-01T04:30:00+10:00",
                "--expected-head-sha",
                "abc123",
                "--confirm-launch",
                "--json",
            ]
            for key, value in refs().items():
                args.extend(["--" + key.replace("_", "-"), value])
            with redirect_stdout(buffer):
                result = main(args)

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], PRODUCTION_LAUNCH_MODEL_ID)
        self.assertTrue(payload["production_launch_ready"])


if __name__ == "__main__":
    unittest.main()
