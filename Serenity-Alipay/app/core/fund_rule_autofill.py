from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import Candidate, FundRule
from app.config import Settings


SOURCE_NAME = "Eastmoney/Tiantian Fund fee/status page"
SOURCE_TYPE = "public_aggregation"
SOURCE_PRIORITY = 5
EVIDENCE_LEVEL = "Medium"


@dataclass(frozen=True)
class FundRuleAutofillRow:
    asset_code: str
    asset_name: str
    status: str
    source_url: str
    missing_fields: tuple[str, ...]
    message: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _fee_url(code: str) -> str:
    return f"https://fundf10.eastmoney.com/jjfl_{code}.html"


def _fetch_text(url: str, timeout_seconds: float) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 SerenityDailyAnalysis/0.1",
            "Referer": "https://fundf10.eastmoney.com/",
            "Accept": "text/html,*/*",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed public fund fee endpoint
        return response.read().decode("utf-8", errors="ignore")


def _strip_tags(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", "", value).strip()


def _section(text: str, start_label: str, end_label: str | None = None) -> str:
    start = text.find(start_label)
    if start < 0:
        return ""
    end = text.find(end_label, start + len(start_label)) if end_label else -1
    return text[start:end] if end > start else text[start:]


def _rows_from_section(section: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", section, flags=re.I | re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", match.group(1), flags=re.I | re.S)
        if len(cells) < 2:
            continue
        left = _strip_tags(cells[0])
        right = _strip_tags(cells[1])
        if left and right and "费率" not in left:
            rows.append((left, right))
    return rows


def _schedule(rows: list[tuple[str, str]]) -> str:
    return "；".join(f"{left} {right}" for left, right in rows)


def _first_percent(schedule: str) -> float | None:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)%", schedule)
    return float(match.group(1)) / 100.0 if match else None


def _annual_fee(text: str, label: str) -> float | None:
    match = re.search(label + r".{0,80}?([0-9]+(?:\.[0-9]+)?)%（?每年", text, flags=re.S)
    return float(match.group(1)) / 100.0 if match else None


def _lag(text: str, label: str, default: str) -> str:
    match = re.search(label + r".{0,80}?(T\+\d+)", text, flags=re.S)
    return match.group(1) if match else default


def _status(text: str, closed_terms: tuple[str, ...], limited_terms: tuple[str, ...], open_default: str = "open") -> str:
    if any(term in text for term in closed_terms):
        return "closed"
    if any(term in text for term in limited_terms):
        return "limited"
    return open_default


def parse_fund_rule_from_fee_page(candidate: Candidate, text: str, *, as_of: str, source_url: str) -> FundRule:
    subscription_rows = _rows_from_section(_section(text, "申购费率", "赎回费率"))
    redemption_rows = _rows_from_section(_section(text, "赎回费率", "注："))
    subscription_schedule = _schedule(subscription_rows)
    redemption_schedule = _schedule(redemption_rows)
    subscription_status = _status(text, ("暂停申购", "不可申购", "停止申购"), ("大额申购", "限制申购", "限购"))
    redemption_status = _status(text, ("暂停赎回", "不可赎回", "停止赎回"), ("限制赎回",))
    return FundRule(
        asset_code=candidate.asset_code,
        subscription_status=subscription_status,
        redemption_status=redemption_status,
        cutoff_time="15:00",
        confirm_lag=_lag(text, "买入确认日", "T+1"),
        redeem_lag=_lag(text, "卖出确认日", "T+3"),
        subscription_fee=_first_percent(subscription_schedule),
        redemption_fee=_first_percent(redemption_schedule),
        management_fee=_annual_fee(text, "管理费率"),
        custody_fee=_annual_fee(text, "托管费率"),
        sales_service_fee=_annual_fee(text, "销售服务费率") or 0.0,
        min_purchase_amount=10.0,
        source_name=SOURCE_NAME,
        source_type=SOURCE_TYPE,
        source_priority=SOURCE_PRIORITY,
        url_or_path=source_url,
        evidence_level=EVIDENCE_LEVEL,
        fallback_aggregated=True,
        as_of=as_of[:10],
        subscription_fee_schedule=subscription_schedule,
        redemption_fee_schedule=redemption_schedule,
        fee_schedule_as_of=as_of[:10],
        fee_schedule_note="自动补齐自天天基金公开费率页；属于公开聚合源，执行前仍需支付宝或基金公司官方页确认。",
        alipay_trade_status="待支付宝交易页确认（自动扩容候选）",
        moomoo_trade_status="未验证MooMoo场外基金交易；MooMoo仅作行情/代理数据参考",
        platform_trade_note="扩容候选交易可用性只作建议；不支持支付宝或MooMoo交易不能单独排除候选；执行前以支付宝交易确认页或基金公司官方平台为准",
    )


def _missing_fields(rule: FundRule) -> tuple[str, ...]:
    missing: list[str] = []
    for field in [
        "subscription_status",
        "redemption_status",
        "subscription_fee",
        "redemption_fee",
        "subscription_fee_schedule",
        "redemption_fee_schedule",
        "management_fee",
        "custody_fee",
    ]:
        value = getattr(rule, field)
        if value in (None, ""):
            missing.append(field)
    return tuple(missing)


def autofill_fund_rules(
    settings: Settings,
    candidates: list[Candidate],
    existing_rules: dict[str, FundRule],
    *,
    max_fetches: int | None = None,
    timeout_seconds: float | None = None,
    write_output: bool = True,
) -> tuple[dict[str, FundRule], dict[str, object]]:
    generated_at = _now(settings)
    if not settings.candidate_universe_rule_autofill_enabled:
        return existing_rules, {"status": "disabled", "generated_at": generated_at, "rows": []}
    rules = dict(existing_rules)
    rows: list[FundRuleAutofillRow] = []
    fetch_limit = max_fetches if max_fetches is not None else settings.candidate_universe_max_rule_autofills
    fetched = 0
    for candidate in candidates:
        if candidate.asset_code in rules or not candidate.asset_code.isdigit():
            continue
        if fetched >= fetch_limit:
            break
        fetched += 1
        source_url = _fee_url(candidate.asset_code)
        try:
            text = _fetch_text(source_url, timeout_seconds or settings.candidate_universe_fetch_timeout_seconds)
            rule = parse_fund_rule_from_fee_page(candidate, text, as_of=generated_at, source_url=source_url)
            rules[candidate.asset_code] = rule
            missing = _missing_fields(rule)
            rows.append(
                FundRuleAutofillRow(
                    candidate.asset_code,
                    candidate.asset_name,
                    "pass" if not missing else "watch",
                    source_url,
                    missing,
                    "自动补齐完成" if not missing else "自动补齐完成但仍有执行关键字段缺失",
                )
            )
        except Exception as exc:
            rows.append(
                FundRuleAutofillRow(
                    candidate.asset_code,
                    candidate.asset_name,
                    "warn",
                    source_url,
                    ("fund_rule_page",),
                    f"自动补齐失败：{exc}",
                )
            )
    result = {
        "generated_at": generated_at,
        "status": "pass" if not any(row.status == "warn" for row in rows) else "watch",
        "attempted_count": fetched,
        "filled_count": sum(1 for row in rows if row.status in {"pass", "watch"}),
        "complete_count": sum(1 for row in rows if row.status == "pass"),
        "rows": [asdict(row) for row in rows],
    }
    if write_output:
        output_dir = settings.root_dir / "outputs" / "preflight"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "fund_rule_autofill_latest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return rules, result
