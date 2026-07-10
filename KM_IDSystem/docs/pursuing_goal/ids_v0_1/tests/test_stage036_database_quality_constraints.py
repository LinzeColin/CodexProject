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


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE036_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE036_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE036_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE036_PHASE4_CLOSEOUT.md"
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
SCRIPT = ROOT / "scripts" / "check_database_quality_constraints.py"
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
            "CREATE TABLE IF NOT EXISTS ids_state_value_registry",
            "PRIMARY KEY (state_namespace, state_value)",
            "VALIDATE CONSTRAINT",
            "SELECT EXISTS (SELECT 1 FROM ids_state_value_registry)",
            "STAGE-036 rollback blocked: ids_state_value_registry is not empty",
            "DROP TABLE IF EXISTS ids_state_value_registry",
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
                    "CREATE TABLE IF NOT EXISTS ids_state_value_registry",
                    "CREATE TABLE ids_state_value_registry",
                    1,
                ),
                "repeat_execution",
            ),
            (
                "missing_registry_rollback_query",
                migration_sql.replace(
                    "SELECT EXISTS (SELECT 1 FROM ids_state_value_registry)",
                    "SELECT FALSE",
                    1,
                ),
                "failure_rollback",
            ),
            (
                "constraint_guard_or_true",
                migration_sql.replace(
                    "AND conrelid = 'ids_chunks'::regclass\n  ) THEN",
                    "AND conrelid = 'ids_chunks'::regclass\n      OR TRUE\n  ) THEN",
                    1,
                ),
                "repeat_execution",
            ),
            (
                "registry_rollback_and_false",
                migration_sql.replace(
                    "SELECT EXISTS (SELECT 1 FROM ids_state_value_registry)'",
                    "SELECT EXISTS (SELECT 1 FROM ids_state_value_registry) AND FALSE'",
                    1,
                ),
                "failure_rollback",
            ),
            (
                "premature_registry_drop",
                migration_sql.replace(
                    "DO $ids_quality_rollback_gate$",
                    "DROP TABLE IF EXISTS ids_state_value_registry;\n\n"
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
                'status: "stage036_completed_local_pending_review"',
                'push_allowed: false',
                '      - "Phase 3"',
                '      - "Phase 4"',
                'next_phase: "stage_review_gate"',
                'next_gate: "IDS-STAGE036-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P4"',
                'acceptance_status: "phase4_closeout_complete"',
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
        self.assertEqual("IDS-STAGE036-REVIEW-GATE", report["next_gate"])
        self.assertEqual("pending_next_run", report["stage_review_status"])
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
        self.assertIn("STAGE-036 review", report["chinese_owner_feedback"])

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
            "CREATE TABLE IF NOT EXISTS ids_state_value_registry",
            "CREATE TABLE ids_state_value_registry",
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
            "noncanonical_path_validation_snapshot",
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
        self.assertEqual("IDS-STAGE036-REVIEW-GATE", payload["next_gate"])
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
                'status: "stage036_completed_local_pending_review"',
                '      - "Phase 4"',
                'next_phase: "stage_review_gate"',
                'next_gate: "IDS-STAGE036-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P4"',
                'acceptance_status: "phase4_closeout_complete"',
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


if __name__ == "__main__":
    unittest.main()
