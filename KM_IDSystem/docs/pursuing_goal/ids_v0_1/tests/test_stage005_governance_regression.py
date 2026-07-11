import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "validate_stage005_governance_regression.py"
APP_ENTRY_INSTALLER = ROOT / "scripts" / "install_app_entries.sh"
APP_ENTRY_DIAGNOSTIC = ROOT / "scripts" / "diagnose_app_entry.sh"
APP_BUNDLE_BUILDER = ROOT / "scripts" / "build_app_bundle.sh"


class Stage005GovernanceRegressionTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(VALIDATOR.exists(), f"missing validator: {VALIDATOR}")
        spec = importlib.util.spec_from_file_location("stage005_validator", VALIDATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_app_entry_install_policy_installs_app_and_command_launchers(self):
        self.assertTrue(APP_ENTRY_INSTALLER.is_file(), f"missing installer: {APP_ENTRY_INSTALLER}")
        self.assertTrue(APP_ENTRY_DIAGNOSTIC.is_file(), f"missing diagnostic: {APP_ENTRY_DIAGNOSTIC}")
        self.assertTrue(APP_BUNDLE_BUILDER.is_file(), f"missing builder: {APP_BUNDLE_BUILDER}")

        installer_text = APP_ENTRY_INSTALLER.read_text(encoding="utf-8")
        builder_text = APP_BUNDLE_BUILDER.read_text(encoding="utf-8")
        required_installer_terms = [
            'APP_NAME="IDS Industrial Data System.app"',
            'COMMAND_NAME="IDS Industrial Data System.command"',
            "DOWNLOADS_APP",
            "APPLICATIONS_APP",
            "DOWNLOADS_COMMAND",
            "APPLICATIONS_COMMAND",
            'exec "$ROOT_DIR/scripts/run_local_services.sh"',
        ]

        for term in required_installer_terms:
            with self.subTest(term=term):
                self.assertIn(term, installer_text)

        self.assertIn("IDS Industrial Data System.app", builder_text)

    def test_phase2_report_validates_current_governance_surface(self):
        module = self._load_module()
        report = module.build_report(ROOT)

        self.assertTrue(report["valid"], report["issues"])
        self.assertEqual(report["stage"], "STAGE-005")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-005")
        self.assertEqual(report["missing_required_files"], [])
        self.assertEqual(report["event_json_errors"], [])
        self.assertEqual(report["forbidden_changed_paths"], [])
        self.assertEqual(report["tracked_forbidden_runtime_files"], [])
        self.assertTrue(all(report["data_boundary_checks"].values()), report["data_boundary_checks"])
        self.assertGreaterEqual(report["surface_counts"]["governance"], 1)
        self.assertGreaterEqual(report["surface_counts"]["scripts"], 1)
        self.assertGreaterEqual(report["accepted_name_hits"]["IDS / Industrial Data System"], 1)
        self.assertGreaterEqual(report["accepted_name_hits"]["ProductMetaDatabase"], 1)
        self.assertGreaterEqual(report["accepted_name_hits"]["FinanceMetaDatabase"], 1)

    def test_policy_helpers_separate_sparse_diagnostics_from_project_regressions(self):
        module = self._load_module()

        self.assertEqual(
            module.classify_governance_error(
                "[ERROR] root: Missing file: governance/schemas/project.schema.json"
            ),
            "sparse_worktree_diagnostic",
        )
        self.assertEqual(
            module.classify_governance_error(
                "[ERROR] Alpha: Registered project path missing: Alpha"
            ),
            "sparse_worktree_diagnostic",
        )
        self.assertEqual(
            module.classify_governance_error(
                "[ERROR] KM_IDSystem: Missing file: docs/governance/roadmap.yaml"
            ),
            "project_regression",
        )
        self.assertTrue(
            module.is_forbidden_runtime_path("KM_IDSystem/data/wuhan_kaiming.sqlite")
        )
        self.assertFalse(
            module.is_forbidden_runtime_path(
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_PHASE2_GOVERNANCE_REGRESSION.md"
            )
        )

    def test_phase_state_allows_phase3_after_phase2_completion(self):
        module = self._load_module()
        batch_text = """
  STAGE-005:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P3"
    acceptance_status: "phase3_validation_complete"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE005"
current_phase_id: "IDS-STAGE005-P3"
current_task_id: "IDS-V0_1-STAGE005-P3"
next_gate_id: "IDS-STAGE005-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_stage036_phase4_event_semantics_fail_closed(self):
        module = self._load_module()
        self.assertTrue(
            hasattr(module, "evaluate_required_event_semantics"),
            "missing required-event semantic validator",
        )
        valid_event = {
            "schema_version": "codexproject.event.v1",
            "event_id": "EVT-IDS-V0_1-STAGE036-P4-20260710-001",
            "project_id": "KM_IDSystem",
            "occurred_at": "2026-07-10T18:00:04Z",
            "event_type": "stage_closeout",
            "summary": "STAGE036 Phase 4 test event",
            "fact_level": "VERIFIED",
            "task_id": "IDS-V0_1-STAGE036-P4",
            "acceptance_ids": ["ACC-STAGE-036"],
            "changed_files": [
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE4_CLOSEOUT.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            ],
            "evidence_refs": [
                {
                    "ref": "KM_IDSystem/scripts/check_database_quality_constraints.py#build_stage036_delivery_report"
                },
                {
                    "ref": "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE4_CLOSEOUT.md"
                },
            ],
            "actor_role": "Codex",
            "notes": (
                "live_schema_diff_result=NOT_EXECUTED; "
                "live_migration_result=NOT_EXECUTED; "
                "live_constraint_validation_result=NOT_EXECUTED; "
                "live_recovery_smoke_result=NOT_EXECUTED; "
                "next_gate=IDS-STAGE036-REVIEW-GATE; push_allowed=false"
            ),
        }
        self.assertEqual([], module.evaluate_required_event_semantics([valid_event]))

        mutations = [
            {**valid_event, "event_type": "upload"},
            {**valid_event, "task_id": "IDS-V0_1-STAGE036-P3"},
            {
                **valid_event,
                "notes": valid_event["notes"].replace(
                    "IDS-STAGE036-REVIEW-GATE", "IDS-STAGE037-P1-GATE"
                ),
            },
            {
                **valid_event,
                "notes": valid_event["notes"].replace(
                    "push_allowed=false", "push_allowed=true"
                ),
            },
            {
                **valid_event,
                "notes": valid_event["notes"]
                + "; live_migration_result=EXECUTED",
            },
            {
                **valid_event,
                "notes": valid_event["notes"] + "; IDS-STAGE037-P1-GATE",
            },
            {
                **valid_event,
                "notes": valid_event["notes"] + "; push_allowed=true",
            },
            {
                **valid_event,
                "notes": valid_event["notes"] + "; push_allowed=TRUE",
            },
            {
                **valid_event,
                "notes": valid_event["notes"] + "; push_allowed = true",
            },
            {
                **valid_event,
                "notes": valid_event["notes"].replace(
                    "next_gate=IDS-STAGE036-REVIEW-GATE",
                    "previous_gate=IDS-STAGE036-REVIEW-GATE; next_gate=garbage",
                ),
            },
            {
                **valid_event,
                "notes": valid_event["notes"] + "; push_allowed=1",
            },
            {**valid_event, "changed_files": [{}]},
        ]
        for event in mutations:
            with self.subTest(event=event):
                self.assertTrue(module.evaluate_required_event_semantics([event]))
        for malformed in (None, [], "event", 1):
            with self.subTest(malformed=malformed):
                self.assertTrue(
                    module.evaluate_required_event_semantics([malformed])
                )

    def test_stage036_phase1_to_phase3_event_semantics_are_not_ignored(self):
        module = self._load_module()
        events_path = ROOT / "docs" / "governance" / "events.jsonl"
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        stage036_events = [
            event
            for event in events
            if event.get("task_id", "").startswith("IDS-V0_1-STAGE036-P")
        ]
        self.assertEqual([], module.evaluate_required_event_semantics(stage036_events))

        for task_id in (
            "IDS-V0_1-STAGE036-P1",
            "IDS-V0_1-STAGE036-P2",
            "IDS-V0_1-STAGE036-P3",
        ):
            with self.subTest(task_id=task_id):
                tampered = [dict(event) for event in stage036_events]
                target = next(event for event in tampered if event["task_id"] == task_id)
                target["event_type"] = "upload"
                self.assertTrue(module.evaluate_required_event_semantics(tampered))

        phase1 = next(
            event
            for event in stage036_events
            if event["task_id"] == "IDS-V0_1-STAGE036-P1"
        )
        for mutation in (
            {**phase1, "notes": phase1["notes"] + "; IDS-STAGE999-P1-GATE"},
            {
                **phase1,
                "notes": phase1["notes"]
                + "; live_migration_result=EXECUTED",
            },
            {**phase1, "push_allowed": True},
        ):
            with self.subTest(mutation=mutation):
                replaced = [
                    mutation if event["event_id"] == phase1["event_id"] else event
                    for event in stage036_events
                ]
                self.assertTrue(module.evaluate_required_event_semantics(replaced))

    def test_stage036_review_event_semantics_fail_closed(self):
        module = self._load_module()
        valid_event = {
            "schema_version": "codexproject.event.v1",
            "event_id": "EVT-IDS-V0_1-STAGE036-REVIEW-20260711-001",
            "project_id": "KM_IDSystem",
            "occurred_at": "2026-07-10T21:51:40Z",
            "event_type": "stage_review",
            "summary": "STAGE036 review test event",
            "fact_level": "VERIFIED",
            "task_id": "IDS-V0_1-STAGE036-REVIEW",
            "acceptance_ids": ["ACC-STAGE-036"],
            "changed_files": [
                "KM_IDSystem/scripts/check_database_quality_constraints.py",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_STAGE_REVIEW.md",
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml",
                "KM_IDSystem/docs/governance/roadmap.yaml",
                "KM_IDSystem/docs/governance/events.jsonl",
            ],
            "evidence_refs": [
                {
                    "ref": "KM_IDSystem/scripts/check_database_quality_constraints.py#build_stage036_delivery_report"
                },
                {
                    "ref": "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_STAGE_REVIEW.md"
                },
            ],
            "actor_role": "Codex",
            "notes": (
                "live_schema_diff_result=NOT_EXECUTED; "
                "live_migration_result=NOT_EXECUTED; "
                "live_constraint_validation_result=NOT_EXECUTED; "
                "live_recovery_smoke_result=NOT_EXECUTED; "
                "next_gate=IDS-STAGE037-P1-GATE; push_allowed=false"
            ),
        }
        self.assertEqual([], module.evaluate_required_event_semantics([valid_event]))
        for old, new in (
            ("stage_review", "upload"),
            ("IDS-STAGE037-P1-GATE", "IDS-STAGE036-REVIEW-GATE"),
            ("push_allowed=false", "push_allowed=true"),
            ("live_migration_result=NOT_EXECUTED", "live_migration_result=EXECUTED"),
        ):
            with self.subTest(old=old, new=new):
                tampered = dict(valid_event)
                if old == "stage_review":
                    tampered["event_type"] = new
                else:
                    tampered["notes"] = valid_event["notes"].replace(old, new)
                self.assertTrue(module.evaluate_required_event_semantics([tampered]))

        top_level_unsafe = dict(valid_event)
        top_level_unsafe["push_allowed"] = True
        self.assertTrue(
            module.evaluate_required_event_semantics([top_level_unsafe])
        )

    def test_ids_metadata_raw_boundary_requires_real_data_only_policy(self):
        module = self._load_module()
        root_lock_text = """
ids_metadata_raw_root: "/Users/linzezhang/Downloads/IDS_MetaData"
ids_metadata_raw_root_record: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
ids_metadata_raw_root_policy: "read-only; path is tracked in GitHub governance; raw database content is not committed, copied, scanned, moved, deleted, or modified"
real_data_only_policy: "fake business data and fabricated evidence are forbidden"
"""
        batch_text = """
data_boundary:
  ids_metadata_raw_root: "/Users/linzezhang/Downloads/IDS_MetaData"
  boundary_record: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
  raw_root_policy: "read-only; do not modify raw database content"
"""
        boundary_text = """
# IDS Metadata Raw Data Boundary
Local raw metadata root: `/Users/linzezhang/Downloads/IDS_MetaData`
Codex must not create, edit, delete, move, clean, rewrite, normalize, rename,
or compact files inside that local raw metadata root.
Raw directory content copied into GitHub: `no`
## Real Data Only Policy
New fake industrial records, fake database rows, fake business documents,
placeholder corpora, and fake business data are forbidden.
"""

        checks = module.evaluate_data_boundary(root_lock_text, batch_text, boundary_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage011_phase2_after_uploaded_batch(self):
        module = self._load_module()
        batch_text = """
status: "uploaded_to_github_main"
upload_gate:
  push_allowed: true
  gate_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"
  merged_sha: "2d418ccba1e16bcb940387c6e8152668fc2dccaf"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE011-P2"
    acceptance_status: "phase2_implementation_complete"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE011"
current_phase_id: "IDS-STAGE011-P2"
current_task_id: "IDS-V0_1-STAGE011-P2"
next_gate_id: "IDS-STAGE011-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage011_phase3_after_scenario_validation(self):
        module = self._load_module()
        batch_text = """
status: "uploaded_to_github_main"
upload_gate:
  push_allowed: true
  gate_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"
  merged_sha: "2d418ccba1e16bcb940387c6e8152668fc2dccaf"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE011-P3"
    acceptance_status: "phase3_scenario_validation_complete"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE011"
current_phase_id: "IDS-STAGE011-P3"
current_task_id: "IDS-V0_1-STAGE011-P3"
next_gate_id: "IDS-STAGE011-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage016_phase3_after_import_scenario_validation(self):
        module = self._load_module()
        batch_text = """
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-016:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE016-P3"
    acceptance_status: "phase3_scenario_validation_complete"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE016"
current_phase_id: "IDS-STAGE016-P3"
current_task_id: "IDS-V0_1-STAGE016-P3"
next_gate_id: "IDS-STAGE016-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE016-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE016-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage016_phase4_import_closeout_completion(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
    current_task_id: "IDS-V0_1-STAGE016-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE016"
current_phase_id: "IDS-STAGE016-P4"
current_task_id: "IDS-V0_1-STAGE016-P4"
next_gate_id: "IDS-STAGE017-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE016-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE016-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage011_phase4_closeout_completion(self):
        module = self._load_module()
        batch_text = """
status: "uploaded_to_github_main"
upload_gate:
  push_allowed: false
  gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-012"
    current_task_id: "IDS-V0_1-STAGE011-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE011"
current_phase_id: "IDS-STAGE011-P4"
current_task_id: "IDS-V0_1-STAGE011-P4"
next_gate_id: "IDS-STAGE012-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage012_phase1_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE012-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE012"
current_phase_id: "IDS-STAGE012-P1"
current_task_id: "IDS-V0_1-STAGE012-P1"
next_gate_id: "IDS-STAGE012-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage012_phase2_readonly_identity_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE012-P2"
    acceptance_status: "phase2_readonly_identity_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE012"
current_phase_id: "IDS-STAGE012-P2"
current_task_id: "IDS-V0_1-STAGE012-P2"
next_gate_id: "IDS-STAGE012-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage012_phase3_scenario_validation(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE012-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE012"
current_phase_id: "IDS-STAGE012-P3"
current_task_id: "IDS-V0_1-STAGE012-P3"
next_gate_id: "IDS-STAGE012-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage012_phase4_closeout_completion(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-013"
    current_task_id: "IDS-V0_1-STAGE012-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE012"
current_phase_id: "IDS-STAGE012-P4"
current_task_id: "IDS-V0_1-STAGE012-P4"
next_gate_id: "IDS-STAGE013-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage013_phase1_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE013-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE013"
current_phase_id: "IDS-STAGE013-P1"
current_task_id: "IDS-V0_1-STAGE013-P1"
next_gate_id: "IDS-STAGE013-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage013_phase2_fingerprint_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE013-P2"
    acceptance_status: "phase2_fingerprint_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE013"
current_phase_id: "IDS-STAGE013-P2"
current_task_id: "IDS-V0_1-STAGE013-P2"
next_gate_id: "IDS-STAGE013-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage013_phase3_scenario_validation(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE013-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE013"
current_phase_id: "IDS-STAGE013-P3"
current_task_id: "IDS-V0_1-STAGE013-P3"
next_gate_id: "IDS-STAGE013-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage013_phase4_closeout_completion(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-014"
    current_task_id: "IDS-V0_1-STAGE013-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE013"
current_phase_id: "IDS-STAGE013-P4"
current_task_id: "IDS-V0_1-STAGE013-P4"
next_gate_id: "IDS-STAGE014-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage014_phase1_scope_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE014-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE014"
current_phase_id: "IDS-STAGE014-P1"
current_task_id: "IDS-V0_1-STAGE014-P1"
next_gate_id: "IDS-STAGE014-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage014_phase2_manifest_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE014-P2"
    acceptance_status: "phase2_manifest_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE014"
current_phase_id: "IDS-STAGE014-P2"
current_task_id: "IDS-V0_1-STAGE014-P2"
next_gate_id: "IDS-STAGE014-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage014_phase3_scenario_validation(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE014-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE014"
current_phase_id: "IDS-STAGE014-P3"
current_task_id: "IDS-V0_1-STAGE014-P3"
next_gate_id: "IDS-STAGE014-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage014_phase4_closeout_completion(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-015"
    current_task_id: "IDS-V0_1-STAGE014-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE014"
current_phase_id: "IDS-STAGE014-P4"
current_task_id: "IDS-V0_1-STAGE014-P4"
next_gate_id: "IDS-STAGE015-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage015_phase1_scope_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE015-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE015"
current_phase_id: "IDS-STAGE015-P1"
current_task_id: "IDS-V0_1-STAGE015-P1"
next_gate_id: "IDS-STAGE015-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage015_phase2_duplicate_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE015-P2"
    acceptance_status: "phase2_duplicate_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE015"
current_phase_id: "IDS-STAGE015-P2"
current_task_id: "IDS-V0_1-STAGE015-P2"
next_gate_id: "IDS-STAGE015-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage015_phase3_scenario_validation(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE015-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE015"
current_phase_id: "IDS-STAGE015-P3"
current_task_id: "IDS-V0_1-STAGE015-P3"
next_gate_id: "IDS-STAGE015-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage015_phase4_closeout_completion(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-016"
    current_task_id: "IDS-V0_1-STAGE015-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE015"
current_phase_id: "IDS-STAGE015-P4"
current_task_id: "IDS-V0_1-STAGE015-P4"
next_gate_id: "IDS-STAGE016-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage016_phase1_scope_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE016-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE016"
current_phase_id: "IDS-STAGE016-P1"
current_task_id: "IDS-V0_1-STAGE016-P1"
next_gate_id: "IDS-STAGE016-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage016_phase2_import_idempotency_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE016-P2"
    acceptance_status: "phase2_import_idempotency_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE016"
current_phase_id: "IDS-STAGE016-P2"
current_task_id: "IDS-V0_1-STAGE016-P2"
next_gate_id: "IDS-STAGE016-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage017_phase1_original_material_regression_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE017-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE017"
current_phase_id: "IDS-STAGE017-P1"
current_task_id: "IDS-V0_1-STAGE017-P1"
next_gate_id: "IDS-STAGE017-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage017_phase2_original_regression_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE017-P2"
    acceptance_status: "phase2_regression_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE017"
current_phase_id: "IDS-STAGE017-P2"
current_task_id: "IDS-V0_1-STAGE017-P2"
next_gate_id: "IDS-STAGE017-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage017_phase3_original_regression_scenario_validation(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE017-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE017"
current_phase_id: "IDS-STAGE017-P3"
current_task_id: "IDS-V0_1-STAGE017-P3"
next_gate_id: "IDS-STAGE017-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage017_phase4_original_regression_closeout_completion(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-018"
    current_task_id: "IDS-V0_1-STAGE017-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE017"
current_phase_id: "IDS-STAGE017-P4"
current_task_id: "IDS-V0_1-STAGE017-P4"
next_gate_id: "IDS-STAGE018-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage018_phase1_import_preflight_scanner_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-018"
  STAGE-018:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE018-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE018"
current_phase_id: "IDS-STAGE018-P1"
current_task_id: "IDS-V0_1-STAGE018-P1"
next_gate_id: "IDS-STAGE018-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage018_phase2_import_preflight_scanner_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-018"
  STAGE-018:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE018-P2"
    acceptance_status: "phase2_preflight_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE018"
current_phase_id: "IDS-STAGE018-P2"
current_task_id: "IDS-V0_1-STAGE018-P2"
next_gate_id: "IDS-STAGE018-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE018-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE018-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage018_phase3_import_preflight_scenarios(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-018"
  STAGE-018:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE018-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE018"
current_phase_id: "IDS-STAGE018-P3"
current_task_id: "IDS-V0_1-STAGE018-P3"
next_gate_id: "IDS-STAGE018-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE018-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE018-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage018_phase4_import_preflight_closeout(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-011:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-012:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-013:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-014:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-015:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
  STAGE-016:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-017"
  STAGE-017:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-018"
  STAGE-018:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-019"
    current_task_id: "IDS-V0_1-STAGE018-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE018"
current_phase_id: "IDS-STAGE018-P4"
current_task_id: "IDS-V0_1-STAGE018-P4"
next_gate_id: "IDS-STAGE019-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE018-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE018-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage019_phase1_import_risk_estimator_scope_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-018:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-019"
    current_task_id: "IDS-V0_1-STAGE018-P4"
    acceptance_status: "local_passed"
  STAGE-019:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE019-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE019"
current_phase_id: "IDS-STAGE019-P1"
current_task_id: "IDS-V0_1-STAGE019-P1"
next_gate_id: "IDS-STAGE019-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE018-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE019-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage019_phase2_import_risk_estimator_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-019:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE019-P2"
    acceptance_status: "phase2_risk_estimator_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE019"
current_phase_id: "IDS-STAGE019-P2"
current_task_id: "IDS-V0_1-STAGE019-P2"
next_gate_id: "IDS-STAGE019-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage019_phase3_import_risk_estimator_scenarios(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-019:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE019-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE019"
current_phase_id: "IDS-STAGE019-P3"
current_task_id: "IDS-V0_1-STAGE019-P3"
next_gate_id: "IDS-STAGE019-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage019_phase4_import_risk_estimator_closeout(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-019:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-020"
    current_task_id: "IDS-V0_1-STAGE019-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE019"
current_phase_id: "IDS-STAGE019-P4"
current_task_id: "IDS-V0_1-STAGE019-P4"
next_gate_id: "IDS-STAGE020-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage020_phase1_import_cost_estimator_boundary(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-019:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-020"
    current_task_id: "IDS-V0_1-STAGE019-P4"
    acceptance_status: "local_passed"
  STAGE-020:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE020-P1"
    acceptance_status: "phase1_scope_boundary_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-STAGE020-P1"
current_task_id: "IDS-V0_1-STAGE020-P1"
next_gate_id: "IDS-STAGE020-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE019-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE020-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage021_phase1_preflight_confirmation_ui_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE021-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE021-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE021"
current_phase_id: "IDS-STAGE021-P1"
current_task_id: "IDS-V0_1-STAGE021-P1"
next_gate_id: "IDS-STAGE021-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"
          status: "completed"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage021_phase2_preflight_confirmation_ui_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE021-P2"
    acceptance_status: "phase2_preflight_confirmation_ui_slice_complete"
    next_gate: "IDS-STAGE021-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE021"
current_phase_id: "IDS-STAGE021-P2"
current_task_id: "IDS-V0_1-STAGE021-P2"
next_gate_id: "IDS-STAGE021-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage021_phase3_preflight_confirmation_ui_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE021-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE021-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE021"
current_phase_id: "IDS-STAGE021-P3"
current_task_id: "IDS-V0_1-STAGE021-P3"
next_gate_id: "IDS-STAGE021-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage021_phase4_preflight_confirmation_ui_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE021"
current_phase_id: "IDS-STAGE021-P4"
current_task_id: "IDS-V0_1-STAGE021-P4"
next_gate_id: "IDS-STAGE022-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage022_phase1_data_priority_queue_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE022-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE022-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE022"
current_phase_id: "IDS-STAGE022-P1"
current_task_id: "IDS-V0_1-STAGE022-P1"
next_gate_id: "IDS-STAGE022-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage022_phase2_data_priority_queue_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE022-P2"
    acceptance_status: "phase2_priority_queue_slice_complete"
    next_gate: "IDS-STAGE022-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE022"
current_phase_id: "IDS-STAGE022-P2"
current_task_id: "IDS-V0_1-STAGE022-P2"
next_gate_id: "IDS-STAGE022-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage022_phase3_data_priority_queue_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE022-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE022-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE022"
current_phase_id: "IDS-STAGE022-P3"
current_task_id: "IDS-V0_1-STAGE022-P3"
next_gate_id: "IDS-STAGE022-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage022_phase4_data_priority_queue_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE022"
current_phase_id: "IDS-STAGE022-P4"
current_task_id: "IDS-V0_1-STAGE022-P4"
next_gate_id: "IDS-STAGE023-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage023_phase1_preflight_scenario_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE023-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE023-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE023"
current_phase_id: "IDS-STAGE023-P1"
current_task_id: "IDS-V0_1-STAGE023-P1"
next_gate_id: "IDS-STAGE023-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage023_phase2_preflight_scenario_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE023-P2"
    acceptance_status: "phase2_preflight_scenario_slice_complete"
    next_gate: "IDS-STAGE023-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE023"
current_phase_id: "IDS-STAGE023-P2"
current_task_id: "IDS-V0_1-STAGE023-P2"
next_gate_id: "IDS-STAGE023-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage023_phase3_preflight_scenario_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE023-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE023-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE023"
current_phase_id: "IDS-STAGE023-P3"
current_task_id: "IDS-V0_1-STAGE023-P3"
next_gate_id: "IDS-STAGE023-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage023_phase4_preflight_scenario_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-024"
    current_task_id: "IDS-V0_1-STAGE023-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE024-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE023"
current_phase_id: "IDS-STAGE023-P4"
current_task_id: "IDS-V0_1-STAGE023-P4"
next_gate_id: "IDS-STAGE024-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage024_phase1_archive_threat_model_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-024"
    current_task_id: "IDS-V0_1-STAGE023-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE024-P1-GATE"
  STAGE-024:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE024-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE024-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE024"
current_phase_id: "IDS-STAGE024-P1"
current_task_id: "IDS-V0_1-STAGE024-P1"
next_gate_id: "IDS-STAGE024-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage024_phase2_archive_safe_extraction_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-024"
    current_task_id: "IDS-V0_1-STAGE023-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE024-P1-GATE"
  STAGE-024:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE024-P2"
    acceptance_status: "phase2_safe_extraction_slice_complete"
    next_gate: "IDS-STAGE024-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE024"
current_phase_id: "IDS-STAGE024-P2"
current_task_id: "IDS-V0_1-STAGE024-P2"
next_gate_id: "IDS-STAGE024-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage024_phase3_archive_threat_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-024"
    current_task_id: "IDS-V0_1-STAGE023-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE024-P1-GATE"
  STAGE-024:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE024-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE024-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE024"
current_phase_id: "IDS-STAGE024-P3"
current_task_id: "IDS-V0_1-STAGE024-P3"
next_gate_id: "IDS-STAGE024-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage024_phase4_archive_threat_model_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-022:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-023"
    current_task_id: "IDS-V0_1-STAGE022-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE023-P1-GATE"
  STAGE-023:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-024"
    current_task_id: "IDS-V0_1-STAGE023-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE024-P1-GATE"
  STAGE-024:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-025"
    current_task_id: "IDS-V0_1-STAGE024-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE025-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE024"
current_phase_id: "IDS-STAGE024-P4"
current_task_id: "IDS-V0_1-STAGE024-P4"
next_gate_id: "IDS-STAGE025-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE022-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE022-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE023-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE023-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage025_phase1_safe_extraction_engine_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-021:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-022"
    current_task_id: "IDS-V0_1-STAGE021-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE022-P1-GATE"
  STAGE-024:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-025"
    current_task_id: "IDS-V0_1-STAGE024-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE025-P1-GATE"
  STAGE-025:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE025-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE025-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE025"
current_phase_id: "IDS-STAGE025-P1"
current_task_id: "IDS-V0_1-STAGE025-P1"
next_gate_id: "IDS-STAGE025-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE021-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE025-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage025_phase2_safe_extraction_engine_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-024:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-025"
    current_task_id: "IDS-V0_1-STAGE024-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE025-P1-GATE"
  STAGE-025:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE025-P2"
    acceptance_status: "phase2_safe_extraction_engine_slice_complete"
    next_gate: "IDS-STAGE025-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE025"
current_phase_id: "IDS-STAGE025-P2"
current_task_id: "IDS-V0_1-STAGE025-P2"
next_gate_id: "IDS-STAGE025-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE025-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage025_phase3_safe_extraction_engine_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-024:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-025"
    current_task_id: "IDS-V0_1-STAGE024-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE025-P1-GATE"
  STAGE-025:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE025-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE025-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE025"
current_phase_id: "IDS-STAGE025-P3"
current_task_id: "IDS-V0_1-STAGE025-P3"
next_gate_id: "IDS-STAGE025-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE025-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage025_phase4_safe_extraction_engine_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-024:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-025"
    current_task_id: "IDS-V0_1-STAGE024-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE025-P1-GATE"
  STAGE-025:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-026"
    current_task_id: "IDS-V0_1-STAGE025-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE026-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE025"
current_phase_id: "IDS-STAGE025-P4"
current_task_id: "IDS-V0_1-STAGE025-P4"
next_gate_id: "IDS-STAGE026-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE024-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE025-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage020_phase2_import_cost_estimator_slice(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-019:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-020"
    current_task_id: "IDS-V0_1-STAGE019-P4"
    acceptance_status: "local_passed"
  STAGE-020:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE020-P2"
    acceptance_status: "phase2_cost_estimator_slice_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-STAGE020-P2"
current_task_id: "IDS-V0_1-STAGE020-P2"
next_gate_id: "IDS-STAGE020-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage020_phase3_import_cost_estimator_scenarios(self):
        module = self._load_module()
        batch_text = """
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-020:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE020-P3"
    acceptance_status: "phase3_scenario_validation_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-STAGE020-P3"
current_task_id: "IDS-V0_1-STAGE020-P3"
next_gate_id: "IDS-STAGE020-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_changed_path_policy_allows_stage011_phase2_files(self):
        module = self._load_module()
        allowed_paths = [
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE2_SAFE_MODE_BASELINE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE2_READONLY_IDENTITY_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE2_FILE_FINGERPRINT_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE2_MANIFEST_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE2_DUPLICATE_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE2_REGRESSION_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE017_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE2_PREFLIGHT_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE018_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE2_RISK_ESTIMATOR_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE019_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE2_COST_ESTIMATOR_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage018_import_preflight.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage019_import_risk_estimator.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage020_import_cost_estimator.py",
            "KM_IDSystem/scripts/check_import_cost_estimator.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage017_original_regression.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_duplicate_detection.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py",
            "KM_IDSystem/scripts/check_safe_mode_baseline.py",
            "KM_IDSystem/scripts/check_original_raw_identity.py",
            "KM_IDSystem/scripts/check_file_fingerprint.py",
            "KM_IDSystem/scripts/check_manifest_generation.py",
            "KM_IDSystem/scripts/check_duplicate_files.py",
            "KM_IDSystem/scripts/check_import_idempotency.py",
            "KM_IDSystem/scripts/check_original_regression.py",
            "KM_IDSystem/scripts/check_import_preflight.py",
            "KM_IDSystem/scripts/check_import_risk_estimator.py",
        ]

        for path in allowed_paths:
            with self.subTest(path=path):
                self.assertTrue(module._is_allowed_changed_path(path))

    def test_phase_state_allows_phase4_closeout_completion(self):
        module = self._load_module()
        batch_text = """
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-006"
    current_task_id: "IDS-V0_1-STAGE005-P4"
    acceptance_status: "local_passed"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE005"
current_phase_id: "IDS-STAGE005-P4"
current_task_id: "IDS-V0_1-STAGE005-P4"
next_gate_id: "IDS-STAGE006-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage020_phase4_closeout_and_batch_review_gate(self):
        module = self._load_module()
        batch_text = """
status: "ready_for_tenth_stage_review_no_github_upload"
upload_gate:
  push_allowed: false
  review_gate: "BATCH011_020_REVIEW_GATE"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-020:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-021"
    current_task_id: "IDS-V0_1-STAGE020-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-STAGE020-P4"
current_task_id: "IDS-V0_1-STAGE020-P4"
next_gate_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P4"
          status: "passed_no_github_upload_until_batch_review"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_batch011_020_review_gate_evidence_records_local_review_without_upload(self):
        review_gate = ROOT / "docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md"

        self.assertTrue(review_gate.exists(), f"missing review gate: {review_gate}")

        text = review_gate.read_text(encoding="utf-8")
        required_markers = [
            "IDS-V0_1-BATCH-011-020-REVIEW-GATE",
            "STAGE-011..STAGE-020",
            "BATCH011_020_UPLOAD_LOCK.yaml",
            "Ten-stage completion",
            "Durable evidence files",
            "Owner render",
            "raw data boundary",
            "push_allowed=false",
            "No GitHub upload",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "repair finding",
            "next allowed gate: IDS-V0_1-BATCH-011-020-UPLOAD-GATE",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_phase_state_allows_batch011_020_reviewed_pending_upload_gate(self):
        module = self._load_module()
        batch_text = """
status: "reviewed_ready_for_upload_no_github_upload"
review_task_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"
review_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_REVIEW_GATE.md"
upload_gate:
  push_allowed: false
  review_gate: "BATCH011_020_REVIEW_GATE"
  gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-020:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-021"
    current_task_id: "IDS-V0_1-STAGE020-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"
current_task_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"
next_gate_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE020-P4"
          status: "passed_no_github_upload_until_batch_review"
        phase_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"
          status: "passed_no_github_upload_until_upload_gate"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_batch011_020_upload_gate_evidence_records_github_main_strategy(self):
        upload_gate = ROOT / "docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md"

        self.assertTrue(upload_gate.exists(), f"missing upload gate: {upload_gate}")

        text = upload_gate.read_text(encoding="utf-8")
        required_markers = [
            "IDS-V0_1-BATCH-011-020-UPLOAD-GATE",
            "STAGE-011..STAGE-020",
            "BATCH011_020_REVIEW_GATE.md",
            "BATCH011_020_UPLOAD_LOCK.yaml",
            "GitHub open PR/issue precheck",
            "push_allowed=true",
            "PR targeting `main`",
            "No STAGE-021",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "raw database content was not read",
            "app entry reinstall",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_batch021_030_upload_lock_records_terminal_main_merge_evidence(self):
        upload_lock = ROOT / "docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml"

        text = upload_lock.read_text(encoding="utf-8")
        required_markers = [
            'status: "uploaded_to_github_main"',
            'github_pr: "https://github.com/LinzeColin/CodexProject/pull/272"',
            'merged_sha: "88a428c7901226bd44d5e4ff106cd51d74b550fe"',
            "post_merge_open_prs: 0",
            "post_merge_open_issues: 0",
            'downloads_command: "/Users/linzezhang/Downloads/IDS Industrial Data System.command"',
            'applications_command: "/Applications/IDS Industrial Data System.command"',
            'launcher_root_dir: "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS/KM_IDSystem"',
            'current_task_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"',
            'next_allowed_task_id: "IDS-STAGE031-P1-GATE"',
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_phase_state_allows_batch011_020_upload_gate_pending_github_merge(self):
        module = self._load_module()
        batch_text = """
status: "local_batch_upload_gate_passed_pending_github_merge"
upload_gate:
  push_allowed: true
  review_gate: "BATCH011_020_REVIEW_GATE"
  gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
  gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-020:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-021"
    current_task_id: "IDS-V0_1-STAGE020-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
current_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
next_gate_id: "IDS-V0_1-BATCH-011-020-GITHUB-MERGE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-V0_1-BATCH-011-020-REVIEW-GATE"
          status: "passed_no_github_upload_until_upload_gate"
        phase_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
          status: "passed_pending_github_merge"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_batch011_020_uploaded_terminal_state(self):
        module = self._load_module()
        batch_text = """
status: "uploaded_to_github_main"
upload_gate:
  push_allowed: true
  gate_task_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
  gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_GATE.md"
  github_pr: "https://github.com/LinzeColin/CodexProject/pull/271"
  merged_sha: "61fcb5295c6e0046059eba236c4cedbdaa2f2fed"
  post_merge_open_prs: 0
  post_merge_open_issues: 0
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-020:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-021"
    current_task_id: "IDS-V0_1-STAGE020-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE020"
current_phase_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"
current_task_id: "IDS-V0_1-BATCH-011-020-MAIN-MERGED"
next_gate_id: "IDS-STAGE021-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-V0_1-BATCH-011-020-UPLOAD-GATE"
          status: "uploaded_to_github_main"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage026_phase1_archive_manifest_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-025:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-026"
    current_task_id: "IDS-V0_1-STAGE025-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE026-P1-GATE"
  STAGE-026:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE026-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE026-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE026"
current_phase_id: "IDS-STAGE026-P1"
current_task_id: "IDS-V0_1-STAGE026-P1"
next_gate_id: "IDS-STAGE026-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE025-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE026-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage026_phase2_archive_manifest_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-025:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-026"
    current_task_id: "IDS-V0_1-STAGE025-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE026-P1-GATE"
  STAGE-026:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE026-P2"
    acceptance_status: "phase2_archive_manifest_slice_complete"
    next_gate: "IDS-STAGE026-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE026"
current_phase_id: "IDS-STAGE026-P2"
current_task_id: "IDS-V0_1-STAGE026-P2"
next_gate_id: "IDS-STAGE026-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage026_phase3_archive_manifest_scenario_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-026:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE026-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE026-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE026"
current_phase_id: "IDS-STAGE026-P3"
current_task_id: "IDS-V0_1-STAGE026-P3"
next_gate_id: "IDS-STAGE026-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage026_phase4_archive_manifest_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-026:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-027"
    current_task_id: "IDS-V0_1-STAGE026-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE027-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE026"
current_phase_id: "IDS-STAGE026-P4"
current_task_id: "IDS-V0_1-STAGE026-P4"
next_gate_id: "IDS-STAGE027-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage027_phase1_reingest_extracted_files_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-026:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-027"
    current_task_id: "IDS-V0_1-STAGE026-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE027-P1-GATE"
  STAGE-027:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE027-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE027-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE027"
current_phase_id: "IDS-STAGE027-P1"
current_task_id: "IDS-V0_1-STAGE027-P1"
next_gate_id: "IDS-STAGE027-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE026-P4"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage027_phase2_reingest_extracted_files_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-027:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE027-P2"
    acceptance_status: "phase2_reingest_slice_complete"
    next_gate: "IDS-STAGE027-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE027"
current_phase_id: "IDS-STAGE027-P2"
current_task_id: "IDS-V0_1-STAGE027-P2"
next_gate_id: "IDS-STAGE027-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage027_phase3_reingest_scenario_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-027:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE027-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE027-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE027"
current_phase_id: "IDS-STAGE027-P3"
current_task_id: "IDS-V0_1-STAGE027-P3"
next_gate_id: "IDS-STAGE027-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage027_phase4_reingest_closeout_completion(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage027_completed_local_pending_stage028"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-027:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-028"
    current_task_id: "IDS-V0_1-STAGE027-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE028-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE027"
current_phase_id: "IDS-STAGE027-P4"
current_task_id: "IDS-V0_1-STAGE027-P4"
next_gate_id: "IDS-STAGE028-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage028_phase1_archive_adversarial_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage028_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-027:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-028"
    current_task_id: "IDS-V0_1-STAGE027-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE028-P1-GATE"
  STAGE-028:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE028-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE028-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE028"
current_phase_id: "IDS-STAGE028-P1"
current_task_id: "IDS-V0_1-STAGE028-P1"
next_gate_id: "IDS-STAGE028-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P4"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage028_phase2_archive_adversarial_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage028_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-027:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-028"
    current_task_id: "IDS-V0_1-STAGE027-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE028-P1-GATE"
  STAGE-028:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE028-P2"
    acceptance_status: "phase2_archive_adversarial_slice_complete"
    next_gate: "IDS-STAGE028-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE028"
current_phase_id: "IDS-STAGE028-P2"
current_task_id: "IDS-V0_1-STAGE028-P2"
next_gate_id: "IDS-STAGE028-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P4"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage028_phase3_archive_adversarial_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage028_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-027:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-028"
    current_task_id: "IDS-V0_1-STAGE027-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE028-P1-GATE"
  STAGE-028:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE028-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE028-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE028"
current_phase_id: "IDS-STAGE028-P3"
current_task_id: "IDS-V0_1-STAGE028-P3"
next_gate_id: "IDS-STAGE028-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE027-P4"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage028_phase4_archive_adversarial_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage028_completed_local_pending_stage029"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-028:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-029"
    current_task_id: "IDS-V0_1-STAGE028-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE029-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE028"
current_phase_id: "IDS-STAGE028-P4"
current_task_id: "IDS-V0_1-STAGE028-P4"
next_gate_id: "IDS-STAGE029-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage029_phase1_archive_cleanup_allowlist_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage029_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-028:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-029"
    current_task_id: "IDS-V0_1-STAGE028-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE029-P1-GATE"
  STAGE-029:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE029-P1"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE029-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE029"
current_phase_id: "IDS-STAGE029-P1"
current_task_id: "IDS-V0_1-STAGE029-P1"
next_gate_id: "IDS-STAGE029-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE028-P4"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage029_phase2_archive_cleanup_allowlist_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage029_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-029:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE029-P2"
    acceptance_status: "phase2_cleanup_allowlist_slice_complete"
    next_gate: "IDS-STAGE029-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE029"
current_phase_id: "IDS-STAGE029-P2"
current_task_id: "IDS-V0_1-STAGE029-P2"
next_gate_id: "IDS-STAGE029-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage029_phase3_archive_cleanup_scenario_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage029_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-029:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE029-P3"
    acceptance_status: "phase3_scenario_validation_complete"
    next_gate: "IDS-STAGE029-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE029"
current_phase_id: "IDS-STAGE029-P3"
current_task_id: "IDS-V0_1-STAGE029-P3"
next_gate_id: "IDS-STAGE029-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage029_phase4_archive_cleanup_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage029_completed_local_pending_stage030"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-029:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-030"
    current_task_id: "IDS-V0_1-STAGE029-P4"
    acceptance_status: "local_passed"
    next_gate: "IDS-STAGE030-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE029"
current_phase_id: "IDS-STAGE029-P4"
current_task_id: "IDS-V0_1-STAGE029-P4"
next_gate_id: "IDS-STAGE030-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE029-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_completed_batch_upload_gate_after_stage005(self):
        module = self._load_module()
        batch_text = """
status: "local_batch_upload_gate_passed_pending_github_merge"
upload_gate:
  push_allowed: true
  gate_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-006"
    current_task_id: "IDS-V0_1-STAGE005-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE010"
current_phase_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"
current_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"
next_gate_id: "IDS-V0_1-BATCH-001-010-GITHUB-MERGE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_uploaded_batch_terminal_state_after_stage005(self):
        module = self._load_module()
        batch_text = """
status: "uploaded_to_github_main"
upload_gate:
  push_allowed: true
  gate_task_id: "IDS-V0_1-BATCH-001-010-UPLOAD-GATE"
  merged_sha: "2d418ccba1e16bcb940387c6e8152668fc2dccaf"
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-006"
    current_task_id: "IDS-V0_1-STAGE005-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE010"
current_phase_id: "IDS-V0_1-BATCH-001-010-MAIN-MERGED"
current_task_id: "IDS-V0_1-BATCH-001-010-MAIN-MERGED"
next_gate_id: "IDS-STAGE011-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage030_phase1_postgresql_control_plane_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage030_phase1_in_progress"
stage_progress:
  STAGE-029:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-030"
    current_task_id: "IDS-V0_1-STAGE029-P4"
    acceptance_status: "local_passed"
  STAGE-030:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE030-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE030-P1"
    acceptance_status: "phase1_scope_boundary_defined"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-STAGE030-P1"
current_task_id: "IDS-V0_1-STAGE030-P1"
next_gate_id: "IDS-STAGE030-P2-GATE"
        phase_id: "IDS-STAGE029-P4"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE030-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage030_phase2_postgresql_control_plane_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage030_phase2_in_progress"
stage_progress:
  STAGE-030:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE030-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE030-P2"
    acceptance_status: "phase2_schema_migration_slice_complete"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-STAGE030-P2"
current_task_id: "IDS-V0_1-STAGE030-P2"
next_gate_id: "IDS-STAGE030-P3-GATE"
        phase_id: "IDS-STAGE030-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage030_phase3_postgresql_control_plane_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage030_phase3_in_progress"
stage_progress:
  STAGE-030:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    next_gate: "IDS-STAGE030-P4-GATE"
    current_task_id: "IDS-V0_1-STAGE030-P3"
    acceptance_status: "phase3_scenario_validation_complete"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-STAGE030-P3"
current_task_id: "IDS-V0_1-STAGE030-P3"
next_gate_id: "IDS-STAGE030-P4-GATE"
        phase_id: "IDS-STAGE030-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage030_phase4_closeout_pending_batch_review(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-021-030"
status: "stage030_completed_local_pending_batch_review"
stage_progress:
  STAGE-030:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "batch_review_gate"
    next_gate: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE030-P4"
    acceptance_status: "local_passed"
upload_gate:
  push_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-STAGE030-P4"
current_task_id: "IDS-V0_1-STAGE030-P4"
next_gate_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
        phase_id: "IDS-STAGE030-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_batch021_030_review_gate_evidence_records_local_review_without_upload(self):
        review_gate = ROOT / "docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md"

        self.assertTrue(review_gate.exists(), f"missing review gate: {review_gate}")

        text = review_gate.read_text(encoding="utf-8")
        required_markers = [
            "IDS-V0_1-BATCH-021-030-REVIEW-GATE",
            "STAGE-021..STAGE-030",
            "BATCH021_030_UPLOAD_LOCK.yaml",
            "Ten-stage completion",
            "Durable evidence files",
            "Owner render",
            "raw data boundary",
            "push_allowed=false",
            "No GitHub upload",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "repair finding",
            "next allowed gate: IDS-V0_1-BATCH-021-030-UPLOAD-GATE",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_phase_state_allows_batch021_030_reviewed_pending_upload_gate(self):
        module = self._load_module()
        batch_text = """
status: "reviewed_ready_for_upload_no_github_upload"
review_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
review_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_REVIEW_GATE.md"
upload_gate:
  push_allowed: false
  review_gate: "BATCH021_030_REVIEW_GATE"
  gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
stage_progress:
  STAGE-030:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "batch_review_gate"
    current_task_id: "IDS-V0_1-STAGE030-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
current_task_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
next_gate_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
        phase_id: "IDS-STAGE030-P4"
          status: "passed_no_github_upload_until_batch_review"
        phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
          status: "passed_no_github_upload_until_upload_gate"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_batch021_030_upload_gate_evidence_records_github_main_strategy(self):
        upload_gate = ROOT / "docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md"

        self.assertTrue(upload_gate.exists(), f"missing upload gate: {upload_gate}")

        text = upload_gate.read_text(encoding="utf-8")
        required_markers = [
            "IDS-V0_1-BATCH-021-030-UPLOAD-GATE",
            "STAGE-021..STAGE-030",
            "BATCH021_030_REVIEW_GATE.md",
            "BATCH021_030_UPLOAD_LOCK.yaml",
            "GitHub open PR/issue precheck",
            "push_allowed=true",
            "Use PR #272 targeting `main`",
            "No STAGE-031",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "raw database content was not read",
            "app entry reinstall",
            "PR #272",
            "GitHub merge SHA: `88a428c7901226bd44d5e4ff106cd51d74b550fe`",
            "Post-merge open PRs in `LinzeColin/CodexProject`: `0`",
            "Post-merge open issues in `LinzeColin/CodexProject`: `0`",
            "/Users/linzezhang/Downloads/IDS Industrial Data System.command",
            "/Applications/IDS Industrial Data System.command",
            "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS/KM_IDSystem",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_phase_state_allows_batch021_030_upload_gate_pending_github_merge(self):
        module = self._load_module()
        batch_text = """
status: "local_batch_upload_gate_passed_pending_github_merge"
upload_gate:
  push_allowed: true
  review_gate: "BATCH021_030_REVIEW_GATE"
  gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
  gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md"
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-030:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-031"
    current_task_id: "IDS-V0_1-STAGE030-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
current_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
next_gate_id: "IDS-V0_1-BATCH-021-030-GITHUB-MERGE"
        phase_id: "IDS-STAGE030-P4"
          status: "passed_no_github_upload_until_batch_review"
        phase_id: "IDS-V0_1-BATCH-021-030-REVIEW-GATE"
          status: "passed_no_github_upload_until_upload_gate"
        phase_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
          status: "passed_pending_github_merge"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_batch021_030_uploaded_terminal_state(self):
        module = self._load_module()
        batch_text = """
status: "uploaded_to_github_main"
upload_gate:
  push_allowed: true
  review_gate: "BATCH021_030_REVIEW_GATE"
  gate_task_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
  gate_evidence_ref: "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_GATE.md"
  github_pr: "https://github.com/LinzeColin/CodexProject/pull/272"
  merged_sha: "88a428c7901226bd44d5e4ff106cd51d74b550fe"
  post_merge_open_prs: 0
  post_merge_open_issues: 0
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-030:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_stage: "STAGE-031"
    current_task_id: "IDS-V0_1-STAGE030-P4"
    acceptance_status: "local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE030"
current_phase_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"
current_task_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"
next_gate_id: "IDS-STAGE031-P1-GATE"
        phase_id: "IDS-STAGE030-P4"
          status: "passed_no_github_upload_until_batch_review"
        phase_id: "IDS-V0_1-BATCH-021-030-UPLOAD-GATE"
          status: "uploaded_to_github_main"
        phase_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"
          status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage031_phase1_schema_migration_safety_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage031_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    current_task_id: "IDS-V0_1-STAGE031-P1"
    acceptance_id: "ACC-STAGE-031"
    acceptance_status: "phase1_scope_boundary_defined"
    next_gate: "IDS-STAGE031-P2-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE031"
current_phase_id: "IDS-STAGE031-P1"
current_task_id: "IDS-V0_1-STAGE031-P1"
next_gate_id: "IDS-STAGE031-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-V0_1-BATCH-021-030-MAIN-MERGED"
          status: "completed"
        phase_id: "IDS-STAGE031-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage031_phase2_schema_migration_safety_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage031_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    current_task_id: "IDS-V0_1-STAGE031-P2"
    acceptance_id: "ACC-STAGE-031"
    acceptance_status: "phase2_safety_slice_defined"
    next_gate: "IDS-STAGE031-P3-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE031"
current_phase_id: "IDS-STAGE031-P2"
current_task_id: "IDS-V0_1-STAGE031-P2"
next_gate_id: "IDS-STAGE031-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage031_phase3_schema_migration_safety_validation(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage031_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    current_task_id: "IDS-V0_1-STAGE031-P3"
    acceptance_id: "ACC-STAGE-031"
    acceptance_status: "phase3_scenario_validation_defined"
    next_gate: "IDS-STAGE031-P4-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE031"
current_phase_id: "IDS-STAGE031-P3"
current_task_id: "IDS-V0_1-STAGE031-P3"
next_gate_id: "IDS-STAGE031-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage031_phase4_closeout_pending_stage_review(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage031_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_local_pending_review"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "stage_review_gate"
    current_task_id: "IDS-V0_1-STAGE031-P4"
    acceptance_id: "ACC-STAGE-031"
    acceptance_status: "local_passed_pending_stage_review"
    next_gate: "IDS-STAGE031-REVIEW-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE031"
current_phase_id: "IDS-STAGE031-P4"
current_task_id: "IDS-V0_1-STAGE031-P4"
next_gate_id: "IDS-STAGE031-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage031_reviewed_local_before_stage032(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage031_completed_reviewed_local"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-032"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_id: "ACC-STAGE-031"
    acceptance_status: "reviewed_local_passed"
    next_gate: "IDS-STAGE032-P1-GATE"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE031"
current_phase_id: "IDS-STAGE031-REVIEW"
current_task_id: "IDS-V0_1-STAGE031-REVIEW"
next_gate_id: "IDS-STAGE032-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE031-P4"
          status: "passed_with_local_evidence"
      review:
        review_id: "IDS-STAGE031-REVIEW"
        task_id: "IDS-V0_1-STAGE031-REVIEW"
        status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage032_phase1_database_connection_pool_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage032_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-032"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "stage032_phase1_in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE032-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE032-P1"
    acceptance_id: "ACC-STAGE-032"
    acceptance_status: "phase1_scope_boundary_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE032"
current_phase_id: "IDS-STAGE032-P1"
current_task_id: "IDS-V0_1-STAGE032-P1"
next_gate_id: "IDS-STAGE032-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE032-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage033_phase1_database_size_guard_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage033_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-033"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "stage033_phase1_in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE033-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE033-P1"
    acceptance_id: "ACC-STAGE-033"
    acceptance_status: "phase1_scope_boundary_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE033"
current_phase_id: "IDS-STAGE033-P1"
current_task_id: "IDS-V0_1-STAGE033-P1"
next_gate_id: "IDS-STAGE033-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE033-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage033_phase2_database_size_guard_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage033_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-033"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "stage033_phase2_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE033-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE033-P2"
    acceptance_id: "ACC-STAGE-033"
    acceptance_status: "phase2_size_guard_slice_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE033"
current_phase_id: "IDS-STAGE033-P2"
current_task_id: "IDS-V0_1-STAGE033-P2"
next_gate_id: "IDS-STAGE033-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE033-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage033_phase3_database_size_guard_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage033_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-033"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "stage033_phase3_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    next_gate: "IDS-STAGE033-P4-GATE"
    current_task_id: "IDS-V0_1-STAGE033-P3"
    acceptance_id: "ACC-STAGE-033"
    acceptance_status: "phase3_scenario_validation_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE033"
current_phase_id: "IDS-STAGE033-P3"
current_task_id: "IDS-V0_1-STAGE033-P3"
next_gate_id: "IDS-STAGE033-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE033-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage033_phase4_database_size_guard_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage033_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-033"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "stage033_completed_local_pending_review"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_gate: "IDS-STAGE033-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE033-P4"
    acceptance_id: "ACC-STAGE-033"
    acceptance_status: "phase4_closeout_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE033"
current_phase_id: "IDS-STAGE033-P4"
current_task_id: "IDS-V0_1-STAGE033-P4"
next_gate_id: "IDS-STAGE033-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE033-P4"
          status: "passed_no_github_upload_until_stage_review"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage032_phase2_database_connection_pool_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage032_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-032"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "stage032_phase2_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE032-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE032-P2"
    acceptance_id: "ACC-STAGE-032"
    acceptance_status: "phase2_connection_pool_slice_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE032"
current_phase_id: "IDS-STAGE032-P2"
current_task_id: "IDS-V0_1-STAGE032-P2"
next_gate_id: "IDS-STAGE032-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE032-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage032_phase3_database_connection_pool_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage032_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-032"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "stage032_phase3_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    next_gate: "IDS-STAGE032-P4-GATE"
    current_task_id: "IDS-V0_1-STAGE032-P3"
    acceptance_id: "ACC-STAGE-032"
    acceptance_status: "phase3_scenario_validation_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE032"
current_phase_id: "IDS-STAGE032-P3"
current_task_id: "IDS-V0_1-STAGE032-P3"
next_gate_id: "IDS-STAGE032-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE032-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage032_phase4_database_connection_pool_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage032_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-032"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "stage032_completed_local_pending_review"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "stage_review_gate"
    next_gate: "IDS-STAGE032-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE032-P4"
    acceptance_id: "ACC-STAGE-032"
    acceptance_status: "local_passed_pending_stage_review"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE032"
current_phase_id: "IDS-STAGE032-P4"
current_task_id: "IDS-V0_1-STAGE032-P4"
next_gate_id: "IDS-STAGE032-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE032-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P4"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage032_reviewed_local_before_stage033(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage032_completed_reviewed_local"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-033"
    next_gate: "IDS-STAGE033-P1-GATE"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_id: "ACC-STAGE-032"
    acceptance_status: "reviewed_local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE032"
current_phase_id: "IDS-STAGE032-REVIEW"
current_task_id: "IDS-V0_1-STAGE032-REVIEW"
next_gate_id: "IDS-STAGE033-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE032-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE032-P4"
          status: "passed_with_local_evidence"
      review:
        review_id: "IDS-STAGE032-REVIEW"
        task_id: "IDS-V0_1-STAGE032-REVIEW"
        status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage033_reviewed_local_database_size_guard(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage033_completed_reviewed_local"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-034"
    next_gate: "IDS-STAGE034-P1-GATE"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_id: "ACC-STAGE-033"
    acceptance_status: "reviewed_local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE033"
current_phase_id: "IDS-STAGE033-REVIEW"
current_task_id: "IDS-V0_1-STAGE033-REVIEW"
next_gate_id: "IDS-STAGE034-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE033-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE033-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE033-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE033-P4"
          status: "passed_no_github_upload_until_stage_review"
      review:
        review_id: "IDS-STAGE033-REVIEW"
        task_id: "IDS-V0_1-STAGE033-REVIEW"
        status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage034_phase1_data_retention_table_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage034_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "stage034_phase1_in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE034-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE034-P1"
    acceptance_id: "ACC-STAGE-034"
    acceptance_status: "phase1_scope_boundary_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE034"
current_phase_id: "IDS-STAGE034-P1"
current_task_id: "IDS-V0_1-STAGE034-P1"
next_gate_id: "IDS-STAGE034-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE034-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage034_phase2_data_retention_table_slice(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage034_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "stage034_phase2_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE034-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE034-P2"
    acceptance_id: "ACC-STAGE-034"
    acceptance_status: "phase2_retention_table_slice_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE034"
current_phase_id: "IDS-STAGE034-P2"
current_task_id: "IDS-V0_1-STAGE034-P2"
next_gate_id: "IDS-STAGE034-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE034-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage034_phase3_data_retention_table_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage034_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "stage034_phase3_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    next_gate: "IDS-STAGE034-P4-GATE"
    current_task_id: "IDS-V0_1-STAGE034-P3"
    acceptance_id: "ACC-STAGE-034"
    acceptance_status: "phase3_scenario_validation_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE034"
current_phase_id: "IDS-STAGE034-P3"
current_task_id: "IDS-V0_1-STAGE034-P3"
next_gate_id: "IDS-STAGE034-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE034-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage034_phase4_data_retention_table_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage034_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "stage034_completed_local_pending_review"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "stage_review_gate"
    next_gate: "IDS-STAGE034-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE034-P4"
    acceptance_id: "ACC-STAGE-034"
    acceptance_status: "phase4_closeout_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE034"
current_phase_id: "IDS-STAGE034-P4"
current_task_id: "IDS-V0_1-STAGE034-P4"
next_gate_id: "IDS-STAGE034-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE034-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P4"
          status: "passed_no_github_upload_until_stage_review"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage034_reviewed_local_no_upload(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage034_completed_reviewed_local"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-035"
    next_gate: "IDS-STAGE035-P1-GATE"
    current_task_id: "IDS-V0_1-STAGE034-REVIEW"
    acceptance_id: "ACC-STAGE-034"
    acceptance_status: "reviewed_local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE034"
current_phase_id: "IDS-STAGE034-REVIEW"
current_task_id: "IDS-V0_1-STAGE034-REVIEW"
next_gate_id: "IDS-STAGE035-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE034-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE034-P4"
          status: "passed_no_github_upload_until_stage_review"
      review_id: "IDS-STAGE034-REVIEW"
      task_id: "IDS-V0_1-STAGE034-REVIEW"
      status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage035_phase1_database_recovery_smoke_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage035_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE034-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-035:
    status: "stage035_phase1_in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE035-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE035-P1"
    acceptance_id: "ACC-STAGE-035"
    acceptance_status: "phase1_scope_boundary_defined"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE035"
current_phase_id: "IDS-STAGE035-P1"
current_task_id: "IDS-V0_1-STAGE035-P1"
next_gate_id: "IDS-STAGE035-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE035-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage035_phase2_static_recovery_smoke_contract(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage035_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE034-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-035:
    status: "stage035_phase2_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE035-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE035-P2"
    acceptance_id: "ACC-STAGE-035"
    acceptance_status: "phase2_static_recovery_smoke_contract_validated"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE035"
current_phase_id: "IDS-STAGE035-P2"
current_task_id: "IDS-V0_1-STAGE035-P2"
next_gate_id: "IDS-STAGE035-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE035-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage035_phase3_recovery_smoke_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage035_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE034-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-035:
    status: "stage035_phase3_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    next_gate: "IDS-STAGE035-P4-GATE"
    current_task_id: "IDS-V0_1-STAGE035-P3"
    acceptance_id: "ACC-STAGE-035"
    acceptance_status: "phase3_scenario_validation_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE035"
current_phase_id: "IDS-STAGE035-P3"
current_task_id: "IDS-V0_1-STAGE035-P3"
next_gate_id: "IDS-STAGE035-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE035-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage035_phase4_recovery_smoke_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage035_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE034-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-035:
    status: "stage035_completed_local_pending_review"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "stage_review_gate"
    next_gate: "IDS-STAGE035-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE035-P4"
    acceptance_id: "ACC-STAGE-035"
    acceptance_status: "phase4_closeout_complete"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE035"
current_phase_id: "IDS-STAGE035-P4"
current_task_id: "IDS-V0_1-STAGE035-P4"
next_gate_id: "IDS-STAGE035-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE035-P4"
          status: "passed_no_github_upload_until_stage_review"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage035_reviewed_local_no_upload(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage035_completed_reviewed_local"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-031:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE031-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-032:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE032-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-033:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE033-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-034:
    status: "completed_reviewed_local"
    current_task_id: "IDS-V0_1-STAGE034-REVIEW"
    acceptance_status: "reviewed_local_passed"
  STAGE-035:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-036"
    next_gate: "IDS-STAGE036-P1-GATE"
    current_task_id: "IDS-V0_1-STAGE035-REVIEW"
    acceptance_id: "ACC-STAGE-035"
    acceptance_status: "reviewed_local_passed"
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE035"
current_phase_id: "IDS-STAGE035-REVIEW"
current_task_id: "IDS-V0_1-STAGE035-REVIEW"
next_gate_id: "IDS-STAGE036-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE035-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE035-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE035-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE035-P4"
          status: "passed_no_github_upload_until_stage_review"
      review_id: "IDS-STAGE035-REVIEW"
      task_id: "IDS-V0_1-STAGE035-REVIEW"
      status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage036_phase1_database_quality_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage036_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-036:
    status: "stage036_phase1_in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE036-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE036-P1"
    acceptance_id: "ACC-STAGE-036"
    acceptance_status: "phase1_scope_boundary_defined"
decision:
  current_task_id: "IDS-V0_1-STAGE036-P1"
  next_allowed_task_id: "IDS-V0_1-STAGE036-P2"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-P1"
current_task_id: "IDS-V0_1-STAGE036-P1"
next_gate_id: "IDS-STAGE036-P2-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE036-P1"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage036_phase2_static_quality_constraints(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage036_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-036:
    status: "stage036_phase2_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE036-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE036-P2"
    acceptance_id: "ACC-STAGE-036"
    acceptance_status: "phase2_static_quality_constraint_contract_validated"
decision:
  current_task_id: "IDS-V0_1-STAGE036-P2"
  next_allowed_task_id: "IDS-V0_1-STAGE036-P3"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-P2"
current_task_id: "IDS-V0_1-STAGE036-P2"
next_gate_id: "IDS-STAGE036-P3-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE036-P2"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage036_phase3_quality_constraint_scenarios(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage036_phase3_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-036:
    status: "stage036_phase3_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
    next_phase: "Phase 4"
    next_gate: "IDS-STAGE036-P4-GATE"
    current_task_id: "IDS-V0_1-STAGE036-P3"
    acceptance_id: "ACC-STAGE-036"
    acceptance_status: "phase3_scenario_validation_passed"
decision:
  current_task_id: "IDS-V0_1-STAGE036-P3"
  next_allowed_task_id: "IDS-V0_1-STAGE036-P4"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-P3"
current_task_id: "IDS-V0_1-STAGE036-P3"
next_gate_id: "IDS-STAGE036-P4-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE036-P3"
          status: "passed_with_local_evidence"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

    def test_phase_state_allows_stage036_phase4_quality_constraint_closeout(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage036_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-036:
    status: "stage036_completed_local_pending_review"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    next_phase: "stage_review_gate"
    next_gate: "IDS-STAGE036-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE036-P4"
    acceptance_id: "ACC-STAGE-036"
    acceptance_status: "phase4_closeout_complete"
decision:
  current_task_id: "IDS-V0_1-STAGE036-P4"
  next_allowed_task_id: "IDS-V0_1-STAGE036-REVIEW"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-P4"
current_task_id: "IDS-V0_1-STAGE036-P4"
next_gate_id: "IDS-STAGE036-REVIEW-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE036-P4"
          status: "passed_no_github_upload_until_stage_review"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)

        self.assertTrue(all(checks.values()), checks)

        wrong_next = batch_text.replace(
            'next_allowed_task_id: "IDS-V0_1-STAGE036-REVIEW"',
            'next_allowed_task_id: "IDS-V0_1-STAGE037-P1"',
        )
        structured_roadmap = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-P4"
current_task_id: "IDS-V0_1-STAGE036-P4"
next_gate_id: "IDS-STAGE036-REVIEW-GATE"
"""
        wrong_checks = module.evaluate_current_state_consistency(
            wrong_next, structured_roadmap
        )
        self.assertFalse(
            wrong_checks["decision_next_allowed_task_matches_gate"],
            wrong_checks,
        )

        missing_next = batch_text.replace(
            '  next_allowed_task_id: "IDS-V0_1-STAGE036-REVIEW"\n', ""
        )
        missing_checks = module.evaluate_current_state_consistency(
            missing_next, structured_roadmap
        )
        self.assertFalse(
            missing_checks["decision_next_allowed_task_matches_gate"],
            missing_checks,
        )

    def test_phase_state_allows_stage036_reviewed_local_no_upload(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage036_completed_reviewed_local"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-036:
    status: "completed_reviewed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    review_status: "passed"
    next_stage: "STAGE-037"
    next_gate: "IDS-STAGE037-P1-GATE"
    current_task_id: "IDS-V0_1-STAGE036-REVIEW"
    acceptance_id: "ACC-STAGE-036"
    acceptance_status: "reviewed_local_passed"
decision:
  current_task_id: "IDS-V0_1-STAGE036-REVIEW"
  next_allowed_task_id: "IDS-V0_1-STAGE037-P1"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-REVIEW"
current_task_id: "IDS-V0_1-STAGE036-REVIEW"
next_gate_id: "IDS-STAGE037-P1-GATE"
        phase_id: "IDS-STAGE005-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE005-P4"
          status: "passed_no_github_upload_until_batch_complete"
        phase_id: "IDS-STAGE036-P1"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE036-P2"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE036-P3"
          status: "passed_with_local_evidence"
        phase_id: "IDS-STAGE036-P4"
          status: "passed_no_github_upload_until_stage_review"
      review_id: "IDS-STAGE036-REVIEW"
      task_id: "IDS-V0_1-STAGE036-REVIEW"
      status: "completed"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)
        self.assertTrue(all(checks.values()), checks)
        structured_roadmap = """
current_stage_id: "IDS-STAGE036"
current_phase_id: "IDS-STAGE036-REVIEW"
current_task_id: "IDS-V0_1-STAGE036-REVIEW"
next_gate_id: "IDS-STAGE037-P1-GATE"
"""
        structured = module.evaluate_current_state_consistency(
            batch_text, structured_roadmap
        )
        self.assertTrue(all(structured.values()), structured)

    def test_phase_state_allows_stage037_phase1_job_state_boundary(self):
        module = self._load_module()
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage037_phase1_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-005:
    status: "completed_local"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
      - "Phase 3"
      - "Phase 4"
    current_task_id: "IDS-V0_1-STAGE005-P4"
  STAGE-037:
    status: "stage037_phase1_in_progress"
    completed_phases:
      - "Phase 1"
    next_phase: "Phase 2"
    next_gate: "IDS-STAGE037-P2-GATE"
    current_task_id: "IDS-V0_1-STAGE037-P1"
    acceptance_id: "ACC-STAGE-037"
    acceptance_status: "phase1_scope_boundary_defined"
decision:
  current_task_id: "IDS-V0_1-STAGE037-P1"
  next_allowed_task_id: "IDS-V0_1-STAGE037-P2"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE037"
current_phase_id: "IDS-STAGE037-P1"
current_task_id: "IDS-V0_1-STAGE037-P1"
next_gate_id: "IDS-STAGE037-P2-GATE"
stages:
  -
    stage_id: "IDS-STAGE005"
    phases:
      -
        phase_id: "IDS-STAGE005-P2"
        status: "passed_with_local_evidence"
      -
        phase_id: "IDS-STAGE005-P3"
        status: "passed_with_local_evidence"
      -
        phase_id: "IDS-STAGE005-P4"
        status: "passed_no_github_upload_until_batch_complete"
  -
    stage_id: "IDS-STAGE037"
    phases:
      -
        phase_id: "IDS-STAGE037-P1"
        status: "passed_with_local_evidence"
        tasks:
          -
            task_id: "IDS-V0_1-STAGE037-P1"
            status: "completed"
            test_results: "GREEN: Stage037 8 tests OK, Stage005 134 tests OK, Stage031-037 aggregate 138 tests OK, Stage026-030 75 tests OK, full IDS v0.1 discovery 532 tests OK, Stage005 validator valid=true"
            evidence_refs:
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_ENTRY_CONTRACT.md"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
"""

        checks = module.evaluate_phase_state(batch_text, roadmap_text)
        self.assertTrue(all(checks.values()), checks)
        structured = module.evaluate_current_state_consistency(
            batch_text,
            roadmap_text,
        )
        self.assertTrue(all(structured.values()), structured)

        missing_completed_phase = batch_text.replace(
            '  STAGE-037:\n    status: "stage037_phase1_in_progress"\n'
            '    completed_phases:\n      - "Phase 1"\n',
            '  STAGE-037:\n    status: "stage037_phase1_in_progress"\n'
            '    completed_phases:\n      - "Phase 0"\n',
        )
        missing_checks = module.evaluate_current_state_consistency(
            missing_completed_phase,
            roadmap_text,
        )
        self.assertIn("batch_current_phase_completed", missing_checks)
        self.assertFalse(
            missing_checks["batch_current_phase_completed"],
            missing_checks,
        )

        planned_phase = roadmap_text.replace(
            '        phase_id: "IDS-STAGE037-P1"\n'
            '        status: "passed_with_local_evidence"',
            '        phase_id: "IDS-STAGE037-P1"\n'
            '        status: "planned"',
        )
        planned_checks = module.evaluate_current_state_consistency(
            batch_text,
            planned_phase,
        )
        self.assertIn("roadmap_current_phase_passed", planned_checks)
        self.assertFalse(
            planned_checks["roadmap_current_phase_passed"],
            planned_checks,
        )

        planned_task = roadmap_text.replace(
            '            task_id: "IDS-V0_1-STAGE037-P1"\n'
            '            status: "completed"',
            '            task_id: "IDS-V0_1-STAGE037-P1"\n'
            '            status: "planned"',
        )
        planned_task_checks = module.evaluate_current_state_consistency(
            batch_text,
            planned_task,
        )
        self.assertFalse(
            planned_task_checks["roadmap_current_task_completed"],
            planned_task_checks,
        )

        not_run_task = roadmap_text.replace(
            '            test_results: "GREEN: Stage037 8 tests OK, '
            'Stage005 134 tests OK, Stage031-037 aggregate 138 tests OK, '
            'Stage026-030 75 tests OK, full IDS v0.1 discovery 532 tests OK, '
            'Stage005 validator valid=true"',
            '            test_results: "NOT_RUN"',
        )
        not_run_checks = module.evaluate_current_state_consistency(
            batch_text,
            not_run_task,
        )
        self.assertFalse(
            not_run_checks["roadmap_current_task_results_recorded"],
            not_run_checks,
        )

        fabricated_results = roadmap_text.replace(
            '            test_results: "GREEN: Stage037 8 tests OK, '
            'Stage005 134 tests OK, Stage031-037 aggregate 138 tests OK, '
            'Stage026-030 75 tests OK, full IDS v0.1 discovery 532 tests OK, '
            'Stage005 validator valid=true"',
            '            test_results: "GREEN: Stage037 0 tests OK; '
            'fabricated valid=true"',
        )
        fabricated_checks = module.evaluate_current_state_consistency(
            batch_text,
            fabricated_results,
        )
        self.assertFalse(
            fabricated_checks["roadmap_current_task_results_recorded"],
            fabricated_checks,
        )

        polluted_results = roadmap_text.replace(
            '            test_results: "GREEN: Stage037 8 tests OK, ',
            '            test_results: "GREEN: Stage037 0 tests OK; '
            'fabricated=true; Stage037 8 tests OK, ',
        )
        polluted_checks = module.evaluate_current_state_consistency(
            batch_text,
            polluted_results,
        )
        self.assertFalse(
            polluted_checks["roadmap_current_task_results_recorded"],
            polluted_checks,
        )

        token_boundary_mutations = {
            "negative_green_prefix": roadmap_text.replace(
                'test_results: "GREEN:',
                'test_results: "NOTGREEN:',
            ),
            "prefixed_stage_label": roadmap_text.replace(
                "Stage037 8 tests OK",
                "FakeStage037 8 tests OK",
            ),
            "negated_test_result": roadmap_text.replace(
                "Stage037 8 tests OK",
                "Stage037 8 tests OK=false",
            ),
            "negated_validator_result": roadmap_text.replace(
                "Stage005 validator valid=true",
                "Stage005 validator valid=true=false",
            ),
        }
        for mutation_name, mutated_roadmap in token_boundary_mutations.items():
            with self.subTest(mutation_name=mutation_name):
                mutation_checks = module.evaluate_current_state_consistency(
                    batch_text,
                    mutated_roadmap,
                )
                self.assertFalse(
                    mutation_checks["roadmap_current_task_results_recorded"],
                    mutation_checks,
                )

        remainder_mutations = {
            "failed_result": "; Stage037 0 tests FAILED",
            "zero_test_count": "; test_count=0",
            "invalid_validator": "; Stage005 validator invalid=true",
            "negative_green_assignment": "; GREEN=false",
            "empty_audit_remainder": "; ",
        }
        for mutation_name, suffix in remainder_mutations.items():
            with self.subTest(mutation_name=mutation_name):
                mutated_roadmap = roadmap_text.replace(
                    'Stage005 validator valid=true"',
                    f'Stage005 validator valid=true{suffix}"',
                )
                mutation_checks = module.evaluate_current_state_consistency(
                    batch_text,
                    mutated_roadmap,
                )
                self.assertFalse(
                    mutation_checks["roadmap_current_task_results_recorded"],
                    mutation_checks,
                )

        no_evidence_task = roadmap_text.replace(
            '            evidence_refs:\n'
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'STAGE037_ENTRY_CONTRACT.md"\n'
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'STAGE037_PHASE1_SCOPE_BOUNDARY.md"\n'
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'BATCH031_040_UPLOAD_LOCK.yaml"\n'
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'tests/test_stage037_job_state_model.py"\n'
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'IDS_METADATA_RAW_DATA_BOUNDARY.md"',
            '            evidence_refs: []',
        )
        no_evidence_checks = module.evaluate_current_state_consistency(
            batch_text,
            no_evidence_task,
        )
        self.assertFalse(
            no_evidence_checks["roadmap_current_task_evidence_recorded"],
            no_evidence_checks,
        )

        missing_batch_evidence = roadmap_text.replace(
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'BATCH031_040_UPLOAD_LOCK.yaml"\n',
            "",
        )
        missing_batch_checks = module.evaluate_current_state_consistency(
            batch_text,
            missing_batch_evidence,
        )
        self.assertFalse(
            missing_batch_checks["roadmap_current_task_evidence_recorded"],
            missing_batch_checks,
        )

        missing_boundary_evidence = roadmap_text.replace(
            '              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/'
            'IDS_METADATA_RAW_DATA_BOUNDARY.md"\n',
            "",
        )
        missing_boundary_checks = module.evaluate_current_state_consistency(
            batch_text,
            missing_boundary_evidence,
        )
        self.assertFalse(
            missing_boundary_checks["roadmap_current_task_evidence_recorded"],
            missing_boundary_checks,
        )

    def test_phase_state_allows_stage037_phase2_job_state_engine(self):
        module = self._load_module()
        result_block = (
            "GREEN: Stage037 Phase2 8 tests OK, Stage037 aggregate 16 tests OK, "
            "Stage005 135 tests OK, Stage031-037 aggregate 146 tests OK, "
            "Stage026-030 75 tests OK, full IDS v0.1 discovery 541 tests OK, "
            "checker contract_valid=true, Stage005 validator valid=true"
        )
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage037_phase2_in_progress"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-037:
    status: "stage037_phase2_in_progress"
    completed_phases:
      - "Phase 1"
      - "Phase 2"
    next_phase: "Phase 3"
    next_gate: "IDS-STAGE037-P3-GATE"
    current_task_id: "IDS-V0_1-STAGE037-P2"
    acceptance_id: "ACC-STAGE-037"
    acceptance_status: "phase2_deterministic_engine_passed"
decision:
  current_task_id: "IDS-V0_1-STAGE037-P2"
  next_allowed_task_id: "IDS-V0_1-STAGE037-P3"
  github_upload_allowed: false
"""
        roadmap_text = f"""
current_stage_id: "IDS-STAGE037"
current_phase_id: "IDS-STAGE037-P2"
current_task_id: "IDS-V0_1-STAGE037-P2"
next_gate_id: "IDS-STAGE037-P3-GATE"
stages:
  -
    stage_id: "IDS-STAGE037"
    phases:
      -
        phase_id: "IDS-STAGE037-P2"
        status: "passed_with_local_evidence"
        tasks:
          -
            task_id: "IDS-V0_1-STAGE037-P2"
            status: "completed"
            test_results: "{result_block}"
            evidence_refs:
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json"
              - "KM_IDSystem/scripts/check_job_state_model.py"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py"
              - "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md"
"""

        phase_checks = module.evaluate_phase_state(batch_text, roadmap_text)
        self.assertTrue(all(phase_checks.values()), phase_checks)
        structured = module.evaluate_current_state_consistency(
            batch_text, roadmap_text
        )
        self.assertTrue(all(structured.values()), structured)

        missing_phase = batch_text.replace('      - "Phase 2"\n', "")
        missing_phase_checks = module.evaluate_current_state_consistency(
            missing_phase, roadmap_text
        )
        self.assertFalse(
            missing_phase_checks["batch_current_phase_completed"],
            missing_phase_checks,
        )

        not_run = roadmap_text.replace(result_block, "NOT_RUN")
        not_run_checks = module.evaluate_current_state_consistency(
            batch_text, not_run
        )
        self.assertFalse(
            not_run_checks["roadmap_current_task_results_recorded"],
            not_run_checks,
        )

        polluted = roadmap_text.replace(
            result_block,
            result_block + "; fabricated=true",
        )
        polluted_checks = module.evaluate_current_state_consistency(
            batch_text, polluted
        )
        self.assertFalse(
            polluted_checks["roadmap_current_task_results_recorded"],
            polluted_checks,
        )

        missing_checker = roadmap_text.replace(
            '              - "KM_IDSystem/scripts/check_job_state_model.py"\n',
            "",
        )
        missing_checker_checks = module.evaluate_current_state_consistency(
            batch_text, missing_checker
        )
        self.assertFalse(
            missing_checker_checks["roadmap_current_task_evidence_recorded"],
            missing_checker_checks,
        )

    def test_structured_state_rejects_stage035_node_contradictions(self):
        module = self._load_module()
        self.assertTrue(
            hasattr(module, "evaluate_current_state_consistency"),
            "missing structured current-state consistency validator",
        )
        batch_text = """
batch_id: "IDS-V0_1-BATCH-031-040"
status: "stage035_completed_local_pending_review"
upload_gate:
  push_allowed: false
stage_progress:
  STAGE-035:
    status: "stage035_completed_local_pending_review"
    next_phase: "stage_review_gate"
    next_gate: "IDS-STAGE035-REVIEW-GATE"
    current_task_id: "IDS-V0_1-STAGE035-P4"
    acceptance_status: "phase4_closeout_complete"
decision:
  current_task_id: "IDS-V0_1-STAGE035-P4"
  next_allowed_task_id: "IDS-V0_1-STAGE035-REVIEW"
  github_upload_allowed: false
"""
        roadmap_text = """
current_stage_id: "IDS-STAGE035"
current_phase_id: "IDS-STAGE035-P4"
current_task_id: "IDS-V0_1-STAGE035-P4"
next_gate_id: "IDS-STAGE035-REVIEW-GATE"
"""

        valid = module.evaluate_current_state_consistency(batch_text, roadmap_text)
        self.assertTrue(all(valid.values()), valid)

        top_status_tampered = batch_text.replace(
            'status: "stage035_completed_local_pending_review"',
            'status: "stage035_phase3_in_progress"',
            1,
        )
        top_checks = module.evaluate_current_state_consistency(
            top_status_tampered, roadmap_text
        )
        self.assertFalse(top_checks["batch_top_status_matches_stage"])

        stage_task_tampered = batch_text.replace(
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-P3"',
            1,
        )
        stage_checks = module.evaluate_current_state_consistency(
            stage_task_tampered, roadmap_text
        )
        self.assertFalse(stage_checks["batch_stage_task_matches_roadmap"])

        decision_task_tampered = batch_text.replace(
            'decision:\n  current_task_id: "IDS-V0_1-STAGE035-P4"',
            'decision:\n  current_task_id: "IDS-V0_1-STAGE035-P3"',
        )
        decision_checks = module.evaluate_current_state_consistency(
            decision_task_tampered, roadmap_text
        )
        self.assertFalse(decision_checks["decision_task_matches_roadmap"])

        missing_stage_node = batch_text.replace("STAGE-035:", "STAGE-034:", 1)
        missing_stage_checks = module.evaluate_current_state_consistency(
            missing_stage_node, roadmap_text
        )
        self.assertFalse(
            missing_stage_checks["current_stage_node_resolved"],
            missing_stage_checks,
        )
        strict_checks = module.evaluate_phase_state(
            missing_stage_node, roadmap_text, require_structured=True
        )
        self.assertFalse(
            strict_checks["current_state_current_stage_node_resolved"],
            strict_checks,
        )


if __name__ == "__main__":
    unittest.main()
