from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s11_p1_quality_rules as quality


class QualityRulesTests(unittest.TestCase):
    def test_catalog_covers_eight_dimensions_and_binds_impact(self) -> None:
        catalog = quality.default_rule_catalog()
        quality.validate_configuration(catalog, quality.default_status_model(), quality.default_score_policy())
        self.assertEqual(len(catalog["dimensions"]), 8)
        self.assertEqual(len(catalog["rules"]), 16)
        self.assertEqual(sum(row["hard_gate"] for row in catalog["rules"]), 7)
        self.assertEqual(sum(row["weight_bps"] for row in catalog["rules"]), 10000)
        self.assertEqual({row["severity"] for row in catalog["rules"]}, set(quality.SEVERITIES))
        self.assertTrue(all(row["process_impact"] in quality.PROCESS_IMPACTS for row in catalog["rules"]))

    def test_all_pass_is_human_readable_and_allows_quality_flow(self) -> None:
        result = quality.evaluate_quality(quality.baseline_snapshot())
        self.assertEqual(result["display"]["label_zh"], "已通过")
        self.assertEqual(result["professional_detail"]["technical_status"], "PASSED")
        self.assertEqual(result["professional_detail"]["score_bps"], 10000)
        self.assertTrue(result["quality_flow_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertTrue(result["display"]["symbol"])
        self.assertTrue(result["display"]["reason_zh"])
        self.assertTrue(result["display"]["next_action_zh"])

    def test_high_score_never_hides_a_hard_gate_failure(self) -> None:
        snapshot = quality.baseline_snapshot()
        snapshot["duplicate_primary_key_count"] = 1
        result = quality.evaluate_quality(snapshot)
        self.assertEqual(result["professional_detail"]["score_bps"], 9375)
        self.assertEqual(result["professional_detail"]["hard_gate_failure_count"], 1)
        self.assertEqual(result["professional_detail"]["technical_status"], "NOT_USABLE")
        self.assertEqual(result["display"]["label_zh"], "不可使用")
        self.assertFalse(result["quality_flow_allowed"])

    def test_non_hard_failure_requires_confirmation(self) -> None:
        snapshot = quality.baseline_snapshot()
        snapshot["invalid_format_count"] = 1
        result = quality.evaluate_quality(snapshot)
        self.assertEqual(result["professional_detail"]["technical_status"], "REVIEW_REQUIRED")
        self.assertEqual(result["display"]["label_zh"], "需确认")
        self.assertEqual(result["professional_detail"]["hard_gate_failure_count"], 0)

    def test_outdated_source_has_explicit_text_not_color_only(self) -> None:
        snapshot = quality.baseline_snapshot()
        snapshot["source_age_minutes"] = snapshot["freshness_limit_minutes"] + 1
        result = quality.evaluate_quality(snapshot)
        self.assertEqual(result["professional_detail"]["technical_status"], "OUTDATED")
        self.assertEqual(result["display"]["label_zh"], "已过期")
        self.assertTrue(result["display"]["color_is_supplemental"])
        for key in ("symbol", "summary_zh", "reason_zh", "process_impact_zh", "next_action_zh"):
            self.assertTrue(result["display"][key])

    def test_low_score_without_hard_gate_is_not_usable(self) -> None:
        result = quality.evaluate_quality(quality.public_scenarios()["low_score_without_hard_gate"])
        self.assertEqual(result["professional_detail"]["score_bps"], 6875)
        self.assertEqual(result["professional_detail"]["hard_gate_failure_count"], 0)
        self.assertEqual(result["display"]["label_zh"], "不可使用")

    def test_thresholds_are_externalized_and_integer_only(self) -> None:
        policy = quality.default_score_policy()
        self.assertEqual(policy["pass_min_bps"], 9500)
        self.assertEqual(policy["not_usable_below_bps"], 7500)
        self.assertTrue(policy["integer_only"])
        bad = copy.deepcopy(policy)
        bad["pass_min_bps"] = 9500.0
        with self.assertRaisesRegex(quality.QualityRuleError, "PASS_THRESHOLD_INVALID"):
            quality.validate_configuration(quality.default_rule_catalog(), quality.default_status_model(), bad)

    def test_invalid_rule_weight_and_color_only_status_fail_closed(self) -> None:
        catalog = quality.default_rule_catalog()
        catalog["rules"][0]["weight_bps"] = 624
        with self.assertRaisesRegex(quality.QualityRuleError, "RULE_WEIGHT_TOTAL_INVALID"):
            quality.validate_configuration(catalog, quality.default_status_model(), quality.default_score_policy())
        statuses = quality.default_status_model()
        statuses["color_is_only_information"] = True
        with self.assertRaisesRegex(quality.QualityRuleError, "COLOR_ONLY_STATUS_REJECTED"):
            quality.validate_configuration(quality.default_rule_catalog(), statuses, quality.default_score_policy())

    def test_missing_negative_float_and_boolean_inputs_fail_closed(self) -> None:
        cases = []
        missing = quality.baseline_snapshot()
        del missing["invalid_format_count"]
        cases.append((missing, "SNAPSHOT_FIELD_MISSING"))
        negative = quality.baseline_snapshot()
        negative["invalid_format_count"] = -1
        cases.append((negative, "SNAPSHOT_VALUE_INVALID"))
        floating = quality.baseline_snapshot()
        floating["invalid_format_count"] = 1.0
        cases.append((floating, "SNAPSHOT_VALUE_INVALID"))
        boolean = quality.baseline_snapshot()
        boolean["invalid_format_count"] = True
        cases.append((boolean, "SNAPSHOT_VALUE_INVALID"))
        for snapshot, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(quality.QualityRuleError, code):
                    quality.evaluate_quality(snapshot)

    def test_evaluation_is_deterministic(self) -> None:
        first = quality.evaluate_quality(quality.baseline_snapshot())
        second = quality.evaluate_quality(quality.baseline_snapshot())
        self.assertEqual(first, second)
        self.assertRegex(first["evaluation_fingerprint"], r"^sha256:[0-9a-f]{64}$")

    def test_public_verification_is_fully_passing_and_public_safe(self) -> None:
        verification = quality.public_verification()
        self.assertGreaterEqual(verification["accounting"]["total"], 50)
        self.assertEqual(verification["accounting"]["failed"], 0)
        self.assertEqual(verification["accounting"]["passed"], verification["accounting"]["total"])
        self.assertTrue(all(row["status"] == "PASS" for row in verification["checks"]))
        self.assertEqual(verification["raw_root_access_count"], 0)
        self.assertEqual(verification["live_source_read_count"], 0)
        self.assertFalse(verification["github_upload_performed"])
        self.assertFalse(verification["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
