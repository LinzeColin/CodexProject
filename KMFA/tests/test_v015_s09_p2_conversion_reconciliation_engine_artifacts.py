from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s09_p2_conversion_reconciliation_engine as builder


class ConversionReconciliationArtifactTests(unittest.TestCase):
    def test_dependency_is_receipt_bound_s09_p1(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["phase_acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 20)
        self.assertTrue(dependency["s09_p2_entry_allowed"])
        self.assertFalse(dependency["s09_p2_started"])

    def test_expected_outputs_are_public_safe_and_complete(self) -> None:
        outputs = builder.expected_outputs()
        self.assertEqual(len(outputs), 14)
        paths = {str(path.relative_to(builder.REPO_ROOT)) for path in outputs}
        for expected in (
            "KMFA/metadata/quality/v015_s09_p2_conversion_policy_public_safe.json",
            "KMFA/metadata/quality/v015_s09_p2_project_financial_reconciliation_public_safe.json",
            "KMFA/metadata/protocol/v015_s09_p2_rerun_confirmation_protocol_public_safe.json",
            "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/s09_p2_conversion_reconciliation_manifest.json",
        ):
            self.assertIn(expected, paths)
        text = "\n".join(outputs.values())
        for forbidden in ("/Users/", "KMFA_MetaData", "private://", ".xlsx", ".xls", ".pdf"):
            self.assertNotIn(forbidden, text)

    def test_machine_outputs_parse_and_encode_acceptance(self) -> None:
        outputs = builder.expected_outputs()
        manifest = json.loads(outputs[builder.MANIFEST_PATH])
        conversion = json.loads(outputs[builder.CONVERSION_CASES_PATH])
        reconciliation = json.loads(outputs[builder.RECONCILIATION_CASES_PATH])
        rerun = json.loads(outputs[builder.RERUN_CASES_PATH])
        self.assertTrue(manifest["conservation_passed"])
        self.assertEqual(manifest["conservation_residual_cents"], 0)
        self.assertTrue(manifest["imbalance_blocked"])
        self.assertEqual(conversion["unapproved_effective_count"], 0)
        self.assertTrue(reconciliation["every_difference_has_source_and_impact"])
        self.assertEqual(reconciliation["opposite_delta_values"], [-1000, 1000])
        self.assertEqual(reconciliation["silent_offset_count"], 0)
        self.assertTrue(rerun["resolved_chain_state_consistent"])
        self.assertTrue(rerun["persistent_chain_state_consistent"])
        self.assertIsNone(rerun["cross_source_automatic_winner"])
        self.assertTrue(rerun["source_snapshot_unchanged"])

    def test_task_matrix_has_exact_three_taskpack_tasks(self) -> None:
        tasks = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual(tasks["task_count"], 3)
        self.assertEqual(
            [row["task_id"] for row in tasks["tasks"]],
            ["S09P2T01", "S09P2T02", "S09P2T03"],
        )
        for row in tasks["tasks"]:
            self.assertEqual(len(row["evidence_refs"]), 2)

    def test_metadata_protocols_fail_closed(self) -> None:
        outputs = builder.expected_outputs()
        policy = json.loads(outputs[builder.CONVERSION_POLICY_PATH])
        reconciliation = json.loads(outputs[builder.RECONCILIATION_POLICY_PATH])
        rerun = json.loads(outputs[builder.RERUN_PROTOCOL_PATH])
        self.assertTrue(policy["input_output_conservation_required"])
        self.assertTrue(policy["imbalance_blocks_processing"])
        self.assertFalse(policy["source_mutation_allowed"])
        self.assertFalse(reconciliation["opposite_difference_netting_allowed"])
        self.assertTrue(reconciliation["missing_source_requires_confirmation"])
        self.assertFalse(rerun["automatic_cross_source_winner_allowed"])
        self.assertFalse(rerun["raw_source_mutation_allowed"])
        self.assertFalse(rerun["old_derived_version_overwrite_allowed"])


if __name__ == "__main__":
    unittest.main()
