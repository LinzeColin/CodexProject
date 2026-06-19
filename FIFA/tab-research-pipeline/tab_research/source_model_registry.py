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
from .model_compare import MODEL_COMPARISON_JSON, OPEN_SOURCE_REFERENCES
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf
from .source_model_metadata import (
    GITHUB_METADATA_FRESHNESS_SLA_HOURS,
    SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST,
    github_metadata_by_source,
    load_source_model_github_metadata,
)


SOURCE_MODEL_REGISTRY_JSON_LATEST = "source_model_registry_latest.json"
SOURCE_MODEL_REGISTRY_MD_LATEST = "source_model_registry_latest.md"
SOURCE_MODEL_REGISTRY_PDF_LATEST = "source_model_registry_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


NEXT_CONVERSION_TASKS = {
    "Hicruben/world-cup-2026-prediction-model": "把 live track record、reliability curve、bracket simulator 和 open data widgets 转成日报可回测组件。",
    "opisthokonta/goalmodel": "把 xG -> 1X2 / OU / BTTS / score_predictions 做成统一市场概率校准层，并输出偏差审计。",
    "RyanSCodes/Dixon-Coles-Football-Predictor": "只保留时间衰减和攻防参数思想；因无明确 license 与 Python 2.7 legacy，不复制实现代码。",
    "martineastwood/penaltyblog": "把 no-vig、Asian handicap、大小球、Bayesian uncertainty 和 ratings 口径映射到本地盘口概率/风险解释层。",
    "ML-KULeuven/socceraction": "等待可用事件流数据后，把 xT/VAEP/action value 转成球员基本面、伤停影响和战术状态解释层。",
    "openfootball/worldcup.json": "把 2026 World Cup public JSON 接入 fixture sanity-check 与 SQLite seed，只校验赛程不替代 TAB 盘口。",
}


UI_BLUEPRINTS = [
    {
        "component_id": "recommendation_command_center",
        "component_title": "推荐下注指挥台",
        "source_refs": [
            "Hicruben/world-cup-2026-prediction-model",
            "martineastwood/penaltyblog",
            "opisthokonta/goalmodel",
        ],
        "borrowed_patterns": [
            "Track record / reliability style cards",
            "No-vig、EV、Edge、Risk controls side-by-side",
            "Poisson/xG model comparison badge",
        ],
        "local_ui_contract": "首页首屏用一张推荐表和操作卡片展示时间、板块、盘口、下注、赔率、金额、EV、Edge、套利率、Risk of ruin、置信度和门禁动作。",
        "business_value": "让用户先看到该怎么下注和为什么，而不是先阅读技术报告。",
        "implementation_status": "implemented",
        "next_step": "接入真实结算和收盘赔率后，把 CLV/ROI 反馈直接回写到推荐卡片的 Edge 阈值。",
    },
    {
        "component_id": "model_divergence_review_queue",
        "component_title": "模型分歧复核队列",
        "source_refs": [
            "RyanSCodes/Dixon-Coles-Football-Predictor",
            "opisthokonta/goalmodel",
            "Hicruben/world-cup-2026-prediction-model",
        ],
        "borrowed_patterns": [
            "Dixon-Coles time decay disagreement",
            "score matrix / 1X2 / OU probability comparison",
            "Monte Carlo scenario confidence",
        ],
        "local_ui_contract": "开源模型 Dashboard 以比赛为行展示共识注、置信度、最大分歧和高分歧标记，并进入人工复核，不解锁下注。",
        "business_value": "把模型不一致的盘口提前暴露，避免只按单一概率模型下注。",
        "implementation_status": "implemented",
        "next_step": "把高分歧队列接入主动测试和周报复盘，统计哪些分歧类型最容易造成误判。",
    },
    {
        "component_id": "fixture_sanity_and_bracket_path",
        "component_title": "赛程校验与路径模拟",
        "source_refs": [
            "openfootball/worldcup.json",
            "Hicruben/world-cup-2026-prediction-model",
        ],
        "borrowed_patterns": [
            "World Cup public fixture JSON sanity-check",
            "48-team bracket / path simulator",
            "stage-aware report sections",
        ],
        "local_ui_contract": "赛程校验 Dashboard 区分 TAB-only、openfootball-only、matched fixtures，并在报告里标注 public source delayed，不替代 live odds。",
        "business_value": "防止比赛、阶段、开球时间或板块映射错误进入下注研究。",
        "implementation_status": "partial",
        "next_step": "等 FIFA/TAB 完整分组与淘汰赛路径稳定后，把 bracket path 概率写入分阶段报告。",
    },
    {
        "component_id": "odds_calibration_lab",
        "component_title": "赔率校准实验室",
        "source_refs": [
            "martineastwood/penaltyblog",
            "opisthokonta/goalmodel",
        ],
        "borrowed_patterns": [
            "Overround removal / no-vig implied probability",
            "Asian handicap and over/under market interface",
            "Bayesian uncertainty / ratings context",
        ],
        "local_ui_contract": "推荐操作报告和首页统一展示盈亏平衡概率、模型概率、EV、Edge 门槛差、半 Kelly 与 Risk of ruin。",
        "business_value": "把赔率价值、盘口风险和资金纪律放在同一决策面板，减少只看赔率高低的误判。",
        "implementation_status": "implemented",
        "next_step": "加入同盘口历史 CLV bucket，自动调整主流/小市场 Edge 门槛。",
    },
    {
        "component_id": "fundamental_context_layer",
        "component_title": "基本面解释层",
        "source_refs": [
            "ML-KULeuven/socceraction",
            "opisthokonta/goalmodel",
        ],
        "borrowed_patterns": [
            "xT / VAEP action value",
            "xG distribution as market probability driver",
            "player and tactical state explanation",
        ],
        "local_ui_contract": "在盘口原因中预留球员状态、伤停、战术节奏、xG/xT/VAEP 解释位；无事件流数据时只标为 data_required。",
        "business_value": "让概率不是黑箱数字，能解释为什么某个盘口比 TAB 隐含概率更有价值。",
        "implementation_status": "data_required",
        "next_step": "接入合法事件流或公开统计源后，补齐球员/战术基本面评分和伤停影响。",
    },
    {
        "component_id": "evidence_and_license_audit",
        "component_title": "证据与许可审计面板",
        "source_refs": [
            "Hicruben/world-cup-2026-prediction-model",
            "opisthokonta/goalmodel",
            "RyanSCodes/Dixon-Coles-Football-Predictor",
            "martineastwood/penaltyblog",
            "ML-KULeuven/socceraction",
            "openfootball/worldcup.json",
        ],
        "borrowed_patterns": [
            "Source registry table",
            "GitHub API metadata freshness",
            "License risk gate",
        ],
        "local_ui_contract": "开源模型库 Dashboard 展示 license 风险、GitHub stars/open issues/pushed_at、FACT/INFERENCE 证据层和下一步转换任务。",
        "business_value": "保证借鉴来源透明，避免把高许可风险或旧运行时项目误当成可直接复用代码。",
        "implementation_status": "implemented",
        "next_step": "把高许可风险项目默认留在 design_reference，除非人工确认许可和实现替代方案。",
    },
]


UI_BLUEPRINT_DASHBOARD_SURFACES = {
    "recommendation_command_center": "首页推荐下注板块；Recommendation Operations PDF/JSON/Markdown",
    "model_divergence_review_queue": "模型分歧复核 Dashboard；开源模型对比 PDF/JSON/Markdown",
    "fixture_sanity_and_bracket_path": "赛程校验 Dashboard；分阶段路径位以 public fixture gate 展示",
    "odds_calibration_lab": "推荐操作 Dashboard；概率/赔率编辑即时重算面板",
    "fundamental_context_layer": "推荐理由中的基本面解释位；缺事件流时显示 data gate 和复核清单",
    "evidence_and_license_audit": "开源模型库 Dashboard；证据层、GitHub freshness、license 风险表",
}


UI_BLUEPRINT_DATA_GATES = {
    "recommendation_command_center": "none",
    "model_divergence_review_queue": "none",
    "fixture_sanity_and_bracket_path": "public_fixture_and_bracket_stability_required",
    "odds_calibration_lab": "none",
    "fundamental_context_layer": "legal_event_stream_or_public_team_stats_required",
    "evidence_and_license_audit": "none",
}


def write_source_model_registry_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_source_model_registry(output_dir, db_path)
    json_path = output_dir / SOURCE_MODEL_REGISTRY_JSON_LATEST
    md_path = output_dir / SOURCE_MODEL_REGISTRY_MD_LATEST
    pdf_path = output_dir / SOURCE_MODEL_REGISTRY_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_source_model_registry_markdown(payload))
    pdf_summary = write_source_model_registry_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_source_model_registry(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_source_model_registry(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    model_payload = load_json(output_dir / MODEL_COMPARISON_JSON)
    github_metadata = load_source_model_github_metadata(output_dir)
    live_metadata_by_source = github_metadata_by_source(github_metadata)
    rows = [source_row(ref, live_metadata_by_source.get(str(ref.get("name") or ""))) for ref in OPEN_SOURCE_REFERENCES]
    summary = summarize_rows(rows, model_payload, github_metadata)
    ui_blueprint = build_ui_blueprint(rows)
    summary.update(summarize_ui_blueprint(ui_blueprint))
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "source_model_registry_dashboard",
        "purpose": "把 GitHub / 开源足球模型转成可审计的本地模型库：哪些能力已经吸收、哪些仅作设计参考、哪些存在许可或运行时风险。",
        "executive_status": {
            "status": "ready_with_license_controls"
            if summary["reference_count"] >= 3 and summary["implemented_reference_count"] >= 2
            else "partial",
            "automation_reuse_ready": summary["implemented_reference_count"] >= 2,
            "license_control_required": summary["license_risk_count"] > 0,
            "primary_user_value": "下注建议可展示模型共识、分歧、回测与来源，而不是只看 TAB 隐含概率。",
            "next_conversion_task": next_conversion_task(rows),
        },
        "summary": summary,
        "rows": rows,
        "ui_blueprint": ui_blueprint,
        "github_metadata": {
            "artifact": SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST,
            "status": str(github_metadata.get("status") or "missing"),
            "generated_at": str(github_metadata.get("generated_at") or ""),
            "freshness_sla_hours": GITHUB_METADATA_FRESHNESS_SLA_HOURS,
            "freshness_status": summary.get("live_metadata_freshness_status", "missing"),
            "source_count": int(github_metadata.get("source_count") or 0),
            "fetched_count": int(github_metadata.get("fetched_count") or 0),
            "failed_count": int(github_metadata.get("failed_count") or 0),
        },
        "source_trace": source_trace(rows),
        "old_new_compare": old_new_compare(db_path, rows),
        "truthfulness_note": "本库记录方法和布局借鉴，不声称复制外部代码；无明确许可或 legacy runtime 的项目只能作为设计参考。",
        "safety_note": "该开源模型库只增强研究报告和概率交叉验证，不自动下注、不点击 TAB 赔率、不写入 Bet Slip。",
    }
    return sanitize_public_payload(payload)


def source_row(ref: dict[str, Any], live_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    name = str(ref.get("name") or "")
    adoption = str(ref.get("adoption_status") or "unknown")
    features = [str(item) for item in ref.get("reusable_features") or []]
    patterns = [str(item) for item in ref.get("layout_patterns") or []]
    evidence = [str(item) for item in ref.get("github_evidence") or []]
    license_name = str(ref.get("license") or "Unknown")
    license_risk = classify_license_risk(license_name)
    implemented = adoption == "implemented_proxy"
    feature_score = min(1.0, len(features) / 6)
    pattern_score = min(1.0, len(patterns) / 4)
    implementation_score = 1.0 if implemented else 0.45 if adoption == "design_reference" else 0.25
    risk_penalty = {"low": 0.0, "medium": 0.1, "high": 0.25}.get(license_risk, 0.2)
    score = max(0.0, min(1.0, (implementation_score * 0.5) + (feature_score * 0.25) + (pattern_score * 0.25) - risk_penalty))
    live = live_metadata_summary(live_metadata)
    freshness = live_metadata_freshness_details(live)
    live_evidence = []
    if live.get("fetch_status") == "ready":
        live_evidence.append(
            {
                "layer": "FACT",
                "text": "GitHub API live metadata: stars {stars}, forks {forks}, open issues {issues}, pushed_at {pushed_at}.".format(
                    stars=live.get("stargazers_count", 0),
                    forks=live.get("forks_count", 0),
                    issues=live.get("open_issues_count", 0),
                    pushed_at=live.get("pushed_at", ""),
                ),
                "source_url": str(ref.get("url") or ""),
            }
        )
    return {
        "source": name,
        "display_name": str(ref.get("display_name") or name),
        "url": str(ref.get("url") or ""),
        "license": license_name,
        "license_risk": license_risk,
        "method_family": str(ref.get("method_family") or ""),
        "adoption_status": adoption,
        "registry_status": "已吸收" if implemented else "设计参考",
        "implemented_score": round(score, 4),
        "feature_count": len(features),
        "layout_pattern_count": len(patterns),
        "static_verified_at": str(ref.get("verified_at") or ""),
        "last_verified_at": str(live.get("fetched_at") or ref.get("verified_at") or ""),
        "live_fetch_status": str(live.get("fetch_status") or "missing"),
        "live_metadata_freshness": freshness["status"],
        "live_metadata_age_hours": freshness["age_hours"],
        "live_metadata_sla_hours": GITHUB_METADATA_FRESHNESS_SLA_HOURS,
        "github_stars": int(live.get("stargazers_count") or 0),
        "github_forks": int(live.get("forks_count") or 0),
        "github_open_issues": int(live.get("open_issues_count") or 0),
        "github_pushed_at": str(live.get("pushed_at") or ""),
        "github_updated_at": str(live.get("updated_at") or ""),
        "github_license_live": str(live.get("license_name") or live.get("license_key") or ""),
        "live_metadata": live,
        "coverage": [str(item) for item in ref.get("coverage") or []],
        "reusable_features": features,
        "layout_patterns": patterns,
        "report_usage": str(ref.get("report_usage") or ""),
        "evidence_layers": live_evidence
        + [
            {"layer": "FACT", "text": item, "source_url": str(ref.get("url") or "")}
            for item in evidence[:4]
        ]
        + [
            {
                "layer": "INFERENCE",
                "text": str(ref.get("report_usage") or ""),
                "source_url": "",
            }
        ],
        "next_conversion_task": NEXT_CONVERSION_TASKS.get(name, "把可复用能力转成可测试、可回测、可解释的本地模块。"),
    }


def summarize_rows(rows: list[dict[str, Any]], model_payload: dict[str, Any], github_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    adoption_counts = Counter(str(row.get("adoption_status") or "") for row in rows)
    license_counts = Counter(str(row.get("license_risk") or "") for row in rows)
    implemented = int(adoption_counts.get("implemented_proxy", 0))
    design = int(adoption_counts.get("design_reference", 0))
    model_dashboard = model_payload.get("model_dashboard") or {}
    metadata_payload = github_metadata or {}
    ready_metadata = [row for row in rows if row.get("live_fetch_status") == "ready"]
    fresh_metadata = [row for row in rows if row.get("live_metadata_freshness") == "fresh_4h"]
    stale_metadata = [row for row in rows if row.get("live_metadata_freshness") == "stale"]
    max_age_values = [float(row.get("live_metadata_age_hours") or 0) for row in ready_metadata if row.get("live_metadata_age_hours") is not None]
    freshness_status = (
        "fresh_4h"
        if ready_metadata and len(fresh_metadata) == len(ready_metadata) and int(metadata_payload.get("failed_count") or 0) == 0
        else "stale_or_partial"
        if ready_metadata
        else str(metadata_payload.get("status") or "missing")
    )
    return {
        "reference_count": len(rows),
        "implemented_reference_count": implemented,
        "design_reference_count": design,
        "license_risk_count": int(license_counts.get("medium", 0) + license_counts.get("high", 0)),
        "high_license_risk_count": int(license_counts.get("high", 0)),
        "reusable_feature_count": sum(int(row.get("feature_count") or 0) for row in rows),
        "layout_pattern_count": sum(int(row.get("layout_pattern_count") or 0) for row in rows),
        "average_implemented_score": round(sum(float(row.get("implemented_score") or 0) for row in rows) / len(rows), 4) if rows else 0.0,
        "model_comparison_match_count": int(model_dashboard.get("match_count") or model_payload.get("match_count") or 0),
        "model_comparison_high_divergence_count": int(model_dashboard.get("high_divergence_count") or 0),
        "live_metadata_status": str(metadata_payload.get("status") or "missing"),
        "live_metadata_source_count": int(metadata_payload.get("source_count") or 0),
        "live_metadata_ready_count": len(ready_metadata),
        "live_metadata_failed_count": int(metadata_payload.get("failed_count") or 0),
        "live_metadata_freshness_sla_hours": GITHUB_METADATA_FRESHNESS_SLA_HOURS,
        "live_metadata_freshness_status": freshness_status,
        "live_metadata_fresh_within_sla_count": len(fresh_metadata),
        "live_metadata_stale_count": len(stale_metadata),
        "live_metadata_max_age_hours": round(max(max_age_values), 2) if max_age_values else None,
        "github_stars_total": sum(int(row.get("github_stars") or 0) for row in ready_metadata),
        "github_forks_total": sum(int(row.get("github_forks") or 0) for row in ready_metadata),
        "github_open_issues_total": sum(int(row.get("github_open_issues") or 0) for row in ready_metadata),
        "latest_github_pushed_at": latest_non_empty([str(row.get("github_pushed_at") or "") for row in ready_metadata]),
        "adoption_counts": dict(adoption_counts),
        "license_risk_counts": dict(license_counts),
    }


def build_ui_blueprint(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_source = {str(row.get("source") or ""): row for row in rows}
    blueprint_rows: list[dict[str, Any]] = []
    for item in UI_BLUEPRINTS:
        source_refs = [str(source) for source in item.get("source_refs") or []]
        implemented_sources = [
            source
            for source in source_refs
            if (rows_by_source.get(source) or {}).get("adoption_status") == "implemented_proxy"
        ]
        license_risks = sorted({str((rows_by_source.get(source) or {}).get("license_risk") or "unknown") for source in source_refs})
        coverage_status = ui_dashboard_coverage_status(str(item["implementation_status"]))
        component_id = str(item["component_id"])
        blueprint_rows.append(
            {
                "component_id": component_id,
                "component_title": item["component_title"],
                "source_refs": source_refs,
                "implemented_source_count": len(implemented_sources),
                "source_count": len(source_refs),
                "borrowed_patterns": [str(pattern) for pattern in item.get("borrowed_patterns") or []],
                "local_ui_contract": item["local_ui_contract"],
                "business_value": item["business_value"],
                "implementation_status": item["implementation_status"],
                "dashboard_coverage_status": coverage_status,
                "dashboard_coverage_ready": coverage_status in {"covered_live", "covered_gated"},
                "dashboard_surface": UI_BLUEPRINT_DASHBOARD_SURFACES.get(component_id, "开源模型库 Dashboard"),
                "data_gate": UI_BLUEPRINT_DATA_GATES.get(component_id, "unknown"),
                "license_risks": license_risks,
                "next_step": item["next_step"],
                "evidence_layer": "INFERENCE",
            }
        )
    return blueprint_rows


def ui_dashboard_coverage_status(implementation_status: str) -> str:
    if implementation_status == "implemented":
        return "covered_live"
    if implementation_status in {"partial", "data_required"}:
        return "covered_gated"
    return "planned"


def summarize_ui_blueprint(ui_blueprint: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(item.get("implementation_status") or "") for item in ui_blueprint)
    coverage_counts = Counter(str(item.get("dashboard_coverage_status") or "") for item in ui_blueprint)
    covered_count = sum(1 for item in ui_blueprint if item.get("dashboard_coverage_ready"))
    gated_count = int(coverage_counts.get("covered_gated", 0))
    return {
        "ui_blueprint_count": len(ui_blueprint),
        "ui_blueprint_implemented_count": int(status_counts.get("implemented", 0)),
        "ui_blueprint_partial_count": int(status_counts.get("partial", 0)),
        "ui_blueprint_data_required_count": int(status_counts.get("data_required", 0)),
        "ui_blueprint_status_counts": dict(status_counts),
        "ui_blueprint_dashboard_covered_count": covered_count,
        "ui_blueprint_dashboard_gated_count": gated_count,
        "ui_blueprint_dashboard_coverage_ratio": round(covered_count / len(ui_blueprint), 4) if ui_blueprint else 0.0,
        "ui_blueprint_dashboard_coverage_counts": dict(coverage_counts),
        "ui_blueprint_layout_ready": bool(ui_blueprint) and covered_count == len(ui_blueprint),
    }


def source_trace(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_count": len(rows),
        "sources": [
            {
                "name": row.get("source"),
                "url": row.get("url"),
                "license": row.get("license"),
                "license_risk": row.get("license_risk"),
                "adoption_status": row.get("adoption_status"),
                "live_fetch_status": row.get("live_fetch_status"),
                "last_verified_at": row.get("last_verified_at"),
            }
            for row in rows
        ],
        "evidence_policy": "FACT 行来自公开 GitHub/README/DESCRIPTION 证据和 GitHub API 元数据；INFERENCE 行是本地报告系统对可复用能力的转化判断。",
    }


def render_source_model_registry_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 开源模型库 Dashboard",
        "",
        "本报告把 GitHub / 开源足球模型整理成可复用能力、Dashboard 布局、许可风险和下一步转换任务。它只服务研究分析，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- automation_reuse_ready: `{yes_no(executive.get('automation_reuse_ready'))}`",
        f"- reference_count: `{summary.get('reference_count', 0)}`",
        f"- implemented / design: `{summary.get('implemented_reference_count', 0)} / {summary.get('design_reference_count', 0)}`",
        f"- license_risk_count: `{summary.get('license_risk_count', 0)}`",
        f"- reusable_feature_count: `{summary.get('reusable_feature_count', 0)}`",
        f"- layout_pattern_count: `{summary.get('layout_pattern_count', 0)}`",
        f"- ui_blueprint: `{summary.get('ui_blueprint_implemented_count', 0)}/{summary.get('ui_blueprint_count', 0)}` implemented，partial `{summary.get('ui_blueprint_partial_count', 0)}`，data_required `{summary.get('ui_blueprint_data_required_count', 0)}`",
        f"- UI界面覆盖 / ui_dashboard_coverage: `{summary.get('ui_blueprint_dashboard_covered_count', 0)}/{summary.get('ui_blueprint_count', 0)}`，gated `{summary.get('ui_blueprint_dashboard_gated_count', 0)}`，layout_ready `{yes_no(summary.get('ui_blueprint_layout_ready'))}`",
        f"- live_metadata: `{summary.get('live_metadata_status', 'missing')}`，ready `{summary.get('live_metadata_ready_count', 0)}/{summary.get('reference_count', 0)}`，stars `{summary.get('github_stars_total', 0)}`，open issues `{summary.get('github_open_issues_total', 0)}`",
        f"- freshness_sla: `{summary.get('live_metadata_freshness_sla_hours', GITHUB_METADATA_FRESHNESS_SLA_HOURS)}h`，status `{summary.get('live_metadata_freshness_status', 'missing')}`，fresh `{summary.get('live_metadata_fresh_within_sla_count', 0)}`，stale `{summary.get('live_metadata_stale_count', 0)}`，max_age `{summary.get('live_metadata_max_age_hours', '')}`h",
        f"- next_conversion_task: {md(executive.get('next_conversion_task'))}",
        "",
        "## 新旧模型库变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- implemented_delta: `{compare.get('implemented_delta', 0)}`",
        f"- license_risk_delta: `{compare.get('license_risk_delta', 0)}`",
        "",
        "## Source Registry",
        "",
        "| 来源 | License风险 | 采用状态 | 得分 | 可复用功能 | Dashboard布局 | 当前用途 | 下一步 |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            "| {source} | {risk} | {status} | {score} | {features} | {patterns} | {usage} | {next_task} |".format(
                source=md(row.get("source")),
                risk=md(row.get("license_risk")),
                status=md(row.get("registry_status")),
                score=pct(row.get("implemented_score")),
                features=md("; ".join((row.get("reusable_features") or [])[:3])),
                patterns=md("; ".join((row.get("layout_patterns") or [])[:3])),
                usage=md(row.get("report_usage")),
                next_task=md(row.get("next_conversion_task")),
            )
        )
    lines.extend(
        [
            "",
            "## UI / Dashboard Blueprint",
            "",
            "| 组件 | 来源 | 借鉴模式 | 本地UI合同 | 用户价值 | 实现状态 | 界面覆盖 | 可用界面 | 数据门禁 | 下一步 |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in payload.get("ui_blueprint") or []:
        lines.append(
            "| {title} | {sources} | {patterns} | {contract} | {value} | {status} | {coverage} | {surface} | {data_gate} | {next_step} |".format(
                title=md(item.get("component_title")),
                sources=md("; ".join(item.get("source_refs") or [])),
                patterns=md("; ".join((item.get("borrowed_patterns") or [])[:3])),
                contract=md(item.get("local_ui_contract")),
                value=md(item.get("business_value")),
                status=md(item.get("implementation_status")),
                coverage=md(item.get("dashboard_coverage_status")),
                surface=md(item.get("dashboard_surface")),
                data_gate=md(item.get("data_gate")),
                next_step=md(item.get("next_step")),
            )
        )
    lines.extend(
        [
            "",
            "## Live GitHub Metadata",
            "",
            "| 来源 | Fetch | Freshness | Age h | Stars | Forks | Open issues | Pushed at | Live license |",
            "|---|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload.get("rows") or []:
        lines.append(
            "| {source} | {status} | {freshness} | {age} | {stars} | {forks} | {issues} | {pushed_at} | {license_live} |".format(
                source=md(row.get("source")),
                status=md(row.get("live_fetch_status")),
                freshness=md(row.get("live_metadata_freshness")),
                age=md(row.get("live_metadata_age_hours")),
                stars=int(row.get("github_stars") or 0),
                forks=int(row.get("github_forks") or 0),
                issues=int(row.get("github_open_issues") or 0),
                pushed_at=md(row.get("github_pushed_at")),
                license_live=md(row.get("github_license_live")),
            )
        )
    lines.extend(
        [
            "",
            "## 证据层",
            "",
            "| 来源 | Evidence layer | 内容 |",
            "|---|---|---|",
        ]
    )
    for row in payload.get("rows") or []:
        for item in row.get("evidence_layers") or []:
            lines.append(f"| {md(row.get('source'))} | {md(item.get('layer'))} | {md(item.get('text'))} |")
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('safety_note', '')}"])
    return "\n".join(lines)


def write_source_model_registry_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("rows") or []
    compare = payload.get("old_new_compare") or {}
    adoption_counts = summary.get("adoption_counts") or {}
    license_counts = summary.get("license_risk_counts") or {}
    blueprint_rows = payload.get("ui_blueprint") or []
    blueprint_counts = summary.get("ui_blueprint_status_counts") or {}
    blueprint_coverage_counts = summary.get("ui_blueprint_dashboard_coverage_counts") or {}
    charts = [
        chart_from_items("模型源得分", [(row.get("display_name", ""), float(row.get("implemented_score") or 0) * 100) for row in rows], "#1F4E79"),
        chart_from_items("采用状态", [(key, value) for key, value in adoption_counts.items()], "#247A5A"),
        chart_from_items("License 风险", [(key, value) for key, value in license_counts.items()], "#A56710"),
        chart_from_items("可复用功能数", [(row.get("display_name", ""), float(row.get("feature_count") or 0)) for row in rows], "#6A4C93"),
        chart_from_items("Dashboard布局数", [(row.get("display_name", ""), float(row.get("layout_pattern_count") or 0)) for row in rows], "#C7352B"),
        chart_from_items("GitHub stars", [(row.get("display_name", ""), float(row.get("github_stars") or 0)) for row in rows], "#2A7A5E"),
        chart_from_items("UI蓝图状态", [(key, value) for key, value in blueprint_counts.items()], "#4B6B8A"),
        chart_from_items("UI界面覆盖", [(key, value) for key, value in blueprint_coverage_counts.items()], "#006D77"),
        chart_from_items("GitHub freshness age h", [(row.get("display_name", ""), float(row.get("live_metadata_age_hours") or 0)) for row in rows if row.get("live_fetch_status") == "ready"], "#8B1E3F"),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 开源模型库 Dashboard",
        subtitle="GitHub 模型源、许可风险、功能吸收、布局借鉴和下一步转换任务；只用于研究分析，不自动下注。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("automation_reuse_ready", yes_no(executive.get("automation_reuse_ready"))),
            ("references", str(summary.get("reference_count", 0))),
            ("implemented/design", f"{summary.get('implemented_reference_count', 0)}/{summary.get('design_reference_count', 0)}"),
            ("license risk", str(summary.get("license_risk_count", 0))),
            ("features/layouts", f"{summary.get('reusable_feature_count', 0)}/{summary.get('layout_pattern_count', 0)}"),
            ("UI blueprint", f"{summary.get('ui_blueprint_implemented_count', 0)}/{summary.get('ui_blueprint_count', 0)} implemented"),
            ("UI dashboard coverage", f"{summary.get('ui_blueprint_dashboard_covered_count', 0)}/{summary.get('ui_blueprint_count', 0)} covered"),
            ("live metadata", f"{summary.get('live_metadata_status', 'missing')} {summary.get('live_metadata_ready_count', 0)}/{summary.get('reference_count', 0)}"),
            ("freshness SLA", f"{summary.get('live_metadata_freshness_status', 'missing')} <= {summary.get('live_metadata_freshness_sla_hours', GITHUB_METADATA_FRESHNESS_SLA_HOURS)}h"),
            ("fresh/stale", f"{summary.get('live_metadata_fresh_within_sla_count', 0)}/{summary.get('live_metadata_stale_count', 0)}"),
            ("GitHub stars/open issues", f"{summary.get('github_stars_total', 0)}/{summary.get('github_open_issues_total', 0)}"),
            ("old-new", str(compare.get("status", ""))),
        ],
        charts=charts,
        table_headers=["来源", "License", "风险", "采用", "得分", "Stars", "下一步"],
        table_rows=[
            [
                str(row.get("display_name", "")),
                str(row.get("license", "")),
                str(row.get("license_risk", "")),
                str(row.get("registry_status", "")),
                pct(row.get("implemented_score")),
                str(row.get("github_stars", 0)),
                str(row.get("next_conversion_task", "")),
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "Live GitHub Metadata",
                "headers": ["来源", "Fetch", "Freshness", "Age h", "Stars", "Forks", "Open issues", "Pushed at", "Live license"],
                "rows": [
                    [
                        str(row.get("display_name", "")),
                        str(row.get("live_fetch_status", "")),
                        str(row.get("live_metadata_freshness", "")),
                        str(row.get("live_metadata_age_hours", "")),
                        str(row.get("github_stars", 0)),
                        str(row.get("github_forks", 0)),
                        str(row.get("github_open_issues", 0)),
                        str(row.get("github_pushed_at", "")),
                        str(row.get("github_license_live", "")),
                    ]
                    for row in rows
                ],
            },
            {
                "title": "可复用功能",
                "headers": ["来源", "功能"],
                "rows": [[str(row.get("display_name", "")), "; ".join((row.get("reusable_features") or [])[:4])] for row in rows],
            },
            {
                "title": "Dashboard布局模式",
                "headers": ["来源", "布局模式"],
                "rows": [[str(row.get("display_name", "")), "; ".join((row.get("layout_patterns") or [])[:4])] for row in rows],
            },
            {
                "title": "UI / Dashboard Blueprint",
                "headers": ["组件", "状态", "界面覆盖", "可用界面", "数据门禁", "下一步"],
                "rows": [
                    [
                        str(item.get("component_title", "")),
                        str(item.get("implementation_status", "")),
                        str(item.get("dashboard_coverage_status", "")),
                        str(item.get("dashboard_surface", "")),
                        str(item.get("data_gate", "")),
                        str(item.get("next_step", "")),
                    ]
                    for item in blueprint_rows
                ],
            },
            {
                "title": "新旧模型库变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["implemented_delta", str(compare.get("implemented_delta", 0))],
                    ["license_risk_delta", str(compare.get("license_risk_delta", 0))],
                    ["new_sources", ", ".join(compare.get("new_sources") or [])],
                    ["removed_sources", ", ".join(compare.get("removed_sources") or [])],
                ],
            },
        ],
    )


def persist_source_model_registry(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS source_model_registry_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    reference_count INTEGER NOT NULL DEFAULT 0,
                    implemented_reference_count INTEGER NOT NULL DEFAULT 0,
                    design_reference_count INTEGER NOT NULL DEFAULT 0,
                    license_risk_count INTEGER NOT NULL DEFAULT 0,
                    reusable_feature_count INTEGER NOT NULL DEFAULT 0,
                    layout_pattern_count INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO source_model_registry_snapshots(
                    snapshot_id, generated_at, status, reference_count,
                    implemented_reference_count, design_reference_count, license_risk_count,
                    reusable_feature_count, layout_pattern_count, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_payload.get("snapshot_id", ""),
                    public_payload.get("generated_at", ""),
                    str(executive.get("status") or ""),
                    int(summary.get("reference_count") or 0),
                    int(summary.get("implemented_reference_count") or 0),
                    int(summary.get("design_reference_count") or 0),
                    int(summary.get("license_risk_count") or 0),
                    int(summary.get("reusable_feature_count") or 0),
                    int(summary.get("layout_pattern_count") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "source_model_registry_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def old_new_compare(db_path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "implemented_delta": 0, "license_risk_delta": 0}
    try:
        with connect_report_db(db_path) as conn:
            row = conn.execute(
                """
                SELECT generated_at, implemented_reference_count, license_risk_count, payload_json
                FROM source_model_registry_snapshots
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except sqlite3.Error:
        return {"status": "compare_unavailable", "implemented_delta": 0, "license_risk_delta": 0}
    if not row:
        return {"status": "no_previous_snapshot", "implemented_delta": 0, "license_risk_delta": 0}
    previous_payload = safe_json(row["payload_json"])
    previous_sources = {str(item.get("source") or "") for item in previous_payload.get("rows", []) if isinstance(item, dict)}
    current_sources = {str(item.get("source") or "") for item in rows}
    current_implemented = sum(1 for item in rows if item.get("adoption_status") == "implemented_proxy")
    current_license_risk = sum(1 for item in rows if item.get("license_risk") in {"medium", "high"})
    return {
        "status": "compared",
        "previous_generated_at": row["generated_at"],
        "implemented_delta": int(current_implemented - int(row["implemented_reference_count"] or 0)),
        "license_risk_delta": int(current_license_risk - int(row["license_risk_count"] or 0)),
        "new_sources": sorted(current_sources - previous_sources),
        "removed_sources": sorted(previous_sources - current_sources),
    }


def next_conversion_task(rows: list[dict[str, Any]]) -> str:
    high_risk = [row for row in rows if row.get("license_risk") == "high"]
    if high_risk:
        return str(high_risk[0].get("next_conversion_task") or "")
    for row in rows:
        if row.get("adoption_status") == "implemented_proxy":
            return str(row.get("next_conversion_task") or "")
    return "先完成 GitHub 源审计，再进入模型转换。"


def classify_license_risk(license_name: str) -> str:
    value = license_name.lower()
    if "no release" in value or "unknown" in value or "not declared" in value:
        return "high"
    if "gpl" in value:
        return "medium"
    return "low"


def live_metadata_summary(live_metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(live_metadata, dict) or not live_metadata:
        return {"fetch_status": "missing"}
    keys = {
        "fetch_status",
        "fetched_at",
        "stargazers_count",
        "forks_count",
        "open_issues_count",
        "watchers_count",
        "default_branch",
        "pushed_at",
        "updated_at",
        "archived",
        "disabled",
        "visibility",
        "license_key",
        "license_name",
        "language",
        "homepage",
        "html_url",
        "error_type",
        "error_message",
    }
    return {key: live_metadata.get(key) for key in keys if key in live_metadata}


def live_metadata_freshness(live: dict[str, Any]) -> str:
    return live_metadata_freshness_details(live)["status"]


def live_metadata_freshness_details(live: dict[str, Any]) -> dict[str, Any]:
    if live.get("fetch_status") != "ready":
        return {"status": str(live.get("fetch_status") or "missing"), "age_hours": None}
    fetched_at = str(live.get("fetched_at") or "")
    fetched_dt = parse_iso_datetime(fetched_at)
    if fetched_dt is None:
        return {"status": "cached", "age_hours": None}
    age_seconds = max(0.0, (datetime.now(REPORT_TZ) - fetched_dt.astimezone(REPORT_TZ)).total_seconds())
    age_hours = round(age_seconds / 3600, 2)
    status = "fresh_4h" if age_hours <= GITHUB_METADATA_FRESHNESS_SLA_HOURS else "stale"
    return {"status": status, "age_hours": age_hours}


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def latest_non_empty(values: list[str]) -> str:
    items = sorted(value for value in values if value)
    return items[-1] if items else ""


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not Path(path).exists():
            return {}
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def safe_json(value: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def snapshot_id(generated_at: str) -> str:
    return "source-model-registry-" + generated_at.replace(":", "").replace("+", "-").replace(".", "-")


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def yes_no(value: Any) -> str:
    return "是" if bool(value) else "否"


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
