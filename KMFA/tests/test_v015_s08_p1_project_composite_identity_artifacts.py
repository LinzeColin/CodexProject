from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s08_p1_project_composite_identity as builder


class ProjectCompositeIdentityArtifactTests(unittest.TestCase):
    def test_s07_review_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["phase_id"], "V015_S07_STAGE_REVIEW")
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["stage_acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 22)
        self.assertTrue(dependency["s08_p1_entry_allowed"])
        self.assertFalse(dependency["s08_p1_started"])

    def test_deterministic_outputs_are_current(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_manifest_covers_all_three_tasks_and_boundaries(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_id"], "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY")
        self.assertEqual(manifest["roadmap_phase_id"], "S08-P1")
        self.assertEqual(manifest["task_execution_complete_count"], 3)
        self.assertEqual(manifest["component_count"], 8)
        self.assertEqual(manifest["configured_weight_total_bps"], 10000)
        self.assertEqual(manifest["missing_contract_renormalized_similarity_bps"], 10000)
        self.assertTrue(manifest["missing_contract_auto_merge_allowed"])
        self.assertFalse(manifest["low_coverage_auto_merge_allowed"])
        self.assertTrue(manifest["amount_evidence_auxiliary_only"])
        self.assertFalse(manifest["amount_alone_decided_match"])
        self.assertFalse(manifest["hard_conflict_auto_merge_allowed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)
        self.assertFalse(manifest["source_mutation_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_has_exact_taskpack_task_ids(self) -> None:
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S08P1T01", "S08P1T02", "S08P1T03"])
        self.assertEqual(matrix["task_execution_complete_count"], 3)

    def test_public_evidence_contains_only_synthetic_name_values(self) -> None:
        paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
        paths.append(builder.CONTRACT_PATH)
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for token in ("/Users/", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".pdf"):
            self.assertNotIn(token, text)
        names = json.loads(builder.NAME_FIXTURES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(names["fixture_scope"], "PUBLIC_SAFE_SYNTHETIC")
        self.assertFalse(names["private_business_values_published"])


if __name__ == "__main__":
    unittest.main()
