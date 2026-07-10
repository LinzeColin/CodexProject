from __future__ import annotations

import unittest

from KMFA.tools import (
    v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance as phase,
)


class RemainingElevenResidualDifferenceTest(unittest.TestCase):
    def test_pdf_amount_normalization_and_disposition_policy(self) -> None:
        self.assertEqual(phase.parse_pdf_amount_to_cents("1,234.56"), 123456)
        self.assertEqual(phase.parse_pdf_amount_to_cents("1，234"), 123400)
        self.assertEqual(phase.parse_pdf_amount_to_cents("0.01"), 1)
        for invalid in (None, "", "-", "12.345", "10%"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    phase.parse_pdf_amount_to_cents(invalid)

        resolved = phase.disposition_policy("unique_authority_cost_component")
        self.assertTrue(resolved["queue_closed"])
        accepted = phase.disposition_policy("final_cash_difference_acceptance")
        self.assertFalse(accepted["queue_closed"])

    def test_unique_travel_row_requires_exact_child_sum(self) -> None:
        table = [
            ["字段", "金额（元）", "备注"],
            ["2.差旅费", "30.00", ""],
            ["车票", "10.00", ""],
            ["住宿", "20.00", ""],
            ["占用的资金利息", "5.00", ""],
        ]
        evidence = phase.extract_component_from_table(table, component="travel")
        self.assertEqual(evidence["value_cents"], 3000)
        self.assertTrue(evidence["child_sum_exact"])

        duplicate = table + [["差旅费补录", "1.00", ""]]
        with self.assertRaises(ValueError):
            phase.extract_component_from_table(duplicate, component="travel")

        mismatch = [row[:] for row in table]
        mismatch[3][1] = "19.99"
        with self.assertRaises(ValueError):
            phase.extract_component_from_table(mismatch, component="travel")


if __name__ == "__main__":
    unittest.main()
