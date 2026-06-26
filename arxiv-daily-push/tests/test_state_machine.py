from __future__ import annotations

import unittest

from arxiv_daily_push.state_machine import initial_run_record, transition_run_record, validate_run_record


class StateMachineTests(unittest.TestCase):
    def test_run_record_initial_state_is_valid(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")

        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["row_version"], 0)
        self.assertEqual(record["state_history"][0]["at"], "2026-06-21T00:00:00+10:00")
        self.assertEqual(validate_run_record(record), [])

    def test_transition_appends_history_and_sets_running_status(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        updated = transition_run_record(record, "health_checked", reason="doctor pass", at="2026-06-21T04:45:00+10:00")

        self.assertEqual(updated["current_state"], "health_checked")
        self.assertEqual(updated["status"], "running")
        self.assertEqual(updated["row_version"], 1)
        self.assertEqual(updated["state_history"][-1]["from_state"], "created")
        self.assertEqual(updated["state_history"][-1]["to_state"], "health_checked")
        self.assertEqual(record["current_state"], "created")

    def test_transition_rejects_skipped_state(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")

        with self.assertRaisesRegex(ValueError, "not allowed"):
            transition_run_record(record, "evidence_bound", reason="skip", at="2026-06-21T05:00:00+10:00")

    def test_validate_run_record_rejects_forged_history_from_state(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        record["current_state"] = "source_collected"
        record["state_history"].append(
            {
                "from_state": "created",
                "to_state": "source_collected",
                "reason": "forged skip",
                "at": "2026-06-21T05:00:00+10:00",
            }
        )

        errors = validate_run_record(record)

        self.assertIn("RunRecord.state_history[1] transition created -> source_collected is not allowed", errors)

    def test_validate_run_record_rejects_current_state_history_drift(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        updated = transition_run_record(record, "health_checked", reason="doctor pass", at="2026-06-21T04:45:00+10:00")
        updated["current_state"] = "source_collected"

        errors = validate_run_record(updated)

        self.assertIn("RunRecord.current_state must match state_history last to_state", errors)

    def test_validate_run_record_rejects_status_drift_from_current_state(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        running = transition_run_record(record, "health_checked", reason="doctor pass", at="2026-06-21T04:45:00+10:00")
        running["status"] = "succeeded"

        errors = validate_run_record(running)

        self.assertIn("RunRecord.status must be running when current_state is health_checked", errors)

        completed = transition_run_record(running | {"status": "running"}, "source_collected", reason="source ready", at="2026-06-21T04:46:00+10:00")
        completed = transition_run_record(completed, "evidence_bound", reason="evidence ready", at="2026-06-21T04:47:00+10:00")
        completed = transition_run_record(completed, "lesson_ready", reason="lesson ready", at="2026-06-21T04:48:00+10:00")
        completed = transition_run_record(completed, "publication_ready", reason="publication ready", at="2026-06-21T04:49:00+10:00")
        completed = transition_run_record(completed, "completed", reason="done", at="2026-06-21T04:50:00+10:00")
        completed["status"] = "blocked"

        errors = validate_run_record(completed)

        self.assertIn("RunRecord.status must be degraded, succeeded when current_state is completed", errors)

    def test_validate_run_record_rejects_schema_or_row_version_drift(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        updated = transition_run_record(record, "health_checked", reason="doctor pass", at="2026-06-21T04:45:00+10:00")
        updated["schema_version"] = 2
        updated["row_version"] = 99

        errors = validate_run_record(updated)

        self.assertIn("RunRecord.schema_version must be 1", errors)
        self.assertIn("RunRecord.row_version must equal state_history transition count", errors)

    def test_validate_run_record_rejects_missing_history_reason_or_at(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        record["state_history"][0]["reason"] = ""
        record["state_history"][0]["at"] = ""

        errors = validate_run_record(record)

        self.assertIn("RunRecord.state_history[0].reason is required", errors)
        self.assertIn("RunRecord.state_history[0].at is required", errors)

    def test_validate_run_record_rejects_unparseable_or_decreasing_history_at(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        updated = transition_run_record(record, "health_checked", reason="doctor pass", at="2026-06-21T04:45:00+10:00")
        updated = transition_run_record(updated, "source_collected", reason="source ready", at="2026-06-21T04:44:59+10:00")

        errors = validate_run_record(updated)

        self.assertIn("RunRecord.state_history[2].at must be non-decreasing", errors)

        updated["state_history"][2]["at"] = "not-a-time"
        errors = validate_run_record(updated)

        self.assertIn("RunRecord.state_history[2].at must be an ISO timestamp", errors)

    def test_validate_run_record_checks_nested_contracts(self) -> None:
        record = initial_run_record("run-001", "2026-06-21", "Australia/Sydney")
        record["source_items"].append({"source_type": "arxiv"})

        errors = validate_run_record(record)

        self.assertIn("SourceItem.source_id is required", errors)


if __name__ == "__main__":
    unittest.main()
