import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE033_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE033_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE033_PHASE2_DATABASE_SIZE_GUARD_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE033_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE033_PHASE4_CLOSEOUT.md"
STAGE_REVIEW = PURSUE_ROOT / "STAGE033_STAGE_REVIEW.md"
INDEX = PURSUE_ROOT / "database_size_guard" / "stage033_database_size_guard_index.json"
SCRIPT = ROOT / "scripts" / "check_database_size_guard.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage033DatabaseSizeGuardPhase1Tests(unittest.TestCase):
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
            "STAGE-033 · 数据库体积护栏",
            "IDS-V0_1-STAGE033-P1",
            "ACC-STAGE-033",
            "D06-S004",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md",
            "454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777",
            "防止 PostgreSQL 无边界存 raw/OCR/大文件派生产物，保护 800GB 内置盘",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_size_guard_inputs_outputs_boundaries_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "database_size_guard_contract_id",
            "control_plane_schema_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "postgres_storage_scope",
            "raw_content_storage_block",
            "ocr_full_text_storage_block",
            "large_file_storage_block",
            "derived_artifact_limit",
            "database_size_budget",
            "table_size_guard",
            "index_bloat_guard",
            "row_payload_guard",
            "retention_and_cleanup_boundary",
            "audit_evidence_ref",
            "rollback_verification_requirement",
            "DATABASE_SIZE_GUARD_DRAFT",
            "DATABASE_SIZE_GUARD_RAW_CONTENT_BLOCKED",
            "DATABASE_SIZE_GUARD_DERIVED_ARTIFACT_BLOCKED",
            "DATABASE_SIZE_GUARD_READY_FOR_PHASE2_SLICE",
            "只存控制面、状态和热索引",
            "不存 500GB 原始文件",
            "不存 OCR 全文",
            "不存无限制派生产物",
            "保护 800GB 内置盘",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_blocks_live_postgres_raw_data_secrets_runtime_outputs_and_fake_data(self):
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
            "NO_SIZE_GUARD_RUNTIME",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置、体积统计 runtime 或清理任务",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore、schema diff、VACUUM、清理或体积统计查询",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage033_phase1_without_upload(self):
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
            "STAGE-033:",
            '      - "Phase 1"',
        ]
        allowed_lock_current_terms = [
            'status: "stage033_phase1_in_progress"',
            'status: "stage033_phase2_in_progress"',
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
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
            'next_gate: "IDS-STAGE033-P2-GATE"',
            'next_gate: "IDS-STAGE033-P3-GATE"',
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        typo_guard_terms = [
            'acceptance_id: "ACC-STAGE-033"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_database_size_guard.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase2_size_guard_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE033"',
            'stage_id: "IDS-STAGE033"',
            'name: "STAGE-033 · 数据库体积护栏"',
            'phase_id: "IDS-STAGE033-P1"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE033-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE033-P1"',
            '"ACC-STAGE-033"',
            "STAGE033_PHASE1_SCOPE_BOUNDARY.md",
            "数据库体积护栏",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE033-P1"', lock_text)
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
        for term in typo_guard_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage033DatabaseSizeGuardPhase3Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage033_database_size_guard", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase3_scenario_report_validates_migration_raw_size_pool_and_constraints(self):
        module = self._load_checker_module()
        self.assertTrue(INDEX.is_file(), f"missing size guard index: {INDEX}")

        report = module.build_stage033_scenario_validation_report(INDEX)

        self.assertEqual("ids.stage033.database_size_guard.phase3.v1", report["schema_version"])
        self.assertEqual("STAGE-033", report["stage"])
        self.assertEqual("Phase 3", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE033-P3", report["task_id"])
        self.assertEqual("ACC-STAGE-033", report["acceptance_id"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])
        self.assertTrue(report["does_not_run_size_queries"])
        self.assertTrue(report["does_not_execute_cleanup"])

        scenario_results = report["scenario_results"]
        expected_scenarios = [
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "recovery_smoke",
            "raw_large_file_block",
            "ocr_full_text_block",
            "derived_artifact_limit",
            "database_size_budget",
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
            "postgres_storage_scope_guard",
            "database_size_budget_guard",
            "row_payload_guard",
            "retention_cleanup_guard",
            "connection_pool_budget_guard",
            "rollback_verification_guard",
            "raw_metadata_boundary_guard",
            "real_data_only_guard",
        ]:
            with self.subTest(constraint_id=constraint_id):
                self.assertIn(constraint_id, explanations)

    def test_phase3_doc_covers_static_scenarios_and_blocks_live_side_effects(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")

        required_terms = [
            "ids.stage033.database_size_guard.phase3.v1",
            "IDS-V0_1-STAGE033-P3",
            "ACC-STAGE-033",
            "build_stage033_scenario_validation_report",
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "recovery_smoke",
            "raw_large_file_block",
            "ocr_full_text_block",
            "derived_artifact_limit",
            "database_size_budget",
            "connection_pool_boundary",
            "transaction_boundary",
            "constraint_error_explanations",
            "不连接 PostgreSQL",
            "不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不运行 size query、VACUUM、reindex、cleanup 或 retention deletion",
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
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/scripts/check_database_size_guard.py",
            'push_allowed: false',
        ]
        allowed_lock_current_terms = [
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
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
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE033"',
            'phase_id: "IDS-STAGE033-P3"',
            'task_id: "IDS-V0_1-STAGE033-P3"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE033-P3-20260703-001"',
            '"event_type":"validation"',
            '"task_id":"IDS-V0_1-STAGE033-P3"',
            '"ACC-STAGE-033"',
            "STAGE033_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage033_scenario_validation_report",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE033-P3"', lock_text)
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
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage033DatabaseSizeGuardPhase4Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage033_database_size_guard", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase4_delivery_report_closes_static_evidence_without_live_side_effects(self):
        module = self._load_checker_module()
        self.assertTrue(INDEX.is_file(), f"missing size guard index: {INDEX}")

        report = module.build_stage033_delivery_report(INDEX)

        self.assertEqual("ids.stage033.database_size_guard.phase4.v1", report["schema_version"])
        self.assertEqual("STAGE-033", report["stage"])
        self.assertEqual("Phase 4", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE033-P4", report["task_id"])
        self.assertEqual("ACC-STAGE-033", report["acceptance_id"])
        self.assertEqual("IDS-STAGE033-REVIEW-GATE", report["next_gate"])
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
            "static_database_size_guard_contract_diff_not_executed",
            report["schema_diff"]["mode"],
        )
        self.assertEqual(
            "static_database_size_guard_migration_output_not_executed",
            report["migration_output"]["mode"],
        )
        self.assertEqual(
            "static_database_size_guard_recovery_log_not_executed",
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
            "does_not_run_size_queries",
            "does_not_execute_cleanup",
        ]:
            with self.subTest(key=key):
                self.assertTrue(report[key])

    def test_phase4_doc_covers_closeout_delivery_review_boundary_and_raw_data_policy(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 evidence: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "ids.stage033.database_size_guard.phase4.v1",
            "IDS-V0_1-STAGE033-P4",
            "ACC-STAGE-033",
            "build_stage033_delivery_report",
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "known_limits",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "chinese_owner_feedback",
            "IDS-STAGE033-REVIEW-GATE",
            "NO_BATCH_UPLOAD",
            "NO_STAGE_REVIEW_THIS_RUN",
            "NO_GITHUB_UPLOAD",
            "不连接 PostgreSQL",
            "不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不运行 size query、VACUUM、reindex、cleanup 或 retention deletion",
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
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_database_size_guard.py",
            'push_allowed: false',
        ]
        allowed_lock_status_terms = [
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
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
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE033"',
            'phase_id: "IDS-STAGE033-P4"',
            'task_id: "IDS-V0_1-STAGE033-P4"',
            'status: "passed_no_github_upload_until_stage_review"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE033-P4-20260703-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE033-P4"',
            '"ACC-STAGE-033"',
            "STAGE033_PHASE4_CLOSEOUT.md",
            "build_stage033_delivery_report",
            "IDS-STAGE033-REVIEW-GATE",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE033-P4"', lock_text)
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
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage033DatabaseSizeGuardReviewTests(unittest.TestCase):
    def test_stage_review_artifact_records_findings_repairs_and_no_upload_boundary(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        review_text = STAGE_REVIEW.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE033-REVIEW",
            "ACC-STAGE-033",
            "STAGE-033 · 数据库体积护栏",
            "STAGE033-REVIEW-F1",
            "STAGE033-REVIEW-F2",
            "STAGE033-REVIEW-F3",
            "STAGE033-REVIEW-F4",
            "P0 source binding",
            "Phase 1 boundary",
            "Phase 2 database size guard checker",
            "Phase 3 scenario validation",
            "Phase 4 closeout",
            "build_stage033_delivery_report",
            "completed_reviewed_local",
            "IDS-STAGE034-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE034_THIS_RUN",
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
            'STAGE-033:',
            'status: "completed_reviewed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'review_status: "passed"',
            'next_stage: "STAGE-034"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'acceptance_status: "reviewed_local_passed"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_STAGE_REVIEW.md",
            'push_allowed: false',
        ]
        allowed_lock_status_terms = [
            'status: "stage033_completed_reviewed_local"',
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
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE033"',
            'review_id: "IDS-STAGE033-REVIEW"',
            'task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'status: "completed"',
            "STAGE033_STAGE_REVIEW.md",
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE033-REVIEW-20260704-001"',
            '"event_type":"stage_review"',
            '"task_id":"IDS-V0_1-STAGE033-REVIEW"',
            '"ACC-STAGE-033"',
            "STAGE033_STAGE_REVIEW.md",
            "IDS-STAGE034-P1-GATE",
        ]

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
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage033DatabaseSizeGuardPhase2Tests(unittest.TestCase):
    def test_phase2_static_size_guard_artifacts_exist(self):
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
            "ids.stage033.database_size_guard.phase2.v1",
            "ids.stage033.database_size_guard.index.v1",
            "IDS-V0_1-STAGE033-P2",
            "ACC-STAGE-033",
            "D06-S004",
            "Phase 2 · 静态数据库体积护栏切片",
            "STAGE033_PHASE1_SCOPE_BOUNDARY.md",
            "stage032_connection_pool_index.json",
            "保护 800GB 内置盘",
            "NO_POSTGRES_CONNECTION",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase2_index_records_storage_budget_quality_and_recovery_guards(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(index["schema_version"], "ids.stage033.database_size_guard.index.v1")
        self.assertEqual(index["task_id"], "IDS-V0_1-STAGE033-P2")
        self.assertEqual(index["acceptance_id"], "ACC-STAGE-033")
        self.assertEqual(index["database_size_guard_contract_id"], "ids_stage033_database_size_guard_static_slice")

        guardrails = index["guardrails"]
        required_guardrails = [
            "postgres_storage_scope_guard",
            "raw_content_block_guard",
            "ocr_full_text_block_guard",
            "large_file_block_guard",
            "derived_artifact_limit_guard",
            "database_size_budget_guard",
            "table_size_guard",
            "index_bloat_guard",
            "row_payload_guard",
            "retention_cleanup_guard",
            "connection_pool_budget_guard",
            "quality_constraint_guard",
            "rollback_verification_guard",
            "raw_metadata_boundary",
            "real_data_only_guard",
        ]
        for key in required_guardrails:
            with self.subTest(key=key):
                self.assertIn(key, guardrails)

        storage_guard = guardrails["postgres_storage_scope_guard"]
        self.assertTrue(storage_guard["stores_control_plane_metadata"])
        self.assertTrue(storage_guard["stores_bounded_hot_index_metadata"])
        self.assertFalse(storage_guard["stores_raw_files"])
        self.assertFalse(storage_guard["stores_raw_database_rows"])
        self.assertFalse(storage_guard["stores_ocr_full_text"])
        self.assertFalse(storage_guard["stores_unbounded_derived_artifacts"])

        budget_guard = guardrails["database_size_budget_guard"]
        self.assertLessEqual(budget_guard["warning_threshold_gib"], budget_guard["hard_stop_threshold_gib"])
        self.assertLessEqual(budget_guard["hard_stop_threshold_gib"], budget_guard["internal_disk_budget_gib"])
        self.assertEqual(budget_guard["internal_disk_budget_gib"], 800)
        self.assertFalse(budget_guard["runtime_size_query_allowed"])

        raw_boundary = guardrails["raw_metadata_boundary"]
        self.assertEqual(raw_boundary["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(raw_boundary["path_only"])
        self.assertFalse(raw_boundary["content_access_allowed"])
        self.assertFalse(raw_boundary["recursive_listing_allowed"])
        self.assertFalse(raw_boundary["hashing_allowed"])
        self.assertFalse(raw_boundary["copy_allowed"])
        self.assertFalse(raw_boundary["modify_allowed"])
        self.assertFalse(raw_boundary["dump_allowed"])

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
        report = payload["database_size_guard_report"]

        self.assertEqual(report["schema_version"], "ids.stage033.database_size_guard.phase2.v1")
        self.assertEqual(report["index_schema_version"], "ids.stage033.database_size_guard.index.v1")
        self.assertEqual(report["stage"], "STAGE-033")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE033-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-033")
        self.assertTrue(all(report["guardrail_results"].values()))
        self.assertTrue(all(report["runtime_policy_results"].values()))
        self.assertEqual(report["raw_metadata_boundary"]["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(report["raw_metadata_boundary"]["path_only"])
        self.assertTrue(report["raw_metadata_boundary"]["no_raw_content_access"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])
        self.assertTrue(report["does_not_run_size_queries"])
        self.assertTrue(report["does_not_execute_cleanup"])

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
            "静态数据库体积护栏切片",
            "PostgreSQL 只存控制面、状态和热索引",
            "PostgreSQL 不存 500GB 原始文件",
            "PostgreSQL 不存 OCR 全文",
            "PostgreSQL 不存无限制派生产物",
            "check_database_size_guard.py",
            "stage033_database_size_guard_index.json",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)

        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE2_DATABASE_SIZE_GUARD_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json",
            "KM_IDSystem/scripts/check_database_size_guard.py",
            'push_allowed: false',
        ]
        allowed_lock_current_terms = [
            'status: "stage033_phase2_in_progress"',
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
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
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_phase: "Phase 4"',
            'next_gate: "IDS-STAGE033-P3-GATE"',
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "phase2_size_guard_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE033"',
            'phase_id: "IDS-STAGE033-P2"',
            'task_id: "IDS-V0_1-STAGE033-P2"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE033-P2-20260703-001"',
            '"event_type":"stage_slice"',
            '"task_id":"IDS-V0_1-STAGE033-P2"',
            '"ACC-STAGE-033"',
            "STAGE033_PHASE2_DATABASE_SIZE_GUARD_SLICE.md",
            "stage033_database_size_guard_index.json",
            "check_database_size_guard.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE033-P2"', lock_text)
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
