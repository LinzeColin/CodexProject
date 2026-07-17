from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s11_p2_check_board_data_model as builder
from KMFA.tools import check_v015_s11_p2_check_board_data_model as checker
from KMFA.tools import v015_s11_p2_check_board_data_model as kernel


class CheckBoardDataModelGovernanceTests(unittest.TestCase):
    def test_manifest_governance_is_current_and_later_work_is_closed(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        checker._check_manifest(pre_final=not accepted)
        self.assertEqual(manifest["run_phase_id"], kernel.RUN_PHASE_ID)
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertEqual(manifest["s11_p1_acceptance_status"], "PASSED")
        self.assertTrue(manifest["s11_p2_started"])
        self.assertEqual(manifest["s11_p3_entry_allowed"], accepted)
        self.assertFalse(manifest["s11_p3_started"])
        self.assertFalse(manifest["s11_stage_review_entry_allowed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_governance_mirrors_and_registries_are_complete(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        checker._check_governance(pre_final=manifest["phase_acceptance_status"] != "PASSED")

    def test_scope_dependency_taskpack_and_public_boundary(self) -> None:
        checker._check_scope()
        checker._check_dependency()
        checker._check_taskpack_source()
        checker._check_public_boundary()

    def test_backend_fact_and_release_boundaries_are_explicit(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertTrue(manifest["backend_fact_only"])
        self.assertFalse(manifest["frontend_status_mutation_allowed"])
        self.assertEqual(manifest["flat_leaf_at_root_count"], 0)
        self.assertEqual(manifest["raw_root_access_count"], 0)
        self.assertFalse(manifest["raw_business_content_read"])
        self.assertEqual(manifest["live_source_read_count"], 0)
        self.assertFalse(manifest["formal_report_generated"])
        self.assertFalse(manifest["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
