import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.check_v014_owner_raw_source_identity_decision import (
    validate_owner_decision_record,
    validate_v014_owner_raw_source_identity_decision,
)
from KMFA.tools.v014_owner_raw_source_identity_decision import (
    ACCEPTANCE_ID,
    PHASE_ID,
    STATUS,
    TASK_ID,
    generate,
)


class V014OwnerRawSourceIdentityDecisionTests(unittest.TestCase):
    def test_generate_owner_decision_intake_without_claiming_authorization(self) -> None:
        manifest = generate(generated_at="2026-07-05T22:30:00+10:00")
        validated = validate_v014_owner_raw_source_identity_decision()

        self.assertEqual(validated["schema_version"], "kmfa.v014_owner_raw_source_identity_decision.v1")
        self.assertEqual(validated["phase_id"], PHASE_ID)
        self.assertEqual(validated["task_id"], TASK_ID)
        self.assertEqual(validated["acceptance_ids"], [ACCEPTANCE_ID])
        self.assertEqual(validated["status"], STATUS)
        self.assertEqual(validated, manifest)

        intake = validated["owner_decision_intake"]
        self.assertEqual(intake["readiness_status"], "ready_for_owner_decision_record")
        self.assertEqual(intake["decision_record_status"], "no_owner_decision_recorded")
        self.assertEqual(
            set(intake["allowed_decision_codes"]),
            {
                "confirm_current_container_as_authoritative",
                "register_corrected_source_package",
                "keep_pending",
            },
        )
        self.assertFalse(intake["owner_decision_supplied_by_this_phase"])
        self.assertFalse(intake["raw_alignment_complete_claimed_by_this_phase"])
        self.assertFalse(intake["public_hash_backfill_allowed_by_this_phase"])

        go_no_go = validated["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("RAW_SOURCE_IDENTITY_OWNER_DECISION_NOT_SUPPLIED", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])

        safety = validated["public_repo_safety"]
        for key, value in safety.items():
            if key == "public_safe_decision_codes_only":
                self.assertTrue(value)
            else:
                self.assertFalse(value, key)

    def test_accepts_public_safe_keep_pending_decision_record(self) -> None:
        decision = {
            "record_type": "v014_raw_source_identity_owner_decision",
            "schema_version": "kmfa.v014_raw_source_identity_owner_decision.v1",
            "project_id": "KMFA",
            "phase_id": "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION",
            "current_gate": "KMFA-V014-RAW-SOURCE-IDENTITY-OWNER-GATE",
            "decision_code": "keep_pending",
            "actor_role": "owner",
            "actor_ref": "owner_role_ref",
            "decision_time": "2026-07-05T22:45:00+10:00",
            "basis_refs": [
                "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_remediation_manifest.json",
                "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_go_no_go_report.json",
            ],
            "source_identity_scope": "raw_container_identity_only",
            "reason_pending": "Owner will confirm whether the local raw container or a corrected source package is authoritative.",
            "next_review_trigger": "owner_supplies_decision_code_or_corrected_package",
            "raw_business_data_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "private_diagnostic_committed": False,
            "public_hash_backfill_performed": False,
            "raw_alignment_complete_claimed_by_intake": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        }

        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision_path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
            code = validate_owner_decision_record(decision_path)

        self.assertEqual(code, "keep_pending")

    def test_rejects_raw_hash_or_plaintext_keys_in_owner_decision(self) -> None:
        decision = {
            "record_type": "v014_raw_source_identity_owner_decision",
            "schema_version": "kmfa.v014_raw_source_identity_owner_decision.v1",
            "project_id": "KMFA",
            "phase_id": "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION",
            "current_gate": "KMFA-V014-RAW-SOURCE-IDENTITY-OWNER-GATE",
            "decision_code": "keep_pending",
            "actor_role": "authorized_delegate",
            "actor_ref": "delegate_ref",
            "decision_time": "2026-07-05T22:45:00+10:00",
            "basis_refs": [
                "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_remediation_manifest.json"
            ],
            "source_identity_scope": "raw_container_identity_only",
            "reason_pending": "pending",
            "next_review_trigger": "owner_decision",
            "raw_business_data_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "private_diagnostic_committed": False,
            "public_hash_backfill_performed": False,
            "raw_alignment_complete_claimed_by_intake": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "actual_package_sha256": "0" * 64,
        }

        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision_path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                validate_owner_decision_record(decision_path)


if __name__ == "__main__":
    unittest.main()
