from __future__ import annotations

import re
from typing import Any, Mapping

from .analyzer import INDUSTRY_RULES, MAJOR_KEYWORDS
from .content_db import all_documents, mark_report_skipped, queued_reports, upsert_report_queue_item
from .industry import (
    DEFAULT_INDUSTRY_NAME,
    DEFAULT_INDUSTRY_RANK,
    IndustryConfig,
    classify_document_industry,
    document_is_since,
    document_sort_time,
    load_industry_config,
)


LEVEL_RANK = {
    "national": 0,
    "central": 0,
    "ministry": 1,
    "provincial": 2,
    "province": 2,
    "municipal": 3,
    "city": 3,
    "county": 4,
    "district": 4,
    "local": 5,
}


def sync_report_queue(
    conn,
    source_conn,
    run_id: str,
    analysis_mode: str,
    industry_config_path=None,
    document_since: str | None = None,
) -> int:
    industry_config = load_industry_config(industry_config_path)
    cutoff = document_since or industry_config.default_since
    source_meta = _source_metadata(source_conn)
    count = 0
    for document in all_documents(conn):
        if not document_is_since(document, cutoff):
            mark_report_skipped(conn, document["document_id"], analysis_mode)
            continue
        if _is_index_or_listing_document(document):
            mark_report_skipped(conn, document["document_id"], analysis_mode)
            continue
        meta = source_meta.get(str(document.get("source_id") or ""), {})
        industry_rank, industry = _primary_industry(document, industry_config)
        level = str(meta.get("administrative_level") or "unknown")
        upsert_report_queue_item(
            conn,
            {
                "document_id": document["document_id"],
                "analysis_mode": analysis_mode,
                "primary_industry": industry,
                "industry_bucket": industry,
                "industry_rank": industry_rank,
                "administrative_level": level,
                "level_rank": LEVEL_RANK.get(level, 99),
                "sort_time": document_sort_time(document),
                "priority_score": _priority_score(document),
                "first_queued_run_id": run_id,
            },
        )
        count += 1
    return count


def _is_index_or_listing_document(document: Mapping[str, Any]) -> bool:
    title = str(document.get("title") or "").strip()
    canonical_url = str(document.get("canonical_url") or document.get("url") or "").rstrip("/")
    source_url = str(document.get("source_url") or "").rstrip("/")
    if canonical_url and source_url and canonical_url == source_url:
        return True
    generic_titles = {
        "文件库",
        "政策文件",
        "政策文件栏目",
        "省政府公报",
        "政府公报",
        "最新动态",
        "最新政策",
        "政策",
        "政策解读",
        "公示公告",
        "公报",
        "国务院公报",
        "惠企助企政策集纳查询",
        "粤企政策通",
        "政府工作报告",
    }
    if title in generic_titles:
        return True
    return bool(re.search(r"(政策文件栏目|文件库|政府公报|省政府公报|欢迎你@国务院|^[\u4e00-\u9fff]\s+[\u4e00-\u9fff]$)", title))


def next_report_queue_item(conn, analysis_mode: str) -> dict[str, Any] | None:
    items = queued_reports(conn, analysis_mode, limit=1)
    return items[0] if items else None


def queue_preview(conn, analysis_mode: str, limit: int = 12) -> list[dict[str, Any]]:
    return queued_reports(conn, analysis_mode, limit=limit)


def _source_metadata(source_conn) -> dict[str, dict[str, Any]]:
    rows = source_conn.execute(
        """
        SELECT source_id, administrative_level, source_type, region, effective_score
        FROM source_authority_current
        """
    ).fetchall()
    return {row["source_id"]: dict(row) for row in rows}


def _primary_industry(document: Mapping[str, Any], industry_config: IndustryConfig | None = None) -> tuple[int, str]:
    if industry_config and industry_config.rules:
        return classify_document_industry(document, industry_config)
    text = " ".join(
        str(document.get(key) or "")
        for key in ("title", "text_excerpt", "source_name")
    )
    for label, keywords in INDUSTRY_RULES:
        if any(keyword in text for keyword in keywords):
            return DEFAULT_INDUSTRY_RANK, label
    return DEFAULT_INDUSTRY_RANK, DEFAULT_INDUSTRY_NAME


def _priority_score(document: Mapping[str, Any]) -> int:
    text = " ".join(
        str(document.get(key) or "")
        for key in ("title", "text_excerpt", "source_name")
    )
    authority = int(document.get("authority_score_snapshot") or 0)
    keyword_bonus = sum(4 for keyword in MAJOR_KEYWORDS if keyword in text)
    recency_bonus = 8 if re.search(r"十五五|2026|2025", text) else 0
    return min(100, authority + keyword_bonus + recency_bonus)
