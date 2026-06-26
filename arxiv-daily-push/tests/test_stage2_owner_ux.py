from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_owner_ux import (
    S2PMT06_PRODUCTION_FALSE_FLAGS,
    S2PMT06_REQUIRED_FINDINGS,
    S2PMT06_REQUIRED_NAV_ITEMS,
    S2PMT06_REQUIRED_STATUS_STATES,
    S2PMT06_SAFE_ACTIONS,
    S2PMT06_SAFE_EDIT_STEPS,
    build_accessibility_matrix,
    build_error_card,
    build_navigation_contract,
    build_owner_first_screen,
    build_queue_view_contract,
    build_s2pmt06_c005_recoverable_error_report,
    build_s2pmt06_c006_safe_config_report,
    build_s2pmt06_c007_append_only_audit_report,
    build_s2pmt06_c012_safe_manual_action_report,
    build_s2pmt06_report,
    build_safe_action_preview,
    build_safe_config_change,
    build_status_state_matrix,
    validate_error_card,
    validate_s2pmt06_c005_recoverable_error_report,
    validate_s2pmt06_c006_safe_config_report,
    validate_s2pmt06_c007_append_only_audit_report,
    validate_s2pmt06_c012_safe_manual_action_report,
    validate_s2pmt06_report,
)


class Stage2OwnerUXTests(unittest.TestCase):
    def test_first_screen_has_required_owner_fields_without_production_claims(self) -> None:
        screen = build_owner_first_screen(generated_at="2026-06-26T16:00:00+10:00")
        fields = screen["fields"]

        self.assertEqual(screen["status"], "pass")
        self.assertTrue(screen["production_disclaimer_visible"])
        self.assertTrue(screen["no_empty_table_as_status"])
        self.assertEqual(fields["current_stage_phase_task"], "Stage2 / S2PM / S2PMT06")
        self.assertEqual(fields["inherited_p0_p1"]["p0"], 8)
        self.assertEqual(fields["inherited_p0_p1"]["p1"], 37)
        self.assertFalse(fields["inherited_p0_p1"]["closed_by_this_task"])
        self.assertEqual(fields["today_3_plus_1_mail"], "local_preview_only_no_send")

    def test_navigation_contract_has_top_bottom_breadcrumb_and_trace_chain(self) -> None:
        navigation = build_navigation_contract()
        labels = [page["label"] for page in navigation["pages"]]

        self.assertEqual(navigation["status"], "pass")
        self.assertEqual(labels, list(S2PMT06_REQUIRED_NAV_ITEMS))
        for page in navigation["pages"]:
            self.assertEqual(page["top_navigation"], list(S2PMT06_REQUIRED_NAV_ITEMS))
            self.assertEqual(page["bottom_navigation"], list(S2PMT06_REQUIRED_NAV_ITEMS))
            self.assertEqual(page["breadcrumb"], ["00_用户中心", page["label"]])
            self.assertGreaterEqual(len(page["related_links"]), 2)
        self.assertEqual(navigation["object_trace_chain"], ["source", "claim", "report", "mail", "review", "action", "roi"])

    def test_status_state_matrix_covers_all_non_happy_path_states(self) -> None:
        matrix = build_status_state_matrix()

        self.assertEqual(matrix["status"], "pass")
        self.assertEqual(set(matrix["states"]), set(S2PMT06_REQUIRED_STATUS_STATES))
        for state in S2PMT06_REQUIRED_STATUS_STATES:
            self.assertIn("reason", matrix["states"][state])
            self.assertIn("owner_next_action", matrix["states"][state])
            self.assertFalse(matrix["states"][state]["empty_table_used_as_status"])

    def test_error_card_has_recovery_owner_runbook_evidence_and_cta(self) -> None:
        card = build_error_card()

        self.assertEqual(validate_error_card(card), [])
        self.assertEqual(card["severity"], "P1")
        self.assertTrue(card["retry_safe"])
        self.assertIn("runbook", card)
        self.assertIn("evidence", card)

        tampered = dict(card)
        tampered.pop("cta")
        self.assertIn("error_card.cta is required", validate_error_card(tampered))

    def test_safe_config_change_uses_preview_to_rollback_and_append_only_receipt(self) -> None:
        change = build_safe_config_change(generated_at="2026-06-26T16:00:00+10:00")

        self.assertEqual(change["status"], "pass")
        self.assertEqual(tuple(change["steps"]), S2PMT06_SAFE_EDIT_STEPS)
        self.assertTrue(change["confirmation_required"])
        self.assertFalse(change["apply"]["production_mutation_applied"])
        self.assertEqual(len(change["append_only_revision_ledger"]), 1)
        self.assertTrue(change["rollback"]["verified"])

    def test_queue_view_supports_search_filter_sort_export_and_drilldown_without_mutation(self) -> None:
        queue_view = build_queue_view_contract()

        self.assertEqual(queue_view["status"], "pass")
        self.assertIn("cycle_id", queue_view["search_fields"])
        self.assertIn("status", queue_view["filters"])
        self.assertEqual(set(queue_view["exports"]), {"json", "csv"})
        self.assertEqual(queue_view["drilldown_trace"], ["queue_item", "source", "claim", "report", "mail", "review", "action", "roi"])
        self.assertFalse(queue_view["production_queue_mutation_allowed"])

    def test_safe_manual_actions_are_previewed_and_receipted_without_production_mutation(self) -> None:
        for action in S2PMT06_SAFE_ACTIONS:
            preview = build_safe_action_preview(action=action)
            with self.subTest(action=action):
                self.assertEqual(preview["status"], "pass")
                self.assertTrue(preview["preview_required"])
                self.assertTrue(preview["confirmation_required"])
                self.assertTrue(preview["receipt_required"])
                self.assertFalse(preview["production_mutation_applied"])

        blocked = build_safe_action_preview(action="delete")
        self.assertEqual(blocked["status"], "blocked")

    def test_c005_report_requires_recoverable_p1_error_with_safe_retry_gate(self) -> None:
        report = build_s2pmt06_c005_recoverable_error_report(generated_at="2026-06-27T06:08:55+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "C-005")
        self.assertEqual(report["subtask_id"], "S2PMT06-RECOVERABLE-ERROR-C005")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        self.assertFalse(report["independent_review_signoff_present"])
        for flag in S2PMT06_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        card = report["p0_p1_error_cards"][0]
        self.assertEqual(card["severity"], "P1")
        self.assertTrue(card["owner"])
        self.assertTrue(card["runbook"])
        self.assertGreaterEqual(len(card["evidence"]), 1)
        self.assertTrue(card["cta"])
        retry = report["safe_actions"]["retry"]
        self.assertEqual(retry["status"], "pass")
        self.assertTrue(retry["preview_required"])
        self.assertTrue(retry["confirmation_required"])
        self.assertTrue(retry["receipt_required"])
        self.assertFalse(retry["production_mutation_applied"])
        self.assertEqual(validate_s2pmt06_c005_recoverable_error_report(report), [])

    def test_c005_report_blocks_missing_owner_or_unsafe_retry(self) -> None:
        report = build_s2pmt06_c005_recoverable_error_report(generated_at="2026-06-27T06:08:55+10:00")
        tampered = dict(report)
        tampered["p0_p1_error_cards"] = [dict(report["p0_p1_error_cards"][0], owner="")]

        owner_errors = validate_s2pmt06_c005_recoverable_error_report(tampered)
        self.assertIn("p0_p1_error_cards[0] must include owner, runbook, evidence, cta, and retry_safe", owner_errors)

        unsafe = build_s2pmt06_c005_recoverable_error_report(generated_at="2026-06-27T06:08:55+10:00")
        unsafe["safe_actions"]["retry"] = dict(unsafe["safe_actions"]["retry"], production_mutation_applied=True)
        retry_errors = validate_s2pmt06_c005_recoverable_error_report(unsafe)
        self.assertIn("safe_actions.retry must be a no-production safe retry preview with confirmation and receipt", retry_errors)

    def test_c006_report_requires_preview_diff_validation_rollback_and_no_mutation(self) -> None:
        report = build_s2pmt06_c006_safe_config_report(generated_at="2026-06-27T06:19:53+10:00")
        change = report["safe_config_change"]

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "C-006")
        self.assertEqual(report["subtask_id"], "S2PMT06-SAFE-CONFIG-C006")
        self.assertTrue(change["preview"])
        self.assertEqual(change["diff_impact"]["before"], 3)
        self.assertEqual(change["diff_impact"]["after"], 4)
        self.assertGreaterEqual(len(change["diff_impact"]["impact"]), 1)
        self.assertEqual(change["validation"]["status"], "pass")
        self.assertTrue(change["confirmation_required"])
        self.assertTrue(change["rollback"]["verified"])
        self.assertEqual(change["rollback"]["token"], change["receipt"]["rollback_token"])
        self.assertFalse(change["apply"]["production_mutation_applied"])
        self.assertFalse(change["receipt"]["applied_to_runtime"])
        for flag in S2PMT06_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        self.assertEqual(validate_s2pmt06_c006_safe_config_report(report), [])

    def test_c006_report_blocks_missing_diff_or_production_mutation(self) -> None:
        report = build_s2pmt06_c006_safe_config_report(generated_at="2026-06-27T06:19:53+10:00")
        no_diff = dict(report)
        no_diff["safe_config_change"] = dict(report["safe_config_change"], diff_impact={})
        self.assertIn(
            "safe_config_change.diff_impact must include before, after, and impact",
            validate_s2pmt06_c006_safe_config_report(no_diff),
        )

        mutating = build_s2pmt06_c006_safe_config_report(generated_at="2026-06-27T06:19:53+10:00")
        mutating["safe_config_change"]["apply"] = dict(
            mutating["safe_config_change"]["apply"],
            production_mutation_applied=True,
        )
        self.assertIn(
            "safe_config_change must not apply production mutation or runtime config changes",
            validate_s2pmt06_c006_safe_config_report(mutating),
        )

    def test_c007_report_requires_append_only_revision_and_result_binding(self) -> None:
        report = build_s2pmt06_c007_append_only_audit_report(generated_at="2026-06-27T06:19:53+10:00")
        revision = report["revision_ledger"][0]

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "C-007")
        self.assertEqual(report["subtask_id"], "S2PMT06-APPEND-ONLY-AUDIT-C007")
        self.assertTrue(revision["revision_id"])
        self.assertTrue(revision["before_hash"])
        self.assertTrue(revision["after_hash"])
        self.assertTrue(revision["rollback_token"])
        self.assertFalse(revision["applied_to_runtime"])
        self.assertEqual(report["result_artifact"]["config_revision_id"], revision["revision_id"])
        self.assertTrue(report["result_artifact"]["artifact_uses_revision"])
        self.assertFalse(report["result_artifact"]["runtime_applied"])
        for flag in S2PMT06_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        self.assertEqual(validate_s2pmt06_c007_append_only_audit_report(report), [])

    def test_c007_report_blocks_missing_revision_or_result_revision_mismatch(self) -> None:
        report = build_s2pmt06_c007_append_only_audit_report(generated_at="2026-06-27T06:19:53+10:00")
        missing_revision = dict(report)
        missing_revision["revision_ledger"] = []
        self.assertIn(
            "revision_ledger must contain at least one append-only revision",
            validate_s2pmt06_c007_append_only_audit_report(missing_revision),
        )

        mismatch = build_s2pmt06_c007_append_only_audit_report(generated_at="2026-06-27T06:19:53+10:00")
        mismatch["result_artifact"] = dict(mismatch["result_artifact"], config_revision_id="CFGREV-WRONG")
        self.assertIn(
            "result_artifact must record the latest config revision id",
            validate_s2pmt06_c007_append_only_audit_report(mismatch),
        )

    def test_c012_report_requires_safe_manual_actions_and_no_mutation(self) -> None:
        report = build_s2pmt06_c012_safe_manual_action_report(generated_at="2026-06-27T06:34:47+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "C-012")
        self.assertEqual(report["subtask_id"], "S2PMT06-SAFE-MANUAL-ACTION-C012")
        self.assertEqual(set(report["safe_actions"]), set(S2PMT06_SAFE_ACTIONS))
        self.assertEqual(report["unsupported_action_probe"]["status"], "blocked")
        self.assertFalse(report["duplicate_click_policy"]["duplicate_click_creates_new_send"])
        self.assertFalse(report["duplicate_click_policy"]["duplicate_click_creates_new_queue_mutation"])
        self.assertTrue(report["duplicate_click_policy"]["receipt_reused"])
        self.assertEqual(len(report["illegal_state_matrix"]), len(S2PMT06_SAFE_ACTIONS))
        for action, preview in report["safe_actions"].items():
            with self.subTest(action=action):
                self.assertEqual(preview["status"], "pass")
                self.assertTrue(preview["idempotency_key"])
                self.assertTrue(preview["allowed_current_states"])
                self.assertTrue(preview["preview_required"])
                self.assertTrue(preview["impact_visible"])
                self.assertTrue(preview["confirmation_required"])
                self.assertTrue(preview["receipt_required"])
                self.assertFalse(preview["production_mutation_applied"])
        for flag in S2PMT06_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        self.assertEqual(validate_s2pmt06_c012_safe_manual_action_report(report), [])

    def test_c012_report_blocks_missing_action_duplicate_key_or_mutation(self) -> None:
        report = build_s2pmt06_c012_safe_manual_action_report(generated_at="2026-06-27T06:34:47+10:00")
        missing_action = dict(report)
        missing_action["safe_actions"] = dict(report["safe_actions"])
        missing_action["safe_actions"].pop("retry")
        self.assertIn("safe_actions.retry is required", validate_s2pmt06_c012_safe_manual_action_report(missing_action))

        duplicate_key = build_s2pmt06_c012_safe_manual_action_report(generated_at="2026-06-27T06:34:47+10:00")
        duplicate_key["safe_actions"]["cancel"] = dict(
            duplicate_key["safe_actions"]["cancel"],
            idempotency_key=duplicate_key["safe_actions"]["retry"]["idempotency_key"],
        )
        self.assertIn(
            "safe_actions idempotency_key values must be unique",
            validate_s2pmt06_c012_safe_manual_action_report(duplicate_key),
        )

        mutating = build_s2pmt06_c012_safe_manual_action_report(generated_at="2026-06-27T06:34:47+10:00")
        mutating["safe_actions"]["requeue"] = dict(mutating["safe_actions"]["requeue"], production_mutation_applied=True)
        self.assertIn(
            "safe_actions.requeue must not mutate production queue or send mail",
            validate_s2pmt06_c012_safe_manual_action_report(mutating),
        )

    def test_accessibility_matrix_covers_a11y_responsive_and_mail_client_requirements(self) -> None:
        matrix = build_accessibility_matrix()
        checks = matrix["checks"]

        self.assertEqual(matrix["status"], "pass")
        self.assertGreaterEqual(checks["contrast_ratio"], 4.5)
        self.assertGreaterEqual(checks["touch_target_px"], 44)
        self.assertTrue(checks["plain_text_equivalent"])
        self.assertEqual(set(checks["mail_clients"]), {"gmail", "apple_mail", "outlook"})

    def test_full_s2pmt06_report_validates_findings_and_no_production_side_effects(self) -> None:
        report = build_s2pmt06_report(generated_at="2026-06-26T16:00:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        self.assertEqual(set(report["findings_covered"]), set(S2PMT06_REQUIRED_FINDINGS))
        for flag in S2PMT06_PRODUCTION_FALSE_FLAGS:
            self.assertFalse(report[flag])
        self.assertEqual(validate_s2pmt06_report(report), [])

        tampered = dict(report)
        tampered["real_smtp_sent"] = True
        self.assertIn("real_smtp_sent must be false", validate_s2pmt06_report(tampered))


if __name__ == "__main__":
    unittest.main()
