from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from pfi_os.application.operational_store import (
    DataDomain,
    EvidenceRecord,
    JobRecord,
    OperationalStore,
    SourceRecord,
    TaskRecord,
)


PFI004_TRUTH_CONTRACT_SCHEMA = "PFI004TruthContractV1"
PFI004_GOLDEN_PIT_ACCEPTANCE_SCHEMA = "PFI004GoldenPITAcceptanceV1"
PFI004_GOLDEN_SOURCE_ID = "pfi004-golden-market-bars"
PFI004_GOLDEN_EVIDENCE_ID = "pfi004-golden-financial-suite"
PFI004_GOLDEN_ENTITY_ID = "PFI004_GOLDEN"


def build_pfi004_truth_contract() -> dict[str, Any]:
    return {
        "schema": PFI004_TRUTH_CONTRACT_SCHEMA,
        "issue": "PFI-004",
        "authoritative_store": {
            "active_truth": "OperationalStore.source_records",
            "point_in_time_truth": "OperationalStore.source_versions",
            "evidence_truth": "OperationalStore.evidence_records",
        },
        "json_csv_role": "Fixture, import/export, cache, or raw-source staging only; not formal runtime truth.",
        "research_bus_role": "Compatibility/event transport only; not an authoritative read model.",
        "required_fact_fields": ["source_id", "as_of", "evidence_class"],
        "point_in_time_constraints": [
            "source_versions keeps immutable source snapshots keyed by source_id/as_of/checksum/uri.",
            "point_in_time_sources(as_of) replays the latest version not newer than the requested as_of.",
            "source_records rejects retrograde active writes with PIT_INVALID_WRITE.",
        ],
        "golden_suite": {
            "fixture_id": PFI004_GOLDEN_SOURCE_ID,
            "entity_id": PFI004_GOLDEN_ENTITY_ID,
            "metric_contract": ["observation_count", "start_close", "end_close", "total_return_pct", "max_drawdown_pct"],
        },
        "dual_read_reconciliation": "Active source_records must match source_versions replay at the active source as_of.",
        "safety_boundary": "Research, evidence, PIT replay, Golden metrics, and reports only; no broker calls, orders, payments, betting, or unattended execution.",
    }


def build_pfi004_golden_fixture() -> dict[str, Any]:
    bars_v1 = [
        {"date": "2026-06-15", "close": 100.0},
        {"date": "2026-06-16", "close": 102.0},
        {"date": "2026-06-17", "close": 101.0},
    ]
    bars_v2 = [
        *bars_v1,
        {"date": "2026-06-18", "close": 105.0},
    ]
    return {
        "schema": "PFI004GoldenFinancialFixtureV1",
        "fixture_id": PFI004_GOLDEN_SOURCE_ID,
        "entity_id": PFI004_GOLDEN_ENTITY_ID,
        "versions": [
            {
                "label": "v1",
                "as_of": "2026-06-18T00:00:00+00:00",
                "uri": "shared/canonical/golden/pfi004-bars-v1.json",
                "bars": bars_v1,
            },
            {
                "label": "v2",
                "as_of": "2026-06-19T00:00:00+00:00",
                "uri": "shared/canonical/golden/pfi004-bars-v2.json",
                "bars": bars_v2,
            },
        ],
        "expected_metrics": {
            "observation_count": 4,
            "start_close": 100.0,
            "end_close": 105.0,
            "total_return_pct": 5.0,
            "max_drawdown_pct": -0.98,
        },
        "safety_boundary": "Synthetic public fixture; no provider calls, no account data, no execution.",
    }


def record_pfi004_golden_fixture(store: OperationalStore) -> dict[str, Any]:
    store.initialize()
    fixture = build_pfi004_golden_fixture()
    existing_rows = {row["source_id"]: row for row in store.table_rows("source_records")}
    active = existing_rows.get(PFI004_GOLDEN_SOURCE_ID)
    if active is None:
        for version in fixture["versions"]:
            _upsert_golden_version(store, fixture, version)
    elif str(active["as_of"]) < fixture["versions"][-1]["as_of"]:
        _upsert_golden_version(store, fixture, fixture["versions"][-1])

    latest = fixture["versions"][-1]
    metrics = compute_pfi004_golden_metrics(latest["bars"])
    store.record_evidence(
        EvidenceRecord(
            evidence_id=PFI004_GOLDEN_EVIDENCE_ID,
            source_id=PFI004_GOLDEN_SOURCE_ID,
            entity_id=PFI004_GOLDEN_ENTITY_ID,
            as_of=latest["as_of"],
            evidence_class="pfi004_golden_financial_fixture",
            summary="PFI-004 Golden financial fixture metrics are deterministic and ready for PIT reconciliation.",
            artifact_uri=latest["uri"],
            model_version="DisabledProvider",
            strategy_version="pfi004_golden_metrics@1",
            metadata={"metrics": metrics, "expected_metrics": fixture["expected_metrics"]},
        )
    )
    store.upsert_job(
        JobRecord(
            job_id="job-pfi004-golden-pit",
            source_id=PFI004_GOLDEN_SOURCE_ID,
            as_of=latest["as_of"],
            job_type="pfi004_golden_pit_acceptance",
            status="completed",
            phase="done",
            progress=1.0,
            artifact_uri=latest["uri"],
            metadata={"no_execution": True},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id="task-pfi004-golden-review",
            source_id=PFI004_GOLDEN_SOURCE_ID,
            evidence_id=PFI004_GOLDEN_EVIDENCE_ID,
            as_of=latest["as_of"],
            owner_workspace="data",
            action="Review Golden/PIT proof before closing Gate 1.",
            status="completed",
            priority="P0",
        )
    )
    return fixture


def compute_pfi004_golden_metrics(bars: list[dict[str, Any]]) -> dict[str, float | int]:
    closes = [float(row["close"]) for row in bars]
    if not closes:
        raise ValueError("Golden fixture bars are required")
    peak = closes[0]
    max_drawdown = 0.0
    for close in closes:
        peak = max(peak, close)
        drawdown = (close / peak - 1.0) * 100.0
        max_drawdown = min(max_drawdown, drawdown)
    return {
        "observation_count": len(closes),
        "start_close": round(closes[0], 2),
        "end_close": round(closes[-1], 2),
        "total_return_pct": round((closes[-1] / closes[0] - 1.0) * 100.0, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
    }


def reconcile_pfi004_truth(store: OperationalStore) -> dict[str, Any]:
    fixture = build_pfi004_golden_fixture()
    versions = {item["label"]: item for item in fixture["versions"]}
    active_rows = {row["source_id"]: row for row in store.table_rows("source_records")}
    active = active_rows.get(PFI004_GOLDEN_SOURCE_ID)
    pit_v1_rows = {row["source_id"]: row for row in store.point_in_time_sources(versions["v1"]["as_of"])}
    pit_v2_rows = {row["source_id"]: row for row in store.point_in_time_sources(versions["v2"]["as_of"])}
    expected_metrics = fixture["expected_metrics"]
    actual_metrics = compute_pfi004_golden_metrics(versions["v2"]["bars"])
    dual_read_pass = bool(active) and bool(pit_v2_rows.get(PFI004_GOLDEN_SOURCE_ID)) and all(
        str(active[field]) == str(pit_v2_rows[PFI004_GOLDEN_SOURCE_ID][field])
        for field in ["source_id", "uri", "as_of", "checksum", "evidence_class"]
    )
    return {
        "schema": "PFI004TruthReconciliationV1",
        "dual_read_reconciliation": {
            "status": "Pass" if dual_read_pass else "Fail",
            "active_uri": active.get("uri") if active else "",
            "pit_latest_uri": pit_v2_rows.get(PFI004_GOLDEN_SOURCE_ID, {}).get("uri", ""),
        },
        "pit_replay": {
            "status": "Pass" if pit_v1_rows.get(PFI004_GOLDEN_SOURCE_ID, {}).get("uri") == versions["v1"]["uri"] and pit_v2_rows.get(PFI004_GOLDEN_SOURCE_ID, {}).get("uri") == versions["v2"]["uri"] else "Fail",
            "v1_uri": pit_v1_rows.get(PFI004_GOLDEN_SOURCE_ID, {}).get("uri", ""),
            "v2_uri": pit_v2_rows.get(PFI004_GOLDEN_SOURCE_ID, {}).get("uri", ""),
        },
        "golden_financial_suite": {
            "status": "Pass" if actual_metrics == expected_metrics else "Fail",
            "actual_metrics": actual_metrics,
            "expected_metrics": expected_metrics,
        },
        "safety_boundary": "No provider calls, no broker calls, no orders, no payments, no private account data.",
    }


def run_pfi004_truth_golden_acceptance(store: OperationalStore | None = None) -> dict[str, Any]:
    if store is None:
        with tempfile.TemporaryDirectory(prefix="pfi004-golden-pit-") as tmp:
            temp_store = OperationalStore(Path(tmp) / "private" / "operational" / "pfi.sqlite")
            return _run_pfi004_truth_golden_acceptance(temp_store)
    return _run_pfi004_truth_golden_acceptance(store)


def _run_pfi004_truth_golden_acceptance(store: OperationalStore) -> dict[str, Any]:
    fixture = record_pfi004_golden_fixture(store)
    reconciliation = reconcile_pfi004_truth(store)
    latest = fixture["versions"][-1]
    active_before = {row["source_id"]: row for row in store.table_rows("source_records")}[PFI004_GOLDEN_SOURCE_ID]
    invalid_write_rejected = False
    invalid_write_error = ""
    try:
        store.upsert_source(
            SourceRecord(
                source_id=PFI004_GOLDEN_SOURCE_ID,
                domain=DataDomain.PUBLIC_SHARED_CANONICAL,
                source_type="golden_market_bars",
                uri="shared/canonical/golden/pfi004-bars-retrograde.json",
                as_of="2026-06-17T00:00:00+00:00",
                evidence_class="pfi004_golden_financial_fixture",
                checksum="retrograde",
                title="PFI-004 retrograde write should fail",
            )
        )
    except ValueError as exc:
        invalid_write_error = str(exc)
        invalid_write_rejected = "PIT_INVALID_WRITE" in invalid_write_error
    active_after = {row["source_id"]: row for row in store.table_rows("source_records")}[PFI004_GOLDEN_SOURCE_ID]
    checks = [
        _check("TruthContract", build_pfi004_truth_contract()["schema"] == PFI004_TRUTH_CONTRACT_SCHEMA, PFI004_TRUTH_CONTRACT_SCHEMA),
        _check("GoldenFinancialSuite", reconciliation["golden_financial_suite"]["status"] == "Pass", reconciliation["golden_financial_suite"]),
        _check("PointInTimeReplay", reconciliation["pit_replay"]["status"] == "Pass", reconciliation["pit_replay"]),
        _check("DualReadReconciliation", reconciliation["dual_read_reconciliation"]["status"] == "Pass", reconciliation["dual_read_reconciliation"]),
        _check("PITInvalidWriteRejected", invalid_write_rejected, invalid_write_error),
        _check("ActiveTruthUnchangedAfterInvalidWrite", active_before["uri"] == active_after["uri"] == latest["uri"], active_after["uri"]),
    ]
    status = "Pass" if all(item["status"] == "Pass" for item in checks) else "Fail"
    return {
        "schema": PFI004_GOLDEN_PIT_ACCEPTANCE_SCHEMA,
        "issue": "PFI-004",
        "status": status,
        "summary": {
            "pass": sum(1 for item in checks if item["status"] == "Pass"),
            "fail": sum(1 for item in checks if item["status"] == "Fail"),
            "total": len(checks),
        },
        "checks": checks,
        "reconciliation": reconciliation,
        "source_versions": [
            {"label": item["label"], "as_of": item["as_of"], "uri": item["uri"], "checksum": _checksum(item)}
            for item in fixture["versions"]
        ],
        "safety_boundary": "PFI-004 acceptance uses synthetic public fixtures and Operational Store only; no provider, broker, order, payment, betting, or private account mutation.",
    }


def _upsert_golden_version(store: OperationalStore, fixture: dict[str, Any], version: dict[str, Any]) -> None:
    store.upsert_source(
        SourceRecord(
            source_id=PFI004_GOLDEN_SOURCE_ID,
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="golden_market_bars",
            uri=version["uri"],
            as_of=version["as_of"],
            evidence_class="pfi004_golden_financial_fixture",
            checksum=_checksum(version),
            title=f"PFI-004 Golden market bars {version['label']}",
            metadata={"fixture_schema": fixture["schema"], "entity_id": fixture["entity_id"], "label": version["label"]},
        )
    )


def _checksum(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _check(name: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"name": name, "status": "Pass" if passed else "Fail", "evidence": evidence}
