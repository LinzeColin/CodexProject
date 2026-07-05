import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.check_v014_raw_source_identity_decision_application import (
    validate_v014_raw_source_identity_decision_application,
)
from KMFA.tools.v014_raw_source_identity_decision_application import (
    ACCEPTANCE_ID,
    PHASE_ID,
    STATUS,
    TASK_ID,
    generate,
)


class V014RawSourceIdentityDecisionApplicationTests(unittest.TestCase):
    def test_generate_blocks_without_active_owner_decision(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:05:00+10:00")
        validated = validate_v014_raw_source_identity_decision_application()

        self.assertEqual(validated["schema_version"], "kmfa.v014_raw_source_identity_decision_application.v1")
        self.assertEqual(validated["phase_id"], PHASE_ID)
        self.assertEqual(validated["task_id"], TASK_ID)
        self.assertEqual(validated["acceptance_ids"], [ACCEPTANCE_ID])
        self.assertEqual(validated["status"], STATUS)
        self.assertEqual(validated, manifest)

        application = validated["decision_application"]
        self.assertEqual(application["application_status"], "blocked_no_active_owner_decision")
        self.assertFalse(application["owner_decision_supplied"])
        self.assertFalse(application["decision_applied"])
        self.assertFalse(application["raw_alignment_complete_claimed_by_application"])
        self.assertFalse(application["public_member_hash_backfill_allowed_by_application"])

        go_no_go = validated["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("RAW_SOURCE_IDENTITY_OWNER_DECISION_NOT_SUPPLIED", go_no_go["blocker_ids"])
        self.assertIn("RAW_SOURCE_IDENTITY_DECISION_APPLICATION_BLOCKED", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])

        safety = validated["public_repo_safety"]
        for key, value in safety.items():
            if key == "public_safe_application_status_only":
                self.assertTrue(value)
            else:
                self.assertFalse(value, key)

    def test_preview_keep_pending_decision_stays_blocked_without_unlocks(self) -> None:
        decision = {
            "record_type": "v014_raw_source_identity_owner_decision",
            "schema_version": "kmfa.v014_raw_source_identity_owner_decision.v1",
            "project_id": "KMFA",
            "phase_id": "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION",
            "current_gate": "KMFA-V014-RAW-SOURCE-IDENTITY-OWNER-GATE",
            "decision_code": "keep_pending",
            "actor_role": "owner",
            "actor_ref": "owner_role_ref",
            "decision_time": "2026-07-05T23:00:00+10:00",
            "basis_refs": [
                "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_remediation_manifest.json",
                "KMFA/stage_artifacts/V014_RAW_ALIGNMENT_REMEDIATION/machine/raw_alignment_go_no_go_report.json",
            ],
            "source_identity_scope": "raw_container_identity_only",
            "reason_pending": "Owner keeps the source identity unresolved.",
            "next_review_trigger": "owner_supplies_corrected_source_or_confirmation",
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
            manifest = generate(
                generated_at="2026-07-05T23:06:00+10:00",
                decision_path=decision_path,
                write=False,
            )

        self.assertEqual(manifest["decision_application"]["decision_code"], "keep_pending")
        self.assertEqual(manifest["decision_application"]["application_status"], "blocked_by_owner_keep_pending")
        self.assertTrue(manifest["decision_application"]["owner_decision_supplied"])
        self.assertFalse(manifest["decision_application"]["decision_applied"])
        self.assertEqual(manifest["go_no_go"]["decision"], "NO_GO")
        self.assertFalse(manifest["go_no_go"]["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
