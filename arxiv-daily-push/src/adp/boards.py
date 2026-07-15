"""板块二～五（J4）——注册表加载、RSS 抓取、雷达聚合.

Owner 指令（2026-07-15）：板块二～五上线，每板块数据源透明可见。
边界：板块二～四是「雷达浏览流」（真实抓取 + 雷达可见 + 来源健康纳管），
**不进入每日精选候选池**——池整合与多样性 10→17 是独立提案（任务包 R5 明文）。
故障模型：任一来源抓取失败只降级（health 记账，连续 3 次自动停用），永不阻塞闭环。
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from . import config, store

FEED_TIMEOUT_SECONDS = 20
USER_AGENT = "ADP/0.3 personal-learning (single-user; contact: owner)"
MAX_ITEMS_PER_FETCH = 30

_SCHEMA = """
CREATE TABLE IF NOT EXISTS board_items (
  id TEXT PRIMARY KEY,            -- sha1(source_id + entry link/guid)
  board_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  published_at TEXT,              -- 源声明时间（缺失容忍）
  fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_board_items_board ON board_items (board_id, fetched_at DESC);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)


def registry_path():
    return config.PROJECT_ROOT / "config" / "boards_v0_3.yaml"


def load_registry() -> dict[str, Any]:
    import yaml

    raw = yaml.safe_load(registry_path().read_text(encoding="utf-8"))
    boards = raw.get("boards") or []
    ids = [b["id"] for b in boards]
    if len(ids) != len(set(ids)) or len(boards) != 5:
        raise ValueError("boards registry must define exactly 5 uniquely-named boards")
    # 源 id 必须全局唯一：三处 keyspace（报表键/健康行 rss:<id>/item sha1）都用裸 id
    source_ids = [s["id"] for b in boards for s in (b.get("sources") or [])]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("boards registry source ids must be globally unique")
    return raw


def _safe_url(link: str) -> str | None:
    """只接受 http/https——外部 feed 可能塞 javascript:/data: 链接，
    Jinja 自动转义防不了 href 里的协议（复审确认的存储型注入面）。"""
    from urllib.parse import urlparse

    try:
        scheme = urlparse(link).scheme.lower()
    except ValueError:
        return None
    return link if scheme in ("http", "https") else None


def _entry_time(entry: Any, *, not_after: str) -> str | None:
    """源声明时间；晚于抓取时刻的（未来日期）丢弃——否则会永久钉在列表顶部（复审确认）。"""
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None) or (entry.get(key) if isinstance(entry, dict) else None)
        if t:
            iso = datetime(*t[:6], tzinfo=timezone.utc).isoformat(timespec="seconds")
            return iso if iso <= not_after else None
    return None


def ingest_feed_entries(conn: sqlite3.Connection, board_id: str, source: dict[str, Any],
                        parsed: Any) -> int:
    """入 board_items（幂等：同源同链接只此一条）；返回新增条数."""
    new_count = 0
    now = store.utcnow_iso()
    for entry in list(parsed.entries)[:MAX_ITEMS_PER_FETCH]:
        link = _safe_url((entry.get("link") or "").strip())
        title = " ".join((entry.get("title") or "").split())
        if not link or not title:
            continue
        item_id = hashlib.sha1(f"{source['id']}|{entry.get('id') or link}".encode()).hexdigest()
        summary = " ".join((entry.get("summary") or "").split())[:500]
        cursor = conn.execute(
            """INSERT OR IGNORE INTO board_items
               (id, board_id, source_id, title, url, summary, published_at, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_id, board_id, source["id"], title[:300], link, summary,
             _entry_time(entry, not_after=now), now))
        new_count += cursor.rowcount
    return new_count


def _download_feed(feed_url: str) -> Any:
    """自带超时下载再解析（feedparser.parse(url) 无超时，单源挂起会卡死每日 run）；
    网络 I/O 在此完成，写库不与之交叠（复审确认：避免 WAL 写事务横跨全部网络请求）。"""
    import urllib.request

    import feedparser

    req = urllib.request.Request(feed_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FEED_TIMEOUT_SECONDS) as resp:
        body = resp.read(8 * 1024 * 1024)  # 8MB 上限防喂食超大响应
    parsed = feedparser.parse(body)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"feed unparsable ({type(parsed.bozo_exception).__name__})")
    if not parsed.entries:
        raise ValueError("feed empty")
    return parsed


def fetch_board_feeds(conn: sqlite3.Connection) -> dict[str, Any]:
    """抓取所有 rss 来源；逐源独立成败，健康入账，报表落 data/boards_fetch_report.json.

    每源：先注册+提交（短事务）→ 网络下载（无事务）→ 入库+健康+提交（短事务）。
    已被连续失败自动停用（disabled_auto）的源跳过抓取（kill switch 真正生效），
    仅在雷达页显示为停用；Owner 修好后手动清零健康即恢复。
    """
    ensure_schema(conn)
    registry = load_registry()
    report: dict[str, Any] = {"at": store.utcnow_iso(), "sources": {}}
    for board in registry["boards"]:
        for source in board.get("sources") or []:
            if source.get("method") != "rss":
                continue
            sid = f"rss:{source['id']}"
            store.upsert_source(conn, source_id=sid, board_id=board["id"],
                                name=source["name"], policy_snapshot={
                                    "platform": source.get("platform"),
                                    "website": source.get("website"),
                                    "official": bool(source.get("official"))})
            conn.commit()  # 注册落库后即释放写锁，网络 I/O 不再持有 WAL 写槽
            health_row = conn.execute(
                "SELECT health FROM sources WHERE id=?", (sid,)).fetchone()
            if health_row and health_row["health"] == "disabled_auto":
                report["sources"][source["id"]] = {"ok": False, "skipped": "disabled_auto"}
                continue
            try:
                parsed = _download_feed(source["feed_url"])          # 网络（无事务）
                new_count = ingest_feed_entries(conn, board["id"], source, parsed)  # 写
                store.record_source_health(conn, sid, ok=True)
                conn.commit()
                report["sources"][source["id"]] = {"ok": True, "new": new_count,
                                                   "entries": len(parsed.entries)}
            except Exception as exc:  # 单源失败只降级：健康记账，不碰其他源
                health = store.record_source_health(conn, sid, ok=False)
                conn.commit()
                report["sources"][source["id"]] = {"ok": False, "health": health,
                                                   "error": f"{type(exc).__name__}: {exc}"[:200]}
    (config.data_dir() / "boards_fetch_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def board_overview(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """雷达页数据：每板块状态 + 数据源明细（平台/网站/健康/近30天条数）+ 最新条目."""
    ensure_schema(conn)
    registry = load_registry()
    overview: list[dict[str, Any]] = []
    for board in registry["boards"]:
        sources = []
        for source in board.get("sources") or []:
            # rss 源计数看 board_items；api 源（精选闭环）计数看 documents 主库
            sid = f"rss:{source['id']}" if source.get("method") == "rss" else source.get("doc_source_id")
            health_row = conn.execute(
                "SELECT health, consecutive_failures FROM sources WHERE id=?", (sid,)
            ).fetchone() if sid else None
            if source.get("doc_source_id"):
                stats = conn.execute(
                    """SELECT COUNT(*) AS n, MAX(first_seen_at) AS last_fetch
                       FROM documents WHERE source_id=?""", (source["doc_source_id"],)).fetchone()
            else:
                stats = conn.execute(
                    """SELECT COUNT(*) AS n, MAX(fetched_at) AS last_fetch
                       FROM board_items WHERE source_id=?""", (source["id"],)).fetchone()
            sources.append({**source,
                            "health": (health_row["health"] if health_row else "—"),
                            "failures": (health_row["consecutive_failures"] if health_row else 0),
                            "items_total": stats["n"] if stats else 0,
                            "last_fetch": (stats["last_fetch"] or "尚未抓取") if stats else "尚未抓取"})
        items = [dict(r) for r in conn.execute(
            """SELECT b.title, b.url, b.source_id, b.published_at, b.fetched_at
               FROM board_items b WHERE b.board_id=?
               ORDER BY COALESCE(b.published_at, b.fetched_at) DESC LIMIT 6""",
            (board["id"],))]
        # 短标签给雷达页快捷导航用（模板不再 split('·')[1]，防名称无分隔符时 500）
        short = board["name"].replace(" ", "").replace("·", " · ")
        overview.append({**board, "short": short, "sources": sources, "items": items})
    # 板块五：聚合板块二～四浏览流（board_items 不含 board1——arXiv 是 api 源，
    # 走精选闭环有自己的今天/队列页）。按 status 定位，不假设它排在末位。
    for agg in overview:
        if agg.get("status") == "aggregate":
            agg["items"] = [dict(r) for r in conn.execute(
                """SELECT b.title, b.url, b.source_id, b.board_id, b.published_at, b.fetched_at
                   FROM board_items b ORDER BY COALESCE(b.published_at, b.fetched_at) DESC LIMIT 10""")]
            agg["counts"] = {row["board_id"]: row["n"] for row in conn.execute(
                "SELECT board_id, COUNT(*) AS n FROM board_items GROUP BY board_id")}
    return overview
