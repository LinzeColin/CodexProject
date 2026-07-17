from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s20_p2_confirmation_workbench as subject


class ConfirmationWorkbenchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "events.jsonl"
        self.workbench = subject.ConfirmationWorkbench(self.path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def confirm_first(self):
        preview = self.workbench.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD")
        return self.workbench.confirm(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对项目编号、业务解释和影响", preview_id=preview["preview_id"], preview_token=preview["preview_token"],
            idempotency_key="unit-confirm-project-001",
        )

    def test_default_list_is_business_only_action_required_and_sorted(self) -> None:
        value = self.workbench.list_issues()
        self.assertEqual(value["issue_count"], 5)
        self.assertEqual(value["governance_log_count_in_main_list"], 0)
        self.assertTrue(all(row["requires_user_action"] and row["status"] == "OPEN" for row in value["issues"]))
        self.assertEqual([row["issue_id"] for row in value["issues"][:3]], ["ISSUE-S20P2-001", "ISSUE-S20P2-002", "ISSUE-S20P2-003"])

    def test_detail_is_side_by_side_plain_and_non_editable(self) -> None:
        value = self.workbench.detail("ISSUE-S20P2-001")
        self.assertTrue(value["current_data"])
        self.assertTrue(value["reference_data"])
        self.assertTrue(value["business_explanation_zh"])
        self.assertTrue(value["impact_zh"])
        self.assertEqual(len(value["suggested_actions"]), 2)
        self.assertFalse(value["raw_value_edit_allowed"])
        self.assertFalse(value["technical_details_default_expanded"])

    def test_action_role_is_fail_closed(self) -> None:
        with self.assertRaisesRegex(subject.ConfirmationError, "ACTION_FORBIDDEN"):
            self.workbench.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::MANAGEMENT")

    def test_high_impact_cannot_confirm_without_exact_preview(self) -> None:
        with self.assertRaisesRegex(subject.ConfirmationError, "HIGH_IMPACT_PREVIEW_REQUIRED"):
            self.workbench.confirm(
                "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD",
                reason_zh="不能绕过预览", idempotency_key="unit-missing-preview-001",
            )
        preview = self.workbench.preview("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD")
        with self.assertRaisesRegex(subject.ConfirmationError, "PREVIEW_STALE"):
            self.workbench.confirm(
                "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD",
                reason_zh="错误预览", preview_id=preview["preview_id"], preview_token="sha256:" + "0" * 64,
                idempotency_key="unit-wrong-preview-001",
            )

    def test_confirm_writes_only_auditable_control_event(self) -> None:
        value = self.confirm_first()
        event = value["event"]
        self.assertEqual((event["event_type"], event["before_status"], event["after_status"]), ("ACTION_CONFIRMED", "OPEN", "RESOLVED"))
        self.assertFalse(event["raw_source_mutation_performed"])
        self.assertFalse(event["fact_layer_mutation_performed"])
        self.assertFalse(event["s20_p3_recalculation_performed"])
        self.assertTrue(event["event_hash"].startswith("sha256:"))
        self.assertEqual(value["detail"]["status"], "RESOLVED")
        self.assertNotIn("ISSUE-S20P2-001", {row["issue_id"] for row in self.workbench.list_issues()["issues"]})

    def test_idempotency_is_exact_and_conflicts_fail(self) -> None:
        first = self.confirm_first()
        preview_id = first["event"]["preview_id"]
        preview_token = first["event"]["preview_token"]
        same = self.workbench.confirm(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="demo-owner", actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对项目编号、业务解释和影响", preview_id=preview_id, preview_token=preview_token,
            idempotency_key="unit-confirm-project-001",
        )
        self.assertEqual(same["event"]["event_id"], first["event"]["event_id"])
        with self.assertRaisesRegex(subject.ConfirmationError, "IDEMPOTENCY_CONFLICT"):
            self.workbench.confirm(
                "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_id="another-owner", actor_role="ROLE::DATA_STEWARD",
                reason_zh="不同请求", preview_id=preview_id, preview_token=preview_token,
                idempotency_key="unit-confirm-project-001",
            )

    def test_undo_requires_preview_and_appends_history(self) -> None:
        confirmed = self.confirm_first()
        event_id = confirmed["event"]["event_id"]
        with self.assertRaisesRegex(subject.ConfirmationError, "UNDO_PREVIEW_REQUIRED"):
            self.workbench.undo(
                event_id, actor_id="demo-auditor", actor_role="ROLE::AUDITOR", reason_zh="无预览撤销",
                idempotency_key="unit-undo-missing-preview-001",
            )
        preview = self.workbench.undo_preview(event_id, actor_role="ROLE::AUDITOR")
        undone = self.workbench.undo(
            event_id, actor_id="demo-auditor", actor_role="ROLE::AUDITOR", reason_zh="复核后撤销并恢复待处理",
            preview_id=preview["preview_id"], preview_token=preview["preview_token"], idempotency_key="unit-undo-project-001",
        )
        self.assertEqual(undone["event"]["event_type"], "ACTION_UNDONE")
        self.assertEqual(undone["detail"]["status"], "OPEN")
        history = self.workbench.history()
        self.assertEqual(history["event_count"], 2)
        self.assertTrue(history["append_only"])

    def test_persistence_replay_and_tamper_detection(self) -> None:
        self.confirm_first()
        replayed = subject.ConfirmationWorkbench(self.path)
        self.assertEqual(replayed.history()["event_count"], 1)
        value = json.loads(self.path.read_text(encoding="utf-8").splitlines()[0])
        value["reason_zh"] = "tampered"
        self.path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(subject.ConfirmationError, "EVENT_TAMPERED"):
            replayed.history()

    def test_public_verification_and_scope_boundary_pass(self) -> None:
        verification = subject.public_verification()
        self.assertEqual((verification["check_count"], verification["pass_count"], verification["fail_count"]), (55, 55, 0))
        self.assertTrue(all(value == 0 for value in subject.scope_boundary().values()))


if __name__ == "__main__":
    unittest.main()
