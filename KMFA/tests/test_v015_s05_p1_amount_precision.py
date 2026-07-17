from __future__ import annotations

import json
import unittest
from decimal import Decimal

from KMFA.tools.v015_s05_p1_amount_precision import (
    COUNT_DIMENSION,
    MONEY_DIMENSION,
    QUANTITY_DIMENSION,
    AmountPrecisionError,
    Money,
    PreciseMoneyCalculation,
    convert_unit,
    difference_cents,
    divide_money,
    multiply_money,
    public_contract_summary,
    resolve_unit,
)


class V015S05P1AmountPrecisionTests(unittest.TestCase):
    def test_exact_money_supports_cent_delta_large_and_negative_values(self) -> None:
        left = Money.from_value("9999999999999999.99", unit="yuan")
        right = Money.from_value("9999999999999999.98", unit="yuan")
        self.assertEqual(difference_cents(left, right), 1)
        self.assertEqual(Money.from_value("-123456.78", unit="yuan").cents, -12345678)
        self.assertEqual(Money.from_value(1, unit="fen").cents, 1)
        self.assertEqual(Money.from_value("0.000001", unit="wan_yuan").cents, 1)

    def test_float_is_rejected_across_money_calculation_and_conversion(self) -> None:
        for call in (
            lambda: Money.from_value(1.25, unit="yuan"),
            lambda: multiply_money(Money(100), 1.25),
            lambda: divide_money(Money(100), 2.0),
            lambda: convert_unit(1.25, from_unit="yuan", to_unit="fen"),
        ):
            with self.subTest(call=call):
                with self.assertRaisesRegex(AmountPrecisionError, "float"):
                    call()

    def test_public_serialization_contains_integer_cents_only(self) -> None:
        payload = Money.from_value("1234.56", unit="yuan").to_public_dict()
        self.assertEqual(payload, {"amount_cents": 123456, "currency": "CNY"})
        encoded = json.dumps(payload, sort_keys=True)
        self.assertNotIn("1234.56", encoded)
        self.assertIsInstance(payload["amount_cents"], int)

    def test_intermediate_calculation_never_rounds_implicitly(self) -> None:
        result = multiply_money(Money(1), Decimal("0.5"))
        self.assertIsInstance(result, PreciseMoneyCalculation)
        self.assertEqual(result.exact_cents, Decimal("0.5"))
        self.assertFalse(isinstance(result, Money))
        with self.assertRaises(AmountPrecisionError):
            Money.from_value("0.005", unit="yuan")
        with self.assertRaisesRegex(AmountPrecisionError, "must be Decimal"):
            PreciseMoneyCalculation(0.5, "MULTIPLY")  # type: ignore[arg-type]
        with self.assertRaisesRegex(AmountPrecisionError, "finite"):
            PreciseMoneyCalculation(Decimal("NaN"), "MULTIPLY")
        with self.assertRaisesRegex(AmountPrecisionError, "not registered"):
            PreciseMoneyCalculation(Decimal("1"), "UNREGISTERED")

    def test_tax_half_up_is_explicit_and_symmetric_for_negative_ties(self) -> None:
        positive = Money.from_value(
            "0.005", unit="yuan",
            rounding_rule_id="TAX_HALF_UP_CENT", rounding_point="TAX_FINALIZATION",
        )
        negative = Money.from_value(
            "-0.005", unit="yuan",
            rounding_rule_id="TAX_HALF_UP_CENT", rounding_point="TAX_FINALIZATION",
        )
        self.assertEqual((positive.cents, negative.cents), (1, -1))

    def test_report_half_even_rounds_only_at_registered_yuan_point(self) -> None:
        self.assertEqual(
            Money.from_value(
                "2.50", unit="yuan",
                rounding_rule_id="REPORT_HALF_EVEN_YUAN", rounding_point="REPORT_PRESENTATION",
            ).cents,
            200,
        )
        self.assertEqual(
            Money.from_value(
                "3.50", unit="yuan",
                rounding_rule_id="REPORT_HALF_EVEN_YUAN", rounding_point="REPORT_PRESENTATION",
            ).cents,
            400,
        )
        with self.assertRaisesRegex(AmountPrecisionError, "registered only"):
            Money.from_value(
                "2.50", unit="yuan",
                rounding_rule_id="REPORT_HALF_EVEN_YUAN", rounding_point="SOURCE_INGEST",
            )

    def test_unknown_rounding_rule_routes_to_manual_confirmation(self) -> None:
        with self.assertRaises(AmountPrecisionError) as context:
            Money.from_value(
                "0.005", unit="yuan",
                rounding_rule_id="UNKNOWN", rounding_point="SOURCE_INGEST",
            )
        self.assertEqual(context.exception.code, "ROUNDING_RULE_UNKNOWN")
        self.assertEqual(context.exception.action, "MANUAL_CONFIRMATION")

    def test_exact_source_rule_rejects_fractional_cent(self) -> None:
        with self.assertRaisesRegex(AmountPrecisionError, "not exact"):
            Money.from_value(
                "0.005", unit="yuan",
                rounding_rule_id="SOURCE_EXACT_CENT", rounding_point="SOURCE_INGEST",
            )

    def test_registered_money_units_convert_exactly(self) -> None:
        self.assertEqual(convert_unit("1", from_unit="yuan", to_unit="fen", expected_dimension=MONEY_DIMENSION), Decimal("1E+2"))
        self.assertEqual(convert_unit("1.25", from_unit="万元", to_unit="元", expected_dimension=MONEY_DIMENSION), Decimal("12500.00"))
        self.assertEqual(Money.from_value("1.25", unit="万元").cents, 1250000)

    def test_quantity_units_are_explicit_and_dimension_safe(self) -> None:
        self.assertEqual(convert_unit("1.25", from_unit="吨", to_unit="kg", expected_dimension=QUANTITY_DIMENSION), Decimal("1250.00"))
        self.assertEqual(convert_unit(3, from_unit="件", to_unit="count", expected_dimension=COUNT_DIMENSION), Decimal(3))
        with self.assertRaisesRegex(AmountPrecisionError, "cross-dimension"):
            convert_unit(1, from_unit="kg", to_unit="yuan")

    def test_missing_or_unknown_unit_never_guesses(self) -> None:
        for unit in (None, "", "mystery"):
            with self.subTest(unit=unit):
                with self.assertRaises(AmountPrecisionError) as context:
                    Money.from_value("1", unit=unit)
                self.assertEqual(context.exception.action, "MANUAL_CONFIRMATION")

    def test_non_finite_boolean_and_divide_by_zero_fail_closed(self) -> None:
        for value in (Decimal("NaN"), Decimal("Infinity"), True):
            with self.subTest(value=value):
                with self.assertRaises(AmountPrecisionError):
                    Money.from_value(value, unit="yuan")  # type: ignore[arg-type]
        with self.assertRaisesRegex(AmountPrecisionError, "zero"):
            divide_money(Money(1), 0)

    def test_arithmetic_preserves_integer_cents(self) -> None:
        self.assertEqual((Money(100) + Money(-1)).cents, 99)
        self.assertEqual((Money(100) - Money(101)).cents, -1)
        self.assertEqual(
            divide_money(Money(100), 3).finalize(
                rounding_rule_id="ALLOCATION_HALF_UP_CENT",
                rounding_point="ALLOCATION_FINALIZATION",
            ).cents,
            33,
        )

    def test_public_contract_is_truthful_and_raw_free(self) -> None:
        summary = public_contract_summary()
        self.assertEqual(summary["canonical_storage"], "SIGNED_INTEGER_CENTS")
        self.assertFalse(summary["float_money_allowed"])
        self.assertFalse(summary["implicit_intermediate_rounding_allowed"])
        self.assertTrue(summary["explicit_unit_required"])
        self.assertEqual(summary["rounding_rule_count"], 4)
        self.assertEqual(summary["raw_root_access_count"], 0)

    def test_unit_aliases_resolve_to_canonical_definitions(self) -> None:
        self.assertEqual(resolve_unit("CNY").unit_id, "yuan")
        self.assertEqual(resolve_unit("万元").unit_id, "wan_yuan")
        self.assertEqual(resolve_unit("吨").unit_id, "tonne")


if __name__ == "__main__":
    unittest.main()
