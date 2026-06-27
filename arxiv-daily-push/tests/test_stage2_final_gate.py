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

    def test_p0_review_receipt_uses_refreshed_current_evidence(self) -> None:
        receipt_path = REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md"
        manifest_path = REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P0-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
        package_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json"
        )
        package_phase_record_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE.md"
        )
        refresh_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json"
        )
        isolated_proof_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json"
        )
        independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a001_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a002_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a003_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a004_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a005_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        b007_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        b008_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        receipt = receipt_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_rows = {
            line.split("|", 3)[1].strip(" `"): line
            for line in receipt.splitlines()
            if line.startswith("| `")
        }

        self.assertIn("PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md", receipt_rows["A-001"])
        self.assertIn("ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json", receipt_rows["A-001"])
        self.assertIn("ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-001"])
        self.assertIn("用户中心/恢复路径安全扫描.md", receipt_rows["A-001"])
        self.assertNotIn("PHASE_S2PMT02_ATOMIC_RECOVERY.md", receipt_rows["A-001"])
        self.assertIn("PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md", receipt_rows["A-002"])
        self.assertIn("ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json", receipt_rows["A-002"])
        self.assertIn("ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-002"])
        self.assertIn("用户中心/恢复原子替换扫描.md", receipt_rows["A-002"])
        self.assertNotIn("PHASE_S2PMT02_ATOMIC_RECOVERY.md", receipt_rows["A-002"])
        self.assertNotIn("PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md", receipt_rows["A-002"])
        self.assertIn("PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md", receipt_rows["A-003"])
        self.assertIn("ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json", receipt_rows["A-003"])
        self.assertIn("ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-003"])
        self.assertIn("用户中心/事务发件箱与消息ID扫描.md", receipt_rows["A-003"])
        self.assertIn("test_stage2_lease_fencing.py", receipt_rows["A-003"])
        self.assertNotIn("PHASE_S2PMT03_LEASE_FENCING.md", receipt_rows["A-003"])
        self.assertNotIn("ADP-S2PMT03-LEASE-FENCING-20260626.json", receipt_rows["A-003"])
        self.assertIn("PHASE_S2PMT01_FRONTSTAGE_EVIDENCE_A004.md", receipt_rows["A-004"])
        self.assertIn("ADP-S2PMT01-FRONTSTAGE-EVIDENCE-A004-20260627.json", receipt_rows["A-004"])
        self.assertIn("ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-004"])
        self.assertIn("用户中心/前台陈述证据绑定扫描.md", receipt_rows["A-004"])
        self.assertIn("security_boundary.py", receipt_rows["A-004"])
        self.assertIn("test_security_boundary.py", receipt_rows["A-004"])
        self.assertNotIn("PHASE_S2PMT01_SECURITY_BOUNDARY.md", receipt_rows["A-004"])
        self.assertNotIn("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", receipt_rows["A-004"])
        self.assertIn("PHASE_S2PMT01_TRUST_BOUNDARY_A005.md", receipt_rows["A-005"])
        self.assertIn("ADP-S2PMT01-TRUST-BOUNDARY-A005-20260627.json", receipt_rows["A-005"])
        self.assertIn("ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-005"])
        self.assertIn("用户中心/来源信任边界扫描.md", receipt_rows["A-005"])
        self.assertIn("security_boundary.py", receipt_rows["A-005"])
        self.assertIn("test_security_boundary.py", receipt_rows["A-005"])
        self.assertNotIn("PHASE_S2PMT01_SECURITY_BOUNDARY.md", receipt_rows["A-005"])
        self.assertNotIn("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", receipt_rows["A-005"])
        self.assertIn("PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md", receipt_rows["B-001"])
        self.assertIn("ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json", receipt_rows["B-001"])
        self.assertIn("ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json", receipt_rows["B-001"])
        self.assertIn("ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["B-001"])
        self.assertIn("用户中心/自动唤醒安装生命周期扫描.md", receipt_rows["B-001"])
        self.assertIn("test_stage2_lifecycle_cache.py", receipt_rows["B-001"])
        self.assertNotIn("PHASE_S2PMT04_LIFECYCLE_CACHE.md", receipt_rows["B-001"])
        self.assertNotIn("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json", receipt_rows["B-001"])
        self.assertIn("PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json", receipt_rows["B-007"])
        self.assertIn("PHASE_S2PMT07_B007_MULTIPROCESS_RACE_EVIDENCE.md", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["B-007"])
        self.assertIn("stage2_stress_e2e.py", receipt_rows["B-007"])
        self.assertIn("stage2_lease_fencing.py", receipt_rows["B-007"])
        self.assertNotIn("ADP-S2PMT05-STRESS-E2E-20260626.json", receipt_rows["B-007"])
        self.assertIn("PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json", receipt_rows["B-008"])
        self.assertIn("PHASE_S2PMT07_B008_FAKE_SMTP_CRASH_WINDOW_EVIDENCE.md", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["B-008"])
        self.assertIn("stage2_lease_fencing.py", receipt_rows["B-008"])
        self.assertIn("test_smtp_delivery.py", receipt_rows["B-008"])
        self.assertNotIn("ADP-S2PMT05-STRESS-E2E-20260626.json", receipt_rows["B-008"])

        findings = {finding["finding_id"]: finding for finding in manifest["p0_findings"]}
        self.assertEqual(
            manifest["refreshed_findings"],
            ["A-001", "A-002", "A-003", "A-004", "A-005", "B-001", "B-007", "B-008"],
        )
        self.assertEqual(
            manifest["refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json",
        )
        self.assertEqual(
            manifest["previous_refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn(manifest["refresh_manifest"], manifest["refresh_manifests"])
        self.assertEqual(
            manifest["technical_closure_candidate_package"],
            "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json",
        )
        self.assertTrue(manifest["all_p0_finding_level_reviews_passed_no_production_acceptance"])
        self.assertTrue(manifest["p0_closure_package_ready_for_final_gate_review"])
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P0-REVIEW-RECEIPT-REFRESH-B001-ISOLATED-PROOF-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertTrue(refresh_manifest_path.exists())
        self.assertTrue(isolated_proof_manifest_path.exists())
        self.assertTrue(independent_review_manifest_path.exists())
        self.assertTrue(a001_independent_review_manifest_path.exists())
        self.assertTrue(a002_independent_review_manifest_path.exists())
        self.assertTrue(a003_independent_review_manifest_path.exists())
        self.assertTrue(a004_independent_review_manifest_path.exists())
        self.assertTrue(a005_independent_review_manifest_path.exists())
        self.assertTrue(b007_independent_review_manifest_path.exists())
        self.assertTrue(b008_independent_review_manifest_path.exists())
        self.assertTrue(package_manifest_path.exists())
        self.assertTrue(package_phase_record_path.exists())
        self.assertFalse(manifest["p0_closure_claimed"])
        self.assertFalse(manifest["stage2_integrated_production_accepted"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md",
            findings["A-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json",
            findings["A-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-001"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/恢复路径安全扫描.md",
            findings["A-001"]["evidence_refs"],
        )
        self.assertEqual(findings["A-001"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-001"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-001"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_ATOMIC_RECOVERY.md", findings["A-001"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/恢复原子替换扫描.md",
            findings["A-002"]["evidence_refs"],
        )
        self.assertEqual(findings["A-002"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-002"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-002"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_ATOMIC_RECOVERY.md", findings["A-002"]["evidence_refs"])
        self.assertNotIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/事务发件箱与消息ID扫描.md",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_stage2_lease_fencing.py", findings["A-003"]["evidence_refs"])
        self.assertEqual(findings["A-003"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-003"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-003"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT03_LEASE_FENCING.md", findings["A-003"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT03-LEASE-FENCING-20260626.json", findings["A-003"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_FRONTSTAGE_EVIDENCE_A004.md",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT01-FRONTSTAGE-EVIDENCE-A004-20260627.json",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/src/arxiv_daily_push/security_boundary.py",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/前台陈述证据绑定扫描.md",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_security_boundary.py", findings["A-004"]["evidence_refs"])
        self.assertEqual(findings["A-004"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-004"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-004"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_SECURITY_BOUNDARY.md", findings["A-004"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", findings["A-004"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_TRUST_BOUNDARY_A005.md",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT01-TRUST-BOUNDARY-A005-20260627.json",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/src/arxiv_daily_push/security_boundary.py",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/来源信任边界扫描.md",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_security_boundary.py", findings["A-005"]["evidence_refs"])
        self.assertEqual(findings["A-005"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-005"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-005"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_SECURITY_BOUNDARY.md", findings["A-005"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", findings["A-005"]["evidence_refs"])
        self.assertEqual(findings["B-001"]["fix_task"], "S2PMT04-INSTALL-LIFECYCLE-B001")
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/自动唤醒安装生命周期扫描.md",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_stage2_lifecycle_cache.py", findings["B-001"]["evidence_refs"])
        self.assertEqual(findings["B-001"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["B-001"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["B-001"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT04_LIFECYCLE_CACHE.md", findings["B-001"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json", findings["B-001"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_B007_MULTIPROCESS_RACE_EVIDENCE.md", findings["B-007"]["evidence_refs"])
        self.assertIn("governance/run_manifests/ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json", findings["B-007"]["evidence_refs"])
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/src/arxiv_daily_push/stage2_stress_e2e.py", findings["B-007"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py", findings["B-007"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/tests/test_stage2_lease_fencing.py", findings["B-007"]["evidence_refs"])
        self.assertEqual(findings["B-007"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["B-007"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["B-007"]["preliminary_review_state"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md",
            findings["B-008"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json",
            findings["B-008"]["evidence_refs"],
        )
        self.assertNotIn("governance/run_manifests/ADP-S2PMT05-STRESS-E2E-20260626.json", findings["B-007"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_B008_FAKE_SMTP_CRASH_WINDOW_EVIDENCE.md", findings["B-008"]["evidence_refs"])
        self.assertIn("governance/run_manifests/ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json", findings["B-008"]["evidence_refs"])
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["B-008"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py", findings["B-008"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/tests/test_stage2_lease_fencing.py", findings["B-008"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/tests/test_smtp_delivery.py", findings["B-008"]["evidence_refs"])
        self.assertEqual(findings["B-008"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["B-008"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["B-008"]["preliminary_review_state"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT05-STRESS-E2E-20260626.json", findings["B-008"]["evidence_refs"])

        package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
        package_phase_record = package_phase_record_path.read_text(encoding="utf-8")
        self.assertEqual(
            package_manifest["status"],
            "technical_closure_candidate_package_ready_no_p0_closure_no_production",
        )
        self.assertEqual(package_manifest["finding_count"], 8)
        self.assertEqual(package_manifest["expected_p0_finding_ids"], list(findings))
        self.assertTrue(package_manifest["package_checks"]["all_8_p0_findings_present"])
        self.assertTrue(package_manifest["package_checks"]["all_finding_level_review_receipts_present"])
        self.assertTrue(
            package_manifest["package_checks"]["all_finding_level_verdicts_pass_with_no_production_acceptance"]
        )
        self.assertTrue(package_manifest["package_checks"]["p0_counter_preserved_open"])
        self.assertTrue(package_manifest["package_checks"]["p1_counter_preserved_open"])
        self.assertFalse(package_manifest["package_checks"]["independent_final_signoff_present"])
        self.assertFalse(package_manifest["package_checks"]["independent_final_command_execution_present"])
        self.assertEqual(package_manifest["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(package_manifest["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(package_manifest["p0_closure_claimed"])
        self.assertFalse(package_manifest["p1_closure_claimed"])
        self.assertFalse(package_manifest["closure_claimed"])
        self.assertFalse(package_manifest["s2pmt07_final_pass_claimed"])
        self.assertFalse(package_manifest["stage2_integrated_production_accepted"])
        self.assertFalse(package_manifest["real_smtp_sent"])
        self.assertFalse(package_manifest["scheduler_install_enabled"])
        self.assertFalse(package_manifest["release_packaging_enabled"])
        self.assertFalse(package_manifest["production_restore_enabled"])
        self.assertFalse(package_manifest["current_pointer_changed"])
        self.assertFalse(package_manifest["v7_1_baseline_changed"])
        self.assertFalse(package_manifest["v7_2_contract_files_changed"])
        packaged = {finding["finding_id"]: finding for finding in package_manifest["packaged_findings"]}
        self.assertEqual(set(packaged), set(findings))
        for finding_id, finding in findings.items():
            self.assertEqual(
                packaged[finding_id]["finding_level_independent_review_receipt"],
                finding["finding_level_independent_review_receipt"],
            )
            self.assertEqual(packaged[finding_id]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(packaged[finding_id]["technical_closure_candidate"])
        self.assertIn("P0 Technical Closure Candidate Package", receipt)
        self.assertIn("P0 findings packaged | `8 / 8`", package_phase_record)
        self.assertIn("Integrated production accepted | `false`", package_phase_record)

        isolated_manifest = json.loads(isolated_proof_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(isolated_manifest["inherited_finding"], "B-001")
        self.assertEqual(
            isolated_manifest["status"],
            "review_ready_external_isolated_proof_recorded_no_closure",
        )
        self.assertFalse(isolated_manifest["closure_claimed"])
        self.assertFalse(isolated_manifest["p0_closure_claimed"])
        self.assertFalse(isolated_manifest["independent_review_signoff_present"])
        self.assertFalse(isolated_manifest["stage2_integrated_production_accepted"])
        self.assertEqual(isolated_manifest["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(isolated_manifest["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertTrue(isolated_manifest["external_proof"]["isolated_label"].startswith("com.linze.adp.b001.isolated."))
        self.assertEqual(isolated_manifest["external_proof"]["production_boundary"]["production_labels_touched"], [])
        self.assertFalse(isolated_manifest["external_proof"]["production_boundary"]["real_smtp_send_enabled_or_run"])
        self.assertFalse(isolated_manifest["external_proof"]["production_boundary"]["local_runner_daily_invoked"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["operation_sequence_complete"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["artifact_hashes_match"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["launchd_run_exit_0_observed"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["launchd_uninstall_not_found_observed"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["production_labels_not_touched"])
        self.assertEqual(isolated_manifest["reconciliation_summary"]["artifact_hash_mismatches"], [])

        independent_review = json.loads(independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(independent_review["finding_id"], "B-001")
        self.assertTrue(independent_review["technical_closure_candidate"])
        self.assertTrue(independent_review["external_isolated_launchd_proof_verified"])
        self.assertEqual(independent_review["artifact_hashes_checked"], 15)
        self.assertTrue(independent_review["artifact_hashes_match"])
        self.assertTrue(independent_review["operation_sequence_complete"])
        self.assertTrue(independent_review["launchd_run_exit_0_observed"])
        self.assertTrue(independent_review["launchd_uninstall_not_found_observed"])
        self.assertTrue(independent_review["isolated_label_not_loaded_now"])
        self.assertTrue(independent_review["isolated_plist_absent_now"])
        self.assertFalse(independent_review["p0_closure_claimed"])
        self.assertFalse(independent_review["p1_closure_claimed"])
        self.assertFalse(independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(independent_review["s2plt04_completed"])
        self.assertFalse(independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(independent_review["scheduler_install_enabled"])
        self.assertFalse(independent_review["real_smtp_sent"])

        a001_independent_review = json.loads(a001_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a001_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a001_independent_review["finding_id"], "A-001")
        self.assertTrue(a001_independent_review["technical_closure_candidate"])
        self.assertTrue(a001_independent_review["restore_path_safety_verified"])
        self.assertTrue(a001_independent_review["real_stage1_restore_probes_verified"])
        self.assertEqual(a001_independent_review["probe_count"], 4)
        self.assertTrue(a001_independent_review["path_traversal_blocked"])
        self.assertTrue(a001_independent_review["absolute_path_escape_blocked"])
        self.assertTrue(a001_independent_review["symlink_escape_blocked"])
        self.assertTrue(a001_independent_review["target_preserved_on_block"])
        self.assertTrue(a001_independent_review["false_pass_guard_verified"])
        self.assertFalse(a001_independent_review["p0_closure_claimed"])
        self.assertFalse(a001_independent_review["p1_closure_claimed"])
        self.assertFalse(a001_independent_review["closure_claimed"])
        self.assertFalse(a001_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a001_independent_review["s2plt04_completed"])
        self.assertFalse(a001_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a001_independent_review["production_restore_executed"])
        self.assertFalse(a001_independent_review["production_restore_enabled"])
        self.assertFalse(a001_independent_review["scheduler_install_enabled"])
        self.assertFalse(a001_independent_review["real_smtp_sent"])

        a002_independent_review = json.loads(a002_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a002_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a002_independent_review["finding_id"], "A-002")
        self.assertTrue(a002_independent_review["technical_closure_candidate"])
        self.assertTrue(a002_independent_review["restore_atomic_replacement_verified"])
        self.assertTrue(a002_independent_review["real_stage1_backup_restore_probes_verified"])
        self.assertEqual(a002_independent_review["probe_count"], 3)
        self.assertTrue(a002_independent_review["valid_restore_new_target_verified"])
        self.assertTrue(a002_independent_review["valid_overwrite_previous_backup_preserved"])
        self.assertTrue(a002_independent_review["invalid_overwrite_target_preserved"])
        self.assertTrue(a002_independent_review["temp_files_cleaned"])
        self.assertTrue(a002_independent_review["false_pass_guard_verified"])
        self.assertFalse(a002_independent_review["p0_closure_claimed"])
        self.assertFalse(a002_independent_review["p1_closure_claimed"])
        self.assertFalse(a002_independent_review["closure_claimed"])
        self.assertFalse(a002_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a002_independent_review["s2plt04_completed"])
        self.assertFalse(a002_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a002_independent_review["production_restore_executed"])
        self.assertFalse(a002_independent_review["production_restore_enabled"])
        self.assertFalse(a002_independent_review["production_side_effects_enabled"])
        self.assertFalse(a002_independent_review["scheduler_install_enabled"])
        self.assertFalse(a002_independent_review["real_scheduler_installed"])
        self.assertFalse(a002_independent_review["real_smtp_sent"])
        self.assertFalse(a002_independent_review["real_release_uploaded"])
        self.assertFalse(a002_independent_review["daily_operation_enabled"])
        self.assertFalse(a002_independent_review["public_schema_changed"])
        self.assertFalse(a002_independent_review["db_migration_executed"])
        self.assertFalse(a002_independent_review["queue_mutation_allowed"])
        self.assertFalse(a002_independent_review["current_pointer_changed"])
        self.assertFalse(a002_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a002_independent_review["v7_2_contract_files_changed"])

        a003_independent_review = json.loads(a003_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a003_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a003_independent_review["finding_id"], "A-003")
        self.assertTrue(a003_independent_review["technical_closure_candidate"])
        self.assertTrue(a003_independent_review["transactional_outbox_verified"])
        self.assertTrue(a003_independent_review["message_id_stability_verified"])
        self.assertTrue(a003_independent_review["changed_revision_rekeys_message_id"])
        self.assertTrue(a003_independent_review["outbox_claim_contention_verified"])
        self.assertEqual(a003_independent_review["claim_attempts"], 100)
        self.assertEqual(a003_independent_review["passed_claims"], 1)
        self.assertEqual(a003_independent_review["blocked_claims"], 99)
        self.assertTrue(a003_independent_review["smtp_accept_pending_commit_fail_closed_verified"])
        self.assertTrue(a003_independent_review["fail_closed_not_retry_safe_not_reclaimed_verified"])
        self.assertTrue(a003_independent_review["provider_accept_finalizes_without_resend_verified"])
        self.assertTrue(a003_independent_review["provider_finalized_not_reclaimed_verified"])
        self.assertTrue(a003_independent_review["at_least_once_with_idempotent_message_id_verified"])
        self.assertFalse(a003_independent_review["exactly_once_claimed"])
        self.assertTrue(a003_independent_review["false_pass_guard_verified"])
        self.assertFalse(a003_independent_review["p0_closure_claimed"])
        self.assertFalse(a003_independent_review["p1_closure_claimed"])
        self.assertFalse(a003_independent_review["closure_claimed"])
        self.assertFalse(a003_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a003_independent_review["s2plt04_completed"])
        self.assertFalse(a003_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a003_independent_review["production_side_effects_enabled"])
        self.assertFalse(a003_independent_review["scheduler_install_enabled"])
        self.assertFalse(a003_independent_review["real_scheduler_installed"])
        self.assertFalse(a003_independent_review["real_smtp_sent"])
        self.assertFalse(a003_independent_review["real_release_uploaded"])
        self.assertFalse(a003_independent_review["daily_operation_enabled"])
        self.assertFalse(a003_independent_review["public_schema_changed"])
        self.assertFalse(a003_independent_review["db_migration_executed"])
        self.assertFalse(a003_independent_review["queue_mutation_allowed"])
        self.assertFalse(a003_independent_review["source_adapter_changed"])
        self.assertFalse(a003_independent_review["ranking_algorithm_changed"])
        self.assertFalse(a003_independent_review["current_pointer_changed"])
        self.assertFalse(a003_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a003_independent_review["v7_2_contract_files_changed"])

        a004_independent_review = json.loads(a004_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a004_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a004_independent_review["finding_id"], "A-004")
        self.assertTrue(a004_independent_review["technical_closure_candidate"])
        self.assertTrue(a004_independent_review["typed_statement_schema_enforced"])
        self.assertTrue(a004_independent_review["evidence_binding_enforced"])
        self.assertTrue(a004_independent_review["unknown_claims_blocked"])
        self.assertTrue(a004_independent_review["unsupported_foreground_claims_blocked"])
        self.assertTrue(a004_independent_review["frontstage_no_production_side_effects_verified"])
        self.assertTrue(a004_independent_review["false_pass_guard_verified"])
        self.assertTrue(a004_independent_review["tampered_gate_blocks"])
        self.assertEqual(a004_independent_review["required_probe_count"], 5)
        self.assertFalse(a004_independent_review["p0_closure_claimed"])
        self.assertFalse(a004_independent_review["p1_closure_claimed"])
        self.assertFalse(a004_independent_review["closure_claimed"])
        self.assertFalse(a004_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a004_independent_review["s2plt04_completed"])
        self.assertFalse(a004_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a004_independent_review["production_side_effects_enabled"])
        self.assertFalse(a004_independent_review["scheduler_install_enabled"])
        self.assertFalse(a004_independent_review["real_scheduler_installed"])
        self.assertFalse(a004_independent_review["real_smtp_sent"])
        self.assertFalse(a004_independent_review["real_release_uploaded"])
        self.assertFalse(a004_independent_review["daily_operation_enabled"])
        self.assertFalse(a004_independent_review["public_schema_changed"])
        self.assertFalse(a004_independent_review["db_migration_executed"])
        self.assertFalse(a004_independent_review["queue_mutation_allowed"])
        self.assertFalse(a004_independent_review["current_pointer_changed"])
        self.assertFalse(a004_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a004_independent_review["v7_2_contract_files_changed"])

        a005_independent_review = json.loads(a005_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a005_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a005_independent_review["finding_id"], "A-005")
        self.assertTrue(a005_independent_review["technical_closure_candidate"])
        self.assertTrue(a005_independent_review["untrusted_source_content_verified"])
        self.assertTrue(a005_independent_review["safe_url_rendering_verified"])
        self.assertTrue(a005_independent_review["unsafe_url_schemes_blocked"])
        self.assertTrue(a005_independent_review["unsafe_hosts_blocked"])
        self.assertTrue(a005_independent_review["source_content_tool_requests_blocked"])
        self.assertTrue(a005_independent_review["secret_access_blocked"])
        self.assertTrue(a005_independent_review["repository_write_blocked"])
        self.assertTrue(a005_independent_review["email_send_blocked"])
        self.assertTrue(a005_independent_review["tool_and_secret_boundary_enforced"])
        self.assertTrue(a005_independent_review["trust_receipt_schema_enforced"])
        self.assertTrue(a005_independent_review["false_pass_guard_verified"])
        self.assertTrue(a005_independent_review["tampered_boundary_blocks"])
        self.assertEqual(a005_independent_review["required_probe_count"], 7)
        self.assertFalse(a005_independent_review["p0_closure_claimed"])
        self.assertFalse(a005_independent_review["p1_closure_claimed"])
        self.assertFalse(a005_independent_review["closure_claimed"])
        self.assertFalse(a005_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a005_independent_review["s2plt04_completed"])
        self.assertFalse(a005_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a005_independent_review["production_side_effects_enabled"])
        self.assertFalse(a005_independent_review["scheduler_install_enabled"])
        self.assertFalse(a005_independent_review["real_scheduler_installed"])
        self.assertFalse(a005_independent_review["real_smtp_sent"])
        self.assertFalse(a005_independent_review["real_release_uploaded"])
        self.assertFalse(a005_independent_review["daily_operation_enabled"])
        self.assertFalse(a005_independent_review["public_schema_changed"])
        self.assertFalse(a005_independent_review["db_migration_executed"])
        self.assertFalse(a005_independent_review["queue_mutation_allowed"])
        self.assertFalse(a005_independent_review["current_pointer_changed"])
        self.assertFalse(a005_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a005_independent_review["v7_2_contract_files_changed"])

        b007_independent_review = json.loads(b007_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(b007_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(b007_independent_review["finding_id"], "B-007")
        self.assertTrue(b007_independent_review["technical_closure_candidate"])
        self.assertTrue(b007_independent_review["multiprocess_race_harness_verified"])
        self.assertTrue(b007_independent_review["dual_scheduler_race_verified"])
        self.assertTrue(b007_independent_review["four_actor_sources_verified"])
        self.assertEqual(b007_independent_review["process_count"], 4)
        self.assertEqual(b007_independent_review["trigger_count"], 100)
        self.assertEqual(b007_independent_review["attempted_revisions"], 400)
        self.assertEqual(b007_independent_review["observed_active_revisions"], 4)
        self.assertEqual(b007_independent_review["observed_blocked_duplicate_attempts"], 396)
        self.assertTrue(b007_independent_review["one_active_revision_per_mail_product_verified"])
        self.assertTrue(b007_independent_review["reason_coded_duplicate_blocks_verified"])
        self.assertTrue(b007_independent_review["lease_fencing_receipts_verified"])
        self.assertTrue(b007_independent_review["scheduler_side_effects_absent"])
        self.assertTrue(b007_independent_review["false_pass_guard_verified"])
        self.assertFalse(b007_independent_review["p0_closure_claimed"])
        self.assertFalse(b007_independent_review["p1_closure_claimed"])
        self.assertFalse(b007_independent_review["closure_claimed"])
        self.assertFalse(b007_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b007_independent_review["s2plt04_completed"])
        self.assertFalse(b007_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(b007_independent_review["production_side_effects_enabled"])
        self.assertFalse(b007_independent_review["scheduler_install_enabled"])
        self.assertFalse(b007_independent_review["real_scheduler_installed"])
        self.assertFalse(b007_independent_review["real_smtp_sent"])
        self.assertFalse(b007_independent_review["real_release_uploaded"])
        self.assertFalse(b007_independent_review["daily_operation_enabled"])
        self.assertFalse(b007_independent_review["public_schema_changed"])
        self.assertFalse(b007_independent_review["db_migration_executed"])
        self.assertFalse(b007_independent_review["queue_mutation_allowed"])
        self.assertFalse(b007_independent_review["current_pointer_changed"])
        self.assertFalse(b007_independent_review["v7_1_baseline_changed"])
        self.assertFalse(b007_independent_review["v7_2_contract_files_changed"])

        b008_independent_review = json.loads(b008_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(b008_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(b008_independent_review["finding_id"], "B-008")
        self.assertTrue(b008_independent_review["technical_closure_candidate"])
        self.assertTrue(b008_independent_review["fake_smtp_crash_window_verified"])
        self.assertTrue(b008_independent_review["outbox_claimed_before_smtp_verified"])
        self.assertTrue(b008_independent_review["accepted_pending_commit_reproduced"])
        self.assertTrue(b008_independent_review["idempotent_message_identity_stable"])
        self.assertTrue(b008_independent_review["mail_key_stable"])
        self.assertTrue(b008_independent_review["message_id_stable"])
        self.assertTrue(b008_independent_review["changed_revision_rekeys_message_id"])
        self.assertTrue(b008_independent_review["resend_without_provider_ref_blocked"])
        self.assertTrue(b008_independent_review["provider_accept_ref_required_before_resolution"])
        self.assertTrue(b008_independent_review["provider_accept_ref_finalizes_without_resend"])
        self.assertTrue(b008_independent_review["durable_fake_provider_ref_finalizes_sent"])
        self.assertTrue(b008_independent_review["retry_safe_false_after_accept"])
        self.assertTrue(b008_independent_review["no_real_smtp_side_effect_verified"])
        self.assertTrue(b008_independent_review["false_pass_guard_verified"])
        self.assertFalse(b008_independent_review["p0_closure_claimed"])
        self.assertFalse(b008_independent_review["p1_closure_claimed"])
        self.assertFalse(b008_independent_review["closure_claimed"])
        self.assertFalse(b008_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b008_independent_review["s2plt04_completed"])
        self.assertFalse(b008_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(b008_independent_review["production_side_effects_enabled"])
        self.assertFalse(b008_independent_review["scheduler_install_enabled"])
        self.assertFalse(b008_independent_review["real_scheduler_installed"])
        self.assertFalse(b008_independent_review["real_smtp_sent"])
        self.assertFalse(b008_independent_review["real_release_uploaded"])
        self.assertFalse(b008_independent_review["daily_operation_enabled"])
        self.assertFalse(b008_independent_review["public_schema_changed"])
        self.assertFalse(b008_independent_review["db_migration_executed"])
        self.assertFalse(b008_independent_review["queue_mutation_allowed"])
        self.assertFalse(b008_independent_review["current_pointer_changed"])
        self.assertFalse(b008_independent_review["v7_1_baseline_changed"])
        self.assertFalse(b008_independent_review["v7_2_contract_files_changed"])

    def test_p1_review_receipt_uses_refreshed_current_evidence(self) -> None:
        receipt_path = REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_INDEPENDENT_REVIEW_RECEIPT.md"
        manifest_path = REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
        refresh_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C011-20260627.json"
        )
        a006_a009_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json"
        )
        a006_a009_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A006_A009_TECHNICAL_REVIEW.md"
        )
        a010_a016_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json"
        )
        a010_a016_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A010_A016_TECHNICAL_REVIEW.md"
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
            "A-019": ("PHASE_S2PMT01_ZERO_CRITICAL_CLAIM_A019.md", "ADP-S2PMT01-ZERO-CRITICAL-CLAIM-A019-20260627.json"),
            "A-020": ("PHASE_S2PMT01_SUPPLY_CHAIN_A020.md", "ADP-S2PMT01-SUPPLY-CHAIN-A020-20260626.json"),
            "A-021": ("PHASE_S2PAT05_ROADMAP_STOP_CODE_A021.md", "ADP-S2PAT05-ROADMAP-STOP-CODE-A021-20260626.json"),
            "B-002": ("PHASE_S2PMT04_PROCESS_LIFECYCLE_B002.md", "ADP-S2PMT04-PROCESS-LIFECYCLE-B002-20260627.json"),
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
            "C-001": (
                "PHASE_S2PIT01_SHALLOW_USER_CENTER_C001.md",
                "ADP-S2PIT01-SHALLOW-USER-CENTER-C001-20260627.json",
            ),
            "C-002": (
                "PHASE_S2PIT02_OWNER_STATUS_C002.md",
                "ADP-S2PIT02-OWNER-STATUS-C002-20260627.json",
            ),
            "C-003": (
                "PHASE_S2PIT05_FOUR_CHECK_FRESHNESS_C003.md",
                "ADP-S2PIT05-FOUR-CHECK-FRESHNESS-C003-20260627.json",
            ),
            "C-005": (
                "PHASE_S2PMT06_RECOVERABLE_ERROR_C005.md",
                "ADP-S2PMT06-RECOVERABLE-ERROR-C005-20260627.json",
            ),
            "C-006": (
                "PHASE_S2PMT06_SAFE_CONFIG_C006.md",
                "ADP-S2PMT06-SAFE-CONFIG-C006-20260627.json",
            ),
            "C-007": (
                "PHASE_S2PMT06_APPEND_ONLY_AUDIT_C007.md",
                "ADP-S2PMT06-APPEND-ONLY-AUDIT-C007-20260627.json",
            ),
            "C-010": (
                "PHASE_S2PAT05_TRACEABILITY_CHAIN_C010.md",
                "ADP-S2PAT05-TRACEABILITY-CHAIN-C010-20260627.json",
                "用户中心/功能任务测试证据追踪链.md",
            ),
            "C-011": (
                "PHASE_S2PAT05_LEGACY_MAIL_SCAN_C011.md",
                "ADP-S2PAT05-LEGACY-MAIL-SCAN-C011-20260627.json",
                "用户中心/旧邮件标识兼容扫描.md",
            ),
            "C-012": (
                "PHASE_S2PMT06_SAFE_MANUAL_ACTION_C012.md",
                "ADP-S2PMT06-SAFE-MANUAL-ACTION-C012-20260627.json",
            ),
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
            "A-019": ("PHASE_S2PMT01_SECURITY_BOUNDARY.md", "ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json"),
            "A-020": ("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json",),
            "A-021": ("PHASE_S2PAT02_PRODUCT_CONTRACT.md",),
            "B-002": ("PHASE_S2PMT04_LIFECYCLE_CACHE.md", "ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json"),
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
            "C-001": (
                "PHASE_S2PIT01_USER_CENTER.md",
                "ADP-S2PIT01-USER-CENTER-20260625.json",
                "docs/owner/00_用户中心/00_开始这里.md",
            ),
            "C-002": (
                "PHASE_S2PIT02_RUNTIME_DASHBOARD.md",
                "ADP-S2PIT02-RUNTIME-DASHBOARD-20260625.json",
                "docs/owner/00_用户中心/01_当前状态.md",
            ),
            "C-003": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-005": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-006": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-007": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-010": ("并行审查汇总与合并结论.md", "问题清单.csv"),
            "C-011": (
                "PHASE_S2PHT01V1_1_T01_EMAIL_PATH_AUDIT.md",
                "PHASE_S2PHT01V1_1_T02_T04_EMAIL_V1_RENDERER.md",
                "PHASE_S2PMT06_OWNER_UX.md",
                "并行审查汇总与合并结论.md",
                "问题清单.csv",
            ),
            "C-012": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
        }

        findings = {finding["finding_id"]: finding for finding in manifest["p1_findings"]}
        self.assertEqual(manifest["refreshed_findings"], list(expected_current_refs))
        self.assertEqual(
            manifest["refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertEqual(
            manifest["previous_refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-20260627.json",
            manifest["refresh_manifests"],
        )
        self.assertIn(manifest["refresh_manifest"], manifest["refresh_manifests"])
        self.assertTrue(refresh_manifest_path.exists())
        self.assertTrue(a006_a009_review_manifest_path.exists())
        self.assertTrue(a006_a009_review_phase_path.exists())
        self.assertTrue(a010_a016_review_manifest_path.exists())
        self.assertTrue(a010_a016_review_phase_path.exists())
        self.assertEqual(
            manifest["p1_technical_review_candidate_findings"],
            [
                "A-006",
                "A-007",
                "A-008",
                "A-009",
                "A-010",
                "A-011",
                "A-012",
                "A-013",
                "A-014",
                "A-015",
                "A-016",
            ],
        )
        self.assertEqual(
            manifest["p1_latest_technical_review_candidate_findings"],
            ["A-010", "A-011", "A-012", "A-013", "A-014", "A-015", "A-016"],
        )
        self.assertEqual(
            manifest["p1_technical_review_candidate_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
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
            if finding_id in {
                "A-006",
                "A-007",
                "A-008",
                "A-009",
                "A-010",
                "A-011",
                "A-012",
                "A-013",
                "A-014",
                "A-015",
                "A-016",
            }:
                self.assertEqual(
                    findings[finding_id]["technical_review_verdict"],
                    "PASS_WITH_NO_PRODUCTION_ACCEPTANCE",
                )
                expected_receipt = (
                    "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json"
                    if finding_id in {"A-006", "A-007", "A-008", "A-009"}
                    else "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json"
                )
                self.assertEqual(
                    findings[finding_id]["finding_level_technical_review_receipt"],
                    expected_receipt,
                )
                self.assertTrue(findings[finding_id]["technical_closure_candidate"])
                self.assertIn("finding_level_technical_review_passed", findings[finding_id]["preliminary_review_state"])
            else:
                self.assertIn("refreshed_current_evidence_located", findings[finding_id]["preliminary_review_state"])

        a006_a009_review = json.loads(a006_a009_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a006_a009_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(a006_a009_review["finding_ids"], ["A-006", "A-007", "A-008", "A-009"])
        self.assertFalse(a006_a009_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a006_a009_review["technical_review_checks"]["all_four_findings_present"])
        self.assertTrue(a006_a009_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(a006_a009_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertFalse(a006_a009_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a006_a009_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a006_a009_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a006_a009_review["p1_closure_claimed"])
        self.assertFalse(a006_a009_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a006_a009_review["stage2_integrated_production_accepted"])
        self.assertFalse(a006_a009_review["real_smtp_sent"])
        self.assertFalse(a006_a009_review["scheduler_install_enabled"])
        self.assertFalse(a006_a009_review["release_packaging_enabled"])
        self.assertFalse(a006_a009_review["production_restore_enabled"])
        self.assertFalse(a006_a009_review["current_pointer_changed"])
        self.assertFalse(a006_a009_review["v7_1_baseline_changed"])
        self.assertFalse(a006_a009_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a006_a009_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-006", "A-007", "A-008", "A-009"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        self.assertIn("A-006", a006_a009_review_phase_path.read_text(encoding="utf-8"))

        a010_a016_review = json.loads(a010_a016_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a010_a016_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(
            a010_a016_review["finding_ids"],
            ["A-010", "A-011", "A-012", "A-013", "A-014", "A-015", "A-016"],
        )
        self.assertFalse(a010_a016_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a010_a016_review["technical_review_checks"]["all_seven_findings_present"])
        self.assertTrue(a010_a016_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(a010_a016_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertFalse(a010_a016_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a010_a016_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a010_a016_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a010_a016_review["p1_closure_claimed"])
        self.assertFalse(a010_a016_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a010_a016_review["stage2_integrated_production_accepted"])
        self.assertFalse(a010_a016_review["real_smtp_sent"])
        self.assertFalse(a010_a016_review["scheduler_install_enabled"])
        self.assertFalse(a010_a016_review["release_packaging_enabled"])
        self.assertFalse(a010_a016_review["production_restore_enabled"])
        self.assertFalse(a010_a016_review["current_pointer_changed"])
        self.assertFalse(a010_a016_review["v7_1_baseline_changed"])
        self.assertFalse(a010_a016_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a010_a016_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-010", "A-011", "A-012", "A-013", "A-014", "A-015", "A-016"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        self.assertIn("A-010", a010_a016_review_phase_path.read_text(encoding="utf-8"))

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
