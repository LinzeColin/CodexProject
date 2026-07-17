from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s14_stage_review as builder


class V015S14StageReviewTests(unittest.TestCase):
    def test_source_and_predecessor_accounting(self) -> None:
        self.assertEqual(builder.source_contract()["source_integrity_status"], "PASS")
        self.assertEqual(
            builder.phase_evidence()["accounting"],
            {
                "phase_count": 3,
                "phase_passed_count": 3,
                "task_count": 9,
                "task_accepted_count": 9,
                "predecessor_public_check_count": 174,
                "predecessor_receipt_count": 59,
            },
        )

    def test_cross_phase_contracts_pass(self) -> None:
        self.assertEqual(
            builder.cross_phase_contracts()["accounting"],
            {"total": 36, "passed": 36, "failed": 0, "blocking_failed": 0},
        )

    def test_findings_fixed_and_risks_routed(self) -> None:
        self.assertEqual(
            [row["finding_id"] for row in builder.findings()],
            ["S14REV-F001", "S14REV-F002", "S14REV-F003", "S14REV-F004"],
        )
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in builder.findings()))
        self.assertEqual(len(builder.risks()), 5)
        self.assertTrue(all(row["status"] == "ROUTED_RESIDUAL" for row in builder.risks()))

    def test_manifest_pending_and_final_truth(self) -> None:
        pending = builder.manifest([])
        self.assertEqual((pending["decision"], pending["stage_acceptance_status"]), ("REMAIN_IN_S14_STAGE_REVIEW", "PENDING"))
        self.assertFalse(pending["s15_p1_entry_allowed"])
        sample = [
            {"name": name, "status": "PASS", "exit_code": 0, "validation_head": "a" * 40, "validation_run_id": "run"}
            for name in builder.EXPECTED_VALIDATION_NAMES
        ]
        final = builder.manifest(sample)
        self.assertEqual((final["decision"], final["stage_acceptance_status"]), ("GO_TO_S15_P1_ONLY", "PASSED"))
        self.assertTrue(final["s15_p1_entry_allowed"])
        self.assertFalse(final["s15_p1_started"])
        for row in (pending, final):
            self.assertEqual(row["overall_accepted_phase_count"], 40)
            self.assertEqual(row["integration_binding_count"], 15)
            self.assertEqual(row["route_mismatch_count"], 0)
            self.assertEqual(row["number_mismatch_count"], 0)
            self.assertEqual(row["language_mismatch_count"], 0)
            self.assertFalse(row["github_upload_performed"])
            self.assertFalse(row["app_reinstall_performed"])

    def test_materialized_files_parse(self) -> None:
        for name, expected in (("stage14_review_findings_public_safe.csv", 4), ("open_risk_register_public_safe.csv", 5)):
            with (builder.MACHINE_ROOT / name).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), expected)
        value = json.loads((builder.MACHINE_ROOT / "integrated_review_public_safe.json").read_text(encoding="utf-8"))
        self.assertEqual(value["integration_binding_count"], 15)
        self.assertEqual(value["integration_binding_failed_count"], 0)
        self.assertTrue(builder.HTML_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
