from __future__ import annotations

import json
import unittest
from pathlib import Path

import pfi_v02.stage_v024_stage1_shell_integrity as shell_integrity


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_1" / "phase_1_3"


class TestV024Stage1Phase13ValidationCloseout(unittest.TestCase):
    def test_phase13_contract_marks_stage_candidate_not_complete(self) -> None:
        self.assertTrue(hasattr(shell_integrity, "build_v024_stage1_phase13_contract"))
        contract = shell_integrity.build_v024_stage1_phase13_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 1")
        self.assertEqual(contract["phase_id"], "1.3")
        self.assertEqual(contract["task_ids"], ["T1.3.1", "T1.3.2", "T1.3.3"])
        self.assertTrue(contract["phase_1_1_complete"])
        self.assertTrue(contract["phase_1_2_complete"])
        self.assertTrue(contract["phase_1_3_complete"])
        self.assertTrue(contract["stage_1_candidate_complete"])
        self.assertFalse(contract["stage_1_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["whole_stage_review_required"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])

    def test_phase13_evidence_pack_is_complete(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in (EVIDENCE_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage1Phase13EvidenceV1")
        self.assertEqual(evidence["stage"], "Stage 1")
        self.assertEqual(evidence["phase_id"], "1.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_1_1_complete"])
        self.assertTrue(evidence["phase_1_2_complete"])
        self.assertTrue(evidence["phase_1_3_complete"])
        self.assertTrue(evidence["stage_1_candidate_complete"])
        self.assertFalse(evidence["stage_1_complete"])
        self.assertEqual(evidence["changed_files"], changed_files)
        for filename in ("terminal.log", "changed_files.txt", "risk_and_rollback.md"):
            self.assertTrue((EVIDENCE_DIR / filename).exists(), filename)

    def test_phase13_records_required_validation_commands(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))
        commands = {entry["cmd"]: entry for entry in evidence["commands"]}

        self.assertEqual(commands["node --check PFI/web/app/shell.js"]["status"], "pass")
        self.assertEqual(commands["node --check PFI/web/app/version.js"]["status"], "pass")
        self.assertEqual(commands["pytest stage1 phase13 contract"]["status"], "pass")
        self.assertEqual(commands["pytest v024 stage1 regression"]["status"], "pass")
        self.assertEqual(commands["changed files audit"]["status"], "pass")
        self.assertEqual(commands["git diff --check -- PFI"]["status"], "pass")
        self.assertNotIn("pending", json.dumps(evidence, ensure_ascii=False).lower())

    def test_phase13_does_not_claim_review_or_upload(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertTrue(evidence["no_auto_closeout"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["business_ui_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertIn("Stage 1 whole-stage review", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
