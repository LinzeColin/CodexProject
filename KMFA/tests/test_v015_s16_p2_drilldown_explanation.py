from __future__ import annotations

import unittest

from KMFA.tools import v015_s16_p2_drilldown_explanation as kernel


class DrilldownKernelTests(unittest.TestCase):
    def test_source_contract_is_exact_s16_p2(self) -> None:
        value = kernel.source_contract()
        self.assertEqual(value["roadmap_phase_id"], "S16-P2")
        self.assertEqual(value["task_ids"], ["S16P2T01", "S16P2T02", "S16P2T03"])
        self.assertEqual(value["data_classification"], "PUBLIC_SYNTHETIC")

    def test_five_homepage_metrics_have_stable_detail_paths(self) -> None:
        self.assertEqual(len(kernel.METRIC_SPECS), 5)
        for metric_id, slug in kernel.METRIC_SLUGS.items():
            path = f"/overview/detail/{slug}"
            self.assertEqual(kernel.detail_path(metric_id), path)
            self.assertEqual(kernel.metric_from_path(path), metric_id)

    def test_all_detail_totals_match_homepage(self) -> None:
        for metric_id in kernel.METRIC_SPECS:
            with self.subTest(metric_id=metric_id):
                value = kernel.drilldown_snapshot(metric_id=metric_id)
                self.assertTrue(value["detail_available"])
                self.assertGreaterEqual(value["detail_row_count"], 3)
                self.assertEqual(value["consistency"]["primary_difference"], 0)
                self.assertIn(value["consistency"]["secondary_difference"], (None, 0))

    def test_context_and_filters_are_preserved(self) -> None:
        value = kernel.drilldown_snapshot(
            company="demo-south",
            period="2026-Q2",
            project_status="attention",
            report_version="previous",
        )
        self.assertTrue(value["context_preserved"])
        self.assertEqual(value["filter_count"], 4)
        self.assertEqual(
            {key: value["context"][key] for key in ("company", "period", "project_status", "report_version")},
            {
                "company": "demo-south",
                "period": "2026-Q2",
                "project_status": "attention",
                "report_version": "previous",
            },
        )

    def test_plain_explanation_precedes_traceable_professional_lineage(self) -> None:
        value = kernel.drilldown_snapshot(metric_id="PROJECT_GROSS_PROFIT")
        explanation = value["explanation"]
        self.assertTrue(explanation["short_explanation_zh"])
        self.assertFalse(explanation["technical_log_default_visible"])
        self.assertEqual(explanation["technical_log_count"], 0)
        self.assertEqual(explanation["professional_lineage_node_count"], 4)
        self.assertTrue(all(row["source_ref"] for row in explanation["professional_lineage_nodes"]))

    def test_three_comparison_kinds_require_exact_basis_and_coverage(self) -> None:
        for kind in kernel.COMPARISON_KINDS:
            with self.subTest(kind=kind):
                value = kernel.drilldown_snapshot(metric_id="PROJECT_GROSS_PROFIT", comparison_kind=kind)["comparison"]
                self.assertTrue(value["comparison_allowed"])
                self.assertTrue(value["basis_consistent"])
                self.assertTrue(value["coverage_consistent"])
                self.assertEqual(value["coverage_bps"], 10_000)

    def test_mismatched_basis_or_coverage_is_blocked_with_human_reason(self) -> None:
        basis = kernel.drilldown_snapshot(comparison_state="basis_mismatch")["comparison"]
        coverage = kernel.drilldown_snapshot(comparison_state="coverage_mismatch")["comparison"]
        self.assertFalse(basis["comparison_allowed"])
        self.assertIn("口径不同", basis["block_reason_zh"])
        self.assertFalse(coverage["comparison_allowed"])
        self.assertIn("覆盖范围不同", coverage["block_reason_zh"])

    def test_incomplete_data_or_lineage_hides_unsupported_detail(self) -> None:
        partial = kernel.drilldown_snapshot(metric_id="OVERDUE_RECEIVABLE", data_state="partial")
        missing_lineage = kernel.drilldown_snapshot(lineage_state="missing")
        for value in (partial, missing_lineage):
            self.assertFalse(value["detail_available"])
            self.assertEqual(value["detail_rows"], [])
            self.assertFalse(value["comparison"]["comparison_allowed"])

    def test_permission_denial_contains_no_detail(self) -> None:
        value = kernel.drilldown_snapshot(user_id="demo-finance", role_id="finance", company="demo-south")
        self.assertFalse(value["allowed"])
        self.assertEqual(value["detail_rows"], [])

    def test_contract_is_public_integer_only_and_side_effect_free(self) -> None:
        value = kernel.build_contract()
        self.assertEqual(value["public_check_failed_count"], 0)
        self.assertEqual(value["public_check_pass_count"], 78)
        for key in (
            "raw_root_access_count",
            "live_source_read_count",
            "external_network_request_count",
            "real_business_action_count",
        ):
            self.assertEqual(value[key], 0)


if __name__ == "__main__":
    unittest.main()
