from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE032_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE032_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE032_PHASE2_CONNECTION_POOL_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE032_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE032_PHASE4_CLOSEOUT.md"
STAGE_REVIEW = PURSUE_ROOT / "STAGE032_STAGE_REVIEW.md"
INDEX = PURSUE_ROOT / "database_connection_pool" / "stage032_connection_pool_index.json"
SCRIPT = ROOT / "scripts" / "check_database_connection_pool.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage032DatabaseConnectionPoolPhase1Tests(unittest.TestCase):
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
            "STAGE-032 · 数据库连接与连接池基线",
            "IDS-V0_1-STAGE032-P1",
            "ACC-STAGE-032",
            "D06-S003",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-032_数据库连接与连接池基线.md",
            "a780cbf5eaf4b565dc0f0e7da1c503275bfa4e066d3409f8a258f13f09a0035a",
            "建立后端、worker、报告任务、检索任务的数据库连接策略",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_connection_pool_inputs_outputs_boundaries_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "database_connection_pool_contract_id",
            "backend_connection_profile",
            "worker_connection_profile",
            "report_task_connection_profile",
            "retrieval_task_connection_profile",
            "connection_url_ref",
            "credential_source_policy",
            "pool_size_boundary",
            "statement_timeout_boundary",
            "transaction_boundary",
            "retry_backoff_boundary",
            "healthcheck_boundary",
            "schema_migration_dependency_ref",
            "control_plane_storage_boundary",
            "hot_index_storage_boundary",
            "backup_restore_requirement",
            "CONNECTION_POOL_DRAFT",
            "CONNECTION_POOL_SECRETS_BLOCKED",
            "CONNECTION_POOL_RAW_CONTENT_BLOCKED",
            "CONNECTION_POOL_READY_FOR_PHASE2_SLICE",
            "只存控制面、状态和热索引",
            "不存 500GB 原始文件",
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
            "NO_CONNECTION_POOL_RUNTIME",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置或连接池 runtime",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage032_phase4_without_upload(self):
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
            "STAGE-032:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'acceptance_id: "ACC-STAGE-032"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE2_CONNECTION_POOL_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json",
            "KM_IDSystem/scripts/check_database_connection_pool.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage032_database_connection_pool.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        allowed_lock_status_terms = [
            'status: "stage032_completed_local_pending_review"',
            'status: "stage032_completed_reviewed_local"',
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
            'status: "stage035_completed_reviewed_local"',
            'status: "stage036_phase1_in_progress"',
            'status: "stage036_phase2_in_progress"',
            'status: "stage036_phase3_in_progress"',
            'status: "stage036_completed_local_pending_review"',
            'status: "stage036_completed_reviewed_local"',
            'status: "stage037_phase1_in_progress"',
            'status: "stage037_phase2_in_progress"',
        ]
        allowed_lock_next_terms = [
            'next_phase: "stage_review_gate"',
            'next_stage: "STAGE-033"',
            'next_phase: "Phase 2"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate: "IDS-STAGE033-P1-GATE"',
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
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
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
        allowed_lock_acceptance_terms = [
            'acceptance_status: "local_passed_pending_stage_review"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase2_size_guard_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'stage_id: "IDS-STAGE032"',
            'name: "STAGE-032 · 数据库连接与连接池基线"',
            'phase_id: "IDS-STAGE032-P1"',
            'status: "passed_with_local_evidence"',
            'phase_id: "IDS-STAGE032-P2"',
            'status: "passed_with_local_evidence"',
            'phase_id: "IDS-STAGE032-P3"',
            'status: "passed_with_local_evidence"',
            'phase_id: "IDS-STAGE032-P4"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE032-REVIEW"',
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
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
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
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
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
            '"event_id":"EVT-IDS-V0_1-STAGE032-P4-20260703-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE032-P4"',
            '"ACC-STAGE-032"',
            "STAGE032_PHASE4_CLOSEOUT.md",
            "build_stage032_delivery_report",
            "stage032_connection_pool_index.json",
            "check_database_connection_pool.py",
            "数据库连接与连接池基线",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_status_terms), allowed_lock_status_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_next_terms), allowed_lock_next_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_acceptance_terms), allowed_lock_acceptance_terms)
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


class Stage032DatabaseConnectionPoolPhase2Tests(unittest.TestCase):
    def test_phase2_static_connection_pool_artifacts_exist(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        self.assertTrue(INDEX.is_file(), f"missing connection pool index: {INDEX}")
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")

        phase2_text = PHASE2.read_text(encoding="utf-8")
        required_terms = [
            "ids.stage032.database_connection_pool.phase2.v1",
            "IDS-V0_1-STAGE032-P2",
            "ACC-STAGE-032",
            "backend_connection_profile",
            "worker_connection_profile",
            "report_task_connection_profile",
            "retrieval_task_connection_profile",
            "CONNECTION_POOL_STATIC_SLICE",
            "NO_POSTGRES_CONNECTION",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)

    def test_phase2_index_defines_four_profiles_and_guardrails(self):
        self.assertTrue(INDEX.is_file(), f"missing connection pool index: {INDEX}")
        index = json.loads(INDEX.read_text(encoding="utf-8"))

        self.assertEqual("ids.stage032.database_connection_pool.index.v1", index["schema_version"])
        self.assertEqual("STAGE-032", index["stage"])
        self.assertEqual("IDS-V0_1-STAGE032-P2", index["task_id"])
        self.assertEqual("ACC-STAGE-032", index["acceptance_id"])

        profiles = index["connection_profiles"]
        self.assertEqual(
            {
                "backend_connection_profile",
                "worker_connection_profile",
                "report_task_connection_profile",
                "retrieval_task_connection_profile",
            },
            set(profiles),
        )
        for name, profile in profiles.items():
            with self.subTest(profile=name):
                self.assertEqual("ENV:IDS_POSTGRES_DSN", profile["connection_url_ref"])
                self.assertGreaterEqual(profile["min_pool_size"], 0)
                self.assertGreater(profile["max_pool_size"], 0)
                self.assertLessEqual(profile["max_pool_size"], 10)
                self.assertLessEqual(profile["statement_timeout_ms"], 30000)
                self.assertLessEqual(profile["lock_timeout_ms"], 5000)
                self.assertLessEqual(profile["idle_timeout_ms"], 60000)
                self.assertFalse(profile["stores_raw_content"])
                self.assertFalse(profile["uses_plaintext_credentials"])

        guardrails = index["guardrails"]
        self.assertTrue(guardrails["credential_guard"]["secrets_forbidden"])
        self.assertEqual(10, guardrails["pool_size_guard"]["max_pool_size"])
        self.assertFalse(guardrails["storage_boundary_guard"]["stores_raw_files"])
        self.assertFalse(guardrails["storage_boundary_guard"]["stores_raw_database_rows"])
        self.assertFalse(guardrails["raw_metadata_boundary"]["content_access_allowed"])
        self.assertFalse(guardrails["raw_metadata_boundary"]["recursive_listing_allowed"])
        self.assertFalse(guardrails["raw_metadata_boundary"]["hashing_allowed"])
        self.assertFalse(guardrails["raw_metadata_boundary"]["copy_allowed"])
        self.assertFalse(guardrails["raw_metadata_boundary"]["modify_allowed"])
        self.assertFalse(guardrails["raw_metadata_boundary"]["dump_allowed"])
        self.assertIn("fake IDS business data", guardrails["real_data_only_guard"]["forbidden"])

    def test_phase2_checker_reports_pass_without_live_connection(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        payload = json.loads(completed.stdout)
        report = payload["connection_pool_report"]

        self.assertEqual("ids.stage032.database_connection_pool.phase2.v1", report["schema_version"])
        self.assertEqual("ids.stage032.database_connection_pool.index.v1", report["index_schema_version"])
        self.assertEqual("STAGE-032", report["stage"])
        self.assertEqual("Phase 2", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE032-P2", report["task_id"])
        self.assertEqual("ACC-STAGE-032", report["acceptance_id"])
        self.assertTrue(all(report["profile_results"].values()), report["profile_results"])
        self.assertTrue(all(report["guardrail_results"].values()), report["guardrail_results"])

        for key in [
            "does_not_connect_to_postgres",
            "does_not_execute_migration",
            "does_not_read_raw_metadata",
            "does_not_write_runtime_outputs",
            "does_not_use_fake_ids_business_data",
        ]:
            with self.subTest(key=key):
                self.assertTrue(report[key])


class Stage032DatabaseConnectionPoolPhase3Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage032_database_connection_pool", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase3_scenario_validation_report_covers_migration_pool_raw_and_constraints(self):
        module = self._load_checker_module()
        self.assertTrue(INDEX.is_file(), f"missing connection pool index: {INDEX}")

        report = module.build_stage032_scenario_validation_report(INDEX)

        self.assertEqual("ids.stage032.database_connection_pool.phase3.v1", report["schema_version"])
        self.assertEqual("STAGE-032", report["stage"])
        self.assertEqual("Phase 3", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE032-P3", report["task_id"])
        self.assertEqual("ACC-STAGE-032", report["acceptance_id"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

        scenario_results = report["scenario_results"]
        expected_scenarios = [
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "recovery_smoke",
            "raw_payload_block",
            "derived_output_limit",
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
            "credential_guard",
            "pool_size_guard",
            "timeout_guard",
            "transaction_guard",
            "retry_backoff_guard",
            "healthcheck_guard",
            "storage_boundary_guard",
            "raw_metadata_boundary_guard",
            "real_data_only_guard",
        ]:
            with self.subTest(constraint_id=constraint_id):
                self.assertIn(constraint_id, explanations)

    def test_phase3_doc_covers_static_scenarios_and_blocks_live_side_effects(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")
        required_terms = [
            "ids.stage032.database_connection_pool.phase3.v1",
            "IDS-V0_1-STAGE032-P3",
            "ACC-STAGE-032",
            "build_stage032_scenario_validation_report",
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "recovery_smoke",
            "raw_payload_block",
            "derived_output_limit",
            "connection_pool_boundary",
            "transaction_boundary",
            "constraint_error_explanations",
            "不连接 PostgreSQL",
            "不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
            "NO_PHASE4",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


class Stage032DatabaseConnectionPoolPhase4Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage032_database_connection_pool", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase4_delivery_report_closes_static_evidence_without_live_side_effects(self):
        module = self._load_checker_module()
        self.assertTrue(INDEX.is_file(), f"missing connection pool index: {INDEX}")

        report = module.build_stage032_delivery_report(INDEX)

        self.assertEqual("ids.stage032.database_connection_pool.phase4.v1", report["schema_version"])
        self.assertEqual("STAGE-032", report["stage"])
        self.assertEqual("Phase 4", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE032-P4", report["task_id"])
        self.assertEqual("ACC-STAGE-032", report["acceptance_id"])
        self.assertEqual("IDS-STAGE032-REVIEW-GATE", report["next_gate"])
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
            "static_connection_pool_contract_diff_not_executed",
            report["schema_diff"]["mode"],
        )
        self.assertEqual(
            "static_connection_pool_migration_output_not_executed",
            report["migration_output"]["mode"],
        )
        self.assertEqual(
            "static_connection_pool_recovery_log_not_executed",
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
        ]:
            with self.subTest(key=key):
                self.assertTrue(report[key])

    def test_phase4_doc_covers_closeout_delivery_review_boundary_and_raw_data_policy(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 evidence: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "ids.stage032.database_connection_pool.phase4.v1",
            "IDS-V0_1-STAGE032-P4",
            "ACC-STAGE-032",
            "build_stage032_delivery_report",
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "known_limits",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "chinese_owner_feedback",
            "IDS-STAGE032-REVIEW-GATE",
            "NO_BATCH_UPLOAD",
            "NO_STAGE_REVIEW_THIS_RUN",
            "NO_GITHUB_UPLOAD",
            "不连接 PostgreSQL",
            "不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


class Stage032DatabaseConnectionPoolReviewTests(unittest.TestCase):
    def test_stage_review_artifact_records_findings_repairs_and_no_upload_boundary(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        review_text = STAGE_REVIEW.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE032-REVIEW",
            "ACC-STAGE-032",
            "STAGE-032 · 数据库连接与连接池基线",
            "STAGE032-REVIEW-F1",
            "STAGE032-REVIEW-F2",
            "STAGE032-REVIEW-F3",
            "STAGE032-REVIEW-F4",
            "P0 source binding",
            "Phase 1 boundary",
            "Phase 2 connection pool checker",
            "Phase 3 scenario validation",
            "Phase 4 closeout",
            "build_stage032_delivery_report",
            "completed_reviewed_local",
            "IDS-STAGE033-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE033_THIS_RUN",
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
            'STAGE-032:',
            'status: "completed_reviewed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'review_status: "passed"',
            'next_stage: "STAGE-033"',
            'next_gate: "IDS-STAGE033-P1-GATE"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'acceptance_status: "reviewed_local_passed"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_STAGE_REVIEW.md",
            'push_allowed: false',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        allowed_lock_status_terms = [
            'status: "stage032_completed_reviewed_local"',
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
            'status: "stage035_completed_reviewed_local"',
            'status: "stage036_phase1_in_progress"',
            'status: "stage036_phase2_in_progress"',
            'status: "stage036_phase3_in_progress"',
            'status: "stage036_completed_local_pending_review"',
            'status: "stage036_completed_reviewed_local"',
            'status: "stage037_phase1_in_progress"',
            'status: "stage037_phase2_in_progress"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE033-P1-GATE"',
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
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
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
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE032"',
            'current_phase_id: "IDS-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
            'review_id: "IDS-STAGE032-REVIEW"',
            'task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'status: "completed"',
            "STAGE032_STAGE_REVIEW.md",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE032-REVIEW"',
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
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
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
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
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
            '"event_id":"EVT-IDS-V0_1-STAGE032-REVIEW-20260703-001"',
            '"event_type":"stage_review"',
            '"task_id":"IDS-V0_1-STAGE032-REVIEW"',
            '"ACC-STAGE-032"',
            "STAGE032_STAGE_REVIEW.md",
            "IDS-STAGE033-P1-GATE",
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
        for term in roadmap_terms[4:]:
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
