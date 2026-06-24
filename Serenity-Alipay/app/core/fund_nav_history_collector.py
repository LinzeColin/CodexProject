from __future__ import annotations

import csv
import json
import math
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import Candidate, load_candidates
from app.config import Settings


SOURCE_NAME = "Eastmoney/Tiantian Fund historical NAV API"
SOURCE_TYPE = "public_aggregation"
SOURCE_PRIORITY = 5
EVIDENCE_LEVEL = "Medium"
PAGE_SIZE = 20


@dataclass(frozen=True)
class NavHistoryRow:
    asset_code: str
    date: str
    close: float
    source_name: str
    source_type: str
    source_priority: int
    url_or_path: str
    evidence_level: str
    as_of: str


@dataclass(frozen=True)
class NavHistorySummary:
    asset_code: str
    asset_name: str
    rows: int
    start_date: str
    end_date: str
    span_days: int
    status: str
    message: str
    source_url: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _today(settings: Settings) -> datetime:
    return datetime.now(ZoneInfo(settings.timezone_primary))


def _history_url(asset_code: str, start_date: str, end_date: str, *, page_index: int = 1) -> str:
    query = urlencode(
        {
            "fundCode": asset_code,
            "pageIndex": page_index,
            "pageSize": PAGE_SIZE,
            "startDate": start_date,
            "endDate": end_date,
        }
    )
    return f"https://api.fund.eastmoney.com/f10/lsjz?{query}"


def _fetch_eastmoney_nav_page(asset_code: str, start_date: str, end_date: str, timeout_seconds: float, page_index: int) -> tuple[list[dict[str, str]], int]:
    url = _history_url(asset_code, start_date, end_date, page_index=page_index)
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 SerenityDailyAnalysis/0.1",
            "Referer": "https://fundf10.eastmoney.com/",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed public NAV endpoint
        payload = json.loads(response.read().decode("utf-8"))
    if int(payload.get("ErrCode") or 0) != 0:
        raise ValueError(f"Eastmoney API error for {asset_code}: {payload.get('ErrMsg')}")
    total_count = int(payload.get("TotalCount") or 0)
    rows = list((payload.get("Data") or {}).get("LSJZList") or [])
    return rows, total_count


def _fetch_eastmoney_nav(
    asset_code: str,
    start_date: str,
    end_date: str,
    timeout_seconds: float,
    *,
    workers: int = 8,
) -> tuple[list[dict[str, str]], str]:
    first_rows, total_count = _fetch_eastmoney_nav_page(asset_code, start_date, end_date, timeout_seconds, 1)
    first_url = _history_url(asset_code, start_date, end_date, page_index=1)
    if total_count <= len(first_rows) or not first_rows:
        return first_rows, first_url
    page_count = max(1, math.ceil(total_count / PAGE_SIZE))
    rows = list(first_rows)
    max_workers = max(1, min(workers, page_count - 1))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_eastmoney_nav_page, asset_code, start_date, end_date, timeout_seconds, page_index): page_index
            for page_index in range(2, page_count + 1)
        }
        for future in as_completed(futures):
            page_rows, _ = future.result()
            rows.extend(page_rows)
    return rows, first_url


def _candidate_scope(settings: Settings, asset_codes: list[str] | None = None) -> list[Candidate]:
    candidates = load_candidates(settings.manual_dir / "candidates.csv")
    requested = set(asset_codes or [])
    scoped: list[Candidate] = []
    for candidate in candidates:
        if requested and candidate.asset_code not in requested:
            continue
        if not requested and candidate.is_excluded:
            continue
        if not candidate.asset_code.isdigit():
            continue
        scoped.append(candidate)
    return scoped


def _summary_for(candidate: Candidate, rows: list[NavHistoryRow], min_span_days: int, source_url: str, message: str = "") -> NavHistorySummary:
    if not rows:
        return NavHistorySummary(
            candidate.asset_code,
            candidate.asset_name,
            0,
            "",
            "",
            0,
            "block",
            message or "no NAV rows fetched",
            source_url,
        )
    start_date = rows[0].date
    end_date = rows[-1].date
    span_days = (datetime.fromisoformat(end_date).date() - datetime.fromisoformat(start_date).date()).days
    status = "pass" if span_days >= min_span_days else "block"
    return NavHistorySummary(
        candidate.asset_code,
        candidate.asset_name,
        len(rows),
        start_date,
        end_date,
        span_days,
        status,
        message or ("24-month NAV history ready" if status == "pass" else "NAV history span is below 24-month requirement"),
        source_url,
    )


def _write_history(path: Path, rows: list[NavHistoryRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(NavHistoryRow.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_summary_csv(path: Path, summaries: list[NavHistorySummary]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(NavHistorySummary.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in summaries:
            writer.writerow(asdict(row))


def _write_markdown(path: Path, result: dict[str, object], summaries: list[NavHistorySummary]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 候选基金 24 个月净值历史采集",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 状态：{result['status']}",
        f"- 覆盖基金：{result['candidate_count']}",
        f"- 最小跨度要求：{result['min_span_days']} 天（24个月硬规则）",
        f"- 数据源：{SOURCE_NAME}，source_type={SOURCE_TYPE}，source_priority={SOURCE_PRIORITY}",
        "",
        "| 基金 | 行数 | 起始 | 最新 | 跨度天数 | 状态 |",
        "|---|---:|---|---|---:|---|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.asset_code} {summary.asset_name} | {summary.rows} | {summary.start_date or '-'} | "
            f"{summary.end_date or '-'} | {summary.span_days} | {summary.status} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_fund_nav_history(
    settings: Settings,
    *,
    asset_codes: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    timeout_seconds: float = 12.0,
    workers: int = 8,
    write_output: bool = True,
    apply: bool = False,
) -> dict[str, object]:
    settings.ensure_dirs()
    generated_at = _now(settings)
    today = _today(settings).date()
    resolved_end = end_date or today.isoformat()
    resolved_start = start_date or (datetime.fromisoformat(resolved_end).date() - timedelta(days=settings.min_candidate_nav_history_span_days + 45)).isoformat()
    candidates = _candidate_scope(settings, asset_codes=asset_codes)

    all_rows: list[NavHistoryRow] = []
    summaries: list[NavHistorySummary] = []
    for candidate in candidates:
        try:
            raw_rows, source_url = _fetch_eastmoney_nav(
                candidate.asset_code,
                resolved_start,
                resolved_end,
                timeout_seconds,
                workers=workers,
            )
            by_date: dict[str, NavHistoryRow] = {}
            for raw in raw_rows:
                nav_date = str(raw.get("FSRQ") or "").strip()
                close_raw = str(raw.get("DWJZ") or raw.get("LJJZ") or "").strip()
                if not nav_date or not close_raw:
                    continue
                by_date[nav_date] = NavHistoryRow(
                    asset_code=candidate.asset_code,
                    date=nav_date,
                    close=float(close_raw),
                    source_name=SOURCE_NAME,
                    source_type=SOURCE_TYPE,
                    source_priority=SOURCE_PRIORITY,
                    url_or_path=source_url,
                    evidence_level=EVIDENCE_LEVEL,
                    as_of=resolved_end,
                )
            rows = [by_date[key] for key in sorted(by_date)]
            all_rows.extend(rows)
            summaries.append(_summary_for(candidate, rows, settings.min_candidate_nav_history_span_days, source_url))
        except Exception as exc:
            source_url = _history_url(candidate.asset_code, resolved_start, resolved_end)
            summaries.append(_summary_for(candidate, [], settings.min_candidate_nav_history_span_days, source_url, str(exc)))

    output_dir = settings.root_dir / "outputs" / "preflight"
    files = {
        "markdown": str(output_dir / "fund_nav_history_latest.md"),
        "csv": str(output_dir / "fund_nav_history_latest.csv"),
        "json": str(output_dir / "fund_nav_history_latest.json"),
        "price_history_candidate": str(output_dir / "price_history_candidate.csv"),
    }
    block_count = sum(1 for summary in summaries if summary.status != "pass")
    backup_path = None
    target_path = settings.manual_dir / "price_history.csv"
    if write_output:
        _write_history(Path(files["price_history_candidate"]), all_rows)
        _write_summary_csv(Path(files["csv"]), summaries)
        result_stub = {
            "generated_at": generated_at,
            "status": "pass" if block_count == 0 else "blocked",
            "candidate_count": len(candidates),
            "min_span_days": settings.min_candidate_nav_history_span_days,
        }
        _write_markdown(Path(files["markdown"]), result_stub, summaries)
    applied = bool(apply and block_count == 0)
    if applied:
        backup_dir = settings.data_dir / "backups" / "nav_history"
        backup_dir.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            backup_path = backup_dir / f"price_history_{generated_at.replace(':', '').replace('-', '').replace('+', '_')}.csv"
            shutil.copy2(target_path, backup_path)
        _write_history(target_path, all_rows)

    result: dict[str, object] = {
        "generated_at": generated_at,
        "status": "pass" if block_count == 0 else "blocked",
        "candidate_count": len(candidates),
        "row_count": len(all_rows),
        "block_count": block_count,
        "start_date": resolved_start,
        "end_date": resolved_end,
        "min_history_months": settings.min_candidate_nav_history_months,
        "min_span_days": settings.min_candidate_nav_history_span_days,
        "workers": workers,
        "applied": applied,
        "apply_requested": apply,
        "target_path": str(target_path),
        "backup_path": str(backup_path) if backup_path else None,
        "source_name": SOURCE_NAME,
        "source_type": SOURCE_TYPE,
        "source_priority": SOURCE_PRIORITY,
        "files": files,
        "summaries": [asdict(summary) for summary in summaries],
    }
    if write_output:
        Path(files["json"]).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
