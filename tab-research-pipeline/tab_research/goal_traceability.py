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


GOAL_TRACEABILITY_JSON_LATEST = "goal_traceability_latest.json"
GOAL_TRACEABILITY_MD_LATEST = "goal_traceability_latest.md"
GOAL_TRACEABILITY_PDF_LATEST = "goal_traceability_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_goal_traceability_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_goal_traceability(output_dir, db_path)
    json_path = output_dir / GOAL_TRACEABILITY_JSON_LATEST
    md_path = output_dir / GOAL_TRACEABILITY_MD_LATEST
    pdf_path = output_dir / GOAL_TRACEABILITY_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_goal_traceability_markdown(payload))
    pdf_summary = write_goal_traceability_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_goal_traceability(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_goal_traceability(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    workspace_root = output_dir.parent
    pipeline_root = Path(__file__).resolve().parents[1]
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")

    latest_commit = load_json(output_dir / "latest_commit.json")
    visual_inventory = load_json(output_dir / "report_visual_inventory_latest.json")
    maturity = load_json(output_dir / "automation_maturity_latest.json")
    intelligence = load_json(output_dir / "report_intelligence_latest.json")
    model_comparison = load_json(output_dir / "tab_fifa_model_comparison_v0_1.json")
    source_registry = load_json(output_dir / "source_model_registry_latest.json")
    timeline = load_json(output_dir / "active_timeline_latest.json")
    backfill = load_json(output_dir / "active_backfill_latest.json")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    available_strategy = load_json(output_dir / "available_board_strategy_latest.json")
    candidate = load_json(output_dir / "automation_candidate_latest.json")
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    position_monitor = load_json(output_dir / "position_monitor_latest.json")
    db = database_trace(db_path)
    downloads_entry = downloads_entry_trace()
    source_files = source_file_trace(workspace_root, pipeline_root)

    rows = build_rows(
        source_files=source_files,
        latest_commit=latest_commit,
        visual_inventory=visual_inventory,
        maturity=maturity,
        intelligence=intelligence,
        model_comparison=model_comparison,
        source_registry=source_registry,
        timeline=timeline,
        backfill=backfill,
        raw_health=raw_health,
        available_strategy=available_strategy,
        candidate=candidate,
        readiness=readiness,
        position_monitor=position_monitor,
        db=db,
        downloads_entry=downloads_entry,
    )
    summary = summarize_rows(rows)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "trace_id": trace_id(generated_at),
        "mode": "goal_traceability_dashboard",
        "purpose": "把用户原始目标拆成可审计验收项：需求/ChatGPT版本参考、GitHub开源模型、图表/Dashboard、PDF/数据库、新旧对比、首页下注决策、主动测试补缺、fail-closed和automation准入。",
        "executive_status": {
            "goal_ready": summary["blocked_count"] == 0 and summary["partial_count"] == 0,
            "status": "ready" if summary["blocked_count"] == 0 and summary["partial_count"] == 0 else "in_progress",
            "overall_score": summary["average_score"],
            "ready_count": summary["ready_count"],
            "partial_count": summary["partial_count"],
            "blocked_count": summary["blocked_count"],
            "primary_gap": first_gap(rows),
            "recommended_next_action": recommended_next_action(rows),
        },
        "summary": summary,
        "rows": rows,
        "source_trace": source_files,
        "database_trace": db,
        "downloads_entry_trace": downloads_entry,
        "old_new_compare": old_new_compare(rows, db_path),
        "truthfulness_note": "本追踪报告只证明目标满足度和缺口；不会把 raw/private/preflight 失败的 attempted run 宣布为可下注日报，也不会自动下注。",
    }
    return sanitize_public_payload(payload)


def build_rows(
    *,
    source_files: dict[str, Any],
    latest_commit: dict[str, Any],
    visual_inventory: dict[str, Any],
    maturity: dict[str, Any],
    intelligence: dict[str, Any],
    model_comparison: dict[str, Any],
    source_registry: dict[str, Any],
    timeline: dict[str, Any],
    backfill: dict[str, Any],
    raw_health: dict[str, Any],
    available_strategy: dict[str, Any],
    candidate: dict[str, Any],
    readiness: dict[str, Any],
    position_monitor: dict[str, Any],
    db: dict[str, Any],
    downloads_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    visual_summary = visual_inventory.get("summary") or {}
    maturity_summary = maturity.get("summary") or {}
    model_dashboard = model_comparison.get("model_dashboard") or {}
    source_adoption = model_comparison.get("source_adoption") or {}
    source_registry_summary = source_registry.get("summary") or {}
    ui_blueprint_count = int(source_registry_summary.get("ui_blueprint_count") or 0)
    ui_blueprint_implemented = int(source_registry_summary.get("ui_blueprint_implemented_count") or 0)
    timeline_summary = timeline.get("summary") or {}
    available_summary = available_strategy.get("summary") or {}
    discovery_ready = bool(available_summary.get("discovery_ready", True))
    discovery_retry_count = int(available_summary.get("discovery_retry_board_count") or 0)
    intelligence_comparison = intelligence.get("report_comparison") or {}
    readiness_private = readiness.get("private_position_bootstrap") or {}
    position_summary = position_monitor.get("summary") or {}
    position_status = position_monitor.get("executive_status") or {}
    position_storage = position_monitor.get("storage") or {}
    position_monitor_ready = bool(position_summary.get("snapshot_ready")) or bool(readiness_private.get("ready"))
    position_monitor_present = (
        position_monitor.get("mode") == "position_monitor_dashboard"
        and position_storage.get("status") == "stored"
    )

    return [
        trace_row(
            "source_requirements",
            "ChatGPT/需求文件与当前 personalization 已纳入",
            "ready" if source_files.get("requirements_trace_ready") else "partial",
            score=1.0 if source_files.get("requirements_trace_ready") else 0.65,
            evidence=(
                f"已读取/维护 {source_files.get('available_source_count', 0)} 个本地需求/交接文件；"
                f"ChatGPT Excel 模板存在={bool(source_files.get('chatgpt_template_exists'))}；"
                f"原始 prompt 文件存在={bool(source_files.get('original_prompt_exists'))}"
            ),
            gap="Downloads 中未找到 fifa_codex_build_prompt.txt；当前以 ChatGPT Excel 模板、PRD、README、RUNBOOK、HANDOFF 和用户最新指令作为需求证据。",
            next_action="若后续拿到原始 build prompt，加入 source_trace 后重新生成本报告；当前继续以已提供 Excel 模板和本地权威文件为准。",
            user_value="避免凭记忆做系统，所有需求来源都可追踪。",
        ),
        trace_row(
            "github_models",
            "GitHub 开源模型已访问并转化为本地模型/界面参考",
            "ready"
            if model_dashboard.get("github_source_audit_ready")
            and int(source_adoption.get("reference_count") or 0) >= 3
            and ui_blueprint_count >= 6
            else "partial",
            score=1.0
            if model_dashboard.get("github_source_audit_ready") and ui_blueprint_count >= 6
            else 0.85
            if model_dashboard.get("github_source_audit_ready")
            else 0.4,
            evidence=(
                f"source_audit={bool(model_dashboard.get('github_source_audit_ready'))}；"
                f"implemented={source_adoption.get('implemented_reference_count', 0)}/{source_adoption.get('reference_count', 0)}；"
                f"design={source_adoption.get('design_reference_count', 0)}；"
                f"UI蓝图={ui_blueprint_implemented}/{ui_blueprint_count}；"
                f"GitHub元数据={source_registry_summary.get('live_metadata_status', 'missing')} "
                f"{source_registry_summary.get('live_metadata_ready_count', 0)}/{source_registry_summary.get('reference_count', source_adoption.get('reference_count', 0))}"
            ),
            gap="部分外部仓库仍只能作为 design reference；基本面事件流等数据依赖未接入。",
            next_action="继续把 track record、calibration、bracket simulator、时间衰减参数和 xT/VAEP 基本面转成可回测模块。",
            user_value="下注概率不只看隐含概率，且开源模型的功能、布局、界面和 UI 已转成本地 Dashboard 蓝图。",
        ),
        trace_row(
            "visual_dashboards",
            "所有公开报告族具备图表、表格和 Dashboard",
            "ready" if visual_summary.get("dashboard_ready_count") == visual_summary.get("report_count") else "partial",
            score=float(visual_summary.get("average_score") or 0),
            evidence=(
                f"reports={visual_summary.get('report_count', 0)}；charts={visual_summary.get('reports_with_charts', 0)}；"
                f"tables={visual_summary.get('reports_with_tables', 0)}；dashboard={visual_summary.get('dashboard_ready_count', 0)}"
            ),
            gap="若新增报告族未进入 inventory，会导致覆盖度回落。",
            next_action="每新增报告族必须加入 report_visual_inventory，并提供 PDF/MD/JSON 或 HTML 入口。",
            user_value="报告不是纯文本，打开就能看图表和状态。",
        ),
        trace_row(
            "business_homepage",
            "首页优先显示推荐下注板块和主动测试按钮",
            "ready" if downloads_entry.get("recommendation_first") and downloads_entry.get("active_test_in_recommendation") else "partial",
            score=1.0 if downloads_entry.get("recommendation_first") and downloads_entry.get("all_required_columns") else 0.5,
            evidence=(
                f"recommendation_first={bool(downloads_entry.get('recommendation_first'))}；"
                f"active_test_in_recommendation={bool(downloads_entry.get('active_test_in_recommendation'))}；"
                f"required_columns={downloads_entry.get('present_required_column_count', 0)}/{downloads_entry.get('required_column_count', 0)}"
            ),
            gap="若入口不是从 .app 打开，按钮只能读取静态 JSON，不能启动本地服务动作。",
            next_action="继续从 Downloads 的 .app 入口打开；所有按钮保持只读/报告生成，不触发下注。",
            user_value="一眼知道看哪个盘、下注什么、金额多少、为什么，以及缺口是否需要补跑。",
        ),
        trace_row(
            "pdf_and_database",
            "报告保存为 PDF 并列入本地数据库",
            "ready" if db.get("run_count", 0) > 0 and latest_commit.get("status") == "ready_for_manual_report" else "partial",
            score=0.9 if db.get("run_count", 0) > 0 else 0.2,
            evidence=(
                f"latest_pdf_date={latest_commit.get('report_date', '')}；runs={db.get('run_count', 0)}；"
                f"recommendations={db.get('recommendation_count', 0)}；artifacts={db.get('artifact_count', 0)}"
            ),
            gap="当前 latest success 仍是旧可信报告，最新 attempted run 未能发布正式 PDF。",
            next_action="raw/private/preflight 恢复后，正式日报才复制到 DDMMYYYY.pdf 并推进 latest_commit。",
            user_value="PDF 可归档，数据库可做日报/周报、回测和趋势分析。",
        ),
        trace_row(
            "old_new_report_compare",
            "新报告新增和旧报告对比",
            "ready" if db.get("report_diff_count", 0) > 0 and intelligence_comparison else "partial",
            score=1.0 if db.get("report_diff_count", 0) > 0 and intelligence_comparison else 0.5,
            evidence=(
                f"report_diffs={db.get('report_diff_count', 0)}；"
                f"current_compare_changed={intelligence_comparison.get('changed_count', 0)}；"
                f"retained={intelligence_comparison.get('retained_count', 0)}"
            ),
            gap="当前 blocked run 的 PDF 不作为正式下注日报发布，因此对比用于研究审计而非执行。",
            next_action="保持每个 run 写 report_diffs；正式 publish 前用 latest_commit 选择可信对比基线。",
            user_value="知道哪些推荐新增、删除、变强或变弱，减少重复下注。",
        ),
        trace_row(
            "active_test_backfill",
            "主动测试会按每天 4 次分析 + 1 份日报检查并补缺",
            "partial" if timeline_summary.get("backfill_queue_count", 0) else "ready",
            score=0.55 if timeline_summary.get("backfill_queue_count", 0) else 1.0,
            evidence=(
                f"day_count={timeline_summary.get('day_count', 0)}；missing_analysis={timeline_summary.get('missing_analysis_day_count', 0)}；"
                f"missing_report={timeline_summary.get('missing_report_day_count', 0)}；backfill_status={backfill.get('status', '')}"
            ),
            gap="公开盘口 raw 未就绪时，补跑被正确阻断，缺口仍存在。",
            next_action="先恢复 raw；raw_ready=true 后再运行 safe_no_latest_publish 补跑。",
            user_value="系统能主动发现漏跑和漏报，不靠人工记忆检查。",
        ),
        trace_row(
            "live_data_gate",
            "公开盘口实时抓取门禁",
            "blocked" if raw_health.get("ready") is not True else "ready",
            score=0.0 if raw_health.get("ready") is not True else 1.0,
            evidence=(
                f"ready={bool(raw_health.get('ready'))}；required={raw_health.get('ready_required_target_count', 0)}/5；"
                f"blockers={', '.join(raw_health.get('blocker_codes') or [])}；"
                f"discovery_ready={discovery_ready}；discovery_retry={discovery_retry_count}"
            ),
            gap=(
                "TAB live board discovery 当前被 Access Denied/低质量页面阻断；在 TAB 拒绝 AI controlled access 时不能继续自动访问，不能判断板块是否真实缺失。"
                if not discovery_ready
                else "raw refresh blocked/stale，且 Australia Markets 存在 route mismatch。"
            ),
            next_action=(
                "停止自动 discovery/raw；等待官方/授权数据源或用户导出导入，成功后再判断板块可用性和 raw refresh。"
                if not discovery_ready
                else "接入授权 raw 或导入用户导出快照；若 TAB live 仍缺失板块，继续 unavailable 策略，不用旧盘口生成下注建议。"
            ),
            user_value="只有实时盘口通过，才允许把研究候选升级为当前可执行建议。",
        ),
        trace_row(
            "available_board_scope",
            "TAB 当前可见板块已进入策略范围控制",
            "blocked" if discovery_retry_count and not available_summary.get("research_allowed_board_count", 0) else "partial" if available_summary.get("research_allowed_board_count", 0) else "blocked",
            score=0.2 if discovery_retry_count else 0.6 if available_summary.get("research_allowed_board_count", 0) else 0.0,
            evidence=(
                f"research_allowed={available_summary.get('research_allowed_board_count', 0)}/{available_summary.get('expected_board_count', 0)}；"
                f"unavailable={available_summary.get('unavailable_board_count', 0)}；"
                f"retry={discovery_retry_count}；executable={bool(available_summary.get('executable_report_allowed'))}"
            ),
            gap=(
                "当前 discovery 质量门禁失败，暂不能把任何板块归为可研究或已缺失。"
                if discovery_retry_count
                else "当前只允许研究诊断，不允许新增执行金额。"
            ),
            next_action=(
                "重试只读 discovery；质量通过后再进入可用板块策略，不用旧盘口替代。"
                if discovery_retry_count
                else "继续排除 Australia Markets 和 Team Futures Multi，直到 TAB live 重新列出并通过 raw/preflight。"
            ),
            user_value="不会为了覆盖完整而拿旧板块数据误导下注。",
        ),
        trace_row(
            "position_roi",
            "已下注持仓、余额和收益率可滚动更新",
            "ready" if position_monitor_ready else "partial" if position_monitor_present else "blocked",
            score=1.0 if position_monitor_ready else 0.45 if position_monitor_present else 0.0,
            evidence=(
                f"private_status={readiness_private.get('status', position_status.get('status', ''))}；"
                f"snapshot_ready={bool(position_summary.get('snapshot_ready') or readiness_private.get('ready'))}；"
                f"monitor={position_status.get('status', '')}；storage={position_storage.get('status', '')}"
            ),
            gap="当前私有持仓快照不适用于最新报告日期；公开报告保持 account-update-pending，无法更新真实持仓金额和累计收益率。",
            next_action="在 .app 中启动只读持仓读取；用户完成 TAB 授权后导入快照，再重跑日报门禁。",
            user_value="胜负结果能改变余额和后续下注金额，策略更贴近真实资金曲线。",
        ),
        trace_row(
            "automation_entry",
            "达到 automation 水平但不自动下注",
            "blocked" if not readiness.get("recurring_automation_ready") else "ready",
            score=float((maturity_summary.get("ready_ratio") or 0)),
            evidence=(
                f"maturity_ready={maturity_summary.get('required_ready_count', 0)}/{maturity_summary.get('required_count', 0)}；"
                f"recurring={bool(readiness.get('recurring_automation_ready'))}；auto_wagering={candidate.get('auto_wagering_allowed')}"
            ),
            gap="raw、每日节奏、每日 PDF、私有持仓和 recurring 授权仍阻塞。",
            next_action="先修 P0 数据门禁；只有用户明确允许后才安装每日报告 automation；allow_auto_betting 保持 false。",
            user_value="系统最终能每日自动生成研究报告，但不会越权下注。",
        ),
    ]


def trace_row(
    requirement_id: str,
    title: str,
    status: str,
    *,
    score: float,
    evidence: str,
    gap: str,
    next_action: str,
    user_value: str,
) -> dict[str, Any]:
    status = status if status in {"ready", "partial", "blocked"} else "blocked"
    if status == "ready":
        gap = ""
    return {
        "requirement_id": requirement_id,
        "title": title,
        "status": status,
        "score": round(max(0.0, min(1.0, float(score))), 4),
        "evidence": evidence,
        "gap": gap,
        "next_action": next_action if status != "ready" else "保持自动审计，并在每次刷新后重新验证。",
        "user_value": user_value,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [row for row in rows if row["status"] == "ready"]
    partial = [row for row in rows if row["status"] == "partial"]
    blocked = [row for row in rows if row["status"] == "blocked"]
    return {
        "requirement_count": len(rows),
        "ready_count": len(ready),
        "partial_count": len(partial),
        "blocked_count": len(blocked),
        "average_score": round(sum(float(row["score"]) for row in rows) / len(rows), 4) if rows else 0.0,
        "ready_ratio": round(len(ready) / len(rows), 4) if rows else 0.0,
        "partial_titles": [row["title"] for row in partial],
        "blocked_titles": [row["title"] for row in blocked],
    }


def render_goal_traceability_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 目标验收追踪 Dashboard",
        "",
        "本报告把用户目标逐项映射到当前代码、报告、Dashboard、SQLite、开源模型和自动化门禁证据。它不自动下注，也不把 blocked run 当作可执行日报。",
        "",
        "## Executive Summary",
        "",
        f"- goal_ready: `{bool(executive.get('goal_ready'))}`",
        f"- status: `{executive.get('status', '')}`",
        f"- overall_score: `{pct(executive.get('overall_score'))}`",
        f"- ready / partial / blocked: `{summary.get('ready_count', 0)} / {summary.get('partial_count', 0)} / {summary.get('blocked_count', 0)}`",
        f"- primary_gap: `{executive.get('primary_gap', '')}`",
        f"- recommended_next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## Visual Summary",
        "",
        "```mermaid",
        "pie showData",
        f"  \"ready\" : {summary.get('ready_count', 0)}",
        f"  \"partial\" : {summary.get('partial_count', 0)}",
        f"  \"blocked\" : {summary.get('blocked_count', 0)}",
        "```",
        "",
        "## 新旧追踪变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- score_delta: `{compare.get('score_delta', 0)}`",
        f"- newly_ready: `{', '.join(compare.get('newly_ready', []) or []) or 'none'}`",
        f"- newly_blocked: `{', '.join(compare.get('newly_blocked', []) or []) or 'none'}`",
        "",
        "## 目标验收矩阵",
        "",
        "| 目标项 | 状态 | 得分 | 证据 | 缺口 | 下一步 | 用户价值 |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            "| {title} | {status} | {score} | {evidence} | {gap} | {next_action} | {user_value} |".format(
                title=md(row.get("title")),
                status=md(row.get("status")),
                score=pct(row.get("score")),
                evidence=md(row.get("evidence")),
                gap=md(row.get("gap") or "无"),
                next_action=md(row.get("next_action")),
                user_value=md(row.get("user_value")),
            )
        )
    source = payload.get("source_trace") or {}
    lines.extend(
        [
            "",
            "## Source Trace",
            "",
            f"- requirements_trace_ready: `{bool(source.get('requirements_trace_ready'))}`",
            f"- chatgpt_template_exists: `{bool(source.get('chatgpt_template_exists'))}`",
            f"- original_prompt_exists: `{bool(source.get('original_prompt_exists'))}`",
            f"- available_source_count: `{source.get('available_source_count', 0)}`",
        ]
    )
    for item in source.get("available_sources") or []:
        lines.append(f"- `{item.get('name', '')}`：{item.get('purpose', '')}")
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}"])
    return "\n".join(lines)


def write_goal_traceability_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("rows") or []
    compare = payload.get("old_new_compare") or {}
    charts = [
        chart_from_items(
            "目标状态",
            [
                ("ready", summary.get("ready_count", 0)),
                ("partial", summary.get("partial_count", 0)),
                ("blocked", summary.get("blocked_count", 0)),
            ],
            "#1F4E79",
        ),
        chart_from_items(
            "目标得分",
            [(row.get("title", ""), float(row.get("score") or 0) * 100) for row in rows],
            "#247A5A",
        ),
        chart_from_items(
            "关键阻塞",
            [(row.get("title", ""), 1 if row.get("status") == "blocked" else 0) for row in rows],
            "#C62828",
        ),
        chart_from_items(
            "系统资产",
            [
                ("runs", (payload.get("database_trace") or {}).get("run_count", 0)),
                ("diffs", (payload.get("database_trace") or {}).get("report_diff_count", 0)),
                ("audits", (payload.get("database_trace") or {}).get("active_timeline_audit_count", 0)),
                ("artifacts", (payload.get("database_trace") or {}).get("artifact_count", 0)),
            ],
            "#6A4C93",
        ),
        chart_from_items(
            "新旧追踪变化",
            [
                ("newly ready", len(compare.get("newly_ready") or [])),
                ("newly blocked", len(compare.get("newly_blocked") or [])),
                ("score delta x100", abs(float(compare.get("score_delta") or 0)) * 100),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 目标验收追踪 Dashboard",
        subtitle="用户目标逐项验收、证据链、新旧追踪和下一步；只生成研究报告，不自动下注。",
        summary_rows=[
            ("goal_ready", str(bool(executive.get("goal_ready")))),
            ("status", str(executive.get("status", ""))),
            ("overall_score", pct(executive.get("overall_score"))),
            ("ready/partial/blocked", f"{summary.get('ready_count', 0)}/{summary.get('partial_count', 0)}/{summary.get('blocked_count', 0)}"),
            ("primary_gap", str(executive.get("primary_gap", ""))),
            ("old-new", str(compare.get("status", ""))),
        ],
        charts=charts,
        table_headers=["目标项", "状态", "得分", "下一步"],
        table_rows=[
            [str(row.get("title", "")), str(row.get("status", "")), pct(row.get("score")), str(row.get("next_action", ""))]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "阻塞/部分完成原因",
                "headers": ["目标项", "缺口", "用户价值"],
                "rows": [
                    [str(row.get("title", "")), str(row.get("gap", "")), str(row.get("user_value", ""))]
                    for row in rows
                    if row.get("status") != "ready"
                ],
            },
            {
                "title": "新旧追踪变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["score_delta", str(compare.get("score_delta", 0))],
                    ["status_delta", str(compare.get("status_delta", ""))],
                    ["newly_ready", ", ".join(compare.get("newly_ready") or [])],
                    ["newly_blocked", ", ".join(compare.get("newly_blocked") or [])],
                ],
            },
            {
                "title": "需求来源",
                "headers": ["来源", "用途"],
                "rows": [
                    [str(item.get("name", "")), str(item.get("purpose", ""))]
                    for item in (payload.get("source_trace") or {}).get("available_sources", [])
                ],
            },
        ],
    )


def source_file_trace(workspace_root: Path, pipeline_root: Path) -> dict[str, Any]:
    original_prompt = Path.home() / "Downloads" / "fifa_codex_build_prompt.txt"
    chatgpt_template = Path.home() / "Downloads" / "football_betting_analysis_ABC_template.xlsx"
    candidates = [
        (chatgpt_template, "ChatGPT 提供的足球下注分析 ABC 模板，已吸收 Edge、EV、Kelly、资金管理和复盘口径"),
        (workspace_root / "HANDOFF.md", "当前跨轮交接和最新真实状态"),
        (workspace_root / "outputs" / "fifa_prd_and_technical_plan.md", "早期 PRD/技术方案和非目标边界"),
        (pipeline_root / "HANDOFF.md", "当前 pipeline 级实现状态、验证命令和剩余风险"),
        (pipeline_root / "README.md", "当前本地 app、runner、报告和按钮行为说明"),
        (pipeline_root / "RUNBOOK.md", "自动化授权边界和运行手册"),
    ]
    available = [{"name": path.name, "purpose": purpose} for path, purpose in candidates if path.exists()]
    if original_prompt.exists():
        available.insert(0, {"name": original_prompt.name, "purpose": "用户最初提供的 Codex build prompt"})
    requirements_trace_ready = chatgpt_template.exists() and any(item["name"] == "HANDOFF.md" for item in available) and len(available) >= 4
    return {
        "original_prompt_exists": original_prompt.exists(),
        "original_prompt_file": original_prompt.name,
        "chatgpt_template_exists": chatgpt_template.exists(),
        "chatgpt_template_file": chatgpt_template.name,
        "requirements_trace_ready": requirements_trace_ready,
        "available_source_count": len(available),
        "available_sources": available,
    }


def database_trace(db_path: Path) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {
            "ready": False,
            "database": Path(db_path).name,
            "run_count": 0,
            "recommendation_count": 0,
            "report_diff_count": 0,
            "automation_run_count": 0,
            "active_timeline_audit_count": 0,
            "artifact_count": 0,
        }
    uri = f"file:{Path(db_path).resolve()}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            return {
                "ready": True,
                "database": Path(db_path).name,
                "run_count": scalar_count(conn, "report_runs"),
                "recommendation_count": scalar_count(conn, "recommendations"),
                "report_diff_count": scalar_count(conn, "report_diffs"),
                "automation_run_count": scalar_count(conn, "automation_runs"),
                "active_timeline_audit_count": scalar_count(conn, "active_timeline_audits"),
                "artifact_count": scalar_count(conn, "artifacts"),
                "goal_trace_count": scalar_count(conn, "goal_traceability_snapshots"),
            }
        finally:
            conn.close()
    except sqlite3.Error:
        return {"ready": False, "database": Path(db_path).name}


def downloads_entry_trace() -> dict[str, Any]:
    entry = Path.home() / "Downloads" / "FIFA Report" / "TAB FIFA盘口研究系统.html"
    columns = [
        "时间",
        "板块",
        "盘口",
        "下注",
        "赔率",
        "金额",
        "操作",
        "分析一致性",
        "盘口价值",
        "Edge",
        "套利率",
        "Risk of ruin",
        "EV",
        "概率赔率编辑",
        "置信度",
        "价值信号",
        "价格容忍度",
        "上限占用",
        "Kelly安全垫",
        "风险调整分",
        "非surebet",
    ]
    if not entry.exists():
        return {
            "ready": False,
            "file": entry.name,
            "recommendation_first": False,
            "active_test_in_recommendation": False,
            "required_column_count": len(columns),
            "present_required_column_count": 0,
            "all_required_columns": False,
        }
    text = entry.read_text(encoding="utf-8", errors="ignore")
    rec_index = text.find("<h2>推荐下注板块</h2>")
    hero_index = text.find("<h2>今日操作摘要</h2>")
    timeline_index = text.find("<h2>主动测试与补跑</h2>")
    active_button_index = text.find("主动测试并自动补缺")
    present = [column for column in columns if column in text]
    return {
        "ready": rec_index >= 0 and len(present) == len(columns),
        "file": entry.name,
        "recommendation_first": rec_index >= 0 and (hero_index < 0 or rec_index < hero_index),
        "active_test_in_recommendation": active_button_index >= 0 and (timeline_index < 0 or active_button_index < timeline_index),
        "required_column_count": len(columns),
        "present_required_column_count": len(present),
        "all_required_columns": len(present) == len(columns),
        "artifact_link_count": len(re.findall(r"<a\s+[^>]*href=", text)),
    }


def persist_goal_traceability(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS goal_traceability_snapshots (
                    trace_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    overall_score REAL NOT NULL DEFAULT 0,
                    ready_count INTEGER NOT NULL DEFAULT 0,
                    partial_count INTEGER NOT NULL DEFAULT 0,
                    blocked_count INTEGER NOT NULL DEFAULT 0,
                    primary_gap TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO goal_traceability_snapshots(
                    trace_id, generated_at, status, overall_score, ready_count,
                    partial_count, blocked_count, primary_gap, payload_json
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("trace_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    float(summary.get("average_score") or 0),
                    int(summary.get("ready_count") or 0),
                    int(summary.get("partial_count") or 0),
                    int(summary.get("blocked_count") or 0),
                    str(executive.get("primary_gap") or ""),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {
            "status": "stored",
            "database": Path(db_path).name,
            "table": "goal_traceability_snapshots",
            "trace_id": str(public_payload.get("trace_id") or ""),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "database": Path(db_path).name,
            "table": "goal_traceability_snapshots",
            "error": str(exc).splitlines()[0][:180],
        }


def latest_goal_traceability(db_path: Path) -> dict[str, Any] | None:
    if not Path(db_path).exists():
        return None
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS goal_traceability_snapshots (
                    trace_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    overall_score REAL NOT NULL DEFAULT 0,
                    ready_count INTEGER NOT NULL DEFAULT 0,
                    partial_count INTEGER NOT NULL DEFAULT 0,
                    blocked_count INTEGER NOT NULL DEFAULT 0,
                    primary_gap TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            row = conn.execute(
                """
                SELECT trace_id, generated_at, status, overall_score, ready_count,
                       partial_count, blocked_count, primary_gap, payload_json
                FROM goal_traceability_snapshots
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except Exception:
        return None
    if not row:
        return None
    try:
        payload = json.loads(row["payload_json"] or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "trace_id": row["trace_id"],
        "generated_at": row["generated_at"],
        "status": row["status"],
        "overall_score": float(row["overall_score"] or 0),
        "ready_count": int(row["ready_count"] or 0),
        "partial_count": int(row["partial_count"] or 0),
        "blocked_count": int(row["blocked_count"] or 0),
        "primary_gap": row["primary_gap"],
        "payload": payload if isinstance(payload, dict) else {},
    }


def old_new_compare(rows: list[dict[str, Any]], db_path: Path) -> dict[str, Any]:
    previous = latest_goal_traceability(db_path)
    current_status = {row["requirement_id"]: row["status"] for row in rows}
    current_score = round(sum(float(row["score"]) for row in rows) / len(rows), 4) if rows else 0.0
    if not previous:
        return {
            "status": "no_previous_snapshot",
            "previous_generated_at": "",
            "score_delta": current_score,
            "status_delta": "first_snapshot",
            "newly_ready": [row["title"] for row in rows if row["status"] == "ready"],
            "newly_blocked": [row["title"] for row in rows if row["status"] == "blocked"],
        }
    previous_rows = (previous.get("payload") or {}).get("rows") or []
    previous_status = {row.get("requirement_id"): row.get("status") for row in previous_rows}
    newly_ready = [row["title"] for row in rows if row["status"] == "ready" and previous_status.get(row["requirement_id"]) != "ready"]
    newly_blocked = [row["title"] for row in rows if row["status"] == "blocked" and previous_status.get(row["requirement_id"]) != "blocked"]
    return {
        "status": "compared_with_previous_snapshot",
        "previous_generated_at": previous.get("generated_at", ""),
        "score_delta": round(current_score - float(previous.get("overall_score") or 0), 4),
        "status_delta": "changed" if newly_ready or newly_blocked else "unchanged",
        "newly_ready": newly_ready,
        "newly_blocked": newly_blocked,
        "current_status_by_requirement": current_status,
    }


def first_gap(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("status") == "blocked":
            return str(row.get("title", ""))
    for row in rows:
        if row.get("status") == "partial":
            return str(row.get("title", ""))
    return "无"


def recommended_next_action(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("status") == "blocked":
            return str(row.get("next_action", ""))
    for row in rows:
        if row.get("status") == "partial":
            return str(row.get("next_action", ""))
    return "所有目标项已通过；保持自动审计。"


def scalar_count(conn: sqlite3.Connection, table: str) -> int:
    exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    if not exists:
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def trace_id(generated_at: str) -> str:
    safe = generated_at.replace(":", "").replace("-", "").replace("+", "_").replace(".", "_")
    return f"goal_traceability_{safe}"


def pct(value: Any) -> str:
    try:
        return f"{float(value or 0) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
