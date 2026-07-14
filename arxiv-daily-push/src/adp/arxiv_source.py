"""发现环节 —— 复用既有 arxiv_adapter（成熟项目替代决策 #2：保留）+ 政策快照.

真实网络抓取只在显式调用时发生；原始 Atom 快照落 data/raw/（本地私有）。
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from arxiv_daily_push.arxiv_adapter import ArxivQuery, fetch_atom, parse_atom_feed

from . import config, store
from .claims import extract_claims, store_claims

SOURCE_ID = "SRC-ARXIV"
BOARD_ID = "B1"
# 兴趣画像映射的抓取类目（features.INTEREST_CATEGORIES 的抓取侧子集，控制请求量）
FETCH_CATEGORIES = ("cs.AI", "cs.LG", "cs.CL", "q-bio.QM", "q-fin.GN", "eess.SY")
POLICY_SNAPSHOT = {
    "api": "https://export.arxiv.org/api/query",
    "terms": "https://info.arxiv.org/help/api/index.html",
    "rate_limit": "1 request / 3 seconds, single connection",
    "verified_at": "2026-07-14",
    "acknowledgement": "Thank you to arXiv for use of its open access interoperability.",
}


def ensure_source(conn: sqlite3.Connection) -> None:
    store.upsert_source(conn, source_id=SOURCE_ID, board_id=BOARD_ID,
                        name="arXiv Atom API", policy_snapshot=POLICY_SNAPSHOT)


def fetch_window(conn: sqlite3.Connection, *, days: int = 1, as_of: datetime | None = None,
                 max_per_category: int = 50, sleep_seconds: float = 3.0,
                 raw_dir: Path | None = None) -> dict[str, Any]:
    """抓取增量：按类目查询提交窗口内条目 → 去重/版本链 → 声明抽取.

    返回计数 dict（进 run manifest）。网络失败记来源健康事件，不抛出。
    """
    ensure_source(conn)
    as_of = as_of or datetime.now(timezone.utc)
    start = as_of - timedelta(days=days)
    window = f"[{start.strftime('%Y%m%d%H%M')} TO {as_of.strftime('%Y%m%d%H%M')}]"
    raw_dir = raw_dir or (config.data_dir() / "raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    counts = {"扫描": 0, "新文档": 0, "新版本": 0, "新声明": 0, "抓取失败类目": 0}
    retrieved_at = as_of.isoformat(timespec="seconds")
    degraded: list[str] = []
    for category in FETCH_CATEGORIES:
        query = ArxivQuery(
            search_query=f"cat:{category} AND submittedDate:{window}",
            max_results=max_per_category,
        )
        try:
            xml_text = fetch_atom(query)
        except Exception as exc:  # 网络/API 失败 → 来源健康事件，降级不阻塞
            counts["抓取失败类目"] += 1
            degraded.append(f"arxiv_fetch_failed:{category}:{type(exc).__name__}")
            store.record_source_health(conn, SOURCE_ID, ok=False)
            continue
        snapshot = raw_dir / f"arxiv-{category.replace('.', '_')}-{as_of.strftime('%Y%m%dT%H%M%SZ')}.xml"
        snapshot.write_text(xml_text, encoding="utf-8")
        try:
            items = parse_atom_feed(xml_text, retrieved_at=retrieved_at)
        except Exception as exc:
            counts["抓取失败类目"] += 1
            degraded.append(f"arxiv_parse_failed:{category}:{type(exc).__name__}")
            store.record_source_health(conn, SOURCE_ID, ok=False)
            continue
        store.record_source_health(conn, SOURCE_ID, ok=True)
        counts["扫描"] += len(items)
        for item in items:
            doc_id, version_id, new_doc, new_version = store.ingest_document(conn, item)
            counts["新文档"] += int(new_doc)
            counts["新版本"] += int(new_version)
            if new_version:
                abstract = item["metadata"]["arxiv"].get("summary") or ""
                counts["新声明"] += store_claims(conn, extract_claims(version_id, abstract))
        if sleep_seconds:
            time.sleep(sleep_seconds)  # arXiv API 礼貌间隔（政策快照 rate_limit）
    conn.commit()
    counts["降级项"] = degraded  # type: ignore[assignment]
    return counts


def candidates_for_date(conn: sqlite3.Connection, as_of_date: str, *, window_days: int = 7) -> list[dict[str, Any]]:
    """构建某日候选池：窗口内的最新版本文档（含元数据），供硬门+打分。"""
    rows = conn.execute(
        """SELECT v.*, d.canonical_url, d.title, d.stable_id
           FROM doc_versions v JOIN documents d ON d.id = v.doc_id
           WHERE v.id IN (SELECT id FROM doc_versions v2 WHERE v2.doc_id = v.doc_id
                          ORDER BY v2.version_no DESC LIMIT 1)
             AND date(substr(v.published_at, 1, 10)) >= date(?, ?)
             AND date(substr(v.published_at, 1, 10)) <= date(?)
           ORDER BY v.published_at DESC""",
        (as_of_date, f"-{window_days} days", as_of_date),
    ).fetchall()
    out = []
    for row in rows:
        meta = json.loads(row["metadata_json"])
        out.append({
            "doc_id": row["doc_id"],
            "doc_version_id": row["id"],
            "version_no": row["version_no"],
            "stable_id": row["stable_id"],
            "title": row["title"],
            "canonical_url": row["canonical_url"],
            "source_id": row["doc_id"],
            "source_type": "arxiv",
            "metadata": {"arxiv": meta},
            "license": {"status": "unknown", "usage": "private_learning_link_only"},
        })
    return out
