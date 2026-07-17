from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s18_p1_receivables_collections as builder
from KMFA.tools import v015_s18_p1_receivables_collections as subject


MODEL_ID = "MOD-KMFA-RECEIVABLES-001"
FORMULA_ID = "FORM-KMFA-V015-S18-P1-RECEIVABLES-COLLECTIONS-001"


class ReceivablesCollectionsGovernanceTests(unittest.TestCase):
    def test_project_mirrors_track_only_s18_p1(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                subject.RUN_PHASE_ID,
                subject.TASK_ID,
                subject.ACCEPTANCE_ID,
                "governance_model_count: 14",
                "active_formula_count: 385",
                "active_parameter_count: 2220",
                'current_parameter_range: "PARAM-KMFA-2586..2605"',
                "stage_execution_percentage: 33",
                's17_stage_review_acceptance_status: "PASSED"',
                "s18_p1_started: true",
                "s18_p1_source_item_count: 8",
                "s18_p1_invoice_item_count: 7",
                "s18_p1_open_receivable_count: 6",
                "s18_p1_unbilled_item_count: 1",
                "s18_p1_aging_bucket_count: 5",
                "s18_p1_priority_component_count: 5",
                "s18_p1_priority_component_max_total: 107",
                "s18_p1_evidence_missing_count: 1",
                "s18_p1_unsupported_recommendation_count: 0",
                "s18_p1_automatic_customer_contact_count: 0",
                "s18_p1_group_dimension_count: 4",
                "s18_p1_group_difference_cents: 0",
                "s18_p1_cross_company_leak_count: 0",
                "s18_p1_browser_flow_count: 8",
                "s18_p1_visual_evidence_count: 5",
                "s18_p1_public_check_count: 50",
                "s18_p1_raw_root_access_count: 0",
                "s18_p2_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameters_are_bound(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row
            for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 2586 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2605
        ]
        self.assertEqual(len(selected), 20)
        self.assertTrue(
            all(
                row["model_id"] == MODEL_ID
                and row["formula_id"] == FORMULA_ID
                and row["status"] == "active"
                and row["fact_level"] == "EXTRACTED"
                for row in selected
            )
        )
        for token in (
            FORMULA_ID,
            "source_item_count == 8",
            "unbilled_item_count == 1",
            "priority_component_max_total == 107",
            "unsupported_recommendation_count == 0",
            "automatic_customer_contact_count == 0",
            "group_difference_cents == 0",
            "cross_company_leak_count == 0",
            "raw_root_access_count == 0",
        ):
            self.assertIn(token, formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s18_p1_receivables_collections:", text)
            self.assertIn(MODEL_ID, text)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S18-P1-RECEIVABLES-COLLECTIONS", trace)
        self.assertIn("PARAM-KMFA-2586;PARAM-KMFA-2587", trace)
        self.assertIn(f'{MODEL_ID}: "{subject.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s18_p1_receivables_collections: "{subject.VERSION}"', version)
        self.assertIn("total_active_parameters: 2220", assurance)
        self.assertIn("total_active_formulas: 385", assurance)
        self.assertIn(FORMULA_ID, spec)

    def test_human_records_use_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in (
            "README.md",
            "HANDOFF.md",
            "CHANGELOG.md",
            "docs/governance/DEVELOPMENT_LEDGER.md",
            "docs/governance/OWNER_STATUS.md",
            "docs/governance/STATUS.md",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S18-P1", text, relative)
        self.assertIn("未开票", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("没有联系客户", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_and_action_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"live_source_read_count": 0',
            '"external_network_request_count": 0',
            '"real_identity_count": 0',
            '"credential_count": 0',
            '"real_business_action_count": 0',
            '"source_data_write_count": 0',
            '"fact_layer_write_count": 0',
            '"payment_execution_count": 0',
            '"automatic_customer_contact_count": 0',
            '"s18_p2_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
