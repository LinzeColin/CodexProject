from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from pfi_v02.stage_v024_stage1_shell_integrity import build_v024_stage1_phase11_contract


ROOT = Path(__file__).resolve().parents[1]


class TestV024Stage1Phase11ShellDiagnosis(unittest.TestCase):
    def test_phase11_contract_records_snapshot_without_closing_stage1(self) -> None:
        contract = build_v024_stage1_phase11_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 1")
        self.assertEqual(contract["phase_id"], "1.1")
        self.assertEqual(contract["task_ids"], ["T1.1.1", "T1.1.2", "T1.1.3"])
        self.assertTrue(contract["phase_1_1_complete"])
        self.assertFalse(contract["phase_1_2_complete"])
        self.assertFalse(contract["phase_1_3_complete"])
        self.assertFalse(contract["stage_1_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["shell_js_modification_allowed"])
        self.assertTrue(contract["next_phase_requires_user_acceptance"])

    def test_snapshot_matches_recorded_hash_and_size(self) -> None:
        contract = build_v024_stage1_phase11_contract().to_dict()
        snapshot = ROOT / "reports" / "pfi_v024" / "stage_1" / "phase_1_1" / "shell.js.snapshot"

        self.assertTrue(snapshot.exists())
        data = snapshot.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), contract["shell_js_sha256"])
        self.assertEqual(len(data), contract["shell_js_bytes"])
        self.assertEqual(data.count(b"\n"), contract["shell_js_lines"])

    def test_phase11_diagnosis_records_current_gaps_for_phase12(self) -> None:
        contract = build_v024_stage1_phase11_contract().to_dict()

        self.assertEqual(contract["syntax_check_current_result"], "pass_via_codex_bundled_node")
        self.assertEqual(contract["fragmented_range_findings"], [])
        gaps = "\n".join(contract["residual_phase_1_2_gaps"])
        self.assertIn("version", gaps)
        self.assertIn("init", gaps)
        self.assertIn("route mount", gaps)
        self.assertIn("error boundary", gaps)

    def test_phase11_evidence_pack_is_present(self) -> None:
        evidence_dir = ROOT / "reports" / "pfi_v024" / "stage_1" / "phase_1_1"
        evidence_path = evidence_dir / "evidence.json"
        terminal_path = evidence_dir / "terminal.log"
        changed_files_path = evidence_dir / "changed_files.txt"
        summary_path = evidence_dir / "shell_before_after_summary.md"
        risk_path = evidence_dir / "risk_and_rollback.md"

        for path in (evidence_path, terminal_path, changed_files_path, summary_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage1Phase11EvidenceV1")
        self.assertEqual(evidence["stage"], "Stage 1")
        self.assertEqual(evidence["phase_id"], "1.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_1_1_complete"])
        self.assertFalse(evidence["stage_1_complete"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["acceptance_checks"]["shell_snapshot_saved"])
        self.assertTrue(evidence["acceptance_checks"]["node_check_recorded"])
        self.assertTrue(evidence["acceptance_checks"]["fragment_range_summary_recorded"])
        self.assertFalse(evidence["business_ui_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])


if __name__ == "__main__":
    unittest.main()
