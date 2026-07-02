import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_duplicate_files.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE015_ENTRY_CONTRACT.md"
REAL_ALT_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE015_PHASE1_SCOPE_BOUNDARY.md"
FIRST_SEEN_AT = "2026-07-02T14:20:00Z"
DUPLICATE_CHECKED_AT = "2026-07-02T14:20:01Z"


class Stage015DuplicateDetectionTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage015_duplicate_detection", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_file_uri_generates_metadata_only_duplicate_identity(self):
        module = self._load_module()
        expected_bytes = REAL_SOURCE.read_bytes()
        expected_sha = hashlib.sha256(expected_bytes).hexdigest()

        report = module.evaluate_duplicate_files(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            duplicate_checked_at=DUPLICATE_CHECKED_AT,
        )

        self.assertEqual(report["schema_version"], "ids.stage015.duplicate_detection.v1")
        self.assertEqual(report["stage"], "STAGE-015")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-015")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["overall_state"], "DUPLICATE_READY")
        self.assertEqual(report["identity_count"], 1)
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["duplicate_input_count"], 0)
        identity = report["duplicate_identities"][0]
        self.assertEqual(identity["duplicate_state"], "DUPLICATE_READY")
        self.assertEqual(identity["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(identity["source_path"], str(REAL_SOURCE.resolve()))
        self.assertEqual(identity["basename"], REAL_SOURCE.name)
        self.assertEqual(identity["sha256"], expected_sha)
        self.assertEqual(identity["file_size"], len(expected_bytes))
        self.assertEqual(identity["first_seen_at"], FIRST_SEEN_AT)
        self.assertEqual(identity["duplicate_checked_at"], DUPLICATE_CHECKED_AT)
        self.assertEqual(identity["content_identity_id"], f"ids-duplicate-sha256-{expected_sha}")
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("# IDS v0.1 STAGE-015 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_duplicate_ledger",
            "does_not_write_database",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)

    def test_repeated_import_is_idempotent_without_database_pollution(self):
        module = self._load_module()

        report = module.evaluate_duplicate_files(
            source_uris=[REAL_SOURCE.as_uri(), REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            duplicate_checked_at=DUPLICATE_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "DUPLICATE_BATCH_REPEAT")
        self.assertEqual(report["identity_count"], 1)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["repeated_batch_import_count"], 1)
        self.assertEqual(report["document_delta"], 0)
        self.assertEqual(report["chunk_delta"], 0)
        self.assertEqual(report["job_delta"], 0)
        self.assertEqual(report["duplicate_write_delta"], 0)

    def test_same_hash_different_path_preserves_provenance_without_delete_or_merge(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            left = base / "left" / "contract-copy-a.md"
            right = base / "right" / "contract-copy-b.md"
            left.parent.mkdir(parents=True, exist_ok=True)
            right.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REAL_SOURCE, left)
            shutil.copy2(REAL_SOURCE, right)

            report = module.evaluate_duplicate_files(
                source_uris=[left.as_uri(), right.as_uri()],
                first_seen_at=FIRST_SEEN_AT,
                duplicate_checked_at=DUPLICATE_CHECKED_AT,
            )

        self.assertEqual(report["overall_state"], "DUPLICATE_SAME_HASH_DIFFERENT_PATH")
        self.assertEqual(report["identity_count"], 2)
        self.assertEqual(report["same_hash_different_path_count"], 1)
        self.assertEqual(report["same_name_different_hash_count"], 0)
        self.assertTrue(report["does_not_delete_originals"])
        self.assertTrue(report["does_not_move_originals"])
        self.assertTrue(report["does_not_overwrite_originals"])

    def test_same_name_different_hash_is_version_conflict_candidate(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            left = base / "left" / "source.md"
            right = base / "right" / "source.md"
            left.parent.mkdir(parents=True, exist_ok=True)
            right.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REAL_SOURCE, left)
            shutil.copy2(REAL_ALT_SOURCE, right)

            report = module.evaluate_duplicate_files(
                source_uris=[left.as_uri(), right.as_uri()],
                first_seen_at=FIRST_SEEN_AT,
                duplicate_checked_at=DUPLICATE_CHECKED_AT,
            )

        self.assertEqual(report["overall_state"], "DUPLICATE_SAME_NAME_DIFFERENT_HASH")
        self.assertEqual(report["identity_count"], 2)
        self.assertEqual(report["same_name_different_hash_count"], 1)
        self.assertEqual(report["version_conflict_count"], 1)
        self.assertEqual(report["same_hash_different_path_count"], 0)
        states = {identity["duplicate_state"] for identity in report["duplicate_identities"]}
        self.assertEqual(states, {"DUPLICATE_SAME_NAME_DIFFERENT_HASH"})

    def test_missing_file_records_explicit_duplicate_failure_without_silent_skip(self):
        module = self._load_module()
        missing = REAL_SOURCE.with_name("STAGE015_MISSING_SOURCE.md")

        report = module.evaluate_duplicate_files(
            source_uris=[missing.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            duplicate_checked_at=DUPLICATE_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "DUPLICATE_SOURCE_BLOCKED")
        self.assertEqual(report["identity_count"], 0)
        self.assertEqual(report["error_count"], 1)
        self.assertEqual(len(report["rejected_inputs"]), 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["duplicate_state"], "DUPLICATE_SOURCE_BLOCKED")
        self.assertEqual(rejected["source_uri"], missing.as_uri())
        self.assertIn("source path is absent", rejected["reason"])
        self.assertNotIn("sha256", rejected)
        self.assertTrue(report["does_not_write_database"])

    def test_ids_metadata_path_is_blocked_before_duplicate_read(self):
        module = self._load_module()
        blocked_uri = "file:///Users/linzezhang/Downloads/IDS_MetaData/blocked-by-contract.txt"

        report = module.evaluate_duplicate_files(
            source_uris=[blocked_uri],
            first_seen_at=FIRST_SEEN_AT,
            duplicate_checked_at=DUPLICATE_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "DUPLICATE_SOURCE_BLOCKED")
        self.assertEqual(report["identity_count"], 0)
        self.assertEqual(report["error_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["duplicate_state"], "DUPLICATE_SOURCE_BLOCKED")
        self.assertIn("IDS_MetaData raw metadata content", rejected["reason"])
        self.assertNotIn("sha256", rejected)
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_cli_json_contract_is_stage015_metadata_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-uri",
                REAL_SOURCE.as_uri(),
                "--first-seen-at",
                FIRST_SEEN_AT,
                "--duplicate-checked-at",
                DUPLICATE_CHECKED_AT,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-015")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "DUPLICATE_READY")
        self.assertEqual(report["duplicate_identities"][0]["source_uri"], REAL_SOURCE.as_uri())
        self.assertTrue(report["does_not_write_duplicate_ledger"])
        self.assertEqual(report["duplicate_write_delta"], 0)


if __name__ == "__main__":
    unittest.main()
