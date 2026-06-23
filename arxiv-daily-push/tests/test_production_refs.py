from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_refs import build_production_refs_input_from_github_metadata, build_production_refs_input_template, build_production_refs_report, validate_production_refs_report


def readiness_input() -> dict:
    return {
        "runner": {"ready": True, "provider": "github-hosted", "label": "ubuntu-latest", "evidence_ref": "github-runners://LinzeColin/CodexProject/ubuntu-latest"},
        "smtp_secrets": {"ready": True, "secret_names": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"], "evidence_ref": "github-secrets://LinzeColin/CodexProject/actions/smtp"},
        "workflow_vars": {"ready": True, "var_names": ["ADP_ALLOW_SMTP_SEND"], "evidence_ref": "github-vars://LinzeColin/CodexProject/actions/workflow-vars"},
    }

class ProductionRefsTests(unittest.TestCase):
    def test_refs_report_ready_without_release_target(self) -> None:
        report = build_production_refs_report(readiness_input(), generated_at="2026-07-01T04:00:00+10:00")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["production_refs_ready"])
        self.assertNotIn("release_target_ref", report["readiness_refs"])
        self.assertFalse(validate_production_refs_report(report))

    def test_template_contains_only_stage1_sections(self) -> None:
        payload = build_production_refs_input_template(runner_label="ubuntu-latest")
        self.assertIn("runner", payload)
        self.assertIn("smtp_secrets", payload)
        self.assertIn("workflow_vars", payload)
        self.assertNotIn("release_target", payload)
        self.assertEqual(payload["workflow_vars"]["var_names"], ["ADP_ALLOW_SMTP_SEND"])

    def test_github_metadata_discovers_stage1_refs(self) -> None:
        payload = build_production_refs_input_from_github_metadata(
            repo="LinzeColin/CodexProject",
            runner_label="ubuntu-latest",
            secrets_metadata={"secrets": [{"name": "ADP_SMTP_HOST"}, {"name": "ADP_SMTP_PORT"}, {"name": "ADP_SMTP_USERNAME"}, {"name": "ADP_SMTP_PASSWORD"}]},
            variables_metadata={"variables": [{"name": "ADP_ALLOW_SMTP_SEND", "value": "false"}]},
            runners_metadata={"runners": [{"name": "Hosted", "status": "online", "busy": False, "labels": [{"name": "ubuntu-latest"}]}]},
        )
        self.assertTrue(payload["runner"]["ready"])
        self.assertTrue(payload["smtp_secrets"]["ready"])
        self.assertTrue(payload["workflow_vars"]["ready"])
        self.assertNotIn("release_target", payload)

    def test_cli_template_outputs_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["print-production-refs-template", "--runner-label", "ubuntu-latest"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertNotIn("release_target", payload)

    def test_cli_plan_refs_outputs_ready_json(self) -> None:
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "refs.json"
            path.write_text(json.dumps(readiness_input()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["plan-production-refs", "--readiness-input", str(path), "--generated-at", "2026-07-01T04:00:00+10:00", "--json"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertTrue(payload["production_refs_ready"])

if __name__ == "__main__":
    unittest.main()
