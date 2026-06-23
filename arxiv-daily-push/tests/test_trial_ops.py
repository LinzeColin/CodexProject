from __future__ import annotations

import unittest

from arxiv_daily_push.trial_ops import annotate_trial_operational_evidence, validate_trial_ops_report

class TrialOpsTests(unittest.TestCase):
    def test_annotates_text_artifacts(self) -> None:
        report = annotate_trial_operational_evidence({"trial_id": "adp", "period": {"expected_days": 1}, "daily_runs": []}, generated_at="2026-07-01T06:00:00+10:00", text_artifacts_verified=True, text_artifact_ref="text-artifact://trial")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["trial_evidence"]["text_artifacts"]["b1_text_artifacts_verified"])
        self.assertFalse(validate_trial_ops_report(report))

if __name__ == "__main__":
    unittest.main()
