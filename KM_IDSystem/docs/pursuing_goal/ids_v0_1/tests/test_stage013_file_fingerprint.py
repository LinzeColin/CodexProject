import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_file_fingerprint.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE013_ENTRY_CONTRACT.md"
FIRST_SEEN_AT = "2026-07-02T13:05:50Z"


class Stage013FileFingerprintTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage013_file_fingerprint", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_file_uri_generates_fingerprint_metadata_record(self):
        module = self._load_module()
        expected_bytes = REAL_SOURCE.read_bytes()

        report = module.evaluate_file_fingerprints(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["schema_version"], "ids.stage013.file_fingerprint.v1")
        self.assertEqual(report["stage"], "STAGE-013")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-013")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["overall_state"], "FINGERPRINT_READY")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 1)
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["duplicate_input_count"], 0)
        record = report["records"][0]
        self.assertEqual(record["state"], "FINGERPRINT_READY")
        self.assertEqual(record["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(record["source_path"], str(REAL_SOURCE.resolve()))
        self.assertEqual(record["sha256"], hashlib.sha256(expected_bytes).hexdigest())
        self.assertEqual(record["size"], len(expected_bytes))
        self.assertEqual(record["file_size"], record["size"])
        self.assertEqual(record["extension"], ".md")
        self.assertEqual(record["mime"], "text/markdown")
        self.assertEqual(record["first_seen_at"], FIRST_SEEN_AT)
        self.assertIn("mtime", record)
        self.assertNotIn("raw_payload", record)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("# IDS v0.1 STAGE-013 Entry Contract", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_manifests",
            "does_not_write_database",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)

    def test_repeated_fingerprint_is_idempotent_and_keeps_one_manifest_record(self):
        module = self._load_module()

        report = module.evaluate_file_fingerprints(
            source_uris=[REAL_SOURCE.as_uri(), REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["overall_state"], "FINGERPRINT_READY")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 1)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["records"][0]["state"], "FINGERPRINT_READY")

    def test_missing_file_records_explicit_failure_without_silent_skip(self):
        module = self._load_module()
        missing = REAL_SOURCE.with_name("STAGE013_MISSING_SOURCE.md")

        report = module.evaluate_file_fingerprints(
            source_uris=[missing.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["overall_state"], "FINGERPRINT_PATH_BLOCKED")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 0)
        self.assertEqual(report["error_count"], 1)
        record = report["records"][0]
        self.assertEqual(record["state"], "FINGERPRINT_PATH_BLOCKED")
        self.assertEqual(record["source_uri"], missing.as_uri())
        self.assertIn("source path is absent", record["reason"])
        self.assertNotIn("sha256", record)
        self.assertTrue(report["does_not_write_database"])

    def test_ids_metadata_path_is_blocked_before_hash_or_content_read(self):
        module = self._load_module()
        blocked_uri = "file:///Users/linzezhang/Downloads/IDS_MetaData/blocked-by-contract.txt"

        report = module.evaluate_file_fingerprints(
            source_uris=[blocked_uri],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["overall_state"], "FINGERPRINT_PATH_BLOCKED")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 0)
        self.assertEqual(report["error_count"], 1)
        record = report["records"][0]
        self.assertEqual(record["state"], "FINGERPRINT_PATH_BLOCKED")
        self.assertIn("IDS_MetaData raw metadata content", record["reason"])
        self.assertNotIn("sha256", record)
        self.assertNotIn("size", record)
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_cli_json_contract_is_stage013_metadata_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-uri",
                REAL_SOURCE.as_uri(),
                "--first-seen-at",
                FIRST_SEEN_AT,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-013")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "FINGERPRINT_READY")
        self.assertEqual(report["records"][0]["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(report["records"][0]["extension"], ".md")
        self.assertEqual(report["records"][0]["mime"], "text/markdown")
        self.assertTrue(report["does_not_write_manifests"])


if __name__ == "__main__":
    unittest.main()
