import json
from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import (
    DataDomain,
    EvidenceRecord,
    OperationalStore,
    PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA,
    SourceRecord,
    build_phase_d_backup_restore_contract,
    default_operational_db_path,
    run_phase_d_backup_restore_acceptance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_phase_d_backup_restore_contract_declares_private_runtime_artifact_policy(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    data_home = tmp_path / "pfi_data_home"

    contract = build_phase_d_backup_restore_contract(project_root, data_home)

    assert contract["schema"] == "PFIOSPhaseDBackupRestoreContractV1"
    assert contract["acceptance_schema"] == PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA
    assert contract["artifact_policy"]["backup_dir"] == "$PFI_OS_DATA_HOME/runtime/backups"
    assert contract["artifact_policy"]["restore_staging_dir"] == "$PFI_OS_DATA_HOME/runtime/restore_staging"
    assert contract["artifact_policy"]["commit_sqlite_to_git"] is False
    assert contract["artifact_policy"]["public_summary_must_be_sanitized"] is True
    assert contract["verification_policy"]["sqlite_integrity_check"] is True
    assert contract["safety_boundary"]["mutates_operational_db"] is False
    assert contract["safety_boundary"]["broker_calls"] is False
    assert contract["safety_boundary"]["order_execution"] is False


def test_phase_d_backup_restore_acceptance_writes_private_backup_and_sanitized_summary(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    data_home = tmp_path / "pfi_data_home"
    _seed_operational_store(data_home)

    payload = run_phase_d_backup_restore_acceptance(
        project_root,
        data_home,
        now=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
    )

    backup_path = Path(payload["private_artifacts"]["backup_path"])
    restored_path = Path(payload["private_artifacts"]["restored_path"])
    manifest_path = Path(payload["private_artifacts"]["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    public_summary_text = json.dumps(payload["sanitized_public_summary"], sort_keys=True)
    manifest_text = json.dumps(manifest, sort_keys=True)

    assert payload["schema"] == PHASE_D_BACKUP_RESTORE_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["run_id"] == "phase_d_backup_restore_20260620T120000Z"
    assert backup_path.exists()
    assert restored_path.exists()
    assert manifest_path.exists()
    assert not backup_path.is_relative_to(project_root)
    assert not restored_path.is_relative_to(project_root)
    assert payload["private_artifacts"]["commit_to_git"] is False
    assert payload["source_table_counts"] == payload["restored_table_counts"]
    assert payload["source_table_counts"]["source_records"] == 1
    assert payload["source_table_counts"]["evidence_records"] == 1
    assert payload["sanitized_public_summary"]["failed_checks"] == []
    assert "$PFI_OS_DATA_HOME/runtime/backups" in public_summary_text
    assert str(tmp_path) not in public_summary_text
    assert str(tmp_path) not in manifest_text
    assert manifest["commit_to_git"] is False
    assert manifest["source_table_counts"] == manifest["restored_table_counts"]
    assert {check["status"] for check in payload["checks"]} == {"Pass"}
    assert payload["safety_boundary"]["creates_private_runtime_artifacts"] is True
    assert payload["safety_boundary"]["holding_mutation"] is False


def test_phase_d_backup_restore_acceptance_blocks_missing_operational_db_without_creating_artifacts(
    tmp_path: Path,
):
    project_root = _minimal_project_root(tmp_path)
    data_home = tmp_path / "pfi_data_home"

    payload = run_phase_d_backup_restore_acceptance(project_root, data_home)
    failed_codes = {check["code"] for check in payload["checks"] if check["status"] == "Fail"}

    assert payload["status"] == "Blocked"
    assert "OPERATIONAL_DB_EXISTS" in failed_codes
    assert not (data_home / "runtime" / "backups").exists()
    assert not (data_home / "runtime" / "restore_staging").exists()
    assert payload["sanitized_public_summary"]["manifest_written"] is False
    assert payload["safety_boundary"]["starts_services"] is False
    assert payload["safety_boundary"]["network_calls"] is False


def test_phase_d_backup_restore_acceptance_blocks_repo_local_data_home(tmp_path: Path):
    project_root = _minimal_project_root(tmp_path)
    data_home = project_root / ".pfi_os"
    _seed_operational_store(data_home)

    payload = run_phase_d_backup_restore_acceptance(project_root, data_home)
    failed_codes = {check["code"] for check in payload["checks"] if check["status"] == "Fail"}

    assert payload["status"] == "Blocked"
    assert "DATA_HOME_OUTSIDE_REPO" in failed_codes
    assert "OPERATIONAL_DB_OUTSIDE_REPO" in failed_codes
    assert not (data_home / "runtime" / "backups").exists()
    assert payload["private_artifacts"]["commit_to_git"] is False


def test_phase_d_docs_and_handoff_reference_backup_restore_acceptance():
    phase_doc = (PROJECT_ROOT / "docs" / "phase" / "PHASE_D_DEPLOYMENT_READINESS.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    plan = (PROJECT_ROOT / "PLANS.md").read_text(encoding="utf-8")
    dev_record = (PROJECT_ROOT / "docs" / "development" / "PFI_PHASE_0_TO_A_RECORD.md").read_text(
        encoding="utf-8"
    )

    assert "PFIOSPhaseDBackupRestoreAcceptanceV1" in phase_doc
    assert "backup/restore acceptance complete" in handoff
    assert "Phase D backup/restore acceptance" in plan
    assert "tests/contract/test_phase_d_backup_restore_acceptance.py" in dev_record


def _seed_operational_store(data_home: Path) -> None:
    store = OperationalStore(default_operational_db_path(data_home))
    store.initialize()
    store.upsert_source(
        SourceRecord(
            source_id="source_phase_d_acceptance",
            domain=DataDomain.PRIVATE_DERIVED,
            source_type="phase_d_acceptance_fixture",
            uri="private://phase-d/acceptance",
            as_of="2026-06-20",
            evidence_class="backup_restore_fixture",
            observed_at="2026-06-20T12:00:00+00:00",
            title="Phase D backup restore fixture",
            checksum="fixture",
            metadata={"scope": "contract"},
        )
    )
    store.record_evidence(
        EvidenceRecord(
            evidence_id="evidence_phase_d_acceptance",
            source_id="source_phase_d_acceptance",
            entity_id="PFI_OS",
            as_of="2026-06-20",
            evidence_class="backup_restore_fixture",
            summary="Phase D backup/restore acceptance fixture.",
            artifact_uri="private://phase-d/acceptance",
            model_version="DisabledProvider",
            metadata={"private_safe": True},
        )
    )


def _minimal_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "PFI_OS"
    for relative_path in [
        "web/index.html",
        "src/pfi_os/application/operational_store.py",
        "scripts/startPFIOS.sh",
        "scripts/statusPFIOS.sh",
        "macos/PFI_OS.app",
    ]:
        path = root / relative_path
        if relative_path.endswith(".app"):
            path.mkdir(parents=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ok", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = \"pfi-os\"\n", encoding="utf-8")
    return root
