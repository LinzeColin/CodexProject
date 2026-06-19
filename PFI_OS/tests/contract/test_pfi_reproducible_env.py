from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


def test_pfi_001_has_python_version_lock_and_install_contract():
    python_version = _text(".python-version").strip()
    lock = _text("requirements.lock")
    installer = _text("scripts/installLockedEnv.sh")
    docs = _text("docs/development/PFI_REPRODUCIBLE_ENV.md")

    assert python_version == "3.12"
    for dependency in ["numpy==", "pandas==", "streamlit==", "pytest==", "python-docx=="]:
        assert dependency in lock
    assert "pip install -r \"$LOCK_FILE\"" in installer
    assert "pip install --no-deps -e \"$PROJECT_DIR\"" in installer
    assert "PFI_VENV_DIR" in installer
    assert ".pfi_os_app_ready" in installer
    assert "Offline Warm Start" in docs
    assert "startup and test commands never install dependencies automatically" in _text("README.md")


def test_runtime_entrypoints_do_not_install_or_upgrade_dependencies():
    runtime_files = [
        "scripts/pfiRuntime.sh",
        "scripts/startPFIOS.sh",
        "StartPFIOS.command",
        "scripts/runTests.sh",
        "scripts/verifyPFIOS.sh",
        "scripts/pfiGate.sh",
    ]

    for relative in runtime_files:
        source = _text(relative)
        assert "pip install" not in source
        assert "install --upgrade pip" not in source
        assert "Run scripts/installLockedEnv.sh once" in source or relative in {
            "scripts/startPFIOS.sh",
            "StartPFIOS.command",
            "scripts/pfiGate.sh",
        }


def test_explicit_pfi_python_overrides_stale_project_venv_marker():
    runtime = _text("scripts/pfiRuntime.sh")

    assert 'if [[ -n "${PFI_PYTHON:-}" ]]' in runtime
    assert 'pfi_os_resolve_command "$PFI_PYTHON"' in runtime
    assert runtime.index('pfi_os_resolve_command "$PFI_PYTHON"') < runtime.index('"$project_dir/.venv/bin/python" && -f "$ready_marker"')


def test_pfi_001_gate_interface_and_secret_scan_are_wired_to_ci():
    gate = _text("scripts/pfiGate.sh")
    secret_scan = _text("scripts/secretScan.sh")
    workflow = _text(".github/workflows/smoke.yml")

    for mode in ["fast)", "target)", "full)", "release)"]:
        assert mode in gate
    assert "scripts/secretScan.sh" in gate
    assert "PFI OS gate dependency pytest is missing." in gate
    assert "Run scripts/installLockedEnv.sh once" in gate
    assert "sk-[A-Za-z0-9_-]" in secret_scan
    assert "ghp_[A-Za-z0-9_]" in secret_scan
    assert "AKIA[0-9A-Z]" in secret_scan
    assert "python -m pip install -r requirements.lock" in workflow
    assert "python -m pip install --no-deps -e ." in workflow
    assert "./scripts/secretScan.sh" in workflow


def test_clean_machine_and_artifact_policy_are_documented():
    docs = _text("docs/development/PFI_REPRODUCIBLE_ENV.md")

    for phrase in [
        "Clean Install",
        "Offline Warm Start",
        "Gate Commands",
        "Artifact Policy",
        "must not contain secrets",
        "private holdings",
        "runtime SQLite databases",
    ]:
        assert phrase in docs
