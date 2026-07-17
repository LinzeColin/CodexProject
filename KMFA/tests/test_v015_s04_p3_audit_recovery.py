from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools.v015_s04_p3_audit_recovery import (
    ACTION_TYPES,
    HEALTH_FINDING_TYPES,
    RESTORE_VALIDATION_DIMENSIONS,
    AppendOnlyEventLog,
    AuditRecoveryError,
    inspect_metadata_health,
    restore_snapshot,
    run_synthetic_recovery_drill,
    synthetic_event_log,
    synthetic_health_verification,
    synthetic_snapshot_registry,
    validate_event_chain,
    validate_snapshot_registry,
)


class V015S04P3AuditRecoveryTests(unittest.TestCase):
    def test_event_log_covers_six_actions_and_append_only_correction(self) -> None:
        events = synthetic_event_log()
        summary = validate_event_chain(events)
        self.assertEqual(summary["action_type_count"], len(ACTION_TYPES))
        self.assertEqual(summary["correction_event_count"], 1)
        self.assertEqual(summary["closure_required_event_count"], 1)
        self.assertEqual(summary["closed_event_count"], 1)
        self.assertEqual(summary["unclosed_event_ids"], [])
        self.assertFalse(summary["in_place_update_allowed"])

    def test_event_log_defensive_copy_and_replace_are_immutable(self) -> None:
        log = AppendOnlyEventLog()
        event = log.append(
            action_type="IMPORT",
            occurred_at="2026-07-14T10:00:00+10:00",
            actor_role="ROLE::SYNTHETIC",
            subject_ref="SUBJECT::SYNTHETIC",
            payload_ref="PAYLOAD::SYNTHETIC",
            reason_code="SYNTHETIC",
        )
        event["reason_code"] = "MUTATED-COPY"
        self.assertEqual(log.events()[0]["reason_code"], "SYNTHETIC")
        with self.assertRaises(AuditRecoveryError):
            log.replace_event(event["event_id"], event)

    def test_correction_requires_prior_event_and_reason(self) -> None:
        log = AppendOnlyEventLog()
        with self.assertRaises(AuditRecoveryError):
            log.append(
                action_type="MAPPING", occurred_at="2026-07-14T10:00:00+10:00",
                actor_role="ROLE::SYNTHETIC", subject_ref="SUBJECT::SYNTHETIC",
                payload_ref="PAYLOAD::SYNTHETIC", reason_code="CORRECTION",
                correction_of_event_id="EVENT::MISSING", correction_reason="fix",
            )
        original = log.append(
            action_type="MAPPING", occurred_at="2026-07-14T10:01:00+10:00",
            actor_role="ROLE::SYNTHETIC", subject_ref="SUBJECT::SYNTHETIC",
            payload_ref="PAYLOAD::SYNTHETIC", reason_code="ORIGINAL",
        )
        with self.assertRaises(AuditRecoveryError):
            log.append(
                action_type="MAPPING", occurred_at="2026-07-14T10:02:00+10:00",
                actor_role="ROLE::SYNTHETIC", subject_ref="SUBJECT::SYNTHETIC",
                payload_ref="PAYLOAD::SYNTHETIC", reason_code="CORRECTION",
                correction_of_event_id=original["event_id"],
            )

    def test_event_chain_tamper_and_gap_fail_closed(self) -> None:
        events = synthetic_event_log()
        tampered = copy.deepcopy(events)
        tampered[2]["payload_ref"] = "PAYLOAD::TAMPERED"
        with self.assertRaises(AuditRecoveryError):
            validate_event_chain(tampered)
        gap = copy.deepcopy(events)
        del gap[2]
        with self.assertRaises(AuditRecoveryError):
            validate_event_chain(gap)

    def test_all_approved_snapshot_versions_restore(self) -> None:
        result = run_synthetic_recovery_drill()
        self.assertEqual(result["approved_snapshot_count"], 3)
        self.assertEqual(result["approved_snapshot_recovery_case_count"], 3)
        self.assertEqual(result["recovery_pass_count"], 3)
        self.assertTrue(result["arbitrary_approved_version_recovery_passed"])
        self.assertEqual(result["restore_validation_dimension_count"], len(RESTORE_VALIDATION_DIMENSIONS))
        self.assertFalse(result["production_restore_performed"])

    def test_draft_snapshot_is_not_restorable(self) -> None:
        registry = synthetic_snapshot_registry()
        snapshot = next(row for row in registry["snapshots"] if row["approval_status"] == "DRAFT")
        with self.assertRaises(AuditRecoveryError):
            restore_snapshot(
                snapshot,
                payload=registry["payloads"][snapshot["snapshot_id"]],
                expected_version_ref=snapshot["version_ref"],
                available_version_refs=snapshot["dependency_version_refs"],
            )

    def test_restore_digest_or_dependency_mismatch_fails(self) -> None:
        registry = synthetic_snapshot_registry()
        snapshot = registry["snapshots"][0]
        with self.assertRaises(AuditRecoveryError):
            restore_snapshot(
                snapshot,
                payload={"fact_ref": "FACT::TAMPERED"},
                expected_version_ref=snapshot["version_ref"],
                available_version_refs=snapshot["dependency_version_refs"],
            )
        with self.assertRaises(AuditRecoveryError):
            restore_snapshot(
                snapshot,
                payload=registry["payloads"][snapshot["snapshot_id"]],
                expected_version_ref=snapshot["version_ref"],
                available_version_refs=[],
            )
        with self.assertRaises(AuditRecoveryError):
            restore_snapshot(
                snapshot,
                payload=registry["payloads"][snapshot["snapshot_id"]],
                expected_version_ref="FACT-VERSION::WRONG",
                available_version_refs=snapshot["dependency_version_refs"],
            )

    def test_duplicate_subject_version_is_rejected(self) -> None:
        snapshots = synthetic_snapshot_registry()["snapshots"]
        duplicate = copy.deepcopy(snapshots[0])
        duplicate["snapshot_id"] = "SNAP-DUPLICATE"
        with self.assertRaises(AuditRecoveryError):
            validate_snapshot_registry([*snapshots, duplicate])

    def test_healthy_metadata_has_no_findings(self) -> None:
        verification = synthetic_health_verification()
        healthy = verification["healthy_case"]
        self.assertEqual(healthy["inspection_status"], "PASS")
        self.assertEqual(healthy["finding_count"], 0)
        self.assertTrue(healthy["metadata_publication_gate_passed"])
        self.assertFalse(healthy["automatic_publication_allowed"])

    def test_faulty_metadata_lists_four_classes_and_repair_paths(self) -> None:
        verification = synthetic_health_verification()
        faulty = verification["faulty_case"]
        self.assertEqual(set(faulty["finding_types"]), set(HEALTH_FINDING_TYPES))
        self.assertEqual(faulty["finding_type_count"], 4)
        self.assertTrue(faulty["all_findings_have_repair_path"])
        self.assertGreaterEqual(faulty["critical_finding_count"], 1)
        self.assertFalse(faulty["metadata_publication_gate_passed"])
        self.assertFalse(faulty["automatic_publication_allowed"])
        self.assertTrue(verification["critical_break_blocks_publication"])

    def test_public_fixtures_are_deterministic_and_path_free(self) -> None:
        payload_a = {
            "events": synthetic_event_log(),
            "snapshots": synthetic_snapshot_registry(),
            "health": synthetic_health_verification(),
        }
        payload_b = {
            "events": synthetic_event_log(),
            "snapshots": synthetic_snapshot_registry(),
            "health": synthetic_health_verification(),
        }
        self.assertEqual(payload_a, payload_b)
        encoded = json.dumps(payload_a, ensure_ascii=False, sort_keys=True)
        for token in ("/Users/", "KMFA_MetaData", ".xlsx", ".xls", "sha256:"):
            self.assertNotIn(token, encoded)


if __name__ == "__main__":
    unittest.main()
