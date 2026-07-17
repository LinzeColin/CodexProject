from __future__ import annotations

import unittest

from KMFA.tools import v015_s05_p3_field_standardization as kernel


class V015S05P3FieldStandardizationTests(unittest.TestCase):
    def test_dictionary_covers_eight_domains_and_required_attributes(self) -> None:
        fields = kernel.validate_field_dictionary()
        self.assertEqual(len(fields), 24)
        self.assertEqual({field.domain for field in fields}, set(kernel.DOMAINS))
        self.assertEqual(sum(field.critical for field in fields), 16)
        for field in fields:
            public = field.to_public_dict()
            for key in ("definition_zh", "data_type", "unit", "source_classes", "required_when"):
                self.assertTrue(public[key])
            self.assertFalse("/Users/" in str(public))

    def test_dictionary_rejects_missing_domain_duplicate_and_invalid_amount_format(self) -> None:
        with self.assertRaisesRegex(kernel.FieldContractError, "eight field domains"):
            kernel.validate_field_dictionary(kernel.STANDARD_FIELDS[:-3])
        with self.assertRaisesRegex(kernel.FieldContractError, "duplicate field"):
            kernel.validate_field_dictionary((*kernel.STANDARD_FIELDS, kernel.STANDARD_FIELDS[0]))
        field = kernel.STANDARD_FIELDS[8]
        invalid = kernel.FieldDefinition(**{**field.__dict__, "storage_format": "DECIMAL_YUAN"})
        with self.assertRaisesRegex(kernel.FieldContractError, "amount format"):
            kernel.validate_field_dictionary((*kernel.STANDARD_FIELDS[:8], invalid, *kernel.STANDARD_FIELDS[9:]))

    def test_alias_rules_are_versioned_and_exact_rules_auto_map(self) -> None:
        registry = kernel.AliasRegistry()
        decision = registry.resolve("项目名称")
        self.assertEqual(decision.status, "AUTO_MAPPED")
        self.assertEqual(decision.canonical_field_id, "project_name")
        self.assertEqual(decision.version, kernel.MAPPING_VERSION)
        self.assertEqual(decision.confidence_bps, 10000)

    def test_low_confidence_typo_and_history_require_confirmation(self) -> None:
        registry = kernel.AliasRegistry()
        typo = registry.resolve("合同編号", template_class="CONTRACT_REGISTER")
        historical = registry.resolve("客商名称", template_class="CUSTOMER_MASTER")
        self.assertEqual((typo.status, typo.action), ("MANUAL_CONFIRMATION", "MANUAL_CONFIRMATION"))
        self.assertEqual((historical.status, historical.action), ("MANUAL_CONFIRMATION", "MANUAL_CONFIRMATION"))
        self.assertLess(typo.confidence_bps or 10000, 9900)

    def test_template_specific_amount_alias_never_guesses_without_context(self) -> None:
        registry = kernel.AliasRegistry()
        self.assertEqual(registry.resolve("金额").status, "AMBIGUOUS")
        self.assertEqual(registry.resolve("金额").action, "MANUAL_CONFIRMATION")
        self.assertEqual(
            registry.resolve("金额", template_class="INVOICE_REGISTER").canonical_field_id,
            "invoice_amount_cents",
        )

    def test_same_template_alias_collision_is_rejected(self) -> None:
        first = kernel.AliasRule("A", "金额", "cost_amount_cents", "X", "TEMPLATE_VARIANT", 9900)
        second = kernel.AliasRule("B", "金额", "invoice_amount_cents", "X", "TEMPLATE_VARIANT", 9900)
        with self.assertRaisesRegex(kernel.FieldContractError, "collision"):
            kernel.AliasRegistry((first, second))

    def test_unregistered_alias_enters_quality_queue(self) -> None:
        decision = kernel.AliasRegistry().resolve("完全未登记字段")
        self.assertEqual((decision.status, decision.action), ("UNREGISTERED", "QUALITY_QUEUE"))
        self.assertIsNone(decision.canonical_field_id)

    def test_blank_dash_unknown_not_applicable_and_parse_failure_are_distinct(self) -> None:
        values = {
            None: kernel.ValueSemantic.BLANK,
            "   ": kernel.ValueSemantic.BLANK,
            "-": kernel.ValueSemantic.DASH,
            "未知": kernel.ValueSemantic.UNKNOWN_VALUE,
            "不适用": kernel.ValueSemantic.NOT_APPLICABLE,
        }
        for value, expected in values.items():
            result = kernel.classify_value("cost_amount_cents", value)
            self.assertEqual(result.semantic, expected)
            self.assertFalse(result.derivation_allowed)
            self.assertIsNone(result.normalized_value)
            self.assertFalse(result.is_zero)
        failed = kernel.classify_value("cost_amount_cents", "10.5")
        self.assertEqual(failed.semantic, kernel.ValueSemantic.PARSE_FAILED)

    def test_zero_is_observed_zero_and_blank_never_becomes_zero(self) -> None:
        for value in (0, "0"):
            result = kernel.classify_value("invoice_amount_cents", value)
            self.assertEqual(result.semantic, kernel.ValueSemantic.ZERO)
            self.assertEqual(result.normalized_value, 0)
            self.assertTrue(result.derivation_allowed)
            self.assertTrue(result.is_zero)
        blank = kernel.classify_value("invoice_amount_cents", "")
        self.assertNotEqual(blank.semantic, kernel.ValueSemantic.ZERO)
        self.assertIsNone(blank.normalized_value)

    def test_amount_float_and_invalid_date_fail_closed(self) -> None:
        self.assertEqual(
            kernel.classify_value("contract_amount_cents", 1.0).semantic,
            kernel.ValueSemantic.PARSE_FAILED,
        )
        self.assertEqual(
            kernel.classify_value("invoice_date", "2026-02-30").semantic,
            kernel.ValueSemantic.PARSE_FAILED,
        )
        self.assertEqual(
            kernel.classify_value("invoice_date", "2026-02-28").normalized_value,
            "2026-02-28",
        )

    def test_explicit_parser_failure_overrides_apparent_value(self) -> None:
        result = kernel.classify_value("project_name", "项目A", parse_failed=True)
        self.assertEqual(result.semantic, kernel.ValueSemantic.PARSE_FAILED)
        self.assertEqual(result.action, "QUALITY_QUEUE")
        self.assertFalse(result.derivation_allowed)


if __name__ == "__main__":
    unittest.main()
