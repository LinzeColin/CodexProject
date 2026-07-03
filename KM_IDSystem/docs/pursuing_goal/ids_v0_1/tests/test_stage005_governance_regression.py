import importlib.util
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

    def test_app_entry_install_policy_is_app_only_without_command_launchers(self):
        self.assertTrue(APP_ENTRY_INSTALLER.is_file(), f"missing installer: {APP_ENTRY_INSTALLER}")
        self.assertTrue(APP_ENTRY_DIAGNOSTIC.is_file(), f"missing diagnostic: {APP_ENTRY_DIAGNOSTIC}")
        self.assertTrue(APP_BUNDLE_BUILDER.is_file(), f"missing builder: {APP_BUNDLE_BUILDER}")

        scripts = {
            "installer": APP_ENTRY_INSTALLER.read_text(encoding="utf-8"),
            "diagnostic": APP_ENTRY_DIAGNOSTIC.read_text(encoding="utf-8"),
            "builder": APP_BUNDLE_BUILDER.read_text(encoding="utf-8"),
        }

        forbidden_terms = [
            ".command",
            "COMMAND_NAME",
            "COMMAND_PATHS",
            "DOWNLOADS_COMMAND",
            "APPLICATIONS_COMMAND",
            "write_command_launcher",
            "command launcher",
        ]
        for script_name, text in scripts.items():
            for term in forbidden_terms:
                with self.subTest(script=script_name, term=term):
                    self.assertNotIn(term, text)

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


if __name__ == "__main__":
    unittest.main()
