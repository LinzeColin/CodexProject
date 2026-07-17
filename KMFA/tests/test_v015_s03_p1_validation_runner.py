from __future__ import annotations

import contextlib
import io
import os
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from KMFA.tools import run_v015_s03_p1_validations as runner


class TestV015S03P1ValidationRunner(unittest.TestCase):
    def test_parse_command_extracts_environment_without_shell(self) -> None:
        environment, argv = runner.parse_command(
            'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c "print(1)"'
        )
        self.assertEqual(environment, {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
        self.assertEqual(argv, ["python3", "-B", "-c", "print(1)"])

    def _clock(self):
        return lambda: datetime(2026, 7, 13, 6, 0, tzinfo=timezone.utc)

    def test_pass_receipt_binds_subject_head_hashes_and_sequence(self) -> None:
        completed = subprocess.CompletedProcess(["tool"], 0, b"ok", b"")
        rows, passed = runner.build_receipts(
            {"one": "tool --check"},
            executor=lambda command: completed,
            subject_resolver=lambda: "sha256:" + "a" * 64,
            head_resolver=lambda: "b" * 40,
            clock=self._clock(),
            monotonic_ns=iter((1_000_000, 4_000_000)).__next__,
            run_id="1" * 32,
        )
        self.assertTrue(passed)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["result"], row["exit_code"], row["execution_sequence"]), ("PASS", 0, 1))
        self.assertEqual(row["duration_ms"], 3)
        self.assertEqual(row["validation_subject_sha256"], "sha256:" + "a" * 64)
        self.assertRegex(row["stdout_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_command_failure_is_recorded_without_output_disclosure(self) -> None:
        completed = subprocess.CompletedProcess(["tool"], 9, b"private output", b"failure detail")
        rows, passed = runner.build_receipts(
            {"one": "tool"},
            executor=lambda command: completed,
            subject_resolver=lambda: "sha256:" + "c" * 64,
            head_resolver=lambda: "d" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="2" * 32,
        )
        self.assertFalse(passed)
        self.assertEqual((rows[0]["result"], rows[0]["exit_code"]), ("FAIL", 9))
        serialized = str(rows[0])
        self.assertNotIn("private output", serialized)
        self.assertNotIn("failure detail", serialized)

    def test_subject_drift_fails_even_when_command_exits_zero(self) -> None:
        subjects = iter(("sha256:" + "e" * 64, "sha256:" + "e" * 64, "sha256:" + "f" * 64))
        rows, passed = runner.build_receipts(
            {"one": "tool"},
            executor=lambda command: subprocess.CompletedProcess(["tool"], 0, b"", b""),
            subject_resolver=subjects.__next__,
            head_resolver=lambda: "a" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="3" * 32,
        )
        self.assertFalse(passed)
        self.assertEqual((rows[0]["result"], rows[0]["exit_code"]), ("FAIL", 98))

    def test_first_failure_stops_later_commands(self) -> None:
        calls = []

        def execute(command):
            calls.append(command)
            return subprocess.CompletedProcess(["tool"], 1, b"", b"failed")

        rows, passed = runner.build_receipts(
            {"first": "tool first", "raw_guard": "tool raw"},
            executor=execute,
            subject_resolver=lambda: "sha256:" + "9" * 64,
            head_resolver=lambda: "8" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="4" * 32,
        )
        self.assertFalse(passed)
        self.assertEqual(calls, ["tool first"])
        self.assertEqual((rows[1]["result"], rows[1]["exit_code"]), ("PENDING", None))
        self.assertEqual(rows[1]["skip_reason"], "STOP_AFTER_first")

    def test_private_receipts_are_atomically_written_mode_0600(self) -> None:
        private_root = runner.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            output = Path(directory) / "receipts.jsonl"
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(stat.S_IMODE(os.lstat(output).st_mode), 0o600)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"result": "PASS"}\n')

    def test_private_writer_rejects_symlink_and_hardlink(self) -> None:
        private_root = runner.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            source.write_text("protected\n", encoding="utf-8")
            output = root / "receipts.jsonl"
            os.link(source, output)
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                with self.assertRaisesRegex(runner.RunnerError, "unsafe"):
                    runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(source.read_text(encoding="utf-8"), "protected\n")
            output.unlink()
            output.symlink_to(source)
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                with self.assertRaisesRegex(runner.RunnerError, "unsafe"):
                    runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(source.read_text(encoding="utf-8"), "protected\n")

    def test_cli_rejects_arguments_before_running(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(["--unexpected"]), 2)


if __name__ == "__main__":
    unittest.main()
