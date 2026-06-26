from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import PROJECT_ROOT
from pfi_os.data.cleaner import normalize_ohlcv
from pfi_os.data.quality import assess_bars
from pfi_os.storage import atomic_write_json, atomic_write_text, file_lock, lock_path_for


MARKET_EVENT_LOG_SCHEMA = "PFIOSMarketEventLogV1"
MARKET_EVENT_SCHEMA = "PFIOSMarketEventV1"
MARKET_EVENT_TYPE_BAR_CLOSED = "BarClosed"
MARKET_EVENT_COLUMNS = [
    "event_id",
    "event_time",
    "event_type",
    "symbol",
    "market",
    "interval",
    "source",
    "sequence",
    "quality_status",
    "evidence_layer",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def bars_to_market_events(
    bars: pd.DataFrame,
    *,
    symbol: str,
    market: str = "US",
    interval: str = "1d",
    source: str = "local",
    evidence_layer: str = "OBSERVATION",
) -> list[dict[str, Any]]:
    normalized = normalize_ohlcv(bars, symbol=symbol, market=market)
    quality = assess_bars(normalized, provider=source, symbol=symbol, market=market, interval=interval)
    events: list[dict[str, Any]] = []
    for sequence, (_, row) in enumerate(normalized.sort_values("datetime").iterrows(), start=1):
        event_time = pd.Timestamp(row["datetime"]).isoformat()
        payload = {
            "open": _safe_float(row["open"]),
            "high": _safe_float(row["high"]),
            "low": _safe_float(row["low"]),
            "close": _safe_float(row["close"]),
            "volume": _safe_float(row["volume"]),
        }
        event_id = market_event_id(
            event_type=MARKET_EVENT_TYPE_BAR_CLOSED,
            source=source,
            market=market,
            symbol=symbol,
            interval=interval,
            event_time=event_time,
        )
        events.append(
            {
                "schema": MARKET_EVENT_SCHEMA,
                "event_id": event_id,
                "event_time": event_time,
                "event_type": MARKET_EVENT_TYPE_BAR_CLOSED,
                "symbol": symbol,
                "market": market.upper(),
                "interval": interval,
                "source": source,
                "sequence": sequence,
                "quality_status": quality.quality_status,
                "evidence_layer": evidence_layer,
                "payload": payload,
            }
        )
    return events


def build_market_event_log(
    bars: pd.DataFrame,
    *,
    symbol: str,
    market: str = "US",
    interval: str = "1d",
    source: str = "local",
    as_of: str | None = None,
    evidence_layer: str = "OBSERVATION",
) -> dict[str, Any]:
    normalized = normalize_ohlcv(bars, symbol=symbol, market=market)
    quality = assess_bars(normalized, provider=source, symbol=symbol, market=market, interval=interval)
    events = bars_to_market_events(
        normalized,
        symbol=symbol,
        market=market,
        interval=interval,
        source=source,
        evidence_layer=evidence_layer,
    )
    return {
        "schema": MARKET_EVENT_LOG_SCHEMA,
        "as_of": as_of or datetime.now().date().isoformat(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "layer": "Market Event Layer",
        "event_log_status": _event_log_status(events, quality.quality_status),
        "event_count": len(events),
        "source_summary": {
            "source": source,
            "symbol": symbol,
            "market": market.upper(),
            "interval": interval,
            "first_event_time": events[0]["event_time"] if events else None,
            "last_event_time": events[-1]["event_time"] if events else None,
        },
        "quality_report": asdict(quality),
        "events": events,
        "assumptions": [
            "This layer normalizes market observations into local research events; it does not connect to live trading or submit orders.",
            "Sample or CSV inputs are observation evidence until cross-source validation upgrades them.",
            "Kafka, QuestDB, ClickHouse, and external real-time feeds are future adapters; this local event log is the stable contract first.",
        ],
    }


def write_market_event_log(
    bars: pd.DataFrame,
    *,
    symbol: str,
    market: str = "US",
    interval: str = "1d",
    source: str = "local",
    as_of: str | None = None,
    output_dir: Path | str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    evidence_layer: str = "OBSERVATION",
) -> dict[str, Any]:
    payload = build_market_event_log(
        bars,
        symbol=symbol,
        market=market,
        interval=interval,
        source=source,
        as_of=as_of,
        evidence_layer=evidence_layer,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "marketEvents"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    safe_symbol = _safe_path_part(symbol)
    stem = f"MarketEventLog_{safe_symbol}_{interval}_{stamp}"
    json_path = target / f"{stem}.json"
    jsonl_path = target / f"{stem}.jsonl"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    latest_json = target / "MarketEventLog_latest.json"
    latest_jsonl = target / "MarketEventLog_latest.jsonl"
    latest_csv = target / "MarketEventLog_latest.csv"
    latest_markdown = target / "MarketEventLog_latest.md"
    payload["outputs"] = {
        "json": str(json_path),
        "jsonl": str(jsonl_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "latest_json": str(latest_json),
        "latest_jsonl": str(latest_jsonl),
        "latest_csv": str(latest_csv),
        "latest_markdown": str(latest_markdown),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    jsonl_text = market_events_jsonl(payload.get("events", []))
    atomic_write_text(jsonl_path, jsonl_text)
    atomic_write_text(latest_jsonl, jsonl_text)
    csv_text = market_events_csv(payload.get("events", []))
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    markdown = market_event_log_markdown(payload)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    return payload


def upsert_market_events_jsonl(path: Path | str, events: list[dict[str, Any]]) -> Path:
    target = Path(path).expanduser()
    with file_lock(lock_path_for(target)):
        merged = {event["event_id"]: event for event in read_market_events_jsonl(target)}
        for event in events:
            merged[str(event["event_id"])] = event
        ordered = sorted(merged.values(), key=lambda row: (str(row.get("event_time", "")), str(row.get("event_id", ""))))
        atomic_write_text(target, market_events_jsonl(ordered))
    return target


def read_market_events_jsonl(path: Path | str) -> list[dict[str, Any]]:
    target = Path(path).expanduser()
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Market event JSONL is corrupt at line {line_number}: {target}") from exc
        if not isinstance(payload, dict) or payload.get("schema") != MARKET_EVENT_SCHEMA:
            raise ValueError(f"Market event JSONL row has invalid schema at line {line_number}: {target}")
        rows.append(payload)
    return rows


def market_events_jsonl(events: list[dict[str, Any]]) -> str:
    if not events:
        return ""
    return "\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events) + "\n"


def market_events_csv(events: list[dict[str, Any]]) -> str:
    rows = []
    for event in events:
        payload = event.get("payload", {})
        rows.append(
            {
                "event_id": event.get("event_id", ""),
                "event_time": event.get("event_time", ""),
                "event_type": event.get("event_type", ""),
                "symbol": event.get("symbol", ""),
                "market": event.get("market", ""),
                "interval": event.get("interval", ""),
                "source": event.get("source", ""),
                "sequence": event.get("sequence", ""),
                "quality_status": event.get("quality_status", ""),
                "evidence_layer": event.get("evidence_layer", ""),
                "open": payload.get("open", ""),
                "high": payload.get("high", ""),
                "low": payload.get("low", ""),
                "close": payload.get("close", ""),
                "volume": payload.get("volume", ""),
            }
        )
    return pd.DataFrame(rows, columns=MARKET_EVENT_COLUMNS).to_csv(index=False)


def market_event_log_markdown(payload: dict[str, Any]) -> str:
    source = payload.get("source_summary", {})
    quality = payload.get("quality_report", {})
    lines = [
        f"# Market Event Layer {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Status: `{payload.get('event_log_status', '')}`",
        f"- Events: `{payload.get('event_count', 0)}`",
        f"- Source: `{source.get('source', '')}`",
        f"- Symbol: `{source.get('market', '')}:{source.get('symbol', '')}`",
        f"- Interval: `{source.get('interval', '')}`",
        f"- Window: `{source.get('first_event_time', '')}` -> `{source.get('last_event_time', '')}`",
        "",
        "## Quality",
        f"- Quality Status: `{quality.get('quality_status', '')}`",
        f"- Rows: `{quality.get('row_count', 0)}`",
        f"- Missing Values: `{quality.get('missing_values', 0)}`",
        f"- Duplicate Datetimes: `{quality.get('duplicate_datetimes', 0)}`",
        f"- Checksum: `{quality.get('checksum', '')}`",
        "",
        "## Event Sample",
        _markdown_table(_flatten_events(payload.get("events", [])[:20]), MARKET_EVENT_COLUMNS),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def market_event_id(*, event_type: str, source: str, market: str, symbol: str, interval: str, event_time: str) -> str:
    key = "|".join([event_type, source, market.upper(), symbol.upper(), interval, event_time])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _flatten_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload", {})
        rows.append(
            {
                "event_id": event.get("event_id", ""),
                "event_time": event.get("event_time", ""),
                "event_type": event.get("event_type", ""),
                "symbol": event.get("symbol", ""),
                "market": event.get("market", ""),
                "interval": event.get("interval", ""),
                "source": event.get("source", ""),
                "sequence": event.get("sequence", ""),
                "quality_status": event.get("quality_status", ""),
                "evidence_layer": event.get("evidence_layer", ""),
                "open": payload.get("open", ""),
                "high": payload.get("high", ""),
                "low": payload.get("low", ""),
                "close": payload.get("close", ""),
                "volume": payload.get("volume", ""),
            }
        )
    return rows


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _event_log_status(events: list[dict[str, Any]], quality_status: str) -> str:
    if not events:
        return "Empty"
    if quality_status == "Pass":
        return "Pass"
    return "Review"


def _safe_float(value: Any) -> float:
    return float(value)


def _safe_path_part(value: str) -> str:
    return value.replace("/", "_").replace(":", "_").replace(" ", "_")


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")
