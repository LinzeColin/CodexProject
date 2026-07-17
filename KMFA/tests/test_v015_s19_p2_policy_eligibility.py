from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s19_p2_policy_eligibility as subject


class PolicyEligibilityTests(unittest.TestCase):
    def test_registry_uses_versioned_official_sources(self) -> None:
        rows = subject.policy_registry()
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(row["rule_use_allowed"] for row in rows), 5)
        self.assertTrue(all(row["rule_version"] and row["source_date"] and row["source_url"].startswith("https://") for row in rows))
        self.assertTrue(all(row["eligibility_conclusion"] is None for row in rows))

    def test_overdue_and_superseded_rules_never_conclude(self) -> None:
        future = subject.policy_registry("2026-10-15")
        self.assertEqual(sum(row["refresh_state"] == "REVIEW_OVERDUE" for row in future), 5)
        self.assertTrue(all(not row["rule_use_allowed"] for row in future))
        legacy = next(row for row in future if row["policy_id"] == "POLICY-HIGH-TECH-LEGACY")
        self.assertEqual(legacy["refresh_state"], "BLOCKED_SUPERSEDED")
        self.assertIsNone(legacy["eligibility_conclusion"])

    def test_evidence_is_exactly_scoped_and_never_fabricated(self) -> None:
        rows = subject.evidence_items("demo-west", "2026-Q2")
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(row["status"] == "AVAILABLE" for row in rows), 7)
        self.assertEqual(sum(row["status"] == "MISSING" for row in rows), 3)
        self.assertEqual(sum(row["status"] == "REVIEW_REQUIRED" for row in rows), 2)
        self.assertTrue(all(row["company_id"] == "demo-west" and row["period"] == "2026-Q2" for row in rows))
        self.assertTrue(all(not row["fabricated"] and not row["packaged_material"] for row in rows))

    def test_readiness_only_reports_gaps_and_risks(self) -> None:
        value = subject.policy_view()
        self.assertEqual(len(value["readiness_categories"]), 6)
        self.assertEqual(value["policy_readiness"]["status"], "GAPS_AND_RISKS")
        self.assertIsNone(value["policy_readiness"]["eligibility_conclusion"])
        self.assertEqual(value["formal_eligibility_conclusion_count"], 0)
        self.assertEqual(value["fabricated_evidence_count"], 0)
        self.assertEqual(value["material_packaging_assistance_count"], 0)

    def test_tasks_have_owner_due_date_target_and_source_gate(self) -> None:
        rows = subject.task_definitions()
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["owner_zh"] and row["due_date"] and row["target_location_ref"] for row in rows))
        self.assertEqual(sum(row["status"] == "MISSING_SOURCE" for row in rows), 3)
        self.assertEqual(sum(row["status"] == "SOURCE_REVIEW" for row in rows), 2)
        self.assertEqual(sum(row["status"] == "READY_TO_COMPLETE" for row in rows), 1)

    def test_no_source_mismatch_and_unverified_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.PolicyTaskJournal(Path(directory) / "tasks.jsonl")
            common = dict(company_id="demo-north", period="2026-07", actor_ref="public-demo-owner", idempotency_key="idem-1")
            with self.assertRaisesRegex(subject.PolicyEligibilityError, "无来源材料"):
                subject.complete_policy_task(journal, task_id="POLTASK-001", source_evidence_ref="", **common)
            with self.assertRaisesRegex(subject.PolicyEligibilityError, "不匹配"):
                subject.complete_policy_task(journal, task_id="POLTASK-006", source_evidence_ref="wrong", **common)
            review_ref = next(row["source_ref"] for row in subject.evidence_items() if row["evidence_id"] == "EVD-PEOPLE-002")
            with self.assertRaisesRegex(subject.PolicyEligibilityError, "尚未核验"):
                subject.complete_policy_task(journal, task_id="POLTASK-002", source_evidence_ref=review_ref, **common)
            self.assertEqual(journal.read(), [])

    def test_verified_source_completes_once_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.PolicyTaskJournal(Path(directory) / "tasks.jsonl")
            source = next(row["source_ref"] for row in subject.evidence_items() if row["evidence_id"] == "EVD-RD-001")
            common = dict(task_id="POLTASK-006", company_id="demo-north", period="2026-07", source_evidence_ref=source, actor_ref="public-demo-owner", idempotency_key="idem-6")
            first = subject.complete_policy_task(journal, **common)
            second = subject.complete_policy_task(journal, **common)
            self.assertFalse(first["idempotent_replay"])
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(len(journal.read()), 1)
            rows = subject.task_list("demo-north", "2026-07", journal.read())
            self.assertEqual(next(row for row in rows if row["task_id"] == "POLTASK-006")["status"], "COMPLETED")

    def test_completion_does_not_leak_across_company_or_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.PolicyTaskJournal(Path(directory) / "tasks.jsonl")
            source = next(row["source_ref"] for row in subject.evidence_items() if row["evidence_id"] == "EVD-RD-001")
            subject.complete_policy_task(journal, task_id="POLTASK-006", company_id="demo-north", period="2026-07", source_evidence_ref=source, actor_ref="owner", idempotency_key="scope")
            west = subject.task_list("demo-west", "2026-07", journal.read())
            q2 = subject.task_list("demo-north", "2026-Q2", journal.read())
            self.assertEqual(next(row for row in west if row["task_id"] == "POLTASK-006")["status"], "READY_TO_COMPLETE")
            self.assertEqual(next(row for row in q2 if row["task_id"] == "POLTASK-006")["status"], "READY_TO_COMPLETE")

    def test_public_contract_has_exactly_eighty_passes(self) -> None:
        rows = subject.public_checks()
        self.assertEqual(len(rows), 80)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))


if __name__ == "__main__":
    unittest.main()
