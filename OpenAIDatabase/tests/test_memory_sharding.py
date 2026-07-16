from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/plan_memory_shards.py"
CONTRACT = DATABASE_DIR / "config/memory.sharding.json"
CANONICAL_MANIFEST = DATABASE_DIR / "data/memory/records/manifest.json"
CANONICAL_SHARD = DATABASE_DIR / "data/memory/records/records-0001.jsonl"
MAX_SHARD_BYTES = 900 * 1024


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_memory_shards", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryShardingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()
        cls.contract = cls.planner.load_contract(CONTRACT)

    def record_with_line_bytes(self, record_id: str, target: int) -> dict[str, str]:
        base = {"id": record_id, "payload": ""}
        overhead = len(self.planner.canonical_record_line(base))
        self.assertGreaterEqual(target, overhead)
        record = {"id": record_id, "payload": "x" * (target - overhead)}
        self.assertEqual(len(self.planner.canonical_record_line(record)), target)
        return record

    def test_899_900_and_over_900_kib_record_boundaries(self) -> None:
        for kib in (899, 900):
            with self.subTest(kib=kib):
                record = self.record_with_line_bytes(f"mem_boundary_{kib}", kib * 1024)
                plan = self.planner.build_shard_plan([record], self.contract)
                self.assertEqual(plan.shards[0].byte_count, kib * 1024)
                self.assertLessEqual(plan.shards[0].byte_count, MAX_SHARD_BYTES)

        oversized = self.record_with_line_bytes("mem_boundary_over", MAX_SHARD_BYTES + 1)
        with self.assertRaisesRegex(self.planner.ShardingError, "single_record_exceeds"):
            self.planner.build_shard_plan([oversized], self.contract)

    def test_double_build_is_identical_and_rotation_is_order_independent(self) -> None:
        records = [
            self.record_with_line_bytes("mem_b", 500 * 1024),
            self.record_with_line_bytes("mem_a", 500 * 1024),
        ]
        first = self.planner.build_shard_plan(records, self.contract)
        second = self.planner.build_shard_plan(list(reversed(records)), self.contract)

        self.assertEqual(first.plan_sha256, second.plan_sha256)
        self.assertEqual(first.manifest_bytes, second.manifest_bytes)
        self.assertEqual([shard.payload for shard in first.shards], [shard.payload for shard in second.shards])
        self.assertEqual(first.manifest["shard_count"], 2)
        self.assertEqual(first.manifest["default_discovery_objects"], 1)
        self.assertEqual(first.manifest["full_dataset_content_gets"], 3)
        self.assertFalse(first.manifest["recursive_tree_scan_required"])

    def test_duplicate_truncated_and_duplicate_key_inputs_fail_closed(self) -> None:
        line = self.planner.canonical_record_line({"id": "mem_duplicate", "payload": "safe"})
        cases = {
            "duplicate_record": line + line,
            "truncated_json": b'{"id":"mem_truncated"\n',
            "missing_final_lf": b'{"id":"mem_no_lf"}',
            "duplicate_json_key": b'{"id":"mem_a","id":"mem_b"}\n',
        }
        for name, payload in cases.items():
            with self.subTest(case=name), self.assertRaises(self.planner.ShardingError):
                self.planner.parse_jsonl_bytes(payload)

    def test_reordered_or_corrupted_shard_set_cannot_rebuild(self) -> None:
        records = [
            self.record_with_line_bytes("mem_a", 500 * 1024),
            self.record_with_line_bytes("mem_b", 500 * 1024),
        ]
        plan = self.planner.build_shard_plan(records, self.contract)
        payloads = {shard.path: shard.payload for shard in plan.shards}
        verified = self.planner.verify_shard_set(plan.manifest, payloads, self.contract)
        self.assertEqual(verified["status"], "PASS")

        reordered = copy.deepcopy(plan.manifest)
        reordered["shards"].reverse()
        with self.assertRaises(self.planner.ShardingError):
            self.planner.verify_shard_set(reordered, payloads, self.contract)

        truncated = dict(payloads)
        truncated[plan.shards[0].path] = truncated[plan.shards[0].path][:-1]
        with self.assertRaises(self.planner.ShardingError):
            self.planner.verify_shard_set(plan.manifest, truncated, self.contract)

    def test_current_canonical_dataset_has_a_verified_one_shard_rebuild(self) -> None:
        before = CANONICAL_SHARD.read_bytes()
        records, source_manifest, _ = self.planner.load_manifest_records(
            DATABASE_DIR,
            Path("data/memory/records/manifest.json"),
            self.contract,
        )
        plan = self.planner.build_shard_plan(records, self.contract)
        result = self.planner.verify_shard_set(
            plan.manifest,
            {shard.path: shard.payload for shard in plan.shards},
            self.contract,
        )

        self.assertEqual(len(before), 488_877)
        self.assertEqual(hashlib.sha256(before).hexdigest(), "fa9edb7191c5751331f52f4103aa1a6709a7a1e22044d6d85e38ed7d771ca927")
        self.assertEqual(source_manifest, plan.manifest)
        self.assertEqual(result["record_count"], 198)
        self.assertEqual(result["shard_count"], 1)
        self.assertEqual([shard.byte_count for shard in plan.shards], [488_877])
        self.assertTrue(all(shard.byte_count <= MAX_SHARD_BYTES for shard in plan.shards))
        self.assertEqual(CANONICAL_SHARD.read_bytes(), before)

    def test_cli_is_read_only_byte_identical_and_requires_explicit_dry_run(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT),
            "--database-dir",
            str(DATABASE_DIR),
            "--manifest",
            "data/memory/records/manifest.json",
            "--dry-run",
        ]
        first = subprocess.run(command, text=True, capture_output=True, check=False)
        second = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["writes_files"])
        self.assertEqual(payload["canonical_data_writes"], 0)
        self.assertTrue(payload["repeat_build_identical"])

        missing_mode = subprocess.run(command[:-1], text=True, capture_output=True, check=False)
        self.assertEqual(missing_mode.returncode, 2)
        self.assertEqual(json.loads(missing_mode.stdout)["status"], "FAIL_CLOSED")

    def test_repository_path_boundary_rejects_absolute_traversal_and_symlink(self) -> None:
        with self.assertRaisesRegex(self.planner.ShardingError, "absolute_path_forbidden"):
            self.planner.resolve_repository_file(DATABASE_DIR, CANONICAL_SHARD)
        with self.assertRaisesRegex(self.planner.ShardingError, "path_traversal_forbidden"):
            self.planner.resolve_repository_file(DATABASE_DIR, Path("../AGENTS.md"))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            target = root / "target.jsonl"
            target.write_text('{"id":"mem_safe"}\n', encoding="utf-8")
            (root / "linked.jsonl").symlink_to(target)
            with self.assertRaisesRegex(self.planner.ShardingError, "symlink_input_forbidden"):
                self.planner.resolve_repository_file(root, Path("linked.jsonl"))


if __name__ == "__main__":
    unittest.main()
