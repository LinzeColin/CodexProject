"""R5 · bioRxiv 生物预印本影子源 —— 三步晋升的机器面.

复用 legacy preprint_adapter（成熟项目替代决策：已验收的官方 details API 适配器）。
影子期**零入库**：候选只在内存评估、结果只进影子报表（data/shadow_biorxiv_report.json），
结构上保证对主线零干扰；Owner 点「应用上板」后才开始真实入库参选。
kill switch = sources 表健康（连续 3 次失败自动停用）+ promoted meta 键。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from arxiv_daily_push.preprint_adapter import (PreprintQuery, fetch_preprint_details,
                                               parse_preprint_details)

from . import config, store
from .config import Thresholds

SOURCE_ID = "SRC-BIORXIV"
PROMOTED_META_KEY = "source_biorxiv_promoted"
POLICY_SNAPSHOT = {
    "api": "https://api.biorxiv.org/details/biorxiv",
    "terms": "https://api.biorxiv.org/",
    "rate_limit": "public JSON API, paginated by 100",
    "verified_at": "2026-07-15",
}


def ensure_source(conn: sqlite3.Connection) -> None:
    store.upsert_source(conn, source_id=SOURCE_ID, board_id="B1",
                        name="bioRxiv preprints (shadow)", policy_snapshot=POLICY_SNAPSHOT)


def is_promoted(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (PROMOTED_META_KEY,)).fetchone()
    return bool(row and row["value"] == "true")


def map_to_candidate(item: dict[str, Any]) -> dict[str, Any]:
    """preprint SourceItem → adp 候选形状（metadata.arxiv 键位映射，特征/硬门可直接复用）."""
    pre = item["metadata"]["preprint"]
    published = pre.get("date") or ""
    return {
        "doc_id": f"biorxiv:{pre['doi']}",
        "doc_version_id": f"biorxiv:{pre['doi']}#v{pre.get('version') or 1}",
        "version_no": int(pre.get("version") or 1),
        "stable_id": pre["doi"],
        "title": item["title"],
        "canonical_url": item["canonical_url"],
        "source_id": SOURCE_ID,
        "source_type": "biorxiv",
        "metadata": {"arxiv": {
            "versioned_id": f"{pre['doi']}v{pre.get('version') or 1}",
            "primary_category": f"bio.{(pre.get('category') or 'general').replace(' ', '_')}",
            "categories": [f"bio.{(pre.get('category') or 'general').replace(' ', '_')}", "q-bio.QM"],
            "published": f"{published}T00:00:00Z" if published else "",
            "updated": f"{published}T00:00:00Z" if published else "",
            "authors": pre.get("authors") or [],
            "summary": pre.get("abstract") or "",
            "comment": "", "journal_ref": pre.get("published") or "",
            "doi": pre.get("doi") or "",
        }},
        "license": {"status": pre.get("license") or "unknown",
                    "usage": "private_learning_link_only"},
    }


def fetch_day(day: str, *, max_records: int = 100) -> list[dict[str, Any]]:
    """抓取某真实日期的 bioRxiv 收录（details API interval=当日）。异常上抛由调用方降级."""
    query = PreprintQuery(server="biorxiv", interval=f"{day}/{day}")
    text = fetch_preprint_details(query, timeout=25.0)
    items = parse_preprint_details(text, server="biorxiv",
                                   retrieved_at=store.utcnow_iso(), max_records=max_records)
    return [map_to_candidate(i) for i in items if i["metadata"]["preprint"].get("abstract")]


def shadow_day(conn: sqlite3.Connection, day: str, thresholds: Thresholds,
               *, as_of: datetime | None = None) -> dict[str, Any] | None:
    """单日影子评估：bioRxiv 候选按同一套硬门+特征打分，与主线当日头名对照（零入库）."""
    from .selection import build_context, evaluate_candidates

    as_of = as_of or datetime.now(timezone.utc)
    try:
        candidates = fetch_day(day)
        store.record_source_health(conn, SOURCE_ID, ok=True)
    except Exception as exc:
        health = store.record_source_health(conn, SOURCE_ID, ok=False)
        conn.commit()
        return {"date": day, "error": f"{type(exc).__name__}", "source_health": health}
    if not candidates:
        return {"date": day, "candidates": 0, "passed": 0, "note": "当日无带摘要的收录"}

    context = build_context(conn, as_of=as_of)
    scored, rejected = evaluate_candidates(
        candidates, context, thresholds,
        gate_context={"seen_version_ids": set(), "source_health": "active"},
    )
    main = conn.execute(
        """SELECT s.score, s.abstain FROM selections s
           JOIN (SELECT as_of_date, MAX(run_id) m FROM selections GROUP BY as_of_date) l
             ON l.as_of_date = s.as_of_date AND l.m = s.run_id
           WHERE s.as_of_date = ?""",
        (day,),
    ).fetchone()
    top = scored[0] if scored else None
    return {
        "date": day,
        "candidates": len(candidates),
        "passed": len(scored),
        "rejected": len(rejected),
        "shadow_top": top["candidate"]["title"][:80] if top else None,
        "shadow_top_category": top["candidate"]["metadata"]["arxiv"]["primary_category"] if top else None,
        "shadow_score": top["score"] if top else None,
        "main_score": main["score"] if main else None,
        "main_abstain": bool(main["abstain"]) if main else None,
        "would_flip_top": bool(top and main and not main["abstain"]
                               and top["score"] > (main["score"] or 0)),
        "above_abstain_line": bool(top and top["score"] >= thresholds.abstain_threshold),
    }


def report_path():
    return config.data_dir() / "shadow_biorxiv_report.json"


def shadow_backfill(conn: sqlite3.Connection, thresholds: Thresholds, *, days: int = 14,
                    as_of: datetime | None = None) -> dict[str, Any]:
    """两周影子报表（真实数据回填，不因等待时间延迟——Owner 交付制先例）."""
    ensure_source(conn)
    as_of = as_of or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for offset in range(days, 0, -1):
        day = (as_of - timedelta(days=offset)).strftime("%Y-%m-%d")
        row = shadow_day(conn, day, thresholds, as_of=as_of)
        if row:
            rows.append(row)
    ok_rows = [r for r in rows if "error" not in r and r.get("candidates")]
    report = {
        "source": SOURCE_ID,
        "generated_at": as_of.isoformat(timespec="seconds"),
        "window_days": days,
        "days_with_data": len(ok_rows),
        "fetch_errors": sum(1 for r in rows if "error" in r),
        "total_candidates": sum(r.get("candidates", 0) for r in ok_rows),
        "days_above_abstain_line": sum(1 for r in ok_rows if r.get("above_abstain_line")),
        "days_would_flip_top": sum(1 for r in ok_rows if r.get("would_flip_top")),
        "promoted": is_promoted(conn),
        "proposal": proposal_summary(),
        "rows": rows,
    }
    report_path().write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def load_report() -> dict[str, Any] | None:
    path = report_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def proposal_summary() -> dict[str, Any]:
    """上板提案（预览内容；应用动作只能由 Owner 点击触发）."""
    return {
        "action": "enable SRC-BIORXIV as a selectable source under board B1",
        "weight_proposal": {"source_weight": 60, "note": "低于 arXiv(100)，受 source_share_cap 0.40 约束"},
        "safeguards": [
            "单源占比 ≤40%（注册表 source_share_cap，现值直接生效）",
            "连续 3 次抓取失败自动停用（sources 健康机制）",
            "随时可撤销：再次点击即降回影子（回执记录）",
        ],
        "proposal_doc": "docs/v03/R5_启用提案_bioRxiv.md",
    }


def promote(conn: sqlite3.Connection, *, actor: str = "owner_click") -> dict[str, Any]:
    """Owner 点「应用上板」：写 meta 键 + 回执。系统永不自行调用（业务规则·自迭代边界）."""
    ensure_source(conn)
    already = is_promoted(conn)
    new_state = not already
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                 (PROMOTED_META_KEY, "true" if new_state else "false"))
    store.record_config_change(
        conn, domain="sources.biorxiv.promoted",
        old={"promoted": already}, new={"promoted": new_state},
        proposal_src=actor, replay_ref="data/shadow_biorxiv_report.json",
        receipt=("R5 上板：bioRxiv 由影子转正式参选（源权重 60、共享 0.40 单源上限）"
                 if new_state else "R5 撤板：bioRxiv 退回影子模式"),
    )
    return {"promoted": new_state}


def ingest_promoted_day(conn: sqlite3.Connection, *, as_of: datetime | None = None) -> dict[str, int]:
    """上板后的真实入库（documents/doc_versions/claims 与 arXiv 同管道）."""
    from .claims import extract_claims, store_claims

    as_of = as_of or datetime.now(timezone.utc)
    day = (as_of - timedelta(days=1)).strftime("%Y-%m-%d")
    counts = {"扫描": 0, "新文档": 0, "新版本": 0, "新声明": 0}
    candidates = fetch_day(day)
    store.record_source_health(conn, SOURCE_ID, ok=True)
    counts["扫描"] = len(candidates)
    for cand in candidates:
        item = {
            "source_id": cand["doc_id"], "source_type": "biorxiv",
            "stable_id": cand["stable_id"], "title": cand["title"],
            "retrieved_at": as_of.isoformat(timespec="seconds"),
            "canonical_url": cand["canonical_url"],
            "metadata": cand["metadata"],
            "license": cand["license"],
        }
        doc_id, version_id, new_doc, new_version = store.ingest_document(
            conn, item, source_id=SOURCE_ID)
        counts["新文档"] += int(new_doc)
        counts["新版本"] += int(new_version)
        if new_version:
            abstract = cand["metadata"]["arxiv"].get("summary") or ""
            counts["新声明"] += store_claims(conn, extract_claims(version_id, abstract))
    conn.commit()
    return counts
