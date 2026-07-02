import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "validate_stage005_governance_regression.py"


class Stage005GovernanceRegressionTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(VALIDATOR.exists(), f"missing validator: {VALIDATOR}")
        spec = importlib.util.spec_from_file_location("stage005_validator", VALIDATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

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

    def test_changed_path_policy_allows_stage011_phase2_files(self):
        module = self._load_module()
        allowed_paths = [
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE2_SAFE_MODE_BASELINE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE011_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py",
            "KM_IDSystem/scripts/check_safe_mode_baseline.py",
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
