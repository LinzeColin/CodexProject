from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "OpenAIDatabase"
ATLASCTL = DATABASE_DIR / "scripts/atlasctl.py"
VALIDATOR = DATABASE_DIR / "scripts/validate_command_ownership.py"
CONTRACT = DATABASE_DIR / "config/command_ownership.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_command_ownership", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CommandOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.validator = load_validator()

    def run_atlasctl(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ATLASCTL), *args],
            cwd=DATABASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_contract_and_repository_have_zero_command_drift(self) -> None:
        result = self.validator.validate(self.contract, DATABASE_DIR, ROOT)
        self.assertEqual(result["status"], "PASS", result["errors"])
        for metric in (
            "duplicate_canonical_owner_count",
            "missing_implementation_count",
            "write_command_missing_mode_count",
            "active_write_invocation_missing_mode_count",
            "ci_missing_canonical_invocation_count",
            "ci_direct_legacy_invocation_count",
            "dead_script_remaining_count",
            "deleted_active_reference_count",
        ):
            self.assertEqual(result["metrics"][metric], 0, metric)

    def test_commands_subcommand_returns_machine_readable_matrix(self) -> None:
        result = self.run_atlasctl("commands")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["writes_files"])
        self.assertEqual(payload["task_id"], "TSK.OpenAIDatabase.CLEAN1.0006")
        self.assertEqual(len(payload["canonical_commands"]), 36)
        memory_rows = [
            row
            for row in payload["canonical_commands"]
            if row["capability"] in {
                "memory-unified-read",
                "memory-generated-views",
                "memory-canonical-apply",
                "memory-governed-mutation",
                "raw-evidence-import",
                "agent-transport-compatibility",
                "memory-retrieval-performance",
                "memory-fault-reliability",
                "memory-automation-c-e2e",
                "memory-snapshot-recovery",
                "memory-production-acceptance",
            }
        ]
        self.assertEqual(len(memory_rows), 11)
        self.assertEqual(
            {row["implementation"] for row in memory_rows},
            {
                "scripts/memory.py",
                "scripts/validate_agent_transport_compatibility.py",
                "scripts/evaluate_memory_retrieval_performance.py",
                "scripts/evaluate_memory_fault_reliability.py",
                "scripts/evaluate_memory_automation_c_e2e.py",
                "scripts/evaluate_memory_snapshot_recovery.py",
                "scripts/evaluate_memory_production_acceptance.py",
            },
        )
        self.assertEqual(
            self.contract["memory_cli"]["snapshot_recovery"]["implementation"],
            "scripts/memory_snapshot.py",
        )
        self.assertEqual(
            self.contract["memory_cli"]["production_acceptance"]["implementation"],
            "scripts/evaluate_memory_production_acceptance.py",
        )

    def test_delegated_audits_have_no_write_dry_runs(self) -> None:
        expected = self.contract["delegated_audits"]
        for check, script in expected.items():
            result = self.run_atlasctl("audit", "--check", check, "--dry-run")
            self.assertEqual(result.returncode, 0, (check, result.stderr))
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertFalse(payload["writes_files"])
            self.assertTrue(payload["planned_command"][1].endswith(script), check)
        for check in ("acceptance", "goal-completion"):
            result = self.run_atlasctl(
                "audit",
                "--check",
                check,
                "--require-local-apps",
                "--dry-run",
            )
            self.assertEqual(result.returncode, 0, (check, result.stderr))
            self.assertIn("--require-local-apps", json.loads(result.stdout)["planned_command"])

    def test_write_command_without_mode_fails_closed(self) -> None:
        result = self.run_atlasctl("build-atlas")
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertFalse(payload["writes_files"])
        self.assertIn("--dry-run or --apply", payload["reason"])

    def test_every_write_command_help_exposes_both_modes(self) -> None:
        for row in self.contract["write_commands"]:
            result = self.run_atlasctl(row["subcommand"], "--help")
            self.assertEqual(result.returncode, 0, row["subcommand"])
            self.assertIn("--dry-run", result.stdout)
            self.assertIn("--apply", result.stdout)

    def test_deprecated_alias_is_thin_and_has_removal_condition(self) -> None:
        alias = self.contract["deprecated_thin_aliases"][0]
        self.assertEqual(alias["business_logic_lines"], 0)
        self.assertTrue(alias["removal_condition"])
        help_result = self.run_atlasctl("--help")
        self.assertIn("DEPRECATED thin alias", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
