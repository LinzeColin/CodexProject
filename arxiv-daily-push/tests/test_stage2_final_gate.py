from __future__ import annotations

import json
from pathlib import Path
import unittest

from arxiv_daily_push.stage2_final_gate import (
    S2PLT02_BLOCKING_REASONS,
    S2PLT02_FORBIDDEN_FLAGS,
    S2PLT02_REQUIRED_DEPENDENCIES,
    S2PLT02_REQUIRED_EMAIL_COUNT,
    S2PLT02_REQUIRED_EVIDENCE,
    S2PLT02_REQUIRED_MAIL_PRODUCTS,
    S2PLT02_REQUIRED_NATURAL_DAYS,
    S2PLT04_BLOCKING_REASONS,
    S2PLT04_FORBIDDEN_FLAGS,
    S2PLT04_REQUIRED_DEPENDENCIES,
    S2PLT04_REQUIRED_EVIDENCE,
    S2PMT07_BLOCKING_REASONS,
    S2PMT07_FORBIDDEN_PASS_FLAGS,
    S2PMT07_REQUIRED_DEPENDENCIES,
    S2PMT07_REQUIRED_EVIDENCE,
    S2PMT07_REQUIRED_TEST_COMMANDS,
    build_s2plt02_dependency_state,
    build_s2plt02_live_2d_precheck_report,
    build_s2plt02_live_evidence_state,
    build_s2plt04_dependency_state,
    build_s2plt04_evidence_state,
    build_s2plt04_integration_candidate_report,
    build_audit_blocker_state,
    build_dependency_state,
    build_evidence_bundle_state,
    build_reviewer_independence_state,
    build_s2pmt07_precheck_report,
    build_test_gate_state,
    validate_s2plt02_live_2d_precheck_report,
    validate_s2plt04_integration_candidate_report,
    validate_s2pmt07_precheck_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class Stage2FinalGateTests(unittest.TestCase):
    def test_s2plt02_dependency_state_blocks_without_s2plt01_acceptance(self) -> None:
        state = build_s2plt02_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT02_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["completed_dependencies"], {})
        self.assertEqual(tuple(state["unmet_dependencies"]), S2PLT02_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["s2plt01_acceptance_status"], "blocked_by_inherited_p0_p1_and_final_gates")

    def test_s2plt02_live_evidence_state_records_missing_real_run(self) -> None:
        state = build_s2plt02_live_evidence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_evidence"]), S2PLT02_REQUIRED_EVIDENCE)
        self.assertEqual(state["required_natural_days"], S2PLT02_REQUIRED_NATURAL_DAYS)
        self.assertEqual(state["observed_natural_days"], 0)
        self.assertEqual(state["required_email_count"], S2PLT02_REQUIRED_EMAIL_COUNT)
        self.assertEqual(state["observed_email_count"], 0)
        self.assertEqual(tuple(state["required_mail_products"]), S2PLT02_REQUIRED_MAIL_PRODUCTS)
        self.assertFalse(state["available_evidence"]["S2PLT01_ACCEPTED"])
        self.assertFalse(state["available_evidence"]["REAL_SCHEDULER_PROVEN"])
        self.assertFalse(state["available_evidence"]["REAL_SMTP_PROVEN"])
        self.assertFalse(state["m4_watermark_correct"])

    def test_s2plt02_live_2d_precheck_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt02_live_2d_precheck_report(generated_at="2026-06-26T19:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PLT02_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PLT02_BLOCKING_REASONS:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertFalse(report["gates"]["s2plt01_accepted"])
        self.assertFalse(report["gates"]["real_scheduler_proven"])
        self.assertFalse(report["gates"]["real_smtp_proven"])
        self.assertEqual(validate_s2plt02_live_2d_precheck_report(report), [])

        tampered = dict(report)
        tampered["real_smtp_sent"] = True
        self.assertIn("real_smtp_sent must be false", validate_s2plt02_live_2d_precheck_report(tampered))

    def test_s2plt04_dependency_state_keeps_unaccepted_upstream_tasks_blocked(self) -> None:
        state = build_s2plt04_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT04_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["completed_dependencies"], {})
        self.assertEqual(set(state["unmet_dependencies"]), set(S2PLT04_REQUIRED_DEPENDENCIES))
        self.assertIn("S2PLT01-INDEPENDENT-REPLAY-REVIEW", state["available_local_evidence"])
        self.assertEqual(state["s2plt01_acceptance_status"], "blocked_by_inherited_p0_p1_and_final_gates")
        self.assertEqual(state["s2plt02_status"], "missing_authoritative_completion_evidence")
        self.assertEqual(state["s2plt03_status"], "missing_authoritative_completion_evidence")

    def test_s2plt04_evidence_state_records_available_local_evidence_without_final_bundle(self) -> None:
        state = build_s2plt04_evidence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_evidence"]), S2PLT04_REQUIRED_EVIDENCE)
        self.assertTrue(state["available_evidence"]["STATE_CONSISTENCY_EVIDENCE"])
        self.assertTrue(state["available_evidence"]["CONTENT_EVIDENCE"])
        self.assertFalse(state["available_evidence"]["S2PLT01_ACCEPTED"])
        self.assertFalse(state["available_evidence"]["S2PLT02_2D_REAL_RUN"])
        self.assertFalse(state["available_evidence"]["S2PLT03_RESILIENCE_DRILL"])
        self.assertFalse(state["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"])

    def test_s2plt04_integration_candidate_report_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-26T18:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PLT04_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PLT04_BLOCKING_REASONS:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertIn("s2pmt07_final_gate_precheck_blocked", report["blocking_reasons"])
        self.assertEqual(report["s2pmt07_precheck"]["status"], "blocked")
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

        tampered = dict(report)
        tampered["s2_integration_candidate_ready"] = True
        self.assertIn("s2_integration_candidate_ready must be false", validate_s2plt04_integration_candidate_report(tampered))

    def test_audit_blocker_state_blocks_current_inherited_p0_p1(self) -> None:
        state = build_audit_blocker_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["inherited_v7_1_open_p0_findings"], 8)
        self.assertEqual(state["inherited_v7_1_open_p1_findings"], 37)
        self.assertFalse(state["checks"]["P0_zero"])
        self.assertFalse(state["checks"]["P1_zero"])

        cleared = build_audit_blocker_state(inherited_p0=0, inherited_p1=0)
        self.assertEqual(cleared["status"], "pass")

    def test_p0_review_receipt_uses_current_b007_b008_evidence(self) -> None:
        receipt_path = REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md"
        manifest_path = REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P0-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
        receipt = receipt_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_rows = {
            line.split("|", 3)[1].strip(" `"): line
            for line in receipt.splitlines()
            if line.startswith("| `B-00")
        }

        self.assertIn("PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json", receipt_rows["B-007"])
        self.assertNotIn("ADP-S2PMT05-STRESS-E2E-20260626.json", receipt_rows["B-007"])
        self.assertIn("PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json", receipt_rows["B-008"])
        self.assertNotIn("ADP-S2PMT05-STRESS-E2E-20260626.json", receipt_rows["B-008"])

        findings = {finding["finding_id"]: finding for finding in manifest["p0_findings"]}
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md",
            findings["B-008"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json",
            findings["B-008"]["evidence_refs"],
        )
        self.assertNotIn("governance/run_manifests/ADP-S2PMT05-STRESS-E2E-20260626.json", findings["B-007"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT05-STRESS-E2E-20260626.json", findings["B-008"]["evidence_refs"])

    def test_p1_review_receipt_uses_refreshed_current_evidence(self) -> None:
        receipt_path = REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_INDEPENDENT_REVIEW_RECEIPT.md"
        manifest_path = REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
        refresh_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A015-20260627.json"
        )
        receipt = receipt_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_rows = {
            line.split("|", 3)[1].strip(" `"): line
            for line in receipt.splitlines()
            if line.startswith("| `")
        }

        expected_current_refs = {
            "A-006": ("PHASE_S2PMT03_RUNTIME_LOCK_A006.md", "ADP-S2PMT03-RUNTIME-LOCK-A006-20260626.json"),
            "A-007": ("PHASE_S2PMT03_STATE_HISTORY_A007.md", "ADP-S2PMT03-STATE-HISTORY-A007-20260626.json"),
            "A-008": (
                "PHASE_S2PMT03_STATE_CONSISTENCY_A008.md",
                "ADP-S2PMT03-STATE-CONSISTENCY-A008-20260626.json",
            ),
            "A-009": (
                "PHASE_S2PMT03_OPTIMISTIC_FENCING_A009.md",
                "ADP-S2PMT03-OPTIMISTIC-FENCING-A009-20260626.json",
            ),
            "A-010": ("PHASE_S2PMT02_ARTIFACT_ATOMIC_PUBLISH.md", "ADP-S2PMT02-ARTIFACT-ATOMIC-PUBLISH-20260626.json"),
            "A-011": ("PHASE_S2PMT02_ARTIFACT_SHA256.md", "ADP-S2PMT02-ARTIFACT-SHA256-20260626.json"),
            "A-012": ("PHASE_S2PMT01_INPUT_URL_SAFETY_A012.md", "ADP-S2PMT01-INPUT-URL-SAFETY-A012-20260626.json"),
            "A-013": ("PHASE_S2PMT04_SCHEDULER_TEMPLATE_A013.md", "ADP-S2PMT04-SCHEDULER-TEMPLATE-A013-20260626.json"),
            "A-014": ("PHASE_S2PMT02_SUPPORTING_FILE_COLLISION.md", "ADP-S2PMT02-SUPPORTING-FILE-COLLISION-20260626.json"),
            "A-015": ("PHASE_S2PMT05_FUTURE_HEARTBEAT_A015.md", "ADP-S2PMT05-FUTURE-HEARTBEAT-A015-20260627.json"),
            "A-016": ("PHASE_S2PMT03_LESSON_REVISION_A016.md", "ADP-S2PMT03-LESSON-REVISION-A016-20260626.json"),
            "A-017": ("PHASE_S2PMT03_SMTP_IDENTITY_A017.md", "ADP-S2PMT03-SMTP-IDENTITY-A017-20260626.json"),
            "A-018": ("PHASE_S2PAT05_ROI_DISCLOSURE_A018.md", "ADP-S2PAT05-ROI-DISCLOSURE-A018-20260626.json"),
            "A-020": ("PHASE_S2PMT01_SUPPLY_CHAIN_A020.md", "ADP-S2PMT01-SUPPLY-CHAIN-A020-20260626.json"),
            "A-021": ("PHASE_S2PAT05_ROADMAP_STOP_CODE_A021.md", "ADP-S2PAT05-ROADMAP-STOP-CODE-A021-20260626.json"),
            "B-003": ("PHASE_S2PMT03_WATCHDOG_RECOVERY_B003.md", "ADP-S2PMT03-WATCHDOG-RECOVERY-B003-20260626.json"),
            "B-004": ("PHASE_S2PMT04_STARTUP_CONVERGENCE_B004.md", "ADP-S2PMT04-STARTUP-CONVERGENCE-B004-20260626.json"),
            "B-005": ("PHASE_S2PMT04_CACHE_LOW_DISK_B005.md", "ADP-S2PMT04-CACHE-LOW-DISK-B005-20260626.json"),
            "B-006": ("PHASE_S2PMT05_CAPACITY_BASELINE_B006.md", "ADP-S2PMT05-CAPACITY-BASELINE-B006-20260627.json"),
            "B-009": ("PHASE_S2PMT05_FAULT_INJECTION_B009.md", "ADP-S2PMT05-FAULT-INJECTION-B009-20260627.json"),
            "B-010": ("PHASE_S2PMT05_TIME_POLICY_B010.md", "ADP-S2PMT05-TIME-POLICY-B010-20260627.json"),
            "B-011": ("PHASE_S2PMT03_M4_WATERMARK_B011.md", "ADP-S2PMT03-M4-WATERMARK-B011-20260626.json"),
            "B-012": ("PHASE_S2PMT05_E2E_B012.md", "ADP-S2PMT05-E2E-B012-20260627.json"),
            "B-013": ("PHASE_S2PMT05_RESULT_VALIDITY_B013.md", "ADP-S2PMT05-RESULT-VALIDITY-B013-20260626.json"),
            "B-014": ("PHASE_S2PMT05_BACKPRESSURE_B014.md", "ADP-S2PMT05-BACKPRESSURE-B014-20260627.json"),
            "B-015": ("PHASE_S2PMT04_TRANSACTION_COMPLETION_B015.md", "ADP-S2PMT04-TRANSACTION-COMPLETION-B015-20260626.json"),
        }
        stale_refs = {
            "A-006": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-007": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-008": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-009": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-010": (
                "PHASE_S2PMT02_ATOMIC_RECOVERY.md",
                "PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
                "ADP-S2PMT02-ATOMIC-RECOVERY-20260626.json",
            ),
            "A-011": (
                "PHASE_S2PMT02_ATOMIC_RECOVERY.md",
                "PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
                "ADP-S2PMT02-ATOMIC-RECOVERY-20260626.json",
            ),
            "A-012": ("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json",),
            "A-013": ("PHASE_S2PMT04_LIFECYCLE_CACHE.md", "ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json"),
            "A-014": (
                "PHASE_S2PMT02_ATOMIC_RECOVERY.md",
                "PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
                "ADP-S2PMT02-ATOMIC-RECOVERY-20260626.json",
            ),
            "A-015": ("PHASE_S2PMT05_STRESS_E2E.md", "ADP-S2PMT05-STRESS-E2E-20260626.json"),
            "A-016": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-017": ("ADP-S2PMT03-LEASE-FENCING-20260626.json",),
            "A-018": ("PHASE_S2PKT01_MAIL_CONTRACT.md",),
            "A-020": ("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json",),
            "A-021": ("PHASE_S2PAT02_PRODUCT_CONTRACT.md",),
            "B-003": ("ADP-S2PMT03-LEASE-FENCING-20260626.json",),
            "B-004": ("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json",),
            "B-005": ("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json",),
            "B-006": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-009": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-010": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-011": ("ADP-S2PMT03-LEASE-FENCING-20260626.json",),
            "B-012": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-013": ("ADP-S2PHT05-CONTENT-QUALITY-GATE-20260626.json", "S2PHT05"),
            "B-014": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-015": ("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json",),
        }

        findings = {finding["finding_id"]: finding for finding in manifest["p1_findings"]}
        self.assertEqual(manifest["refreshed_findings"], list(expected_current_refs))
        self.assertEqual(
            manifest["refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-A015-20260627.json",
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-20260627.json",
            manifest["refresh_manifests"],
        )
        self.assertIn(manifest["refresh_manifest"], manifest["refresh_manifests"])
        self.assertTrue(refresh_manifest_path.exists())
        self.assertFalse(manifest["p1_closure_claimed"])
        self.assertFalse(manifest["independent_review_signoff_present"])
        self.assertFalse(manifest["stage2_integrated_production_accepted"])
        self.assertEqual(manifest["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(manifest["inherited_v7_1_open_p1_findings_after"], 37)

        for finding_id, refs in expected_current_refs.items():
            row = receipt_rows[finding_id]
            finding_refs = "\n".join(findings[finding_id]["evidence_refs"])
            for ref in refs:
                self.assertIn(ref, row)
                self.assertIn(ref, finding_refs)
            for stale_ref in stale_refs[finding_id]:
                self.assertNotIn(stale_ref, row)
                self.assertNotIn(stale_ref, finding_refs)
            self.assertIn("refreshed_current_evidence_located", findings[finding_id]["preliminary_review_state"])

    def test_dependency_state_requires_s2plt04_and_records_missing_completion(self) -> None:
        state = build_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PMT07_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["s2plt04_status"], "missing_authoritative_completion_evidence")
        self.assertIn("S2PLT04", state["missing_dependencies"])
        for task_id in S2PMT07_REQUIRED_DEPENDENCIES[:6]:
            self.assertIn(task_id, state["completed_dependencies"])

    def test_reviewer_independence_does_not_self_certify_final_review(self) -> None:
        state = build_reviewer_independence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertTrue(state["reviewer_involved_in_s2pmt01_t06"])
        self.assertFalse(state["independent_reviewer_proven"])

        independent = build_reviewer_independence_state(reviewer_involved_in_s2pmt01_t06=False)
        self.assertEqual(independent["status"], "pass")

    def test_evidence_bundle_and_test_gate_are_blocked_until_final_artifacts_exist(self) -> None:
        evidence = build_evidence_bundle_state()
        tests = build_test_gate_state()

        self.assertEqual(evidence["status"], "blocked")
        self.assertEqual(tuple(evidence["required_evidence"]), S2PMT07_REQUIRED_EVIDENCE)
        self.assertEqual(set(evidence["missing_evidence"]), set(S2PMT07_REQUIRED_EVIDENCE))
        self.assertEqual(tests["status"], "blocked")
        self.assertEqual(tuple(tests["required_test_commands"]), S2PMT07_REQUIRED_TEST_COMMANDS)
        self.assertFalse(tests["executed_as_final_reviewer"])

    def test_full_precheck_report_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2pmt07_precheck_report(generated_at="2026-06-26T17:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PMT07_FORBIDDEN_PASS_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PMT07_BLOCKING_REASONS[:4]:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertIn("final_acceptance_bundle_missing", report["blocking_reasons"])
        self.assertIn("independent_review_signoff_missing", report["blocking_reasons"])
        self.assertIn("independent_final_command_execution_missing", report["blocking_reasons"])
        self.assertFalse(report["test_gates"]["executed_as_final_reviewer"])
        self.assertEqual(validate_s2pmt07_precheck_report(report), [])

        tampered = dict(report)
        tampered["integrated_production_accepted"] = True
        self.assertIn("integrated_production_accepted must be false", validate_s2pmt07_precheck_report(tampered))

    def test_s2pmt07_final_command_blocker_is_recorded_in_report_phase_and_manifest(self) -> None:
        blocker = "independent_final_command_execution_missing"
        report = build_s2pmt07_precheck_report(generated_at="2026-06-27T02:59:04+10:00")
        phase_record = (
            REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_FINAL_GATE_PRECHECK.md"
        ).read_text(encoding="utf-8")
        manifest = json.loads(
            (REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-FINAL-GATE-PRECHECK-20260626.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(blocker, S2PMT07_BLOCKING_REASONS)
        self.assertIn(blocker, report["blocking_reasons"])
        self.assertFalse(report["gates"]["required_final_commands_executed"])
        self.assertFalse(report["test_gates"]["executed_as_final_reviewer"])
        self.assertIn(blocker, phase_record)
        self.assertIn(blocker, manifest["blocking_reasons"])
        self.assertFalse(manifest["independent_final_command_execution_present"])


if __name__ == "__main__":
    unittest.main()
