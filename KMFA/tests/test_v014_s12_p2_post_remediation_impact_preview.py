# -*- coding: utf-8 -*-
import importlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PHASE_ID = "V014_S12_P2_POST_REMEDIATION_IMPACT_PREVIEW"
TASK_ID = "KMFA-V014-S12-P2-POST-REMEDIATION-IMPACT-PREVIEW-20260711"
VERSION = "0.1.4-s12-p2-post-remediation-impact-preview"
ROOT = Path("KMFA/stage_artifacts") / PHASE_ID
MANIFEST = ROOT / "machine/impact_preview_manifest.json"
SUMMARY = ROOT / "machine/impact_preview_summary.json"
PREVIEWS = ROOT / "machine/impact_preview_definitions_public_safe.json"
HTML = ROOT / "exports/html/kmfa_impact_preview_workbench.html"
PRIVATE = Path("KMFA/.codex_private_runtime/v014_s12_p2_post_remediation_impact_preview")


class TestV014S12P2PostRemediationImpactPreview(unittest.TestCase):
    def _json(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"missing expected artifact: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_current_s12_p1_state_replaces_stale_legacy_preview_counts(self) -> None:
        manifest = self._json(MANIFEST)
        summary = self._json(SUMMARY)
        self.assertEqual(manifest["phase_id"], PHASE_ID)
        self.assertEqual(manifest["task_id"], TASK_ID)
        self.assertEqual(manifest["version"], VERSION)
        self.assertEqual(manifest["summary"], summary)
        self.assertTrue(manifest["s12_p1_post_remediation_dependency_validated"])
        self.assertTrue(manifest["legacy_s12_p2_policy_fixture_validated"])
        self.assertEqual(summary["source_pending_action_group_count"], 6)
        self.assertEqual(summary["source_event_template_count"], 4)
        self.assertEqual(summary["impact_preview_definition_count"], 6)
        self.assertEqual(summary["current_approved_business_event_count"], 0)
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_preview_definitions_cover_projects_metrics_reports_without_attribution(self) -> None:
        payload = self._json(PREVIEWS)
        previews = payload["previews"]
        self.assertEqual(payload["preview_count"], 6)
        self.assertEqual(len(previews), 6)
        self.assertEqual(len({row["source_group_id"] for row in previews}), 6)
        self.assertEqual({row["manual_action_kind"] for row in previews}, {
            "field_mapping", "project_matching", "difference_handling", "note"
        })
        self.assertEqual(sum(row["risk_level"] == "high" for row in previews), 5)
        self.assertEqual(sum(row["second_confirmation_required"] for row in previews), 5)
        for row in previews:
            self.assertEqual(row["project_attribution"], "unproven_or_not_applicable")
            self.assertEqual(row["project_scope_semantics"], "potential_impact_not_attribution")
            self.assertIsInstance(row["affected_project_scope"], list)
            self.assertIsInstance(row["affected_metrics"], list)
            self.assertIsInstance(row["affected_reports"], list)
            self.assertTrue(row["affected_project_scope"])
            self.assertTrue(row["affected_metrics"])
            self.assertTrue(row["affected_reports"])
            self.assertFalse(row["business_value_committed"])
            self.assertFalse(row["raw_layer_write_allowed"])

    def test_preview_and_publish_gates_require_confirmation_and_never_approve_business_events(self) -> None:
        manifest = self._json(MANIFEST)
        previews = self._json(PREVIEWS)["previews"]
        quality = manifest["quality_gate"]
        self.assertTrue(quality["impact_preview_generation_allowed"])
        self.assertTrue(quality["impact_preview_required_before_publish"])
        self.assertTrue(quality["high_risk_second_confirmation_required"])
        self.assertFalse(quality["unpassed_preview_publish_allowed"])
        self.assertFalse(quality["current_business_event_approval_allowed"])
        self.assertFalse(quality["current_business_event_publish_allowed"])
        self.assertFalse(quality["derived_rerun_allowed"])
        self.assertFalse(quality["persistent_business_write_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        for row in previews:
            self.assertEqual(row["preview_status"], "definition_ready_session_preview_required")
            self.assertFalse(row["preview_passed_persistently"])
            self.assertFalse(row["publish_allowed"])
            self.assertFalse(row["business_event_approval_allowed"])
            self.assertFalse(row["derived_rerun_allowed"])
            if row["risk_level"] == "high":
                self.assertEqual(row["second_confirmation_status"], "required_in_session")

    def test_html_exposes_search_preview_confirmation_and_blocked_publish_flow(self) -> None:
        self.assertTrue(HTML.is_file(), f"missing expected artifact: {HTML}")
        text = HTML.read_text(encoding="utf-8")
        for token in (
            "data-preview-search",
            "data-risk-filter",
            "data-generate-preview",
            "data-high-risk-ack",
            "data-confirm-preview",
            "data-check-publish",
            "data-reset-session",
            "受影响项目",
            "受影响指标",
            "受影响报告",
            "高风险二次确认",
            "未通过影响预览不得发布",
            "Q4 / D · NO_GO",
        ):
            self.assertIn(token, text)
        self.assertNotIn("data-rerun", text)
        self.assertNotIn("localStorage", text)
        self.assertNotIn("sessionStorage", text)
        self.assertNotIn("indexedDB", text)
        self.assertNotIn("fetch(", text)
        self.assertNotIn("XMLHttpRequest", text)

    def test_browser_evidence_covers_medium_and_high_risk_session_flows(self) -> None:
        evidence = self._json(PRIVATE / "browser_verification.json")
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(len(evidence["viewport_checks"]), 2)
        self.assertEqual(len(evidence["search_checks"]), 2)
        self.assertEqual(len(evidence["risk_filter_checks"]), 2)
        self.assertEqual(len(evidence["medium_preview_checks"]), 2)
        self.assertEqual(len(evidence["high_preview_checks"]), 2)
        self.assertEqual(len(evidence["preconfirmation_block_checks"]), 2)
        self.assertEqual(len(evidence["second_confirmation_checks"]), 2)
        self.assertEqual(len(evidence["publish_block_checks"]), 4)
        self.assertEqual(len(evidence["reload_reset_checks"]), 2)
        self.assertEqual(len(evidence["return_link_http_checks"]), 4)
        self.assertEqual(len(evidence["actual_navigation_checks"]), 4)
        self.assertTrue(all(row["no_horizontal_overflow"] for row in evidence["viewport_checks"]))
        self.assertTrue(all(row["console_error_count"] == 0 for row in evidence["viewport_checks"]))
        ignored = subprocess.run(["git", "check-ignore", "-q", PRIVATE.as_posix()]).returncode
        self.assertEqual(ignored, 0)

    def test_raw_and_downstream_boundaries_remain_closed(self) -> None:
        manifest = self._json(MANIFEST)
        summary = manifest["summary"]
        before = self._json(PRIVATE / "raw_immutability_before.json")
        after = self._json(PRIVATE / "raw_immutability_after.json")
        self.assertEqual(before["files"], after["files"])
        self.assertEqual(before["file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])
        self.assertFalse(summary["s12_p3_performed"])
        self.assertFalse(summary["stage12_review_performed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_strict_validator_and_frozen_semantics(self) -> None:
        result = subprocess.run(
            [
                "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
                "KMFA/tools/check_v014_s12_p2_post_remediation_impact_preview.py",
                "--require-private-evidence",
                "--require-browser-evidence",
            ],
            env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        try:
            validator = importlib.import_module(
                "KMFA.tools.check_v014_s12_p2_post_remediation_impact_preview"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"validator module missing: {exc}")
        matrix_path = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
        future = matrix_path.read_text(encoding="utf-8").replace(
            f'current_phase: "{PHASE_ID}"',
            'current_phase: "V014_S12_P3_FUTURE_TEST_ONLY"',
        )
        with tempfile.TemporaryDirectory() as tmp:
            temporary_matrix = Path(tmp) / "VERSION_MATRIX.yaml"
            temporary_matrix.write_text(future, encoding="utf-8")
            with mock.patch.object(validator.phase, "VERSION_MATRIX_PATH", temporary_matrix):
                validator.validate_v014_s12_p2_post_remediation_impact_preview.cache_clear()
                validated = validator.validate_v014_s12_p2_post_remediation_impact_preview(
                    require_private_evidence=True,
                    require_browser_evidence=True,
                )
        self.assertEqual(validated["phase_id"], PHASE_ID)


if __name__ == "__main__":
    unittest.main()
