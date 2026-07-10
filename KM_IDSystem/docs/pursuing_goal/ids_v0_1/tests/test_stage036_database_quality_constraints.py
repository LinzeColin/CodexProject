import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE036_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE036_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md"
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

    def test_cli_emits_phase2_json_without_writing_outputs(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("Phase 2", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE036-P2", payload["task_id"])
        self.assertTrue(payload["contract_valid"])
        self.assertFalse(payload["execution_ready"])
        self.assertEqual("IDS-STAGE036-P3-GATE", payload["next_gate"])

    def test_governance_tracks_phase2_and_preserves_upload_lock(self):
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        required = {
            lock_text: [
                'status: "stage036_phase2_in_progress"',
                'push_allowed: false',
                '      - "Phase 2"',
                'next_phase: "Phase 3"',
                'next_gate: "IDS-STAGE036-P3-GATE"',
                'current_task_id: "IDS-V0_1-STAGE036-P2"',
                'acceptance_status: "phase2_static_quality_constraint_contract_validated"',
            ],
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
        for text, terms in required.items():
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
