from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/evaluate_memory_fault_reliability.py"
CONFIG = DATABASE_DIR / "config/evaluation/memory_fault_reliability_v1.json"
REPORT = DATABASE_DIR / "data/derived/evaluation/memory_gold/reports/fault_reliability_v1.json"


def load_evaluator():
    scripts = str(DATABASE_DIR / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("memory_fault_reliability_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemoryFaultReliabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = load_evaluator()
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_tracked_offline_fault_report_is_deterministic_and_passes_every_hard_gate(self) -> None:
        report, failures = self.evaluator.evaluate(DATABASE_DIR, self.config)
        tracked = json.loads(REPORT.read_text(encoding="utf-8"))

        self.assertEqual(failures, [])
        self.assertEqual(report, tracked)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["hard_gates"].values()))
        self.assertEqual(report["metrics"]["fault_case_count"], 37)
        self.assertEqual(report["metrics"]["passed_case_count"], 37)

    def test_corruption_transport_and_atomic_compensation_fail_closed(self) -> None:
        report, _ = self.evaluator.evaluate(DATABASE_DIR, self.config)
        cases = {row["scenario"]: row for row in report["cases"]}

        for scenario in (
            "truncated_jsonl",
            "duplicate_record_id",
            "wrong_record_hash",
            "missing_shard",
            "missing_lexical_index",
            "forbidden_403",
            "not_found_404",
            "rate_limit_429_exhaustion",
            "server_500_exhaustion",
            "timeout_exhaustion",
        ):
            self.assertEqual(cases[scenario]["status"], "PASS", scenario)
            self.assertEqual(cases[scenario]["observed"]["outcome"], "fail_closed", scenario)
        self.assertEqual(
            cases["atomic_precommit_rollback"]["observed"]["outcome"], "rolled_back"
        )
        self.assertTrue(
            cases["atomic_postcommit_convergence"]["observed"]["retry_idempotent"]
        )
        self.assertEqual(report["metrics"]["partial_canonical_write_count"], 0)
        self.assertLessEqual(report["metrics"]["max_request_count"], 3)

    def test_concurrency_settlement_and_janitor_have_zero_duplicate_write(self) -> None:
        report, _ = self.evaluator.evaluate(DATABASE_DIR, self.config)
        cases = {row["scenario"]: row["observed"] for row in report["cases"]}

        self.assertEqual(report["metrics"]["writer_counts"], [2, 5, 10])
        for count in (2, 5, 10):
            observed = cases[f"concurrent_writers_{count}"]
            self.assertEqual(observed["legal_write_count"], 1)
            self.assertEqual(observed["rejected_writer_count"], count - 1)
            self.assertEqual(observed["duplicate_record_count"], 0)
        self.assertEqual(cases["duplicate_workflow_run"]["action"], "NOOP")
        self.assertEqual(cases["settlement_double_run"]["actions"], ["MERGE_DELETE", "NOOP"])
        self.assertEqual(cases["settlement_double_run"]["duplicate_settlement_write_count"], 0)
        self.assertEqual(cases["janitor_active_transaction"]["action"], "WAIT")
        self.assertEqual(cases["janitor_trusted_orphan"]["action"], "DELETE_ORPHAN")
        self.assertLessEqual(report["metrics"]["max_convergence_minutes"], 15)
        self.assertEqual(report["metrics"]["live_network_request_count"], 0)
        self.assertEqual(report["metrics"]["github_write_count"], 0)


if __name__ == "__main__":
    unittest.main()
