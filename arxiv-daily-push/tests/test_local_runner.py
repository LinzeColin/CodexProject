from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from email.message import EmailMessage
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.global_scan import ALL_ARXIV_ARCHIVES
from arxiv_daily_push.local_runner import (
    LOCAL_RUNNER_MODEL_ID,
    build_launchd_package,
    build_local_preflight,
    run_local_daily,
    validate_local_runner_report,
)
from arxiv_daily_push.source_ingest import SOURCE_INGEST_MODEL_ID


GENERATED_AT = "2026-06-24T05:00:00+10:00"


def command_resolver(command: str) -> str | None:
    return f"/usr/bin/{command}" if command in {"python3", "git"} else None


def smtp_env(**extra: str) -> dict[str, str]:
    env = {
        "ADP_SMTP_HOST": "smtp.example.invalid",
        "ADP_SMTP_PORT": "587",
        "ADP_SMTP_USERNAME": "sender@example.invalid",
        "ADP_SMTP_PASSWORD": "configured-password",
    }
    env.update(extra)
    return env


def high_roi_summary(topic: str) -> str:
    return (
        f"This paper introduces a benchmark and method for agent decision learning in {topic}. "
        "It covers finance, portfolio risk, market simulation, automation, privacy, security, "
        "optimization, cost efficiency, evaluation, policy, statistics, and robust deployment."
    )


def source_item(source_id: str, title: str, primary: str, categories: list[str]) -> dict:
    stable_id = source_id.removeprefix("arxiv:")
    return {
        "source_id": source_id,
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": stable_id,
        "title": title,
        "retrieved_at": GENERATED_AT,
        "canonical_url": f"https://arxiv.org/abs/{stable_id}",
        "metadata": {
            "arxiv": {
                "summary": high_roi_summary(title),
                "primary_category": primary,
                "categories": categories,
            }
        },
        "content_refs": [{"ref_type": "abstract", "url": f"https://arxiv.org/abs/{stable_id}"}],
        "license": {"name": "arXiv", "url": "https://arxiv.org/licenses"},
    }


def source_batch(archive_id: str, items: list[dict]) -> dict:
    return {
        "ingest_id": "source-ingest:arxiv-latest",
        "model_id": SOURCE_INGEST_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "source_adapter": "arxiv.atom.v1",
        "generated_at": GENERATED_AT,
        "status": "pass" if items else "blocked",
        "request": {
            "base_url": "https://export.arxiv.org/api/query",
            "url": f"https://export.arxiv.org/api/query?search_query=cat:{archive_id}",
            "search_query": f"cat:{archive_id}",
            "start": 0,
            "max_results": 3,
            "sort_by": "submittedDate",
            "sort_order": "descending",
        },
        "source_policy": {
            "network_fetch_enabled": True,
            "pdf_download_enabled": False,
            "bulk_harvest_enabled": False,
            "max_results_per_call": 25,
            "polite_min_interval_seconds": 3,
        },
        "seen_source_ids": [],
        "duplicate_source_ids": [],
        "source_items": items,
        "new_items": items,
        "new_item_count": len(items),
        "blocking_reasons": [] if items else ["no unseen arXiv SourceItems returned for the configured query"],
    }


def source_batches(**items_by_archive: list[dict]) -> dict[str, dict]:
    batches = {}
    for archive in ALL_ARXIV_ARCHIVES:
        archive_id = archive["archive_id"]
        batches[archive_id] = source_batch(archive_id, items_by_archive.get(archive_id, []))
    return batches


class LocalRunnerTests(unittest.TestCase):
    def test_local_daily_persists_queue_ledger_report_and_email_preview_without_smtp(self) -> None:
        candidate = source_item(
            "arxiv:2606.24001",
            "Agent benchmark for portfolio risk automation",
            "q-fin.PM",
            ["q-fin.PM", "cs.AI", "stat.ML"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            state = Path(tmp) / "state"
            report = run_local_daily(
                project_root=root,
                state_dir=state,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=source_batches(**{"q-fin": [candidate]}),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
            )

            self.assertEqual(report["model_id"], LOCAL_RUNNER_MODEL_ID)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["runner_strategy"], "local_codex_runner")
            self.assertFalse(report["github_cloud_schedule_enabled"])
            self.assertFalse(report["production_evidence_ready"])
            self.assertEqual(report["notification_report"]["status"], "dry_run")
            self.assertTrue((state / "candidate_queue.json").is_file())
            self.assertTrue((state / "local_content_ledger.jsonl").is_file())
            self.assertTrue(Path(report["email_preview_paths"]["plain"]).is_file())
            self.assertIn("【今天讲透一个问题】", Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8"))
            self.assertFalse(validate_local_runner_report(report))

    def test_local_daily_real_smtp_requires_secret_env_names_and_does_not_log_values(self) -> None:
        candidate = source_item(
            "arxiv:2606.24002",
            "Automation benchmark for market risk control",
            "cs.AI",
            ["cs.AI", "q-fin.RM"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            report = run_local_daily(
                project_root=root,
                state_dir=Path(tmp) / "state",
                date="2026-06-24",
                generated_at=GENERATED_AT,
                env={"ADP_SMTP_PASSWORD": "super-secret-value"},
                allow_smtp_send=True,
                source_batches=source_batches(**{"cs": [candidate]}),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("missing required SMTP environment keys", " ".join(report["blocking_reasons"]))
            self.assertNotIn("super-secret-value", json.dumps(report))

    def test_local_daily_no_write_does_not_persist_state_or_artifacts(self) -> None:
        candidate = source_item(
            "arxiv:2606.24004",
            "Cross-domain agent benchmark for execution quality",
            "cs.AI",
            ["cs.AI", "q-fin.PM"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            state = Path(tmp) / "state"
            report = run_local_daily(
                project_root=root,
                state_dir=state,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=source_batches(**{"cs": [candidate]}),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                write=False,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("at least one release asset path is required", " ".join(report["blocking_reasons"]))
            self.assertFalse(state.exists())
            self.assertFalse(report["email_preview_written"])
            self.assertFalse(report["candidate_queue_persisted"])

    def test_local_daily_can_send_with_explicit_fake_smtp(self) -> None:
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

        candidate = source_item(
            "arxiv:2606.24003",
            "Foundation model agents for supply optimization",
            "cs.AI",
            ["cs.AI", "q-fin.PM"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            report = run_local_daily(
                project_root=root,
                state_dir=Path(tmp) / "state",
                date="2026-06-24",
                generated_at=GENERATED_AT,
                env=smtp_env(),
                allow_smtp_send=True,
                source_batches=source_batches(**{"cs": [candidate]}),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                smtp_factory=FakeSMTP,
            )

            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["production_evidence_ready"])
            self.assertTrue(report["real_smtp_sent"])
            self.assertEqual(report["notification_report"]["status"], "sent")
            self.assertEqual(len(FakeSMTP.sent_messages), 1)

    def test_launchd_package_is_generated_but_not_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_launchd_package(
                project_root=Path(tmp) / "repo",
                state_dir=Path(tmp) / "state",
                artifact_dir=Path(tmp) / "launchd",
                generated_at=GENERATED_AT,
            )

            self.assertEqual(report["status"], "pass")
            self.assertFalse(report["applied"])
            self.assertFalse(report["real_scheduler_installed"])
            self.assertFalse(report["github_cloud_schedule_required"])
            self.assertTrue((Path(tmp) / "launchd" / "README_LOCAL_LAUNCHD.md").is_file())
            plist = (Path(tmp) / "launchd" / "com.linze.adp.local.daily.plist").read_text(encoding="utf-8")
            self.assertIn("ADP_LOCAL_DAILY_RUN_ENABLED=true", plist)
            self.assertIn("local-runner daily", plist)
            self.assertNotIn("github-actions", plist)
            self.assertFalse(validate_local_runner_report(report))

    def test_cli_local_preflight_and_launchd_package_output_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            state.mkdir()
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "local-runner",
                        "preflight",
                        "--project-root",
                        tmp,
                        "--state-dir",
                        str(state),
                        "--generated-at",
                        GENERATED_AT,
                        "--json",
                    ]
                )
            payload = json.loads(buffer.getvalue())
            self.assertIn(result, {0, 2})
            self.assertEqual(payload["validator_id"], "adp-production-preflight-v1")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "local-runner",
                        "launchd-package",
                        "--project-root",
                        tmp,
                        "--state-dir",
                        str(state),
                        "--artifact-dir",
                        str(Path(tmp) / "launchd"),
                        "--generated-at",
                        GENERATED_AT,
                        "--json",
                    ]
                )
            payload = json.loads(buffer.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["model_id"], LOCAL_RUNNER_MODEL_ID)


if __name__ == "__main__":
    unittest.main()
