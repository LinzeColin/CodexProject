from __future__ import annotations

import unittest

from KMFA.tools import v015_s07_p2_conflict_classification as kernel


class S07P2ConflictClassificationTests(unittest.TestCase):
    def obs(self, values: tuple[int, ...], *, source: str = "SRC-A") -> list[kernel.ReferenceObservation]:
        return [
            kernel.ReferenceObservation(source, "V1", "amount_cents", f"VIEW-{index}", value)
            for index, value in enumerate(values, start=1)
        ]

    def test_same_source_mismatch_invalidates_all_consumers_and_reruns(self) -> None:
        pending = kernel.classify_same_source_references(self.obs((100, 101)))
        self.assertEqual(pending["status"], "INVALIDATED_RERUN_REQUIRED")
        self.assertEqual(pending["invalidated_consumer_count"], 2)
        self.assertTrue(pending["formal_report_blocked"])

        resolved = kernel.classify_same_source_references(
            self.obs((100, 101)), rerun_observations=self.obs((100, 100)),
        )
        self.assertEqual(resolved["status"], "RESOLVED_BY_RERUN")
        self.assertTrue(resolved["rerun_consistent"])
        self.assertFalse(resolved["formal_report_blocked"])

    def test_persistent_same_source_mismatch_is_system_error_not_user_error(self) -> None:
        result = kernel.classify_same_source_references(
            self.obs((100, 101)), rerun_observations=self.obs((100, 101)),
        )
        self.assertEqual(result["classification"], "SYSTEM_ERROR")
        self.assertEqual(result["status"], "PERSISTENT_MISMATCH_AFTER_RERUN")
        self.assertTrue(result["system_error"])
        self.assertFalse(result["user_responsibility_assigned"])
        self.assertTrue(result["formal_report_blocked"])

    def test_rerun_cannot_change_source_binding_or_consumer_scope(self) -> None:
        with self.assertRaisesRegex(kernel.ConflictClassificationError, "相同来源"):
            kernel.classify_same_source_references(
                self.obs((100, 101)), rerun_observations=self.obs((100, 100), source="SRC-B"),
            )
        with self.assertRaisesRegex(kernel.ConflictClassificationError, "全部原消费位置"):
            kernel.classify_same_source_references(
                self.obs((100, 101)), rerun_observations=self.obs((100, 100, 100)),
            )

    def test_cross_source_difference_queues_without_automatic_winner(self) -> None:
        rows = [
            kernel.ReferenceObservation("SRC-PDF", "V1", "amount_cents", "PDF", 100),
            kernel.ReferenceObservation("SRC-EXCEL", "V1", "amount_cents", "EXCEL", 101),
        ]
        result = kernel.queue_cross_source_conflict(
            case_ref="CASE-1", field_id="amount_cents", observations=rows,
            evidence_refs=("E-PDF", "E-EXCEL"),
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["status"], "PENDING_HUMAN_DECISION")
        self.assertTrue(result["manual_decision_required"])
        self.assertIsNone(result["automatic_winner"])
        self.assertFalse(result["auto_selection_performed"])
        self.assertIsNone(result["resolved_value"])
        self.assertTrue(result["formal_report_blocked"])

    def test_cross_source_equal_values_do_not_create_false_conflict(self) -> None:
        rows = [
            kernel.ReferenceObservation("SRC-PDF", "V1", "amount_cents", "PDF", 100),
            kernel.ReferenceObservation("SRC-EXCEL", "V1", "amount_cents", "EXCEL", 100),
        ]
        self.assertIsNone(kernel.queue_cross_source_conflict(
            case_ref="CASE-2", field_id="amount_cents", observations=rows,
            evidence_refs=("E-PDF", "E-EXCEL"),
        ))

    def test_five_layer_matrix_assigns_system_faults_to_system(self) -> None:
        cases = kernel.synthetic_acceptance_cases()["responsibility_cases"]
        for name in ("mapping", "rule", "calculation", "display"):
            self.assertEqual(cases[name]["classification"], "SYSTEM_ERROR")
            self.assertFalse(cases[name]["system_problem_assigned_to_user"])
            self.assertGreater(cases[name]["evidence_count"], 0)

    def test_source_input_correction_requires_explicit_authorized_evidence(self) -> None:
        without_authorization = kernel.determine_responsibility(kernel._chain(kernel.RAW_VALUE))
        with_authorization = kernel.determine_responsibility(
            kernel._chain(kernel.RAW_VALUE), explicit_authorized_user_entry=True,
        )
        self.assertEqual(without_authorization["classification"], "UNDETERMINED")
        self.assertEqual(with_authorization["classification"], "SOURCE_INPUT_CORRECTION_REQUIRED")
        self.assertFalse(with_authorization["system_problem_assigned_to_user"])

    def test_missing_or_ambiguous_evidence_is_undetermined(self) -> None:
        missing = kernel.determine_responsibility(kernel._chain(kernel.MAPPING, missing_failure_evidence=True))
        self.assertEqual(missing["classification"], "UNDETERMINED")
        multiple = list(kernel._chain(kernel.MAPPING))
        multiple[2] = kernel.LayerEvidence(kernel.RULE, kernel.FAIL, ("E-RULE",))
        self.assertEqual(kernel.determine_responsibility(multiple)["classification"], "UNDETERMINED")

    def test_private_queue_remains_aggregate_unresolved_and_public_safe(self) -> None:
        result = kernel.validate_private_conflict_boundary()
        self.assertEqual(result["private_queue_item_count"], 147)
        self.assertEqual(result["private_open_unconfirmed_item_count"], 128)
        self.assertEqual(result["private_conflict_candidate_count"], 6)
        self.assertEqual(result["private_conflict_auto_selected_count"], 0)
        self.assertFalse(result["private_conflict_candidates_treated_as_resolved"])
        for key in (
            "private_value_count_public", "private_identity_count_public",
            "private_source_locator_count_public", "private_digest_count_public",
        ):
            self.assertEqual(result[key], 0)

    def test_public_projection_satisfies_taskpack_boundaries(self) -> None:
        result = kernel.public_projection()
        self.assertEqual(result["conflict_class_count"], 2)
        self.assertEqual(result["responsibility_layer_count"], 5)
        self.assertEqual(result["same_source_rerun_resolved_count"], 1)
        self.assertEqual(result["same_source_persistent_system_error_count"], 1)
        self.assertEqual(result["cross_source_conflict_count"], 1)
        self.assertFalse(result["automatic_source_selection_allowed"])
        self.assertEqual(result["system_problem_assigned_to_user_count"], 0)
        self.assertEqual(result["stage_execution_percentage"], 67)
        self.assertFalse(result["s07_p3_started"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
