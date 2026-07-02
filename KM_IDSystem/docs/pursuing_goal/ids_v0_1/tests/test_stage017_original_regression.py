import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_original_regression.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE017_ENTRY_CONTRACT.md"
FIRST_SEEN_AT = "2026-07-02T19:20:00Z"
SCAN_CHECKED_AT = "2026-07-02T19:20:01Z"


class Stage017OriginalRegressionTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage017_original_regression", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_file_uri_builds_metadata_only_regression_record(self):
        module = self._load_module()
        expected_bytes = REAL_SOURCE.read_bytes()
        expected_sha = hashlib.sha256(expected_bytes).hexdigest()

        report = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
        )

        self.assertEqual(report["schema_version"], "ids.stage017.original_regression.v1")
        self.assertEqual(report["stage"], "STAGE-017")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-017")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["overall_state"], "REGRESSION_READY")
        self.assertFalse(report["customer_visible"])
        self.assertEqual(report["regression_record_count"], 1)
        self.assertEqual(report["rejected_input_count"], 0)
        self.assertEqual(report["error_count"], 0)
        record = report["regression_records"][0]
        self.assertEqual(record["regression_state"], "REGRESSION_READY")
        self.assertEqual(record["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(record["source_path"], str(REAL_SOURCE.resolve()))
        self.assertEqual(record["basename"], REAL_SOURCE.name)
        self.assertEqual(record["sha256"], expected_sha)
        self.assertEqual(record["file_size"], len(expected_bytes))
        self.assertEqual(record["first_seen_at"], FIRST_SEEN_AT)
        self.assertEqual(record["scan_checked_at"], SCAN_CHECKED_AT)
        self.assertEqual(record["manifest_identity"], f"ids-manifest-sha256-{expected_sha}")
        self.assertEqual(record["import_idempotency_key"], f"ids-import-file-sha256-{expected_sha}")
        self.assertEqual(report["manifest_identity_count"], 1)
        self.assertEqual(report["import_record_count"], 1)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("# IDS v0.1 STAGE-017 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_manifest_files",
            "does_not_write_database",
            "does_not_write_index",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)

    def test_repeated_scan_blocks_duplicate_registration_with_zero_deltas(self):
        module = self._load_module()

        report = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri(), REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "REGRESSION_REPEAT_SCAN")
        self.assertEqual(report["regression_record_count"], 1)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["repeated_scan_count"], 1)
        self.assertEqual(report["duplicate_registration_blocked_count"], 1)
        for key in [
            "document_delta",
            "chunk_delta",
            "job_delta",
            "index_delta",
            "import_write_delta",
            "manifest_write_delta",
            "duplicate_write_delta",
            "evidence_write_delta",
            "audit_write_delta",
            "report_write_delta",
            "database_write_delta",
        ]:
            self.assertEqual(report[key], 0, key)

    def test_resume_with_matching_checkpoint_is_explicit_pending_state(self):
        module = self._load_module()
        initial = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
        )
        checkpoint = initial["checkpoint_candidates"][0]

        report = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
            resume_requested=True,
            resume_checkpoint=checkpoint,
            resume_token=checkpoint["resume_token"],
        )

        self.assertEqual(report["overall_state"], "REGRESSION_RESUME_PENDING")
        self.assertTrue(report["resume_valid"])
        self.assertTrue(report["checkpoint_comparison"]["matches"])
        self.assertEqual(report["checkpoint_error_count"], 0)
        self.assertEqual(report["hash_drift_count"], 0)
        self.assertEqual(report["document_delta"], 0)
        self.assertEqual(report["import_write_delta"], 0)

    def test_resume_without_checkpoint_fails_closed_before_scan(self):
        module = self._load_module()

        report = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
            resume_requested=True,
        )

        self.assertEqual(report["overall_state"], "REGRESSION_CHECKPOINT_MISSING")
        self.assertFalse(report["stage016_evaluated"])
        self.assertEqual(report["regression_record_count"], 0)
        self.assertEqual(report["checkpoint_error_count"], 1)
        self.assertEqual(report["rejected_inputs"][0]["regression_state"], "REGRESSION_CHECKPOINT_MISSING")

    def test_offline_drive_fails_closed_without_touching_source_identity(self):
        module = self._load_module()

        report = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
            drive_state="offline",
        )

        self.assertEqual(report["overall_state"], "REGRESSION_DRIVE_OFFLINE")
        self.assertFalse(report["stage016_evaluated"])
        self.assertEqual(report["regression_record_count"], 0)
        self.assertEqual(report["rejected_inputs"][0]["regression_state"], "REGRESSION_DRIVE_OFFLINE")
        self.assertNotIn("sha256", report["rejected_inputs"][0])
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_checkpoint_hash_drift_is_explicit_conflict_state(self):
        module = self._load_module()
        initial = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
        )
        checkpoint = dict(initial["checkpoint_candidates"][0])
        checkpoint["sha256"] = "0" * 64

        report = module.evaluate_original_material_regression(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
            resume_requested=True,
            resume_checkpoint=checkpoint,
            resume_token=checkpoint["resume_token"],
        )

        self.assertEqual(report["overall_state"], "REGRESSION_HASH_DRIFT")
        self.assertFalse(report["resume_valid"])
        self.assertFalse(report["checkpoint_comparison"]["matches"])
        self.assertEqual(report["hash_drift_count"], 1)
        self.assertEqual(report["document_delta"], 0)
        self.assertEqual(report["index_delta"], 0)

    def test_ids_metadata_path_is_blocked_before_regression_read(self):
        module = self._load_module()
        blocked_uri = "file:///Users/linzezhang/Downloads/IDS_MetaData/blocked-by-contract.txt"

        report = module.evaluate_original_material_regression(
            source_uris=[blocked_uri],
            first_seen_at=FIRST_SEEN_AT,
            scan_checked_at=SCAN_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "REGRESSION_SOURCE_BLOCKED")
        self.assertEqual(report["regression_record_count"], 0)
        self.assertEqual(report["error_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["regression_state"], "REGRESSION_SOURCE_BLOCKED")
        self.assertIn("IDS_MetaData raw metadata content", rejected["reason"])
        self.assertNotIn("sha256", rejected)
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_cli_json_contract_is_stage017_metadata_only(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-uri",
                REAL_SOURCE.as_uri(),
                "--first-seen-at",
                FIRST_SEEN_AT,
                "--scan-checked-at",
                SCAN_CHECKED_AT,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-017")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "REGRESSION_READY")
        self.assertEqual(report["regression_records"][0]["source_uri"], REAL_SOURCE.as_uri())
        self.assertTrue(report["does_not_write_database"])
        self.assertEqual(report["database_write_delta"], 0)


if __name__ == "__main__":
    unittest.main()
