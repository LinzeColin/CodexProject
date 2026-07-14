#!/usr/bin/env python3
"""Behavior tests for current KMFA v0.1.4 S17-P2 notifications."""

from __future__ import annotations

import json
import re
import unittest
from copy import deepcopy
from pathlib import Path


GENERATOR_PATH = Path("KMFA/tools/v014_s17_p2_post_remediation_notification.py")
CHECKER_PATH = Path("KMFA/tools/check_v014_s17_p2_post_remediation_notification.py")
IMPLEMENTATION_EXISTS = GENERATOR_PATH.is_file() and CHECKER_PATH.is_file()


class V014S17P2PostRemediationNotificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s17_p2_post_remediation_notification as phase
        from KMFA.tools.check_v014_s17_p2_post_remediation_notification import (
            validate_v014_s17_p2_post_remediation_notification,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s17_p2_post_remediation_notification(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = json.loads(phase.SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.rules = cls._read_jsonl(phase.RULE_PATH)
        cls.evaluations = cls._read_jsonl(phase.TRIGGER_EVALUATION_PATH)
        cls.outbox = cls._read_jsonl(phase.OUTBOX_PATH)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_implementation_exists(self) -> None:
        self.assertTrue(GENERATOR_PATH.is_file(), f"missing generator: {GENERATOR_PATH}")
        self.assertTrue(CHECKER_PATH.is_file(), f"missing checker: {CHECKER_PATH}")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_identity_dependencies_and_historical_quarantine(self) -> None:
        self.assertEqual(self.manifest["phase_id"], self.phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "S17-P2")
        self.assertEqual(self.manifest["task_id"], self.phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.phase.ACCEPTANCE_ID)
        self.assertTrue(self.manifest["current_s17_p1_validated"])
        self.assertTrue(self.manifest["current_s10_review_validated"])
        self.assertTrue(self.manifest["historical_s17_p2_validated"])
        self.assertFalse(self.manifest["historical_s17_p2_dynamic_state_is_authoritative"])
        self.assertEqual(self.manifest["next_phase"], "S17-P3")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_three_notification_rules_are_complete_and_fail_closed(self) -> None:
        self.assertEqual(len(self.rules), 3)
        self.assertEqual({row["trigger_id"] for row in self.rules}, set(self.phase.REQUIRED_TRIGGER_IDS))
        self.assertEqual({row["recipient_role"] for row in self.rules}, {"management", "reviewer", "finance"})
        for row in self.rules:
            self.assertEqual(row["channel"], "email_reminder")
            self.assertTrue(row["metadata_log_required"])
            self.assertTrue(row["in_app_link_required"])
            self.assertFalse(row["full_report_body_allowed"])
            self.assertFalse(row["report_attachment_allowed"])
            self.assertFalse(row["recipient_address_plaintext_allowed"])
            self.assertFalse(row["external_connector_allowed"])
            self.assertFalse(row["real_delivery_allowed"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_trigger_evaluations_are_evidence_bound(self) -> None:
        self.assertEqual(len(self.evaluations), 3)
        by_trigger = {row["trigger_id"]: row for row in self.evaluations}
        self.assertEqual(set(by_trigger), set(self.phase.REQUIRED_TRIGGER_IDS))
        self.assertEqual(by_trigger["report_generation_completed"]["source_evidence_count"], 2)
        self.assertEqual(by_trigger["major_risk"]["source_evidence_count"], 12)
        self.assertEqual(by_trigger["data_source_missing"]["source_evidence_count"], 4)
        for row in self.evaluations:
            self.assertTrue(row["eligible_for_metadata_outbox"])
            self.assertEqual(row["status"], "PASS")
            self.assertFalse(row["real_delivery_eligible"])
            self.assertFalse(row["business_value_materialized"])
        self.assertEqual(self.summary["trigger_evaluation_mismatch_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_outbox_contains_short_chinese_reminders_and_existing_links(self) -> None:
        self.assertEqual(len(self.outbox), 3)
        chinese = re.compile(r"[\u4e00-\u9fff]")
        for row in self.outbox:
            self.assertTrue(chinese.search(str(row["subject"])))
            self.assertTrue(chinese.search(str(row["body_summary"])))
            self.assertLessEqual(len(str(row["body_summary"])), 120)
            self.assertEqual(row["body_kind"], "short_reminder_and_link_only")
            self.assertTrue(Path(str(row["in_app_link_ref"])).is_file())
            self.assertTrue(chinese.search(str(row["in_app_link_label"])))
            self.assertFalse(row["full_report_body_included"])
            self.assertFalse(row["report_attachment_included"])
            self.assertFalse(row["recipient_address_plaintext_included"])
            self.assertFalse(row["external_connector_invoked"])
            self.assertFalse(row["real_notification_delivery_performed"])
            self.assertTrue(self.phase.validate_outbox_candidate(row)["valid"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_outbox_tampering_is_rejected(self) -> None:
        base = self.outbox[0]
        cases = (
            ("full_report_body_included", True, "full_report_body_forbidden"),
            ("report_attachment_included", True, "report_attachment_forbidden"),
            ("recipient_address_plaintext_included", True, "recipient_plaintext_forbidden"),
            ("external_connector_invoked", True, "external_connector_forbidden"),
            ("real_notification_delivery_performed", True, "real_delivery_forbidden"),
            ("in_app_link_ref", "", "in_app_link_required"),
        )
        for key, value, reason in cases:
            with self.subTest(key=key):
                row = deepcopy(base)
                row[key] = value
                result = self.phase.validate_outbox_candidate(row)
                self.assertFalse(result["valid"])
                self.assertIn(reason, result["errors"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_metadata_logs_match_public_evidence_and_audit_contract(self) -> None:
        self.assertEqual(self.rules, self._read_jsonl(self.phase.METADATA_RULE_PATH))
        self.assertEqual(self.evaluations, self._read_jsonl(self.phase.METADATA_TRIGGER_EVALUATION_PATH))
        self.assertEqual(self.outbox, self._read_jsonl(self.phase.METADATA_OUTBOX_PATH))
        required_audit_fields = {
            "event_id",
            "event_time",
            "actor_role",
            "action_type",
            "subject_ref",
            "evidence_ref",
            "result_status",
        }
        for row in self.outbox:
            self.assertTrue(required_audit_fields.issubset(row))
            self.assertEqual(row["actor_role"], "reviewer")
            self.assertEqual(row["action_type"], "notification")
            self.assertTrue(row["append_only"])
            self.assertEqual(row["result_status"], "metadata_logged_only_not_delivered")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_snapshots_remain_exact(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        boundary = self.manifest["raw_boundary"]
        self.assertTrue(boundary["raw_snapshot_read_performed"])
        for key, value in boundary.items():
            if key != "raw_snapshot_read_performed":
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_quality_and_all_downstream_actions_remain_closed(self) -> None:
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(
            (
                self.summary["open_final_difference_accepted_count"],
                self.summary["nonzero_delta_reconciliation_count"],
                self.summary["zero_delta_reconciliation_count"],
                self.summary["incomplete_reconciliation_count"],
            ),
            (3, 9, 2, 1),
        )
        self.assertTrue(self.summary["s17_p2_performed"])
        for key, value in self.phase._phase_boundaries().items():
            if key in {"s17_p1_performed", "s17_p2_performed", "notification_metadata_log_written"}:
                self.assertTrue(value, key)
            else:
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_governance_and_next_run_boundary_are_locked(self) -> None:
        formula = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        parameters = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn(self.phase.FORMULA_ID, formula)
        for parameter_id in self.phase.PARAMETER_IDS:
            self.assertIn(parameter_id, parameters)
        self.assertIn(self.phase.MODEL_REGISTRY_KEY, version_matrix)
        self.assertIn(self.phase.VERSION, version_matrix)
        if f'current_phase: "{self.phase.PHASE_ID}"' in version_matrix:
            self.assertIn("下一步只能执行 S17-P3", handoff)
            self.assertIn("不得执行 Stage 17 整体复审", handoff)
            self.assertIn("不得执行 GitHub upload", handoff)


if __name__ == "__main__":
    unittest.main()
