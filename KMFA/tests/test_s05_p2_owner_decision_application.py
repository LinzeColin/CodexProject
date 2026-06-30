import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREVIEWER = ROOT / "KMFA" / "tools" / "preview_s05_p2_owner_decision_application.py"
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
        "decision_time": "2026-06-30T12:20:00+10:00",
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
            "cross_source_support_scope": "Excel workbook supports review only; it is not a standalone A0 project fixture.",
            "q5_exclusion_confirmed": True,
        }
    )
    return decision


def private_mapping_decision() -> dict:
    decision = base_decision("provide_private_field_mapping")
    decision.update(
        {
            "private_hash_refs": {
                field_key: f"sha256:{str(index + 1) * 64}" for index, field_key in enumerate(FIELD_KEYS)
            },
            "source_anchor_refs": {
                field_key: f"private-source-anchor:{field_key}" for field_key in FIELD_KEYS
            },
        }
    )
    return decision


def keep_pending_decision() -> dict:
    decision = base_decision("keep_pending")
    decision.update(
        {
            "reason_pending": "Owner has not supplied a resolving mapping or downgrade decision.",
            "next_review_trigger": "Owner or authorized delegate supplies a resolving decision record.",
        }
    )
    return decision


class S05P2OwnerDecisionApplicationPreviewTests(unittest.TestCase):
    def run_previewer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(PREVIEWER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_decision(self, payload: dict, root: Path) -> Path:
        path = root / "decision.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return path

    def load_json_output(self, result: subprocess.CompletedProcess[str]) -> dict:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"stdout is not JSON: {exc}\nstdout={result.stdout}\nstderr={result.stderr}")
        self.assertIsInstance(payload, dict)
        return payload

    def test_no_decision_produces_blocked_public_safe_preview(self) -> None:
        result = self.run_previewer()

        self.assertEqual(result.returncode, 2)
        preview = self.load_json_output(result)
        self.assertEqual(preview["application_status"], "blocked")
        self.assertEqual(preview["decision_code"], "none")
        self.assertEqual(preview["blocker"], "no_owner_or_authorized_decision_supplied")
        self.assertFalse(preview["q4_confirmation_claimed"])
        self.assertFalse(preview["q5_baseline_claimed"])

    def test_downgrade_decision_previews_cross_source_support_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = self.write_decision(downgrade_decision(), Path(tmp))
            output_path = Path(tmp) / "preview.json"
            result = self.run_previewer("--decision", str(decision_path), "--output", str(output_path))

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            preview = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(preview["application_status"], "ready")
        self.assertEqual(preview["decision_code"], "downgrade_to_cross_source_support")
        self.assertEqual(preview["candidate_application"]["candidate_role"], "cross_source_support_only")
        self.assertEqual(preview["completion_gate_effect"], "resolves_excel_candidate_without_q4_q5")
        self.assertFalse(preview["q4_confirmation_claimed"])
        self.assertFalse(preview["q5_baseline_claimed"])
        self.assertNotIn("raw_value", json.dumps(preview, ensure_ascii=False))
        self.assertNotIn("normalized_value", json.dumps(preview, ensure_ascii=False))

    def test_private_mapping_decision_previews_hash_backfill_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = self.write_decision(private_mapping_decision(), Path(tmp))
            result = self.run_previewer("--decision", str(decision_path))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        preview = self.load_json_output(result)
        self.assertEqual(preview["application_status"], "ready")
        self.assertEqual(preview["decision_code"], "provide_private_field_mapping")
        self.assertEqual(preview["candidate_application"]["candidate_role"], "a0_fixture_with_private_hash_refs")
        self.assertEqual(preview["candidate_application"]["pending_field_count"], 5)
        self.assertEqual(set(preview["candidate_application"]["field_actions"]), set(FIELD_KEYS))
        self.assertEqual(preview["completion_gate_effect"], "resolves_excel_candidate_without_public_plaintext")

    def test_keep_pending_decision_remains_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = self.write_decision(keep_pending_decision(), Path(tmp))
            result = self.run_previewer("--decision", str(decision_path))

        self.assertEqual(result.returncode, 2)
        preview = self.load_json_output(result)
        self.assertEqual(preview["application_status"], "blocked")
        self.assertEqual(preview["decision_code"], "keep_pending")
        self.assertEqual(preview["blocker"], "owner_decision_keeps_excel_candidate_pending")


if __name__ == "__main__":
    unittest.main()
