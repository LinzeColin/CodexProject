import json
import unittest

from KMFA.tools.redcircle_postponement_policy import (
    REQUIRED_REDCIRCLE_EXPORT_TYPES,
    build_default_redcircle_postponement_policy,
    classify_redcircle_ingestion_request,
    validate_redcircle_postponement_policy,
)


class RedcirclePostponementPolicyTests(unittest.TestCase):
    def test_default_policy_reserves_four_templates_and_blocks_d15_connector(self) -> None:
        manifest, templates, connector_policy, rollback_plan = build_default_redcircle_postponement_policy(
            generated_at="2026-06-30T18:00:00+10:00"
        )
        validate_redcircle_postponement_policy(manifest, templates, connector_policy, rollback_plan)

        self.assertEqual(set(REQUIRED_REDCIRCLE_EXPORT_TYPES), {"operating", "contract", "collection", "finance"})
        self.assertEqual(set(manifest["redcircle_export_types"]), set(REQUIRED_REDCIRCLE_EXPORT_TYPES))
        self.assertEqual(manifest["summary"]["reserved_template_count"], 4)
        self.assertEqual(manifest["summary"]["rollback_plan_count"], 4)
        self.assertTrue(manifest["stage_scope"]["redcircle_scope_included"])
        self.assertFalse(manifest["stage_scope"]["finance_scope_included"])
        self.assertFalse(manifest["stage_scope"]["wps_scope_included"])
        self.assertFalse(manifest["stage_scope"]["external_connector_included"])
        self.assertFalse(manifest["mvp_scope"]["d15_file_mvp_automatic_connector_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["q5_calculation_baseline_allowed"])

        template_types = {template["export_type"] for template in templates}
        self.assertEqual(template_types, set(REQUIRED_REDCIRCLE_EXPORT_TYPES))
        for template in templates:
            self.assertEqual(template["stage_phase"], "S07-P3")
            self.assertEqual(template["template_status"], "reserved_postponed")
            self.assertFalse(template["automatic_connector_allowed"])
            self.assertTrue(template["manual_export_file_allowed"])
            self.assertTrue(template["future_ingestion_controls"]["read_only_required"])
            self.assertTrue(template["future_ingestion_controls"]["hash_retention_required"])
            self.assertTrue(template["future_ingestion_controls"]["rollback_plan_required"])
            self.assertRegex(template["template_contract_hash"], r"^sha256:[a-f0-9]{64}$")

    def test_connector_policy_requires_readonly_hash_and_rollback_for_future_use(self) -> None:
        manifest, templates, connector_policy, rollback_plan = build_default_redcircle_postponement_policy(
            generated_at="2026-06-30T18:00:00+10:00"
        )
        validate_redcircle_postponement_policy(manifest, templates, connector_policy, rollback_plan)

        self.assertEqual(connector_policy["record_type"], "redcircle_connector_postponement_policy")
        self.assertEqual(connector_policy["stage_phase"], "S07-P3")
        self.assertFalse(connector_policy["d15_file_mvp_automatic_connector_allowed"])
        self.assertEqual(connector_policy["connector_status"], "postponed_until_after_file_mvp")
        self.assertTrue(connector_policy["future_connector_controls"]["read_only_required"])
        self.assertTrue(connector_policy["future_connector_controls"]["hash_retention_required"])
        self.assertTrue(connector_policy["future_connector_controls"]["rollback_plan_required"])
        self.assertTrue(connector_policy["future_connector_controls"]["manual_approval_required"])

        rollback_by_type = {item["export_type"]: item for item in rollback_plan}
        self.assertEqual(set(rollback_by_type), set(REQUIRED_REDCIRCLE_EXPORT_TYPES))
        for item in rollback_plan:
            self.assertEqual(item["rollback_status"], "required_before_ingestion")
            self.assertTrue(item["read_only_required"])
            self.assertTrue(item["hash_retention_required"])
            self.assertTrue(item["rollback_plan_required"])
            self.assertFalse(item["raw_layer_write_allowed"])
            self.assertFalse(item["raw_source_mutation_allowed"])

    def test_ingestion_request_classification_never_stores_plaintext_or_raw_values(self) -> None:
        manual_plan = classify_redcircle_ingestion_request(
            export_type="operating",
            request_kind="manual_export_file",
            source_ref="SRC-REDCIRCLE-OPERATING-RESERVED",
        )
        connector_plan = classify_redcircle_ingestion_request(
            export_type="contract",
            request_kind="automatic_connector",
            source_ref="SRC-REDCIRCLE-CONTRACT-RESERVED",
        )

        self.assertEqual(manual_plan["ingestion_decision"], "allowed_after_private_file_registration")
        self.assertEqual(connector_plan["ingestion_decision"], "blocked_for_d15_file_mvp")
        self.assertFalse(manual_plan["automatic_connector_allowed"])
        self.assertFalse(connector_plan["automatic_connector_allowed"])
        self.assertTrue(manual_plan["future_ingestion_controls"]["read_only_required"])
        self.assertTrue(connector_plan["future_ingestion_controls"]["rollback_plan_required"])

        public_payload = json.dumps([manual_plan, connector_plan], ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "source_header_text",
            "raw_value",
            "normalized_value",
            "original_filename",
            "bank_account_number",
            "contract_plaintext",
        ):
            self.assertNotIn(forbidden, public_payload)


if __name__ == "__main__":
    unittest.main()
