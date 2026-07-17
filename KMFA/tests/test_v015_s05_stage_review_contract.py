from __future__ import annotations

import unittest

from KMFA.tools import v015_s05_p1_amount_precision as amount
from KMFA.tools import v015_s05_p2_date_period as date_period
from KMFA.tools import v015_s05_stage_review_contract as contract


class V015S05StageReviewContractTests(unittest.TestCase):
    def test_public_verification_passes_all_ten_checks(self) -> None:
        result = contract.public_verification()
        self.assertEqual(result["accounting"], {"total": 10, "passed": 10, "failed": 0})
        self.assertEqual([row["check_id"] for row in result["checks"]], list(contract.CHECK_IDS))
        self.assertEqual(result["unit_bindings"], {"CNY_CENT": "fen"})
        self.assertEqual(result["raw_root_access_count"], 0)

    def test_amount_path_preserves_signed_integer_cents_and_zero(self) -> None:
        positive = contract.standardize_amount_field("金额", 101, template_class="COST_REGISTER")
        negative = contract.standardize_amount_field("回款金额分", -9)
        zero = contract.standardize_amount_field("发票金额分", 0)
        self.assertEqual((positive["amount_cents"], negative["amount_cents"]), (101, -9))
        self.assertEqual((positive["dictionary_unit"], positive["amount_unit_id"]), ("CNY_CENT", "fen"))
        self.assertEqual((zero["semantic"], zero["amount_cents"]), ("ZERO", 0))

    def test_float_blank_and_non_integer_amounts_fail_closed(self) -> None:
        for value in (1.0, "", None, "10.5", "-"):
            with self.subTest(value=value):
                with self.assertRaises(contract.StageReviewContractError):
                    contract.standardize_amount_field("合同金额分", value)

    def test_ambiguous_low_confidence_and_unregistered_aliases_fail_closed(self) -> None:
        cases = (
            ("金额", None),
            ("含税金额", "CONTRACT_REGISTER"),
            ("完全未登记字段", None),
        )
        for alias, template in cases:
            with self.subTest(alias=alias):
                with self.assertRaises(contract.StageReviewContractError):
                    contract.standardize_amount_field(alias, 1, template_class=template)

    def test_wrong_field_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(contract.StageReviewContractError, "not a registered cents field"):
            contract.standardize_amount_field("项目名称", 1)
        with self.assertRaisesRegex(contract.StageReviewContractError, "not a registered business-date field"):
            contract.standardize_date_field(
                "项目名称", "2026-07-15", source_kind="DATE", business_timezone="Australia/Sydney"
            )

    def test_date_path_normalizes_before_iso_storage(self) -> None:
        result = contract.standardize_date_field(
            "开票日",
            "2026-07-15T23:30:00+00:00",
            source_kind="DATETIME",
            business_timezone="Australia/Sydney",
            template_class="INVOICE_REGISTER",
        )
        self.assertEqual(result["business_date"], "2026-07-16")
        self.assertEqual(
            result["normalization_order"],
            ["ALIAS_RESOLUTION", "S05_P2_DATE_NORMALIZATION", "S05_P3_STORAGE_CLASSIFICATION"],
        )

    def test_date_policy_cannot_be_bypassed(self) -> None:
        with self.assertRaises(date_period.DatePeriodError):
            contract.standardize_date_field(
                "开票日期", "2026-07-15", source_kind="DATE", business_timezone=""
            )
        with self.assertRaises(date_period.DatePeriodError):
            contract.standardize_date_field(
                "开票日期", "2026-07-15 10:00:00", source_kind="DATETIME",
                business_timezone="Australia/Sydney", source_timezone=None,
            )

    def test_adapter_does_not_weaken_p1_float_guard(self) -> None:
        with self.assertRaises(amount.AmountPrecisionError):
            amount.Money.from_value(1.0, unit="fen")
        with self.assertRaises(contract.StageReviewContractError):
            contract.standardize_amount_field("合同金额分", 1.0)


if __name__ == "__main__":
    unittest.main()
