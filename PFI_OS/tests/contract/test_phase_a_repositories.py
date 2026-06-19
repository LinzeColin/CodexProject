from pathlib import Path

from pfi_os.application import (
    DataDomain,
    EntityRepository,
    EvidenceRecord,
    EvidenceRepository,
    HoldingSnapshotRepository,
    JobRepository,
    OperationalStore,
    SourceRecord,
    TaskRepository,
)


def test_task_repository_creates_stable_human_review_tasks_and_filters_open(tmp_path: Path):
    store, source, evidence = _seed_store(tmp_path)
    repository = TaskRepository(store)

    first = repository.upsert_review_task(
        source_id=source.source_id,
        evidence_id=evidence.evidence_id,
        as_of=source.as_of,
        owner_workspace="research",
        action="Review evidence and invalidation conditions.",
        priority="P0",
    )
    second = repository.upsert_review_task(
        source_id=source.source_id,
        evidence_id=evidence.evidence_id,
        as_of=source.as_of,
        owner_workspace="research",
        action="Review evidence and invalidation conditions.",
        priority="P0",
    )

    assert first.task_id == second.task_id
    assert first.human_review_required is True
    assert repository.open_items(workspace="research")[0].priority == "P0"

    closed = repository.set_status(first.task_id, "completed")
    assert closed.status == "completed"
    assert repository.open_items(workspace="research") == []


def test_holding_snapshot_repository_defaults_to_private_user_domain_and_returns_latest(tmp_path: Path):
    store, source, evidence = _seed_store(tmp_path)
    repository = HoldingSnapshotRepository(store)

    older = repository.upsert_snapshot(
        source_id=source.source_id,
        evidence_id=evidence.evidence_id,
        as_of="2026-06-18T08:45:00+00:00",
        portfolio_id="Main",
        holdings=[{"symbol": "SPY", "weight": 0.2, "private_note": "drop me"}],
    )
    newer = repository.upsert_snapshot(
        source_id=source.source_id,
        evidence_id=evidence.evidence_id,
        as_of="2026-06-19T08:45:00+00:00",
        portfolio_id="Main",
        holdings=[{"symbol": "SPY", "weight": 0.25, "position_value": 1000.0}],
    )

    latest = repository.latest_for_portfolio("Main")

    assert older.data_domain == DataDomain.PRIVATE_USER.value
    assert latest == newer
    assert latest.holdings[0]["symbol"] == "SPY"
    assert latest.holdings[0]["weight"] == 0.25
    assert "private_note" not in latest.holdings[0]
    assert repository.latest_for_portfolio("Missing") is None


def test_entity_repository_upserts_searches_and_resolves_symbols(tmp_path: Path):
    store, _, _ = _seed_store(tmp_path)
    repository = EntityRepository(store)

    spy = repository.upsert_entity(
        "SPY",
        entity_type="ETF",
        display_name="SPDR S&P 500 ETF",
        canonical_symbol="SPY",
        metadata={"market": "US"},
    )
    repository.upsert_entity(
        "AAPL",
        entity_type="Equity",
        display_name="Apple Inc.",
        canonical_symbol="AAPL",
        metadata={"market": "US"},
    )

    assert spy.metadata["market"] == "US"
    assert repository.by_symbol("spy") == spy
    assert repository.search(text="apple")[0].entity_id == "AAPL"
    assert repository.search(entity_type="ETF")[0].entity_id == "SPY"
    assert repository.by_symbol("") is None


def test_evidence_repository_records_stable_searchable_evidence(tmp_path: Path):
    store, source, _ = _seed_store(tmp_path)
    repository = EvidenceRepository(store)

    first = repository.record(
        source_id=source.source_id,
        entity_id="SPY",
        as_of="2026-06-18T08:45:00+00:00",
        evidence_class="market_digest",
        summary="Older SPY market evidence.",
        artifact_uri="shared/canonical/market/older.json",
        strategy_version="ma@1",
    )
    duplicate = repository.record(
        source_id=source.source_id,
        entity_id="SPY",
        as_of="2026-06-18T08:45:00+00:00",
        evidence_class="market_digest",
        summary="Older SPY market evidence.",
        artifact_uri="shared/canonical/market/older.json",
        strategy_version="ma@1",
    )
    latest = repository.record(
        source_id=source.source_id,
        entity_id="SPY",
        as_of="2026-06-19T08:45:00+00:00",
        evidence_class="market_digest",
        summary="Latest SPY market evidence.",
        artifact_uri="shared/canonical/market/latest.json",
        metadata={"source_adapter": "contract-test"},
    )

    assert first.evidence_id == duplicate.evidence_id
    assert repository.latest_for_entity("SPY").evidence_id == latest.evidence_id
    assert repository.search(text="older")[0].artifact_uri == "shared/canonical/market/older.json"
    assert repository.search(evidence_class="market_digest", limit=1)[0].summary == "Latest SPY market evidence."
    assert latest.metadata["source_adapter"] == "contract-test"


def test_job_repository_tracks_execution_lifecycle_and_active_jobs(tmp_path: Path):
    store, source, _ = _seed_store(tmp_path)
    repository = JobRepository(store)

    started = repository.start(
        source_id=source.source_id,
        as_of=source.as_of,
        job_type="source_ingestion",
        metadata={"source_adapter": "contract-test"},
    )
    same = repository.start(
        source_id=source.source_id,
        as_of=source.as_of,
        job_type="source_ingestion",
    )

    assert started.job_id == same.job_id
    assert repository.active_jobs(job_type="source_ingestion")[0].status == "running"
    completed = repository.complete(started.job_id, artifact_uri="shared/canonical/output.json", metadata={"row_count": 2})
    assert completed.status == "completed"
    assert completed.phase == "done"
    assert completed.progress == 1.0
    assert completed.metadata["row_count"] == 2
    assert repository.active_jobs() == []

    failed_seed = repository.start(source_id=source.source_id, as_of=source.as_of, job_type="evidence_refresh", job_id="job-fail")
    failed = repository.fail(failed_seed.job_id, error_message="provider unavailable")
    assert failed.status == "failed"
    assert failed.retry_count == 1
    assert failed.error_message == "provider unavailable"


def _seed_store(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    source = SourceRecord(
        source_id="src-repo-test",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="market_event_digest",
        uri="shared/canonical/market/events.json",
        as_of="2026-06-19T08:45:00+00:00",
        evidence_class="cached_public_fact",
    )
    store.upsert_source(source)
    store.upsert_entity("SPY", entity_type="ETF", display_name="SPY", canonical_symbol="SPY")
    evidence = EvidenceRecord(
        evidence_id="ev-repo-test",
        source_id=source.source_id,
        entity_id="SPY",
        as_of=source.as_of,
        evidence_class="market_digest",
        summary="Evidence ready.",
    )
    store.record_evidence(evidence)
    return store, source, evidence
