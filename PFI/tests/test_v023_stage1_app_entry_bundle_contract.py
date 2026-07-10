from __future__ import annotations

import json
import plistlib
from pathlib import Path
import unittest

from pfi_v02.stage_v023_contract import (
    app_version,
    build_stage1_contract,
    build_stage1_runtime_metadata,
    build_stage1_web_bundle_manifest,
    stage1_build_id,
    stage1_bundle_version,
    stage1_query_string,
    stage1_ui_contract_version,
)
from pfi_v02.stage_v024_stage2_entry_consistency import (
    STAGE2_BUILD_ID,
    STAGE2_UI_CONTRACT_VERSION,
    build_v024_stage2_entry_runtime_metadata,
)


ROOT = Path(__file__).resolve().parents[1]


class TestV023Stage1AppEntryBundleContract(unittest.TestCase):
    def test_stage1_contract_scope_is_app_entry_and_bundle_consistency_only(self) -> None:
        contract = build_stage1_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 1")
        self.assertEqual(contract["stage_name"], "App 入口与前端版本一致性")
        self.assertTrue(contract["current_stage_only"])
        self.assertTrue(contract["no_stage2"])
        self.assertEqual(contract["app_entry_focus"], "~/Downloads/PFI.app")
        self.assertIn("~/Downloads/PFI.app", contract["app_entry_targets"])
        self.assertIn("web_bundle_hash", contract["required_consistency_fields"])
        self.assertIn("browser_profile", contract["required_consistency_fields"])
        self.assertIn("Stage 2 page rebuild", contract["explicitly_not_done"])
        self.assertIn("data computation or read-model changes", contract["explicitly_not_done"])

    def test_stage1_runtime_metadata_has_bundle_hash_and_file_hashes(self) -> None:
        manifest = build_stage1_web_bundle_manifest(ROOT)
        metadata = build_stage1_runtime_metadata(ROOT)

        self.assertEqual(manifest["schema"], "PFIV023Stage1WebBundleManifestV1")
        self.assertEqual(len(manifest["files"]), 3)
        self.assertEqual(metadata["schema"], "PFIV023Stage1RuntimeMetadataV1")
        self.assertEqual(metadata["pfiVersion"], "v0.2.3")
        self.assertEqual(metadata["appVersion"], app_version)
        self.assertEqual(metadata["buildId"], stage1_build_id)
        self.assertEqual(metadata["bundleVersion"], stage1_bundle_version)
        self.assertEqual(metadata["uiContractVersion"], stage1_ui_contract_version)
        self.assertEqual(metadata["webBundleHash"], manifest["web_bundle_hash"])
        self.assertRegex(metadata["webBundleHash"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["webIndexSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(metadata["shellJsSha256"], r"^[0-9a-f]{64}$")

    def test_static_web_shell_exposes_current_entry_contract_markers(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn('data-pfi-version="v0.2.3"', html)
        self.assertIn(f'data-pfi-app-version="{app_version}"', html)
        self.assertIn(f'data-pfi-build-id="{STAGE2_BUILD_ID}"', html)
        self.assertIn(f'data-pfi-ui-contract-version="{STAGE2_UI_CONTRACT_VERSION}"', html)
        self.assertNotIn(f'data-pfi-build-id="{stage1_build_id}"', html)
        self.assertNotIn(f'data-pfi-ui-contract-version="{stage1_ui_contract_version}"', html)
        self.assertIn("PFI_STAGE1_ENTRY_METADATA", js)
        self.assertIn("PFI_STAGE2_ENTRY_METADATA", js)
        self.assertIn("webBundleHash", js)
        self.assertIn("shellJsSha256", js)

    def test_streamlit_shell_injects_dynamic_stage2_runtime_metadata(self) -> None:
        source = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

        metadata = build_v024_stage2_entry_runtime_metadata(ROOT)

        self.assertIn("build_v024_stage2_entry_runtime_metadata", source)
        self.assertIn('"projectRoot": str(ROOT)', source)
        self.assertIn("runtime_payload", source)
        self.assertEqual(metadata["buildId"], STAGE2_BUILD_ID)
        self.assertEqual(metadata["uiContractVersion"], STAGE2_UI_CONTRACT_VERSION)

    def test_app_bundle_keeps_v023_version_and_launchers_use_current_entry_url(self) -> None:
        plist = plistlib.loads((ROOT / "macos" / "PFI.app" / "Contents" / "Info.plist").read_bytes())
        self.assertEqual(plist["CFBundleShortVersionString"], app_version)
        self.assertEqual(plist["CFBundleVersion"], stage1_bundle_version)

        current_query_string = (
            f"pfi_app_version={app_version}"
            f"&pfi_build={STAGE2_BUILD_ID}"
            f"&pfi_ui_contract={STAGE2_UI_CONTRACT_VERSION}"
        )
        for relative in ("StartPFI.command", "scripts/startPFI.sh"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(current_query_string, text)
            self.assertNotIn(stage1_query_string, text)
            self.assertNotIn("pfi_app_version=0.2.1.1", text)

    def test_start_pfi_lock_path_accepts_clean_first_launch(self) -> None:
        script = (ROOT / "StartPFI.command").read_text(encoding="utf-8")

        self.assertIn("LOCK_ACQUIRED=0", script)
        self.assertIn('if mkdir "$LOCK_DIR" 2>/dev/null; then', script)
        self.assertIn("LOCK_ACQUIRED=1", script)
        self.assertIn('if [[ "$LOCK_ACQUIRED" != "1" ]] && ! mkdir "$LOCK_DIR" 2>/dev/null; then', script)
        self.assertNotIn('if ! mkdir "$LOCK_DIR" 2>/dev/null; then\n  EXISTING_LOCK_PID=', script)

    def test_downloads_only_install_scope_is_supported(self) -> None:
        script = (ROOT / "scripts" / "installPFIEntryApps.sh").read_text(encoding="utf-8")

        self.assertIn("--downloads-only", script)
        self.assertIn('INSTALL_SCOPE="downloads"', script)
        self.assertIn('install_required_app "$DOWNLOADS_APP"', script)
        self.assertIn('if [[ "$INSTALL_SCOPE" == "all" ]]', script)
        self.assertIn('BUILT_LAUNCHER_DIR="$(mktemp -d', script)
        self.assertIn('BUILT_LAUNCHER_BINARY="$BUILT_LAUNCHER_DIR/PFI"', script)
        self.assertIn("-Wl,-no_uuid", script)
        self.assertIn('install -m 755 "$BUILT_LAUNCHER_BINARY"', script)
        self.assertNotIn('LAUNCHER_BINARY="$SOURCE_APP/Contents/MacOS/PFI"', script)

    def test_cache_cleanup_uses_locked_runtime_resolver(self) -> None:
        script = (ROOT / "scripts" / "cleanCache.sh").read_text(encoding="utf-8")

        self.assertIn('source "$PROJECT_DIR/scripts/pfiRuntime.sh"', script)
        self.assertIn('pfi_os_ensure_app_python "$PROJECT_DIR"', script)
        self.assertNotIn('PFI_PYTHON:-python3', script)

    def test_stage1_evidence_pack_contract_is_declared(self) -> None:
        contract = build_stage1_contract()
        commands = [item["command"] for item in contract["validation_commands"]]

        self.assertIn("PFI/scripts/installPFIEntryApps.sh --downloads-only", commands)
        self.assertIn("fresh browser profile bundle verification", commands)
        self.assertIn("PFI/reports/pfi_v023/stage_1/evidence.json", contract["evidence_files"])
        self.assertIn("PFI/reports/pfi_v023/stage_1/browser_fresh_profile.json", contract["evidence_files"])
        json.dumps(contract, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
