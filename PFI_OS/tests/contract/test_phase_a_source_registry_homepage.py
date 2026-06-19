from datetime import datetime, timezone
from pathlib import Path

from pfi_os.application import (
    DataDomain,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    SourceRecord,
    SourceRegistry,
    TaskRecord,
    build_homepage_summary,
)


def test_source_registry_redacts_private_uris_and_reports_freshness(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    registry = SourceRegistry(store)
    registry.register_source(
        SourceRecord(
            source_id="src-public",
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="market_event_digest",
            uri="shared/canonical/market/events.json",
            as_of="2026-06-19T08:00:00+00:00",
            evidence_class="cached_public_fact",
        )
    )
    registry.register_source(
        SourceRecord(
            source_id="src-private",
            domain=DataDomain.PRIVATE_USER,
            source_type="holding_snapshot",
            uri="/Users/example/private/holdings.csv",
            as_of="2026-06-18T08:00:00+00:00",
            evidence_class="private_user_fact",
        )
    )

    summary = registry.summary(now=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc))
    rows = {row["source_id"]: row for row in summary["rows"]}

    assert summary["schema"] == "PFIOSSourceRegistrySummaryV1"
    assert summary["domain_counts"][DataDomain.PUBLIC_SHARED_CANONICAL.value] == 1
    assert summary["domain_counts"][DataDomain.PRIVATE_USER.value] == 1
    assert rows["src-public"]["uri"] == "shared/canonical/market/events.json"
    assert rows["src-public"]["freshness"] == "Fresh"
    assert rows["src-private"]["uri"] == "[redacted-private-uri]"
    assert rows["src-private"]["freshness"] == "Stale"
    assert summary["truth_role"] == "Operational source_records table is the source registry; ResearchBus remains compatibility events only."


def test_source_registry_supports_point_in_time_source_versions(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    registry = SourceRegistry(store)
    registry.register_source(
        SourceRecord(
            source_id="src-market",
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="market_event_digest",
            uri="shared/canonical/market/events-v1.json",
            as_of="2026-06-18T08:00:00+00:00",
            evidence_class="cached_public_fact",
            checksum="v1",
        )
    )
    registry.register_source(
        SourceRecord(
            source_id="src-market",
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="market_event_digest",
            uri="shared/canonical/market/events-v2.json",
            as_of="2026-06-19T08:00:00+00:00",
            evidence_class="cached_public_fact",
            checksum="v2",
        )
    )

    old_rows = registry.point_in_time_rows("2026-06-18T23:59:00+00:00")
    new_rows = registry.point_in_time_rows("2026-06-19T23:59:00+00:00")

    assert len(store.table_rows("source_versions")) == 2
    assert old_rows[0].uri == "shared/canonical/market/events-v1.json"
    assert new_rows[0].uri == "shared/canonical/market/events-v2.json"
    assert store.table_rows("source_records")[0]["uri"] == "shared/canonical/market/events-v2.json"


def test_homepage_summary_uses_operational_store_read_model(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    source = SourceRecord(
        source_id="src-market-brief",
        domain=DataDomain.PUBLIC_SHARED_CANONICAL,
        source_type="market_event_digest",
        uri="shared/canonical/market/events.json",
        as_of="2026-06-19T08:45:00+00:00",
        evidence_class="cached_public_fact",
        title="Market digest",
    )
    store.upsert_source(source)
    store.upsert_entity("SPY", entity_type="ETF", display_name="SPY", canonical_symbol="SPY")
    evidence = EvidenceRecord(
        evidence_id="ev-spy-market",
        source_id=source.source_id,
        entity_id="SPY",
        as_of=source.as_of,
        evidence_class="market_digest",
        summary="SPY cached market evidence is ready.",
        artifact_uri="shared/canonical/market/events.json",
        strategy_version="ma_crossover@1",
    )
    store.record_evidence(evidence)
    store.upsert_task(
        TaskRecord(
            task_id="task-spy-review",
            source_id=source.source_id,
            evidence_id=evidence.evidence_id,
            as_of=source.as_of,
            owner_workspace="research",
            action="Review SPY evidence.",
            priority="P0",
        )
    )
    store.upsert_job(
        JobRecord(
            job_id="job-strategy-validation",
            source_id=source.source_id,
            as_of=source.as_of,
            job_type="strategy_validation",
            status="completed",
            phase="done",
            progress=1.0,
        )
    )
    store.upsert_holding_snapshot(
        snapshot_id="holdings-main",
        source_id=source.source_id,
        evidence_id=evidence.evidence_id,
        as_of=source.as_of,
        portfolio_id="Main",
        holdings=[{"symbol": "SPY", "weight": 0.25}],
    )

    summary = build_homepage_summary(store, now=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc))
    cards = {card["key"]: card for card in summary["metric_cards"]}

    assert summary["schema"] == "PFIOSHomeSummaryV1"
    assert summary["read_model"] == "OperationalStore -> SourceRegistry -> PFIOSHomeSummaryV1"
    assert "does not read provider JSON" in summary["cache_policy"]
    assert cards["open_tasks"]["value"] == "1"
    assert cards["market_events"]["value"] == "2"
    assert cards["portfolio_risk"]["value"] == "Review"
    assert cards["strategy_runs"]["value"] == "2"
    assert summary["decision_rows"][0]["priority"] == "P0"
    assert summary["evidence_drawer"]["Evidence"] == "SPY cached market evidence is ready."
    assert "src-market-brief -> ev-spy-market" in summary["evidence_drawer"]["Data lineage"]


def test_streamlit_web_shell_injects_homepage_summary_without_direct_json_reads(tmp_path: Path):
    from pfi_os.app.streamlit_app import _pfi_web_shell_html

    summary = {
        "schema": "PFIOSHomeSummaryV1",
        "as_of": "2026-06-19T08:45:00+00:00",
        "metric_cards": [{"key": "open_tasks", "label": "Open tasks", "value": "9", "detail": "source: task_records · updated now · status Ready"}],
        "decision_rows": [{"priority": "P0", "object": "research", "evidence": "ev", "action": "Review", "status": "open"}],
        "evidence_drawer": {"title": "Injected", "Evidence": "Injected evidence"},
    }

    rendered = _pfi_web_shell_html(summary)

    assert '"schema": "PFIOSHomeSummaryV1"' in rendered
    assert '"value": "9"' in rendered
    assert "operational_store:task_records" in rendered
    assert "data/systemAudit/latest" not in rendered
    assert "data/marketEvents/latest" not in rendered
