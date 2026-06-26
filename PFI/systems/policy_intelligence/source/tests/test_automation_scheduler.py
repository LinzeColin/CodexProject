from __future__ import annotations

import io
import json
import plistlib
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.automation_scheduler import (
    build_launchd_plist,
    write_automation_scheduler_plan,
)
from source_registry.cli import main as cli_main


class AutomationSchedulerPlanTest(unittest.TestCase):
    def test_build_launchd_plist_uses_two_calendar_intervals(self) -> None:
        payload = build_launchd_plist(
            workspace=Path("/tmp/policy-workspace"),
            data_dir=Path("data"),
            label="com.example.policy",
            schedule_times=["09:00", "21:00"],
            entrypoint="bash scripts/run_policy_report.sh",
        )
        self.assertEqual(payload["Label"], "com.example.policy")
        self.assertEqual(payload["StartCalendarInterval"], [{"Hour": 9, "Minute": 0}, {"Hour": 21, "Minute": 0}])
        self.assertIn("run_policy_report.sh", payload["ProgramArguments"][-1])
        self.assertIn("data/run_logs/launchd.out.log", payload["StandardOutPath"])

    def test_scheduler_plan_writes_reviewable_artifacts_without_scheduler_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_automation_scheduler_plan(
                root / "reports",
                workspace=root,
                data_dir="data",
                label="com.example.policy",
                schedule_times=["09:00", "21:00"],
            )
            artifacts = result["artifacts"]
            plist_path = Path(artifacts["launchd_plist"])
            manifest_path = Path(artifacts["scheduler_manifest_example"])
            dashboard_path = Path(artifacts["dashboard"])
            self.assertTrue(plist_path.exists())
            self.assertTrue(manifest_path.exists())
            self.assertTrue(dashboard_path.exists())
            self.assertFalse((root / "data" / "automation" / "scheduler.json").exists())
            plist = plistlib.loads(plist_path.read_bytes())
            self.assertEqual(plist["Label"], "com.example.policy")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(manifest["enabled"])
            self.assertIn("Only create", manifest["notes"])
            self.assertEqual(result["status"], "planned_not_installed")

    def test_cli_automation_scheduler_plan_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "automation-scheduler-plan",
                        "--workspace",
                        str(root),
                        "--output-dir",
                        str(root / "reports"),
                        "--schedule-time",
                        "09:00",
                        "--schedule-time",
                        "21:00",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["status"], "planned_not_installed")
            self.assertTrue(Path(payload["artifacts"]["dashboard"]).exists())
            self.assertNotIn("SESSDATA=", out.getvalue())
            self.assertNotIn("sk-", out.getvalue())


if __name__ == "__main__":
    unittest.main()
