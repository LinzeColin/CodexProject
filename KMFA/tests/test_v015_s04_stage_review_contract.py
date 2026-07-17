from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import v015_s04_stage_review_contract as contract


class V015S04StageReviewContractTests(unittest.TestCase):
    def test_complete_cross_phase_binding_passes(self) -> None:
        result = contract.public_verification()
        self.assertEqual(result["accounting"], {"total": 8, "passed": 8, "failed": 0})
        self.assertEqual([row["check_id"] for row in result["checks"]], list(contract.CHECK_IDS))
        self.assertTrue(all(row["status"] == "PASS" for row in result["checks"]))
        self.assertEqual(result["raw_root_access_count"], 0)
        self.assertEqual(result["actual_business_lineage_record_count"], 0)
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["production_restore_performed"])

    def test_source_version_break_fails_closed(self) -> None:
        binding = contract.build_synthetic_stage_binding()
        binding["source_version_refs"][0] = "SOURCE-VERSION::WRONG::1.0.0"
        with self.assertRaises(contract.StageReviewContractError):
            contract.validate_stage_binding(binding)

    def test_fact_lineage_break_fails_closed(self) -> None:
        binding = contract.build_synthetic_stage_binding()
        binding["field_lineage"][0]["fact_version_ref"] = "FACT-VERSION::WRONG::1.0.0"
        with self.assertRaises(contract.StageReviewContractError):
            contract.validate_stage_binding(binding)

    def test_requested_restore_version_break_fails_closed(self) -> None:
        binding = contract.build_synthetic_stage_binding()
        binding["requested_restore_version_ref"] = "REPORT-VERSION::WRONG::1.0.0"
        with self.assertRaises(Exception):
            contract.validate_stage_binding(binding)

    def test_public_projection_contains_no_private_import_hash(self) -> None:
        encoded = json.dumps(contract.public_verification(), sort_keys=True)
        self.assertNotIn("file_hash", encoded)
        self.assertNotIn("sha256:", encoded)
        self.assertNotIn("/Users/", encoded)

    def test_caller_mutation_does_not_create_false_pass(self) -> None:
        binding = contract.build_synthetic_stage_binding()
        tampered = copy.deepcopy(binding)
        tampered["event_version_bindings"][tampered["events"][-1]["event_id"]] = [
            "REPORT-VERSION::WRONG::1.0.0"
        ]
        with self.assertRaises(contract.StageReviewContractError):
            contract.validate_stage_binding(tampered)


if __name__ == "__main__":
    unittest.main()
