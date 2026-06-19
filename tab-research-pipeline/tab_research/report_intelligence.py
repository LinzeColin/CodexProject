from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .io import atomic_write_json, atomic_write_text
from .model_compare import MODEL_COMPARISON_JSON, OPEN_SOURCE_REFERENCES
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


REPORT_INTELLIGENCE_JSON_LATEST = "report_intelligence_latest.json"
REPORT_INTELLIGENCE_MD_LATEST = "report_intelligence_latest.md"
REPORT_INTELLIGENCE_PDF_LATEST = "report_intelligence_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def report_intelligence_run_json(run_id: str) -> str:
    return f"report_intelligence_{run_id}.json"


def report_intelligence_run_md(run_id: str) -> str:
    return f"report_intelligence_{run_id}.md"


def report_intelligence_run_pdf(run_id: str) -> str:
    return f"report_intelligence_{run_id}.pdf"


def write_report_intelligence_bundle(
    output_dir: Path,
    db_path: Path | None = None,
    *,
    json_name: str = REPORT_INTELLIGENCE_JSON_LATEST,
    markdown_name: str = REPORT_INTELLIGENCE_MD_LATEST,
    pdf_name: str = REPORT_INTELLIGENCE_PDF_LATEST,
    latest_commit_override: dict[str, Any] | None = None,
    report_index_override: dict[str, Any] | None = None,
    readiness_override: dict[str, Any] | None = None,
    candidate_override: dict[str, Any] | None = None,
    timeline_override: dict[str, Any] | None = None,
    backfill_override: dict[str, Any] | None = None,
    model_compare_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_report_intelligence(
        output_dir,
        db_path,
        latest_commit_override=latest_commit_override,
        report_index_override=report_index_override,
        readiness_override=readiness_override,
        candidate_override=candidate_override,
        timeline_override=timeline_override,
        backfill_override=backfill_override,
        model_compare_override=model_compare_override,
    )
    json_path = output_dir / json_name
    md_path = output_dir / markdown_name
    pdf_path = output_dir / pdf_name
    atomic_write_json(json_path, payload)
    markdown = render_report_intelligence_markdown(payload)
    atomic_write_text(md_path, markdown)
    pdf_summary = write_report_intelligence_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_report_intelligence(
    output_dir: Path,
    db_path: Path,
    *,
    latest_commit_override: dict[str, Any] | None = None,
    report_index_override: dict[str, Any] | None = None,
    readiness_override: dict[str, Any] | None = None,
    candidate_override: dict[str, Any] | None = None,
    timeline_override: dict[str, Any] | None = None,
    backfill_override: dict[str, Any] | None = None,
    model_compare_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    latest_commit = latest_commit_override or load_json(output_dir / "latest_commit.json")
    report_index = report_index_override or load_json(output_dir / "report_index_latest.json")
    readiness = readiness_override or load_json(output_dir / "automation_readiness_latest.json")
    candidate = candidate_override or load_json(output_dir / "automation_candidate_latest.json")
    timeline = timeline_override or load_json(output_dir / "active_timeline_latest.json")
    backfill = backfill_override or load_json(output_dir / "active_backfill_latest.json")
    model_compare = model_compare_override or load_json(output_dir / MODEL_COMPARISON_JSON)
    run_id = str(latest_commit.get("run_id") or report_index.get("latest_success_run_id") or "")
    recommendation_rows = fetch_recommendations(db_path, run_id, limit=12)
    board_exposure = fetch_board_exposure(db_path, run_id)
    report_runs = report_index.get("runs") or fetch_report_runs(db_path, limit=20)
    automation_runs = report_index.get("automation_runs") or fetch_automation_runs(db_path, limit=12)
    active_timeline_audits = fetch_active_timeline_audits(db_path, limit=12)
    reference_alignment = build_reference_alignment(
        output_dir=output_dir,
        db_path=db_path,
        latest_commit=latest_commit,
        report_index=report_index,
        readiness=readiness,
        timeline=timeline,
        model_compare=model_compare,
    )
    feature_counts = feature_status_counts(reference_alignment)
    next_actions = build_next_actions(readiness, timeline, backfill, candidate)
    automation_gates = build_automation_gates(readiness, candidate)
    report_history = build_report_history(report_runs, automation_runs)
    report_comparison = build_report_comparison(report_index)
    automation_dashboard = build_automation_dashboard(
        readiness=readiness,
        timeline=timeline,
        backfill=backfill,
        automation_gates=automation_gates,
        report_history=report_history,
        report_comparison=report_comparison,
        model_compare=model_compare,
        reference_alignment=reference_alignment,
    )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "report_intelligence",
        "purpose": "把推荐下注、报告历史、主动测试、开源模型对齐和自动化门禁合并成业务可读的日报决策层。",
        "executive_status": build_executive_status(latest_commit, readiness, report_index, timeline),
        "recommendation_summary": {
            "run_id": run_id,
            "display_note": "只展示研究建议，不自动下注；执行前需复核 TAB 实时赔率。",
            "top_count": len(recommendation_rows),
            "buy_count": sum(1 for row in recommendation_rows if row.get("action") == "买入"),
            "total_recommended_stake_aud": round(sum(float(row.get("stake_aud") or 0) for row in recommendation_rows), 2),
            "rows": recommendation_rows,
            "board_exposure": board_exposure,
        },
        "reference_alignment": reference_alignment,
        "feature_status_counts": feature_counts,
        "open_source_model_alignment": build_open_source_alignment(model_compare),
        "timeline_health": build_timeline_health(timeline, backfill, active_timeline_audits),
        "automation_gates": automation_gates,
        "automation_dashboard": automation_dashboard,
        "report_comparison": report_comparison,
        "report_history": report_history,
        "next_actions": next_actions,
        "public_artifacts": {
            "database": db_path.name if db_path.exists() else "",
            "latest_commit": "latest_commit.json" if (output_dir / "latest_commit.json").exists() else "",
            "report_index": "report_index_latest.json" if (output_dir / "report_index_latest.json").exists() else "",
            "active_timeline": "active_timeline_latest.json" if (output_dir / "active_timeline_latest.json").exists() else "",
            "model_comparison": MODEL_COMPARISON_JSON if (output_dir / MODEL_COMPARISON_JSON).exists() else "",
        },
    }
    return payload


def build_executive_status(
    latest_commit: dict[str, Any],
    readiness: dict[str, Any],
    report_index: dict[str, Any],
    timeline: dict[str, Any],
) -> dict[str, Any]:
    timeline_summary = timeline.get("summary") or {}
    publish_ready = bool(readiness.get("formal_report_publish_ready"))
    recurring_ready = bool(readiness.get("recurring_automation_ready"))
    current_action = "可使用上一份可信报告做人工复核" if latest_commit.get("run_id") else "等待生成第一份可信报告"
    if not publish_ready:
        current_action = "保留上一份可信报告；当前 attempted run 不发布为下注日报"
    return {
        "trusted_run_id": latest_commit.get("run_id", ""),
        "trusted_report_date": latest_commit.get("report_date", ""),
        "trusted_status": latest_commit.get("status", ""),
        "latest_success_run_id": report_index.get("latest_success_run_id", ""),
        "latest_attempt_run_id": (readiness.get("technical_preflight") or {}).get("run_id", ""),
        "formal_report_publish_ready": publish_ready,
        "recurring_automation_ready": recurring_ready,
        "active_timeline_backfill_queue_count": int(timeline_summary.get("backfill_queue_count") or 0),
        "active_timeline_missing_analysis_day_count": int(timeline_summary.get("missing_analysis_day_count") or 0),
        "active_timeline_missing_report_day_count": int(timeline_summary.get("missing_report_day_count") or 0),
        "current_action": current_action,
    }


def fetch_recommendations(db_path: Path, run_id: str, limit: int = 12) -> list[dict[str, Any]]:
    if not db_path.exists() or not run_id:
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT board_name, rank, event_name, market, selection, odds,
                   probability, expected_value, stake_aud, action, raw_json
            FROM recommendations
            WHERE run_id = ?
            ORDER BY
              CASE WHEN stake_aud > 0 THEN 0 ELSE 1 END,
              stake_aud DESC,
              COALESCE(expected_value, -999) DESC,
              rank ASC
            LIMIT ?
            """,
            (run_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [normalize_recommendation_row(row) for row in rows]


def normalize_recommendation_row(row: sqlite3.Row) -> dict[str, Any]:
    raw = parse_json(row["raw_json"])
    odds = optional_float(row["odds"])
    probability = optional_float(row["probability"])
    breakeven = (1.0 / odds) if odds and odds > 0 else None
    edge = (probability - breakeven) if probability is not None and breakeven is not None else None
    expected_value = optional_float(row["expected_value"])
    stake = float(row["stake_aud"] or 0)
    return {
        "board": str(row["board_name"] or ""),
        "rank": int(row["rank"] or 0),
        "event": str(row["event_name"] or ""),
        "market": str(row["market"] or ""),
        "selection": str(row["selection"] or ""),
        "odds": odds,
        "probability": probability,
        "breakeven_probability": breakeven,
        "probability_edge": edge,
        "expected_value": expected_value,
        "stake_aud": round(stake, 2),
        "action": "买入" if stake > 0 else "观察/不下注",
        "analysis_consistency": consistency_label(raw),
        "confidence": confidence_label(raw),
        "value_label": value_label(expected_value, edge, stake),
        "reason": recommendation_reason(probability, breakeven, edge, expected_value, stake, raw),
    }


def fetch_board_exposure(db_path: Path, run_id: str) -> list[dict[str, Any]]:
    if not db_path.exists() or not run_id:
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT board_name,
                   COUNT(*) AS recommendation_count,
                   SUM(CASE WHEN stake_aud > 0 THEN 1 ELSE 0 END) AS buy_count,
                   SUM(stake_aud) AS stake_aud,
                   AVG(expected_value) AS avg_expected_value
            FROM recommendations
            WHERE run_id = ?
            GROUP BY board_name
            ORDER BY SUM(stake_aud) DESC, COUNT(*) DESC
            """,
            (run_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "board": str(row["board_name"] or ""),
            "recommendation_count": int(row["recommendation_count"] or 0),
            "buy_count": int(row["buy_count"] or 0),
            "stake_aud": round(float(row["stake_aud"] or 0), 2),
            "avg_expected_value": optional_float(row["avg_expected_value"]),
        }
        for row in rows
    ]


def fetch_report_runs(db_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT run_id, status, report_date, started_at, finished_at,
                   technical_ready, raw_refresh_ready, safety_ready,
                   portfolio_ready, time_adjusted_new_exposure_aud
            FROM report_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "run_id": row["run_id"],
            "status": row["status"],
            "report_date": row["report_date"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "technical_ready": bool(row["technical_ready"]),
            "raw_refresh_ready": bool(row["raw_refresh_ready"]),
            "safety_ready": bool(row["safety_ready"]),
            "portfolio_ready": bool(row["portfolio_ready"]),
            "time_adjusted_new_exposure_aud": float(row["time_adjusted_new_exposure_aud"] or 0),
        }
        for row in rows
    ]


def fetch_automation_runs(db_path: Path, limit: int = 12) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT automation_run_id, mode, verify_mode, status, exit_code,
                   started_at, finished_at, formal_report_publish_ready,
                   recurring_automation_ready, raw_refresh_ready
            FROM automation_runs
            ORDER BY started_at DESC, automation_run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "automation_run_id": row["automation_run_id"],
            "mode": row["mode"],
            "verify_mode": row["verify_mode"],
            "status": row["status"],
            "exit_code": int(row["exit_code"] or 0),
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "formal_report_publish_ready": bool(row["formal_report_publish_ready"]),
            "recurring_automation_ready": bool(row["recurring_automation_ready"]),
            "raw_refresh_ready": bool(row["raw_refresh_ready"]),
        }
        for row in rows
    ]


def fetch_active_timeline_audits(db_path: Path, limit: int = 12) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'active_timeline_audits'"
        ).fetchone()
        if not table_exists:
            return []
        rows = conn.execute(
            """
            SELECT audit_id, generated_at, timezone, day_count, complete_day_count,
                   missing_analysis_day_count, missing_report_day_count, backfill_queue_count,
                   cadence_ready_for_all_days, formal_report_ready_for_all_days,
                   backfill_status, raw_refresh_ready, raw_refresh_status
            FROM active_timeline_audits
            ORDER BY generated_at DESC, audit_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    normalized = [
        {
            "audit_id": row["audit_id"],
            "generated_at": row["generated_at"],
            "timezone": row["timezone"],
            "day_count": int(row["day_count"] or 0),
            "complete_day_count": int(row["complete_day_count"] or 0),
            "missing_analysis_day_count": int(row["missing_analysis_day_count"] or 0),
            "missing_report_day_count": int(row["missing_report_day_count"] or 0),
            "backfill_queue_count": int(row["backfill_queue_count"] or 0),
            "cadence_ready_for_all_days": bool(row["cadence_ready_for_all_days"]),
            "formal_report_ready_for_all_days": bool(row["formal_report_ready_for_all_days"]),
            "backfill_status": row["backfill_status"],
            "raw_refresh_ready": bool(row["raw_refresh_ready"]),
            "raw_refresh_status": row["raw_refresh_status"],
        }
        for row in rows
    ]
    return list(reversed(normalized))


def build_reference_alignment(
    *,
    output_dir: Path,
    db_path: Path,
    latest_commit: dict[str, Any],
    report_index: dict[str, Any],
    readiness: dict[str, Any],
    timeline: dict[str, Any],
    model_compare: dict[str, Any],
) -> list[dict[str, str]]:
    timeline_summary = timeline.get("summary") or {}
    bootstrap = readiness.get("private_position_bootstrap") or {}
    implemented_refs = (model_compare.get("source_adoption") or {}).get("implemented_reference_count", 0)
    return [
        alignment_row(
            "4-5 小时一次分析节奏",
            "参考版定时 refresh_runs；用户要求每天至少四次。",
            "主动测试按 5 个时间窗回测有效分析次数，并生成缺口队列。",
            "已落地" if timeline_summary.get("cadence_ready_for_all_days") else "部分落地",
            "缺口日需要安全补跑；正式 automation 尚需用户授权。",
        ),
        alignment_row(
            "每日一份中文报告",
            "参考版每日 Markdown/报告输出；用户要求 PDF 保存到本地报告夹。",
            "正式 PDF、report index、Downloads app 已接入；失败门禁时保留上次可信报告。",
            "已落地" if timeline_summary.get("formal_report_ready_for_all_days") else "部分落地",
            "当前日期序列仍有日报缺口，需要补跑后复测。",
        ),
        alignment_row(
            "本地数据库与新旧对比",
            "参考版 SQLite 记录 predictions/reports/backtests。",
            "本系统使用 SQLite 记录 run、板块、推荐、图表、diff、缺失数据和审计。",
            "已落地" if db_path.exists() and int(report_index.get("run_count") or 0) > 0 else "阻塞",
            "继续补足真实赛果/结算字段后可做完整命中率回测。",
        ),
        alignment_row(
            "业务首页 Dashboard",
            "参考版有 dashboard API；用户要求一眼能知道怎么操作。",
            "Downloads app 首屏展示推荐下注板块、金额、EV、概率/赔率编辑和主动测试按钮。",
            "已落地" if (output_dir / "tab_fifa_dashboard_latest.html").exists() else "部分落地",
            "继续减少工程状态词，把缺口、赔率变化和行动建议前置。",
        ),
        alignment_row(
            "开源模型参考",
            "用户要求参考 GitHub 开源版本模型。",
            "已桥接 Elo、Dixon-Coles、goalmodel 思路，输出模型分歧和能力覆盖。",
            "已落地" if int(implemented_refs or 0) >= 2 else "部分落地",
            "下一步把晋级路径 Monte Carlo 与赛果回测连到同一评价表。",
        ),
        alignment_row(
            "主动回测/缺失补齐",
            "参考版 backtests + refresh_runs；用户要求缺失则主动补上。",
            "主动测试可识别缺失分析和日报；补跑使用 no-latest-publish 重建模式。",
            "部分落地",
            "补跑不能伪装历史原时点盘口；需要标记为当前数据重建。",
        ),
        alignment_row(
            "私有持仓读取",
            "用户要求能自动读取 TAB 已下注状态。",
            "已有只读专用浏览器 profile 和导入链，但当前未完成私有快照 bootstrap。",
            "已落地" if bootstrap.get("ready") else "阻塞",
            "需要一次性完成本地浏览器授权；系统不保存密码、不自动下注。",
        ),
        alignment_row(
            "自动化准入门禁",
            "参考版 scheduler 可每 4 小时跑；用户要求成熟后再进入 automation。",
            "已有 hermetic verifier、public safety、PDF QA、raw freshness、report publish gates。",
            "已落地" if latest_commit.get("technical_automation_ready") else "部分落地",
            "正式 recurring automation 仍处于用户未授权状态。",
        ),
    ]


def alignment_row(feature: str, reference: str, current: str, status: str, gap: str) -> dict[str, str]:
    return {
        "feature": feature,
        "reference_requirement": reference,
        "current_implementation": current,
        "status": status,
        "next_gap": gap,
    }


def feature_status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status") or "未知"
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_open_source_alignment(model_compare: dict[str, Any]) -> dict[str, Any]:
    source_adoption = model_compare.get("source_adoption") or {}
    references = model_compare.get("references") or OPEN_SOURCE_REFERENCES
    return {
        "reference_count": int(source_adoption.get("reference_count") or len(references)),
        "implemented_reference_count": int(source_adoption.get("implemented_reference_count") or 0),
        "design_reference_count": int(source_adoption.get("design_reference_count") or 0),
        "coverage_counts": source_adoption.get("coverage_counts") or {},
        "rows": [
            {
                "name": ref.get("display_name") or ref.get("name", ""),
                "method_family": ref.get("method_family", ""),
                "license": ref.get("license", ""),
                "adoption_status": adoption_status_label(ref.get("adoption_status", "")),
                "usage": ref.get("report_usage", ""),
            }
            for ref in references
        ],
    }


def build_timeline_health(
    timeline: dict[str, Any],
    backfill: dict[str, Any],
    active_timeline_audits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    summary = timeline.get("summary") or {}
    cadence_rule = timeline.get("cadence_rule") or {}
    recent_days = (timeline.get("days") or [])[-8:]
    target_slots = [str(slot) for slot in (cadence_rule.get("target_slots") or [])]
    audit_history = build_timeline_audit_history(active_timeline_audits or [])
    return {
        "generated_at": timeline.get("generated_at", ""),
        "min_analyses_per_day": cadence_rule.get("min_analyses_per_day", 4),
        "target_slots": target_slots,
        "day_count": int(summary.get("day_count") or 0),
        "complete_day_count": int(summary.get("complete_day_count") or 0),
        "missing_analysis_day_count": int(summary.get("missing_analysis_day_count") or 0),
        "missing_report_day_count": int(summary.get("missing_report_day_count") or 0),
        "backfill_queue_count": int(summary.get("backfill_queue_count") or 0),
        "backfill_last_status": backfill.get("status") or backfill.get("mode") or "not_run",
        "slot_coverage": build_slot_coverage(recent_days, target_slots),
        "slot_heatmap": build_slot_heatmap(recent_days, target_slots),
        "audit_history_count": len(audit_history),
        "audit_history": audit_history,
        "audit_trend_summary": build_timeline_audit_trend_summary(audit_history),
        "recent_days": [
            {
                "date": item.get("display_date", ""),
                "effective_analysis_count": int(item.get("effective_analysis_count") or 0),
                "formal_report_exists": bool(item.get("formal_report_exists")),
                "needs_backfill": bool(item.get("needs_backfill")),
                "reason": "；".join(item.get("backfill_reasons") or []),
            }
            for item in recent_days
        ],
    }


def build_timeline_audit_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    history = []
    for row in rows[-12:]:
        day_count = int(row.get("day_count") or 0)
        complete = int(row.get("complete_day_count") or 0)
        gap_count = int(row.get("missing_analysis_day_count") or 0) + int(row.get("missing_report_day_count") or 0)
        complete_ratio = (complete / day_count) if day_count else 0.0
        history.append(
            {
                "audit_id": row.get("audit_id", ""),
                "generated_at": row.get("generated_at", ""),
                "label": timeline_audit_label(str(row.get("generated_at") or "")),
                "day_count": day_count,
                "complete_day_count": complete,
                "complete_ratio": complete_ratio,
                "missing_analysis_day_count": int(row.get("missing_analysis_day_count") or 0),
                "missing_report_day_count": int(row.get("missing_report_day_count") or 0),
                "gap_count": gap_count,
                "backfill_queue_count": int(row.get("backfill_queue_count") or 0),
                "raw_refresh_ready": bool(row.get("raw_refresh_ready")),
                "raw_refresh_status": row.get("raw_refresh_status", ""),
                "backfill_status": row.get("backfill_status", ""),
            }
        )
    return history


def build_timeline_audit_trend_summary(history: list[dict[str, Any]]) -> dict[str, Any]:
    if not history:
        return {
            "audit_count": 0,
            "latest_complete_ratio": 0.0,
            "latest_gap_count": 0,
            "raw_ready_audit_count": 0,
            "trend_direction": "insufficient_history",
        }
    latest = history[-1]
    first = history[0]
    delta = float(latest.get("complete_ratio") or 0) - float(first.get("complete_ratio") or 0)
    if len(history) < 2:
        direction = "baseline_only"
    elif delta > 0.001:
        direction = "improving"
    elif delta < -0.001:
        direction = "deteriorating"
    else:
        direction = "flat"
    return {
        "audit_count": len(history),
        "latest_complete_ratio": float(latest.get("complete_ratio") or 0),
        "latest_gap_count": int(latest.get("gap_count") or 0),
        "raw_ready_audit_count": sum(1 for row in history if row.get("raw_refresh_ready")),
        "trend_direction": direction,
    }


def timeline_audit_label(value: str) -> str:
    if not value:
        return ""
    return value.replace("T", " ")[5:16]


def build_slot_coverage(days: list[dict[str, Any]], target_slots: list[str]) -> list[dict[str, Any]]:
    rows = []
    total_days = len(days)
    for slot in target_slots:
        covered_count = sum(1 for item in days if slot in set(item.get("covered_slots") or []))
        rows.append(
            {
                "slot": slot,
                "label": short_slot_label(slot),
                "covered_day_count": covered_count,
                "day_count": total_days,
                "coverage_ratio": (covered_count / total_days) if total_days else 0.0,
            }
        )
    return rows


def build_slot_heatmap(days: list[dict[str, Any]], target_slots: list[str]) -> list[dict[str, Any]]:
    rows = []
    for item in days:
        covered_slots = set(item.get("covered_slots") or [])
        missing_slots = set(item.get("missing_slots") or [])
        cells = []
        for slot in target_slots:
            status = "covered" if slot in covered_slots else "missing" if slot in missing_slots else "unknown"
            cells.append({"slot": slot, "label": short_slot_label(slot), "status": status})
        rows.append(
            {
                "date": item.get("display_date", ""),
                "effective_analysis_count": int(item.get("effective_analysis_count") or 0),
                "formal_report_exists": bool(item.get("formal_report_exists")),
                "needs_backfill": bool(item.get("needs_backfill")),
                "reason": "；".join(item.get("backfill_reasons") or []),
                "cells": cells,
            }
        )
    return rows


def short_slot_label(slot: str) -> str:
    return str(slot or "").replace(":00", "").replace("-", "-")


def build_automation_gates(readiness: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    bootstrap = readiness.get("private_position_bootstrap") or {}
    raw_refresh = readiness.get("raw_refresh") or {}
    return {
        "formal_report_publish_ready": bool(readiness.get("formal_report_publish_ready")),
        "recurring_automation_ready": bool(readiness.get("recurring_automation_ready")),
        "raw_refresh_ready": bool(raw_refresh.get("ready", readiness.get("raw_refresh_ready"))),
        "public_safety_ready": bool((readiness.get("public_safety") or {}).get("output_safety_ready", readiness.get("public_safety_ready"))),
        "technical_preflight_ready": bool((readiness.get("technical_preflight") or {}).get("ready", readiness.get("technical_preflight_ready"))),
        "private_position_ready": bool(bootstrap.get("ready")),
        "candidate_status": candidate.get("status", ""),
        "candidate_next_action": candidate.get("next_action", ""),
    }


def build_report_history(report_runs: list[dict[str, Any]], automation_runs: list[dict[str, Any]]) -> dict[str, Any]:
    success_runs = [run for run in report_runs if run.get("status") == "ready_for_manual_report"]
    blocked_runs = [run for run in report_runs if "blocked" in str(run.get("status") or "")]
    return {
        "run_count": len(report_runs),
        "success_run_count": len(success_runs),
        "blocked_run_count": len(blocked_runs),
        "automation_run_count": len(automation_runs),
        "recent_runs": [
            {
                "run_id": run.get("run_id", ""),
                "date": run.get("report_date", ""),
                "status": run.get("status", ""),
                "exposure_aud": round(float(run.get("time_adjusted_new_exposure_aud") or 0), 2),
                "recommendation_count": int((run.get("counts") or {}).get("recommendations") or 0),
            }
            for run in report_runs[:10]
        ],
    }


def build_report_comparison(report_index: dict[str, Any]) -> dict[str, Any]:
    runs = report_index.get("runs") or []
    latest_run = runs[0] if runs else {}
    summary = (
        latest_run.get("compare_summary")
        or report_index.get("diff_summary")
        or (report_index.get("latest_commit") or {}).get("diff_summary")
        or {}
    )
    artifact_refs = latest_run.get("artifact_refs") or {}
    return {
        "run_id": latest_run.get("run_id") or report_index.get("latest_success_run_id", ""),
        "report_date": latest_run.get("report_date") or (report_index.get("latest_commit") or {}).get("report_date", ""),
        "run_status": latest_run.get("status") or (report_index.get("latest_commit") or {}).get("status", ""),
        "added_count": int(summary.get("added_count") or 0),
        "removed_count": int(summary.get("removed_count") or 0),
        "changed_count": int(summary.get("changed_count") or 0),
        "retained_count": int(summary.get("retained_count") or 0),
        "exposure_change_aud": round(float(summary.get("exposure_change_aud") or 0), 2),
        "visual_chart_count": int((latest_run.get("counts") or {}).get("visual_charts") or 0),
        "recommendation_count": int((latest_run.get("counts") or {}).get("recommendations") or 0),
        "report_index_run_count": int(report_index.get("run_count") or len(runs)),
        "automation_run_count": int(report_index.get("automation_run_count") or len(report_index.get("automation_runs") or [])),
        "has_diff": bool(summary),
        "artifact_pdf": artifact_refs.get("pdf_report", ""),
    }


def build_automation_dashboard(
    *,
    readiness: dict[str, Any],
    timeline: dict[str, Any],
    backfill: dict[str, Any],
    automation_gates: dict[str, Any],
    report_history: dict[str, Any],
    report_comparison: dict[str, Any],
    model_compare: dict[str, Any],
    reference_alignment: list[dict[str, str]],
) -> dict[str, Any]:
    summary = timeline.get("summary") or {}
    source_adoption = model_compare.get("source_adoption") or {}
    ref_count = int(source_adoption.get("reference_count") or len(OPEN_SOURCE_REFERENCES))
    implemented_refs = int(source_adoption.get("implemented_reference_count") or 0)
    day_count = int(summary.get("day_count") or 0)
    complete_days = int(summary.get("complete_day_count") or 0)
    cadence_score = (complete_days / day_count) if day_count else 0.0
    rows = [
        operation_row(
            "公开盘口 raw",
            automation_gates.get("raw_refresh_ready"),
            1.0 if automation_gates.get("raw_refresh_ready") else 0.0,
            raw_gate_evidence(readiness),
            "先恢复 5 个 TAB FIFA 板块 raw freshness，再允许补跑或发布。",
        ),
        operation_row(
            "4-5小时分析节奏",
            bool(summary.get("cadence_ready_for_all_days")),
            cadence_score,
            f"{complete_days}/{day_count} 天完整；待补队列 {int(summary.get('backfill_queue_count') or 0)}。",
            "点击主动测试并按补跑优先队列修复缺口。",
        ),
        operation_row(
            "每日PDF报告",
            bool(summary.get("formal_report_ready_for_all_days")),
            1.0 if summary.get("formal_report_ready_for_all_days") else 0.0,
            f"日报缺口日 {int(summary.get('missing_report_day_count') or 0)}。",
            "raw ready 后安全补跑缺失日报；补跑不发布 latest。",
        ),
        operation_row(
            "本地数据库",
            int(report_history.get("run_count") or 0) > 0,
            1.0 if int(report_history.get("run_count") or 0) > 0 else 0.0,
            f"report_runs {report_history.get('run_count', 0)}；automation_runs {report_history.get('automation_run_count', 0)}。",
            "继续把每次报告、审计、补跑和对比写入 SQLite。",
        ),
        operation_row(
            "新旧报告对比",
            bool(report_comparison.get("has_diff")),
            1.0 if report_comparison.get("has_diff") else 0.0,
            f"新增 {report_comparison.get('added_count', 0)} / 移除 {report_comparison.get('removed_count', 0)} / 变化 {report_comparison.get('changed_count', 0)}。",
            "每份新报告必须展示与上一可信报告的变化。",
        ),
        operation_row(
            "开源模型参考",
            implemented_refs >= 2,
            (implemented_refs / ref_count) if ref_count else 0.0,
            f"已转化 {implemented_refs}/{ref_count} 个 GitHub 参考；覆盖 {len(source_adoption.get('coverage_counts') or {})} 类能力。",
            "下一步接入真实赛果 track record、校准曲线和淘汰赛 Monte Carlo。",
        ),
        operation_row(
            "发布门禁",
            automation_gates.get("formal_report_publish_ready"),
            1.0 if automation_gates.get("formal_report_publish_ready") else 0.0,
            f"formal_report_publish_ready={bool(automation_gates.get('formal_report_publish_ready'))}。",
            "fresh raw + private snapshot + preflight + public safety 全部通过才发布。",
        ),
        operation_row(
            "私有持仓快照",
            automation_gates.get("private_position_ready"),
            1.0 if automation_gates.get("private_position_ready") else 0.0,
            private_position_evidence(readiness),
            "完成只读持仓读取 bootstrap，更新已下注金额和累计收益率。",
        ),
    ]
    ready_count = sum(1 for row in rows if row["ready"])
    blocked_count = sum(1 for row in rows if row["status"] == "阻塞")
    avg_score = sum(float(row["score"]) for row in rows) / len(rows) if rows else 0.0
    return {
        "title": "Automation Operations Dashboard",
        "reading_path": "先看 raw 和发布门禁，再看主动测试缺口、补跑队列、私有持仓，最后看开源模型和新旧报告对比。",
        "ready_count": ready_count,
        "blocked_count": blocked_count,
        "watch_count": len(rows) - ready_count - blocked_count,
        "average_score": avg_score,
        "rows": rows,
        "reference_feature_count": len(reference_alignment),
    }


def operation_row(label: str, ready: Any, score: float, evidence: str, next_action: str) -> dict[str, Any]:
    normalized = max(0.0, min(1.0, float(score or 0)))
    is_ready = bool(ready)
    if is_ready:
        status = "就绪"
    elif normalized > 0:
        status = "部分"
    else:
        status = "阻塞"
    return {
        "label": label,
        "ready": is_ready,
        "status": status,
        "score": normalized,
        "score_pct": round(normalized * 100, 2),
        "evidence": evidence,
        "next_action": next_action,
    }


def raw_gate_evidence(readiness: dict[str, Any]) -> str:
    raw = readiness.get("raw_refresh") or {}
    blockers = raw.get("blocker_codes") or readiness.get("raw_refresh_blocker_codes") or []
    if blockers:
        return f"raw_refresh.ready={bool(raw.get('ready'))}；blockers={', '.join(str(item) for item in blockers)}。"
    return f"raw_refresh.ready={bool(raw.get('ready', readiness.get('raw_refresh_ready')))}。"


def private_position_evidence(readiness: dict[str, Any]) -> str:
    bootstrap = readiness.get("private_position_bootstrap") or {}
    status = bootstrap.get("status") or ("ready" if bootstrap.get("ready") else "not_ready")
    report_date = bootstrap.get("report_date", "")
    return f"status={status}；report_date={report_date}。"


def build_next_actions(
    readiness: dict[str, Any],
    timeline: dict[str, Any],
    backfill: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, str]]:
    summary = timeline.get("summary") or {}
    actions: list[dict[str, str]] = []
    if int(summary.get("backfill_queue_count") or 0) > 0:
        actions.append(
            next_action(
                "P0",
                "补齐主动测试发现的缺口",
                "运行安全补跑后重新点击主动测试，目标是每日至少 4 次分析且 1 份报告。",
                "提升日报连续性；补跑报告仍标记为重建版本。",
            )
        )
    raw = readiness.get("raw_refresh") or {}
    if raw.get("ready") is False or readiness.get("formal_report_publish_ready") is False:
        actions.append(
            next_action(
                "P0",
                "刷新实时公开盘口并重跑日报",
                "先让 5 个 TAB FIFA 板块 raw snapshot 回到 freshness 门槛内，再运行日报。",
                "解决当前 attempted run 不能发布的问题之一。",
            )
        )
    bootstrap = readiness.get("private_position_bootstrap") or {}
    if not bootstrap.get("ready"):
        actions.append(
            next_action(
                "P0",
                "完成私有持仓读取 bootstrap",
                "使用本地只读浏览器 profile 完成一次授权，然后导入当日持仓快照。",
                "同步已下注金额、未结算暴露和累计收益率所必需。",
            )
        )
    if not readiness.get("recurring_automation_ready"):
        actions.append(
            next_action(
                "P1",
                "等待用户授权后安装 recurring automation",
                "保持当前手动触发；成熟后再接入每 4-5 小时一次的调度。",
                "避免在门禁未清前产生误导性自动日报。",
            )
        )
    if not backfill:
        actions.append(
            next_action(
                "P1",
                "生成第一次补跑结果记录",
                "主动测试之后保存 active_backfill_latest.json，供下一版报告做对比。",
                "让报告能区分未运行、已补跑、补跑失败三种状态。",
            )
        )
    actions.append(
        next_action(
            "P2",
            "接入赛果与结算结果",
            "为每条历史建议增加结果、命中率、Brier/log-loss 和资金曲线字段。",
            "把现在的节奏回测升级为真实下注研究回测。",
        )
    )
    if candidate.get("next_action") and not any(candidate.get("next_action") in item["operation"] for item in actions):
        actions.append(
            next_action("P2", "复核自动化候选状态", str(candidate.get("next_action")), "对齐候选配置与当前门禁。")
        )
    return actions[:6]


def next_action(priority: str, title: str, operation: str, expected_effect: str) -> dict[str, str]:
    return {
        "priority": priority,
        "title": title,
        "operation": operation,
        "expected_effect": expected_effect,
    }


def render_report_intelligence_markdown(payload: dict[str, Any]) -> str:
    status = payload.get("executive_status") or {}
    rec = payload.get("recommendation_summary") or {}
    timeline = payload.get("timeline_health") or {}
    automation_dashboard = payload.get("automation_dashboard") or {}
    report_comparison = payload.get("report_comparison") or {}
    lines = [
        "# TAB FIFA 盘口研究智能层",
        "",
        "本报告把下注推荐、报告历史、主动测试、开源模型对齐和自动化门禁合并成一个业务可读视图。它只提供研究建议，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- 当前可信报告日期：`{status.get('trusted_report_date', '')}`",
        f"- 当前可信 run：`{status.get('trusted_run_id', '')}`",
        f"- 当前操作判断：{status.get('current_action', '')}",
        f"- 推荐买入候选：`{rec.get('buy_count', 0)}` 条，展示金额合计 `AUD {float(rec.get('total_recommended_stake_aud') or 0):,.2f}`",
        f"- 主动测试缺口：分析缺口日 `{timeline.get('missing_analysis_day_count', 0)}`，日报缺口日 `{timeline.get('missing_report_day_count', 0)}`，待补队列 `{timeline.get('backfill_queue_count', 0)}`",
        "",
        "## Automation Dashboard",
        "",
        f"- 读取路径：{automation_dashboard.get('reading_path', '')}",
        f"- 就绪项：`{automation_dashboard.get('ready_count', 0)}`，阻塞项：`{automation_dashboard.get('blocked_count', 0)}`，平均得分：`{fmt_pct(automation_dashboard.get('average_score'))}`",
        "",
        "| 模块 | 状态 | 得分 | 证据 | 下一步 |",
        "|---|---|---:|---|---|",
    ]
    for row in automation_dashboard.get("rows") or []:
        lines.append(
            f"| {md_cell(row.get('label'))} | {md_cell(row.get('status'))} | {fmt_pct(row.get('score'))} | {md_cell(row.get('evidence'))} | {md_cell(row.get('next_action'))} |"
        )
    lines.extend(
        [
            "",
            "## 新旧报告对比与本地数据库",
            "",
            f"- 对比 run：`{report_comparison.get('run_id', '')}`，报告日期：`{report_comparison.get('report_date', '')}`，状态：`{report_comparison.get('run_status', '')}`",
            f"- 新增 `{report_comparison.get('added_count', 0)}`，移除 `{report_comparison.get('removed_count', 0)}`，变化 `{report_comparison.get('changed_count', 0)}`，保留 `{report_comparison.get('retained_count', 0)}`。",
            f"- 暴露变化：`AUD {float(report_comparison.get('exposure_change_aud') or 0):,.2f}`；图表 `{report_comparison.get('visual_chart_count', 0)}`；推荐 `{report_comparison.get('recommendation_count', 0)}`。",
            "",
        ]
    )
    lines.extend(
        [
        "## 推荐下注板块",
        "",
        "| 板块 | 盘口 | 下注 | 赔率 | 概率 | EV | 金额 | 一致性 | 置信度 | 原因 |",
        "|---|---|---|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for row in (rec.get("rows") or [])[:10]:
        lines.append(
            "| {board} | {event} / {market} | {selection} | {odds} | {prob} | {ev} | AUD {stake:,.0f} | {consistency} | {confidence} | {reason} |".format(
                board=md_cell(row.get("board")),
                event=md_cell(row.get("event")),
                market=md_cell(row.get("market")),
                selection=md_cell(row.get("selection")),
                odds=f"{float(row.get('odds') or 0):.2f}" if row.get("odds") else "",
                prob=fmt_pct(row.get("probability")),
                ev=fmt_pct(row.get("expected_value")),
                stake=float(row.get("stake_aud") or 0),
                consistency=md_cell(row.get("analysis_consistency")),
                confidence=md_cell(row.get("confidence")),
                reason=md_cell(row.get("reason")),
            )
        )
    slot_headers = [str(row.get("label", "")) for row in (timeline.get("slot_coverage") or [])]
    lines.extend(["", "## 主动测试时间线热力图", ""])
    if slot_headers:
        lines.append("| 日期 | " + " | ".join(md_cell(slot) for slot in slot_headers) + " | 有效分析 | 日报 | 状态 |")
        lines.append("|---|" + "|".join("---" for _ in slot_headers) + "|---:|---|---|")
        for row in timeline.get("slot_heatmap") or []:
            cell_labels = [slot_status_label((cell or {}).get("status")) for cell in row.get("cells") or []]
            lines.append(
                "| {date} | {cells} | {count} | {report} | {status} |".format(
                    date=md_cell(row.get("date")),
                    cells=" | ".join(md_cell(cell) for cell in cell_labels),
                    count=int(row.get("effective_analysis_count") or 0),
                    report="有" if row.get("formal_report_exists") else "缺失",
                    status="缺口" if row.get("needs_backfill") else "完整",
                )
            )
    else:
        lines.append("暂无主动测试时段覆盖数据。")
    trend = timeline.get("audit_trend_summary") or {}
    lines.extend(
        [
            "",
            "## 主动测试历史趋势",
            "",
            f"- 历史审计次数：`{trend.get('audit_count', 0)}`",
            f"- 最新完整率：`{fmt_pct(trend.get('latest_complete_ratio'))}`",
            f"- 最新缺口数：`{trend.get('latest_gap_count', 0)}`",
            f"- Raw 可用审计次数：`{trend.get('raw_ready_audit_count', 0)}`",
            f"- 趋势方向：`{trend.get('trend_direction', 'insufficient_history')}`",
            "",
            "| 审计时间 | 完整率 | 缺口数 | 补跑队列 | Raw | 补跑状态 |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for row in timeline.get("audit_history") or []:
        lines.append(
            "| {label} | {ratio} | {gap} | {queue} | {raw} | {backfill} |".format(
                label=md_cell(row.get("label")),
                ratio=fmt_pct(row.get("complete_ratio")),
                gap=int(row.get("gap_count") or 0),
                queue=int(row.get("backfill_queue_count") or 0),
                raw="ready" if row.get("raw_refresh_ready") else md_cell(row.get("raw_refresh_status")),
                backfill=md_cell(row.get("backfill_status")),
            )
        )
    lines.extend(
        [
            "",
            "## 功能成熟度对齐",
            "",
            "| 功能 | 当前状态 | 当前实现 | 下一步 |",
            "|---|---|---|---|",
        ]
    )
    for row in payload.get("reference_alignment") or []:
        lines.append(
            f"| {md_cell(row.get('feature'))} | {md_cell(row.get('status'))} | {md_cell(row.get('current_implementation'))} | {md_cell(row.get('next_gap'))} |"
        )
    lines.extend(
        [
            "",
            "## 开源模型参考采用",
            "",
            "| 参考 | 方法 | 许可 | 采用状态 | 用法 |",
            "|---|---|---|---|---|",
        ]
    )
    for row in (payload.get("open_source_model_alignment") or {}).get("rows") or []:
        lines.append(
            f"| {md_cell(row.get('name'))} | {md_cell(row.get('method_family'))} | {md_cell(row.get('license'))} | {md_cell(row.get('adoption_status'))} | {md_cell(row.get('usage'))} |"
        )
    lines.extend(["", "## 下一步", "", "| 优先级 | 事项 | 操作 | 预期效果 |", "|---|---|---|---|"])
    for item in payload.get("next_actions") or []:
        lines.append(
            f"| {md_cell(item.get('priority'))} | {md_cell(item.get('title'))} | {md_cell(item.get('operation'))} | {md_cell(item.get('expected_effect'))} |"
        )
    return "\n".join(lines)


def write_report_intelligence_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    status = payload.get("executive_status") or {}
    rec = payload.get("recommendation_summary") or {}
    timeline = payload.get("timeline_health") or {}
    gates = payload.get("automation_gates") or {}
    model = payload.get("open_source_model_alignment") or {}
    automation_dashboard = payload.get("automation_dashboard") or {}
    report_comparison = payload.get("report_comparison") or {}
    report_history = payload.get("report_history") or {}
    trend = timeline.get("audit_trend_summary") or {}
    charts = [
        chart_from_items("Automation Dashboard", automation_dashboard_items(automation_dashboard), "#1F4E79"),
        chart_from_items("功能成熟度", feature_status_items(payload.get("feature_status_counts") or {}), "#1F4E79"),
        chart_from_items("板块金额分配", board_exposure_items(rec.get("board_exposure") or []), "#C62828"),
        chart_from_items("推荐 EV Top", recommendation_ev_items(rec.get("rows") or []), "#247A5A"),
        chart_from_items("主动测试缺口", timeline_gap_items(timeline), "#A56710"),
        chart_from_items("主动测试时段覆盖", timeline_slot_items(timeline), "#1D4ED8"),
        chart_from_items("主动测试完整率趋势", timeline_audit_complete_items(timeline), "#247A5A"),
        chart_from_items("自动化门禁", gate_items(gates), "#6A4C93"),
        chart_from_items("报告历史", report_history_items(report_history), "#1F4E79"),
        chart_from_items("开源采用状态", open_source_items(model), "#247A5A"),
        chart_from_items("开源能力覆盖", open_source_coverage_items(model), "#A56710"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 盘口研究智能层",
        subtitle="推荐下注、主动测试、开源模型、报告历史和自动化门禁汇总；仅用于研究分析，不自动下注。",
        summary_rows=[
            ("可信报告日期", str(status.get("trusted_report_date", ""))),
            ("可信 run", short_id(status.get("trusted_run_id", ""))),
            ("当前判断", str(status.get("current_action", ""))),
            ("买入候选", str(rec.get("buy_count", 0))),
            ("展示金额", f"AUD {float(rec.get('total_recommended_stake_aud') or 0):,.0f}"),
            ("缺口队列", str(timeline.get("backfill_queue_count", 0))),
            ("运营得分", fmt_pct(automation_dashboard.get("average_score"))),
            ("报告对比", f"+{report_comparison.get('added_count', 0)} / Δ{report_comparison.get('changed_count', 0)}"),
            ("历史审计", f"{int(trend.get('audit_count') or 0)} 次 / 完整率 {fmt_pct(trend.get('latest_complete_ratio'))}"),
            ("开源参考", f"{int(model.get('implemented_reference_count') or 0)}/{int(model.get('reference_count') or 0)}"),
        ],
        charts=charts,
        table_headers=["板块", "盘口", "下注", "赔率", "概率", "EV", "金额", "置信度"],
        table_rows=pdf_recommendation_rows(rec.get("rows") or []),
        extra_tables=[
            {
                "title": "Automation Dashboard",
                "headers": ["模块", "状态", "得分", "证据", "下一步"],
                "rows": [
                    [
                        row.get("label", ""),
                        row.get("status", ""),
                        fmt_pct(row.get("score")),
                        row.get("evidence", ""),
                        row.get("next_action", ""),
                    ]
                    for row in (automation_dashboard.get("rows") or [])[:8]
                ],
            },
            {
                "title": "功能成熟度对齐",
                "headers": ["功能", "状态", "当前实现", "下一步"],
                "rows": [
                    [row.get("feature", ""), row.get("status", ""), row.get("current_implementation", ""), row.get("next_gap", "")]
                    for row in (payload.get("reference_alignment") or [])[:8]
                ],
            },
            {
                "title": "下一步行动",
                "headers": ["优先级", "事项", "操作", "效果"],
                "rows": [
                    [row.get("priority", ""), row.get("title", ""), row.get("operation", ""), row.get("expected_effect", "")]
                    for row in (payload.get("next_actions") or [])[:6]
                ],
            },
            {
                "title": "主动测试时间线热力图",
                "headers": timeline_heatmap_headers(timeline),
                "rows": timeline_heatmap_rows(timeline),
            },
            {
                "title": "主动测试历史趋势",
                "headers": ["审计时间", "完整率", "缺口数", "补跑队列", "Raw", "补跑状态"],
                "rows": timeline_audit_rows(timeline),
            },
            {
                "title": "开源模型参考采用",
                "headers": ["参考", "方法", "许可", "采用状态", "用途"],
                "rows": [
                    [
                        row.get("name", ""),
                        row.get("method_family", ""),
                        row.get("license", ""),
                        row.get("adoption_status", ""),
                        row.get("usage", ""),
                    ]
                    for row in (model.get("rows") or [])[:8]
                ],
            },
        ],
    )


def pdf_recommendation_rows(rows: list[dict[str, Any]]) -> list[list[str]]:
    return [
        [
            str(row.get("board", "")),
            f"{row.get('event', '')} / {row.get('market', '')}",
            str(row.get("selection", "")),
            f"{float(row.get('odds') or 0):.2f}" if row.get("odds") else "",
            fmt_pct(row.get("probability")),
            fmt_pct(row.get("expected_value")),
            f"AUD {float(row.get('stake_aud') or 0):,.0f}",
            str(row.get("confidence", "")),
        ]
        for row in rows[:12]
    ]


def automation_dashboard_items(dashboard: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        (str(row.get("label", "")), float(row.get("score") or 0) * 100)
        for row in (dashboard.get("rows") or [])
    ]


def feature_status_items(counts: dict[str, int]) -> list[tuple[str, float]]:
    return [(key, float(value)) for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def board_exposure_items(rows: list[dict[str, Any]]) -> list[tuple[str, float]]:
    return [(short_board(str(row.get("board", ""))), float(row.get("stake_aud") or 0)) for row in rows]


def recommendation_ev_items(rows: list[dict[str, Any]]) -> list[tuple[str, float]]:
    items = []
    for row in rows:
        ev = max(0.0, float(row.get("expected_value") or 0))
        label = f"{row.get('event', '')}/{row.get('selection', '')}"
        items.append((short_label(label), ev * 100))
    return items[:7]


def timeline_gap_items(timeline: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        ("分析缺口日", float(timeline.get("missing_analysis_day_count") or 0)),
        ("日报缺口日", float(timeline.get("missing_report_day_count") or 0)),
        ("待补队列", float(timeline.get("backfill_queue_count") or 0)),
        ("完整日", float(timeline.get("complete_day_count") or 0)),
    ]


def timeline_slot_items(timeline: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        (str(row.get("label", "")), float(row.get("covered_day_count") or 0))
        for row in (timeline.get("slot_coverage") or [])
    ]


def timeline_audit_complete_items(timeline: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        (str(row.get("label", "")), float(row.get("complete_ratio") or 0) * 100)
        for row in (timeline.get("audit_history") or [])[-7:]
    ]


def timeline_heatmap_headers(timeline: dict[str, Any]) -> list[str]:
    labels = [str(row.get("label", "")) for row in (timeline.get("slot_coverage") or [])]
    return ["日期", *labels, "分析", "日报", "状态"]


def timeline_heatmap_rows(timeline: dict[str, Any]) -> list[list[str]]:
    rows = []
    for row in (timeline.get("slot_heatmap") or [])[:8]:
        cells = [slot_status_label((cell or {}).get("status")) for cell in row.get("cells") or []]
        rows.append(
            [
                str(row.get("date", "")),
                *cells,
                str(int(row.get("effective_analysis_count") or 0)),
                "有" if row.get("formal_report_exists") else "缺失",
                "缺口" if row.get("needs_backfill") else "完整",
            ]
        )
    return rows


def timeline_audit_rows(timeline: dict[str, Any]) -> list[list[str]]:
    rows = []
    for row in (timeline.get("audit_history") or [])[-10:]:
        rows.append(
            [
                str(row.get("label", "")),
                fmt_pct(row.get("complete_ratio")),
                str(int(row.get("gap_count") or 0)),
                str(int(row.get("backfill_queue_count") or 0)),
                "ready" if row.get("raw_refresh_ready") else str(row.get("raw_refresh_status", "")),
                str(row.get("backfill_status", "")),
            ]
        )
    return rows


def slot_status_label(status: Any) -> str:
    mapping = {"covered": "有", "missing": "缺", "unknown": "待"}
    return mapping.get(str(status or ""), "待")


def gate_items(gates: dict[str, Any]) -> list[tuple[str, float]]:
    labels = [
        ("发布", "formal_report_publish_ready"),
        ("调度", "recurring_automation_ready"),
        ("Raw", "raw_refresh_ready"),
        ("安全", "public_safety_ready"),
        ("预检", "technical_preflight_ready"),
        ("持仓", "private_position_ready"),
    ]
    return [(label, 1.0 if gates.get(key) else 0.0) for label, key in labels]


def report_history_items(history: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        ("总 run", float(history.get("run_count") or 0)),
        ("成功", float(history.get("success_run_count") or 0)),
        ("阻塞", float(history.get("blocked_run_count") or 0)),
        ("Runner", float(history.get("automation_run_count") or 0)),
    ]


def open_source_items(model: dict[str, Any]) -> list[tuple[str, float]]:
    return [
        ("已落地参考", float(model.get("implemented_reference_count") or 0)),
        ("设计参考", float(model.get("design_reference_count") or 0)),
        ("参考总数", float(model.get("reference_count") or 0)),
    ]


def open_source_coverage_items(model: dict[str, Any]) -> list[tuple[str, float]]:
    coverage = model.get("coverage_counts") or {}
    return [
        (str(name), float(value))
        for name, value in sorted(coverage.items(), key=lambda item: (-float(item[1] or 0), str(item[0])))[:10]
    ]


def parse_json(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def optional_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def consistency_label(raw: dict[str, Any]) -> str:
    signal = raw.get("model_signal") or {}
    if not signal:
        return "待校准"
    if signal.get("high_divergence"):
        return "模型分歧高"
    if signal.get("selection_aligned_with_consensus"):
        return "三模型一致"
    return "部分一致"


def confidence_label(raw: dict[str, Any]) -> str:
    signal = raw.get("model_signal") or {}
    mapping = {"high": "高", "medium": "中", "low": "低"}
    return mapping.get(str(signal.get("consensus_confidence") or "").lower(), "待校准")


def value_label(expected_value: float | None, edge: float | None, stake: float) -> str:
    if stake <= 0:
        return "观察价值"
    if expected_value is not None and expected_value >= 0.15:
        return "高价值"
    if expected_value is not None and expected_value >= 0.05:
        return "中高价值"
    if edge is not None and edge > 0:
        return "小正边际"
    return "待复核"


def recommendation_reason(
    probability: float | None,
    breakeven: float | None,
    edge: float | None,
    expected_value: float | None,
    stake: float,
    raw: dict[str, Any],
) -> str:
    if probability is not None and breakeven is not None and expected_value is not None:
        reason = (
            f"模型概率 {fmt_pct(probability)} 高于赔率盈亏平衡 {fmt_pct(breakeven)}，"
            f"边际 {fmt_pp(edge)}，EV {fmt_pct(expected_value)}。"
        )
    else:
        reason = "证据不足以形成强下注结论，当前应以观察为主。"
    if stake > 0:
        reason += f" 建议金额 AUD {stake:,.0f}，属于分散小仓位。"
    if (raw.get("event_risk") or {}).get("flag_count"):
        reason += " 赛前仍需复核伤停、阵容和新闻。"
    return reason


def adoption_status_label(value: str) -> str:
    mapping = {
        "implemented_proxy": "已转化为本地 proxy",
        "design_reference": "设计参考",
    }
    return mapping.get(str(value), str(value or "待确认"))


def fmt_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return ""


def fmt_pp(value: Any) -> str:
    try:
        return f"{float(value) * 100:+.2f}pp"
    except (TypeError, ValueError):
        return ""


def short_id(value: Any) -> str:
    text = str(value or "")
    return text[-14:] if len(text) > 14 else text


def short_board(value: str) -> str:
    return (
        value.replace("2026 World Cup ", "")
        .replace("Australia Markets", "Australia")
        .replace("Team Futures Multi", "Team Multi")
        .replace("Group Betting", "Groups")
    )


def short_label(value: str, limit: int = 36) -> str:
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
