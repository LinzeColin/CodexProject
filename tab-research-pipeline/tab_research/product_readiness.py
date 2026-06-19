from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .raw_refresh import normalize_partial_research_refresh
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


PRODUCT_READINESS_JSON_LATEST = "product_readiness_dashboard_latest.json"
PRODUCT_READINESS_MD_LATEST = "product_readiness_dashboard_latest.md"
PRODUCT_READINESS_PDF_LATEST = "product_readiness_dashboard_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_product_readiness_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_product_readiness(output_dir, db_path)
    json_path = output_dir / PRODUCT_READINESS_JSON_LATEST
    md_path = output_dir / PRODUCT_READINESS_MD_LATEST
    pdf_path = output_dir / PRODUCT_READINESS_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_product_readiness_markdown(payload))
    pdf_summary = write_product_readiness_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_product_readiness(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_product_readiness(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    evidence = {
        "goal": load_json(output_dir / "goal_traceability_latest.json"),
        "visual": load_json(output_dir / "report_visual_inventory_latest.json"),
        "model": load_json(output_dir / "tab_fifa_model_comparison_v0_1.json"),
        "source_registry": load_json(output_dir / "source_model_registry_latest.json"),
        "timeline": load_json(output_dir / "active_timeline_report_latest.json")
        or load_json(output_dir / "active_timeline_latest.json"),
        "available": load_json(output_dir / "available_board_strategy_latest.json"),
        "live": load_json(output_dir / "live_board_discovery_latest.json"),
        "fixture": load_json(output_dir / "fixture_sanity_latest.json"),
        "raw": load_json(output_dir / "raw_refresh_health_latest.json"),
        "raw_diagnostics": load_json(output_dir / "raw_refresh_diagnostics_latest.json"),
        "position": load_json(output_dir / "position_monitor_latest.json"),
        "recommendation_operations": load_json(output_dir / "recommendation_operations_latest.json"),
        "strategy_performance": load_json(output_dir / "strategy_performance_latest.json"),
        "report_evolution": load_json(output_dir / "report_evolution_latest.json"),
        "maturity": load_json(output_dir / "automation_maturity_latest.json"),
        "automation_readiness": load_json(output_dir / "automation_readiness_latest.json"),
        "intelligence": load_json(output_dir / "report_intelligence_latest.json"),
        "latest_commit": load_json(output_dir / "latest_commit.json"),
    }
    if evidence["raw"]:
        raw = dict(evidence["raw"])
        raw["partial_research_refresh"] = normalize_partial_research_refresh(raw.get("partial_research_refresh") or {})
        evidence["raw"] = raw
    db = database_summary(db_path)
    entry = downloads_entry_summary()
    rows = build_rows(evidence=evidence, db=db, entry=entry)
    summary = summarize_rows(rows, evidence=evidence, db=db, entry=entry)
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "product_readiness_dashboard",
        "purpose": "用用户视角验收 TAB FIFA 盘口研究系统：下注决策体验、可视化报告、开源模型吸收、数据库/新旧对比、主动测试补缺、持仓收益率和 automation 准入。",
        "executive_status": {
            "status": "ready" if summary["blocked_count"] == 0 and summary["partial_count"] == 0 else "in_progress",
            "product_readiness_score": summary["average_score"],
            "automation_entry_ready": bool(summary["automation_candidate_ready"]),
            "current_executable_new_stake_aud": summary["current_executable_new_stake_aud"],
            "primary_user_action": primary_user_action(rows),
            "primary_gap": primary_gap(rows),
            "recommended_next_action": recommended_next_action(rows),
        },
        "summary": summary,
        "rows": rows,
        "db_summary": db,
        "downloads_entry": entry,
        "chatgpt_baseline_note": "本面板不声称访问到 ChatGPT 私有实现；只把用户要求中的 ChatGPT 版本参照转化为可验证能力：本地 Dashboard、PDF、SQLite、新旧对比、开源模型审计、主动测试和 fail-closed 门禁。",
        "truthfulness_note": "该 Dashboard 只评估产品/报告系统成熟度；raw/private/preflight 未通过时仍不得发布当前可执行下注日报，也不会自动下注。",
    }
    payload["old_new_compare"] = old_new_compare(db_path, payload)
    return sanitize_public_payload(payload)


def build_rows(*, evidence: dict[str, dict[str, Any]], db: dict[str, Any], entry: dict[str, Any]) -> list[dict[str, Any]]:
    visual_summary = (evidence["visual"].get("summary") or {})
    model_adoption = (evidence["model"].get("source_adoption") or {})
    source_registry_summary = evidence["source_registry"].get("summary") or {}
    timeline_summary = (evidence["timeline"].get("summary") or {})
    available_summary = (evidence["available"].get("summary") or {})
    live_summary = (evidence["live"].get("summary") or {})
    raw = evidence["raw"]
    raw_diagnostics = evidence["raw_diagnostics"]
    partial_refresh = raw.get("partial_research_refresh") or {}
    fixture_summary = evidence["fixture"].get("summary") or {}
    fixture_executive = evidence["fixture"].get("executive_status") or {}
    position_summary = evidence["position"].get("summary") or {}
    recommendation_summary = evidence["recommendation_operations"].get("summary") or {}
    recommendation_executive = evidence["recommendation_operations"].get("executive_status") or {}
    strategy_summary = evidence["strategy_performance"].get("summary") or {}
    strategy_executive = evidence["strategy_performance"].get("executive_status") or {}
    evolution_summary = evidence["report_evolution"].get("summary") or {}
    evolution_executive = evidence["report_evolution"].get("executive_status") or {}
    maturity_summary = evidence["maturity"].get("summary") or {}
    automation_readiness = evidence["automation_readiness"]
    automation_public_safety = automation_readiness.get("public_safety") or {}
    automation_blockers = automation_readiness.get("blocking_reasons") or []
    latest = evidence["latest_commit"]
    intelligence_compare = evidence["intelligence"].get("report_comparison") or {}

    return [
        readiness_row(
            "betting_decision_home",
            "下注决策首页",
            "ready" if entry.get("recommendation_first") and entry.get("all_required_columns") else "partial",
            1.0 if entry.get("recommendation_first") and entry.get("all_required_columns") else 0.5,
            "首页第一屏已显示推荐下注板块、主动测试、补跑按钮和概率/赔率即时 EV 编辑。",
            f"推荐表字段 {entry.get('present_required_column_count', 0)}/{entry.get('required_column_count', 0)}；EV 输入 {entry.get('ev_input_count', 0)} 个。",
            "保持推荐下注板块在首页最前，所有新增按钮继续只生成研究/报告，不触发下注。",
            "强于静态报告：打开入口即可看到该怎么操作、为什么暂停或下注、金额和 EV。",
        ),
        readiness_row(
            "recommendation_operation_archive",
            "推荐操作归档",
            "ready" if evidence["recommendation_operations"].get("mode") == "recommendation_operations_dashboard" and db.get("recommendation_operation_count", 0) else "partial",
            1.0 if evidence["recommendation_operations"].get("mode") == "recommendation_operations_dashboard" and db.get("recommendation_operation_count", 0) else 0.5,
            "首页推荐下注板块已沉淀为正式 PDF/JSON/Markdown 操作研究报告，并写入本地 SQLite 快照。",
            f"候选盘口 {recommendation_summary.get('candidate_count', 0)}；研究候选金额 {aud0(recommendation_summary.get('research_candidate_stake_aud'))}；当前可执行金额 {aud0(recommendation_summary.get('executable_new_stake_aud'))}；状态 {recommendation_executive.get('status', '')}。",
            "保持推荐操作报告随每次日报和门禁状态重算；raw blocked 时继续显示 AUD 0 可执行金额。",
            "比静态报告更直接：用户可以把首页操作建议、暂停原因、新旧变化和金额归档到同一份研究报告。",
        ),
        readiness_row(
            "strategy_performance_tracking",
            "策略表现与回测闭环",
            "ready"
            if (
                evidence["strategy_performance"].get("mode") == "strategy_performance_dashboard"
                and int(strategy_summary.get("settled_bet_count") or 0) > 0
                and float(strategy_summary.get("clv_coverage_rate") or 0) > 0
            )
            else "partial"
            if evidence["strategy_performance"].get("mode") == "strategy_performance_dashboard"
            and db.get("strategy_performance_count", 0)
            else "blocked",
            float(strategy_summary.get("backtest_readiness_score") or 0)
            if evidence["strategy_performance"].get("mode") == "strategy_performance_dashboard"
            else 0.0,
            "历史推荐、EV/Edge、研究金额、预期收益、CLV/ROI 准备度和新旧变化已形成策略表现 Dashboard；真实收益缺失时明确 outcome_pending。",
            f"历史推荐 {strategy_summary.get('recommendation_count', 0)}；买入样本 {strategy_summary.get('buy_recommendation_count', 0)}；研究金额 {aud0(strategy_summary.get('research_stake_aud'))}；加权EV {pct(strategy_summary.get('stake_weighted_ev'))}；ROI={strategy_summary.get('realized_roi_status', '')}；CLV={strategy_summary.get('clv_tracking_status', '')}；状态 {strategy_executive.get('status', '')}。",
            "导入只读 My Bets 结算结果和开赛前/收盘赔率后，按板块、EV bucket 和 CLV/ROI 偏差校准下注阈值。",
            "不只给下注建议，还能追踪这些建议后来有没有变好：预期收益、真实收益、CLV、EV 分桶和板块表现能逐日优化。",
        ),
        readiness_row(
            "visual_report_system",
            "可视化报告体系",
            "ready" if visual_summary.get("dashboard_ready_count") == visual_summary.get("report_count") else "partial",
            float(visual_summary.get("average_score") or 0),
            "公开报告族已纳入图表、表格、Dashboard、自动化状态、新旧对比和 GitHub 参考审计。",
            f"报告族 {visual_summary.get('report_count', 0)}；图表 {visual_summary.get('reports_with_charts', 0)}；Dashboard {visual_summary.get('dashboard_ready_count', 0)}；新旧对比 {visual_summary.get('old_new_compare_count', 0)}/{visual_summary.get('report_count', 0)}。",
            "新增报告族必须进入 visual inventory，并至少有 JSON/MD/PDF 或 HTML 入口。",
            "比单一 PDF 更适合每日复盘：报告、仪表盘、状态门禁和源证据能一起看。",
        ),
        readiness_row(
            "report_evolution_control",
            "新旧报告变化总控",
            "ready" if evidence["report_evolution"].get("mode") == "report_evolution_dashboard" and db.get("report_evolution_count", 0) else "partial",
            float(evolution_summary.get("evolution_score") or 0)
            if evidence["report_evolution"].get("mode") == "report_evolution_dashboard"
            else 0.4,
            "已把日报 diff、报告族目录、推荐操作变化、策略表现变化和产品完成度变化汇总成跨报告族新旧变化总控台。",
            f"status={evolution_executive.get('status', '')}；diffs={evolution_summary.get('report_diff_count', 0)}；报告族={evolution_summary.get('current_report_family_count', 0)}；新旧覆盖={evolution_summary.get('old_new_compare_count', 0)}；目录变化={evolution_summary.get('catalog_changed_report_count', 0)}。",
            "保持该总控台在每次日报后重算；一旦出现报告族缺图表、缺新旧对比或得分下降，优先修复。",
            "比静态报告更适合长期优化：能直接看新报告相对旧报告哪些变了、哪些退化、哪些仍不能执行。",
        ),
        readiness_row(
            "open_source_model_adoption",
            "开源模型吸收",
            "ready"
            if int(model_adoption.get("implemented_reference_count") or 0) >= 2
            and (
                int(source_registry_summary.get("ui_blueprint_count") or 0) == 0
                or int(source_registry_summary.get("ui_blueprint_count") or 0) >= 6
            )
            else "partial",
            min(
                1.0,
                (
                    int(model_adoption.get("implemented_reference_count") or 0)
                    + int(source_registry_summary.get("ui_blueprint_implemented_count") or 0) / max(int(source_registry_summary.get("ui_blueprint_count") or 1), 1)
                )
                / 3,
            )
            if int(source_registry_summary.get("ui_blueprint_count") or 0)
            else min(1.0, int(model_adoption.get("implemented_reference_count") or 0) / 3),
            "已把 Hicruben、goalmodel、Dixon-Coles、penaltyblog、socceraction、openfootball 等 GitHub/开源模型和公开数据源转为本地模型审计、分歧、基本面、赛程校验、布局参考和 UI/Dashboard 蓝图。",
            "参考源 {refs}；已落地 {impl}；design reference {design}；GitHub元数据 {meta_status} {meta_ready}/{meta_refs}；4小时freshness={freshness_status} {fresh}/{ready}，stale={stale}，max_age={max_age}h；stars/open issues {stars}/{issues}。".format(
                refs=model_adoption.get("reference_count", 0),
                impl=model_adoption.get("implemented_reference_count", 0),
                design=model_adoption.get("design_reference_count", 0),
                meta_status=source_registry_summary.get("live_metadata_status", "missing"),
                meta_ready=source_registry_summary.get("live_metadata_ready_count", 0),
                meta_refs=source_registry_summary.get("reference_count", model_adoption.get("reference_count", 0)),
                freshness_status=source_registry_summary.get("live_metadata_freshness_status", "missing"),
                fresh=source_registry_summary.get("live_metadata_fresh_within_sla_count", 0),
                ready=source_registry_summary.get("live_metadata_ready_count", 0),
                stale=source_registry_summary.get("live_metadata_stale_count", 0),
                max_age=source_registry_summary.get("live_metadata_max_age_hours", ""),
                stars=source_registry_summary.get("github_stars_total", 0),
                issues=source_registry_summary.get("github_open_issues_total", 0),
            )
            + " UI蓝图 {implemented}/{count}；partial {partial}；data_required {data_required}。".format(
                implemented=source_registry_summary.get("ui_blueprint_implemented_count", 0),
                count=source_registry_summary.get("ui_blueprint_count", 0),
                partial=source_registry_summary.get("ui_blueprint_partial_count", 0),
                data_required=source_registry_summary.get("ui_blueprint_data_required_count", 0),
            )
            + " UI界面覆盖 {covered}/{count}；gated {gated}；layout_ready={layout_ready}。".format(
                covered=source_registry_summary.get("ui_blueprint_dashboard_covered_count", 0),
                count=source_registry_summary.get("ui_blueprint_count", 0),
                gated=source_registry_summary.get("ui_blueprint_dashboard_gated_count", 0),
                layout_ready=source_registry_summary.get("ui_blueprint_layout_ready", False),
            ),
            "继续把 calibration、track record、bracket simulator、时间衰减权重、xT/VAEP 基本面和 fixture sanity-check 转为可回测模块。",
            "下注建议不只看隐含概率，能展示模型共识、赔率去水、基本面、赛程校验、分歧、开源方法来源和对应的报告界面设计。",
        ),
        readiness_row(
            "public_fixture_sanity",
            "公开赛程校验",
            "ready" if evidence["fixture"].get("mode") == "fixture_sanity_dashboard" and int(fixture_summary.get("matched_count") or 0) > 0 else "partial",
            1.0 if evidence["fixture"].get("mode") == "fixture_sanity_dashboard" and int(fixture_summary.get("matched_count") or 0) > 0 else 0.45,
            "已把 openfootball/worldcup.json 公开赛程接入为 TAB Matches raw 的辅助校验，帮助发现队名、日期、分组、场地和赛果差异。",
            f"status={fixture_executive.get('status', '')}；openfootball={fixture_summary.get('openfootball_match_count', 0)}；TAB raw={fixture_summary.get('tab_match_count', 0)}；matched={fixture_summary.get('matched_count', 0)}；review={fixture_summary.get('mismatch_review_count', 0)}。",
            "继续把它作为延迟公开源 sanity-check；不要用它替代 TAB 盘口、赔率或 raw refresh。",
            "比静态报告更可靠：能把公开赛程源与 TAB raw 做每日差异检查，并写入新旧对比。",
        ),
        readiness_row(
            "database_and_old_new_compare",
            "数据库与新旧对比",
            "ready" if db.get("run_count", 0) and db.get("report_diff_count", 0) else "partial",
            0.9 if db.get("run_count", 0) and db.get("report_diff_count", 0) else 0.45,
            "日报 run、推荐、artifact、report diff、automation audit 和当前产品成熟度快照写入 SQLite。",
            f"runs={db.get('run_count', 0)}；diffs={db.get('report_diff_count', 0)}；recommendations={db.get('recommendation_count', 0)}；report_evolution={db.get('report_evolution_count', 0)}；strategy_performance={db.get('strategy_performance_count', 0)}；fixture_sanity={db.get('fixture_sanity_count', 0)}；report_catalog={db.get('report_catalog_item_count', 0)}；visual_inventory={db.get('report_visual_inventory_count', 0)}；automation_maturity={db.get('automation_maturity_count', 0)}；automation_doctor={db.get('automation_doctor_count', 0)}；product_snapshots={db.get('product_readiness_count', 0)}。",
            "每次新增日报或产品能力审计后继续写入数据库，并在入口展示新旧变化。",
            "能做日报/周报、回测、能力变化和旧报告差异追踪。",
        ),
        readiness_row(
            "live_data_and_board_gate",
            "实时盘口与板块门禁",
            live_data_status(raw, live_summary),
            live_data_score(raw, live_summary),
            "系统已把 TAB Live discovery、available board strategy 和 raw refresh 作为执行建议前置门禁。",
            (
                f"raw_ready={bool(raw.get('ready'))}；discovery_ready={bool(live_summary.get('discovery_ready'))}；"
                f"listed={live_summary.get('listed_expected_count', 0)}/{live_summary.get('expected_board_count', 0)}；"
                f"missing={live_summary.get('missing_expected_count', 0)}；"
                f"route_mismatch={bool(live_summary.get('route_mismatch_active'))}；"
                f"matches_live_targets={raw_diagnostics.get('matches_target_count', 0)}；"
                f"partial_refresh={partial_refresh.get('successful_board_count', 0)}/{partial_refresh.get('attempted_board_count', 0)}。"
            ),
            live_data_next_action(raw, live_summary, raw_diagnostics),
            "阻止用旧盘口或被拦截页面生成误导性下注建议。",
        ),
        readiness_row(
            "active_test_and_backfill",
            "主动测试与补缺",
            "partial" if int(timeline_summary.get("backfill_queue_count") or 0) else "ready",
            0.55 if int(timeline_summary.get("backfill_queue_count") or 0) else 1.0,
            "主动测试会按每天至少 4 次分析、每天 1 份报告检查时间线，并在 raw 通过后补跑缺口。",
            f"检查天数 {timeline_summary.get('day_count', 0)}；分析缺口日 {timeline_summary.get('missing_analysis_day_count', 0)}；日报缺口日 {timeline_summary.get('missing_report_day_count', 0)}；补跑队列 {timeline_summary.get('backfill_queue_count', 0)}。",
            "raw_ready=true 后运行 safe_no_latest_publish 补跑，再重跑日报门禁。",
            "减少人工漏跑，后续 automation 能主动发现缺口并修复。",
        ),
        readiness_row(
            "position_roi_loop",
            "持仓金额与收益率闭环",
            "partial" if evidence["position"].get("mode") == "position_monitor_dashboard" else "blocked",
            1.0 if position_summary.get("snapshot_ready") else 0.45 if evidence["position"].get("mode") == "position_monitor_dashboard" else 0.0,
            "已建立公开安全的持仓监控 Dashboard；私有资金状态、已下注金额和收益率未 ready 时显示 funding-update-pending。",
            f"snapshot_ready={bool(position_summary.get('snapshot_ready'))}；funding_state={public_pending_value(position_summary.get('public_visible_balance'))}。",
            "从 .app 启动只读持仓读取，用户完成 TAB 授权后导入当前日期私有快照。",
            "胜负结果会影响下一期可用余额和下注金额，而不是静态预算分配。",
        ),
        readiness_row(
            "automation_without_autobet",
            "每日 automation 准入",
            "blocked" if not maturity_summary.get("automation_ready") else "ready",
            float(maturity_summary.get("ready_ratio") or 0),
            "系统已将每日自动报告和不自动下注分离；automation 只允许生成研究、PDF、Dashboard 和补缺报告。",
            (
                f"maturity_ready={maturity_summary.get('required_ready_count', 0)}/{maturity_summary.get('required_count', 0)}；"
                f"latest_success={latest.get('report_date', '')}；"
                f"current_executable={available_summary.get('current_executable_new_stake_aud', 0)}；"
                f"public_safety={yes_no(automation_public_safety.get('output_safety_ready'))}/{yes_no(automation_public_safety.get('artifact_safety_ready'))}；"
                f"blockers={len(automation_blockers)}。"
            ),
            "先恢复 Live/raw/private snapshot，再安装 recurring automation；allow_auto_betting 保持 false。",
            "成熟后可每日生成报告，但不会越权下注。",
        ),
        readiness_row(
            "formal_pdf_archive",
            "正式 PDF 归档",
            "ready" if latest.get("status") == "ready_for_manual_report" else "partial",
            0.85 if latest.get("status") == "ready_for_manual_report" else 0.35,
            "最新可信成功报告继续通过 latest_commit 指针和 Downloads/FIFA Report/DDMMYYYY.pdf 管理。",
            f"latest_status={latest.get('status', '')}；latest_date={latest.get('report_date', '')}；intelligence_changed={intelligence_compare.get('changed_count', 0)}。",
            "当前 blocked attempted run 不发布为 DDMMYYYY.pdf；门禁通过后再生成新的正式报告。",
            "避免 PDF 存在就误认为可下注，保留真实可信的报告版本线。",
        ),
    ]


def live_data_next_action(raw: dict[str, Any], live_summary: dict[str, Any], diagnostics: dict[str, Any]) -> str:
    if raw.get("ready") is True and live_summary.get("discovery_ready") is True:
        return "继续重跑日报门禁，并核对私有持仓快照。"
    partial = raw.get("partial_research_refresh") or {}
    partial_current = bool(partial.get("current_research_only_allowed"))
    if live_summary.get("discovery_ready") is True and (
        live_summary.get("missing_expected_count") or live_summary.get("route_mismatch_active")
    ):
        match_targets = int(diagnostics.get("matches_target_count") or 0)
        partial_text = ""
        if partial_current:
            partial_text = f"最新 raw diagnostics 已证明 {partial.get('successful_board_count')}/{partial.get('attempted_board_count')} 个尝试板块可研究；"
        elif int(partial.get("successful_board_count") or 0):
            partial_text = (
                f"上一份 partial raw 已变为 {partial.get('freshness_status')}，age={partial.get('age_hours')}h，"
                "只能作为历史诊断；"
            )
        return (
            f"Matches/Futures/Group Betting 已能只读刷新，当前 Matches live targets={match_targets}；{partial_text}"
            "Australia Markets、Team Futures Multi 未在 TAB live 导航中列出并出现 route mismatch。"
            "保持这两个板块 unavailable，不用旧盘口；等待 TAB 重新列出或只生成研究-only 诊断，新增执行金额维持 AUD 0。"
        )
    if live_summary.get("access_denied") or "access_denied" in (raw.get("blocker_codes") or []):
        return "TAB 返回 Access Denied；视为 AI controlled access 被拒绝，自动 raw 保持 fail-closed。下一步接入官方/授权数据源或用户导出导入，latest_commit 不变。"
    return "先接入授权 board/raw 数据源或导入用户导出快照；质量通过后再重跑日报门禁。"


def live_data_status(raw: dict[str, Any], live_summary: dict[str, Any]) -> str:
    if raw.get("ready") is True and live_summary.get("discovery_ready") is True:
        return "ready"
    partial = raw.get("partial_research_refresh") or {}
    if live_summary.get("discovery_ready") is True and bool(partial.get("current_research_only_allowed")):
        return "partial"
    return "blocked"


def live_data_score(raw: dict[str, Any], live_summary: dict[str, Any]) -> float:
    if raw.get("ready") is True and live_summary.get("discovery_ready") is True:
        return 1.0
    partial = raw.get("partial_research_refresh") or {}
    attempted = int(partial.get("attempted_board_count") or 0)
    successful = int(partial.get("successful_board_count") or 0)
    if live_summary.get("discovery_ready") is True and successful > 0 and bool(partial.get("current_research_only_allowed")):
        return round(min(0.65, 0.25 + 0.4 * (successful / max(attempted, 1))), 4)
    return 0.0


def readiness_row(
    row_id: str,
    title: str,
    status: str,
    score: float,
    user_takeaway: str,
    evidence: str,
    next_action: str,
    value_over_static_report: str,
) -> dict[str, Any]:
    status = status if status in {"ready", "partial", "blocked"} else "blocked"
    return {
        "row_id": row_id,
        "title": title,
        "status": status,
        "score": round(max(0.0, min(1.0, float(score))), 4),
        "user_takeaway": user_takeaway,
        "evidence": evidence,
        "next_action": "保持并随每次日报重算。" if status == "ready" else next_action,
        "value_over_static_report": value_over_static_report,
    }


def summarize_rows(
    rows: list[dict[str, Any]],
    *,
    evidence: dict[str, dict[str, Any]],
    db: dict[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any]:
    ready = [row for row in rows if row["status"] == "ready"]
    partial = [row for row in rows if row["status"] == "partial"]
    blocked = [row for row in rows if row["status"] == "blocked"]
    available = evidence["available"].get("summary") or {}
    maturity = evidence["maturity"].get("summary") or {}
    return {
        "capability_count": len(rows),
        "ready_count": len(ready),
        "partial_count": len(partial),
        "blocked_count": len(blocked),
        "average_score": round(sum(float(row["score"]) for row in rows) / len(rows), 4) if rows else 0.0,
        "current_executable_new_stake_aud": float(available.get("current_executable_new_stake_aud") or 0),
        "automation_candidate_ready": bool(maturity.get("automation_ready")),
        "database_ready": bool(db.get("ready")),
        "homepage_ready": bool(entry.get("recommendation_first") and entry.get("all_required_columns")),
        "blocked_titles": [row["title"] for row in blocked],
        "partial_titles": [row["title"] for row in partial],
    }


def render_product_readiness_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA 产品完成度 Dashboard",
        "",
        "本报告从用户视角验收当前系统是否已经达到下注研究日报/自动化前的产品水位。它不是下注执行指令。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- product_readiness_score: `{pct(executive.get('product_readiness_score'))}`",
        f"- ready / partial / blocked: `{summary.get('ready_count', 0)} / {summary.get('partial_count', 0)} / {summary.get('blocked_count', 0)}`",
        f"- current_executable_new_stake_aud: `{aud0(summary.get('current_executable_new_stake_aud'))}`",
        f"- primary_user_action: {md(executive.get('primary_user_action'))}",
        f"- primary_gap: {md(executive.get('primary_gap'))}",
        f"- recommended_next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## 新旧完成度变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- score_delta: `{compare.get('score_delta', 0)}`",
        f"- status_delta: `{compare.get('status_delta', '')}`",
        "",
        "## Capability Matrix",
        "",
        "| 能力 | 状态 | 得分 | 用户结论 | 证据 | 下一步 | 相对静态报告价值 |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            "| {title} | {status} | {score} | {takeaway} | {evidence} | {next_action} | {value} |".format(
                title=md(row.get("title")),
                status=md(row.get("status")),
                score=pct(row.get("score")),
                takeaway=md(row.get("user_takeaway")),
                evidence=md(row.get("evidence")),
                next_action=md(row.get("next_action")),
                value=md(row.get("value_over_static_report")),
            )
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('chatgpt_baseline_note', '')}"])
    return "\n".join(lines)


def write_product_readiness_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("rows") or []
    compare = payload.get("old_new_compare") or {}
    charts = [
        chart_from_items("产品能力得分", [(row.get("title", ""), float(row.get("score") or 0) * 100) for row in rows], "#1F4E79"),
        chart_from_items(
            "状态分布",
            [("ready", summary.get("ready_count", 0)), ("partial", summary.get("partial_count", 0)), ("blocked", summary.get("blocked_count", 0))],
            "#247A5A",
        ),
        chart_from_items("阻塞能力", [(row.get("title", ""), 1 if row.get("status") == "blocked" else 0) for row in rows], "#C62828"),
        chart_from_items(
            "数据库资产",
            [
                ("runs", (payload.get("db_summary") or {}).get("run_count", 0)),
                ("diffs", (payload.get("db_summary") or {}).get("report_diff_count", 0)),
                ("recommendations", (payload.get("db_summary") or {}).get("recommendation_count", 0)),
                ("operation snapshots", (payload.get("db_summary") or {}).get("recommendation_operation_count", 0)),
                ("report evolution", (payload.get("db_summary") or {}).get("report_evolution_count", 0)),
                ("strategy perf", (payload.get("db_summary") or {}).get("strategy_performance_count", 0)),
                ("fixture sanity", (payload.get("db_summary") or {}).get("fixture_sanity_count", 0)),
                ("report catalog", (payload.get("db_summary") or {}).get("report_catalog_item_count", 0)),
                ("automation maturity", (payload.get("db_summary") or {}).get("automation_maturity_count", 0)),
                ("automation doctor", (payload.get("db_summary") or {}).get("automation_doctor_count", 0)),
                ("product snapshots", (payload.get("db_summary") or {}).get("product_readiness_count", 0)),
            ],
            "#6A4C93",
        ),
        chart_from_items(
            "新旧变化",
            [
                ("score delta x100", abs(float(compare.get("score_delta") or 0)) * 100),
                ("newly ready", len(compare.get("newly_ready") or [])),
                ("newly blocked", len(compare.get("newly_blocked") or [])),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 产品完成度 Dashboard",
        subtitle="用户视角验收：下注决策体验、可视化报告、开源模型、数据库对比、主动测试和 automation 准入；只生成研究报告，不自动下注。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("product_readiness_score", pct(executive.get("product_readiness_score"))),
            ("ready/partial/blocked", f"{summary.get('ready_count', 0)}/{summary.get('partial_count', 0)}/{summary.get('blocked_count', 0)}"),
            ("current executable stake", aud0(summary.get("current_executable_new_stake_aud"))),
            ("primary_gap", str(executive.get("primary_gap", ""))),
            ("primary_user_action", str(executive.get("primary_user_action", ""))),
        ],
        charts=charts,
        table_headers=["能力", "状态", "得分", "用户结论"],
        table_rows=[
            [str(row.get("title", "")), str(row.get("status", "")), pct(row.get("score")), str(row.get("user_takeaway", ""))]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "下一步动作",
                "headers": ["能力", "下一步"],
                "rows": [[str(row.get("title", "")), str(row.get("next_action", ""))] for row in rows if row.get("status") != "ready"],
            },
            {
                "title": "相对静态报告价值",
                "headers": ["能力", "价值"],
                "rows": [[str(row.get("title", "")), str(row.get("value_over_static_report", ""))] for row in rows],
            },
            {
                "title": "新旧完成度变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["score_delta", str(compare.get("score_delta", 0))],
                    ["status_delta", str(compare.get("status_delta", ""))],
                    ["newly_ready", ", ".join(compare.get("newly_ready") or [])],
                    ["newly_blocked", ", ".join(compare.get("newly_blocked") or [])],
                ],
            },
        ],
    )


def persist_product_readiness(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS product_readiness_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    product_readiness_score REAL NOT NULL DEFAULT 0,
                    ready_count INTEGER NOT NULL DEFAULT 0,
                    partial_count INTEGER NOT NULL DEFAULT 0,
                    blocked_count INTEGER NOT NULL DEFAULT 0,
                    automation_entry_ready INTEGER NOT NULL DEFAULT 0,
                    current_executable_new_stake_aud REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO product_readiness_snapshots(
                    snapshot_id, generated_at, status, product_readiness_score,
                    ready_count, partial_count, blocked_count, automation_entry_ready,
                    current_executable_new_stake_aud, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_payload.get("snapshot_id", ""),
                    public_payload.get("generated_at", ""),
                    str(executive.get("status") or ""),
                    float(executive.get("product_readiness_score") or 0),
                    int(summary.get("ready_count") or 0),
                    int(summary.get("partial_count") or 0),
                    int(summary.get("blocked_count") or 0),
                    int(bool(executive.get("automation_entry_ready"))),
                    float(summary.get("current_executable_new_stake_aud") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "product_readiness_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def old_new_compare(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "score_delta": 0, "status_delta": "none"}
    try:
        with connect_report_db(db_path) as conn:
            row = conn.execute(
                """
                SELECT generated_at, status, product_readiness_score, payload_json
                FROM product_readiness_snapshots
                WHERE snapshot_id != ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (payload.get("snapshot_id", ""),),
            ).fetchone()
    except sqlite3.Error:
        return {"status": "compare_unavailable", "score_delta": 0, "status_delta": "unknown"}
    if not row:
        return {"status": "no_previous_snapshot", "score_delta": 0, "status_delta": "none"}
    previous_payload = safe_json(row["payload_json"])
    previous_rows = {item.get("row_id"): item for item in previous_payload.get("rows", []) if isinstance(item, dict)}
    current_rows = {item.get("row_id"): item for item in payload.get("rows", []) if isinstance(item, dict)}
    newly_ready = [
        str(current_rows[row_id].get("title", row_id))
        for row_id, item in current_rows.items()
        if item.get("status") == "ready" and (previous_rows.get(row_id) or {}).get("status") != "ready"
    ]
    newly_blocked = [
        str(current_rows[row_id].get("title", row_id))
        for row_id, item in current_rows.items()
        if item.get("status") == "blocked" and (previous_rows.get(row_id) or {}).get("status") != "blocked"
    ]
    score_delta = round(float(payload.get("summary", {}).get("average_score") or 0) - float(row["product_readiness_score"] or 0), 4)
    return {
        "status": "compared",
        "previous_generated_at": row["generated_at"],
        "score_delta": score_delta,
        "status_delta": f"{row['status']} -> {(payload.get('executive_status') or {}).get('status', '')}",
        "newly_ready": newly_ready,
        "newly_blocked": newly_blocked,
    }


def database_summary(db_path: Path) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"ready": False, "database": Path(db_path).name}
    try:
        uri = f"file:{Path(db_path).resolve()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            return {
                "ready": True,
                "database": Path(db_path).name,
                "run_count": table_count(conn, "report_runs"),
                "recommendation_count": table_count(conn, "recommendations"),
                "report_diff_count": table_count(conn, "report_diffs"),
                "artifact_count": table_count(conn, "artifacts"),
                "automation_run_count": table_count(conn, "automation_runs"),
                "report_visual_inventory_count": table_count(conn, "report_visual_inventory_snapshots"),
                "report_catalog_item_count": table_count(conn, "report_catalog_items"),
                "recommendation_operation_count": table_count(conn, "recommendation_operation_snapshots"),
                "report_evolution_count": table_count(conn, "report_evolution_snapshots"),
                "strategy_performance_count": table_count(conn, "strategy_performance_snapshots"),
                "fixture_sanity_count": table_count(conn, "fixture_sanity_snapshots"),
                "automation_maturity_count": table_count(conn, "automation_maturity_snapshots"),
                "automation_doctor_count": table_count(conn, "automation_doctor_snapshots"),
                "product_readiness_count": table_count(conn, "product_readiness_snapshots"),
            }
        finally:
            conn.close()
    except sqlite3.Error:
        return {"ready": False, "database": Path(db_path).name}


def downloads_entry_summary() -> dict[str, Any]:
    entry = Path.home() / "Downloads" / "FIFA Report" / "TAB FIFA盘口研究系统.html"
    required = [
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
            "recommendation_first": False,
            "required_column_count": len(required),
            "present_required_column_count": 0,
            "ev_input_count": 0,
            "all_required_columns": False,
        }
    text = entry.read_text(encoding="utf-8", errors="ignore")
    rec_index = text.find("<h2>推荐下注板块</h2>")
    hero_index = text.find("<h2>今日操作摘要</h2>")
    present = [item for item in required if item in text]
    return {
        "ready": rec_index >= 0 and len(present) == len(required),
        "recommendation_first": rec_index >= 0 and (hero_index < 0 or rec_index < hero_index),
        "required_column_count": len(required),
        "present_required_column_count": len(present),
        "ev_input_count": text.count("mini-input"),
        "all_required_columns": len(present) == len(required),
    }


def primary_user_action(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("row_id") == "live_data_and_board_gate" and row.get("status") == "blocked":
            return str(row.get("next_action") or "先恢复 TAB live/raw 门禁。")
    for row in rows:
        if row.get("status") != "ready":
            return str(row.get("next_action") or "")
    return "保持每日生成报告并继续审计。"


def primary_gap(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("status") == "blocked":
            return str(row.get("title"))
    for row in rows:
        if row.get("status") == "partial":
            return str(row.get("title"))
    return "无关键缺口"


def recommended_next_action(rows: list[dict[str, Any]]) -> str:
    gap = primary_gap(rows)
    action = primary_user_action(rows)
    return f"{gap}：{action}"


def table_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except sqlite3.Error:
        return 0


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


def public_pending_value(value: Any) -> str:
    text = str(value or "funding-update-pending")
    return text.replace("account-update-pending", "funding-update-pending").replace("balance", "funding")


def yes_no(value: Any) -> str:
    return "是" if bool(value) else "否"


def snapshot_id(generated_at: str) -> str:
    return "product-readiness-" + generated_at.replace(":", "").replace("+", "-").replace(".", "-")


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def aud0(value: Any) -> str:
    try:
        return f"AUD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "AUD 0"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
