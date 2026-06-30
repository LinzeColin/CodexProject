from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import pfi_v02.stage_v024_stage1_shell_integrity as shell_integrity


ROOT = Path(__file__).resolve().parents[1]
SHELL_JS = ROOT / "web" / "app" / "shell.js"
VERSION_JS = ROOT / "web" / "app" / "version.js"


class TestV024Stage1Phase12ShellRepair(unittest.TestCase):
    def test_phase12_contract_keeps_stage1_open(self) -> None:
        self.assertTrue(hasattr(shell_integrity, "build_v024_stage1_phase12_contract"))
        contract = shell_integrity.build_v024_stage1_phase12_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 1")
        self.assertEqual(contract["phase_id"], "1.2")
        self.assertEqual(contract["task_ids"], ["T1.2.1", "T1.2.2", "T1.2.3", "T1.2.4"])
        self.assertTrue(contract["phase_1_1_complete"])
        self.assertTrue(contract["phase_1_2_complete"])
        self.assertFalse(contract["phase_1_3_complete"])
        self.assertFalse(contract["stage_1_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["shell_js_modification_allowed"])
        self.assertTrue(contract["version_js_required"])
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])

    def test_version_js_exposes_readable_version_contract(self) -> None:
        self.assertTrue(VERSION_JS.exists())
        source = VERSION_JS.read_text(encoding="utf-8")

        self.assertIn("PFIV024Stage1VersionInfoV1", source)
        self.assertIn("window.PFI_STAGE1_VERSION", source)
        self.assertIn("window.PFI_READ_STAGE1_VERSION", source)
        self.assertIn("v0.2.4", source)
        self.assertIn("v0.2.3-repair", source)
        self.assertIn("PFI-V024-STAGE1-SHELL-INTEGRITY", source)

    def test_shell_js_exposes_integrity_api(self) -> None:
        source = SHELL_JS.read_text(encoding="utf-8")

        self.assertIn("function readPFIStage1Version", source)
        self.assertIn("function initializePFIStage1Shell", source)
        self.assertIn("function mountPFIStage1Route", source)
        self.assertIn("function handlePFIStage1ShellError", source)
        self.assertIn("window.PFI_STAGE1_SHELL", source)
        self.assertRegex(source, re.compile(r"initialize:\s*initializePFIStage1Shell"))
        self.assertRegex(source, re.compile(r"mountRoute:\s*mountPFIStage1Route"))
        self.assertRegex(source, re.compile(r"errorBoundary:\s*handlePFIStage1ShellError"))
        self.assertRegex(source, re.compile(r"version:\s*readPFIStage1Version"))

    def test_dom_boot_uses_stage1_error_boundary(self) -> None:
        source = SHELL_JS.read_text(encoding="utf-8")

        self.assertIn("initializePFIStage1Shell({ source: \"DOMContentLoaded\" })", source)
        self.assertIn("handlePFIStage1ShellError(error, { source: \"DOMContentLoaded\" })", source)
        self.assertIn("handlePFIStage1ShellError(error, { source: \"route\" })", source)

    def test_phase12_does_not_introduce_formal_fake_financial_data(self) -> None:
        version_source = VERSION_JS.read_text(encoding="utf-8")
        shell_source = SHELL_JS.read_text(encoding="utf-8")
        forbidden_patterns = [
            "mockFinancial",
            "sampleFinancial",
            "demoFinancial",
            "syntheticFinancial",
            "fixtureFinancial",
            "fakeFinancial",
            "hardcodedNetWorth",
            "hardcodedCash",
            "hardcodedInvestmentValue",
        ]

        for forbidden in forbidden_patterns:
            self.assertNotIn(forbidden, version_source)
            self.assertNotIn(forbidden, shell_source)

    def test_phase12_evidence_pack_records_repair_not_stage_closeout(self) -> None:
        evidence_dir = ROOT / "reports" / "pfi_v024" / "stage_1" / "phase_1_2"
        evidence = json.loads((evidence_dir / "evidence.json").read_text(encoding="utf-8"))

        self.assertEqual(evidence["schema"], "PFIV024Stage1Phase12EvidenceV1")
        self.assertEqual(evidence["stage"], "Stage 1")
        self.assertEqual(evidence["phase_id"], "1.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_1_1_complete"])
        self.assertTrue(evidence["phase_1_2_complete"])
        self.assertFalse(evidence["phase_1_3_complete"])
        self.assertFalse(evidence["stage_1_complete"])
        self.assertTrue(evidence["acceptance_checks"]["safe_initialization_skeleton"])
        self.assertTrue(evidence["acceptance_checks"]["version_read_interface"])
        self.assertTrue(evidence["acceptance_checks"]["error_boundary"])
        self.assertTrue(evidence["acceptance_checks"]["no_formal_fake_financial_data"])


if __name__ == "__main__":
    unittest.main()
