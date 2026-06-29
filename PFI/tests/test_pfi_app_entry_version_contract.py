from __future__ import annotations

import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pfi_app_bundle_version_matches_v0211_delivery() -> None:
    plist_path = ROOT / "macos" / "PFI.app" / "Contents" / "Info.plist"
    payload = plistlib.loads(plist_path.read_bytes())

    assert payload["CFBundleShortVersionString"] == "0.2.1.1"
    assert payload["CFBundleVersion"] == "20260629"


def test_pfi_launchers_open_versioned_url_to_avoid_stale_browser_tabs() -> None:
    required = "pfi_app_version=0.2.1.1&pfi_build=20260629"

    assert required in (ROOT / "StartPFI.command").read_text(encoding="utf-8")
    assert required in (ROOT / "scripts" / "startPFI.sh").read_text(encoding="utf-8")
