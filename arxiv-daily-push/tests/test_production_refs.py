from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_refs import (
    PRODUCTION_REFS_VALIDATOR_ID,
    build_production_refs_input_template,
    build_production_refs_report,
    validate_production_refs_report,
)


def readiness_input(**overrides) -> dict:
    payload = {
        "runner": {
            "ready": True,
            "label": "arxiv-daily-push",
            "evidence_ref": "github-runner://LinzeColin/CodexProject/arxiv-daily-push",
        },
        "smtp_secrets": {
            "ready": True,
            "secret_names": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
            "evidence_ref": "github-secrets://LinzeColin/CodexProject/actions/smtp",
        },
        "release_target": {
            "ready": True,
            "var_name": "ADP_RELEASE_TARGET",
            "target": "main",
            "evidence_ref": "github-vars://LinzeColin/CodexProject/actions/ADP_RELEASE_TARGET",
        },
        "workflow_vars": {
            "ready": True,
            "var_names": ["ADP_RELEASE_TARGET", "ADP_ALLOW_SMTP_SEND", "ADP_ALLOW_RELEASE_UPLOAD"],
            "evidence_ref": "github-vars://LinzeColin/CodexProject/actions/workflow-vars",
        },
    }
    payload.update(overrides)
    return payload


class ProductionRefsTests(unittest.TestCase):
    def test_production_refs_pass_with_no_secret_values(self) -> None:
        report = build_production_refs_report(readiness_input(), generated_at="2026-07-01T04:20:00+10:00")

        self.assertEqual(report["validator_id"], PRODUCTION_REFS_VALIDATOR_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["production_refs_ready"])
        self.assertFalse(report["side_effects_performed"])
        self.assertFalse(report["secret_values_logged"])
        self.assertFalse(report["codex_auth_read"])
        self.assertFalse(report["workflow_dispatched"])
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(validate_production_refs_report(report))

    def test_production_refs_block_secret_like_payload(self) -> None:
        payload = readiness_input(
            smtp_secrets={
                "ready": True,
                "secret_names": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
                "secret_values": {"ADP_SMTP_PASSWORD": "sk-real-secret"},
                "evidence_ref": "github-secrets://LinzeColin/CodexProject/actions/smtp",
            }
        )

        report = build_production_refs_report(payload, generated_at="2026-07-01T04:20:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("must not contain secret or credential values", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_production_refs_report(report))

    def test_production_refs_block_missing_smtp_secret_name(self) -> None:
        payload = readiness_input(
            smtp_secrets={
                "ready": True,
                "secret_names": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME"],
                "evidence_ref": "github-secrets://LinzeColin/CodexProject/actions/smtp",
            }
        )

        report = build_production_refs_report(payload, generated_at="2026-07-01T04:20:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("ADP_SMTP_PASSWORD", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_production_refs_report(report))

    def test_production_refs_template_contains_only_no_secret_names_and_blocks_until_filled(self) -> None:
        template = build_production_refs_input_template(
            runner_label="arxiv-daily-push-prod",
            release_target="adp-private",
        )

        self.assertEqual(template["runner"]["label"], "arxiv-daily-push-prod")
        self.assertFalse(template["runner"]["ready"])
        self.assertEqual(template["smtp_secrets"]["secret_names"], ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"])
        self.assertNotIn("secret_values", template["smtp_secrets"])
        self.assertNotIn("sk-", json.dumps(template, ensure_ascii=False).lower())

        report = build_production_refs_report(template, generated_at="2026-07-01T04:20:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("runner.ready must be true", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_production_refs_report(report))

    def test_cli_plan_production_refs_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "production-refs-input.json"
            input_path.write_text(json.dumps(readiness_input(), ensure_ascii=False), encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "plan-production-refs",
                        "--readiness-input",
                        str(input_path),
                        "--generated-at",
                        "2026-07-01T04:20:00+10:00",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], PRODUCTION_REFS_VALIDATOR_ID)
        self.assertTrue(payload["production_refs_ready"])

    def test_cli_print_production_refs_template_outputs_no_secret_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "print-production-refs-template",
                    "--runner-label",
                    "arxiv-daily-push-prod",
                    "--release-target",
                    "adp-private",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["runner"]["label"], "arxiv-daily-push-prod")
        self.assertEqual(payload["release_target"]["target"], "adp-private")
        self.assertEqual(payload["workflow_vars"]["var_names"], ["ADP_RELEASE_TARGET", "ADP_ALLOW_SMTP_SEND", "ADP_ALLOW_RELEASE_UPLOAD"])
        self.assertNotIn("secret_values", json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
