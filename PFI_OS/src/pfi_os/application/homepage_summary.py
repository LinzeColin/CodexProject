from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pfi_os.application.operational_store import OperationalStore
from pfi_os.application.source_registry import SourceRegistry
from pfi_os.application.workflow_runtime_read_model import build_workflow_runtime_read_model, empty_workflow_runtime_read_model


def build_homepage_summary(store: OperationalStore | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    operational_store = store or OperationalStore()
    source_registry = SourceRegistry(operational_store)
    source_summary = source_registry.summary(now=now)
    sources = operational_store.table_rows("source_records")
    evidence = operational_store.table_rows("evidence_records")
    jobs = operational_store.table_rows("job_records")
    tasks = operational_store.table_rows("task_records")
    holdings = operational_store.table_rows("holding_snapshots")

    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    latest_as_of = _latest_text([row.get("as_of", "") for row in [*sources, *evidence, *jobs, *tasks, *holdings]])
    cards = [
        {
            "key": "open_tasks",
            "label": "Open tasks",
            "value": str(sum(1 for row in tasks if str(row.get("status", "")).lower() in {"open", "queued", "running"})),
            "detail": _card_detail("task_records", latest_as_of, _status_from_count(len(tasks))),
        },
        {
            "key": "market_events",
            "label": "Market events",
            "value": str(_count_market_sources(sources, evidence)),
            "detail": _card_detail("source_records", _latest_text(row.get("as_of", "") for row in sources), _freshest_status(source_summary)),
        },
        {
            "key": "portfolio_risk",
            "label": "Portfolio risk",
            "value": "Review" if holdings else "Missing",
            "detail": _card_detail("holding_snapshots", _latest_text(row.get("as_of", "") for row in holdings), "Human review" if holdings else "Needs data"),
        },
        {
            "key": "strategy_runs",
            "label": "Strategy runs",
            "value": str(_count_strategy_records(evidence, jobs)),
            "detail": _card_detail("evidence_records", _latest_text(row.get("as_of", "") for row in evidence), _status_from_count(len(evidence))),
        },
    ]
    decision_rows = _decision_rows(tasks, jobs, evidence)
    return {
        "schema": "PFIOSHomeSummaryV1",
        "generated_at": generated_at,
        "as_of": latest_as_of,
        "source_registry": source_summary,
        "metric_cards": cards,
        "decision_rows": decision_rows,
        "evidence_drawer": _evidence_drawer(evidence, sources),
        "workflow_runtime": build_workflow_runtime_read_model(operational_store, now=now),
        "read_model": "OperationalStore -> SourceRegistry -> PFIOSHomeSummaryV1",
        "cache_policy": "Web shell consumes this compact summary; it does not read provider JSON, ResearchBus tables, or private source files directly.",
        "safety_boundary": "Decision support only; no live automatic orders, broker submission, payments, betting, or unattended execution.",
    }


def empty_homepage_summary() -> dict[str, Any]:
    return {
        "schema": "PFIOSHomeSummaryV1",
        "generated_at": "",
        "as_of": "",
        "source_registry": {
            "schema": "PFIOSSourceRegistrySummaryV1",
            "source_count": 0,
            "domain_counts": {},
            "freshness_counts": {},
            "rows": [],
            "private_uri_policy": "Private, private-derived, and secret source URIs are redacted by default.",
            "truth_role": "Operational source_records table is the source registry; ResearchBus remains compatibility events only.",
        },
        "metric_cards": [
            {"key": "open_tasks", "label": "Open tasks", "value": "0", "detail": "source: task_records · updated missing · status Missing"},
            {"key": "market_events", "label": "Market events", "value": "0", "detail": "source: source_records · updated missing · status Missing"},
            {"key": "portfolio_risk", "label": "Portfolio risk", "value": "Missing", "detail": "source: holding_snapshots · updated missing · status Needs data"},
            {"key": "strategy_runs", "label": "Strategy runs", "value": "0", "detail": "source: evidence_records · updated missing · status Missing"},
        ],
        "decision_rows": [],
        "evidence_drawer": {
            "title": "No evidence selected",
            "Evidence": "No operational evidence records are available.",
            "Source": "Operational Store is empty.",
            "Model": "DisabledProvider",
            "Parameters": "",
            "Data lineage": "No lineage yet.",
            "Raw document": "No source record.",
        },
        "workflow_runtime": empty_workflow_runtime_read_model(),
        "read_model": "OperationalStore -> SourceRegistry -> PFIOSHomeSummaryV1",
        "cache_policy": "Web shell consumes this compact summary; it does not read provider JSON, ResearchBus tables, or private source files directly.",
        "safety_boundary": "Decision support only; no live automatic orders, broker submission, payments, betting, or unattended execution.",
    }


def _decision_rows(tasks: list[dict[str, Any]], jobs: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in sorted(tasks, key=lambda item: (str(item.get("priority", "P9")), str(item.get("task_id", ""))))[:6]:
        rows.append(
            {
                "priority": str(row.get("priority", "")),
                "object": str(row.get("owner_workspace", "")),
                "evidence": str(row.get("evidence_id", "")),
                "action": str(row.get("action", "")),
                "status": str(row.get("status", "")),
            }
        )
    if rows:
        return rows
    for row in sorted(jobs, key=lambda item: str(item.get("updated_at", "")), reverse=True)[:3]:
        rows.append(
            {
                "priority": "P1",
                "object": str(row.get("job_type", "")),
                "evidence": str(row.get("source_id", "")),
                "action": f"Review job phase: {row.get('phase', '')}",
                "status": str(row.get("status", "")),
            }
        )
    if rows:
        return rows
    for row in sorted(evidence, key=lambda item: str(item.get("created_at", "")), reverse=True)[:3]:
        rows.append(
            {
                "priority": "P2",
                "object": str(row.get("entity_id", "")),
                "evidence": str(row.get("evidence_class", "")),
                "action": str(row.get("summary", "")),
                "status": "ready",
            }
        )
    return rows


def _evidence_drawer(evidence: list[dict[str, Any]], sources: list[dict[str, Any]]) -> dict[str, str]:
    latest_evidence = sorted(evidence, key=lambda item: str(item.get("created_at", "")), reverse=True)
    latest = latest_evidence[0] if latest_evidence else {}
    source_by_id = {str(row.get("source_id", "")): row for row in sources}
    source = source_by_id.get(str(latest.get("source_id", "")), {})
    return {
        "title": f"{latest.get('entity_id', 'PFI')} · Operational evidence",
        "Evidence": str(latest.get("summary", "No operational evidence records are available.")),
        "Source": f"{source.get('source_type', 'Missing')} · {source.get('title', '')}".strip(" ·"),
        "Model": str(latest.get("model_version", "DisabledProvider") or "DisabledProvider"),
        "Parameters": str(latest.get("metadata_json", "{}")),
        "Data lineage": f"{source.get('source_id', 'source missing')} -> {latest.get('evidence_id', 'evidence missing')}",
        "Raw document": str(latest.get("artifact_uri", "") or source.get("uri", "No source record.")),
    }


def _count_market_sources(sources: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> int:
    return sum(1 for row in sources if "market" in str(row.get("source_type", "")).lower()) + sum(
        1 for row in evidence if "market" in str(row.get("evidence_class", "")).lower()
    )


def _count_strategy_records(evidence: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> int:
    return sum(1 for row in evidence if str(row.get("strategy_version", ""))) + sum(1 for row in jobs if "strategy" in str(row.get("job_type", "")).lower())


def _latest_text(values) -> str:
    clean = sorted((str(item or "").strip() for item in values if str(item or "").strip()), reverse=True)
    return clean[0] if clean else "missing"


def _status_from_count(count: int) -> str:
    return "Ready" if count else "Missing"


def _freshest_status(source_summary: dict[str, Any]) -> str:
    counts = source_summary.get("freshness_counts", {})
    for status in ("Fresh", "Delayed", "Stale", "Expired", "Unknown"):
        if counts.get(status):
            return status
    return "Missing"


def _card_detail(source: str, as_of: str, status: str) -> str:
    return f"source: {source} · updated {as_of} · status {status}"
