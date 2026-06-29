from __future__ import annotations

import json
from pathlib import Path
import unittest

from pfi_v02.stage_v023_contract import (
    build_stage2_phase1_contract,
    stage2_expected_taskpack_inputs,
    stage2_phase1_id,
    stage2_phase1_name,
)


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage2Phase1TaskpackRecovery(unittest.TestCase):
    def test_contract_locks_phase1_to_taskpack_recovery_only(self) -> None:
        contract = build_stage2_phase1_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 2")
        self.assertEqual(contract["phase_id"], stage2_phase1_id)
        self.assertEqual(contract["phase_name"], stage2_phase1_name)
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["taskpack_required_before_ui_implementation"])

    def test_expected_taskpack_inputs_are_explicit_and_not_historical_aliases(self) -> None:
        contract = build_stage2_phase1_contract()

        self.assertEqual(tuple(contract["expected_taskpack_inputs"]), stage2_expected_taskpack_inputs)
        self.assertIn("~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_Roadmap.txt", contract["expected_taskpack_inputs"])
        self.assertIn("~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_TaskPack.zip", contract["expected_taskpack_inputs"])
        for forbidden in ("pfi_v0211", "pfi_v022", "PFI V0.2 Stage 2"):
            self.assertNotIn(forbidden, "\n".join(contract["expected_taskpack_inputs"]))

    def test_allowed_files_exclude_ui_data_and_app_changes(self) -> None:
        contract = build_stage2_phase1_contract()

        self.assertIn("PFI/docs/pfi_v023/*", contract["allowed_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_2/phase_1/*", contract["allowed_files"])
        self.assertNotIn("PFI/web/index.html", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["allowed_files"])
        self.assertIn("Stage 2 page rebuild", contract["explicitly_not_done"])
        self.assertIn("route implementation changes", contract["explicitly_not_done"])
        self.assertIn("data computation or read-model changes", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_stage2_phase1_document_records_missing_taskpack_boundary(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE2_PHASE1_TASKPACK_RECOVERY.md"
        text = doc_path.read_text(encoding="utf-8")

        self.assertIn("Stage 2 Phase 1", text)
        self.assertIn("任务包恢复与防幻觉门", text)
        self.assertIn("当前新电脑检查未找到这些文件", text)
        self.assertIn("不能开发后续功能", text)
        self.assertIn("不上传 GitHub main；中间 phase 完成不上传", text)

    def test_evidence_pack_is_machine_readable_and_reports_missing_inputs(self) -> None:
        evidence_path = ROOT / "reports" / "pfi_v023" / "stage_2" / "phase_1" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v023" / "stage_2" / "phase_1" / "changed_files.txt"
        terminal_log_path = ROOT / "reports" / "pfi_v023" / "stage_2" / "phase_1" / "terminal.log"

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 2")
        self.assertEqual(evidence["phase_id"], stage2_phase1_id)
        self.assertEqual(evidence["status"], "phase_1_pass_taskpack_missing")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["taskpack_status"], "missing")
        self.assertTrue(evidence["ui_changes_made"] is False)
        self.assertTrue(evidence["data_changes_made"] is False)
        self.assertTrue(evidence["github_upload_required"] is False)
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertIn("PFI/docs/pfi_v023/STAGE2_PHASE1_TASKPACK_RECOVERY.md", changed_files)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("python3 -m pytest PFI/tests/test_v023_stage2_phase1_taskpack_recovery.py -q", terminal_log)
        self.assertIn("git diff --check -- PFI", terminal_log)


if __name__ == "__main__":
    unittest.main()
