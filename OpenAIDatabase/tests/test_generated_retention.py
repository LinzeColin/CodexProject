from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .memory_test_support import write_canonical_memory


ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "OpenAIDatabase"
VALIDATOR = DATABASE_DIR / "scripts/validate_generated_retention.py"
CONTRACT = DATABASE_DIR / "config/storage/generated_retention.json"
MEMORY_SCRIPT = (
    DATABASE_DIR
    / "skills/openai-memory-analysis/scripts/openai_memory_analysis.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class GeneratedRetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.validator = load_module(VALIDATOR, "validate_generated_retention")
        cls.memory = load_module(MEMORY_SCRIPT, "openai_memory_analysis_for_retention")

    def test_repository_has_zero_retention_drift(self) -> None:
        result = self.validator.validate(self.contract, DATABASE_DIR, ROOT)
        self.assertEqual(result["status"], "PASS", result["errors"])
        for metric in (
            "tracked_transient_count",
            "unclassified_target_count",
            "multiply_classified_target_count",
            "no_consumer_generated_count",
            "missing_generator_binding_count",
            "missing_consumer_binding_count",
            "missing_gitignore_marker_count",
            "safe_deletion_fingerprint_mismatch_count",
            "safe_deletion_remaining_count",
            "active_deleted_reference_count",
            "retained_drift_count",
        ):
            self.assertEqual(result["metrics"][metric], 0, metric)

    def test_local_outputs_are_ignored(self) -> None:
        for relative in (
            "OpenAIDatabase/data/processed/indexes/memory_index.sqlite",
            "OpenAIDatabase/data/processed/indexes/memory_index.sqlite-wal",
            "OpenAIDatabase/apps/memory-atlas/dist/index.html",
            "OpenAIDatabase/data/run_logs/example/stdout.txt",
        ):
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", relative],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(result.returncode, 0, relative)

    def test_search_rebuilds_missing_local_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database_dir = Path(tmp)
            active = database_dir / "data/memory/active/active_memory.jsonl"
            active.parent.mkdir(parents=True)
            active.write_text(
                json.dumps(
                    {
                        "id": "mem_retention_0001",
                        "statement": "portable retention contract",
                        "category": "governance",
                        "review_status": "active",
                        "importance": "high",
                        "validity": "durable",
                        "confidence": "high",
                        "sensitivity": "public",
                        "date": "2026-07-16",
                        "source": "synthetic regression fixture",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            write_canonical_memory(
                database_dir,
                [json.loads(line) for line in active.read_text(encoding="utf-8").splitlines()],
            )
            (database_dir / "data/memory/candidates").mkdir(parents=True)
            index = database_dir / "data/processed/indexes/memory_index.sqlite"
            self.assertFalse(index.exists())
            rows = self.memory.query_index(database_dir, "portable retention")
            self.assertTrue(index.exists())
            self.assertEqual(rows[0]["id"], "mem_retention_0001")


if __name__ == "__main__":
    unittest.main()
