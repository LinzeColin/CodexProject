from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s13_stage_review as builder


class V015S13StageReviewTests(unittest.TestCase):
    def test_source_and_predecessor_accounting(self) -> None:
        source = builder.source_contract()
        self.assertEqual(source["source_integrity_status"], "PASS")
        self.assertEqual((source["phase_count"], source["task_count"]), (3, 9))
        self.assertEqual(
            builder.phase_evidence()["accounting"],
            {
                "phase_count": 3,
                "phase_passed_count": 3,
                "task_count": 9,
                "task_accepted_count": 9,
                "predecessor_public_check_count": 254,
                "predecessor_receipt_count": 60,
            },
        )

    def test_cross_phase_contracts_pass(self) -> None:
        self.assertEqual(builder.cross_phase_contracts()["accounting"], {"total": 36, "passed": 36, "failed": 0, "blocking_failed": 0})

    def test_findings_fixed_and_risks_routed(self) -> None:
        self.assertEqual([row["finding_id"] for row in builder.findings()], ["S13REV-F001", "S13REV-F002", "S13REV-F003", "S13REV-F004"])
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in builder.findings()))
        self.assertEqual(len(builder.risks()), 6)
        self.assertTrue(all(row["status"] == "ROUTED_RESIDUAL" for row in builder.risks()))

    def test_manifest_pending_and_final_truth(self) -> None:
        pending = builder.manifest([])
        self.assertEqual((pending["decision"], pending["stage_acceptance_status"]), ("REMAIN_IN_S13_STAGE_REVIEW", "PENDING"))
        self.assertFalse(pending["s14_p1_entry_allowed"])
        sample = [
            {"name": name, "status": "PASS", "exit_code": 0, "validation_head": "a" * 40, "validation_run_id": "run"}
            for name in builder.EXPECTED_VALIDATION_NAMES
        ]
        final = builder.manifest(sample)
        self.assertEqual((final["decision"], final["stage_acceptance_status"]), ("GO_TO_S14_P1_ONLY", "PASSED"))
        self.assertTrue(final["s14_p1_entry_allowed"])
        self.assertFalse(final["s14_p1_started"])
        for row in (pending, final):
            self.assertEqual(row["overall_accepted_phase_count"], 37)
            self.assertEqual(row["source_binding_count"], 7)
            self.assertEqual(row["generated_action_candidate_count"], 6)
            self.assertEqual(row["focus_item_count"], 5)
            self.assertFalse(row["github_upload_performed"])
            self.assertFalse(row["app_reinstall_performed"])

    def test_materialized_files_parse(self) -> None:
        for name, expected in (("stage13_review_findings_public_safe.csv", 4), ("open_risk_register_public_safe.csv", 6)):
            with (builder.MACHINE_ROOT / name).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), expected)
        value = json.loads((builder.MACHINE_ROOT / "integrated_review_public_safe.json").read_text(encoding="utf-8"))
        self.assertEqual(value["source_binding_count"], 7)
        self.assertEqual(value["focus_selection"]["focus_item_count"], 5)


if __name__ == "__main__":
    unittest.main()
