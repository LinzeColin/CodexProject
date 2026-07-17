import copy
import unittest

from KMFA.tools import v015_s13_p1_indicator_registry as kernel


class TestV015S13P1IndicatorRegistry(unittest.TestCase):
    def test_registry_covers_all_required_business_domains(self) -> None:
        rows = kernel.indicator_registry()
        summary = kernel.validate_indicator_registry(rows)
        self.assertEqual((summary["indicator_count"], summary["domain_count"]), (8, 8))
        self.assertEqual({row["domain"] for row in rows}, set(kernel.INDICATOR_DOMAINS))
        for row in rows:
            for field in ("formula_zh", "unit", "period_kind", "source_contract_refs", "limitations_zh"):
                self.assertTrue(row[field])
            self.assertTrue(row["source_required"])
            self.assertFalse(row["display_without_source_allowed"])
            self.assertFalse(row["frontend_definition_write_allowed"])
            self.assertFalse(row["production_direct_write_allowed"])

    def test_indicator_without_source_is_rejected(self) -> None:
        rows = kernel.indicator_registry()
        rows[0]["source_contract_refs"] = []
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "SOURCE_REQUIRED"):
            kernel.validate_indicator_registry(rows)

    def test_duplicate_and_incomplete_indicator_are_rejected(self) -> None:
        duplicate = kernel.indicator_registry()
        duplicate[1]["indicator_id"] = duplicate[0]["indicator_id"]
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "INDICATOR_DUPLICATE"):
            kernel.validate_indicator_registry(duplicate)
        incomplete = kernel.indicator_registry()
        del incomplete[0]["limitations_zh"]
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "INDICATOR_FIELD_MISSING"):
            kernel.validate_indicator_registry(incomplete)

    def test_parameter_versions_require_reason_approval_and_regression(self) -> None:
        rows = kernel.parameter_versions()
        summary = kernel.validate_parameter_versions(rows)
        self.assertEqual(summary["parameter_count"], 8)
        for row in rows:
            self.assertTrue(row["rationale_zh"])
            self.assertTrue(row["approval_ref"])
            self.assertTrue(row["regression_case_ids"])
            self.assertFalse(row["frontend_write_allowed"])
            self.assertFalse(row["production_direct_write_allowed"])

    def test_parameter_direct_write_and_immutable_conflict_are_rejected(self) -> None:
        row = kernel.parameter_versions()[0]
        direct = copy.deepcopy(row)
        direct["frontend_write_allowed"] = True
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "DIRECT_WRITE_REJECTED"):
            kernel.ParameterVersionRegistry().register(direct)
        registry = kernel.ParameterVersionRegistry()
        first = registry.register(row)
        replay = registry.register(row)
        self.assertEqual(first, replay)
        conflict = copy.deepcopy(row)
        conflict["value"] = False
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "IMMUTABLE_VERSION_CONFLICT"):
            registry.register(conflict)

    def test_parameter_float_and_missing_regression_are_rejected(self) -> None:
        floating = copy.deepcopy(kernel.parameter_versions()[0])
        floating["value"] = 1.5
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "PARAMETER_VALUE_INVALID"):
            kernel.ParameterVersionRegistry().register(floating)
        missing = copy.deepcopy(kernel.parameter_versions()[0])
        missing["regression_case_ids"] = []
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "REGRESSION_REQUIRED"):
            kernel.ParameterVersionRegistry().register(missing)

    def test_safe_ratio_has_explicit_boundaries(self) -> None:
        self.assertEqual(kernel.safe_ratio_bps(1, 3)["value"], 3333)
        self.assertEqual(kernel.safe_ratio_bps(-1, 4)["value"], -2500)
        self.assertEqual(kernel.safe_ratio_bps(1, 0)["status"], "ZERO_DENOMINATOR")
        self.assertEqual(kernel.safe_ratio_bps(1, -4)["status"], "NEGATIVE_DENOMINATOR_UNSUPPORTED")
        self.assertEqual(kernel.safe_ratio_bps(1, -4, negative_denominator_allowed=True)["value"], -2500)
        self.assertEqual(kernel.safe_ratio_bps(None, 4)["status"], "MISSING_INPUT")
        self.assertEqual(kernel.safe_ratio_bps(1, 4, sample_size=1, minimum_sample_size=2)["status"], "SMALL_SAMPLE")

    def test_money_and_ratio_reject_float_and_bool(self) -> None:
        for value in (1.0, True):
            with self.assertRaisesRegex(kernel.IndicatorRegistryError, "INTEGER_REQUIRED"):
                kernel.safe_ratio_bps(value, 2)
            with self.assertRaisesRegex(kernel.IndicatorRegistryError, "INTEGER_REQUIRED"):
                kernel.bridge_delta_cents([value], [1])

    def test_trend_bridge_sort_and_missing_are_deterministic(self) -> None:
        self.assertEqual(kernel.trend_change_bps(125, 100)["value"], 2500)
        self.assertEqual(kernel.trend_change_bps(5, 0)["status"], "ZERO_DENOMINATOR")
        self.assertEqual(kernel.bridge_delta_cents([10_000, 5_000], [4_000, 1_000])["value"], 10_000)
        self.assertEqual(kernel.bridge_delta_cents(None, [1])["status"], "MISSING_INPUT")
        rows = [
            {"indicator_id": "IND-BBB", "priority_score_bps": 7000},
            {"indicator_id": "IND-AAA", "priority_score_bps": 7000},
            {"indicator_id": "IND-CCC", "priority_score_bps": 5000},
        ]
        self.assertEqual([row["indicator_id"] for row in sorted(rows, key=kernel.priority_sort_key)], ["IND-AAA", "IND-BBB", "IND-CCC"])
        self.assertEqual(kernel.availability_gate({"a": None}, sample_size=1)["missing_fields"], ["a"])

    def test_private_material_is_rejected(self) -> None:
        rows = kernel.indicator_registry()
        rows[0]["limitations_zh"] = "/" + "Users" + "/example/private"
        with self.assertRaisesRegex(kernel.IndicatorRegistryError, "PRIVATE_VALUE_REJECTED"):
            kernel.validate_indicator_registry(rows)

    def test_function_contracts_are_complete_and_fail_closed(self) -> None:
        rows = kernel.function_contracts()
        summary = kernel.validate_function_contracts(rows)
        self.assertEqual(summary["function_count"], 5)
        self.assertEqual({row["function_id"] for row in rows}, set(kernel.FUNCTION_IDS))
        self.assertTrue(all(row["silent_exception_allowed"] is False for row in rows))

    def test_public_verification_is_complete_and_deterministic(self) -> None:
        first = kernel.public_verification()
        second = kernel.public_verification()
        self.assertEqual(first, second)
        self.assertEqual(first["accounting"], {"total": 78, "passed": 78, "failed": 0})
        self.assertEqual(first["failed_checks"], [])
        self.assertFalse(first["summary"]["health_score_computed"])
        self.assertFalse(first["summary"]["action_priority_computed"])
        self.assertEqual(first["summary"]["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
