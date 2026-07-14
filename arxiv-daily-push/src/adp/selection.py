"""选择环节（R1-2/R1-3）—— 硬门 → 加权 → 选中 1 篇或弃权 → 双向解释 → 可重放.

弃权是一等决策（业务规则）：最高分 < 弃权线当日不发，理由与最高分入 manifest 与周报。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping

from . import store
from .config import FEATURE_KEYS, Thresholds
from .features import attention_cost, legacy_score, score_features, total_score
from .gates import run_gates

FEATURE_LABELS = {
    "user_relevance": "用户相关",
    "knowledge_gap": "知识差距",
    "novelty_to_user": "相对新颖",
    "transfer_potential": "迁移潜力",
    "forgetting_pressure": "遗忘压力",
    "urgency": "紧迫度",
    "evidence_quality": "证据质量",
    "diversity": "多样性",
}


def build_context(conn: sqlite3.Connection, *, as_of: datetime) -> dict[str, Any]:
    """从库里取打分上下文：已学词面、近期已见、到期复习主题、近期入选类目."""
    from .features import _tokens  # 复用同一分词，保证可重放

    learned_tokens: set[str] = set()
    for row in conn.execute(
        """SELECT l.sections_json FROM lessons l
           WHERE EXISTS (SELECT 1 FROM learning_events e
                         WHERE e.item_id = l.id AND e.kind='self_grade' AND e.undone_by IS NULL)"""
    ):
        sections = json.loads(row["sections_json"])
        learned_tokens |= _tokens(" ".join(str(s.get("body", "")) for s in sections))

    seen_token_sets: list[set[str]] = []
    for row in conn.execute(
        "SELECT title, metadata_json FROM doc_versions v JOIN documents d ON d.id=v.doc_id "
        "ORDER BY v.retrieved_at DESC LIMIT 200"
    ):
        meta = json.loads(row["metadata_json"])
        seen_token_sets.append(_tokens(f"{row['title']} {meta.get('summary', '')}"))

    due_topic_tokens: set[str] = set()
    now_iso = as_of.isoformat(timespec="seconds")
    for row in conn.execute(
        """SELECT l.sections_json FROM review_state r JOIN lessons l ON l.id = r.item_id
           WHERE r.due_at IS NOT NULL AND r.due_at <= ?""",
        (now_iso,),
    ):
        sections = json.loads(row["sections_json"])
        title_terms = _tokens(" ".join(str(s.get("body", ""))[:200] for s in sections[:2]))
        due_topic_tokens |= set(list(title_terms)[:20])

    recent_primary = [
        json.loads(row["contributions_json"]).get("_primary_category", "")
        for row in conn.execute(
            "SELECT contributions_json FROM selections WHERE abstain=0 ORDER BY as_of_date DESC LIMIT 20"
        )
    ]
    return {
        "as_of": as_of,
        "learned_tokens": learned_tokens,
        "seen_token_sets": seen_token_sets,
        "due_topic_tokens": due_topic_tokens,
        "recent_selected_primary": [p for p in recent_primary if p],
    }


def seen_version_ids(conn: sqlite3.Connection) -> set[str]:
    """已入选或已生成讲义的版本（dedup 硬门输入）."""
    ids: set[str] = set()
    for row in conn.execute(
        """SELECT v.versioned_id FROM lessons l JOIN doc_versions v ON v.id = l.doc_version_id
           WHERE l.status != 'reopened'"""
    ):
        ids.add(row["versioned_id"])
    return ids


def evaluate_candidates(candidates: list[dict[str, Any]], context: Mapping[str, Any],
                        thresholds: Thresholds, *, gate_context: Mapping[str, Any],
                        single_board: bool = True) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """返回 (scored, rejected)。scored 按分数降序；每条含特征值/贡献/理由/旧分（对照）."""
    weights = thresholds.effective_weights(single_board=single_board)
    scored: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for candidate in candidates:
        gate = run_gates(candidate, gate_context)
        if not gate.passed:
            rejected.append({
                "doc_id": candidate["doc_id"],
                "title": candidate["title"],
                "gate_results": dict(gate.results),
                "reason": gate.reject_reason,
            })
            continue
        features = score_features(candidate, context)
        cost, cost_reason = attention_cost(candidate)
        score, contributions = total_score(features, weights, cost, thresholds.attention_cost_penalty)
        scored.append({
            "candidate": candidate,
            "features": features,
            "attention_cost": cost,
            "attention_reason": cost_reason,
            "score": score,
            "contributions": contributions,
            "legacy_score": legacy_score(features, cost),
            "gate_results": dict(gate.results),
        })
    scored.sort(key=lambda entry: entry["score"], reverse=True)
    return scored, rejected


def explain_choice(top: Mapping[str, Any], runner: Mapping[str, Any] | None) -> tuple[str, str]:
    """双向解释：为什么选它 / 为什么不是第二名（含特征贡献）."""
    contributions = top["contributions"]
    ranked = sorted(FEATURE_KEYS, key=lambda key: contributions[key], reverse=True)[:3]
    why_parts = [
        f"{FEATURE_LABELS[key]} 贡献 {contributions[key]:.1f} 分（{top['features'][key]['reason']}）"
        for key in ranked
    ]
    why = f"总分 {top['score']:.1f}：" + "；".join(why_parts)
    if runner is None:
        return why, "今日无第二名（过门候选只有一篇）"
    deltas = {key: contributions[key] - runner["contributions"][key] for key in FEATURE_KEYS}
    key_gap = max(deltas, key=lambda k: deltas[k])
    why_not = (
        f"第二名《{runner['candidate']['title'][:60]}》总分 {runner['score']:.1f}，"
        f"差距主要在{FEATURE_LABELS[key_gap]}（{deltas[key_gap]:+.1f} 分：{runner['features'][key_gap]['reason']}）"
    )
    return why, why_not


def select_daily(conn: sqlite3.Connection, *, run_id: str, as_of_date: str,
                 candidates: list[dict[str, Any]], thresholds: Thresholds,
                 as_of: datetime | None = None) -> dict[str, Any]:
    """执行一次每日选择并持久化（selections + candidates 两表，不变量 10）."""
    as_of = as_of or datetime.now(timezone.utc)
    context = build_context(conn, as_of=as_of)
    gate_context = {
        "seen_version_ids": seen_version_ids(conn),
        "source_health": _source_health(conn),
    }
    scored, rejected = evaluate_candidates(candidates, context, thresholds, gate_context=gate_context)

    for entry in scored:
        candidate = entry["candidate"]
        conn.execute(
            """INSERT OR IGNORE INTO candidates (id, doc_id, board_id, as_of_date, features_json, gate_results_json)
               VALUES (?, ?, 'B1', ?, ?, ?)""",
            (f"{candidate['doc_id']}@{as_of_date}", candidate["doc_id"], as_of_date,
             json.dumps({k: v["value"] for k, v in entry["features"].items()}, ensure_ascii=False),
             json.dumps(entry["gate_results"], ensure_ascii=False)),
        )

    result: dict[str, Any] = {
        "run_id": run_id, "as_of_date": as_of_date,
        "scanned": len(candidates), "passed_gates": len(scored), "rejected": rejected,
    }
    params_json = json.dumps({
        "registry": thresholds.registry_id,
        "weights": thresholds.effective_weights(single_board=True),
        "abstain_threshold": thresholds.abstain_threshold,
        "attention_cost_penalty": thresholds.attention_cost_penalty,
    }, ensure_ascii=False)

    if not scored or scored[0]["score"] < thresholds.abstain_threshold:
        top_score = scored[0]["score"] if scored else None
        reason = (
            f"最高分 {top_score:.1f} 低于弃权线 {thresholds.abstain_threshold}" if scored
            else "无候选通过资格硬门"
        )
        conn.execute(
            """INSERT INTO selections (run_id, as_of_date, candidate_id, score, abstain, abstain_reason, params_json)
               VALUES (?, ?, NULL, ?, 1, ?, ?)""",
            (run_id, as_of_date, top_score, reason, params_json),
        )
        conn.commit()
        result.update({"abstain": True, "abstain_reason": reason, "top_score": top_score})
        return result

    top = scored[0]
    runner = scored[1] if len(scored) > 1 else None
    why, why_not = explain_choice(top, runner)
    contributions = dict(top["contributions"])
    contributions["_primary_category"] = top["candidate"]["metadata"]["arxiv"].get("primary_category", "")
    conn.execute(
        """INSERT INTO selections
           (run_id, as_of_date, candidate_id, score, contributions_json, why, why_not_next,
            runner_up_id, runner_up_score, abstain, params_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (run_id, as_of_date, f"{top['candidate']['doc_id']}@{as_of_date}", top["score"],
         json.dumps(contributions, ensure_ascii=False), why, why_not,
         (runner["candidate"]["doc_id"] + "@" + as_of_date) if runner else None,
         runner["score"] if runner else None, params_json),
    )
    conn.commit()
    result.update({"abstain": False, "top": top, "runner": runner, "why": why, "why_not": why_not})
    return result


def _source_health(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT health FROM sources WHERE id='SRC-ARXIV'").fetchone()
    return str(row["health"]) if row else "active"


def replay_30d(conn: sqlite3.Connection, thresholds: Thresholds, *, as_of: datetime,
               days: int = 30) -> dict[str, Any]:
    """R1-3：30 天历史回放 —— 逐日重演硬门+打分，输出新旧头名对照与弃权线重校.

    重校规则（盲点三）：弃权线随权重总和等比缩放 55 × (Σw_new / 96)，
    并给出该线下的回放弃权天数对照，供 Owner 抽查合理性。
    """
    from datetime import timedelta

    from .arxiv_source import candidates_for_date

    rows: list[dict[str, Any]] = []
    abstain_days_old_line = 0
    abstain_days_new_line = 0
    scale = thresholds.weight_total / 96.0
    recalibrated = round(55 * scale, 1)

    for offset in range(days, -1, -1):
        day = (as_of - timedelta(days=offset)).strftime("%Y-%m-%d")
        candidates = candidates_for_date(conn, day, window_days=3)
        if not candidates:
            continue
        context = build_context(conn, as_of=as_of)
        scored, _ = evaluate_candidates(
            candidates, context, thresholds,
            gate_context={"seen_version_ids": set(), "source_health": "active"},
        )
        if not scored:
            continue
        top = scored[0]
        by_legacy = max(scored, key=lambda entry: entry["legacy_score"])
        rows.append({
            "date": day,
            "candidates": len(candidates),
            "passed": len(scored),
            "new_top": top["candidate"]["title"][:80],
            "new_score": top["score"],
            "old_top": by_legacy["candidate"]["title"][:80],
            "old_score": by_legacy["legacy_score"],
            "same_pick": top["candidate"]["doc_id"] == by_legacy["candidate"]["doc_id"],
            "top_reason": explain_choice(top, scored[1] if len(scored) > 1 else None)[0],
        })
        if top["score"] < 55:
            abstain_days_old_line += 1
        if top["score"] < recalibrated:
            abstain_days_new_line += 1

    return {
        "generated_at": as_of.isoformat(timespec="seconds"),
        "days_with_data": len(rows),
        "weight_total": thresholds.weight_total,
        "abstain_line_placeholder": 55,
        "abstain_line_recalibrated": recalibrated,
        "abstain_days_at_placeholder": abstain_days_old_line,
        "abstain_days_at_recalibrated": abstain_days_new_line,
        "agreement_rate": round(
            sum(1 for r in rows if r["same_pick"]) / len(rows), 3
        ) if rows else None,
        "rows": rows,
    }
