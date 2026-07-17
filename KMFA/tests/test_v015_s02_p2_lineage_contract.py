from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools.v015_s02_p2_lineage_contract import (
    DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV,
    LineageContractError,
    build_lineage_contract_payload,
    count_actual_lineage_records,
    parse_source_domain_csv,
    validate_lineage_contract_payload,
)


class V015S02P2LineageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = build_lineage_contract_payload()

    def assert_contract_rejected(self, payload: dict) -> None:
        with self.assertRaises(LineageContractError):
            validate_lineage_contract_payload(payload)

    def test_contract_build_is_deterministic_and_phase_bounded(self) -> None:
        self.assertEqual(self.payload, build_lineage_contract_payload())
        summary = validate_lineage_contract_payload(self.payload)

        self.assertEqual(summary["edge_count"], 10)
        self.assertEqual(summary["top_level_path_field_count"], 25)
        self.assertEqual(summary["locator_kind_count"], 4)
        self.assertEqual(summary["report_target_kind_count"], 6)
        self.assertEqual(summary["hard_gate_count"], 12)
        self.assertEqual(summary["source_domain_row_count"], 21)
        self.assertEqual(summary["source_system_count"], 7)
        self.assertEqual(summary["business_line_profile_count"], 10)
        self.assertEqual(summary["actual_lineage_record_count"], 0)
        self.assertEqual(self.payload["target_release"], "v1.5")
        self.assertEqual(self.payload["task_id"], "S02P2T02")
        self.assertEqual(self.payload["status"], "PLANNING_CONTRACT_ONLY")
        self.assertFalse(self.payload["lineage_full_check_complete"])
        self.assertFalse(self.payload["formal_report_allowed"])
        self.assertFalse(self.payload["business_decision_basis_allowed"])
        self.assertFalse(self.payload["business_execution_allowed"])
        self.assertFalse(self.payload["product_implementation_allowed"])

    def test_noncanonical_release_identity_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["target_release"] = "1.5"
        self.assert_contract_rejected(mutated)

    def test_noncanonical_task_identity_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["task_id"] = "T02"
        self.assert_contract_rejected(mutated)

    def test_public_member_09_parser_is_parameterized_and_deterministic(self) -> None:
        parsed_a = parse_source_domain_csv(DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV)
        parsed_b = parse_source_domain_csv(DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV.encode("utf-8"))

        self.assertEqual(parsed_a, parsed_b)
        self.assertEqual(len(parsed_a), 21)
        self.assertEqual(len({row["source_system_code"] for row in parsed_a}), 7)
        parsed_payload = build_lineage_contract_payload(source_domain_rows=parsed_a)
        self.assertEqual(validate_lineage_contract_payload(parsed_payload)["source_domain_row_count"], 21)

    def test_protocol_headers_are_never_counted_as_actual_lineage(self) -> None:
        rows = [
            {"record_type": "protocol_header", "schema_version": "kmfa.field_lineage.v1"},
            {"record_type": "field_lineage", "lineage_record_id": "LIN-REC-001"},
        ]
        self.assertEqual(count_actual_lineage_records(rows[:1]), 0)
        self.assertEqual(count_actual_lineage_records(rows), 1)

        mutated = copy.deepcopy(self.payload)
        mutated["lineage_record_accounting"]["field"]["actual_lineage_record_count"] = 1
        self.assert_contract_rejected(mutated)

    def test_illegal_layer_edge_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["layer_edge_contract"].append(
            {
                "edge_id": "EDGE-ILLEGAL-L7-L0",
                "from_layer": "L7",
                "to_layer": "L0",
                "edge_kind": "CONTROL",
                "version_append_required": False,
                "raw_mutation_allowed": True,
            }
        )
        self.assert_contract_rejected(mutated)

    def test_zero_actual_rows_cannot_claim_full_lineage_or_release(self) -> None:
        for key in (
            "lineage_full_check_complete",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "business_execution_allowed",
            "product_implementation_allowed",
        ):
            with self.subTest(key=key):
                mutated = copy.deepcopy(self.payload)
                mutated[key] = True
                self.assert_contract_rejected(mutated)

    def test_bl10_cannot_be_forged_as_a_source_domain(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["source_domain_coverage"][0]["business_line_ids"].append("BL-10")
        self.assert_contract_rejected(mutated)

    def test_missing_top_level_path_field_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["path_record_schema"]["top_level_required_fields"].remove("source")
        self.assert_contract_rejected(mutated)

    def test_missing_required_version_binding_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["path_record_schema"]["version_required_fields"].remove("formula_version")
        self.assert_contract_rejected(mutated)

    def test_missing_amount_semantics_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["path_record_schema"]["amount_semantics_required_fields"].remove("currency")
        self.assert_contract_rejected(mutated)

    def test_binary_float_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["path_record_schema"]["amount_representation_allowed"].append("BINARY_FLOAT")
        self.assert_contract_rejected(mutated)

        mutated = copy.deepcopy(self.payload)
        mutated["path_record_schema"]["binary_float_allowed"] = True
        self.assert_contract_rejected(mutated)

    def test_unknown_parameter_default_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["path_record_schema"]["unknown_parameter_policy"] = "USE_DEFAULT"
        self.assert_contract_rejected(mutated)

    def test_public_payload_is_json_serializable_without_raw_dependency(self) -> None:
        encoded = json.dumps(self.payload, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("KMFA_MetaData", encoded)
        self.assertFalse(self.payload["public_private_plane_contract"]["raw_access_performed_by_module"])
        self.assertFalse(self.payload["public_private_plane_contract"]["raw_root_dependency_allowed"])


if __name__ == "__main__":
    unittest.main()
