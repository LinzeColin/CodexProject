import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.integration_preparation import (
    IntegrationPreparationError,
    REQUIRED_BACKLOG_IDS,
    REQUIRED_CONNECTOR_IDS,
    REQUIRED_OPME_ENTRY_SURFACES,
    build_default_integration_preparation_suite,
    validate_integration_preparation_artifacts,
    write_integration_preparation_artifacts,
)


class IntegrationPreparationTests(unittest.TestCase):
    def test_default_suite_covers_s18_p3_required_scope(self) -> None:
        manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)

        self.assertEqual(manifest["stage_phase"], "S18-P3")
        self.assertEqual(tuple(manifest["required_connector_ids"]), REQUIRED_CONNECTOR_IDS)
        self.assertEqual(tuple(manifest["required_backlog_ids"]), REQUIRED_BACKLOG_IDS)
        self.assertTrue(manifest["stage_scope"]["s18_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage18_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])
        self.assertEqual(manifest["summary"]["connector_plan_count"], 3)
        self.assertEqual(manifest["summary"]["opme_entry_surface_count"], 4)
        self.assertEqual(manifest["summary"]["backlog_item_count"], 6)
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])
        self.assertFalse(manifest["quality_gate"]["external_connector_called"])
        self.assertFalse(manifest["quality_gate"]["business_execution_allowed"])

    def test_connector_plans_are_read_only_future_proposals(self) -> None:
        manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)

        plans_by_id = {row["connector_id"]: row for row in connector_plans}
        self.assertEqual(set(plans_by_id), set(REQUIRED_CONNECTOR_IDS))
        for connector_id, row in plans_by_id.items():
            self.assertEqual(row["record_type"], "s18_p3_read_only_connector_plan")
            self.assertEqual(row["stage_phase"], "S18-P3")
            self.assertEqual(row["connector_id"], connector_id)
            self.assertEqual(row["integration_mode"], "read_only_future_connector")
            self.assertEqual(row["lifecycle_state"], "proposal_only")
            self.assertTrue(row["manual_authorization_required"])
            self.assertTrue(row["hash_retention_required"])
            self.assertFalse(row["source_mutation_allowed"])
            self.assertFalse(row["auto_write_allowed"])
            self.assertFalse(row["credential_required_now"])
            self.assertFalse(row["live_connector_called"])
            self.assertFalse(row["raw_business_data_committed"])
            self.assertFalse(row["field_plaintext_committed"])
            self.assertFalse(row["github_upload_allowed"])

    def test_opme_entry_plan_is_light_entry_only(self) -> None:
        manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)

        self.assertEqual(opme_plan["record_type"], "s18_p3_opme_entry_integration_plan")
        self.assertEqual(tuple(opme_plan["entry_surfaces"]), REQUIRED_OPME_ENTRY_SURFACES)
        self.assertEqual(opme_plan["integration_mode"], "entry_link_and_status_index_only")
        self.assertEqual(opme_plan["coupling_level"], "light_entry_only")
        self.assertFalse(opme_plan["deep_coupling_allowed"])
        self.assertFalse(opme_plan["shared_database_allowed"])
        self.assertFalse(opme_plan["sensitive_data_mixing_allowed"])
        self.assertFalse(opme_plan["opme_controls_kmfa_business_logic"])
        self.assertEqual(opme_plan["responsibility_split"]["kmfa_owner"], "project_finance_operation")
        self.assertEqual(opme_plan["responsibility_split"]["opme_owner"], "technical_service_entry_and_status")

    def test_backlog_is_public_safe_and_not_started(self) -> None:
        manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)

        backlog_by_id = {row["backlog_id"]: row for row in backlog_items}
        self.assertEqual(tuple(backlog_by_id), REQUIRED_BACKLOG_IDS)
        self.assertIn("BL-KMFA-NEXT-006", backlog_by_id)
        for row in backlog_items:
            self.assertEqual(row["record_type"], "s18_p3_next_stage_backlog_item")
            self.assertEqual(row["stage_phase"], "S18-P3")
            self.assertEqual(row["status"], "backlog_proposed_not_started")
            self.assertFalse(row["started"])
            self.assertFalse(row["business_execution_allowed"])
            self.assertFalse(row["external_connector_allowed"])
            self.assertFalse(row["github_upload_allowed"])
            self.assertFalse(row["raw_business_data_required_in_public_repo"])

    def test_public_payload_has_no_raw_private_or_secret_material(self) -> None:
        manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        payload = json.dumps([manifest, connector_plans, opme_plan, backlog_items], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            "bank_statement",
            "contract_full_text",
            "salary_detail",
            "tax_filing",
            "recipient_email",
            "smtp",
            "sk-",
            "-----BEGIN",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_missing_or_overreaching_scope(self) -> None:
        manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )

        broken_connectors = [row for row in connector_plans if row["connector_id"] != "wps"]
        with self.assertRaises(IntegrationPreparationError):
            validate_integration_preparation_artifacts(manifest, broken_connectors, opme_plan, backlog_items)

        broken_opme = copy.deepcopy(opme_plan)
        broken_opme["deep_coupling_allowed"] = True
        with self.assertRaises(IntegrationPreparationError):
            validate_integration_preparation_artifacts(manifest, connector_plans, broken_opme, backlog_items)

        broken_backlog = [row for row in backlog_items if row["backlog_id"] != "BL-KMFA-NEXT-006"]
        with self.assertRaises(IntegrationPreparationError):
            validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, broken_backlog)

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["stage_scope"]["stage18_review_scope_included"] = True
        with self.assertRaises(IntegrationPreparationError):
            validate_integration_preparation_artifacts(broken_manifest, connector_plans, opme_plan, backlog_items)

    def test_cli_validator_accepts_generated_public_safe_artifacts(self) -> None:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            manifest_path = tmp_root / "integration_preparation_manifest.json"
            connectors_path = tmp_root / "read_only_connector_plan.jsonl"
            opme_path = tmp_root / "opme_entry_integration_plan.json"
            backlog_path = tmp_root / "next_stage_backlog.jsonl"
            stage_manifest_path = tmp_root / "s18_p3_manifest.json"
            write_integration_preparation_artifacts(
                generated_at="2026-07-01T23:59:59+10:00",
                manifest_path=manifest_path,
                connectors_path=connectors_path,
                opme_path=opme_path,
                backlog_path=backlog_path,
                stage_manifest_path=stage_manifest_path,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/check_s18_p3_integration_preparation.py",
                    "--manifest",
                    str(manifest_path),
                    "--connectors",
                    str(connectors_path),
                    "--opme",
                    str(opme_path),
                    "--backlog",
                    str(backlog_path),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: KMFA S18-P3 integration preparation check passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
