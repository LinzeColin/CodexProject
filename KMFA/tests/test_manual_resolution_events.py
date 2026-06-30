import json
import unittest

from KMFA.tools.manual_resolution_events import (
    REQUIRED_MANUAL_ACTION_KINDS,
    ManualResolutionEventError,
    build_default_manual_resolution_event_artifacts,
    validate_manual_resolution_event_artifacts,
)


class ManualResolutionEventTests(unittest.TestCase):
    def test_default_runtime_covers_s12_p1_manual_event_scope(self) -> None:
        manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        validate_manual_resolution_event_artifacts(manifest, events, render_outputs)

        self.assertEqual(manifest["stage_phase"], "S12-P1")
        self.assertEqual(tuple(manifest["required_manual_action_kinds"]), REQUIRED_MANUAL_ACTION_KINDS)
        self.assertEqual(manifest["summary"]["manual_event_count"], 5)
        self.assertEqual(manifest["summary"]["manual_action_kind_count"], 4)
        self.assertEqual(manifest["summary"]["approved_event_count"], 1)
        self.assertEqual(manifest["summary"]["reverse_event_count"], 1)
        self.assertFalse(manifest["quality_gate"]["raw_layer_write_allowed"])
        self.assertFalse(manifest["quality_gate"]["impact_preview_publish_allowed"])
        self.assertFalse(manifest["quality_gate"]["derived_rerun_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["stage_scope"]["s12_p2_impact_preview_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s12_p3_rerun_mechanism_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage12_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_each_event_has_actor_time_reason_impact_scope_and_version(self) -> None:
        manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        validate_manual_resolution_event_artifacts(manifest, events, render_outputs)

        covered_actions = {event["manual_action_kind"] for event in events}
        self.assertEqual(covered_actions, set(REQUIRED_MANUAL_ACTION_KINDS))
        for event in events:
            for required_field in (
                "event_id",
                "actor_ref",
                "actor_role",
                "event_time",
                "reason_code",
                "reason_summary",
                "impact_scope",
                "event_version",
                "target_layer",
                "target_ref",
            ):
                self.assertTrue(event[required_field], required_field)
            self.assertFalse(event["raw_layer_write_allowed"])
            self.assertFalse(event["raw_source_mutation_allowed"])
            self.assertFalse(event["source_layer_write_allowed"])
            self.assertFalse(event["business_plaintext_committed"])
            self.assertFalse(event["forbidden_plaintext"])
            self.assertTrue(event["append_only"])

    def test_approved_events_require_reverse_event_instead_of_silent_update(self) -> None:
        manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        validate_manual_resolution_event_artifacts(manifest, events, render_outputs)

        approved_events = [event for event in events if event.get("approval_state") == "approved"]
        reverse_events = [event for event in events if event.get("event_action") == "reverse_approved_event"]
        self.assertEqual(len(approved_events), 1)
        self.assertEqual(len(reverse_events), 1)

        approved = approved_events[0]
        reverse = reverse_events[0]
        self.assertTrue(approved["approved_event_immutable"])
        self.assertFalse(approved["silent_update_allowed"])
        self.assertTrue(approved["reversal_required_for_change"])
        self.assertEqual(reverse["reverses_event_id"], approved["event_id"])
        self.assertEqual(reverse["target_ref"], approved["target_ref"])
        self.assertNotEqual(reverse["event_id"], approved["event_id"])

    def test_rendered_html_is_public_safe_workbench_without_preview_or_rerun_execution(self) -> None:
        manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        validate_manual_resolution_event_artifacts(manifest, events, render_outputs)
        html_text = render_outputs["html"]["kmfa_manual_resolution_workbench"]

        self.assertTrue(html_text.startswith("<!doctype html>"))
        for required_text in (
            "KMFA 人工处理工作台",
            "处理事件",
            "字段映射",
            "项目匹配",
            "差异处理",
            "备注",
            "追加反向事件",
            "原始数据 0 写入",
            "影响预览未发布",
            "重跑未执行",
        ):
            self.assertIn(required_text, html_text)
        for forbidden_text in (
            "private_ref://",
            "source_ref://",
            "raw_value",
            "normalized_value",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "password",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, html_text.lower())

    def test_validator_rejects_raw_writes_missing_actor_or_missing_reverse_event(self) -> None:
        manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )

        raw_write_events = [dict(event) for event in events]
        raw_write_events[0]["raw_layer_write_allowed"] = True
        with self.assertRaises(ManualResolutionEventError):
            validate_manual_resolution_event_artifacts(manifest, raw_write_events, render_outputs)

        missing_actor_events = [dict(event) for event in events]
        missing_actor_events[0]["actor_ref"] = ""
        with self.assertRaises(ManualResolutionEventError):
            validate_manual_resolution_event_artifacts(manifest, missing_actor_events, render_outputs)

        no_reverse_events = [event for event in events if event.get("event_action") != "reverse_approved_event"]
        with self.assertRaises(ManualResolutionEventError):
            validate_manual_resolution_event_artifacts(manifest, no_reverse_events, render_outputs)

    def test_public_payload_has_no_raw_values_or_private_documents(self) -> None:
        manifest, events, render_outputs = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        payload = json.dumps([manifest, events, render_outputs], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_ref://",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)


if __name__ == "__main__":
    unittest.main()
