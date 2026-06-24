from __future__ import annotations

import json
from csv import DictWriter
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import PricePoint, load_price_history
from app.config import Settings
from app.core.metrics import WINDOWS, calculate_returns
from app.core.moomoo_lifecycle import cleanup_started_processes, ensure_opend, lifecycle_to_dict
from app.core.moomoo_smoke import probe_sdk


@dataclass(frozen=True)
class BenchmarkSourceCandidate:
    benchmark: str
    canonical_code: str
    symbol: str
    source_type: str
    source_role: str
    note: str


BENCHMARK_CANDIDATES = (
    BenchmarkSourceCandidate(
        "Shanghai Composite",
        "000001.SH",
        "SH.000001",
        "moomoo",
        "exact_index",
        "MooMoo Shanghai Composite index symbol; requires CN market index quote permission.",
    ),
    BenchmarkSourceCandidate(
        "S&P 500",
        "SPX",
        "US..SPX",
        "moomoo",
        "exact_index",
        "MooMoo may reject US stock index history; exact S&P 500 still must be verified.",
    ),
    BenchmarkSourceCandidate(
        "S&P 500",
        "SPX",
        "US.SPX",
        "moomoo",
        "exact_index",
        "Alternate exact-index probe; current local smoke may return unknown stock.",
    ),
    BenchmarkSourceCandidate(
        "S&P 500",
        "SPX",
        "US.SPY",
        "moomoo",
        "proxy_etf",
        "SPDR S&P 500 ETF proxy; usable for warning-level fallback only, not production exact-index proof.",
    ),
    BenchmarkSourceCandidate(
        "S&P 500",
        "SPX",
        "US.VOO",
        "moomoo",
        "proxy_etf",
        "Vanguard S&P 500 ETF proxy; usable for warning-level fallback only, not production exact-index proof.",
    ),
)

YAHOO_CANDIDATES = (
    BenchmarkSourceCandidate(
        "Shanghai Composite",
        "000001.SH",
        "000001.SS",
        "public_aggregation",
        "exact_index_fallback",
        "Yahoo Finance exact Shanghai Composite chart fallback.",
    ),
    BenchmarkSourceCandidate(
        "S&P 500",
        "SPX",
        "^GSPC",
        "public_aggregation",
        "exact_index_fallback",
        "Yahoo Finance exact S&P 500 chart fallback.",
    ),
)

THEMATIC_YAHOO_CANDIDATES = (
    BenchmarkSourceCandidate(
        "Nasdaq 100",
        "NDX",
        "^NDX",
        "public_aggregation",
        "thematic_index",
        "Yahoo Finance exact Nasdaq 100 chart; used for US Nasdaq/QDII growth funds.",
    ),
    BenchmarkSourceCandidate(
        "Hang Seng TECH ETF proxy",
        "HSTECH_PROXY",
        "3033.HK",
        "public_aggregation",
        "thematic_proxy",
        "Yahoo Finance CSOP Hang Seng TECH ETF chart; used when exact HSTECH index history is unavailable.",
    ),
)

EASTMONEY_CANDIDATES = (
    BenchmarkSourceCandidate(
        "ChiNext Index",
        "399006.SZ",
        "0.399006",
        "public_aggregation",
        "thematic_index",
        "Eastmoney exact ChiNext Index daily kline.",
    ),
    BenchmarkSourceCandidate(
        "CNI Chip Index",
        "CNI_CHIP",
        "0.980017",
        "public_aggregation",
        "thematic_index",
        "Eastmoney CNI Chip Index daily kline; used for CNI semiconductor chip exposure.",
    ),
    BenchmarkSourceCandidate(
        "CSI All Share Semiconductor Index",
        "H30184.CSI",
        "2.H30184",
        "public_aggregation",
        "thematic_index",
        "Eastmoney CSI All Share Semiconductors & Semiconductor Production Equipment daily kline.",
    ),
    BenchmarkSourceCandidate(
        "CSI Semiconductor Index",
        "931865.CSI",
        "2.931865",
        "public_aggregation",
        "thematic_index",
        "Eastmoney CSI Semiconductor Industry daily kline.",
    ),
    BenchmarkSourceCandidate(
        "CSI Artificial Intelligence Index",
        "930713.CSI",
        "2.930713",
        "public_aggregation",
        "thematic_index",
        "Eastmoney CSI Artificial Intelligence daily kline.",
    ),
)

MIN_REQUIRED_SPAN_DAYS = 365
MIN_REQUIRED_TRADING_ROWS = 11
DEFAULT_LOOKBACK_DAYS = 396


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def default_benchmark_window(settings: Settings, *, today: date | None = None) -> tuple[str, str]:
    current = today or datetime.now(ZoneInfo(settings.timezone_primary)).date()
    end_day = current
    while end_day.weekday() >= 5:
        end_day -= timedelta(days=1)
    start_day = end_day - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    return start_day.isoformat(), end_day.isoformat()


def _resolve_window(settings: Settings, start: str | None, end: str | None) -> tuple[str, str, str]:
    default_start, default_end = default_benchmark_window(settings)
    resolved_end = end or default_end
    resolved_start = start or (datetime.fromisoformat(resolved_end).date() - timedelta(days=DEFAULT_LOOKBACK_DAYS)).isoformat()
    source = "explicit" if start and end else ("mixed" if start or end else "dynamic_latest_weekday")
    return resolved_start, resolved_end, source


def _probe_moomoo_candidates(
    candidates: tuple[BenchmarkSourceCandidate, ...],
    *,
    start: str,
    end: str,
    host: str,
    port: int,
) -> list[dict[str, object]]:
    import moomoo as ft

    rows: list[dict[str, object]] = []
    quote_ctx = ft.OpenQuoteContext(host=host, port=port)
    try:
        for candidate in candidates:
            frames: list[Any] = []
            ret, data, page_req_key = quote_ctx.request_history_kline(
                candidate.symbol,
                start=start,
                end=end,
                ktype=ft.KLType.K_DAY,
            )
            if ret == ft.RET_OK:
                frames.append(data)
                while page_req_key:
                    ret, data, page_req_key = quote_ctx.request_history_kline(
                        candidate.symbol,
                        start=start,
                        end=end,
                        ktype=ft.KLType.K_DAY,
                        page_req_key=page_req_key,
                    )
                    if ret != ft.RET_OK:
                        break
                    frames.append(data)
            ok = ret == ft.RET_OK and bool(frames) and sum(len(frame) for frame in frames) > 0
            history: list[dict[str, object]] = []
            if ok:
                all_data = frames[0] if len(frames) == 1 else __import__("pandas").concat(frames, ignore_index=True)
                for raw_row in all_data.to_dict("records"):
                    date_value = str(raw_row.get("time_key") or raw_row.get("time") or "")[:10]
                    close_value = raw_row.get("close")
                    if not date_value or close_value in (None, ""):
                        continue
                    history.append(
                        {
                            "asset_code": candidate.canonical_code,
                            "date": date_value,
                            "close": float(close_value),
                            "source_name": "MooMoo OpenD history kline",
                            "source_type": "moomoo",
                            "source_priority": 1,
                            "url_or_path": candidate.symbol,
                            "evidence_level": "High",
                            "as_of": end,
                        }
                    )
            sufficient = _history_supports_required_windows(history)
            row = asdict(candidate)
            row.update(
                {
                    "status": "pass" if ok else "fail",
                    "rows": len(history),
                    "latest_close": history[-1]["close"] if history else None,
                    "message": "ok" if ok else str(data),
                    "production_eligible": ok and candidate.source_role == "exact_index" and sufficient,
                    "sufficient_for_required_windows": sufficient,
                    "source_priority": 1,
                    "history": history,
                }
            )
            rows.append(row)
    finally:
        quote_ctx.close()
    return rows


def _period_seconds(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


def _history_supports_required_windows(history: list[dict[str, object]]) -> bool:
    if len(history) < MIN_REQUIRED_TRADING_ROWS:
        return False
    points = sorted(
        (
            PricePoint(
                str(row.get("asset_code") or ""),
                datetime.fromisoformat(str(row["date"])).date(),
                float(row["close"]),
            )
            for row in history
            if row.get("date") and row.get("close") not in (None, "")
        ),
        key=lambda point: point.date,
    )
    if len(points) < MIN_REQUIRED_TRADING_ROWS:
        return False
    if (points[-1].date - points[0].date).days < MIN_REQUIRED_SPAN_DAYS:
        return False
    returns = calculate_returns(points)
    return all(returns.get(window) is not None for window in WINDOWS)


def _select_benchmark_history(
    *,
    benchmark_names: set[str],
    moomoo_rows: list[dict[str, object]],
    yahoo_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for benchmark in sorted(benchmark_names):
        chosen = next(
            (
                row
                for row in moomoo_rows
                if row.get("benchmark") == benchmark
                and row.get("source_role") == "exact_index"
                and row.get("production_eligible")
            ),
            None,
        )
        if chosen is None:
            chosen = next(
                (
                    row
                    for row in yahoo_rows
                    if row.get("benchmark") == benchmark
                    and row.get("source_role") == "exact_index_fallback"
                    and row.get("production_eligible")
                ),
                None,
            )
        if chosen:
            selected.extend(chosen.get("history", []))
    return selected


def _probe_yahoo_candidates(
    candidates: tuple[BenchmarkSourceCandidate, ...],
    *,
    start: str,
    end: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    period1 = _period_seconds(start)
    period2 = _period_seconds(end) + 86400
    for candidate in candidates:
        encoded = quote(candidate.symbol, safe="")
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
            f"?period1={period1}&period2={period2}&interval=1d&events=history"
        )
        row = asdict(candidate)
        row.update(
            {
                "status": "fail",
                "rows": 0,
                "latest_close": None,
                "message": "",
                "production_eligible": False,
                "source_priority": 5,
                "url": url,
                "history": [],
            }
        )
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
            chart = payload.get("chart", {})
            if chart.get("error"):
                row["message"] = str(chart["error"])
                rows.append(row)
                continue
            result = (chart.get("result") or [None])[0]
            if not result:
                row["message"] = "empty chart result"
                rows.append(row)
                continue
            timestamps = result.get("timestamp") or []
            closes = (((result.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
            history = []
            for stamp, close in zip(timestamps, closes):
                if close is None:
                    continue
                history.append(
                    {
                        "asset_code": candidate.canonical_code,
                        "date": datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat(),
                        "close": float(close),
                        "source_name": "Yahoo Finance chart",
                        "source_type": "public_aggregation",
                        "source_priority": 5,
                        "url_or_path": url,
                        "evidence_level": "Medium",
                        "as_of": end,
                    }
                )
            row["history"] = history
            row["rows"] = len(history)
            row["latest_close"] = history[-1]["close"] if history else None
            row["status"] = "pass" if history else "fail"
            row["message"] = "ok" if history else "no close rows"
            row["sufficient_for_required_windows"] = _history_supports_required_windows(history)
            row["production_eligible"] = bool(history) and bool(row["sufficient_for_required_windows"])
        except Exception as exc:
            row["message"] = f"{exc.__class__.__name__}: {exc}"
        rows.append(row)
    return rows


def _probe_eastmoney_candidates(
    candidates: tuple[BenchmarkSourceCandidate, ...],
    *,
    start: str,
    end: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        query = (
            "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            f"?secid={quote(candidate.symbol, safe='.')}"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b"
            "&fields1=f1,f2,f3,f4,f5,f6"
            "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
            f"&klt=101&fqt=1&beg={start.replace('-', '')}&end={end.replace('-', '')}&lmt=1000000"
        )
        row = asdict(candidate)
        row.update(
            {
                "status": "fail",
                "rows": 0,
                "latest_close": None,
                "message": "",
                "production_eligible": False,
                "source_priority": 5,
                "url": query,
                "history": [],
            }
        )
        try:
            request = Request(query, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
            data = payload.get("data") or {}
            klines = data.get("klines") or []
            history = []
            source_name = f"Eastmoney index kline: {data.get('name') or candidate.benchmark}"
            for item in klines:
                parts = str(item).split(",")
                if len(parts) < 3:
                    continue
                day, close = parts[0], parts[2]
                if not day or close in {"", "-"}:
                    continue
                history.append(
                    {
                        "asset_code": candidate.canonical_code,
                        "date": day,
                        "close": float(close),
                        "source_name": source_name,
                        "source_type": candidate.source_type,
                        "source_priority": 5,
                        "url_or_path": query,
                        "evidence_level": "Medium",
                        "as_of": end,
                    }
                )
            row["history"] = history
            row["rows"] = len(history)
            row["latest_close"] = history[-1]["close"] if history else None
            row["status"] = "pass" if history else "fail"
            row["message"] = "ok" if history else "no close rows"
            row["sufficient_for_required_windows"] = _history_supports_required_windows(history)
            row["production_eligible"] = bool(history) and bool(row["sufficient_for_required_windows"])
        except Exception as exc:
            row["message"] = f"{exc.__class__.__name__}: {exc}"
        rows.append(row)
    return rows


def _dedupe_history_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        key = (str(row.get("asset_code") or ""), str(row.get("date") or ""))
        if key[0] and key[1]:
            deduped[key] = row
    return [deduped[key] for key in sorted(deduped)]


def _manual_history_status(settings: Settings) -> list[dict[str, object]]:
    path = settings.manual_dir / "benchmark_price_history.csv"
    if not path.exists():
        path = settings.manual_dir / "price_history.csv"
    if not path.exists():
        return []
    history = load_price_history(path)
    rows: list[dict[str, object]] = []
    for benchmark, canonical_code in [("Shanghai Composite", "000001.SH"), ("S&P 500", "SPX")]:
        points = history.get(canonical_code, [])
        sample_like = bool(points and points[0].close == 100.0 and str(path).endswith("data/manual/price_history.csv"))
        rows.append(
            {
                "benchmark": benchmark,
                "canonical_code": canonical_code,
                "symbol": canonical_code,
                "source_type": "manual_local",
                "source_role": "manual_fallback",
                "status": "warn" if points else "fail",
                "rows": len(points),
                "latest_close": points[-1].close if points else None,
                "message": "local manual history present" if points else "local manual history missing",
                "sample_like": sample_like,
                "production_eligible": False,
                "path": str(path),
            }
        )
    return rows


def run_benchmark_smoke(
    settings: Settings,
    *,
    start: str | None = None,
    end: str | None = None,
    host: str = "127.0.0.1",
    port: int = 11111,
    auto_start_opend: bool = True,
    cleanup_auto_started: bool = True,
    opend_wait_seconds: float = 20.0,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    start, end, window_source = _resolve_window(settings, start, end)
    lifecycle = ensure_opend(
        settings,
        host=host,
        port=port,
        auto_start=auto_start_opend,
        cleanup_if_started=cleanup_auto_started,
        wait_seconds=opend_wait_seconds,
    )
    sdk = probe_sdk()
    moomoo_rows: list[dict[str, object]] = []
    yahoo_rows: list[dict[str, object]] = []
    thematic_yahoo_rows: list[dict[str, object]] = []
    eastmoney_rows: list[dict[str, object]] = []
    errors: list[str] = []
    cleanup = None
    if lifecycle.socket_is_reachable and sdk.import_available:
        moomoo_rows = _probe_moomoo_candidates(BENCHMARK_CANDIDATES, start=start, end=end, host=host, port=port)
    else:
        errors.append(lifecycle.detail if not lifecycle.socket_is_reachable else sdk.detail)
    if cleanup_auto_started and lifecycle.started_by_tool and lifecycle.socket_is_reachable:
        cleanup = cleanup_started_processes(lifecycle)

    yahoo_rows = _probe_yahoo_candidates(YAHOO_CANDIDATES, start=start, end=end)
    thematic_yahoo_rows = _probe_yahoo_candidates(THEMATIC_YAHOO_CANDIDATES, start=start, end=end)
    eastmoney_rows = _probe_eastmoney_candidates(EASTMONEY_CANDIDATES, start=start, end=end)
    manual_rows = _manual_history_status(settings)
    benchmark_names = {candidate.benchmark for candidate in BENCHMARK_CANDIDATES}
    production_ready_by_benchmark = {
        benchmark: any(
            row["benchmark"] == benchmark and row.get("production_eligible")
            for row in moomoo_rows + yahoo_rows
        )
        for benchmark in benchmark_names
    }
    production_ready = all(production_ready_by_benchmark.values())
    proxy_available = {
        benchmark: any(row["benchmark"] == benchmark and row["status"] == "pass" and row["source_role"] == "proxy_etf" for row in moomoo_rows)
        for benchmark in benchmark_names
    }
    result: dict[str, object] = {
        "generated_at": _now(settings),
        "window": {"start": start, "end": end, "source": window_source, "lookback_days": DEFAULT_LOOKBACK_DAYS},
        "status": "pass" if production_ready else "blocked",
        "production_ready": production_ready,
        "production_ready_by_benchmark": production_ready_by_benchmark,
        "proxy_available": proxy_available,
        "moomoo_candidates": moomoo_rows,
        "public_aggregation_candidates": yahoo_rows,
        "thematic_benchmark_candidates": thematic_yahoo_rows + eastmoney_rows,
        "manual_history": manual_rows,
        "errors": errors,
        "opend_lifecycle": lifecycle_to_dict(lifecycle),
        "cleanup": cleanup,
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "preflight"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "benchmark_smoke_latest.json"
        md_path = output_dir / "benchmark_smoke_latest.md"
        csv_path = settings.manual_dir / "benchmark_price_history.csv"
        history_rows = _select_benchmark_history(
            benchmark_names=benchmark_names,
            moomoo_rows=moomoo_rows,
            yahoo_rows=yahoo_rows,
        )
        history_rows.extend(
            history
            for row in thematic_yahoo_rows + eastmoney_rows
            if row.get("production_eligible")
            for history in row.get("history", [])
        )
        history_rows = _dedupe_history_rows(history_rows)
        if history_rows:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = DictWriter(
                    handle,
                    fieldnames=[
                        "asset_code",
                        "date",
                        "close",
                        "source_name",
                        "source_type",
                        "source_priority",
                        "url_or_path",
                        "evidence_level",
                        "as_of",
                    ],
                )
                writer.writeheader()
                writer.writerows(history_rows)
            result["benchmark_history_path"] = str(csv_path)
            manual_rows = _manual_history_status(settings)
            result["manual_history"] = manual_rows
        else:
            result["benchmark_history_path"] = None
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# Benchmark Source Smoke",
            "",
            f"- Generated at: {result['generated_at']}",
            f"- Window: {start} to {end} ({window_source})",
            f"- Production ready: {production_ready}",
            "",
            "## MooMoo Candidates",
            "",
        ]
        for row in moomoo_rows:
            lines.append(
                f"- {row['benchmark']} `{row['symbol']}` ({row['source_role']}): "
                f"{row['status']} - {row['message']}"
            )
        if not moomoo_rows:
            lines.append("- None")
        lines.extend(["", "## Public Aggregation Exact Fallback", ""])
        for row in yahoo_rows:
            lines.append(
                f"- {row['benchmark']} `{row['symbol']}` ({row['source_role']}): "
                f"{row['status']} rows={row['rows']} - {row['message']}"
            )
        if not yahoo_rows:
            lines.append("- None")
        lines.extend(["", "## Thematic Benchmark Sources", ""])
        for row in thematic_yahoo_rows + eastmoney_rows:
            lines.append(
                f"- {row['benchmark']} `{row['canonical_code']}` via `{row['symbol']}` ({row['source_role']}): "
                f"{row['status']} rows={row['rows']} - {row['message']}"
            )
        if not thematic_yahoo_rows and not eastmoney_rows:
            lines.append("- None")
        lines.extend(["", "## Manual Local History", ""])
        for row in manual_rows:
            lines.append(
                f"- {row['benchmark']} `{row['canonical_code']}`: {row['status']}, "
                f"rows={row['rows']}, sample_like={row['sample_like']}"
            )
        lines.extend(["", "## Production Gate", ""])
        for benchmark, ready in production_ready_by_benchmark.items():
            lines.append(f"- {benchmark}: {'ready' if ready else 'blocked'}")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result["json_path"] = str(json_path)
        result["markdown_path"] = str(md_path)
    return result
