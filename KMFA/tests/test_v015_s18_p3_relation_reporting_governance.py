from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s18_p3_relation_reporting as builder
from KMFA.tools import v015_s18_p3_relation_reporting as subject


MODEL_ID = "MOD-KMFA-CASH-REPORT-001"
FORMULA_ID = "FORM-KMFA-V015-S18-P3-RELATION-REPORTING-001"


class RelationReportingGovernanceTests(unittest.TestCase):
    def test_project_mirrors_track_only_s18_p3(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                subject.RUN_PHASE_ID,
                subject.TASK_ID,
                subject.ACCEPTANCE_ID,
                "governance_model_count: 16",
                "active_formula_count: 387",
                "active_parameter_count: 2260",
                'current_parameter_range: "PARAM-KMFA-2626..2645"',
                "stage_execution_percentage: 100",
                's18_p2_acceptance_status: "PASSED"',
                "s18_p3_started: true",
                "s18_p3_project_count: 6",
                "s18_p3_profit_cash_substitution_count: 0",
                "s18_p3_scope_limitation_displayed_count: 6",
                "s18_p3_profit_equation_difference_cents: 0",
                "s18_p3_cash_occupancy_reconciliation_difference_cents: 0",
                "s18_p3_alert_count: 5",
                "s18_p3_alert_type_count: 3",
                "s18_p3_thresholds_externalized: true",
                "s18_p3_full_sensitive_detail_count: 0",
                "s18_p3_notification_send_count: 0",
                "s18_p3_report_page_row_count: 6",
                "s18_p3_report_appendix_row_count: 6",
                "s18_p3_report_page_export_difference_cents: 0",
                "s18_p3_degraded_report_test_count: 1",
                "s18_p3_unverified_numeric_visible_count: 0",
                "s18_p3_browser_flow_count: 9",
                "s18_p3_visual_evidence_count: 6",
                "s18_p3_public_check_count: 76",
                "s18_p3_raw_root_access_count: 0",
                "s18_stage_review_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameters_are_bound(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 2626 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2645]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID and row["status"] == "active" and row["fact_level"] == "EXTRACTED" for row in selected))
        for token in (
            FORMULA_ID,
            "project_count == 6",
            "profit_cash_substitution_count == 0",
            "profit_equation_difference_cents == 0",
            "alert_type_count == 3",
            "thresholds_externalized == true",
            "full_sensitive_detail_count == 0",
            "report_page_export_difference_cents == 0",
            "unverified_numeric_visible_count == 0",
            "raw_root_access_count == 0",
        ):
            self.assertIn(token, formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s18_p3_relation_reporting:", text)
            self.assertIn(MODEL_ID, text)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S18-P3-RELATION-REPORTING", trace)
        self.assertIn("PARAM-KMFA-2626;PARAM-KMFA-2627", trace)
        self.assertIn(f'{MODEL_ID}: "{subject.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s18_p3_relation_reporting: "{subject.VERSION}"', version)
        self.assertIn("total_active_parameters: 2260", assurance)
        self.assertIn("total_active_formulas: 387", assurance)
        self.assertIn(FORMULA_ID, spec)

    def test_human_records_use_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(subject.RUN_PHASE_ID, text, relative)
        for relative in ("README.md", "HANDOFF.md", "CHANGELOG.md", "docs/governance/DEVELOPMENT_LEDGER.md", "docs/governance/OWNER_STATUS.md", "docs/governance/STATUS.md", "docs/governance/DELIVERY_PLAN.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S18-P3", text, relative)
        self.assertIn("两套数字", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("未核验", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_private_action_and_release_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"live_source_read_count": 0',
            '"external_network_request_count": 0',
            '"full_sensitive_detail_count": 0',
            '"notification_send_count": 0',
            '"external_message_count": 0',
            '"payment_execution_count": 0',
            '"bank_operation_count": 0',
            '"s18_stage_review_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
