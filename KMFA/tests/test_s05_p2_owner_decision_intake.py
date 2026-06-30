import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "KMFA" / "tools" / "check_s05_p2_owner_decision_intake.py"


def public_safe_downgrade_decision() -> dict:
    return {
        "record_type": "s05_p2_excel_owner_resolution_decision",
        "schema_version": "kmfa.s05_p2_excel_owner_resolution_decision.v1",
        "project_id": "KMFA",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "current_gate": "KMFA-S05-P2-EXCEL-RESOLUTION-GATE",
        "candidate_id": "A0-CAND-70023EFC7305",
        "file_id": "A0-FILE-BAE6D90834C5",
        "decision_code": "downgrade_to_cross_source_support",
        "actor_role": "owner",
        "actor_ref": "owner_role_ref",
        "decision_time": "2026-06-30T10:15:00+10:00",
        "field_keys": ["contract_amount", "total_expense", "gross_profit", "gross_margin", "cost_category"],
        "candidate_role": "cross_source_support_only",
        "cross_source_support_scope": "Excel workbook may support later review but is not a standalone A0 project fixture.",
        "q5_exclusion_confirmed": True,
        "business_plaintext_committed": False,
        "raw_source_committed": False,
        "private_csv_committed": False,
        "q4_confirmation_claimed": False,
        "q5_baseline_claimed": False,
        "source_layer_write_allowed": False,
    }


class S05P2OwnerDecisionIntakeTests(unittest.TestCase):
    def run_checker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_contract_matches_owner_packet_without_resolving_pending_fields(self) -> None:
        result = self.run_checker()

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASS: KMFA S05-P2 owner decision intake check passed", result.stdout)
        self.assertIn("contract_status=ready_for_owner_decision_record", result.stdout)
        self.assertIn("decision_status=no_decision_supplied", result.stdout)

    def test_accepts_public_safe_downgrade_decision_without_q4_or_q5_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision_path.write_text(
                json.dumps(public_safe_downgrade_decision(), ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )

            result = self.run_checker("--decision", str(decision_path))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("decision_status=validated_public_safe", result.stdout)
        self.assertIn("decision_code=downgrade_to_cross_source_support", result.stdout)

    def test_rejects_plaintext_value_keys_in_decision_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = public_safe_downgrade_decision()
            decision["raw_value"] = "must not enter public metadata"
            decision_path.write_text(json.dumps(decision, ensure_ascii=False, sort_keys=True), encoding="utf-8")

            result = self.run_checker("--decision", str(decision_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden public metadata key", result.stdout + result.stderr)

    def test_rejects_non_owner_or_unauthorized_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = public_safe_downgrade_decision()
            decision["actor_role"] = "analyst"
            decision_path.write_text(json.dumps(decision, ensure_ascii=False, sort_keys=True), encoding="utf-8")

            result = self.run_checker("--decision", str(decision_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("actor_role must be owner or authorized_delegate", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
