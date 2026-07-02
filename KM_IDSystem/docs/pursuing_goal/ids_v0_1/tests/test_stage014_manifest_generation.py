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
SCRIPT = ROOT / "scripts" / "check_manifest_generation.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE014_ENTRY_CONTRACT.md"
REAL_ALT_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE014_PHASE2_MANIFEST_SLICE.md"
FIRST_SEEN_AT = "2026-07-02T13:44:21Z"
MANIFEST_GENERATED_AT = "2026-07-02T13:44:22Z"


class Stage014ManifestGenerationTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage014_manifest_generation", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_explicit_file_uri_generates_metadata_only_manifest_candidate(self):
        module = self._load_module()
        expected_bytes = REAL_SOURCE.read_bytes()
        expected_sha = hashlib.sha256(expected_bytes).hexdigest()

        report = module.evaluate_manifest_candidates(
            source_uris=[REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            manifest_generated_at=MANIFEST_GENERATED_AT,
        )

        self.assertEqual(report["schema_version"], "ids.stage014.manifest_generation.v1")
        self.assertEqual(report["stage"], "STAGE-014")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-014")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["overall_state"], "MANIFEST_READY")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["duplicate_input_count"], 0)
        candidate = report["manifest_candidates"][0]
        self.assertEqual(candidate["manifest_state"], "MANIFEST_READY")
        self.assertEqual(candidate["source_uri"], REAL_SOURCE.as_uri())
        self.assertEqual(candidate["source_path"], str(REAL_SOURCE.resolve()))
        self.assertEqual(candidate["sha256"], expected_sha)
        self.assertEqual(candidate["file_size"], len(expected_bytes))
        self.assertEqual(candidate["first_seen_at"], FIRST_SEEN_AT)
        self.assertEqual(candidate["manifest_generated_at"], MANIFEST_GENERATED_AT)
        self.assertEqual(candidate["manifest_id"], f"ids-manifest-sha256-{expected_sha}")
        self.assertIn("mtime", candidate)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("# IDS v0.1 STAGE-014 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_manifest_files",
            "does_not_write_database",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)

    def test_repeated_manifest_generation_is_idempotent_without_persistence_pollution(self):
        module = self._load_module()

        report = module.evaluate_manifest_candidates(
            source_uris=[REAL_SOURCE.as_uri(), REAL_SOURCE.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            manifest_generated_at=MANIFEST_GENERATED_AT,
        )

        self.assertEqual(report["overall_state"], "MANIFEST_READY")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["document_delta"], 0)
        self.assertEqual(report["chunk_delta"], 0)
        self.assertEqual(report["job_delta"], 0)
        self.assertEqual(report["manifest_write_delta"], 0)

    def test_missing_file_records_explicit_manifest_failure_without_silent_skip(self):
        module = self._load_module()
        missing = REAL_SOURCE.with_name("STAGE014_MISSING_SOURCE.md")

        report = module.evaluate_manifest_candidates(
            source_uris=[missing.as_uri()],
            first_seen_at=FIRST_SEEN_AT,
            manifest_generated_at=MANIFEST_GENERATED_AT,
        )

        self.assertEqual(report["overall_state"], "MANIFEST_SOURCE_BLOCKED")
        self.assertEqual(report["candidate_count"], 0)
        self.assertEqual(report["error_count"], 1)
        self.assertEqual(len(report["rejected_inputs"]), 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["manifest_state"], "MANIFEST_SOURCE_BLOCKED")
        self.assertEqual(rejected["source_uri"], missing.as_uri())
        self.assertIn("source path is absent", rejected["reason"])
        self.assertNotIn("sha256", rejected)
        self.assertTrue(report["does_not_write_database"])

    def test_ids_metadata_path_is_blocked_before_manifest_or_fingerprint_read(self):
        module = self._load_module()
        blocked_uri = "file:///Users/linzezhang/Downloads/IDS_MetaData/blocked-by-contract.txt"

        report = module.evaluate_manifest_candidates(
            source_uris=[blocked_uri],
            first_seen_at=FIRST_SEEN_AT,
            manifest_generated_at=MANIFEST_GENERATED_AT,
        )

        self.assertEqual(report["overall_state"], "MANIFEST_SOURCE_BLOCKED")
        self.assertEqual(report["candidate_count"], 0)
        self.assertEqual(report["error_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["manifest_state"], "MANIFEST_SOURCE_BLOCKED")
        self.assertIn("IDS_MetaData raw metadata content", rejected["reason"])
        self.assertNotIn("sha256", rejected)
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_cli_json_contract_is_stage014_metadata_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-uri",
                REAL_SOURCE.as_uri(),
                "--first-seen-at",
                FIRST_SEEN_AT,
                "--manifest-generated-at",
                MANIFEST_GENERATED_AT,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-014")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "MANIFEST_READY")
        self.assertEqual(report["manifest_candidates"][0]["source_uri"], REAL_SOURCE.as_uri())
        self.assertTrue(report["does_not_write_manifest_files"])
        self.assertEqual(report["manifest_write_delta"], 0)

    def test_phase3_scenario_report_covers_manifest_duplicates_conflicts_and_hash_stability(self):
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

            report = module.build_stage014_scenario_report(
                same_file_uri=REAL_SOURCE.as_uri(),
                same_name_left_uri=same_name_left.as_uri(),
                same_name_right_uri=same_name_right.as_uri(),
                same_hash_left_uri=same_hash_left.as_uri(),
                same_hash_right_uri=same_hash_right.as_uri(),
                first_seen_at=FIRST_SEEN_AT,
                manifest_generated_at=MANIFEST_GENERATED_AT,
            )

        after_sha = hashlib.sha256(REAL_SOURCE.read_bytes()).hexdigest()
        scenarios = {item["scenario_id"]: item for item in report["scenarios"]}
        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage014.manifest_scenarios.v1")
        self.assertEqual(report["stage"], "STAGE-014")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-014")
        self.assertTrue(report["overall_valid"], report)
        self.assertEqual(scenarios["same_file_same_hash"]["state"], "MANIFEST_READY")
        self.assertEqual(scenarios["same_file_same_hash"]["duplicate_input_count"], 1)
        self.assertEqual(scenarios["same_file_same_hash"]["candidate_count"], 1)
        self.assertEqual(scenarios["same_name_different_hash"]["state"], "MANIFEST_HASH_CONFLICT")
        self.assertEqual(scenarios["same_name_different_hash"]["conflict_count"], 1)
        self.assertEqual(scenarios["same_hash_different_path"]["state"], "MANIFEST_DUPLICATE_CONTENT")
        self.assertEqual(scenarios["same_hash_different_path"]["duplicate_content_count"], 1)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["document_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["chunk_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["job_delta"], 0)
        self.assertEqual(scenarios["duplicate_import_no_persistence"]["manifest_write_delta"], 0)
        self.assertEqual(scenarios["original_hash_stable"]["before_sha256"], before_sha)
        self.assertEqual(scenarios["original_hash_stable"]["after_sha256"], after_sha)
        self.assertEqual(scenarios["original_hash_stable"]["before_size"], before_size)
        self.assertEqual(scenarios["original_hash_stable"]["after_size"], before_size)
        self.assertTrue(scenarios["original_hash_stable"]["hash_unchanged"])
        self.assertTrue(scenarios["original_hash_stable"]["size_unchanged"])
        self.assertNotIn("# IDS v0.1 STAGE-014 Entry Contract", serialized)
        for flag in [
            "does_not_scan_recursively",
            "does_not_move_originals",
            "does_not_delete_originals",
            "does_not_overwrite_originals",
            "does_not_write_manifest_files",
            "does_not_write_database",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)


if __name__ == "__main__":
    unittest.main()
