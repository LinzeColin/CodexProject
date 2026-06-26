from __future__ import annotations

import json
import os
import signal
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

from src.config import ROOT
from src.data_io import write_csv
from src.models import Source


DEFAULT_POLICY_ROOT = Path(
    os.environ.get("AI_RESEARCH_POLICY_ROOT", ROOT.parent.parent / "policy_intelligence" / "source")
).expanduser()
REQUEST_DIR = ROOT / "data" / "report_artifacts" / "policy_bridge" / "requests"
STATUS_DIR = ROOT / "data" / "report_artifacts" / "policy_bridge" / "status"
EVENT_DIR = ROOT / "data" / "report_artifacts" / "policy_bridge" / "events"
THEME_ALIASES = {
    "AI": {"人工智能", "智能算力", "数字经济", "大模型", "科技"},
    "半导体": {"半导体", "芯片", "集成电路", "先进制造", "科技"},
    "机器人": {"机器人", "智能制造", "自动化", "高端装备"},
    "农业": {"农业", "种业", "农机", "乡村", "粮食"},
    "化工": {"化工", "新材料", "石化", "周期"},
    "银行": {"银行", "金融", "资本市场", "利率"},
    "红利": {"红利", "低波", "央企", "分红"},
    "黄金": {"黄金", "贵金属", "避险"},
    "港股": {"港股", "香港", "粤港澳", "科技"},
    "美股": {"美股", "纳斯达克", "科技", "汇率"},
    "科创": {"科创", "科技", "硬科技", "先进制造"},
    "宽基": {"宏观经济", "资本市场", "指数", "金融"},
}
BROAD_POLICY_TOKENS = {"科技", "金融", "资本市场", "指数", "周期", "政策", "行业", "经济", "市场"}
GENERIC_GOVERNMENT_TERMS = {
    "政府信息公开",
    "信息公开",
    "信息处理费",
    "行政复议",
    "年度报告格式",
    "规章集中公开",
    "公共企事业单位信息公开",
    "政务公开",
}
CONFIRMED_REFRESH_STATUSES = {"refreshed", "cached_refreshed"}
PLAN_END_YEAR_BY_ORDINAL = {
    "第十一个": 2010,
    "第十二个": 2015,
    "第十三个": 2020,
    "第十四个": 2025,
    "十一五": 2010,
    "十二五": 2015,
    "十三五": 2020,
    "十四五": 2025,
}


def enrich_events_with_policy_system(
    events: list[dict[str, str]],
    factors: list[dict[str, object]],
    as_of: str,
) -> tuple[list[dict[str, str]], Source | None]:
    request_path = _write_policy_request(as_of, factors)
    refresh_status = _refresh_policy_system_if_enabled(as_of, request_path)
    policy_events = _load_policy_events(as_of, factors, refresh_status, request_path)
    if policy_events:
        write_csv(EVENT_DIR / f"policy_events_{as_of}.csv", policy_events)
    status_path = _write_status(as_of, request_path, refresh_status, len(policy_events))
    if not policy_events:
        policy_events = [_no_match_event(as_of, factors, refresh_status, status_path, request_path)]
    source = Source(
        source_name="Government Policy Interpretation Bridge",
        source_url=str(_policy_root() / "data" / "policy_documents.sqlite"),
        fetch_time=datetime.now().isoformat(),
        data_version="policy_bridge_v1",
    )
    return [*events, *policy_events], source


def _write_policy_request(as_of: str, factors: list[dict[str, object]]) -> Path:
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)
    themes = sorted({str(item.get("research_group") or item.get("industry") or "未分类") for item in factors})
    symbols = [
        {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "exchange": item.get("exchange", ""),
            "asset_class": item.get("asset_class", ""),
            "theme": item.get("research_group") or item.get("industry") or "未分类",
        }
        for item in factors
    ]
    path = REQUEST_DIR / f"policy_context_request_{as_of}.json"
    payload = {
        "as_of": as_of,
        "created_at": datetime.now().isoformat(),
        "requester": "AI-Research-System",
        "purpose": "为日报/周报事件催化提供政府文件和政策解读证据链",
        "themes": themes,
        "symbols": symbols,
        "crawler_task": {
            "mode": "separate_policy_catalyst_crawl",
            "instruction": "按当前自选池主题单独抓取政府文件、政策解读、公告/新闻原文和可验证来源链；不要只返回搜索入口或标题；每条催化剂必须给出原文URL、抓取状态、误读风险和可操作影响。",
            "must_verify_original_text": True,
            "must_flag_misread_risk": True,
            "must_link_operation_impact": True,
            "fallback_rule": "若无法抓到原文或只得到搜索入口，只能作为风险背景，不能提高买入分、买入金额或Volume。",
        },
        "required_output": [
            "政策标题",
            "发布机构",
            "权威等级",
            "相关主题",
            "相关对象名称",
            "影响方向",
            "业务影响",
            "风险约束",
            "操作影响",
            "原文URL",
            "原文抓取状态",
            "公告/新闻原文来源",
            "公告/新闻误读风险",
            "独立爬虫任务报告路径",
            "政策系统报告路径",
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _refresh_policy_system_if_enabled(as_of: str, request_path: Path | None = None) -> dict[str, object]:
    enabled = os.getenv("AI_RESEARCH_POLICY_REFRESH", "0") == "1"
    root = _policy_root()
    script = root / "scripts" / "run_policy_report.sh"
    cached = _recent_refresh_status(as_of)
    if cached:
        return cached
    if not enabled:
        recent_policy_cache = _recent_policy_report_cache_status(
            as_of, "AI_RESEARCH_POLICY_REFRESH not enabled"
        )
        if recent_policy_cache:
            return recent_policy_cache
        return {"status": "db_cached", "reason": "AI_RESEARCH_POLICY_REFRESH not enabled; reading policy database cache", "report_path": ""}
    recent_policy_cache = _recent_policy_report_cache_status(
        as_of, "using recent policy system report/database cache before launching refresh"
    )
    if recent_policy_cache:
        return recent_policy_cache
    if not script.exists():
        return {"status": "missing", "reason": f"policy pipeline script not found: {script}", "report_path": ""}
    timeout_seconds = int(os.getenv("AI_RESEARCH_POLICY_TIMEOUT_SECONDS", "240"))
    env = os.environ.copy()
    env.setdefault("MAX_ANALYZE", "8")
    env.setdefault("MAX_INTERPRETATION_DOCUMENTS", "6")
    env.setdefault("MAX_SOURCES", "3")
    env.setdefault("MAX_PAGES_PER_SOURCE", "2")
    env.setdefault("MAX_LINKS_PER_PAGE", "15")
    env.setdefault("MIN_EXTERNAL_REFERENCES", "3")
    env.setdefault("MIN_EXTERNAL_PLATFORMS", "2")
    env.setdefault("FETCH_INTERPRETATION_RESULTS", "1")
    env.setdefault("FETCH_SEARCH_RESULT_PAGES", "1")
    env.setdefault("AUTOMATION_RUN_ID", f"ai_research_policy_{as_of.replace('-', '')}_{datetime.now().strftime('%H%M%S')}")
    if request_path:
        env["AI_RESEARCH_POLICY_REQUEST_FILE"] = str(request_path)
    process = subprocess.Popen(
        ["bash", str(script)],
        cwd=str(root),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        stdout, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_process_group(process)
        recent_policy_cache = _recent_policy_report_cache_status(as_of, f"policy pipeline exceeded {timeout_seconds}s")
        if recent_policy_cache:
            return recent_policy_cache
        return {"status": "timeout", "reason": f"policy pipeline exceeded {timeout_seconds}s", "report_path": ""}
    report_path = _latest_policy_report_path(root)
    if process.returncode != 0:
        recent_policy_cache = _recent_policy_report_cache_status(as_of, _compact_text(stdout, 220))
        if recent_policy_cache:
            return recent_policy_cache
        return {
            "status": "failed",
            "reason": _compact_text(stdout, 220),
            "report_path": report_path,
        }
    return {"status": "refreshed", "reason": "policy pipeline completed", "report_path": report_path}


def _load_policy_events(
    as_of: str,
    factors: list[dict[str, object]],
    refresh_status: dict[str, object],
    request_path: Path,
) -> list[dict[str, str]]:
    db_path = _policy_root() / "data" / "policy_documents.sqlite"
    if not db_path.exists():
        return []
    theme_index = _theme_index(factors)
    keywords = _keywords_for_themes(theme_index)
    if not keywords:
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                d.document_id,
                d.title,
                COALESCE(d.published_date, d.discovered_at) AS published_at,
                d.source_name,
                d.source_url,
                d.url,
                d.authority_tier_snapshot,
                d.authority_score_snapshot,
                q.primary_industry,
                q.industry_bucket,
                a.importance_score,
                a.chinese_summary,
                a.policy_points_json,
                a.business_impacts_json,
                a.risks_json,
                a.actions_json
            FROM documents d
            LEFT JOIN report_queue q ON q.document_id = d.document_id
            LEFT JOIN analyses a ON a.document_id = d.document_id
            WHERE (a.analysis_id IS NOT NULL OR d.status IN ('fetched', 'analyzed'))
            ORDER BY CAST(COALESCE(a.importance_score, d.authority_score_snapshot, 0) AS INTEGER) DESC,
                     COALESCE(d.published_date, d.discovered_at) DESC
            LIMIT 80
            """
        ).fetchall()
    finally:
        conn.close()
    events = []
    seen: set[str] = set()
    for row in rows:
        if _is_low_value_policy_document(row, as_of):
            continue
        matched = _matched_theme(row, theme_index, keywords)
        if not matched:
            continue
        key = str(row["document_id"])
        if key in seen:
            continue
        seen.add(key)
        events.append(_policy_event_from_row(row, matched, as_of, refresh_status, request_path))
        if len(events) >= 6:
            break
    return events


def _policy_event_from_row(
    row: sqlite3.Row,
    matched: dict[str, object],
    as_of: str,
    refresh_status: dict[str, object],
    request_path: Path,
) -> dict[str, str]:
    published_at = str(row["published_at"] or as_of)
    date_part, time_part = _date_time_parts(published_at, as_of)
    importance = int(row["importance_score"] or row["authority_score_snapshot"] or 0)
    impact = "positive" if importance >= 82 else "neutral"
    symbols = ";".join(str(item.get("symbol") or "") for item in matched["items"] if item.get("symbol"))
    title = str(row["title"] or "")
    authority = f"{row['authority_tier_snapshot'] or '未标注'}/{row['authority_score_snapshot'] or '未标注'}"
    summary = _policy_summary(row, matched)
    source_url = str(row["url"] or row["source_url"] or "")
    operation = _policy_operation_impact(impact, matched, importance, refresh_status, source_url)
    return {
        "date": date_part,
        "event_time": time_part,
        "type": "government_policy_bridge",
        "title": f"政策系统解析：{_compact_text(title, 52)}",
        "summary": summary,
        "impact": impact,
        "related_symbols": symbols,
        "industry": str(matched["theme"]),
        "source_name": f"{row['source_name']} / 政府文件解读系统",
        "source_url": source_url,
        "policy_authority": authority,
        "policy_importance_score": str(importance),
        "policy_bridge_status": str(refresh_status.get("status") or ""),
        "policy_original_fetch_status": "verified" if _has_original_url(source_url) else "missing",
        "policy_request_path": str(request_path),
        "policy_report_path": str(refresh_status.get("report_path") or ""),
        "policy_match_basis": str(matched.get("basis") or ""),
        "policy_operation_impact": operation,
    }


def _policy_summary(row: sqlite3.Row, matched: dict[str, object]) -> str:
    points = _json_list(row["policy_points_json"])
    impacts = _json_list(row["business_impacts_json"])
    summary = str(row["chinese_summary"] or "")
    pieces = [
        _compact_text(points[0] if points else summary, 72),
        _compact_text(impacts[0] if impacts else "", 72),
        f"匹配主题：{matched['theme']}；匹配对象：{matched['names']}",
    ]
    return "；".join(piece for piece in pieces if piece)


def _policy_operation_impact(
    impact: str,
    matched: dict[str, object],
    importance: int,
    refresh_status: dict[str, object],
    source_url: str,
) -> str:
    refresh = str(refresh_status.get("status") or "")
    if refresh not in {"refreshed", "cached_refreshed"}:
        return "政策链路未完成刷新：不把政策项作为新增买入依据，只保留风险权重。"
    if not _has_original_url(source_url):
        return "政策原文未完成核验：只作为风险背景，不提高买入分、买入金额或Volume。"
    if impact == "positive" and importance >= 90:
        return f"操作影响：{matched['theme']} 只提高研究优先级；账户、PFIOS和量价闸门未同时通过时Volume=0，通过后才进入候选上限重算。"
    if impact == "positive":
        return f"操作影响：{matched['theme']} 只增强观察优先级；不单独扩大Volume。"
    return f"操作影响：{matched['theme']} 维持观望或降额，直到行情和成交额同向。"


def _no_match_event(
    as_of: str,
    factors: list[dict[str, object]],
    refresh_status: dict[str, object],
    status_path: Path,
    request_path: Path,
) -> dict[str, str]:
    themes = "、".join(sorted({str(item.get("research_group") or item.get("industry") or "未分类") for item in factors})[:8])
    status = str(refresh_status.get("status") or "unknown")
    reason = str(refresh_status.get("reason") or "")
    return {
        "date": as_of,
        "event_time": "00:00 Asia/Shanghai",
        "type": "government_policy_bridge",
        "title": "政府文件解读系统未命中自选池高相关新政策",
        "summary": f"已提交主题：{themes}；桥接状态：{status}；{_compact_text(reason, 70)}",
        "impact": "neutral",
        "related_symbols": "",
        "industry": "政策背景",
        "source_name": "Government Policy Interpretation Bridge",
        "source_url": str(status_path),
        "policy_authority": "系统状态",
        "policy_importance_score": "0",
        "policy_bridge_status": status,
        "policy_original_fetch_status": "no_match",
        "policy_request_path": str(request_path),
        "policy_report_path": str(refresh_status.get("report_path") or ""),
        "policy_match_basis": "no_high_relevance_policy_match",
        "policy_operation_impact": "操作影响：不因缺少政策催化而扩大买入；既有卖出/风控逻辑不受影响。",
    }


def _theme_index(factors: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in factors:
        if str(item.get("exchange") or "") not in {"SSE", "SZSE", "SEHK", "US"}:
            continue
        theme = str(item.get("research_group") or item.get("industry") or "未分类")
        grouped.setdefault(theme, []).append(item)
    return grouped


def _keywords_for_themes(theme_index: dict[str, list[dict[str, object]]]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for theme, items in theme_index.items():
        tokens = set(_split_theme(theme))
        for token, values in THEME_ALIASES.items():
            if token in theme:
                tokens |= values
        for item in items:
            tokens |= set(_split_theme(str(item.get("name") or "")))
        mapping[theme] = {token for token in tokens if len(token) >= 2}
    return mapping


def _matched_theme(
    row: sqlite3.Row,
    theme_index: dict[str, list[dict[str, object]]],
    keywords: dict[str, set[str]],
) -> dict[str, object]:
    original_blob = " ".join(
        str(row[key] or "")
        for key in [
            "title",
            "primary_industry",
            "industry_bucket",
        ]
    )
    blob = " ".join(
        str(row[key] or "")
        for key in [
            "title",
            "primary_industry",
            "industry_bucket",
            "chinese_summary",
            "policy_points_json",
            "business_impacts_json",
        ]
    )
    best_theme = ""
    best_score = 0.0
    best_basis = ""
    for theme, tokens in keywords.items():
        items = theme_index.get(theme, [])
        hard_tokens = _hard_relevance_tokens(theme, items)
        original_hits = sorted(token for token in hard_tokens if token and token in original_blob)
        full_hard_hits = sorted(token for token in hard_tokens if token and token in blob)
        weak_hits = sorted(token for token in tokens if token and token not in BROAD_POLICY_TOKENS and token in blob)
        if not original_hits and len(full_hard_hits) < 2:
            continue
        if _is_generic_government_document(original_blob) and not original_hits:
            continue
        score = len(original_hits) * 4 + len(full_hard_hits) * 2 + len(weak_hits) * 0.5
        if score > best_score:
            best_theme = theme
            best_score = score
            best_basis = f"原文硬命中:{'、'.join(original_hits) or '无'}；全文硬命中:{'、'.join(full_hard_hits[:5]) or '无'}"
    if best_score <= 0:
        return {}
    items = theme_index.get(best_theme, [])
    names = "、".join(str(item.get("name") or item.get("symbol") or "") for item in items[:4])
    return {"theme": best_theme, "items": items, "names": names, "score": best_score, "basis": best_basis}


def _hard_relevance_tokens(theme: str, items: list[dict[str, object]]) -> set[str]:
    tokens = {token for token in _split_theme(theme) if token not in BROAD_POLICY_TOKENS}
    for alias_key, values in THEME_ALIASES.items():
        if alias_key in theme:
            tokens |= {value for value in values if value not in BROAD_POLICY_TOKENS}
    for item in items:
        tokens |= {token for token in _split_theme(str(item.get("name") or "")) if token not in BROAD_POLICY_TOKENS}
        symbol = str(item.get("symbol") or "")
        if symbol and not symbol.isdigit():
            tokens.add(symbol)
    return {token for token in tokens if len(token) >= 2}


def _is_generic_government_document(original_blob: str) -> bool:
    return any(term in original_blob for term in GENERIC_GOVERNMENT_TERMS)


def _is_low_value_policy_document(row: sqlite3.Row, as_of: str) -> bool:
    title = str(row["title"] or "")
    try:
        as_of_year = int(as_of[:4])
    except ValueError:
        as_of_year = 9999
    for ordinal, end_year in PLAN_END_YEAR_BY_ORDINAL.items():
        if ordinal in title and ("五年规划" in title or ordinal.endswith("五")) and as_of_year > end_year:
            return True
    return False


def _has_original_url(value: object) -> bool:
    url = str(value or "")
    if not url or "example.com" in url:
        return False
    return url.startswith("https://") or url.startswith("http://")


def _split_theme(value: str) -> list[str]:
    normalized = (
        value.replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
        .replace("ETF", " ")
        .replace("指数", " 指数 ")
    )
    return [token.strip() for token in normalized.split() if token.strip()]


def _json_list(value: object) -> list[str]:
    if not value:
        return []
    try:
        payload = json.loads(str(value))
    except json.JSONDecodeError:
        return [str(value)]
    if isinstance(payload, list):
        return [str(item) for item in payload]
    return [str(payload)]


def _date_time_parts(raw: str, fallback_date: str) -> tuple[str, str]:
    text = raw.replace("T", " ").replace("Z", "")
    date_part = fallback_date
    time_part = "00:00 Asia/Shanghai"
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        date_part = text[:10]
    if len(text) >= 16 and text[13] == ":":
        time_part = text[11:16] + " Asia/Shanghai"
    return date_part, time_part


def _latest_policy_report_path(root: Path) -> str:
    latest_json = root / "data" / "automation" / "latest_run.json"
    if latest_json.exists():
        try:
            payload = json.loads(latest_json.read_text(encoding="utf-8"))
            report_path = str(payload.get("report_path") or "")
            if report_path:
                return report_path
        except json.JSONDecodeError:
            pass
    reports = sorted(
        [
            path
            for pattern in ["*.pdf", "*.md", "*.html"]
            for path in (root / "reports").glob(pattern)
            if path.is_file()
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return str(reports[0]) if reports else ""


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.communicate(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    try:
        process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        pass


def _write_status(as_of: str, request_path: Path, refresh_status: dict[str, object], event_count: int) -> Path:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    path = STATUS_DIR / f"policy_bridge_status_{as_of}.json"
    payload = {
        "as_of": as_of,
        "updated_at": datetime.now().isoformat(),
        "policy_root": str(_policy_root()),
        "request_path": str(request_path),
        "refresh": refresh_status,
        "matched_event_count": event_count,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _recent_refresh_status(as_of: str) -> dict[str, object]:
    path = STATUS_DIR / f"policy_bridge_status_{as_of}.json"
    if not path.exists():
        return {}
    max_age_seconds = int(os.getenv("AI_RESEARCH_POLICY_CACHE_SECONDS", "7200"))
    age = datetime.now().timestamp() - path.stat().st_mtime
    if age > max_age_seconds:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    refresh = payload.get("refresh") or {}
    if not isinstance(refresh, dict):
        return {}
    status = str(refresh.get("status") or "")
    if status not in CONFIRMED_REFRESH_STATUSES:
        return {}
    return {**refresh, "status": "cached_refreshed", "reason": f"using policy bridge cache {path}"}


def _recent_policy_report_cache_status(as_of: str, reason: str) -> dict[str, object]:
    root = _policy_root()
    db_path = root / "data" / "policy_documents.sqlite"
    if not db_path.exists() or db_path.stat().st_size <= 0:
        return {}
    report_path = _latest_policy_report_path(root)
    if not report_path:
        return {}
    report = Path(report_path)
    if not _is_recent_cache_file(report):
        return {}
    return {
        "status": "cached_refreshed",
        "reason": f"{reason}; using verified policy DB/report cache for {as_of}: {report_path}",
        "report_path": report_path,
    }


def _is_recent_cache_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    max_age_seconds = int(os.getenv("AI_RESEARCH_POLICY_CACHE_SECONDS", "7200"))
    age = datetime.now().timestamp() - path.stat().st_mtime
    return age <= max_age_seconds


def _policy_root() -> Path:
    return Path(os.getenv("POLICY_SYSTEM_ROOT") or DEFAULT_POLICY_ROOT)


def _compact_text(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"
