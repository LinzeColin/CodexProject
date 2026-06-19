from pathlib import Path

import pytest

from pfi_os.application import DataDomain, OperationalStore, SourceRegistry, ingest_file_source


def test_file_source_ingestion_registers_public_relative_source_with_checksum(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    source_path = project_root / "data" / "commandCenter" / "PFICommandCenter_latest.json"
    source_path.parent.mkdir(parents=True)
    source_path.write_text('{"schema":"PFICommandCenterV1"}', encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_file_source(
        store,
        project_root=project_root,
        file_path=source_path,
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="command_center_cache",
        as_of="2026-06-19T09:30:00+00:00",
        evidence_class="local_operational_cache",
        title="Command center latest",
    )
    duplicate = ingest_file_source(
        store,
        project_root=project_root,
        file_path=source_path,
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="command_center_cache",
        as_of="2026-06-19T09:30:00+00:00",
        evidence_class="local_operational_cache",
    )
    source = store.table_rows("source_records")[0]

    assert result.schema == "PFIOSFileSourceIngestionV1"
    assert result.source_id == duplicate.source_id
    assert result.uri == "data/commandCenter/PFICommandCenter_latest.json"
    assert result.checksum == source["checksum"]
    assert result.byte_size == len('{"schema":"PFICommandCenterV1"}'.encode("utf-8"))
    assert len(store.table_rows("source_versions")) == 1
    assert "project_relative" in source["metadata_json"]


def test_file_source_ingestion_rejects_public_absolute_source_outside_project(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    with pytest.raises(ValueError, match="PUBLIC_SOURCE_OUTSIDE_PROJECT"):
        ingest_file_source(
            store,
            project_root=project_root,
            file_path=outside,
            domain=DataDomain.PUBLIC_SHARED_RAW,
            source_type="public_fixture",
            as_of="2026-06-19",
            evidence_class="public_fixture",
        )


def test_file_source_ingestion_rejects_private_source_inside_public_repo(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    private_path = project_root / "data" / "holdings" / "HoldingsBook.json"
    private_path.parent.mkdir(parents=True)
    private_path.write_text("{}", encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    with pytest.raises(ValueError, match="PRIVATE_SOURCE_INSIDE_PUBLIC_REPO"):
        ingest_file_source(
            store,
            project_root=project_root,
            file_path=private_path,
            domain=DataDomain.PRIVATE_USER,
            source_type="holding_snapshot",
            as_of="2026-06-19",
            evidence_class="private_user_fact",
        )


def test_file_source_ingestion_allows_private_source_outside_repo_and_registry_redacts_uri(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    project_root.mkdir()
    private_path = tmp_path / "private_home" / "HoldingsBook.json"
    private_path.parent.mkdir(parents=True)
    private_path.write_text('{"holdings":[]}', encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    result = ingest_file_source(
        store,
        project_root=project_root,
        file_path=private_path,
        domain=DataDomain.PRIVATE_USER,
        source_type="holding_snapshot",
        as_of="2026-06-19T09:30:00+00:00",
        evidence_class="private_user_fact",
    )
    registry = SourceRegistry(store).summary()

    assert result.uri == str(private_path.resolve(strict=False))
    assert registry["rows"][0]["uri"] == "[redacted-private-uri]"
    assert registry["domain_counts"][DataDomain.PRIVATE_USER.value] == 1


def test_file_source_ingestion_rejects_ephemeral_and_missing_files(tmp_path: Path):
    project_root = tmp_path / "PFI_OS"
    source_path = project_root / "data" / "cache" / "runtime.tmp"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("runtime", encoding="utf-8")
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    with pytest.raises(ValueError, match="EPHEMERAL_SOURCE_NOT_INGESTIBLE"):
        ingest_file_source(
            store,
            project_root=project_root,
            file_path=source_path,
            domain=DataDomain.EPHEMERAL,
            source_type="runtime_cache",
            as_of="2026-06-19",
            evidence_class="runtime_cache",
        )
    with pytest.raises(FileNotFoundError):
        ingest_file_source(
            store,
            project_root=project_root,
            file_path=project_root / "missing.json",
            domain=DataDomain.PUBLIC_SHARED_RAW,
            source_type="missing",
            as_of="2026-06-19",
            evidence_class="missing",
        )
