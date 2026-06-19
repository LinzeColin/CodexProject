from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from .boards import BOARD_CONFIGS
from .evidence import build_evidence_bundle
from .io import atomic_copy, atomic_write_json, atomic_write_text
from .model_compare import MODEL_COMPARISON_JSON
from .odds import parse_decimal_odds
from .recommendations import apply_public_time_adjusted_match_stakes, display_stake_aud
from .report_store import latest_automation_runs, latest_runs, load_optional_json
from .sidecar_pdf import chart_from_items, render_sidecar_pdf
from .visuals import build_visual_summary, chart_by_id


DASHBOARD_LATEST = "tab_fifa_dashboard_latest.html"
DASHBOARD_DATA_LATEST = "tab_fifa_dashboard_data_latest.json"
DASHBOARD_MD_LATEST = "tab_fifa_dashboard_latest.md"
DASHBOARD_PDF_LATEST = "tab_fifa_dashboard_latest.pdf"


def write_dashboard(output_dir: Path, db_path: Path, manifest: Dict, publish_latest: bool = True) -> Dict:
    output_dir = Path(output_dir)
    payload = build_dashboard_payload(output_dir, db_path, manifest)
    run_id = payload["run_id"]
    latest_html = output_dir / DASHBOARD_LATEST
    latest_json = output_dir / DASHBOARD_DATA_LATEST
    run_html = output_dir / f"tab_fifa_dashboard_{run_id}.html"
    run_json = output_dir / f"tab_fifa_dashboard_data_{run_id}.json"
    html_text = render_dashboard_html(payload)
    atomic_write_json(run_json, payload)
    atomic_write_text(run_html, html_text)
    if publish_latest:
        publish_dashboard_latest(output_dir, run_html, run_json)
    dashboard_path = latest_html if publish_latest else run_html
    dashboard_data_path = latest_json if publish_latest else run_json
    return {
        "dashboard": str(dashboard_path),
        "dashboard_run_copy": str(run_html),
        "dashboard_latest": str(latest_html),
        "dashboard_markdown": str(output_dir / DASHBOARD_MD_LATEST),
        "dashboard_pdf": str(output_dir / DASHBOARD_PDF_LATEST),
        "dashboard_data": str(dashboard_data_path),
        "dashboard_data_run_copy": str(run_json),
        "dashboard_data_latest": str(latest_json),
        "run_id": run_id,
        "kpi_count": len(payload["kpis"]),
        "chart_count": len(payload.get("visual_summary", [])),
    }


def publish_dashboard_latest(output_dir: Path, run_html: Path, run_json: Path) -> Dict:
    output_dir = Path(output_dir)
    latest_html = output_dir / DASHBOARD_LATEST
    latest_json = output_dir / DASHBOARD_DATA_LATEST
    atomic_copy(run_json, latest_json)
    atomic_copy(run_html, latest_html)
    sidecar = write_dashboard_sidecar_bundle(output_dir)
    return {
        "dashboard": str(latest_html),
        "dashboard_data": str(latest_json),
        "dashboard_markdown": str(output_dir / DASHBOARD_MD_LATEST),
        "dashboard_pdf": str(output_dir / DASHBOARD_PDF_LATEST),
        "sidecar": sidecar,
    }


def write_dashboard_sidecar_bundle(output_dir: Path) -> Dict:
    output_dir = Path(output_dir)
    json_path = output_dir / DASHBOARD_DATA_LATEST
    payload = load_optional_json(json_path)
    if not payload:
        return {"status": "missing_dashboard_data", "json": str(json_path)}
    md_path = output_dir / DASHBOARD_MD_LATEST
    pdf_path = output_dir / DASHBOARD_PDF_LATEST
    atomic_write_text(md_path, render_dashboard_markdown(payload))
    pdf_summary = write_dashboard_pdf(payload, pdf_path)
    payload.setdefault("artifacts", {})
    payload["artifacts"].update(
        {
            "dashboard": DASHBOARD_LATEST,
            "dashboard_data": DASHBOARD_DATA_LATEST,
            "markdown": DASHBOARD_MD_LATEST,
            "pdf": DASHBOARD_PDF_LATEST,
            "pdf_summary": pdf_summary,
        }
    )
    atomic_write_json(json_path, payload)
    return {
        "status": "ready",
        "markdown": str(md_path),
        "pdf": str(pdf_path),
        "pdf_summary": pdf_summary,
    }


def build_dashboard_payload(output_dir: Path, db_path: Path, manifest: Dict) -> Dict:
    outputs = manifest.get("outputs", {})
    portfolio = load_output_json(output_dir, outputs, "portfolio_gate", "portfolio_automation_gate_v0_12.json")
    preflight = load_output_json(output_dir, outputs, "automation_preflight", "automation_preflight_latest.json")
    raw_refresh = load_output_json(output_dir, outputs, "raw_refresh_manifest", "raw_refresh_manifest_latest.json")
    safety = load_output_json(output_dir, outputs, "safety_gate", "automation_safety_gate.json")
    bankroll = load_run_bankroll(output_dir, outputs, manifest.get("report_date", ""))
    recommendations_by_board = load_recommendations_by_board(output_dir)
    if "world_cup_matches" in recommendations_by_board:
        recommendations_by_board["world_cup_matches"] = apply_public_time_adjusted_match_stakes(
            recommendations_by_board["world_cup_matches"],
            bankroll,
        )
    model_comparison = load_model_comparison(output_dir, outputs)
    portfolio_compare = load_portfolio_compare(output_dir, outputs)
    match_recommendations = recommendations_by_board.get("world_cup_matches", {}).get("recommendations", [])
    compare = portfolio_compare or recommendations_by_board.get("world_cup_matches", {}).get("daily_compare", {})
    compare_summary = compare.get("summary", {}) if isinstance(compare, dict) else {}
    board_statuses = portfolio.get("board_statuses", [])
    generated_at = datetime.now(timezone.utc).isoformat()
    technical_ready = bool(manifest.get("technical_automation_ready") or outputs.get("technical_automation_ready"))
    automation_entry_ready = bool(manifest.get("automation_entry_ready") or outputs.get("automation_entry_ready"))
    ready_boards = f"{portfolio.get('ready_required_board_count', 0)}/{portfolio.get('required_board_count', len(BOARD_CONFIGS))}"
    exposure = float(outputs.get("pdf_time_adjusted_new_exposure_aud") or bankroll.get("time_adjusted_new_exposure_aud") or 0)
    model_summary = model_comparison.get("summary", {}) if isinstance(model_comparison, dict) else {}
    high_divergence_count = int(model_summary.get("high_divergence_count") or 0)
    recent = public_recent_runs(latest_runs(db_path))
    automation_history = public_automation_runs(latest_automation_runs(db_path))
    recommendation_counts = board_recommendation_counts(recommendations_by_board, bankroll)
    normalized_compare_summary = {
        "added_count": int(compare_summary.get("added_count") or 0),
        "removed_count": int(compare_summary.get("removed_count") or 0),
        "changed_count": int(compare_summary.get("changed_count") or 0),
        "retained_count": int(compare_summary.get("retained_count") or 0),
        "exposure_change_aud": float(compare_summary.get("exposure_change_aud") or 0),
    }
    visual_summary = build_visual_summary(
        board_statuses=board_statuses,
        compare_summary=normalized_compare_summary,
        recommendation_counts=recommendation_counts,
        match_recommendations=match_recommendations[:7],
        model_rows=model_comparison.get("rows", [])[:7] if isinstance(model_comparison, dict) else [],
        model_references=model_comparison.get("references", []) if isinstance(model_comparison, dict) else [],
    )
    evidence = build_evidence_bundle(output_dir, manifest)
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "run_id": manifest.get("run_id", "unknown"),
        "report_date": manifest.get("report_date"),
        "status": manifest.get("status", ""),
        "technical_ready": technical_ready,
        "automation_entry_ready": automation_entry_ready,
        "automation_authorized": bool(manifest.get("user_automation_authorized")),
        "kpis": [
            {"label": "技术自动化", "value": "通过" if technical_ready else "未通过", "state": "ok" if technical_ready else "warn"},
            {"label": "正式调度入口", "value": "已授权" if automation_entry_ready else "未授权", "state": "ok" if automation_entry_ready else "neutral"},
            {"label": "板块就绪", "value": ready_boards, "state": "ok" if portfolio.get("portfolio_automation_ready") else "warn"},
            {"label": "新增执行金额", "value": f"AUD {exposure:,.0f}", "state": "alert" if exposure > 0 else "neutral"},
            {"label": "报告对比", "value": format_compare_value(compare_summary), "state": "ok" if not compare_summary.get("changed_count") else "warn"},
            {"label": "模型分歧", "value": f"{high_divergence_count}场高分歧", "state": "warn" if high_divergence_count else "ok"},
            {"label": "本地数据库", "value": "已保存" if recent else "待写入", "state": "ok" if recent else "neutral"},
            {"label": "自动化历史", "value": f"{len(automation_history)}次", "state": "ok" if automation_history else "neutral"},
        ],
        "board_statuses": board_statuses,
        "recommendations": flatten_recommendations(recommendations_by_board, bankroll),
        "match_recommendations": match_recommendations,
        "recommendations_by_board": recommendation_counts,
        "visual_summary": visual_summary,
        "evidence": {
            "summary": evidence.get("summary", {}),
            "source_logs": evidence.get("source_logs", [])[:18],
            "audit_logs": evidence.get("audit_logs", [])[:18],
            "missing_data_logs": evidence.get("missing_data_logs", [])[:18],
            "manual_review_queue": evidence.get("manual_review_queue", [])[:18],
        },
        "model_comparison": {
            "ready": bool(model_comparison.get("ready")),
            "match_count": int(model_comparison.get("match_count") or 0),
            "summary": {
                "high_divergence_count": high_divergence_count,
                "avg_current_vs_elo_disagreement": float(model_summary.get("avg_current_vs_elo_disagreement") or 0),
            },
            "rows": model_comparison.get("rows", [])[:12],
            "references": model_comparison.get("references", []),
            "source_adoption": model_comparison.get("source_adoption", {}),
        },
        "compare_summary": normalized_compare_summary,
        "portfolio_compare": {
            "ready": bool(portfolio_compare),
            "by_board": list((portfolio_compare.get("by_board", {}) if isinstance(portfolio_compare, dict) else {}).values()),
            "changed": (portfolio_compare.get("changed", []) if isinstance(portfolio_compare, dict) else [])[:12],
        },
        "bankroll": public_bankroll_payload(bankroll),
        "preflight": {
            "technical_preflight_ready": bool(preflight.get("technical_preflight_ready")),
            "automation_entry_ready": bool(preflight.get("automation_entry_ready")),
            "blocking_reasons": preflight.get("blocking_reasons", []),
        },
        "raw_refresh": {
            "ready": bool(raw_refresh.get("raw_refresh_ready")),
            "ready_required": f"{raw_refresh.get('ready_required_target_count', 0)}/{raw_refresh.get('required_target_count', 0)}",
            "generated_at": raw_refresh.get("generated_at"),
        },
        "safety": {
            "ready": bool(safety.get("automation_safety_ready")),
            "blocking_reasons": safety.get("blocking_reasons", []),
        },
        "recent_runs": recent,
        "automation_runs": automation_history,
        "artifacts": {
            "pdf_output_copy": public_artifact_ref(outputs.get("pdf_output_copy")),
            "bankroll_plan": public_artifact_ref(outputs.get("bankroll_plan")),
            "model_comparison_report": public_artifact_ref(outputs.get("model_comparison_report")),
            "model_comparison_pdf": public_artifact_ref(outputs.get("model_comparison_pdf")),
            "manifest": public_artifact_ref(outputs.get("manifest")),
            "report_database": public_artifact_ref(db_path),
            "report_index": public_artifact_ref(outputs.get("report_index")),
            "report_index_latest": public_artifact_ref(outputs.get("report_index_latest")),
            "report_index_report": public_artifact_ref(outputs.get("report_index_report")),
            "report_index_report_latest": public_artifact_ref(outputs.get("report_index_report_latest")),
            "report_index_pdf": public_artifact_ref(outputs.get("report_index_pdf")),
            "report_index_pdf_latest": public_artifact_ref(outputs.get("report_index_pdf_latest")),
            "report_intelligence": public_artifact_ref(outputs.get("report_intelligence")),
            "report_intelligence_latest": public_artifact_ref(outputs.get("report_intelligence_latest")),
            "report_intelligence_report": public_artifact_ref(outputs.get("report_intelligence_report")),
            "report_intelligence_report_latest": public_artifact_ref(outputs.get("report_intelligence_report_latest")),
            "report_intelligence_pdf": public_artifact_ref(outputs.get("report_intelligence_pdf")),
            "report_intelligence_pdf_latest": public_artifact_ref(outputs.get("report_intelligence_pdf_latest")),
            "automation_readiness": public_artifact_ref(outputs.get("automation_readiness")),
            "automation_readiness_report": public_artifact_ref(outputs.get("automation_readiness_report")),
            "automation_readiness_pdf": public_artifact_ref(outputs.get("automation_readiness_pdf")),
            "automation_candidate": public_artifact_ref(outputs.get("automation_candidate")),
            "automation_candidate_report": public_artifact_ref(outputs.get("automation_candidate_report")),
            "automation_candidate_pdf": public_artifact_ref(outputs.get("automation_candidate_pdf")),
        },
    }


def render_dashboard_markdown(payload: Dict) -> str:
    kpis = payload.get("kpis") or []
    model = payload.get("model_comparison") or {}
    model_summary = model.get("summary") or {}
    compare = payload.get("compare_summary") or {}
    preflight = payload.get("preflight") or {}
    raw_refresh = payload.get("raw_refresh") or {}
    safety = payload.get("safety") or {}
    lines = [
        "# TAB FIFA 本地业务 Dashboard",
        "",
        "本报告是本地 HTML Dashboard 的正式 Markdown/PDF 镜像，用于把核心入口纳入日报归档、数据库和新旧报告覆盖审计。它只生成研究报告，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- report_date: `{md(payload.get('report_date'))}`",
        f"- run_id: `{md(payload.get('run_id'))}`",
        f"- status: `{md(payload.get('status'))}`",
        f"- technical_ready: `{bool(payload.get('technical_ready'))}`",
        f"- automation_entry_ready: `{bool(payload.get('automation_entry_ready'))}`",
        f"- automation_authorized: `{bool(payload.get('automation_authorized'))}`",
        f"- raw_refresh: `{md(raw_refresh.get('ready_required'))}` / ready `{bool(raw_refresh.get('ready'))}`",
        f"- public_safety_ready: `{bool(safety.get('ready'))}`",
        f"- model_high_divergence_count: `{int(model_summary.get('high_divergence_count') or 0)}`",
        f"- report_compare: `+{int(compare.get('added_count') or 0)} / -{int(compare.get('removed_count') or 0)} / changed {int(compare.get('changed_count') or 0)}`",
        "",
        "## KPI",
        "",
        "| 指标 | 值 | 状态 |",
        "|---|---|---|",
    ]
    for item in kpis:
        lines.append(f"| {md(item.get('label'))} | {md(item.get('value'))} | {md(item.get('state'))} |")
    lines.extend(
        [
            "",
            "## 可视化图表摘要",
            "",
            "| 图表 | 类型 | 指标 | 说明 |",
            "|---|---|---|---|",
        ]
    )
    for chart in payload.get("visual_summary") or []:
        items = ", ".join(f"{item.get('label')}={item.get('display')}" for item in (chart.get("items") or [])[:5])
        lines.append(f"| {md(chart.get('title'))} | {md(chart.get('kind'))} | {md(items)} | {md(chart.get('note'))} |")
    lines.extend(
        [
            "",
            "## 推荐候选",
            "",
            "| 板块 | 比赛/对象 | 盘口 | 选择 | 赔率 | 概率 | EV | 金额 | 操作 | 模型/理由 |",
            "|---|---|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in (payload.get("recommendations") or [])[:12]:
        stake = float(row.get("stake_aud") or 0)
        action = "买入" if stake > 0 else "观察"
        lines.append(
            "| {board} | {event} | {market} | {selection} | {odds} | {prob} | {ev} | {stake} | {action} | {reason} |".format(
                board=md(short_board_name(row.get("board_name"))),
                event=md(row.get("event_name")),
                market=md(row.get("market")),
                selection=md(row.get("selection")),
                odds=md(fmt_odds(row.get("odds"))),
                prob=md(fmt_pct(row.get("probability"))),
                ev=md(fmt_pct(row.get("expected_value"))),
                stake=md(f"AUD {stake:,.0f}"),
                action=md(action),
                reason=md(row.get("model_summary") or row.get("decision_reason") or ""),
            )
        )
    lines.extend(
        [
            "",
            "## 模型共识交叉验证",
            "",
            "| 比赛 | 共识方向 | 均值概率 | 置信 | 最大分歧 | 评级来源 |",
            "|---|---|---:|---|---:|---|",
        ]
    )
    for row in (model.get("rows") or [])[:10]:
        consensus = row.get("consensus") or {}
        disagreement = row.get("disagreement") or {}
        ratings = row.get("ratings") or {}
        lines.append(
            "| {match} | {selection} | {prob} | {confidence} | {spread} | {source} |".format(
                match=md(row.get("match")),
                selection=md(consensus.get("selection")),
                prob=md(fmt_pct(consensus.get("mean_probability"))),
                confidence=md(consensus.get("confidence")),
                spread=md(fmt_pct(disagreement.get("max_abs_current_vs_elo_dc"))),
                source=md(ratings.get("source")),
            )
        )
    blockers = preflight.get("blocking_reasons") or []
    lines.extend(
        [
            "",
            "## Automation / 门禁",
            "",
            f"- technical_preflight_ready: `{bool(preflight.get('technical_preflight_ready'))}`",
            f"- automation_entry_ready: `{bool(preflight.get('automation_entry_ready'))}`",
            f"- raw_refresh_ready: `{bool(raw_refresh.get('ready'))}`",
            f"- safety_ready: `{bool(safety.get('ready'))}`",
            f"- blocker_count: `{len(blockers)}`",
        ]
    )
    for item in blockers[:6]:
        lines.append(f"- blocker: {md(item)}")
    lines.extend(
        [
            "",
            "## 新旧对比与本地归档",
            "",
            f"- added_count: `{int(compare.get('added_count') or 0)}`",
            f"- removed_count: `{int(compare.get('removed_count') or 0)}`",
            f"- changed_count: `{int(compare.get('changed_count') or 0)}`",
            f"- retained_count: `{int(compare.get('retained_count') or 0)}`",
            f"- exposure_change_aud: `AUD {float(compare.get('exposure_change_aud') or 0):,.0f}`",
            "",
            "安全边界：本 Dashboard 只读展示公开研究、报告历史、模型分歧和门禁状态；不点击赔率、不添加投注单、不自动下注。",
        ]
    )
    return "\n".join(lines)


def write_dashboard_pdf(payload: Dict, output_path: Path) -> Dict:
    charts = dashboard_pdf_charts(payload)
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 本地业务 Dashboard",
        subtitle="HTML Dashboard 的正式 PDF 镜像：推荐、模型分歧、板块状态、新旧对比、automation 门禁和本地归档；不自动下注。",
        summary_rows=[
            ("报告日期", str(payload.get("report_date") or "")),
            ("Run", str(payload.get("run_id") or "")),
            ("状态", str(payload.get("status") or "")),
            ("技术自动化", "通过" if payload.get("technical_ready") else "未通过"),
            ("调度入口", "已授权" if payload.get("automation_entry_ready") else "未授权"),
            ("安全门禁", "通过" if (payload.get("safety") or {}).get("ready") else "未通过"),
            ("模型高分歧", str(((payload.get("model_comparison") or {}).get("summary") or {}).get("high_divergence_count", 0))),
        ],
        charts=charts,
        table_headers=["板块", "对象", "盘口", "选择", "赔率", "概率", "EV", "金额", "操作"],
        table_rows=dashboard_recommendation_table_rows(payload),
        extra_tables=[
            {
                "title": "KPI",
                "headers": ["指标", "值", "状态"],
                "rows": [[str(item.get("label", "")), str(item.get("value", "")), str(item.get("state", ""))] for item in (payload.get("kpis") or [])],
            },
            {
                "title": "板块状态",
                "headers": ["板块", "Ready", "Raw", "Gate", "缺口"],
                "rows": dashboard_board_rows(payload),
            },
            {
                "title": "模型共识",
                "headers": ["比赛", "共识", "均值概率", "置信", "最大分歧", "来源"],
                "rows": dashboard_model_rows(payload),
            },
        ],
    )


def dashboard_pdf_charts(payload: Dict) -> List[Dict]:
    charts: List[Dict] = []
    for chart in (payload.get("visual_summary") or [])[:8]:
        items = []
        for item in chart.get("items") or []:
            value = item.get("value")
            if str(chart.get("unit") or "") == "%":
                value = float(value or 0) * 100
            items.append((str(item.get("label") or ""), float(value or 0)))
        charts.append(chart_from_items(str(chart.get("title") or "Dashboard chart"), items, "#1F4E79"))
    return charts


def dashboard_recommendation_table_rows(payload: Dict) -> List[List[str]]:
    rows: List[List[str]] = []
    for item in (payload.get("recommendations") or [])[:12]:
        stake = float(item.get("stake_aud") or 0)
        rows.append(
            [
                short_board_name(item.get("board_name")),
                str(item.get("event_name") or ""),
                str(item.get("market") or ""),
                str(item.get("selection") or ""),
                fmt_odds(item.get("odds")),
                fmt_pct(item.get("probability")),
                fmt_pct(item.get("expected_value")),
                f"AUD {stake:,.0f}",
                "买入" if stake > 0 else "观察",
            ]
        )
    return rows


def dashboard_board_rows(payload: Dict) -> List[List[str]]:
    rows: List[List[str]] = []
    for board in (payload.get("board_statuses") or [])[:10]:
        rows.append(
            [
                str(board.get("name") or ""),
                "是" if board.get("ready") else "否",
                "新鲜/有效" if board.get("raw_fresh") and board.get("raw_valid") else "需刷新",
                "通过" if board.get("gate_ready") else "未通过",
                ", ".join(board.get("missing") or []) or "无",
            ]
        )
    return rows


def dashboard_model_rows(payload: Dict) -> List[List[str]]:
    rows: List[List[str]] = []
    model = payload.get("model_comparison") or {}
    for item in (model.get("rows") or [])[:10]:
        consensus = item.get("consensus") or {}
        disagreement = item.get("disagreement") or {}
        ratings = item.get("ratings") or {}
        rows.append(
            [
                str(item.get("match") or ""),
                str(consensus.get("selection") or ""),
                fmt_pct(consensus.get("mean_probability")),
                str(consensus.get("confidence") or ""),
                fmt_pct(disagreement.get("max_abs_current_vs_elo_dc")),
                str(ratings.get("source") or ""),
            ]
        )
    return rows


def load_recommendations_by_board(output_dir: Path) -> Dict[str, Dict]:
    result = {}
    for board in BOARD_CONFIGS:
        if board.recommendations_artifact:
            result[board.board_id] = load_optional_json(output_dir / board.recommendations_artifact)
    return result


def load_latest_bankroll(output_dir: Path, report_date: str) -> Dict:
    if report_date:
        exact = output_dir / f"tab_fifa_bankroll_plan_{report_date}.json"
        if exact.exists():
            return load_optional_json(exact)
    candidates = sorted(output_dir.glob("tab_fifa_bankroll_plan_*.json"), key=bankroll_sort_key, reverse=True)
    return load_optional_json(candidates[0]) if candidates else {}


def load_run_bankroll(output_dir: Path, outputs: Dict, report_date: str) -> Dict:
    for key in ["bankroll_plan_run_copy", "bankroll_plan"]:
        path = resolve_output_artifact(output_dir, outputs.get(key))
        if path and path.exists():
            return load_optional_json(path)
    return load_latest_bankroll(output_dir, report_date)


def load_output_json(output_dir: Path, outputs: Dict, key: str, fallback_name: str) -> Dict:
    path = resolve_output_artifact(output_dir, outputs.get(key))
    if path and path.exists():
        return load_optional_json(path)
    return load_optional_json(output_dir / fallback_name)


def resolve_output_artifact(output_dir: Path, value) -> Path | None:
    text = str(value or "")
    if not text:
        return None
    path = Path(text)
    return path if path.is_absolute() else output_dir / path


def public_bankroll_payload(bankroll: Dict) -> Dict:
    allowed = {}
    for key in [
        "report_date",
        "pdf_output_copy",
        "base_selected_exposure_aud",
        "time_adjusted_new_exposure_aud",
        "match_candidate_count",
        "private_pdf_path_omitted",
        "private_fields_omitted",
    ]:
        if key in bankroll:
            allowed[key] = bankroll[key]
    if "pdf_output_copy" in allowed:
        allowed["pdf_output_copy"] = public_artifact_ref(allowed["pdf_output_copy"])
    return allowed


def public_recent_runs(rows: Iterable[Dict]) -> List[Dict]:
    result = []
    for row in rows:
        public_row = dict(row)
        if public_row.get("dashboard_path"):
            public_row["dashboard_path"] = public_artifact_ref(public_row["dashboard_path"])
        result.append(public_row)
    return result


def public_automation_runs(rows: Iterable[Dict]) -> List[Dict]:
    result = []
    for row in rows:
        public_row = dict(row)
        public_row["capture_log"] = public_artifact_ref(public_row.get("capture_log"))
        public_row["import_log"] = public_artifact_ref(public_row.get("import_log"))
        result.append(public_row)
    return result


def load_model_comparison(output_dir: Path, outputs: Dict) -> Dict:
    return load_output_json(output_dir, outputs, "model_comparison_json", MODEL_COMPARISON_JSON)


def load_portfolio_compare(output_dir: Path, outputs: Dict) -> Dict:
    return load_output_json(output_dir, outputs, "portfolio_daily_compare", "portfolio_daily_compare_latest.json")


def bankroll_sort_key(path: Path):
    stem = path.stem.replace("tab_fifa_bankroll_plan_", "")
    date_part = stem.split("_", 1)[0]
    try:
        return datetime.strptime(date_part, "%d%m%Y")
    except ValueError:
        return datetime.min


def flatten_recommendations(recommendations_by_board: Dict[str, Dict], bankroll: Dict | None = None) -> List[Dict]:
    rows: List[Dict] = []
    for board in BOARD_CONFIGS:
        payload = recommendations_by_board.get(board.board_id, {})
        for item in payload.get("recommendations", []):
            probability = item.get("model_probability", item.get("no_vig_probability", item.get("probability", 0)))
            event_name = item.get("match") or item.get("team") or (f"Group {item.get('group')}" if item.get("group") else item.get("market", ""))
            selection = item.get("selection") or item.get("team", "")
            stake_aud = display_stake_aud(board.board_id, item, bankroll)
            rows.append(
                {
                    "board_id": board.board_id,
                    "board_name": board.name,
                    "event_name": event_name,
                    "market": item.get("market", ""),
                    "selection": selection,
                    "odds": item.get("odds"),
                    "probability": probability,
                    "expected_value": item.get("expected_value"),
                    "stake_aud": stake_aud,
                    "base_stake_aud": float(item.get("stake_aud") or 0),
                    "decision": "buy" if stake_aud > 0 else item.get("decision", "watch_or_no_bet"),
                    "decision_reason": item.get("rationale", ""),
                    "model_summary": (item.get("model_signal") or {}).get("summary_zh", item.get("model_divergence_summary", "")),
                    "model_signal": item.get("model_signal", {}),
                }
            )
    rows.sort(key=lambda item: (float(item.get("stake_aud") or 0), float(item.get("expected_value") or 0)), reverse=True)
    return rows


def board_recommendation_counts(recommendations_by_board: Dict[str, Dict], bankroll: Dict | None = None) -> List[Dict]:
    counts = []
    for board in BOARD_CONFIGS:
        payload = recommendations_by_board.get(board.board_id, {})
        recommendations = payload.get("recommendations", [])
        counts.append(
            {
                "board_id": board.board_id,
                "name": board.name.replace("2026 World Cup ", ""),
                "count": len(recommendations),
                "stake_aud": sum(display_stake_aud(board.board_id, item, bankroll) for item in recommendations),
            }
        )
    return counts


def render_dashboard_html(payload: Dict) -> str:
    board_rows = render_board_rows(payload["board_statuses"])
    recommendation_rows = render_recommendation_rows(payload["recommendations"][:12])
    model_rows = render_model_rows(payload["model_comparison"]["rows"][:8])
    recent_rows = render_recent_rows(payload["recent_runs"])
    automation_rows = render_automation_run_rows(payload.get("automation_runs", []))
    compare_board_rows = render_portfolio_compare_rows(payload.get("portfolio_compare", {}).get("by_board", []))
    evidence_rows = render_source_log_rows(payload.get("evidence", {}).get("source_logs", []))
    audit_rows = render_audit_log_rows(payload.get("evidence", {}).get("audit_logs", []))
    review_rows = render_manual_review_rows(payload.get("evidence", {}).get("manual_review_queue", []))
    charts = payload.get("visual_summary", [])
    blocking = payload["preflight"].get("blocking_reasons", [])[:4]
    blocking_text = "<br>".join(esc(reason) for reason in blocking) if blocking else "无阻塞；正式 automation 仍需用户授权。"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TAB FIFA 盘口研究仪表盘</title>
  <style>
    :root {{
      --ink:#172033;
      --muted:#5F6B7A;
      --line:#D9E1EA;
      --surface:#FFFFFF;
      --soft:#F5F7FA;
      --head:#FBFCFE;
      --green:#247A5A;
      --red:#C62828;
      --blue:#1F4E79;
      --amber:#A56710;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Arial,sans-serif;
      color:var(--ink);
      background:#F1F4F7;
    }}
    main {{ max-width:1240px; margin:0 auto; padding:24px; }}
    header {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-end; margin-bottom:18px; }}
    h1 {{ margin:0; font-size:25px; line-height:1.25; letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:17px; line-height:1.3; }}
    .sub {{ color:var(--muted); font-size:13px; margin-top:6px; }}
    .pill {{ display:inline-flex; align-items:center; min-height:26px; padding:4px 9px; border:1px solid var(--line); border-radius:8px; background:var(--surface); color:var(--muted); font-size:12px; }}
    .grid {{ display:grid; gap:14px; }}
    .kpis {{ grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); margin-bottom:14px; }}
    .panel {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px; }}
    .kpi-label {{ color:var(--muted); font-size:12px; margin-bottom:8px; }}
    .kpi-value {{ font-size:20px; font-weight:700; white-space:nowrap; }}
    .state-ok {{ border-top:3px solid var(--green); }}
    .state-warn {{ border-top:3px solid var(--amber); }}
    .state-alert {{ border-top:3px solid var(--red); }}
    .state-neutral {{ border-top:3px solid #91A0B3; }}
    .layout {{ grid-template-columns:1.1fr .9fr; }}
    .charts {{ grid-template-columns:1fr 1fr; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th {{ background:var(--head); color:#0B1F3A; text-align:left; font-weight:700; }}
    th,td {{ border-bottom:1px solid var(--line); padding:8px 7px; vertical-align:top; overflow-wrap:anywhere; }}
    tr:nth-child(even) td {{ background:#FAFBFC; }}
    .buy {{ background:var(--red); color:white; border-radius:5px; padding:2px 6px; display:inline-block; }}
    .watch {{ color:var(--muted); }}
    .ok {{ color:var(--green); font-weight:700; }}
    .bad {{ color:var(--red); font-weight:700; }}
    svg {{ width:100%; height:auto; display:block; }}
    .note {{ color:var(--muted); font-size:12px; line-height:1.55; }}
    .artifacts a {{ color:var(--blue); text-decoration:none; word-break:break-all; }}
    .artifacts a:hover {{ text-decoration:underline; }}
    @media (max-width: 960px) {{
      main {{ padding:14px; }}
      header {{ display:block; }}
      .kpis,.layout,.charts {{ grid-template-columns:1fr; }}
      .kpi-value {{ white-space:normal; }}
      .panel {{ min-width:0; overflow:hidden; }}
      table {{ font-size:11px; table-layout:fixed; }}
      th,td {{ padding:7px 5px; }}
      .recommendation-table {{ table-layout:auto; }}
      .recommendation-table thead {{ display:none; }}
      .recommendation-table tr {{ display:block; border-bottom:1px solid var(--line); padding:8px 0; }}
      .recommendation-table td {{
        display:grid;
        grid-template-columns:72px minmax(0,1fr);
        gap:8px;
        border-bottom:0;
        padding:4px 2px;
        background:transparent !important;
      }}
      .recommendation-table td::before {{
        content:attr(data-label);
        color:var(--muted);
        font-weight:700;
      }}
      .recommendation-table .buy,
      .recommendation-table .watch {{
        justify-self:start;
        width:max-content;
      }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>TAB FIFA 2026 盘口研究仪表盘</h1>
      <div class="sub">报告日期 {esc(payload.get("report_date"))} · Run {esc(payload.get("run_id"))}</div>
    </div>
    <div class="pill">静态本地文件 · 不自动下注 · 更新时间 {esc(payload.get("generated_at"))}</div>
  </header>

  <section class="grid kpis">
    {render_kpis(payload["kpis"])}
  </section>

  <section class="grid layout">
    <div class="panel">
      <h2>板块自动化状态</h2>
      {render_chart_svg(chart_by_id(charts, "board_readiness"), width=620)}
      <table aria-label="板块状态表">
        <thead><tr><th>板块</th><th>就绪</th><th>Raw</th><th>Gate</th><th>缺口</th></tr></thead>
        <tbody>{board_rows}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>新旧报告对比</h2>
      {render_chart_svg(chart_by_id(charts, "report_compare"), width=430)}
      <div class="note">{blocking_text}</div>
      <table aria-label="板块级新旧报告对比">
        <thead><tr><th>板块</th><th>新增</th><th>移除</th><th>变化</th><th>金额变化</th></tr></thead>
        <tbody>{compare_board_rows}</tbody>
      </table>
    </div>
  </section>

		  <section class="grid charts" style="margin-top:14px;">
	    <div class="panel">
	      <h2>盘口推荐分布</h2>
	      {render_chart_svg(chart_by_id(charts, "recommendation_distribution"), width=530)}
	    </div>
	    <div class="panel">
	      <h2>跨板块新增金额</h2>
	      {render_chart_svg(chart_by_id(charts, "stake_allocation"), width=530)}
	    </div>
	    <div class="panel">
	      <h2>比赛盘口价值排序</h2>
	      {render_chart_svg(chart_by_id(charts, "match_value"), width=590)}
	    </div>
	    <div class="panel">
	      <h2>概率-赔率边际</h2>
	      {render_chart_svg(chart_by_id(charts, "odds_probability_edge"), width=590)}
	    </div>
		    <div class="panel">
		      <h2>开源模型分歧</h2>
		      {render_chart_svg(chart_by_id(charts, "model_divergence"), width=590)}
		    </div>
		    <div class="panel">
		      <h2>模型共识强度</h2>
		      {render_chart_svg(chart_by_id(charts, "model_consensus"), width=590)}
		    </div>
		    <div class="panel">
		      <h2>开源模型采用覆盖</h2>
		      {render_chart_svg(chart_by_id(charts, "model_source_coverage"), width=590)}
		    </div>
		    <div class="panel">
		      <h2>模型能力覆盖矩阵</h2>
		      {render_chart_svg(chart_by_id(charts, "model_capability_coverage"), width=590)}
		    </div>
		  </section>

	  <section class="panel" style="margin-top:14px;">
	    <h2>候选盘口与操作建议</h2>
    <table class="recommendation-table" aria-label="候选盘口">
      <thead><tr><th>板块</th><th>比赛/对象</th><th>盘口</th><th>选择</th><th>赔率</th><th>概率</th><th>EV</th><th>金额</th><th>操作</th><th>模型/理由</th></tr></thead>
      <tbody>{recommendation_rows}</tbody>
    </table>
	  </section>

		  <section class="panel" style="margin-top:14px;">
		    <h2>模型共识交叉验证</h2>
		    <table aria-label="模型共识交叉验证">
		      <thead><tr><th>比赛</th><th>共识方向</th><th>均值概率</th><th>置信</th><th>最大分歧</th><th>评级来源</th></tr></thead>
		      <tbody>{model_rows}</tbody>
		    </table>
		  </section>

		  <section class="panel" style="margin-top:14px;">
		    <h2>开源模型采用矩阵</h2>
		    <table aria-label="开源模型采用矩阵">
		      <thead><tr><th>来源</th><th>方法族</th><th>状态</th><th>覆盖盘口/模块</th><th>可复用/UI启发</th><th>本系统用途</th></tr></thead>
		      <tbody>{render_model_source_rows(payload["model_comparison"].get("source_adoption", {}))}</tbody>
		    </table>
		  </section>

		  <section class="grid layout" style="margin-top:14px;">
		    <div class="panel">
		      <h2>证据源日志</h2>
		      <table aria-label="证据源日志">
		        <thead><tr><th>类型</th><th>来源</th><th>状态</th><th>证据层</th><th>用途/说明</th></tr></thead>
		        <tbody>{evidence_rows}</tbody>
		      </table>
		    </div>
		    <div class="panel">
		      <h2>运行审计与人工复核</h2>
		      <table aria-label="运行审计">
		        <thead><tr><th>检查</th><th>状态</th><th>级别</th><th>说明</th></tr></thead>
		        <tbody>{audit_rows}</tbody>
		      </table>
		      <div style="height:10px"></div>
		      <table aria-label="人工复核队列">
		        <thead><tr><th>队列</th><th>对象</th><th>级别</th><th>说明</th></tr></thead>
		        <tbody>{review_rows}</tbody>
		      </table>
		    </div>
		  </section>

  <section class="grid layout" style="margin-top:14px;">
    <div class="panel">
      <h2>最近运行记录</h2>
      {render_recent_runs_svg(payload["recent_runs"])}
      <table aria-label="最近运行记录">
        <thead><tr><th>Run</th><th>状态</th><th>报告日</th><th>技术</th><th>金额</th></tr></thead>
        <tbody>{recent_rows}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>自动化运行历史</h2>
      {render_automation_runs_svg(payload.get("automation_runs", []))}
      <table aria-label="自动化运行历史">
        <thead><tr><th>Run</th><th>模式</th><th>状态</th><th>Raw</th><th>发布</th><th>私有持仓</th><th>Capture/Import</th></tr></thead>
        <tbody>{automation_rows}</tbody>
      </table>
    </div>
    <div class="panel artifacts" style="grid-column:1 / -1;">
      <h2>本地产物</h2>
      <p class="note">PDF、JSON、SQLite 和仪表盘都保存在本地；正式自动化只生成报告和数据库记录，不自动下注。</p>
      {render_artifact_links(payload["artifacts"])}
    </div>
  </section>
</main>
</body>
</html>
"""


def render_kpis(kpis: Iterable[Dict]) -> str:
    return "\n".join(
        f"""<div class="panel state-{esc(item.get('state', 'neutral'))}">
      <div class="kpi-label">{esc(item.get('label'))}</div>
      <div class="kpi-value">{esc(item.get('value'))}</div>
    </div>"""
        for item in kpis
    )


def render_board_rows(statuses: Iterable[Dict]) -> str:
    rows = []
    for board in statuses:
        ready = '<span class="ok">就绪</span>' if board.get("ready") else '<span class="bad">阻塞</span>'
        raw = "新鲜/有效" if board.get("raw_fresh") and board.get("raw_valid") else "需刷新"
        gate = "通过" if board.get("gate_ready") else "未通过"
        missing = ", ".join(board.get("missing") or []) or "none"
        rows.append(
            f"<tr><td>{esc(board.get('name'))}</td><td>{ready}</td><td>{esc(raw)}</td><td>{esc(gate)}</td><td>{esc(missing)}</td></tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="5">暂无板块状态</td></tr>'


def render_recommendation_rows(recommendations: Iterable[Dict]) -> str:
    rows = []
    for item in recommendations:
        stake = float(item.get("stake_aud") or 0)
        action = '<span class="buy">买入</span>' if stake > 0 else '<span class="watch">观察</span>'
        rows.append(
            "<tr>"
            f"<td data-label=\"板块\">{esc(short_board_name(item.get('board_name')))}</td>"
            f"<td data-label=\"对象\">{esc(item.get('event_name'))}</td>"
            f"<td data-label=\"盘口\">{esc(item.get('market'))}</td>"
            f"<td data-label=\"选择\">{esc(item.get('selection'))}</td>"
            f"<td data-label=\"赔率\">{fmt_odds(item.get('odds'))}</td>"
            f"<td data-label=\"概率\">{fmt_pct(item.get('probability'))}</td>"
            f"<td data-label=\"EV\">{fmt_pct(item.get('expected_value'))}</td>"
            f"<td data-label=\"金额\">AUD {stake:,.0f}</td>"
            f"<td data-label=\"操作\">{action}</td>"
            f"<td data-label=\"模型/理由\">{esc(item.get('model_summary') or item.get('decision_reason') or '')}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="10">暂无推荐</td></tr>'


def render_recent_rows(runs: Iterable[Dict]) -> str:
    rows = []
    for run in runs:
        technical = "通过" if run.get("technical_ready") else "未通过"
        rows.append(
            "<tr>"
            f"<td>{esc(run.get('run_id'))}</td>"
            f"<td>{esc(run.get('status'))}</td>"
            f"<td>{esc(run.get('report_date'))}</td>"
            f"<td>{esc(technical)}</td>"
            f"<td>AUD {float(run.get('time_adjusted_new_exposure_aud') or run.get('recommended_new_exposure_aud') or 0):,.0f}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="5">暂无数据库记录</td></tr>'


def render_automation_run_rows(runs: Iterable[Dict]) -> str:
    rows = []
    for run in runs:
        exit_code = int(run.get("exit_code") or 0)
        status_text = "通过" if exit_code == 0 else "失败"
        status_class = "ok" if exit_code == 0 else "bad"
        raw_ready = "Ready" if run.get("raw_refresh_ready") else "Blocked"
        publish = "可发布" if run.get("formal_report_publish_ready") else "不发布"
        capture = "启用" if run.get("my_bets_capture_enabled") else "未启用"
        raw_seen = "raw已见" if run.get("my_bets_raw_text_seen") else "raw未见"
        mode_label = automation_mode_label(run)
        rows.append(
            "<tr>"
            f"<td>{esc(run.get('automation_run_id'))}</td>"
            f"<td>{esc(mode_label)}</td>"
            f"<td><span class=\"{status_class}\">{esc(status_text)}</span><br>{esc(run.get('status'))}</td>"
            f"<td>{esc(raw_ready)}</td>"
            f"<td>{esc(publish)}</td>"
            f"<td>{esc(capture)}<br>{esc(raw_seen)}</td>"
            f"<td>capture {int(run.get('my_bets_capture_exit_code') or 0)} / import {int(run.get('my_bets_import_exit_code') or 0)}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="7">暂无 automation runner 记录</td></tr>'


def render_portfolio_compare_rows(rows_in: Iterable[Dict]) -> str:
    rows = []
    for item in rows_in:
        rows.append(
            "<tr>"
            f"<td>{esc(short_board_name(item.get('board_name')))}</td>"
            f"<td>{int(item.get('added_count') or 0)}</td>"
            f"<td>{int(item.get('removed_count') or 0)}</td>"
            f"<td>{int(item.get('changed_count') or 0)}</td>"
            f"<td>AUD {float(item.get('exposure_change_aud') or 0):,.0f}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="5">暂无跨板块对比数据</td></tr>'


def render_model_rows(rows_in: Iterable[Dict]) -> str:
    rows = []
    for item in rows_in:
        consensus = item.get("consensus", {})
        disagreement = item.get("disagreement", {})
        ratings = item.get("ratings", {})
        high = bool(disagreement.get("high_divergence"))
        disagreement_text = fmt_pct(disagreement.get("max_abs_current_vs_elo_dc"))
        disagreement_cell = f'<span class="bad">{disagreement_text}</span>' if high else disagreement_text
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('match'))}</td>"
            f"<td>{esc(consensus.get('selection'))}</td>"
            f"<td>{fmt_pct(consensus.get('mean_probability'))}</td>"
            f"<td>{esc(consensus.get('confidence'))}</td>"
            f"<td>{disagreement_cell}</td>"
            f"<td>{esc(ratings.get('source'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="6">暂无模型对比数据</td></tr>'


def render_model_source_rows(source_adoption: Dict) -> str:
    rows = []
    for item in source_adoption.get("rows", []):
        features = "; ".join((item.get("reusable_features") or [])[:2])
        layouts = "; ".join((item.get("layout_patterns") or [])[:2])
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('display_name') or item.get('source'))}</td>"
            f"<td>{esc(item.get('method_family'))}</td>"
            f"<td>{esc(source_status_label(item.get('adoption_status')))}</td>"
            f"<td>{esc(', '.join(item.get('coverage') or []))}</td>"
            f"<td>{esc(features + (' / ' if features and layouts else '') + layouts)}</td>"
            f"<td>{esc(item.get('report_usage'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="6">暂无开源模型采用数据</td></tr>'


def render_source_log_rows(rows_in: Iterable[Dict]) -> str:
    rows = []
    for item in rows_in:
        rows.append(
            "<tr>"
            f"<td>{esc(source_type_label(item.get('source_type')))}</td>"
            f"<td>{esc(item.get('name'))}</td>"
            f"<td>{esc(status_label(item.get('status')))}</td>"
            f"<td>{esc(item.get('evidence_layer'))}</td>"
            f"<td>{esc(item.get('usage') or item.get('message'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="5">暂无证据源日志</td></tr>'


def render_audit_log_rows(rows_in: Iterable[Dict]) -> str:
    rows = []
    for item in rows_in:
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('check_name'))}</td>"
            f"<td>{esc(status_label(item.get('status')))}</td>"
            f"<td>{esc(item.get('severity'))}</td>"
            f"<td>{esc(item.get('message'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="4">暂无审计记录</td></tr>'


def render_manual_review_rows(rows_in: Iterable[Dict]) -> str:
    rows = []
    for item in rows_in:
        rows.append(
            "<tr>"
            f"<td>{esc(review_type_label(item.get('queue_type')))}</td>"
            f"<td>{esc(item.get('item'))}</td>"
            f"<td>{esc(item.get('severity'))}</td>"
            f"<td>{esc(item.get('message'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="4">当前无阻塞型人工复核项</td></tr>'


def source_type_label(value) -> str:
    return {
        "official_public_source": "官方公开源",
        "event_news_feed": "事件新闻源",
        "open_source_model": "开源模型",
        "local_reference_file": "本地参考文件",
    }.get(str(value or ""), str(value or ""))


def review_type_label(value) -> str:
    return {
        "missing_data": "缺失数据",
        "model_divergence": "模型分歧",
        "decision_reason": "决策理由",
    }.get(str(value or ""), str(value or ""))


def status_label(value) -> str:
    return {
        "ok": "通过",
        "pass": "通过",
        "blocked": "阻塞",
        "watch": "观察",
        "missing": "缺失",
    }.get(str(value or ""), str(value or ""))


def source_status_label(value) -> str:
    return {
        "implemented_proxy": "已进入本地交叉验证",
        "design_reference": "设计参考",
    }.get(str(value or ""), str(value or ""))


def render_artifact_links(artifacts: Dict) -> str:
    labels = {
        "pdf_output_copy": "公开 PDF 副本",
        "bankroll_plan": "公开资金计划 JSON",
        "model_comparison_report": "开源模型对比报告",
        "model_comparison_pdf": "开源模型对比 PDF",
        "manifest": "运行 Manifest",
        "report_database": "本地 SQLite 数据库",
        "report_index": "本地报告索引",
        "report_index_latest": "最新报告索引",
        "report_index_report": "本地报告历史可视化",
        "report_index_report_latest": "最新报告历史可视化",
        "report_index_pdf": "本地报告历史 PDF",
        "report_index_pdf_latest": "最新报告历史 PDF",
        "report_intelligence": "本地研究智能层 JSON",
        "report_intelligence_latest": "最新研究智能层 JSON",
        "report_intelligence_report": "本地研究智能层报告",
        "report_intelligence_report_latest": "最新研究智能层报告",
        "report_intelligence_pdf": "本地研究智能层 PDF",
        "report_intelligence_pdf_latest": "最新研究智能层 PDF",
        "automation_readiness": "自动化就绪审计",
        "automation_readiness_report": "自动化就绪可视化报告",
        "automation_readiness_pdf": "自动化就绪 PDF",
        "automation_candidate": "自动化候选配置",
        "automation_candidate_report": "自动化候选可视化报告",
        "automation_candidate_pdf": "自动化候选 PDF",
    }
    items = []
    for key, label in labels.items():
        path = artifacts.get(key)
        if not path:
            continue
        items.append(f'<li><strong>{esc(label)}</strong><br><a href="{esc(relative_link(path))}">{esc(public_artifact_ref(path))}</a></li>')
    return "<ul>" + "\n".join(items) + "</ul>" if items else '<p class="note">暂无产物链接。</p>'


def render_chart_svg(chart: Dict, width: int = 560) -> str:
    items = chart.get("items", [])
    if not items:
        return f'<p class="note">{esc(chart.get("note") or "暂无数据。")}</p>'
    label_width = 210 if width >= 560 else 170
    bar_width = max(120, width - label_width - 90)
    row_h = 30
    height = max(92, 30 + row_h * len(items) + 24)
    rows = []
    for idx, item in enumerate(items):
        y = 24 + idx * row_h
        fraction = max(0.0, min(1.0, float(item.get("bar_fraction") or 0)))
        fill_width = int(bar_width * fraction)
        color = item.get("color") or "#1F4E79"
        rows.append(f'<text x="0" y="{y + 14}" font-size="11" fill="#172033">{esc(truncate(item.get("label"), 34))}</text>')
        rows.append(f'<rect x="{label_width}" y="{y}" width="{bar_width}" height="17" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="{label_width}" y="{y}" width="{fill_width}" height="17" fill="{esc(color)}" rx="4"></rect>')
        rows.append(f'<text x="{label_width + bar_width + 12}" y="{y + 14}" font-size="12" fill="#5F6B7A">{esc(item.get("display"))}</text>')
    note = chart.get("note")
    if note:
        rows.append(f'<text x="0" y="{height - 6}" font-size="11" fill="#5F6B7A">{esc(truncate(note, 70))}</text>')
    return svg(width, height, rows, chart.get("title") or chart.get("id") or "chart")


def render_recent_runs_svg(runs: List[Dict]) -> str:
    items = list(runs)[:8]
    if not items:
        return '<p class="note">暂无历史运行。</p>'
    values = [
        float(item.get("time_adjusted_new_exposure_aud") or item.get("recommended_new_exposure_aud") or 0)
        for item in items
    ]
    max_value = max(values + [1.0])
    rows = []
    for idx, item in enumerate(items):
        y = 24 + idx * 24
        value = values[idx]
        width = int(230 * value / max_value)
        color = "#247A5A" if item.get("technical_ready") else "#A56710"
        label = f"{item.get('report_date', '')} / {str(item.get('status', ''))[:18]}"
        rows.append(f'<text x="0" y="{y + 13}" font-size="11" fill="#172033">{esc(truncate(label, 30))}</text>')
        rows.append(f'<rect x="190" y="{y}" width="230" height="15" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="190" y="{y}" width="{width}" height="15" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="432" y="{y + 12}" font-size="11" fill="#5F6B7A">AUD {value:,.0f}</text>')
    rows.append('<text x="0" y="12" font-size="12" fill="#5F6B7A">报告历史索引：绿色=技术通过，琥珀=未通过/阻塞</text>')
    return svg(530, max(80, 36 + 24 * len(items)), rows, "报告历史索引")


def render_automation_runs_svg(runs: List[Dict]) -> str:
    items = list(runs)[:8]
    if not items:
        return '<p class="note">暂无 automation runner 历史。</p>'
    rows = ['<text x="0" y="12" font-size="12" fill="#5F6B7A">自动化运行：绿色=可发布，琥珀=门禁未发布，红色=runner失败</text>']
    for idx, item in enumerate(items):
        y = 24 + idx * 24
        if int(item.get("exit_code") or 0) != 0:
            color = "#C62828"
            width = 90
        elif item.get("formal_report_publish_ready"):
            color = "#247A5A"
            width = 230
        else:
            color = "#A56710"
            width = 150
        label = f"{automation_mode_label(item)} / {item.get('status', '')}"
        rows.append(f'<text x="0" y="{y + 13}" font-size="11" fill="#172033">{esc(truncate(label, 30))}</text>')
        rows.append(f'<rect x="190" y="{y}" width="230" height="15" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="190" y="{y}" width="{width}" height="15" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="432" y="{y + 12}" font-size="11" fill="#5F6B7A">{esc(publish_label(item))}</text>')
    return svg(530, max(80, 36 + 24 * len(items)), rows, "自动化运行历史")


def publish_label(item: Dict) -> str:
    if int(item.get("exit_code") or 0) != 0:
        return "runner失败"
    return "可发布" if item.get("formal_report_publish_ready") else "不发布"


def automation_mode_label(item: Dict) -> str:
    mode = str(item.get("mode") or "")
    verify_mode = str(item.get("verify_mode") or "")
    return f"{mode} / {verify_mode}" if mode == "verify-only" and verify_mode else mode


def render_board_readiness_svg(statuses: List[Dict]) -> str:
    width = 620
    row_h = 28
    height = max(80, 24 + row_h * len(statuses))
    rows = []
    for idx, board in enumerate(statuses):
        y = 24 + idx * row_h
        score = readiness_score(board)
        bar = int(score * 260)
        color = "#247A5A" if board.get("ready") else "#A56710"
        rows.append(f'<text x="0" y="{y + 15}" font-size="12" fill="#172033">{esc(short_board_name(board.get("name")))}</text>')
        rows.append(f'<rect x="210" y="{y}" width="260" height="16" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="210" y="{y}" width="{bar}" height="16" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="485" y="{y + 13}" font-size="12" fill="#5F6B7A">{int(score * 100)}%</text>')
    return svg(width, height, rows, "板块就绪度")


def render_compare_svg(summary: Dict) -> str:
    data = [
        ("新增", int(summary.get("added_count") or 0), "#247A5A"),
        ("移除", int(summary.get("removed_count") or 0), "#C62828"),
        ("变化", int(summary.get("changed_count") or 0), "#A56710"),
        ("保留", int(summary.get("retained_count") or 0), "#1F4E79"),
    ]
    max_value = max([item[1] for item in data] + [1])
    rows = []
    for idx, (label, value, color) in enumerate(data):
        y = 22 + idx * 30
        width = int(300 * value / max_value)
        rows.append(f'<text x="0" y="{y + 14}" font-size="12" fill="#172033">{label}</text>')
        rows.append(f'<rect x="52" y="{y}" width="300" height="17" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="52" y="{y}" width="{width}" height="17" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="365" y="{y + 14}" font-size="12" fill="#5F6B7A">{value}</text>')
    exposure = float(summary.get("exposure_change_aud") or 0)
    rows.append(f'<text x="0" y="152" font-size="12" fill="#5F6B7A">暴露变化 AUD {exposure:,.0f}</text>')
    return svg(430, 170, rows, "新旧报告对比")


def render_board_recommendation_svg(counts: List[Dict]) -> str:
    max_count = max([item.get("count", 0) for item in counts] + [1])
    rows = []
    for idx, item in enumerate(counts):
        y = 22 + idx * 30
        width = int(280 * item.get("count", 0) / max_count)
        color = "#C62828" if item.get("stake_aud", 0) > 0 else "#1F4E79"
        rows.append(f'<text x="0" y="{y + 14}" font-size="12" fill="#172033">{esc(item.get("name"))}</text>')
        rows.append(f'<rect x="170" y="{y}" width="280" height="17" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="170" y="{y}" width="{width}" height="17" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="462" y="{y + 14}" font-size="12" fill="#5F6B7A">{item.get("count", 0)}个</text>')
    return svg(530, max(90, 34 + 30 * len(counts)), rows, "各板块推荐数量")


def render_ev_svg(items: List[Dict]) -> str:
    if not items:
        return '<p class="note">暂无比赛推荐。</p>'
    evs = [max(0.0, float(item.get("expected_value") or 0)) for item in items]
    max_ev = max(evs + [0.01])
    rows = []
    for idx, item in enumerate(items):
        y = 22 + idx * 30
        width = int(260 * max(0.0, float(item.get("expected_value") or 0)) / max_ev)
        stake = float(item.get("stake_aud") or 0)
        color = "#C62828" if stake > 0 else "#A56710"
        label = f"{item.get('match','')} / {item.get('selection','')}"
        rows.append(f'<text x="0" y="{y + 14}" font-size="11" fill="#172033">{esc(truncate(label, 34))}</text>')
        rows.append(f'<rect x="230" y="{y}" width="260" height="17" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="230" y="{y}" width="{width}" height="17" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="502" y="{y + 14}" font-size="12" fill="#5F6B7A">{fmt_pct(item.get("expected_value"))}</text>')
    return svg(590, max(90, 34 + 30 * len(items)), rows, "比赛盘口 EV 排序")


def render_model_divergence_svg(items: List[Dict]) -> str:
    if not items:
        return '<p class="note">暂无模型对比数据。</p>'
    values = [float(item.get("disagreement", {}).get("max_abs_current_vs_elo_dc") or 0) for item in items]
    max_value = max(values + [0.01])
    rows = []
    for idx, item in enumerate(items):
        y = 22 + idx * 30
        disagreement = float(item.get("disagreement", {}).get("max_abs_current_vs_elo_dc") or 0)
        width = int(260 * disagreement / max_value)
        color = "#C62828" if item.get("disagreement", {}).get("high_divergence") else "#1F4E79"
        label = f"{item.get('match','')} / {item.get('consensus', {}).get('selection','')}"
        rows.append(f'<text x="0" y="{y + 14}" font-size="11" fill="#172033">{esc(truncate(label, 34))}</text>')
        rows.append(f'<rect x="230" y="{y}" width="260" height="17" fill="#EEF2F6" rx="4"></rect>')
        rows.append(f'<rect x="230" y="{y}" width="{width}" height="17" fill="{color}" rx="4"></rect>')
        rows.append(f'<text x="502" y="{y + 14}" font-size="12" fill="#5F6B7A">{fmt_pct(disagreement)}</text>')
    return svg(590, max(90, 34 + 30 * len(items)), rows, "开源模型分歧")


def readiness_score(board: Dict) -> float:
    checks = [board.get("raw_fresh"), board.get("raw_valid"), board.get("gate_ready"), board.get("report_exists")]
    return sum(1 for item in checks if item) / len(checks)


def svg(width: int, height: int, children: List[str], title: str) -> str:
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{"".join(children)}</svg>'


def short_board_name(value) -> str:
    return str(value or "").replace("2026 World Cup ", "")


def format_compare_value(summary: Dict) -> str:
    return f"+{int(summary.get('added_count') or 0)} / 改{int(summary.get('changed_count') or 0)}"


def relative_link(path: str) -> str:
    value = str(path or "")
    return Path(value).name if value else ""


def public_artifact_ref(path) -> str:
    value = str(path or "")
    return Path(value).name if value else ""


def truncate(value, length: int) -> str:
    text = str(value or "")
    return text if len(text) <= length else text[: length - 1] + "…"


def fmt_pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "待同步"


def fmt_num(value, decimals: int) -> str:
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "待同步"


def fmt_odds(value) -> str:
    odds = parse_decimal_odds(value)
    return f"{odds:.2f}" if odds is not None else "待同步"


def md(value) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)
