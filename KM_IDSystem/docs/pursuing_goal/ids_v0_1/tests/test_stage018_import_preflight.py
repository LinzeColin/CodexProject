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

    def test_phase3_scenario_report_covers_empty_small_large_offline_archive_and_space(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            empty_dir = base / "empty"
            small_dir = base / "small"
            large_dir = base / "large"
            archive_dir = base / "archive"
            for path in [empty_dir, small_dir, large_dir, archive_dir]:
                path.mkdir()
            shutil.copy2(REAL_SOURCE, small_dir / "stage018-entry.md")
            shutil.copy2(REAL_ALT_SOURCE, small_dir / "stage018-scope.md")
            for index in range(101):
                shutil.copy2(REAL_SOURCE, large_dir / f"stage018-entry-{index:03}.md")
            shutil.copy2(REAL_SOURCE, archive_dir / "stage018-entry.md")
            (archive_dir / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")

            scenario_report = module.build_stage018_scenario_report(
                scenario_sources={
                    "empty_directory": {"source_uris": [empty_dir.as_uri()]},
                    "small_directory": {"source_uris": [small_dir.as_uri()]},
                    "large_directory": {"source_uris": [large_dir.as_uri()]},
                    "offline_drive": {"source_uris": [small_dir.as_uri()], "drive_state": "offline"},
                    "archive_present": {"source_uris": [archive_dir.as_uri()]},
                    "insufficient_space": {"source_uris": [small_dir.as_uri()], "available_space_bytes": 1},
                },
                prechecked_at=PRECHECKED_AT,
                batch_size=50,
            )

        self.assertEqual(scenario_report["schema_version"], "ids.stage018.import_preflight.scenario_validation.v1")
        self.assertEqual(scenario_report["stage"], "STAGE-018")
        self.assertEqual(scenario_report["phase"], "Phase 3")
        self.assertEqual(scenario_report["acceptance_id"], "ACC-STAGE-018")
        self.assertEqual(scenario_report["validation_state"], "SCENARIO_VALIDATION_PASSED")
        self.assertTrue(scenario_report["required_scenarios_covered"])
        self.assertEqual(scenario_report["scenario_count"], 6)

        scenarios = scenario_report["scenario_results"]
        self.assertEqual(scenarios["empty_directory"]["preflight"]["overall_state"], "PREFLIGHT_READY")
        self.assertEqual(scenarios["small_directory"]["preflight"]["overall_state"], "PREFLIGHT_READY")
        self.assertEqual(scenarios["large_directory"]["preflight"]["overall_state"], "PREFLIGHT_REVIEW_REQUIRED")
        self.assertIn("PREFLIGHT_LARGE_BATCH", scenarios["large_directory"]["preflight"]["risk_items"])
        self.assertGreater(scenarios["large_directory"]["operator_decision_plan"]["batch_plan"]["batch_count"], 1)
        self.assertEqual(scenarios["offline_drive"]["preflight"]["overall_state"], "PREFLIGHT_DRIVE_OFFLINE")
        self.assertEqual(scenarios["archive_present"]["preflight"]["overall_state"], "PREFLIGHT_REVIEW_REQUIRED")
        self.assertIn("PREFLIGHT_ARCHIVE_PRESENT", scenarios["archive_present"]["preflight"]["risk_items"])
        self.assertEqual(scenarios["insufficient_space"]["preflight"]["overall_state"], "PREFLIGHT_REVIEW_REQUIRED")
        self.assertIn("PREFLIGHT_INSUFFICIENT_SPACE", scenarios["insufficient_space"]["preflight"]["risk_items"])

        for key in [
            "actual_parse_jobs_started",
            "actual_ocr_jobs_started",
            "actual_embedding_jobs_started",
            "actual_index_jobs_started",
            "actual_import_jobs_started",
        ]:
            self.assertEqual(scenario_report["processing_guard"][key], 0)

    def test_phase3_operator_decision_plan_supports_save_cancel_split_and_skip_without_persistence(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "operator"
            docs.mkdir()
            shutil.copy2(REAL_SOURCE, docs / "stage018-entry.md")
            shutil.copy2(REAL_ALT_SOURCE, docs / "stage018-scope.md")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")

            preflight = module.evaluate_import_preflight(
                source_uris=[docs.as_uri()],
                prechecked_at=PRECHECKED_AT,
            )
            decision = module.build_operator_decision_plan(preflight, batch_size=2)

        self.assertEqual(decision["schema_version"], "ids.stage018.import_preflight.operator_decision.v1")
        self.assertEqual(decision["stage"], "STAGE-018")
        self.assertEqual(decision["phase"], "Phase 3")
        self.assertEqual(decision["save_contract"]["state"], "PREFLIGHT_RESULT_SERIALIZABLE")
        self.assertTrue(decision["save_contract"]["can_save_result"])
        self.assertFalse(decision["save_contract"]["persisted_by_helper"])
        self.assertEqual(decision["cancel_contract"]["state"], "PREFLIGHT_CANCEL_READY")
        self.assertEqual(decision["cancel_contract"]["document_delta"], 0)
        self.assertTrue(decision["batch_plan"]["can_split"])
        self.assertEqual(decision["batch_plan"]["batch_size"], 2)
        self.assertEqual(decision["batch_plan"]["batch_count"], 2)
        self.assertEqual(decision["skip_high_risk_plan"]["high_risk_file_count"], 1)
        self.assertEqual(decision["skip_high_risk_plan"]["kept_file_count"], 2)
        self.assertIn("save_for_owner_review", decision["supported_owner_actions"])
        self.assertIn("cancel_without_side_effects", decision["supported_owner_actions"])
        self.assertIn("split_into_batches", decision["supported_owner_actions"])
        self.assertIn("skip_high_risk_files", decision["supported_owner_actions"])
        for key in [
            "document_delta",
            "chunk_delta",
            "job_delta",
            "index_delta",
            "import_write_delta",
            "manifest_write_delta",
            "database_write_delta",
        ]:
            self.assertEqual(decision["no_persistence_deltas"][key], 0)

    def test_phase3_scenario_report_serializes_without_body_content_or_processing(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "serialize"
            docs.mkdir()
            shutil.copy2(REAL_SOURCE, docs / "stage018-entry.md")

            scenario_report = module.build_stage018_scenario_report(
                scenario_sources={"small_directory": {"source_uris": [docs.as_uri()]}},
                prechecked_at=PRECHECKED_AT,
            )

        serialized = json.dumps(scenario_report, ensure_ascii=False)

        self.assertNotIn("# IDS v0.1 STAGE-018 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        self.assertTrue(scenario_report["does_not_parse_body_text"])
        self.assertTrue(scenario_report["does_not_start_ocr"])
        self.assertTrue(scenario_report["does_not_create_embeddings"])
        self.assertTrue(scenario_report["does_not_build_index"])
        self.assertTrue(scenario_report["does_not_start_import"])
        self.assertTrue(scenario_report["does_not_write_database"])

    def test_phase4_owner_feedback_summary_contains_report_sample_risks_uncertainty_and_rollback(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "feedback"
            docs.mkdir()
            shutil.copy2(REAL_SOURCE, docs / "stage018-entry.md")
            shutil.copy2(REAL_ALT_SOURCE, docs / "stage018-scope.md")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")

            preflight = module.evaluate_import_preflight(
                source_uris=[docs.as_uri()],
                prechecked_at=PRECHECKED_AT,
                available_space_bytes=1,
            )
            decision = module.build_operator_decision_plan(preflight, batch_size=2)
            feedback = module.build_owner_feedback_summary(
                preflight,
                decision,
                feedback_at=PRECHECKED_AT,
            )

        self.assertEqual(feedback["schema_version"], "ids.stage018.import_preflight.owner_feedback.v1")
        self.assertEqual(feedback["stage"], "STAGE-018")
        self.assertEqual(feedback["phase"], "Phase 4")
        self.assertEqual(feedback["acceptance_id"], "ACC-STAGE-018")
        self.assertTrue(feedback["customer_visible"])
        self.assertEqual(feedback["report_sample"]["overall_state"], "PREFLIGHT_REVIEW_REQUIRED")
        self.assertEqual(feedback["report_sample"]["file_count_estimate"], 3)
        self.assertIn("PREFLIGHT_ARCHIVE_PRESENT", feedback["risk_checklist"])
        self.assertIn("PREFLIGHT_INSUFFICIENT_SPACE", feedback["risk_checklist"])
        self.assertTrue(feedback["confirmation_flow_log"])
        flow_text = "\n".join(feedback["confirmation_flow_log"])
        self.assertIn("保存预检结果", flow_text)
        self.assertIn("取消", flow_text)
        self.assertIn("分批", flow_text)
        self.assertIn("跳过高风险文件", flow_text)
        self.assertGreaterEqual(len(feedback["uncertainty_notes"]), 3)
        self.assertIn("PREFLIGHT_DRIVE_OFFLINE", feedback["failure_explanations"])
        self.assertIn("PREFLIGHT_SOURCE_BLOCKED", feedback["failure_explanations"])
        self.assertIn("PREFLIGHT_INSUFFICIENT_SPACE", feedback["failure_explanations"])
        self.assertTrue(any("回滚" in step for step in feedback["rollback_steps"]))
        self.assertFalse(feedback["sample_persistence"]["persisted_by_helper"])
        self.assertEqual(feedback["no_persistence_deltas"]["database_write_delta"], 0)

    def test_phase4_owner_feedback_serializes_without_raw_body_or_runtime_writes(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "owner"
            docs.mkdir()
            shutil.copy2(REAL_SOURCE, docs / "stage018-entry.md")

            preflight = module.evaluate_import_preflight(
                source_uris=[docs.as_uri()],
                prechecked_at=PRECHECKED_AT,
            )
            decision = module.build_operator_decision_plan(preflight, batch_size=50)
            feedback = module.build_owner_feedback_summary(
                preflight,
                decision,
                feedback_at=PRECHECKED_AT,
            )

        serialized = json.dumps(feedback, ensure_ascii=False)

        self.assertNotIn("# IDS v0.1 STAGE-018 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        self.assertTrue(feedback["does_not_parse_body_text"])
        self.assertTrue(feedback["does_not_start_ocr"])
        self.assertTrue(feedback["does_not_create_embeddings"])
        self.assertTrue(feedback["does_not_build_index"])
        self.assertTrue(feedback["does_not_start_import"])
        self.assertTrue(feedback["does_not_write_database"])


if __name__ == "__main__":
    unittest.main()
