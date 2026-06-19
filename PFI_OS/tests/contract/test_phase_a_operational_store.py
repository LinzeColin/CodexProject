import json
import sqlite3
from pathlib import Path

import pytest

from pfi_os.application import (
    DataDomain,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    SourceRecord,
    TaskRecord,
    build_phase_a_data_foundation_contract,
    default_data_home,
    default_operational_db_path,
)


def test_default_operational_store_path_uses_private_data_home_not_repo(tmp_path: Path):
    env = {"PFI_OS_DATA_HOME": str(tmp_path / "data_home")}

    data_home = default_data_home(env)
    db_path = default_operational_db_path(data_home)

    assert data_home == tmp_path / "data_home"
    assert db_path == tmp_path / "data_home" / "private" / "operational" / "pfi.sqlite"
    assert "PFI_OS/data" not in str(db_path)


def test_phase_a_contract_declares_domains_tables_and_internal_bus_role(tmp_path: Path):
    contract = build_phase_a_data_foundation_contract(tmp_path / "data_home")

    assert contract["schema"] == "PFIOSPhaseADataFoundationContractV1"
    assert contract["research_bus_role"] == "internal_event_compatibility_layer"
    assert contract["no_live_trading"] is True
    assert set(contract["domains"]) == {item.value for item in DataDomain}
    assert contract["required_fact_fields"] == ["source_id", "as_of", "evidence_class"]
    assert set(contract["official_tables"]) == {
        "source_records",
        "source_versions",
        "entity_records",
        "evidence_records",
        "job_records",
        "task_records",
        "holding_snapshots",
    }
    assert "outside Git" in contract["git_policy"]


def test_operational_store_initializes_official_tables_with_foreign_keys(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    db_path = store.initialize()

    with sqlite3.connect(db_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        foreign_keys = conn.execute("PRAGMA foreign_key_list(evidence_records)").fetchall()

    assert {"source_records", "source_versions", "entity_records", "evidence_records", "job_records", "task_records", "holding_snapshots"} <= tables
    assert any(row[2] == "source_records" for row in foreign_keys)


def test_store_records_source_evidence_job_task_and_holding_snapshot(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    source = SourceRecord(
        source_id="src-market-2026-06-19",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="market_event_digest",
        uri="shared/canonical/market/events/2026-06-19.json",
        as_of="2026-06-19T08:45:00+10:00",
        evidence_class="cached_public_fact",
        title="US market event digest",
    )
    store.upsert_source(source)
    store.upsert_entity("SPY", entity_type="ETF", display_name="SPY", canonical_symbol="SPY")
    evidence = EvidenceRecord(
        evidence_id="ev-spy-daily-brief",
        source_id=source.source_id,
        entity_id="SPY",
        as_of=source.as_of,
        evidence_class=source.evidence_class,
        summary="Cached market digest is available for review.",
        artifact_uri="shared/canonical/market/events/2026-06-19.json",
    )
    store.record_evidence(evidence)
    store.upsert_job(
        JobRecord(
            job_id="job-refresh-market",
            source_id=source.source_id,
            as_of=source.as_of,
            job_type="refresh_cached_market_slice",
            status="running",
            phase="fetch",
            progress=0.4,
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id="task-review-spy",
            source_id=source.source_id,
            evidence_id=evidence.evidence_id,
            as_of=source.as_of,
            owner_workspace="research",
            action="Review cached evidence and invalidation conditions.",
        )
    )
    store.upsert_holding_snapshot(
        snapshot_id="holdings-main-2026-06-19",
        source_id=source.source_id,
        evidence_id=evidence.evidence_id,
        as_of=source.as_of,
        portfolio_id="Main",
        holdings=[{"symbol": "SPY", "weight": 0.25}],
        domain=DataDomain.PRIVATE_USER,
    )

    assert store.table_rows("source_records")[0]["source_id"] == source.source_id
    assert store.table_rows("source_versions")[0]["source_id"] == source.source_id
    assert store.table_rows("evidence_records")[0]["evidence_class"] == "cached_public_fact"
    assert store.table_rows("job_records")[0]["progress"] == 0.4
    task = store.table_rows("task_records")[0]
    assert task["human_review_required"] == 1
    holding = store.table_rows("holding_snapshots")[0]
    assert holding["data_domain"] == DataDomain.PRIVATE_USER.value
    assert json.loads(holding["holdings_json"]) == [{"symbol": "SPY", "weight": 0.25}]


def test_store_fails_closed_when_source_as_of_or_evidence_fields_are_missing(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    with pytest.raises(ValueError, match="source_id is required"):
        store.upsert_source(
            SourceRecord(
                source_id="",
                domain=DataDomain.PUBLIC_SHARED_RAW,
                source_type="public_csv",
                uri="shared/raw/sample.csv",
                as_of="2026-06-19",
                evidence_class="raw_public_fixture",
            )
        )
    with pytest.raises(ValueError, match="as_of is required"):
        store.record_evidence(
            EvidenceRecord(
                evidence_id="ev-missing-asof",
                source_id="src-missing",
                entity_id="SPY",
                as_of="",
                evidence_class="cached_public_fact",
                summary="missing as-of",
            )
        )
    with pytest.raises(ValueError, match="evidence_id is required"):
        store.upsert_task(
            TaskRecord(
                task_id="task-missing-evidence",
                source_id="src-missing",
                evidence_id="",
                as_of="2026-06-19",
                owner_workspace="research",
                action="Review evidence.",
            )
        )


def test_table_reader_allows_only_official_operational_tables(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()

    with pytest.raises(ValueError, match="Unknown operational table"):
        store.table_rows("sqlite_master")
