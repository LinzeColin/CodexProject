from __future__ import annotations

import hashlib
import json
import re
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
MORNING_PROMPT = REPO_ROOT / "KMFA" / "kmfa-dingtalk-attendance-skill" / "automation" / "morning_prompt.md"
DWS_AUTH_KEEPALIVE_PROMPT = (
    REPO_ROOT / "KMFA" / "metadata" / "automation" / "dws_auth_keepalive.prompt.md"
)
DAILY_ROUTINE_VALIDATOR = (
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "tools" / "validate_skill_package.py"
)
DAILY_ROUTINE_MANIFEST = (
    REPO_ROOT
    / "KMFA"
    / "metadata"
    / "daily_routine_check"
    / "codex_automation"
    / "automation_manifest.json"
)
DAILY_ROUTINE_PROMPT = (
    REPO_ROOT
    / "KMFA"
    / "metadata"
    / "daily_routine_check"
    / "codex_automation"
    / "daily_routine_check.prompt.md"
)
DAILY_ROUTINE_CONTRACT_FILES = (
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "SKILL.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "README.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "功能清单.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "references" / "codex_desktop_setup.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "references" / "configuration.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "references" / "data_contract.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "references" / "runbook.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "references" / "rules.md",
    REPO_ROOT / "KMFA" / "daily_routine_check_skill" / "templates" / "env.local.example",
    REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "README.md",
    REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "routine_rules.public.yaml",
    REPO_ROOT / "KMFA" / "metadata" / "daily_routine_check" / "onedrive_storage_manifest.yaml",
    DAILY_ROUTINE_MANIFEST,
    DAILY_ROUTINE_PROMPT,
    REPO_ROOT
    / "KMFA"
    / "metadata"
    / "daily_routine_check"
    / "codex_automation"
    / "install_or_update_skill.prompt.md",
)
CANONICAL_DWS_OUTPUT_ZIP = (
    "/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip"
)
TRIGGER_ONCE_PATTERN = re.compile(
    r"exactly one matching (?:trigger )?window(?: command)? once",
    re.IGNORECASE,
)


class KmfaAutomationScheduleContractTests(unittest.TestCase):
    def test_dws_auth_keepalive_uses_deterministic_refresh_wrapper(self) -> None:
        prompt = DWS_AUTH_KEEPALIVE_PROMPT.read_text(encoding="utf-8")
        contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        keepalive = next(
            item for item in contract["automations"]
            if item["id"] == "dws-auth-keepalive-2"
        )

        self.assertIn(
            "/Users/linzezhang/CodexProject/KMFA/tools/automation/dws_auth_keepalive.py",
            prompt,
        )
        self.assertNotIn("auth login --format json --yes --no-browser", prompt)
        self.assertNotIn("automations/dws-auth-keepalive/memory.md", prompt)
        self.assertIn("automations/dws-auth-keepalive-2/memory.md", prompt)
        self.assertIn("Do not execute any `dws auth login` command", prompt)
        self.assertIn("private-pinned-profile", prompt)
        self.assertIn("parseable", prompt)
        self.assertIn("atomically writes 0600", prompt)
        expected_prompt_hash = hashlib.sha256(
            prompt.rstrip("\r\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(keepalive["prompt_sha256"], expected_prompt_hash)
        self.assertEqual(keepalive["project_id"], "cbf3c45e-f4ad-47d7-b397-faf7e3dea35e")
        self.assertEqual(
            keepalive["rrule"],
            "RRULE:FREQ=DAILY;BYHOUR=0,4,8,12,16,20;BYMINUTE=20",
        )
        self.assertEqual(keepalive["profile_selection"], "machine_private_pinned_profile")
        self.assertEqual(keepalive["dws_timeout_seconds"], 20)
        self.assertEqual(keepalive["outer_timeout_seconds"], 25)
        self.assertFalse(keepalive["automatic_login_allowed"])
        self.assertEqual(keepalive["ledger_owner"], "deterministic_wrapper")
        self.assertNotIn("timezone", keepalive)

    def test_daily_routine_contract_is_zip_only_without_folder_fallback(self) -> None:
        manifest = json.loads(DAILY_ROUTINE_MANIFEST.read_text(encoding="utf-8"))
        corpus = "\n".join(
            path.read_text(encoding="utf-8") for path in DAILY_ROUTINE_CONTRACT_FILES
        )

        self.assertIs(manifest.get("zip_input_only"), True)
        self.assertEqual(manifest["zip_input_path"], CANONICAL_DWS_OUTPUT_ZIP)
        self.assertIn(CANONICAL_DWS_OUTPUT_ZIP, corpus)
        self.assertNotIn("input_root_default", corpus)
        self.assertNotIn("direct_input_fallback", corpus)
        self.assertNotIn("compatibility fallback", corpus.lower())

    def test_daily_routine_trigger_commands_are_explicit_single_runs_without_cleanup(self) -> None:
        manifest = json.loads(DAILY_ROUTINE_MANIFEST.read_text(encoding="utf-8"))
        prompt = DAILY_ROUTINE_PROMPT.read_text(encoding="utf-8")
        contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        routine = next(item for item in contract["automations"] if item["id"] == "kmfa-4")

        for trigger in manifest["trigger_windows"]:
            command = trigger["command"]
            self.assertIn(f"--input-zip {CANONICAL_DWS_OUTPUT_ZIP}", command)
            self.assertNotIn("--cleanup", command)
            self.assertNotIn("--apply", command)
        self.assertRegex(prompt, TRIGGER_ONCE_PATTERN)
        expected_prompt_hash = hashlib.sha256(
            prompt.rstrip("\r\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(routine["prompt_sha256"], expected_prompt_hash)
        self.assertEqual(routine["project_id"], "40dd52a0-b6eb-4528-9577-0cb5f4f86e3e")

        completed = subprocess.run(
            [sys.executable, str(DAILY_ROUTINE_VALIDATOR)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

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
            "TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot evening "
            "--trigger-source automation --automation-id kmfa-3 --allow-dws-commands",
            prompt,
        )
        self.assertIn("config-only healthcheck is authoritative", prompt)

    def test_attendance_prompts_do_not_run_legacy_sweep_or_mislabel_live_failures(self) -> None:
        required = (
            "The production official collector intentionally skips the legacy per-member record/summary sweep.",
            "Do not interrupt the entry while its process is still inside the runner's bounded DWS timeout/retry budget.",
            "must never be reported as DWS_AUTH_REQUIRED",
            "report the entry's exact final JSON status and exit code",
        )
        for path in (MORNING_PROMPT, EVENING_PROMPT):
            prompt = path.read_text(encoding="utf-8")
            for phrase in required:
                self.assertIn(phrase, prompt, path)

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
