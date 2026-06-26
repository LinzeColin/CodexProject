from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.analysis.market_hotspots import build_hotspot_history, hotspot_focus_rows, hotspot_runtime_summary, hotspot_summary
from pfi_os.analysis.sentiment import SentimentInstrument, sentiment_from_bars, sentiment_summary
from pfi_os.application.operational_store import DataDomain, EvidenceRecord, JobRecord, OperationalStore, SourceRecord, TaskRecord
from pfi_os.data.market_events import build_market_event_log


MARKETS_WORKFLOW_SCHEMA = "PFIOSPhaseBMarketsWorkflowV1"


def build_markets_workflow(
    price_frames: dict[str, pd.DataFrame],
    instruments: list[SentimentInstrument],
    *,
    source_id: str,
    as_of: str,
    data_source: str = "local_fixture",
    market: str = "US",
    interval: str = "1d",
    evidence_class: str = "market_observation",
    model_version: str = "DisabledProvider",
    max_snapshots: int = 24,
) -> dict[str, Any]:
    """Build the Phase B Markets vertical workflow from local bar frames.

    Provider fetch, worker scheduling, and live push are Phase C concerns. This
    slice accepts already-observed bars and turns them into research evidence.
    """
    normalized_market = str(market).upper()
    clean_frames = _clean_price_frames(price_frames)
    instrument_by_symbol = {item.symbol.upper(): item for item in instruments}
    requested_count = len(instruments)
    primary_symbol = _primary_symbol(clean_frames, instruments)
    market_event_log = _market_event_section(
        clean_frames.get(primary_symbol, pd.DataFrame()),
        primary_symbol=primary_symbol,
        market=normalized_market,
        interval=interval,
        data_source=data_source,
        as_of=as_of,
    )
    sentiment_rows, missing_data_log = _sentiment_rows(clean_frames, instrument_by_symbol, normalized_market)
    hotspot_history = build_hotspot_history(clean_frames, instruments, data_source=data_source, max_snapshots=max_snapshots)
    hotspot_summary_payload = _hotspot_summary_payload(
        hotspot_history,
        requested_count=requested_count,
        data_source=data_source,
        market=normalized_market,
        interval=interval,
        max_snapshots=max_snapshots,
    )
    latest_event_time = _latest_event_time(market_event_log)
    freshness = _freshness_summary(latest_event_time, as_of=as_of)
    cards = _market_cards(market_event_log, sentiment_rows, hotspot_summary_payload, freshness)
    decision = _decision_object(
        source_id=source_id,
        as_of=as_of,
        evidence_class=evidence_class,
        market=normalized_market,
        interval=interval,
        cards=cards,
        sentiment_rows=sentiment_rows,
        hotspot_summary_payload=hotspot_summary_payload,
        freshness=freshness,
        model_version=model_version,
    )
    workflow_id = _stable_id("markets", source_id, as_of, _frames_checksum(clean_frames), cards)
    status = _workflow_status(market_event_log, sentiment_rows, hotspot_summary_payload, missing_data_log)
    return {
        "schema": MARKETS_WORKFLOW_SCHEMA,
        "workspace": "markets",
        "workflow_id": workflow_id,
        "status": status,
        "source_id": source_id,
        "as_of": as_of,
        "evidence_class": evidence_class,
        "model_versions": [model_version],
        "data_source": data_source,
        "market": normalized_market,
        "interval": interval,
        "requested_count": requested_count,
        "observed_symbol_count": len(clean_frames),
        "market_event_log": market_event_log,
        "sentiment": {
            "summary": sentiment_summary(pd.DataFrame(sentiment_rows)),
            "rows": sentiment_rows,
        },
        "hotspots": hotspot_summary_payload,
        "freshness": freshness,
        "cards": cards,
        "decision": decision,
        "assumptions": [
            "Markets workflow consumes already-observed local bars and does not fetch providers directly.",
            "Market events, hotspot heat, and sentiment scores are observation evidence, not trading instructions.",
            "Source freshness and data coverage must be reviewed before using cards in research decisions.",
            "Phase C will add worker scheduling, retry/backoff, and 60-second Fast Path acceptance.",
        ],
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "human_review_required": True,
        },
        "missing_data_log": missing_data_log + hotspot_summary_payload.get("missing_data_log", []),
    }


def record_markets_workflow(
    store: OperationalStore,
    payload: dict[str, Any],
    *,
    artifact_uri: str = "operational_store:markets_workflow",
) -> dict[str, str]:
    if payload.get("schema") != MARKETS_WORKFLOW_SCHEMA:
        raise ValueError(f"payload schema must be {MARKETS_WORKFLOW_SCHEMA}")
    store.initialize()
    source_id = str(payload["source_id"])
    as_of = str(payload["as_of"])
    evidence_class = str(payload["evidence_class"])
    market = str(payload.get("market", "MARKET"))
    workflow_id = str(payload["workflow_id"])
    evidence_id = f"evidence-{workflow_id}"
    job_id = f"job-{workflow_id}"
    task_id = f"task-{workflow_id}"

    store.upsert_source(
        SourceRecord(
            source_id=source_id,
            domain=DataDomain.PUBLIC_SHARED_CANONICAL,
            source_type="markets_vertical_slice",
            uri=artifact_uri,
            as_of=as_of,
            evidence_class=evidence_class,
            title=f"Markets vertical workflow for {market}",
            checksum=str(payload.get("market_event_log", {}).get("quality_report", {}).get("checksum", "")),
            metadata={
                "workflow_id": workflow_id,
                "market": market,
                "interval": payload.get("interval", ""),
                "freshness": payload.get("freshness", {}),
                "safety_boundary": payload.get("safety_boundary", {}),
            },
        )
    )
    store.upsert_entity(market, entity_type="market", display_name=market, canonical_symbol=market)
    store.record_evidence(
        EvidenceRecord(
            evidence_id=evidence_id,
            source_id=source_id,
            entity_id=market,
            as_of=as_of,
            evidence_class=evidence_class,
            summary=_evidence_summary(payload),
            artifact_uri=artifact_uri,
            model_version=",".join(payload.get("model_versions", ["DisabledProvider"])),
            metadata={
                "workflow_id": workflow_id,
                "cards": payload.get("cards", []),
                "decision": payload.get("decision", {}),
                "freshness": payload.get("freshness", {}),
            },
        )
    )
    store.upsert_job(
        JobRecord(
            job_id=job_id,
            source_id=source_id,
            as_of=as_of,
            job_type="markets_vertical_slice",
            status="completed",
            phase="evidence_recorded",
            progress=1.0,
            artifact_uri=artifact_uri,
            metadata={"workflow_id": workflow_id, "schema": MARKETS_WORKFLOW_SCHEMA},
        )
    )
    store.upsert_task(
        TaskRecord(
            task_id=task_id,
            source_id=source_id,
            evidence_id=evidence_id,
            as_of=as_of,
            owner_workspace="markets",
            action="Review market cards, freshness, coverage, counter-evidence, and invalidation conditions.",
            status="open",
            priority="P1",
            human_review_required=True,
            metadata={"workflow_id": workflow_id, "decision": payload.get("decision", {})},
        )
    )
    return {"source_id": source_id, "evidence_id": evidence_id, "job_id": job_id, "task_id": task_id}


def build_phase_b_markets_contract() -> dict[str, Any]:
    return {
        "schema": "PFIOSPhaseBMarketsContractV1",
        "workflow_schema": MARKETS_WORKFLOW_SCHEMA,
        "workspace": "markets",
        "required_steps": [
            "load_observed_market_bars",
            "build_market_event_log",
            "build_hotspot_summary",
            "build_sentiment_summary",
            "classify_freshness_and_coverage",
            "publish_evidence_and_review_task",
        ],
        "required_fact_fields": ["source_id", "as_of", "evidence_class"],
        "required_card_fields": ["card_id", "title", "status", "summary", "source_ids", "as_of", "evidence_class", "freshness"],
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
            "markets_vertical_slice": True,
            "source_freshness_visible": True,
            "evidence_and_counter_evidence_required": True,
            "no_live_trading": True,
            "human_review_required": True,
            "provider_fetch_required": False,
            "llm_required": False,
        },
    }


def _clean_price_frames(price_frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    clean: dict[str, pd.DataFrame] = {}
    for symbol, frame in price_frames.items():
        if frame is None or frame.empty:
            continue
        data = frame.copy()
        if "datetime" not in data or "close" not in data:
            continue
        data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
        for column in ["open", "high", "low", "close", "volume"]:
            if column in data:
                data[column] = pd.to_numeric(data[column], errors="coerce")
        data = data.dropna(subset=["datetime", "close"]).sort_values("datetime").reset_index(drop=True)
        if not data.empty:
            clean[str(symbol).upper()] = data
    return clean


def _primary_symbol(clean_frames: dict[str, pd.DataFrame], instruments: list[SentimentInstrument]) -> str:
    for instrument in instruments:
        symbol = instrument.symbol.upper()
        if symbol in clean_frames:
            return symbol
    return next(iter(clean_frames), "")


def _market_event_section(
    bars: pd.DataFrame,
    *,
    primary_symbol: str,
    market: str,
    interval: str,
    data_source: str,
    as_of: str,
) -> dict[str, Any]:
    if primary_symbol and not bars.empty:
        return build_market_event_log(
            bars,
            symbol=primary_symbol,
            market=market,
            interval=interval,
            source=data_source,
            as_of=as_of,
            evidence_layer="OBSERVATION",
        )
    return {
        "schema": "PFIOSMarketEventLogV1",
        "as_of": as_of,
        "layer": "Market Event Layer",
        "event_log_status": "Empty",
        "event_count": 0,
        "source_summary": {"source": data_source, "symbol": primary_symbol, "market": market, "interval": interval},
        "quality_report": {"quality_status": "Empty", "row_count": 0, "checksum": ""},
        "events": [],
        "assumptions": ["No primary market bars were available."],
    }


def _sentiment_rows(
    clean_frames: dict[str, pd.DataFrame],
    instrument_by_symbol: dict[str, SentimentInstrument],
    market: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for symbol, frame in clean_frames.items():
        instrument = instrument_by_symbol.get(symbol, SentimentInstrument(symbol, symbol, market, "观察对象"))
        try:
            rows.append(sentiment_from_bars(frame, symbol=instrument.symbol, name=instrument.name, market=instrument.market, role=instrument.role).to_row())
        except ValueError as exc:
            missing.append({"dataset": "sentiment", "symbol": symbol, "status": "InsufficientData", "message": str(exc)})
    return rows, missing


def _hotspot_summary_payload(
    history: pd.DataFrame,
    *,
    requested_count: int,
    data_source: str,
    market: str,
    interval: str,
    max_snapshots: int,
) -> dict[str, Any]:
    if history.empty:
        return {
            "status": "Empty",
            "summary": asdict(hotspot_summary(history)),
            "runtime_summary": hotspot_runtime_summary(
                history,
                [],
                data_source=data_source,
                market=market,
                interval=interval,
                requested_count=requested_count,
                max_snapshots=max_snapshots,
            ),
            "focus_rows": [],
            "missing_data_log": [{"dataset": "hotspots", "status": "Missing", "message": "No hotspot history could be built."}],
        }
    latest = str(history["snapshot_time"].max())
    summary = hotspot_summary(history, latest)
    runtime = hotspot_runtime_summary(
        history,
        [],
        data_source=data_source,
        market=market,
        interval=interval,
        requested_count=requested_count,
        max_snapshots=max_snapshots,
    )
    return {
        "status": runtime.get("status", "Review"),
        "summary": asdict(summary),
        "runtime_summary": runtime,
        "focus_rows": _json_safe(hotspot_focus_rows(history, latest, n=6).to_dict("records")),
        "missing_data_log": [],
    }


def _freshness_summary(latest_event_time: str, *, as_of: str) -> dict[str, Any]:
    latest = pd.to_datetime(latest_event_time, errors="coerce")
    reference = pd.to_datetime(as_of, errors="coerce")
    if pd.isna(latest) or pd.isna(reference):
        return {"status": "Missing", "latest_event_time": latest_event_time, "as_of": as_of, "age_hours": None}
    if latest.tzinfo is not None and reference.tzinfo is None:
        latest = latest.tz_convert(None)
    if reference.tzinfo is not None and latest.tzinfo is None:
        reference = reference.tz_convert(None)
    age_hours = max(0.0, float((reference - latest).total_seconds() / 3600))
    if age_hours <= 36:
        status = "Fresh"
    elif age_hours <= 168:
        status = "Delayed"
    else:
        status = "Stale"
    return {"status": status, "latest_event_time": latest_event_time, "as_of": as_of, "age_hours": round(age_hours, 2)}


def _latest_event_time(market_event_log: dict[str, Any]) -> str:
    events = market_event_log.get("events", [])
    if events:
        return str(events[-1].get("event_time", ""))
    return str(market_event_log.get("source_summary", {}).get("last_event_time", "") or "")


def _market_cards(
    market_event_log: dict[str, Any],
    sentiment_rows: list[dict[str, Any]],
    hotspot_summary_payload: dict[str, Any],
    freshness: dict[str, Any],
) -> list[dict[str, Any]]:
    sentiment = sentiment_summary(pd.DataFrame(sentiment_rows))
    hotspot = hotspot_summary_payload.get("summary", {})
    evidence_class = "market_observation"
    as_of = str(market_event_log.get("as_of", ""))
    return [
        {
            "card_id": "market_event_log",
            "title": "Market events",
            "status": str(market_event_log.get("event_log_status", "Empty")),
            "summary": f"{market_event_log.get('event_count', 0)} observed market events from {market_event_log.get('source_summary', {}).get('source', '')}.",
            "source_ids": [str(market_event_log.get("source_summary", {}).get("source", ""))],
            "as_of": as_of,
            "evidence_class": evidence_class,
            "freshness": freshness,
        },
        {
            "card_id": "market_hotspots",
            "title": "Hotspots",
            "status": str(hotspot_summary_payload.get("status", "Review")),
            "summary": f"{hotspot.get('object_count', 0)} objects, leading sector {hotspot.get('leading_sector', '')}, lagging sector {hotspot.get('lagging_sector', '')}.",
            "source_ids": [str(market_event_log.get("source_summary", {}).get("source", ""))],
            "as_of": as_of,
            "evidence_class": evidence_class,
            "freshness": freshness,
        },
        {
            "card_id": "market_sentiment",
            "title": "Sentiment",
            "status": "Review" if sentiment.get("object_count", 0) else "Empty",
            "summary": f"average={sentiment.get('average_score', 0.0)}, hot={sentiment.get('hot_count', 0)}, cold={sentiment.get('cold_count', 0)}.",
            "source_ids": [str(market_event_log.get("source_summary", {}).get("source", ""))],
            "as_of": as_of,
            "evidence_class": evidence_class,
            "freshness": freshness,
        },
    ]


def _decision_object(
    *,
    source_id: str,
    as_of: str,
    evidence_class: str,
    market: str,
    interval: str,
    cards: list[dict[str, Any]],
    sentiment_rows: list[dict[str, Any]],
    hotspot_summary_payload: dict[str, Any],
    freshness: dict[str, Any],
    model_version: str,
) -> dict[str, Any]:
    sentiment = sentiment_summary(pd.DataFrame(sentiment_rows))
    hotspot = hotspot_summary_payload.get("summary", {})
    decision_id = _stable_id("markets-decision", source_id, as_of, cards)
    confidence = _confidence(freshness, sentiment, hotspot)
    return {
        "decision_id": decision_id,
        "entity_id": market,
        "action": "review_market_update",
        "horizon": f"market_{interval}_research_window",
        "target_weight_change": 0.0,
        "status": "ReviewRequired",
        "confidence": confidence,
        "evidence_class": evidence_class,
        "as_of": as_of,
        "thesis": [
            "Market event, hotspot, and sentiment cards summarize observed public market data.",
            "The workflow exposes freshness, coverage, source ids, and evidence class before downstream research use.",
        ],
        "catalysts": [
            f"Leading hotspot sector: {hotspot.get('leading_sector', '')}.",
            f"Hot sentiment objects: {sentiment.get('hot_count', 0)}; cold sentiment objects: {sentiment.get('cold_count', 0)}.",
        ],
        "counter_evidence": [
            "Hotspot and sentiment scores are derived from price/volume structure, not fundamentals.",
            "Stale, delayed, or partial coverage can invalidate the card summary.",
            "Single-source market bars require cross-source validation before high-conviction research use.",
        ],
        "invalidation_conditions": [
            "Source checksum, latest event time, provider adjustment mode, or universe selection changes.",
            "Freshness status becomes Stale or data coverage drops below the accepted review threshold.",
            "Policy, earnings, macro, or position-specific evidence contradicts the market card reading.",
        ],
        "risks": ["Momentum reversal", "Data freshness gap", "Coverage bias", "Over-reading technical proxies"],
        "portfolio_effect": {"no_private_holdings_used": True, "requires_portfolio_slice_before_position_impact": True},
        "model_versions": [model_version],
        "source_ids": [source_id],
        "human_review_required": True,
    }


def _workflow_status(
    market_event_log: dict[str, Any],
    sentiment_rows: list[dict[str, Any]],
    hotspot_summary_payload: dict[str, Any],
    missing_data_log: list[dict[str, str]],
) -> str:
    if market_event_log.get("event_log_status") == "Empty" and not sentiment_rows and hotspot_summary_payload.get("status") == "Empty":
        return "Blocked"
    if missing_data_log or market_event_log.get("event_log_status") != "Pass":
        return "Review"
    return "Pass"


def _confidence(freshness: dict[str, Any], sentiment: dict[str, Any], hotspot: dict[str, Any]) -> float:
    base = 0.5
    if freshness.get("status") == "Fresh":
        base += 0.15
    elif freshness.get("status") == "Stale":
        base -= 0.2
    if sentiment.get("object_count", 0) >= 3:
        base += 0.05
    if hotspot.get("object_count", 0) >= 3:
        base += 0.05
    return round(min(max(base, 0.0), 0.85), 2)


def _evidence_summary(payload: dict[str, Any]) -> str:
    market = payload.get("market", "")
    cards = {card.get("card_id", ""): card for card in payload.get("cards", [])}
    event_summary = cards.get("market_event_log", {}).get("summary", "")
    sentiment_summary_text = cards.get("market_sentiment", {}).get("summary", "")
    return f"Markets workflow for {market}: {event_summary} {sentiment_summary_text}".strip()


def _frames_checksum(clean_frames: dict[str, pd.DataFrame]) -> str:
    chunks = []
    for symbol in sorted(clean_frames):
        frame = clean_frames[symbol]
        columns = [column for column in ["datetime", "symbol", "market", "open", "high", "low", "close", "volume"] if column in frame.columns]
        data = frame[columns].copy()
        data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
        chunks.append(symbol)
        chunks.append(data.to_csv(index=False))
    return hashlib.sha256("\n".join(chunks).encode("utf-8")).hexdigest()


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
            return value.item()
        except Exception:
            return str(value)
    return value
