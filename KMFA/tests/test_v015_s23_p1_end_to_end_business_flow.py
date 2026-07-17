from __future__ import annotations

import unittest

from KMFA.tools import v015_s20_p3_recalculation_publication as publication_kernel
from KMFA.tools import v015_s21_p2_report_generation as report_generation
from KMFA.tools import v015_s23_p1_end_to_end_business_flow as kernel


class EndToEndBusinessFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verification = kernel.public_verification()

    def test_taskpack_source_contract_is_exact(self) -> None:
        contract = kernel.source_contract()
        self.assertEqual(contract["roadmap_phase_id"], "S23-P1")
        self.assertEqual(contract["task_ids"], ["S23P1T01", "S23P1T02", "S23P1T03"])
        self.assertEqual(
            contract["acceptance_zh"],
            ["后端状态、页面和报告一致。", "权威项目零差异。", "页面、HTML、PDF、Excel 一致。"],
        )

    def test_authoritative_homepage_and_report_use_same_publication(self) -> None:
        publication = publication_kernel.baseline_publication()
        home = kernel.authoritative_homepage_snapshot(publication)
        report = report_generation.demo_report_model()
        payload = kernel.build_authoritative_report_payload(report, publication)
        result = kernel.assert_authoritative_zero_difference(publication, home, payload)
        self.assertEqual(result["difference_cents"], 0)
        self.assertEqual(home["publication_version_id"], payload["publication_version_id"])
        self.assertEqual(home["shared_metric_fingerprint"], payload["shared_metric_fingerprint"])

    def test_project_allocation_reconciles_every_integer_cent(self) -> None:
        publication = publication_kernel.baseline_publication()
        rows = kernel.authoritative_projects(publication)
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(row["revenue_cents"] for row in rows), publication["facts"]["project_revenue_cents"])
        self.assertEqual(sum(row["cost_cents"] for row in rows), publication["facts"]["project_cost_cents"])
        self.assertEqual(sum(row["gross_profit_cents"] for row in rows), publication["metrics"]["project_margin_cents"])
        self.assertTrue(all(row["revenue_cents"] - row["cost_cents"] == row["gross_profit_cents"] for row in rows))

    def test_public_verification_covers_export_approval_revision_and_refresh(self) -> None:
        value = self.verification
        self.assertEqual((value["status"], value["fail_count"]), ("PASS", 0))
        self.assertGreaterEqual(value["check_count"], 45)
        self.assertEqual(value["result"]["formats"], ["HTML", "PDF", "CSV", "XLSX"])
        self.assertEqual(value["result"]["cross_format_difference_integer"], 0)
        self.assertEqual(value["result"]["latest_workflow_state"], "PUBLISHED_INTERNAL")
        self.assertEqual(len(value["result"]["report_versions"]), 2)
        self.assertTrue(value["result"]["refresh_persistence_passed"])

    def test_scope_stops_before_later_phases_and_release(self) -> None:
        self.assertEqual(
            kernel.scope_boundary(),
            {
                "raw_root_access_count": 0,
                "raw_write_count": 0,
                "external_network_request_count": 0,
                "github_upload_count": 0,
                "app_reinstall_count": 0,
                "s23_p2_execution_count": 0,
                "s23_p3_execution_count": 0,
                "stage_review_execution_count": 0,
            },
        )


if __name__ == "__main__":
    unittest.main()
