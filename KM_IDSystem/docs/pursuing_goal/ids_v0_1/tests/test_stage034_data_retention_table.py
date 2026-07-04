import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE034_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE034_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE034_PHASE2_DATA_RETENTION_TABLE_SLICE.md"
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
        ]
        allowed_lock_next_terms = [
            'next_phase: "Phase 2"',
            'next_phase: "Phase 3"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
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
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
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
            'status: "stage034_phase2_in_progress"',
            'next_phase: "Phase 3"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'push_allowed: false',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'phase_id: "IDS-STAGE034-P2"',
            'task_id: "IDS-V0_1-STAGE034-P2"',
            'status: "passed_with_local_evidence"',
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
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
