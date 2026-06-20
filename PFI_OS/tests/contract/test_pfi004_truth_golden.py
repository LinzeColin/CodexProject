from pathlib import Path

import pytest

from pfi_os.application import (
    DataDomain,
    OperationalStore,
    PFI004_GOLDEN_PIT_ACCEPTANCE_SCHEMA,
    PFI004_TRUTH_CONTRACT_SCHEMA,
    SourceRecord,
    build_pfi004_golden_fixture,
    build_pfi004_truth_contract,
    compute_pfi004_golden_metrics,
    reconcile_pfi004_truth,
    record_pfi004_golden_fixture,
    run_pfi004_truth_golden_acceptance,
)


def _store(tmp_path: Path) -> OperationalStore:
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    return store


def test_pfi004_contract_declares_authoritative_truth_and_boundaries():
    contract = build_pfi004_truth_contract()

    assert contract["schema"] == PFI004_TRUTH_CONTRACT_SCHEMA
    assert contract["issue"] == "PFI-004"
    assert contract["authoritative_store"]["active_truth"] == "OperationalStore.source_records"
    assert contract["authoritative_store"]["point_in_time_truth"] == "OperationalStore.source_versions"
    assert contract["required_fact_fields"] == ["source_id", "as_of", "evidence_class"]
    assert "not formal runtime truth" in contract["json_csv_role"]
    assert "not an authoritative read model" in contract["research_bus_role"]
    assert any("PIT_INVALID_WRITE" in item for item in contract["point_in_time_constraints"])
    assert "no broker calls" in contract["safety_boundary"]
    assert "orders" in contract["safety_boundary"]


def test_pfi004_golden_financial_fixture_metrics_are_deterministic():
    fixture = build_pfi004_golden_fixture()
    metrics = compute_pfi004_golden_metrics(fixture["versions"][-1]["bars"])

    assert fixture["schema"] == "PFI004GoldenFinancialFixtureV1"
    assert metrics == fixture["expected_metrics"]
    assert metrics["observation_count"] == 4
    assert metrics["start_close"] == 100.0
    assert metrics["end_close"] == 105.0
    assert metrics["total_return_pct"] == 5.0
    assert metrics["max_drawdown_pct"] == -0.98


def test_pfi004_records_golden_versions_and_reconciles_dual_read(tmp_path: Path):
    store = _store(tmp_path)

    fixture = record_pfi004_golden_fixture(store)
    reconciliation = reconcile_pfi004_truth(store)
    versions = {item["label"]: item for item in fixture["versions"]}

    assert len(store.table_rows("source_versions")) == 2
    assert store.point_in_time_sources(versions["v1"]["as_of"])[0]["uri"] == versions["v1"]["uri"]
    assert store.point_in_time_sources(versions["v2"]["as_of"])[0]["uri"] == versions["v2"]["uri"]
    assert store.table_rows("source_records")[0]["uri"] == versions["v2"]["uri"]
    assert reconciliation["dual_read_reconciliation"]["status"] == "Pass"
    assert reconciliation["pit_replay"]["status"] == "Pass"
    assert reconciliation["golden_financial_suite"]["status"] == "Pass"
    assert reconciliation["safety_boundary"].startswith("No provider calls")


def test_operational_store_rejects_pit_retrograde_active_write(tmp_path: Path):
    store = _store(tmp_path)
    fixture = record_pfi004_golden_fixture(store)
    latest = fixture["versions"][-1]

    with pytest.raises(ValueError, match="PIT_INVALID_WRITE"):
        store.upsert_source(
            SourceRecord(
                source_id="pfi004-golden-market-bars",
                domain=DataDomain.PUBLIC_SHARED_CANONICAL,
                source_type="golden_market_bars",
                uri="shared/canonical/golden/pfi004-bars-old.json",
                as_of="2026-06-17T00:00:00+00:00",
                evidence_class="pfi004_golden_financial_fixture",
                checksum="retrograde",
            )
        )

    active = store.table_rows("source_records")[0]
    assert active["uri"] == latest["uri"]
    assert active["as_of"] == latest["as_of"]
    assert len(store.table_rows("source_versions")) == 2


def test_pfi004_acceptance_payload_proves_golden_pit_and_no_execution(tmp_path: Path):
    store = _store(tmp_path)

    payload = run_pfi004_truth_golden_acceptance(store)
    checks = {item["name"]: item for item in payload["checks"]}

    assert payload["schema"] == PFI004_GOLDEN_PIT_ACCEPTANCE_SCHEMA
    assert payload["issue"] == "PFI-004"
    assert payload["status"] == "Pass"
    assert payload["summary"] == {"pass": 6, "fail": 0, "total": 6}
    assert checks["GoldenFinancialSuite"]["status"] == "Pass"
    assert checks["PointInTimeReplay"]["status"] == "Pass"
    assert checks["DualReadReconciliation"]["status"] == "Pass"
    assert checks["PITInvalidWriteRejected"]["status"] == "Pass"
    assert checks["ActiveTruthUnchangedAfterInvalidWrite"]["status"] == "Pass"
    assert "no provider" in payload["safety_boundary"].lower()
    assert "broker" in payload["safety_boundary"].lower()
    assert "order" in payload["safety_boundary"].lower()
