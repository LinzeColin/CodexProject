from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from email.message import EmailMessage
from pathlib import Path

import arxiv_daily_push.cli as cli_module
import arxiv_daily_push.local_runner as local_runner_module
from arxiv_daily_push.cli import main
from arxiv_daily_push.global_scan import ALL_ARXIV_ARCHIVES
from arxiv_daily_push.local_runner import (
    LOCAL_RUNNER_MODEL_ID,
    ACTION_ROI_REPORT_FILENAME,
    REVIEW_REPORT_FILENAME,
    USER_CENTER_LEARNING_PAGE,
    USER_CENTER_MAIL_STATUS_PAGES,
    build_launchd_package,
    build_local_preflight,
    run_local_daily,
    validate_local_runner_report,
)
from arxiv_daily_push.mail_templates import EMAIL_LEARNING_V1_CONTRACT_ID
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


def write_user_center_sync_inputs(root: Path, state: Path) -> None:
    page = root / USER_CENTER_LEARNING_PAGE
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "\n".join(
            [
                "# 复习行动与收益",
                "",
                "| 字段 | 当前值 | 来源 |",
                "|---|---|---|",
                "| 今日到期复习 | 待今日运行快照写入 | 今日报告 |",
                "| 未来 7 天复习 | 待今日运行快照写入 | 今日报告 |",
                "| 已逾期复习 | 待今日运行快照写入 | 今日报告 |",
                "| 已完成复习 | 待今日运行快照写入 | 今日报告 |",
                "| 今日 15 分钟行动 | 待今日运行快照写入 | 今日报告 |",
                "| 今日 2 小时行动 | 待今日运行快照写入 | 今日报告 |",
                "| 今日 7 天行动 | 待今日运行快照写入 | 今日报告 |",
                "| 今日 30 天行动 | 待今日运行快照写入 | 今日报告 |",
                "| 新增能力资产 | 待今日运行快照写入 | 今日报告 |",
                "| 可验证实际收益 / 转化 | 待今日运行快照写入 | 今日报告 |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for mail_status_page in USER_CENTER_MAIL_STATUS_PAGES:
        page = root / mail_status_page
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(
            "\n".join(
                [
                    f"# {page.stem}",
                    "",
                    "| 项目 | 当前值 |",
                    "|---|---|",
                    "| 受控发送证据 / 计划应发 | 2 / 待确认 |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    state.mkdir(parents=True, exist_ok=True)
    (state / REVIEW_REPORT_FILENAME).write_text(
        json.dumps(
            {
                "status": "pass",
                "s2pjt02_review_schedule_ready": True,
                "computed_counts": {
                    "due_today": 1,
                    "due_next_7_days": 2,
                    "overdue": 0,
                    "completed": 3,
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (state / ACTION_ROI_REPORT_FILENAME).write_text(
        json.dumps(
            {
                "status": "pass",
                "s2pjt03_action_roi_ready": True,
                "action_counts": {
                    "15m": 1,
                    "2h": 1,
                    "7d": 2,
                    "30d": 4,
                },
                "capability_assets": [{"asset_id": "asset-1"}],
                "actual_roi_status_counts": {"calculated": 1},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


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
            write_user_center_sync_inputs(root, state)
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
            self.assertEqual(set(report["notification_reports"]), {"M1", "M2", "M3", "M4"})
            self.assertTrue(all(item["status"] == "dry_run" for item in report["notification_reports"].values()))
            self.assertEqual(report["mail_delivery_summary"]["sent_mail_count"], 0)
            self.assertEqual(report["mail_delivery_summary"]["dry_run_mail_products"], ["M1", "M2", "M3", "M4"])
            self.assertTrue((state / "candidate_queue.json").is_file())
            self.assertTrue((state / "local_content_ledger.jsonl").is_file())
            self.assertTrue(Path(report["email_preview_paths"]["plain"]).is_file())
            self.assertTrue(Path(report["email_preview_paths"]["by_product"]["M4"]["html"]).is_file())
            self.assertEqual(report["delivery_package"]["email_template_contract"], EMAIL_LEARNING_V1_CONTRACT_ID)
            self.assertEqual(report["delivery_package"]["mail_product_id"], "M1")
            self.assertEqual(set(report["delivery_packages"]), {"M1", "M2", "M3", "M4"})
            self.assertEqual(report["delivery_packages"]["M4"]["mail_product_id"], "M4")
            self.assertEqual(report["planned_mail_delivery"]["planned_send_total"], 4)
            self.assertEqual(report["planned_mail_delivery"]["planned_mail_products"], ["M1", "M2", "M3", "M4"])
            self.assertIn("【先把论文讲成人话】", Path(report["email_preview_paths"]["plain"]).read_text(encoding="utf-8"))
            self.assertTrue(report["user_center_sync_ready"])
            score_gate = report["user_center_sync"]["candidate_score_detail_gate"]
            self.assertEqual(score_gate["status"], "pass")
            self.assertTrue(report["user_center_sync"]["candidate_score_detail_ready"])
            self.assertEqual(
                score_gate["required_components"],
                [
                    "relevance",
                    "learning_value",
                    "economic_conversion_rate",
                    "roi",
                    "interdisciplinary_value",
                    "explainability",
                ],
            )
            self.assertEqual(score_gate["checked_candidate_count"], score_gate["candidate_count"])
            self.assertTrue(score_gate["candidate_score_details"])
            self.assertIn("| 今日到期复习 | 1 项 |", (root / USER_CENTER_LEARNING_PAGE).read_text(encoding="utf-8"))
            for mail_status_page in USER_CENTER_MAIL_STATUS_PAGES:
                page_text = (root / mail_status_page).read_text(encoding="utf-8")
                self.assertIn("| 受控发送证据 / 计划应发 | 2 / 4 |", page_text)
                self.assertIn("计划来源：Email V1 每日 3+1（M1, M2, M3, M4），计划应发 4 封", page_text)
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
            state = Path(tmp) / "state"
            write_user_center_sync_inputs(root, state)
            report = run_local_daily(
                project_root=root,
                state_dir=state,
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
            state = Path(tmp) / "state"
            write_user_center_sync_inputs(root, state)
            report = run_local_daily(
                project_root=root,
                state_dir=state,
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
            self.assertEqual(report["mail_delivery_summary"]["sent_mail_count"], 4)
            self.assertTrue(report["mail_delivery_summary"]["all_planned_products_sent"])
            self.assertEqual(report["mail_delivery_summary"]["newly_sent_mail_products"], ["M1", "M2", "M3", "M4"])
            self.assertEqual(report["mail_delivery_summary"]["historical_sent_mail_products"], [])
            self.assertTrue(all(item["status"] == "sent" for item in report["notification_reports"].values()))
            self.assertEqual([item["product_id"] for item in report["notification_reports"].values()], ["M1", "M2", "M3", "M4"])
            self.assertEqual(len(FakeSMTP.sent_messages), 4)
            subjects = [str(message["Subject"]) for message in FakeSMTP.sent_messages]
            self.assertTrue(any("-- M1 --" in subject for subject in subjects))
            self.assertTrue(any("-- M4 --" in subject for subject in subjects))
            for mail_status_page in USER_CENTER_MAIL_STATUS_PAGES:
                page_text = (root / mail_status_page).read_text(encoding="utf-8")
                self.assertIn("| 受控发送证据 / 计划应发 | 4 / 4 |", page_text)

    def test_local_daily_real_smtp_skips_already_sent_products_and_catches_up_missing_products(self) -> None:
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
            "arxiv:2606.24007",
            "Catch-up orchestration for product-level mail delivery",
            "cs.AI",
            ["cs.AI", "q-fin.PM"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            state = Path(tmp) / "state"
            write_user_center_sync_inputs(root, state)
            (state / "local_content_ledger.jsonl").write_text(
                json.dumps(
                    {
                        "date": "2026-06-24",
                        "email_status": "sent",
                        "email_ref": "smtp://message/legacy-m1",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            report = run_local_daily(
                project_root=root,
                state_dir=state,
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
            self.assertEqual(len(FakeSMTP.sent_messages), 3)
            self.assertEqual(report["notification_reports"]["M1"]["status"], "sent")
            self.assertTrue(report["notification_reports"]["M1"]["historical_delivery_evidence"])
            self.assertFalse(report["notification_reports"]["M1"]["real_send_attempted"])
            self.assertEqual(report["notification_reports"]["M1"]["delivery_ref"], "smtp://message/legacy-m1")
            self.assertEqual(report["mail_delivery_summary"]["sent_mail_count"], 4)
            self.assertEqual(report["mail_delivery_summary"]["historical_sent_mail_products"], ["M1"])
            self.assertEqual(report["mail_delivery_summary"]["newly_sent_mail_products"], ["M2", "M3", "M4"])
            subjects = [str(message["Subject"]) for message in FakeSMTP.sent_messages]
            self.assertFalse(any("-- M1 --" in subject for subject in subjects))
            self.assertTrue(any("-- M2 --" in subject for subject in subjects))
            self.assertTrue(any("-- M4 --" in subject for subject in subjects))
            for mail_status_page in USER_CENTER_MAIL_STATUS_PAGES:
                page_text = (root / mail_status_page).read_text(encoding="utf-8")
                self.assertIn("| 受控发送证据 / 计划应发 | 4 / 4 |", page_text)

    def test_local_daily_can_reuse_existing_daily_input_report_for_catch_up_without_live_fetch(self) -> None:
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
            "arxiv:2606.24008",
            "Resend recovery without live source fetch",
            "cs.AI",
            ["cs.AI", "q-fin.PM"],
        )
        original_builder = local_runner_module.build_all_arxiv_daily_input

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            state = Path(tmp) / "state"
            write_user_center_sync_inputs(root, state)
            initial_report = run_local_daily(
                project_root=root,
                state_dir=state,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=source_batches(**{"cs": [candidate]}),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
            )
            daily_input_report_path = Path(initial_report["run_dir"]) / "adp-daily-input-report.json"

            def fail_if_live_builder_called(*args, **kwargs):
                raise AssertionError("live daily input builder must not run during resend recovery")

            local_runner_module.build_all_arxiv_daily_input = fail_if_live_builder_called
            try:
                report = run_local_daily(
                    project_root=root,
                    state_dir=state,
                    date="2026-06-24",
                    generated_at=GENERATED_AT,
                    env=smtp_env(),
                    allow_smtp_send=True,
                    daily_input_report_path=daily_input_report_path,
                    command_resolver=command_resolver,
                    disk_free_gib=120.0,
                    memory_total_gib=16.0,
                    smtp_factory=FakeSMTP,
                )
            finally:
                local_runner_module.build_all_arxiv_daily_input = original_builder

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["daily_input_source"], "existing_report")
            self.assertEqual(report["daily_input_report_path"], str(daily_input_report_path.resolve()))
            self.assertEqual(report["mail_delivery_summary"]["sent_mail_count"], 4)
            self.assertEqual(len(FakeSMTP.sent_messages), 4)
            self.assertFalse(validate_local_runner_report(report))

    def test_local_daily_blocks_reused_daily_input_report_with_mismatched_date(self) -> None:
        candidate = source_item(
            "arxiv:2606.24009",
            "Date guard for resend recovery input",
            "cs.AI",
            ["cs.AI", "q-fin.PM"],
        )
        original_builder = local_runner_module.build_all_arxiv_daily_input

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            state = Path(tmp) / "state"
            write_user_center_sync_inputs(root, state)
            initial_report = run_local_daily(
                project_root=root,
                state_dir=state,
                date="2026-06-24",
                generated_at=GENERATED_AT,
                source_batches=source_batches(**{"cs": [candidate]}),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
            )
            daily_input_report_path = Path(initial_report["run_dir"]) / "adp-daily-input-report.json"

            def fail_if_live_builder_called(*args, **kwargs):
                raise AssertionError("live daily input builder must not run when explicit input report is provided")

            local_runner_module.build_all_arxiv_daily_input = fail_if_live_builder_called
            try:
                report = run_local_daily(
                    project_root=root,
                    state_dir=state,
                    date="2026-06-25",
                    generated_at=GENERATED_AT,
                    daily_input_report_path=daily_input_report_path,
                    command_resolver=command_resolver,
                    disk_free_gib=120.0,
                    memory_total_gib=16.0,
                )
            finally:
                local_runner_module.build_all_arxiv_daily_input = original_builder

            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["daily_input_source"], "existing_report")
            self.assertIn("daily input report date mismatch", " ".join(report["blocking_reasons"]))
            self.assertFalse(validate_local_runner_report(report))

    def test_local_daily_blocks_when_user_center_sync_missing(self) -> None:
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
            "arxiv:2606.24005",
            "Runner readiness gate for human center synchronization",
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

            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["user_center_sync_ready"])
            self.assertIn("user center sync missing required files", " ".join(report["blocking_reasons"]))
            self.assertEqual(report["notification_report"]["status"], "blocked")
            self.assertFalse(report["notification_report"]["real_send_attempted"])
            self.assertEqual(set(report["notification_reports"]), {"M1", "M2", "M3", "M4"})
            self.assertTrue(all(item["status"] == "blocked" for item in report["notification_reports"].values()))
            self.assertEqual(report["mail_delivery_summary"]["blocked_mail_products"], ["M1", "M2", "M3", "M4"])
            self.assertEqual(FakeSMTP.sent_messages, [])
            self.assertTrue(validate_local_runner_report(report) == [])

    def test_local_daily_blocks_when_candidate_score_detail_missing(self) -> None:
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
            "arxiv:2606.24006",
            "Score detail gate for candidate queue synchronization",
            "cs.AI",
            ["cs.AI", "q-fin.PM"],
        )
        original_builder = local_runner_module.build_all_arxiv_daily_input

        def builder_without_score_detail(*args, **kwargs):
            report = original_builder(*args, **kwargs)
            selection = report.get("selection")
            if isinstance(selection, dict) and isinstance(selection.get("selected"), dict):
                selection["selected"].pop("roi_signals", None)
            scan = report.get("scan")
            if isinstance(scan, dict):
                for item in scan.get("candidates") or []:
                    if isinstance(item, dict):
                        item.pop("roi_signals", None)
            queue = report.get("candidate_queue")
            if isinstance(queue, dict):
                for item in queue.get("items") or []:
                    if isinstance(item, dict):
                        item.pop("roi_signals", None)
            return report

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            state = Path(tmp) / "state"
            write_user_center_sync_inputs(root, state)
            local_runner_module.build_all_arxiv_daily_input = builder_without_score_detail
            try:
                report = run_local_daily(
                    project_root=root,
                    state_dir=state,
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
            finally:
                local_runner_module.build_all_arxiv_daily_input = original_builder

            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["user_center_sync_ready"])
            self.assertFalse(report["user_center_sync"]["candidate_score_detail_ready"])
            self.assertIn("missing roi_signals six-factor detail", " ".join(report["blocking_reasons"]))
            self.assertEqual(report["notification_report"]["status"], "blocked")
            self.assertFalse(report["notification_report"]["real_send_attempted"])
            self.assertEqual(set(report["notification_reports"]), {"M1", "M2", "M3", "M4"})
            self.assertTrue(all(item["status"] == "blocked" for item in report["notification_reports"].values()))
            self.assertEqual(FakeSMTP.sent_messages, [])
            self.assertTrue(validate_local_runner_report(report) == [])

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
            self.assertIn("--project-root", plist)
            self.assertIn(str((Path(tmp) / "repo" / "arxiv-daily-push").resolve()), plist)
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

    def test_cli_local_daily_passes_explicit_daily_input_report_path(self) -> None:
        captured: dict[str, object] = {}
        original_runner = cli_module.run_local_daily

        def fake_run_local_daily(**kwargs):
            captured.update(kwargs)
            return {
                "model_id": local_runner_module.LOCAL_RUNNER_MODEL_ID,
                "schema_version": local_runner_module.LOCAL_RUNNER_SCHEMA_VERSION,
                "acceptance_id": local_runner_module.LOCAL_RUNNER_ACCEPTANCE_ID,
                "action": "daily_run",
                "status": "blocked",
                "generated_at": kwargs["generated_at"],
                "date": kwargs["date"],
                "runner_strategy": "local_codex_runner",
                "daily_input_ready": False,
                "github_cloud_schedule_required": False,
                "github_cloud_schedule_enabled": False,
                "release_upload_enabled": False,
                "video_generated": False,
                "secret_values_logged": False,
                "blocking_reasons": ["fake cli capture"],
            }

        cli_module.run_local_daily = fake_run_local_daily
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "local-runner",
                        "daily",
                        "--project-root",
                        "/tmp/repo",
                        "--state-dir",
                        "/tmp/state",
                        "--date",
                        "2026-06-24",
                        "--generated-at",
                        GENERATED_AT,
                        "--daily-input-report",
                        "/tmp/state/runs/20260624/adp-daily-input-report.json",
                        "--json",
                    ]
                )
        finally:
            cli_module.run_local_daily = original_runner

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(captured["daily_input_report_path"], "/tmp/state/runs/20260624/adp-daily-input-report.json")


if __name__ == "__main__":
    unittest.main()
