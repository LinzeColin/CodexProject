from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s12_p1_project_cost_facts as builder


class ProjectCostFactsArtifactTests(unittest.TestCase):
    def test_s11_review_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 24)
        self.assertTrue(dependency["s12_p1_entry_allowed"])
        self.assertFalse(dependency["s12_p1_started"])

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_income_contract_keeps_five_layers_and_blocks_unknown_scope(self) -> None:
        contract = json.loads(builder.INCOME_CONTRACT_PATH.read_text(encoding="utf-8"))["fact_contract"]
        self.assertEqual(
            contract["income_layers"],
            ["CONTRACT", "CHANGE_ORDER", "SETTLEMENT", "INVOICE", "COLLECTION"],
        )
        self.assertEqual(contract["amount_bases"], ["TAX_INCLUSIVE", "TAX_EXCLUSIVE", "UNKNOWN"])
        self.assertFalse(contract["unknown_basis_combination_allowed"])
        self.assertFalse(contract["cross_layer_combination_allowed"])
        self.assertIn("period_ref", contract["required_fields"])
        self.assertIn("period_version", contract["required_fields"])

    def test_cost_and_pool_contracts_cover_categories_traceability_and_conservation(self) -> None:
        cost = json.loads(builder.COST_CONTRACT_PATH.read_text(encoding="utf-8"))["fact_contract"]
        pool = json.loads(builder.POOL_CONTRACT_PATH.read_text(encoding="utf-8"))["pool_contract"]
        self.assertEqual(len(cost["cost_categories"]), 10)
        self.assertEqual(len(cost["traceability_fields"]), 7)
        self.assertTrue(cost["unknown_cost_routes_to_pool"])
        self.assertEqual(len(pool["reason_codes"]), 4)
        self.assertFalse(pool["dropped_cost_allowed"])
        self.assertFalse(pool["average_allocation_allowed"])
        self.assertFalse(pool["silent_classification_allowed"])
        self.assertEqual(pool["money_tolerance_cents"], 0)

    def test_public_verification_and_conservation_are_exact(self) -> None:
        verification = json.loads(builder.VERIFICATION_PATH.read_text(encoding="utf-8"))
        conservation = json.loads(builder.CONSERVATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(verification["accounting"], {"total": 63, "passed": 63, "failed": 0})
        self.assertEqual(verification["failed_checks"], [])
        self.assertEqual(conservation["input_cost_fact_count"], 13)
        self.assertEqual(conservation["allocated_cost_fact_count"], 10)
        self.assertEqual(conservation["unallocated_cost_pool_count"], 3)
        self.assertEqual(conservation["input_cost_cents"], 70000)
        self.assertEqual(conservation["allocated_cost_cents"], 55000)
        self.assertEqual(conservation["unallocated_cost_cents"], 15000)
        self.assertEqual(conservation["conservation_delta_cents"], 0)
        self.assertEqual(conservation["dropped_cost_fact_count"], 0)
        self.assertEqual(conservation["average_allocation_count"], 0)
        self.assertEqual(conservation["silent_classification_count"], 0)

    def test_manifest_and_task_matrix_advance_only_p2_entry(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        tasks = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(tasks["phase_acceptance_status"], manifest["phase_acceptance_status"])
        self.assertEqual(tasks["task_accepted_count"], 3 if accepted else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 32 if accepted else 31)
        self.assertEqual(manifest["s12_p2_entry_allowed"], accepted)
        self.assertFalse(manifest["s12_p2_started"])
        self.assertFalse(manifest["s12_p3_entry_allowed"])
        self.assertFalse(manifest["s12_stage_review_entry_allowed"])
        self.assertFalse(manifest["formal_calculation_performed"])

    def test_human_files_use_plain_chinese_and_state_limits(self) -> None:
        implementation = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.FACT_GUIDE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        for token in ("合同、变更、结算、开票和回款", "未归集池", "差额为 0 分", "没有读取原始财务资料"):
            self.assertIn(token, implementation)
        self.assertIn("本阶段不计算毛利", guide)
        self.assertIn("不计算合同毛利", risks)
        self.assertIn("不触碰原始资料", risks)


if __name__ == "__main__":
    unittest.main()
