from pathlib import Path

from quantlab.system import (
    APP_BUNDLE_NAME,
    APP_DISPLAY_NAME,
    LEGACY_APP_NAME,
    MASTER_DISPLAY_NAME,
    MASTER_SHORT_TITLE,
    MASTER_SYSTEM_ID,
    app_bundle_paths,
    eva_manifest,
    legacy_app_bundle_paths,
)


def test_eva_identity_keeps_quantlab_as_master_entry():
    manifest = eva_manifest()

    assert MASTER_SYSTEM_ID == "EVA_OS"
    assert MASTER_DISPLAY_NAME == "EVA_OS"
    assert MASTER_SHORT_TITLE == "EVA_OS｜证值智能中台"
    assert manifest["entry_system"] == "QuantLab"
    assert manifest["research_only"] is True
    assert manifest["no_live_trading"] is True
    assert [item["order"] for item in manifest["subsystems"]] == list(range(1, 10))
    assert manifest["subsystems"][3]["name_en"] == "QuantLab"
    assert len(manifest["foundation_layers"]) == 5


def test_eva_app_bundle_paths_use_new_name_and_preserve_legacy_lookup():
    home = Path("/Users/example")
    apps = Path("/Applications")

    paths = app_bundle_paths(home=home, applications_dir=apps)
    legacy_paths = legacy_app_bundle_paths(home=home, applications_dir=apps)

    assert APP_BUNDLE_NAME == "EVA_OS"
    assert APP_DISPLAY_NAME == "EVA_OS"
    assert LEGACY_APP_NAME == "量化回测系统"
    assert paths["desktop"] == home / "Desktop" / "EVA_OS.app"
    assert paths["downloads"] == home / "Downloads" / "EVA_OS.app"
    assert paths["applications"] == apps / "EVA_OS.app"
    assert legacy_paths["desktop"] == home / "Desktop" / "量化回测系统.app"
