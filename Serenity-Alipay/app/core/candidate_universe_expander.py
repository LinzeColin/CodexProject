from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.fund_nav_history_collector import _fetch_eastmoney_nav, _history_url


EASTMONEY_FUND_LIST_URL = "https://fund.eastmoney.com/js/fundcode_search.js"
SOURCE_NAME = "Eastmoney/Tiantian Fund all-market fund list"
SOURCE_TYPE = "public_aggregation"
EVIDENCE_LEVEL = "Medium"

CANDIDATE_FIELDS = [
    "asset_code",
    "asset_name",
    "asset_type",
    "market",
    "fund_company",
    "risk_level",
    "theme",
    "is_off_platform_fund",
    "is_excluded",
    "exclusion_reason",
    "official_source_count",
    "fallback_aggregated",
    "evidence_level",
    "source_name",
    "source_type",
    "source_url",
    "missing_nav_days",
    "missing_holding_days",
    "conflict_flag",
    "as_of",
]

PRICE_HISTORY_FIELDS = [
    "asset_code",
    "date",
    "close",
    "source_name",
    "source_type",
    "source_priority",
    "url_or_path",
    "evidence_level",
    "as_of",
]

CONSERVATIVE_KEYWORDS = (
    "债",
    "货币",
    "现金",
    "理财",
    "稳健",
    "固收",
    "短债",
    "同业存单",
    "余额宝",
    "bond",
    "money",
    "cash",
    "fixed income",
)

THEME_KEYWORDS: tuple[tuple[str, int], ...] = (
    ("人工智能", 6),
    ("AI", 6),
    ("半导体", 6),
    ("芯片", 6),
    ("科技", 5),
    ("互联网", 5),
    ("纳斯达克", 5),
    ("纳指", 5),
    ("QDII", 5),
    ("创业板", 4),
    ("科创", 4),
    ("通信", 4),
    ("5G", 4),
    ("机器人", 4),
    ("软件", 4),
    ("云计算", 4),
    ("数字经济", 4),
    ("计算机", 4),
    ("信息技术", 4),
    ("电子", 4),
    ("恒生科技", 4),
    ("港股通", 3),
    ("新能源", 3),
    ("光伏", 3),
    ("创新", 2),
    ("成长", 2),
)


@dataclass(frozen=True)
class FundUniverseItem:
    code: str
    name: str
    fund_type: str
    pinyin: str
    theme_score: int
    matched_keywords: tuple[str, ...]


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def parse_eastmoney_fund_list(text: str) -> list[dict[str, str]]:
    cleaned = text.lstrip("\ufeff").strip()
    match = re.search(r"var\s+r\s*=\s*(\[.*\])\s*;?\s*$", cleaned, flags=re.S)
    if not match:
        raise ValueError("Eastmoney fund list payload does not match expected JavaScript array")
    payload = json.loads(match.group(1))
    rows: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, list) or len(item) < 5:
            continue
        rows.append(
            {
                "code": str(item[0]).strip(),
                "abbr": str(item[1]).strip(),
                "name": str(item[2]).strip(),
                "fund_type": str(item[3]).strip(),
                "pinyin": str(item[4]).strip(),
            }
        )
    return rows


def fetch_eastmoney_fund_list(timeout_seconds: float) -> list[dict[str, str]]:
    request = Request(
        EASTMONEY_FUND_LIST_URL,
        headers={
            "User-Agent": "Mozilla/5.0 SerenityDailyAnalysis/0.1",
            "Referer": "https://fund.eastmoney.com/",
            "Accept": "application/javascript,text/plain,*/*",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed public fund-list endpoint
        text = response.read().decode("utf-8-sig", errors="ignore")
    return parse_eastmoney_fund_list(text)


def _cache_path(settings: Settings) -> Path:
    return settings.data_dir / "cache" / "fund_universe_eastmoney_latest.json"


def _nav_cache_path(settings: Settings, code: str) -> Path:
    return settings.data_dir / "cache" / "fund_nav_history" / f"{code}.csv"


def _load_cached_fund_list(settings: Settings) -> list[dict[str, str]]:
    path = _cache_path(settings)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def _write_cached_fund_list(settings: Settings, rows: list[dict[str, str]], generated_at: str) -> Path:
    path = _cache_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "source_url": EASTMONEY_FUND_LIST_URL,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _theme_score(row: dict[str, str]) -> tuple[int, tuple[str, ...]]:
    name_type_haystack = " ".join([row.get("name", ""), row.get("fund_type", "")]).upper()
    full_haystack = " ".join([row.get("name", ""), row.get("fund_type", ""), row.get("pinyin", "")]).upper()
    score = 0
    matched: list[str] = []
    for keyword, weight in THEME_KEYWORDS:
        key = keyword.upper()
        haystack = name_type_haystack if key.isascii() and len(key) <= 4 else full_haystack
        if key in haystack:
            score += weight
            matched.append(keyword)
    fund_type = row.get("fund_type", "")
    if any(kind in fund_type for kind in ["股票", "混合型-偏股", "指数型-股票"]):
        score += 2
    return score, tuple(matched)


def _is_conservative(row: dict[str, str]) -> bool:
    haystack = " ".join([row.get("name", ""), row.get("fund_type", "")]).lower()
    return any(keyword.lower() in haystack for keyword in CONSERVATIVE_KEYWORDS)


def select_growth_funds(
    rows: list[dict[str, str]],
    *,
    min_theme_score: int,
    limit: int,
    existing_codes: set[str] | None = None,
) -> list[FundUniverseItem]:
    existing = existing_codes or set()
    selected: list[FundUniverseItem] = []
    for row in rows:
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()
        if not code or code in existing or _is_conservative(row):
            continue
        score, matched = _theme_score(row)
        if score < min_theme_score:
            continue
        selected.append(
            FundUniverseItem(
                code=code,
                name=name,
                fund_type=row.get("fund_type", "").strip(),
                pinyin=row.get("pinyin", "").strip(),
                theme_score=score,
                matched_keywords=matched,
            )
        )
    selected.sort(key=lambda item: (-item.theme_score, item.code))
    return selected[:limit]


def _read_candidate_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or CANDIDATE_FIELDS)
        rows = [dict(row) for row in reader]
    for field in CANDIDATE_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
    return fieldnames, rows


def _read_csv_rows(path: Path, fallback_fields: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return list(fallback_fields), []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or fallback_fields), [dict(row) for row in reader]


def _write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _market_for(item: FundUniverseItem) -> str:
    haystack = f"{item.name} {item.fund_type}".upper()
    if any(keyword in haystack for keyword in ["QDII", "纳斯达克", "纳指", "标普", "美国", "全球"]):
        return "CN/US"
    if any(keyword in haystack for keyword in ["恒生", "港股", "香港"]):
        return "CN/HK"
    return "CN"


def _candidate_row(item: FundUniverseItem, as_of: str) -> dict[str, str]:
    qdii = "QDII" in f"{item.name} {item.fund_type}".upper()
    return {
        "asset_code": item.code,
        "asset_name": item.name,
        "asset_type": "off_platform_qdii_fund" if qdii else "off_platform_fund",
        "market": _market_for(item),
        "fund_company": "",
        "risk_level": "high",
        "theme": "、".join(item.matched_keywords) or "高成长",
        "is_off_platform_fund": "true",
        "is_excluded": "false",
        "exclusion_reason": "",
        "official_source_count": "0",
        "fallback_aggregated": "true",
        "evidence_level": EVIDENCE_LEVEL,
        "source_name": SOURCE_NAME,
        "source_type": SOURCE_TYPE,
        "source_url": EASTMONEY_FUND_LIST_URL,
        "missing_nav_days": "0",
        "missing_holding_days": "0",
        "conflict_flag": "false",
        "as_of": as_of[:10],
    }


def _write_candidates(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    _write_csv_rows(path, fieldnames, rows)


def _price_span_days(rows: list[dict[str, str]]) -> int:
    dates = sorted(row.get("date", "") for row in rows if row.get("date"))
    if len(dates) < 2:
        return 0
    return (datetime.fromisoformat(dates[-1]).date() - datetime.fromisoformat(dates[0]).date()).days


def _load_nav_cache(settings: Settings, code: str) -> list[dict[str, str]]:
    _, rows = _read_csv_rows(_nav_cache_path(settings, code), PRICE_HISTORY_FIELDS)
    return rows


def _write_nav_cache(settings: Settings, code: str, rows: list[dict[str, str]]) -> None:
    _write_csv_rows(_nav_cache_path(settings, code), PRICE_HISTORY_FIELDS, rows)


def _fetch_nav_history_rows(
    settings: Settings,
    item: FundUniverseItem,
    *,
    generated_at: str,
) -> tuple[list[dict[str, str]], str]:
    end_date = generated_at[:10]
    start_date = (
        datetime.fromisoformat(end_date).date()
        - timedelta(days=settings.min_candidate_nav_history_span_days + 45)
    ).isoformat()
    raw_rows, source_url = _fetch_eastmoney_nav(
        item.code,
        start_date,
        end_date,
        settings.candidate_universe_fetch_timeout_seconds,
        workers=4,
    )
    by_date: dict[str, dict[str, str]] = {}
    for raw in raw_rows:
        nav_date = str(raw.get("FSRQ") or "").strip()
        close_raw = str(raw.get("DWJZ") or raw.get("LJJZ") or "").strip()
        if not nav_date or not close_raw:
            continue
        by_date[nav_date] = {
            "asset_code": item.code,
            "date": nav_date,
            "close": str(float(close_raw)),
            "source_name": "Eastmoney/Tiantian Fund historical NAV API",
            "source_type": SOURCE_TYPE,
            "source_priority": "5",
            "url_or_path": source_url,
            "evidence_level": EVIDENCE_LEVEL,
            "as_of": end_date,
        }
    return [by_date[key] for key in sorted(by_date)], source_url


def _runtime_price_history(
    settings: Settings,
    *,
    output_dir: Path,
    additions: list[FundUniverseItem],
    generated_at: str,
    backfill_nav: bool,
) -> tuple[str | None, dict[str, object]]:
    base_path = settings.manual_dir / "price_history.csv"
    fieldnames, base_rows = _read_csv_rows(base_path, PRICE_HISTORY_FIELDS)
    for field in PRICE_HISTORY_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
    existing_pairs = {(row.get("asset_code", ""), row.get("date", "")) for row in base_rows}
    existing_codes = {row.get("asset_code", "") for row in base_rows}
    nav_rows: list[dict[str, str]] = []
    backfilled: list[str] = []
    short: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    attempted = 0

    if backfill_nav:
        for item in additions:
            if item.code in existing_codes or attempted >= settings.candidate_universe_max_nav_backfills:
                continue
            attempted += 1
            rows = _load_nav_cache(settings, item.code)
            if _price_span_days(rows) < settings.min_candidate_nav_history_span_days:
                try:
                    rows, _ = _fetch_nav_history_rows(settings, item, generated_at=generated_at)
                    if rows:
                        _write_nav_cache(settings, item.code, rows)
                except Exception as exc:
                    errors.append({"asset_code": item.code, "asset_name": item.name, "error": str(exc)})
                    rows = []
            span = _price_span_days(rows)
            if span >= settings.min_candidate_nav_history_span_days:
                backfilled.append(item.code)
                for row in rows:
                    pair = (row.get("asset_code", ""), row.get("date", ""))
                    if pair not in existing_pairs:
                        nav_rows.append(row)
                        existing_pairs.add(pair)
            else:
                short.append({"asset_code": item.code, "asset_name": item.name, "span_days": span, "rows": len(rows)})

    expanded_price_path = output_dir / "price_history_expanded_latest.csv"
    if base_rows or nav_rows:
        _write_csv_rows(expanded_price_path, fieldnames, base_rows + nav_rows)
    result = {
        "base_price_history_path": str(base_path),
        "expanded_price_history_path": str(expanded_price_path) if (base_rows or nav_rows) else None,
        "base_price_rows": len(base_rows),
        "nav_backfill_enabled": backfill_nav,
        "nav_backfill_attempted_count": attempted,
        "nav_backfilled_count": len(backfilled),
        "nav_backfilled_codes": backfilled,
        "nav_short_count": len(short),
        "nav_short": short[:20],
        "nav_error_count": len(errors),
        "nav_errors": errors[:20],
    }
    return result["expanded_price_history_path"], result


def _write_markdown(path: Path, result: dict[str, object], additions: list[FundUniverseItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    price_result = result.get("price_history_expansion") or {}
    lines = [
        "# Serenity 全市场候选池自动扩容",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 状态：{result['status']}",
        f"- 全市场扫描数量：{result['scanned_count']}",
        f"- 基础候选数量：{result['base_count']}",
        f"- 本轮新增候选：{result['added_count']}",
        f"- 扩容后候选数量：{result['expanded_count']}",
        f"- 24个月净值补齐：{price_result.get('nav_backfilled_count', 0)} / {price_result.get('nav_backfill_attempted_count', 0)}",
        f"- 来源：{SOURCE_NAME}",
        f"- 来源链接：{EASTMONEY_FUND_LIST_URL}",
        "",
        "## 处理原则",
        "",
        "- 扩容只扩大 Serenity 可观察范围，不等于直接给出买入建议。",
        "- 自动发现的新对象如果缺少 24 个月净值、申赎/费率或官方级来源，会被降级到观察/复核，不进入可执行结论。",
        "- 债券、货币、现金、余额宝、固收和其他保守类对象在扩容阶段直接排除。",
        "",
        "| 代码 | 基金 | 类型 | 主题命中 | 主题分 |",
        "|---|---|---|---|---:|",
    ]
    if additions:
        for item in additions:
            lines.append(
                f"| {item.code} | {item.name} | {item.fund_type} | "
                f"{'、'.join(item.matched_keywords) or '-'} | {item.theme_score} |"
            )
    else:
        lines.append("| - | 本轮无新增 | - | - | 0 |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def expand_candidate_universe(
    settings: Settings,
    *,
    base_candidates_path: Path | None = None,
    output_dir: Path | None = None,
    live_fetch: bool | None = None,
    max_additions: int | None = None,
    backfill_nav: bool | None = None,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    base_path = base_candidates_path or settings.manual_dir / "candidates.csv"
    generated_at = _now(settings)
    out_dir = output_dir or settings.root_dir / "outputs" / "preflight"
    expanded_path = out_dir / "candidate_universe_expanded_latest.csv"
    json_path = out_dir / "candidate_universe_expansion_latest.json"
    md_path = out_dir / "candidate_universe_expansion_latest.md"

    if not base_path.exists():
        result = {
            "generated_at": generated_at,
            "status": "block",
            "message": "base candidate universe missing",
            "base_candidates_path": str(base_path),
            "expanded_candidates_path": str(base_path),
            "scanned_count": 0,
            "base_count": 0,
            "added_count": 0,
            "expanded_count": 0,
            "live_fetch": False,
            "cache_used": False,
            "source_url": EASTMONEY_FUND_LIST_URL,
            "json_path": str(json_path),
            "markdown_path": str(md_path),
        }
        return result

    fieldnames, base_rows = _read_candidate_rows(base_path)
    existing_codes = {row.get("asset_code", "").strip() for row in base_rows if row.get("asset_code")}
    if not settings.candidate_universe_auto_expand_enabled:
        if write_output:
            _write_candidates(expanded_path, fieldnames, base_rows)
        return {
            "generated_at": generated_at,
            "status": "disabled",
            "message": "candidate universe auto expansion disabled",
            "base_candidates_path": str(base_path),
            "expanded_candidates_path": str(expanded_path if write_output else base_path),
            "scanned_count": 0,
            "base_count": len(base_rows),
            "added_count": 0,
            "expanded_count": len(base_rows),
            "live_fetch": False,
            "cache_used": False,
            "source_url": EASTMONEY_FUND_LIST_URL,
            "json_path": str(json_path),
            "markdown_path": str(md_path),
        }

    resolved_live_fetch = settings.candidate_universe_live_fetch_enabled if live_fetch is None else live_fetch
    rows: list[dict[str, str]] = []
    fetch_error = ""
    cache_used = False
    if resolved_live_fetch:
        try:
            rows = fetch_eastmoney_fund_list(settings.candidate_universe_fetch_timeout_seconds)
            _write_cached_fund_list(settings, rows, generated_at)
        except Exception as exc:
            fetch_error = str(exc)
    if not rows:
        rows = _load_cached_fund_list(settings)
        cache_used = bool(rows)

    additions = select_growth_funds(
        rows,
        min_theme_score=settings.candidate_universe_min_theme_score,
        limit=max_additions or settings.candidate_universe_max_additions,
        existing_codes=existing_codes,
    )
    expanded_rows = list(base_rows) + [_candidate_row(item, generated_at) for item in additions]
    nav_backfill_enabled = (
        settings.candidate_universe_nav_backfill_enabled if backfill_nav is None else backfill_nav
    )
    if write_output:
        expanded_price_history_path, price_result = _runtime_price_history(
            settings,
            output_dir=out_dir,
            additions=additions,
            generated_at=generated_at,
            backfill_nav=nav_backfill_enabled,
        )
    else:
        expanded_price_history_path = None
        price_result = {
            "base_price_history_path": str(settings.manual_dir / "price_history.csv"),
            "expanded_price_history_path": None,
            "base_price_rows": 0,
            "nav_backfill_enabled": nav_backfill_enabled,
            "nav_backfill_attempted_count": 0,
            "nav_backfilled_count": 0,
            "nav_backfilled_codes": [],
            "nav_short_count": 0,
            "nav_short": [],
            "nav_error_count": 0,
            "nav_errors": [],
        }
    status = "pass" if rows else "warn"
    message = (
        "all-market public fund universe expanded"
        if rows
        else "public fund universe unavailable; using base candidate universe only"
    )
    if fetch_error and cache_used:
        message = f"live fetch failed; cache used: {fetch_error}"
    elif fetch_error:
        message = f"live fetch failed and no cache available: {fetch_error}"

    result = {
        "generated_at": generated_at,
        "status": status,
        "message": message,
        "base_candidates_path": str(base_path),
        "expanded_candidates_path": str(expanded_path if write_output else base_path),
        "expanded_price_history_path": expanded_price_history_path,
        "scanned_count": len(rows),
        "base_count": len(base_rows),
        "added_count": len(additions),
        "expanded_count": len(expanded_rows),
        "live_fetch": bool(resolved_live_fetch),
        "cache_used": cache_used,
        "fetch_error": fetch_error,
        "source_name": SOURCE_NAME,
        "source_type": SOURCE_TYPE,
        "source_url": EASTMONEY_FUND_LIST_URL,
        "additions": [asdict(item) for item in additions],
        "price_history_expansion": price_result,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }
    if write_output:
        _write_candidates(expanded_path, fieldnames, expanded_rows)
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_markdown(md_path, result, additions)
    return result
