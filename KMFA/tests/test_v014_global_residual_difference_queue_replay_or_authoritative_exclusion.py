from __future__ import annotations

import unittest

from KMFA.tools import (
    v014_global_residual_difference_queue_replay_or_authoritative_exclusion as phase,
)


class GlobalResidualDifferenceQueueReplayTest(unittest.TestCase):
    def test_classification_policy_keeps_unproven_values_open(self) -> None:
        cases = [
            ("materialized_target", True, "replayed_private_integer_value"),
            ("integer_metric", True, "replayed_private_integer_formula"),
            ("non_numeric", True, "owner_authorized_non_numeric_exclusion"),
            ("ambiguous_source", False, "open_missing_unique_authoritative_source"),
            ("accepted_cash_difference", False, "open_final_difference_accepted"),
        ]

        for evidence_kind, expected_closed, expected_status in cases:
            with self.subTest(evidence_kind=evidence_kind):
                decision = phase.classification_policy(
                    evidence_kind=evidence_kind,
                    owner_authorized_exclusion=True,
                )
                self.assertEqual(decision["queue_closed"], expected_closed)
                self.assertEqual(decision["replay_status"], expected_status)

    def test_integer_fingerprint_and_nonzero_difference_guard(self) -> None:
        fingerprint = phase.canonical_value_fingerprint("cents", 12345)
        self.assertEqual(len(fingerprint), 64)
        with self.assertRaises(TypeError):
            phase.canonical_value_fingerprint("cents", 123.45)  # type: ignore[arg-type]

        comparisons = [
            {"comparison_status": "comparison_complete_nonzero_delta", "delta": 9},
            {"comparison_status": "comparison_complete_zero_delta", "delta": 0},
            {
                "comparison_status": "comparison_incomplete_cash_source_disambiguation_required",
                "delta": None,
            },
        ]
        phase.validate_nonzero_difference_guard(comparisons, required_nonzero_count=1)
        with self.assertRaises(ValueError):
            phase.validate_nonzero_difference_guard(
                [{"comparison_status": "comparison_complete_nonzero_delta", "delta": 0}],
                required_nonzero_count=1,
            )


if __name__ == "__main__":
    unittest.main()
