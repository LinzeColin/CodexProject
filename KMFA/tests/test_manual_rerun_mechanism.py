import json
import unittest

from KMFA.tools.manual_impact_preview import build_default_manual_impact_preview_artifacts
from KMFA.tools.manual_resolution_events import build_default_manual_resolution_event_artifacts
from KMFA.tools.manual_rerun_mechanism import (
    REQUIRED_RERUN_CHAIN,
    ManualRerunMechanismError,
    build_default_manual_rerun_mechanism_artifacts,
    validate_manual_rerun_mechanism_artifacts,
)


class ManualRerunMechanismTests(unittest.TestCase):
    def _build_upstream(self):
        event_manifest, events, _ = build_default_manual_resolution_event_artifacts(
            generated_at="2026-07-01T12:00:00+10:00"
        )
        preview_manifest, previews, _ = build_default_manual_impact_preview_artifacts(
            source_event_manifest=event_manifest,
            source_events=events,
            generated_at="2026-07-01T13:00:00+10:00",
        )
        return event_manifest, events, preview_manifest, previews

    def test_default_runtime_covers_s12_p3_rerun_scope(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )
        validate_manual_rerun_mechanism_artifacts(
            manifest, invalidations, rerun_steps, consistency_checks, render_outputs, events, previews
        )

        eligible = [preview for preview in previews if preview["control_event_publish_allowed"]]
        self.assertEqual(manifest["stage_phase"], "S12-P3")
        self.assertEqual(tuple(manifest["required_rerun_chain"]), REQUIRED_RERUN_CHAIN)
        self.assertEqual(manifest["summary"]["source_preview_count"], len(previews))
        self.assertEqual(manifest["summary"]["eligible_event_count"], len(eligible))
        self.assertEqual(manifest["summary"]["blocked_preview_count"], len(previews) - len(eligible))
        self.assertEqual(manifest["summary"]["cache_invalidation_count"], len(eligible))
        self.assertEqual(manifest["summary"]["rerun_step_count"], len(eligible) * len(REQUIRED_RERUN_CHAIN))
        self.assertEqual(manifest["summary"]["same_source_consistency_check_count"], len(eligible))
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["report_grade_upgrade_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage12_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_only_preview_passed_events_invalidate_cache_and_rerun(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )
        validate_manual_rerun_mechanism_artifacts(
            manifest, invalidations, rerun_steps, consistency_checks, render_outputs, events, previews
        )

        eligible_event_ids = {
            preview["source_event_id"] for preview in previews if preview["control_event_publish_allowed"]
        }
        blocked_event_ids = set(preview["source_event_id"] for preview in previews) - eligible_event_ids
        self.assertEqual({item["source_event_id"] for item in invalidations}, eligible_event_ids)
        self.assertEqual({item["source_event_id"] for item in rerun_steps}, eligible_event_ids)
        self.assertTrue(blocked_event_ids)
        self.assertFalse(blocked_event_ids & {item["source_event_id"] for item in invalidations})
        self.assertFalse(blocked_event_ids & {item["source_event_id"] for item in rerun_steps})

    def test_rerun_chain_preserves_versions_without_overwriting_old_outputs(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )
        validate_manual_rerun_mechanism_artifacts(
            manifest, invalidations, rerun_steps, consistency_checks, render_outputs, events, previews
        )

        steps_by_event = {}
        for step in rerun_steps:
            steps_by_event.setdefault(step["source_event_id"], []).append(step)
            self.assertTrue(step["old_derived_version_ref"])
            self.assertTrue(step["new_derived_version_ref"])
            self.assertNotEqual(step["old_derived_version_ref"], step["new_derived_version_ref"])
            self.assertFalse(step["overwrite_old_version_allowed"])
            self.assertFalse(step["raw_layer_write_allowed"])
            self.assertFalse(step["formal_report_generated"])

        for steps in steps_by_event.values():
            ordered = sorted(steps, key=lambda item: item["chain_order"])
            self.assertEqual(tuple(step["chain_layer"] for step in ordered), REQUIRED_RERUN_CHAIN)

    def test_same_source_consistency_is_required_after_rerun(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )
        validate_manual_rerun_mechanism_artifacts(
            manifest, invalidations, rerun_steps, consistency_checks, render_outputs, events, previews
        )

        for check in consistency_checks:
            self.assertTrue(check["same_source_consistency_passed"])
            self.assertEqual(check["consistency_status"], "passed")
            self.assertTrue(check["checked_layers"])
            self.assertFalse(check["raw_layer_write_allowed"])

        broken_checks = [dict(check) for check in consistency_checks]
        broken_checks[0]["same_source_consistency_passed"] = False
        with self.assertRaises(ManualRerunMechanismError):
            validate_manual_rerun_mechanism_artifacts(
                manifest, invalidations, rerun_steps, broken_checks, render_outputs, events, previews
            )

    def test_blocked_preview_cannot_be_forced_into_rerun(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )

        blocked_preview = next(preview for preview in previews if not preview["control_event_publish_allowed"])
        forced_step = dict(rerun_steps[0])
        forced_step["rerun_step_id"] = "RERUN-S12P3-999-01"
        forced_step["source_event_id"] = blocked_preview["source_event_id"]
        forced_step["source_preview_id"] = blocked_preview["preview_id"]
        with self.assertRaises(ManualRerunMechanismError):
            validate_manual_rerun_mechanism_artifacts(
                manifest,
                invalidations,
                rerun_steps + [forced_step],
                consistency_checks,
                render_outputs,
                events,
                previews,
            )

    def test_rendered_html_exposes_rerun_without_formal_report_or_raw_data(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )
        validate_manual_rerun_mechanism_artifacts(
            manifest, invalidations, rerun_steps, consistency_checks, render_outputs, events, previews
        )
        html_text = render_outputs["html"]["kmfa_manual_rerun_mechanism"]

        self.assertTrue(html_text.startswith("<!doctype html>"))
        for required_text in (
            "KMFA 重跑机制",
            "派生缓存失效",
            "字段映射",
            "事实层",
            "指标",
            "报告引用",
            "同源引用一致性",
            "正式报告未生成",
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

    def test_public_payload_has_no_raw_private_or_upload_scope(self) -> None:
        _, events, preview_manifest, previews = self._build_upstream()
        manifest, invalidations, rerun_steps, consistency_checks, render_outputs = (
            build_default_manual_rerun_mechanism_artifacts(
                source_events=events,
                source_preview_manifest=preview_manifest,
                source_previews=previews,
                generated_at="2026-07-01T14:00:00+10:00",
            )
        )
        validate_manual_rerun_mechanism_artifacts(
            manifest, invalidations, rerun_steps, consistency_checks, render_outputs, events, previews
        )
        payload = json.dumps(
            [manifest, invalidations, rerun_steps, consistency_checks, render_outputs],
            ensure_ascii=False,
            sort_keys=True,
        )

        for forbidden_text in (
            "private_ref://",
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
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])
        self.assertFalse(manifest["quality_gate"]["stage12_review_allowed"])


if __name__ == "__main__":
    unittest.main()
