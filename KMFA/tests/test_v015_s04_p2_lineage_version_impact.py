from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools.v015_s04_p2_lineage_version_impact import (
    LineageVersionError,
    analyze_impact,
    reconstruct_historical_report,
    synthetic_field_lineage_records,
    synthetic_impact_graph,
    synthetic_version_chain,
    validate_field_lineage,
    validate_version_chain,
)


class V015S04P2LineageVersionImpactTests(unittest.TestCase):
    def test_critical_amount_and_status_lineage_is_complete(self) -> None:
        records = synthetic_field_lineage_records()
        summary = validate_field_lineage(records)
        self.assertEqual(summary["lineage_coverage_bps"], 10_000)
        self.assertEqual(summary["declared_critical_field_count"], 4)
        self.assertEqual(summary["critical_field_class_count"], 2)
        self.assertEqual(summary["actual_business_lineage_record_count"], 0)
        self.assertEqual(summary["synthetic_lineage_record_count"], 4)
        self.assertFalse(summary["formal_report_allowed"])

    def test_missing_critical_field_fails_closed(self) -> None:
        with self.assertRaises(LineageVersionError):
            validate_field_lineage(synthetic_field_lineage_records()[:-1])

    def test_raw_value_or_incomplete_path_is_rejected(self) -> None:
        records = synthetic_field_lineage_records()
        records[0]["contains_raw_business_value"] = True
        with self.assertRaises(LineageVersionError):
            validate_field_lineage(records)
        records = synthetic_field_lineage_records()
        del records[0]["cell_ref"]
        with self.assertRaises(LineageVersionError):
            validate_field_lineage(records)

    def test_time_travel_rebuild_orders_all_historical_inputs(self) -> None:
        result = reconstruct_historical_report(
            synthetic_version_chain(),
            "REPORT-VERSION::management_overview::1.0.0",
        )
        self.assertEqual(result["status"], "REBUILDABLE")
        self.assertEqual(len(result["rebuild_order"]), 4)
        self.assertEqual(result["rebuild_order"][-1], "REPORT-VERSION::management_overview::1.0.0")
        self.assertFalse(result["formal_report_allowed"])

    def test_missing_historical_input_is_truthfully_not_rebuildable(self) -> None:
        chain = synthetic_version_chain()
        chain["source_versions"].remove("SOURCE-VERSION::SYNTHETIC-BANK::1.0.0")
        result = reconstruct_historical_report(
            chain,
            "REPORT-VERSION::management_overview::1.0.0",
        )
        self.assertEqual(result["status"], "NOT_REBUILDABLE")
        self.assertEqual(
            result["missing_input_version_refs"],
            ["SOURCE-VERSION::SYNTHETIC-BANK::1.0.0"],
        )
        self.assertEqual(result["rebuild_order"], [])

    def test_every_derived_node_has_three_version_bindings(self) -> None:
        chain = synthetic_version_chain()
        summary = validate_version_chain(chain)
        self.assertEqual(summary["derived_version_node_type_count"], 3)
        self.assertEqual(summary["required_version_binding_count"], 3)
        mutated = copy.deepcopy(chain)
        del mutated["nodes"][0]["formula_version"]
        with self.assertRaises(LineageVersionError):
            validate_version_chain(mutated)

    def test_impact_is_transitive_and_excludes_unrelated_nodes(self) -> None:
        result = analyze_impact(
            synthetic_impact_graph(),
            ["FORMULA::COLLECTION-RATIO"],
        )
        self.assertTrue(result["scope_known"])
        self.assertEqual(
            result["affected_refs"],
            [
                "METRIC::COLLECTION-RATIO",
                "PAGE::MANAGEMENT-OVERVIEW",
                "REPORT::MANAGEMENT-OVERVIEW",
            ],
        )
        self.assertNotIn("FACT::UNRELATED-STATUS", result["affected_refs"])
        self.assertFalse(result["automatic_publication_allowed"])

    def test_unknown_change_or_cycle_blocks_automatic_publication(self) -> None:
        unknown = analyze_impact(synthetic_impact_graph(), ["RULE::UNKNOWN"])
        self.assertFalse(unknown["scope_known"])
        self.assertFalse(unknown["automatic_publication_allowed"])
        graph = synthetic_impact_graph()
        graph["edges"].append(["REPORT::MANAGEMENT-OVERVIEW", "SOURCE::LEDGER"])
        cyclic = analyze_impact(graph, ["SOURCE::LEDGER"])
        self.assertTrue(cyclic["cycle_detected"])
        self.assertFalse(cyclic["automatic_publication_allowed"])

    def test_public_fixtures_are_serializable_and_path_free(self) -> None:
        encoded = json.dumps(
            {
                "lineage": synthetic_field_lineage_records(),
                "versions": synthetic_version_chain(),
                "impact": synthetic_impact_graph(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("KMFA_MetaData", encoded)
        self.assertNotIn(".xlsx", encoded)


if __name__ == "__main__":
    unittest.main()
