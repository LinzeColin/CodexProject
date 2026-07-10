from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "KMFA" / "tools" / "automation" / "check_kmfa_automation_schedules.py"
CONTRACT = REPO_ROOT / "KMFA" / "metadata" / "automation" / "codex_app_schedules.contract.toml"
EVENING_PROMPT = REPO_ROOT / "KMFA" / "kmfa-dingtalk-attendance-skill" / "automation" / "evening_prompt.md"


class KmfaAutomationScheduleContractTests(unittest.TestCase):
    def test_kmfa_evening_contract_is_local_wall_clock_2000_without_scheduler_timezone(self) -> None:
        contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        evening = next(item for item in contract["automations"] if item["id"] == "kmfa-3")

        self.assertEqual(
            evening["rrule"],
            "RRULE:FREQ=WEEKLY;BYHOUR=20;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA",
        )
        self.assertNotIn("business_time", evening)
        self.assertEqual(evening["business_clock"], "Asia/Shanghai")
        self.assertEqual(evening["local_wall_clock_time"], "20:00")
        self.assertEqual(
            evening["summary_datetime_source"],
            "actual_run_datetime_in_business_clock",
        )
        self.assertTrue(evening["fixed_local_wall_clock"])
        self.assertFalse(evening["offset_conversion_allowed"])
        self.assertNotIn("timezone", evening)
        self.assertNotIn("tzid", evening)
        self.assertNotIn("scheduler_timezone", evening)
        self.assertNotIn("TZID", evening["rrule"])
        self.assertNotIn("DTSTART", evening["rrule"])
        expected_prompt_hash = hashlib.sha256(
            EVENING_PROMPT.read_text(encoding="utf-8").rstrip("\r\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(evening["prompt_sha256"], expected_prompt_hash)
        self.assertEqual(evening["project_id"], "40dd52a0-b6eb-4528-9577-0cb5f4f86e3e")

    def test_kmfa_evening_prompt_locks_exact_entry_and_authoritative_healthcheck(self) -> None:
        prompt = EVENING_PROMPT.read_text(encoding="utf-8")

        self.assertIn("Scheduled local wall-clock time: 20:00.", prompt)
        self.assertIn(
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai",
            prompt,
        )
        self.assertIn("config-only healthcheck is authoritative", prompt)

    def test_checker_rejects_dtstart_tzid_and_explicit_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract_path = root / "contract.toml"
            contract_path.write_text(
                textwrap.dedent(
                    """
                    version = 1

                    [[automations]]
                    id = "kmfa"
                    rrule = "RRULE:FREQ=DAILY;BYHOUR=12;BYMINUTE=35"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            automation_dir = root / "automations" / "kmfa"
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(
                textwrap.dedent(
                    """
                    id = "kmfa"
                    status = "ACTIVE"
                    timezone = "Asia/Shanghai"
                    rrule = "DTSTART;TZID=Asia/Shanghai:20260710T103500\\nRRULE:FREQ=DAILY"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "--contract-path",
                    str(contract_path),
                    "--automation-root",
                    str(root / "automations"),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 4, completed.stderr or completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "CODEX_AUTOMATION_MISMATCH")
            mismatches = payload["automations"][0]["mismatches"]
            self.assertIn("forbidden_dtstart_or_tzid", mismatches)
            self.assertIn("forbidden_explicit_timezone", mismatches)
            self.assertIn("rrule", mismatches)

    def test_checker_rejects_prompt_and_project_binding_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expected_prompt = "canonical prompt"
            expected_hash = hashlib.sha256(expected_prompt.encode("utf-8")).hexdigest()
            contract_path = root / "contract.toml"
            contract_path.write_text(
                textwrap.dedent(
                    f"""
                    version = 1

                    [[automations]]
                    id = "kmfa-3"
                    status = "ACTIVE"
                    rrule = "RRULE:FREQ=WEEKLY;BYHOUR=20;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA"
                    prompt_sha256 = "{expected_hash}"
                    project_id = "canonical-project"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            automation_dir = root / "automations" / "kmfa-3"
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(
                textwrap.dedent(
                    """
                    id = "kmfa-3"
                    status = "ACTIVE"
                    rrule = "RRULE:FREQ=WEEKLY;BYHOUR=20;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA"
                    prompt = "stale prompt"
                    target = { type = "project", project_id = "stale-project" }
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "--contract-path",
                    str(contract_path),
                    "--automation-root",
                    str(root / "automations"),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 4, completed.stderr or completed.stdout)
            mismatches = json.loads(completed.stdout)["automations"][0]["mismatches"]
            self.assertIn("prompt", mismatches)
            self.assertIn("project_id", mismatches)

    def test_checker_accepts_one_pure_rrule_without_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract_path = root / "contract.toml"
            contract_path.write_text(
                textwrap.dedent(
                    """
                    version = 1

                    [[automations]]
                    id = "kmfa-4"
                    status = "ACTIVE"
                    rrule = "RRULE:FREQ=DAILY;BYHOUR=13,19;BYMINUTE=5,35;BYSETPOS=2,3"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            automation_dir = root / "automations" / "kmfa-4"
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(
                textwrap.dedent(
                    """
                    id = "kmfa-4"
                    status = "ACTIVE"
                    rrule = "RRULE:FREQ=DAILY;BYHOUR=13,19;BYMINUTE=5,35;BYSETPOS=2,3"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "--contract-path",
                    str(contract_path),
                    "--automation-root",
                    str(root / "automations"),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual(json.loads(completed.stdout)["status"], "CODEX_AUTOMATIONS_READY")

    def test_checker_rejects_multiline_contract_rrule(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract_path = root / "contract.toml"
            contract_path.write_text(
                'version = 1\n[[automations]]\nid = "kmfa"\n'
                'rrule = "RRULE:FREQ=DAILY;BYHOUR=12;BYMINUTE=35\\nRRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=5"\n',
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "--contract-path",
                    str(contract_path),
                    "--automation-root",
                    str(root / "automations"),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 3, completed.stderr or completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "CODEX_AUTOMATION_CONTRACT_INVALID")
            self.assertIn(
                "forbidden_multiple_or_multiline_rrule",
                payload["automations"][0]["errors"],
            )


if __name__ == "__main__":
    unittest.main()
