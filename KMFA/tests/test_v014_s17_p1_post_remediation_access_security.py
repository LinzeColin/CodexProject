from __future__ import annotations

import json
import unittest
from pathlib import Path


MODULE_PATH = Path("KMFA/tools/v014_s17_p1_post_remediation_access_security.py")
CHECKER_PATH = Path("KMFA/tools/check_v014_s17_p1_post_remediation_access_security.py")


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class V014S17P1PostRemediationAccessSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MODULE_PATH.is_file() or not CHECKER_PATH.is_file():
            return
        from KMFA.tools import v014_s17_p1_post_remediation_access_security as phase
        from KMFA.tools.check_v014_s17_p1_post_remediation_access_security import (
            validate_v014_s17_p1_post_remediation_access_security,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s17_p1_post_remediation_access_security(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]

    def _require_implementation(self) -> None:
        if not hasattr(self, "manifest"):
            self.skipTest("S17-P1 post-remediation implementation is not present yet")

    def test_implementation_exists(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "S17-P1 generator is missing")
        self.assertTrue(CHECKER_PATH.is_file(), "S17-P1 validator is missing")

    def test_identity_dependency_and_legacy_quarantine(self) -> None:
        self._require_implementation()
        self.assertEqual(self.manifest["phase_id"], self.phase.PHASE_ID)
        self.assertEqual(self.manifest["task_id"], self.phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.phase.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["version"], self.phase.VERSION)
        self.assertTrue(self.manifest["current_s16_review_validated"])
        self.assertTrue(self.manifest["historical_s17_p1_validated"])
        self.assertFalse(self.manifest["historical_s17_p1_dynamic_state_is_authoritative"])
        self.assertTrue(self.manifest["historical_four_roles_quarantined"])
        self.assertTrue(self.manifest["historical_fifteen_sensitive_categories_quarantined"])
        self.assertTrue(self.manifest["historical_five_audit_actions_quarantined"])

    def test_four_role_least_privilege_policy_is_complete(self) -> None:
        self._require_implementation()
        roles = _read_jsonl(self.phase.ROLE_POLICY_PATH)
        self.assertEqual({row["role_id"] for row in roles}, {"management", "finance", "reviewer", "readonly"})
        self.assertEqual(self.summary["role_count"], 4)
        self.assertEqual(self.summary["allowed_action_assignment_count"], 14)
        self.assertTrue(all(row["least_privilege_applied"] for row in roles))
        self.assertTrue(all(row["audit_required"] for row in roles))
        self.assertEqual(next(row for row in roles if row["role_id"] == "readonly")["max_write_scope"], "none")

    def test_authorization_probe_is_deny_by_default(self) -> None:
        self._require_implementation()
        probes = _read_jsonl(self.phase.AUTHORIZATION_PROBE_PATH)
        self.assertEqual(len(probes), 16)
        self.assertEqual(sum(row["actual_decision"] == "ALLOW" for row in probes), 8)
        self.assertEqual(sum(row["actual_decision"] == "DENY" for row in probes), 8)
        self.assertTrue(all(row["actual_decision"] == row["expected_decision"] for row in probes))
        self.assertEqual(self.summary["authorization_probe_mismatch_count"], 0)
        self.assertTrue(self.manifest["deny_by_default_enforced"])

    def test_sensitive_public_repository_policy_is_fail_closed(self) -> None:
        self._require_implementation()
        policies = _read_jsonl(self.phase.SENSITIVE_POLICY_PATH)
        self.assertEqual(len(policies), 15)
        self.assertTrue(all(row["public_repo_allowed"] is False for row in policies))
        self.assertTrue(all(row["git_upload_allowed"] is False for row in policies))
        self.assertTrue(all(row["value_plaintext_allowed"] is False for row in policies))
        self.assertEqual(self.summary["tracked_forbidden_suffix_count"], 0)
        self.assertEqual(self.summary["tracked_private_runtime_path_count"], 0)

    def test_five_audit_contracts_and_probes_are_complete(self) -> None:
        self._require_implementation()
        contracts = _read_jsonl(self.phase.AUDIT_CONTRACT_PATH)
        probes = _read_jsonl(self.phase.AUDIT_PROBE_PATH)
        self.assertEqual({row["action_type"] for row in contracts}, {"import", "processing", "report", "export", "notification"})
        self.assertEqual(len(probes), 5)
        self.assertTrue(all(row["status"] == "PASS" for row in probes))
        self.assertTrue(all(row["persistent_audit_event_written"] is False for row in probes))
        self.assertEqual(self.summary["audit_contract_probe_mismatch_count"], 0)
        self.assertEqual(self.summary["actual_business_audit_event_count"], 0)
        self.assertEqual(self.summary["notification_delivery_count"], 0)
        notification = next(row for row in contracts if row["action_type"] == "notification")
        self.assertEqual(notification["delivery_scope"], "audit_log_contract_only_no_delivery")

    def test_raw_snapshots_remain_exact(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertFalse(self.manifest["raw_boundary"]["raw_mutation_performed"])
        self.assertFalse(self.manifest["raw_boundary"]["raw_content_materialization_performed"])

    def test_quality_and_all_downstream_actions_remain_closed(self) -> None:
        self._require_implementation()
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertTrue(self.summary["s17_p1_performed"])
        for key in (
            "s17_p2_performed",
            "s17_p3_performed",
            "stage17_review_performed",
            "live_identity_provider_configured",
            "credential_or_user_record_created",
            "persistent_audit_event_write_performed",
            "notification_delivery_performed",
            "external_connector_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "difference_closure_performed",
            "persistent_business_write_performed",
            "business_execution_performed",
        ):
            self.assertFalse(self.summary[key])

    def test_governance_and_next_run_boundary_are_locked(self) -> None:
        self._require_implementation()
        self.assertEqual(self.manifest["formula_id"], self.phase.FORMULA_ID)
        self.assertEqual(self.manifest["parameter_ids"], list(self.phase.PARAMETER_IDS))
        self.assertEqual(self.manifest["model_registry_key"], self.phase.MODEL_REGISTRY_KEY)
        self.assertEqual(self.manifest["acceptance_matrix"]["check_fail_count"], 0)
        self.assertEqual(self.manifest["next_phase"], "S17-P2")
        self.assertFalse(self.manifest["go_no_go"]["s17_p2_allowed_in_this_run"])
        self.assertFalse(self.manifest["go_no_go"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
