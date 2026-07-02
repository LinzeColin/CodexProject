import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_import_preflight.py"
REAL_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE018_ENTRY_CONTRACT.md"
REAL_ALT_SOURCE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "STAGE018_PHASE1_SCOPE_BOUNDARY.md"
PRECHECKED_AT = "2026-07-02T19:59:21Z"


class Stage018ImportPreflightTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage018_import_preflight", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_metadata_only_directory_preflight_estimates_counts_risks_costs_and_priority(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "owner_docs"
            docs.mkdir()
            md_file = docs / "stage018-entry.md"
            txt_file = docs / "phase1-scope.txt"
            archive_file = docs / "candidate.zip"
            scan_file = docs / "scan-page.png"
            shutil.copy2(REAL_SOURCE, md_file)
            shutil.copy2(REAL_ALT_SOURCE, txt_file)
            archive_file.write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            scan_file.write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")

            expected_size = sum(path.stat().st_size for path in docs.iterdir())

            report = module.evaluate_import_preflight(
                source_uris=[docs.as_uri()],
                prechecked_at=PRECHECKED_AT,
            )

        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage018.import_preflight.v1")
        self.assertEqual(report["stage"], "STAGE-018")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-018")
        self.assertEqual(report["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(report["customer_visible"])
        self.assertEqual(report["overall_state"], "PREFLIGHT_REVIEW_REQUIRED")
        self.assertEqual(report["confirmation_status"], "PREFLIGHT_REVIEW_REQUIRED")
        self.assertEqual(report["source_root_count"], 1)
        self.assertEqual(report["file_count_estimate"], 4)
        self.assertEqual(report["total_size_bytes_estimate"], expected_size)
        self.assertEqual(report["format_counts"][".md"], 1)
        self.assertEqual(report["format_counts"][".txt"], 1)
        self.assertEqual(report["format_counts"][".zip"], 1)
        self.assertEqual(report["format_counts"][".png"], 1)
        self.assertEqual(report["archive_candidate_count"], 1)
        self.assertEqual(report["scanned_document_candidate_count"], 1)
        self.assertGreater(report["estimated_ocr_units"], 0)
        self.assertGreater(report["estimated_embedding_units"], 0)
        self.assertIn("PREFLIGHT_ARCHIVE_PRESENT", report["risk_items"])
        self.assertIn("PREFLIGHT_SCANNED_DOCUMENT_PRESENT", report["risk_items"])
        self.assertEqual(report["priority_hint"], "manual_review_first")
        self.assertEqual(report["cost_items"]["ocr_workload_class"], "low")
        self.assertEqual(report["cost_items"]["embedding_workload_class"], "low")
        self.assertNotIn("# IDS v0.1 STAGE-018 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        for flag in [
            "does_not_parse_body_text",
            "does_not_start_ocr",
            "does_not_create_embeddings",
            "does_not_build_index",
            "does_not_start_import",
            "does_not_write_manifest_files",
            "does_not_write_database",
            "does_not_create_documents_chunks_jobs",
            "does_not_read_raw_metadata",
            "does_not_call_external_apis",
        ]:
            self.assertTrue(report[flag], flag)

    def test_empty_directory_is_ready_with_zero_counts_and_owner_confirmation_required(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            report = module.evaluate_import_preflight(
                source_uris=[Path(tmp).as_uri()],
                prechecked_at=PRECHECKED_AT,
            )

        self.assertEqual(report["overall_state"], "PREFLIGHT_READY")
        self.assertEqual(report["confirmation_status"], "PREFLIGHT_READY")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["total_size_bytes_estimate"], 0)
        self.assertEqual(report["risk_items"], [])
        self.assertEqual(report["priority_hint"], "low_risk_first")
        self.assertTrue(report["confirmation_required"])

    def test_ids_metadata_path_is_blocked_before_directory_listing(self):
        module = self._load_module()
        blocked_uri = "file:///Users/linzezhang/Downloads/IDS_MetaData"

        report = module.evaluate_import_preflight(
            source_uris=[blocked_uri],
            prechecked_at=PRECHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "PREFLIGHT_SOURCE_BLOCKED")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["source_root_count"], 0)
        self.assertEqual(report["rejected_input_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["state"], "PREFLIGHT_SOURCE_BLOCKED")
        self.assertIn("IDS_MetaData raw metadata content", rejected["reason"])
        self.assertNotIn("file_count", rejected)
        self.assertTrue(report["does_not_read_raw_metadata"])

    def test_offline_drive_fails_closed_before_source_metadata_evaluation(self):
        module = self._load_module()

        report = module.evaluate_import_preflight(
            source_uris=[REAL_SOURCE.as_uri()],
            prechecked_at=PRECHECKED_AT,
            drive_state="offline",
        )

        self.assertEqual(report["overall_state"], "PREFLIGHT_DRIVE_OFFLINE")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["source_root_count"], 0)
        self.assertEqual(report["rejected_input_count"], 1)
        rejected = report["rejected_inputs"][0]
        self.assertEqual(rejected["state"], "PREFLIGHT_DRIVE_OFFLINE")
        self.assertNotIn("source_path", rejected)
        self.assertTrue(report["does_not_start_import"])

    def test_cli_json_contract_is_stage018_preflight_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shutil.copy2(REAL_SOURCE, base / "stage018-entry.md")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    base.as_uri(),
                    "--prechecked-at",
                    PRECHECKED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-018")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["overall_state"], "PREFLIGHT_READY")
        self.assertEqual(report["file_count_estimate"], 1)
        self.assertEqual(report["format_counts"][".md"], 1)
        self.assertTrue(report["does_not_parse_body_text"])
        self.assertTrue(report["does_not_write_database"])


if __name__ == "__main__":
    unittest.main()
