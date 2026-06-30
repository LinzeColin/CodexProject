from __future__ import annotations

import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pfi_app_bundle_version_matches_v023_stage1_delivery() -> None:
    plist_path = ROOT / "macos" / "PFI.app" / "Contents" / "Info.plist"
    payload = plistlib.loads(plist_path.read_bytes())

    assert payload["CFBundleShortVersionString"] == "0.2.3"
    assert payload["CFBundleVersion"] == "20260629.1"


def test_pfi_launchers_open_versioned_url_to_avoid_stale_browser_tabs() -> None:
    required = (
        "pfi_app_version=0.2.3"
        "&pfi_build=pfi-v024-stage2-phase22"
        "&pfi_ui_contract=PFI-V024-STAGE2-ENTRY-CONSISTENCY"
    )

    assert required in (ROOT / "StartPFI.command").read_text(encoding="utf-8")
    assert required in (ROOT / "scripts" / "startPFI.sh").read_text(encoding="utf-8")
