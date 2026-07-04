from pathlib import Path
import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
SCRIPT = ROOT / "scripts" / "check_archive_cleanup_allowlist.py"
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE029_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE029_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE029_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE029_PHASE4_CLOSEOUT.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage029ArchiveCleanupAllowlistPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage029_archive_cleanup_allowlist", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def _write_zip_fixture(self, base: Path, entries: dict[str, bytes]) -> Path:
        archive_path = base / "stage029-real-governance-payload.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            for entry_name, payload in entries.items():
                archive.writestr(entry_name, payload)
        return archive_path

    def _tracked_payload(self) -> bytes:
        return PHASE1.read_bytes()

    def _phase3_scenario_archives(self, base: Path) -> dict[str, dict[str, object]]:
        payload = self._tracked_payload()

        def scenario(name: str, entries: dict[str, bytes], **limits: object) -> dict[str, object]:
            scenario_dir = base / name
            scenario_dir.mkdir(parents=True, exist_ok=True)
            archive_path = self._write_zip_fixture(scenario_dir, entries)
            return {
                "archive_uri": archive_path.as_uri(),
                "staging_area_uri": (scenario_dir / "staging").as_uri(),
                **limits,
            }

        return {
            "path_traversal": scenario(
                "path-traversal",
                {
                    "safe/path-traversal.md": payload,
                    "../escape.md": payload,
                },
            ),
            "absolute_path": scenario(
                "absolute-path",
                {
                    "safe/absolute.md": payload,
                    "/absolute.md": payload,
                },
            ),
            "archive_bomb": scenario(
                "archive-bomb",
                {"safe/bomb.md": payload},
                archive_total_size_limit_bytes=1,
                archive_single_file_size_limit_bytes=1,
            ),
            "nested_archive": scenario(
                "nested-archive",
                {
                    "safe/nested.md": payload,
                    "nested/inner.zip": payload,
                },
                archive_nested_depth_limit=0,
            ),
            "garbled_filename": scenario(
                "garbled-filename",
                {
                    "safe/garbled.md": payload,
                    "bad/\ufffd-name.md": payload,
                },
            ),
            "too_many_files": scenario(
                "too-many-files",
                {
                    "safe/one.md": payload,
                    "safe/two.md": payload,
                    "safe/three.md": payload,
                },
                archive_file_count_limit=2,
            ),
        }

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
            "STAGE-029",
            "IDS-V0_1-STAGE029-P1",
            "ACC-STAGE-029",
            "D05-S006",
            "压缩包清理白名单",
            "IDS 系统运营入口",
            "D05 · 自动解压与压缩包安全",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-029_压缩包清理白名单.md",
            "b17be7330d9a4ce1f5a9ead4c0620d733693ccd10d6eeff7c8a1298c11889ac2",
            "STAGE-024",
            "STAGE-025",
            "STAGE-026",
            "STAGE-027",
            "STAGE-028",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_cleanup_allowlist_boundary_staging_limits_manifest_and_reingest_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "archive_cleanup_allowlist_id",
            "archive_security_boundary_id",
            "cleanup_request_ref",
            "archive_source_uri",
            "original_archive_ref",
            "archive_staging_area_uri",
            "archive_manifest_ref",
            "safe_extraction_ref",
            "post_extract_reingest_ref",
            "cleanup_candidate_uri",
            "cleanup_candidate_class",
            "cleanup_allowlist_ref",
            "cleanup_decision_state",
            "cleanup_reason_code",
            "cleanup_protected_ref",
            "archive_file_count_limit",
            "archive_total_size_limit_bytes",
            "archive_single_file_size_limit_bytes",
            "archive_nested_depth_limit",
            "ARCHIVE_CLEANUP_ALLOWLIST_DRAFT",
            "ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF",
            "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP",
            "ARCHIVE_STAGING_TEMP_FILE",
            "PROTECTED_ORIGINAL_ARCHIVE",
            "PROTECTED_ARCHIVE_MANIFEST",
            "PROTECTED_EVIDENCE_LEDGER",
            "PROTECTED_AUDIT_LOG",
            "PROTECTED_DELIVERED_REPORT",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_cleanup_no_delete_no_runtime_and_raw_data_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行 cleanup runner",
            "不自动清理",
            "不删除原始资料",
            "不删除原始压缩包",
            "不删除 manifest",
            "不删除 evidence",
            "不删除 audit",
            "不删除报告",
            "不覆盖原始压缩包",
            "不写出指定 staging 区",
            "不读取真实压缩包内容",
            "不写 archive_cleanup runtime output",
            "不写 archive_manifest runtime output",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage029_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            "STAGE-028:",
            "STAGE-029:",
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-029"',
            'push_allowed:',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_archive_cleanup_allowlist.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        allowed_status_terms = [
            'status: "stage029_phase1_in_progress"',
            'status: "stage029_phase2_in_progress"',
            'status: "stage029_phase3_in_progress"',
            'status: "stage029_completed_local_pending_stage030"',
            'status: "stage030_phase1_in_progress"',
            'status: "stage030_phase2_in_progress"',
            'status: "stage030_phase3_in_progress"',
            'status: "stage030_completed_local_pending_batch_review"',
            'status: "reviewed_ready_for_upload_no_github_upload"',
            'status: "completed_local"',
        ]
        allowed_next_phase_terms = [
            'next_phase: "Phase 2"',
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_stage: "STAGE-030"',
        ]
        allowed_current_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
        ]
        allowed_acceptance_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase2_size_guard_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase2_cleanup_allowlist_slice_complete"',
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        allowed_gate_terms = [
            'next_gate: "IDS-STAGE029-P2-GATE"',
            'next_gate: "IDS-STAGE029-P3-GATE"',
            'next_gate: "IDS-STAGE029-P4-GATE"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'next_gate: "IDS-STAGE030-P4-GATE"',
            'next_gate: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
        ]
        allowed_next_task_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)
        self.assertTrue(any(term in text for term in allowed_next_phase_terms), allowed_next_phase_terms)
        self.assertTrue(any(term in text for term in allowed_current_task_terms), allowed_current_task_terms)
        self.assertTrue(any(term in text for term in allowed_acceptance_terms), allowed_acceptance_terms)
        self.assertTrue(any(term in text for term in allowed_gate_terms), allowed_gate_terms)
        self.assertTrue(any(term in text for term in allowed_next_task_terms), allowed_next_task_terms)

    def test_roadmap_and_events_track_stage029_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'stage_id: "IDS-STAGE029"',
            'name: "STAGE-029 · 压缩包清理白名单"',
            'phase_id: "IDS-STAGE029-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE029"',
            'current_stage_id: "IDS-STAGE030"',
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
            'current_stage_id: "IDS-STAGE034"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE029-P1"',
            'current_phase_id: "IDS-STAGE029-P2"',
            'current_phase_id: "IDS-STAGE029-P3"',
            'current_phase_id: "IDS-STAGE029-P4"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_phase_id: "IDS-STAGE030-P3"',
            'current_phase_id: "IDS-STAGE030-P4"',
            'current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_phase_id: "IDS-STAGE031-P1"',
            'current_phase_id: "IDS-STAGE031-P2"',
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE029-P2-GATE"',
            'next_gate_id: "IDS-STAGE029-P3-GATE"',
            'next_gate_id: "IDS-STAGE029-P4-GATE"',
            'next_gate_id: "IDS-STAGE030-P1-GATE"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'next_gate_id: "IDS-STAGE030-P4-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
            'next_gate_id: "IDS-STAGE031-P2-GATE"',
            'next_gate_id: "IDS-STAGE031-P3-GATE"',
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE029-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE029-P1"',
            '"ACC-STAGE-029"',
            "STAGE029_PHASE1_SCOPE_BOUNDARY.md",
        ]

        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase2_builds_cleanup_allowlist_from_safe_extraction_without_deleting_protected_refs(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = self._write_zip_fixture(
                base,
                {
                    "safe/stage029-scope-boundary.md": self._tracked_payload(),
                    "safe/stage029-entry-contract.md": ENTRY.read_bytes(),
                },
            )
            staging = base / "stage029-staging"

            report = module.build_archive_cleanup_allowlist(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at="2026-07-03T12:26:00Z",
            )

        self.assertEqual(report["schema_version"], "ids.stage029.archive_cleanup_allowlist.v1")
        self.assertEqual(report["stage"], "STAGE-029")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE029-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-029")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(report["source_schema_version"], "ids.stage028.archive_adversarial_tests.v1")
        self.assertTrue(report["archive_cleanup_allowlist_id"].startswith("ids.stage029.cleanup_allowlist."))
        self.assertEqual(report["cleanup_decision_state"], "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP")
        self.assertGreater(report["safe_extracted_file_count"], 0)
        self.assertEqual(report["cleanup_candidate_count"], len(report["cleanup_candidates"]))
        self.assertEqual(report["cleanup_validation"]["state"], "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED")
        self.assertTrue(report["cleanup_validation"]["cleanup_targets_are_staging_temp_files_only"])
        self.assertTrue(report["cleanup_validation"]["protected_refs_preserved"])
        self.assertFalse(report["cleanup_validation"]["original_archive_in_cleanup_allowlist"])
        self.assertEqual(report["post_extract_reingest"]["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertEqual(report["reingest_validation"]["state"], "ARCHIVE_CLEANUP_REINGEST_READY_FOR_PIPELINE")
        self.assertEqual(
            report["reingest_validation"]["actual_jobs_started"],
            {"hash": 0, "manifest": 0, "dedup": 0, "parser": 0, "ocr": 0, "embedding": 0, "index": 0, "import": 0},
        )
        self.assertEqual(set(report["cleanup_validation"]["allowed_cleanup_classes"]), {"ARCHIVE_STAGING_TEMP_FILE"})
        self.assertTrue(all(candidate["cleanup_candidate_class"] == "ARCHIVE_STAGING_TEMP_FILE" for candidate in report["cleanup_candidates"]))
        self.assertTrue(all(candidate["cleanup_executed"] is False for candidate in report["cleanup_candidates"]))
        self.assertTrue(all(candidate["delete_operation_started"] is False for candidate in report["cleanup_candidates"]))
        protected_classes = {item["protected_class"] for item in report["protected_refs"]}
        for expected_class in {
            "PROTECTED_ORIGINAL_ARCHIVE",
            "PROTECTED_ARCHIVE_MANIFEST",
            "PROTECTED_EVIDENCE_LEDGER",
            "PROTECTED_AUDIT_LOG",
            "PROTECTED_DELIVERED_REPORT",
            "PROTECTED_DATABASE_OR_INDEX",
            "PROTECTED_RAW_METADATA_ROOT",
        }:
            with self.subTest(expected_class=expected_class):
                self.assertIn(expected_class, protected_classes)
        for delta_name, delta_value in report["no_persistence_deltas"].items():
            with self.subTest(delta_name=delta_name):
                self.assertEqual(delta_value, 0)
        self.assertFalse(report["cleanup_runner_executed"])
        self.assertTrue(report["does_not_delete_files"])
        self.assertTrue(report["does_not_clean_original_archive"])
        self.assertTrue(report["does_not_clean_fact_source_or_evidence"])
        self.assertTrue(report["does_not_write_archive_cleanup_runtime_output"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_phase2_routes_failed_risk_and_over_limit_entries_to_owner_review_or_quarantine(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = self._tracked_payload()
            archive_path = self._write_zip_fixture(
                base,
                {
                    "safe/ok.md": payload,
                    "../escape.md": payload,
                    "/absolute.md": payload,
                    "nested/depth/archive.zip": payload,
                    "too-many/one.md": payload,
                    "too-many/two.md": payload,
                },
            )
            staging = base / "stage029-staging"

            report = module.build_archive_cleanup_allowlist(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at="2026-07-03T12:27:00Z",
                archive_file_count_limit=2,
                archive_nested_depth_limit=0,
            )

        self.assertEqual(report["cleanup_decision_state"], "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED")
        self.assertGreater(report["blocked_entry_count"], 0)
        self.assertGreater(report["owner_review_entry_count"], 0)
        self.assertGreater(report["quarantine_entry_count"], 0)
        self.assertEqual(
            report["manual_review_routing"]["state"],
            "ARCHIVE_CLEANUP_OWNER_REVIEW_OR_QUARANTINE_REQUIRED",
        )
        self.assertTrue(report["manual_review_routing"]["failure_files_to_owner_review"])
        self.assertTrue(report["manual_review_routing"]["risk_files_to_owner_review"])
        self.assertTrue(report["manual_review_routing"]["over_limit_files_to_owner_review"])
        self.assertTrue(report["manual_review_routing"]["quarantine_required"])
        self.assertTrue(all(entry["cleanup_routing_state"] in {"ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED", "ARCHIVE_CLEANUP_QUARANTINE_REQUIRED"} for entry in report["risk_entries"]))
        self.assertTrue(report["cleanup_validation"]["protected_refs_preserved"])
        self.assertFalse(report["cleanup_runner_executed"])
        self.assertTrue(report["does_not_delete_files"])

    def test_phase2_blocks_protected_cleanup_candidates(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = self._write_zip_fixture(base, {"safe/ok.md": self._tracked_payload()})
            staging = base / "stage029-staging"
            report = module.build_archive_cleanup_allowlist(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at="2026-07-03T12:28:00Z",
                additional_cleanup_candidates=[
                    {"uri": archive_path.as_uri(), "cleanup_candidate_class": "PROTECTED_ORIGINAL_ARCHIVE"},
                    {"uri": "evidence://stage029/evidence-ledger", "cleanup_candidate_class": "PROTECTED_EVIDENCE_LEDGER"},
                    {"uri": "audit://stage029/audit-log", "cleanup_candidate_class": "PROTECTED_AUDIT_LOG"},
                    {
                        "uri": "file:///Users/linzezhang/Downloads/IDS_MetaData/raw.db",
                        "cleanup_candidate_class": "ARCHIVE_STAGING_TEMP_FILE",
                    },
                ],
            )

        blocked_candidates = [
            candidate
            for candidate in report["cleanup_candidates"]
            if candidate["cleanup_decision_state"] == "ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF"
        ]
        self.assertEqual(len(blocked_candidates), 4)
        self.assertEqual(report["blocked_protected_candidate_count"], 4)
        self.assertEqual(report["cleanup_decision_state"], "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED")
        self.assertTrue(all(candidate["cleanup_executed"] is False for candidate in blocked_candidates))
        self.assertTrue(all(candidate["delete_operation_started"] is False for candidate in blocked_candidates))
        self.assertTrue(report["cleanup_validation"]["protected_refs_preserved"])
        self.assertTrue(report["cleanup_validation"]["does_not_clean_original_archive"])
        self.assertTrue(report["cleanup_validation"]["does_not_clean_fact_source_or_evidence"])

    def test_phase2_cli_emits_json_without_runtime_output_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = self._write_zip_fixture(base, {"safe/ok.md": self._tracked_payload()})
            staging = base / "stage029-staging"
            result = subprocess.run(
                [
                    "python3",
                    "-B",
                    str(SCRIPT),
                    "--archive-uri",
                    archive_path.as_uri(),
                    "--staging-area-uri",
                    staging.as_uri(),
                    "--evaluated-at",
                    "2026-07-03T12:29:00Z",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "ids.stage029.archive_cleanup_allowlist.v1")
        self.assertFalse(report["cleanup_runner_executed"])
        self.assertTrue(report["does_not_write_archive_cleanup_runtime_output"])

    def test_phase2_evidence_batch_roadmap_and_event_track_local_no_upload_gate(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        phase2_text = PHASE2.read_text(encoding="utf-8")
        batch_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase2_terms = [
            "IDS-V0_1-STAGE029-P2",
            "ACC-STAGE-029",
            "build_archive_cleanup_allowlist",
            "ids.stage029.archive_cleanup_allowlist.v1",
            "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP",
            "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF",
            "safe extraction",
            "path filtering",
            "risk marking",
            "quarantine",
            "owner review",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "不执行 cleanup runner",
            "不删除原始资料",
            "不删除原始压缩包",
            "不删除 manifest",
            "不删除 evidence",
            "不删除 audit",
            "不删除报告",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "file:///Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE3",
        ]
        batch_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            'push_allowed:',
            "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md",
        ]
        allowed_batch_status_terms = [
            'status: "stage029_phase2_in_progress"',
            'status: "stage029_phase3_in_progress"',
            'status: "stage029_completed_local_pending_stage030"',
            'status: "stage030_phase1_in_progress"',
            'status: "stage030_phase2_in_progress"',
            'status: "stage030_phase3_in_progress"',
            'status: "stage030_completed_local_pending_batch_review"',
            'status: "reviewed_ready_for_upload_no_github_upload"',
            'status: "completed_local"',
        ]
        allowed_batch_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
        ]
        allowed_batch_acceptance_terms = [
            'acceptance_status: "phase2_cleanup_allowlist_slice_complete"',
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        allowed_batch_gate_terms = [
            'next_gate: "IDS-STAGE029-P3-GATE"',
            'next_gate: "IDS-STAGE029-P4-GATE"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'next_gate: "IDS-STAGE030-P4-GATE"',
            'next_gate: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
        ]
        allowed_batch_next_task_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
        ]
        roadmap_terms = [
            'phase_id: "IDS-STAGE029-P2"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE029"',
            'current_stage_id: "IDS-STAGE030"',
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
            'current_stage_id: "IDS-STAGE034"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE029-P2"',
            'current_phase_id: "IDS-STAGE029-P3"',
            'current_phase_id: "IDS-STAGE029-P4"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_phase_id: "IDS-STAGE030-P3"',
            'current_phase_id: "IDS-STAGE030-P4"',
            'current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_phase_id: "IDS-STAGE031-P1"',
            'current_phase_id: "IDS-STAGE031-P2"',
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE029-P3-GATE"',
            'next_gate_id: "IDS-STAGE029-P4-GATE"',
            'next_gate_id: "IDS-STAGE030-P1-GATE"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'next_gate_id: "IDS-STAGE030-P4-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
            'next_gate_id: "IDS-STAGE031-P2-GATE"',
            'next_gate_id: "IDS-STAGE031-P3-GATE"',
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE029-P2-20260703-001"',
            '"event_type":"implementation"',
            '"task_id":"IDS-V0_1-STAGE029-P2"',
            '"ACC-STAGE-029"',
            "check_archive_cleanup_allowlist.py",
            "STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md",
        ]

        for term in phase2_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)
        for term in batch_terms:
            with self.subTest(term=term):
                self.assertIn(term, batch_text)
        self.assertTrue(any(term in batch_text for term in allowed_batch_status_terms), allowed_batch_status_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_task_terms), allowed_batch_task_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_acceptance_terms), allowed_batch_acceptance_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_gate_terms), allowed_batch_gate_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_next_task_terms), allowed_batch_next_task_terms)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase3_scenario_report_validates_risks_reingest_cleanup_and_no_delete(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            report = module.build_stage029_scenario_report(
                scenario_archives=self._phase3_scenario_archives(Path(tmp)),
                evaluated_at="2026-07-03T13:12:00Z",
            )

        self.assertEqual(report["schema_version"], "ids.stage029.archive_cleanup_allowlist.scenario_validation.v1")
        self.assertEqual(report["stage"], "STAGE-029")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE029-P3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-029")
        self.assertEqual(report["source_schema_version"], "ids.stage029.archive_cleanup_allowlist.v1")
        self.assertEqual(report["validation_state"], "ARCHIVE_CLEANUP_SCENARIO_VALIDATION_PASSED")
        self.assertTrue(report["required_scenarios_covered"])
        self.assertEqual(
            report["required_scenarios"],
            [
                "path_traversal",
                "absolute_path",
                "archive_bomb",
                "nested_archive",
                "garbled_filename",
                "too_many_files",
            ],
        )
        self.assertEqual(report["scenario_count"], 6)

        expected_risks = {
            "path_traversal": "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
            "absolute_path": "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
            "archive_bomb": "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
            "nested_archive": "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
            "garbled_filename": "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "too_many_files": "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
        }
        by_id = {item["scenario_id"]: item for item in report["scenario_results"]}
        for scenario_id, risk_code in expected_risks.items():
            with self.subTest(scenario_id=scenario_id):
                result = by_id[scenario_id]
                self.assertEqual(result["scenario_state"], "ARCHIVE_CLEANUP_SCENARIO_VALIDATED")
                self.assertEqual(result["expected_risk_code"], risk_code)
                self.assertTrue(result["expected_risk_observed"])
                self.assertIn(risk_code, result["risk_codes"])
                self.assertGreaterEqual(result["cleanup_candidate_count"], 0)
                self.assertFalse(result["cleanup_runner_executed"])
                self.assertTrue(result["does_not_delete_files"])

        reingest_validation = report["reingest_validation"]
        self.assertEqual(reingest_validation["state"], "ARCHIVE_CLEANUP_REINGEST_VALIDATED")
        self.assertEqual(reingest_validation["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertGreaterEqual(reingest_validation["safe_extracted_file_count"], 1)
        self.assertEqual(
            reingest_validation["actual_jobs_started"],
            {"hash": 0, "manifest": 0, "dedup": 0, "parser": 0, "ocr": 0, "embedding": 0, "index": 0, "import": 0},
        )
        self.assertFalse(reingest_validation["import_queue_created"])

        cleanup_validation = report["cleanup_validation"]
        self.assertEqual(cleanup_validation["state"], "ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_VALIDATED")
        self.assertTrue(cleanup_validation["cleanup_targets_are_staging_temp_files_only"])
        self.assertFalse(cleanup_validation["original_archive_in_cleanup_allowlist"])
        self.assertTrue(cleanup_validation["protected_refs_preserved"])
        self.assertTrue(cleanup_validation["does_not_clean_original_archive"])
        self.assertTrue(cleanup_validation["does_not_clean_fact_source_or_evidence"])

        self.assertFalse(report["cleanup_runner_executed"])
        self.assertTrue(report["does_not_delete_files"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_archive_cleanup_runtime_output"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])
        self.assertTrue(report["does_not_start_processing_jobs"])
        self.assertTrue(report["does_not_create_import_queue"])
        self.assertTrue(all(value == 0 for value in report["no_persistence_deltas"].values()))

    def test_phase3_evidence_batch_roadmap_and_event_track_local_no_upload_gate(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        phase3_text = PHASE3.read_text(encoding="utf-8")
        batch_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase3_terms = [
            "IDS-V0_1-STAGE029-P3",
            "ACC-STAGE-029",
            "build_stage029_scenario_report",
            "ids.stage029.archive_cleanup_allowlist.scenario_validation.v1",
            "path_traversal",
            "absolute_path",
            "archive_bomb",
            "nested_archive",
            "garbled_filename",
            "too_many_files",
            "ARCHIVE_CLEANUP_SCENARIO_VALIDATION_PASSED",
            "ARCHIVE_CLEANUP_REINGEST_VALIDATED",
            "ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_VALIDATED",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "只清理允许的临时文件",
            "不执行 cleanup runner",
            "不删除原始资料",
            "不删除原始压缩包",
            "不删除 manifest",
            "不删除 evidence",
            "不删除 audit",
            "不删除报告",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE4",
        ]
        batch_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            'push_allowed:',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE3_SCENARIO_VALIDATION.md",
        ]
        allowed_batch_status_terms = [
            'status: "stage029_phase3_in_progress"',
            'status: "stage029_completed_local_pending_stage030"',
            'status: "stage030_phase1_in_progress"',
            'status: "stage030_phase2_in_progress"',
            'status: "stage030_phase3_in_progress"',
            'status: "stage030_completed_local_pending_batch_review"',
            'status: "reviewed_ready_for_upload_no_github_upload"',
            'status: "completed_local"',
        ]
        allowed_batch_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
        ]
        allowed_batch_acceptance_terms = [
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        allowed_batch_gate_terms = [
            'next_gate: "IDS-STAGE029-P4-GATE"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'next_gate: "IDS-STAGE030-P4-GATE"',
            'next_gate: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
        ]
        allowed_batch_next_task_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_allowed_task_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
        ]
        roadmap_terms = [
            'phase_id: "IDS-STAGE029-P3"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage029_scenario_report",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE029"',
            'current_stage_id: "IDS-STAGE030"',
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
            'current_stage_id: "IDS-STAGE034"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE029-P3"',
            'current_phase_id: "IDS-STAGE029-P4"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_phase_id: "IDS-STAGE030-P3"',
            'current_phase_id: "IDS-STAGE030-P4"',
            'current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_phase_id: "IDS-STAGE031-P1"',
            'current_phase_id: "IDS-STAGE031-P2"',
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE029-P4-GATE"',
            'next_gate_id: "IDS-STAGE030-P1-GATE"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'next_gate_id: "IDS-STAGE030-P4-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
            'next_gate_id: "IDS-STAGE031-P2-GATE"',
            'next_gate_id: "IDS-STAGE031-P3-GATE"',
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE029-P3-20260703-001"',
            '"event_type":"validation"',
            '"task_id":"IDS-V0_1-STAGE029-P3"',
            '"ACC-STAGE-029"',
            "STAGE029_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage029_scenario_report",
        ]

        for term in phase3_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase3_text)
        for term in batch_terms:
            with self.subTest(term=term):
                self.assertIn(term, batch_text)
        self.assertTrue(any(term in batch_text for term in allowed_batch_status_terms), allowed_batch_status_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_task_terms), allowed_batch_task_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_acceptance_terms), allowed_batch_acceptance_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_gate_terms), allowed_batch_gate_terms)
        self.assertTrue(any(term in batch_text for term in allowed_batch_next_task_terms), allowed_batch_next_task_terms)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase4_closeout_summary_records_delivery_evidence_rollback_owner_feedback_and_no_upload(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            scenario_report = module.build_stage029_scenario_report(
                scenario_archives=self._phase3_scenario_archives(Path(tmp)),
                evaluated_at="2026-07-03T13:34:00Z",
            )
            closeout = module.build_stage029_closeout_summary(
                scenario_report=scenario_report,
                evaluated_at="2026-07-03T13:34:00Z",
            )

        self.assertEqual(closeout["schema_version"], "ids.stage029.archive_cleanup_allowlist.closeout.v1")
        self.assertEqual(closeout["stage"], "STAGE-029")
        self.assertEqual(closeout["phase"], "Phase 4")
        self.assertEqual(closeout["task_id"], "IDS-V0_1-STAGE029-P4")
        self.assertEqual(closeout["acceptance_id"], "ACC-STAGE-029")
        self.assertEqual(closeout["source_scenario_schema"], "ids.stage029.archive_cleanup_allowlist.scenario_validation.v1")
        self.assertEqual(closeout["closeout_state"], "ARCHIVE_CLEANUP_STAGE_CLOSEOUT_PASSED")
        self.assertEqual(closeout["whole_stage_review"]["result"], "passed_with_local_evidence")
        self.assertEqual(closeout["next_allowed_task_id"], "IDS-V0_1-STAGE030-P1")
        self.assertFalse(closeout["github_upload_allowed"])
        self.assertFalse(closeout["app_reinstall_allowed"])

        delivery = closeout["delivery_evidence"]
        self.assertEqual(delivery["evidence_state"], "ARCHIVE_CLEANUP_DELIVERY_EVIDENCE_READY")
        manifest_sample = delivery["archive_manifest_sample"]
        self.assertEqual(manifest_sample["schema_version"], "ids.stage029.archive_cleanup_allowlist.manifest_sample.v1")
        self.assertEqual(manifest_sample["sample_state"], "ARCHIVE_CLEANUP_MANIFEST_SAMPLE_READY")
        self.assertGreaterEqual(manifest_sample["entry_count"], 1)
        self.assertFalse(manifest_sample["runtime_output_written"])
        self.assertFalse(manifest_sample["archive_manifest_runtime_output_written"])
        self.assertTrue(manifest_sample["original_archive_preserved"])

        block_log = delivery["safety_block_log_sample"]
        self.assertEqual(block_log["state"], "ARCHIVE_CLEANUP_BLOCK_LOG_READY")
        self.assertTrue(
            {
                "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
                "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
                "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
                "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
                "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
                "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
            }
            <= set(block_log["risk_codes"]),
            block_log,
        )
        self.assertGreaterEqual(block_log["blocked_entry_count"], 6)
        self.assertFalse(block_log["runtime_output_written"])
        self.assertFalse(block_log["audit_log_written"])

        cleanup_sample = delivery["cleanup_allowlist_sample"]
        self.assertEqual(cleanup_sample["state"], "ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_VALIDATED")
        self.assertTrue(cleanup_sample["cleanup_targets_are_staging_temp_files_only"])
        self.assertFalse(cleanup_sample["original_archive_in_cleanup_allowlist"])
        self.assertTrue(cleanup_sample["protected_refs_preserved"])

        risk_boundary = closeout["risk_boundary"]
        self.assertTrue(risk_boundary["raw_metadata_path_only_boundary"])
        self.assertTrue(risk_boundary["real_data_only_policy"])
        self.assertTrue(risk_boundary["no_runtime_output"])
        self.assertTrue(risk_boundary["no_processing_jobs"])
        self.assertTrue(risk_boundary["no_deletion"])
        self.assertIn("/Users/linzezhang/Downloads/IDS_MetaData", risk_boundary["raw_metadata_root"])
        self.assertGreaterEqual(len(risk_boundary["stop_conditions"]), 5)

        rollback = closeout["staging_rollback"]
        self.assertEqual(rollback["rollback_state"], "ARCHIVE_CLEANUP_STAGING_ROLLBACK_DOCUMENTED")
        self.assertTrue(rollback["cleanup_instructions"]["temp_only"])
        self.assertTrue(rollback["cleanup_instructions"]["do_not_delete_original_archive"])
        self.assertTrue(rollback["cleanup_instructions"]["do_not_touch_raw_metadata_root"])
        self.assertTrue(rollback["cleanup_instructions"]["do_not_clean_manifest_evidence_audit_or_reports"])

        self.assertGreaterEqual(len(closeout["owner_feedback_zh"]), 3)
        self.assertTrue(closeout["does_not_read_raw_metadata"])
        self.assertTrue(closeout["does_not_write_runtime_outputs"])
        self.assertTrue(closeout["does_not_delete_files"])
        self.assertTrue(closeout["does_not_use_fake_ids_business_data"])

    def test_phase4_closeout_doc_records_delivery_evidence_risk_stop_rollback_and_chinese_feedback(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE029-P4",
            "ACC-STAGE-029",
            "ids.stage029.archive_cleanup_allowlist.closeout.v1",
            "build_stage029_closeout_summary",
            "archive_manifest 样例",
            "安全阻断日志",
            "清理白名单",
            "自动解压风险边界",
            "停止条件",
            "staging 区回滚",
            "清理说明",
            "Whole-Stage Review",
            "中文 owner feedback",
            "ARCHIVE_CLEANUP_STAGE_CLOSEOUT_PASSED",
            "ARCHIVE_CLEANUP_DELIVERY_EVIDENCE_READY",
            "ARCHIVE_CLEANUP_STAGING_ROLLBACK_DOCUMENTED",
            "No GitHub upload",
            "No app reinstall",
            "next allowed task",
            "IDS-V0_1-STAGE030-P1",
            "process-owned temporary archive fixtures",
            "不得使用虚构 IDS 业务数据",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE030",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_stage029_completed_local_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            "STAGE-029:",
            'status: "completed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'next_stage: "STAGE-030"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'acceptance_id: "ACC-STAGE-029"',
            'acceptance_status: "local_passed"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'push_allowed:',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE2_CLEANUP_ALLOWLIST_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_archive_cleanup_allowlist.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage029_phase4_closeout_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'stage_id: "IDS-STAGE029"',
            'name: "STAGE-029 · 压缩包清理白名单"',
            'phase_id: "IDS-STAGE029-P4"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_archive_cleanup_allowlist.py",
            "build_stage029_closeout_summary",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE029"',
            'current_stage_id: "IDS-STAGE030"',
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
            'current_stage_id: "IDS-STAGE034"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE029-P4"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_phase_id: "IDS-STAGE030-P3"',
            'current_phase_id: "IDS-STAGE030-P4"',
            'current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_phase_id: "IDS-STAGE031-P1"',
            'current_phase_id: "IDS-STAGE031-P2"',
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P4"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE030-P1-GATE"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'next_gate_id: "IDS-STAGE030-P4-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"',
            'next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"',
            'next_gate_id: "IDS-STAGE031-P2-GATE"',
            'next_gate_id: "IDS-STAGE031-P3-GATE"',
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE029-P4-20260703-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE029-P4"',
            '"ACC-STAGE-029"',
            "STAGE029_PHASE4_CLOSEOUT.md",
            "check_archive_cleanup_allowlist.py",
            "build_stage029_closeout_summary",
        ]
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
