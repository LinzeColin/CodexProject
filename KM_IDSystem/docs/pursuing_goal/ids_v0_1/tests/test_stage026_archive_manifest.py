import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE026_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE026_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE026_PHASE2_ARCHIVE_MANIFEST_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE026_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE026_PHASE4_CLOSEOUT.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
SCRIPT = ROOT / "scripts" / "check_archive_manifest.py"
MANIFESTED_AT = "2026-07-03T03:21:34Z"


class Stage026ArchiveManifestPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage026_archive_manifest", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _write_zip(self, archive_path, entries):
        with zipfile.ZipFile(archive_path, "w") as archive:
            for entry_path, payload in entries.items():
                archive.writestr(entry_path, payload)

    def _phase3_scenario_archives(self, base):
        scenario_archives = {}
        scenario_specs = {
            "path_traversal": {
                "entries": {
                    "safe/path-traversal-note.md": b"ok",
                    "../escape.txt": b"escape",
                },
            },
            "absolute_path": {
                "entries": {
                    "safe/absolute-note.md": b"ok",
                    "/absolute.txt": b"absolute",
                },
            },
            "archive_bomb": {
                "entries": {
                    "huge.bin": b"0123456789",
                },
                "archive_total_size_limit_bytes": 4,
            },
            "nested_archive": {
                "entries": {
                    "safe/nested-note.md": b"ok",
                    "nested/inner.zip": b"PK\x03\x04ids nested structural archive",
                },
                "archive_nested_depth_limit": 0,
            },
            "garbled_filename": {
                "entries": {
                    "safe/garbled-note.md": b"ok",
                    "bad-\ufffd-name.txt": b"bad",
                },
            },
            "too_many_files": {
                "entries": {
                    "safe/one.txt": b"one",
                    "safe/two.txt": b"two",
                },
                "archive_file_count_limit": 1,
            },
        }
        for scenario_id, spec in scenario_specs.items():
            archive_path = base / f"{scenario_id}.zip"
            staging = base / f"{scenario_id}-staging"
            self._write_zip(archive_path, spec["entries"])
            scenario_archives[scenario_id] = {
                "archive_uri": archive_path.as_uri(),
                "staging_area_uri": staging.as_uri(),
            }
            for key in (
                "archive_file_count_limit",
                "archive_total_size_limit_bytes",
                "archive_nested_depth_limit",
            ):
                if key in spec:
                    scenario_archives[scenario_id][key] = spec[key]
        return scenario_archives

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
            "STAGE-026",
            "IDS-V0_1-STAGE026-P1",
            "ACC-STAGE-026",
            "压缩包 Manifest",
            "压缩包 hash",
            "解压文件列表",
            "解压体积",
            "嵌套层级",
            "失败项",
            "风险项",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-026_压缩包Manifest.md",
            "71f966c9a669563073a502e3beef5bc85a50d9cdb077b996687653ca48c3da70",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_archive_manifest_boundary_staging_limits_and_reingest_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "archive_manifest_id",
            "archive_manifest_schema",
            "archive_source_uri",
            "original_archive_ref",
            "archive_staging_area_uri",
            "archive_hash_sha256",
            "archive_type",
            "archive_entry_manifest",
            "archive_entry_path_policy",
            "archive_file_count_limit",
            "archive_total_size_limit_bytes",
            "archive_single_file_size_limit_bytes",
            "archive_nested_depth_limit",
            "archive_failed_items",
            "archive_risk_items",
            "archive_manifest_decision_state",
            "ARCHIVE_MANIFEST_DRAFT",
            "ARCHIVE_MANIFEST_BLOCKED",
            "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_MANIFEST_READY_FOR_SAFE_EXTRACTION",
            "POST_EXTRACT_REINGEST_REQUIRED",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_extraction_no_runtime_manifest_and_raw_data_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行解压",
            "不覆盖原始压缩包",
            "不写出指定 staging 区",
            "不读取真实压缩包内容",
            "不写 archive_manifest runtime output",
            "不创建 staging runtime directory",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不生成 runtime 输出",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage026_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            "STAGE-021:",
            "STAGE-022:",
            "STAGE-023:",
            "STAGE-024:",
            "STAGE-025:",
            "STAGE-026:",
            'completed_phases:',
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-026"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        allowed_stage_status_terms = [
            'status: "in_progress"',
            'status: "completed_local"',
        ]
        self.assertTrue(any(term in text for term in allowed_stage_status_terms), allowed_stage_status_terms)
        allowed_status_terms = [
            'status: "stage026_phase1_in_progress"',
            'status: "stage026_phase2_in_progress"',
            'status: "stage026_phase3_in_progress"',
            'status: "stage026_completed_local_pending_stage027"',
            'status: "completed_local"',
            'status: "stage027_phase1_in_progress"',
            'status: "stage027_completed_local_pending_stage028"',
            'status: "stage028_phase1_in_progress"',
            'status: "stage028_phase2_in_progress"',
            'status: "stage028_phase3_in_progress"',
            'status: "stage028_completed_local_pending_stage029"',
            'status: "stage029_phase1_in_progress"',
            'status: "stage029_phase2_in_progress"',
            'status: "stage029_phase3_in_progress"',
            'status: "stage029_completed_local_pending_stage030"',
            'status: "stage030_phase1_in_progress"',
            'status: "stage030_phase2_in_progress"',
            'status: "stage030_phase3_in_progress"',
        ]
        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE026-P1"',
            'current_task_id: "IDS-V0_1-STAGE026-P2"',
            'current_task_id: "IDS-V0_1-STAGE026-P3"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P4"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'current_task_id: "IDS-V0_1-STAGE028-P2"',
            'current_task_id: "IDS-V0_1-STAGE028-P3"',
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
        ]
        allowed_acceptance_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_archive_manifest_slice_complete"',
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        allowed_gate_terms = [
            'next_gate: "IDS-STAGE026-P2-GATE"',
            'next_gate: "IDS-STAGE026-P3-GATE"',
            'next_gate: "IDS-STAGE026-P4-GATE"',
            'next_gate: "IDS-STAGE027-P1-GATE"',
            'next_gate: "IDS-STAGE027-P2-GATE"',
            'next_gate: "IDS-STAGE027-P3-GATE"',
            'next_gate: "IDS-STAGE027-P4-GATE"',
            'next_gate: "IDS-STAGE028-P1-GATE"',
            'next_gate: "IDS-STAGE028-P2-GATE"',
            'next_gate: "IDS-STAGE028-P3-GATE"',
            'next_gate: "IDS-STAGE028-P4-GATE"',
            'next_gate: "IDS-STAGE029-P1-GATE"',
            'next_gate: "IDS-STAGE029-P2-GATE"',
            'next_gate: "IDS-STAGE029-P3-GATE"',
            'next_gate: "IDS-STAGE029-P4-GATE"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'next_gate: "IDS-STAGE030-P4-GATE"',
        ]
        allowed_next_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
        ]
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)
        self.assertTrue(any(term in text for term in allowed_task_terms), allowed_task_terms)
        self.assertTrue(any(term in text for term in allowed_acceptance_terms), allowed_acceptance_terms)
        self.assertTrue(any(term in text for term in allowed_gate_terms), allowed_gate_terms)
        self.assertTrue(any(term in text for term in allowed_next_terms), allowed_next_terms)

    def test_roadmap_and_events_track_stage026_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'stage_id: "IDS-STAGE026"',
            'name: "STAGE-026 · 压缩包 Manifest"',
            'phase_id: "IDS-STAGE026-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE1_SCOPE_BOUNDARY.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE026-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE026-P1"',
            '"ACC-STAGE-026"',
            "STAGE026_PHASE1_SCOPE_BOUNDARY.md",
        ]

        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        allowed_current_terms = [
            'current_phase_id: "IDS-STAGE026-P1"',
            'current_phase_id: "IDS-STAGE026-P2"',
            'current_phase_id: "IDS-STAGE026-P3"',
            'current_phase_id: "IDS-STAGE026-P4"',
            'current_phase_id: "IDS-STAGE027-P1"',
            'current_phase_id: "IDS-STAGE027-P2"',
            'current_phase_id: "IDS-STAGE027-P3"',
            'current_phase_id: "IDS-STAGE027-P4"',
            'current_phase_id: "IDS-STAGE028-P1"',
            'current_phase_id: "IDS-STAGE028-P2"',
            'current_phase_id: "IDS-STAGE028-P3"',
            'current_phase_id: "IDS-STAGE028-P4"',
            'current_phase_id: "IDS-STAGE029-P1"',
            'current_phase_id: "IDS-STAGE029-P2"',
            'current_phase_id: "IDS-STAGE029-P3"',
            'current_phase_id: "IDS-STAGE029-P4"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_phase_id: "IDS-STAGE030-P3"',
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE026-P1"',
            'current_task_id: "IDS-V0_1-STAGE026-P2"',
            'current_task_id: "IDS-V0_1-STAGE026-P3"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P2"',
            'current_task_id: "IDS-V0_1-STAGE027-P3"',
            'current_task_id: "IDS-V0_1-STAGE027-P4"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'current_task_id: "IDS-V0_1-STAGE028-P2"',
            'current_task_id: "IDS-V0_1-STAGE028-P3"',
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_gate_id: "IDS-STAGE026-P2-GATE"',
            'next_gate_id: "IDS-STAGE026-P3-GATE"',
            'next_gate_id: "IDS-STAGE026-P4-GATE"',
            'next_gate_id: "IDS-STAGE027-P1-GATE"',
            'next_gate_id: "IDS-STAGE027-P2-GATE"',
            'next_gate_id: "IDS-STAGE027-P3-GATE"',
            'next_gate_id: "IDS-STAGE027-P4-GATE"',
            'next_gate_id: "IDS-STAGE028-P1-GATE"',
            'next_gate_id: "IDS-STAGE028-P2-GATE"',
            'next_gate_id: "IDS-STAGE028-P3-GATE"',
            'next_gate_id: "IDS-STAGE028-P4-GATE"',
            'next_gate_id: "IDS-STAGE029-P1-GATE"',
            'next_gate_id: "IDS-STAGE029-P2-GATE"',
            'next_gate_id: "IDS-STAGE029-P3-GATE"',
            'next_gate_id: "IDS-STAGE029-P4-GATE"',
            'next_gate_id: "IDS-STAGE030-P1-GATE"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'next_gate_id: "IDS-STAGE030-P4-GATE"',
        ]
        allowed_phase_terms = [term for term in allowed_current_terms if term.startswith("current_phase_id")]
        allowed_task_terms = [term for term in allowed_current_terms if term.startswith("current_task_id")]
        allowed_gate_terms = [term for term in allowed_current_terms if term.startswith("next_gate_id")]
        self.assertTrue(any(term in roadmap_text for term in allowed_phase_terms), allowed_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_task_terms), allowed_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_gate_terms), allowed_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase2_archive_manifest_records_hash_entries_risks_reingest_and_cleanup_without_runtime_manifest(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-archive-manifest.zip"
            staging = base / "staging"
            outside = base / "escape.txt"
            entries = {
                "safe/manifest-note.md": b"ok",
                "../escape.txt": b"escape",
                "/absolute.txt": b"absolute",
                "too-large.bin": b"0123456789",
            }
            self._write_zip(archive_path, entries)
            expected_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()

            manifest = module.build_archive_manifest(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                manifested_at=MANIFESTED_AT,
                archive_single_file_size_limit_bytes=4,
            )

            safe_target = staging / "safe" / "manifest-note.md"
            self.assertTrue(safe_target.is_file())
            self.assertEqual(safe_target.read_bytes(), b"ok")
            self.assertTrue(archive_path.is_file())
            self.assertFalse(outside.exists())

        self.assertEqual(manifest["schema_version"], "ids.stage026.archive_manifest.v1")
        self.assertEqual(manifest["source_schema_version"], "ids.stage025.safe_extraction_engine.v1")
        self.assertEqual(manifest["stage"], "STAGE-026")
        self.assertEqual(manifest["phase"], "Phase 2")
        self.assertEqual(manifest["task_id"], "IDS-V0_1-STAGE026-P2")
        self.assertEqual(manifest["acceptance_id"], "ACC-STAGE-026")
        self.assertEqual(manifest["archive_manifest_schema"], "ids.stage026.archive_manifest.v1")
        self.assertEqual(manifest["archive_hash_sha256"], expected_hash)
        self.assertTrue(manifest["archive_manifest_id"].startswith("ids.stage026.archive_manifest."))
        self.assertEqual(manifest["archive_manifest_decision_state"], "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED")
        self.assertEqual(manifest["safe_extracted_file_count"], 1)
        self.assertGreaterEqual(manifest["archive_blocked_entry_count"], 3)
        self.assertGreaterEqual(len(manifest["archive_entry_manifest"]), 4)
        self.assertEqual(len(manifest["post_extract_reingest"]["reingest_queue"]), 1)
        self.assertEqual(manifest["post_extract_reingest"]["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertEqual(manifest["post_extract_reingest"]["state"], "POST_EXTRACT_REINGEST_REQUIRED")
        risk_codes = {entry["risk_code"] for entry in manifest["archive_risk_items"]}
        self.assertIn("ARCHIVE_MANIFEST_PATH_TRAVERSAL_BLOCKED", risk_codes)
        self.assertIn("ARCHIVE_MANIFEST_ABSOLUTE_PATH_BLOCKED", risk_codes)
        self.assertIn("ARCHIVE_MANIFEST_ENTRY_SIZE_LIMIT_EXCEEDED", risk_codes)
        quarantine_states = {entry["manifest_entry_state"] for entry in manifest["archive_risk_items"]}
        self.assertIn("ARCHIVE_MANIFEST_ENTRY_QUARANTINE_REQUIRED", quarantine_states)
        self.assertTrue(manifest["cleanup_allowlist"])
        self.assertTrue(all(item["cleanup_class"] == "ARCHIVE_STAGING_TEMP_FILE" for item in manifest["cleanup_allowlist"]))
        self.assertTrue(manifest["cleanup_policy"]["does_not_clean_original_archive"])
        self.assertTrue(manifest["cleanup_policy"]["does_not_clean_fact_source_or_evidence"])
        self.assertTrue(manifest["original_archive_preserved"])
        self.assertTrue(manifest["does_not_overwrite_original_archive"])
        self.assertTrue(manifest["does_not_write_outside_staging"])
        self.assertTrue(manifest["does_not_write_archive_manifest_runtime_output"])
        self.assertTrue(manifest["does_not_start_processing_jobs"])
        for value in manifest["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in manifest["no_persistence_deltas"].values():
            self.assertEqual(value, 0)

    def test_phase2_manifest_routes_missing_raw_and_adapter_cases_without_raw_access_or_fake_support(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            staging = base / "staging"
            missing = base / "missing.zip"
            rar_path = base / "owner-review.rar"
            rar_path.write_bytes(b"Rar!\x1a\x07\x00ids structural rar placeholder")

            missing_manifest = module.build_archive_manifest(
                archive_uri=missing.as_uri(),
                staging_area_uri=staging.as_uri(),
                manifested_at=MANIFESTED_AT,
            )
            rar_manifest = module.build_archive_manifest(
                archive_uri=rar_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                manifested_at=MANIFESTED_AT,
            )
            raw_manifest = module.build_archive_manifest(
                archive_uri="file:///Users/linzezhang/Downloads/IDS_MetaData/raw-owner.zip",
                staging_area_uri=(base / "raw-staging").as_uri(),
                manifested_at=MANIFESTED_AT,
            )

        self.assertEqual(missing_manifest["archive_manifest_decision_state"], "ARCHIVE_MANIFEST_BLOCKED")
        missing_risks = {entry["risk_code"] for entry in missing_manifest["archive_risk_items"]}
        self.assertIn("ARCHIVE_MANIFEST_SOURCE_MISSING", missing_risks)
        self.assertIsNone(missing_manifest["archive_hash_sha256"])

        self.assertEqual(rar_manifest["archive_manifest_decision_state"], "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED")
        rar_risks = {entry["risk_code"] for entry in rar_manifest["archive_risk_items"]}
        self.assertIn("ARCHIVE_MANIFEST_ADAPTER_OWNER_REVIEW_REQUIRED", rar_risks)
        self.assertTrue(rar_manifest["does_not_fake_rar_7z_support"])

        self.assertEqual(raw_manifest["archive_manifest_decision_state"], "ARCHIVE_MANIFEST_BLOCKED")
        raw_risks = {entry["risk_code"] for entry in raw_manifest["archive_risk_items"]}
        self.assertIn("ARCHIVE_MANIFEST_SOURCE_BLOCKED_RAW_METADATA_ROOT", raw_risks)
        self.assertIsNone(raw_manifest["archive_hash_sha256"])
        self.assertTrue(raw_manifest["does_not_read_raw_metadata"])

    def test_phase2_evidence_document_records_implemented_slice_and_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")
        required_terms = [
            "STAGE-026",
            "IDS-V0_1-STAGE026-P2",
            "ACC-STAGE-026",
            "KM_IDSystem/scripts/check_archive_manifest.py",
            "build_archive_manifest",
            "ids.stage026.archive_manifest.v1",
            "压缩包 hash",
            "解压文件列表",
            "解压体积",
            "嵌套层级",
            "失败项",
            "风险项",
            "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_MANIFEST_BLOCKED",
            "POST_EXTRACT_REINGEST_REQUIRED",
            "cleanup allowlist",
            "不清理事实源和证据产物",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_current_stage026_phase2_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")
        required_terms = [
            "STAGE-026:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            'acceptance_id: "ACC-STAGE-026"',
            'push_allowed: false',
            "KM_IDSystem/scripts/check_archive_manifest.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE2_ARCHIVE_MANIFEST_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        allowed_status_terms = [
            'status: "stage026_phase2_in_progress"',
            'status: "stage026_phase3_in_progress"',
            'status: "completed_local"',
            'status: "stage027_phase1_in_progress"',
            'status: "stage027_completed_local_pending_stage028"',
            'status: "stage028_phase1_in_progress"',
            'status: "stage028_phase2_in_progress"',
            'status: "stage028_phase3_in_progress"',
            'status: "stage028_completed_local_pending_stage029"',
            'status: "stage029_phase1_in_progress"',
            'status: "stage029_phase2_in_progress"',
            'status: "stage029_phase3_in_progress"',
            'status: "stage029_completed_local_pending_stage030"',
            'status: "stage030_phase1_in_progress"',
            'status: "stage030_phase2_in_progress"',
            'status: "stage030_phase3_in_progress"',
        ]
        allowed_next_phase_terms = [
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_stage: "STAGE-027"',
            'next_stage: "STAGE-028"',
            'next_phase: "Phase 2"',
        ]
        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE026-P2"',
            'current_task_id: "IDS-V0_1-STAGE026-P3"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P4"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'current_task_id: "IDS-V0_1-STAGE028-P2"',
            'current_task_id: "IDS-V0_1-STAGE028-P3"',
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
        ]
        allowed_acceptance_terms = [
            'acceptance_status: "phase2_archive_manifest_slice_complete"',
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        allowed_gate_terms = [
            'next_gate: "IDS-STAGE026-P3-GATE"',
            'next_gate: "IDS-STAGE026-P4-GATE"',
            'next_gate: "IDS-STAGE027-P1-GATE"',
            'next_gate: "IDS-STAGE027-P2-GATE"',
            'next_gate: "IDS-STAGE027-P3-GATE"',
            'next_gate: "IDS-STAGE027-P4-GATE"',
            'next_gate: "IDS-STAGE028-P1-GATE"',
            'next_gate: "IDS-STAGE028-P2-GATE"',
            'next_gate: "IDS-STAGE028-P3-GATE"',
            'next_gate: "IDS-STAGE028-P4-GATE"',
            'next_gate: "IDS-STAGE029-P1-GATE"',
            'next_gate: "IDS-STAGE029-P2-GATE"',
            'next_gate: "IDS-STAGE029-P3-GATE"',
            'next_gate: "IDS-STAGE029-P4-GATE"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'next_gate: "IDS-STAGE030-P4-GATE"',
        ]
        allowed_next_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
        ]
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)
        self.assertTrue(any(term in text for term in allowed_next_phase_terms), allowed_next_phase_terms)
        self.assertTrue(any(term in text for term in allowed_task_terms), allowed_task_terms)
        self.assertTrue(any(term in text for term in allowed_acceptance_terms), allowed_acceptance_terms)
        self.assertTrue(any(term in text for term in allowed_gate_terms), allowed_gate_terms)
        self.assertTrue(any(term in text for term in allowed_next_terms), allowed_next_terms)

    def test_phase3_scenario_report_validates_manifest_cases_reingest_cleanup_and_no_runtime_output(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            report = module.build_stage026_scenario_report(
                scenario_archives=self._phase3_scenario_archives(base),
                evaluated_at=MANIFESTED_AT,
            )

        self.assertEqual(report["schema_version"], "ids.stage026.archive_manifest.scenario_validation.v1")
        self.assertEqual(report["stage"], "STAGE-026")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE026-P3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-026")
        self.assertEqual(report["archive_manifest_schema"], "ids.stage026.archive_manifest.v1")
        self.assertEqual(report["validation_state"], "ARCHIVE_MANIFEST_SCENARIO_VALIDATION_PASSED")
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
            "path_traversal": "ARCHIVE_MANIFEST_PATH_TRAVERSAL_BLOCKED",
            "absolute_path": "ARCHIVE_MANIFEST_ABSOLUTE_PATH_BLOCKED",
            "archive_bomb": "ARCHIVE_MANIFEST_TOTAL_SIZE_LIMIT_EXCEEDED",
            "nested_archive": "ARCHIVE_MANIFEST_NESTED_DEPTH_LIMIT_EXCEEDED",
            "garbled_filename": "ARCHIVE_MANIFEST_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "too_many_files": "ARCHIVE_MANIFEST_FILE_COUNT_LIMIT_EXCEEDED",
        }
        by_id = {item["scenario_id"]: item for item in report["scenario_results"]}
        self.assertEqual(set(by_id), set(expected_risks))
        for scenario_id, risk_code in expected_risks.items():
            with self.subTest(scenario_id=scenario_id):
                result = by_id[scenario_id]
                self.assertEqual(result["scenario_state"], "ARCHIVE_MANIFEST_SCENARIO_VALIDATED")
                self.assertEqual(result["expected_risk_code"], risk_code)
                self.assertTrue(result["expected_risk_observed"])
                self.assertIn(risk_code, result["risk_codes"])
                self.assertEqual(result["archive_manifest_report"]["schema_version"], "ids.stage026.archive_manifest.v1")

        reingest_validation = report["reingest_validation"]
        self.assertEqual(reingest_validation["state"], "POST_EXTRACT_REINGEST_VALIDATED")
        self.assertEqual(reingest_validation["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertGreaterEqual(reingest_validation["safe_extracted_file_count"], 1)
        self.assertEqual(reingest_validation["actual_jobs_started"], {"hash": 0, "manifest": 0, "dedup": 0, "parser": 0})

        cleanup_validation = report["cleanup_validation"]
        self.assertEqual(cleanup_validation["state"], "ARCHIVE_MANIFEST_CLEANUP_ALLOWLIST_VALIDATED")
        self.assertTrue(cleanup_validation["cleanup_targets_are_staging_temp_files_only"])
        self.assertFalse(cleanup_validation["original_archive_in_cleanup_allowlist"])
        self.assertTrue(cleanup_validation["protected_refs_preserved"])
        for value in report["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in report["no_persistence_deltas"].values():
            self.assertEqual(value, 0)
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])
        self.assertTrue(report["does_not_start_processing_jobs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_phase3_evidence_document_records_scenarios_reingest_cleanup_raw_boundary_and_no_phase4(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")
        required_terms = [
            "IDS-V0_1-STAGE026-P3",
            "ACC-STAGE-026",
            "ids.stage026.archive_manifest.scenario_validation.v1",
            "build_stage026_scenario_report",
            "路径穿越",
            "绝对路径",
            "压缩炸弹",
            "嵌套包",
            "乱码文件名",
            "超大文件数",
            "ARCHIVE_MANIFEST_PATH_TRAVERSAL_BLOCKED",
            "ARCHIVE_MANIFEST_ABSOLUTE_PATH_BLOCKED",
            "ARCHIVE_MANIFEST_TOTAL_SIZE_LIMIT_EXCEEDED",
            "ARCHIVE_MANIFEST_NESTED_DEPTH_LIMIT_EXCEEDED",
            "ARCHIVE_MANIFEST_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_MANIFEST_FILE_COUNT_LIMIT_EXCEEDED",
            "POST_EXTRACT_REINGEST_VALIDATED",
            "ARCHIVE_MANIFEST_CLEANUP_ALLOWLIST_VALIDATED",
            "process-owned temporary structural archive fixtures",
            "不是 IDS corpus、database rows、business evidence、raw metadata 或 committed user data",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE4",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_current_stage026_phase3_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")
        required_terms = [
            "STAGE-026:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            'acceptance_id: "ACC-STAGE-026"',
            'push_allowed: false',
            "KM_IDSystem/scripts/check_archive_manifest.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        allowed_status_terms = [
            'status: "stage026_phase3_in_progress"',
            'status: "completed_local"',
            'status: "stage027_phase1_in_progress"',
            'status: "stage027_completed_local_pending_stage028"',
            'status: "stage028_phase1_in_progress"',
            'status: "stage028_phase2_in_progress"',
            'status: "stage028_phase3_in_progress"',
            'status: "stage028_completed_local_pending_stage029"',
            'status: "stage029_phase1_in_progress"',
            'status: "stage029_phase2_in_progress"',
            'status: "stage029_phase3_in_progress"',
            'status: "stage029_completed_local_pending_stage030"',
            'status: "stage030_phase1_in_progress"',
            'status: "stage030_phase2_in_progress"',
            'status: "stage030_phase3_in_progress"',
        ]
        allowed_next_phase_terms = [
            'next_phase: "Phase 4"',
            'next_stage: "STAGE-027"',
            'next_stage: "STAGE-028"',
            'next_phase: "Phase 2"',
        ]
        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE026-P3"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P4"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'current_task_id: "IDS-V0_1-STAGE028-P2"',
            'current_task_id: "IDS-V0_1-STAGE028-P3"',
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
        ]
        allowed_acceptance_terms = [
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        allowed_gate_terms = [
            'next_gate: "IDS-STAGE026-P4-GATE"',
            'next_gate: "IDS-STAGE027-P1-GATE"',
            'next_gate: "IDS-STAGE027-P2-GATE"',
            'next_gate: "IDS-STAGE027-P3-GATE"',
            'next_gate: "IDS-STAGE027-P4-GATE"',
            'next_gate: "IDS-STAGE028-P1-GATE"',
            'next_gate: "IDS-STAGE028-P2-GATE"',
            'next_gate: "IDS-STAGE028-P3-GATE"',
            'next_gate: "IDS-STAGE028-P4-GATE"',
            'next_gate: "IDS-STAGE029-P1-GATE"',
            'next_gate: "IDS-STAGE029-P2-GATE"',
            'next_gate: "IDS-STAGE029-P3-GATE"',
            'next_gate: "IDS-STAGE029-P4-GATE"',
            'next_gate: "IDS-STAGE030-P1-GATE"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'next_gate: "IDS-STAGE030-P4-GATE"',
        ]
        allowed_next_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
        ]
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)
        self.assertTrue(any(term in text for term in allowed_next_phase_terms), allowed_next_phase_terms)
        self.assertTrue(any(term in text for term in allowed_task_terms), allowed_task_terms)
        self.assertTrue(any(term in text for term in allowed_acceptance_terms), allowed_acceptance_terms)
        self.assertTrue(any(term in text for term in allowed_gate_terms), allowed_gate_terms)
        self.assertTrue(any(term in text for term in allowed_next_terms), allowed_next_terms)

    def test_phase4_closeout_records_whole_stage_review_raw_boundary_rollback_and_no_upload(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")
        required_terms = [
            "IDS-V0_1-STAGE026-P4",
            "ACC-STAGE-026",
            "压缩包 Manifest",
            "Whole-Stage Review",
            "passed_with_local_evidence",
            "Phase 1",
            "Phase 2",
            "Phase 3",
            "Phase 4",
            "build_archive_manifest",
            "build_stage026_scenario_report",
            "ARCHIVE_MANIFEST_SCENARIO_VALIDATION_PASSED",
            "POST_EXTRACT_REINGEST_VALIDATED",
            "ARCHIVE_MANIFEST_CLEANUP_ALLOWLIST_VALIDATED",
            "rollback",
            "中文 owner feedback",
            "push_allowed=false",
            "No GitHub upload",
            "No app reinstall",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不写 archive_manifest runtime output",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、index、import",
            "NO_STAGE027",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_completed_stage026_phase4_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")
        required_terms = [
            'status: "completed_local"',
            "STAGE-026:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'next_stage: "STAGE-027"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            'acceptance_id: "ACC-STAGE-026"',
            'acceptance_status: "local_passed"',
            'next_gate: "IDS-STAGE027-P1-GATE"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        allowed_next_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P4"',
        ]
        self.assertTrue(any(term in text for term in allowed_next_terms), allowed_next_terms)

    def test_roadmap_and_events_track_stage026_phase4_closeout_without_batch_upload(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        roadmap_terms = [
            'status: "completed"',
            'status: "passed_with_local_evidence"',
            'phase_id: "IDS-STAGE026-P4"',
            "STAGE026_PHASE4_CLOSEOUT.md",
            "No GitHub upload",
            "No app reinstall",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE026-P4-20260703-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE026-P4"',
            '"ACC-STAGE-026"',
            "STAGE026_PHASE4_CLOSEOUT.md",
        ]
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        allowed_current_terms = [
            'current_stage_id: "IDS-STAGE026"',
            'current_stage_id: "IDS-STAGE027"',
            'current_stage_id: "IDS-STAGE028"',
            'current_stage_id: "IDS-STAGE029"',
            'current_stage_id: "IDS-STAGE030"',
            'current_phase_id: "IDS-STAGE026-P4"',
            'current_phase_id: "IDS-STAGE027-P1"',
            'current_phase_id: "IDS-STAGE027-P2"',
            'current_phase_id: "IDS-STAGE027-P3"',
            'current_phase_id: "IDS-STAGE027-P4"',
            'current_phase_id: "IDS-STAGE028-P1"',
            'current_phase_id: "IDS-STAGE028-P2"',
            'current_phase_id: "IDS-STAGE028-P3"',
            'current_phase_id: "IDS-STAGE028-P4"',
            'current_phase_id: "IDS-STAGE029-P1"',
            'current_phase_id: "IDS-STAGE029-P2"',
            'current_phase_id: "IDS-STAGE029-P3"',
            'current_phase_id: "IDS-STAGE029-P4"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_phase_id: "IDS-STAGE030-P3"',
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P2"',
            'current_task_id: "IDS-V0_1-STAGE027-P3"',
            'current_task_id: "IDS-V0_1-STAGE027-P4"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'current_task_id: "IDS-V0_1-STAGE028-P2"',
            'current_task_id: "IDS-V0_1-STAGE028-P3"',
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P2"',
            'current_task_id: "IDS-V0_1-STAGE029-P3"',
            'current_task_id: "IDS-V0_1-STAGE029-P4"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P3"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_gate_id: "IDS-STAGE027-P1-GATE"',
            'next_gate_id: "IDS-STAGE027-P2-GATE"',
            'next_gate_id: "IDS-STAGE027-P3-GATE"',
            'next_gate_id: "IDS-STAGE027-P4-GATE"',
            'next_gate_id: "IDS-STAGE028-P1-GATE"',
            'next_gate_id: "IDS-STAGE028-P2-GATE"',
            'next_gate_id: "IDS-STAGE028-P3-GATE"',
            'next_gate_id: "IDS-STAGE028-P4-GATE"',
            'next_gate_id: "IDS-STAGE029-P1-GATE"',
            'next_gate_id: "IDS-STAGE029-P2-GATE"',
            'next_gate_id: "IDS-STAGE029-P3-GATE"',
            'next_gate_id: "IDS-STAGE029-P4-GATE"',
            'next_gate_id: "IDS-STAGE030-P1-GATE"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'next_gate_id: "IDS-STAGE030-P4-GATE"',
        ]
        allowed_stage_terms = [term for term in allowed_current_terms if term.startswith("current_stage_id")]
        allowed_phase_terms = [term for term in allowed_current_terms if term.startswith("current_phase_id")]
        allowed_task_terms = [term for term in allowed_current_terms if term.startswith("current_task_id")]
        allowed_gate_terms = [term for term in allowed_current_terms if term.startswith("next_gate_id")]
        self.assertTrue(any(term in roadmap_text for term in allowed_stage_terms), allowed_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_phase_terms), allowed_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_task_terms), allowed_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_gate_terms), allowed_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
