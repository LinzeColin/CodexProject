from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
ROOT = DATABASE_DIR.parent
EVALUATOR_PATH = DATABASE_DIR / "scripts/evaluate_memory_gold_benchmark.py"
CONFIG_PATH = DATABASE_DIR / "config/evaluation/memory_gold_evaluation_v1.json"
DATASET_PATH = DATABASE_DIR / "data/derived/evaluation/memory_gold/benchmark_v1.jsonl"
WORKFLOW_PATH = ROOT / ".github/workflows/openai-database-ci.yml"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("evaluate_memory_gold_benchmark", EVALUATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {EVALUATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryGoldEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = load_evaluator()
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.cases = cls.evaluator.load_jsonl(DATASET_PATH)

    def test_predictor_is_gold_label_isolated(self) -> None:
        case = self.cases[0]
        baseline = self.evaluator.predict(self.evaluator.build_prediction_input(case))
        mutated = copy.deepcopy(case)
        mutated["expected_ids"] = []
        mutated["forbidden_ids"] = ["fabricated"]
        mutated["should_abstain"] = True
        mutated["answer_traits"] = ["fabricated"]

        self.assertEqual(
            baseline,
            self.evaluator.predict(self.evaluator.build_prediction_input(mutated)),
        )
        self.assertEqual(set(self.evaluator.build_prediction_input(case)), {"state", "query", "as_of"})
        with self.assertRaises(self.evaluator.EvaluationError):
            self.evaluator.predict({**self.evaluator.build_prediction_input(case), "expected_ids": []})

    def test_fast_and_full_suites_pass_every_hard_gate(self) -> None:
        for suite, expected_count in (("fast", 16), ("full", 160)):
            report, runtime = self.evaluator.evaluate_suite(DATABASE_DIR, self.config, suite)
            self.assertEqual(report["status"], "PASS", report["hard_gate_failures"])
            self.assertEqual(report["case_count"], expected_count)
            self.assertEqual(report["algorithm"]["gold_label_dependency_count"], 0)
            self.assertIsNone(report["algorithm"]["llm_judge"])
            self.assertEqual(report["metrics"]["profile_pass_count"], 5)
            self.assertEqual(report["metrics"]["critical_stale_use_count"], 0)
            self.assertFalse(
                [name for name, row in runtime["gates"].items() if row["status"] != "PASS"]
            )

    def test_each_threshold_fixture_fails_closed(self) -> None:
        report, _ = self.evaluator.evaluate_suite(DATABASE_DIR, self.config, "fast")
        for gate_name, contract in self.config["hard_gates"].items():
            mutated = copy.deepcopy(report["metrics"])
            metric = contract["metric"]
            threshold = contract["threshold"]
            mutated[metric] = threshold - 1 if contract["operator"] in {"gte", "eq"} else threshold + 1
            assessed = self.evaluator.assess_gates(mutated, {gate_name: contract})
            self.assertEqual(assessed[gate_name]["status"], "FAIL", gate_name)

    def test_required_thresholds_and_suite_sizes_cannot_be_lowered(self) -> None:
        lowered = copy.deepcopy(self.config)
        lowered["hard_gates"]["recall_at_5"]["threshold"] = 0.1
        with self.assertRaisesRegex(self.evaluator.EvaluationError, "required_hard_gate_drift"):
            self.evaluator.validate_config(lowered)
        shortened = copy.deepcopy(self.config)
        shortened["suites"]["full"]["case_count"] = 16
        with self.assertRaisesRegex(self.evaluator.EvaluationError, "full_case_count_drift"):
            self.evaluator.validate_config(shortened)

    def test_reports_are_hash_reproducible_and_committed(self) -> None:
        for suite in ("fast", "full"):
            first, _ = self.evaluator.evaluate_suite(DATABASE_DIR, self.config, suite)
            second, _ = self.evaluator.evaluate_suite(DATABASE_DIR, self.config, suite)
            rendered = self.evaluator.render_report(first)
            self.assertEqual(rendered, self.evaluator.render_report(second))
            report_path = DATABASE_DIR / self.config["suites"][suite]["report"]
            self.assertEqual(rendered, report_path.read_bytes())

    def test_cli_check_is_a_hard_gate(self) -> None:
        for suite in ("fast", "full"):
            result = subprocess.run(
                [sys.executable, str(EVALUATOR_PATH), "--suite", suite, "--check"],
                cwd=DATABASE_DIR,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertFalse(payload["report_drift"])

    def test_required_ci_routes_fast_and_full_without_soft_failure(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        ci = self.config["ci"]
        self.assertIn("schedule:", workflow)
        self.assertIn(ci["fast_command"], workflow)
        self.assertIn(ci["full_command"], workflow)
        self.assertIn("if: github.event_name == 'pull_request'", workflow)
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertNotIn("continue-on-error: true", workflow)
        self.assertNotIn("|| true", workflow)
        self.assertFalse(ci["soft_failure_allowed"])


if __name__ == "__main__":
    unittest.main()
