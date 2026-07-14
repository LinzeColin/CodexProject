"""R4 试运行 —— 影子对照 + 四指标报告 + 持久运行决策记录（压缩为 1 个周五，Owner 指令）.

影子记录本体在 selections 表（第二名 runner_up_* 与弃权行随每日 run 常开）；
本模块提供「换个参数会怎样」的对照视图与试运行报告聚合。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from . import store
from .config import Thresholds


def shadow_compare(conn: sqlite3.Connection, thresholds: Thresholds, *, days: int = 14,
                   as_of: datetime | None = None) -> dict[str, Any]:
    """影子对照（盲点二实证）：多样性上限 10（现行）vs 放开 17（板块二后），逐日头名对照."""
    from .arxiv_source import candidates_for_date
    from .features import total_score
    from .selection import build_context, evaluate_candidates

    as_of = as_of or datetime.now(timezone.utc)
    rows = []
    changed = 0
    context = build_context(conn, as_of=as_of)
    gate_context = {"seen_version_ids": set(), "source_health": "active"}
    uncapped_weights = thresholds.effective_weights(single_board=False)
    for offset in range(days, -1, -1):
        day = (as_of - timedelta(days=offset)).strftime("%Y-%m-%d")
        candidates = candidates_for_date(conn, day, window_days=3)
        if not candidates:
            continue
        # 复审修复：特征只打一遍分；影子权重直接套用缓存的特征向量（打分是廉价加权和）
        capped, _ = evaluate_candidates(candidates, context, thresholds,
                                        gate_context=gate_context, single_board=True)
        if not capped:
            continue
        shadow_scored = []
        for entry in capped:
            score, _contrib = total_score(entry["features"], uncapped_weights,
                                          entry["attention_cost"], thresholds.attention_cost_penalty)
            shadow_scored.append((score, entry))
        shadow_top_score, shadow_top = max(shadow_scored, key=lambda pair: pair[0])
        same = capped[0]["candidate"]["doc_id"] == shadow_top["candidate"]["doc_id"]
        changed += 0 if same else 1
        rows.append({
            "date": day, "same": same,
            "current_top": capped[0]["candidate"]["title"][:70],
            "current_score": capped[0]["score"],
            "shadow_top": shadow_top["candidate"]["title"][:70],
            "shadow_score": shadow_top_score,
        })
    return {
        "question": "如果把多样性权重从上限 10 放开到 17（板块二启用后的状态），头名会怎么变？",
        "days": len(rows), "changed_days": changed, "rows": rows,
        "note": "影子只记录不交付；正式放开须走 提案→回放预览→应用→回执。",
    }


def pilot_report(conn: sqlite3.Connection, *, as_of: datetime | None = None) -> dict[str, Any]:
    """四指标试运行报告：7 天回忆、30 天回忆、复习债务、注意力成本（数据不足如实标注）."""
    from .config import load_thresholds

    thresholds = load_thresholds()
    as_of = as_of or datetime.now(timezone.utc)

    def recall_rate(days: int) -> dict[str, Any]:
        since = (as_of - timedelta(days=days)).isoformat(timespec="seconds")
        rows = conn.execute(
            "SELECT grade FROM learning_events WHERE kind='self_grade' AND undone_by IS NULL AND at >= ?",
            (since,),
        ).fetchall()
        grades = [int(r["grade"]) for r in rows if r["grade"]]
        if not grades:
            return {"rate": None, "n": 0, "note": "暂无回忆事件"}
        success = sum(1 for g in grades if g >= 3)
        return {"rate": round(success / len(grades), 3), "n": len(grades),
                "note": f"{success}/{len(grades)} 次自评 ≥ 良好"}

    now_iso = as_of.isoformat(timespec="seconds")
    overdue = conn.execute(
        "SELECT COUNT(*) n FROM review_state WHERE due_at IS NOT NULL AND due_at <= ?", (now_iso,)
    ).fetchone()["n"]
    open_debts = conn.execute("SELECT COUNT(*) n FROM debts WHERE status='open'").fetchone()["n"]
    review_cap = thresholds.max_daily_reviews

    week_ago = (as_of - timedelta(days=7)).isoformat(timespec="seconds")
    daily_events = conn.execute(
        """SELECT substr(at, 1, 10) d, COUNT(*) n FROM learning_events
           WHERE at >= ? AND actor='owner' AND kind IN ('recall_reveal','self_grade','manual_mark')
           GROUP BY d""",
        (week_ago,),
    ).fetchall()
    avg_events = round(sum(r["n"] for r in daily_events) / max(1, len(daily_events)), 1)

    review_count = conn.execute(
        "SELECT COUNT(*) n FROM learning_events WHERE kind='self_grade' AND undone_by IS NULL"
    ).fetchone()["n"]

    return {
        "generated_at": now_iso,
        "metrics": {
            "recall_7d": recall_rate(7),
            "recall_30d": recall_rate(30),
            "review_debt": {"overdue_items": int(overdue), "open_debts": int(open_debts),
                            "note": f"上限 {review_cap}（读注册表），逾期超限触发保护复盘"},
            "attention_cost": {"avg_owner_events_per_active_day": avg_events,
                               "note": "未采集阅读时长，以每日主动事件数为代理指标（诚实标注）"},
        },
        "fsrs_personalization": {
            "reviews_recorded": int(review_count),
            "personalize_after": thresholds.personalize_after_reviews,
            "status": f"官方默认 21 参数运行中；满 {thresholds.personalize_after_reviews} 条回忆后训练个性化参数",
        },
        "data_sufficiency": "试运行按 Owner 指令压缩为 1 个周五；回忆样本量尚小，指标以趋势看待",
    }


def record_decision(conn: sqlite3.Connection, decision: str, note: str = "") -> dict[str, Any]:
    """持久运行决策（批准/退回/降级）——记录 Owner 点击为回执；系统不代替 Owner 决策."""
    if decision not in {"approve", "return", "degrade"}:
        raise ValueError("decision must be approve/return/degrade")
    store.record_config_change(
        conn, domain="pilot_decision", old={},
        new={"decision": decision, "note": note}, proposal_src="owner_click",
        receipt=f"R4 持久运行决策：{decision}（由 Owner 在 /pilot 页点击记录）",
    )
    return {"recorded": decision}
