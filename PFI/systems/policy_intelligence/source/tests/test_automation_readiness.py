from __future__ import annotations

import io
import json
import plistlib
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from source_registry.automation_readiness import (
    build_automation_readiness,
    cleanup_stale_pipeline_lock,
    inspect_pipeline_lock,
    render_automation_readiness_dashboard,
    write_automation_readiness_dashboard,
)
from source_registry.cli import main as cli_main
from source_registry.content_db import begin_run, complete_run, connect_content, init_content_database


class AutomationReadinessTest(unittest.TestCase):
    def test_readiness_marks_p0_credentials_as_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = _content_db(root / "policy_documents.sqlite")
            report = build_automation_readiness(
                content_conn=conn,
                data_dir=root / "data",
                search_secrets_file=root / "missing-search.json",
                platform_auth_file=root / "missing-auth.json",
                now=datetime(2026, 6, 4, tzinfo=timezone.utc),
            )
            conn.close()
        self.assertEqual(report["overall_status"], "blocked")
        self.assertEqual(report["summary"]["p0_status"], "p0_blocked")
        self.assertTrue(any(item["key"] == "p0_credentials" and item["status"] == "fail" for item in report["checks"]))

    def test_stale_lock_is_not_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            (data / "pipeline.lock").write_text("999999", encoding="utf-8")
            conn = _content_db(root / "policy_documents.sqlite")
            report = build_automation_readiness(content_conn=conn, data_dir=data)
            conn.close()
        lock = next(item for item in report["checks"] if item["key"] == "pipeline_lock")
        self.assertEqual(lock["status"], "pass")
        self.assertIn("stale lock", lock["detail"])

    def test_cleanup_stale_lock_removes_only_dead_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "data" / "pipeline.lock"
            lock.parent.mkdir()
            lock.write_text("999999", encoding="utf-8")
            result = cleanup_stale_pipeline_lock(lock)
            self.assertTrue(result["removed"])
            self.assertFalse(lock.exists())

    def test_cleanup_does_not_remove_running_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "data" / "pipeline.lock"
            lock.parent.mkdir()
            lock.write_text(str(__import__("os").getpid()), encoding="utf-8")
            state = inspect_pipeline_lock(lock)
            result = cleanup_stale_pipeline_lock(lock)
            self.assertEqual(state["status"], "running")
            self.assertFalse(result["removed"])
            self.assertTrue(lock.exists())

    def test_render_dashboard_contains_schedule_and_no_secrets(self) -> None:
        report = build_automation_readiness(schedule_times=["09:00", "21:00"])
        rendered = render_automation_readiness_dashboard(report)
        self.assertIn("自动化运行就绪检查", rendered)
        self.assertIn("09:00, 21:00", rendered)
        self.assertIn("P0", rendered)
        self.assertIn("运行策略", rendered)
        self.assertIn("请求超时", rendered)
        self.assertNotIn("SESSDATA=", rendered)
        self.assertNotIn("sk-", rendered)

    def test_runtime_policy_warns_for_no_retry_or_rate_limit(self) -> None:
        report = build_automation_readiness(
            runtime_policy={
                "max_sources": 3,
                "max_pages_per_source": 2,
                "max_links_per_page": 20,
                "max_interpretation_documents": 10,
                "interpretation_request_timeout": 20,
                "interpretation_request_retries": 0,
                "interpretation_request_delay_seconds": 0,
                "max_running_minutes": 180,
            }
        )
        row = next(item for item in report["checks"] if item["key"] == "runtime_policy")
        self.assertEqual(row["status"], "warn")
        self.assertIn("至少 1 次重试", row["detail"])
        self.assertIn("至少 0.2 秒限速", row["detail"])
        self.assertTrue(any(item["source"] == "运行策略" for item in report["next_actions"]))

    def test_scheduler_persistence_warns_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = _content_db(root / "policy_documents.sqlite")
            report = build_automation_readiness(
                content_conn=conn,
                data_dir=root / "data",
                schedule_times=["09:00", "21:00"],
                now=datetime(2026, 6, 4, 12, tzinfo=timezone.utc),
            )
            conn.close()
        row = next(item for item in report["checks"] if item["key"] == "scheduler_persistence")
        self.assertEqual(row["status"], "warn")
        self.assertIn("不能证明 launchd/cron/外部 automation 已安装", row["detail"])
        self.assertEqual(report["summary"]["scheduler_status"], "warn")

    def test_scheduler_persistence_passes_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            scheduler = data / "automation" / "scheduler.json"
            scheduler.parent.mkdir(parents=True)
            scheduler.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "scheduler_type": "launchd",
                        "entrypoint": "bash scripts/run_policy_report.sh",
                        "schedule_times": ["09:00", "21:00"],
                        "timezone": "Australia/Sydney",
                    }
                ),
                encoding="utf-8",
            )
            conn = _content_db(root / "policy_documents.sqlite")
            report = build_automation_readiness(
                content_conn=conn,
                data_dir=data,
                schedule_times=["09:00", "21:00"],
                now=datetime(2026, 6, 4, 12, tzinfo=timezone.utc),
            )
            conn.close()
        row = next(item for item in report["checks"] if item["key"] == "scheduler_persistence")
        self.assertEqual(row["status"], "pass")
        self.assertIn("入口脚本匹配", row["detail"])
        self.assertEqual(report["summary"]["scheduler_status"], "pass")

    def test_scheduler_persistence_passes_with_launchd_plist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            plist = root / "policy.plist"
            plist.write_bytes(
                plistlib.dumps(
                    {
                        "Label": "com.example.policy",
                        "ProgramArguments": ["/bin/bash", "-lc", "cd /tmp && bash scripts/run_policy_report.sh"],
                        "StartCalendarInterval": [{"Hour": 9, "Minute": 0}, {"Hour": 21, "Minute": 0}],
                    }
                )
            )
            conn = _content_db(root / "policy_documents.sqlite")
            report = build_automation_readiness(
                content_conn=conn,
                data_dir=data,
                scheduler_file=plist,
                schedule_times=["09:00", "21:00"],
                now=datetime(2026, 6, 4, 12, tzinfo=timezone.utc),
            )
            conn.close()
        row = next(item for item in report["checks"] if item["key"] == "scheduler_persistence")
        self.assertEqual(row["status"], "pass")
        self.assertEqual(row["evidence"]["scheduler_type"], "launchd")
        self.assertEqual(row["evidence"]["schedule_times"], ["09:00", "21:00"])

    def test_scheduler_persistence_warns_when_schedule_does_not_match_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            scheduler = data / "automation" / "scheduler.json"
            scheduler.parent.mkdir(parents=True)
            scheduler.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "scheduler_type": "launchd",
                        "entrypoint": "bash scripts/run_policy_report.sh",
                        "schedule_times": ["08:00", "20:00"],
                    }
                ),
                encoding="utf-8",
            )
            conn = _content_db(root / "policy_documents.sqlite")
            report = build_automation_readiness(
                content_conn=conn,
                data_dir=data,
                schedule_times=["09:00", "21:00"],
                now=datetime(2026, 6, 4, 12, tzinfo=timezone.utc),
            )
            conn.close()
        row = next(item for item in report["checks"] if item["key"] == "scheduler_persistence")
        self.assertEqual(row["status"], "warn")
        self.assertIn("运行时间与目标每日调度不匹配", row["detail"])

    def test_latest_success_freshness_warns_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = _content_db(root / "policy_documents.sqlite")
            conn.execute(
                "UPDATE pipeline_runs SET completed_at = ? WHERE run_id = ?",
                ("2026-06-03T09:00:00+00:00", "2026060401"),
            )
            conn.commit()
            report = build_automation_readiness(
                content_conn=conn,
                data_dir=root / "data",
                schedule_times=["09:00", "21:00"],
                now=datetime(2026, 6, 4, 12, tzinfo=timezone.utc),
            )
            conn.close()
        row = next(item for item in report["checks"] if item["key"] == "latest_success_freshness")
        self.assertEqual(row["status"], "warn")
        self.assertIn("已过期", row["action"])
        self.assertEqual(report["summary"]["latest_success_status"], "warn")

    def test_write_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "readiness.html"
            result = write_automation_readiness_dashboard(output, data_dir=Path(tmp) / "data")
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_automation_readiness_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_db = root / "policy_documents.sqlite"
            _content_db(content_db).close()
            output = root / "readiness.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "automation-readiness",
                        "--content-db",
                        str(content_db),
                        "--data-dir",
                        str(root / "data"),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertIn("summary", payload)
            self.assertTrue(output.exists())

    def test_cli_automation_lock_clean_removes_stale_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            (data / "pipeline.lock").write_text("999999", encoding="utf-8")
            content_db = root / "policy_documents.sqlite"
            conn = connect_content(content_db)
            init_content_database(conn)
            begin_run(conn, "2026060402", "automation")
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "automation-lock-clean",
                        "--data-dir",
                        str(data),
                        "--content-db",
                        str(content_db),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertTrue(payload["removed"])
            self.assertEqual(len(payload["reconciled_pipeline_runs"]), 1)
            self.assertFalse((data / "pipeline.lock").exists())
            conn = connect_content(content_db)
            status = conn.execute("SELECT status FROM pipeline_runs WHERE run_id = '2026060402'").fetchone()["status"]
            conn.close()
            self.assertEqual(status, "failed")

    def test_cli_automation_lock_clean_keeps_running_lock_and_pipeline_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            (data / "pipeline.lock").write_text(str(__import__("os").getpid()), encoding="utf-8")
            content_db = root / "policy_documents.sqlite"
            conn = connect_content(content_db)
            init_content_database(conn)
            begin_run(conn, "2026060403", "automation")
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "automation-lock-clean",
                        "--data-dir",
                        str(data),
                        "--content-db",
                        str(content_db),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertFalse(payload["removed"])
            self.assertEqual(payload["reconciled_pipeline_runs"], [])
            conn = connect_content(content_db)
            status = conn.execute("SELECT status FROM pipeline_runs WHERE run_id = '2026060403'").fetchone()["status"]
            conn.close()
            self.assertEqual(status, "running")


def _content_db(path: Path):
    conn = connect_content(path)
    init_content_database(conn)
    begin_run(conn, "2026060401", "automation")
    complete_run(conn, "2026060401", "completed", "reports/missing.pdf", {"analyzed_documents": 1})
    return conn


if __name__ == "__main__":
    unittest.main()
