from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "OpenAIDatabase"
SCRIPT = DATABASE_DIR / "scripts" / "validate_directory_lifecycle.py"
CONTRACT_PATH = DATABASE_DIR / "config" / "storage" / "directory_lifecycle.json"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_directory_lifecycle", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectoryLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_current_migration_passes_all_hard_metrics(self) -> None:
        result = self.module.validate_contract(
            self.contract,
            DATABASE_DIR,
            ROOT,
            self.contract["implementation_base_sha"],
        )
        self.assertEqual(result["status"], "PASS", result["errors"])
        metrics = result["metrics"]
        for metric in (
            "unowned_directory_count",
            "duplicate_owner_count",
            "duplicate_destination_count",
            "duplicate_destination_domain_count",
            "excessive_destination_depth_count",
            "missing_required_writer_literal_count",
            "forbidden_writer_literal_count",
            "moved_hash_mismatch_count",
            "moved_source_remaining_count",
            "dual_write_count",
            "retired_path_remaining_count",
            "retired_fingerprint_mismatch_count",
        ):
            self.assertEqual(metrics[metric], 0, metric)
        self.assertEqual(metrics["moved_file_count"], 7)
        self.assertEqual(metrics["moved_bytes"], 4337)
        self.assertLess(
            metrics["current_top_level_count_including_root"],
            metrics["base_top_level_count_including_root"],
        )

    def test_duplicate_destination_fails_closed(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["destinations"].append(
            {"domain": "invalid_duplicate", "path": "data/run_logs/token_usage"}
        )
        result = self.module.validate_contract(
            contract,
            DATABASE_DIR,
            ROOT,
            contract["implementation_base_sha"],
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["metrics"]["duplicate_destination_count"], 1)

    def test_writer_bindings_are_single_destination(self) -> None:
        exporter = (DATABASE_DIR / "scripts/export_codex_history_archives.py").read_text(encoding="utf-8")
        sync = (DATABASE_DIR / "scripts/sync_codex_memory_data.py").read_text(encoding="utf-8")
        self.assertIn("data/run_logs/token_usage", exporter)
        self.assertNotIn("token_usage/current-mac-latest", exporter)
        self.assertNotIn("token_usage/current-mac-latest", sync)


if __name__ == "__main__":
    unittest.main()
