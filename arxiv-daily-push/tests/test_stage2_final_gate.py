from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_final_gate import (
    S2PLT04_BLOCKING_REASONS,
    S2PLT04_FORBIDDEN_FLAGS,
    S2PLT04_REQUIRED_DEPENDENCIES,
    S2PLT04_REQUIRED_EVIDENCE,
    S2PMT07_BLOCKING_REASONS,
    S2PMT07_FORBIDDEN_PASS_FLAGS,
    S2PMT07_REQUIRED_DEPENDENCIES,
    S2PMT07_REQUIRED_EVIDENCE,
    S2PMT07_REQUIRED_TEST_COMMANDS,
    build_s2plt04_dependency_state,
    build_s2plt04_evidence_state,
    build_s2plt04_integration_candidate_report,
    build_audit_blocker_state,
    build_dependency_state,
    build_evidence_bundle_state,
    build_reviewer_independence_state,
    build_s2pmt07_precheck_report,
    build_test_gate_state,
    validate_s2plt04_integration_candidate_report,
    validate_s2pmt07_precheck_report,
)


class Stage2FinalGateTests(unittest.TestCase):
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
        self.assertEqual(validate_s2pmt07_precheck_report(report), [])

        tampered = dict(report)
        tampered["integrated_production_accepted"] = True
        self.assertIn("integrated_production_accepted must be false", validate_s2pmt07_precheck_report(tampered))


if __name__ == "__main__":
    unittest.main()
