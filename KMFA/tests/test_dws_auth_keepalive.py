from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from KMFA.tools.automation import dws_auth_keepalive as keepalive


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "KMFA" / "tools" / "automation" / "dws_auth_keepalive.py"


class DwsAuthKeepaliveTests(unittest.TestCase):
    def run_scenario(
        self,
        scenario: str,
        attempts: int = 3,
        command_timeout_seconds: float = 25,
        dws_timeout_seconds: int = 20,
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            log = root / "commands.log"
            profile_config = root / "expected_profile.json"
            ledger = root / "memory.md"
            keepalive_state = root / "keepalive_state.json"
            profile_config.write_text(
                json.dumps({"version": 1, "profile": "corp-test"}),
                encoding="utf-8",
            )
            fake_dws = root / "dws"
            fake_dws.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import os
                    import sys
                    import time
                    from pathlib import Path

                    state = Path(os.environ["FAKE_DWS_STATE"])
                    log = Path(os.environ["FAKE_DWS_LOG"])
                    scenario = os.environ["FAKE_DWS_SCENARIO"]
                    args = sys.argv[1:]
                    with log.open("a", encoding="utf-8") as handle:
                        handle.write(" ".join(args) + "\\n")

                    if args[:2] == ["auth", "status"]:
                        count = int(state.read_text() or "0") if state.exists() else 0
                        count += 1
                        state.write_text(str(count))
                        if scenario == "malformed_json" or (
                            scenario == "transient_malformed" and count == 1
                        ):
                            print("not-json")
                            raise SystemExit(0)
                        if scenario == "command_failure":
                            raise SystemExit(7)
                        if scenario == "timeout":
                            time.sleep(3)
                        base = {
                            "success": True,
                            "authenticated": True,
                            "expires_at": "2099-07-11T10:00:00+10:00",
                            "refresh_expires_at": "2099-08-10T00:00:00+10:00",
                            "corp_id": "corp-test",
                            "corp_name": "Test Corp",
                        }
                        if scenario in {
                            "healthy",
                            "doctor_command_failure",
                            "doctor_failure",
                            "doctor_malformed_json",
                            "doctor_malformed_summary",
                            "access_expired",
                            "access_malformed",
                            "refresh_expired",
                            "refresh_missing",
                        }:
                            base.update(token_valid=True, refresh_token_valid=True)
                        elif scenario == "refresh_success" and count >= 2:
                            base.update(token_valid=True, refresh_token_valid=True, refreshed=True)
                        elif scenario == "access_valid_refresh_invalid":
                            base.update(token_valid=True, refresh_token_valid=False)
                        elif scenario == "unauthenticated_token_valid":
                            base.update(authenticated=False, token_valid=True, refresh_token_valid=True)
                        elif scenario == "unsuccessful_token_valid":
                            base.update(success=False, token_valid=True, refresh_token_valid=True)
                        elif scenario == "profile_mismatch":
                            base.update(corp_id="corp-other", token_valid=True, refresh_token_valid=True)
                        elif scenario == "refresh_invalid":
                            base.update(refresh_token_valid=False)
                        else:
                            base.update(refresh_token_valid=True)
                        if scenario == "access_expired":
                            base["expires_at"] = "2020-01-01T00:00:00+00:00"
                        elif scenario == "access_malformed":
                            base["expires_at"] = "not-a-timestamp"
                        elif scenario == "refresh_expired":
                            base["refresh_expires_at"] = "2020-01-01T00:00:00+00:00"
                        elif scenario == "refresh_missing":
                            base.pop("refresh_expires_at")
                        print(json.dumps(base))
                        raise SystemExit(0)

                    if args == ["doctor", "--json"]:
                        print(json.dumps({"error": "missing timeout flag"}))
                        raise SystemExit(9)
                    if args == [
                        "doctor", "--json", "--profile", "corp-test", "--timeout", "20"
                    ]:
                        if scenario == "doctor_command_failure":
                            raise SystemExit(8)
                        if scenario == "doctor_failure":
                            print(json.dumps({
                                "kind": "doctor",
                                "summary": {"pass": 4, "warn": 0, "fail": 1},
                            }))
                            raise SystemExit(0)
                        if scenario == "doctor_malformed_json":
                            print("not-json")
                            raise SystemExit(0)
                        if scenario == "doctor_malformed_summary":
                            print(json.dumps({
                                "kind": "doctor",
                                "summary": {"pass": "invalid", "warn": 0, "fail": 0},
                            }))
                            raise SystemExit(0)
                        print(json.dumps({
                            "kind": "doctor",
                            "summary": {"pass": 5, "warn": 0, "fail": 0},
                            "checks": [],
                        }))
                        raise SystemExit(0)

                    print(json.dumps({"error": "unexpected command"}))
                    raise SystemExit(9)
                    """
                ),
                encoding="utf-8",
            )
            fake_dws.chmod(0o755)
            env = os.environ | {
                "FAKE_DWS_STATE": str(state),
                "FAKE_DWS_LOG": str(log),
                "FAKE_DWS_SCENARIO": scenario,
            }
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--dws-bin",
                    str(fake_dws),
                    "--attempts",
                    str(attempts),
                    "--backoff-seconds",
                    "0",
                    "--command-timeout-seconds",
                    str(command_timeout_seconds),
                    "--dws-timeout-seconds",
                    str(dws_timeout_seconds),
                    "--profile-config",
                    str(profile_config),
                    "--ledger-path",
                    str(ledger),
                    "--state-path",
                    str(keepalive_state),
                ],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            commands = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
            return completed, commands

    def test_healthy_access_token_does_not_login(self) -> None:
        completed, commands = self.run_scenario("healthy")

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "healthy")
        self.assertTrue(payload["token_valid"])
        self.assertEqual(payload["attempts_used"], 1)
        self.assertEqual(
            commands,
            [
                "auth status --format json --profile corp-test --timeout 20",
                "doctor --json --profile corp-test --timeout 20",
            ],
        )

    def test_expired_access_token_is_refreshed_by_status_retry_without_login(self) -> None:
        completed, commands = self.run_scenario("refresh_success")

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "refreshed")
        self.assertTrue(payload["refreshed"])
        self.assertTrue(payload["token_valid"])
        self.assertEqual(payload["attempts_used"], 2)
        self.assertEqual(
            commands.count(
                "auth status --format json --profile corp-test --timeout 20"
            ),
            2,
        )
        self.assertNotIn("auth login", "\n".join(commands))

    def test_silent_status_success_without_token_valid_fails_closed(self) -> None:
        completed, commands = self.run_scenario("refresh_failed")

        self.assertEqual(completed.returncode, 3, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "auto_refresh_failed")
        self.assertFalse(payload["token_valid"])
        self.assertTrue(payload["refresh_token_valid"])
        self.assertEqual(payload["attempts_used"], 3)
        self.assertEqual(
            commands,
            ["auth status --format json --profile corp-test --timeout 20"] * 3,
        )
        self.assertIn("dws auth login --device", payload["next_action"])
        self.assertIn('--profile "$DWS_KEEPALIVE_PROFILE"', payload["next_action"])
        self.assertNotIn("auth login", "\n".join(commands))

    def test_invalid_refresh_token_requires_device_login_without_starting_it(self) -> None:
        completed, commands = self.run_scenario("refresh_invalid")

        self.assertEqual(completed.returncode, 4, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "needs_manual_auth")
        self.assertFalse(payload["refresh_token_valid"])
        self.assertEqual(payload["attempts_used"], 1)
        self.assertIn("dws auth login --device", payload["next_action"])
        self.assertIn('--profile "$DWS_KEEPALIVE_PROFILE"', payload["next_action"])
        self.assertEqual(
            commands,
            ["auth status --format json --profile corp-test --timeout 20"],
        )

    def test_malformed_json_fails_closed_without_login(self) -> None:
        completed, commands = self.run_scenario("malformed_json", attempts=2)

        self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "MALFORMED_JSON")
        self.assertEqual(
            commands,
            ["auth status --format json --profile corp-test --timeout 20"] * 2,
        )
        self.assertNotIn("auth login", "\n".join(commands))

    def test_nonzero_auth_status_fails_closed_without_login(self) -> None:
        completed, commands = self.run_scenario("command_failure", attempts=2)

        self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "COMMAND_EXIT_7")
        self.assertEqual(
            commands,
            ["auth status --format json --profile corp-test --timeout 20"] * 2,
        )
        self.assertNotIn("auth login", "\n".join(commands))

    def test_earlier_transient_error_does_not_mask_final_parsed_failure_reason(self) -> None:
        completed, commands = self.run_scenario("transient_malformed", attempts=2)

        self.assertEqual(completed.returncode, 3, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "auto_refresh_failed")
        self.assertEqual(payload["reason"], "TOKEN_VALID_NOT_TRUE_AFTER_REFRESH_ATTEMPTS")
        self.assertEqual(
            commands,
            ["auth status --format json --profile corp-test --timeout 20"] * 2,
        )

    def test_auth_status_timeout_fails_closed_without_login(self) -> None:
        completed, commands = self.run_scenario(
            "timeout",
            attempts=2,
            command_timeout_seconds=1.5,
            dws_timeout_seconds=1,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "COMMAND_TIMEOUT")
        self.assertEqual(payload["attempts_used"], 2)
        self.assertTrue(
            all(
                command == "auth status --format json --profile corp-test --timeout 1"
                for command in commands
            )
        )
        self.assertNotIn("auth login", "\n".join(commands))

    def test_malformed_doctor_summary_fails_closed(self) -> None:
        completed, commands = self.run_scenario("doctor_malformed_summary")

        self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(payload["token_valid"])
        self.assertEqual(payload["doctor"]["status"], "unavailable")
        self.assertEqual(payload["doctor"]["reason"], "DOCTOR_SUMMARY_INVALID")
        self.assertEqual(
            commands,
            [
                "auth status --format json --profile corp-test --timeout 20",
                "doctor --json --profile corp-test --timeout 20",
            ],
        )

    def test_access_valid_but_refresh_invalid_requires_manual_auth(self) -> None:
        completed, commands = self.run_scenario("access_valid_refresh_invalid")

        self.assertEqual(completed.returncode, 4, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "needs_manual_auth")
        self.assertTrue(payload["token_valid"])
        self.assertFalse(payload["refresh_token_valid"])
        self.assertNotIn("doctor", "\n".join(commands))

    def test_inconsistent_success_or_authentication_fails_closed(self) -> None:
        for scenario in ("unauthenticated_token_valid", "unsuccessful_token_valid"):
            with self.subTest(scenario=scenario):
                completed, commands = self.run_scenario(scenario, attempts=1)
                self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "blocked")
                self.assertEqual(payload["reason"], "AUTH_STATUS_INCONSISTENT")
                self.assertNotIn("doctor", "\n".join(commands))

    def test_profile_mismatch_fails_closed(self) -> None:
        completed, commands = self.run_scenario("profile_mismatch", attempts=1)

        self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "PROFILE_MISMATCH")
        self.assertFalse(payload["profile_match"])
        self.assertNotIn("doctor", "\n".join(commands))

    def test_doctor_fail_or_unavailable_propagates_nonzero(self) -> None:
        expectations = {
            "doctor_failure": "DOCTOR_FAILED",
            "doctor_command_failure": "COMMAND_EXIT_8",
            "doctor_malformed_json": "MALFORMED_JSON",
        }
        for scenario, reason in expectations.items():
            with self.subTest(scenario=scenario):
                completed, commands = self.run_scenario(scenario)
                self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "blocked")
                self.assertEqual(payload["reason"], reason)
                self.assertTrue(payload["token_valid"])
                self.assertIn("doctor --json --profile corp-test --timeout 20", commands)

    def test_access_and_refresh_expiry_must_be_parseable_and_future(self) -> None:
        expectations = {
            "access_expired": "ACCESS_EXPIRY_NOT_FUTURE",
            "access_malformed": "ACCESS_EXPIRY_INVALID",
            "refresh_expired": "REFRESH_EXPIRY_NOT_FUTURE",
            "refresh_missing": "REFRESH_EXPIRY_INVALID",
        }
        for scenario, reason in expectations.items():
            with self.subTest(scenario=scenario):
                completed, commands = self.run_scenario(scenario)
                self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "blocked")
                self.assertEqual(payload["reason"], reason)
                self.assertTrue(payload["token_valid"])
                self.assertNotIn("doctor", "\n".join(commands))

    def test_ledger_is_private_sanitized_atomic_and_reminder_deduped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "automation"
            ledger = root / "memory.md"
            state = root / "state.json"
            root.mkdir()
            ledger.write_text("legacy corp_id=secret-corp corp_name=secret-name\n")
            now = datetime(2099, 8, 9, 1, 0, tzinfo=timezone.utc)
            refresh_expiry = now + timedelta(hours=23)
            base = {
                "status": "healthy",
                "authenticated": True,
                "token_valid": True,
                "refresh_token_valid": True,
                "refreshed": False,
                "profile_match": True,
                "access_expires_at": (now + timedelta(hours=2)).isoformat(),
                "refresh_expires_at": refresh_expiry.isoformat(),
                "attempts_used": 1,
                "doctor": {"status": "ok", "pass": 5, "warn": 0, "fail": 0},
                "next_action": "continue_monitoring",
                "corp_id": "must-not-be-written",
                "corp_name": "must-not-be-written",
            }

            first = keepalive.persist_sanitized_ledger(dict(base), ledger, state, now)
            second = keepalive.persist_sanitized_ledger(
                dict(base), ledger, state, now + timedelta(minutes=1)
            )
            final_window = keepalive.persist_sanitized_ledger(
                dict(base), ledger, state, now + timedelta(hours=20)
            )

            self.assertEqual(first["reminder_window"], "within_24h")
            self.assertTrue(first["reminder_due"])
            self.assertFalse(second["reminder_due"])
            self.assertEqual(final_window["reminder_window"], "last_4h")
            self.assertTrue(final_window["reminder_due"])
            active_text = ledger.read_text(encoding="utf-8")
            self.assertTrue(active_text.startswith(keepalive.LEDGER_HEADER))
            self.assertNotIn("must-not-be-written", active_text)
            self.assertNotIn("secret-corp", active_text)
            legacy = root / "memory.legacy-private.md"
            self.assertTrue(legacy.is_file())
            self.assertIn("secret-corp", legacy.read_text(encoding="utf-8"))
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            self.assertEqual(state.stat().st_mode & 0o777, 0o600)
            self.assertEqual(legacy.stat().st_mode & 0o777, 0o600)
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)

    def test_bootstrap_pins_current_profile_privately_without_printing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "automation"
            root.mkdir()
            fake_dws = root / "dws"
            fake_dws.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import sys
                    if sys.argv[1:] != ["profile", "list", "--format", "json", "--timeout", "20"]:
                        raise SystemExit(9)
                    print(json.dumps({
                        "success": True,
                        "currentProfile": "corp-test",
                        "profiles": [{"corpId": "corp-test", "isCurrent": True}],
                    }))
                    """
                ),
                encoding="utf-8",
            )
            fake_dws.chmod(0o755)
            profile_config = root / "expected_profile.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--dws-bin",
                    str(fake_dws),
                    "--bootstrap-current-profile",
                    "--profile-config",
                    str(profile_config),
                    "--state-path",
                    str(root / "state.json"),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            output = json.loads(completed.stdout)
            self.assertEqual(output["status"], "profile_pinned")
            self.assertNotIn("corp-test", completed.stdout)
            saved = json.loads(profile_config.read_text(encoding="utf-8"))
            self.assertEqual(saved["profile"], "corp-test")
            self.assertEqual(profile_config.stat().st_mode & 0o777, 0o600)

    def test_missing_profile_config_blocks_before_invoking_dws(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "automation"
            root.mkdir()
            log = root / "commands.log"
            fake_dws = root / "dws"
            fake_dws.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import os
                    from pathlib import Path
                    Path(os.environ["FAKE_DWS_LOG"]).write_text("called")
                    raise SystemExit(9)
                    """
                ),
                encoding="utf-8",
            )
            fake_dws.chmod(0o755)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--dws-bin",
                    str(fake_dws),
                    "--profile-config",
                    str(root / "missing_profile.json"),
                    "--ledger-path",
                    str(root / "memory.md"),
                    "--state-path",
                    str(root / "state.json"),
                ],
                cwd=REPO_ROOT,
                env=os.environ | {"FAKE_DWS_LOG": str(log)},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["reason"], "PROFILE_CONFIG_MISSING")
            self.assertEqual(payload["next_action"], "pin_expected_profile")
            self.assertFalse(log.exists())


if __name__ == "__main__":
    unittest.main()
