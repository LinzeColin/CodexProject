from pathlib import Path

from pfi_os.system import (
    APP_BUNDLE_NAME,
    APP_DISPLAY_NAME,
    LEGACY_APP_NAME,
    MASTER_DISPLAY_NAME,
    MASTER_SHORT_TITLE,
    MASTER_SYSTEM_ID,
    app_bundle_paths,
    pfi_manifest,
    legacy_app_bundle_paths,
)


def test_pfi_identity_keeps_pfi_os_as_master_entry():
    manifest = pfi_manifest()

    assert MASTER_SYSTEM_ID == "PFI_OS"
    assert MASTER_DISPLAY_NAME == "PFI OS"
    assert MASTER_SHORT_TITLE == "PFI OS｜证值智能中台"
    assert manifest["entry_system"] == "PFIOS"
    assert manifest["research_only"] is True
    assert manifest["no_live_trading"] is True
    assert [item["order"] for item in manifest["subsystems"]] == list(range(1, 9))
    assert manifest["subsystems"][2]["name_en"] == "PFI OS"
    assert len(manifest["foundation_layers"]) == 5


def test_pfi_app_bundle_paths_use_new_name_and_preserve_legacy_lookup():
    home = Path("/Users/example")
    apps = Path("/Applications")

    paths = app_bundle_paths(home=home, applications_dir=apps)
    legacy_paths = legacy_app_bundle_paths(home=home, applications_dir=apps)

    assert APP_BUNDLE_NAME == "PFI_OS"
    assert APP_DISPLAY_NAME == "PFI OS"
    assert LEGACY_APP_NAME == "量化回测系统"
    assert paths["desktop"] == home / "Desktop" / "PFI_OS.app"
    assert paths["downloads"] == home / "Downloads" / "PFI_OS.app"
    assert paths["applications"] == apps / "PFI_OS.app"
    assert legacy_paths["desktop"] == home / "Desktop" / "量化回测系统.app"
