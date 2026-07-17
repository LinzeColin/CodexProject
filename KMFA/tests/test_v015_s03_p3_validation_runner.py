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

from KMFA.tools import run_v015_s03_p3_validations as runner


class S03P3ValidationRunnerTests(unittest.TestCase):
    def _clock(self):
        return lambda: datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc)

    def test_parse_command_never_uses_a_shell(self) -> None:
        environment, argv = runner.parse_command(
            'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c "print(1)"'
        )
        self.assertEqual(environment, {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
        self.assertEqual(argv, ["python3", "-B", "-c", "print(1)"])

    def test_pass_receipt_binds_subject_head_and_digests_only(self) -> None:
        rows, passed = runner.build_receipts(
            {"one": "tool --check"},
            executor=lambda command: subprocess.CompletedProcess(["tool"], 0, b"private output", b""),
            subject_resolver=lambda: "sha256:" + "a" * 64,
            head_resolver=lambda: "b" * 40,
            clock=self._clock(),
            monotonic_ns=iter((1_000_000, 4_000_000)).__next__,
            run_id="1" * 32,
        )
        self.assertTrue(passed)
        self.assertEqual((rows[0]["result"], rows[0]["exit_code"], rows[0]["duration_ms"]), ("PASS", 0, 3))
        self.assertNotIn("private output", str(rows[0]))
        self.assertRegex(rows[0]["stdout_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_subject_drift_fails_zero_exit(self) -> None:
        subjects = iter(("sha256:" + "c" * 64, "sha256:" + "c" * 64, "sha256:" + "d" * 64))
        rows, passed = runner.build_receipts(
            {"one": "tool"},
            executor=lambda command: subprocess.CompletedProcess(["tool"], 0, b"", b""),
            subject_resolver=subjects.__next__,
            head_resolver=lambda: "e" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="2" * 32,
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
            subject_resolver=lambda: "sha256:" + "f" * 64,
            head_resolver=lambda: "a" * 40,
            clock=self._clock(),
            monotonic_ns=iter((0, 1)).__next__,
            run_id="3" * 32,
        )
        self.assertFalse(passed)
        self.assertEqual(calls, ["tool first"])
        self.assertEqual(rows[1]["result"], "PENDING")

    def test_private_writer_is_atomic_0600_and_rejects_hardlink(self) -> None:
        private_root = runner.PROJECT_ROOT / ".codex_private_runtime"
        with tempfile.TemporaryDirectory(dir=private_root) as directory:
            output = Path(directory) / "receipts.jsonl"
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(stat.S_IMODE(os.lstat(output).st_mode), 0o600)
            source = Path(directory) / "source"
            source.write_text("protected\n", encoding="utf-8")
            output.unlink()
            os.link(source, output)
            with mock.patch.object(runner, "OUTPUT_PATH", output):
                with self.assertRaisesRegex(runner.RunnerError, "unsafe"):
                    runner.write_private_receipts(output, [{"result": "PASS"}])
            self.assertEqual(source.read_text(encoding="utf-8"), "protected\n")

    def test_cli_rejects_arguments(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(["--unexpected"]), 2)

    def test_validation_subject_deletion_is_explicit_and_tamper_evident(self) -> None:
        builder = runner.builder
        ref = "KMFA/metadata/example/deleted.json"

        with mock.patch.object(builder, "_git_paths", return_value=()):
            with self.assertRaisesRegex(builder.BuildError, "missing without a bound deletion"):
                builder._validation_entry_at_ref(ref, None)

        with mock.patch.object(builder, "_git_paths", return_value=(ref,)) as git_paths:
            with mock.patch.object(
                builder,
                "_blob_at_ref",
                side_effect=builder.BuildError("base blob missing"),
            ):
                with self.assertRaisesRegex(builder.BuildError, "base blob missing"):
                    builder._validation_entry_at_ref(ref, None)
                self.assertIn("--no-renames", git_paths.call_args.args[0])

        with mock.patch.object(builder, "validation_subject_refs", return_value=(ref,)):
            with mock.patch.object(
                builder,
                "_validation_entry_at_ref",
                return_value=("PRESENT", b""),
            ):
                present_digest = builder.validation_subject_sha256(changed_refs=(ref,))
            with mock.patch.object(
                builder,
                "_validation_entry_at_ref",
                return_value=("DELETED", b""),
            ):
                deleted_digest = builder.validation_subject_sha256(changed_refs=(ref,))
        self.assertNotEqual(present_digest, deleted_digest)

    def test_validation_subject_deletion_matches_worktree_and_commit_ref(self) -> None:
        builder = runner.builder
        ref = "KMFA/metadata/example/deleted.json"
        missing = subprocess.CompletedProcess(["git", "show"], 1, b"", b"missing")
        with mock.patch.object(builder, "_git_paths", return_value=(ref,)):
            with mock.patch.object(builder, "_blob_at_ref", return_value=b"base"):
                worktree_state = builder._validation_entry_at_ref(ref, None)
                with mock.patch.object(builder.subprocess, "run", return_value=missing):
                    commit_state = builder._validation_entry_at_ref(ref, "a" * 40)
        self.assertEqual(worktree_state, ("DELETED", b""))
        self.assertEqual(commit_state, worktree_state)


if __name__ == "__main__":
    unittest.main()
