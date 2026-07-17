from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s11_stage_review as builder


class V015S11StageReviewTests(unittest.TestCase):
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
                "predecessor_receipt_count": 58,
            },
        )

    def test_cross_phase_contracts_pass(self) -> None:
        self.assertEqual(
            builder.cross_phase_contracts()["accounting"],
            {"total": 28, "passed": 28, "failed": 0, "blocking_failed": 0},
        )

    def test_findings_fixed_and_risks_routed(self) -> None:
        self.assertEqual(
            [row["finding_id"] for row in builder.findings()],
            ["S11REV-F001", "S11REV-F002", "S11REV-F003"],
        )
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in builder.findings()))
        self.assertEqual(len(builder.risks()), 5)
        self.assertTrue(all(row["status"] == "ROUTED_RESIDUAL" for row in builder.risks()))

    def test_manifest_pending_and_final_truth(self) -> None:
        pending = builder.manifest([])
        self.assertEqual((pending["decision"], pending["stage_acceptance_status"]), ("REMAIN_IN_S11_STAGE_REVIEW", "PENDING"))
        self.assertFalse(pending["s12_p1_entry_allowed"])
        sample = [
            {
                "name": name,
                "status": "PASS",
                "exit_code": 0,
                "validation_head": "a" * 40,
                "validation_run_id": "run",
            }
            for name in builder.EXPECTED_VALIDATION_NAMES
        ]
        final = builder.manifest(sample)
        self.assertEqual((final["decision"], final["stage_acceptance_status"]), ("GO_TO_S12_P1_ONLY", "PASSED"))
        self.assertTrue(final["s12_p1_entry_allowed"])
        self.assertFalse(final["s12_p1_started"])
        for row in (pending, final):
            self.assertEqual(row["overall_accepted_phase_count"], 31)
            self.assertEqual(row["raw_root_access_count"], 0)
            self.assertFalse(row["github_upload_performed"])
            self.assertFalse(row["app_reinstall_performed"])

    def test_materialized_files_parse(self) -> None:
        for name, expected in (("stage11_review_findings_public_safe.csv", 3), ("open_risk_register_public_safe.csv", 5)):
            with (builder.MACHINE_ROOT / name).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), expected)
        value = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertIn(value["stage_acceptance_status"], {"PENDING", "PASSED"})


if __name__ == "__main__":
    unittest.main()
