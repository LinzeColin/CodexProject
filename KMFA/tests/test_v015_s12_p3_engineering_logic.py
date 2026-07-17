from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import v015_s12_p3_engineering_logic as kernel


class ChangeSettlementChainTests(unittest.TestCase):
    def test_supported_change_and_settlement_chain(self) -> None:
        result = kernel.build_change_settlement_chain(kernel._change_fixture())
        self.assertEqual(result["confirmed_change_amount_cents"], 20000)
        self.assertEqual(result["unconfirmed_change_amount_cents"], 15000)
        self.assertEqual(result["unsupported_change_recognized_cents"], 0)
        self.assertEqual(result["contract_and_supported_change_cents"], 120000)
        self.assertEqual(result["settlement_difference_cents"], -5000)
        self.assertEqual(result["invoice_collection_rate_bps"], 7778)
        self.assertTrue(result["business_decision_allowed"])

    def test_confirmed_change_without_evidence_fails(self) -> None:
        payload = kernel._change_fixture()
        payload["changes"][0]["evidence_ref"] = None
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "CONFIRMED_CHANGE_EVIDENCE_REQUIRED"):
            kernel.build_change_settlement_chain(payload)

    def test_cross_project_change_fails(self) -> None:
        payload = kernel._change_fixture()
        payload["changes"][0]["project_ref"] = "PROJECT-PUBLIC-OTHER"
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "CHANGE_SCOPE_MISMATCH"):
            kernel.build_change_settlement_chain(payload)

    def test_unresolved_collection_degrades_and_is_not_counted(self) -> None:
        result = kernel.build_change_settlement_chain(kernel._change_fixture(unresolved_collection=True))
        self.assertEqual(result["calculation_status"], kernel.DEGRADED)
        self.assertEqual(result["confirmed_collection_cents"], 0)
        self.assertFalse(result["business_decision_allowed"])

    def test_float_money_fails(self) -> None:
        payload = kernel._change_fixture()
        payload["changes"][0]["amount_cents"] = json.loads("1.25")
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "FLOAT_NOT_ALLOWED"):
            kernel.build_change_settlement_chain(payload)

    def test_change_result_is_deterministic_and_input_isolated(self) -> None:
        payload = kernel._change_fixture()
        before = copy.deepcopy(payload)
        first = kernel.build_change_settlement_chain(payload)
        second = kernel.build_change_settlement_chain(payload)
        self.assertEqual(first, second)
        self.assertEqual(payload, before)


class ExternalCostChainTests(unittest.TestCase):
    def test_cost_chain_classifies_all_required_anomalies(self) -> None:
        result = kernel.build_external_cost_chain(kernel._cost_fixture(), kernel.DEFAULT_LINK_POLICY)
        self.assertEqual(result["record_count"], 9)
        self.assertEqual(result["unique_source_key_count"], 8)
        self.assertEqual(result["duplicate_record_count"], 1)
        self.assertEqual(result["requires_confirmation_count"], 1)
        self.assertEqual(result["cross_project_anomaly_count"], 1)
        self.assertEqual(result["automatic_low_confidence_allocation_count"], 0)
        self.assertEqual(result["recognized_project_cost_cents"], 42000)
        self.assertFalse(result["business_decision_allowed"])

    def test_inventory_conservation_is_exact(self) -> None:
        result = kernel.build_external_cost_chain(kernel._cost_fixture(), kernel.DEFAULT_LINK_POLICY)
        self.assertEqual(result["inventory_receipt_cents"], 20000)
        self.assertEqual(result["inventory_issue_cents"], 12000)
        self.assertEqual(result["inventory_balance_cents"], 8000)
        self.assertEqual(result["inventory_conservation_delta_cents"], 0)

    def test_duplicate_does_not_double_count_payment(self) -> None:
        result = kernel.build_external_cost_chain(kernel._cost_fixture(), kernel.DEFAULT_LINK_POLICY)
        self.assertEqual(result["confirmed_paid_cash_cents"], 25000)
        self.assertEqual(result["duplicate_excluded_amount_cents"], 25000)

    def test_conflicting_duplicate_fails(self) -> None:
        payload = kernel._cost_fixture()
        payload["records"][6]["amount_cents"] += 1
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "DUPLICATE_SOURCE_CONFLICT"):
            kernel.build_external_cost_chain(payload, kernel.DEFAULT_LINK_POLICY)

    def test_source_effect_mismatch_fails(self) -> None:
        payload = kernel._cost_fixture()
        payload["records"][0]["cost_effect"] = "CASH_ONLY"
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "COST_EFFECT_MISMATCH"):
            kernel.build_external_cost_chain(payload, kernel.DEFAULT_LINK_POLICY)

    def test_low_confidence_threshold_is_external_and_integer(self) -> None:
        policy = {**kernel.DEFAULT_LINK_POLICY, "auto_link_min_confidence_bps": json.loads("1.5")}
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "FLOAT_NOT_ALLOWED"):
            kernel.build_external_cost_chain(kernel._cost_fixture(), policy)

    def test_cost_result_is_deterministic_and_input_isolated(self) -> None:
        payload = kernel._cost_fixture()
        before = copy.deepcopy(payload)
        first = kernel.build_external_cost_chain(payload, kernel.DEFAULT_LINK_POLICY)
        second = kernel.build_external_cost_chain(payload, kernel.DEFAULT_LINK_POLICY)
        self.assertEqual(first, second)
        self.assertEqual(payload, before)


class ExplanationLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.change = kernel.build_change_settlement_chain(kernel._change_fixture())
        self.cost = kernel.build_external_cost_chain(kernel._cost_fixture(), kernel.DEFAULT_LINK_POLICY)

    def test_professional_and_ordinary_layers_are_complete(self) -> None:
        result = kernel.build_result_explanations(self.change, self.cost)
        self.assertEqual(result["explanation_count"], 6)
        self.assertEqual(result["professional_trace_count"], 6)
        self.assertEqual(result["ordinary_summary_count"], 6)
        for row in result["explanations"]:
            self.assertTrue(row["professional_trace"])
            self.assertTrue(row["ordinary_summary_zh"])
            self.assertNotIn("FORM-", row["ordinary_summary_zh"])
            self.assertNotIn("sha256", row["ordinary_summary_zh"])

    def test_explanations_recalculate_to_source_results(self) -> None:
        explanations = kernel.build_result_explanations(self.change, self.cost)
        result = kernel.verify_explanation_consistency(explanations, self.change, self.cost)
        self.assertTrue(result["consistency_pass"])
        self.assertEqual(result["matched_result_count"], 6)
        self.assertEqual(result["mismatch_count"], 0)

    def test_one_cent_explanation_drift_fails(self) -> None:
        explanations = kernel.build_result_explanations(self.change, self.cost)
        explanations["explanations"][0]["value"] += 1
        result = kernel.verify_explanation_consistency(explanations, self.change, self.cost)
        self.assertFalse(result["consistency_pass"])
        self.assertGreaterEqual(result["mismatch_count"], 1)

    def test_source_result_tampering_fails_fingerprint(self) -> None:
        tampered = copy.deepcopy(self.change)
        tampered["confirmed_change_amount_cents"] += 1
        with self.assertRaisesRegex(kernel.EngineeringLogicError, "RESULT_FINGERPRINT_MISMATCH"):
            kernel.build_result_explanations(tampered, self.cost)

    def test_explanations_are_deterministic(self) -> None:
        first = kernel.build_result_explanations(self.change, self.cost)
        second = kernel.build_result_explanations(self.change, self.cost)
        self.assertEqual(first, second)


class PublicVerificationTests(unittest.TestCase):
    def test_public_verification_passes_every_check(self) -> None:
        result = kernel.public_verification()
        self.assertEqual(result["accounting"], {"total": 63, "passed": 63, "failed": 0})
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(result["raw_root_access_count"], 0)
        self.assertEqual(result["live_source_read_count"], 0)
        self.assertFalse(result["real_business_calculation_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
