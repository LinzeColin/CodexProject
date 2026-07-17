from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import v015_s09_p3_human_readable_audit as engine


class HumanReadableAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = engine.synthetic_acceptance_cases()

    def _event(self, sequence: int, event_type: str, *, feedback: str = "已有反馈。", **payload: object) -> dict[str, object]:
        return {
            "schema_version": engine.CLOSURE_EVENT_SCHEMA,
            "event_ref": f"EVENT-{sequence}",
            "difference_ref": "DIFF-1",
            "sequence": sequence,
            "event_type": event_type,
            "actor_role": "FINANCE_REVIEWER" if event_type == "HUMAN_CONFIRMED" else "SYSTEM",
            "occurred_at": f"2026-07-15T1{sequence}:00:00+10:00",
            "feedback_zh": feedback,
            **payload,
        }

    def _snapshot(self) -> dict[str, object]:
        return engine.new_closure_snapshot(
            difference_ref="DIFF-1",
            business_label_zh="模拟经营差异",
            initial_report_version="经营摘要-v1",
        )

    def test_manual_covers_two_transformations_and_eight_differences(self) -> None:
        review = self.cases["manual_review"]
        self.assertEqual(review["transformation_rule_count"], 2)
        self.assertEqual(review["difference_rule_count"], 8)
        self.assertEqual(review["total_rule_count"], 10)
        self.assertEqual(review["unexplained_rule_count"], 0)

    def test_manual_serves_finance_and_owner_without_fake_signoff(self) -> None:
        review = self.cases["manual_review"]
        self.assertEqual(review["audience_count"], 2)
        self.assertEqual(review["finance_review_status"], "PASS")
        self.assertEqual(review["owner_summary_status"], "PASS")
        self.assertFalse(review["external_human_signoff_claimed"])

    def test_manual_rejects_missing_rule(self) -> None:
        manual = engine.build_human_rule_manual()
        manual["rules"].pop()
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "RULE_COVERAGE_INVALID"):
            engine.validate_human_rule_manual(manual)

    def test_manual_rejects_fake_external_signoff(self) -> None:
        manual = engine.build_human_rule_manual()
        manual["external_human_signoff_claimed"] = True
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "UNSUPPORTED_SIGNOFF_CLAIM"):
            engine.validate_human_rule_manual(manual)

    def test_report_keeps_only_decision_relevant_difference(self) -> None:
        report = self.cases["report_summary"]
        self.assertEqual(report["input_difference_count"], 2)
        self.assertEqual(report["included_difference_count"], 1)
        self.assertEqual(report["excluded_non_decision_difference_count"], 1)

    def test_report_item_has_exact_human_field_whitelist(self) -> None:
        item = self.cases["report_summary"]["items"][0]
        self.assertEqual(tuple(item), engine.REPORT_ITEM_FIELDS)
        self.assertNotIn("difference_ref", item)
        self.assertNotIn("difference_type_code", item)
        self.assertNotIn("debug_payload", item)

    def test_report_contains_no_internal_term_or_debug_field(self) -> None:
        report = self.cases["report_summary"]
        self.assertEqual(report["technical_term_occurrence_count"], 0)
        self.assertEqual(report["debug_field_count"], 0)
        self.assertEqual(report["internal_reference_field_count"], 0)

    def test_report_rejects_internal_mechanism_in_visible_text(self) -> None:
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "INTERNAL_TERM_IN_BUSINESS_REPORT"):
            engine.build_management_difference_summary(
                [
                    {
                        "difference_ref": "DIFF-1",
                        "difference_type_code": "UNBILLED",
                        "affects_business_decision": True,
                        "plain_reason_zh": "请查看 debug_payload。",
                        "business_impact_zh": "影响经营判断。",
                        "current_status_zh": "待确认。",
                        "owner_action_zh": "请确认。",
                    }
                ]
            )

    def test_report_rejects_unregistered_difference_type(self) -> None:
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "UNKNOWN_DIFFERENCE_TYPE"):
            engine.build_management_difference_summary(
                [
                    {
                        "difference_ref": "DIFF-1",
                        "difference_type_code": "UNKNOWN",
                        "affects_business_decision": True,
                        "plain_reason_zh": "模拟。",
                        "business_impact_zh": "模拟。",
                        "current_status_zh": "模拟。",
                        "owner_action_zh": "模拟。",
                    }
                ]
            )

    def test_closure_has_all_six_steps_with_feedback(self) -> None:
        closure = self.cases["closure_snapshot"]
        self.assertEqual([row["event_type"] for row in closure["events"]], list(engine.CLOSURE_STEPS))
        self.assertEqual(sum(bool(row["feedback_zh"]) for row in closure["events"]), 6)
        self.assertTrue(closure["closure_complete"])

    def test_missing_feedback_is_rejected(self) -> None:
        event = self._event(
            1,
            "DIFFERENCE_DISCOVERED",
            feedback="",
            difference_summary_zh="模拟差异。",
        )
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "TEXT_REQUIRED"):
            engine.append_closure_event(self._snapshot(), event)

    def test_out_of_order_step_is_rejected(self) -> None:
        event = self._event(1, "HANDLING_PROPOSED", handling_zh="模拟处理。")
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "CLOSURE_STEP_OUT_OF_ORDER"):
            engine.append_closure_event(self._snapshot(), event)

    def test_confirmation_requires_human_role(self) -> None:
        closure = self._snapshot()
        closure = engine.append_closure_event(
            closure,
            self._event(1, "DIFFERENCE_DISCOVERED", difference_summary_zh="模拟差异。"),
        )
        closure = engine.append_closure_event(
            closure,
            self._event(2, "HANDLING_PROPOSED", handling_zh="模拟处理。"),
        )
        closure = engine.append_closure_event(
            closure,
            self._event(3, "IMPACT_PREVIEWED", impact_before_zh="处理前。", impact_after_zh="处理后。"),
        )
        event = self._event(4, "HUMAN_CONFIRMED", decision_zh="确认。")
        event["actor_role"] = "SYSTEM"
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "HUMAN_CONFIRMATION_REQUIRED"):
            engine.append_closure_event(closure, event)

    def test_failed_recalculation_cannot_advance(self) -> None:
        closure = copy.deepcopy(self.cases["closure_snapshot"])
        closure["events"] = closure["events"][:4]
        closure["current_step_count"] = 4
        closure["current_status_zh"] = engine.CLOSURE_STATUS_ZH["HUMAN_CONFIRMED"]
        closure["closure_complete"] = False
        closure["history_hash"] = "ignored-by-append"
        event = self._event(
            5,
            "RECALCULATED",
            recalculation_status="FAIL",
            affected_output_labels_zh=["经营摘要"],
        )
        event["difference_ref"] = closure["difference_ref"]
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "RECALCULATION_NOT_PASSED"):
            engine.append_closure_event(closure, event)

    def test_report_update_must_advance_version(self) -> None:
        closure = copy.deepcopy(self.cases["closure_snapshot"])
        closure["events"] = closure["events"][:5]
        closure["current_step_count"] = 5
        closure["current_status_zh"] = engine.CLOSURE_STATUS_ZH["RECALCULATED"]
        closure["current_report_version"] = closure["initial_report_version"]
        closure["closure_complete"] = False
        event = self._event(
            6,
            "REPORT_UPDATED",
            report_version=closure["initial_report_version"],
            report_update_summary_zh="模拟更新。",
        )
        event["difference_ref"] = closure["difference_ref"]
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "REPORT_VERSION_NOT_ADVANCED"):
            engine.append_closure_event(closure, event)

    def test_completed_closure_is_append_only(self) -> None:
        event = self._event(
            7,
            "REPORT_UPDATED",
            report_version="经营摘要-v3",
            report_update_summary_zh="再次更新。",
        )
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "CLOSURE_ALREADY_COMPLETE"):
            engine.append_closure_event(self.cases["closure_snapshot"], event)

    def test_refresh_preserves_state_and_history(self) -> None:
        closure = self.cases["closure_snapshot"]
        restored = engine.restore_closure_snapshot(json.dumps(closure, ensure_ascii=False, sort_keys=True))
        self.assertEqual(restored, closure)
        self.assertEqual(len(engine.query_closure_history(restored)), 6)

    def test_refresh_detects_tampered_status(self) -> None:
        closure = copy.deepcopy(self.cases["closure_snapshot"])
        closure["current_status_zh"] = "伪造状态"
        with self.assertRaisesRegex(engine.HumanReadableAuditError, "CLOSURE_REFRESH_DRIFT"):
            engine.restore_closure_snapshot(json.dumps(closure, ensure_ascii=False, sort_keys=True))

    def test_source_fact_raw_and_release_boundaries_remain_closed(self) -> None:
        closure = self.cases["closure_snapshot"]
        self.assertFalse(closure["source_or_fact_mutation_performed"])
        self.assertEqual(self.cases["raw_root_access_count"], 0)
        self.assertFalse(self.cases["formal_report_generated"])
        self.assertFalse(self.cases["github_upload_performed"])
        self.assertFalse(self.cases["app_reinstall_performed"])

    def test_acceptance_cases_are_deterministic(self) -> None:
        replay = engine.synthetic_acceptance_cases()
        self.assertEqual(replay, self.cases)


if __name__ == "__main__":
    unittest.main()
