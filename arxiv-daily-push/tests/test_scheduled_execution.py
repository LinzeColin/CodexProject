from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from email.message import EmailMessage
from pathlib import Path

from arxiv_daily_push.arxiv_adapter import ArxivQuery
from arxiv_daily_push.cli import main
from arxiv_daily_push.daily_input import build_daily_input_package
from arxiv_daily_push.production_preflight import PRODUCTION_REQUIRED_COMMANDS, PRODUCTION_SECRET_ENV_KEYS, build_production_preflight
from arxiv_daily_push.scheduled_execution import (
    SCHEDULED_EXECUTION_MODEL_ID,
    run_scheduled_execution,
    validate_scheduled_execution_report,
)
from arxiv_daily_push.source_ingest import ingest_latest_arxiv


ROOT = Path(__file__).resolve().parents[2]
PIPELINE_INPUT = ROOT / "arxiv-daily-push/tests/fixtures/pipeline_input.json"
ARXIV_FIXTURE = ROOT / "arxiv-daily-push/tests/fixtures/arxiv_atom_sample.xml"


def complete_env(**extra: str) -> dict[str, str]:
    env = {key: f"present-{key.lower()}" for key in PRODUCTION_SECRET_ENV_KEYS}
    env.update(
        {
            "ADP_SMTP_HOST": "smtp.example.invalid",
            "ADP_SMTP_PORT": "587",
            "ADP_SMTP_USERNAME": "sender@example.invalid",
            "ADP_SMTP_PASSWORD": "super-secret-password",
            "ADP_RELEASE_TARGET": "abc123",
        }
    )
    env.update(extra)
    return env


def command_resolver(command: str) -> str | None:
    return f"/usr/local/bin/{command}" if command in PRODUCTION_REQUIRED_COMMANDS else None


def preflight_pass(env: dict[str, str] | None = None) -> dict:
    return build_production_preflight(
        ROOT,
        generated_at="2026-07-01T04:45:00+10:00",
        env=env or complete_env(),
        command_resolver=command_resolver,
        disk_free_gib=120.0,
        memory_total_gib=16.0,
        git_scan={"gate_id": "git_artifact_hygiene", "passed": True, "blocking_reasons": [], "violations": []},
    )


def fixture_fetcher(query: ArxivQuery) -> str:
    assert query.search_query == "cat:cs.AI"
    return ARXIV_FIXTURE.read_text(encoding="utf-8")


def daily_input_builder_report() -> dict:
    batch = ingest_latest_arxiv(
        search_query="cat:cs.AI",
        generated_at="2026-07-01T05:00:00+10:00",
        max_results=1,
        fetcher=fixture_fetcher,
    )
    return build_daily_input_package(
        batch,
        date="2026-07-01",
        generated_at="2026-07-01T05:00:00+10:00",
    )


def production_daily_input_payload() -> dict:
    payload = json.loads(PIPELINE_INPUT.read_text(encoding="utf-8"))
    payload["queue_summary"] = {
        "queue_model_id": "adp-candidate-queue-v1",
        "queued_item_count": 1,
        "top_queued": [
            {
                "source_id": "arxiv:2401.00002",
                "title": "Queued high-value arXiv candidate",
                "roi_total_score": 87.0,
                "primary_category": "q-fin.PM",
            }
        ],
    }
    return payload


class ScheduledExecutionTests(unittest.TestCase):
    def test_health_check_succeeds_with_passed_preflight_and_dry_run_notification(self) -> None:
        report = run_scheduled_execution(
            mode="health-check",
            generated_at="2026-07-01T04:45:00+10:00",
            preflight_report=preflight_pass(),
            env=complete_env(),
        )

        self.assertEqual(report["validator_id"], SCHEDULED_EXECUTION_MODEL_ID)
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["notification_report"]["status"], "dry_run")
        self.assertFalse(report["side_effect_policy"]["secret_values_logged"])
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_blocks_until_scheduled_run_enabled(self) -> None:
        report = run_scheduled_execution(
            mode="daily-run",
            generated_at="2026-07-01T05:00:00+10:00",
            preflight_report=preflight_pass(),
            env=complete_env(),
            daily_input_path=PIPELINE_INPUT,
            release_asset_paths=[PIPELINE_INPUT],
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["exit_code"], 2)
        self.assertIn("ADP_SCHEDULED_RUN_ENABLED", " ".join(report["blocking_reasons"]))
        self.assertEqual(report["notification_report"]["status"], "dry_run")
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_degrades_when_side_effects_are_still_dry_run(self) -> None:
        report = run_scheduled_execution(
            mode="daily-run",
            generated_at="2026-07-01T05:00:00+10:00",
            preflight_report=preflight_pass(),
            env=complete_env(ADP_SCHEDULED_RUN_ENABLED="true"),
            daily_input_path=PIPELINE_INPUT,
            release_asset_paths=[PIPELINE_INPUT],
        )

        self.assertEqual(report["status"], "degraded")
        self.assertEqual(report["exit_code"], 2)
        self.assertFalse(report["production_evidence_ready"])
        self.assertEqual(report["release_report"]["status"], "dry_run")
        self.assertEqual(report["notification_report"]["status"], "dry_run")
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_accepts_daily_input_builder_report(self) -> None:
        report = run_scheduled_execution(
            mode="daily-run",
            generated_at="2026-07-01T05:00:00+10:00",
            preflight_report=preflight_pass(),
            env=complete_env(ADP_SCHEDULED_RUN_ENABLED="true"),
            daily_input=daily_input_builder_report(),
        )

        self.assertEqual(report["status"], "degraded")
        self.assertEqual(report["daily_run_report"]["status"], "succeeded")
        self.assertEqual(report["daily_run_report"]["run_id"], "daily:2026-07-01:arxiv:2401.00001")
        self.assertEqual(report["daily_run_report"]["source_id"], "arxiv:2401.00001")
        self.assertTrue(report["daily_run_report"]["p0_claims_traceable"])
        self.assertFalse(report["daily_run_report"]["unsupported_claims_published"])
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_daily_run_production_ready_only_with_real_smtp_and_release_evidence(self) -> None:
        release_commands: list[list[str]] = []

        class FakeSMTP:
            sent_messages: list[EmailMessage] = []

            def __init__(self, host, port, timeout):
                self.host = host
                self.port = port
                self.timeout = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def starttls(self):
                return None

            def login(self, username, password):
                return None

            def send_message(self, message):
                FakeSMTP.sent_messages.append(message)
                return {}

        with tempfile.TemporaryDirectory() as tmp:
            video_artifact = Path(tmp) / "adp-daily-video.mp4"
            video_artifact.write_bytes(b"\x00\x00\x00\x18ftypmp42fake-video")
            report = run_scheduled_execution(
                mode="daily-run",
                generated_at="2026-07-01T05:00:00+10:00",
                preflight_report=preflight_pass(),
                env=complete_env(
                    ADP_SCHEDULED_RUN_ENABLED="true",
                    ADP_ALLOW_SMTP_SEND="true",
                    ADP_ALLOW_RELEASE_UPLOAD="true",
                    ADP_RELEASE_DRAFT="false",
                ),
                daily_input=production_daily_input_payload(),
                release_asset_paths=[PIPELINE_INPUT, video_artifact],
                smtp_factory=FakeSMTP,
                release_command_resolver=lambda _name: "/usr/bin/gh",
                release_command_runner=lambda command: release_commands.append(list(command)) or {"returncode": 0},
            )

        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(report["production_evidence_ready"])
        self.assertEqual(report["release_report"]["status"], "created")
        self.assertEqual(report["notification_report"]["status"], "sent")
        self.assertTrue(report["delivery_package"]["video_link_ready"])
        self.assertTrue(report["delivery_package"]["email_contains_html"])
        self.assertTrue(report["delivery_package"]["email_contains_candidate_queue_summary"])
        self.assertEqual(report["daily_run_report"]["scheduled_local_time"], "05:00")
        self.assertTrue(report["daily_run_report"]["p0_claims_traceable"])
        self.assertEqual(FakeSMTP.sent_messages[0]["To"], "linzezhang35@gmail.com")
        self.assertEqual(
            str(FakeSMTP.sent_messages[0]["Subject"]),
            "20260621 -- arXiv Computer Science -- Computer Science -- A Useful Paper",
        )
        self.assertTrue(FakeSMTP.sent_messages[0].is_multipart())
        email_body = FakeSMTP.sent_messages[0].get_body(preferencelist=("plain",)).get_content()
        html_body = FakeSMTP.sent_messages[0].get_body(preferencelist=("html",)).get_content()
        self.assertIn("https://github.com/LinzeColin/CodexProject/releases/download/adp-daily-20260621/adp-daily-video.mp4", email_body)
        self.assertNotIn("https://github.com/LinzeColin/CodexProject/releases/tag/adp-daily-20260621", email_body)
        self.assertIn("【视频入口】", email_body)
        self.assertIn("观看图解视频", html_body)
        self.assertNotIn("【12秒视频】", email_body)
        self.assertNotIn("Release 资料包", email_body)
        self.assertIn("候选队列摘要", email_body)
        self.assertNotIn("Claim Ledger", email_body)
        self.assertNotIn("project:", email_body)
        self.assertNotIn("recipient:", email_body)
        self.assertNotIn("ROI score", email_body)
        self.assertNotIn("roi_total_score", email_body)
        self.assertNotIn("delivery_policy", email_body)
        self.assertNotRegex(str(FakeSMTP.sent_messages[0]["Subject"]), r"\d(?:\.\d)?/5")
        self.assertNotRegex(email_body, r"\d(?:\.\d)?/5")
        self.assertNotRegex(html_body, r"\d(?:\.\d)?/5")
        self.assertIn("not the reading entry point", " ".join(release_commands[0]))
        self.assertNotIn("--draft", release_commands[0])
        self.assertNotIn("super-secret-password", str(report))
        self.assertFalse(validate_scheduled_execution_report(report))

    def test_cli_run_scheduled_production_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            preflight_path = Path(tmp) / "preflight.json"
            preflight_path.write_text(json.dumps(preflight_pass()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "run-scheduled-production",
                        "--mode",
                        "health-check",
                        "--generated-at",
                        "2026-07-01T04:45:00+10:00",
                        "--preflight-report",
                        str(preflight_path),
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], SCHEDULED_EXECUTION_MODEL_ID)
        self.assertEqual(payload["status"], "succeeded")


if __name__ == "__main__":
    unittest.main()
