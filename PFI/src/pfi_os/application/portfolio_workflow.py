from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, SourceRecord, TaskRecord
from pfi_os.integrations import canonical_holdings_frame, holdings_exposure_frame, holdings_quality_frame
from pfi_os.risk import fixed_fraction_weight


PORTFOLIO_WORKFLOW_SCHEMA = "PFIOSPhaseBPortfolioWorkflowV1"
PRIVATE_PORTFOLIO_DOMAIN = DataDomain.PRIVATE_DERIVED.value


def build_portfolio_workflow(
    holdings: pd.DataFrame,
    *,
    source_id: str,
    as_of: str,
    portfolio_id: str = "default",
    evidence_class: str = "private_portfolio_review",
    model_version: str = "DisabledProvider",
    max_single_weight: float = 0.35,
    max_top3_weight: float = 0.65,
) -> dict[str, Any]:
    """Build the Phase B Portfolio workflow from reviewed private holdings.

    The returned payload is private-derived. It may contain a holding snapshot
    for Operational Store persistence, but it never places orders or mutates a
    broker/account state.
    """
    canonical = canonical_holdings_frame(_frame(holdings))
    snapshot_holdings = _holding_records(canonical)
    snapshot_checksum = _stable_id("holdings", snapshot_holdings)
    workflow_id = _stable_id("portfolio", source_id, as_of, portfolio_id, snapshot_checksum, max_single_weight, max_top3_weight)
    snapshot_id = f"holdingSnapshot_{workflow_id}"
    quality_rows = _quality_rows(canonical)
    exposure_rows = _exposure_rows(canonical)
    summary = _portfolio_summary(canonical, quality_rows, exposure_rows)
    risk_review = _risk_review(summary, quality_rows, max_single_weight=max_single_weight, max_top3_weight=max_top3_weight)
    position_guardrails = {
        "max_single_weight": float(max_single_weight),
        "max_top3_weight": float(max_top3_weight),
        "default_new_position_review_cap": fixed_fraction_weight(0.10, max_weight=float(max_single_weight)),
        "sizing_mode": "review_only_no_order_intent",
    }
    cards = _cards(
        source_id=source_id,
        as_of=as_of,
        evidence_class=evidence_class,
        summary=summary,
        quality_rows=quality_rows,
        exposure_rows=exposure_rows,
        risk_review=risk_review,
    )
    decision = _decision_object(
        source_id=source_id,
        as_of=as_of,
        evidence_class=evidence_class,
        portfolio_id=portfolio_id,
        summary=summary,
        risk_review=risk_review,
        position_guardrails=position_guardrails,
        model_version=model_version,
    )
    return {
        "schema": PORTFOLIO_WORKFLOW_SCHEMA,
        "workspace": "portfolio",
        "workflow_id": workflow_id,
        "status": _workflow_status(summary, risk_review),
        "source_id": source_id,
        "as_of": as_of,
        "portfolio_id": portfolio_id,
        "evidence_class": evidence_class,
        "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
        "model_versions": [model_version],
        "holdings_snapshot": {
            "snapshot_id": snapshot_id,
            "portfolio_id": portfolio_id,
            "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
            "holding_count": int(summary["holding_count"]),
            "checksum": snapshot_checksum,
            "holdings": snapshot_holdings,
            "public_git_allowed": False,
        },
        "portfolio_summary": summary,
        "quality": {"rows": quality_rows},
        "exposure": {"rows": exposure_rows},
        "risk_review": risk_review,
        "position_guardrails": position_guardrails,
        "cards": cards,
        "decision": decision,
        "assumptions": [
            "Portfolio workflow consumes local reviewed holdings or sanitized fixtures only.",
            "Holding snapshots are private-derived records and must stay outside public Git.",
            "Exposure, concentration, and quality outputs are review evidence, not trade instructions.",
            "No broker call, account mutation, order placement, payment, or unattended execution is performed.",
        ],
        "safety_boundary": {
            "research_only": True,
            "private_data_not_for_public_git": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_holding_mutation": True,
            "human_review_required": True,
        },
        "missing_data_log": _missing_data_log(summary, quality_rows, risk_review),
    }


def record_portfolio_workflow(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    artifact_uri: str = "operational_store:portfolio_workflow",
) -> dict[str, str]:
    if payload.get("schema") != PORTFOLIO_WORKFLOW_SCHEMA:
        raise ValueError(f"payload schema must be {PORTFOLIO_WORKFLOW_SCHEMA}")
    store.initialize()
    source_id = str(payload["source_id"])
    as_of = str(payload["as_of"])
    evidence_class = str(payload["evidence_class"])
    portfolio_id = str(payload.get("portfolio_id", "default"))
    workflow_id = str(payload["workflow_id"])
    evidence_id = f"evidence-{workflow_id}"
    job_id = f"job-{workflow_id}"
    task_id = f"task-{workflow_id}"
    snapshot = payload.get("holdings_snapshot", {})
    snapshot_id = str(snapshot.get("snapshot_id") or f"holdingSnapshot_{workflow_id}")

    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PRIVATE_DERIVED,
            source_type="portfolio_vertical_slice",
            uri=artifact_uri,
            as_of=as_of,
            evidence_class=evidence_class,
            title=f"Portfolio vertical workflow for {portfolio_id}",
            checksum=str(snapshot.get("checksum", "")),
            metadata={
                "workflow_id": workflow_id,
                "portfolio_id": portfolio_id,
                "holding_count": snapshot.get("holding_count", 0),
                "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
                "safety_boundary": payload.get("safety_boundary", {}),
            },
        )
    )
    store.upsert_entity(portfolio_id, entity_type="portfolio", display_name=portfolio_id, canonical_symbol=portfolio_id)
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id=portfolio_id,
            as_of=as_of,
            evidence_class=evidence_class,
            summary=_evidence_summary(payload),
            artifact_uri=artifact_uri,
            model_version=",".join(payload.get("model_versions", ["DisabledProvider"])),
            metadata={
                "workflow_id": workflow_id,
                "portfolio_id": portfolio_id,
                "snapshot_id": snapshot_id,
                "cards": payload.get("cards", []),
                "decision": payload.get("decision", {}),
                "portfolio_summary": payload.get("portfolio_summary", {}),
                "risk_review": payload.get("risk_review", {}),
            },
        )
    )
    store.upsert_holding_snapshot(
        snapshot_id=snapshot_id,
        source_id=source_id,
        evidence_id=evidence_id,
        as_of=as_of,
        portfolio_id=portfolio_id,
        holdings=list(snapshot.get("holdings", [])),
        domain=DataDomain.PRIVATE_DERIVED,
    )
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="portfolio_vertical_slice",
            status="completed",
            phase="evidence_recorded",
            progress=1.0,
            artifact_uri=artifact_uri,
            metadata={"workflow_id": workflow_id, "schema": PORTFOLIO_WORKFLOW_SCHEMA, "snapshot_id": snapshot_id},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="portfolio",
            action="Review private holdings, exposure, concentration, counter-evidence, and invalidation conditions before any real-world action.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={"workflow_id": workflow_id, "snapshot_id": snapshot_id, "decision": payload.get("decision", {})},
        )
    )
    return {"source_id": source_id, "evidence_id": evidence_id, "job_id": job_id, "task_id": task_id, "snapshot_id": snapshot_id}


def build_phase_b_portfolio_contract() -> dict[str, Any]:
    return {
        "schema": "PFIOSPhaseBPortfolioContractV1",
        "workflow_schema": PORTFOLIO_WORKFLOW_SCHEMA,
        "workspace": "portfolio",
        "required_steps": [
            "load_reviewed_private_holdings",
            "canonicalize_holding_snapshot",
            "classify_private_derived_boundary",
            "build_quality_exposure_and_risk_cards",
            "publish_evidence_snapshot_and_review_task",
        ],
        "required_fact_fields": ["source_id", "as_of", "evidence_class"],
        "required_card_fields": ["card_id", "title", "status", "summary", "source_ids", "as_of", "evidence_class", "review_required", "data_domain"],
        "decision_contract_fields": [
            "decision_id",
            "entity_id",
            "action",
            "horizon",
            "target_weight_change",
            "status",
            "confidence",
            "evidence_class",
            "as_of",
            "thesis",
            "catalysts",
            "counter_evidence",
            "invalidation_conditions",
            "risks",
            "portfolio_effect",
            "model_versions",
            "source_ids",
            "human_review_required",
        ],
        "non_regression_constraints": {
            "portfolio_vertical_slice": True,
            "private_holdings_stay_outside_public_git": True,
            "holding_snapshot_operational_store": True,
            "exposure_and_concentration_visible": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_holding_mutation": True,
            "human_review_required": True,
            "llm_required": False,
        },
    }


def _cards(
    *,
    source_id: str,
    as_of: str,
    evidence_class: str,
    summary: dict[str, Any],
    quality_rows: list[dict[str, Any]],
    exposure_rows: list[dict[str, Any]],
    risk_review: dict[str, Any],
) -> list[dict[str, Any]]:
    source_ids = [source_id]
    top_market = next((row for row in exposure_rows if row.get("dimension") == "market"), {})
    review_required = risk_review.get("status") != "Pass"
    return [
        {
            "card_id": "portfolio_holdings",
            "title": "Private holdings",
            "status": "Pass" if summary["holding_count"] else "Blocked",
            "summary": f"holdings={summary['holding_count']}, total_abs_value={summary['total_abs_position_value']:.2f}, sources={summary['source_count']}.",
            "source_ids": source_ids,
            "as_of": as_of,
            "evidence_class": evidence_class,
            "review_required": summary["holding_count"] == 0,
            "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
        },
        {
            "card_id": "portfolio_exposure",
            "title": "Exposure and concentration",
            "status": "Review" if review_required else "Pass",
            "summary": (
                f"top_market={top_market.get('bucket', '')}, "
                f"max_single={summary['max_single_weight']:.2%}, top3={summary['top3_weight']:.2%}."
            ),
            "source_ids": source_ids,
            "as_of": as_of,
            "evidence_class": evidence_class,
            "review_required": review_required,
            "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
        },
        {
            "card_id": "portfolio_risk_review",
            "title": "Risk review",
            "status": str(risk_review.get("status", "Review")),
            "summary": f"risk_status={risk_review.get('status', 'Review')}, quality_checks={len(quality_rows)}, reasons={len(risk_review.get('reasons', []))}.",
            "source_ids": source_ids,
            "as_of": as_of,
            "evidence_class": evidence_class,
            "review_required": True,
            "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
        },
    ]


def _decision_object(
    *,
    source_id: str,
    as_of: str,
    evidence_class: str,
    portfolio_id: str,
    summary: dict[str, Any],
    risk_review: dict[str, Any],
    position_guardrails: dict[str, Any],
    model_version: str,
) -> dict[str, Any]:
    return {
        "decision_id": _stable_id("portfolio-decision", source_id, as_of, portfolio_id, summary, risk_review),
        "entity_id": portfolio_id,
        "action": "review_portfolio_risk",
        "horizon": "portfolio_review_window",
        "target_weight_change": 0.0,
        "status": "ReviewRequired",
        "confidence": _confidence(summary, risk_review),
        "evidence_class": evidence_class,
        "as_of": as_of,
        "thesis": [
            "Portfolio workflow turns reviewed private holdings into quality, exposure, concentration, and risk-review evidence.",
            "The snapshot is classified as private-derived and is persisted only in the Operational Store.",
        ],
        "catalysts": [
            f"Holding count: {summary['holding_count']}.",
            f"Maximum single holding weight: {summary['max_single_weight']:.2%}.",
            f"Top-three holding weight: {summary['top3_weight']:.2%}.",
        ],
        "counter_evidence": [
            "Holdings may be stale, incomplete, or manually entered.",
            "Market value, cost basis, currency, and source-system fields require review before downstream use.",
            "Concentration thresholds are review gates, not forced rebalance instructions.",
        ],
        "invalidation_conditions": [
            "Holding snapshot checksum, source file, manual entry, or as-of timestamp changes.",
            "A source-system reconciliation shows missing holdings, pending orders, or stale market values.",
            "Portfolio concentration, liquidity, or policy constraints change after review.",
        ],
        "risks": ["Private data leakage", "Stale holdings", "Concentration risk", "Currency or source mapping error", "Manual-entry error"],
        "portfolio_effect": {
            "private_holdings_used": True,
            "data_domain": PRIVATE_PORTFOLIO_DOMAIN,
            "holding_count": int(summary["holding_count"]),
            "max_single_weight": float(summary["max_single_weight"]),
            "top3_weight": float(summary["top3_weight"]),
            "position_guardrails": position_guardrails,
            "no_order_execution": True,
        },
        "model_versions": [model_version],
        "source_ids": [source_id],
        "human_review_required": True,
    }


def _portfolio_summary(canonical: pd.DataFrame, quality_rows: list[dict[str, Any]], exposure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if canonical.empty:
        return {
            "holding_count": 0,
            "source_count": 0,
            "market_count": 0,
            "total_abs_position_value": 0.0,
            "max_single_weight": 0.0,
            "top3_weight": 0.0,
            "latest_updated_at": "",
            "quality_status_counts": {},
            "exposure_bucket_count": len(exposure_rows),
        }
    data = canonical.copy()
    weights = pd.to_numeric(data["weight"], errors="coerce").fillna(0.0).abs().sort_values(ascending=False)
    values = pd.to_numeric(data["position_value"], errors="coerce").fillna(0.0).abs()
    updated = pd.to_datetime(data["updated_at"], errors="coerce", utc=True).dropna()
    quality_counts: dict[str, int] = {}
    for row in quality_rows:
        status = str(row.get("status", ""))
        quality_counts[status] = quality_counts.get(status, 0) + 1
    return {
        "holding_count": int(len(data)),
        "source_count": int(data["source_system"].fillna("").astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
        "market_count": int(data["market"].fillna("").astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
        "total_abs_position_value": round(float(values.sum()), 6),
        "max_single_weight": float(weights.iloc[0]) if not weights.empty else 0.0,
        "top3_weight": float(weights.head(3).sum()) if not weights.empty else 0.0,
        "latest_updated_at": updated.max().isoformat() if not updated.empty else "",
        "quality_status_counts": quality_counts,
        "exposure_bucket_count": len(exposure_rows),
    }


def _quality_rows(canonical: pd.DataFrame) -> list[dict[str, Any]]:
    frame = holdings_quality_frame(canonical)
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "check_id": str(row.get("检查项", "")),
                "status": str(row.get("状态", "")),
                "summary": str(row.get("说明", "")),
            }
        )
    return rows


def _exposure_rows(canonical: pd.DataFrame) -> list[dict[str, Any]]:
    frame = holdings_exposure_frame(canonical)
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        dimension = str(row.get("维度", ""))
        dimension_key = {"市场": "market", "来源": "source"}.get(dimension, dimension)
        rows.append(
            {
                "dimension": dimension_key,
                "bucket": str(row.get("类别", "")),
                "exposure_value": _safe_float(row.get("市值", 0.0)),
                "exposure_weight": _safe_float(row.get("权重", 0.0)),
            }
        )
    return rows


def _risk_review(
    summary: dict[str, Any],
    quality_rows: list[dict[str, Any]],
    *,
    max_single_weight: float,
    max_top3_weight: float,
) -> dict[str, Any]:
    reasons: list[str] = []
    actions: list[str] = []
    missing_evidence: list[str] = []
    if int(summary["holding_count"]) == 0:
        missing_evidence.append("reviewed_private_holdings")
        reasons.append("No reviewed holdings were available.")
        actions.append("Load reviewed holdings into the private portfolio data home before downstream portfolio decisions.")
    for row in quality_rows:
        if row.get("status") != "Pass":
            reasons.append(f"{row.get('check_id', 'quality_check')}: {row.get('summary', '')}")
            actions.append("Review holding source, market value, market label, update timestamp, and concentration before reuse.")
    if float(summary["max_single_weight"]) >= float(max_single_weight):
        reasons.append(f"Max single holding weight {summary['max_single_weight']:.2%} meets or exceeds review threshold {max_single_weight:.2%}.")
        actions.append("Review single-name concentration before adding exposure.")
    if float(summary["top3_weight"]) >= float(max_top3_weight):
        reasons.append(f"Top-three holding weight {summary['top3_weight']:.2%} meets or exceeds review threshold {max_top3_weight:.2%}.")
        actions.append("Review portfolio concentration and correlation before adding exposure.")
    if missing_evidence:
        status = "Blocked"
    elif reasons:
        status = "Review"
    else:
        status = "Pass"
        reasons.append("No major portfolio quality or concentration gate was triggered.")
        actions.append("Continue research review and refresh holdings before any real-world action.")
    return {"status": status, "reasons": reasons, "actions": actions, "missing_evidence": missing_evidence}


def _workflow_status(summary: dict[str, Any], risk_review: dict[str, Any]) -> str:
    if int(summary["holding_count"]) == 0:
        return "Blocked"
    if risk_review.get("status") == "Pass":
        return "Pass"
    return "Review"


def _confidence(summary: dict[str, Any], risk_review: dict[str, Any]) -> float:
    if int(summary["holding_count"]) == 0:
        return 0.2
    base = 0.55
    if risk_review.get("status") == "Pass":
        base += 0.15
    elif risk_review.get("status") == "Blocked":
        base -= 0.25
    if summary.get("latest_updated_at"):
        base += 0.05
    return round(min(max(base, 0.0), 0.85), 2)


def _missing_data_log(summary: dict[str, Any], quality_rows: list[dict[str, Any]], risk_review: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if int(summary["holding_count"]) == 0:
        rows.append({"dataset": "private_holdings", "status": "Missing", "message": "No reviewed private holdings were available."})
    for missing in risk_review.get("missing_evidence", []):
        rows.append({"dataset": "portfolio_review", "status": "Missing", "message": str(missing)})
    for row in quality_rows:
        if row.get("status") != "Pass":
            rows.append({"dataset": "holding_quality", "status": str(row.get("status", "")), "message": str(row.get("summary", ""))})
    return rows


def _evidence_summary(payload: dict[str, Any]) -> str:
    summary = payload.get("portfolio_summary", {})
    risk = payload.get("risk_review", {})
    return (
        f"Portfolio workflow for {payload.get('portfolio_id', 'default')}: "
        f"holdings={summary.get('holding_count', 0)}, "
        f"max_single={float(summary.get('max_single_weight', 0.0) or 0.0):.4f}, "
        f"risk_status={risk.get('status', 'Review')}."
    )


def _holding_records(canonical: pd.DataFrame) -> list[dict[str, Any]]:
    if canonical.empty:
        return []
    return _json_safe(canonical.to_dict("records"))


def _frame(frame: pd.DataFrame | None) -> pd.DataFrame:
    if isinstance(frame, pd.DataFrame):
        return frame.copy()
    return pd.DataFrame()


def _stable_id(*parts: Any) -> str:
    payload = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _safe_float(value: Any) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
