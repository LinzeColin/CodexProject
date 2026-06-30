from __future__ import annotations

import json
import unittest
from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_2" / "phase_2_1"


def load_entry_consistency_module():
    try:
        return import_module("pfi_v02.stage_v024_stage2_entry_consistency")
    except ModuleNotFoundError as exc:
        raise AssertionError("missing stage_v024_stage2_entry_consistency module") from exc


class TestV024Stage2Phase21EntryMapping(unittest.TestCase):
    def test_phase21_contract_maps_all_required_entry_surfaces(self) -> None:
        entry_consistency = load_entry_consistency_module()
        contract = entry_consistency.build_v024_stage2_phase21_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 2")
        self.assertEqual(contract["phase_id"], "2.1")
        self.assertEqual(contract["task_ids"], ["T2.1.1", "T2.1.2", "T2.1.3", "T2.1.4"])
        self.assertTrue(contract["phase_2_1_complete"])
        self.assertFalse(contract["phase_2_2_complete"])
        self.assertFalse(contract["phase_2_3_complete"])
        self.assertFalse(contract["stage_2_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)

        surfaces = {item["surface_id"]: item for item in contract["entry_surfaces"]}
        self.assertEqual(surfaces["streamlit_host"]["path"], "PFI/src/pfi_os/app/streamlit_app.py")
        self.assertEqual(surfaces["static_html"]["path"], "PFI/web/index.html")
        self.assertEqual(surfaces["shell_runtime"]["path"], "PFI/web/app/shell.js")
        self.assertEqual(surfaces["version_runtime"]["path"], "PFI/web/app/version.js")
        self.assertEqual(surfaces["macos_template_app"]["path"], "PFI/macos/PFI.app")
        self.assertEqual(surfaces["launcher_installer"]["path"], "PFI/scripts/installPFIEntryApps.sh")
        self.assertEqual(surfaces["start_command"]["path"], "PFI/StartPFI.command")
        self.assertEqual(surfaces["start_script"]["path"], "PFI/scripts/startPFI.sh")

    def test_phase21_records_installed_app_bindings_without_modifying_apps(self) -> None:
        entry_consistency = load_entry_consistency_module()
        contract = entry_consistency.build_v024_stage2_phase21_contract().to_dict()
        bindings = {item["path"]: item for item in contract["installed_app_bindings"]}

        self.assertEqual(
            bindings["/Applications/PFI.app"]["project_root"],
            "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI",
        )
        self.assertEqual(
            bindings["~/Downloads/PFI.app"]["project_root"],
            "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI",
        )
        self.assertEqual(bindings["~/Desktop/PFI.app"]["binding_type"], "symlink_to_applications")
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["launcher_changes_allowed"])

    def test_phase21_artifacts_are_present_and_match_changed_files(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        entry_map_path = EVIDENCE_DIR / "entry_map.md"
        signatures_path = EVIDENCE_DIR / "old_ui_signatures.json"
        display_spec_path = EVIDENCE_DIR / "build_hash_display_spec.md"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        stage_doc_path = ROOT / "docs" / "pfi_v024" / "STAGE2_ENTRY_CONSISTENCY.md"

        for path in (
            evidence_path,
            changed_files_path,
            entry_map_path,
            signatures_path,
            display_spec_path,
            terminal_path,
            risk_path,
            stage_doc_path,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage2Phase21EvidenceV1")
        self.assertEqual(evidence["phase_id"], "2.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["phase_2_1_complete"])
        self.assertFalse(evidence["phase_2_2_complete"])
        self.assertFalse(evidence["phase_2_3_complete"])
        self.assertFalse(evidence["stage_2_complete"])
        self.assertTrue(evidence["acceptance_checks"]["entry_map_present"])
        self.assertTrue(evidence["acceptance_checks"]["old_ui_signatures_recorded"])
        self.assertTrue(evidence["acceptance_checks"]["build_hash_display_spec_present"])
        self.assertTrue(evidence["acceptance_checks"]["installed_app_roots_recorded"])

    def test_phase21_records_old_ui_signatures_as_findings_not_fixes(self) -> None:
        signatures = json.loads((EVIDENCE_DIR / "old_ui_signatures.json").read_text(encoding="utf-8"))
        signature_ids = {item["signature_id"] for item in signatures["old_ui_signatures"]}

        self.assertIn("legacy_query_contract_v023_stage1", signature_ids)
        self.assertIn("legacy_index_dataset_v023_stage1", signature_ids)
        self.assertIn("legacy_shell_fallback_v023_stage1", signature_ids)
        self.assertEqual(signatures["remediation_phase"], "2.2")
        self.assertFalse(signatures["fixed_in_phase_2_1"])

    def test_phase21_validation_and_boundaries_are_explicit(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))
        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}

        self.assertEqual(command_status["node --check PFI/web/app/shell.js"], "pass")
        self.assertEqual(command_status["node --check PFI/web/app/version.js"], "pass")
        self.assertEqual(command_status["pytest stage2 phase21 contract"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")
        self.assertFalse(evidence["business_ui_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 2 Phase 2.2 version-link implementation", evidence["explicitly_not_done"])
        self.assertIn("Stage 2 Phase 2.3 real app/browser validation", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
