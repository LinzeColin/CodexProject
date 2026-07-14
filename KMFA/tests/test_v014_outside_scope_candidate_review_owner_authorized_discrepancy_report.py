from __future__ import annotations

import json
import subprocess
import unittest

from KMFA.tools import v014_outside_scope_candidate_review_owner_authorized_discrepancy_report as generator
from KMFA.tools.check_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report import validate


class OwnerAuthorizedDiscrepancyReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
            write_governance_event=False,
        )
        cls.summary = cls.manifest["summary"]

    def test_summary_counts_lock_unresolved_items(self) -> None:
        self.assertEqual(self.summary["source_review_item_count"], 72)
        self.assertEqual(self.summary["auto_ambiguous_item_count"], 24)
        self.assertEqual(self.summary["ambiguous_tied_candidate_item_count"], 24)
        self.assertEqual(self.summary["auto_unmatched_item_count"], 40)
        self.assertEqual(self.summary["non_numeric_or_calculation_item_count"], 8)
        self.assertEqual(self.summary["discrepancy_queue_item_count"], 72)
        self.assertEqual(self.summary["safe_auto_resolution_count"], 0)

    def test_downstream_gates_remain_closed(self) -> None:
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertFalse(self.summary["source_map_correction_ready"])
        self.assertFalse(self.summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(self.summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(self.summary["business_value_consistency_verified"])
        self.assertFalse(self.summary["github_upload_performed"])

    def test_raw_inbox_not_accessed_or_mutated(self) -> None:
        raw_boundary = self.summary["raw_boundary"]
        self.assertTrue(raw_boundary["user_declared_raw_data_immutable"])
        self.assertFalse(raw_boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

    def test_private_discrepancy_queue_is_ignored(self) -> None:
        private_path = generator.PRIVATE_QUEUE_PATH
        self.assertTrue(private_path.exists())
        result = subprocess.run(["git", "check-ignore", "-q", private_path.as_posix()], check=False)
        self.assertEqual(result.returncode, 0)
        rows = [json.loads(line) for line in private_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 72)
        self.assertTrue(all(row["safe_auto_resolution_available"] is False for row in rows))

    def test_validator_passes_with_private_discrepancy(self) -> None:
        validate(require_private_discrepancy=True)


if __name__ == "__main__":
    unittest.main()
