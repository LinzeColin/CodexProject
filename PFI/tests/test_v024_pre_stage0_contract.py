from __future__ import annotations

import json
import unittest
from pathlib import Path

from pfi_v02.stage_v024_pre_stage0_contract import build_v024_pre_stage0_contract


ROOT = Path(__file__).resolve().parents[1]


class TestV024PreStage0Contract(unittest.TestCase):
    def test_contract_maps_v023_repair_sources_to_v024_pre_stage0_without_entering_stage0(self) -> None:
        contract = build_v024_pre_stage0_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["pre_stage_id"], "PRE-S0")
        self.assertEqual(contract["phase_id"], "P0.0")
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["stage_0_executed"])
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertTrue(contract["stop_after_pre_stage0"])

    def test_contract_keeps_ten_primary_entries_and_deprecates_old_constraints(self) -> None:
        contract = build_v024_pre_stage0_contract().to_dict()

        self.assertEqual(len(contract["official_nav"]), 10)
        self.assertEqual(contract["official_nav"][8], "市场与研究")
        self.assertTrue(contract["market_research_top_level"])
        self.assertIn("历史 9 入口正式约束", contract["deprecated_constraints"])
        self.assertIn("市场与研究不得作为一级入口", contract["deprecated_constraints"])
        self.assertIn("暗色 AI 控制台作为默认视觉方向", contract["deprecated_constraints"])
        self.assertTrue(contract["no_mock_financial_data"])
        self.assertEqual(
            contract["forbidden_financial_data_labels"],
            ["mock", "sample", "demo", "synthetic", "fixture", "fake"],
        )

    def test_pre_stage0_evidence_records_current_main_audit_and_source_hashes(self) -> None:
        evidence_path = ROOT / "reports" / "pfi_v024" / "pre_stage_0" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v024" / "pre_stage_0" / "changed_files.txt"
        current_audit_path = ROOT / "reports" / "pfi_v024" / "pre_stage_0" / "current_main_audit.md"

        for path in (evidence_path, changed_files_path, current_audit_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024PreStage0EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Pre Stage 0")
        self.assertEqual(evidence["phase_id"], "P0.0")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["requires_user_acceptance"])
        self.assertTrue(evidence["no_auto_stage0"])
        self.assertFalse(evidence["stage_0_executed"])
        self.assertTrue(evidence["source_files"]["roadmap"]["exists"])
        self.assertTrue(evidence["source_files"]["taskpack_zip"]["exists"])
        self.assertEqual(evidence["source_files"]["taskpack_zip"]["zip_entry_count"], 15)
        self.assertEqual(evidence["current_main_audit"]["docs_pfi_v023_present"], True)
        self.assertGreaterEqual(evidence["current_main_audit"]["v023_test_file_count"], 10)
        self.assertEqual(evidence["current_main_audit"]["shell_js_node_check"], "pass")
        self.assertTrue(evidence["acceptance_checks"]["taskpack_version_mapped_to_v024"])
        self.assertTrue(evidence["acceptance_checks"]["current_main_reverified_not_assumed_from_taskpack"])
        self.assertTrue(evidence["acceptance_checks"]["pre_stage0_only_no_stage0_execution"])


if __name__ == "__main__":
    unittest.main()

