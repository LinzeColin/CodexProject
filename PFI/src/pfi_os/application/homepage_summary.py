from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pfi_os.application.operational_store import OperationalStore
from pfi_os.application.source_registry import SourceRegistry
from pfi_os.application.workflow_runtime_read_model import build_workflow_runtime_read_model, empty_workflow_runtime_read_model

RETIRED_PUBLIC_FRAGMENTS = (
    "Token" + " ROI",
    "E" + "VA" + "Token",
    "E" + "VA" + "CommandCenter",
    "E" + "VA" + "_OS",
    "E" + "VA" + " OS",
)
SAFE_METADATA_KEYS = (
    "source_adapter",
    "schema",
    "command_status",
    "scorecard_count",
    "risk_gate_count",
    "action_count",
    "artifact_uri",
)


def build_homepage_summary(store: OperationalStore | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    operational_store = store or OperationalStore()
    source_registry = SourceRegistry(operational_store)
    source_summary = _without_retired_source_rows(source_registry.summary(now=now))
    sources = _without_retired_rows(operational_store.table_rows("source_records"))
    evidence = _without_retired_rows(operational_store.table_rows("evidence_records"))
    jobs = _without_retired_rows(operational_store.table_rows("job_records"))
    tasks = _without_retired_rows(operational_store.table_rows("task_records"))
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
        "workflow_runtime": _sanitize_public_payload(build_workflow_runtime_read_model(operational_store, now=now)),
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
    for row in sorted(_without_retired_rows(tasks), key=lambda item: (str(item.get("priority", "P9")), str(item.get("task_id", ""))))[:6]:
        rows.append(
            {
                "priority": _safe_public_text(row.get("priority", "")),
                "object": _safe_public_text(row.get("owner_workspace", "")),
                "evidence": _safe_public_text(row.get("evidence_id", "")),
                "action": _safe_public_text(row.get("action", "")),
                "status": _safe_public_text(row.get("status", "")),
            }
        )
    if rows:
        return rows
    for row in sorted(_without_retired_rows(jobs), key=lambda item: str(item.get("updated_at", "")), reverse=True)[:3]:
        rows.append(
            {
                "priority": "P1",
                "object": _safe_public_text(row.get("job_type", "")),
                "evidence": _safe_public_text(row.get("source_id", "")),
                "action": _safe_public_text(f"Review job phase: {row.get('phase', '')}"),
                "status": _safe_public_text(row.get("status", "")),
            }
        )
    if rows:
        return rows
    for row in sorted(_without_retired_rows(evidence), key=lambda item: str(item.get("created_at", "")), reverse=True)[:3]:
        rows.append(
            {
                "priority": "P2",
                "object": _safe_public_text(row.get("entity_id", "")),
                "evidence": _safe_public_text(row.get("evidence_class", "")),
                "action": _safe_public_text(row.get("summary", "")),
                "status": "ready",
            }
        )
    return rows


def _evidence_drawer(evidence: list[dict[str, Any]], sources: list[dict[str, Any]]) -> dict[str, str]:
    latest_evidence = sorted(_without_retired_rows(evidence), key=lambda item: str(item.get("created_at", "")), reverse=True)
    latest = latest_evidence[0] if latest_evidence else {}
    source_by_id = {str(row.get("source_id", "")): row for row in _without_retired_rows(sources)}
    source = source_by_id.get(str(latest.get("source_id", "")), {})
    return {
        "title": f"{_safe_public_text(latest.get('entity_id', 'PFI'))} · Operational evidence",
        "Evidence": _safe_public_text(latest.get("summary", "No operational evidence records are available.")),
        "Source": _safe_public_text(f"{source.get('source_type', 'Missing')} · {source.get('title', '')}".strip(" ·")),
        "Model": _safe_public_text(latest.get("model_version", "DisabledProvider") or "DisabledProvider"),
        "Parameters": _safe_metadata_parameters(latest.get("metadata_json", "{}")),
        "Data lineage": _safe_public_text(f"{source.get('source_id', 'source missing')} -> {latest.get('evidence_id', 'evidence missing')}"),
        "Raw document": _safe_public_text(latest.get("artifact_uri", "") or source.get("uri", "No source record.")),
    }


def _without_retired_source_rows(summary: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in summary.get("rows", []) if isinstance(row, dict) and not _contains_retired_public_reference(row)]
    domain_counts: dict[str, int] = {}
    freshness_counts: dict[str, int] = {}
    for row in rows:
        domain = str(row.get("domain", ""))
        freshness = str(row.get("freshness", ""))
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        freshness_counts[freshness] = freshness_counts.get(freshness, 0) + 1
    clean = dict(summary)
    clean["source_count"] = len(rows)
    clean["domain_counts"] = domain_counts
    clean["freshness_counts"] = freshness_counts
    clean["rows"] = [_sanitize_public_payload(row) for row in rows]
    return clean


def _without_retired_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not _contains_retired_public_reference(row)]


def _safe_metadata_parameters(metadata_json: Any) -> str:
    try:
        metadata = json.loads(str(metadata_json or "{}"))
    except json.JSONDecodeError:
        metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}
    compact = {
        key: _sanitize_public_payload(metadata[key])
        for key in SAFE_METADATA_KEYS
        if key in metadata and not _contains_retired_public_reference(metadata[key])
    }
    return json.dumps(compact, ensure_ascii=False, sort_keys=True)


def _safe_public_text(value: Any) -> str:
    if _contains_retired_public_reference(value):
        return "[retired legacy reference hidden]"
    return str(_sanitize_public_payload(value))


def _sanitize_public_payload(value: Any) -> Any:
    if isinstance(value, str):
        if _contains_retired_public_reference(value):
            return "[retired legacy reference hidden]"
        if value.startswith("/Users/") or value.startswith("/private/") or value.startswith("~"):
            return "[redacted-private-uri]"
        return value
    if isinstance(value, dict):
        return {str(key): _sanitize_public_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_public_payload(item) for item in value]
    return value


def _contains_retired_public_reference(value: Any) -> bool:
    if isinstance(value, str):
        return any(fragment in value for fragment in RETIRED_PUBLIC_FRAGMENTS)
    if isinstance(value, dict):
        return any(_contains_retired_public_reference(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_retired_public_reference(item) for item in value)
    return False


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
