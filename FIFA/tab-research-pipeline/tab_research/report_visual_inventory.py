from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


REPORT_VISUAL_INVENTORY_JSON_LATEST = "report_visual_inventory_latest.json"
REPORT_VISUAL_INVENTORY_MD_LATEST = "report_visual_inventory_latest.md"
REPORT_VISUAL_INVENTORY_PDF_LATEST = "report_visual_inventory_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


REPORT_SPECS = [
    {
        "report_id": "recommendation_operations",
        "name": "推荐操作 Dashboard",
        "json": "recommendation_operations_latest.json",
        "markdown": "recommendation_operations_latest.md",
        "pdf": "recommendation_operations_latest.pdf",
        "db_tables": ["recommendation_operation_snapshots", "recommendations"],
        "decision_focus": "下注推荐、金额、Edge、Risk of ruin、模型校准和执行门禁。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "strategy_performance",
        "name": "策略表现 / CLV / ROI 回测 Dashboard",
        "json": "strategy_performance_latest.json",
        "markdown": "strategy_performance_latest.md",
        "pdf": "strategy_performance_latest.pdf",
        "db_tables": ["strategy_performance_snapshots"],
        "decision_focus": "CLV、ROI、EV分桶、样本覆盖和策略复盘。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "report_evolution",
        "name": "新旧报告变化总控台",
        "json": "report_evolution_latest.json",
        "markdown": "report_evolution_latest.md",
        "pdf": "report_evolution_latest.pdf",
        "db_tables": ["report_evolution_snapshots", "report_diffs"],
        "decision_focus": "新旧报告变化、报告族覆盖变化和业务信号变化。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "source_model_registry",
        "name": "开源模型库 Dashboard",
        "json": "source_model_registry_latest.json",
        "markdown": "source_model_registry_latest.md",
        "pdf": "source_model_registry_latest.pdf",
        "db_tables": ["source_model_registry_snapshots"],
        "decision_focus": "GitHub开源模型、UI蓝图、能力覆盖和许可风险。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "product_readiness",
        "name": "产品完成度 Dashboard",
        "json": "product_readiness_dashboard_latest.json",
        "markdown": "product_readiness_dashboard_latest.md",
        "pdf": "product_readiness_dashboard_latest.pdf",
        "db_tables": ["product_readiness_snapshots"],
        "decision_focus": "产品完成度、automation准入、报告系统和用户目标覆盖。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "goal_traceability",
        "name": "目标验收追踪",
        "json": "goal_traceability_latest.json",
        "markdown": "goal_traceability_latest.md",
        "pdf": "goal_traceability_latest.pdf",
        "db_tables": ["goal_traceability_snapshots"],
        "decision_focus": "用户目标逐项验收、证据缺口和下一步。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "position_monitor",
        "name": "持仓监控",
        "json": "position_monitor_latest.json",
        "markdown": "position_monitor_latest.md",
        "pdf": "position_monitor_latest.pdf",
        "db_tables": ["position_monitor_snapshots"],
        "decision_focus": "已下注持仓、结算状态、余额和累计收益率。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "automation_maturity",
        "name": "Automation 成熟度验收",
        "json": "automation_maturity_latest.json",
        "markdown": "automation_maturity_latest.md",
        "pdf": "automation_maturity_latest.pdf",
        "db_tables": ["automation_maturity_snapshots"],
        "decision_focus": "每日自动报告成熟度、P0/P1门禁和进入automation判断。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "raw_refresh_recovery",
        "name": "Raw 恢复与补跑控制台",
        "json": "raw_refresh_recovery_latest.json",
        "markdown": "raw_refresh_recovery_latest.md",
        "pdf": "raw_refresh_recovery_latest.pdf",
        "db_tables": ["audit_logs", "missing_data_logs"],
        "decision_focus": "TAB raw刷新失败隔离、staged gate、partial research和恢复动作。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "live_board_discovery",
        "name": "TAB Live 板块发现",
        "json": "live_board_discovery_latest.json",
        "markdown": "live_board_discovery_latest.md",
        "pdf": "live_board_discovery_latest.pdf",
        "db_tables": ["missing_data_logs"],
        "decision_focus": "TAB live板块发现、缺失板块、可研究范围和重试动作。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "available_board_strategy",
        "name": "可用板块策略",
        "json": "available_board_strategy_latest.json",
        "markdown": "available_board_strategy_latest.md",
        "pdf": "available_board_strategy_latest.pdf",
        "db_tables": ["available_board_strategy_snapshots"],
        "decision_focus": "可用板块、last-success fallback、研究-only边界和排除板块。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "fixture_sanity",
        "name": "公开赛程校验",
        "json": "fixture_sanity_latest.json",
        "markdown": "fixture_sanity_latest.md",
        "pdf": "fixture_sanity_latest.pdf",
        "db_tables": ["fixture_sanity_snapshots"],
        "decision_focus": "openfootball赛程一致性、缺失/冲突比赛和赛程门禁。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "active_timeline",
        "name": "主动测试时间线",
        "json": "active_timeline_report_latest.json",
        "markdown": "active_timeline_report_latest.md",
        "pdf": "active_timeline_report_latest.pdf",
        "db_tables": ["active_timeline_report_snapshots", "active_timeline_audits"],
        "decision_focus": "每日4次分析+1份日报的时间线覆盖和补缺队列。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "report_intelligence",
        "name": "研究智能层",
        "json": "report_intelligence_latest.json",
        "markdown": "report_intelligence_latest.md",
        "pdf": "report_intelligence_latest.pdf",
        "db_tables": ["report_runs", "recommendations", "visual_snapshots"],
        "decision_focus": "推荐、历史、主动测试、模型对齐和门禁合并后的业务决策层。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "automation_doctor",
        "name": "Automation Doctor",
        "json": "automation_doctor_latest.json",
        "markdown": "automation_doctor_latest.md",
        "pdf": "automation_doctor_latest.pdf",
        "db_tables": ["automation_doctor_snapshots"],
        "decision_focus": "automation阻塞诊断、修复优先级和补跑安全边界。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "report_index",
        "name": "报告索引",
        "json": "report_index_latest.json",
        "markdown": "report_index_latest.md",
        "pdf": "report_index_latest.pdf",
        "db_tables": ["report_runs", "report_diffs", "artifacts"],
        "decision_focus": "所有日报run、artifact、diff和latest指针历史。",
        "must_have": ["charts", "tables", "old_new_compare", "automation", "database"],
    },
    {
        "report_id": "automation_readiness",
        "name": "自动化就绪审计",
        "json": "automation_readiness_latest.json",
        "markdown": "automation_readiness_latest.md",
        "pdf": "automation_readiness_latest.pdf",
        "db_tables": ["automation_runs", "audit_logs"],
        "decision_focus": "日报发布门禁、技术preflight和fail-closed证据。",
        "must_have": ["charts", "tables", "automation", "database"],
    },
    {
        "report_id": "automation_candidate",
        "name": "自动化候选配置",
        "json": "automation_candidate_latest.json",
        "markdown": "automation_candidate_latest.md",
        "pdf": "automation_candidate_latest.pdf",
        "db_tables": ["automation_runs", "decision_records"],
        "decision_focus": "每日自动报告候选配置、调度窗口和禁止动作。",
        "must_have": ["charts", "tables", "automation", "database"],
    },
    {
        "report_id": "model_comparison",
        "name": "开源模型对比",
        "json": "tab_fifa_model_comparison_v0_1.json",
        "markdown": "tab_fifa_model_comparison_v0_1.md",
        "pdf": "tab_fifa_model_comparison_v0_1.pdf",
        "db_tables": ["model_comparisons"],
        "decision_focus": "开源模型概率、共识方向、分歧和本地概率交叉验证。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "model_divergence_review",
        "name": "模型分歧复核 Dashboard",
        "json": "model_divergence_review_latest.json",
        "markdown": "model_divergence_review_latest.md",
        "pdf": "model_divergence_review_latest.pdf",
        "db_tables": ["model_divergence_review_snapshots"],
        "decision_focus": "模型高分歧、逆共识和推荐下注复核队列。",
        "must_have": ["charts", "tables", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
    {
        "report_id": "dashboard",
        "name": "本地业务 Dashboard",
        "json": "tab_fifa_dashboard_data_latest.json",
        "markdown": "tab_fifa_dashboard_latest.md",
        "pdf": "tab_fifa_dashboard_latest.pdf",
        "html": "tab_fifa_dashboard_latest.html",
        "db_tables": ["visual_snapshots", "report_runs"],
        "decision_focus": "本地业务总览、图表摘要、开源模型采用和关键入口。",
        "must_have": ["charts", "dashboard", "old_new_compare", "automation", "github_reference", "database"],
    },
]


def write_report_visual_inventory_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_report_visual_inventory(output_dir, db_path)
    json_path = output_dir / REPORT_VISUAL_INVENTORY_JSON_LATEST
    md_path = output_dir / REPORT_VISUAL_INVENTORY_MD_LATEST
    pdf_path = output_dir / REPORT_VISUAL_INVENTORY_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_report_visual_inventory_markdown(payload))
    pdf_summary = write_report_visual_inventory_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_report_visual_inventory(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_report_visual_inventory(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path) if db_path else None
    table_counts = database_table_counts(db_path)
    rows = [build_report_row(output_dir, spec, table_counts=table_counts) for spec in REPORT_SPECS]
    gap_counts = capability_gap_counts(rows)
    full_matrix_count = sum(1 for row in rows if row["decision_matrix_ready"])
    summary = {
        "report_count": len(rows),
        "json_count": sum(1 for row in rows if row["has_json"]),
        "markdown_count": sum(1 for row in rows if row["has_markdown"]),
        "pdf_count": sum(1 for row in rows if row["has_pdf"]),
        "html_count": sum(1 for row in rows if row["has_html"]),
        "reports_with_charts": sum(1 for row in rows if row["chart_count"] > 0),
        "reports_with_tables": sum(1 for row in rows if row["table_count"] > 0),
        "dashboard_ready_count": sum(1 for row in rows if row["has_dashboard"]),
        "old_new_compare_count": sum(1 for row in rows if row["has_old_new_compare"]),
        "automation_view_count": sum(1 for row in rows if row["has_automation_view"]),
        "github_reference_count": sum(1 for row in rows if row["has_github_reference"]),
        "database_saved_count": sum(1 for row in rows if row["has_database_snapshot"]),
        "decision_matrix_ready_count": full_matrix_count,
        "manual_review_required_count": sum(1 for row in rows if row["gap_severity"] != "无缺口"),
        "blocking_gap_count": sum(1 for row in rows if row["gap_severity"] == "阻塞"),
        "partial_gap_count": sum(1 for row in rows if row["gap_severity"] == "需增强"),
        "top_gap_capabilities": top_gap_capabilities(gap_counts),
        "average_score": round(sum(float(row["score"]) for row in rows) / len(rows), 4) if rows else 0.0,
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "report_visual_inventory",
        "purpose": "审计所有公开报告族是否具备图表、表格、Dashboard、自动化状态、新旧对比、数据库保存和开源模型参考。",
        "summary": summary,
        "rows": rows,
        "gap_counts": gap_counts,
        "reading_path": "先看决策矩阵就绪数和阻塞缺口，再打开对应 PDF/HTML；正式下注日报仍由 latest_commit 门禁决定。",
    }


def persist_report_visual_inventory(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    rows = [row for row in public_payload.get("rows") or [] if isinstance(row, dict)]
    snapshot_id = report_visual_inventory_snapshot_id(str(public_payload.get("generated_at") or ""))
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_visual_inventory_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    report_count INTEGER NOT NULL DEFAULT 0,
                    reports_with_charts INTEGER NOT NULL DEFAULT 0,
                    reports_with_tables INTEGER NOT NULL DEFAULT 0,
                    dashboard_ready_count INTEGER NOT NULL DEFAULT 0,
                    old_new_compare_count INTEGER NOT NULL DEFAULT 0,
                    automation_view_count INTEGER NOT NULL DEFAULT 0,
                    github_reference_count INTEGER NOT NULL DEFAULT 0,
                    average_score REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_catalog_items (
                    snapshot_id TEXT NOT NULL DEFAULT '',
                    report_id TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    score REAL NOT NULL DEFAULT 0,
                    chart_count INTEGER NOT NULL DEFAULT 0,
                    table_count INTEGER NOT NULL DEFAULT 0,
                    has_json INTEGER NOT NULL DEFAULT 0,
                    has_markdown INTEGER NOT NULL DEFAULT 0,
                    has_pdf INTEGER NOT NULL DEFAULT 0,
                    has_html INTEGER NOT NULL DEFAULT 0,
                    has_dashboard INTEGER NOT NULL DEFAULT 0,
                    has_old_new_compare INTEGER NOT NULL DEFAULT 0,
                    has_automation_view INTEGER NOT NULL DEFAULT 0,
                    has_github_reference INTEGER NOT NULL DEFAULT 0,
                    has_database_snapshot INTEGER NOT NULL DEFAULT 0,
                    database_snapshot_count INTEGER NOT NULL DEFAULT 0,
                    decision_focus TEXT NOT NULL DEFAULT '',
                    decision_matrix_ready INTEGER NOT NULL DEFAULT 0,
                    gap_severity TEXT NOT NULL DEFAULT '',
                    publish_action TEXT NOT NULL DEFAULT '',
                    missing_capabilities_json TEXT NOT NULL DEFAULT '[]',
                    json_artifact TEXT NOT NULL DEFAULT '',
                    markdown_artifact TEXT NOT NULL DEFAULT '',
                    pdf_artifact TEXT NOT NULL DEFAULT '',
                    html_artifact TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(snapshot_id, report_id)
                )
                """
            )
            ensure_report_catalog_columns(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO report_visual_inventory_snapshots(
                    snapshot_id, generated_at, report_count, reports_with_charts,
                    reports_with_tables, dashboard_ready_count, old_new_compare_count,
                    automation_view_count, github_reference_count, average_score, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    str(public_payload.get("generated_at") or ""),
                    int(summary.get("report_count") or 0),
                    int(summary.get("reports_with_charts") or 0),
                    int(summary.get("reports_with_tables") or 0),
                    int(summary.get("dashboard_ready_count") or 0),
                    int(summary.get("old_new_compare_count") or 0),
                    int(summary.get("automation_view_count") or 0),
                    int(summary.get("github_reference_count") or 0),
                    float(summary.get("average_score") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            for row in rows:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO report_catalog_items(
                        snapshot_id, report_id, name, status, score, chart_count, table_count,
                        has_json, has_markdown, has_pdf, has_html, has_dashboard,
                        has_old_new_compare, has_automation_view, has_github_reference,
                        has_database_snapshot, database_snapshot_count, decision_focus,
                        decision_matrix_ready, gap_severity, publish_action,
                        missing_capabilities_json, json_artifact, markdown_artifact,
                        pdf_artifact, html_artifact, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        str(row.get("report_id") or ""),
                        str(row.get("name") or ""),
                        str(row.get("status") or ""),
                        float(row.get("score") or 0),
                        int(row.get("chart_count") or 0),
                        int(row.get("table_count") or 0),
                        int(bool(row.get("has_json"))),
                        int(bool(row.get("has_markdown"))),
                        int(bool(row.get("has_pdf"))),
                        int(bool(row.get("has_html"))),
                        int(bool(row.get("has_dashboard"))),
                        int(bool(row.get("has_old_new_compare"))),
                        int(bool(row.get("has_automation_view"))),
                        int(bool(row.get("has_github_reference"))),
                        int(bool(row.get("has_database_snapshot"))),
                        int(row.get("database_snapshot_count") or 0),
                        str(row.get("decision_focus") or ""),
                        int(bool(row.get("decision_matrix_ready"))),
                        str(row.get("gap_severity") or ""),
                        str(row.get("publish_action") or ""),
                        json.dumps(row.get("missing_capabilities") or [], ensure_ascii=False, sort_keys=True),
                        str(row.get("json") or ""),
                        str(row.get("markdown") or ""),
                        str(row.get("pdf") or ""),
                        str(row.get("html") or ""),
                        str(row.get("updated_at") or ""),
                    ),
                )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_report_catalog_snapshot ON report_catalog_items(snapshot_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_report_catalog_report ON report_catalog_items(report_id)")
            conn.commit()
        return {
            "status": "stored",
            "database": Path(db_path).name,
            "snapshot_table": "report_visual_inventory_snapshots",
            "catalog_table": "report_catalog_items",
            "snapshot_id": snapshot_id,
            "catalog_item_count": len(rows),
        }
    except sqlite3.Error as exc:
        return {
            "status": "failed",
            "database": Path(db_path).name,
            "snapshot_table": "report_visual_inventory_snapshots",
            "catalog_table": "report_catalog_items",
            "error": str(exc),
        }


def report_visual_inventory_snapshot_id(generated_at: str) -> str:
    return "report-visual-inventory-" + str(generated_at or "").replace(":", "").replace("+", "-").replace(".", "-")


def build_report_row(output_dir: Path, spec: dict[str, Any], *, table_counts: dict[str, int] | None = None) -> dict[str, Any]:
    json_path = artifact_path(output_dir, spec.get("json"))
    md_path = artifact_path(output_dir, spec.get("markdown"))
    pdf_path = artifact_path(output_dir, spec.get("pdf"))
    html_path = artifact_path(output_dir, spec.get("html"))
    table_counts = table_counts or {}
    db_tables = [str(item) for item in spec.get("db_tables") or []]
    database_snapshot_count = sum(int(table_counts.get(table, 0)) for table in db_tables)
    has_database_snapshot = database_snapshot_count > 0
    json_payload = load_json(json_path)
    text_blob = "\n".join(
        value
        for value in [
            read_text(md_path),
            read_text(html_path),
            json.dumps(json_payload, ensure_ascii=False) if json_payload else "",
        ]
        if value
    )
    pdf_summary = (json_payload.get("artifacts") or {}).get("pdf_summary") or {}
    chart_count = int(pdf_summary.get("chart_count") or count_markdown_charts(text_blob))
    table_count = int(pdf_summary.get("extra_table_count") or count_markdown_tables(text_blob))
    capability = {
        "charts": chart_count > 0,
        "tables": table_count > 0,
        "dashboard": exists_file(html_path) or contains_any(text_blob, ["Dashboard", "仪表盘", "Automation Dashboard"]),
        "old_new_compare": contains_any(text_blob, ["新旧", "old", "diff", "compare", "changed_count", "报告对比"]),
        "automation": contains_any(text_blob, ["automation", "自动化", "门禁", "主动测试"]),
        "github_reference": contains_any(text_blob, ["GitHub", "Hicruben", "goalmodel", "Dixon-Coles", "openfootball", "worldcup.json", "开源模型"]),
        "database": has_database_snapshot,
    }
    must_have = [str(item) for item in spec.get("must_have") or []]
    missing = [item for item in must_have if not capability.get(item)]
    file_score = sum(
        [
            exists_file(json_path),
            exists_file(md_path),
            exists_file(pdf_path),
            exists_file(html_path),
        ]
    )
    capability_score = sum(1 for item in must_have if capability.get(item))
    denominator = max(1, len(must_have) + 3)
    score = min(1.0, (capability_score + min(file_score, 3)) / denominator)
    gap_severity = gap_severity_for_missing(missing, score)
    return {
        "report_id": spec["report_id"],
        "name": spec["name"],
        "status": "完整" if not missing and score >= 0.85 else "需增强" if score >= 0.55 else "阻塞",
        "score": round(score, 4),
        "score_pct": round(score * 100, 2),
        "decision_focus": str(spec.get("decision_focus") or ""),
        "decision_matrix_ready": not missing and has_database_snapshot and score >= 0.85,
        "gap_severity": gap_severity,
        "publish_action": publish_action_for_row(missing, score, has_database_snapshot),
        "has_json": exists_file(json_path),
        "has_markdown": exists_file(md_path),
        "has_pdf": exists_file(pdf_path),
        "has_html": exists_file(html_path),
        "chart_count": chart_count,
        "table_count": table_count,
        "has_dashboard": capability["dashboard"],
        "has_old_new_compare": capability["old_new_compare"],
        "has_automation_view": capability["automation"],
        "has_github_reference": capability["github_reference"],
        "has_database_snapshot": has_database_snapshot,
        "database_snapshot_count": database_snapshot_count,
        "database_tables": db_tables,
        "missing_capabilities": missing,
        "next_action": next_action_for_missing(missing),
        "json": json_path.name if json_path else "",
        "markdown": md_path.name if md_path else "",
        "pdf": pdf_path.name if pdf_path else "",
        "html": html_path.name if html_path else "",
        "updated_at": latest_mtime([json_path, md_path, pdf_path, html_path]),
    }


def render_report_visual_inventory_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    gaps = payload.get("gap_counts") or {}
    lines = [
        "# TAB FIFA 报表决策矩阵覆盖审计",
        "",
        "本审计检查公开报告族是否已经具备图表、表格、Dashboard、自动化状态、新旧对比、数据库保存和开源模型参考。它不自动下注，也不替代正式日报门禁。",
        "",
        "## Executive Summary",
        "",
        f"- 报告族：`{summary.get('report_count', 0)}`",
        f"- 带图表报告：`{summary.get('reports_with_charts', 0)}`",
        f"- 带 Dashboard/仪表盘：`{summary.get('dashboard_ready_count', 0)}`",
        f"- 带新旧对比：`{summary.get('old_new_compare_count', 0)}`",
        f"- 带 automation 状态：`{summary.get('automation_view_count', 0)}`",
        f"- 已入库报告：`{summary.get('database_saved_count', 0)}`",
        f"- 带 GitHub/开源模型参考：`{summary.get('github_reference_count', 0)}`",
        f"- 决策矩阵就绪：`{summary.get('decision_matrix_ready_count', 0)}`",
        f"- 需人工复核：`{summary.get('manual_review_required_count', 0)}`；阻塞缺口：`{summary.get('blocking_gap_count', 0)}`",
        f"- 平均覆盖得分：`{pct(summary.get('average_score'))}`",
        f"- Top缺口：`{', '.join(str(item.get('capability')) + ':' + str(item.get('count')) for item in summary.get('top_gap_capabilities') or []) or '无'}`",
        "",
        "## 覆盖矩阵",
        "",
        "| 报告 | 决策用途 | 状态 | 缺口级别 | 得分 | 图表 | 附表 | Dashboard | 新旧对比 | 入库 | Automation | GitHub参考 | 动作 |",
        "|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            "| {name} | {focus} | {status} | {gap_severity} | {score} | {charts} | {tables} | {dashboard} | {compare} | {database} | {automation} | {github} | {publish_action} |".format(
                name=md(row.get("name")),
                focus=md(row.get("decision_focus")),
                status=md(row.get("status")),
                gap_severity=md(row.get("gap_severity")),
                score=pct(row.get("score")),
                charts=int(row.get("chart_count") or 0),
                tables=int(row.get("table_count") or 0),
                dashboard=yes_no(row.get("has_dashboard")),
                compare=yes_no(row.get("has_old_new_compare")),
                database=f"{yes_no(row.get('has_database_snapshot'))}({int(row.get('database_snapshot_count') or 0)})",
                automation=yes_no(row.get("has_automation_view")),
                github=yes_no(row.get("has_github_reference")),
                publish_action=md(row.get("publish_action")),
            )
        )
    lines.extend(
        [
            "",
            "## 缺口计数",
            "",
            "| 能力 | 缺口报告数 |",
            "|---|---:|",
        ]
    )
    for key, count in sorted(gaps.items(), key=lambda item: (-int(item[1]), item[0])):
        lines.append(f"| {md(capability_label(key))} | {int(count)} |")
    return "\n".join(lines)


def write_report_visual_inventory_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    rows = payload.get("rows") or []
    charts = [
        chart_from_items("报表覆盖得分", [(row.get("name", ""), float(row.get("score") or 0) * 100) for row in rows], "#1F4E79"),
        chart_from_items("图表数量", [(row.get("name", ""), float(row.get("chart_count") or 0)) for row in rows], "#247A5A"),
        chart_from_items("数据库保存覆盖", [(row.get("name", ""), 1 if row.get("has_database_snapshot") else 0) for row in rows], "#B42318"),
        chart_from_items(
            "能力覆盖",
            [
                ("图表", summary.get("reports_with_charts", 0)),
                ("附表", summary.get("reports_with_tables", 0)),
                ("Dashboard", summary.get("dashboard_ready_count", 0)),
                ("新旧对比", summary.get("old_new_compare_count", 0)),
                ("Automation", summary.get("automation_view_count", 0)),
                ("数据库", summary.get("database_saved_count", 0)),
                ("GitHub", summary.get("github_reference_count", 0)),
            ],
            "#A56710",
        ),
        chart_from_items(
            "文件覆盖",
            [
                ("JSON", summary.get("json_count", 0)),
                ("Markdown", summary.get("markdown_count", 0)),
                ("PDF", summary.get("pdf_count", 0)),
                ("HTML", summary.get("html_count", 0)),
            ],
            "#6A4C93",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 报表决策矩阵覆盖审计",
        subtitle="审计公开报告族的图表、Dashboard、自动化状态、新旧对比、数据库保存和开源模型参考覆盖；只用于报告质量控制。",
        summary_rows=[
            ("报告族", str(summary.get("report_count", 0))),
            ("带图表报告", str(summary.get("reports_with_charts", 0))),
            ("带 Dashboard", str(summary.get("dashboard_ready_count", 0))),
            ("带新旧对比", str(summary.get("old_new_compare_count", 0))),
            ("带 Automation", str(summary.get("automation_view_count", 0))),
            ("已入库报告", str(summary.get("database_saved_count", 0))),
            ("带 GitHub参考", str(summary.get("github_reference_count", 0))),
            ("决策矩阵就绪", str(summary.get("decision_matrix_ready_count", 0))),
            ("阻塞缺口", str(summary.get("blocking_gap_count", 0))),
            ("平均覆盖得分", pct(summary.get("average_score"))),
        ],
        charts=charts,
        table_headers=["报告", "状态", "缺口级别", "得分", "图表", "附表", "缺口"],
        table_rows=[
            [
                str(row.get("name", "")),
                str(row.get("status", "")),
                str(row.get("gap_severity", "")),
                pct(row.get("score")),
                str(int(row.get("chart_count") or 0)),
                str(int(row.get("table_count") or 0)),
                "、".join(row.get("missing_capabilities") or []) or "无",
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "Report Center 文件覆盖",
                "headers": ["报告", "JSON", "Markdown", "PDF", "HTML", "入库", "更新时间"],
                "rows": [
                    [
                        str(row.get("name", "")),
                        yes_no(row.get("has_json")),
                        yes_no(row.get("has_markdown")),
                        yes_no(row.get("has_pdf")),
                        yes_no(row.get("has_html")),
                        f"{yes_no(row.get('has_database_snapshot'))} / {int(row.get('database_snapshot_count') or 0)}",
                        str(row.get("updated_at", "")),
                    ]
                    for row in rows
                ],
            },
            {
                "title": "Automation缺口与动作",
                "headers": ["报告", "决策用途", "缺口级别", "可发布动作", "下一步"],
                "rows": [
                    [
                        str(row.get("name", "")),
                        str(row.get("decision_focus", "")),
                        str(row.get("gap_severity", "")),
                        str(row.get("publish_action", "")),
                        str(row.get("next_action", "")),
                    ]
                    for row in rows
                ],
            },
        ],
    )


def ensure_report_catalog_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(report_catalog_items)").fetchall()}
    desired = {
        "has_database_snapshot": "INTEGER NOT NULL DEFAULT 0",
        "database_snapshot_count": "INTEGER NOT NULL DEFAULT 0",
        "decision_focus": "TEXT NOT NULL DEFAULT ''",
        "decision_matrix_ready": "INTEGER NOT NULL DEFAULT 0",
        "gap_severity": "TEXT NOT NULL DEFAULT ''",
        "publish_action": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in desired.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE report_catalog_items ADD COLUMN {column} {definition}")


def database_table_counts(db_path: Path | None) -> dict[str, int]:
    if not db_path or not db_path.exists():
        return {}
    uri = f"file:{db_path.resolve()}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(uri, uri=True)
        try:
            tables = [
                str(row[0])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            ]
            counts: dict[str, int] = {}
            for table in tables:
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table):
                    continue
                try:
                    counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                except sqlite3.Error:
                    counts[table] = 0
            return counts
        finally:
            conn.close()
    except sqlite3.Error:
        return {}


def capability_gap_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for item in row.get("missing_capabilities") or []:
            key = str(item)
            counts[key] = counts.get(key, 0) + 1
    return counts


def top_gap_capabilities(counts: dict[str, int], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {"capability": capability_label(key), "count": int(value)}
        for key, value in sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))[:limit]
    ]


def gap_severity_for_missing(missing: list[str], score: float) -> str:
    if not missing:
        return "无缺口"
    critical = {"charts", "tables", "database", "old_new_compare"}
    if critical.intersection(missing) or score < 0.55:
        return "阻塞"
    return "需增强"


def publish_action_for_row(missing: list[str], score: float, has_database_snapshot: bool) -> str:
    if not missing and score >= 0.85 and has_database_snapshot:
        return "可进入日报矩阵，保持自动生成。"
    if "database" in missing or not has_database_snapshot:
        return "先补数据库落点，再允许进入automation日报矩阵。"
    if "old_new_compare" in missing:
        return "补新旧对比后再作为日报复盘依据。"
    if "charts" in missing or "tables" in missing:
        return "补图表/附表后再给用户决策使用。"
    return "可保留在研究区，但需要补齐缺口后再提升权重。"


def capability_label(value: Any) -> str:
    return {
        "charts": "图表",
        "tables": "明细表",
        "dashboard": "Dashboard",
        "old_new_compare": "新旧对比",
        "automation": "Automation状态",
        "github_reference": "GitHub/开源参考",
        "database": "数据库保存",
    }.get(str(value), str(value))


def artifact_path(output_dir: Path, name: Any) -> Path | None:
    value = str(name or "").strip()
    return output_dir / value if value else None


def exists_file(path: Path | None) -> bool:
    return bool(path and path.exists() and path.is_file())


def load_json(path: Path | None) -> dict[str, Any]:
    try:
        if not exists_file(path):
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path | None) -> str:
    try:
        if not exists_file(path):
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def count_markdown_charts(text: str) -> int:
    return text.count("```mermaid") + text.count("<svg") + text.count("Visual Summary")


def count_markdown_tables(text: str) -> int:
    return len(re.findall(r"(?m)^\\|.+\\|$", text))


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def latest_mtime(paths: list[Path | None]) -> str:
    timestamps = [path.stat().st_mtime for path in paths if exists_file(path)]
    if not timestamps:
        return ""
    return datetime.fromtimestamp(max(timestamps), REPORT_TZ).isoformat(timespec="seconds")


def next_action_for_missing(missing: list[str]) -> str:
    if not missing:
        return "保持自动生成并纳入 report center。"
    labels = {
        "charts": "补图表",
        "tables": "补明细表",
        "dashboard": "补 Dashboard 区块",
        "old_new_compare": "补新旧对比",
        "automation": "补 automation 状态",
        "github_reference": "补 GitHub 参考说明",
    }
    return "；".join(labels.get(item, item) for item in missing)


def yes_no(value: Any) -> str:
    return "有" if value else "缺"


def pct(value: Any) -> str:
    try:
        return f"{float(value or 0) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
