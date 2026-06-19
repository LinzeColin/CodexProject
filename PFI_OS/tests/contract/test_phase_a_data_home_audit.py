from pathlib import Path

from pfi_os.application import audit_data_home_boundary, build_data_home_boundary_contract


def test_data_home_contract_keeps_operational_store_outside_public_repo(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    data_home = tmp_path / "pfi_data_home"

    contract = build_data_home_boundary_contract(project_root, data_home)
    audit = audit_data_home_boundary(project_root, data_home, tracked_paths=["README.md", ".env.example"])

    assert contract["schema"] == "PFIOSPhaseADataHomeBoundaryContractV1"
    assert contract["operational_db_path"].endswith("/private/operational/pfi.sqlite")
    assert contract["no_live_trading"] is True
    assert "Public Git must not contain runtime SQLite" in " ".join(contract["required"])
    assert audit.status == "Pass"
    assert audit.scanned_paths == 2
    assert audit.findings == ()
    assert str(project_root) not in audit.operational_db_path


def test_data_home_audit_fails_when_data_home_or_operational_db_is_inside_repo(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    data_home = project_root / ".pfi_os"

    audit = audit_data_home_boundary(project_root, data_home, tracked_paths=[])
    codes = {finding.code for finding in audit.findings}

    assert audit.status == "Fail"
    assert "DATA_HOME_INSIDE_REPO" in codes
    assert "OPERATIONAL_DB_INSIDE_REPO" in codes


def test_data_home_audit_detects_private_runtime_and_secret_git_fixtures(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    data_home = tmp_path / "pfi_data_home"
    tracked_paths = [
        ".env",
        "data/private/HoldingsBook.json",
        "data/holdings/HoldingsBook.json",
        "data/researchBus/ResearchBus.sqlite",
        "data/researchBus/ResearchBusSnapshot.json",
        "shared/secrets/provider.key",
        "browser/Login Data",
    ]

    audit = audit_data_home_boundary(project_root, data_home, tracked_paths=tracked_paths)
    codes = {finding.code for finding in audit.findings}

    assert audit.status == "Fail"
    assert "ENV_FILE_IN_GIT" in codes
    assert "PRIVATE_PATH_IN_GIT" in codes
    assert "RUNTIME_DATABASE_IN_GIT" in codes
    assert "RESEARCH_BUS_RUNTIME_SNAPSHOT_IN_GIT" in codes
    assert "SECRET_LIKE_FILE_IN_GIT" in codes


def test_data_home_audit_allows_public_safe_placeholders_and_examples(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    data_home = tmp_path / "pfi_data_home"
    tracked_paths = [
        ".env.example",
        "data/holdings/.gitkeep",
        "data/holdings/imports/.gitkeep",
        "data/imports/.gitkeep",
        "data/researchBus/ResearchBusSnapshot.example.json",
        "docs/data/PFI_DATA_BOUNDARIES.md",
    ]

    audit = audit_data_home_boundary(project_root, data_home, tracked_paths=tracked_paths)

    assert audit.status == "Pass"
    assert audit.to_dict()["schema"] == "PFIOSPhaseADataHomeBoundaryAuditV1"
    assert audit.to_dict()["findings"] == []
