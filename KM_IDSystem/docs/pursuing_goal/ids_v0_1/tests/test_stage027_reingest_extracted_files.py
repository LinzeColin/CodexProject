import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE027_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE027_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE027_PHASE2_REINGEST_EXTRACTED_FILES_SLICE.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
SCRIPT = ROOT / "scripts" / "check_reingest_extracted_files.py"
EVALUATED_AT = "2026-07-03T08:08:27Z"


class Stage027ReingestExtractedFilesPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage027_reingest_extracted_files", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _write_zip(self, archive_path, entries):
        with zipfile.ZipFile(archive_path, "w") as archive:
            for entry_path, payload in entries.items():
                archive.writestr(entry_path, payload)

    def test_phase1_contracts_exist_and_bind_taskpack_identity(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")

        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        required_terms = [
            "STAGE-027",
            "IDS-V0_1-STAGE027-P1",
            "ACC-STAGE-027",
            "D05-S004",
            "解压文件重新入库",
            "IDS 系统运营入口",
            "D05 · 自动解压与压缩包安全",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-027_解压文件重新入库.md",
            "STAGE-025",
            "STAGE-026",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_reingest_boundary_fields_states_and_pipeline_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "reingest_job_id",
            "reingest_batch_id",
            "extracted_file_ref",
            "extracted_file_uri",
            "archive_manifest_ref",
            "original_archive_ref",
            "safe_extraction_ref",
            "reingest_source_state",
            "reingest_idempotency_key",
            "reingest_duplicate_policy",
            "reingest_owner_decision_state",
            "REINGEST_DRAFT",
            "REINGEST_BLOCKED",
            "REINGEST_OWNER_REVIEW_REQUIRED",
            "REINGEST_READY_FOR_HASH",
            "REINGEST_READY_FOR_MANIFEST",
            "REINGEST_READY_FOR_DEDUP",
            "REINGEST_READY_FOR_PARSER",
            "REINGEST_READY_FOR_IMPORT_QUEUE",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "STAGE-016",
            "STAGE-018",
            "STAGE-021",
            "STAGE-022",
            "STAGE-023",
            "STAGE-025",
            "STAGE-026",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_runtime_ingest_no_raw_data_and_original_archive_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行重新入库",
            "不读取真实 extracted file 内容",
            "不打开、hash 或复制真实 extracted file",
            "不写 reingest runtime output",
            "不创建 document/chunk/job/index/import row",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不覆盖、移动、删除、清理原始压缩包或事实源",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage027_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            "STAGE-026:",
            'status: "completed_local"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            "STAGE-027:",
            'status: "in_progress"',
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-027"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_reingest_extracted_files.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        allowed_status_terms = [
            'status: "stage027_phase1_in_progress"',
            'status: "stage027_phase2_in_progress"',
        ]
        allowed_next_phase_terms = [
            'next_phase: "Phase 2"',
            'next_phase: "Phase 3"',
        ]
        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P2"',
        ]
        allowed_acceptance_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_reingest_slice_complete"',
        ]
        allowed_gate_terms = [
            'next_gate: "IDS-STAGE027-P2-GATE"',
            'next_gate: "IDS-STAGE027-P3-GATE"',
        ]
        allowed_next_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P3"',
        ]
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)
        self.assertTrue(any(term in text for term in allowed_next_phase_terms), allowed_next_phase_terms)
        self.assertTrue(any(term in text for term in allowed_task_terms), allowed_task_terms)
        self.assertTrue(any(term in text for term in allowed_acceptance_terms), allowed_acceptance_terms)
        self.assertTrue(any(term in text for term in allowed_gate_terms), allowed_gate_terms)
        self.assertTrue(any(term in text for term in allowed_next_terms), allowed_next_terms)

    def test_roadmap_and_events_track_stage027_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'current_stage_id: "IDS-STAGE027"',
            'stage_id: "IDS-STAGE027"',
            'name: "STAGE-027 · 解压文件重新入库"',
            'phase_id: "IDS-STAGE027-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE1_SCOPE_BOUNDARY.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE027-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE027-P1"',
            '"ACC-STAGE-027"',
            "STAGE027_PHASE1_SCOPE_BOUNDARY.md",
        ]

        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE027-P1"',
            'current_phase_id: "IDS-STAGE027-P2"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P2"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE027-P2-GATE"',
            'next_gate_id: "IDS-STAGE027-P3-GATE"',
        ]
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase2_builds_reingest_plan_from_archive_manifest_without_import_writes(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-reingest.zip"
            staging = base / "staging"
            payload = b"stage027 structural reingest payload"
            self._write_zip(archive_path, {"safe/reingest-note.md": payload})
            expected_file_sha = hashlib.sha256(payload).hexdigest()

            report = module.build_reingest_extracted_files(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at=EVALUATED_AT,
            )

            extracted_file = staging / "safe" / "reingest-note.md"
            self.assertTrue(extracted_file.is_file())
            self.assertTrue(archive_path.is_file())

        self.assertEqual(report["schema_version"], "ids.stage027.reingest_extracted_files.v1")
        self.assertEqual(report["source_schema_version"], "ids.stage026.archive_manifest.v1")
        self.assertEqual(report["stage"], "STAGE-027")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE027-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-027")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["reingest_decision_state"], "REINGEST_READY_FOR_IMPORT_QUEUE")
        self.assertEqual(report["reingest_record_count"], 1)
        self.assertEqual(report["blocked_reingest_count"], 0)
        self.assertEqual(report["owner_review_count"], 0)
        self.assertEqual(report["reingest_required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertEqual(report["actual_jobs_started"], {"hash": 0, "manifest": 0, "dedup": 0, "parser": 0})
        record = report["reingest_records"][0]
        self.assertEqual(record["reingest_record_state"], "REINGEST_READY_FOR_IMPORT_QUEUE")
        self.assertEqual(record["extracted_file_sha256"], expected_file_sha)
        self.assertEqual(record["import_state"], "IMPORT_KEY_READY")
        self.assertEqual(record["reingest_duplicate_policy"], "REINGEST_DEDUP_BEFORE_PARSER")
        self.assertTrue(record["reingest_idempotency_key"].startswith("ids-reingest-sha256-"))
        self.assertTrue(record["import_idempotency_key"].startswith("ids-import-file-sha256-"))
        self.assertEqual(record["pipeline_stage_states"]["hash"], "REINGEST_HASH_OBSERVED")
        self.assertEqual(record["pipeline_stage_states"]["manifest"], "REINGEST_MANIFEST_READY")
        self.assertEqual(record["pipeline_stage_states"]["dedup"], "REINGEST_DEDUP_READY")
        self.assertEqual(record["pipeline_stage_states"]["parser"], "REINGEST_PARSER_READY_FOR_HANDOFF")
        for value in report["no_persistence_deltas"].values():
            self.assertEqual(value, 0)
        self.assertTrue(report["does_not_write_reingest_runtime_output"])
        self.assertTrue(report["does_not_create_import_queue"])
        self.assertTrue(report["does_not_create_documents_chunks_jobs"])
        self.assertTrue(report["does_not_write_database"])
        self.assertTrue(report["does_not_write_index"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_start_processing_jobs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_phase2_routes_duplicate_extracted_files_to_owner_review_without_persistence(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-duplicate-reingest.zip"
            staging = base / "staging"
            payload = b"same extracted bytes"
            self._write_zip(
                archive_path,
                {
                    "safe/duplicate-a.md": payload,
                    "safe/duplicate-b.md": payload,
                },
            )

            report = module.build_reingest_extracted_files(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at=EVALUATED_AT,
            )

        self.assertEqual(report["reingest_decision_state"], "REINGEST_OWNER_REVIEW_REQUIRED")
        self.assertEqual(report["reingest_record_count"], 2)
        self.assertEqual(report["duplicate_content_count"], 1)
        self.assertEqual(report["owner_review_count"], 2)
        self.assertEqual({item["import_state"] for item in report["reingest_records"]}, {"IMPORT_DUPLICATE_CONTENT"})
        self.assertEqual({item["reingest_record_state"] for item in report["reingest_records"]}, {"REINGEST_OWNER_REVIEW_REQUIRED"})
        for value in report["no_persistence_deltas"].values():
            self.assertEqual(value, 0)

    def test_phase2_blocks_missing_raw_and_no_safe_entry_cases_without_raw_access(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            staging = base / "staging"
            missing = base / "missing.zip"

            missing_report = module.build_reingest_extracted_files(
                archive_uri=missing.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at=EVALUATED_AT,
            )
            raw_report = module.build_reingest_extracted_files(
                archive_uri="file:///Users/linzezhang/Downloads/IDS_MetaData/raw-owner.zip",
                staging_area_uri=(base / "raw-staging").as_uri(),
                evaluated_at=EVALUATED_AT,
            )

        self.assertEqual(missing_report["reingest_decision_state"], "REINGEST_BLOCKED")
        self.assertEqual(missing_report["blocked_reingest_count"], 1)
        self.assertIn("REINGEST_SOURCE_MISSING", {item["risk_code"] for item in missing_report["reingest_risk_items"]})
        self.assertEqual(raw_report["reingest_decision_state"], "REINGEST_BLOCKED")
        self.assertEqual(raw_report["reingest_record_count"], 0)
        self.assertTrue(raw_report["does_not_read_raw_metadata"])
        self.assertIn(
            "REINGEST_SOURCE_BLOCKED_RAW_METADATA_ROOT",
            {item["risk_code"] for item in raw_report["reingest_risk_items"]},
        )

    def test_phase2_cli_json_contract_is_reingest_only(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "cli-reingest.zip"
            staging = base / "staging"
            self._write_zip(archive_path, {"safe/cli-note.md": b"cli structural payload"})
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--archive-uri",
                    archive_path.as_uri(),
                    "--staging-area-uri",
                    staging.as_uri(),
                    "--evaluated-at",
                    EVALUATED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "ids.stage027.reingest_extracted_files.v1")
        self.assertEqual(report["stage"], "STAGE-027")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE027-P2")
        self.assertEqual(report["reingest_decision_state"], "REINGEST_READY_FOR_IMPORT_QUEUE")
        self.assertTrue(report["does_not_write_reingest_runtime_output"])

    def test_phase2_evidence_document_records_implemented_slice_and_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")
        required_terms = [
            "STAGE-027",
            "IDS-V0_1-STAGE027-P2",
            "ACC-STAGE-027",
            "KM_IDSystem/scripts/check_reingest_extracted_files.py",
            "build_reingest_extracted_files",
            "ids.stage027.reingest_extracted_files.v1",
            "REINGEST_READY_FOR_IMPORT_QUEUE",
            "REINGEST_OWNER_REVIEW_REQUIRED",
            "REINGEST_BLOCKED",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "import_idempotency_key",
            "reingest_idempotency_key",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_current_stage027_phase2_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")
        required_terms = [
            'status: "stage027_phase2_in_progress"',
            "STAGE-027:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            'next_phase: "Phase 3"',
            'current_task_id: "IDS-V0_1-STAGE027-P2"',
            'acceptance_id: "ACC-STAGE-027"',
            'acceptance_status: "phase2_reingest_slice_complete"',
            'next_gate: "IDS-STAGE027-P3-GATE"',
            'push_allowed: false',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P3"',
            "KM_IDSystem/scripts/check_reingest_extracted_files.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE2_REINGEST_EXTRACTED_FILES_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_reingest_extracted_files.py",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage027_phase2_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE027"',
            'current_phase_id: "IDS-STAGE027-P2"',
            'current_task_id: "IDS-V0_1-STAGE027-P2"',
            'next_gate_id: "IDS-STAGE027-P3-GATE"',
            'phase_id: "IDS-STAGE027-P2"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE2_REINGEST_EXTRACTED_FILES_SLICE.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE027-P2-20260703-001"',
            '"event_type":"implementation"',
            '"task_id":"IDS-V0_1-STAGE027-P2"',
            '"ACC-STAGE-027"',
            "STAGE027_PHASE2_REINGEST_EXTRACTED_FILES_SLICE.md",
        ]
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
