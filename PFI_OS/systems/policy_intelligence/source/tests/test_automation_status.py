from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.automation_status import (
    load_latest_automation_run,
    record_automation_step,
    render_automation_dashboard,
    write_automation_dashboard,
)
from source_registry.cli import main as cli_main


class AutomationStatusTest(unittest.TestCase):
    def test_record_step_updates_latest_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = record_automation_step(
                data_dir=tmp,
                run_id="20260604120000",
                step_key="pipeline",
                step_label="生成报告",
                status="running",
            )
            self.assertEqual(first["status"], "running")
            result = record_automation_step(
                data_dir=tmp,
                run_id="20260604120000",
                step_key="pipeline",
                step_label="生成报告",
                status="completed",
                exit_code=0,
            )
            latest = load_latest_automation_run(tmp)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(latest["summary"]["completed_count"], 1)
        self.assertEqual(latest["steps"][0]["exit_code"], 0)
        self.assertIn("latest_run.json", result["latest_path"])

    def test_failed_step_sanitizes_long_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_automation_step(
                data_dir=tmp,
                run_id="20260604120001",
                step_key="search",
                step_label="搜索验证",
                status="running",
            )
            result = record_automation_step(
                data_dir=tmp,
                run_id="20260604120001",
                step_key="search",
                step_label="搜索验证",
                status="failed",
                exit_code=2,
                error_summary="x" * 700,
            )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["summary"]["failed_count"], 1)
        self.assertEqual(len(result["steps"][0]["error_summary"]), 500)

    def test_render_dashboard_contains_steps_without_secrets(self) -> None:
        payload = {
            "run_id": "20260604120002",
            "status": "completed",
            "updated_at": "2026-06-04T00:00:00+00:00",
            "summary": {"step_count": 1, "completed_count": 1, "failed_count": 0, "running_count": 0},
            "steps": [
                {
                    "step_key": "auth",
                    "label": "平台授权验证",
                    "status": "completed",
                    "duration_seconds": 1,
                    "exit_code": 0,
                }
            ],
        }
        html = render_automation_dashboard(payload)
        self.assertIn("自动化运行状态", html)
        self.assertIn("平台授权验证", html)
        self.assertNotIn("SESSDATA=", html)

    def test_write_automation_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_automation_step(
                data_dir=tmp,
                run_id="20260604120003",
                step_key="pipeline",
                step_label="生成报告",
                status="completed",
            )
            output = Path(tmp) / "automation.html"
            result = write_automation_dashboard(output, data_dir=tmp)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_records_step_and_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "automation-step",
                        "--data-dir",
                        str(root / "data"),
                        "--run-id",
                        "20260604120004",
                        "--step-key",
                        "pipeline",
                        "--step-label",
                        "生成报告",
                        "--status",
                        "completed",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["summary"]["completed_count"], 1)

            dashboard = root / "automation.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "automation-dashboard",
                        "--data-dir",
                        str(root / "data"),
                        "--output",
                        str(dashboard),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            rendered = json.loads(out.getvalue())
            self.assertEqual(rendered["dashboard_path"], str(dashboard))
            self.assertTrue(dashboard.exists())


if __name__ == "__main__":
    unittest.main()
