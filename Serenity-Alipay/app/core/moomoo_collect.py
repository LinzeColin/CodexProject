from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.moomoo_lifecycle import cleanup_started_processes, ensure_opend, lifecycle_to_dict
from app.db import connect, init_db, insert_row, upsert_asset


KLINE_TYPES = {
    "K_DAY": "K_DAY",
    "K_1M": "K_1M",
    "K_5M": "K_5M",
    "K_15M": "K_15M",
    "K_30M": "K_30M",
    "K_60M": "K_60M",
}


def safe_symbol(symbol: str) -> str:
    return symbol.replace(".", "_").replace("/", "_").replace(":", "_")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now_in(tz_name: str) -> str:
    return datetime.now(ZoneInfo(tz_name)).isoformat(timespec="seconds")


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _records_from_frame(frame: Any) -> list[dict[str, Any]]:
    return [{key: _json_safe(value) for key, value in row.items()} for row in frame.to_dict("records")]


def _kline_enum(ft: Any, ktype: str) -> Any:
    if ktype not in KLINE_TYPES:
        raise ValueError(f"Unsupported kline type: {ktype}")
    return getattr(ft.KLType, KLINE_TYPES[ktype])


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def collect_moomoo_data(
    settings: Settings,
    symbols: list[str],
    *,
    start: str,
    end: str,
    ktype: str = "K_DAY",
    host: str = "127.0.0.1",
    port: int = 11111,
    include_snapshot: bool = True,
    include_kline: bool = True,
    auto_start_opend: bool = True,
    cleanup_auto_started: bool = True,
    opend_wait_seconds: float = 20.0,
) -> dict[str, object]:
    if not symbols:
        raise ValueError("At least one symbol is required")

    init_db(settings.db_path)
    run_id = f"moomoo_collect_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    created_at = _now_utc()
    output_dir = settings.data_dir / "moomoo" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    lifecycle = ensure_opend(
        settings,
        host=host,
        port=port,
        auto_start=auto_start_opend,
        cleanup_if_started=cleanup_auto_started,
        wait_seconds=opend_wait_seconds,
    )
    lifecycle_result: dict[str, object] = lifecycle_to_dict(lifecycle)
    if not lifecycle.socket_is_reachable:
        errors = [{"scope": "opend", "message": lifecycle.detail}]
        with connect(settings.db_path) as conn:
            insert_row(
                conn,
                "run_log",
                {
                    "run_id": run_id,
                    "run_time_bj": _now_in(settings.timezone_primary),
                    "run_time_au": _now_in(settings.timezone_secondary),
                    "schedule_slot": "MOOMOO_COLLECT",
                    "model_profile": settings.model_profile,
                    "status": "failed",
                    "data_quality_status": "manual_review",
                    "notification_status": "not_applicable",
                    "notes": f"symbols={','.join(symbols)}; ktype={ktype}; source=moomoo_opend; opend_unreachable",
                    "report_path": None,
                    "offline_html_path": None,
                    "created_at": created_at,
                },
            )
            insert_row(
                conn,
                "audit_log",
                {
                    "run_id": run_id,
                    "event_type": "moomoo_collect_error",
                    "severity": "critical",
                    "message": lifecycle.detail,
                    "context_json": json.dumps({"lifecycle": lifecycle_result}, ensure_ascii=False),
                    "created_at": created_at,
                },
            )
        return {
            "run_id": run_id,
            "status": "failed",
            "symbols": symbols,
            "snapshot_path": None,
            "kline_outputs": [],
            "errors": errors,
            "opend_lifecycle": lifecycle_result,
            "output_dir": str(output_dir),
        }

    import moomoo as ft

    quote_ctx = ft.OpenQuoteContext(host=host, port=port)
    snapshot_path: Path | None = None
    kline_outputs: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    global_state: dict[str, Any] = {}
    cleanup_result: dict[str, object] | None = None

    try:
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            global_state = {key: _json_safe(value) for key, value in dict(state).items()}
        else:
            errors.append({"scope": "global_state", "message": str(state)})

        if include_snapshot:
            ret, data = quote_ctx.get_market_snapshot(symbols)
            if ret == ft.RET_OK:
                snapshot_records = _records_from_frame(data)
                snapshot_path = output_dir / "snapshot.json"
                snapshot_path.write_text(
                    json.dumps(
                        {
                            "run_id": run_id,
                            "fetched_at": created_at,
                            "source": "moomoo OpenD",
                            "symbols": symbols,
                            "global_state": global_state,
                            "records": snapshot_records,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            else:
                errors.append({"scope": "snapshot", "message": str(data)})

        if include_kline:
            for symbol in symbols:
                frames = []
                ret, data, page_req_key = quote_ctx.request_history_kline(
                    symbol,
                    start=start,
                    end=end,
                    ktype=_kline_enum(ft, ktype),
                )
                if ret != ft.RET_OK:
                    errors.append({"scope": f"kline:{symbol}", "message": str(data)})
                    continue
                frames.append(data)
                while page_req_key:
                    ret, data, page_req_key = quote_ctx.request_history_kline(
                        symbol,
                        start=start,
                        end=end,
                        ktype=_kline_enum(ft, ktype),
                        page_req_key=page_req_key,
                    )
                    if ret != ft.RET_OK:
                        errors.append({"scope": f"kline:{symbol}", "message": str(data)})
                        break
                    frames.append(data)
                if not frames:
                    continue
                all_data = frames[0] if len(frames) == 1 else __import__("pandas").concat(frames, ignore_index=True)
                rows = _records_from_frame(all_data)
                path = output_dir / f"{safe_symbol(symbol)}_{ktype}_{start}_{end}.csv"
                _write_csv(path, rows)
                kline_outputs.append({"symbol": symbol, "rows": len(rows), "path": str(path)})
    finally:
        quote_ctx.close()
        if cleanup_auto_started and lifecycle.started_by_tool and lifecycle.socket_is_reachable:
            cleanup_result = cleanup_started_processes(lifecycle)

    status = "success" if not errors else ("partial" if kline_outputs or snapshot_path else "failed")
    with connect(settings.db_path) as conn:
        insert_row(
            conn,
            "run_log",
            {
                "run_id": run_id,
                "run_time_bj": _now_in(settings.timezone_primary),
                "run_time_au": _now_in(settings.timezone_secondary),
                "schedule_slot": "MOOMOO_COLLECT",
                "model_profile": settings.model_profile,
                "status": status,
                "data_quality_status": "pass" if status == "success" else "manual_review",
                "notification_status": "not_applicable",
                    "notes": (
                        f"symbols={','.join(symbols)}; ktype={ktype}; source=moomoo_opend; "
                        f"opend_started_by_tool={lifecycle.started_by_tool}"
                    ),
                "report_path": None,
                "offline_html_path": None,
                "created_at": created_at,
            },
        )
        for symbol in symbols:
            upsert_asset(
                conn,
                {
                    "asset_id": symbol,
                    "asset_code": symbol,
                    "asset_name": symbol,
                    "asset_type": "market_symbol",
                    "market": symbol.split(".", 1)[0] if "." in symbol else None,
                    "fund_company": None,
                    "risk_level": None,
                    "is_excluded": 0,
                    "exclusion_reason": None,
                },
            )
        if snapshot_path:
            insert_row(
                conn,
                "source_log",
                {
                    "source_id": f"{run_id}_snapshot",
                    "run_id": run_id,
                    "asset_id": None,
                    "source_name": "moomoo OpenD snapshot",
                    "source_type": "moomoo",
                    "source_priority": 1,
                    "url_or_path": str(snapshot_path),
                    "observed_at": created_at,
                    "fetched_at": created_at,
                    "evidence_level": "Strong",
                    "field_list": "global_state,market_snapshot",
                    "fallback_aggregated": 0,
                    "conflict_group": None,
                },
            )
        for output in kline_outputs:
            symbol = str(output["symbol"])
            source_id = f"{run_id}_{safe_symbol(symbol)}_kline"
            insert_row(
                conn,
                "source_log",
                {
                    "source_id": source_id,
                    "run_id": run_id,
                    "asset_id": symbol,
                    "source_name": "moomoo OpenD historical kline",
                    "source_type": "moomoo",
                    "source_priority": 1,
                    "url_or_path": str(output["path"]),
                    "observed_at": end,
                    "fetched_at": created_at,
                    "evidence_level": "Strong",
                    "field_list": "open,high,low,close,volume,turnover",
                    "fallback_aggregated": 0,
                    "conflict_group": None,
                },
            )
            with Path(str(output["path"])).open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    start_time = row.get("time_key") or row.get("time") or row.get("date") or ""
                    insert_row(
                        conn,
                        "market_kline_snapshot",
                        {
                            "run_id": run_id,
                            "asset_id": symbol,
                            "bar_interval": ktype,
                            "start_time": start_time,
                            "end_time": start_time,
                            "open": _safe_float(row.get("open")),
                            "high": _safe_float(row.get("high")),
                            "low": _safe_float(row.get("low")),
                            "close": _safe_float(row.get("close")),
                            "volume": _safe_float(row.get("volume")),
                            "turnover": _safe_float(row.get("turnover")),
                            "source_id": source_id,
                        },
                    )
        if cleanup_result:
            insert_row(
                conn,
                "audit_log",
                {
                    "run_id": run_id,
                    "event_type": "moomoo_opend_cleanup",
                    "severity": "info",
                    "message": str(cleanup_result.get("cleanup_result")),
                    "context_json": json.dumps(cleanup_result, ensure_ascii=False),
                    "created_at": created_at,
                },
            )
        for error in errors:
            insert_row(
                conn,
                "audit_log",
                {
                    "run_id": run_id,
                    "event_type": "moomoo_collect_error",
                    "severity": "warn",
                    "message": error["message"],
                    "context_json": json.dumps(error, ensure_ascii=False),
                    "created_at": created_at,
                },
            )
    return {
        "run_id": run_id,
        "status": status,
        "symbols": symbols,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
        "kline_outputs": kline_outputs,
        "errors": errors,
        "opend_lifecycle": lifecycle_result,
        "cleanup": cleanup_result,
        "output_dir": str(output_dir),
    }
