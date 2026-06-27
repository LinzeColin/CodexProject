from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pfi_os.application.operational_store import OperationalStore
from pfi_os.application.source_registry import SourceRegistry
from pfi_os.application.workflow_runtime_read_model import build_workflow_runtime_read_model, empty_workflow_runtime_read_model
from pfi_v02.stage3_read_mvp import build_stage3_read_model
from pfi_v02.stage4_analysis_mvp import build_stage4_analysis_model
from pfi_v02.stage5_advice_report_alpha import build_stage5_delivery_model
from pfi_v02.stage6_e2e_stabilization import build_stage6_e2e_stabilization_model

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
    stage3_dashboard = build_stage3_read_model(now=now)
    stage4_dashboard = build_stage4_analysis_model(stage3_dashboard=stage3_dashboard, now=now)
    stage5_dashboard = build_stage5_delivery_model(stage3_dashboard=stage3_dashboard, stage4_dashboard=stage4_dashboard, now=now)
    stage6_dashboard = build_stage6_e2e_stabilization_model(
        stage3_dashboard=stage3_dashboard,
        stage4_dashboard=stage4_dashboard,
        stage5_dashboard=stage5_dashboard,
        now=now,
    )
    source_registry = SourceRegistry(operational_store)
    source_summary = _without_retired_source_rows(source_registry.summary(now=now))
    sources = _without_retired_rows(operational_store.table_rows("source_records"))
    evidence = _without_retired_rows(operational_store.table_rows("evidence_records"))
    jobs = _without_retired_rows(operational_store.table_rows("job_records"))
    tasks = _without_retired_rows(operational_store.table_rows("task_records"))
    holdings = operational_store.table_rows("holding_snapshots")

    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    latest_as_of = _latest_text([row.get("as_of", "") for row in [*sources, *evidence, *jobs, *tasks, *holdings]])
    cards = _stage4_metric_cards(stage4_dashboard) or _stage3_metric_cards(stage3_dashboard)
    decision_rows = (
        _stage5_decision_rows(stage5_dashboard)
        or _stage4_decision_rows(stage4_dashboard)
        or _stage3_decision_rows(stage3_dashboard)
        or _decision_rows(tasks, jobs, evidence)
    )
    return {
        "schema": "PFIOSHomeSummaryV1",
        "generated_at": generated_at,
        "as_of": latest_as_of,
        "source_registry": source_summary,
        "metric_cards": cards,
        "decision_rows": decision_rows,
        "evidence_drawer": _stage6_evidence_drawer(stage6_dashboard)
        or _stage5_evidence_drawer(stage5_dashboard)
        or _stage4_evidence_drawer(stage4_dashboard)
        or _stage3_evidence_drawer(stage3_dashboard)
        or _evidence_drawer(evidence, sources),
        "stage6_dashboard": _sanitize_public_payload(stage6_dashboard),
        "stage5_dashboard": _sanitize_public_payload(stage5_dashboard),
        "stage4_dashboard": _sanitize_public_payload(stage4_dashboard),
        "stage3_dashboard": _sanitize_public_payload(stage3_dashboard),
        "workflow_runtime": _sanitize_public_payload(build_workflow_runtime_read_model(operational_store, now=now)),
        "read_model": "OperationalStore -> SourceRegistry -> PFIOSHomeSummaryV1",
        "cache_policy": "Web shell consumes this compact summary; it does not read provider JSON, ResearchBus tables, or private source files directly.",
        "safety_boundary": "Decision support only; no live automatic orders, broker submission, payments, betting, or unattended execution.",
    }


def empty_homepage_summary() -> dict[str, Any]:
    stage3_dashboard = build_stage3_read_model()
    stage4_dashboard = build_stage4_analysis_model(stage3_dashboard=stage3_dashboard)
    stage5_dashboard = build_stage5_delivery_model(stage3_dashboard=stage3_dashboard, stage4_dashboard=stage4_dashboard)
    stage6_dashboard = build_stage6_e2e_stabilization_model(
        stage3_dashboard=stage3_dashboard,
        stage4_dashboard=stage4_dashboard,
        stage5_dashboard=stage5_dashboard,
    )
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
        "metric_cards": _stage4_metric_cards(stage4_dashboard),
        "decision_rows": _stage5_decision_rows(stage5_dashboard),
        "evidence_drawer": _stage6_evidence_drawer(stage6_dashboard),
        "stage6_dashboard": _sanitize_public_payload(stage6_dashboard),
        "stage5_dashboard": _sanitize_public_payload(stage5_dashboard),
        "stage4_dashboard": _sanitize_public_payload(stage4_dashboard),
        "stage3_dashboard": _sanitize_public_payload(stage3_dashboard),
        "workflow_runtime": empty_workflow_runtime_read_model(),
        "read_model": "OperationalStore -> SourceRegistry -> PFIOSHomeSummaryV1",
        "cache_policy": "Web shell consumes this compact summary; it does not read provider JSON, ResearchBus tables, or private source files directly.",
        "safety_boundary": "Decision support only; no live automatic orders, broker submission, payments, betting, or unattended execution.",
    }


def _stage3_metric_cards(stage3_dashboard: dict[str, Any]) -> list[dict[str, str]]:
    cards = stage3_dashboard.get("home", {}).get("financial_status_cards", [])
    return [_sanitize_public_payload(card) for card in cards[:5] if isinstance(card, dict)]


def _stage4_metric_cards(stage4_dashboard: dict[str, Any]) -> list[dict[str, str]]:
    cards = stage4_dashboard.get("metric_cards", [])
    return [_sanitize_public_payload(card) for card in cards[:5] if isinstance(card, dict)]


def _stage4_decision_rows(stage4_dashboard: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in stage4_dashboard.get("decision_rows", [])[:4]:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "priority": str(item.get("priority", "P2")),
                "object": str(item.get("object", "首页总览")),
                "evidence": str(item.get("evidence", "")),
                "action": str(item.get("action", "查看分析")),
                "status": str(item.get("status", "有建议")),
            }
        )
    return rows


def _stage5_decision_rows(stage5_dashboard: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in stage5_dashboard.get("top_recommendations", [])[:4]:
        if not isinstance(item, dict):
            continue
        evidence_refs = item.get("evidence_refs", [])
        if isinstance(evidence_refs, (list, tuple)):
            evidence = ", ".join(str(ref) for ref in evidence_refs[:2])
        else:
            evidence = str(evidence_refs)
        rows.append(
            {
                "priority": f"P{item.get('priority', 9)}",
                "object": str(item.get("target_entry", "建议与复盘")),
                "evidence": evidence or str(item.get("recommendation_id", "")),
                "action": str(item.get("suggested_action", "查看建议并人工决策")),
                "status": str(item.get("status", "有建议")),
            }
        )
    return rows


def _stage3_decision_rows(stage3_dashboard: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in stage3_dashboard.get("recommendations", [])[:4]:
        if not isinstance(item, dict):
            continue
        evidence_refs = item.get("evidence_refs", [])
        if isinstance(evidence_refs, (list, tuple)):
            evidence = ", ".join(str(ref) for ref in evidence_refs[:2])
        else:
            evidence = str(evidence_refs)
        rows.append(
            {
                "priority": f"P{item.get('priority', 9)}",
                "object": str(item.get("target_entry", "首页总览")),
                "evidence": evidence or str(item.get("recommendation_id", "")),
                "action": str(item.get("action", "查看建议")),
                "status": str(item.get("status", "有建议")),
            }
        )
    return rows


def _stage3_evidence_drawer(stage3_dashboard: dict[str, Any]) -> dict[str, str]:
    return {
        "title": "PFI Stage 3 · 首页、账户、账本",
        "Evidence": "Stage 3 使用本地 synthetic/read-only read-model 验证首页、账户地图、账本流水、待复核和同步全部计划。",
        "Source": "pfi_v02.stage3_read_mvp",
        "Model": str(stage3_dashboard.get("schema", "PFIV02Stage3ReadableMVPV1")),
        "Parameters": "FX fixture AUD/CNY/USD/HKD; no live market rate; no real credential.",
        "Data lineage": "Stage2 import fixtures -> Stage3 account/ledger/recommendation read-model.",
        "Raw document": "PFI/docs/pfi_v02/STAGE3_READABLE_MVP.md",
    }


def _stage4_evidence_drawer(stage4_dashboard: dict[str, Any]) -> dict[str, str]:
    return {
        "title": "PFI Stage 4 · 投资与消费智能分析",
        "Evidence": "Stage 4 使用本地 synthetic/read-only read-model 验证投资总览、收益归因、风险、行为复盘、消费预算、订阅、异常和现金流预测。",
        "Source": "pfi_v02.stage4_analysis_mvp",
        "Model": str(stage4_dashboard.get("schema", "PFIV02Stage4AnalysisMVPV1")),
        "Parameters": "Attribution components market/active/fees/fx/cash_drag; budget AUD 3600; reserve AUD 5000; no exact conclusion without evidence.",
        "Data lineage": "Stage3 account/ledger read-model + Stage4 synthetic analysis fixtures -> Stage4 investment/consumption analysis read-model.",
        "Raw document": "PFI/docs/pfi_v02/STAGE4_ANALYSIS_MVP.md",
    }


def _stage5_evidence_drawer(stage5_dashboard: dict[str, Any]) -> dict[str, str]:
    alpha_context = stage5_dashboard.get("alpha_context_export", {})
    export_center = stage5_dashboard.get("export_center", {})
    return {
        "title": "PFI Stage 5 · Stage 4 inputs · 建议、报告、Alpha 只读出口",
        "Evidence": "Stage 5 使用本地只读模型验证建议模型、review lifecycle、投资/消费建议、Top N 排序、四类报告、导出中心和 Alpha context snapshot。",
        "Source": "pfi_v02.stage5_advice_report_alpha",
        "Model": str(stage5_dashboard.get("schema", "PFIV02Stage5AdviceReportAlphaExportV1")),
        "Parameters": f"top_n={len(stage5_dashboard.get('top_recommendations', []))}; export_formats={', '.join(export_center.get('preferred_formats', ())) or 'markdown/json/csv'}; context_schema={alpha_context.get('schema', 'pfi_context_snapshot_v1')}",
        "Data lineage": "Stage3 account/ledger read-model + Stage4 analysis read-model -> Stage5 recommendation/report/context export.",
        "Raw document": "PFI/docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md",
    }


def _stage6_evidence_drawer(stage6_dashboard: dict[str, Any]) -> dict[str, str]:
    phase_6a = stage6_dashboard.get("phase_6a", {})
    source_count = len(phase_6a.get("source_fixture_matrix", ())) if isinstance(phase_6a, dict) else 0
    total_gates = stage6_dashboard.get("total_acceptance_gate", ())
    taskpack_audit = stage6_dashboard.get("taskpack_acceptance_audit", ())
    return {
        "title": "PFI Stage 6 · Stage 5 · Stage 4 inputs · 端到端验收与稳定化",
        "Evidence": "Stage 6 使用本地 synthetic/read-only 模型验证多数据源、首页、账本、建议生命周期、回归治理、交付回滚和 TaskPack acceptance gates。",
        "Source": "pfi_v02.stage6_e2e_stabilization",
        "Model": str(stage6_dashboard.get("schema", "PFIV02Stage6E2EStabilizationV1")),
        "Parameters": f"core_sources={source_count}; total_gates={len(total_gates)}; acceptance_checks={len(taskpack_audit)}; live_trade_submission_authorized=false",
        "Data lineage": "Stage2 contracts + Stage3 account/ledger read-model + Stage4 analysis + Stage5 recommendations/reports/context export -> Stage6 E2E closeout.",
        "Raw document": "PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md",
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
