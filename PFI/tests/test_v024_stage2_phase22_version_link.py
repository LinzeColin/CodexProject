from __future__ import annotations

import json
import re
import unittest
from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_INDEX = ROOT / "web" / "index.html"
TOKENS_CSS = ROOT / "web" / "styles" / "tokens.css"
SHELL_JS = ROOT / "web" / "app" / "shell.js"
VERSION_JS = ROOT / "web" / "app" / "version.js"
ENTRY_AUDIT_JS = ROOT / "web" / "app" / "entry_audit.js"
START_COMMAND = ROOT / "StartPFI.command"
START_SCRIPT = ROOT / "scripts" / "startPFI.sh"
STREAMLIT_APP = ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py"
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_2" / "phase_2_2"

EXPECTED_REPAIR_LABEL = "PFI v0.2.3 Repair"
EXPECTED_BUILD_ID = "pfi-v024-stage2-phase22"
EXPECTED_BUNDLE_VERSION = "20260630.2"
EXPECTED_UI_CONTRACT = "PFI-V024-STAGE2-ENTRY-CONSISTENCY"
LEGACY_BUILD_ID = "20260629-stage1"
LEGACY_UI_CONTRACT = "PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY"


def load_entry_consistency_module():
    return import_module("pfi_v02.stage_v024_stage2_entry_consistency")


class TestV024Stage2Phase22VersionLink(unittest.TestCase):
    def test_phase22_contract_and_runtime_metadata_are_declared(self) -> None:
        entry_consistency = load_entry_consistency_module()
        self.assertTrue(hasattr(entry_consistency, "build_v024_stage2_phase22_contract"))
        self.assertTrue(hasattr(entry_consistency, "build_v024_stage2_entry_runtime_metadata"))

        contract = entry_consistency.build_v024_stage2_phase22_contract().to_dict()
        metadata = entry_consistency.build_v024_stage2_entry_runtime_metadata(ROOT)

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 2")
        self.assertEqual(contract["phase_id"], "2.2")
        self.assertEqual(contract["task_ids"], ["T2.2.1", "T2.2.2", "T2.2.3", "T2.2.4"])
        self.assertTrue(contract["phase_2_1_complete"])
        self.assertTrue(contract["phase_2_2_complete"])
        self.assertFalse(contract["phase_2_3_complete"])
        self.assertFalse(contract["stage_2_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["github_main_upload_allowed"])

        self.assertEqual(metadata["schema"], "PFIV024Stage2EntryRuntimeMetadataV1")
        self.assertEqual(metadata["repairLabel"], EXPECTED_REPAIR_LABEL)
        self.assertEqual(metadata["buildId"], EXPECTED_BUILD_ID)
        self.assertEqual(metadata["bundleVersion"], EXPECTED_BUNDLE_VERSION)
        self.assertEqual(metadata["uiContractVersion"], EXPECTED_UI_CONTRACT)
        self.assertRegex(metadata["webBundleHash"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["webIndexSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["tokensCssSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["shellJsSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["versionJsSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["entryAuditJsSha256"], r"^[0-9a-f]{64}$")
        self.assertIn("web/styles/tokens.css", metadata["frontendBundleFiles"])

    def test_static_index_exposes_visible_stage2_entry_identity(self) -> None:
        html = WEB_INDEX.read_text(encoding="utf-8")

        self.assertIn(f'data-pfi-repair-label="{EXPECTED_REPAIR_LABEL}"', html)
        self.assertIn(f'data-pfi-build-id="{EXPECTED_BUILD_ID}"', html)
        self.assertIn(f'data-pfi-bundle-version="{EXPECTED_BUNDLE_VERSION}"', html)
        self.assertIn(f'data-pfi-ui-contract-version="{EXPECTED_UI_CONTRACT}"', html)
        self.assertIn('data-pfi-web-bundle-hash="runtime-computed"', html)
        self.assertIn("data-pfi-entry-version-strip", html)
        self.assertIn("data-pfi-entry-repair-label", html)
        self.assertIn("data-pfi-entry-build-id", html)
        self.assertIn("data-pfi-entry-bundle-hash", html)
        self.assertIn("data-pfi-entry-ui-contract", html)
        self.assertIn(EXPECTED_REPAIR_LABEL, html)
        self.assertIn(EXPECTED_BUILD_ID, html)
        self.assertIn(EXPECTED_UI_CONTRACT, html)
        self.assertIn('<script src="./app/version.js"></script>', html)
        self.assertIn('<script src="./app/entry_audit.js"></script>', html)
        self.assertNotIn(LEGACY_BUILD_ID, html)
        self.assertNotIn(LEGACY_UI_CONTRACT, html)

    def test_entry_status_strip_has_stable_layout_styles(self) -> None:
        css = TOKENS_CSS.read_text(encoding="utf-8")

        self.assertIn(".entry-status-strip", css)
        self.assertIn("text-overflow: ellipsis", css)
        self.assertIn("data-pfi-entry-repair-label", css)
        self.assertIn("minmax(210px, 0.82fr)", css)
        self.assertIn("minmax(220px, 0.8fr)", css)

    def test_version_and_entry_audit_scripts_expose_read_interfaces(self) -> None:
        self.assertTrue(ENTRY_AUDIT_JS.exists())
        version_source = VERSION_JS.read_text(encoding="utf-8")
        audit_source = ENTRY_AUDIT_JS.read_text(encoding="utf-8")

        self.assertIn("PFIV024Stage2EntryVersionInfoV1", version_source)
        self.assertIn("window.PFI_STAGE2_ENTRY_VERSION", version_source)
        self.assertIn("window.PFI_READ_STAGE2_ENTRY_VERSION", version_source)
        self.assertIn(EXPECTED_REPAIR_LABEL, version_source)
        self.assertIn(EXPECTED_BUILD_ID, version_source)
        self.assertIn(EXPECTED_UI_CONTRACT, version_source)
        self.assertIn("PFI-V024-STAGE1-SHELL-INTEGRITY", version_source)

        self.assertIn("PFIV024Stage2EntryAuditReadModelV1", audit_source)
        self.assertIn("window.PFI_STAGE2_ENTRY_AUDIT", audit_source)
        self.assertIn("window.PFI_READ_STAGE2_ENTRY_AUDIT", audit_source)
        self.assertIn("webIndexSha256", audit_source)
        self.assertIn("tokensCssSha256", audit_source)
        self.assertIn("shellJsSha256", audit_source)
        self.assertIn("webBundleHash", audit_source)
        self.assertIn("localhostUrl", audit_source)
        self.assertIn("appPath", audit_source)

    def test_shell_streamlit_and_launchers_use_stage2_entry_metadata(self) -> None:
        shell_source = SHELL_JS.read_text(encoding="utf-8")
        streamlit_source = STREAMLIT_APP.read_text(encoding="utf-8")
        launcher_sources = "\n".join(
            (
                START_COMMAND.read_text(encoding="utf-8"),
                START_SCRIPT.read_text(encoding="utf-8"),
            )
        )

        self.assertIn(EXPECTED_BUILD_ID, shell_source)
        self.assertIn(EXPECTED_UI_CONTRACT, shell_source)
        self.assertIn("PFI_STAGE2_ENTRY_METADATA", shell_source)
        self.assertIn("applyPFIStage2EntryMetadata", shell_source)
        self.assertIn("tokensCssSha256", shell_source)
        self.assertNotIn(LEGACY_BUILD_ID, shell_source)
        self.assertNotIn(LEGACY_UI_CONTRACT, shell_source)

        self.assertIn("build_v024_stage2_entry_runtime_metadata", streamlit_source)
        self.assertIn('version_path = ROOT / "web" / "app" / "version.js"', streamlit_source)
        self.assertIn('entry_audit_path = ROOT / "web" / "app" / "entry_audit.js"', streamlit_source)

        self.assertIn(f"pfi_build={EXPECTED_BUILD_ID}", launcher_sources)
        self.assertIn(f"pfi_ui_contract={EXPECTED_UI_CONTRACT}", launcher_sources)
        self.assertNotIn(f"pfi_build={LEGACY_BUILD_ID}", launcher_sources)
        self.assertNotIn(f"pfi_ui_contract={LEGACY_UI_CONTRACT}", launcher_sources)

    def test_phase22_evidence_pack_records_boundaries(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        bundle_hash_path = EVIDENCE_DIR / "bundle_hash.txt"

        for path in (evidence_path, changed_files_path, terminal_path, risk_path, bundle_hash_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage2Phase22EvidenceV1")
        self.assertEqual(evidence["phase_id"], "2.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["phase_2_1_complete"])
        self.assertTrue(evidence["phase_2_2_complete"])
        self.assertFalse(evidence["phase_2_3_complete"])
        self.assertFalse(evidence["stage_2_complete"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 2 Phase 2.3 real app/browser validation", evidence["explicitly_not_done"])

        bundle_hash = bundle_hash_path.read_text(encoding="utf-8").strip()
        self.assertRegex(bundle_hash, re.compile(r"^[0-9a-f]{64}$"))


if __name__ == "__main__":
    unittest.main()
