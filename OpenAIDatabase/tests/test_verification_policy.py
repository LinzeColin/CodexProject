from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
RUNNER = DATABASE_DIR / "scripts/run_verification.py"
POLICY = DATABASE_DIR / "config/quality/verification_policy.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_verification", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VerificationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_repository_has_zero_verification_policy_drift(self) -> None:
        result = self.runner.validate_policy(DATABASE_DIR, POLICY)

        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["metrics"]["test_file_count"], 71)
        for metric in (
            "unowned_test_count",
            "multi_owned_test_count",
            "duplicate_test_group_count",
            "conditional_skip_count",
            "known_flaky_count",
            "unit_live_side_effect_count",
            "duplicate_npm_command_count",
            "compatibility_alias_drift_count",
            "unowned_frontend_script_count",
            "missing_frontend_script_count",
            "lock_dependency_drift_count",
            "duplicate_config_group_count",
            "nested_workflow_count",
            "missing_ci_tier_count",
            "missing_ci_command_count",
            "forbidden_ci_fragment_count",
            "reproducible_build_missing_count",
            "ci_step_order_drift_count",
            "duplicate_ci_audit_count",
            "aggregate_audit_delegation_drift_count",
            "unpinned_ci_action_count",
        ):
            self.assertEqual(result["metrics"][metric], 0, metric)
        self.assertEqual(result["metrics"]["aggregate_audit_count"], 1)

    def test_full_tier_aggregates_each_owned_test_once(self) -> None:
        tiers = self.policy["execution_tiers"]
        executable = tiers["full"]["includes"]
        files = [name for tier in executable for name in tiers[tier]["test_files"]]

        self.assertEqual(executable, ["fast", "unit", "security", "integration"])
        self.assertEqual(len(files), len(set(files)))
        self.assertEqual(len(files), 71)


if __name__ == "__main__":
    unittest.main()
