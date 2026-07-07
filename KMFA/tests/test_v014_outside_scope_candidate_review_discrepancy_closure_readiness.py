from __future__ import annotations

import json
import subprocess
import unittest

from KMFA.tools import v014_outside_scope_candidate_review_discrepancy_closure_readiness as generator
from KMFA.tools.check_v014_outside_scope_candidate_review_discrepancy_closure_readiness import validate


class DiscrepancyClosureReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
            write_governance_event=False,
        )
        cls.summary = cls.manifest["summary"]

    def test_closure_readiness_counts_lock_blockers(self) -> None:
        self.assertEqual(self.summary["source_discrepancy_queue_item_count"], 72)
        self.assertEqual(self.summary["closure_plan_item_count"], 72)
        self.assertEqual(self.summary["closure_ready_item_count"], 0)
        self.assertEqual(self.summary["closure_blocked_item_count"], 72)
        self.assertEqual(self.summary["safe_auto_closure_count"], 0)
        self.assertEqual(self.summary["ambiguous_tie_closure_blocker_count"], 24)
        self.assertEqual(self.summary["no_context_candidate_closure_blocker_count"], 40)
        self.assertEqual(self.summary["non_numeric_or_calculation_closure_blocker_count"], 8)

    def test_downstream_gates_remain_closed(self) -> None:
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertFalse(self.summary["source_map_correction_ready"])
        self.assertFalse(self.summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(self.summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(self.summary["business_value_consistency_verified"])
        self.assertFalse(self.summary["github_upload_performed"])
        self.assertFalse(self.summary["app_reinstall_performed"])
        self.assertFalse(self.summary["business_execution_performed"])

    def test_raw_inbox_not_accessed_or_mutated(self) -> None:
        raw_boundary = self.summary["raw_boundary"]
        self.assertTrue(raw_boundary["user_declared_raw_data_immutable"])
        self.assertTrue(raw_boundary["source_private_discrepancy_queue_read_by_this_phase"])
        self.assertFalse(raw_boundary["source_private_discrepancy_queue_mutated_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

    def test_private_closure_workpack_is_ignored(self) -> None:
        for private_path in (
            generator.PRIVATE_RECORD_PATH,
            generator.PRIVATE_ITEMS_PATH,
            generator.PRIVATE_BLOCKING_QUEUE_PATH,
            generator.PRIVATE_DIAGNOSTIC_PATH,
            generator.PRIVATE_WORKPACK_PATH,
        ):
            self.assertTrue(private_path.exists())
            result = subprocess.run(["git", "check-ignore", "-q", private_path.as_posix()], check=False)
            self.assertEqual(result.returncode, 0)
        rows = [
            json.loads(line)
            for line in generator.PRIVATE_BLOCKING_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 72)
        self.assertTrue(all(row["closure_ready"] is False for row in rows))

    def test_validator_passes_with_private_readiness(self) -> None:
        validate(require_private_readiness=True)


if __name__ == "__main__":
    unittest.main()
