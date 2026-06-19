from pathlib import Path

from pfi_os.application import (
    DataDomain,
    EvidenceRecord,
    HoldingSnapshotRepository,
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
