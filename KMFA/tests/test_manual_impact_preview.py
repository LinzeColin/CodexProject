import json
import unittest

from KMFA.tools.manual_resolution_events import build_default_manual_resolution_event_artifacts
from KMFA.tools.manual_impact_preview import (
    REQUIRED_IMPACT_DOMAINS,
    ManualImpactPreviewError,
    build_default_manual_impact_preview_artifacts,
    validate_manual_impact_preview_artifacts,
)


class ManualImpactPreviewTests(unittest.TestCase):
    def test_default_runtime_covers_s12_p2_impact_preview_scope(self) -> None:
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )
        validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, events)

        self.assertEqual(manifest["stage_phase"], "S12-P2")
        self.assertEqual(tuple(manifest["required_impact_domains"]), REQUIRED_IMPACT_DOMAINS)
        self.assertEqual(manifest["summary"]["impact_preview_count"], len(events))
        self.assertGreaterEqual(manifest["summary"]["affected_project_count"], 4)
        self.assertGreaterEqual(manifest["summary"]["affected_metric_count"], 6)
        self.assertGreaterEqual(manifest["summary"]["affected_report_count"], 3)
        self.assertFalse(manifest["quality_gate"]["derived_rerun_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["stage_scope"]["s12_p3_rerun_mechanism_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage12_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_each_preview_links_to_event_and_displays_project_metric_report_impact(self) -> None:
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )
        validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, events)

        source_event_ids = {event["event_id"] for event in events}
        self.assertEqual({preview["source_event_id"] for preview in previews}, source_event_ids)
        for preview in previews:
            self.assertTrue(preview["affected_projects"])
            self.assertTrue(preview["affected_metrics"])
            self.assertTrue(preview["affected_reports"])
            self.assertTrue(preview["impact_reason"])
            self.assertTrue(preview["preview_version"])
            self.assertFalse(preview["raw_layer_write_allowed"])
            self.assertFalse(preview["derived_rerun_executed"])
            self.assertFalse(preview["formal_report_generated"])

    def test_high_risk_previews_require_second_confirmation_before_publish(self) -> None:
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )
        validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, events)

        high_risk = [preview for preview in previews if preview["risk_level"] == "high"]
        self.assertGreaterEqual(len(high_risk), 2)
        for preview in high_risk:
            self.assertTrue(preview["second_confirmation_required"])
            self.assertEqual(preview["second_confirmation_status"], "pending")
            self.assertFalse(preview["control_event_publish_allowed"])
            self.assertEqual(preview["release_gate"], "blocked_pending_second_confirmation")

    def test_failed_or_incomplete_preview_cannot_publish(self) -> None:
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )

        missing_report = [dict(preview) for preview in previews]
        missing_report[0]["affected_reports"] = []
        with self.assertRaises(ManualImpactPreviewError):
            validate_manual_impact_preview_artifacts(manifest, missing_report, render_outputs, events)

        unsafe_publish = [dict(preview) for preview in previews]
        unsafe_publish[0]["preview_passed"] = False
        unsafe_publish[0]["control_event_publish_allowed"] = True
        with self.assertRaises(ManualImpactPreviewError):
            validate_manual_impact_preview_artifacts(manifest, unsafe_publish, render_outputs, events)

        high_risk_publish = [dict(preview) for preview in previews]
        high_index = next(i for i, preview in enumerate(high_risk_publish) if preview["risk_level"] == "high")
        high_risk_publish[high_index]["control_event_publish_allowed"] = True
        with self.assertRaises(ManualImpactPreviewError):
            validate_manual_impact_preview_artifacts(manifest, high_risk_publish, render_outputs, events)

    def test_rendered_html_exposes_impact_preview_without_rerun_or_raw_data(self) -> None:
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )
        validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, events)
        html_text = render_outputs["html"]["kmfa_manual_impact_preview"]

        self.assertTrue(html_text.startswith("<!doctype html>"))
        for required_text in (
            "KMFA 影响预览",
            "受影响项目",
            "受影响指标",
            "受影响报告",
            "高风险二次确认",
            "未通过预览不得发布",
            "重跑未执行",
        ):
            self.assertIn(required_text, html_text)
        for forbidden_text in (
            "private_ref://",
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

    def test_public_payload_has_no_raw_values_private_docs_or_rerun_execution(self) -> None:
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        manifest, previews, render_outputs = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )
        validate_manual_impact_preview_artifacts(manifest, previews, render_outputs, events)
        payload = json.dumps([manifest, previews, render_outputs], ensure_ascii=False, sort_keys=True)

        self.assertNotIn("private_ref://", payload)
        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "identity_document_number",
            "password",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)
        self.assertFalse(any(preview["derived_rerun_executed"] for preview in previews))


if __name__ == "__main__":
    unittest.main()
