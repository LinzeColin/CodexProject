from __future__ import annotations

import html
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit


CHROME_EPOCH_OFFSET_SECONDS = 11644473600
BILIBILI_HOST_KEYWORDS = ("bilibili.com", "b23.tv")
POLICY_RESEARCH_KEYWORDS = (
    "政策",
    "解读",
    "白皮书",
    "蓝皮书",
    "规划",
    "意见",
    "通知",
    "办法",
    "人工智能",
    "半导体",
    "芯片",
    "机器人",
    "算力",
    "数据中心",
    "云计算",
    "云上的中国",
    "化工",
    "新材料",
    "新能源",
    "智能汽车",
    "金融",
    "储能",
    "工业母机",
    "5g",
    "6g",
    "卫星互联网",
    "航空航天",
    "商业航天",
    "低空经济",
    "生物医药",
    "电网",
    "种业",
    "房地产",
    "城市更新",
    "交通物流",
    "数据要素",
    "数字经济",
    "国企改革",
    "平台经济",
    "财政税收",
    "政府债务",
    "双碳",
    "网络安全",
)


def build_chrome_bilibili_discovery(
    *,
    chrome_profile_dir: str | Path | None = None,
    history_file: str | Path | None = None,
    cookies_file: str | Path | None = None,
    limit: int = 30,
    keyword: str = "",
) -> dict[str, Any]:
    profile = Path(chrome_profile_dir).expanduser() if chrome_profile_dir else _default_chrome_profile_dir()
    history_path = Path(history_file).expanduser() if history_file else profile / "History"
    cookies_path = Path(cookies_file).expanduser() if cookies_file else profile / "Cookies"
    history = _inspect_history(history_path, limit=max(1, limit), keyword=keyword)
    cookies = _inspect_cookies(cookies_path)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chrome_profile": _path_label(profile),
        "history": history,
        "cookies": cookies,
        "summary": {
            "history_available": history["status"] == "ok",
            "cookie_db_available": cookies["status"] == "ok",
            "bilibili_history_count": history.get("total_count", 0),
            "bilibili_cookie_row_count": cookies.get("bilibili_cookie_row_count", 0),
            "latest_bilibili_visit_at": history.get("latest_visit_at", ""),
            "candidate_count": len(history.get("candidates") or []),
        },
        "next_actions": _next_actions(history, cookies),
        "security_boundary": (
            "只读取你授权的本机 Chrome History/Cookies SQLite 文件状态；输出仅包含脱敏统计和公开视频/搜索候选 URL。"
            "不输出 cookie 名称、cookie 值、账号密码、完整 Chrome 路径；不绕过验证码、付费墙、访问控制或平台禁止接口。"
        ),
    }


def write_chrome_bilibili_discovery_dashboard(
    path: str | Path,
    *,
    chrome_profile_dir: str | Path | None = None,
    history_file: str | Path | None = None,
    cookies_file: str | Path | None = None,
    limit: int = 30,
    keyword: str = "",
    title: str = "B站 Chrome 本地证据发现",
) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_chrome_bilibili_discovery(
        chrome_profile_dir=chrome_profile_dir,
        history_file=history_file,
        cookies_file=cookies_file,
        limit=limit,
        keyword=keyword,
    )
    output.write_text(render_chrome_bilibili_discovery_dashboard(report, title=title), encoding="utf-8")
    return str(output)


def render_chrome_bilibili_discovery_dashboard(report: dict[str, Any], *, title: str) -> str:
    summary = report.get("summary") or {}
    history = report.get("history") or {}
    cookies = report.get("cookies") or {}
    candidates = list(history.get("candidates") or [])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ --ink:#172033; --muted:#667085; --line:#d0d5dd; --paper:#f4f6f8; --panel:#fff; --teal:#0b6477; --green:#177245; --amber:#9a4a13; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--paper); font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif; line-height:1.5; }}
    .page {{ max-width:1180px; margin:0 auto; padding:24px 18px 48px; }}
    .hero {{ background:var(--panel); border-top:5px solid var(--teal); border-bottom:1px solid var(--line); padding:18px 0 16px; }}
    .hero h1 {{ margin:2px 0 8px; color:#063f4b; font-size:26px; line-height:1.25; }}
    .hero p {{ margin:0; color:var(--muted); }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border:1px solid var(--line); background:var(--panel); margin:14px 0; }}
    .metric {{ padding:10px 12px; border-right:1px solid var(--line); min-height:68px; }}
    .metric:last-child {{ border-right:0; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; color:#063f4b; font-size:20px; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); padding:13px 14px; margin-top:12px; }}
    .panel h2 {{ margin:0 0 10px; color:#063f4b; font-size:16px; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th,td {{ border:1px solid var(--line); padding:7px 8px; text-align:left; vertical-align:top; }}
    th {{ background:#edf4f7; color:#063f4b; }}
    td {{ background:#fff; overflow-wrap:anywhere; }}
    .ok {{ color:var(--green); font-weight:700; }}
    .warn {{ color:var(--amber); font-weight:700; }}
    @media (max-width:800px) {{ .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} table {{ font-size:11px; }} }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p>Chrome Local Evidence Discovery</p>
      <h1>{html.escape(title)}</h1>
      <p>Profile：{html.escape(str(report.get("chrome_profile") or ""))}｜不展示 cookie、账号密码或完整本地路径。</p>
    </section>
    <section class="metrics">
      {_metric("History", "ok" if summary.get("history_available") else "blocked")}
      {_metric("B站历史记录", summary.get("bilibili_history_count", 0))}
      {_metric("候选 URL", summary.get("candidate_count", 0))}
      {_metric("Cookie DB", "ok" if summary.get("cookie_db_available") else "blocked")}
      {_metric("B站 cookie 行", summary.get("bilibili_cookie_row_count", 0))}
    </section>
    <article class="panel"><h2>状态</h2><table><tbody>
      <tr><th>最近 B站访问</th><td>{html.escape(str(summary.get("latest_bilibili_visit_at") or ""))}</td></tr>
      <tr><th>History 状态</th><td class="{_status_class(str(history.get("status") or ""))}">{html.escape(str(history.get("status") or ""))}</td></tr>
      <tr><th>Cookie DB 状态</th><td class="{_status_class(str(cookies.get("status") or ""))}">{html.escape(str(cookies.get("status") or ""))}</td></tr>
    </tbody></table></article>
    {_candidate_panel(candidates)}
    {_next_action_panel(report.get("next_actions") or [])}
    <article class="panel"><h2>安全与合规边界</h2><p>{html.escape(str(report.get("security_boundary") or ""))}</p></article>
  </main>
</body>
</html>
"""


def _inspect_history(path: Path, *, limit: int, keyword: str) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing_file", "path_label": "<chrome_history>", "total_count": 0, "candidates": []}
    query = """
        SELECT urls.url, urls.title, urls.visit_count, urls.last_visit_time
        FROM urls
        WHERE urls.url LIKE '%bilibili.com%' OR urls.url LIKE '%b23.tv%'
        ORDER BY urls.last_visit_time DESC
        LIMIT ?
    """
    try:
        rows = _query_sqlite_copy(path, query, (max(limit * 10, 100),))
    except Exception as exc:  # pragma: no cover - exact SQLite lock errors vary by platform.
        return {
            "status": "read_failed",
            "path_label": "<chrome_history>",
            "error_class": exc.__class__.__name__,
            "total_count": 0,
            "candidates": [],
        }
    filtered = [_history_candidate(row) for row in rows]
    if keyword:
        key = keyword.casefold()
        filtered = [
            item
            for item in filtered
            if key in str(item.get("title", "")).casefold() or key in str(item.get("url", "")).casefold()
        ]
    candidate_pool = [
        item
        for item in filtered
        if item.get("kind") in {"video", "search", "article", "space"} and _is_policy_relevant(item)
    ]
    candidates = _dedupe_candidates(candidate_pool)[:limit]
    latest = filtered[0]["last_visit_at"] if filtered else ""
    return {
        "status": "ok",
        "path_label": "<chrome_history>",
        "total_count": len(filtered),
        "latest_visit_at": latest,
        "candidates": candidates,
    }


def _inspect_cookies(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing_file", "path_label": "<chrome_cookies>", "bilibili_cookie_row_count": 0}
    query = "SELECT COUNT(*) FROM cookies WHERE host_key LIKE ?"
    try:
        rows = _query_sqlite_copy(path, query, ("%bilibili.com",))
    except Exception as exc:  # pragma: no cover - exact SQLite lock errors vary by platform.
        return {
            "status": "read_failed",
            "path_label": "<chrome_cookies>",
            "error_class": exc.__class__.__name__,
            "bilibili_cookie_row_count": 0,
        }
    count = int(rows[0][0]) if rows else 0
    return {
        "status": "ok",
        "path_label": "<chrome_cookies>",
        "bilibili_cookie_row_count": count,
        "cookie_values_exported": False,
    }


def _query_sqlite_copy(path: Path, query: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
    with tempfile.TemporaryDirectory() as tmp:
        copied = Path(tmp) / path.name
        shutil.copy2(path, copied)
        conn = sqlite3.connect(copied)
        conn.row_factory = sqlite3.Row
        try:
            return list(conn.execute(query, params))
        finally:
            conn.close()


def _history_candidate(row: sqlite3.Row) -> dict[str, Any]:
    url = str(row["url"] or "")
    title = str(row["title"] or "").strip()
    return {
        "url": _sanitize_bilibili_url(url),
        "title": title[:120],
        "kind": _url_kind(url),
        "relevance": _relevance(title, url),
        "visit_count": int(row["visit_count"] or 0),
        "last_visit_at": _chrome_time_to_iso(int(row["last_visit_time"] or 0)),
    }


def _sanitize_bilibili_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.lower()
    path = parts.path
    if "bilibili.com" not in host and "b23.tv" not in host:
        return ""
    if "/video/" in path or path.startswith("/video/"):
        return f"{parts.scheme}://{host}{path}"
    if path.startswith("/read/"):
        return f"{parts.scheme}://{host}{path}"
    if path.startswith("/opus/"):
        return f"{parts.scheme}://{host}{path}"
    if path.startswith("/space/"):
        return f"{parts.scheme}://{host}{path}"
    if host.startswith("search.") or path.startswith("/search"):
        query = parse_qs(parts.query)
        keyword = (query.get("keyword") or query.get("q") or [""])[0]
        return f"{parts.scheme}://{host}{path}?keyword={keyword}" if keyword else f"{parts.scheme}://{host}{path}"
    return f"{parts.scheme}://{host}{path}"


def _url_kind(url: str) -> str:
    path = urlsplit(url).path
    if "/video/" in path or path.startswith("/video/"):
        return "video"
    host = urlsplit(url).netloc.lower()
    if host.startswith("search.") or path.startswith("/search"):
        return "search"
    if path.startswith("/read/") or path.startswith("/opus/"):
        return "article"
    if path.startswith("/space/"):
        return "space"
    return "other"


def _chrome_time_to_iso(value: int) -> str:
    if value <= 0:
        return ""
    timestamp = (value / 1_000_000) - CHROME_EPOCH_OFFSET_SECONDS
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def _default_chrome_profile_dir() -> Path:
    return Path("~/Library/Application Support/Google/Chrome/Default").expanduser()


def _path_label(path: Path) -> str:
    return "<chrome_default_profile>" if path == _default_chrome_profile_dir() else "<chrome_profile>"


def _next_actions(history: dict[str, Any], cookies: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if history.get("status") == "ok" and history.get("candidates"):
        actions.append(
            {
                "priority": 90,
                "action": "review_bilibili_candidates",
                "label": "从候选 B站公开 URL 中筛选政策解读参考，进入外部参考队列。",
            }
        )
    if int(cookies.get("bilibili_cookie_row_count") or 0) > 0:
        actions.append(
            {
                "priority": 85,
                "action": "optional_cookie_export",
                "label": "如需直接采集，使用受控本地导出把 B站 cookie 写入私有文件；不要在聊天中粘贴。",
            }
        )
    actions.append(
        {
            "priority": 80,
            "action": "add_search_api",
            "label": "补至少一个搜索 API key，否则全网召回仍是 P0 blocker。",
        }
    )
    return actions


def _is_policy_relevant(item: dict[str, Any]) -> bool:
    return int(item.get("relevance") or 0) > 0


def _relevance(title: str, url: str) -> int:
    text = f"{title} {url}".casefold()
    return sum(1 for keyword in POLICY_RESEARCH_KEYWORDS if keyword.casefold() in text)


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in candidates:
        key = str(item.get("url") or "").rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _candidate_panel(candidates: list[dict[str, Any]]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(item.get('kind') or ''))}</td>"
        f"<td>{html.escape(str(item.get('title') or ''))}</td>"
        f"<td>{html.escape(str(item.get('url') or ''))}</td>"
        f"<td>{html.escape(str(item.get('relevance') or 0))}</td>"
        f"<td>{html.escape(str(item.get('last_visit_at') or ''))}</td>"
        f"<td>{html.escape(str(item.get('visit_count') or 0))}</td>"
        "</tr>"
        for item in candidates
    )
    if not rows:
        rows = "<tr><td colspan=\"5\">暂无候选 URL。</td></tr>"
    return (
        "<article class=\"panel\"><h2>候选公开 URL</h2><table><thead><tr>"
        "<th>类型</th><th>标题</th><th>URL</th><th>相关度</th><th>最近访问</th><th>次数</th>"
        "</tr></thead><tbody>"
        + rows
        + "</tbody></table></article>"
    )


def _next_action_panel(actions: list[dict[str, Any]]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(item.get('priority') or ''))}</td>"
        f"<td>{html.escape(str(item.get('action') or ''))}</td>"
        f"<td>{html.escape(str(item.get('label') or ''))}</td>"
        "</tr>"
        for item in actions
    )
    return (
        "<article class=\"panel\"><h2>下一步</h2><table><thead><tr>"
        "<th>优先级</th><th>动作</th><th>说明</th>"
        "</tr></thead><tbody>"
        + rows
        + "</tbody></table></article>"
    )


def _metric(label: str, value: object) -> str:
    return f"<div class=\"metric\"><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong></div>"


def _status_class(status: str) -> str:
    return "ok" if status == "ok" else "warn"
