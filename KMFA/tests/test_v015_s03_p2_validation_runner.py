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

from KMFA.tools import run_v015_s03_p2_validations as runner


class TestV015S03P2ValidationRunner(unittest.TestCase):
    def _clock(self):
        return lambda: datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)

    def test_parse_command_extracts_environment_without_shell(self) -> None:
        environment, argv = runner.parse_command(
            'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c "print(1)"'
        )
        self.assertEqual(environment, {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
        self.assertEqual(argv, ["python3", "-B", "-c", "print(1)"])

    def test_pass_receipt_binds_subject_head_and_sequence(self) -> None:
        rows, passed = runner.build_receipts(
            {"one": "tool --check"},
            executor=lambda command: subprocess.CompletedProcess(["tool"], 0, b"ok", b""),
            subject_resolver=lambda: "sha256:" + "a" * 64,
            head_resolver=lambda: "b" * 40,
            clock=self._clock(),
            monotonic_ns=iter((1_000_000, 4_000_000)).__next__,
            run_id="1" * 32,
        )
        self.assertTrue(passed)
        self.assertEqual((rows[0]["result"], rows[0]["exit_code"], rows[0]["duration_ms"]), ("PASS", 0, 3))
        self.assertRegex(rows[0]["stdout_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_failure_discloses_only_output_digests(self) -> None:
        rows, passed = runner.build_receipts(
            {"one": "tool"},
            executor=lambda command: subprocess.CompletedProcess(["tool"], 9, b"private output", b"secret detail"),
            subject_resolver=lambda: "sha256:" + "c" * 64,
            head_resolver=lambda: "d" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="2" * 32,
        )
        self.assertFalse(passed)
        self.assertNotIn("private output", str(rows[0]))
        self.assertNotIn("secret detail", str(rows[0]))

    def test_subject_drift_fails_zero_exit_command(self) -> None:
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
            {"first": "tool first", "second": "tool second"},
            executor=execute,
            subject_resolver=lambda: "sha256:" + "9" * 64,
            head_resolver=lambda: "8" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="4" * 32,
        )
        self.assertFalse(passed)
        self.assertEqual(calls, ["tool first"])
        self.assertEqual(rows[1]["result"], "PENDING")

    def test_private_writer_is_atomic_mode_0600(self) -> None:
        private_root = runner.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            output = Path(directory) / "receipts.jsonl"
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(stat.S_IMODE(os.lstat(output).st_mode), 0o600)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"result": "PASS"}\n')

    def test_private_writer_rejects_hardlink(self) -> None:
        private_root = runner.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            root = Path(directory)
            source = root / "source"
            source.write_text("protected\n", encoding="utf-8")
            output = root / "receipts.jsonl"
            os.link(source, output)
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                with self.assertRaisesRegex(runner.RunnerError, "unsafe"):
                    runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(source.read_text(encoding="utf-8"), "protected\n")

    def test_private_writer_rejects_symlink(self) -> None:
        private_root = runner.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            root = Path(directory)
            source = root / "source"
            source.write_text("protected\n", encoding="utf-8")
            output = root / "receipts.jsonl"
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
