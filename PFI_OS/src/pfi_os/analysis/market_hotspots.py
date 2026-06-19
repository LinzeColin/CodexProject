from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pfi_os.analysis.sentiment import SentimentInstrument


HOTSPOT_REFRESH_TTL_SECONDS = 3600
HOTSPOT_RUNTIME_SUMMARY_SCHEMA = "PFIOSHotspotRuntimeSummaryV1"
HOTSPOT_PERSISTED_CACHE_SCHEMA = "PFIOSHotspotPersistedCacheV1"
HOTSPOT_CACHE_STATUS_SCHEMA = "PFIOSHotspotCacheStatusV1"
HOTSPOT_CACHE_DIRECTORY_SUMMARY_SCHEMA = "PFIOSHotspotCacheDirectorySummaryV1"
HOTSPOT_REQUEST_TRACE_SCHEMA = "PFIOSHotspotRequestTraceV1"
HOTSPOT_STABLE_HEAT_SPAN = 5
HOTSPOT_STABLE_HEAT_WARMUP_SNAPSHOTS = 30
HOTSPOT_MAX_STABLE_HEAT_STEP = 12.0


@dataclass(frozen=True)
class HotspotSnapshotSummary:
    snapshot_time: str
    object_count: int
    average_heat_score: float
    strong_count: int
    weak_count: int
    leading_sector: str
    lagging_sector: str


def default_hotspot_universe(market: str) -> list[SentimentInstrument]:
    normalized = market.upper()
    if normalized == "CN":
        return [
            SentimentInstrument("000001", "上证指数", "CN", "宽基指数"),
            SentimentInstrument("399001", "深证成指", "CN", "宽基指数"),
            SentimentInstrument("399006", "创业板指", "CN", "成长风格"),
            SentimentInstrument("510300", "沪深300ETF", "CN", "大盘宽基"),
            SentimentInstrument("512760", "半导体ETF", "CN", "科技制造"),
            SentimentInstrument("512880", "证券ETF", "CN", "金融周期"),
            SentimentInstrument("512400", "有色金属ETF", "CN", "资源周期"),
            SentimentInstrument("518880", "黄金ETF", "CN", "避险资产"),
        ]
    if normalized == "HK":
        return [
            SentimentInstrument("^HSI", "恒生指数", "HK", "宽基指数"),
            SentimentInstrument("3033.HK", "恒生科技ETF", "HK", "科技成长"),
            SentimentInstrument("2800.HK", "盈富基金", "HK", "大盘宽基"),
            SentimentInstrument("3067.HK", "恒生中国企业ETF", "HK", "中资蓝筹"),
            SentimentInstrument("2840.HK", "SPDR金ETF", "HK", "避险资产"),
        ]
    return [
        SentimentInstrument("SPY", "S&P 500 ETF", "US", "大盘宽基"),
        SentimentInstrument("QQQ", "NASDAQ 100 ETF", "US", "科技成长"),
        SentimentInstrument("IWM", "Russell 2000 ETF", "US", "小盘风格"),
        SentimentInstrument("SMH", "半导体ETF", "US", "科技制造"),
        SentimentInstrument("XLF", "金融ETF", "US", "金融"),
        SentimentInstrument("XLE", "能源ETF", "US", "能源"),
        SentimentInstrument("XLV", "医疗ETF", "US", "医疗"),
        SentimentInstrument("XLY", "可选消费ETF", "US", "消费"),
        SentimentInstrument("GLD", "黄金ETF", "US", "避险资产"),
        SentimentInstrument("TLT", "长期美债ETF", "US", "利率资产"),
        SentimentInstrument("^VIX", "VIX波动率", "US", "风险温度"),
    ]


def build_hotspot_history(
    price_frames: dict[str, pd.DataFrame],
    instruments: list[SentimentInstrument],
    data_source: str = "",
    max_snapshots: int = 48,
    display_start: str | pd.Timestamp | None = None,
    display_end: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    instrument_by_symbol = {item.symbol: item for item in instruments}
    display_start_ts = _display_boundary_timestamp(display_start)
    display_end_ts = _display_boundary_timestamp(display_end, end_of_day=True)
    cleaned: dict[str, pd.DataFrame] = {}
    snapshot_times: list[pd.Timestamp] = []
    for symbol, raw in price_frames.items():
        data = _clean_hotspot_bars(raw)
        if len(data) < 30:
            continue
        cleaned[symbol] = data
        candidate_times = data.loc[data["datetime"].notna(), "datetime"]
        if not pd.isna(display_end_ts):
            candidate_times = candidate_times[candidate_times.le(display_end_ts)]
        snapshot_times.extend(pd.to_datetime(candidate_times, errors="coerce").dropna().tolist())
    if not cleaned or not snapshot_times:
        return pd.DataFrame()
    all_snapshot_series = pd.Series(snapshot_times).drop_duplicates().sort_values(kind="mergesort").reset_index(drop=True)
    display_snapshot_series = all_snapshot_series.copy()
    if not pd.isna(display_start_ts):
        display_snapshot_series = display_snapshot_series[display_snapshot_series.ge(display_start_ts)]
    if not pd.isna(display_end_ts):
        display_snapshot_series = display_snapshot_series[display_snapshot_series.le(display_end_ts)]
    display_snapshot_series = display_snapshot_series.reset_index(drop=True)
    if display_snapshot_series.empty:
        return pd.DataFrame()
    if max_snapshots and max_snapshots > 0:
        display_snapshot_series = display_snapshot_series.tail(int(max_snapshots)).reset_index(drop=True)
    calculation_snapshot_series = _calculation_snapshot_series(all_snapshot_series, display_snapshot_series)
    display_snapshot_labels = {pd.Timestamp(value).isoformat() for value in display_snapshot_series}
    for snapshot_time in calculation_snapshot_series:
        snapshot_ts = pd.Timestamp(snapshot_time)
        for symbol, data in cleaned.items():
            instrument = instrument_by_symbol.get(symbol, SentimentInstrument(symbol, symbol, "", "观察对象"))
            idx = int(data["datetime"].searchsorted(snapshot_ts, side="right") - 1)
            if idx < 29:
                continue
            window = data.iloc[: idx + 1].copy()
            rows.append(_hotspot_row(window, instrument, data_source=data_source, snapshot_time=snapshot_ts))
    if not rows:
        return pd.DataFrame()
    history = pd.DataFrame(rows)
    history = _stabilize_hotspot_heat(history)
    history = history[history["snapshot_time"].astype(str).isin(display_snapshot_labels)].copy()
    if history.empty:
        return pd.DataFrame()
    history = history.sort_values(["snapshot_time", "sector", "name"]).reset_index(drop=True)
    return history


def hotspot_summary(rows: pd.DataFrame, snapshot_time: str | None = None) -> HotspotSnapshotSummary:
    current = _hotspot_current_slice(rows, snapshot_time)
    if current.empty:
        return HotspotSnapshotSummary("", 0, 0.0, 0, 0, "", "")
    heat = pd.to_numeric(current["heat_score"], errors="coerce").fillna(50.0)
    strong = current[current["hotspot_state"].isin(["强势扩散", "局部偏强"])]
    weak = current[current["hotspot_state"].isin(["局部偏弱", "风险降温"])]
    sector_scores = current.assign(_heat=heat).groupby("sector")["_heat"].mean().sort_values()
    return HotspotSnapshotSummary(
        snapshot_time=str(current["snapshot_time"].max()),
        object_count=int(len(current)),
        average_heat_score=float(round(heat.mean(), 2)),
        strong_count=int(len(strong)),
        weak_count=int(len(weak)),
        leading_sector=str(sector_scores.index[-1]) if not sector_scores.empty else "",
        lagging_sector=str(sector_scores.index[0]) if not sector_scores.empty else "",
    )


def hotspot_focus_rows(rows: pd.DataFrame, snapshot_time: str | None = None, n: int = 6) -> pd.DataFrame:
    current = _hotspot_current_slice(rows, snapshot_time)
    if current.empty:
        return current
    current = current.copy()
    current["_distance"] = (pd.to_numeric(current["heat_score"], errors="coerce").fillna(50.0) - 50.0).abs()
    return current.sort_values(["_distance", "five_step_return"], ascending=[False, False]).head(n).drop(columns=["_distance"])


def hotspot_runtime_cache_key(
    *,
    data_source: str,
    market: str,
    interval: str,
    instruments: list[SentimentInstrument] | tuple[SentimentInstrument, ...],
    display_start: str,
    display_end: str,
    max_snapshots: int,
) -> str:
    payload = {
        "data_source": str(data_source).strip(),
        "market": str(market).strip().upper(),
        "interval": str(interval).strip().lower(),
        "instruments": sorted(_instrument_cache_payload(item) for item in instruments),
        "display_start": str(display_start),
        "display_end": str(display_end),
        "max_snapshots": int(max_snapshots),
        "ttl_seconds": HOTSPOT_REFRESH_TTL_SECONDS,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def hotspot_runtime_summary(
    history: pd.DataFrame,
    errors: list[dict[str, str]],
    *,
    data_source: str,
    market: str,
    interval: str,
    requested_count: int | None = None,
    max_snapshots: int = 0,
    ttl_seconds: int = HOTSPOT_REFRESH_TTL_SECONDS,
    request_key: str = "",
    cache_source: str = "computed",
    persisted_cache_age_seconds: float | None = None,
    request_trace: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    requested = _hotspot_requested_count(history, errors, requested_count=requested_count)
    success_count = int(history["symbol"].nunique()) if not history.empty and "symbol" in history.columns else 0
    row_count = int(len(history))
    slice_count = int(history["snapshot_time"].nunique()) if not history.empty and "snapshot_time" in history.columns else 0
    first_snapshot = _hotspot_first_snapshot(history)
    latest_snapshot = _hotspot_latest_snapshot(history)
    cadence_minutes = _hotspot_cadence_minutes(history)
    gate_rows = build_hotspot_evidence_gate_rows(
        history,
        errors,
        data_source=data_source,
        interval=interval,
        requested_count=requested,
    )
    gate_status = _hotspot_gate_status(gate_rows)
    coverage_rate = 0.0 if requested <= 0 else success_count / requested
    failure_rate = 0.0 if requested <= 0 else len(errors) / requested
    cache_source_value = str(cache_source or "computed")
    cache_hit = cache_source_value == "persisted"
    cache_detail = "persisted cache hit" if cache_hit else "computed and eligible for persisted cache"
    return {
        "schema": HOTSPOT_RUNTIME_SUMMARY_SCHEMA,
        "status": gate_status,
        "market": str(market).upper(),
        "data_source": str(data_source),
        "interval": str(interval),
        "request_key": request_key,
        "ttl_seconds": int(ttl_seconds),
        "max_snapshots": int(max_snapshots or 0),
        "requested_count": requested,
        "success_count": success_count,
        "failed_count": int(len(errors)),
        "coverage_rate": round(float(coverage_rate), 4),
        "failure_rate": round(float(failure_rate), 4),
        "row_count": row_count,
        "slice_count": slice_count,
        "first_snapshot": first_snapshot,
        "latest_snapshot": latest_snapshot,
        "cadence_minutes": None if cadence_minutes is None else round(float(cadence_minutes), 2),
        "cache_source": cache_source_value,
        "cache_hit": cache_hit,
        "persisted_cache_age_seconds": None if persisted_cache_age_seconds is None else round(float(persisted_cache_age_seconds), 2),
        "request_trace": hotspot_request_trace_summary(request_trace or []),
        "gate_rows": gate_rows,
        "cards": [
            {"label": "证据状态", "value": gate_status, "detail": "Review/Block 只作研究观察"},
            {"label": "对象覆盖", "value": f"{success_count}/{requested}", "detail": f"coverage={coverage_rate:.2%}"},
            {"label": "时间切片", "value": slice_count, "detail": f"rows={row_count}, max={int(max_snapshots or 0)}"},
            {"label": "缓存状态", "value": "Persisted Hit" if cache_hit else "Computed", "detail": f"{cache_detail}; ttl={int(ttl_seconds) // 60} min"},
        ],
        "token_policy": (
            "UI renders this compact runtime summary after cached hotspot history; it does not retain raw price frames, "
            "rerun charts for guidance text, connect brokers, create orders, or mutate holdings. Persisted cache stores only "
            "computed hotspot rows and compact metadata under local data/cache."
        ),
        "safety_boundary": "Research observation only; no live trading, broker action, orders, or position sizing.",
    }


def hotspot_persisted_cache_path(cache_root: Path | str, request_key: str) -> Path:
    safe_key = "".join(char for char in str(request_key) if char.isalnum() or char in {"-", "_"})
    if not safe_key:
        raise ValueError("request_key is required for hotspot persisted cache")
    return Path(cache_root) / f"{safe_key}.json"


def write_hotspot_persisted_cache(
    cache_root: Path | str,
    *,
    request_key: str,
    history: pd.DataFrame,
    errors: list[dict[str, str]],
    summary: dict[str, object],
    request_trace: list[dict[str, object]] | None = None,
    ttl_seconds: int = HOTSPOT_REFRESH_TTL_SECONDS,
    now: pd.Timestamp | None = None,
) -> dict[str, object]:
    if history.empty:
        return {"schema": HOTSPOT_PERSISTED_CACHE_SCHEMA, "status": "Skipped", "reason": "empty_history"}
    path = hotspot_persisted_cache_path(cache_root, request_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    written_at = _utc_now(now).isoformat()
    payload = {
        "schema": HOTSPOT_PERSISTED_CACHE_SCHEMA,
        "request_key": str(request_key),
        "written_at": written_at,
        "ttl_seconds": int(ttl_seconds),
        "summary": summary,
        "errors": errors,
        "request_trace": _normalized_hotspot_trace_rows(request_trace or []),
        "history_records": _dataframe_records(history),
        "safety_boundary": "Local derived hotspot cache only; no raw provider frames, secrets, broker calls, orders, or holdings mutation.",
    }
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)
    return {
        "schema": HOTSPOT_PERSISTED_CACHE_SCHEMA,
        "status": "Written",
        "path": str(path),
        "request_key": str(request_key),
        "row_count": int(len(history)),
        "ttl_seconds": int(ttl_seconds),
        "written_at": written_at,
    }


def load_hotspot_persisted_cache(
    cache_root: Path | str,
    *,
    request_key: str,
    ttl_seconds: int = HOTSPOT_REFRESH_TTL_SECONDS,
    now: pd.Timestamp | None = None,
) -> dict[str, object] | None:
    try:
        path = hotspot_persisted_cache_path(cache_root, request_key)
    except ValueError:
        return None
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("schema") != HOTSPOT_PERSISTED_CACHE_SCHEMA or str(payload.get("request_key", "")) != str(request_key):
        return None
    written_at = pd.to_datetime(payload.get("written_at"), errors="coerce", utc=True)
    if pd.isna(written_at):
        return None
    age_seconds = float((_utc_now(now) - pd.Timestamp(written_at)).total_seconds())
    effective_ttl = int(payload.get("ttl_seconds") or ttl_seconds)
    if age_seconds < 0 or age_seconds > effective_ttl:
        return None
    records = payload.get("history_records", [])
    if not isinstance(records, list):
        return None
    history = pd.DataFrame(records)
    errors = payload.get("errors", [])
    if not isinstance(errors, list):
        errors = []
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    return {
        "schema": HOTSPOT_PERSISTED_CACHE_SCHEMA,
        "status": "Hit",
        "path": str(path),
        "request_key": str(request_key),
        "age_seconds": round(age_seconds, 2),
        "history": history,
        "errors": errors,
        "summary": summary,
        "request_trace": _normalized_hotspot_trace_rows(payload.get("request_trace", []) if isinstance(payload.get("request_trace", []), list) else []),
    }


def hotspot_request_trace_summary(trace_rows: list[dict[str, object]] | tuple[dict[str, object], ...]) -> dict[str, object]:
    rows = _normalized_hotspot_trace_rows(trace_rows)
    request_count = len(rows)
    success_count = sum(1 for row in rows if row.get("status") == "Pass")
    failed_count = sum(1 for row in rows if row.get("status") == "Fail")
    elapsed_values = [float(row.get("elapsed_ms", 0.0) or 0.0) for row in rows]
    total_elapsed = round(sum(elapsed_values), 2)
    average_elapsed = round(total_elapsed / request_count, 2) if request_count else 0.0
    slowest = sorted(rows, key=lambda row: float(row.get("elapsed_ms", 0.0) or 0.0), reverse=True)[:5]
    status = "Pass" if failed_count == 0 else "Review" if success_count > 0 else "Block"
    return {
        "schema": HOTSPOT_REQUEST_TRACE_SCHEMA,
        "status": status,
        "request_count": request_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "total_elapsed_ms": total_elapsed,
        "average_elapsed_ms": average_elapsed,
        "slowest_elapsed_ms": round(max(elapsed_values), 2) if elapsed_values else 0.0,
        "slowest": slowest,
        "token_policy": "Compact per-symbol timing only; no raw price frames, provider payloads, secrets, orders, or holdings mutations.",
        "safety_boundary": "Read-only request diagnostics for hotspot generation. Use to identify slow symbols/providers before recomputing.",
    }


def hotspot_persisted_cache_status(
    cache_root: Path | str,
    *,
    request_key: str,
    ttl_seconds: int = HOTSPOT_REFRESH_TTL_SECONDS,
    now: pd.Timestamp | None = None,
) -> dict[str, object]:
    try:
        path = hotspot_persisted_cache_path(cache_root, request_key)
    except ValueError:
        return _hotspot_cache_status_payload(request_key=request_key, path="", state="invalid_request", exists=False)
    if not path.exists():
        return _hotspot_cache_status_payload(request_key=request_key, path=str(path), state="miss", exists=False)
    file_kb = round(path.stat().st_size / 1024, 2)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _hotspot_cache_status_payload(
            request_key=request_key,
            path=str(path),
            state="corrupt",
            exists=True,
            file_kb=file_kb,
            detail=f"{type(exc).__name__}: {exc}",
        )
    if payload.get("schema") != HOTSPOT_PERSISTED_CACHE_SCHEMA or str(payload.get("request_key", "")) != str(request_key):
        return _hotspot_cache_status_payload(
            request_key=request_key,
            path=str(path),
            state="mismatch",
            exists=True,
            file_kb=file_kb,
            detail="schema or request_key mismatch",
        )
    written_at = pd.to_datetime(payload.get("written_at"), errors="coerce", utc=True)
    if pd.isna(written_at):
        return _hotspot_cache_status_payload(
            request_key=request_key,
            path=str(path),
            state="corrupt",
            exists=True,
            file_kb=file_kb,
            detail="written_at missing or invalid",
        )
    effective_ttl = int(payload.get("ttl_seconds") or ttl_seconds)
    age_seconds = float((_utc_now(now) - pd.Timestamp(written_at)).total_seconds())
    remaining_seconds = max(0.0, float(effective_ttl) - age_seconds)
    records = payload.get("history_records", [])
    summary = payload.get("summary", {})
    state = "hit" if 0 <= age_seconds <= effective_ttl else "expired"
    return _hotspot_cache_status_payload(
        request_key=request_key,
        path=str(path),
        state=state,
        exists=True,
        file_kb=file_kb,
        age_seconds=round(age_seconds, 2),
        remaining_seconds=round(remaining_seconds, 2),
        ttl_seconds=effective_ttl,
        row_count=len(records) if isinstance(records, list) else None,
        summary_status=str(summary.get("status", "")) if isinstance(summary, dict) else "",
    )


def hotspot_cache_directory_summary(
    cache_root: Path | str,
    *,
    ttl_seconds: int = HOTSPOT_REFRESH_TTL_SECONDS,
    now: pd.Timestamp | None = None,
) -> dict[str, object]:
    root = Path(cache_root)
    files = sorted(root.glob("*.json")) if root.exists() else []
    total_kb = round(sum(path.stat().st_size for path in files if path.is_file()) / 1024, 2)
    states: dict[str, int] = {"hit": 0, "expired": 0, "corrupt": 0, "mismatch": 0, "other": 0}
    for path in files:
        request_key = path.stem
        status = hotspot_persisted_cache_status(root, request_key=request_key, ttl_seconds=ttl_seconds, now=now)
        state = str(status.get("state", "other"))
        states[state if state in states else "other"] += 1
    return {
        "schema": HOTSPOT_CACHE_DIRECTORY_SUMMARY_SCHEMA,
        "status": "Available",
        "cache_root": str(root),
        "file_count": len(files),
        "total_kb": total_kb,
        "valid_count": states["hit"],
        "expired_count": states["expired"],
        "invalid_count": states["corrupt"] + states["mismatch"] + states["other"],
        "ttl_seconds": int(ttl_seconds),
        "states": states,
        "safety_boundary": "Derived hotspot cache metadata only; no raw provider frames, secrets, broker calls, orders, or holdings mutation.",
    }


def invalidate_hotspot_persisted_cache(cache_root: Path | str, *, request_key: str) -> dict[str, object]:
    try:
        path = hotspot_persisted_cache_path(cache_root, request_key)
    except ValueError:
        return {"schema": HOTSPOT_CACHE_STATUS_SCHEMA, "status": "InvalidRequest", "request_key": str(request_key), "path": ""}
    if not path.exists():
        return {"schema": HOTSPOT_CACHE_STATUS_SCHEMA, "status": "Missing", "request_key": str(request_key), "path": str(path), "bytes_removed": 0}
    size = path.stat().st_size
    try:
        path.unlink()
    except OSError as exc:
        return {
            "schema": HOTSPOT_CACHE_STATUS_SCHEMA,
            "status": "Failed",
            "request_key": str(request_key),
            "path": str(path),
            "bytes_removed": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "schema": HOTSPOT_CACHE_STATUS_SCHEMA,
        "status": "Deleted",
        "request_key": str(request_key),
        "path": str(path),
        "bytes_removed": int(size),
        "kb_removed": round(size / 1024, 2),
    }


def _hotspot_cache_status_payload(
    *,
    request_key: str,
    path: str,
    state: str,
    exists: bool,
    file_kb: float = 0.0,
    age_seconds: float | None = None,
    remaining_seconds: float | None = None,
    ttl_seconds: int = HOTSPOT_REFRESH_TTL_SECONDS,
    row_count: int | None = None,
    summary_status: str = "",
    detail: str = "",
) -> dict[str, object]:
    return {
        "schema": HOTSPOT_CACHE_STATUS_SCHEMA,
        "status": "Hit" if state == "hit" else "Miss" if state == "miss" else "Review",
        "state": state,
        "request_key": str(request_key),
        "path": path,
        "exists": bool(exists),
        "file_kb": float(file_kb),
        "age_seconds": age_seconds,
        "remaining_seconds": remaining_seconds,
        "ttl_seconds": int(ttl_seconds),
        "row_count": row_count,
        "summary_status": summary_status,
        "detail": detail,
        "safety_boundary": "Derived hotspot cache metadata only; no raw provider frames, secrets, broker calls, orders, or holdings mutation.",
    }


def build_hotspot_evidence_gate_rows(
    history: pd.DataFrame,
    errors: list[dict[str, str]],
    *,
    data_source: str,
    interval: str,
    requested_count: int | None = None,
) -> list[dict[str, str]]:
    requested = _hotspot_requested_count(history, errors, requested_count=requested_count)
    success_count = int(history["symbol"].nunique()) if not history.empty and "symbol" in history.columns else 0
    failure_rate = 0.0 if requested == 0 else len(errors) / requested
    coverage_rate = 0.0 if requested == 0 else success_count / requested
    sample_min = 0
    if not history.empty and "data_points" in history.columns:
        sample_min = int(pd.to_numeric(history["data_points"], errors="coerce").fillna(0).min())
    slice_count = int(history["snapshot_time"].nunique()) if not history.empty and "snapshot_time" in history.columns else 0
    cadence_minutes = _hotspot_cadence_minutes(history)
    latest_snapshot = _hotspot_latest_snapshot(history)
    source_status = "Review" if data_source.strip().lower() == "sample" else "Pass"
    source_note = "Sample 只用于功能演示；真实研究请切换到 Moomoo、Yahoo Finance 或 AKShare 等可验证数据源。" if source_status == "Review" else "当前选择真实数据源；仍需检查覆盖率、失败率和刷新粒度。"
    cadence_status, cadence_note = _hotspot_cadence_status(interval, cadence_minutes, slice_count)
    concentration_status, concentration_note = _hotspot_concentration_status(history)
    return [
        {"检查项": "数据源", "状态": source_status, "说明": source_note},
        {
            "检查项": "数据覆盖率",
            "状态": "Pass" if coverage_rate >= 0.80 and success_count >= 5 else "Review" if success_count >= 3 else "Block",
            "说明": f"成功 {success_count} 个，请求 {requested} 个，覆盖率 {coverage_rate:.2%}。横向热点建议至少 5 个对象。",
        },
        {
            "检查项": "失败率",
            "状态": "Pass" if failure_rate <= 0.10 else "Review" if failure_rate <= 0.25 else "Block",
            "说明": f"失败率 {failure_rate:.2%}。失败对象过多时，先修正代码、权限、时间粒度或网络。",
        },
        {
            "检查项": "样本长度",
            "状态": "Pass" if sample_min >= 60 else "Review" if sample_min >= 30 else "Block",
            "说明": f"最小样本点 {sample_min}。低于 60 时，热点热度、波动和回撤判断不够稳定。",
        },
        {
            "检查项": "时间切片",
            "状态": "Pass" if slice_count >= 12 else "Review" if slice_count >= 4 else "Block",
            "说明": f"可用时间切片 {slice_count} 个。切片过少时，无法判断热点扩散、降温或分化是否持续。",
        },
        {"检查项": "刷新粒度", "状态": cadence_status, "说明": cadence_note},
        {
            "检查项": "数据新鲜度",
            "状态": "Pass" if latest_snapshot else "Block",
            "说明": f"最新时间切片：{latest_snapshot or '缺失'}。若日期明显滞后，只能作为历史复盘观察。",
        },
        {"检查项": "热度集中度", "状态": concentration_status, "说明": concentration_note},
    ]


def _hotspot_current_slice(rows: pd.DataFrame, snapshot_time: str | None = None) -> pd.DataFrame:
    if rows.empty or "snapshot_time" not in rows.columns:
        return pd.DataFrame()
    selected = snapshot_time or str(rows["snapshot_time"].max())
    current = rows[rows["snapshot_time"].astype(str).eq(str(selected))]
    if current.empty:
        latest = str(rows["snapshot_time"].max())
        current = rows[rows["snapshot_time"].astype(str).eq(latest)]
    return current.copy()


def _instrument_cache_payload(item: SentimentInstrument) -> tuple[str, str, str, str]:
    return (str(item.symbol), str(item.name), str(item.market), str(item.role))


def _hotspot_requested_count(
    history: pd.DataFrame,
    errors: list[dict[str, str]],
    *,
    requested_count: int | None = None,
) -> int:
    if requested_count is not None:
        return max(0, int(requested_count))
    success_count = int(history["symbol"].nunique()) if not history.empty and "symbol" in history.columns else 0
    failed_symbols = {str(item.get("代码", "")).strip() for item in errors if str(item.get("代码", "")).strip()}
    return success_count + len(failed_symbols)


def _hotspot_first_snapshot(history: pd.DataFrame) -> str:
    if history.empty or "snapshot_time" not in history.columns:
        return ""
    return str(history["snapshot_time"].min())


def _hotspot_latest_snapshot(history: pd.DataFrame) -> str:
    if history.empty or "snapshot_time" not in history.columns:
        return ""
    return str(history["snapshot_time"].max())


def _hotspot_cadence_minutes(history: pd.DataFrame) -> float | None:
    if history.empty or "snapshot_time" not in history.columns:
        return None
    timestamps = pd.to_datetime(pd.Series(history["snapshot_time"].drop_duplicates()), errors="coerce").dropna().sort_values()
    if len(timestamps) < 2:
        return None
    deltas = timestamps.diff().dropna().dt.total_seconds() / 60.0
    if deltas.empty:
        return None
    return float(deltas.median())


def _hotspot_cadence_status(interval: str, cadence_minutes: float | None, slice_count: int) -> tuple[str, str]:
    if cadence_minutes is None:
        return ("Block" if slice_count <= 1 else "Review", "时间切片不足，暂不能验证刷新粒度。")
    normalized = interval.lower()
    if normalized == "60min":
        if cadence_minutes <= 90:
            return "Pass", f"典型切片间隔约 {cadence_minutes:.0f} 分钟，满足小时级观察。"
        if cadence_minutes <= 24 * 60:
            return "Review", f"典型切片间隔约 {cadence_minutes:.0f} 分钟，可能不是稳定小时级行情。"
        return "Block", f"典型切片间隔约 {cadence_minutes:.0f} 分钟，不满足小时级热点观察。"
    if normalized == "1d":
        return ("Pass" if cadence_minutes <= 3 * 24 * 60 else "Review", f"典型切片间隔约 {cadence_minutes:.0f} 分钟，用于日线热点观察。")
    return "Review", f"当前时间粒度 {interval} 的典型切片间隔约 {cadence_minutes:.0f} 分钟。"


def _hotspot_concentration_status(history: pd.DataFrame) -> tuple[str, str]:
    if history.empty or not {"snapshot_time", "hotspot_state", "symbol"}.issubset(history.columns):
        return "Block", "缺少热点状态或对象信息，不能判断热度集中度。"
    current = history[history["snapshot_time"].astype(str).eq(str(history["snapshot_time"].max()))].copy()
    if current.empty:
        return "Block", "缺少最新时间切片，不能判断热度集中度。"
    total = max(1, len(current))
    strong_ratio = float(current["hotspot_state"].isin(["强势扩散", "局部偏强"]).sum()) / total
    weak_ratio = float(current["hotspot_state"].isin(["局部偏弱", "风险降温"]).sum()) / total
    concentration = max(strong_ratio, weak_ratio)
    if concentration >= 0.85:
        status = "Block"
    elif concentration >= 0.70:
        status = "Review"
    else:
        status = "Pass"
    return status, f"偏强集中 {strong_ratio:.2%}，偏弱集中 {weak_ratio:.2%}。集中度高时需补资金流、新闻催化和基本面证据。"


def _hotspot_gate_status(rows: list[dict[str, str]]) -> str:
    statuses = {str(row.get("状态", "")) for row in rows}
    if "Block" in statuses:
        return "Block"
    if "Review" in statuses:
        return "Review"
    return "Pass" if rows else "Missing"


def _dataframe_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso", force_ascii=False))


def _normalized_hotspot_trace_rows(trace_rows: list[dict[str, object]] | tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in trace_rows:
        if not isinstance(row, dict):
            continue
        status = "Fail" if str(row.get("status", "")).lower() in {"fail", "failed", "error", "blocked"} else "Pass"
        rows.append(
            {
                "symbol": str(row.get("symbol", ""))[:32],
                "name": str(row.get("name", ""))[:80],
                "market": str(row.get("market", ""))[:16],
                "provider_symbol": str(row.get("provider_symbol", ""))[:48],
                "status": status,
                "elapsed_ms": round(_safe_float(row.get("elapsed_ms")), 2),
                "row_count": _safe_int(row.get("row_count")),
                "fallback": str(row.get("fallback", ""))[:48],
                "error": str(row.get("error", ""))[:180],
            }
        )
    return rows


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: object) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _utc_now(value: pd.Timestamp | None = None) -> pd.Timestamp:
    if value is None:
        return pd.Timestamp.now(tz="UTC")
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _hotspot_row(
    data: pd.DataFrame,
    instrument: SentimentInstrument,
    data_source: str,
    snapshot_time: pd.Timestamp | None = None,
) -> dict[str, object]:
    close = pd.to_numeric(data["close"], errors="coerce").dropna()
    returns = close.pct_change().dropna()
    latest_close = float(close.iloc[-1])
    one_step_return = _period_return(close, 1)
    five_step_return = _period_return(close, 5)
    twenty_step_return = _period_return(close, 20)
    rsi14 = _rsi(close, 14)
    volatility20 = float(returns.tail(20).std(ddof=0) * np.sqrt(252)) if len(returns) >= 2 else 0.0
    drawdown20 = _max_drawdown(close.tail(20))
    instant_heat_score = _hotspot_heat_score(
        one_step_return=one_step_return,
        five_step_return=five_step_return,
        twenty_step_return=twenty_step_return,
        rsi14=rsi14,
        volatility20=volatility20,
        drawdown20=drawdown20,
        is_volatility_symbol=_is_volatility_symbol(instrument.symbol, instrument.name),
    )
    state = hotspot_state(instant_heat_score)
    bar_time = pd.Timestamp(data["datetime"].iloc[-1]).isoformat()
    snapshot_label = (pd.Timestamp(snapshot_time) if snapshot_time is not None else pd.Timestamp(data["datetime"].iloc[-1])).isoformat()
    bubble_size = float(round(max(8.0, min(44.0, 9.0 + abs(five_step_return) * 260.0 + volatility20 * 18.0)), 2))
    return {
        "snapshot_time": snapshot_label,
        "bar_time": bar_time,
        "symbol": instrument.symbol,
        "name": instrument.name,
        "market": instrument.market,
        "sector": instrument.role,
        "close": latest_close,
        "one_step_return": one_step_return,
        "five_step_return": five_step_return,
        "twenty_step_return": twenty_step_return,
        "rsi14": rsi14,
        "volatility20": volatility20,
        "drawdown20": drawdown20,
        "instant_heat_score": instant_heat_score,
        "heat_score": instant_heat_score,
        "heat_score_delta": 0.0,
        "hotspot_state": state,
        "bubble_size": bubble_size,
        "evidence_note": _hotspot_evidence_note(instrument.role, five_step_return, rsi14, volatility20, drawdown20),
        "data_source": data_source,
        "data_points": int(len(data)),
    }


def _calculation_snapshot_series(all_snapshot_series: pd.Series, display_snapshot_series: pd.Series) -> pd.Series:
    if all_snapshot_series.empty or display_snapshot_series.empty:
        return display_snapshot_series
    first_display = pd.Timestamp(display_snapshot_series.iloc[0])
    last_display = pd.Timestamp(display_snapshot_series.iloc[-1])
    start_position = int(all_snapshot_series.searchsorted(first_display, side="left"))
    end_position = int(all_snapshot_series.searchsorted(last_display, side="right"))
    lower_position = max(0, start_position - HOTSPOT_STABLE_HEAT_WARMUP_SNAPSHOTS)
    return all_snapshot_series.iloc[lower_position:end_position].reset_index(drop=True)


def _stabilize_hotspot_heat(history: pd.DataFrame) -> pd.DataFrame:
    if history.empty or "symbol" not in history.columns or "instant_heat_score" not in history.columns:
        return history
    stabilized = history.copy()
    stabilized["_snapshot_sort"] = pd.to_datetime(stabilized["snapshot_time"], errors="coerce")
    stabilized = stabilized.sort_values(["symbol", "_snapshot_sort", "snapshot_time"], kind="mergesort")
    stabilized["instant_heat_score"] = pd.to_numeric(stabilized["instant_heat_score"], errors="coerce").fillna(50.0)
    stabilized["heat_score"] = (
        stabilized.groupby("symbol", group_keys=False)["instant_heat_score"]
        .transform(_stable_heat_from_recent_context)
        .round(2)
    )
    stabilized["heat_score_delta"] = (
        stabilized.groupby("symbol", group_keys=False)["heat_score"]
        .diff()
        .fillna(0.0)
        .round(2)
    )
    stabilized["hotspot_state"] = stabilized["heat_score"].map(lambda value: hotspot_state(float(value)))
    return stabilized.drop(columns=["_snapshot_sort"])


def hotspot_state(score: float) -> str:
    if score >= 72:
        return "强势扩散"
    if score >= 58:
        return "局部偏强"
    if score >= 43:
        return "中性轮动"
    if score >= 28:
        return "局部偏弱"
    return "风险降温"


def _hotspot_heat_score(
    one_step_return: float,
    five_step_return: float,
    twenty_step_return: float,
    rsi14: float,
    volatility20: float,
    drawdown20: float,
    is_volatility_symbol: bool,
) -> float:
    if is_volatility_symbol:
        raw = 50.0 - _clip(one_step_return * 100, -8, 8) * 2.4 - _clip(five_step_return * 100, -15, 15) * 1.4
        raw += _clip(55.0 - rsi14, -25, 25) * 0.25
        return float(round(_clip(raw, 0, 100), 2))
    raw = 50.0
    raw += _clip(one_step_return * 100, -8, 8) * 2.1
    raw += _clip(five_step_return * 100, -15, 15) * 1.35
    raw += _clip(twenty_step_return * 100, -25, 25) * 0.45
    raw += _clip(rsi14 - 50.0, -35, 35) * 0.24
    raw -= _clip((volatility20 - 0.35) * 100, 0, 60) * 0.12
    raw += _clip(drawdown20 * 100, -25, 0) * 0.25
    return float(round(_clip(raw, 0, 100), 2))


def _hotspot_evidence_note(sector: str, five_step_return: float, rsi14: float, volatility20: float, drawdown20: float) -> str:
    return (
        f"{sector}：近5期涨跌 {five_step_return:.2%}，RSI {rsi14:.2f}，"
        f"20期波动 {volatility20:.2%}，20期回撤 {drawdown20:.2%}。"
    )


def _clean_hotspot_bars(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty or "close" not in raw.columns or "datetime" not in raw.columns:
        return pd.DataFrame()
    data = raw.copy()
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["datetime", "close"]).sort_values("datetime")
    return data.reset_index(drop=True)


def _display_boundary_timestamp(value: str | pd.Timestamp | None, end_of_day: bool = False) -> pd.Timestamp:
    if value is None:
        return pd.NaT
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return pd.NaT
    if end_of_day and _looks_like_date_only(value):
        return pd.Timestamp(timestamp) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return pd.Timestamp(timestamp)


def _looks_like_date_only(value: object) -> bool:
    text = str(value).strip()
    return len(text) == 10 and text[4] == "-" and text[7] == "-"


def _stable_heat_from_recent_context(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(50.0)
    values = numeric.to_numpy(dtype=float)
    alpha = 2.0 / (HOTSPOT_STABLE_HEAT_SPAN + 1.0)
    stable_values: list[float] = []
    for index in range(len(values)):
        start = max(0, index - HOTSPOT_STABLE_HEAT_WARMUP_SNAPSHOTS)
        smoothed = 50.0
        capped = 50.0
        for raw_value in values[start : index + 1]:
            smoothed = alpha * float(raw_value) + (1.0 - alpha) * smoothed
            capped += _clip(smoothed - capped, -HOTSPOT_MAX_STABLE_HEAT_STEP, HOTSPOT_MAX_STABLE_HEAT_STEP)
        stable_values.append(capped)
    return pd.Series(stable_values, index=series.index)


def _period_return(close: pd.Series, periods: int) -> float:
    if len(close) <= periods:
        return 0.0
    base = float(close.iloc[-periods - 1])
    if abs(base) < 1e-12:
        return 0.0
    return float(close.iloc[-1] / base - 1.0)


def _rsi(close: pd.Series, window: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    value = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50.0
    return float(round(value, 2))


def _max_drawdown(close: pd.Series) -> float:
    if close.empty:
        return 0.0
    peak = close.cummax()
    drawdown = close / peak - 1
    return float(drawdown.min())


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _is_volatility_symbol(symbol: str, name: str) -> bool:
    text = f"{symbol} {name}".lower()
    return "vix" in text or "波动" in text or "volatility" in text
