import copy
import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE034_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE034_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE034_PHASE2_DATA_RETENTION_TABLE_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE034_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE034_PHASE4_CLOSEOUT.md"
STAGE_REVIEW = PURSUE_ROOT / "STAGE034_STAGE_REVIEW.md"
INDEX = PURSUE_ROOT / "data_retention_table" / "stage034_data_retention_table_index.json"
SCRIPT = ROOT / "scripts" / "check_data_retention_table.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage034DataRetentionTablePhase1Tests(unittest.TestCase):
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
            "STAGE-034 · 数据保留表",
            "IDS-V0_1-STAGE034-P1",
            "ACC-STAGE-034",
            "D06-S005",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-034_数据保留表.md",
            "af3196bb6ce76bbf22888abbb8c178b3deb0570e6cd2e19235853bac649b818d",
            "定义临时文件、缓存、旧索引、日志、报告快照的保留策略字段",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_retention_inputs_outputs_states_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "data_retention_table_contract_id",
            "control_plane_schema_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "database_size_guard_ref",
            "retention_subject_class",
            "temp_file_retention_policy",
            "cache_retention_policy",
            "old_index_retention_policy",
            "log_retention_policy",
            "report_snapshot_retention_policy",
            "retention_ttl_policy",
            "owner_hold_policy",
            "cleanup_dry_run_requirement",
            "deletion_stop_gate",
            "audit_evidence_ref",
            "rollback_restore_ref",
            "DATA_RETENTION_TABLE_DRAFT",
            "DATA_RETENTION_TEMP_FILES_POLICY_DEFINED",
            "DATA_RETENTION_CACHES_POLICY_DEFINED",
            "DATA_RETENTION_OLD_INDEXES_POLICY_DEFINED",
            "DATA_RETENTION_LOGS_POLICY_DEFINED",
            "DATA_RETENTION_REPORT_SNAPSHOTS_POLICY_DEFINED",
            "DATA_RETENTION_CLEANUP_OWNER_CONFIRMATION_REQUIRED",
            "DATA_RETENTION_READY_FOR_PHASE2_SLICE",
            "临时文件",
            "缓存",
            "旧索引",
            "日志",
            "报告快照",
            "不执行删除",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_blocks_live_postgres_cleanup_raw_data_secrets_outputs_and_fake_data(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        required_terms = [
            "NO_PHASE2",
            "NO_POSTGRES_CONNECTION",
            "NO_RETENTION_CLEANUP_RUNTIME",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置、数据保留 runtime 或清理任务",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore、schema diff、清理、删除、retention 或恢复冒烟",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage034_phase1_without_upload(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            'batch_id: "IDS-V0_1-BATCH-031-040"',
            'stage_range: "STAGE-031..STAGE-040"',
            'acceptance_range: "ACC-STAGE-031..ACC-STAGE-040"',
            'push_allowed: false',
            "STAGE-034:",
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-034"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage034_data_retention_table.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]
        allowed_lock_current_terms = [
            'status: "stage034_phase1_in_progress"',
            'status: "stage034_phase2_in_progress"',
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_next_terms = [
            'next_phase: "Phase 2"',
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate: "IDS-STAGE035-P1-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'stage_id: "IDS-STAGE034"',
            'name: "STAGE-034 · 数据保留表"',
            'phase_id: "IDS-STAGE034-P1"',
            'task_id: "IDS-V0_1-STAGE034-P1"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
            'current_phase_id: "IDS-STAGE034-REVIEW"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE035-P1-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE034-P1-20260704-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE034-P1"',
            '"ACC-STAGE-034"',
            "STAGE034_PHASE1_SCOPE_BOUNDARY.md",
            "数据保留表",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE034-P1"', lock_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_next_terms), allowed_lock_next_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(
            any(term in lock_text for term in allowed_acceptance_status_terms),
            allowed_acceptance_status_terms,
        )
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage034DataRetentionTablePhase2Tests(unittest.TestCase):
    def test_phase2_static_retention_artifacts_exist(self):
        for path in [PHASE2, INDEX, SCRIPT]:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"missing Phase 2 artifact: {path}")

        combined = "\n".join(
            [
                PHASE2.read_text(encoding="utf-8"),
                INDEX.read_text(encoding="utf-8"),
                SCRIPT.read_text(encoding="utf-8"),
            ]
        )
        required_terms = [
            "ids.stage034.data_retention_table.phase2.v1",
            "ids.stage034.data_retention_table.index.v1",
            "IDS-V0_1-STAGE034-P2",
            "ACC-STAGE-034",
            "D06-S005",
            "Phase 2 · 静态数据保留表切片",
            "STAGE034_PHASE1_SCOPE_BOUNDARY.md",
            "stage033_database_size_guard_index.json",
            "临时文件",
            "缓存",
            "旧索引",
            "日志",
            "报告快照",
            "NO_POSTGRES_CONNECTION",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase2_index_records_subjects_ttl_hold_audit_and_recovery_guards(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(index["schema_version"], "ids.stage034.data_retention_table.index.v1")
        self.assertEqual(index["task_id"], "IDS-V0_1-STAGE034-P2")
        self.assertEqual(index["acceptance_id"], "ACC-STAGE-034")
        self.assertEqual(index["data_retention_table_contract_id"], "ids_stage034_data_retention_table_static_slice")

        subjects = index["retention_subjects"]
        expected_subjects = ["temporary_file", "cache", "old_index", "log", "report_snapshot"]
        self.assertEqual(sorted(expected_subjects), sorted(subjects))
        for subject_id in expected_subjects:
            with self.subTest(subject_id=subject_id):
                subject = subjects[subject_id]
                self.assertTrue(subject["owner_label_zh"])
                self.assertIn("ttl_policy", subject)
                self.assertIn("owner_hold_policy", subject)
                self.assertIn("cleanup_mode", subject)
                self.assertFalse(subject["stores_raw_content"])

        guardrails = index["guardrails"]
        required_guardrails = [
            "retention_subject_class_guard",
            "ttl_policy_guard",
            "owner_hold_guard",
            "cleanup_dry_run_guard",
            "deletion_stop_gate_guard",
            "audit_evidence_guard",
            "rollback_restore_guard",
            "postgres_storage_scope_guard",
            "database_size_guard_dependency",
            "connection_pool_budget_guard",
            "raw_metadata_boundary",
            "real_data_only_guard",
        ]
        for key in required_guardrails:
            with self.subTest(key=key):
                self.assertIn(key, guardrails)

        cleanup = guardrails["cleanup_dry_run_guard"]
        self.assertEqual(cleanup["cleanup_default_mode"], "dry_run_only")
        self.assertFalse(cleanup["runtime_cleanup_allowed"])
        self.assertFalse(cleanup["auto_delete_allowed"])
        self.assertTrue(cleanup["owner_impact_report_required"])

        deletion = guardrails["deletion_stop_gate_guard"]
        self.assertTrue(deletion["owner_stop_gate_required"])
        self.assertFalse(deletion["destructive_action_allowed_by_default"])
        self.assertFalse(deletion["report_snapshot_pruning_allowed"])
        self.assertFalse(deletion["log_compaction_allowed"])
        self.assertFalse(deletion["cache_eviction_allowed"])

        raw_boundary = guardrails["raw_metadata_boundary"]
        self.assertEqual(raw_boundary["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(raw_boundary["path_only"])
        self.assertFalse(raw_boundary["content_access_allowed"])
        self.assertFalse(raw_boundary["recursive_listing_allowed"])
        self.assertFalse(raw_boundary["hashing_allowed"])
        self.assertFalse(raw_boundary["copy_allowed"])
        self.assertFalse(raw_boundary["modify_allowed"])
        self.assertFalse(raw_boundary["delete_allowed"])
        self.assertFalse(raw_boundary["dump_allowed"])
        self.assertFalse(raw_boundary["scan_allowed"])
        self.assertFalse(raw_boundary["normalize_allowed"])

        forbidden = guardrails["real_data_only_guard"]["forbidden"]
        for term in [
            "fake IDS business data",
            "fake database rows",
            "fake source documents",
            "placeholder corpus",
            "fabricated evidence",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, forbidden)

    def test_phase2_checker_outputs_static_report_without_postgres_raw_data_or_runtime_writes(self):
        result = subprocess.run(
            [sys.executable, "-B", SCRIPT.as_posix()],
            cwd=ROOT.as_posix(),
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(result.stdout)
        report = payload["data_retention_table_report"]

        self.assertEqual(report["schema_version"], "ids.stage034.data_retention_table.phase2.v1")
        self.assertEqual(report["index_schema_version"], "ids.stage034.data_retention_table.index.v1")
        self.assertEqual(report["stage"], "STAGE-034")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE034-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-034")
        self.assertTrue(all(report["guardrail_results"].values()))
        self.assertTrue(all(report["runtime_policy_results"].values()))
        self.assertEqual(report["raw_metadata_boundary"]["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(report["raw_metadata_boundary"]["path_only"])
        self.assertTrue(report["raw_metadata_boundary"]["no_raw_content_access"])
        self.assertEqual(
            sorted(["temporary_file", "cache", "old_index", "log", "report_snapshot"]),
            sorted(report["retention_subjects"]),
        )
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])
        self.assertTrue(report["does_not_execute_cleanup"])
        self.assertTrue(report["does_not_execute_deletion"])

    def test_phase2_doc_batch_roadmap_and_event_track_local_no_upload_gate(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 document: {PHASE2}")
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        phase2_text = PHASE2.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        for term in [
            "静态数据保留表切片",
            "retention_subject_class_guard",
            "cleanup_dry_run_guard",
            "deletion_stop_gate_guard",
            "audit_evidence_guard",
            "rollback_restore_guard",
            "check_data_retention_table.py",
            "stage034_data_retention_table_index.json",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)

        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE2_DATA_RETENTION_TABLE_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json",
            "KM_IDSystem/scripts/check_data_retention_table.py",
            'push_allowed: false',
        ]
        allowed_lock_current_terms = [
            'status: "stage034_phase2_in_progress"',
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_next_terms = [
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate: "IDS-STAGE035-P1-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'phase_id: "IDS-STAGE034-P2"',
            'task_id: "IDS-V0_1-STAGE034-P2"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
            'current_phase_id: "IDS-STAGE034-REVIEW"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE035-P1-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE034-P2-20260704-001"',
            '"event_type":"stage_slice"',
            '"task_id":"IDS-V0_1-STAGE034-P2"',
            '"ACC-STAGE-034"',
            "STAGE034_PHASE2_DATA_RETENTION_TABLE_SLICE.md",
            "stage034_data_retention_table_index.json",
            "check_data_retention_table.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE034-P2"', lock_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_next_terms), allowed_lock_next_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(
            any(term in lock_text for term in allowed_acceptance_status_terms),
            allowed_acceptance_status_terms,
        )
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage034DataRetentionTablePhase3Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage034_data_retention_table", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase3_scenario_report_validates_retention_migration_raw_pool_and_constraints(self):
        module = self._load_checker_module()
        self.assertTrue(INDEX.is_file(), f"missing data retention index: {INDEX}")

        report = module.build_stage034_scenario_validation_report(INDEX)

        self.assertEqual("ids.stage034.data_retention_table.phase3.v1", report["schema_version"])
        self.assertEqual("STAGE-034", report["stage"])
        self.assertEqual("Phase 3", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE034-P3", report["task_id"])
        self.assertEqual("ACC-STAGE-034", report["acceptance_id"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])
        self.assertTrue(report["does_not_execute_cleanup"])
        self.assertTrue(report["does_not_execute_deletion"])

        scenario_results = report["scenario_results"]
        expected_scenarios = [
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "recovery_smoke",
            "raw_payload_block",
            "unbounded_derived_artifact_block",
            "retention_subject_validation",
            "ttl_owner_hold_policy",
            "cleanup_dry_run",
            "deletion_stop_gate",
            "connection_pool_boundary",
            "transaction_boundary",
            "constraint_error_explanations",
        ]
        self.assertEqual(sorted(expected_scenarios), sorted(scenario_results))
        for scenario_id, result in scenario_results.items():
            with self.subTest(scenario_id=scenario_id):
                self.assertEqual("PASS", result["status"])
                self.assertTrue(result["evidence"])
                self.assertTrue(result["owner_explanation"])

        explanations = scenario_results["constraint_error_explanations"]["explanations"]
        for constraint_id in [
            "retention_subject_class_guard",
            "ttl_policy_guard",
            "owner_hold_guard",
            "cleanup_dry_run_guard",
            "deletion_stop_gate_guard",
            "audit_evidence_guard",
            "rollback_restore_guard",
            "postgres_storage_scope_guard",
            "database_size_guard_dependency",
            "connection_pool_budget_guard",
            "raw_metadata_boundary_guard",
            "real_data_only_guard",
        ]:
            with self.subTest(constraint_id=constraint_id):
                self.assertIn(constraint_id, explanations)

    def test_phase3_doc_covers_static_scenarios_and_blocks_live_side_effects(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")

        required_terms = [
            "ids.stage034.data_retention_table.phase3.v1",
            "IDS-V0_1-STAGE034-P3",
            "ACC-STAGE-034",
            "build_stage034_scenario_validation_report",
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "recovery_smoke",
            "raw_payload_block",
            "unbounded_derived_artifact_block",
            "retention_subject_validation",
            "ttl_owner_hold_policy",
            "cleanup_dry_run",
            "deletion_stop_gate",
            "connection_pool_boundary",
            "transaction_boundary",
            "constraint_error_explanations",
            "不连接 PostgreSQL",
            "不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不执行 retention scan、cleanup、deletion、log compaction、cache eviction、old-index rebuild 或 report snapshot pruning",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
            "NO_PHASE4",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase3_batch_roadmap_and_event_track_local_no_upload_gate(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/scripts/check_data_retention_table.py",
            'push_allowed: false',
        ]
        allowed_lock_current_terms = [
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate: "IDS-STAGE035-P1-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
            'phase_id: "IDS-STAGE034-P3"',
            'task_id: "IDS-V0_1-STAGE034-P3"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE034-P3-20260710-001"',
            '"event_type":"validation"',
            '"task_id":"IDS-V0_1-STAGE034-P3"',
            '"ACC-STAGE-034"',
            "STAGE034_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage034_scenario_validation_report",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE034-P3"', lock_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(
            any(term in lock_text for term in allowed_acceptance_status_terms),
            allowed_acceptance_status_terms,
        )
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage034DataRetentionTablePhase4Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage034_data_retention_table", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase4_delivery_report_closes_static_evidence_without_live_side_effects(self):
        module = self._load_checker_module()
        self.assertTrue(INDEX.is_file(), f"missing data retention index: {INDEX}")

        report = module.build_stage034_delivery_report(INDEX)

        self.assertEqual("ids.stage034.data_retention_table.phase4.v1", report["schema_version"])
        self.assertEqual("STAGE-034", report["stage"])
        self.assertEqual("Phase 4", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE034-P4", report["task_id"])
        self.assertEqual("ACC-STAGE-034", report["acceptance_id"])
        self.assertEqual("IDS-STAGE034-REVIEW-GATE", report["next_gate"])
        self.assertEqual("pending_next_run", report["stage_review_status"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

        for key in [
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "known_limits",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "chinese_owner_feedback",
            "phase2_report",
            "scenario_report",
        ]:
            with self.subTest(key=key):
                self.assertIn(key, report)
                self.assertTrue(report[key])

        self.assertEqual(
            "static_data_retention_table_contract_diff_not_executed",
            report["schema_diff"]["mode"],
        )
        self.assertEqual(
            "static_data_retention_table_migration_output_not_executed",
            report["migration_output"]["mode"],
        )
        self.assertEqual(
            "static_data_retention_table_recovery_log_not_executed",
            report["recovery_test_log"]["mode"],
        )
        self.assertEqual(
            "PASS",
            report["migration_output"]["scenario_results"]["constraint_error_explanations"]["status"],
        )

        confirmation = report["destructive_migration_confirmation"]
        self.assertTrue(confirmation["required"])
        self.assertFalse(confirmation["current_contract_value"])
        self.assertTrue(confirmation["manual_confirmation_required_before_change"])

        for key in [
            "does_not_connect_to_postgres",
            "does_not_execute_migration",
            "does_not_read_raw_metadata",
            "does_not_write_runtime_outputs",
            "does_not_use_fake_ids_business_data",
            "does_not_execute_cleanup",
            "does_not_execute_deletion",
            "does_not_execute_log_compaction",
            "does_not_execute_cache_eviction",
            "does_not_execute_index_rebuild",
            "does_not_execute_report_snapshot_pruning",
        ]:
            with self.subTest(key=key):
                self.assertTrue(report[key])

    def test_phase4_doc_covers_closeout_delivery_review_boundary_and_raw_data_policy(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 evidence: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "ids.stage034.data_retention_table.phase4.v1",
            "IDS-V0_1-STAGE034-P4",
            "ACC-STAGE-034",
            "build_stage034_delivery_report",
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "known_limits",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "chinese_owner_feedback",
            "IDS-STAGE034-REVIEW-GATE",
            "NO_BATCH_UPLOAD",
            "NO_STAGE_REVIEW_THIS_RUN",
            "NO_GITHUB_UPLOAD",
            "不连接 PostgreSQL",
            "不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不执行 retention scan、cleanup、deletion、log compaction、cache eviction、old-index rebuild 或 report snapshot pruning",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase4_batch_roadmap_and_event_track_review_gate_no_upload(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 evidence: {PHASE4}")
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_data_retention_table.py",
            'push_allowed: false',
        ]
        allowed_lock_status_terms = [
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate: "IDS-STAGE035-P1-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'current_phase_id: "IDS-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
            'phase_id: "IDS-STAGE034-P4"',
            'task_id: "IDS-V0_1-STAGE034-P4"',
            'status: "passed_no_github_upload_until_stage_review"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE034-P4-20260710-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE034-P4"',
            '"ACC-STAGE-034"',
            "STAGE034_PHASE4_CLOSEOUT.md",
            "build_stage034_delivery_report",
            "IDS-STAGE034-REVIEW-GATE",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE034-P4"', lock_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_status_terms), allowed_lock_status_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(
            any(term in lock_text for term in allowed_acceptance_status_terms),
            allowed_acceptance_status_terms,
        )
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage034DataRetentionTableReviewTests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage034_data_retention_table", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_review_repair_rejects_contradictory_safety_and_recovery_evidence(self):
        module = self._load_checker_module()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        index["runtime_policy"]["connect_to_postgres"] = True
        index["runtime_policy"]["execute_cleanup"] = True
        index["guardrails"]["cleanup_dry_run_guard"]["auto_delete_allowed"] = True

        original_loader = module._load_json
        module._load_json = lambda _path: copy.deepcopy(index)
        try:
            phase2_report = module.build_stage034_data_retention_table_report(Path("memory-only.json"))
            scenario_report = module.build_stage034_scenario_validation_report(Path("memory-only.json"))
            delivery_report = module.build_stage034_delivery_report(Path("memory-only.json"))
        finally:
            module._load_json = original_loader

        self.assertFalse(phase2_report["does_not_connect_to_postgres"])
        self.assertFalse(phase2_report["does_not_execute_cleanup"])
        self.assertFalse(scenario_report["does_not_connect_to_postgres"])
        self.assertFalse(scenario_report["does_not_execute_cleanup"])
        self.assertEqual("FAIL", scenario_report["scenario_results"]["cleanup_dry_run"]["status"])
        self.assertFalse(delivery_report["contract_valid"])
        self.assertEqual("FAIL", delivery_report["recovery_test_log"]["result"])
        self.assertFalse(delivery_report["recovery_test_log"]["check_results"]["cleanup_default_mode_dry_run_only"])
        self.assertFalse(delivery_report["does_not_connect_to_postgres"])
        self.assertFalse(delivery_report["does_not_execute_cleanup"])

    def test_stage_review_artifact_records_findings_repairs_and_no_upload_boundary(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        review_text = STAGE_REVIEW.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE034-REVIEW",
            "ACC-STAGE-034",
            "STAGE-034 · 数据保留表",
            "STAGE034-REVIEW-F1",
            "STAGE034-REVIEW-F2",
            "STAGE034-REVIEW-F3",
            "STAGE034-REVIEW-F4",
            "P0 source binding",
            "Phase 1 boundary",
            "Phase 2 data retention table",
            "Phase 3 scenario validation",
            "Phase 4 closeout",
            "build_stage034_delivery_report",
            "contract_valid",
            "recovery_test_log",
            "completed_reviewed_local",
            "IDS-STAGE035-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE035_THIS_RUN",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, review_text)

    def test_stage_review_gate_batch_roadmap_and_event_track_reviewed_local_no_upload(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            'STAGE-034:',
            'status: "completed_reviewed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'review_status: "passed"',
            'next_stage: "STAGE-035"',
            'next_gate: "IDS-STAGE035-P1-GATE"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
            'acceptance_status: "reviewed_local_passed"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_STAGE_REVIEW.md",
            'push_allowed: false',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'current_phase_id: "IDS-STAGE034-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
            'next_gate_id: "IDS-STAGE035-P1-GATE"',
            'review_id: "IDS-STAGE034-REVIEW"',
            'task_id: "IDS-V0_1-STAGE034-REVIEW"',
            'status: "completed"',
            "STAGE034_STAGE_REVIEW.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE034-REVIEW-20260710-001"',
            '"event_type":"stage_review"',
            '"task_id":"IDS-V0_1-STAGE034-REVIEW"',
            '"ACC-STAGE-034"',
            "STAGE034_STAGE_REVIEW.md",
            "IDS-STAGE035-P1-GATE",
        ]

        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
