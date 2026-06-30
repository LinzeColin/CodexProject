import json
import unittest

from KMFA.tools.project_scope_reconciliation import (
    REQUIRED_HUMAN_FIELDS,
    REQUIRED_RECONCILIATION_DOMAINS,
    ProjectScopeReconciliationError,
    build_default_project_scope_reconciliation_layer,
    validate_project_scope_reconciliation_artifacts,
)


class ProjectScopeReconciliationTests(unittest.TestCase):
    def test_default_layer_builds_required_domains_and_reconciliation_records(self) -> None:
        manifest, records, domain_controls = build_default_project_scope_reconciliation_layer(
            generated_at="2026-06-30T23:55:00+10:00"
        )
        validate_project_scope_reconciliation_artifacts(manifest, records, domain_controls)

        self.assertEqual(manifest["stage_phase"], "S09-P3")
        self.assertEqual(set(manifest["required_reconciliation_domains"]), set(REQUIRED_RECONCILIATION_DOMAINS))
        self.assertEqual(manifest["summary"]["reconciliation_record_count"], len(records))
        self.assertEqual(manifest["summary"]["domain_control_count"], len(domain_controls))
        self.assertEqual(len(domain_controls), len(REQUIRED_RECONCILIATION_DOMAINS))
        self.assertGreaterEqual(len(records), 1)

        for record in records:
            for field_name in REQUIRED_HUMAN_FIELDS:
                self.assertIn(field_name, record)
            self.assertEqual(record["record_type"], "scope_reconciliation_record")
            self.assertEqual(record["stage_phase"], "S09-P3")
            self.assertTrue(record["difference_id"].startswith("S09P3-REC-"))
            self.assertIn(record["reconciliation_domain"], REQUIRED_RECONCILIATION_DOMAINS)
            self.assertTrue(record["amount_a_cents_private_ref"].startswith("private_ref://"))
            self.assertTrue(record["amount_b_cents_private_ref"].startswith("private_ref://"))
            self.assertTrue(record["delta_cents_private_ref"].startswith("private_ref://"))
            self.assertTrue(record["amount_a_cents_hash"].startswith("sha256:"))
            self.assertTrue(record["amount_b_cents_hash"].startswith("sha256:"))
            self.assertTrue(record["delta_cents_hash"].startswith("sha256:"))
            self.assertFalse(record["public_amount_values_committed"])
            self.assertFalse(record["raw_layer_write_allowed"])

    def test_reconciliation_stays_pending_and_blocks_rerun_until_confirmed(self) -> None:
        manifest, records, domain_controls = build_default_project_scope_reconciliation_layer(
            generated_at="2026-06-30T23:55:00+10:00"
        )

        self.assertEqual(manifest["summary"]["confirmed_resolution_count"], 0)
        self.assertFalse(manifest["quality_gate"]["derived_metric_rerun_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_rerun_allowed"])
        self.assertFalse(manifest["quality_gate"]["stage9_review_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage9_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["formal_report_scope_included"])
        for record in records:
            self.assertEqual(record["resolution_status"], "pending_owner_or_authorized_review")
            self.assertEqual(record["closed_at"], None)
            self.assertFalse(record["confirmed_for_rerun"])
            self.assertFalse(record["derived_metric_rerun_allowed"])
            self.assertFalse(record["formal_report_rerun_allowed"])
        for control in domain_controls:
            self.assertEqual(control["control_status"], "active_pending_difference_review")
            self.assertFalse(control["domain_confirmed_for_rerun"])

    def test_public_payload_has_no_raw_values_or_private_business_files(self) -> None:
        manifest, records, domain_controls = build_default_project_scope_reconciliation_layer(
            generated_at="2026-06-30T23:55:00+10:00"
        )
        payload = json.dumps([manifest, records, domain_controls], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_a_cents":',
            '"amount_b_cents":',
            '"delta_cents":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_csv",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            "bank_account_number",
            "identity_document_number",
        ):
            self.assertNotIn(forbidden_text, payload)
        self.assertIn("sha256:", payload)
        self.assertIn("private_ref://", payload)

    def test_validator_rejects_missing_human_readable_fields(self) -> None:
        manifest, records, domain_controls = build_default_project_scope_reconciliation_layer(
            generated_at="2026-06-30T23:55:00+10:00"
        )
        broken = [dict(records[0]), *records[1:]]
        broken[0].pop("reason_candidate")

        with self.assertRaises(ProjectScopeReconciliationError):
            validate_project_scope_reconciliation_artifacts(manifest, broken, domain_controls)


if __name__ == "__main__":
    unittest.main()
