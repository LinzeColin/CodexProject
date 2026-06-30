import json
import unittest

from KMFA.tools.entity_matching_quality import (
    QUALITY_SCENARIOS,
    build_default_entity_matching_quality,
    validate_entity_matching_quality_artifacts,
)


class EntityMatchingQualityTests(unittest.TestCase):
    def test_default_quality_scenarios_cover_name_entity_account_and_period_risks(self) -> None:
        manifest, cases, report, review_queue = build_default_entity_matching_quality(
            generated_at="2026-06-30T22:00:00+10:00"
        )
        validate_entity_matching_quality_artifacts(manifest, cases, report, review_queue)

        scenario_types = {case["scenario_type"] for case in cases}
        self.assertEqual(
            scenario_types,
            {
                "same_project_name",
                "multiple_company_entities",
                "multiple_accounts",
                "multiple_periods",
            },
        )
        self.assertEqual(set(QUALITY_SCENARIOS), scenario_types)
        self.assertEqual(manifest["summary"]["scenario_count"], 4)
        self.assertEqual(manifest["summary"]["quality_case_count"], len(cases))
        self.assertGreaterEqual(manifest["summary"]["manual_review_queue_count"], 3)
        self.assertEqual(report["report_type"], "entity_matching_report")
        self.assertFalse(report["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_mismatch_risks_enter_manual_review_without_auto_merge(self) -> None:
        manifest, cases, report, review_queue = build_default_entity_matching_quality(
            generated_at="2026-06-30T22:00:00+10:00"
        )

        risk_cases = [case for case in cases if case["risk_level"] in {"medium", "high"}]
        self.assertTrue(risk_cases)
        self.assertEqual(len(review_queue), report["manual_review_queue_count"])
        for case in risk_cases:
            self.assertTrue(case["manual_review_required"])
            self.assertFalse(case["auto_merge_allowed"])
            self.assertIn(case["case_id"], {item["case_id"] for item in review_queue})
        for queue_item in review_queue:
            self.assertEqual(queue_item["queue_type"], "entity_matching_quality_manual_review")
            self.assertFalse(queue_item["auto_merge_allowed"])
            self.assertFalse(queue_item["raw_layer_write_allowed"])

    def test_public_payload_has_no_raw_values_or_field_plaintext(self) -> None:
        manifest, cases, report, review_queue = build_default_entity_matching_quality(
            generated_at="2026-06-30T22:00:00+10:00"
        )
        payload = json.dumps([manifest, cases, report, review_queue], ensure_ascii=False, sort_keys=True)

        for forbidden_key in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_csv",
            "bank_account_number",
            "identity_document_number",
            "account_number",
            "project_name_plaintext",
            "customer_name_plaintext",
        ):
            self.assertNotIn(forbidden_key, payload)
        self.assertIn("profile_ref", payload)
        self.assertIn("entity_ref", payload)
        self.assertIn("source_hash", payload)

    def test_scope_excludes_stage_review_fact_layer_lineage_report_ui_connector_and_upload(self) -> None:
        manifest, cases, report, review_queue = build_default_entity_matching_quality(
            generated_at="2026-06-30T22:00:00+10:00"
        )

        self.assertTrue(manifest["stage_scope"]["s08_p3_matching_quality_scope_included"])
        for flag in (
            "stage8_review_scope_included",
            "fact_layer_scope_included",
            "lineage_full_check_scope_included",
            "formal_report_scope_included",
            "ui_scope_included",
            "external_connector_scope_included",
        ):
            self.assertFalse(manifest["stage_scope"][flag])


if __name__ == "__main__":
    unittest.main()
