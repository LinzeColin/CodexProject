import json
import unittest

from KMFA.tools.check_v014_s18_p3_integration_preparation import (
    validate_v014_s18_p3_integration_preparation,
)
from KMFA.tools.v014_s18_p3_integration_preparation import (
    REQUIRED_BACKLOG_IDS,
    REQUIRED_CONNECTOR_IDS,
    REQUIRED_OPME_ENTRY_SURFACES,
    generate,
)


class V014S18P3IntegrationPreparationTests(unittest.TestCase):
    def test_v014_s18_p3_locks_future_readonly_integration_without_running_connectors(self) -> None:
        manifest = generate(generated_at="2026-07-05T18:20:00+10:00")
        validated = validate_v014_s18_p3_integration_preparation()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_s18_p3_integration_preparation.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S18")
        self.assertEqual(validated["phase_id"], "S18-P3")
        self.assertEqual(validated["phase_scope"], "v014_s18_p3_integration_preparation_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S18-P3-INTEGRATION-PREPARATION-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S18-P3-INTEGRATION-PREPARATION"])
        self.assertEqual(validated["completed_task_ids"], ["S18P3T01", "S18P3T02", "S18P3T03"])

        self.assertTrue(validated["s18_p2_dependency_validated"])
        self.assertTrue(validated["historical_s18_p3_public_safe_baseline_validated"])
        self.assertEqual(tuple(validated["required_connector_ids"]), REQUIRED_CONNECTOR_IDS)
        self.assertEqual(tuple(validated["required_opme_entry_surfaces"]), REQUIRED_OPME_ENTRY_SURFACES)
        self.assertEqual(tuple(validated["required_backlog_ids"]), REQUIRED_BACKLOG_IDS)

        progress = validated["stage18_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 10000)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s18_p1_performed"])
        self.assertTrue(progress["s18_p2_performed"])
        self.assertTrue(progress["s18_p3_performed"])
        self.assertFalse(progress["stage18_review_performed"])

        summary = validated["integration_preparation_summary"]
        self.assertEqual(summary["connector_plan_count"], 3)
        self.assertEqual(summary["read_only_connector_count"], 3)
        self.assertEqual(summary["opme_entry_surface_count"], 4)
        self.assertEqual(summary["backlog_item_count"], 6)
        self.assertEqual(summary["live_connector_call_count"], 0)
        self.assertEqual(summary["external_service_call_count"], 0)
        self.assertEqual(summary["next_required_phase"], "S18_STAGE_REVIEW")

        connector_ids = [row["connector_id"] for row in validated["read_only_connector_plans"]]
        self.assertEqual(tuple(connector_ids), REQUIRED_CONNECTOR_IDS)
        for row in validated["read_only_connector_plans"]:
            self.assertEqual(row["integration_mode"], "read_only_future_connector")
            self.assertEqual(row["lifecycle_state"], "proposal_only")
            self.assertTrue(row["manual_authorization_required"])
            self.assertTrue(row["hash_retention_required"])
            self.assertTrue(row["rollback_required"])
            for key in (
                "source_mutation_allowed",
                "auto_write_allowed",
                "credential_required_now",
                "live_connector_called",
                "external_service_called",
                "raw_business_data_committed",
                "field_plaintext_committed",
                "github_upload_allowed",
                "business_execution_allowed",
            ):
                self.assertFalse(row[key], f"{row['connector_id']}.{key}")

        opme = validated["opme_entry_plan"]
        self.assertEqual(tuple(opme["entry_surfaces"]), REQUIRED_OPME_ENTRY_SURFACES)
        self.assertEqual(opme["integration_mode"], "entry_link_and_status_index_only")
        self.assertEqual(opme["coupling_level"], "light_entry_only")
        for key in (
            "deep_coupling_allowed",
            "shared_database_allowed",
            "sensitive_data_mixing_allowed",
            "opme_controls_kmfa_business_logic",
            "kmfa_controls_opme_service_logic",
            "external_service_called",
            "raw_business_data_committed",
            "field_plaintext_committed",
            "credential_committed",
            "github_upload_allowed",
            "business_execution_allowed",
        ):
            self.assertFalse(opme[key], key)

        backlog_ids = [row["backlog_id"] for row in validated["next_stage_backlog"]]
        self.assertEqual(tuple(backlog_ids), REQUIRED_BACKLOG_IDS)
        for row in validated["next_stage_backlog"]:
            self.assertEqual(row["status"], "backlog_proposed_not_started")
            self.assertFalse(row["started"])
            self.assertFalse(row["business_execution_allowed"])
            self.assertFalse(row["external_connector_allowed"])
            self.assertFalse(row["github_upload_allowed"])
            self.assertFalse(row["raw_business_data_required_in_public_repo"])

        quality = validated["quality_gate"]
        for key in (
            "read_only_connector_plan_created",
            "opme_entry_plan_created",
            "next_stage_backlog_created",
            "stage18_review_next_required",
            "metadata_only",
            "public_safe_proposal_only",
            "no_live_connector_called",
        ):
            self.assertTrue(quality[key], key)
        for key in (
            "stage18_review_allowed_in_this_phase",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "external_connector_called",
            "external_connector_allowed",
            "live_connector_called",
            "source_mutation_allowed",
            "credential_required_now",
            "business_execution_allowed",
            "production_restore_allowed",
            "official_report_release_allowed",
            "business_decision_basis_allowed",
            "lineage_full_check_complete",
            "delivery_allowed",
            "raw_business_data_used",
        ):
            self.assertFalse(quality[key], key)

        go_no_go = validated["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("STAGE18_REVIEW_PENDING", go_no_go["blocker_ids"])
        self.assertIn("LINEAGE_FULL_CHECK_NOT_COMPLETE", go_no_go["blocker_ids"])
        self.assertIn("OFFICIAL_REPORT_RELEASE_NOT_ALLOWED", go_no_go["blocker_ids"])
        self.assertNotIn("S18_P3_PENDING", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["delivery_allowed"])
        self.assertFalse(go_no_go["business_decision_basis_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])

        for key, value in validated["raw_data_boundary"].items():
            self.assertFalse(value, key)

        payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "raw_value",
            "normalized_value",
            "source_header_text",
            "original_filename",
            "private_ref://",
            "member_sha256",
            "actual_package_sha256",
            "amount_cents:",
            "amount_yuan:",
            "customer_name_plaintext",
            "project_name_plaintext",
            "credential_payload",
            "connector_token",
        ):
            self.assertNotIn(forbidden, payload)

        self.assertFalse(validated["github_upload"]["github_upload_performed"])
        self.assertTrue(validated["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S18_STAGE_REVIEW")


if __name__ == "__main__":
    unittest.main()
