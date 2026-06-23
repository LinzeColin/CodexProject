from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from email.message import EmailMessage
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_preflight import PRODUCTION_REQUIRED_COMMANDS, PRODUCTION_SECRET_ENV_KEYS, build_production_preflight
from arxiv_daily_push.scheduled_execution import SCHEDULED_EXECUTION_MODEL_ID, run_scheduled_execution, validate_scheduled_execution_report

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_INPUT = ROOT / "arxiv-daily-push/tests/fixtures/pipeline_input.json"


def complete_env(**extra: str) -> dict[str, str]:
    env = {key: f"present-{key.lower()}" for key in PRODUCTION_SECRET_ENV_KEYS}
    env.update({"ADP_SMTP_HOST": "smtp.example.invalid", "ADP_SMTP_PORT": "587", "ADP_SMTP_USERNAME": "sender@example.invalid", "ADP_SMTP_PASSWORD": "super-secret-password"})
    env.update(extra)
    return env


def command_resolver(command: str) -> str | None:
    return f"/usr/local/bin/{command}" if command in PRODUCTION_REQUIRED_COMMANDS else None


def preflight_pass(env: dict[str, str] | None = None) -> dict:
    return build_production_preflight(ROOT, generated_at="2026-07-01T04:45:00+10:00", env=env or complete_env(), command_resolver=command_resolver, disk_free_gib=120.0, memory_total_gib=16.0, git_scan={"gate_id": "git_artifact_hygiene", "passed": True, "blocking_reasons": [], "violations": []})


def production_daily_input_payload() -> dict:
    payload = json.loads(PIPELINE_INPUT.read_text(encoding="utf-8"))
    payload["queue_summary"] = {"queue_model_id": "adp-candidate-queue-v1", "queued_item_count": 1, "top_queued": [{"source_id": "arxiv:2401.00002", "title": "Queued high-value arXiv candidate", "roi_total_score": 87.0, "primary_category": "q-fin.PM"}]}
    payload["artifact_paths"] = {"delivery_policy": "adp-text-delivery-policy.json"}
    return payload


class ScheduledExecutionTests(unittest.TestCase):
    def test_health_check_succeeds_with_passed_preflight_and_dry_run_notification(self) -> None:
        report = run_scheduled_execution(mode="health-check", generated_at="2026-07-01T04:45:00+10:00", preflight_report=preflight_pass(), env=complete_env())
        self.assertEqual(report["validator_id"], SCHEDULED_EXECUTION_MODEL_ID)
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["notification_report"]["status"], "dry_run")
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_blocks_until_scheduled_run_enabled(self) -> None:
        report = run_scheduled_execution(mode="daily-run", generated_at="2026-07-01T05:00:00+10:00", preflight_report=preflight_pass(), env=complete_env(), daily_input_path=PIPELINE_INPUT)
        self.assertEqual(report["status"], "blocked")
        self.assertIn("ADP_SCHEDULED_RUN_ENABLED", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_degrades_when_smtp_is_still_dry_run(self) -> None:
        report = run_scheduled_execution(mode="daily-run", generated_at="2026-07-01T05:00:00+10:00", preflight_report=preflight_pass(), env=complete_env(ADP_SCHEDULED_RUN_ENABLED="true"), daily_input=production_daily_input_payload())
        self.assertEqual(report["status"], "degraded")
        self.assertFalse(report["production_evidence_ready"])
        self.assertFalse(report["delivery_package"]["video_required"])
        self.assertFalse(report["delivery_package"]["release_required"])
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_production_ready_with_real_smtp_and_text_artifact(self) -> None:
        class FakeSMTP:
            sent_messages: list[EmailMessage] = []
            def __init__(self, host, port, timeout): pass
            def __enter__(self): return self
            def __exit__(self, exc_type, exc, traceback): return False
            def starttls(self): return None
            def login(self, username, password): return None
            def send_message(self, message):
                FakeSMTP.sent_messages.append(message)
                return {}

        report = run_scheduled_execution(mode="daily-run", generated_at="2026-07-01T05:00:00+10:00", preflight_report=preflight_pass(), env=complete_env(ADP_SCHEDULED_RUN_ENABLED="true", ADP_ALLOW_SMTP_SEND="true"), daily_input=production_daily_input_payload(), smtp_factory=FakeSMTP)
        self.assertEqual(report["status"], "succeeded")
        self.assertTrue(report["production_evidence_ready"])
        self.assertEqual(report["notification_report"]["status"], "sent")
        self.assertTrue(report["evidence_refs"]["text_artifact_ref"])
        self.assertFalse(report["delivery_package"]["video_required"])
        self.assertFalse(report["delivery_package"]["release_required"])
        self.assertFalse(report["delivery_package"]["email_contains_video_link"])
        email_body = FakeSMTP.sent_messages[0].get_body(preferencelist=("plain",)).get_content()
        self.assertIn("【今天学什么】", email_body)
        self.assertIn("候选队列摘要", email_body)
        self.assertNotIn("视频入口", email_body)
        self.assertNotIn("Release 资料包", email_body)
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_cli_run_scheduled_production_outputs_json(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            preflight_path = Path(tmp) / "preflight.json"
            preflight_path.write_text(json.dumps(preflight_pass()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["run-scheduled-production", "--mode", "health-check", "--generated-at", "2026-07-01T04:45:00+10:00", "--preflight-report", str(preflight_path), "--json"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], SCHEDULED_EXECUTION_MODEL_ID)


if __name__ == "__main__":
    unittest.main()
