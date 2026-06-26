from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import PROJECT_ROOT
from pfi_os.data.lake import DATA_LAKE_MANIFEST_SCHEMA, DATA_LAKE_REPLAY_CURSOR_SCHEMA
from pfi_os.data.market_events import read_market_events_jsonl
from pfi_os.storage import atomic_write_json, atomic_write_text


EVENT_REPLAY_SCHEMA = "PFIOSEventReplayBatchV1"
EVENT_REPLAY_RECORD_COLUMNS = [
    "replay_index",
    "cursor_id",
    "asset_id",
    "event_id",
    "event_time",
    "event_type",
    "symbol",
    "market",
    "interval",
    "source",
    "quality_status",
    "evidence_layer",
    "payload_json",
]


def build_event_replay(
    *,
    project_root: Path | str = PROJECT_ROOT,
    manifest_path: Path | str | None = None,
    cursors_path: Path | str | None = None,
    cursor_id: str | None = None,
    dataset: str | None = None,
    market: str | None = None,
    symbol: str | None = None,
    interval: str | None = None,
    source: str | None = None,
    start_after: str | None = None,
    end_at: str | None = None,
    limit: int | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    manifest_file = Path(manifest_path).expanduser() if manifest_path else root / "data" / "dataLake" / "DataLakeManifest_latest.json"
    cursors_file = Path(cursors_path).expanduser() if cursors_path else root / "data" / "dataLake" / "DataLakeManifest_latest_replay_cursors.json"
    missing_data_log: list[dict[str, str]] = []
    manifest = _read_manifest(manifest_file, missing_data_log)
    cursor_payload = _read_cursor_payload(cursors_file, missing_data_log)
    cursors = _cursor_rows(manifest, cursor_payload)
    selected_cursors = _select_cursors(
        cursors,
        cursor_id=cursor_id,
        dataset=dataset,
        market=market,
        symbol=symbol,
        interval=interval,
        source=source,
    )
    if not selected_cursors and cursors:
        missing_data_log.append(_missing("replay_cursor", "No replay cursor matched the requested filters."))
    cursor_ids = {str(row.get("cursor_id", "")) for row in selected_cursors}
    selected_assets = _select_assets(manifest.get("assets", []), cursor_ids, missing_data_log)
    records, source_event_count = _event_records(
        root=root,
        assets=selected_assets,
        start_after=start_after,
        end_at=end_at,
        limit=limit,
        missing_data_log=missing_data_log,
    )
    status = _replay_status(records, selected_cursors, selected_assets, missing_data_log)
    first_event_time = records[0]["event_time"] if records else None
    last_event_time = records[-1]["event_time"] if records else None
    next_after = last_event_time if records else start_after
    return {
        "schema": EVENT_REPLAY_SCHEMA,
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "layer": "Event Replay",
        "replay_status": status,
        "project_root": str(root),
        "manifest_path": str(manifest_file),
        "cursors_path": str(cursors_file),
        "cursor_count": len(selected_cursors),
        "asset_count": len(selected_assets),
        "source_event_count": source_event_count,
        "event_count": len(records),
        "first_event_time": first_event_time,
        "last_event_time": last_event_time,
        "next_after": next_after,
        "filters": {
            "cursor_id": cursor_id,
            "dataset": dataset,
            "market": market.upper() if market else None,
            "symbol": symbol,
            "interval": interval,
            "source": source,
            "start_after": start_after,
            "end_at": end_at,
            "limit": limit,
        },
        "selected_cursors": selected_cursors,
        "selected_assets": selected_assets,
        "records": records,
        "missing_data_log": missing_data_log,
        "assumptions": [
            "Event replay is deterministic and ordered by event_time, then event_id.",
            "This MVP replays local market event JSONL assets only; it does not simulate orders or connect to live trading.",
            "The replay batch is a stable input contract for later vectorized, discrete-event, and agent-market simulation modes.",
        ],
    }


def write_event_replay(
    *,
    project_root: Path | str = PROJECT_ROOT,
    output_dir: Path | str | None = None,
    manifest_path: Path | str | None = None,
    cursors_path: Path | str | None = None,
    cursor_id: str | None = None,
    dataset: str | None = None,
    market: str | None = None,
    symbol: str | None = None,
    interval: str | None = None,
    source: str | None = None,
    start_after: str | None = None,
    end_at: str | None = None,
    limit: int | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    payload = build_event_replay(
        project_root=project_root,
        manifest_path=manifest_path,
        cursors_path=cursors_path,
        cursor_id=cursor_id,
        dataset=dataset,
        market=market,
        symbol=symbol,
        interval=interval,
        source=source,
        start_after=start_after,
        end_at=end_at,
        limit=limit,
        as_of=as_of,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "replay"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    cursor_part = _cursor_path_part(payload.get("selected_cursors", []))
    stem = f"EventReplay_{cursor_part}_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    latest_json = target / "EventReplay_latest.json"
    latest_csv = target / "EventReplay_latest.csv"
    latest_markdown = target / "EventReplay_latest.md"
    payload["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "latest_json": str(latest_json),
        "latest_csv": str(latest_csv),
        "latest_markdown": str(latest_markdown),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    csv_text = event_replay_csv(payload.get("records", []))
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    markdown = event_replay_markdown(payload)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    return payload


def event_replay_csv(records: list[dict[str, Any]]) -> str:
    return pd.DataFrame(records, columns=EVENT_REPLAY_RECORD_COLUMNS).to_csv(index=False)


def event_replay_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Event Replay {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Status: `{payload.get('replay_status', '')}`",
        f"- Cursors: `{payload.get('cursor_count', 0)}`",
        f"- Assets: `{payload.get('asset_count', 0)}`",
        f"- Source Events: `{payload.get('source_event_count', 0)}`",
        f"- Emitted Events: `{payload.get('event_count', 0)}`",
        f"- Window: `{payload.get('first_event_time', '')}` -> `{payload.get('last_event_time', '')}`",
        f"- Next After: `{payload.get('next_after', '')}`",
        "",
        "## Selected Cursors",
        _markdown_table(
            payload.get("selected_cursors", []),
            ["cursor_id", "dataset", "market", "symbol", "interval", "source", "event_count", "first_event_time", "last_event_time"],
        ),
        "",
        "## Replay Records",
        _markdown_table(payload.get("records", [])[:40], EVENT_REPLAY_RECORD_COLUMNS),
        "",
        "## Missing Data Log",
        _markdown_table(payload.get("missing_data_log", []), ["dataset", "status", "message"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _read_manifest(path: Path, missing_data_log: list[dict[str, str]]) -> dict[str, Any]:
    if not path.exists():
        missing_data_log.append(_missing("data_lake_manifest", f"Manifest file not found: {path}"))
        return {"schema": DATA_LAKE_MANIFEST_SCHEMA, "assets": [], "replay_cursors": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        missing_data_log.append(_missing("data_lake_manifest", f"Manifest file is not valid JSON: {path}"))
        return {"schema": DATA_LAKE_MANIFEST_SCHEMA, "assets": [], "replay_cursors": []}
    if not isinstance(payload, dict) or payload.get("schema") != DATA_LAKE_MANIFEST_SCHEMA:
        missing_data_log.append(_missing("data_lake_manifest", f"Manifest schema is not {DATA_LAKE_MANIFEST_SCHEMA}: {path}"))
        return {"schema": DATA_LAKE_MANIFEST_SCHEMA, "assets": [], "replay_cursors": []}
    return payload


def _read_cursor_payload(path: Path, missing_data_log: list[dict[str, str]]) -> dict[str, Any]:
    if not path.exists():
        missing_data_log.append(_missing("replay_cursors", f"Replay cursor file not found: {path}"))
        return {"schema": DATA_LAKE_REPLAY_CURSOR_SCHEMA, "replay_cursors": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        missing_data_log.append(_missing("replay_cursors", f"Replay cursor file is not valid JSON: {path}"))
        return {"schema": DATA_LAKE_REPLAY_CURSOR_SCHEMA, "replay_cursors": []}
    if not isinstance(payload, dict) or payload.get("schema") != DATA_LAKE_REPLAY_CURSOR_SCHEMA:
        missing_data_log.append(_missing("replay_cursors", f"Replay cursor schema is not {DATA_LAKE_REPLAY_CURSOR_SCHEMA}: {path}"))
        return {"schema": DATA_LAKE_REPLAY_CURSOR_SCHEMA, "replay_cursors": []}
    return payload


def _cursor_rows(manifest: dict[str, Any], cursor_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = cursor_payload.get("replay_cursors") or manifest.get("replay_cursors") or []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _select_cursors(
    cursors: list[dict[str, Any]],
    *,
    cursor_id: str | None,
    dataset: str | None,
    market: str | None,
    symbol: str | None,
    interval: str | None,
    source: str | None,
) -> list[dict[str, Any]]:
    selected = []
    for cursor in cursors:
        if cursor_id and str(cursor.get("cursor_id", "")) != cursor_id:
            continue
        if dataset and str(cursor.get("dataset", "")) != dataset:
            continue
        if market and str(cursor.get("market", "")).upper() != market.upper():
            continue
        if symbol and str(cursor.get("symbol", "")).upper() != symbol.upper():
            continue
        if interval and str(cursor.get("interval", "")) != interval:
            continue
        if source and str(cursor.get("source", "")) != source:
            continue
        selected.append(cursor)
    if not any([cursor_id, dataset, market, symbol, interval, source]) and selected:
        return [selected[0]]
    return selected


def _select_assets(
    assets: list[dict[str, Any]],
    cursor_ids: set[str],
    missing_data_log: list[dict[str, str]],
) -> list[dict[str, Any]]:
    selected = [dict(asset) for asset in assets if str(asset.get("replay_cursor_id", "")) in cursor_ids]
    unsupported = [asset for asset in selected if str(asset.get("dataset", "")) != "market_events"]
    if unsupported:
        missing_data_log.append(_missing("event_replay", "Only market_events JSONL assets are replayable in this MVP."))
    replayable = [asset for asset in selected if str(asset.get("dataset", "")) == "market_events"]
    if cursor_ids and not replayable:
        missing_data_log.append(_missing("market_events", "No replayable market event assets matched the selected cursor."))
    return replayable


def _event_records(
    *,
    root: Path,
    assets: list[dict[str, Any]],
    start_after: str | None,
    end_at: str | None,
    limit: int | None,
    missing_data_log: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    for asset in assets:
        path = root / str(asset.get("relative_path", ""))
        if not path.exists():
            missing_data_log.append(_missing("market_events", f"Market event asset not found: {path}"))
            continue
        try:
            events = read_market_events_jsonl(path)
        except ValueError as exc:
            missing_data_log.append(_missing("market_events", str(exc)))
            continue
        for event in events:
            event_time = str(event.get("event_time", ""))
            if start_after and event_time <= start_after:
                continue
            if end_at and event_time > end_at:
                continue
            rows.append(_record_from_event(asset, event))
    ordered = sorted(rows, key=lambda row: (str(row.get("event_time", "")), str(row.get("event_id", ""))))
    total = len(ordered)
    if limit is not None and limit >= 0:
        ordered = ordered[:limit]
    for index, row in enumerate(ordered, start=1):
        row["replay_index"] = index
    return ordered, total


def _record_from_event(asset: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    return {
        "replay_index": 0,
        "cursor_id": asset.get("replay_cursor_id", ""),
        "asset_id": asset.get("asset_id", ""),
        "event_id": event.get("event_id", ""),
        "event_time": event.get("event_time", ""),
        "event_type": event.get("event_type", ""),
        "symbol": event.get("symbol", asset.get("symbol", "")),
        "market": event.get("market", asset.get("market", "")),
        "interval": event.get("interval", asset.get("interval", "")),
        "source": event.get("source", asset.get("source", "")),
        "quality_status": event.get("quality_status", asset.get("quality_status", "")),
        "evidence_layer": event.get("evidence_layer", ""),
        "payload_json": json.dumps(payload if isinstance(payload, dict) else {}, ensure_ascii=False, sort_keys=True),
    }


def _replay_status(
    records: list[dict[str, Any]],
    selected_cursors: list[dict[str, Any]],
    selected_assets: list[dict[str, Any]],
    missing_data_log: list[dict[str, str]],
) -> str:
    if records and any(str(row.get("quality_status", "")) not in {"", "Pass"} for row in records):
        return "Review"
    if records:
        return "Pass"
    if selected_cursors or selected_assets or missing_data_log:
        return "Empty"
    return "Empty"


def _cursor_path_part(cursors: list[dict[str, Any]]) -> str:
    if not cursors:
        return "empty"
    if len(cursors) == 1:
        return _safe_path_part(str(cursors[0].get("cursor_id", "cursor")))
    return "multi"


def _safe_path_part(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return safe.strip("._") or "cursor"


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _missing(dataset: str, message: str) -> dict[str, str]:
    return {"dataset": dataset, "status": "Missing", "message": message}


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")
