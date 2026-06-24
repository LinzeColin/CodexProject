from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.adapters.manual_sources import Candidate, FundRule, load_candidates, load_fund_rules
from app.config import Settings
from app.db import connect, init_db, insert_row


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) SerenityDailyAnalysis/0.1"
)
DEFAULT_MAX_BYTES = 8 * 1024 * 1024

BUY_OPEN_TERMS = ("开放申购", "申购开放", "可申购", "可购买", "开放购买", "办理申购", "接受申购", "买入")
BUY_LIMITED_TERMS = ("暂停大额申购", "限制大额申购", "大额申购", "限购", "限额", "申购上限", "单日累计")
BUY_CLOSED_TERMS = ("暂停申购", "暂停接受申购", "暂停办理申购", "暂停购买", "不可申购", "停止申购", "封闭期")

SELL_OPEN_TERMS = ("开放赎回", "赎回开放", "可赎回", "办理赎回", "接受赎回", "卖出")
SELL_CLOSED_TERMS = ("暂停赎回", "暂停接受赎回", "暂停办理赎回", "不可赎回", "停止赎回", "封闭期")

STATUS_LABELS = {
    "open": "可买/可卖",
    "limited": "受限/需复核",
    "closed": "不可用",
    "unknown": "未知",
}


@dataclass(frozen=True)
class FetchResult:
    fetch_status: str
    http_status: int | None
    content_type: str
    text: str
    content_sha256: str
    message: str


@dataclass(frozen=True)
class PlatformTradeRow:
    check_run_id: str
    generated_at: str
    asset_code: str
    asset_name: str
    preferred_source: str
    source_field: str
    source_url: str
    http_status: int | None
    fetch_status: str
    subscription_advisory: str
    redemption_advisory: str
    confidence: str
    advisory_only: bool
    evidence_snippet: str
    matched_terms: str
    content_sha256: str
    message: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _read_candidates(settings: Settings) -> dict[str, Candidate]:
    path = settings.manual_dir / "candidates.csv"
    if not path.exists():
        return {}
    return {candidate.asset_code: candidate for candidate in load_candidates(path)}


def _read_rules(settings: Settings) -> dict[str, FundRule]:
    path = settings.manual_dir / "fund_rules.csv"
    if not path.exists():
        return {}
    return load_fund_rules(path)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _source_kind(url: str, source_type: str) -> str:
    lowered = f"{url} {source_type}".lower()
    if "alipay" in lowered or "支付宝" in lowered or "antfin" in lowered:
        return "alipay"
    if "official" in lowered or "官网" in lowered or "基金公司" in lowered:
        return "official"
    if "moomoo" in lowered:
        return "moomoo"
    return "public"


def _source_priority(kind: str) -> int:
    return {"alipay": 0, "official": 1, "public": 2, "moomoo": 3}.get(kind, 9)


def _select_source(rule: FundRule | None, candidate: Candidate | None) -> tuple[str, str, str]:
    options: list[tuple[int, str, str, str]] = []
    if rule and _is_http_url(rule.url_or_path):
        kind = _source_kind(rule.url_or_path, rule.source_type)
        options.append((_source_priority(kind), kind, "fund_rules.url_or_path", rule.url_or_path))
    if candidate and _is_http_url(candidate.source_url):
        kind = _source_kind(candidate.source_url, candidate.source_type)
        options.append((_source_priority(kind), kind, "candidates.source_url", candidate.source_url))
    if not options:
        return "unknown", "", ""
    options.sort(key=lambda item: item[0])
    _, kind, field, url = options[0]
    return kind, field, url


def _decode_text(raw: bytes, content_type: str) -> str:
    charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.IGNORECASE)
    encodings = [charset_match.group(1)] if charset_match else []
    encodings.extend(["utf-8", "gb18030", "big5"])
    seen: set[str] = set()
    for encoding in encodings:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="ignore")


def _extract_pdf_text(raw: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", "PDF已抓取但当前环境未安装pypdf，无法解析正文"
    try:
        reader = PdfReader(BytesIO(raw))
        text_parts = [(page.extract_text() or "") for page in reader.pages[:8]]
        return "\n".join(part for part in text_parts if part).strip(), "PDF正文已解析"
    except Exception as exc:  # pragma: no cover - defensive optional parser boundary
        return "", f"PDF已抓取但解析失败：{exc}"


def fetch_url(url: str, timeout_seconds: float = 8.0, max_bytes: int = DEFAULT_MAX_BYTES) -> FetchResult:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - user-provided fund/source URLs
            raw = response.read(max_bytes + 1)
            truncated = len(raw) > max_bytes
            if truncated:
                raw = raw[:max_bytes]
            content_type = response.headers.get("Content-Type", "")
            sha256 = hashlib.sha256(raw).hexdigest()
            is_pdf = "pdf" in content_type.lower() or url.lower().endswith(".pdf") or raw.startswith(b"%PDF")
            if is_pdf:
                text, pdf_message = _extract_pdf_text(raw)
                status = "fetched" if text else "fetched_pdf_unparsed"
                suffix = "；内容已截断" if truncated else ""
                return FetchResult(
                    fetch_status=status,
                    http_status=response.status,
                    content_type=content_type,
                    text=text,
                    content_sha256=sha256,
                    message=pdf_message + suffix,
                )
            text = _decode_text(raw, content_type)
            return FetchResult(
                fetch_status="fetched",
                http_status=response.status,
                content_type=content_type,
                text=text,
                content_sha256=sha256,
                message="页面已抓取" + ("；内容已截断" if truncated else ""),
            )
    except HTTPError as exc:
        raw = exc.read(256 * 1024)
        return FetchResult(
            fetch_status="http_error",
            http_status=exc.code,
            content_type=exc.headers.get("Content-Type", ""),
            text=_decode_text(raw, exc.headers.get("Content-Type", "")) if raw else "",
            content_sha256=hashlib.sha256(raw).hexdigest() if raw else "",
            message=f"HTTP错误：{exc.code}",
        )
    except (TimeoutError, URLError, OSError) as exc:
        return FetchResult(
            fetch_status="fetch_error",
            http_status=None,
            content_type="",
            text="",
            content_sha256="",
            message=f"抓取失败：{exc}",
        )


def _normalize_text(text: str) -> str:
    cleaned = re.sub(r"<script\b.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<style\b.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def _classify_buy(text: str) -> tuple[str, list[str]]:
    limited = _matched_terms(text, BUY_LIMITED_TERMS)
    closed = _matched_terms(text, BUY_CLOSED_TERMS)
    open_terms = _matched_terms(text, BUY_OPEN_TERMS)
    if closed and not limited:
        return "closed", closed
    if limited:
        return "limited", limited + open_terms
    if open_terms:
        return "open", open_terms
    return "unknown", []


def _classify_sell(text: str) -> tuple[str, list[str]]:
    closed = _matched_terms(text, SELL_CLOSED_TERMS)
    open_terms = _matched_terms(text, SELL_OPEN_TERMS)
    if closed:
        return "closed", closed
    if open_terms:
        return "open", open_terms
    return "unknown", []


def _confidence(source_kind: str, fetch_status: str, buy: str, sell: str) -> str:
    known_count = int(buy != "unknown") + int(sell != "unknown")
    if source_kind in {"alipay", "official"} and fetch_status == "fetched" and known_count == 2:
        return "high"
    if fetch_status.startswith("fetched") and known_count >= 1:
        return "medium"
    return "low"


def _snippet(text: str, terms: list[str], max_len: int = 180) -> str:
    if not text:
        return ""
    start = 0
    for term in terms:
        position = text.find(term)
        if position >= 0:
            start = max(0, position - 60)
            break
    snippet = text[start : start + max_len]
    return snippet.replace("|", "/").strip()


def _check_row(
    *,
    check_run_id: str,
    generated_at: str,
    asset_code: str,
    asset_name: str,
    source_kind: str,
    source_field: str,
    source_url: str,
    fetcher: Callable[[str, float], FetchResult],
    timeout_seconds: float,
) -> PlatformTradeRow:
    if not source_url:
        return PlatformTradeRow(
            check_run_id=check_run_id,
            generated_at=generated_at,
            asset_code=asset_code,
            asset_name=asset_name,
            preferred_source=source_kind,
            source_field=source_field,
            source_url="",
            http_status=None,
            fetch_status="skipped_no_http_source",
            subscription_advisory="unknown",
            redemption_advisory="unknown",
            confidence="low",
            advisory_only=True,
            evidence_snippet="",
            matched_terms="",
            content_sha256="",
            message="没有支付宝或官方HTTP来源；仅保留人工复核建议，不影响候选池",
        )
    fetched = fetcher(source_url, timeout_seconds)
    clean_text = _normalize_text(fetched.text)
    buy, buy_terms = _classify_buy(clean_text)
    sell, sell_terms = _classify_sell(clean_text)
    terms = buy_terms + sell_terms
    confidence = _confidence(source_kind, fetched.fetch_status, buy, sell)
    if buy == "unknown" and sell == "unknown":
        status_note = "未在抓取内容中稳定识别申购/赎回状态"
    else:
        status_note = f"识别结果：申购={buy}，赎回={sell}"
    return PlatformTradeRow(
        check_run_id=check_run_id,
        generated_at=generated_at,
        asset_code=asset_code,
        asset_name=asset_name,
        preferred_source=source_kind,
        source_field=source_field,
        source_url=source_url,
        http_status=fetched.http_status,
        fetch_status=fetched.fetch_status,
        subscription_advisory=buy,
        redemption_advisory=sell,
        confidence=confidence,
        advisory_only=True,
        evidence_snippet=_snippet(clean_text, terms),
        matched_terms=";".join(dict.fromkeys(terms)),
        content_sha256=fetched.content_sha256,
        message=f"{fetched.message}；{status_note}；advisory-only，不改候选池、不改权重、不自动交易",
    )


def _write_csv(path: Path, rows: list[PlatformTradeRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(PlatformTradeRow.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            payload = asdict(row)
            payload["advisory_only"] = "true" if row.advisory_only else "false"
            writer.writerow(payload)


def _write_markdown(path: Path, result: dict[str, object], rows: list[PlatformTradeRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 平台交易可用性真实校验",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 校验ID：{result['check_run_id']}",
        f"- 状态：{result['status']}",
        f"- 覆盖基金：{result['row_count']}",
        f"- 需要人工复核：{result['manual_review_count']}",
        f"- 规则：只做建议，不改候选池、不改权重、不自动交易；执行前仍以支付宝或官方交易确认页为准。",
        "",
        "| 基金 | 来源 | 申购建议 | 赎回建议 | 置信度 | 证据 |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        buy = STATUS_LABELS.get(row.subscription_advisory, row.subscription_advisory)
        sell = STATUS_LABELS.get(row.redemption_advisory, row.redemption_advisory)
        source = row.preferred_source if row.source_url else "无HTTP来源"
        evidence = row.evidence_snippet or row.message
        evidence = evidence.replace("\n", " ").replace("|", "/")[:140]
        lines.append(f"| {row.asset_code} {row.asset_name} | {source} | {buy} | {sell} | {row.confidence} | {evidence} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _persist_rows(settings: Settings, rows: list[PlatformTradeRow]) -> int:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        for row in rows:
            payload = asdict(row)
            payload["advisory_only"] = 1 if row.advisory_only else 0
            insert_row(conn, "platform_trade_check_snapshot", payload)
    return len(rows)


def run_platform_trade_check(
    settings: Settings,
    *,
    asset_codes: list[str] | None = None,
    limit: int | None = None,
    timeout_seconds: float = 8.0,
    write_output: bool = True,
    write_db: bool = True,
    fetcher: Callable[[str, float], FetchResult] = fetch_url,
) -> dict[str, object]:
    settings.ensure_dirs()
    generated_at = _now(settings)
    check_run_id = "platform_trade_" + generated_at.replace(":", "").replace("-", "").replace("+", "_").replace("T", "_")
    candidates = _read_candidates(settings)
    rules = _read_rules(settings)
    selected_codes = list(dict.fromkeys(asset_codes or sorted(set(rules) | set(candidates))))
    rows: list[PlatformTradeRow] = []
    explicit_filter = bool(asset_codes)
    for asset_code in selected_codes:
        candidate = candidates.get(asset_code)
        rule = rules.get(asset_code)
        if not rule and not candidate:
            continue
        if candidate and candidate.is_excluded and not explicit_filter:
            continue
        asset_name = candidate.asset_name if candidate else asset_code
        source_kind, source_field, source_url = _select_source(rule, candidate)
        rows.append(
            _check_row(
                check_run_id=check_run_id,
                generated_at=generated_at,
                asset_code=asset_code,
                asset_name=asset_name,
                source_kind=source_kind,
                source_field=source_field,
                source_url=source_url,
                fetcher=fetcher,
                timeout_seconds=timeout_seconds,
            )
        )
        if limit and len(rows) >= limit:
            break

    output_dir = settings.root_dir / "outputs" / "preflight"
    files = {
        "markdown": str(output_dir / "platform_trade_check_latest.md"),
        "csv": str(output_dir / "platform_trade_check_latest.csv"),
        "json": str(output_dir / "platform_trade_check_latest.json"),
    }
    manual_review_count = sum(
        1
        for row in rows
        if row.confidence == "low"
        or row.subscription_advisory == "unknown"
        or row.redemption_advisory == "unknown"
        or row.fetch_status not in {"fetched"}
    )
    unavailable_count = sum(
        1
        for row in rows
        if row.subscription_advisory == "closed" or row.redemption_advisory == "closed"
    )
    db_rows_written = _persist_rows(settings, rows) if write_output and write_db else 0
    result: dict[str, object] = {
        "generated_at": generated_at,
        "check_run_id": check_run_id,
        "status": "watch" if manual_review_count else "pass",
        "row_count": len(rows),
        "manual_review_count": manual_review_count,
        "unavailable_count": unavailable_count,
        "advisory_only": True,
        "ranking_impact": "none",
        "execution_impact": "manual_confirm_required",
        "db_rows_written": db_rows_written,
        "source_counts": dict(Counter(row.preferred_source for row in rows)),
        "fetch_status_counts": dict(Counter(row.fetch_status for row in rows)),
        "confidence_counts": dict(Counter(row.confidence for row in rows)),
        "files": files,
    }
    if write_output:
        _write_csv(Path(files["csv"]), rows)
        _write_markdown(Path(files["markdown"]), result, rows)
        Path(files["json"]).write_text(
            json.dumps({**result, "rows": [asdict(row) for row in rows]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return result
