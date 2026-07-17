from __future__ import annotations

import unittest

from KMFA.tools import v015_s07_p1_zero_delta_validator as kernel


class S07P1ZeroDeltaValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.specs = (
            kernel.FieldSpec("amount_cents", kernel.INTEGER_CENTS, "AUTH"),
            kernel.FieldSpec("label", kernel.EXACT_TEXT, "AUTH"),
            kernel.FieldSpec("status", kernel.ENUM, "AUTH", allowed_values=("OPEN", "CLOSED")),
            kernel.FieldSpec("business_date", kernel.ISO_DATE, "AUTH"),
            kernel.FieldSpec("unit", kernel.UNIT, "AUTH", allowed_values=("CNY_CENT", "DAY")),
        )
        self.values = {
            "amount_cents": 101,
            "label": "严格文本",
            "status": "OPEN",
            "business_date": "2026-07-15",
            "unit": "CNY_CENT",
        }

    def test_five_registered_types_compare_exactly(self) -> None:
        result = kernel.compare_fields(self.values, dict(self.values), self.specs, record_ref="R-001")
        self.assertTrue(result["zero_difference"])
        self.assertEqual(result["comparison_count"], 5)
        self.assertEqual(result["passed_count"], 5)
        self.assertEqual(result["differences"], [])

    def test_any_one_cent_difference_fails_with_actionable_record(self) -> None:
        actual = dict(self.values)
        actual["amount_cents"] = 100
        result = kernel.compare_fields(self.values, actual, self.specs, record_ref="R-002")
        self.assertFalse(result["zero_difference"])
        self.assertEqual(result["money_tolerance_cents"], 0)
        self.assertEqual(result["minimum_fail_difference_cents"], 1)
        difference = result["differences"][0]
        self.assertEqual(difference["difference_value"], -1)
        for field in kernel.DIFFERENCE_FIELDS:
            self.assertIn(field, difference)
        self.assertTrue(difference["blocking"])

    def test_text_enum_date_and_unit_differences_are_not_normalized_away(self) -> None:
        actual = dict(self.values)
        actual.update({
            "label": "严格文本 ",
            "status": "CLOSED",
            "business_date": "2026-07-16",
            "unit": "DAY",
        })
        result = kernel.compare_fields(self.values, actual, self.specs, record_ref="R-003")
        self.assertEqual(result["failed_count"], 4)
        self.assertEqual(
            {row["field_id"] for row in result["differences"]},
            {"label", "status", "business_date", "unit"},
        )

    def test_float_money_and_noncanonical_date_fail_closed(self) -> None:
        bad_money = dict(self.values)
        bad_money["amount_cents"] = 1.01
        with self.assertRaisesRegex(kernel.ZeroDeltaError, "整数分"):
            kernel.compare_fields(self.values, bad_money, self.specs, record_ref="R-004")
        bad_date = dict(self.values)
        bad_date["business_date"] = "2026-7-15"
        with self.assertRaisesRegex(kernel.ZeroDeltaError, "YYYY-MM-DD"):
            kernel.compare_fields(self.values, bad_date, self.specs, record_ref="R-005")

    def test_reconciliation_proves_all_layers_and_records_zero_differences(self) -> None:
        result = kernel.reconcile_project({
            "project_ref": "SYN-001",
            "details": [
                {"detail_ref": "D1", "category_key": "A", "amount_cents": 4000},
                {"detail_ref": "D2", "category_key": "A", "amount_cents": 1000},
                {"detail_ref": "D3", "category_key": "B", "amount_cents": 2500},
            ],
            "category_totals": [
                {"category_key": "A", "amount_cents": 5000},
                {"category_key": "B", "amount_cents": 2500},
            ],
            "project_totals": {
                "revenue_cents": 10000,
                "total_cost_cents": 7500,
                "gross_profit_cents": 2500,
                "gross_margin_basis_points": 2500,
            },
        })
        self.assertTrue(result["zero_difference"])
        self.assertEqual(result["formula_check_count"], 5)
        self.assertEqual(result["formula_pass_count"], 5)
        self.assertTrue(result["every_formula_has_evidence"])
        self.assertTrue(all(row["difference_recorded"] for row in result["checks"]))

    def test_unexplained_reconciliation_difference_blocks_and_points_to_fix(self) -> None:
        result = kernel.reconcile_project({
            "project_ref": "SYN-002",
            "details": [{"detail_ref": "D1", "category_key": "A", "amount_cents": 4999}],
            "category_totals": [{"category_key": "A", "amount_cents": 5000}],
            "project_totals": {
                "revenue_cents": 10000,
                "total_cost_cents": 5000,
                "gross_profit_cents": 5000,
                "gross_margin_basis_points": 5000,
            },
        })
        self.assertFalse(result["zero_difference"])
        self.assertEqual(result["blocking_unexplained_difference_count"], 1)
        difference = result["differences"][0]
        self.assertEqual(difference["difference_value"], -1)
        self.assertIn("明细", difference["recommended_action"])

    def test_margin_uses_registered_half_up_basis_point_rule(self) -> None:
        self.assertEqual(kernel.gross_margin_basis_points(1, 6), 1667)
        self.assertEqual(kernel.gross_margin_basis_points(-1, 6), -1667)
        with self.assertRaisesRegex(kernel.ZeroDeltaError, "没有定义"):
            kernel.gross_margin_basis_points(1, 0)

    def test_private_golden_recomputation_is_zero_delta_but_keeps_open_boundary(self) -> None:
        result = kernel.validate_private_golden_scope()
        self.assertEqual(result["private_project_count"], 8)
        self.assertEqual(result["private_accepted_field_count"], 92)
        self.assertEqual(result["private_formula_fail_count"], 0)
        self.assertTrue(result["private_zero_difference"])
        self.assertEqual(result["open_unconfirmed_item_count"], 128)
        self.assertFalse(result["open_items_may_be_treated_as_resolved"])
        self.assertFalse(result["tax_normalization_allowed"])
        self.assertFalse(result["cross_period_generalization_allowed"])

    def test_public_projection_is_aggregate_and_satisfies_taskpack_acceptance(self) -> None:
        result = kernel.public_projection()
        self.assertEqual(result["field_type_count"], 5)
        self.assertEqual(result["money_tolerance_cents"], 0)
        self.assertTrue(result["one_cent_difference_detected"])
        self.assertTrue(result["private_zero_difference"])
        self.assertEqual(result["blocking_unexplained_difference_count"], 0)
        self.assertEqual(result["difference_report_complete_count"], result["synthetic_difference_report_count"])
        self.assertEqual(result["private_project_identity_count_public"], 0)
        self.assertEqual(result["private_money_value_count_public"], 0)
        self.assertFalse(result["s07_p2_started"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
