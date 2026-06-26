from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import CACHE_DATA_DIR, PROJECT_ROOT
from pfi_os.data.market_events import MARKET_EVENT_LOG_SCHEMA, MARKET_EVENT_SCHEMA, read_market_events_jsonl
from pfi_os.data.models import REQUIRED_BAR_COLUMNS
from pfi_os.storage import atomic_write_json, atomic_write_text


DATA_LAKE_MANIFEST_SCHEMA = "PFIOSReproducibleDataLakeManifestV1"
DATA_LAKE_REPLAY_CURSOR_SCHEMA = "PFIOSDataLakeReplayCursorV1"
ASSET_COLUMNS = [
    "asset_id",
    "dataset",
    "asset_type",
    "format",
    "relative_path",
    "size_bytes",
    "checksum_sha256",
    "schema",
    "market",
    "symbol",
    "interval",
    "source",
    "partition",
    "row_count",
    "first_event_time",
    "last_event_time",
    "quality_status",
    "replay_cursor_id",
]
CURSOR_COLUMNS = [
    "cursor_id",
    "dataset",
    "market",
    "symbol",
    "interval",
    "source",
    "asset_count",
    "event_count",
    "first_event_time",
    "last_event_time",
    "next_after",
]


def build_data_lake_manifest(
    *,
    project_root: Path | str = PROJECT_ROOT,
    as_of: str | None = None,
    include_cache: bool = True,
    include_market_events: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    assets: list[dict[str, Any]] = []
    missing_data_log: list[dict[str, str]] = []
    if include_market_events:
        event_assets = _market_event_assets(root)
        if event_assets:
            assets.extend(event_assets)
        else:
            missing_data_log.append(_missing("market_events", "No immutable MarketEventLog_*.jsonl files found."))
    if include_cache:
        cache_assets = _bar_cache_assets(root)
        if cache_assets:
            assets.extend(cache_assets)
        else:
            missing_data_log.append(_missing("bar_cache", "No structured bar cache CSV/Parquet files found."))
    latest_aliases = _latest_aliases(root)
    replay_cursors = _replay_cursors(assets)
    partitions = _partitions(assets)
    status = _lake_status(assets, missing_data_log)
    return {
        "schema": DATA_LAKE_MANIFEST_SCHEMA,
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "layer": "Reproducible Data Lake",
        "lake_status": status,
        "project_root": str(root),
        "asset_count": len(assets),
        "immutable_asset_count": len(assets),
        "latest_alias_count": len(latest_aliases),
        "partition_count": len(partitions),
        "replay_cursor_count": len(replay_cursors),
        "assets": assets,
        "partitions": partitions,
        "replay_cursors": replay_cursors,
        "latest_aliases": latest_aliases,
        "missing_data_log": missing_data_log,
        "assumptions": [
            "The manifest indexes local immutable data assets and records mutable latest files only as aliases.",
            "Checksums are SHA-256 over file bytes; replay cursors are derived from event_time windows.",
            "This MVP does not copy assets, stream Kafka, write QuestDB/ClickHouse, or connect to live trading.",
        ],
    }


def write_data_lake_manifest(
    *,
    project_root: Path | str = PROJECT_ROOT,
    as_of: str | None = None,
    output_dir: Path | str | None = None,
    include_cache: bool = True,
    include_market_events: bool = True,
) -> dict[str, Any]:
    payload = build_data_lake_manifest(
        project_root=project_root,
        as_of=as_of,
        include_cache=include_cache,
        include_market_events=include_market_events,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "dataLake"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"DataLakeManifest_{stamp}"
    json_path = target / f"{stem}.json"
    assets_csv_path = target / f"{stem}_assets.csv"
    cursors_json_path = target / f"{stem}_replay_cursors.json"
    cursors_csv_path = target / f"{stem}_replay_cursors.csv"
    markdown_path = target / f"{stem}.md"
    latest_json = target / "DataLakeManifest_latest.json"
    latest_assets_csv = target / "DataLakeManifest_latest_assets.csv"
    latest_cursors_json = target / "DataLakeManifest_latest_replay_cursors.json"
    latest_cursors_csv = target / "DataLakeManifest_latest_replay_cursors.csv"
    latest_markdown = target / "DataLakeManifest_latest.md"
    payload["outputs"] = {
        "json": str(json_path),
        "assets_csv": str(assets_csv_path),
        "replay_cursors_json": str(cursors_json_path),
        "replay_cursors_csv": str(cursors_csv_path),
        "markdown": str(markdown_path),
        "latest_json": str(latest_json),
        "latest_assets_csv": str(latest_assets_csv),
        "latest_replay_cursors_json": str(latest_cursors_json),
        "latest_replay_cursors_csv": str(latest_cursors_csv),
        "latest_markdown": str(latest_markdown),
    }
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    assets_csv = data_lake_assets_csv(payload.get("assets", []))
    atomic_write_text(assets_csv_path, assets_csv)
    atomic_write_text(latest_assets_csv, assets_csv)
    cursor_payload = {"schema": DATA_LAKE_REPLAY_CURSOR_SCHEMA, "as_of": payload["as_of"], "replay_cursors": payload.get("replay_cursors", [])}
    atomic_write_json(cursors_json_path, cursor_payload)
    atomic_write_json(latest_cursors_json, cursor_payload)
    cursors_csv = data_lake_replay_cursors_csv(payload.get("replay_cursors", []))
    atomic_write_text(cursors_csv_path, cursors_csv)
    atomic_write_text(latest_cursors_csv, cursors_csv)
    markdown = data_lake_manifest_markdown(payload)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    return payload


def data_lake_assets_csv(assets: list[dict[str, Any]]) -> str:
    return pd.DataFrame(assets, columns=ASSET_COLUMNS).to_csv(index=False)


def data_lake_replay_cursors_csv(cursors: list[dict[str, Any]]) -> str:
    return pd.DataFrame(cursors, columns=CURSOR_COLUMNS).to_csv(index=False)


def data_lake_manifest_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Reproducible Data Lake {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Status: `{payload.get('lake_status', '')}`",
        f"- Assets: `{payload.get('asset_count', 0)}`",
        f"- Partitions: `{payload.get('partition_count', 0)}`",
        f"- Replay Cursors: `{payload.get('replay_cursor_count', 0)}`",
        f"- Latest Aliases: `{payload.get('latest_alias_count', 0)}`",
        "",
        "## Partitions",
        _markdown_table(payload.get("partitions", []), ["partition", "dataset", "asset_count", "row_count", "first_event_time", "last_event_time"]),
        "",
        "## Replay Cursors",
        _markdown_table(payload.get("replay_cursors", []), CURSOR_COLUMNS),
        "",
        "## Assets",
        _markdown_table(payload.get("assets", [])[:40], ASSET_COLUMNS),
        "",
        "## Missing Data Log",
        _markdown_table(payload.get("missing_data_log", []), ["dataset", "status", "message"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _market_event_assets(root: Path) -> list[dict[str, Any]]:
    event_dir = root / "data" / "marketEvents"
    if not event_dir.exists():
        return []
    assets: list[dict[str, Any]] = []
    for path in sorted(event_dir.glob("MarketEventLog_*.jsonl")):
        if "latest" in path.name:
            continue
        events = read_market_events_jsonl(path)
        if not events:
            continue
        first = events[0]
        last = events[-1]
        market = str(first.get("market", "UNKNOWN")).upper()
        symbol = str(first.get("symbol", "UNKNOWN"))
        interval = str(first.get("interval", "UNKNOWN"))
        source = str(first.get("source", "UNKNOWN"))
        row_count = len(events)
        first_event_time = str(first.get("event_time", ""))
        last_event_time = str(last.get("event_time", ""))
        assets.append(
            _asset_row(
                root=root,
                path=path,
                dataset="market_events",
                asset_type="event_jsonl",
                schema=MARKET_EVENT_SCHEMA,
                market=market,
                symbol=symbol,
                interval=interval,
                source=source,
                row_count=row_count,
                first_event_time=first_event_time,
                last_event_time=last_event_time,
                quality_status=_worst_quality(events),
                replay_cursor_id=_cursor_id("market_events", market, symbol, interval, source),
            )
        )
    return assets


def _bar_cache_assets(root: Path) -> list[dict[str, Any]]:
    cache_root = root / CACHE_DATA_DIR.relative_to(PROJECT_ROOT)
    if not cache_root.exists():
        return []
    assets: list[dict[str, Any]] = []
    for path in sorted([*cache_root.glob("**/*.csv"), *cache_root.glob("**/*.parquet")]):
        meta = _bar_cache_meta(cache_root, path)
        if meta is None:
            continue
        asset_type = str(meta.pop("asset_type"))
        assets.append(_asset_row(root=root, path=path, dataset="bar_cache", asset_type=asset_type, **meta))
    return assets


def _bar_cache_meta(cache_root: Path, path: Path) -> dict[str, Any] | None:
    try:
        relative = path.relative_to(cache_root)
    except ValueError:
        return None
    if len(relative.parts) < 3:
        return None
    market, interval = relative.parts[0], relative.parts[1]
    symbol = Path(relative.parts[-1]).stem
    try:
        frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    except Exception:
        return None
    required = set(REQUIRED_BAR_COLUMNS)
    if not required.issubset({str(column).lower() for column in frame.columns}):
        return None
    frame.columns = [str(column).lower() for column in frame.columns]
    frame["datetime"] = pd.to_datetime(frame["datetime"], errors="coerce")
    frame = frame.dropna(subset=["datetime"]).sort_values("datetime")
    if frame.empty:
        return None
    return {
        "asset_type": "bar_parquet" if path.suffix == ".parquet" else "bar_csv",
        "schema": "PFIOSOHLCV",
        "market": market.upper(),
        "symbol": symbol,
        "interval": interval,
        "source": "DataStore",
        "row_count": int(len(frame)),
        "first_event_time": pd.Timestamp(frame["datetime"].iloc[0]).isoformat(),
        "last_event_time": pd.Timestamp(frame["datetime"].iloc[-1]).isoformat(),
        "quality_status": "Pass",
        "replay_cursor_id": _cursor_id("bar_cache", market.upper(), symbol, interval, "DataStore"),
    }


def _latest_aliases(root: Path) -> list[dict[str, Any]]:
    aliases = []
    for path in sorted((root / "data" / "marketEvents").glob("*latest*")) if (root / "data" / "marketEvents").exists() else []:
        if path.is_file():
            aliases.append(
                {
                    "relative_path": _relative(root, path),
                    "size_bytes": path.stat().st_size,
                    "checksum_sha256": _sha256(path),
                    "status": "MutableAlias",
                }
            )
    return aliases


def _replay_cursors(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for asset in assets:
        cursor_id = str(asset.get("replay_cursor_id", ""))
        if not cursor_id:
            continue
        row = groups.setdefault(
            cursor_id,
            {
                "cursor_id": cursor_id,
                "dataset": asset.get("dataset", ""),
                "market": asset.get("market", ""),
                "symbol": asset.get("symbol", ""),
                "interval": asset.get("interval", ""),
                "source": asset.get("source", ""),
                "asset_count": 0,
                "event_count": 0,
                "first_event_time": asset.get("first_event_time", ""),
                "last_event_time": asset.get("last_event_time", ""),
                "next_after": asset.get("last_event_time", ""),
            },
        )
        row["asset_count"] = int(row["asset_count"]) + 1
        row["event_count"] = int(row["event_count"]) + int(asset.get("row_count", 0) or 0)
        row["first_event_time"] = min(str(row["first_event_time"]), str(asset.get("first_event_time", "")))
        row["last_event_time"] = max(str(row["last_event_time"]), str(asset.get("last_event_time", "")))
        row["next_after"] = row["last_event_time"]
    return sorted(groups.values(), key=lambda row: (str(row.get("dataset", "")), str(row.get("market", "")), str(row.get("symbol", ""))))


def _partitions(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for asset in assets:
        key = str(asset.get("partition", ""))
        row = groups.setdefault(
            key,
            {
                "partition": key,
                "dataset": asset.get("dataset", ""),
                "asset_count": 0,
                "row_count": 0,
                "first_event_time": asset.get("first_event_time", ""),
                "last_event_time": asset.get("last_event_time", ""),
            },
        )
        row["asset_count"] = int(row["asset_count"]) + 1
        row["row_count"] = int(row["row_count"]) + int(asset.get("row_count", 0) or 0)
        row["first_event_time"] = min(str(row["first_event_time"]), str(asset.get("first_event_time", "")))
        row["last_event_time"] = max(str(row["last_event_time"]), str(asset.get("last_event_time", "")))
    return sorted(groups.values(), key=lambda row: str(row.get("partition", "")))


def _asset_row(
    *,
    root: Path,
    path: Path,
    dataset: str,
    asset_type: str,
    schema: str,
    market: str,
    symbol: str,
    interval: str,
    source: str,
    row_count: int,
    first_event_time: str,
    last_event_time: str,
    quality_status: str,
    replay_cursor_id: str,
) -> dict[str, Any]:
    checksum = _sha256(path)
    partition = f"dataset={dataset}/market={market.upper()}/symbol={symbol}/interval={interval}"
    return {
        "asset_id": hashlib.sha256(f"{_relative(root, path)}|{checksum}".encode("utf-8")).hexdigest()[:24],
        "dataset": dataset,
        "asset_type": asset_type,
        "format": path.suffix.lstrip("."),
        "relative_path": _relative(root, path),
        "size_bytes": path.stat().st_size,
        "checksum_sha256": checksum,
        "schema": schema,
        "market": market.upper(),
        "symbol": symbol,
        "interval": interval,
        "source": source,
        "partition": partition,
        "row_count": int(row_count),
        "first_event_time": first_event_time,
        "last_event_time": last_event_time,
        "quality_status": quality_status,
        "replay_cursor_id": replay_cursor_id,
    }


def _worst_quality(events: list[dict[str, Any]]) -> str:
    statuses = {str(event.get("quality_status", "")) for event in events}
    if "Review" in statuses:
        return "Review"
    if "Empty" in statuses:
        return "Empty"
    return "Pass" if statuses else "Empty"


def _lake_status(assets: list[dict[str, Any]], missing_data_log: list[dict[str, str]]) -> str:
    if not assets:
        return "Empty"
    if any(str(asset.get("quality_status")) == "Review" for asset in assets):
        return "Review"
    return "Pass"


def _missing(dataset: str, message: str) -> dict[str, str]:
    return {"dataset": dataset, "status": "Missing", "message": message}


def _cursor_id(dataset: str, market: str, symbol: str, interval: str, source: str) -> str:
    key = "|".join([dataset, market.upper(), symbol.upper(), interval, source])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")
