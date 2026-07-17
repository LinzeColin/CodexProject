from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s11_p1_quality_rules as quality
from KMFA.tools import v015_s11_p2_check_board_data_model as board
from KMFA.tools import v015_s11_stage_review_contract as review


class V015S11StageReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facts = board.public_backend_facts()
        self.projection = review.reviewed_projection(self.facts)
        self.by_fact = {row["fact_id"]: row for row in self.projection["leaves"]}
        self.context = {
            "search_text": "合同",
            "status_filters": ["不可使用"],
            "owner_filter": "合同负责人",
            "alert_only": True,
            "expanded_node_ids": self.projection["node_ids"][:2],
            "scroll_y": 300,
            "table_scroll_left": 100,
            "focus_node_id": self.by_fact["QBF-005"]["node_id"],
        }

    def test_all_forty_five_cross_part_checks_pass(self) -> None:
        self.assertEqual(review.public_verification()["accounting"], {"total": 45, "passed": 45, "failed": 0})

    def test_quality_policy_is_bound_through_board_and_interface(self) -> None:
        binding = review.validate_quality_contract_binding(self.projection["quality_contract"])
        self.assertEqual(binding["status_labels_zh"], list(quality.STATUS_LABELS_ZH))
        self.assertTrue(binding["hard_gate_precedence"])
        for leaf in self.projection["leaves"]:
            self.assertEqual(leaf["quality_contract_fingerprint"], binding["binding_fingerprint"])

    def test_hard_gate_uses_remediation_not_ordinary_confirmation(self) -> None:
        self.assertEqual(self.by_fact["QBF-002"]["reviewed_action"]["kind"], "CONFIRM_QUALITY")
        self.assertEqual(self.by_fact["QBF-005"]["reviewed_action"]["kind"], "REMEDIATE_QUALITY")
        self.assertFalse(self.by_fact["QBF-005"]["reviewed_action"]["frontend_status_change_allowed"])

    def test_request_binds_fact_revision_state_policy_and_context(self) -> None:
        request = review.create_review_action_request("QBF-005", self.context, facts=self.facts)
        authorization = review.validate_review_action_request(request, current_facts=self.facts)
        self.assertEqual(authorization["authorization_status"], "AUTHORIZED_FOR_BACKEND_RECHECK")
        self.assertEqual(request["fact_revision"], 1)
        for key in ("fact_fingerprint", "state_fingerprint", "leaf_binding_fingerprint", "context_token"):
            self.assertTrue(request[key].startswith("sha256:"))

    def test_stale_action_is_rejected_after_backend_revision_changes(self) -> None:
        request = review.create_review_action_request("QBF-002", self.context, facts=self.facts)
        changed = copy.deepcopy(self.facts)
        target = next(row for row in changed if row["fact_id"] == "QBF-002")
        target["fact_revision"] = 2
        target["updated_at"] = "2026-07-15T12:00:00+10:00"
        with self.assertRaisesRegex(review.StageReviewError, "STALE_ACTION_REQUEST"):
            review.validate_review_action_request(request, current_facts=changed)

    def test_frontend_status_write_and_wrong_action_are_rejected(self) -> None:
        request = review.create_review_action_request("QBF-005", self.context, facts=self.facts)
        write = copy.deepcopy(request)
        write["frontend_status_write_count"] = 1
        write["status_change_requested"] = True
        write["request_fingerprint"] = review._fingerprint(review._request_without_fingerprint(write))
        with self.assertRaisesRegex(review.StageReviewError, "FRONTEND_STATUS_WRITE_FORBIDDEN"):
            review.validate_review_action_request(write, current_facts=self.facts)

        wrong = copy.deepcopy(request)
        wrong["action_kind"] = "CONFIRM_QUALITY"
        wrong["request_fingerprint"] = review._fingerprint(review._request_without_fingerprint(wrong))
        with self.assertRaisesRegex(review.StageReviewError, "ACTION_POLICY_DRIFT"):
            review.validate_review_action_request(wrong, current_facts=self.facts)

    def test_status_changes_only_after_newer_backend_recheck(self) -> None:
        before = copy.deepcopy(next(row for row in self.facts if row["fact_id"] == "QBF-003"))
        request = review.create_review_action_request("QBF-003", self.context, facts=self.facts)
        after = copy.deepcopy(before)
        after.update({
            "fact_revision": 2,
            "updated_at": "2026-07-15T12:30:00+10:00",
            "ingestion_state": "IMPORTED",
            "quality_snapshot": quality.baseline_snapshot(),
        })
        result = review.recheck_after_backend_update(request, before, after, other_facts=self.facts)
        self.assertEqual((result["transition"]["before_status_zh"], result["transition"]["after_status_zh"]), ("不可使用", "已通过"))
        self.assertTrue(result["status_changed_by_backend_recheck"])
        self.assertEqual(result["frontend_status_write_count"], 0)


if __name__ == "__main__":
    unittest.main()
