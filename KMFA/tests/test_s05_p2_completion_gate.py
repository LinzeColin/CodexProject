import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "KMFA" / "tools" / "check_s05_p2_completion_gate.py"
FIELD_KEYS = ["contract_amount", "total_expense", "gross_profit", "gross_margin", "cost_category"]


def base_decision(decision_code: str) -> dict:
    return {
        "record_type": "s05_p2_excel_owner_resolution_decision",
        "schema_version": "kmfa.s05_p2_excel_owner_resolution_decision.v1",
        "project_id": "KMFA",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "current_gate": "KMFA-S05-P2-EXCEL-RESOLUTION-GATE",
        "candidate_id": "A0-CAND-70023EFC7305",
        "file_id": "A0-FILE-BAE6D90834C5",
        "decision_code": decision_code,
        "actor_role": "owner",
        "actor_ref": "owner_role_ref",
        "decision_time": "2026-06-30T11:05:00+10:00",
        "field_keys": FIELD_KEYS,
        "business_plaintext_committed": False,
        "raw_source_committed": False,
        "private_csv_committed": False,
        "q4_confirmation_claimed": False,
        "q5_baseline_claimed": False,
        "source_layer_write_allowed": False,
    }


def downgrade_decision() -> dict:
    decision = base_decision("downgrade_to_cross_source_support")
    decision.update(
        {
            "candidate_role": "cross_source_support_only",
            "cross_source_support_scope": "Excel workbook supports later review but is not a standalone A0 fixture.",
            "q5_exclusion_confirmed": True,
        }
    )
    return decision


def keep_pending_decision() -> dict:
    decision = base_decision("keep_pending")
    decision.update(
        {
            "reason_pending": "Owner has not supplied a resolving mapping or downgrade decision.",
            "next_review_trigger": "Owner or authorized delegate supplies the resolving decision record.",
        }
    )
    return decision


class S05P2CompletionGateTests(unittest.TestCase):
    def run_checker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_decision(self, payload: dict, root: Path) -> Path:
        path = root / "decision.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return path

    def test_current_state_is_blocked_without_full_hashes_or_resolving_decision(self) -> None:
        result = self.run_checker("--expect-blocked")

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASS: KMFA S05-P2 completion gate blocked as expected", result.stdout)
        self.assertIn("pending_fields=5", result.stdout)
        self.assertIn("decision_code=none", result.stdout)

    def test_default_gate_fails_when_current_state_is_blocked(self) -> None:
        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCKED: KMFA S05-P2 completion gate not satisfied", result.stdout + result.stderr)

    def test_resolving_downgrade_decision_allows_s05_p2_to_close_without_q4_or_q5(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = self.write_decision(downgrade_decision(), Path(tmp))
            result = self.run_checker("--decision", str(decision_path))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASS: KMFA S05-P2 completion gate ready", result.stdout)
        self.assertIn("mode=owner_downgrade_to_cross_source_support", result.stdout)
        self.assertIn("decision_code=downgrade_to_cross_source_support", result.stdout)

    def test_keep_pending_decision_still_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = self.write_decision(keep_pending_decision(), Path(tmp))
            result = self.run_checker("--decision", str(decision_path), "--expect-blocked")

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("decision_code=keep_pending", result.stdout)
        self.assertIn("reason=keep_pending_decision_does_not_resolve_s05_p2", result.stdout)


if __name__ == "__main__":
    unittest.main()
