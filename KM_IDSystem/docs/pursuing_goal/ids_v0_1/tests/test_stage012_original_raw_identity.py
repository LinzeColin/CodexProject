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
SCRIPT = ROOT / "scripts" / "check_original_raw_identity.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE012_ENTRY_CONTRACT.md"
REAL_ALT_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE012_PHASE1_SCOPE_BOUNDARY.md"
FIRST_SEEN_AT = "2026-07-02T12:25:00Z"


class Stage012OriginalRawIdentityTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage012_original_raw_identity", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_file_uri_generates_metadata_only_identity_record(self):
        module = self._load_module()
        expected_bytes = REAL_SOURCE.read_bytes()

        report = module.evaluate_original_raw_identity(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["schema_version"], "ids.stage012.original_raw_identity.v1")
        self.assertEqual(report["stage"], "STAGE-012")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-012")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["overall_state"], "ORIGINAL_RAW_READY")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 1)
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["duplicate_input_count"], 0)
        record = report["records"][0]
        self.assertEqual(record["state"], "ORIGINAL_RAW_READY")
        self.assertEqual(record["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(record["source_path"], str(REAL_SOURCE.resolve()))
        self.assertEqual(record["sha256"], hashlib.sha256(expected_bytes).hexdigest())
        self.assertEqual(record["file_size"], len(expected_bytes))
        self.assertEqual(record["first_seen_at"], FIRST_SEEN_AT)
        self.assertIn("mtime", record)
        self.assertNotIn("raw_payload", record)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("# IDS v0.1 STAGE-012 Entry Contract", serialized)
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

    def test_repeated_scan_is_idempotent_and_keeps_one_manifest_record(self):
        module = self._load_module()

        report = module.evaluate_original_raw_identity(
            source_uris=[REAL_SOURCE.as_uri(), REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["overall_state"], "ORIGINAL_RAW_READY")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 1)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["records"][0]["state"], "ORIGINAL_RAW_READY")

    def test_missing_file_records_explicit_failure_without_silent_skip(self):
        module = self._load_module()
        missing = REAL_SOURCE.with_name("STAGE012_MISSING_SOURCE.md")

        report = module.evaluate_original_raw_identity(
            source_uris=[missing.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
        )

        self.assertEqual(report["overall_state"], "ORIGINAL_RAW_PATH_BLOCKED")
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["manifest_record_count"], 0)
        self.assertEqual(report["error_count"], 1)
        record = report["records"][0]
        self.assertEqual(record["state"], "ORIGINAL_RAW_PATH_BLOCKED")
        self.assertEqual(record["source_uri"], missing.as_uri())
        self.assertIn("source path is absent", record["reason"])
        self.assertNotIn("sha256", record)
        self.assertTrue(report["does_not_write_database"])

    def test_cli_json_contract_is_stage012_metadata_only(self):
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

        self.assertEqual(report["stage"], "STAGE-012")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "ORIGINAL_RAW_READY")
        self.assertEqual(report["records"][0]["source_uri"], REAL_SOURCE.as_uri())
        self.assertTrue(report["does_not_write_manifests"])

    def test_phase3_scenario_report_covers_duplicates_conflicts_and_hash_stability(self):
        module = self._load_module()
        before_sha = hashlib.sha256(REAL_SOURCE.read_bytes()).hexdigest()
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

            report = module.build_stage012_scenario_report(
                same_file_uri=REAL_SOURCE.as_uri(),
                same_name_left_uri=same_name_left.as_uri(),
                same_name_right_uri=same_name_right.as_uri(),
                same_hash_left_uri=same_hash_left.as_uri(),
                same_hash_right_uri=same_hash_right.as_uri(),
                first_seen_at=FIRST_SEEN_AT,
            )

        after_sha = hashlib.sha256(REAL_SOURCE.read_bytes()).hexdigest()
        scenarios = {item["scenario_id"]: item for item in report["scenarios"]}

        self.assertEqual(report["schema_version"], "ids.stage012.original_raw_identity_scenarios.v1")
        self.assertEqual(report["stage"], "STAGE-012")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-012")
        self.assertTrue(report["overall_valid"], report)
        self.assertEqual(scenarios["same_file_same_hash"]["state"], "ORIGINAL_RAW_READY")
        self.assertEqual(scenarios["same_file_same_hash"]["duplicate_input_count"], 1)
        self.assertEqual(scenarios["same_file_same_hash"]["manifest_record_count"], 1)
        self.assertEqual(scenarios["same_name_different_hash"]["state"], "ORIGINAL_RAW_HASH_CONFLICT")
        self.assertEqual(scenarios["same_name_different_hash"]["conflict_count"], 1)
        self.assertEqual(scenarios["same_hash_different_path"]["state"], "ORIGINAL_RAW_DUPLICATE_CONTENT")
        self.assertEqual(scenarios["same_hash_different_path"]["duplicate_content_count"], 1)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["document_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["chunk_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["job_delta"], 0)
        self.assertEqual(scenarios["original_hash_stable"]["before_sha256"], before_sha)
        self.assertEqual(scenarios["original_hash_stable"]["after_sha256"], after_sha)
        self.assertTrue(scenarios["original_hash_stable"]["hash_unchanged"])
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


if __name__ == "__main__":
    unittest.main()
