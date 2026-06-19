from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


MODEL_DIVERGENCE_REVIEW_JSON_LATEST = "model_divergence_review_latest.json"
MODEL_DIVERGENCE_REVIEW_MD_LATEST = "model_divergence_review_latest.md"
MODEL_DIVERGENCE_REVIEW_PDF_LATEST = "model_divergence_review_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_model_divergence_review_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_model_divergence_review(output_dir, db_path)
    json_path = output_dir / MODEL_DIVERGENCE_REVIEW_JSON_LATEST
    md_path = output_dir / MODEL_DIVERGENCE_REVIEW_MD_LATEST
    pdf_path = output_dir / MODEL_DIVERGENCE_REVIEW_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_model_divergence_review_markdown(payload))
    pdf_summary = write_model_divergence_review_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_model_divergence_review(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_model_divergence_review(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    model_payload = load_json(output_dir / "tab_fifa_model_comparison_v0_1.json")
    recommendation_payload = load_json(output_dir / "recommendation_operations_latest.json")
    rows = build_review_rows(model_payload, recommendation_payload)
    summary = summarize_review_rows(rows, model_payload, recommendation_payload)
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "model_divergence_review_dashboard",
        "purpose": "把开源模型对比中的高分歧比赛沉淀为可归档复核队列：展示共识注、置信度、最大模型分歧、是否关联推荐下注、复核优先级和允许动作。",
        "executive_status": {
            "status": "manual_review_required" if summary["high_priority_review_count"] else "monitoring_ready",
            "automation_role": "研究交叉验证层，不是执行授权层",
            "execution_unlock": "blocked_by_design",
            "current_action": "高分歧或低置信盘口先进入人工复核；raw/private/preflight/public-safety 未过时，所有新增执行金额仍为 AUD 0。",
            "primary_gap": primary_gap(summary),
            "recommended_next_action": recommended_next_action(summary),
        },
        "summary": summary,
        "review_rows": rows,
        "automation_view": {
            "automation_view_ready": True,
            "gate": "high_divergence_review_queue",
            "execution_unlock_status": "blocked_by_design",
            "fail_closed_policy": "本报告只能提高解释质量和复核优先级，不能绕过 raw/private/preflight/public-safety 门禁。",
            "prohibited_actions": ["不自动下注", "不点击赔率", "不添加投注单", "不绕过门禁"],
            "dashboard_usage": [
                "高分歧 + 关联推荐下注 => 优先人工复核",
                "高分歧 + 无下注金额 => 进入观察解释层",
                "低置信 + Edge 未达门槛 => 默认降级为 No Bet / Watch",
            ],
        },
        "old_new_compare": old_new_compare(db_path, rows),
        "source_alignment": {
            "source_report": "tab_fifa_model_comparison_v0_1.json",
            "recommendation_report": "recommendation_operations_latest.json",
            "github_reference_note": "复核逻辑来自 Dixon-Coles / goalmodel / Hicruben 风格的模型分歧与共识置信度展示，但不复制外部代码。",
        },
        "evidence_layers": [
            {"layer": "FACT", "text": "模型分歧、共识注和置信度来自开源模型对比报告。"},
            {"layer": "FACT", "text": "关联下注、Edge、EV、RoR 和研究金额来自推荐操作报告。"},
            {"layer": "INFERENCE", "text": "复核优先级由高分歧、低置信、关联下注金额、Edge门槛和RoR等级综合计算。"},
            {"layer": "OBSERVATION", "text": "当前只生成研究复核队列；不自动下注，不点击赔率，不加入 Bet Slip。"},
        ],
        "truthfulness_note": "本报告不把模型共识当作下注执行授权；分歧越高，越需要人工复核或降仓。",
        "safety_note": "该报告只用于研究复核和报告解释，不自动下注、不点击 TAB 赔率、不写入 Bet Slip。",
    }
    return sanitize_public_payload(payload)


def build_review_rows(model_payload: dict[str, Any], recommendation_payload: dict[str, Any]) -> list[dict[str, Any]]:
    recommendation_by_event = {
        str(row.get("event") or ""): row
        for row in recommendation_payload.get("recommendation_rows", [])
        if isinstance(row, dict)
    }
    rows: list[dict[str, Any]] = []
    for item in model_payload.get("rows", []) or []:
        if not isinstance(item, dict):
            continue
        match = str(item.get("match") or "")
        consensus = item.get("consensus") or {}
        disagreement = item.get("disagreement") or {}
        recommendation = recommendation_by_event.get(match) or {}
        max_gap = to_float(disagreement.get("max_abs_current_vs_elo_dc")) or 0.0
        high_divergence = bool(disagreement.get("high_divergence"))
        confidence = str(consensus.get("confidence") or "unknown")
        linked_stake = to_float(recommendation.get("stake_aud")) or 0.0
        edge_gap = to_float(recommendation.get("edge_threshold_gap"))
        risk_grade = str(recommendation.get("risk_of_ruin_grade") or "")
        priority = review_priority(high_divergence, confidence, linked_stake, edge_gap, risk_grade)
        rows.append(
            {
                "row_key": row_key(match, consensus.get("selection"), recommendation.get("selection")),
                "match": match,
                "consensus_selection": str(consensus.get("selection") or ""),
                "consensus_probability": to_float(consensus.get("mean_probability")),
                "consensus_confidence": confidence,
                "model_spread": to_float(consensus.get("model_spread")),
                "max_disagreement": round(max_gap, 4),
                "high_divergence": high_divergence,
                "rating_source": str((item.get("ratings") or {}).get("source") or ""),
                "linked_recommendation": bool(recommendation),
                "linked_market": str(recommendation.get("market") or ""),
                "linked_selection": str(recommendation.get("selection") or ""),
                "linked_action": str(recommendation.get("action") or ""),
                "linked_research_stake_aud": round(linked_stake, 2),
                "linked_edge": to_float(recommendation.get("edge")),
                "linked_edge_threshold_gap": edge_gap,
                "linked_ev": to_float(recommendation.get("expected_value")),
                "linked_risk_of_ruin": to_float(recommendation.get("risk_of_ruin")),
                "linked_risk_grade": risk_grade,
                "review_priority": priority,
                "review_action": review_action(priority, high_divergence, linked_stake),
                "review_reason": review_reason(item, recommendation, priority),
                "evidence_layers": [
                    {"layer": "FACT", "text": f"模型最大分歧 {pct(max_gap)}；共识置信度 {confidence}。"},
                    {"layer": "INFERENCE", "text": f"复核优先级 {priority}，不会解锁下注执行。"},
                ],
            }
        )
    return sorted(rows, key=review_sort_key)


def summarize_review_rows(rows: list[dict[str, Any]], model_payload: dict[str, Any], recommendation_payload: dict[str, Any]) -> dict[str, Any]:
    match_count = len(rows)
    high_rows = [row for row in rows if row.get("high_divergence")]
    linked_rows = [row for row in rows if row.get("linked_recommendation")]
    priority_counts = Counter(str(row.get("review_priority") or "低") for row in rows)
    confidence_counts = Counter(str(row.get("consensus_confidence") or "unknown") for row in rows)
    gaps = [float(row.get("max_disagreement") or 0) for row in rows]
    linked_stake = sum(float(row.get("linked_research_stake_aud") or 0) for row in linked_rows)
    return {
        "match_count": match_count,
        "high_divergence_count": len(high_rows),
        "high_divergence_ratio": round(len(high_rows) / match_count, 4) if match_count else 0.0,
        "low_confidence_count": sum(1 for row in rows if str(row.get("consensus_confidence") or "").lower() == "low"),
        "linked_recommendation_count": len(linked_rows),
        "linked_research_stake_aud": round(linked_stake, 2),
        "high_priority_review_count": int(priority_counts.get("高", 0)),
        "medium_priority_review_count": int(priority_counts.get("中", 0)),
        "average_max_disagreement": round(sum(gaps) / len(gaps), 4) if gaps else 0.0,
        "max_disagreement": round(max(gaps), 4) if gaps else 0.0,
        "priority_distribution": dict(priority_counts),
        "confidence_distribution": dict(confidence_counts),
        "execution_unlock": "blocked_by_design",
        "model_report_ready": bool(model_payload.get("ready")),
        "recommendation_candidate_count": int((recommendation_payload.get("summary") or {}).get("candidate_count") or 0),
        "recommendation_executable_new_stake_aud": float((recommendation_payload.get("summary") or {}).get("executable_new_stake_aud") or 0),
        "top_review_match": rows[0].get("match", "") if rows else "",
        "top_review_action": rows[0].get("review_action", "") if rows else "",
    }


def review_priority(high_divergence: bool, confidence: str, linked_stake: float, edge_gap: float | None, risk_grade: str) -> str:
    score = 0
    if high_divergence:
        score += 3
    if confidence.lower() == "low":
        score += 2
    elif confidence.lower() == "medium":
        score += 1
    if linked_stake > 0:
        score += 2
    if edge_gap is not None and edge_gap < 0:
        score += 1
    if risk_grade in {"偏高", "高"}:
        score += 1
    if score >= 5:
        return "高"
    if score >= 3:
        return "中"
    return "低"


def review_action(priority: str, high_divergence: bool, linked_stake: float) -> str:
    if priority == "高" and linked_stake > 0:
        return "优先人工复核，门禁通过前不执行新增下注"
    if priority == "高":
        return "进入高分歧解释队列，不做买入"
    if high_divergence:
        return "保留观察，等待赔率/基本面更新"
    if priority == "中":
        return "正常复核后再进入推荐解释"
    return "低优先级监控"


def review_reason(model_row: dict[str, Any], recommendation: dict[str, Any], priority: str) -> str:
    consensus = model_row.get("consensus") or {}
    disagreement = model_row.get("disagreement") or {}
    parts = [
        f"共识方向 {consensus.get('selection', '')}，共识概率 {pct(consensus.get('mean_probability'))}，置信度 {consensus.get('confidence', '')}。",
        f"当前市场/开源 Elo-DC 最大分歧 {pct(disagreement.get('max_abs_current_vs_elo_dc'))}。",
        f"复核优先级 {priority}；该报告只进入人工复核和解释层，不解锁下注。",
    ]
    if recommendation:
        parts.append(
            "关联推荐：{market} / {selection}，研究金额 {stake}，Edge门槛差 {edge_gap}，RoR {ror}。".format(
                market=recommendation.get("market", ""),
                selection=recommendation.get("selection", ""),
                stake=money(recommendation.get("stake_aud")),
                edge_gap=pp(recommendation.get("edge_threshold_gap")),
                ror=pct(recommendation.get("risk_of_ruin")),
            )
        )
    else:
        parts.append("当前未关联推荐下注金额，作为模型解释和后续赔率变动监控。")
    return " ".join(parts)


def old_new_compare(db_path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "high_priority_delta": 0, "high_divergence_delta": 0}
    try:
        with connect_report_db(db_path) as conn:
            row = conn.execute(
                """
                SELECT generated_at, high_priority_review_count, high_divergence_count, payload_json
                FROM model_divergence_review_snapshots
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except sqlite3.Error:
        return {"status": "compare_unavailable", "high_priority_delta": 0, "high_divergence_delta": 0}
    if not row:
        return {"status": "no_previous_snapshot", "high_priority_delta": 0, "high_divergence_delta": 0}
    previous_payload = parse_json(row["payload_json"])
    previous_rows = {str(item.get("row_key") or ""): item for item in previous_payload.get("review_rows", []) if isinstance(item, dict)}
    current_rows = {str(item.get("row_key") or ""): item for item in rows}
    current_high_priority = sum(1 for item in rows if item.get("review_priority") == "高")
    current_high_divergence = sum(1 for item in rows if item.get("high_divergence"))
    previous_top = (previous_payload.get("summary") or {}).get("top_review_match", "")
    current_top = rows[0].get("match", "") if rows else ""
    return {
        "status": "compared",
        "previous_generated_at": str(row["generated_at"] or ""),
        "high_priority_delta": int(current_high_priority - int(row["high_priority_review_count"] or 0)),
        "high_divergence_delta": int(current_high_divergence - int(row["high_divergence_count"] or 0)),
        "new_review_items": sorted(current_rows.keys() - previous_rows.keys())[:8],
        "removed_review_items": sorted(previous_rows.keys() - current_rows.keys())[:8],
        "top_review_changed": previous_top != current_top,
    }


def render_model_divergence_review_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 模型分歧复核 Dashboard",
        "",
        "本报告把 GitHub / 开源模型对比转成可执行前的人工复核队列。它只用于研究解释和风险控制，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- automation_role: `{executive.get('automation_role', '')}`",
        f"- execution_unlock: `{executive.get('execution_unlock', '')}`",
        f"- match_count: `{summary.get('match_count', 0)}`",
        f"- high_divergence_count: `{summary.get('high_divergence_count', 0)}` / `{pct(summary.get('high_divergence_ratio'))}`",
        f"- high_priority_review_count: `{summary.get('high_priority_review_count', 0)}`",
        f"- linked_recommendation_count: `{summary.get('linked_recommendation_count', 0)}`",
        f"- linked_research_stake_aud: `{money(summary.get('linked_research_stake_aud'))}`",
        f"- max_disagreement: `{pct(summary.get('max_disagreement'))}`",
        f"- current_action: {md(executive.get('current_action'))}",
        "",
        "## Automation 使用视角",
        "",
        f"- gate: `{(payload.get('automation_view') or {}).get('gate', '')}`",
        f"- execution_unlock_status: `{(payload.get('automation_view') or {}).get('execution_unlock_status', '')}`",
        f"- fail_closed_policy: {md((payload.get('automation_view') or {}).get('fail_closed_policy'))}",
        f"- prohibited_actions: {md('；'.join((payload.get('automation_view') or {}).get('prohibited_actions') or []))}",
        "",
        "## 新旧复核变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- high_priority_delta: `{compare.get('high_priority_delta', 0)}`",
        f"- high_divergence_delta: `{compare.get('high_divergence_delta', 0)}`",
        f"- top_review_changed: `{compare.get('top_review_changed', False)}`",
        "",
        "## 复核队列",
        "",
        "| 比赛 | 共识注 | 概率 | 置信度 | 最大分歧 | 高分歧 | 关联盘口 | 金额 | Edge差 | RoR | 优先级 | 复核动作 | 原因 |",
        "|---|---|---:|---|---:|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in payload.get("review_rows") or []:
        lines.append(
            "| {match} | {selection} | {prob} | {confidence} | {gap} | {high} | {market} / {linked_selection} | {stake} | {edge_gap} | {ror} | {priority} | {action} | {reason} |".format(
                match=md(row.get("match")),
                selection=md(row.get("consensus_selection")),
                prob=pct(row.get("consensus_probability")),
                confidence=md(row.get("consensus_confidence")),
                gap=pct(row.get("max_disagreement")),
                high="是" if row.get("high_divergence") else "否",
                market=md(row.get("linked_market")),
                linked_selection=md(row.get("linked_selection")),
                stake=money(row.get("linked_research_stake_aud")),
                edge_gap=pp(row.get("linked_edge_threshold_gap")),
                ror=pct(row.get("linked_risk_of_ruin")),
                priority=md(row.get("review_priority")),
                action=md(row.get("review_action")),
                reason=md(row.get("review_reason")),
            )
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('safety_note', '')}"])
    return "\n".join(lines)


def write_model_divergence_review_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    rows = payload.get("review_rows") or []
    compare = payload.get("old_new_compare") or {}
    charts = [
        chart_from_items("复核优先级", [(key, value) for key, value in (summary.get("priority_distribution") or {}).items()], "#8B1E3F"),
        chart_from_items("共识置信度", [(key, value) for key, value in (summary.get("confidence_distribution") or {}).items()], "#1F4E79"),
        chart_from_items("最大模型分歧", [(row.get("match", ""), float(row.get("max_disagreement") or 0) * 100) for row in rows[:12]], "#C7352B"),
        chart_from_items(
            "复核门禁",
            [
                ("高分歧", summary.get("high_divergence_count", 0)),
                ("高优先级", summary.get("high_priority_review_count", 0)),
                ("关联推荐", summary.get("linked_recommendation_count", 0)),
                ("可执行金额", summary.get("recommendation_executable_new_stake_aud", 0)),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 模型分歧复核 Dashboard",
        subtitle="把开源模型对比转成人工复核队列；只用于研究解释和风险控制，不自动下注。",
        summary_rows=[
            ("status", str((payload.get("executive_status") or {}).get("status", ""))),
            ("execution_unlock", str(summary.get("execution_unlock", ""))),
            ("matches", str(summary.get("match_count", 0))),
            ("high divergence", str(summary.get("high_divergence_count", 0))),
            ("high priority", str(summary.get("high_priority_review_count", 0))),
            ("linked recs", str(summary.get("linked_recommendation_count", 0))),
            ("linked stake", money(summary.get("linked_research_stake_aud"))),
            ("max disagreement", pct(summary.get("max_disagreement"))),
            ("old-new", str(compare.get("status", ""))),
        ],
        charts=charts,
        table_headers=["比赛", "共识注", "置信度", "最大分歧", "优先级", "复核动作"],
        table_rows=[
            [
                str(row.get("match", "")),
                str(row.get("consensus_selection", "")),
                str(row.get("consensus_confidence", "")),
                pct(row.get("max_disagreement")),
                str(row.get("review_priority", "")),
                str(row.get("review_action", "")),
            ]
            for row in rows[:14]
        ],
        extra_tables=[
            {
                "title": "关联推荐下注",
                "headers": ["比赛", "盘口", "下注", "研究金额", "Edge差", "RoR", "动作"],
                "rows": [
                    [
                        str(row.get("match", "")),
                        str(row.get("linked_market", "")),
                        str(row.get("linked_selection", "")),
                        money(row.get("linked_research_stake_aud")),
                        pp(row.get("linked_edge_threshold_gap")),
                        pct(row.get("linked_risk_of_ruin")),
                        str(row.get("linked_action", "")),
                    ]
                    for row in rows
                    if row.get("linked_recommendation")
                ][:12],
            },
            {
                "title": "Automation 使用视角",
                "headers": ["项目", "状态"],
                "rows": [
                    ["automation_role", str((payload.get("executive_status") or {}).get("automation_role", ""))],
                    ["execution_unlock", str((payload.get("automation_view") or {}).get("execution_unlock_status", ""))],
                    ["fail_closed_policy", str((payload.get("automation_view") or {}).get("fail_closed_policy", ""))],
                    ["prohibited_actions", "；".join((payload.get("automation_view") or {}).get("prohibited_actions") or [])],
                ],
            },
            {
                "title": "新旧复核变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["high_priority_delta", str(compare.get("high_priority_delta", 0))],
                    ["high_divergence_delta", str(compare.get("high_divergence_delta", 0))],
                    ["top_review_changed", str(compare.get("top_review_changed", False))],
                ],
            },
        ],
    )


def persist_model_divergence_review(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_divergence_review_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    match_count INTEGER NOT NULL DEFAULT 0,
                    high_divergence_count INTEGER NOT NULL DEFAULT 0,
                    high_priority_review_count INTEGER NOT NULL DEFAULT 0,
                    linked_recommendation_count INTEGER NOT NULL DEFAULT 0,
                    linked_research_stake_aud REAL NOT NULL DEFAULT 0,
                    average_max_disagreement REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO model_divergence_review_snapshots(
                    snapshot_id, generated_at, status, match_count, high_divergence_count,
                    high_priority_review_count, linked_recommendation_count,
                    linked_research_stake_aud, average_max_disagreement, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("snapshot_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    int(summary.get("match_count") or 0),
                    int(summary.get("high_divergence_count") or 0),
                    int(summary.get("high_priority_review_count") or 0),
                    int(summary.get("linked_recommendation_count") or 0),
                    float(summary.get("linked_research_stake_aud") or 0),
                    float(summary.get("average_max_disagreement") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "model_divergence_review_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def primary_gap(summary: dict[str, Any]) -> str:
    if summary.get("high_priority_review_count"):
        return "高优先级模型分歧仍需人工复核。"
    if summary.get("high_divergence_count"):
        return "存在高分歧比赛，但当前未关联执行金额。"
    return "暂无高优先级分歧缺口。"


def recommended_next_action(summary: dict[str, Any]) -> str:
    if summary.get("high_priority_review_count"):
        return "优先复核高分歧且关联推荐下注的盘口；必要时降仓或保持 No Bet。"
    if summary.get("high_divergence_count"):
        return "把高分歧比赛保留在解释层，等待赔率和基本面更新。"
    return "继续作为每日模型一致性监控。"


def review_sort_key(row: dict[str, Any]) -> tuple[int, float, float]:
    priority_rank = {"高": 0, "中": 1, "低": 2}.get(str(row.get("review_priority")), 3)
    return (
        priority_rank,
        -float(row.get("linked_research_stake_aud") or 0),
        -float(row.get("max_disagreement") or 0),
    )


def snapshot_id(generated_at: str) -> str:
    return "model-divergence-review-" + generated_at.replace(":", "").replace("+", "-").replace(".", "-")


def row_key(match: Any, consensus_selection: Any, linked_selection: Any) -> str:
    return "|".join(str(item or "").strip() for item in [match, consensus_selection, linked_selection])


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not Path(path).exists():
            return {}
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_json(value: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "待校准"


def pp(value: Any) -> str:
    try:
        return f"{float(value) * 100:+.2f}pp"
    except (TypeError, ValueError):
        return "待校准"


def money(value: Any) -> str:
    try:
        return f"AUD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "AUD 0"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
