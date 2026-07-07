import copy
import json
import unittest

from KMFA.tools.access_security_policy import (
    REQUIRED_AUDIT_ACTION_TYPES,
    REQUIRED_ROLES,
    REQUIRED_SENSITIVE_POLICY_CATEGORIES,
    AccessSecurityPolicyError,
    build_default_access_security_policy,
    validate_access_security_policy_artifacts,
)


class AccessSecurityPolicyTests(unittest.TestCase):
    def test_default_runtime_covers_s17_p1_required_scope(self) -> None:
        manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_access_security_policy_artifacts(
            manifest,
            role_matrix,
            sensitive_policies,
            audit_policies,
        )

        self.assertEqual(manifest["stage_phase"], "S17-P1")
        self.assertEqual(tuple(manifest["required_roles"]), REQUIRED_ROLES)
        self.assertEqual(tuple(manifest["required_sensitive_policy_categories"]), REQUIRED_SENSITIVE_POLICY_CATEGORIES)
        self.assertEqual(tuple(manifest["required_audit_action_types"]), REQUIRED_AUDIT_ACTION_TYPES)
        self.assertEqual(manifest["summary"]["role_count"], 4)
        self.assertEqual(manifest["summary"]["sensitive_policy_category_count"], 15)
        self.assertEqual(manifest["summary"]["audit_action_type_count"], 5)
        self.assertTrue(manifest["quality_gate"]["role_permission_matrix_complete"])
        self.assertTrue(manifest["quality_gate"]["sensitive_public_repo_policy_enforced"])
        self.assertTrue(manifest["quality_gate"]["audit_log_policy_complete"])
        self.assertTrue(manifest["quality_gate"]["raw_sensitive_public_repo_allowed"])
        self.assertTrue(manifest["quality_gate"]["github_upload_allowed"])
        self.assertTrue(manifest["quality_gate"]["phase_completion_upload_allowed"])
        self.assertFalse(manifest["quality_gate"]["credential_secret_public_repo_allowed"])
        self.assertFalse(manifest["quality_gate"]["notification_delivery_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["stage_scope"]["s17_p2_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s17_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage17_review_scope_included"])
        self.assertEqual(
            manifest["summary"]["public_repo_safety_status"],
            "owner_authorized_plaintext_github_allowed_except_credentials",
        )
        owner_policy = manifest["owner_authorized_plaintext_github_policy"]
        self.assertTrue(owner_policy["allowed"])
        self.assertTrue(owner_policy["requires_explicit_owner_authorization"])
        self.assertTrue(owner_policy["requires_upload_manifest"])
        self.assertEqual(owner_policy["denied_categories"], ["credential_secret"])

    def test_role_permissions_cover_management_finance_reviewer_and_readonly(self) -> None:
        manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_access_security_policy_artifacts(
            manifest,
            role_matrix,
            sensitive_policies,
            audit_policies,
        )

        roles = {row["role_id"]: row for row in role_matrix}
        self.assertEqual(set(roles), set(REQUIRED_ROLES))
        for role_id, row in roles.items():
            self.assertEqual(row["record_type"], "access_role_permission")
            self.assertGreaterEqual(len(row["allowed_public_safe_actions"]), 2)
            if role_id == "readonly":
                self.assertFalse(row["raw_business_data_access_in_public_repo"])
                self.assertFalse(row["sensitive_file_public_commit_allowed"])
            else:
                self.assertTrue(row["raw_business_data_access_in_public_repo"])
                self.assertTrue(row["sensitive_file_public_commit_allowed"])
                self.assertTrue(row["owner_authorization_required_for_sensitive_commit"])
            self.assertFalse(row["credential_access_allowed"])
            self.assertFalse(row["business_execution_allowed"])
            self.assertFalse(row["bypass_quality_gate_allowed"])
            self.assertFalse(row["notification_body_report_allowed"])
            self.assertTrue(row["audit_required"])
            self.assertTrue(row["least_privilege_applied"])
            if role_id == "readonly":
                self.assertEqual(row["max_write_scope"], "none")
            else:
                self.assertEqual(row["max_write_scope"], "metadata_and_owner_authorized_plaintext_upload_manifest")

    def test_sensitive_policy_allows_owner_authorized_plaintext_except_credentials(self) -> None:
        manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_access_security_policy_artifacts(
            manifest,
            role_matrix,
            sensitive_policies,
            audit_policies,
        )

        categories = {row["category_id"]: row for row in sensitive_policies}
        self.assertEqual(set(categories), set(REQUIRED_SENSITIVE_POLICY_CATEGORIES))
        for category_id, row in categories.items():
            self.assertEqual(row["record_type"], "public_repo_sensitive_data_policy")
            self.assertIn("explicit_owner_authorization_required", row["enforcement_controls"])
            if category_id == "credential_secret":
                self.assertFalse(row["public_repo_allowed"])
                self.assertFalse(row["git_upload_allowed"])
                self.assertFalse(row["value_plaintext_allowed"])
                self.assertTrue(row["metadata_hash_or_ref_only_allowed"])
                self.assertFalse(row["credential_secret_allowed"])
                self.assertEqual(row["handling"], "secret_or_credential_never_plaintext_public_repo")
            else:
                self.assertTrue(row["public_repo_allowed"])
                self.assertTrue(row["git_upload_allowed"])
                self.assertTrue(row["value_plaintext_allowed"])
                self.assertFalse(row["metadata_hash_or_ref_only_allowed"])
                self.assertTrue(row["metadata_hash_or_ref_allowed"])
                self.assertTrue(row["requires_explicit_owner_authorization"])
                self.assertFalse(row["credential_secret_allowed"])
                self.assertEqual(row["handling"], "owner_authorized_plaintext_github_upload")

    def test_audit_policy_records_import_processing_report_export_and_notification(self) -> None:
        manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_access_security_policy_artifacts(
            manifest,
            role_matrix,
            sensitive_policies,
            audit_policies,
        )

        actions = {row["action_type"]: row for row in audit_policies}
        self.assertEqual(set(actions), set(REQUIRED_AUDIT_ACTION_TYPES))
        for action_type, row in actions.items():
            self.assertEqual(row["record_type"], "audit_log_policy")
            self.assertTrue(row["append_only"])
            self.assertTrue(row["requires_actor_role"])
            self.assertTrue(row["requires_event_time"])
            self.assertTrue(row["requires_evidence_ref"])
            self.assertFalse(row["raw_payload_allowed"])
            self.assertFalse(row["private_document_allowed"])
            self.assertFalse(row["business_value_plaintext_allowed"])
            self.assertEqual(row["metadata_target"], "KMFA/metadata/security/audit_events.jsonl")
            if action_type == "notification":
                self.assertFalse(row["sends_full_report_body"])
                self.assertEqual(row["delivery_scope"], "log_policy_only_s17_p2_not_implemented")

    def test_public_payload_has_no_raw_files_values_private_refs_or_live_secrets(self) -> None:
        manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        payload = json.dumps(
            [manifest, role_matrix, sensitive_policies, audit_policies],
            ensure_ascii=False,
            sort_keys=True,
        )

        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "identity_document_number",
            '"amount_cents":',
            '"amount_yuan":',
            '"project_name_plaintext":',
            '"customer_name_plaintext":',
            "sk-",
            "-----BEGIN",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_missing_roles_sensitive_allowance_audit_gap_or_scope_escape(self) -> None:
        manifest, role_matrix, sensitive_policies, audit_policies = build_default_access_security_policy(
            generated_at="2026-07-01T23:55:00+10:00"
        )

        broken_roles = [row for row in role_matrix if row["role_id"] != "readonly"]
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                manifest,
                broken_roles,
                sensitive_policies,
                audit_policies,
            )

        broken_sensitive = copy.deepcopy(sensitive_policies)
        broken_sensitive[0]["public_repo_allowed"] = False
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                manifest,
                role_matrix,
                broken_sensitive,
                audit_policies,
            )

        broken_sensitive = copy.deepcopy(sensitive_policies)
        categories = {row["category_id"]: row for row in broken_sensitive}
        categories["credential_secret"]["public_repo_allowed"] = True
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                manifest,
                role_matrix,
                broken_sensitive,
                audit_policies,
            )

        broken_audit = [row for row in audit_policies if row["action_type"] != "notification"]
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                manifest,
                role_matrix,
                sensitive_policies,
                broken_audit,
            )

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["stage_scope"]["stage17_review_scope_included"] = True
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                broken_manifest,
                role_matrix,
                sensitive_policies,
                audit_policies,
            )

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["quality_gate"]["raw_sensitive_public_repo_allowed"] = False
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                broken_manifest,
                role_matrix,
                sensitive_policies,
                audit_policies,
            )

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["quality_gate"]["notification_delivery_allowed"] = True
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                broken_manifest,
                role_matrix,
                sensitive_policies,
                audit_policies,
            )

        broken_roles = copy.deepcopy(role_matrix)
        broken_roles[0]["allowed_public_safe_actions"].append("raw_value_export")
        with self.assertRaises(AccessSecurityPolicyError):
            validate_access_security_policy_artifacts(
                manifest,
                broken_roles,
                sensitive_policies,
                audit_policies,
            )


if __name__ == "__main__":
    unittest.main()
