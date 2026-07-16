from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/migrate_memory_records.py"
CONTRACT = DATABASE_DIR / "config/memory.cutover.json"
ACTIVE = DATABASE_DIR / "data/memory/active/active_memory.jsonl"
MANIFEST = DATABASE_DIR / "data/memory/records/manifest.json"
SHARD = DATABASE_DIR / "data/memory/records/records-0001.jsonl"


def load_module():
    spec = importlib.util.spec_from_file_location("migrate_memory_records", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryCanonicalCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_actual_cutover_is_complete_deterministic_and_legacy_writer_is_retired(self) -> None:
        before_active = hashlib.sha256(ACTIVE.read_bytes()).hexdigest()
        first = self.module.run(
            ["--database-dir", str(DATABASE_DIR), "--contract", "config/memory.cutover.json", "--dry-run"]
        )
        second = self.module.run(
            ["--database-dir", str(DATABASE_DIR), "--contract", "config/memory.cutover.json", "--dry-run"]
        )
        with self.assertRaisesRegex(self.module.CutoverError, "legacy canonical writer retired"):
            self.module.run(
                ["--database-dir", str(DATABASE_DIR), "--contract", "config/memory.cutover.json", "--write"]
            )

        self.assertEqual(first, second)
        self.assertFalse(first["writes_files"])
        self.assertTrue(self.module.LEGACY_CANONICAL_WRITE_RETIRED)
        self.assertEqual(first["unique_legacy_ids"], 278)
        self.assertEqual(first["canonical_record_count"], 198)
        self.assertEqual(first["audit_only_record_count"], 80)
        self.assertEqual(first["canonical_status_counts"], {"active": 6, "candidate": 108, "disputed": 0, "retired": 84})
        self.assertEqual(first["schema_valid_record_count"], 198)
        self.assertEqual(first["source_ref_coverage_count"], 198)
        self.assertEqual(first["legacy_row_hash_coverage_count"], 198)
        self.assertEqual(first["record_hash_coverage_count"], 198)
        self.assertEqual(first["credential_or_secret_count"], 0)
        self.assertEqual(first["dual_write_count"], 0)
        self.assertEqual(first["shard_count"], 1)
        self.assertLessEqual(first["max_shard_bytes"], 900 * 1024)
        self.assertEqual(hashlib.sha256(ACTIVE.read_bytes()).hexdigest(), before_active)

    def test_tracked_canonical_dataset_passes_schema_hash_and_reference_gates(self) -> None:
        records, manifest = self.module.load_canonical_records(DATABASE_DIR)
        self.assertEqual(len(records), 198)
        self.assertEqual(manifest["record_count"], 198)
        self.assertEqual(manifest["shard_count"], 1)
        self.assertEqual(manifest["dataset_bytes"], len(SHARD.read_bytes()))
        self.assertEqual(manifest["dataset_sha256"], "sha256:" + hashlib.sha256(SHARD.read_bytes()).hexdigest())
        self.assertEqual(
            "sha256:" + hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
            self.contract["canonical_output"]["manifest_sha256"],
        )
        for record in records:
            self.module.validate_record(record)
            self.assertTrue(record["source"]["ref"])
            self.assertTrue(
                any(ref.startswith("legacy-record-sha256:") for ref in record["verification"]["evidence_refs"])
            )
        self.module.validate_dataset(records)

    def test_credential_shape_fails_closed_without_echo(self) -> None:
        active_rows = {
            row["id"]: row
            for row in (json.loads(line) for line in ACTIVE.read_text(encoding="utf-8").splitlines())
        }
        map_entry = next(
            json.loads(line)
            for line in (DATABASE_DIR / "data/derived/migration/memory_migration_map.v1.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if json.loads(line)["migration"]["disposition"] == "migrate-candidate"
        )
        record = copy.deepcopy(active_rows[map_entry["legacy_id"]])
        secret_value = "sk-" + "A" * 24
        record["statement"] = secret_value
        with self.assertRaisesRegex(self.module.CutoverError, "credential-shaped") as raised:
            self.module.migrate_record(record, map_entry)
        self.assertNotIn(secret_value, str(raised.exception))

    def test_tampered_manifest_or_symlink_shard_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "data/memory/records").mkdir(parents=True)
            shutil.copy2(DATABASE_DIR / "config/memory.sharding.json", root / "config/memory.sharding.json")
            shutil.copy2(MANIFEST, root / "data/memory/records/manifest.json")
            shutil.copy2(SHARD, root / "data/memory/records/records-0001.jsonl")
            manifest_path = root / "data/memory/records/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["dataset_bytes"] += 1
            manifest_path.write_bytes(self.module.canonical_json_bytes(manifest) + b"\n")
            with self.assertRaises(self.module.CutoverError):
                self.module.load_canonical_records(root)

            shutil.copy2(MANIFEST, manifest_path)
            shard_path = root / "data/memory/records/records-0001.jsonl"
            shard_path.unlink()
            shard_path.symlink_to(SHARD)
            with self.assertRaises(self.module.CutoverError):
                self.module.load_canonical_records(root)

    def test_production_consumers_have_zero_legacy_memory_writes(self) -> None:
        analyzer = (DATABASE_DIR / "skills/openai-memory-analysis/scripts/openai_memory_analysis.py").read_text(
            encoding="utf-8"
        )
        atlas = (DATABASE_DIR / "scripts/build_memory_atlas_data.py").read_text(encoding="utf-8")
        forbidden = [
            'write_jsonl(state.database_dir / "data/memory/candidates"',
            'write_jsonl(state.database_dir / "data/memory/active/active_memory.jsonl"',
            'write_jsonl(state.database_dir / "data/memory/secret_refs"',
        ]
        self.assertTrue(all(fragment not in analyzer for fragment in forbidden))
        self.assertIn("load_canonical_records", analyzer)
        self.assertIn("load_canonical_records", atlas)
        self.assertNotIn("ACTIVE_MEMORY_SOURCE", atlas)

    def test_cli_requires_mode_and_failure_output_is_value_redacted(self) -> None:
        with self.assertRaises(SystemExit):
            self.module.parse_args(["--database-dir", str(DATABASE_DIR)])
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = self.module.main(
                ["--database-dir", str(DATABASE_DIR), "--contract", "../escape.json", "--dry-run"]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("FAIL_CLOSED", output.getvalue())


if __name__ == "__main__":
    unittest.main()
