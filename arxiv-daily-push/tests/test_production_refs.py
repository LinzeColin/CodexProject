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
    PROVISIONING_AUDIT_REVIEW_ID,
    ProductionRefsDiscoveryError,
    build_production_refs_input_from_github_metadata,
    build_production_refs_input_template,
    build_production_refs_report,
    build_provisioning_audit_review,
    discover_production_refs_input_with_gh,
    validate_production_refs_report,
    validate_provisioning_audit_review,
)


ROOT = Path(__file__).resolve().parents[2]


def readiness_input(**overrides) -> dict:
    payload = {
        "runner": {
            "ready": True,
            "provider": "github-hosted",
            "label": "ubuntu-latest",
            "evidence_ref": "github-hosted://LinzeColin/CodexProject/actions/ubuntu-latest",
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
            runner_label="ubuntu-latest",
            release_target="adp-private",
        )

        self.assertEqual(template["runner"]["provider"], "github-hosted")
        self.assertEqual(template["runner"]["label"], "ubuntu-latest")
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

    def test_provisioning_audit_review_passes_with_durable_artifact_refs(self) -> None:
        refs_report = build_production_refs_report(readiness_input(), generated_at="2026-07-01T04:20:00+10:00")

        review = build_provisioning_audit_review(
            refs_report,
            generated_at="2026-07-01T04:25:00+10:00",
            workflow_run_ref="github-actions://LinzeColin/CodexProject/actions/runs/123456",
            artifact_ref="github-artifact://LinzeColin/CodexProject/actions/runs/123456/adp-production-provisioning-audit",
        )

        self.assertEqual(review["validator_id"], PROVISIONING_AUDIT_REVIEW_ID)
        self.assertEqual(review["status"], "pass")
        self.assertTrue(review["provisioning_audit_ready"])
        self.assertEqual(review["readiness_refs"], refs_report["readiness_refs"])
        self.assertFalse(review["side_effects_performed"])
        self.assertFalse(review["secret_values_logged"])
        self.assertFalse(review["codex_auth_read"])
        self.assertFalse(review["workflow_dispatched"])
        self.assertFalse(review["smtp_sent"])
        self.assertFalse(review["release_uploaded"])
        self.assertFalse(review["production_acceptance_claimed"])
        self.assertFalse(validate_provisioning_audit_review(review))

    def test_provisioning_audit_review_blocks_missing_artifact_refs(self) -> None:
        refs_report = build_production_refs_report(readiness_input(), generated_at="2026-07-01T04:20:00+10:00")

        review = build_provisioning_audit_review(
            refs_report,
            generated_at="2026-07-01T04:25:00+10:00",
        )

        self.assertEqual(review["status"], "blocked")
        self.assertFalse(review["provisioning_audit_ready"])
        self.assertIn("workflow_run_ref must be a durable ref", " ".join(review["blocking_reasons"]))
        self.assertIn("artifact_ref must be a durable ref", " ".join(review["blocking_reasons"]))
        self.assertFalse(validate_provisioning_audit_review(review))

    def test_cli_review_provisioning_audit_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "adp-production-provisioning-audit.json"
            report_path.write_text(
                json.dumps(build_production_refs_report(readiness_input(), generated_at="2026-07-01T04:20:00+10:00"), ensure_ascii=False),
                encoding="utf-8",
            )

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "review-provisioning-audit",
                        "--production-refs-report",
                        str(report_path),
                        "--workflow-run-ref",
                        "github-actions://LinzeColin/CodexProject/actions/runs/123456",
                        "--artifact-ref",
                        "github-artifact://LinzeColin/CodexProject/actions/runs/123456/adp-production-provisioning-audit",
                        "--generated-at",
                        "2026-07-01T04:25:00+10:00",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], PROVISIONING_AUDIT_REVIEW_ID)
        self.assertTrue(payload["provisioning_audit_ready"])

    def test_cli_print_production_refs_template_outputs_no_secret_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "print-production-refs-template",
                    "--runner-label",
                    "ubuntu-latest",
                    "--release-target",
                    "adp-private",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["runner"]["provider"], "github-hosted")
        self.assertEqual(payload["runner"]["label"], "ubuntu-latest")
        self.assertEqual(payload["release_target"]["target"], "adp-private")
        self.assertEqual(payload["workflow_vars"]["var_names"], ["ADP_RELEASE_TARGET", "ADP_ALLOW_SMTP_SEND", "ADP_ALLOW_RELEASE_UPLOAD"])
        self.assertNotIn("secret_values", json.dumps(payload, ensure_ascii=False))

    def test_github_metadata_discovery_builds_ready_no_secret_input(self) -> None:
        payload = build_production_refs_input_from_github_metadata(
            repo="LinzeColin/CodexProject",
            runner_label="arxiv-daily-push",
            secrets_metadata={
                "secrets": [
                    {"name": "ADP_SMTP_HOST", "updated_at": "2026-07-01T00:00:00Z"},
                    {"name": "ADP_SMTP_PORT", "updated_at": "2026-07-01T00:00:00Z"},
                    {"name": "ADP_SMTP_USERNAME", "updated_at": "2026-07-01T00:00:00Z"},
                    {"name": "ADP_SMTP_PASSWORD", "updated_at": "2026-07-01T00:00:00Z"},
                ]
            },
            variables_metadata={
                "variables": [
                    {"name": "ADP_RELEASE_TARGET", "value": "main"},
                    {"name": "ADP_ALLOW_SMTP_SEND", "value": "true"},
                    {"name": "ADP_ALLOW_RELEASE_UPLOAD", "value": "true"},
                ]
            },
            runners_metadata={
                "runners": [
                    {
                        "name": "adp-runner",
                        "status": "online",
                        "busy": False,
                        "labels": [{"name": "self-hosted"}, {"name": "arxiv-daily-push"}],
                    }
                ]
            },
        )

        report = build_production_refs_report(payload, generated_at="2026-07-01T04:20:00+10:00")
        text = json.dumps(payload, ensure_ascii=False)
        self.assertTrue(payload["runner"]["ready"])
        self.assertTrue(payload["smtp_secrets"]["ready"])
        self.assertTrue(payload["release_target"]["ready"])
        self.assertTrue(payload["workflow_vars"]["ready"])
        self.assertEqual(report["status"], "pass")
        self.assertNotIn("super-secret-password", text)
        self.assertNotIn("credential-material", text)

    def test_github_metadata_discovery_blocks_missing_runner_label(self) -> None:
        payload = build_production_refs_input_from_github_metadata(
            repo="LinzeColin/CodexProject",
            runner_label="arxiv-daily-push",
            secrets_metadata={
                "secrets": [
                    {"name": "ADP_SMTP_HOST"},
                    {"name": "ADP_SMTP_PORT"},
                    {"name": "ADP_SMTP_USERNAME"},
                    {"name": "ADP_SMTP_PASSWORD"},
                ]
            },
            variables_metadata={
                "variables": [
                    {"name": "ADP_RELEASE_TARGET", "value": "main"},
                    {"name": "ADP_ALLOW_SMTP_SEND", "value": "true"},
                    {"name": "ADP_ALLOW_RELEASE_UPLOAD", "value": "true"},
                ]
            },
            runners_metadata={"runners": [{"name": "other", "status": "online", "labels": [{"name": "self-hosted"}]}]},
        )

        report = build_production_refs_report(payload, generated_at="2026-07-01T04:20:00+10:00")
        self.assertFalse(payload["runner"]["ready"])
        self.assertEqual(report["status"], "blocked")
        self.assertIn("runner.ready must be true", " ".join(report["blocking_reasons"]))

    def test_gh_discovery_error_redacts_stdout_and_stderr(self) -> None:
        class Result:
            returncode = 1
            stdout = "stdout-should-not-leak"
            stderr = "stderr-should-not-leak"

        def fake_runner(command: list[str]) -> Result:
            return Result()

        with self.assertRaises(ProductionRefsDiscoveryError) as context:
            discover_production_refs_input_with_gh(runner=fake_runner)

        message = str(context.exception)
        self.assertIn("gh api /repos/LinzeColin/CodexProject/actions/secrets failed", message)
        self.assertNotIn("stdout-should-not-leak", message)
        self.assertNotIn("stderr-should-not-leak", message)

    def test_provisioning_audit_workflow_is_github_hosted_and_no_secret(self) -> None:
        workflow = (ROOT / ".github/workflows/arxiv-daily-push-provisioning-audit.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertNotIn("runner_label", workflow)
        self.assertIn("secrets.ADP_SMTP_PASSWORD", workflow)
        self.assertIn("vars.ADP_RELEASE_TARGET", workflow)
        self.assertIn("plan-production-refs", workflow)
        self.assertIn("adp-production-provisioning-audit", workflow)
        self.assertIn("production_refs_ready=true", workflow)
        self.assertNotIn("auth.json", workflow)
        self.assertLess(workflow.index("plan-production-refs"), workflow.index("Stop if provisioning audit blocked"))


if __name__ == "__main__":
    unittest.main()
