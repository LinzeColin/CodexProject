from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s08_stage_review as builder


class V015S08StageReviewTests(unittest.TestCase):
    def test_source_and_predecessor_accounting(self) -> None:
        self.assertEqual(builder.source_contract()["s08_counts"], {"phases": 3, "tasks": 9})
        self.assertEqual(builder.phase_evidence()["accounting"], {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_receipt_count": 57,
        })

    def test_cross_phase_contracts_pass(self) -> None:
        result = builder.cross_phase_contracts()
        self.assertEqual(result["accounting"], {"total": 22, "passed": 22, "failed": 0, "blocking_failed": 0})
        self.assertTrue(all(row["status"] == "PASS" for row in result["contracts"]))

    def test_findings_fixed_and_risks_routed(self) -> None:
        self.assertEqual([row["finding_id"] for row in builder.findings()], ["S08REV-F001", "S08REV-F002", "S08REV-F003"])
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in builder.findings()))
        self.assertEqual(len(builder.risks()), 5)
        self.assertTrue(all(row["status"] == "ROUTED_RESIDUAL" and row["plan_complete"] == "true" for row in builder.risks()))

    def test_manifest_pending_and_final_truth(self) -> None:
        pending = builder.manifest(final_validation=False)
        self.assertEqual((pending["decision"], pending["stage_acceptance_status"]), ("REMAIN_IN_S08_STAGE_REVIEW", "PENDING"))
        self.assertFalse(pending["s09_p1_entry_allowed"])
        sample = [{"status": "PASS", "exit_code": 0, "validation_head": "a" * 40, "validation_run_id": "run"}]
        final = builder.manifest(final_validation=True, receipts=sample)
        self.assertEqual((final["decision"], final["stage_acceptance_status"]), ("GO_TO_S09_P1_ONLY", "PASSED"))
        self.assertTrue(final["s09_p1_entry_allowed"])
        self.assertFalse(final["s09_p1_started"])
        for row in (pending, final):
            self.assertEqual(row["overall_accepted_phase_count"], 22)
            self.assertEqual(row["raw_root_access_count"], 0)
            self.assertFalse(row["github_upload_performed"])
            self.assertFalse(row["app_reinstall_performed"])

    def test_materialized_files_parse(self) -> None:
        for name, expected in (("stage8_review_findings_public_safe.csv", 3), ("open_risk_register_public_safe.csv", 5)):
            with (builder.MACHINE_ROOT / name).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), expected)
        value = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertIn(value["stage_acceptance_status"], {"PENDING", "PASSED"})


if __name__ == "__main__":
    unittest.main()
