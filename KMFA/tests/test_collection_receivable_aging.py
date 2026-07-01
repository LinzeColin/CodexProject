import json
import unittest

from KMFA.tools.collection_receivable_aging import (
    REQUIRED_ISSUE_TYPES,
    REQUIRED_SOURCE_LANES,
    CollectionReceivableAgingError,
    build_default_collection_receivable_aging_artifacts,
    validate_collection_receivable_aging_artifacts,
)


class CollectionReceivableAgingTests(unittest.TestCase):
    def test_default_runtime_covers_s13_p2_required_scope(self) -> None:
        manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
            build_default_collection_receivable_aging_artifacts(generated_at="2026-07-01T18:00:00+10:00")
        )
        validate_collection_receivable_aging_artifacts(
            manifest, source_lanes, priority_items, responsibility_items, html_outputs
        )

        self.assertEqual(manifest["stage_phase"], "S13-P2")
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_issue_types"]), REQUIRED_ISSUE_TYPES)
        self.assertEqual(manifest["summary"]["source_lane_count"], 5)
        self.assertEqual(manifest["summary"]["required_issue_type_count"], 4)
        self.assertEqual(manifest["summary"]["priority_item_count"], 4)
        self.assertEqual(manifest["summary"]["responsibility_item_count"], 4)
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["legal_collection_decision_allowed"])
        self.assertFalse(manifest["quality_gate"]["payment_or_bank_operation_allowed"])
        self.assertFalse(manifest["stage_scope"]["s13_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage13_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_cover_collection_aging_journal_and_invoice_plan_inputs(self) -> None:
        manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
            build_default_collection_receivable_aging_artifacts(generated_at="2026-07-01T18:00:00+10:00")
        )
        validate_collection_receivable_aging_artifacts(
            manifest, source_lanes, priority_items, responsibility_items, html_outputs
        )

        lane_by_id = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lane_by_id), set(REQUIRED_SOURCE_LANES))
        self.assertEqual(lane_by_id["collection_table"]["source_kind"], "wps_collection_export")
        self.assertEqual(lane_by_id["receivable_aging"]["source_kind"], "wps_receivable_aging_export")
        self.assertEqual(lane_by_id["customer_aging"]["finance_categories"], ["customer_aging"])
        self.assertEqual(lane_by_id["journal"]["finance_categories"], ["journal"])
        self.assertEqual(lane_by_id["invoice_plan"]["finance_categories"], ["invoice"])

        for lane in source_lanes:
            self.assertEqual(lane["record_type"], "collection_receivable_aging_source_lane")
            self.assertGreaterEqual(lane["source_count"], 1)
            self.assertGreaterEqual(lane["field_mapping_count"], 5)
            self.assertTrue(lane["all_sources_readonly"])
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["formal_report_allowed"])
            self.assertFalse(lane["business_decision_basis_allowed"])

    def test_priority_items_cover_required_issue_types_and_responsibility(self) -> None:
        manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
            build_default_collection_receivable_aging_artifacts(generated_at="2026-07-01T18:00:00+10:00")
        )
        validate_collection_receivable_aging_artifacts(
            manifest, source_lanes, priority_items, responsibility_items, html_outputs
        )

        self.assertEqual({item["issue_type"] for item in priority_items}, set(REQUIRED_ISSUE_TYPES))
        self.assertEqual({item["issue_type"] for item in responsibility_items}, set(REQUIRED_ISSUE_TYPES))
        self.assertEqual([item["priority_rank"] for item in priority_items], [1, 2, 3, 4])

        for item in priority_items:
            self.assertEqual(item["record_type"], "collection_receivable_priority_item")
            self.assertTrue(item["customer_group_ref"].startswith("public_customer_group_ref_"))
            self.assertTrue(item["project_group_ref"].startswith("public_project_group_ref_"))
            self.assertFalse(item["raw_business_values_allowed"])
            self.assertFalse(item["collection_action_allowed"])
            self.assertFalse(item["legal_collection_decision_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

        for item in responsibility_items:
            self.assertEqual(item["record_type"], "collection_receivable_responsibility_item")
            self.assertIn(item["responsible_role"], {"finance_owner", "project_owner", "sales_owner"})
            self.assertFalse(item["payment_or_bank_operation_allowed"])
            self.assertFalse(item["legal_collection_decision_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

    def test_rendered_html_is_public_safe_and_business_readable(self) -> None:
        manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
            build_default_collection_receivable_aging_artifacts(generated_at="2026-07-01T18:00:00+10:00")
        )
        validate_collection_receivable_aging_artifacts(
            manifest, source_lanes, priority_items, responsibility_items, html_outputs
        )

        self.assertEqual(set(html_outputs), {"collection_receivable_aging_priority"})
        html_text = html_outputs["collection_receivable_aging_priority"]
        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 经营分析系统", html_text)
        self.assertIn("回款应收账龄", html_text)
        self.assertIn("已开票未回款", html_text)
        self.assertIn("完工未结算", html_text)
        self.assertIn("结算未开票", html_text)
        self.assertIn("超期应收", html_text)
        self.assertIn("不可作为催收、付款、法务或经营决策依据", html_text)
        for forbidden_visible in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_or_credentials(self) -> None:
        manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
            build_default_collection_receivable_aging_artifacts(generated_at="2026-07-01T18:00:00+10:00")
        )
        payload = json.dumps(
            [manifest, source_lanes, priority_items, responsibility_items, html_outputs],
            ensure_ascii=False,
            sort_keys=True,
        )

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            "private_csv",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_s13_p3_formal_report_or_payment_scope(self) -> None:
        manifest, source_lanes, priority_items, responsibility_items, html_outputs = (
            build_default_collection_receivable_aging_artifacts(generated_at="2026-07-01T18:00:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["formal_report_allowed"] = True
        with self.assertRaises(CollectionReceivableAgingError):
            validate_collection_receivable_aging_artifacts(
                broken_manifest, source_lanes, priority_items, responsibility_items, html_outputs
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s13_p3_scope_included"] = True
        with self.assertRaises(CollectionReceivableAgingError):
            validate_collection_receivable_aging_artifacts(
                broken_manifest, source_lanes, priority_items, responsibility_items, html_outputs
            )

        broken_items = [dict(priority_items[0]), *priority_items[1:]]
        broken_items[0]["collection_action_allowed"] = True
        with self.assertRaises(CollectionReceivableAgingError):
            validate_collection_receivable_aging_artifacts(
                manifest, source_lanes, broken_items, responsibility_items, html_outputs
            )


if __name__ == "__main__":
    unittest.main()
