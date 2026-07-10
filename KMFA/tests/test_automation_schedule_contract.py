from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "KMFA" / "tools" / "automation" / "check_kmfa_automation_schedules.py"


class KmfaAutomationScheduleContractTests(unittest.TestCase):
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
