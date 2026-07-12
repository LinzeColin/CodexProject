from __future__ import annotations

import unittest

from KMFA.tools.v014_raw_value_matching_private_dry_run import generate
from KMFA.tools.check_v014_raw_value_matching_private_dry_run import (
    validate_v014_raw_value_matching_private_dry_run,
)


class V014RawValueMatchingPrivateDryRunTest(unittest.TestCase):
    def test_private_dry_run_generates_no_go_gap_evidence(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:58+10:00")
        validated = validate_v014_raw_value_matching_private_dry_run(require_private_diagnostic=True)

        self.assertEqual(validated["phase_id"], "V014_RAW_VALUE_MATCHING_PRIVATE_DRY_RUN")
        self.assertEqual(validated["status"], manifest["status"])
        self.assertTrue(validated["raw_private_extraction_summary"]["raw_value_fingerprints_generated"])
        self.assertGreater(validated["raw_private_extraction_summary"]["raw_value_fingerprint_count"], 0)
        self.assertFalse(validated["processed_target_summary"]["processed_value_targets_available"])
        self.assertEqual(validated["value_matching_summary"]["comparable_value_pair_count"], 0)
        self.assertFalse(validated["value_matching_summary"]["business_value_consistency_verified"])
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")

    def test_release_upload_and_business_actions_remain_blocked(self) -> None:
        manifest = validate_v014_raw_value_matching_private_dry_run(require_private_diagnostic=True)
        go_no_go = manifest["go_no_go"]

        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])
        self.assertTrue(manifest["raw_readonly_boundary"]["raw_root_stat_unchanged_after_dry_run"])
        self.assertFalse(manifest["raw_readonly_boundary"]["raw_inbox_mutated_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
