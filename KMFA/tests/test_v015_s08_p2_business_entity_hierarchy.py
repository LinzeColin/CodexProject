from __future__ import annotations

import json
import unittest

from KMFA.tools.v015_s08_p2_business_entity_hierarchy import (
    BusinessEntityError,
    aggregate_funds,
    build_account_directory,
    build_company_registry,
    build_counterparty_master,
    resolve_account_alias,
    resolve_counterparty_name,
    synthetic_acceptance_cases,
)


class BusinessEntityHierarchyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = synthetic_acceptance_cases()

    def test_every_record_is_assigned_or_explicitly_requires_confirmation(self) -> None:
        assignments = self.cases["entity_assignment_cases"]
        self.assertEqual(
            [row["assignment_status"] for row in assignments],
            ["ASSIGNED", "REQUIRES_CONFIRMATION", "REQUIRES_CONFIRMATION"],
        )
        self.assertTrue(assignments[0]["funds_aggregation_allowed"])
        self.assertFalse(assignments[1]["funds_aggregation_allowed"])
        self.assertFalse(assignments[2]["funds_aggregation_allowed"])

    def test_unknown_entity_funds_fail_as_one_batch_without_partial_total(self) -> None:
        rejected = self.cases["unknown_entity_funds_aggregation"]
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["error_code"], "ENTITY_REQUIRED_FOR_FUNDS_AGGREGATION")
        self.assertFalse(rejected["partial_aggregation_performed"])

    def test_known_entity_funds_use_integer_cents_and_group_by_company(self) -> None:
        result = self.cases["valid_funds_aggregation"]
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["total_amount_cents"], 18000)
        self.assertEqual(
            result["company_totals"],
            [
                {"company_entity_ref": "ENT-OPS-A", "amount_cents": 10000},
                {"company_entity_ref": "ENT-OPS-B", "amount_cents": 8000},
            ],
        )
        with self.assertRaisesRegex(BusinessEntityError, "INTEGER_CENTS_REQUIRED"):
            aggregate_funds(
                [{"record_ref": "BAD-FLOAT", "company_entity_ref": "ENT-OPS-A", "amount_cents": 1.5}],
                self.cases["company_registry"],
            )

    def test_company_registry_supports_multiple_entities_and_rejects_cycles(self) -> None:
        registry = self.cases["company_registry"]
        self.assertEqual(registry["company_entity_count"], 3)
        self.assertEqual(registry["company_relationship_count"], 2)
        with self.assertRaisesRegex(BusinessEntityError, "COMPANY_HIERARCHY_CYCLE"):
            build_company_registry(
                [
                    {"company_entity_ref": "ENT-A", "display_name": "甲"},
                    {"company_entity_ref": "ENT-B", "display_name": "乙"},
                ],
                [
                    {
                        "from_company_entity_ref": "ENT-A",
                        "relationship_type": "PARENT_OF",
                        "to_company_entity_ref": "ENT-B",
                    },
                    {
                        "from_company_entity_ref": "ENT-B",
                        "relationship_type": "PARENT_OF",
                        "to_company_entity_ref": "ENT-A",
                    },
                ],
            )

    def test_account_directory_masks_every_account_and_never_returns_full_values(self) -> None:
        directory = self.cases["account_directory"]
        self.assertEqual((directory["bank_count"], directory["account_count"]), (2, 3))
        self.assertEqual(directory["masked_account_count"], 3)
        self.assertEqual(directory["public_full_account_value_count"], 0)
        self.assertTrue(all(row["masked_account"].startswith("****") for row in directory["accounts"]))
        text = json.dumps(directory, ensure_ascii=False)
        self.assertNotIn("99999999", text)
        self.assertNotIn("full_account_number", text)

    def test_account_alias_resolution_is_entity_scoped_and_cross_entity_is_high_risk(self) -> None:
        cases = self.cases["account_resolution_cases"]
        self.assertEqual(cases["same_entity_resolved"]["status"], "RESOLVED")
        self.assertTrue(cases["same_entity_resolved"]["funds_aggregation_allowed"])
        self.assertEqual(cases["cross_entity_high_risk"]["status"], "HIGH_RISK_CROSS_ENTITY_MISMATCH")
        self.assertTrue(cases["cross_entity_high_risk"]["cross_entity_mismatch"])
        self.assertFalse(cases["cross_entity_high_risk"]["funds_aggregation_allowed"])
        self.assertEqual(cases["ambiguous_requires_confirmation"]["status"], "REQUIRES_CONFIRMATION")

    def test_invalid_account_owner_or_bank_fails_closed(self) -> None:
        companies = self.cases["company_registry"]
        with self.assertRaisesRegex(BusinessEntityError, "UNKNOWN_ACCOUNT_COMPANY_ENTITY"):
            build_account_directory(
                companies,
                [{"bank_ref": "BANK-A", "display_name": "示例银行"}],
                [
                    {
                        "account_ref": "ACCOUNT-A",
                        "company_entity_ref": "ENT-NOT-REGISTERED",
                        "bank_ref": "BANK-A",
                        "full_account_number": "1" * 12,
                        "aliases": [],
                    }
                ],
            )

    def test_counterparty_roles_and_relationships_remain_multi_value(self) -> None:
        master = self.cases["counterparty_master"]
        self.assertEqual(master["counterparty_master_count"], 2)
        self.assertEqual(master["multi_role_counterparty_count"], 2)
        self.assertEqual(master["historical_name_count"], 2)
        self.assertEqual(master["forced_merge_count"], 0)
        self.assertEqual(master["masters"][0]["roles"], ["CUSTOMER", "OWNER"])
        self.assertEqual(len(master["masters"][0]["relationships"]), 2)

    def test_same_counterparty_name_is_not_force_merged_but_history_can_resolve(self) -> None:
        cases = self.cases["counterparty_resolution_cases"]
        self.assertEqual(cases["historical_name_resolved"]["status"], "RESOLVED")
        self.assertEqual(cases["same_name_not_force_merged"]["status"], "REQUIRES_CONFIRMATION")
        self.assertEqual(cases["same_name_not_force_merged"]["candidate_count"], 2)
        self.assertFalse(cases["same_name_not_force_merged"]["forced_merge_performed"])

    def test_unknown_role_is_rejected(self) -> None:
        with self.assertRaisesRegex(BusinessEntityError, "INVALID_COUNTERPARTY_ROLE"):
            build_counterparty_master(
                [{"counterparty_ref": "CP-X", "canonical_name": "示例", "roles": ["UNKNOWN"]}]
            )

    def test_missing_alias_requires_confirmation(self) -> None:
        result = resolve_account_alias("not registered", self.cases["account_directory"])
        self.assertEqual(result["status"], "REQUIRES_CONFIRMATION")
        result = resolve_counterparty_name("未登记名称", self.cases["counterparty_master"])
        self.assertEqual(result["status"], "REQUIRES_CONFIRMATION")


if __name__ == "__main__":
    unittest.main()
