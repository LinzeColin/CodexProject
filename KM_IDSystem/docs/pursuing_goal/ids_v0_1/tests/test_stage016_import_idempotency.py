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
SCRIPT = ROOT / "scripts" / "check_import_idempotency.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE016_ENTRY_CONTRACT.md"
REAL_ALT_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE016_PHASE1_SCOPE_BOUNDARY.md"
FIRST_SEEN_AT = "2026-07-02T15:05:00Z"
IMPORT_CHECKED_AT = "2026-07-02T15:05:01Z"


class Stage016ImportIdempotencyTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage016_import_idempotency", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_file_uri_generates_metadata_only_import_key(self):
        module = self._load_module()
        expected_bytes = REAL_SOURCE.read_bytes()
        expected_sha = hashlib.sha256(expected_bytes).hexdigest()

        report = module.evaluate_import_idempotency(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            import_checked_at=IMPORT_CHECKED_AT,
        )

        self.assertEqual(report["schema_version"], "ids.stage016.import_idempotency.v1")
        self.assertEqual(report["stage"], "STAGE-016")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-016")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["overall_state"], "IMPORT_KEY_READY")
        self.assertEqual(report["import_record_count"], 1)
        self.assertEqual(report["error_count"], 0)
        record = report["import_records"][0]
        self.assertEqual(record["import_state"], "IMPORT_KEY_READY")
        self.assertEqual(record["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(record["source_path"], str(REAL_SOURCE.resolve()))
        self.assertEqual(record["basename"], REAL_SOURCE.name)
        self.assertEqual(record["sha256"], expected_sha)
        self.assertEqual(record["file_size"], len(expected_bytes))
        self.assertEqual(record["first_seen_at"], FIRST_SEEN_AT)
        self.assertEqual(record["import_checked_at"], IMPORT_CHECKED_AT)
        self.assertEqual(record["import_idempotency_key"], f"ids-import-file-sha256-{expected_sha}")
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("# IDS v0.1 STAGE-016 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_import_records",
            "does_not_write_database",
            "does_not_write_index",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)

    def test_repeated_single_file_import_has_zero_persistence_deltas(self):
        module = self._load_module()

        report = module.evaluate_import_idempotency(
            source_uris=[REAL_SOURCE.as_uri(), REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            import_checked_at=IMPORT_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "IMPORT_SINGLE_REPEAT")
        self.assertEqual(report["import_record_count"], 1)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["repeated_import_count"], 1)
        self.assertEqual(report["document_delta"], 0)
        self.assertEqual(report["chunk_delta"], 0)
        self.assertEqual(report["job_delta"], 0)
        self.assertEqual(report["index_delta"], 0)
        self.assertEqual(report["import_write_delta"], 0)

    def test_same_hash_different_path_preserves_provenance_without_merge(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            left = base / "left" / "contract-copy-a.md"
            right = base / "right" / "contract-copy-b.md"
            left.parent.mkdir(parents=True, exist_ok=True)
            right.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REAL_SOURCE, left)
            shutil.copy2(REAL_SOURCE, right)

            report = module.evaluate_import_idempotency(
                source_uris=[left.as_uri(), right.as_uri()],
                first_seen_at=FIRST_SEEN_AT,
                import_checked_at=IMPORT_CHECKED_AT,
            )

        self.assertEqual(report["overall_state"], "IMPORT_DUPLICATE_CONTENT")
        self.assertEqual(report["import_record_count"], 2)
        self.assertEqual(report["duplicate_content_count"], 1)
        self.assertEqual(report["key_conflict_count"], 0)
        self.assertTrue(report["does_not_delete_originals"])
        self.assertTrue(report["does_not_move_originals"])
        self.assertTrue(report["does_not_overwrite_originals"])

    def test_same_name_different_hash_is_import_key_conflict_candidate(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            left = base / "left" / "source.md"
            right = base / "right" / "source.md"
            left.parent.mkdir(parents=True, exist_ok=True)
            right.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REAL_SOURCE, left)
            shutil.copy2(REAL_ALT_SOURCE, right)

            report = module.evaluate_import_idempotency(
                source_uris=[left.as_uri(), right.as_uri()],
                first_seen_at=FIRST_SEEN_AT,
                import_checked_at=IMPORT_CHECKED_AT,
            )

        self.assertEqual(report["overall_state"], "IMPORT_KEY_CONFLICT")
        self.assertEqual(report["import_record_count"], 2)
        self.assertEqual(report["key_conflict_count"], 1)
        self.assertEqual(report["version_conflict_count"], 1)
        states = {record["import_state"] for record in report["import_records"]}
        self.assertEqual(states, {"IMPORT_KEY_CONFLICT"})
        self.assertEqual(report["document_delta"], 0)
        self.assertEqual(report["index_delta"], 0)

    def test_missing_file_records_explicit_import_failure_without_silent_skip(self):
        module = self._load_module()
        missing = REAL_SOURCE.with_name("STAGE016_MISSING_SOURCE.md")

        report = module.evaluate_import_idempotency(
            source_uris=[missing.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            import_checked_at=IMPORT_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "IMPORT_SOURCE_BLOCKED")
        self.assertEqual(report["import_record_count"], 0)
        self.assertEqual(report["error_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["import_state"], "IMPORT_SOURCE_BLOCKED")
        self.assertEqual(rejected["source_uri"], missing.as_uri())
        self.assertIn("source path is absent", rejected["reason"])
        self.assertNotIn("import_idempotency_key", rejected)
        self.assertTrue(report["does_not_write_database"])

    def test_ids_metadata_path_is_blocked_before_import_read(self):
        module = self._load_module()
        blocked_uri = "file:///Users/linzezhang/Downloads/IDS_MetaData/blocked-by-contract.txt"

        report = module.evaluate_import_idempotency(
            source_uris=[blocked_uri],
            first_seen_at=FIRST_SEEN_AT,
            import_checked_at=IMPORT_CHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "IMPORT_SOURCE_BLOCKED")
        self.assertEqual(report["import_record_count"], 0)
        self.assertEqual(report["error_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["import_state"], "IMPORT_SOURCE_BLOCKED")
        self.assertIn("IDS_MetaData raw metadata content", rejected["reason"])
        self.assertNotIn("sha256", rejected)
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_cli_json_contract_is_stage016_metadata_only(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-uri",
                REAL_SOURCE.as_uri(),
                "--first-seen-at",
                FIRST_SEEN_AT,
                "--import-checked-at",
                IMPORT_CHECKED_AT,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-016")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "IMPORT_KEY_READY")
        self.assertEqual(report["import_records"][0]["source_uri"], REAL_SOURCE.as_uri())
        self.assertTrue(report["does_not_write_import_records"])
        self.assertEqual(report["import_write_delta"], 0)

    def test_phase3_scenario_report_covers_import_idempotency_and_original_stability(self):
        module = self._load_module()
        before_sha = hashlib.sha256(REAL_SOURCE.read_bytes()).hexdigest()
        before_size = REAL_SOURCE.stat().st_size
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            same_name_left = base / "same_name" / "left" / "source.md"
            same_name_right = base / "same_name" / "right" / "source.md"
            same_hash_left = base / "same_hash" / "left" / "copy-a.md"
            same_hash_right = base / "same_hash" / "right" / "copy-b.md"
            for path in [same_name_left, same_name_right, same_hash_left, same_hash_right]:
                path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REAL_SOURCE, same_name_left)
            shutil.copy2(REAL_ALT_SOURCE, same_name_right)
            shutil.copy2(REAL_SOURCE, same_hash_left)
            shutil.copy2(REAL_SOURCE, same_hash_right)

            report = module.build_stage016_scenario_report(
                same_file_uri=REAL_SOURCE.as_uri(),
                same_name_left_uri=same_name_left.as_uri(),
                same_name_right_uri=same_name_right.as_uri(),
                same_hash_left_uri=same_hash_left.as_uri(),
                same_hash_right_uri=same_hash_right.as_uri(),
                first_seen_at=FIRST_SEEN_AT,
                import_checked_at=IMPORT_CHECKED_AT,
            )

        after_sha = hashlib.sha256(REAL_SOURCE.read_bytes()).hexdigest()
        scenarios = {item["scenario_id"]: item for item in report["scenarios"]}
        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage016.import_scenarios.v1")
        self.assertEqual(report["stage"], "STAGE-016")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-016")
        self.assertTrue(report["overall_valid"], report)
        self.assertEqual(scenarios["same_file_same_hash"]["state"], "IMPORT_SINGLE_REPEAT")
        self.assertEqual(scenarios["same_file_same_hash"]["duplicate_input_count"], 1)
        self.assertEqual(scenarios["same_file_same_hash"]["import_record_count"], 1)
        self.assertEqual(scenarios["same_name_different_hash"]["state"], "IMPORT_KEY_CONFLICT")
        self.assertEqual(scenarios["same_name_different_hash"]["key_conflict_count"], 1)
        self.assertEqual(scenarios["same_name_different_hash"]["version_conflict_count"], 1)
        self.assertEqual(scenarios["same_hash_different_path"]["state"], "IMPORT_DUPLICATE_CONTENT")
        self.assertEqual(scenarios["same_hash_different_path"]["duplicate_content_count"], 1)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["document_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["chunk_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["job_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["index_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["import_write_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["manifest_write_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["duplicate_write_delta"], 0)
        self.assertEqual(scenarios["original_hash_stable"]["before_sha256"], before_sha)
        self.assertEqual(scenarios["original_hash_stable"]["after_sha256"], after_sha)
        self.assertEqual(scenarios["original_hash_stable"]["before_size"], before_size)
        self.assertEqual(scenarios["original_hash_stable"]["after_size"], before_size)
        self.assertTrue(scenarios["original_hash_stable"]["hash_unchanged"])
        self.assertTrue(scenarios["original_hash_stable"]["size_unchanged"])
        self.assertNotIn("# IDS v0.1 STAGE-016 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_import_records",
            "does_not_write_manifest_files",
            "does_not_write_database",
            "does_not_write_index",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)


if __name__ == "__main__":
    unittest.main()
