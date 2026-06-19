from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _old_root_name() -> str:
    return "E" + "VA" + "_OS"


def _old_package_name() -> str:
    return "quant" + "lab"


def _old_script_stem() -> str:
    return "Quant" + "Lab"


def test_repository_and_python_package_paths_use_pfi_identity():
    assert PROJECT_ROOT.name == "PFI_OS"
    assert (PROJECT_ROOT / "src" / "pfi_os").is_dir()
    assert not (PROJECT_ROOT / "src" / _old_package_name()).exists()

    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "pfi-os"' in pyproject
    assert "Personal Financial Intelligence OS" in pyproject


def test_root_commands_and_runtime_scripts_use_pfi_identity():
    expected_files = [
        PROJECT_ROOT / "StartPFIOS.command",
        PROJECT_ROOT / "StopPFIOS.command",
        PROJECT_ROOT / "scripts" / "startPFIOS.sh",
        PROJECT_ROOT / "scripts" / "stopPFIOS.sh",
        PROJECT_ROOT / "scripts" / "statusPFIOS.sh",
        PROJECT_ROOT / "scripts" / "pfiRuntime.sh",
        PROJECT_ROOT / "scripts" / "verifyPFIOS.sh",
        PROJECT_ROOT / "scripts" / "auditPFIIntegration.sh",
        PROJECT_ROOT / "scripts" / "installPFIOSEntryApps.sh",
    ]

    missing = [path.relative_to(PROJECT_ROOT).as_posix() for path in expected_files if not path.exists()]
    assert missing == []

    assert not (PROJECT_ROOT / f"Start{_old_script_stem()}.command").exists()
    assert not (PROJECT_ROOT / f"Stop{_old_script_stem()}.command").exists()
    assert not (PROJECT_ROOT / "scripts" / f"start{_old_script_stem()}.sh").exists()
    assert not (PROJECT_ROOT / "scripts" / f"stop{_old_script_stem()}.sh").exists()
    assert not (PROJECT_ROOT / "scripts" / f"status{_old_script_stem()}.sh").exists()


def test_macos_app_bundle_uses_pfi_identity():
    bundle = PROJECT_ROOT / "macos" / "PFI_OS.app"
    assert bundle.is_dir()
    assert (bundle / "Contents" / "Info.plist").is_file()
    assert (bundle / "Contents" / "MacOS" / "PFI_OS").is_file()
    assert (bundle / "Contents" / "Resources" / "PFI_OSAppIcon.icns").is_file()
    assert (PROJECT_ROOT / "macos" / "PFI_OS_launcher.c").is_file()

    old_bundle = PROJECT_ROOT / "macos" / f"{_old_root_name()}.app"
    assert not old_bundle.exists()


def test_current_non_data_paths_do_not_keep_legacy_identity_fragments():
    old_fragments = [
        _old_root_name(),
        "E" + "VA" + "_",
        _old_script_stem(),
        _old_package_name(),
        "QUANT" + "LAB",
    ]
    violations = []

    for path in PROJECT_ROOT.rglob("*"):
        relative = path.relative_to(PROJECT_ROOT)
        if relative.parts and relative.parts[0] == "data":
            continue
        if "docs" in relative.parts and "archive" in relative.parts:
            continue
        relative_text = relative.as_posix()
        if any(fragment in relative_text for fragment in old_fragments):
            violations.append(relative_text)

    assert violations == []
