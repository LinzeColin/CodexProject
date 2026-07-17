from __future__ import annotations

import unittest

from KMFA.tools import v015_s23_p2_precision_stress_extreme as model


class PrecisionStressExtremeTests(unittest.TestCase):
    def test_taskpack_contract_and_scope_are_exact(self) -> None:
        contract = model.source_contract()
        self.assertEqual(contract["task_ids"], ["S23P2T01", "S23P2T02", "S23P2T03"])
        self.assertEqual(contract["acceptance_zh"], ["0 分误差。", "达到约定响应和资源门槛。", "系统安全失败且可恢复。"])
        self.assertTrue(all(value == 0 for value in model.scope_boundary().values()))

    def test_precision_uses_integer_cents_and_zero_difference(self) -> None:
        value = model.precision_probe(case_count=500, worksheet_count=8, project_count=200, account_count=50)
        self.assertEqual((value["status"], value["difference_cents"], value["float_money_accept_count"]), ("PASS", 0, 0))
        self.assertEqual(model.round_ratio_half_away_from_zero(5, 2), 3)
        self.assertEqual(model.round_ratio_half_away_from_zero(-5, 2), -3)
        with self.assertRaisesRegex(model.PrecisionStressError, "整数分"):
            model.round_ratio_half_away_from_zero(1.0, 2)  # type: ignore[arg-type]

    def test_scale_concurrency_uses_real_import_and_report_paths(self) -> None:
        value = model.scale_concurrency_probe(file_count=8, worksheet_count=8, project_count=200, account_count=50, import_count=8, report_count=8, workers=4)
        self.assertEqual((value["status"], value["data_error_count"], value["completed_import_count"], value["consistent_report_fingerprint_count"]), ("PASS", 0, 8, 1))

    def test_extreme_inputs_fail_closed_and_recover(self) -> None:
        value = model.extreme_malicious_recovery_probe()
        self.assertEqual((value["status"], value["attack_case_count"], value["rejected_attack_count"]), ("PASS", 9, 9))
        self.assertEqual((value["safe_interruption_count"], value["successful_recovery_count"], value["data_pollution_count"]), (1, 1, 0))
        self.assertNotIn("NOT_REJECTED", {row["error_code"] for row in value["cases"]})

    def test_full_public_workload_passes_49_checks(self) -> None:
        value = model.public_verification()
        self.assertEqual((value["status"], value["check_count"], value["pass_count"], value["fail_count"]), ("PASS", 49, 49, 0))
        self.assertEqual((value["precision"]["difference_cents"], value["scale"]["data_error_count"], value["extreme"]["data_pollution_count"]), (0, 0, 0))

    def test_invalid_dimensions_and_zero_denominator_fail(self) -> None:
        with self.assertRaisesRegex(model.PrecisionStressError, "大于 0"):
            model.precision_probe(case_count=0)
        with self.assertRaisesRegex(model.PrecisionStressError, "分母"):
            model.round_ratio_half_away_from_zero(1, 0)


if __name__ == "__main__":
    unittest.main()
