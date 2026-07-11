import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE036_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE036_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE036_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE036_PHASE4_CLOSEOUT.md"
STAGE_REVIEW = PURSUE_ROOT / "STAGE036_STAGE_REVIEW.md"
INDEX = (
    PURSUE_ROOT
    / "database_quality_constraints"
    / "stage036_database_quality_constraints_index.json"
)
MIGRATION = (
    PURSUE_ROOT
    / "database_quality_constraints"
    / "002_database_quality_constraints.sql"
)
PROFILE_QUERIES = (
    PURSUE_ROOT
    / "database_quality_constraints"
    / "stage036_quality_profile_queries.json"
)
SCRIPT = ROOT / "scripts" / "check_database_quality_constraints.py"
MIGRATION_RUNNER = ROOT / "scripts" / "run_stage036_migration_section.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage036DatabaseQualityConstraintsPhase1Tests(unittest.TestCase):
    def test_phase1_contracts_exist_and_bind_taskpack_identity(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")

        combined = "\n".join(
            [ENTRY.read_text(encoding="utf-8"), PHASE1.read_text(encoding="utf-8")]
        )
        required_terms = [
            "STAGE-036 · 数据库质量约束",
            "IDS-V0_1-STAGE036-P1",
            "ACC-STAGE-036",
            "D06-S007",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md",
            "13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b",
            "增加关键唯一性、非空、外键、状态枚举和一致性约束",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_real_schema_inputs_constraint_classes_and_outputs(self):
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")
        required_terms = [
            "database_quality_constraint_contract_id",
            "control_plane_schema_ref",
            "control_plane_schema_index_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "database_size_guard_ref",
            "data_retention_table_ref",
            "database_recovery_smoke_ref",
            "constraint_inventory",
            "PRIMARY_KEY_UNIQUENESS",
            "COMPOSITE_UNIQUENESS",
            "NOT_NULL_REQUIRED",
            "FOREIGN_KEY_INTEGRITY",
            "STATUS_VALUESET_INTEGRITY",
            "CROSS_FIELD_CONSISTENCY",
            "ids_chunks(document_id, chunk_ordinal)",
            "ids_documents.source_id -> ids_metadata_sources.source_id",
            "ids_chunks.document_id -> ids_documents.document_id",
            "ids_jobs.parent_job_id -> ids_jobs.job_id",
            "database_quality_constraint_summary",
            "constraint_inventory_payload",
            "constraint_migration_plan_payload",
            "constraint_validation_payload",
            "constraint_violation_payload",
            "rollback_verification_payload",
            "phase2_ready_contract",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_stage037_extensibility_and_blocks_live_or_fake_work(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")
        combined = "\n".join(
            [ENTRY.read_text(encoding="utf-8"), PHASE1.read_text(encoding="utf-8")]
        )
        required_terms = [
            "versioned_state_registry",
            "state_namespace",
            "STAGE-037",
            "job_state",
            "parser_state",
            "validation_state",
            "decision_state",
            "DB_QUALITY_STATE_REGISTRY_DEFERRED_TO_STAGE037",
            "DB_QUALITY_DATA_PROFILE_REQUIRED",
            "DB_QUALITY_MIGRATION_SAFETY_REQUIRED",
            "DB_QUALITY_READY_FOR_PHASE2_SLICE",
            "NO_PHASE2",
            "NO_POSTGRES_CONNECTION",
            "NO_SCHEMA_CHANGE",
            "NO_LIVE_MIGRATION",
            "NO_LIVE_CONSTRAINT_VALIDATION",
            "NO_RAW_DB_CONTENT",
            "NO_FAKE_DATA",
            "NO_STAGE037",
            "PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch_lock_roadmap_and_event_track_stage036_phase1_without_upload(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        lock_terms = [
            'push_allowed: false',
            "STAGE-036:",
            'acceptance_id: "ACC-STAGE-036"',
        ]
        allowed_lock_states = [
            [
                'status: "stage036_phase1_in_progress"',
                'next_phase: "Phase 2"',
                'next_gate: "IDS-STAGE036-P2-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P1"',
                'acceptance_status: "phase1_scope_boundary_defined"',
            ],
            [
                'status: "stage036_phase2_in_progress"',
                'next_phase: "Phase 3"',
                'next_gate: "IDS-STAGE036-P3-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P2"',
                'acceptance_status: "phase2_static_quality_constraint_contract_validated"',
            ],
            [
                'status: "stage036_phase3_in_progress"',
                'next_phase: "Phase 4"',
                'next_gate: "IDS-STAGE036-P4-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P3"',
                'acceptance_status: "phase3_scenario_validation_passed"',
            ],
            [
                'status: "stage036_completed_local_pending_review"',
                'next_phase: "stage_review_gate"',
                'next_gate: "IDS-STAGE036-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P4"',
                'acceptance_status: "phase4_closeout_complete"',
            ],
            [
                'status: "stage037_phase1_in_progress"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
            [
                'status: "stage037_phase2_in_progress"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
            [
                'status: "stage037_phase4_completed_review_pending"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE036"',
            'current_phase_id: "IDS-STAGE036-P1"',
            'current_task_id: "IDS-V0_1-STAGE036-P1"',
            'next_gate_id: "IDS-STAGE036-P2-GATE"',
            'stage_id: "IDS-STAGE036"',
            'phase_id: "IDS-STAGE036-P1"',
            'task_id: "IDS-V0_1-STAGE036-P1"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE036-P1-20260710-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE036-P1"',
            '"ACC-STAGE-036"',
            "STAGE036_PHASE1_SCOPE_BOUNDARY.md",
            "数据库质量约束",
        ]

        self.assertTrue(
            any(
                all(term in lock_text for term in state_terms)
                for state_terms in allowed_lock_states
            ),
            allowed_lock_states,
        )

        for terms, text in [
            (lock_terms, lock_text),
            (roadmap_terms, roadmap_text),
            (event_terms, events_text),
        ]:
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)


class Stage036DatabaseQualityConstraintsPhase2Tests(unittest.TestCase):
    EXPECTED_CANDIDATE_CONSTRAINTS = {
        "uq_ids_chunks_document_ordinal",
        "chk_ids_metadata_sources_quality_v2",
        "chk_ids_jobs_quality_v2",
        "chk_ids_documents_quality_v2",
        "chk_ids_chunks_quality_v2",
        "chk_ids_evidence_records_quality_v2",
        "chk_ids_audit_events_quality_v2",
        "chk_ids_index_versions_quality_v2",
        "chk_ids_schema_migrations_quality_v2",
    }

    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker: {SCRIPT}")
        spec = importlib.util.spec_from_file_location(
            "stage036_database_quality_constraints", SCRIPT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase2_static_artifacts_exist_and_bind_identity(self):
        for path in [PHASE2, INDEX, MIGRATION, SCRIPT]:
            self.assertTrue(path.is_file(), f"missing Phase 2 artifact: {path}")

        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [PHASE2, INDEX, MIGRATION, SCRIPT]
        )
        required_terms = [
            "ids.stage036.database_quality_constraints.index.v1",
            "ids.stage036.database_quality_constraints.phase2.v1",
            "ids_stage036_002_database_quality_constraints",
            "ids_stage036_database_quality_constraints_static_slice",
            "IDS-V0_1-STAGE036-P2",
            "ACC-STAGE-036",
            "STATIC_QUALITY_CONSTRAINT_CONTRACT_VALID",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE",
            "versioned_state_registry",
            "IDS-STAGE036-P3-GATE",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_migration_is_guarded_reversible_and_contains_no_fake_row_dml(self):
        self.assertTrue(MIGRATION.is_file(), f"missing migration: {MIGRATION}")
        sql = MIGRATION.read_text(encoding="utf-8")
        required_terms = [
            "-- migrate:up",
            "-- migrate:down",
            "ids.owner_authorized_real_profile_ref",
            "ids.migration_backup_checkpoint_ref",
            "ids.migration_rollback_plan_ref",
            "CREATE TABLE IF NOT EXISTS public.ids_state_value_registry",
            "PRIMARY KEY (state_namespace, state_value)",
            "VALIDATE CONSTRAINT",
            "SELECT EXISTS (SELECT 1 FROM public.ids_state_value_registry)",
            "STAGE-036 rollback blocked: ids_state_value_registry is not empty",
            "DROP TABLE IF EXISTS public.ids_state_value_registry",
        ] + sorted(self.EXPECTED_CANDIDATE_CONSTRAINTS)
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, sql)

        uncommented = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.MULTILINE | re.DOTALL)
        self.assertIsNone(
            re.search(r"\b(?:INSERT|UPDATE|DELETE|TRUNCATE|COPY)\b", uncommented, re.I)
        )
        self.assertNotIn("INSERT INTO ids_state_value_registry", sql)
        self.assertNotIn("/Users/linzezhang/Downloads/IDS_MetaData", sql)
        self.assertLess(sql.index("-- migrate:up"), sql.index("-- migrate:down"))

    def test_machine_index_separates_existing_candidate_and_deferred_constraints(self):
        self.assertTrue(INDEX.is_file(), f"missing index: {INDEX}")
        index = json.loads(INDEX.read_text(encoding="utf-8"))

        self.assertEqual(
            "ids.stage036.database_quality_constraints.index.v1",
            index["schema_version"],
        )
        self.assertEqual("IDS-V0_1-STAGE036-P2", index["task_id"])
        self.assertEqual("ACC-STAGE-036", index["acceptance_id"])
        self.assertEqual(
            self.EXPECTED_CANDIDATE_CONSTRAINTS,
            {item["constraint_id"] for item in index["constraint_inventory"]["candidates"]},
        )
        self.assertEqual(
            {
                "ids_documents.source_id -> ids_metadata_sources.source_id",
                "ids_chunks.document_id -> ids_documents.document_id",
                "ids_jobs.parent_job_id -> ids_jobs.job_id",
            },
            set(index["constraint_inventory"]["existing_foreign_keys"]),
        )

        registry = index["versioned_state_registry"]
        self.assertFalse(registry["populated"])
        self.assertFalse(registry["state_values_defined"])
        self.assertEqual("STAGE-037", registry["state_values_owner"])
        self.assertTrue(registry["rollback_requires_empty"])
        self.assertNotIn("allowed_values", registry)

        unique_candidate = next(
            item
            for item in index["constraint_inventory"]["candidates"]
            if item["constraint_id"] == "uq_ids_chunks_document_ordinal"
        )
        self.assertTrue(unique_candidate["owner_authorized_real_data_profile_required"])
        self.assertTrue(unique_candidate["live_apply_blocked"])
        self.assertEqual(
            "OWNER_AUTHORIZED_REAL_DATA_PROFILE_REQUIRED",
            unique_candidate["candidate_state"],
        )
        self.assertTrue(index["raw_metadata_boundary"]["path_only"])
        self.assertFalse(index["raw_metadata_boundary"]["content_access_allowed"])
        self.assertTrue(all(value is False for value in index["runtime_policy"].values()))

    def test_checker_validates_static_contract_and_keeps_live_execution_blocked(self):
        module = self._load_checker_module()
        report = module.build_stage036_quality_constraint_report(
            INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH
        )

        self.assertEqual(
            "ids.stage036.database_quality_constraints.phase2.v1",
            report["schema_version"],
        )
        self.assertEqual("IDS-V0_1-STAGE036-P2", report["task_id"])
        self.assertTrue(report["contract_valid"], report)
        self.assertIn(
            "future_check_validation_steps_present",
            report["migration_contract_results"],
        )
        self.assertIn(
            "state_registry_rollback_requires_empty",
            report["migration_contract_results"],
        )
        self.assertNotIn(
            "check_constraints_validated",
            report["migration_contract_results"],
        )
        for group in [
            "source_integrity_results",
            "baseline_schema_results",
            "migration_contract_results",
            "constraint_inventory_results",
            "guardrail_results",
            "runtime_policy_results",
        ]:
            self.assertTrue(all(report[group].values()), {group: report[group]})
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE",
            report["execution_state"],
        )
        self.assertFalse(report["migration_execution_performed"])
        self.assertFalse(report["real_data_profile_executed"])
        self.assertEqual("IDS-STAGE036-P3-GATE", report["next_gate"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_tampered_index_or_migration_fails_closed_in_memory(self):
        module = self._load_checker_module()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        migration_sql = MIGRATION.read_text(encoding="utf-8")
        baseline_sql = module.CONTROL_SCHEMA_PATH.read_text(encoding="utf-8")

        tampered_index = copy.deepcopy(index)
        tampered_index["runtime_policy"]["execute_migration"] = True
        index_report = module.build_stage036_quality_constraint_report(
            INDEX,
            MIGRATION,
            module.CONTROL_SCHEMA_PATH,
            index_snapshot=tampered_index,
            migration_sql_snapshot=migration_sql,
            baseline_sql_snapshot=baseline_sql,
        )
        self.assertFalse(index_report["contract_valid"])
        self.assertEqual("BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT", index_report["execution_state"])
        self.assertEqual(
            "INVALID_QUALITY_CONSTRAINT_CONTRACT",
            index_report["contract_state"],
        )
        self.assertIn("无效", index_report["owner_feedback_zh"])

        tampered_candidate = copy.deepcopy(index)
        tampered_candidate["constraint_inventory"]["candidates"][1]["table"] = (
            "ids_jobs"
        )
        candidate_report = module.build_stage036_quality_constraint_report(
            INDEX,
            MIGRATION,
            module.CONTROL_SCHEMA_PATH,
            index_snapshot=tampered_candidate,
            migration_sql_snapshot=migration_sql,
            baseline_sql_snapshot=baseline_sql,
        )
        self.assertFalse(candidate_report["contract_valid"])
        self.assertFalse(
            candidate_report["constraint_inventory_results"]["candidate_specs_exact"]
        )

        tampered_sql = migration_sql.replace(
            "uq_ids_chunks_document_ordinal", "removed_unique_constraint"
        )
        sql_report = module.build_stage036_quality_constraint_report(
            INDEX,
            MIGRATION,
            module.CONTROL_SCHEMA_PATH,
            index_snapshot=index,
            migration_sql_snapshot=tampered_sql,
            baseline_sql_snapshot=baseline_sql,
        )
        self.assertFalse(sql_report["contract_valid"])
        self.assertFalse(
            sql_report["migration_contract_results"]["candidate_constraints_present"]
        )

        semantic_sql = migration_sql.replace(
            "AND retry_count <= max_retries",
            "AND retry_count >= max_retries",
        )
        semantic_report = module.build_stage036_quality_constraint_report(
            INDEX,
            MIGRATION,
            module.CONTROL_SCHEMA_PATH,
            index_snapshot=index,
            migration_sql_snapshot=semantic_sql,
            baseline_sql_snapshot=baseline_sql,
        )
        self.assertFalse(semantic_report["contract_valid"])
        self.assertFalse(
            semantic_report["migration_contract_results"]
            ["candidate_sql_definitions_exact"]
        )

    def test_cli_preserves_phase2_report_under_current_phase4_output(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("Phase 4", payload["phase"])
        phase2 = payload["phase2_report"]
        self.assertEqual("Phase 2", phase2["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P2", phase2["task_id"])
        self.assertTrue(phase2["contract_valid"])
        self.assertFalse(phase2["execution_ready"])
        self.assertEqual("IDS-STAGE036-P3-GATE", phase2["next_gate"])

    def test_governance_tracks_phase2_and_preserves_upload_lock(self):
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        lock_terms = [
            'push_allowed: false',
            '      - "Phase 2"',
        ]
        allowed_lock_states = [
            [
                'status: "stage036_phase2_in_progress"',
                'next_phase: "Phase 3"',
                'next_gate: "IDS-STAGE036-P3-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P2"',
                'acceptance_status: "phase2_static_quality_constraint_contract_validated"',
            ],
            [
                'status: "stage036_phase3_in_progress"',
                'next_phase: "Phase 4"',
                'next_gate: "IDS-STAGE036-P4-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P3"',
                'acceptance_status: "phase3_scenario_validation_passed"',
            ],
            [
                'status: "stage036_completed_local_pending_review"',
                'next_phase: "stage_review_gate"',
                'next_gate: "IDS-STAGE036-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P4"',
                'acceptance_status: "phase4_closeout_complete"',
            ],
            [
                'status: "stage037_phase1_in_progress"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
            [
                'status: "stage037_phase2_in_progress"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
            [
                'status: "stage037_phase4_completed_review_pending"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
        ]
        required = {
            lock_text: lock_terms,
            roadmap_text: [
                'current_stage_id: "IDS-STAGE036"',
                'current_phase_id: "IDS-STAGE036-P2"',
                'current_task_id: "IDS-V0_1-STAGE036-P2"',
                'next_gate_id: "IDS-STAGE036-P3-GATE"',
                'phase_id: "IDS-STAGE036-P2"',
                'task_id: "IDS-V0_1-STAGE036-P2"',
            ],
            events_text: [
                '"event_id":"EVT-IDS-V0_1-STAGE036-P2-20260710-001"',
                '"event_type":"stage_slice"',
                '"task_id":"IDS-V0_1-STAGE036-P2"',
                '"ACC-STAGE-036"',
                "STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md",
                "check_database_quality_constraints.py",
            ],
        }
        self.assertTrue(
            any(
                all(term in lock_text for term in state_terms)
                for state_terms in allowed_lock_states
            ),
            allowed_lock_states,
        )
        for text, terms in required.items():
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)


class Stage036DatabaseQualityConstraintsPhase3Tests(unittest.TestCase):
    EXPECTED_SCENARIOS = {
        "migration_dry_run",
        "repeat_execution",
        "failure_rollback",
        "recovery_smoke",
        "candidate_constraint_semantics",
        "duplicate_uniqueness_profile_gate",
        "existing_foreign_key_integrity",
        "state_registry_deferred",
        "raw_large_file_block",
        "unbounded_derived_artifact_block",
        "connection_pool_boundary",
        "transaction_boundary",
        "constraint_error_explanations",
        "source_non_interference",
    }

    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker: {SCRIPT}")
        spec = importlib.util.spec_from_file_location(
            "stage036_database_quality_constraints_p3", SCRIPT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _scenario_builder(self):
        module = self._load_checker_module()
        self.assertTrue(
            hasattr(module, "build_stage036_scenario_validation_report"),
            "missing Phase 3 scenario report builder",
        )
        return module, module.build_stage036_scenario_validation_report

    def test_phase3_artifact_and_scenario_contract_exist(self):
        self.assertTrue(PHASE3.is_file(), f"missing Phase 3 evidence: {PHASE3}")
        combined = "\n".join(
            [PHASE3.read_text(encoding="utf-8"), SCRIPT.read_text(encoding="utf-8")]
        )
        required_terms = [
            "ids.stage036.database_quality_constraints.phase3.v1",
            "IDS-V0_1-STAGE036-P3",
            "ACC-STAGE-036",
            "build_stage036_scenario_validation_report",
            "scenario_validation_valid",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE",
            "STATIC_TRACKED_CONTRACT_SCENARIO_VALIDATION_ONLY",
            "live_execution_performed",
            "NO_PHASE4",
            "13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b",
        ] + sorted(self.EXPECTED_SCENARIOS)
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_scenario_report_passes_static_checks_and_keeps_execution_blocked(self):
        module, builder = self._scenario_builder()
        report = builder(INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH)

        self.assertEqual(
            "ids.stage036.database_quality_constraints.phase3.v1",
            report["schema_version"],
        )
        self.assertEqual("Phase 3", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P3", report["task_id"])
        self.assertEqual("ACC-STAGE-036", report["acceptance_id"])
        self.assertEqual(self.EXPECTED_SCENARIOS, set(report["scenario_results"]))
        self.assertTrue(report["phase2_contract_valid"], report)
        self.assertTrue(report["scenario_validation_valid"], report)
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE",
            report["execution_state"],
        )
        self.assertTrue(
            all(
                result["status"] == "PASS"
                for result in report["scenario_results"].values()
            ),
            report["scenario_results"],
        )
        recovery = report["scenario_results"]["recovery_smoke"]
        self.assertTrue(recovery["expected_block"])
        self.assertEqual(report["execution_state"], recovery["observed_state"])
        for field in [
            "live_execution_performed",
            "postgresql_connection_performed",
            "migration_dry_run_performed",
            "migration_apply_performed",
            "constraint_validation_performed",
            "rollback_performed",
            "backup_performed",
            "restore_performed",
            "recovery_smoke_performed",
            "real_data_profile_executed",
            "state_values_seeded",
            "runtime_output_written",
        ]:
            with self.subTest(field=field):
                self.assertFalse(report[field])
        self.assertEqual("IDS-STAGE036-P4-GATE", report["next_gate"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_scenario_report_is_deterministic_and_owner_explainable(self):
        module, builder = self._scenario_builder()
        first = builder(INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH)
        second = builder(INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH)

        self.assertEqual(first["scenario_results"], second["scenario_results"])
        for scenario_id, result in first["scenario_results"].items():
            with self.subTest(scenario_id=scenario_id):
                self.assertTrue(result["evidence"])
                self.assertRegex(result["owner_explanation_zh"], r"[\u4e00-\u9fff]")
                self.assertFalse(result["live_execution_performed"])

    def test_runtime_policy_tampering_fails_relevant_scenarios_closed(self):
        module, builder = self._scenario_builder()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        migration_sql = MIGRATION.read_text(encoding="utf-8")
        baseline_sql = module.CONTROL_SCHEMA_PATH.read_text(encoding="utf-8")

        for runtime_key, scenario_id in [
            ("execute_migration", "migration_dry_run"),
            ("execute_restore", "recovery_smoke"),
            ("connect_to_postgres", "transaction_boundary"),
        ]:
            tampered = copy.deepcopy(index)
            tampered["runtime_policy"][runtime_key] = True
            report = builder(
                INDEX,
                MIGRATION,
                module.CONTROL_SCHEMA_PATH,
                index_snapshot=tampered,
                migration_sql_snapshot=migration_sql,
                baseline_sql_snapshot=baseline_sql,
            )
            with self.subTest(runtime_key=runtime_key):
                self.assertFalse(report["phase2_contract_valid"])
                self.assertFalse(report["scenario_validation_valid"])
                self.assertEqual(
                    "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT",
                    report["execution_state"],
                )
                self.assertEqual(
                    "FAIL", report["scenario_results"][scenario_id]["status"]
                )
                self.assertFalse(report["live_execution_performed"])

    def test_repeat_and_rollback_contract_tampering_fail_closed(self):
        module, builder = self._scenario_builder()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        migration_sql = MIGRATION.read_text(encoding="utf-8")
        baseline_sql = module.CONTROL_SCHEMA_PATH.read_text(encoding="utf-8")
        mutations = [
            (
                "missing_table_idempotency_guard",
                migration_sql.replace(
                    "CREATE TABLE IF NOT EXISTS public.ids_state_value_registry",
                    "CREATE TABLE public.ids_state_value_registry",
                    1,
                ),
                "repeat_execution",
            ),
            (
                "missing_registry_rollback_query",
                migration_sql.replace(
                    "SELECT EXISTS (SELECT 1 FROM public.ids_state_value_registry)",
                    "SELECT FALSE",
                    1,
                ),
                "failure_rollback",
            ),
            (
                "constraint_guard_or_true",
                migration_sql.replace(
                    "AND conrelid = 'public.ids_chunks'::regclass\n  ) THEN",
                    "AND conrelid = 'public.ids_chunks'::regclass\n      OR TRUE\n  ) THEN",
                    1,
                ),
                "repeat_execution",
            ),
            (
                "registry_rollback_and_false",
                migration_sql.replace(
                    "SELECT EXISTS (SELECT 1 FROM public.ids_state_value_registry)'",
                    "SELECT EXISTS (SELECT 1 FROM public.ids_state_value_registry) AND FALSE'",
                    1,
                ),
                "failure_rollback",
            ),
            (
                "premature_registry_drop",
                migration_sql.replace(
                    "DO $ids_quality_rollback_gate$",
                    "DROP TABLE IF EXISTS public.ids_state_value_registry;\n\n"
                    "DO $ids_quality_rollback_gate$",
                    1,
                ),
                "failure_rollback",
            ),
        ]
        for mutation_id, tampered_sql, scenario_id in mutations:
            self.assertNotEqual(migration_sql, tampered_sql, mutation_id)
            report = builder(
                INDEX,
                MIGRATION,
                module.CONTROL_SCHEMA_PATH,
                index_snapshot=index,
                migration_sql_snapshot=tampered_sql,
                baseline_sql_snapshot=baseline_sql,
            )
            with self.subTest(mutation_id=mutation_id, scenario_id=scenario_id):
                self.assertFalse(report["phase2_contract_valid"])
                self.assertFalse(report["scenario_validation_valid"])
                self.assertEqual(
                    "FAIL", report["scenario_results"][scenario_id]["status"]
                )

    def test_malformed_candidate_inventory_fails_closed_without_crashing(self):
        module, builder = self._scenario_builder()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        index["constraint_inventory"] = "invalid"
        try:
            report = builder(
                INDEX,
                MIGRATION,
                module.CONTROL_SCHEMA_PATH,
                index_snapshot=index,
                migration_sql_snapshot=MIGRATION.read_text(encoding="utf-8"),
                baseline_sql_snapshot=module.CONTROL_SCHEMA_PATH.read_text(
                    encoding="utf-8"
                ),
            )
        except Exception as exc:
            self.fail(f"scenario builder must fail closed without crashing: {exc}")

        self.assertFalse(report["phase2_contract_valid"])
        self.assertFalse(report["scenario_validation_valid"])
        self.assertEqual(
            "FAIL",
            report["scenario_results"]["candidate_constraint_semantics"]["status"],
        )
        self.assertEqual(
            "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT",
            report["execution_state"],
        )

    def test_cli_preserves_phase3_report_under_current_phase4_output(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("Phase 4", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P4", payload["task_id"])
        self.assertFalse(payload["live_execution_performed"])
        self.assertIn("scenario_report", payload)
        scenario = payload["scenario_report"]
        self.assertEqual("Phase 3", scenario["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P3", scenario["task_id"])
        self.assertTrue(scenario["scenario_validation_valid"])
        self.assertIn("phase2_report", scenario)
        self.assertTrue(scenario["phase2_report"]["contract_valid"])
        self.assertEqual("", completed.stderr)

    def test_governance_tracks_phase3_and_preserves_upload_lock(self):
        self.assertTrue(PHASE3.is_file(), f"missing Phase 3 evidence: {PHASE3}")
        phase3_text = PHASE3.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        required = {
            phase3_text: [
                "Phase 3 · 数据库质量约束专项验证与异常场景",
                "migration_dry_run",
                "recovery_smoke",
                "live_execution_performed=false",
                "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
                "/Users/linzezhang/Downloads/IDS_MetaData",
                "NO_PHASE4",
            ],
            lock_text: [
                'status: "stage037_phase4_completed_review_pending"',
                'status: "completed_reviewed_local"',
                'push_allowed: false',
                '      - "Phase 3"',
                '      - "Phase 4"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
            ],
            roadmap_text: [
                'current_stage_id: "IDS-STAGE036"',
                'current_phase_id: "IDS-STAGE036-P4"',
                'current_task_id: "IDS-V0_1-STAGE036-P4"',
                'next_gate_id: "IDS-STAGE036-REVIEW-GATE"',
                'phase_id: "IDS-STAGE036-P3"',
                'task_id: "IDS-V0_1-STAGE036-P3"',
            ],
            events_text: [
                '"event_id":"EVT-IDS-V0_1-STAGE036-P3-20260710-001"',
                '"event_type":"validation"',
                '"task_id":"IDS-V0_1-STAGE036-P3"',
                '"ACC-STAGE-036"',
                "STAGE036_PHASE3_SCENARIO_VALIDATION.md",
                "build_stage036_scenario_validation_report",
            ],
        }
        for text, terms in required.items():
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)


class Stage036DatabaseQualityConstraintsPhase4Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker: {SCRIPT}")
        spec = importlib.util.spec_from_file_location(
            "stage036_database_quality_constraints_p4", SCRIPT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _delivery_builder(self):
        module = self._load_checker_module()
        self.assertTrue(
            hasattr(module, "build_stage036_delivery_report"),
            "missing Phase 4 delivery report builder",
        )
        return module, module.build_stage036_delivery_report

    def test_phase4_artifact_and_delivery_contract_exist(self):
        self.assertTrue(PHASE4.is_file(), f"missing Phase 4 evidence: {PHASE4}")
        combined = "\n".join(
            [PHASE4.read_text(encoding="utf-8"), SCRIPT.read_text(encoding="utf-8")]
        )
        required_terms = [
            "ids.stage036.database_quality_constraints.phase4.v1",
            "ids.stage036.database_quality_constraints.delivery_contract.v1",
            "IDS-V0_1-STAGE036-P4",
            "ACC-STAGE-036",
            "build_stage036_delivery_report",
            "delivery_contract_valid",
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "known_limits",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "chinese_owner_feedback",
            "PASS_WITH_EXPECTED_BLOCK",
            "NO_STAGE_REVIEW_THIS_RUN",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_delivery_report_is_valid_and_keeps_every_live_action_blocked(self):
        module, builder = self._delivery_builder()
        report = builder(INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH)

        self.assertEqual(
            "ids.stage036.database_quality_constraints.phase4.v1",
            report["schema_version"],
        )
        self.assertEqual("Phase 4", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P4", report["task_id"])
        self.assertEqual("ACC-STAGE-036", report["acceptance_id"])
        self.assertTrue(report["delivery_contract_valid"], report)
        self.assertTrue(all(report["delivery_check_results"].values()), report)
        self.assertTrue(all(report["phase4_contract_results"].values()), report)
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE",
            report["execution_state"],
        )
        self.assertEqual("IDS-STAGE037-P1-GATE", report["next_gate"])
        self.assertEqual("completed_reviewed_local", report["stage_review_status"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])
        self.assertEqual("tracked_files", report["snapshot_binding"]["source"])
        self.assertTrue(report["snapshot_binding"]["tracked_snapshot_bound"])
        self.assertTrue(report["snapshot_binding"]["single_snapshot_reused"])
        for field in [
            "live_execution_performed",
            "postgresql_connection_performed",
            "migration_dry_run_performed",
            "migration_apply_performed",
            "constraint_validation_performed",
            "rollback_performed",
            "backup_performed",
            "restore_performed",
            "recovery_smoke_performed",
            "real_data_profile_executed",
            "state_values_seeded",
            "runtime_output_written",
        ]:
            with self.subTest(field=field):
                self.assertFalse(report[field])

    def test_delivery_evidence_is_real_tracked_snapshot_not_live_output(self):
        module, builder = self._delivery_builder()
        report = builder(INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH)
        migration_sha = hashlib.sha256(MIGRATION.read_bytes()).hexdigest()
        baseline_sha = hashlib.sha256(
            module.CONTROL_SCHEMA_PATH.read_bytes()
        ).hexdigest()

        schema_diff = report["schema_diff"]
        self.assertEqual("static_tracked_schema_diff_not_executed", schema_diff["mode"])
        self.assertEqual("NOT_EXECUTED", schema_diff["live_schema_diff_result"])
        self.assertEqual(migration_sha, schema_diff["migration_sha256"])
        self.assertEqual(baseline_sha, schema_diff["baseline_schema_sha256"])
        self.assertEqual(["ids_state_value_registry"], schema_diff["added_table_contracts"])
        self.assertEqual(9, schema_diff["candidate_constraint_count"])
        self.assertEqual(3, schema_diff["existing_foreign_key_count"])

        migration_output = report["migration_output"]
        self.assertEqual(
            "static_tracked_migration_output_not_executed",
            migration_output["mode"],
        )
        self.assertEqual(
            "ids_stage036_002_database_quality_constraints",
            migration_output["migration_id"],
        )
        self.assertEqual(migration_sha, migration_output["tracked_migration_sha256"])
        self.assertEqual("NOT_EXECUTED", migration_output["live_migration_result"])
        self.assertEqual(
            "NOT_EXECUTED",
            migration_output["live_constraint_validation_result"],
        )
        self.assertFalse(migration_output["destructive_migration_allowed"])

        recovery_log = report["recovery_test_log"]
        self.assertEqual(
            "static_quality_constraint_recovery_log_expected_block",
            recovery_log["mode"],
        )
        self.assertEqual("PASS_WITH_EXPECTED_BLOCK", recovery_log["result"])
        self.assertEqual("NOT_EXECUTED", recovery_log["live_recovery_smoke_result"])
        self.assertEqual(14, recovery_log["scenario_count"])
        self.assertTrue(
            all(item["status"] == "PASS" for item in recovery_log["scenario_results"].values())
        )
        self.assertFalse(recovery_log["live_execution_performed"])

    def test_manual_confirmation_rollback_backup_and_limits_are_explicit(self):
        module, builder = self._delivery_builder()
        report = builder(INDEX, MIGRATION, module.CONTROL_SCHEMA_PATH)

        confirmation = report["destructive_migration_confirmation"]
        self.assertTrue(confirmation["required"])
        self.assertFalse(confirmation["destructive_allowed_by_default"])
        self.assertFalse(confirmation["authorized_this_run"])
        self.assertTrue(confirmation["manual_owner_confirmation_required"])
        self.assertGreaterEqual(len(report["rollback_steps"]), 5)
        self.assertGreaterEqual(len(report["backup_restore_steps"]), 6)
        self.assertGreaterEqual(len(report["known_limits"]), 6)
        self.assertIn("未执行真实 migration", report["chinese_owner_feedback"])
        self.assertIn("STAGE-036 review 已完成", report["chinese_owner_feedback"])
        self.assertIn("IDS-STAGE037-P1-GATE", report["chinese_owner_feedback"])
        self.assertNotIn("review 尚未执行", report["chinese_owner_feedback"])
        self.assertNotIn(
            "下一步只能进入独立 STAGE-036 review",
            report["chinese_owner_feedback"],
        )
        review_limit = next(
            item
            for item in report["known_limits"]
            if item["limit_id"] == "stage_review_and_batch_upload_blocked"
        )
        self.assertIn("STAGE-036 review 已完成", review_limit["owner_message_zh"])
        self.assertIn("BATCH031_040", review_limit["owner_message_zh"])
        self.assertNotIn("尚未执行", review_limit["owner_message_zh"])

    def test_tampered_delivery_runtime_or_sql_contract_fails_closed(self):
        module, builder = self._delivery_builder()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        migration_sql = MIGRATION.read_text(encoding="utf-8")
        baseline_sql = module.CONTROL_SCHEMA_PATH.read_text(encoding="utf-8")

        bad_confirmation = copy.deepcopy(index)
        bad_confirmation["phase4_delivery_contract"][
            "destructive_migration_confirmation"
        ]["authorized_this_run"] = True
        bad_runtime = copy.deepcopy(index)
        bad_runtime["runtime_policy"]["execute_migration"] = True
        bad_phase4_root = copy.deepcopy(index)
        bad_phase4_root["phase4_delivery_contract"][
            "future_destructive_authorization"
        ] = True
        bad_guardrails = copy.deepcopy(index)
        bad_guardrails["guardrails"]["connection_pool"] = []
        bad_candidate_columns = copy.deepcopy(index)
        bad_candidate_columns["constraint_inventory"]["candidates"][0][
            "columns"
        ] = None
        bad_sql = migration_sql.replace(
            "CREATE TABLE IF NOT EXISTS public.ids_state_value_registry",
            "CREATE TABLE public.ids_state_value_registry",
            1,
        )
        destructive_sql = migration_sql.replace(
            "-- migrate:down",
            "-- migrate:down\nDROP TABLE ids_documents;",
            1,
        )
        quoted_destructive_sql = migration_sql.replace(
            "-- migrate:down",
            '-- migrate:down\nDROP TABLE "ids_documents";',
            1,
        )
        drop_owned_sql = migration_sql.replace(
            "-- migrate:down", "-- migrate:down\nDROP OWNED BY ids_runtime;", 1
        )
        drop_sequence_sql = migration_sql.replace(
            "-- migrate:down", "-- migrate:down\nDROP SEQUENCE ids_sequence;", 1
        )
        drop_function_sql = migration_sql.replace(
            "-- migrate:down", "-- migrate:down\nDROP FUNCTION ids_fn();", 1
        )
        alter_column_type_sql = migration_sql.replace(
            "-- migrate:down",
            "-- migrate:down\nALTER TABLE ids_documents ALTER COLUMN document_id TYPE integer;",
            1,
        )
        check_or_true_sql = migration_sql.replace(
            "AND is_raw_content_stored = false\n      ) NOT VALID;",
            "AND is_raw_content_stored = false\n        OR TRUE\n      ) NOT VALID;",
            1,
        )
        comment_drift_sql = migration_sql + "\n-- untracked content drift\n"
        for mutation_id, index_snapshot, sql_snapshot in [
            ("unauthorized_destructive_confirmation", bad_confirmation, migration_sql),
            ("runtime_migration_enabled", bad_runtime, migration_sql),
            ("extra_phase4_root_field", bad_phase4_root, migration_sql),
            ("malformed_nested_guardrails", bad_guardrails, migration_sql),
            ("migration_guard_removed", index, bad_sql),
            ("extra_destructive_down_sql", index, destructive_sql),
            ("quoted_destructive_down_sql", index, quoted_destructive_sql),
            ("drop_owned_down_sql", index, drop_owned_sql),
            ("drop_sequence_down_sql", index, drop_sequence_sql),
            ("drop_function_down_sql", index, drop_function_sql),
            ("alter_column_type_down_sql", index, alter_column_type_sql),
            ("check_constraint_or_true", index, check_or_true_sql),
            ("snapshot_hash_drift", index, comment_drift_sql),
            ("malformed_candidate_columns", bad_candidate_columns, migration_sql),
        ]:
            report = builder(
                INDEX,
                MIGRATION,
                module.CONTROL_SCHEMA_PATH,
                index_snapshot=index_snapshot,
                migration_sql_snapshot=sql_snapshot,
                baseline_sql_snapshot=baseline_sql,
            )
            with self.subTest(mutation_id=mutation_id):
                self.assertFalse(report["delivery_contract_valid"], report)
                self.assertEqual("FAIL_CLOSED", report["recovery_test_log"]["result"])
                self.assertEqual(
                    "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT",
                    report["execution_state"],
                )
                self.assertFalse(report["live_execution_performed"])
                self.assertIn("失败关闭", report["chinese_owner_feedback"])
                self.assertEqual(
                    "in_memory_validation_snapshot",
                    report["snapshot_binding"]["source"],
                )
                self.assertFalse(report["snapshot_binding"]["tracked_snapshot_bound"])
                if mutation_id == "extra_phase4_root_field":
                    self.assertFalse(
                        report["phase4_contract_results"]["root_keys_exact"]
                    )
                if mutation_id in {
                    "extra_destructive_down_sql",
                    "quoted_destructive_down_sql",
                    "drop_owned_down_sql",
                    "drop_sequence_down_sql",
                    "drop_function_down_sql",
                    "alter_column_type_down_sql",
                }:
                    self.assertFalse(
                        report["delivery_check_results"][
                            "destructive_migration_blocked"
                        ]
                    )
                if mutation_id == "check_constraint_or_true":
                    self.assertFalse(
                        report["phase2_report"]["migration_contract_results"][
                            "candidate_sql_definitions_exact"
                        ]
                    )
                if mutation_id == "snapshot_hash_drift":
                    self.assertFalse(
                        report["delivery_check_results"][
                            "snapshot_hashes_match_contract"
                        ]
                    )

    def test_noncanonical_path_cannot_claim_tracked_snapshot_binding(self):
        module, builder = self._delivery_builder()

        class NonCanonicalMigrationPath:
            def __fspath__(self):
                return "/tmp/not-a-tracked-stage036-migration.sql"

            def read_text(self, encoding="utf-8"):
                return MIGRATION.read_text(encoding=encoding)

            def as_posix(self):
                return self.__fspath__()

            def resolve(self):
                return Path(self.__fspath__())

        report = builder(
            INDEX,
            NonCanonicalMigrationPath(),
            module.CONTROL_SCHEMA_PATH,
        )
        self.assertFalse(report["snapshot_binding"]["tracked_snapshot_bound"])
        self.assertEqual(
            "unbound_worktree_validation_snapshot",
            report["snapshot_binding"]["source"],
        )
        self.assertFalse(report["delivery_contract_valid"])
        self.assertEqual("FAIL_CLOSED", report["result"])

    def test_malformed_top_level_index_fails_closed_without_crashing(self):
        module, builder = self._delivery_builder()
        migration_sql = MIGRATION.read_text(encoding="utf-8")
        baseline_sql = module.CONTROL_SCHEMA_PATH.read_text(encoding="utf-8")

        for malformed_index in ([], "not-an-object", 36):
            with self.subTest(malformed_index=malformed_index):
                report = builder(
                    INDEX,
                    MIGRATION,
                    module.CONTROL_SCHEMA_PATH,
                    index_snapshot=malformed_index,
                    migration_sql_snapshot=migration_sql,
                    baseline_sql_snapshot=baseline_sql,
                )
                self.assertFalse(report["delivery_contract_valid"])
                self.assertEqual("FAIL_CLOSED", report["result"])
                self.assertIn("失败关闭", report["chinese_owner_feedback"])
                self.assertFalse(report["live_execution_performed"])

        with tempfile.TemporaryDirectory() as tmp_dir:
            invalid_json_path = Path(tmp_dir) / "stage036-invalid-index.json"
            invalid_json_path.write_text("{invalid-json", encoding="utf-8")
            report = builder(
                invalid_json_path,
                MIGRATION,
                module.CONTROL_SCHEMA_PATH,
            )
        self.assertFalse(report["delivery_contract_valid"])
        self.assertEqual("FAIL_CLOSED", report["result"])
        self.assertIn("失败关闭", report["chinese_owner_feedback"])
        self.assertFalse(report["live_execution_performed"])

    def test_cli_emits_phase4_top_level_and_preserves_nested_history(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("Phase 4", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P4", payload["task_id"])
        self.assertTrue(payload["delivery_contract_valid"])
        self.assertEqual("PASS_WITH_EXPECTED_BLOCK", payload["recovery_test_log"]["result"])
        self.assertFalse(payload["live_execution_performed"])
        self.assertEqual("Phase 3", payload["scenario_report"]["phase"])
        self.assertEqual("Phase 2", payload["phase2_report"]["phase"])
        self.assertEqual("IDS-STAGE037-P1-GATE", payload["next_gate"])
        self.assertEqual("", completed.stderr)

    def test_governance_tracks_phase4_and_stops_at_separate_review_gate(self):
        self.assertTrue(PHASE4.is_file(), f"missing Phase 4 evidence: {PHASE4}")
        phase4_text = PHASE4.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        required = {
            phase4_text: [
                "Phase 4 · 数据库质量约束交付证据、回滚与中文反馈",
                "live_schema_diff_result=NOT_EXECUTED",
                "live_migration_result=NOT_EXECUTED",
                "live_recovery_smoke_result=NOT_EXECUTED",
                "result=PASS_WITH_EXPECTED_BLOCK",
                "stage_review_status=pending_next_run",
                "任何破坏性 migration 必须单独人工确认",
                "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
                "/Users/linzezhang/Downloads/IDS_MetaData",
                "NO_STAGE_REVIEW_THIS_RUN",
            ],
            lock_text: [
                'status: "stage037_phase4_completed_review_pending"',
                'status: "completed_reviewed_local"',
                '      - "Phase 4"',
                'review_status: "passed"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
                'push_allowed: false',
                "STAGE036_PHASE4_CLOSEOUT.md",
            ],
            roadmap_text: [
                'current_stage_id: "IDS-STAGE036"',
                'current_phase_id: "IDS-STAGE036-P4"',
                'current_task_id: "IDS-V0_1-STAGE036-P4"',
                'next_gate_id: "IDS-STAGE036-REVIEW-GATE"',
                'phase_id: "IDS-STAGE036-P4"',
                'task_id: "IDS-V0_1-STAGE036-P4"',
                'status: "passed_no_github_upload_until_stage_review"',
            ],
            events_text: [
                '"event_id":"EVT-IDS-V0_1-STAGE036-P4-',
                '"event_type":"stage_closeout"',
                '"task_id":"IDS-V0_1-STAGE036-P4"',
                '"ACC-STAGE-036"',
                "STAGE036_PHASE4_CLOSEOUT.md",
                "build_stage036_delivery_report",
                "PASS_WITH_EXPECTED_BLOCK",
                "IDS-STAGE036-REVIEW-GATE",
            ],
        }
        for text, terms in required.items():
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)


class Stage036DatabaseQualityConstraintsReviewTests(unittest.TestCase):
    OWNERSHIP_MARKER = (
        "ids.stage036.owner:ids_stage036_002_database_quality_constraints"
    )

    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker: {SCRIPT}")
        spec = importlib.util.spec_from_file_location(
            "stage036_database_quality_constraints_review", SCRIPT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _phase2_report(self, module, index):
        return module.build_stage036_quality_constraint_report(
            INDEX,
            MIGRATION,
            module.CONTROL_SCHEMA_PATH,
            index_snapshot=index,
            migration_sql_snapshot=MIGRATION.read_text(encoding="utf-8"),
            baseline_sql_snapshot=module.CONTROL_SCHEMA_PATH.read_text(
                encoding="utf-8"
            ),
        )

    def test_review_artifact_records_full_stage_audit_and_no_upload_boundary(self):
        self.assertTrue(
            STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}"
        )
        review_text = STAGE_REVIEW.read_text(encoding="utf-8")
        required_terms = [
            "IDS-V0_1-STAGE036-REVIEW",
            "ACC-STAGE-036",
            "STAGE-036 · 数据库质量约束",
            "P0 source binding",
            "Phase 1 boundary",
            "Phase 2 static quality-constraint contract",
            "Phase 3 scenario validation",
            "Phase 4 closeout",
            "STAGE036-REVIEW-F1",
            "completed_reviewed_local",
            "IDS-STAGE037-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE037_THIS_RUN",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, review_text)

    def test_review_gate_tracks_reviewed_local_and_keeps_batch_upload_locked(self):
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        required = {
            lock_text: [
                'status: "stage037_phase4_completed_review_pending"',
                'status: "completed_reviewed_local"',
                'review_status: "passed"',
                'next_stage: "STAGE-037"',
                'next_gate: "IDS-STAGE037-P1-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'acceptance_status: "reviewed_local_passed"',
                "STAGE036_STAGE_REVIEW.md",
                "push_allowed: false",
            ],
            roadmap_text: [
                'current_stage_id: "IDS-STAGE036"',
                'current_phase_id: "IDS-STAGE036-REVIEW"',
                'current_task_id: "IDS-V0_1-STAGE036-REVIEW"',
                'next_gate_id: "IDS-STAGE037-P1-GATE"',
                'review_id: "IDS-STAGE036-REVIEW"',
                'task_id: "IDS-V0_1-STAGE036-REVIEW"',
                "STAGE036_STAGE_REVIEW.md",
            ],
            events_text: [
                '"event_id":"EVT-IDS-V0_1-STAGE036-REVIEW-',
                '"event_type":"stage_review"',
                '"task_id":"IDS-V0_1-STAGE036-REVIEW"',
                '"ACC-STAGE-036"',
                "STAGE036_STAGE_REVIEW.md",
                "IDS-STAGE037-P1-GATE",
            ],
        }
        for text, terms in required.items():
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)
        self.assertTrue(
            any(
                term in lock_text
                for term in (
                    'next_allowed_task_id: "IDS-V0_1-STAGE037-P1"',
                    'next_allowed_task_id: "IDS-V0_1-STAGE037-P2"',
                    'next_allowed_task_id: "IDS-V0_1-STAGE037-P3"',
                    'next_allowed_task_id: "IDS-V0_1-STAGE037-P4"',
                    'next_allowed_task_id: "IDS-V0_1-STAGE037-REVIEW"',
                )
            )
        )

    def test_review_rejects_unknown_safety_authorization_fields(self):
        module = self._load_checker_module()
        base = json.loads(INDEX.read_text(encoding="utf-8"))
        cases = {
            "top_level": lambda index: index.__setitem__(
                "live_execution_authorized", True
            ),
            "migration": lambda index: index["migration_contract"].__setitem__(
                "execute_now", True
            ),
            "candidate": lambda index: index["constraint_inventory"][
                "candidates"
            ][0].__setitem__("live_apply_allowed", True),
            "raw_metadata": lambda index: index["raw_metadata_boundary"].__setitem__(
                "open_allowed", True
            ),
            "real_data": lambda index: index["real_data_only_guard"].__setitem__(
                "synthetic_rows_allowed", True
            ),
            "storage": lambda index: index["guardrails"][
                "storage_boundary"
            ].__setitem__("stores_raw_payloads", True),
        }

        for name, mutate in cases.items():
            with self.subTest(case=name):
                index = copy.deepcopy(base)
                mutate(index)
                report = self._phase2_report(module, index)
                self.assertIn("contract_shape_results", report)
                self.assertFalse(report["contract_valid"], report)
                self.assertFalse(all(report["contract_shape_results"].values()))
                self.assertEqual(
                    "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT",
                    report["execution_state"],
                )

    def test_review_malformed_contract_and_missing_sources_fail_closed(self):
        module = self._load_checker_module()
        base = json.loads(INDEX.read_text(encoding="utf-8"))
        malformed_cases = {
            "null_required_tables": (
                "dependency_contract",
                "required_control_plane_tables",
            ),
            "null_forbidden_values": ("real_data_only_guard", "forbidden"),
        }
        for name, (container, field) in malformed_cases.items():
            with self.subTest(case=name):
                index = copy.deepcopy(base)
                index[container][field] = None
                try:
                    report = self._phase2_report(module, index)
                except Exception as exc:  # pragma: no cover - RED diagnostic
                    self.fail(f"{name} raised {type(exc).__name__}: {exc}")
                self.assertFalse(report["contract_valid"], report)
                self.assertEqual(
                    "BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT",
                    report["execution_state"],
                )

        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / "missing.sql"
            for field, kwargs in {
                "migration": {"migration_path": missing},
                "baseline": {"baseline_schema_path": missing},
            }.items():
                with self.subTest(missing_source=field):
                    try:
                        report = module.build_stage036_delivery_report(**kwargs)
                    except Exception as exc:  # pragma: no cover - RED diagnostic
                        self.fail(
                            f"missing {field} raised {type(exc).__name__}: {exc}"
                        )
                    self.assertFalse(report["delivery_contract_valid"], report)
                    self.assertEqual("FAIL_CLOSED", report["result"])
                    self.assertIn("失败关闭", report["chinese_owner_feedback"])

    def test_review_migration_pins_schema_and_guards_owned_objects(self):
        module = self._load_checker_module()
        sql = MIGRATION.read_text(encoding="utf-8")
        for term in [
            "SET LOCAL search_path = pg_catalog, public;",
            self.OWNERSHIP_MARKER,
            "COMMENT ON TABLE public.ids_state_value_registry",
            "COMMENT ON INDEX public.idx_ids_state_value_registry_active",
            "obj_description",
            "STAGE-036 apply blocked: pre-existing migration object requires recovery",
            "STAGE-036 rollback blocked: database object is not owned by this migration",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, sql)

        report = module.build_stage036_quality_constraint_report()
        migration_results = report["migration_contract_results"]
        self.assertIn("search_path_pinned", migration_results)
        self.assertIn("owned_object_guards_exact", migration_results)
        self.assertTrue(migration_results["search_path_pinned"])
        self.assertTrue(migration_results["owned_object_guards_exact"])

    def test_review_migration_runner_selects_one_section_and_blocks_unauthorized_up(self):
        self.assertTrue(
            MIGRATION_RUNNER.is_file(),
            f"missing migration section runner: {MIGRATION_RUNNER}",
        )
        down = subprocess.run(
            [sys.executable, "-B", str(MIGRATION_RUNNER), "--section", "down"],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, down.returncode, down.stderr)
        self.assertNotIn("-- migrate:up", down.stdout)
        self.assertIn("-- migrate:down", down.stdout)
        self.assertIn("DROP CONSTRAINT", down.stdout)
        self.assertNotIn("ADD CONSTRAINT", down.stdout)

        blocked_env = {
            key: value
            for key, value in __import__("os").environ.items()
            if key
            not in {
                "IDS_OWNER_AUTHORIZED_REAL_PROFILE_REF",
                "IDS_MIGRATION_BACKUP_CHECKPOINT_REF",
                "IDS_MIGRATION_ROLLBACK_PLAN_REF",
                "IDS_STAGE036_AUTHORIZATION_ENVELOPE",
            }
        }
        up = subprocess.run(
            [sys.executable, "-B", str(MIGRATION_RUNNER), "--section", "up"],
            cwd=ROOT.parent,
            env=blocked_env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, up.returncode)
        self.assertEqual("", up.stdout)
        self.assertIn("owner-authorized", up.stderr)

        index = json.loads(INDEX.read_text(encoding="utf-8"))
        migration_contract = index["migration_contract"]
        self.assertEqual(
            "BLOCKED_V0_1_NO_TRUSTED_AUTHORIZATION_OR_TARGET_BINDING",
            migration_contract["future_apply_command_ref"],
        )
        self.assertIn(
            "run_stage036_migration_section.py --section down",
            migration_contract["future_rollback_command_ref"],
        )
        self.assertNotIn("psql --section", migration_contract["future_rollback_command_ref"])

    def test_review_authorization_contract_binds_bounded_profile_queries(self):
        self.assertTrue(
            PROFILE_QUERIES.is_file(),
            f"missing profile query contract: {PROFILE_QUERIES}",
        )
        query_contract = json.loads(PROFILE_QUERIES.read_text(encoding="utf-8"))
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        queries = query_contract["queries"]
        by_id = {item["constraint_id"]: item for item in queries}
        self.assertEqual(
            Stage036DatabaseQualityConstraintsPhase2Tests.EXPECTED_CANDIDATE_CONSTRAINTS,
            set(by_id),
        )
        self.assertEqual(9, len(queries))
        for constraint_id, item in by_id.items():
            with self.subTest(constraint_id=constraint_id):
                sql = item["query_sql"]
                self.assertRegex(sql, r"^SELECT count\(\*\) AS violation_count FROM ")
                self.assertEqual(
                    hashlib.sha256(sql.encode("utf-8")).hexdigest(),
                    item["query_sha256"],
                )
                self.assertNotRegex(sql, r"(?i)SELECT\s+\*")
                self.assertNotIn("/Users/linzezhang/Downloads/IDS_MetaData", sql)

        envelope_contract = index["authorization_envelope_contract"]
        self.assertTrue(envelope_contract["required"])
        self.assertFalse(envelope_contract["runtime_authorization_default"])
        self.assertEqual(
            {constraint_id: item["query_sha256"] for constraint_id, item in by_id.items()},
            envelope_contract["candidate_query_sha256"],
        )
        candidates = {
            item["constraint_id"]: item
            for item in index["constraint_inventory"]["candidates"]
        }
        for constraint_id, query in by_id.items():
            candidate = candidates[constraint_id]
            with self.subTest(candidate_ref=constraint_id):
                self.assertEqual(query["query_id"], candidate["preflight_query_id"])
                self.assertEqual(
                    query["query_sha256"], candidate["preflight_query_sha256"]
                )
                self.assertEqual(
                    "002_database_quality_constraints.sql",
                    candidate["migration_ref"],
                )
                self.assertEqual(
                    "owner_authorized_zero_violation_evidence_required",
                    candidate["validation_evidence_ref"],
                )
                self.assertEqual(
                    "002_database_quality_constraints.sql#migrate:down",
                    candidate["rollback_ref"],
                )

    def test_review_dependency_indexes_are_bound_by_content_hash(self):
        module = self._load_checker_module()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        expected_hashes = {
            "stage030_control_plane_index_ref": "00779a914d7eb08ea94285cc07f9ae9583ca4d50a7d7f6d8f647cc9bdbd278cd",
            "stage031_migration_safety_index_ref": "cd1362d8bda358becc6d5cfc14d6e4f9a3b85ca3d6155d70fe2714fac66b2bb0",
            "stage032_connection_pool_index_ref": "2ffb32d423429c40e5198fe22c95fc15f038a06c92ce401aa7e4527d13d1b56d",
            "stage033_database_size_guard_index_ref": "008f582cb2d2a95d53f02a45b5f4acbd54f749d77ebdb216192f2b61db3ed419",
            "stage034_data_retention_table_index_ref": "0b579f93c623cd20e99752c9801f5c9bb14757e531697d687f87fe5c7c6c8504",
            "stage035_database_recovery_smoke_index_ref": "34cf0f28f921d0a136fc91256b7a5e9119d71cccbbb8db4bbc1f98bcb9f6345c",
        }
        self.assertEqual(
            expected_hashes,
            index["dependency_contract"]["dependency_index_sha256"],
        )
        report = self._phase2_report(module, index)
        self.assertTrue(
            report["source_integrity_results"]["dependency_content_hashes_match"]
        )

        tampered = copy.deepcopy(index)
        tampered["dependency_contract"]["dependency_index_sha256"][
            "stage035_database_recovery_smoke_index_ref"
        ] = "0" * 64
        report = self._phase2_report(module, tampered)
        self.assertFalse(report["contract_valid"], report)
        self.assertFalse(
            report["source_integrity_results"]["dependency_content_hashes_match"]
        )

    def test_review_tracked_snapshot_requires_real_git_tracked_paths_and_raw_hash(self):
        module = self._load_checker_module()
        report = module.build_stage036_delivery_report()
        binding = report["snapshot_binding"]
        self.assertTrue(binding["canonical_paths_bound"])
        self.assertTrue(binding["path_objects_verified"])
        self.assertTrue(binding["git_paths_tracked"])
        self.assertTrue(binding["tracked_snapshot_bound"])
        self.assertEqual(
            hashlib.sha256(INDEX.read_bytes()).hexdigest(),
            binding["index_raw_sha256"],
        )
        self.assertEqual(module.EXPECTED_INDEX_SHA256, binding["index_raw_sha256"])

        class SpoofPath:
            def __init__(self, real_path):
                self.real_path = real_path

            def resolve(self):
                return self.real_path.resolve()

            def read_text(self, encoding="utf-8"):
                return self.real_path.read_text(encoding=encoding)

            def as_posix(self):
                return self.real_path.as_posix()

        spoofed = module.build_stage036_delivery_report(
            index_path=SpoofPath(INDEX),
            migration_path=SpoofPath(MIGRATION),
            baseline_schema_path=SpoofPath(module.CONTROL_SCHEMA_PATH),
        )
        spoofed_binding = spoofed["snapshot_binding"]
        self.assertFalse(spoofed_binding["path_objects_verified"])
        self.assertFalse(spoofed_binding["tracked_snapshot_bound"])
        self.assertFalse(spoofed["delivery_contract_valid"])

    def test_review_runner_never_emits_live_up_and_rejects_boolean_zero(self):
        spec = importlib.util.spec_from_file_location(
            "stage036_migration_runner_review", MIGRATION_RUNNER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)

        self.assertEqual(
            hashlib.sha256(INDEX.read_bytes()).hexdigest(),
            runner.EXPECTED_INDEX_SHA256,
        )
        self.assertEqual(9, len(runner.EXPECTED_PROFILE_QUERY_SHA256))
        self.assertTrue(runner._zero_violation_count(0))
        for unsafe_zero in (False, 0.0, "0", None):
            with self.subTest(unsafe_zero=unsafe_zero):
                self.assertFalse(runner._zero_violation_count(unsafe_zero))

        sql = MIGRATION.read_text(encoding="utf-8")
        with self.assertRaises(runner.SelectionError):
            runner.select_migration_section(
                sql,
                "up",
                session_refs={"ids.owner_authorized_real_profile_ref": "ref"},
            )
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        authorization = index["authorization_envelope_contract"]
        self.assertFalse(authorization["trusted_signature_verifier_available"])
        self.assertFalse(authorization["target_binding_verifier_available"])
        self.assertFalse(authorization["live_up_emission_allowed"])
        self.assertEqual(
            "BLOCKED_V0_1_NO_TRUSTED_AUTHORIZATION_OR_TARGET_BINDING",
            index["migration_contract"]["future_apply_command_ref"],
        )

    def test_review_repeat_apply_blocks_existing_objects_and_down_is_atomic(self):
        module = self._load_checker_module()
        sql = MIGRATION.read_text(encoding="utf-8")
        up_sql, down_sql = sql.split("-- migrate:down", 1)
        self.assertIn(
            "STAGE-036 apply blocked: pre-existing migration object requires recovery",
            up_sql,
        )
        self.assertNotIn(
            "existing database object is not owned by this migration", up_sql
        )
        registry_guard = down_sql.index("DO $ids_quality_rollback_gate$")
        first_drop = down_sql.index("DROP CONSTRAINT IF EXISTS")
        self.assertLess(registry_guard, first_drop)

        down = subprocess.run(
            [sys.executable, "-B", str(MIGRATION_RUNNER), "--section", "down"],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, down.returncode, down.stderr)
        self.assertTrue(down.stdout.startswith("\\set ON_ERROR_STOP on\nBEGIN;\n"))
        self.assertTrue(down.stdout.rstrip().endswith("COMMIT;"))
        results = module.build_stage036_quality_constraint_report()[
            "migration_contract_results"
        ]
        for check_id in (
            "preexisting_object_fail_closed",
            "rollback_registry_guard_before_drops",
            "runner_atomic_transaction_contract",
        ):
            with self.subTest(check_id=check_id):
                self.assertTrue(results[check_id], results)

    def test_review_security_sources_are_git_bound_hashed_and_read_once(self):
        module = self._load_checker_module()
        source_paths = [
            module.PURSUE_ROOT
            / "postgresql_control_plane"
            / "control_plane_schema_index.json",
            module.PURSUE_ROOT
            / "schema_migration_safety"
            / "stage031_migration_safety_index.json",
            module.PURSUE_ROOT
            / "database_connection_pool"
            / "stage032_connection_pool_index.json",
            module.PURSUE_ROOT
            / "database_size_guard"
            / "stage033_database_size_guard_index.json",
            module.PURSUE_ROOT
            / "data_retention_table"
            / "stage034_data_retention_table_index.json",
            module.PURSUE_ROOT
            / "database_recovery_smoke"
            / "stage035_database_recovery_smoke_index.json",
            PROFILE_QUERIES,
            MIGRATION_RUNNER,
        ]
        canonical = {path.resolve() for path in source_paths}
        counts = {path: 0 for path in canonical}
        original_read_text = Path.read_text

        def counting_read_text(path, *args, **kwargs):
            resolved = path.resolve()
            if resolved in counts:
                counts[resolved] += 1
            return original_read_text(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", counting_read_text):
            report = module.build_stage036_delivery_report()

        self.assertEqual({path: 1 for path in canonical}, counts)
        binding = report["snapshot_binding"]
        self.assertTrue(binding["security_sources_git_tracked"])
        self.assertEqual(
            hashlib.sha256(PROFILE_QUERIES.read_bytes()).hexdigest(),
            binding["profile_queries_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(MIGRATION_RUNNER.read_bytes()).hexdigest(),
            binding["migration_runner_sha256"],
        )

    def test_review_checker_reports_current_reviewed_local_state(self):
        module = self._load_checker_module()
        report = module.build_stage036_delivery_report()
        self.assertEqual("completed_reviewed_local", report["stage_review_status"])
        self.assertEqual("IDS-STAGE037-P1-GATE", report["next_gate"])


if __name__ == "__main__":
    unittest.main()
