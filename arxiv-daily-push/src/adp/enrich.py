"""元数据增强（R2）—— OpenAlex(pyalex) + Semantic Scholar 官方客户端.

合同：免费层、失败只降证据深度标记、绝不阻塞主干（功能清单·证据域）。
产出：enrichments 表一行 + 证据等级 摘要级 → 全文级（引用数/场馆/开放获取状态）。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from . import store

EVIDENCE_LEVEL_ABSTRACT = "摘要级"
EVIDENCE_LEVEL_FULL = "全文级"


def enrich_document(conn: sqlite3.Connection, doc_id: str, *, timeout: float = 10.0) -> dict[str, Any]:
    """对单篇文档做一次增强（每日仅选中篇，1+1 次免费 API 调用）；失败返回降级标记."""
    row = conn.execute(
        """SELECT d.stable_id, v.metadata_json FROM documents d
           JOIN doc_versions v ON v.doc_id = d.id
           WHERE d.id=? ORDER BY v.version_no DESC LIMIT 1""",
        (doc_id,),
    ).fetchone()
    if row is None:
        return {"ok": False, "degraded": ["enrich_doc_not_found"]}

    arxiv_id = row["stable_id"]
    degraded: list[str] = []
    payload: dict[str, Any] = {"arxiv_id": arxiv_id}

    payload["openalex"] = _try_openalex(arxiv_id, timeout, degraded)
    payload["semanticscholar"] = _try_semanticscholar(arxiv_id, timeout, degraded)

    level = EVIDENCE_LEVEL_FULL if (payload["openalex"] or payload["semanticscholar"]) else EVIDENCE_LEVEL_ABSTRACT
    payload["evidence_level"] = level
    conn.execute(
        "INSERT INTO enrichments (doc_id, payload_json, fetched_at) VALUES (?, ?, ?)",
        (doc_id, json.dumps(payload, ensure_ascii=False), store.utcnow_iso()),
    )
    conn.commit()
    return {"ok": True, "evidence_level": level, "degraded": degraded, "payload": payload}


def _try_openalex(arxiv_id: str, timeout: float, degraded: list[str]) -> dict[str, Any] | None:
    try:
        import pyalex

        pyalex.config.max_retries = 0
        work = pyalex.Works()[f"https://arxiv.org/abs/{arxiv_id}"]
        return {
            "openalex_id": work.get("id"),
            "cited_by_count": work.get("cited_by_count"),
            "is_retracted": bool(work.get("is_retracted")),
            "open_access": (work.get("open_access") or {}).get("oa_status"),
            "primary_topic": ((work.get("primary_topic") or {}).get("display_name")),
        }
    except Exception as exc:  # 任何失败（网络/404/限速）都只降级
        degraded.append(f"openalex_enrich_failed:{type(exc).__name__}")
        return None


def _try_semanticscholar(arxiv_id: str, timeout: float, degraded: list[str]) -> dict[str, Any] | None:
    try:
        from semanticscholar import SemanticScholar

        client = SemanticScholar(timeout=int(timeout))
        paper = client.get_paper(f"arXiv:{arxiv_id}",
                                 fields=["citationCount", "influentialCitationCount", "tldr",
                                         "externalIds", "publicationVenue"])
        return {
            "citation_count": paper.citationCount,
            "influential_citations": paper.influentialCitationCount,
            "tldr": (paper.tldr.text if paper.tldr else None),
            "venue": (paper.publicationVenue.name if paper.publicationVenue else None),
        }
    except Exception as exc:
        degraded.append(f"semanticscholar_enrich_failed:{type(exc).__name__}")
        return None


def latest_enrichment(conn: sqlite3.Connection, doc_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT payload_json FROM enrichments WHERE doc_id=? ORDER BY id DESC LIMIT 1", (doc_id,)
    ).fetchone()
    return json.loads(row["payload_json"]) if row else None
