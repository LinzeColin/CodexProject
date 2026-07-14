from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/raw_archive_manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("raw_archive_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S03P3RawManifestTests(unittest.TestCase):
    def test_generate_manifest_maps_source_file_hash_and_imported_at(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            raw_file = database / "data/public_raw/codex/session-001.jsonl"
            raw_file.parent.mkdir(parents=True)
            raw_file.write_text('{"role":"user","text":"ordinary transcript"}\n', encoding="utf-8")

            result = module.generate_raw_manifest(
                database_dir=database,
                run_id="unit_s03p3",
                imported_at="2026-07-08T00:00:00Z",
            )

            manifest_path = database / result["manifest_path"]
            ledger_path = database / result["hash_ledger_path"]
            manifest_rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
            ledger_rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["raw_file_count"], 1)
        self.assertEqual(len(manifest_rows), 1)
        self.assertEqual(manifest_rows, ledger_rows)
        self.assertEqual(manifest_rows[0]["source_id"], "codex")
        self.assertEqual(manifest_rows[0]["relative_path"], "codex/session-001.jsonl")
        self.assertRegex(manifest_rows[0]["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest_rows[0]["imported_at"], "2026-07-08T00:00:00Z")

    def test_append_only_audit_fails_on_hash_drift_or_delete(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            raw_file = database / "data/public_raw/chatgpt/export-001.jsonl"
            raw_file.parent.mkdir(parents=True)
            raw_file.write_text('{"role":"user","text":"original transcript"}\n', encoding="utf-8")
            module.generate_raw_manifest(
                database_dir=database,
                run_id="unit_s03p3",
                imported_at="2026-07-08T00:00:00Z",
            )

            clean_audit = module.audit_raw_append_only(database_dir=database)
            raw_file.write_text('{"role":"user","text":"changed transcript"}\n', encoding="utf-8")
            changed_audit = module.audit_raw_append_only(database_dir=database)
            raw_file.unlink()
            deleted_audit = module.audit_raw_append_only(database_dir=database)

        self.assertEqual(clean_audit["status"], "PASS", clean_audit)
        self.assertEqual(changed_audit["status"], "FAIL", changed_audit)
        self.assertEqual(changed_audit["hash_drift_count"], 1, changed_audit)
        self.assertEqual(deleted_audit["status"], "FAIL", deleted_audit)
        self.assertEqual(deleted_audit["deleted_manifest_entry_count"], 1, deleted_audit)

    def test_public_raw_readme_is_not_locked_as_transcript_raw(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            readme = database / "data/public_raw/README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text("# Public raw\n", encoding="utf-8")

            result = module.generate_raw_manifest(
                database_dir=database,
                run_id="unit_s03p3",
                imported_at="2026-07-08T00:00:00Z",
            )
            manifest_path = database / result["manifest_path"]
            rows = manifest_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["raw_file_count"], 0)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
