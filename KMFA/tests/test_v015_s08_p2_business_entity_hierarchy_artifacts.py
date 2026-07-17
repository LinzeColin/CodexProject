from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s08_p2_business_entity_hierarchy as builder


class BusinessEntityHierarchyArtifactTests(unittest.TestCase):
    def test_s08_p1_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["phase_id"], "V015_S08_P1_PROJECT_COMPOSITE_IDENTITY")
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 19)
        self.assertTrue(dependency["s08_p2_entry_allowed"])
        self.assertFalse(dependency["s08_p2_started"])

    def test_deterministic_outputs_are_current(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_manifest_covers_three_tasks_and_fail_closed_boundaries(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_id"], "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY")
        self.assertEqual(manifest["roadmap_phase_id"], "S08-P2")
        self.assertEqual(manifest["task_execution_complete_count"], 3)
        self.assertEqual((manifest["company_entity_count"], manifest["company_relationship_count"]), (3, 2))
        self.assertFalse(manifest["unknown_entity_funds_aggregation_allowed"])
        self.assertFalse(manifest["partial_funds_aggregation_performed"])
        self.assertEqual((manifest["bank_count"], manifest["account_count"]), (2, 3))
        self.assertEqual(manifest["masked_account_count"], 3)
        self.assertEqual(manifest["public_full_account_value_count"], 0)
        self.assertEqual(manifest["cross_entity_account_resolution_status"], "HIGH_RISK_CROSS_ENTITY_MISMATCH")
        self.assertFalse(manifest["cross_entity_funds_aggregation_allowed"])
        self.assertEqual(manifest["multi_role_counterparty_count"], 2)
        self.assertEqual(manifest["forced_counterparty_merge_count"], 0)
        self.assertEqual(manifest["raw_root_access_count"], 0)
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_uses_exact_taskpack_ids(self) -> None:
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S08P2T01", "S08P2T02", "S08P2T03"])

    def test_public_account_artifact_contains_only_masked_display_values(self) -> None:
        artifact = json.loads(builder.ACCOUNT_DIRECTORY_PATH.read_text(encoding="utf-8"))
        directory = artifact["directory"]
        self.assertTrue(all(row["masked_account"].startswith("****") for row in directory["accounts"]))
        self.assertEqual(directory["public_full_account_value_count"], 0)
        text = json.dumps(artifact, ensure_ascii=False)
        self.assertNotIn("full_account_number", text)
        self.assertNotIn("99999999", text)

    def test_public_evidence_stays_synthetic_and_local_path_free(self) -> None:
        paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
        paths.append(builder.CONTRACT_PATH)
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for token in ("/Users/", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".pdf"):
            self.assertNotIn(token, text)
        self.assertIn("PUBLIC_SAFE_SYNTHETIC", text)


if __name__ == "__main__":
    unittest.main()
