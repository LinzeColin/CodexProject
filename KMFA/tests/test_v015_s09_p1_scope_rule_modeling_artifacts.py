from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s09_p1_scope_rule_modeling as builder


class ScopeRuleModelingArtifactTests(unittest.TestCase):
    def _json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_is_deterministic(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_ledger_view_evidence_covers_positive_and_stop_cases(self) -> None:
        policy = self._json(builder.LEDGER_POLICY_PATH)
        cases = self._json(builder.BOUNDARY_CASES_PATH)
        self.assertEqual(policy["legal_ledger_count"], 1)
        self.assertEqual(len(policy["views"]), 5)
        self.assertEqual(cases["positive_case_count"], cases["positive_pass_count"])
        self.assertEqual(cases["negative_case_count"], cases["negative_pass_count"])
        self.assertIn("PARALLEL_LEDGER_FORBIDDEN", cases["rejected_codes"])
        self.assertIn("REGULATORY_EVASION_STOP", cases["rejected_codes"])

    def test_difference_dictionary_is_complete_and_fail_closed(self) -> None:
        dictionary = self._json(builder.DIFFERENCE_DICTIONARY_PATH)
        cases = self._json(builder.DIFFERENCE_CASES_PATH)
        self.assertEqual(len(dictionary["types"]), 8)
        self.assertEqual(cases["registered_case_count"], 8)
        self.assertEqual(cases["registered_case_pass_count"], 8)
        self.assertEqual(cases["unknown_result"]["state"], "UNKNOWN_REQUIRES_CONFIRMATION")
        self.assertEqual(cases["incomplete_result"]["state"], "EVIDENCE_INCOMPLETE_REQUIRES_CONFIRMATION")
        self.assertTrue(cases["float_money_rejected"])
        self.assertEqual(cases["silent_offset_count"], 0)

    def test_adjustment_protocol_is_append_only_and_approval_bound(self) -> None:
        protocol = self._json(builder.ADJUSTMENT_PROTOCOL_PATH)
        cases = self._json(builder.ADJUSTMENT_CASES_PATH)
        self.assertTrue(protocol["append_only_required"])
        self.assertFalse(protocol["direct_legal_ledger_mutation_allowed"])
        self.assertFalse(protocol["unapproved_adjustment_effective_allowed"])
        self.assertTrue(cases["event_roundtrip_exact"])
        self.assertTrue(cases["high_risk_unauthorized_rejected"])
        self.assertEqual(cases["normal_before_approval"]["status"], "PENDING_APPROVAL")
        self.assertEqual(cases["normal_reversed"]["status"], "REVERSED")
        self.assertTrue(cases["direct_ledger_mutation_rejected"])
        self.assertTrue(cases["source_snapshot_unchanged"])

    def test_manifest_preserves_one_phase_and_release_boundary(self) -> None:
        manifest = self._json(builder.MANIFEST_PATH)
        self.assertEqual(manifest["roadmap_phase_id"], "S09-P1")
        self.assertTrue(manifest["s09_p1_started"])
        self.assertFalse(manifest["s09_p2_started"])
        self.assertFalse(manifest["s09_p3_entry_allowed"])
        self.assertFalse(manifest["s09_stage_review_entry_allowed"])
        self.assertFalse(manifest["formal_report_generated"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
