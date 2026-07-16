from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "agent_loop"))

import validate_taskpack  # noqa: E402


class TaskpackIdCompatibilityTest(unittest.TestCase):
    def test_existing_legacy_examples_stay_readable(self) -> None:
        examples = [
            "minimal_t1_taskpack.md",
            "minimal_t1_taskpack_zh.md",
            "minimal_t1_taskpack_escape_slash.md",
        ]
        for name in examples:
            with self.subTest(name=name):
                text = (
                    ROOT / "docs" / "governance" / "agent_loop" / "examples" / name
                ).read_text(encoding="utf-8")
                _metadata, errors = validate_taskpack.validate(text)
                self.assertEqual(errors, [])

    def test_namespaced_v2_pair_is_accepted(self) -> None:
        path = (
            ROOT
            / "docs"
            / "governance"
            / "agent_loop"
            / "examples"
            / "minimal_t1_taskpack.md"
        )
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            '"roadmap_task_id": "AGENT-LOOP-C2C3D1-T01"',
            '"roadmap_task_id": "TSK.CodexProject.REPO1.0002"',
        ).replace(
            '"acceptance_id": "AGENT-LOOP-C2C3D1-A01"',
            '"acceptance_id": "ACC.CodexProject.REPO1.0002"',
        )
        _metadata, errors = validate_taskpack.validate(text)
        self.assertEqual(errors, [])

    def test_namespaced_suffix_mismatch_fails(self) -> None:
        path = (
            ROOT
            / "docs"
            / "governance"
            / "agent_loop"
            / "examples"
            / "minimal_t1_taskpack.md"
        )
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            '"roadmap_task_id": "AGENT-LOOP-C2C3D1-T01"',
            '"roadmap_task_id": "TSK.CodexProject.REPO1.0002"',
        ).replace(
            '"acceptance_id": "AGENT-LOOP-C2C3D1-A01"',
            '"acceptance_id": "ACC.CodexProject.REPO1.0003"',
        )
        _metadata, errors = validate_taskpack.validate(text)
        self.assertTrue(any("same project/program/sequence suffix" in error for error in errors))

    def test_external_submitter_dry_run_never_calls_github(self) -> None:
        taskpack = (
            ROOT
            / "docs"
            / "governance"
            / "agent_loop"
            / "examples"
            / "minimal_t1_taskpack.md"
        )
        process = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "agent_loop" / "submit_taskpack.py"),
                "--taskpack",
                str(taskpack),
                "--head",
                "automation-c/legacy-example/idempotency-key",
                "--dry-run-local",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertIn("ISSUE_MUTATION=0", process.stdout)
        self.assertIn("DRY_RUN_LOCAL", process.stdout)


if __name__ == "__main__":
    unittest.main()
