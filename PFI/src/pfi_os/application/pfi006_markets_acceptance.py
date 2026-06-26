from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.analysis import default_sentiment_universe
from pfi_os.analysis.sentiment import SentimentInstrument
from pfi_os.application.markets_workflow import build_markets_workflow, record_markets_workflow
from pfi_os.application.operational_store import OperationalStore


PFI006_MARKETS_ACCEPTANCE_SCHEMA = "PFI006MarketsVerticalAcceptanceV1"
PFI006_MARKETS_UI_READ_MODEL_SCHEMA = "PFI006MarketsUIReadModelV1"
PFI006_GOLDEN_SOURCE_ID = "src-pfi006-markets-golden-us-2026-06-19"
PFI006_GOLDEN_AS_OF = "2026-06-19T16:00:00+10:00"


def build_pfi006_markets_golden_fixture() -> dict[str, Any]:
    instruments = default_sentiment_universe("US")[:4]
    close_sets = [
        _linear(100.0, 130.0, 90),
        _joined(_linear(120.0, 105.0, 45), _linear(105.0, 135.0, 45)),
        _linear(30.0, 24.0, 90),
        _linear(180.0, 200.0, 90),
    ]
    price_frames = {
        instrument.symbol: _bars(close_sets[index], instrument.symbol)
        for index, instrument in enumerate(instruments)
    }
    return {
        "schema": "PFI006MarketsGoldenFixtureV1",
        "market": "US",
        "interval": "1d",
        "source_id": PFI006_GOLDEN_SOURCE_ID,
        "as_of": PFI006_GOLDEN_AS_OF,
        "price_frames": price_frames,
        "instruments": instruments,
        "expected": {
            "requested_count": 4,
            "observed_symbol_count": 4,
            "event_count": 90,
            "human_review_required": True,
            "target_weight_change": 0.0,
        },
    }


def build_pfi006_markets_ui_read_model(payload: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    cards = {card.get("card_id", ""): card for card in payload.get("cards", [])}
    decision = payload.get("decision", {})
    hotspots = payload.get("hotspots", {})
    freshness = payload.get("freshness", {})
    return {
        "schema": PFI006_MARKETS_UI_READ_MODEL_SCHEMA,
        "workspace": "market",
        "workspace_label": "市场",
        "primary_route": "market",
        "primary_feature_view": "market_slice",
        "secondary_feature_views": ["hotspots", "market_overlay", "market_alerts"],
        "title": "市场垂直切片",
        "summary": "从本地已观察行情生成市场事件、热点、情绪、任务和人工复核队列。",
        "cards": [
            _ui_card("市场事件", cards.get("market_event_log", {})),
            _ui_card("热点扩散", cards.get("market_hotspots", {})),
            _ui_card("市场情绪", cards.get("market_sentiment", {})),
        ],
        "portfolio_overlay": {
            "title": "组合影响覆盖层",
            "target_weight_change": float(decision.get("target_weight_change", 0.0) or 0.0),
            "no_private_holdings_used": True,
            "requires_portfolio_slice_before_position_impact": True,
            "effect": "仅提示市场观察对组合复核的影响；不读取私有持仓、不自动调仓。",
            "review_required": True,
        },
        "alerts": [
            {
                "alert_id": "market_freshness_review",
                "label": "新鲜度复核",
                "trigger": "freshness.status != Fresh or age_hours > 36",
                "current_status": freshness.get("status", "Missing"),
                "action": "创建人工复核任务",
                "human_review_required": True,
            },
            {
                "alert_id": "hotspot_divergence_review",
                "label": "热点分歧复核",
                "trigger": "leading and lagging sectors diverge or coverage drops",
                "current_status": hotspots.get("status", "Review"),
                "action": "保存观察视图并等待反证",
                "human_review_required": True,
            },
        ],
        "saved_views": [
            {
                "view_id": "market_us_daily_review",
                "label": "美股市场每日复核",
                "workspace": "market",
                "feature_view": "market_slice",
                "filters": {"market": payload.get("market", ""), "interval": payload.get("interval", "")},
                "source_ids": [payload.get("source_id", "")],
                "readonly": True,
            },
            {
                "view_id": "market_hotspot_watch",
                "label": "热点观察",
                "workspace": "market",
                "feature_view": "hotspots",
                "filters": {"evidence_class": payload.get("evidence_class", "")},
                "source_ids": [payload.get("source_id", "")],
                "readonly": True,
            },
        ],
        "journey": [
            "打开一级入口：市场",
            "打开功能：市场垂直切片",
            "查看市场事件、热点扩散和市场情绪卡片",
            "打开组合影响覆盖层",
            "保存观察视图并创建人工复核提醒",
        ],
        "operational_record_ids": ids,
        "safety_boundary": {
            "research_only": True,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_private_holdings_used": True,
            "human_review_required": True,
        },
    }


def run_pfi006_markets_acceptance(*, db_path: Path | str | None = None) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if db_path is None:
        with tempfile.TemporaryDirectory(prefix="pfi006-markets-") as tmp_dir:
            return _run_acceptance(Path(tmp_dir) / "private" / "operational" / "pfi.sqlite", generated_at=generated_at)
    return _run_acceptance(Path(db_path), generated_at=generated_at)


def rollback_pfi006_markets_records(store: OperationalStore, ids: dict[str, str]) -> dict[str, Any]:
    source_id = str(ids.get("source_id", ""))
    evidence_id = str(ids.get("evidence_id", ""))
    job_id = str(ids.get("job_id", ""))
    task_id = str(ids.get("task_id", ""))
    counts: dict[str, int] = {}
    with store.connect() as conn:
        counts["task_records"] = conn.execute("DELETE FROM task_records WHERE task_id = ?", (task_id,)).rowcount
        counts["job_records"] = conn.execute("DELETE FROM job_records WHERE job_id = ?", (job_id,)).rowcount
        counts["evidence_records"] = conn.execute("DELETE FROM evidence_records WHERE evidence_id = ?", (evidence_id,)).rowcount
        counts["source_versions"] = conn.execute("DELETE FROM source_versions WHERE source_id = ?", (source_id,)).rowcount
        counts["source_records"] = conn.execute("DELETE FROM source_records WHERE source_id = ?", (source_id,)).rowcount
    residue = {
        "source_records": _count_rows(store, "source_records", "source_id", source_id),
        "evidence_records": _count_rows(store, "evidence_records", "evidence_id", evidence_id),
        "job_records": _count_rows(store, "job_records", "job_id", job_id),
        "task_records": _count_rows(store, "task_records", "task_id", task_id),
    }
    return {
        "schema": "PFI006MarketsRollbackProofV1",
        "mode": "temporary_operational_store",
        "deleted_counts": counts,
        "residue_counts": residue,
        "status": "Pass" if all(value == 0 for value in residue.values()) else "Fail",
        "note": "Rollback deletes only PFI-006 source/evidence/job/task records in the temporary acceptance store; shared entity rows are left untouched.",
    }


def _run_acceptance(db_path: Path, *, generated_at: str) -> dict[str, Any]:
    fixture = build_pfi006_markets_golden_fixture()
    store = OperationalStore(db_path)
    payload = build_markets_workflow(
        fixture["price_frames"],
        fixture["instruments"],
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        data_source="PFI006GoldenFixture",
        market=fixture["market"],
        interval=fixture["interval"],
        max_snapshots=12,
    )
    ids = record_markets_workflow(store, payload, artifact_uri="operational_store:pfi006_markets_acceptance")
    ui_read_model = build_pfi006_markets_ui_read_model(payload, ids)
    golden_metrics = _golden_metrics(payload, ui_read_model, store)
    checks = _acceptance_checks(payload, ui_read_model, golden_metrics, ids, store)
    rollback_proof = rollback_pfi006_markets_records(store, ids)
    checks.append(_check("RollbackProof", rollback_proof["status"] == "Pass", json.dumps(rollback_proof["residue_counts"], sort_keys=True)))

    summary = _summary(checks)
    status = "Pass" if summary["fail"] == 0 else "Fail"
    return {
        "schema": PFI006_MARKETS_ACCEPTANCE_SCHEMA,
        "generated_at": generated_at,
        "status": status,
        "summary": summary,
        "workflow": _json_safe(payload),
        "ui_read_model": _json_safe(ui_read_model),
        "golden_metrics": golden_metrics,
        "rollback_proof": rollback_proof,
        "checks": checks,
        "safety_boundary": {
            "research_only": True,
            "provider_fetch_required": False,
            "broker_required": False,
            "llm_required": False,
            "no_live_trading": True,
            "no_broker_calls": True,
            "no_order_execution": True,
            "no_private_holdings_used": True,
            "human_review_required": True,
        },
        "next_action": "Use this as Gate 3 Markets evidence, then continue PFI-007 Research/Policy vertical slice.",
    }


def _acceptance_checks(
    payload: dict[str, Any],
    ui_read_model: dict[str, Any],
    golden_metrics: dict[str, Any],
    ids: dict[str, str],
    store: OperationalStore,
) -> list[dict[str, str]]:
    rows = {table: store.table_rows(table) for table in ("source_records", "evidence_records", "job_records", "task_records")}
    checks = [
        _check("DataChain:MarketEventLog", payload.get("market_event_log", {}).get("event_count") == 90, f"events={payload.get('market_event_log', {}).get('event_count')}"),
        _check("Domain:HotspotSentimentDecision", payload.get("hotspots", {}).get("summary", {}).get("object_count") == 4 and payload.get("sentiment", {}).get("summary", {}).get("object_count") == 4, "hotspot/sentiment object_count=4"),
        _check("API:UIReadModel", ui_read_model.get("schema") == PFI006_MARKETS_UI_READ_MODEL_SCHEMA and ui_read_model.get("primary_route") == "market", ui_read_model.get("schema", "")),
        _check("UI:ChineseJourney", all(step for step in ui_read_model.get("journey", [])) and "市场" in ui_read_model.get("workspace_label", ""), "market journey labels"),
        _check("TasksEvidence:Source", any(row["source_id"] == ids["source_id"] for row in rows["source_records"]), ids["source_id"]),
        _check("TasksEvidence:Evidence", any(row["evidence_id"] == ids["evidence_id"] for row in rows["evidence_records"]), ids["evidence_id"]),
        _check("TasksEvidence:Job", any(row["job_id"] == ids["job_id"] and row["status"] == "completed" for row in rows["job_records"]), ids["job_id"]),
        _check("TasksEvidence:ReviewTask", any(row["task_id"] == ids["task_id"] and row["human_review_required"] == 1 for row in rows["task_records"]), ids["task_id"]),
        _check("PortfolioOverlay:NoPrivateHoldings", ui_read_model.get("portfolio_overlay", {}).get("no_private_holdings_used") is True, "no private holdings used"),
        _check("AlertSavedView:Present", len(ui_read_model.get("alerts", [])) >= 2 and len(ui_read_model.get("saved_views", [])) >= 2, "alerts and saved views present"),
        _check("GoldenMetrics:StableWorkflow", bool(golden_metrics.get("workflow_id")) and golden_metrics.get("event_count") == 90, str(golden_metrics.get("workflow_id", ""))),
        _check("Safety:NoExecution", all(payload.get("safety_boundary", {}).get(key) is True for key in ("research_only", "no_live_trading", "no_broker_calls", "no_order_execution", "human_review_required")), "research-only boundary"),
    ]
    return checks


def _golden_metrics(payload: dict[str, Any], ui_read_model: dict[str, Any], store: OperationalStore) -> dict[str, Any]:
    return {
        "workflow_id": payload.get("workflow_id", ""),
        "source_id": payload.get("source_id", ""),
        "checksum": payload.get("market_event_log", {}).get("quality_report", {}).get("checksum", ""),
        "event_count": payload.get("market_event_log", {}).get("event_count", 0),
        "observed_symbol_count": payload.get("observed_symbol_count", 0),
        "focus_row_count": len(payload.get("hotspots", {}).get("focus_rows", [])),
        "confidence": payload.get("decision", {}).get("confidence", 0.0),
        "target_weight_change": payload.get("decision", {}).get("target_weight_change", 0.0),
        "alert_count": len(ui_read_model.get("alerts", [])),
        "saved_view_count": len(ui_read_model.get("saved_views", [])),
        "source_record_count": len(store.table_rows("source_records")),
        "evidence_record_count": len(store.table_rows("evidence_records")),
        "job_record_count": len(store.table_rows("job_records")),
        "task_record_count": len(store.table_rows("task_records")),
    }


def _ui_card(label: str, card: dict[str, Any]) -> dict[str, Any]:
    freshness = card.get("freshness", {})
    return {
        "label": label,
        "status": card.get("status", "Review"),
        "summary": card.get("summary", ""),
        "source_ids": card.get("source_ids", []),
        "as_of": card.get("as_of", ""),
        "freshness_status": freshness.get("status", "Missing"),
        "latest_event_time": freshness.get("latest_event_time", ""),
        "evidence_class": card.get("evidence_class", "market_observation"),
    }


def _bars(close_values: list[float], symbol: str) -> pd.DataFrame:
    index = pd.date_range("2026-02-16", periods=len(close_values), freq="B")
    close = pd.Series(close_values, dtype="float64")
    return pd.DataFrame(
        {
            "datetime": index,
            "symbol": symbol,
            "market": "US",
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 100000,
        }
    )


def _linear(start: float, end: float, count: int) -> list[float]:
    if count <= 1:
        return [float(end)]
    step = (end - start) / float(count - 1)
    return [round(start + step * index, 6) for index in range(count)]


def _joined(first: list[float], second: list[float]) -> list[float]:
    return first + second


def _count_rows(store: OperationalStore, table: str, column: str, value: str) -> int:
    with store.connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE {column} = ?", (value,)).fetchone()
    return int(row["count"])


def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "Pass" if passed else "Fail", "evidence": evidence}


def _summary(checks: list[dict[str, str]]) -> dict[str, int]:
    passed = sum(1 for item in checks if item["status"] == "Pass")
    failed = sum(1 for item in checks if item["status"] == "Fail")
    info = sum(1 for item in checks if item["status"] == "Info")
    return {"pass": passed, "fail": failed, "info": info, "total": len(checks)}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.DataFrame):
        return value.to_dict("records")
    if isinstance(value, SentimentInstrument):
        return asdict(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, Path):
        return str(value)
    return value
