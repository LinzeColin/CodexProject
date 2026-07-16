from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = DATABASE_DIR / "scripts"
CONFIG_PATH = DATABASE_DIR / "config/evaluation/memory_gold_benchmark_v1.json"
DATASET_PATH = DATABASE_DIR / "data/derived/evaluation/memory_gold/benchmark_v1.jsonl"
SCHEMA_PATH = DATABASE_DIR / "data/derived/evaluation/memory_gold/benchmark_v1.schema.json"
BUILDER_PATH = SCRIPTS_DIR / "build_memory_gold_benchmark.py"
VALIDATOR_PATH = SCRIPTS_DIR / "validate_memory_gold_benchmark.py"


def load_module(name: str, path: Path):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MemoryGoldBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module("build_memory_gold_benchmark", BUILDER_PATH)
        cls.validator = load_module("validate_memory_gold_benchmark", VALIDATOR_PATH)
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.cases, cls.loader_errors = cls.validator.load_jsonl(DATASET_PATH)

    def validate(self, cases):
        return self.validator.validate_cases(self.config, self.schema, cases)

    def test_tracked_dataset_is_the_exact_deterministic_160_case_build(self) -> None:
        first = self.builder.render_cases(self.builder.build_cases(self.config))
        second = self.builder.render_cases(self.builder.build_cases(self.config))

        self.assertEqual(first, second)
        self.assertEqual(first, DATASET_PATH.read_bytes())
        self.assertEqual(len(first.splitlines()), 160)

        check = subprocess.run(
            [sys.executable, str(BUILDER_PATH), "--check"],
            cwd=DATABASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(json.loads(check.stdout)["status"], "PASS")

    def test_independent_validator_accepts_exact_distribution_and_quality_gates(self) -> None:
        result = self.validator.validate_cases(
            self.config,
            self.schema,
            self.cases,
            self.loader_errors,
        )

        self.assertEqual(result["status"], "PASS", result["error_counts"])
        metrics = result["metrics"]
        self.assertEqual(metrics["case_count"], 160)
        self.assertEqual(metrics["category_count"], 8)
        self.assertEqual(set(metrics["category_distribution"].values()), {20})
        self.assertEqual(metrics["stale_or_retired_trap_count"], 62)
        self.assertEqual(metrics["abstention_count"], 28)
        self.assertEqual(metrics["hard_negative_complete_case_count"], 160)
        self.assertEqual(metrics["duplicate_case_id_count"], 0)
        self.assertEqual(metrics["duplicate_query_count"], 0)
        self.assertEqual(metrics["leak_error_count"], 0)
        self.assertEqual(metrics["gold_role_separation_error_count"], 0)

    def test_count_duplicate_and_seed_drift_fail_closed(self) -> None:
        missing = copy.deepcopy(self.cases[:-1])
        duplicated = copy.deepcopy(self.cases)
        duplicated.append(copy.deepcopy(duplicated[0]))
        wrong_seed = copy.deepcopy(self.cases)
        wrong_seed[0]["fixed_seed"] = "PAM1-GOLD-WRONG-SEED"

        checks = (
            (missing, "case_count_mismatch"),
            (duplicated, "duplicate_case_id"),
            (wrong_seed, "fixed_seed_mismatch"),
        )
        for cases, code in checks:
            with self.subTest(code=code):
                result = self.validate(cases)
                self.assertEqual(result["status"], "FAIL")
                self.assertIn(code, result["error_counts"])

    def test_query_leak_and_gold_self_approval_fail_closed(self) -> None:
        leaked = copy.deepcopy(self.cases)
        expected_id = leaked[0]["expected_ids"][0]
        expected_record = next(row for row in leaked[0]["state"] if row["id"] == expected_id)
        leaked[0]["query"]["noise"] = expected_record["statement"]
        self_approved = copy.deepcopy(self.cases)
        provenance = self_approved[0]["gold_provenance"]
        provenance["approval_role"] = provenance["author_role"]

        leak_result = self.validate(leaked)
        self_approval_result = self.validate(self_approved)
        self.assertEqual(leak_result["error_counts"]["query_answer_leak"], 1)
        self.assertEqual(self_approval_result["error_counts"]["gold_role_separation"], 1)

    def test_cli_failure_reports_aggregate_codes_without_payload_echo(self) -> None:
        mutated = copy.deepcopy(self.cases)
        expected_id = mutated[0]["expected_ids"][0]
        expected_record = next(row for row in mutated[0]["state"] if row["id"] == expected_id)
        marker = expected_record["statement"]
        mutated[0]["query"]["noise"] = marker
        encoded = "".join(
            json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for case in mutated
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mutated.jsonl"
            path.write_text(encoded, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR_PATH), "--dataset", str(path)],
                cwd=DATABASE_DIR,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertNotIn(marker, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["error_counts"]["query_answer_leak"], 1)


if __name__ == "__main__":
    unittest.main()
