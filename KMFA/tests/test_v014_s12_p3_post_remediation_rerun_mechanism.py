# -*- coding: utf-8 -*-
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PHASE_ID = "V014_S12_P3_POST_REMEDIATION_RERUN_MECHANISM"
TASK_ID = "KMFA-V014-S12-P3-POST-REMEDIATION-RERUN-MECHANISM-20260711"
VERSION = "0.1.4-s12-p3-post-remediation-rerun-mechanism"
ROOT = Path("KMFA/stage_artifacts") / PHASE_ID
MANIFEST = ROOT / "machine/rerun_manifest.json"
SUMMARY = ROOT / "machine/rerun_summary.json"
PLANS = ROOT / "machine/rerun_plan_definitions_public_safe.json"
HTML = ROOT / "exports/html/kmfa_rerun_workbench.html"
PRIVATE = Path("KMFA/.codex_private_runtime/v014_s12_p3_post_remediation_rerun_mechanism")
REQUIRED_CHAIN = ("field_mapping", "fact_layer", "derived_metric", "report_reference")


class TestV014S12P3PostRemediationRerunMechanism(unittest.TestCase):
    def _json(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"missing expected artifact: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_current_s12_p2_state_replaces_stale_legacy_rerun_counts(self) -> None:
        manifest = self._json(MANIFEST)
        summary = self._json(SUMMARY)
        self.assertEqual(manifest["phase_id"], PHASE_ID)
        self.assertEqual(manifest["task_id"], TASK_ID)
        self.assertEqual(manifest["version"], VERSION)
        self.assertEqual(manifest["summary"], summary)
        self.assertTrue(manifest["s12_p2_post_remediation_dependency_validated"])
        self.assertTrue(manifest["legacy_s12_p3_policy_fixture_validated"])
        self.assertEqual(summary["source_pending_action_group_count"], 6)
        self.assertEqual(summary["source_impact_preview_definition_count"], 6)
        self.assertEqual(summary["rerun_plan_definition_count"], 6)
        self.assertEqual(summary["planned_rerun_step_count"], 24)
        self.assertEqual(summary["required_rerun_chain_layer_count"], 4)
        self.assertEqual(summary["current_approved_business_event_count"], 0)
        self.assertEqual(summary["current_published_business_event_count"], 0)
        self.assertEqual(summary["current_persistent_cache_invalidation_count"], 0)
        self.assertEqual(summary["current_persistent_rerun_step_count"], 0)
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertNotIn("eligible_event_count", summary)
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_six_plans_cover_four_layer_chain_without_project_attribution(self) -> None:
        payload = self._json(PLANS)
        plans = payload["plans"]
        self.assertEqual(payload["plan_count"], 6)
        self.assertEqual(tuple(payload["required_rerun_chain"]), REQUIRED_CHAIN)
        self.assertEqual(len(plans), 6)
        self.assertEqual(len({row["source_preview_id"] for row in plans}), 6)
        self.assertEqual(sum(row["risk_level"] == "high" for row in plans), 5)
        for plan in plans:
            self.assertEqual(plan["project_attribution"], "unproven_or_not_applicable")
            self.assertEqual(plan["project_scope_semantics"], "potential_impact_not_attribution")
            self.assertEqual(plan["eligibility_status"], "blocked_no_approved_published_event")
            self.assertEqual(tuple(step["layer"] for step in plan["rerun_steps"]), REQUIRED_CHAIN)
            self.assertEqual(len(plan["rerun_steps"]), 4)
            self.assertEqual(
                {step["source_anchor_id"] for step in plan["rerun_steps"]},
                {plan["source_anchor_id"]},
            )
            self.assertTrue(all(step["old_version_retained"] for step in plan["rerun_steps"]))
            self.assertTrue(all(step["new_version_append_required"] for step in plan["rerun_steps"]))
            self.assertTrue(all(step["status"] == "planned_session_simulation_only" for step in plan["rerun_steps"]))
            self.assertFalse(plan["persistent_cache_invalidation_allowed"])
            self.assertFalse(plan["persistent_rerun_allowed"])
            self.assertFalse(plan["raw_layer_write_allowed"])
            self.assertFalse(plan["business_value_committed"])

    def test_session_simulation_is_bounded_and_persistent_execution_remains_blocked(self) -> None:
        manifest = self._json(MANIFEST)
        plans = self._json(PLANS)["plans"]
        quality = manifest["quality_gate"]
        self.assertTrue(quality["rerun_plan_generation_allowed"])
        self.assertTrue(quality["session_only_rerun_simulation_allowed"])
        self.assertTrue(quality["same_source_reference_consistency_check_required"])
        self.assertTrue(quality["append_only_derived_version_required"])
        self.assertEqual(quality["money_tolerance_minor_units"], 0)
        self.assertFalse(quality["one_cent_difference_ignored"])
        self.assertFalse(quality["persistent_cache_invalidation_allowed"])
        self.assertFalse(quality["persistent_derived_rerun_allowed"])
        self.assertFalse(quality["old_version_overwrite_allowed"])
        self.assertFalse(quality["current_business_event_approval_allowed"])
        self.assertFalse(quality["current_business_event_publish_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertTrue(all(row["session_rerun_simulation_allowed"] for row in plans))
        self.assertTrue(all(row["second_confirmation_required"] for row in plans if row["risk_level"] == "high"))

    def test_html_exposes_rerun_plan_confirmation_simulation_and_consistency_flow(self) -> None:
        self.assertTrue(HTML.is_file(), f"missing expected artifact: {HTML}")
        text = HTML.read_text(encoding="utf-8")
        for token in (
            "data-rerun-search",
            "data-risk-filter",
            "data-select-plan",
            "data-preview-rerun",
            "data-high-risk-ack",
            "data-confirm-rerun",
            "data-run-simulation",
            "data-check-consistency",
            "data-reset-session",
            "派生缓存失效",
            "字段映射",
            "事实层",
            "指标",
            "报告引用",
            "同源引用一致性",
            "Q4 / D · NO_GO",
        ):
            self.assertIn(token, text)
        self.assertNotIn("localStorage", text)
        self.assertNotIn("sessionStorage", text)
        self.assertNotIn("indexedDB", text)
        self.assertNotIn("fetch(", text)
        self.assertNotIn("XMLHttpRequest", text)
        self.assertNotIn("public-safe session simulation", text)
        self.assertNotIn("GitHub upload", text)

    def test_browser_evidence_covers_medium_and_high_risk_session_simulations(self) -> None:
        browser_summary = self._json(MANIFEST)["browser_review"]
        self.assertEqual(browser_summary["current_html_control_row_count"], 12)
        self.assertEqual(browser_summary["current_html_pass_count"], 12)
        self.assertEqual(browser_summary["current_html_fail_count"], 0)
        evidence = self._json(PRIVATE / "browser_verification.json")
        self.assertEqual(evidence["status"], "PASS")
        for key, expected in (
            ("viewport_checks", 2),
            ("search_checks", 2),
            ("risk_filter_checks", 2),
            ("medium_plan_checks", 2),
            ("high_plan_checks", 2),
            ("preconfirmation_block_checks", 2),
            ("second_confirmation_checks", 2),
            ("rerun_simulation_checks", 2),
            ("consistency_checks", 2),
            ("persistent_execution_block_checks", 2),
            ("reload_reset_checks", 2),
            ("return_link_http_checks", 4),
            ("actual_navigation_checks", 4),
        ):
            self.assertEqual(len(evidence[key]), expected, key)
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
        self.assertTrue(summary["s12_p3_performed"])
        self.assertFalse(summary["persistent_derived_rerun_performed"])
        self.assertFalse(summary["stage12_review_performed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_strict_validator_and_frozen_semantics(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "KMFA/tools/check_v014_s12_p3_post_remediation_rerun_mechanism.py",
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
                "KMFA.tools.check_v014_s12_p3_post_remediation_rerun_mechanism"
            )
        except ModuleNotFoundError as exc:
            self.fail(f"validator module missing: {exc}")
        matrix_path = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
        future = matrix_path.read_text(encoding="utf-8").replace(
            f'current_phase: "{PHASE_ID}"',
            'current_phase: "V014_S12_STAGE_REVIEW_FUTURE_TEST_ONLY"',
        )
        with tempfile.TemporaryDirectory() as tmp:
            temporary_matrix = Path(tmp) / "VERSION_MATRIX.yaml"
            temporary_matrix.write_text(future, encoding="utf-8")
            with mock.patch.object(validator.phase, "VERSION_MATRIX_PATH", temporary_matrix):
                validator.validate_v014_s12_p3_post_remediation_rerun_mechanism.cache_clear()
                validated = validator.validate_v014_s12_p3_post_remediation_rerun_mechanism(
                    require_private_evidence=True,
                    require_browser_evidence=True,
                )
        self.assertEqual(validated["phase_id"], PHASE_ID)


if __name__ == "__main__":
    unittest.main()
