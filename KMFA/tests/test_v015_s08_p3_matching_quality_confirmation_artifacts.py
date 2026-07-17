from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s08_p3_matching_quality_confirmation as builder


class MatchingQualityConfirmationArtifactTests(unittest.TestCase):
    def test_s08_p2_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["phase_id"], "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY")
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 19)
        self.assertTrue(dependency["s08_p3_entry_allowed"])
        self.assertFalse(dependency["s08_p3_started"])

    def test_deterministic_outputs_are_current(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_manifest_covers_all_three_taskpack_tasks(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_id"], "V015_S08_P3_MATCHING_QUALITY_CONFIRMATION")
        self.assertEqual(manifest["roadmap_phase_id"], "S08-P3")
        self.assertEqual(manifest["task_execution_complete_count"], 3)
        self.assertEqual(manifest["match_state_count"], 3)
        self.assertEqual((manifest["auto_match_min_bps"], manifest["candidate_review_min_bps"]), (8500, 7000))
        self.assertTrue(manifest["thresholds_externalized"])
        self.assertTrue(manifest["threshold_change_requires_regression"])
        self.assertEqual(manifest["policy_regression_case_count"], 5)
        self.assertEqual(manifest["policy_regression_fail_count"], 0)
        self.assertEqual(manifest["confirmation_card_count"], 2)
        self.assertEqual(manifest["confirmation_technical_term_occurrence_count"], 0)
        self.assertEqual(manifest["control_event_count"], 4)
        self.assertEqual((manifest["reversal_event_count"], manifest["rollback_event_count"]), (1, 1))
        self.assertEqual(manifest["recalculation_receipt_count"], 4)
        self.assertTrue(manifest["direct_fact_mutation_rejected"])
        self.assertTrue(manifest["source_snapshot_unchanged"])
        self.assertTrue(manifest["fact_snapshot_unchanged"])
        self.assertEqual(manifest["raw_root_access_count"], 0)
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_uses_exact_taskpack_ids(self) -> None:
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            [row["task_id"] for row in matrix["tasks"]],
            ["S08P3T01", "S08P3T02", "S08P3T03"],
        )

    def test_confirmation_artifact_is_plain_language_and_side_by_side(self) -> None:
        artifact = json.loads(builder.CONFIRMATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(artifact["acceptance"]["confirmation_card_count"], 2)
        self.assertEqual(artifact["acceptance"]["side_by_side_column_count_per_card"], 2)
        self.assertEqual(artifact["acceptance"]["required_explanation_section_count"], 4)
        self.assertEqual(artifact["acceptance"]["technical_term_occurrence_count"], 0)
        text = json.dumps(artifact["confirmation_cards"], ensure_ascii=False).lower()
        for term in ("hash", "sha-", "digest", "payload", "record_ref", "基点"):
            self.assertNotIn(term, text)
        self.assertIn("相同点", text)
        self.assertIn("冲突点", text)
        self.assertIn("可能影响", text)

    def test_decision_and_recalculation_artifacts_are_one_to_one(self) -> None:
        events = json.loads(builder.EVENT_LEDGER_PATH.read_text(encoding="utf-8"))
        recalculation = json.loads(builder.RECALCULATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(events["acceptance"]["control_event_count"], 4)
        self.assertEqual(events["acceptance"]["append_only_event_count"], 4)
        self.assertTrue(events["acceptance"]["persistence_roundtrip_exact"])
        self.assertTrue(events["acceptance"]["direct_fact_mutation_rejected"])
        self.assertEqual(recalculation["acceptance"]["recalculation_receipt_count"], 4)
        self.assertEqual(recalculation["acceptance"]["recalculation_pass_count"], 4)
        self.assertEqual(recalculation["acceptance"]["raw_source_mutation_count"], 0)
        self.assertEqual(recalculation["acceptance"]["fact_table_mutation_count"], 0)
        self.assertEqual(
            [row["event_ref"] for row in events["events"]],
            [row["trigger_event_ref"] for row in recalculation["recalculation_receipts"]],
        )

    def test_public_evidence_stays_synthetic_and_local_path_free(self) -> None:
        paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
        paths.append(builder.CONTRACT_PATH)
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for token in ("/Users/", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".pdf"):
            self.assertNotIn(token, text)
        self.assertIn("PUBLIC_SAFE_SYNTHETIC", text)


if __name__ == "__main__":
    unittest.main()
