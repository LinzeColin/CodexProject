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


AUTOMATION_MATURITY_JSON_LATEST = "automation_maturity_latest.json"
AUTOMATION_MATURITY_MD_LATEST = "automation_maturity_latest.md"
AUTOMATION_MATURITY_PDF_LATEST = "automation_maturity_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_automation_maturity_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_automation_maturity(output_dir, db_path)
    json_path = output_dir / AUTOMATION_MATURITY_JSON_LATEST
    md_path = output_dir / AUTOMATION_MATURITY_MD_LATEST
    pdf_path = output_dir / AUTOMATION_MATURITY_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_automation_maturity_markdown(payload))
    pdf_summary = write_automation_maturity_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_automation_maturity(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_automation_maturity(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    latest_commit = load_json(output_dir / "latest_commit.json")
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    candidate = load_json(output_dir / "automation_candidate_latest.json")
    doctor = load_json(output_dir / "automation_doctor_latest.json")
    intelligence = load_json(output_dir / "report_intelligence_latest.json")
    report_index = load_json(output_dir / "report_index_latest.json")
    timeline = load_json(output_dir / "active_timeline_latest.json")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    model_comparison = load_json(output_dir / "tab_fifa_model_comparison_v0_1.json")
    source_registry = load_json(output_dir / "source_model_registry_latest.json")
    db = database_status(output_dir / "tab_fifa_reports.sqlite3")
    entry = downloads_entry_status()
    rows = build_rows(
        output_dir=output_dir,
        latest_commit=latest_commit,
        readiness=readiness,
        candidate=candidate,
        doctor=doctor,
        intelligence=intelligence,
        report_index=report_index,
        timeline=timeline,
        raw_health=raw_health,
        model_comparison=model_comparison,
        source_registry=source_registry,
        db=db,
        entry=entry,
    )
    summary = summarize_rows(rows)
    recovery_playbook = build_recovery_playbook(rows, readiness, raw_health, timeline, candidate)
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "automation_maturity",
        "purpose": "把用户要求的自动爬虫、PDF日报、本地数据库、新旧对比、图表/Dashboard、开源模型参考、主动测试和安全边界拆成可验证验收矩阵。",
        "executive_status": {
            "automation_ready": summary["required_ready_count"] == summary["required_count"],
            "overall_score": summary["average_score"],
            "status": "ready" if summary["required_ready_count"] == summary["required_count"] else "blocked",
            "primary_gap": first_gap(rows),
            "recommended_next_action": recommended_next_action(rows),
        },
        "summary": summary,
        "rows": rows,
        "manual_review_queue": [row for row in rows if row["status"] != "ready"],
        "automation_recovery_playbook": recovery_playbook,
        "old_new_compare": old_new_compare(db_path, summary, snapshot_id(generated_at)),
        "source_artifacts": {
            "latest_commit": "latest_commit.json" if latest_commit else "",
            "automation_readiness": "automation_readiness_latest.json" if readiness else "",
            "automation_candidate": "automation_candidate_latest.json" if candidate else "",
            "automation_doctor": "automation_doctor_latest.json" if doctor else "",
            "report_intelligence": "report_intelligence_latest.json" if intelligence else "",
            "report_index": "report_index_latest.json" if report_index else "",
            "active_timeline": "active_timeline_latest.json" if timeline else "",
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "model_comparison": "tab_fifa_model_comparison_v0_1.json" if model_comparison else "",
            "source_model_registry": "source_model_registry_latest.json" if source_registry else "",
            "database": db.get("database", ""),
            "downloads_entry": entry.get("file", ""),
        },
        "truthfulness_note": "本矩阵只证明报告系统成熟度；不自动下注。被阻塞的项目不能用人工乐观判断改成 ready。",
        "automation_boundary_note": "恢复 playbook 只允许只读刷新、补跑报告和人工授权调度；禁止自动下注、点击赔率、添加 Bet Slip 或绕过 fail-closed 门禁。",
    }
    return sanitize_public_payload(payload)


def build_rows(
    *,
    output_dir: Path,
    latest_commit: dict[str, Any],
    readiness: dict[str, Any],
    candidate: dict[str, Any],
    doctor: dict[str, Any],
    intelligence: dict[str, Any],
    report_index: dict[str, Any],
    timeline: dict[str, Any],
    raw_health: dict[str, Any],
    model_comparison: dict[str, Any],
    source_registry: dict[str, Any],
    db: dict[str, Any],
    entry: dict[str, Any],
) -> list[dict[str, Any]]:
    timeline_summary = timeline.get("summary") or {}
    visual_chart_count = int(((intelligence.get("artifacts") or {}).get("pdf_summary") or {}).get("chart_count") or 0)
    model_adoption = model_comparison.get("source_adoption") or {}
    source_registry_summary = source_registry.get("summary") or {}
    ui_blueprint_count = int(source_registry_summary.get("ui_blueprint_count") or 0)
    ui_blueprint_implemented = int(source_registry_summary.get("ui_blueprint_implemented_count") or 0)
    recommendation_labels = entry.get("recommendation_labels") or {}
    intelligence_dashboard = intelligence.get("automation_dashboard") or {}
    raw_ready = bool((readiness.get("raw_refresh") or {}).get("ready", raw_health.get("ready")))
    private_bootstrap = readiness.get("private_position_bootstrap") or {}
    research_only_daily = readiness.get("research_only_daily_report") or {}
    formal_ready = bool(readiness.get("formal_report_publish_ready"))
    research_only_daily_ready = bool(readiness.get("research_only_daily_report_ready")) or (
        file_exists(output_dir / "partial_daily_research_latest.pdf")
        and file_exists(output_dir / "partial_daily_research_latest.json")
    )
    latest_ready = latest_commit.get("status") == "ready_for_manual_report"
    latest_fail_closed = latest_ready and not formal_ready and bool((readiness.get("technical_preflight") or {}).get("blocks_publication"))
    return [
        row(
            "public_raw_crawler",
            "自动爬虫抓取公开盘口",
            raw_ready,
            "公开盘口 raw freshness 通过，5个目标板块可用于正式日报。",
            evidence=(readiness.get("raw_refresh") or {}).get("ready_required") or str(raw_health.get("ready_required_target_count") or "0/5"),
            gap="公开盘口 raw 当前 blocked/stale，不能发布新日报。",
            next_action="先接入授权 raw 或导入用户导出快照后重跑日报门禁；TAB 拒绝 AI controlled access 时不运行 headed fallback。",
            user_value="保证下注建议来自当前盘口，而不是旧赔率。",
        ),
        row(
            "four_hour_cadence",
            "每4-5小时至少一次分析",
            bool(timeline_summary.get("cadence_ready_for_all_days")),
            "主动测试显示每天至少4次有效分析。",
            evidence=f"缺口日 {timeline_summary.get('missing_analysis_day_count', 0)}；补跑队列 {timeline_summary.get('backfill_queue_count', 0)}",
            gap="主动测试仍发现每日分析缺口。",
            next_action="raw 恢复后执行安全补跑；补跑报告不发布 latest_commit。",
            user_value="让报告具备时间效应，避免预算长期闲置或错过早盘变化。",
        ),
        row(
            "daily_pdf_report",
            "每天一份中文PDF日报",
            bool(timeline_summary.get("formal_report_ready_for_all_days")) and formal_ready,
            "正式日报每日生成并通过发布门禁。",
            evidence=f"日报缺口日 {timeline_summary.get('missing_report_day_count', 0)}；formal={formal_ready}",
            gap="当前正式日报门禁未通过，缺口日报不能作为可执行报告。",
            next_action="修复 raw 和私有持仓快照后重跑日报；只在门禁通过时复制为 DDMMYYYY.pdf。",
            user_value="每天打开一个明确的 PDF 决策包。",
        ),
        row(
            "research_only_daily_report",
            "正式门禁失败时仍生成研究诊断PDF",
            research_only_daily_ready,
            "partial_daily_research_latest.pdf 已生成并保持 research-only / AUD 0，不替代正式可执行下注日报。",
            evidence=(
                f"status={research_only_daily.get('status', 'missing')}；"
                f"pdf={research_only_daily.get('pdf', 'partial_daily_research_latest.pdf')}；"
                f"stake=AUD {research_only_daily.get('current_executable_new_stake_aud', 0)}"
            ),
            gap="缺少可用的 research-only 诊断日报；formal blocked 时用户没有每日研究产物。",
            next_action="生成 partial_daily_research_latest.pdf，并确认 execution_allowed=false、current_executable_new_stake_aud=0。",
            user_value="即使 TAB 部分板块缺失，仍能每日拿到研究诊断和缺口说明，不误当作下注执行报告。",
        ),
        row(
            "local_database",
            "本地SQLite数据库保存报告历史",
            bool(db.get("ready")),
            "SQLite 存在并保存 run、recommendation、automation audit 等记录。",
            evidence=f"runs={db.get('run_count', 0)}；automation_runs={db.get('automation_run_count', 0)}；audits={db.get('active_timeline_audit_count', 0)}",
            gap="数据库不存在或缺少关键历史记录。",
            next_action="先运行日报或主动测试，让 report_store 写入数据库。",
            user_value="支持日报/周报、回测和新旧报告对比。",
        ),
        row(
            "old_new_compare",
            "新报告与旧报告对比",
            has_report_comparison(intelligence, report_index),
            "Report Intelligence 和 Report Index 提供 added/removed/changed/retained 对比。",
            evidence=compare_evidence(intelligence, report_index),
            gap="缺少可读的新旧推荐差异。",
            next_action="确保每次 run 写入 report_index，并生成 report_comparison。",
            user_value="看清推荐变化、赔率变化和仓位变化，不重复下注。",
        ),
        row(
            "visual_reports_dashboard",
            "所有核心报表有图表和Dashboard",
            visual_chart_count >= 10 and file_exists(output_dir / "tab_fifa_dashboard_latest.html"),
            "核心报告包含图表、附表和本地 Dashboard。",
            evidence=f"report_intelligence_charts={visual_chart_count}；dashboard={'有' if file_exists(output_dir / 'tab_fifa_dashboard_latest.html') else '缺'}",
            gap="图表或本地 dashboard 缺失。",
            next_action="补齐缺少图表/附表的报告，并纳入 report_visual_inventory。",
            user_value="不用读技术日志，一页看懂下注和自动化状态。",
        ),
        row(
            "report_intelligence_dashboard",
            "业务可读的自动化总控台",
            int(intelligence_dashboard.get("ready_count") or 0) >= 6,
            "Report Intelligence 已把推荐下注、主动测试、报告历史、开源模型和自动化门禁合并成业务总控台。",
            evidence=(
                f"ready_count={intelligence_dashboard.get('ready_count', 0)}；"
                f"blocked_count={intelligence_dashboard.get('blocked_count', 0)}；"
                f"average_score={intelligence_dashboard.get('average_score', 0)}"
            ),
            gap="缺少业务可读的自动化总控台；用户仍需看多个技术报告。",
            next_action="重建 report_intelligence_latest.*，确认 Automation Dashboard ready_count 至少 6。",
            user_value="用户一眼看到 raw、节奏、PDF、数据库、新旧对比、模型和发布门禁，而不是阅读工程日志。",
        ),
        row(
            "open_source_models",
            "GitHub开源模型参考已转化",
            int(model_adoption.get("implemented_reference_count") or 0) >= 2 and (ui_blueprint_count == 0 or ui_blueprint_count >= 6),
            "已把 Elo/Dixon-Coles/Monte Carlo、goalmodel xG/OU/BTTS、penaltyblog no-vig/盘口概率、socceraction xT/VAEP、openfootball 赛程源等转成模型、报告、界面参考和 UI蓝图，并通过 GitHub元数据追踪来源新鲜度。"
            f"4小时freshness={source_registry_summary.get('live_metadata_freshness_status', 'missing')} "
            f"{source_registry_summary.get('live_metadata_fresh_within_sla_count', 0)}/{source_registry_summary.get('live_metadata_ready_count', 0)}，"
            f"stale={source_registry_summary.get('live_metadata_stale_count', 0)}。",
            evidence=(
                f"implemented={model_adoption.get('implemented_reference_count', 0)}/{model_adoption.get('reference_count', 0)}；"
                f"UI蓝图={ui_blueprint_implemented}/{ui_blueprint_count}；"
                f"GitHub元数据={source_registry_summary.get('live_metadata_status', 'missing')} "
                f"{source_registry_summary.get('live_metadata_ready_count', 0)}/{source_registry_summary.get('reference_count', model_adoption.get('reference_count', 0))}；"
                f"4小时freshness={source_registry_summary.get('live_metadata_freshness_status', 'missing')} "
                f"{source_registry_summary.get('live_metadata_fresh_within_sla_count', 0)}/{source_registry_summary.get('live_metadata_ready_count', 0)}，"
                f"stale={source_registry_summary.get('live_metadata_stale_count', 0)}"
            ),
            gap="开源参考未完整落到本地生产模型；基本面事件流和部分 license 风险仍需人工控制。",
            next_action="继续把 track record、calibration、bracket simulator、xT/VAEP 基本面和 fixture sanity-check 转成可视化审计区块。",
            user_value="比只看隐含概率更有独立研究价值，能同时解释盘口价值、基本面、赛程证据和报告界面设计来源。",
        ),
        row(
            "bet_recommendation_board",
            "首页推荐下注板块可直接操作",
            bool(entry.get("ready")) and all(recommendation_labels.values()),
            "首页优先展示推荐下注板块，含时间/盘口/下注/赔率/金额/EV/置信度等。",
            evidence=", ".join(label for label, ok in recommendation_labels.items() if ok) or "入口未检测到推荐表",
            gap="入口缺少关键下注决策字段。",
            next_action="刷新 Downloads app entry 并检查推荐表字段。",
            user_value="打开首页即可知道应该看哪些盘、下注什么、金额多少。",
        ),
        row(
            "private_position_monitoring",
            "已下注持仓和收益率监控",
            bool(private_bootstrap.get("ready")),
            "当日私有持仓快照就绪，可更新持仓金额和累计收益率。",
            evidence=f"status={private_bootstrap.get('status', 'missing')}；report_date={private_bootstrap.get('report_date', '')}",
            gap="当前私有持仓快照不适用于最新日报。",
            next_action="在本地入口启动只读持仓读取；完成 TAB 授权后导入快照并重跑日报。",
            user_value="胜利会增加可用余额，失败会降低预算；策略可按真实余额滚动。",
        ),
        row(
            "fail_closed_publish",
            "失败run不覆盖最新成功报告",
            bool(latest_fail_closed or (latest_ready and latest_commit.get("public_artifact_safety_ready") is True)),
            "当前 blocked attempted run 没有推进 latest_commit，仍保留最后可信成功报告。",
            evidence=f"latest={latest_commit.get('report_date', '')}/{latest_commit.get('status', '')}；formal={formal_ready}",
            gap="latest 指针或公开安全门禁不一致。",
            next_action="继续保持 latest_commit 只由通过门禁的 run 更新。",
            user_value="避免把失败报告误当成下注日报。",
        ),
        row(
            "local_app_report_center",
            "本地入口和报告中心",
            bool(entry.get("ready")) and file_exists(output_dir / "report_index_latest.pdf"),
            "Downloads 入口、app bundle、报告历史和辅助报告均可打开。",
            evidence=f"entry={entry.get('file', '')}；links={entry.get('artifact_link_count', 0)}",
            gap="入口或报告中心产物缺失。",
            next_action="运行 build_downloads_app_entry.py 刷新入口和 app_assets。",
            user_value="所有 PDF、JSON、Dashboard 有统一入口。",
        ),
        row(
            "scheduler_authorization",
            "可进入每日automation调度",
            bool(readiness.get("recurring_automation_ready")) and bool(candidate.get("activation_ready_after_authorization")),
            "技术门禁和授权均已满足，可创建 recurring automation。",
            evidence=f"candidate={candidate.get('status', '')}；installed={bool(candidate.get('installed'))}；recurring={bool(readiness.get('recurring_automation_ready'))}",
            gap="当前只能手动触发；调度候选未安装或授权/技术门禁未通过。",
            next_action="所有 P0 门禁通过后，再由用户明确授权创建 recurring automation。",
            user_value="进入无人值守日报，但仍只生成报告、不下注。",
        ),
        row(
            "no_auto_wagering",
            "安全边界：不自动下注",
            candidate.get("auto_wagering_allowed") is False,
            "系统只生成研究报告、检查和补跑队列，不点击赔率、不添加投注单。",
            evidence=f"auto_wagering_allowed={candidate.get('auto_wagering_allowed')}",
            gap="候选配置未声明禁止自动下注。",
            next_action="保持 auto_wagering_allowed=false，并继续用测试扫描交互代码。",
            user_value="研究建议可用于人工下注参考，不会越权操作账户。",
        ),
    ]


def row(
    requirement_id: str,
    title: str,
    ready: bool,
    ready_evidence: str,
    *,
    evidence: str,
    gap: str,
    next_action: str,
    user_value: str,
) -> dict[str, Any]:
    status = "ready" if ready else "blocked"
    return {
        "requirement_id": requirement_id,
        "title": title,
        "required_for_automation": True,
        "status": status,
        "score": 1.0 if ready else 0.0,
        "evidence": ready_evidence if ready else evidence,
        "gap": "" if ready else gap,
        "next_action": "保持自动生成并持续审计。" if ready else next_action,
        "user_value": user_value,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = [row for row in rows if row.get("required_for_automation")]
    ready = [row for row in required if row.get("status") == "ready"]
    blocked = [row for row in required if row.get("status") != "ready"]
    return {
        "requirement_count": len(rows),
        "required_count": len(required),
        "required_ready_count": len(ready),
        "required_blocked_count": len(blocked),
        "average_score": round(sum(float(row.get("score") or 0) for row in rows) / len(rows), 4) if rows else 0.0,
        "ready_ratio": round(len(ready) / len(required), 4) if required else 0.0,
        "p0_blocker_count": len([row for row in blocked if row["requirement_id"] in {"public_raw_crawler", "daily_pdf_report", "private_position_monitoring"}]),
        "blocked_titles": [row["title"] for row in blocked],
    }


def build_recovery_playbook(
    rows: list[dict[str, Any]],
    readiness: dict[str, Any],
    raw_health: dict[str, Any],
    timeline: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {row.get("requirement_id"): row for row in rows}
    raw_row = by_id.get("public_raw_crawler") or {}
    cadence_row = by_id.get("four_hour_cadence") or {}
    pdf_row = by_id.get("daily_pdf_report") or {}
    private_row = by_id.get("private_position_monitoring") or {}
    scheduler_row = by_id.get("scheduler_authorization") or {}
    timeline_summary = timeline.get("summary") or {}
    private_status = (readiness.get("private_position_bootstrap") or {}).get("status", "missing")
    raw_blockers = raw_health.get("blocker_codes") or []
    return [
        playbook_item(
            "P0",
            1,
            "恢复公开盘口 raw refresh",
            raw_row,
            evidence=f"raw_ready={bool(raw_health.get('ready'))}；blockers={', '.join(map(str, raw_blockers)) or 'none'}",
            action="接入授权 raw 或导入用户导出快照；如果 TAB 仍 route mismatch，则继续 unavailable，不用旧盘口生成建议。",
            verify="检查 raw_refresh_health_latest.json ready=true，且 portfolio/preflight 不再出现 stale_raw 或 route_mismatch。",
            allowed="只读抓取公开盘口、写入 diagnostics 和研究-only 报告。",
            forbidden="不点击赔率、不登录下注、不把 blocked raw 发布为最新正式日报。",
        ),
        playbook_item(
            "P0",
            2,
            "导入最新只读持仓快照",
            private_row,
            evidence=f"private_position_status={private_status}",
            action="从本地入口启动只读持仓读取；用户完成 TAB 授权后，只导入聚合快照并重跑日报门禁。",
            verify="检查 automation_readiness_latest.json private_position_bootstrap.ready=true，且 report_date 为当前报告日期。",
            allowed="只读读取 My Bets/余额聚合状态，公开报告只显示安全聚合值。",
            forbidden="不提交投注单、不修改账户、不在公开产物泄露账户明细或余额路径。",
        ),
        playbook_item(
            "P1",
            3,
            "补齐主动测试时间线缺口",
            cadence_row,
            evidence=(
                f"missing_analysis_days={timeline_summary.get('missing_analysis_day_count', 0)}；"
                f"missing_report_days={timeline_summary.get('missing_report_day_count', 0)}；"
                f"backfill_queue={timeline_summary.get('backfill_queue_count', 0)}"
            ),
            action="raw_ready=true 后运行 safe_no_latest_publish 补跑；历史补跑只标注 reconstruction，不覆盖 latest_commit。",
            verify="检查 active_timeline_report_latest.json cadence_ready_for_all_days=true 且 formal_report_ready_for_all_days=true。",
            allowed="补跑缺口分析和报告，保留时间线证据。",
            forbidden="不使用 stale/blocked raw 重建下注建议，不覆盖真实 latest success。",
        ),
        playbook_item(
            "P1",
            4,
            "重跑正式 PDF 日报门禁",
            pdf_row,
            evidence=str(pdf_row.get("evidence", "")),
            action="raw/private/preflight/public-safety 都通过后，重跑 daily report；通过后才复制为 Downloads/FIFA Report/DDMMYYYY.pdf。",
            verify="检查 latest_commit.json status=ready_for_manual_report，public_artifact_safety_ready=true，PDF QA 通过。",
            allowed="生成正式 PDF、dashboard、SQLite 记录和新旧对比。",
            forbidden="不在任一 P0 门禁失败时发布可执行新增下注金额。",
        ),
        playbook_item(
            "P2",
            5,
            "安装每日自动报告调度候选",
            scheduler_row,
            evidence=f"candidate={candidate.get('status', '')}；installed={bool(candidate.get('installed'))}",
            action="所有 P0/P1 门禁通过后，再由用户明确允许创建 recurring automation；allow_auto_betting 必须保持 false。",
            verify="检查 automation_candidate_latest.json activation_ready_after_authorization=true 且 recurring_automation_ready=true。",
            allowed="每日生成研究 PDF、Dashboard、数据库记录和缺口提醒。",
            forbidden="不自动下注、不点击赔率、不添加 Bet Slip。",
        ),
    ]


def playbook_item(
    priority: str,
    order: int,
    title: str,
    row: dict[str, Any],
    *,
    evidence: str,
    action: str,
    verify: str,
    allowed: str,
    forbidden: str,
) -> dict[str, Any]:
    status = str(row.get("status") or "blocked")
    return {
        "priority": priority,
        "order": order,
        "title": title,
        "linked_requirement_id": str(row.get("requirement_id") or ""),
        "status": status,
        "ready": status == "ready",
        "evidence": evidence,
        "action": "保持自动审计。" if status == "ready" else action,
        "verify": verify,
        "allowed_scope": allowed,
        "forbidden_scope": forbidden,
        "user_value": str(row.get("user_value") or ""),
    }


def persist_automation_maturity(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_maturity_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    average_score REAL NOT NULL DEFAULT 0,
                    required_ready_count INTEGER NOT NULL DEFAULT 0,
                    required_blocked_count INTEGER NOT NULL DEFAULT 0,
                    p0_blocker_count INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO automation_maturity_snapshots(
                    snapshot_id, generated_at, status, average_score,
                    required_ready_count, required_blocked_count, p0_blocker_count, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_payload.get("snapshot_id", ""),
                    public_payload.get("generated_at", ""),
                    str(executive.get("status") or ""),
                    float(summary.get("average_score") or 0),
                    int(summary.get("required_ready_count") or 0),
                    int(summary.get("required_blocked_count") or 0),
                    int(summary.get("p0_blocker_count") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "automation_maturity_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def old_new_compare(db_path: Path, summary: dict[str, Any], current_snapshot_id: str) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "score_delta": 0, "ready_delta": 0, "blocked_delta": 0}
    try:
        with connect_report_db(db_path) as conn:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='automation_maturity_snapshots'"
            ).fetchone()
            if not exists:
                return {"status": "no_previous_snapshot", "score_delta": 0, "ready_delta": 0, "blocked_delta": 0}
            row = conn.execute(
                """
                SELECT generated_at, status, average_score, required_ready_count, required_blocked_count, p0_blocker_count, payload_json
                FROM automation_maturity_snapshots
                WHERE snapshot_id != ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (current_snapshot_id,),
            ).fetchone()
    except sqlite3.Error:
        return {"status": "compare_unavailable", "score_delta": 0, "ready_delta": 0, "blocked_delta": 0}
    if not row:
        return {"status": "no_previous_snapshot", "score_delta": 0, "ready_delta": 0, "blocked_delta": 0}
    return {
        "status": "compared",
        "previous_generated_at": row["generated_at"],
        "previous_status": row["status"],
        "score_delta": round(float(summary.get("average_score") or 0) - float(row["average_score"] or 0), 4),
        "ready_delta": int(summary.get("required_ready_count") or 0) - int(row["required_ready_count"] or 0),
        "blocked_delta": int(summary.get("required_blocked_count") or 0) - int(row["required_blocked_count"] or 0),
        "p0_blocker_delta": int(summary.get("p0_blocker_count") or 0) - int(row["p0_blocker_count"] or 0),
    }


def render_automation_maturity_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    lines = [
        "# TAB FIFA Automation 成熟度验收矩阵",
        "",
        "本报告把用户目标拆成可验证验收项：自动爬虫、4小时节奏、每日PDF、本地数据库、新旧对比、图表/Dashboard、GitHub模型参考、下注推荐首页、持仓监控、fail-closed、安全边界和调度授权。",
        "",
        "## Executive Summary",
        "",
        f"- automation_ready: `{bool(executive.get('automation_ready'))}`",
        f"- status: `{executive.get('status', '')}`",
        f"- overall_score: `{pct(summary.get('average_score'))}`",
        f"- required_ready: `{summary.get('required_ready_count', 0)}/{summary.get('required_count', 0)}`",
        f"- primary_gap: `{executive.get('primary_gap', '')}`",
        f"- recommended_next_action: {executive.get('recommended_next_action', '')}",
        f"- old_new_compare: `{compare.get('status', '')}`；score_delta `{compare.get('score_delta', 0)}`；ready_delta `{compare.get('ready_delta', 0)}`；blocked_delta `{compare.get('blocked_delta', 0)}`",
        "",
        "## 新旧成熟度变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- score_delta: `{compare.get('score_delta', 0)}`",
        f"- ready_delta: `{compare.get('ready_delta', 0)}`",
        f"- blocked_delta: `{compare.get('blocked_delta', 0)}`",
        f"- p0_blocker_delta: `{compare.get('p0_blocker_delta', 0)}`",
        "",
        "## Visual Summary",
        "",
        "```mermaid",
        "pie showData",
        f"  \"ready\" : {summary.get('required_ready_count', 0)}",
        f"  \"blocked\" : {summary.get('required_blocked_count', 0)}",
        "```",
        "",
        "## 验收矩阵",
        "",
        "| 验收项 | 状态 | 得分 | 证据 | 缺口 | 下一步 |",
        "|---|---|---:|---|---|---|",
    ]
    for item in payload.get("rows") or []:
        lines.append(
            "| {title} | {status} | {score} | {evidence} | {gap} | {next_action} |".format(
                title=md(item.get("title")),
                status=md(item.get("status")),
                score=pct(item.get("score")),
                evidence=md(item.get("evidence")),
                gap=md(item.get("gap") or "无"),
                next_action=md(item.get("next_action")),
            )
        )
    lines.extend(
        [
            "",
            "## 人工复核队列",
            "",
        ]
    )
    for item in payload.get("manual_review_queue") or []:
        lines.append(f"- `{item.get('title', '')}`：{item.get('next_action', '')}")
    lines.extend(
        [
            "",
            "## Automation 恢复 Playbook",
            "",
            "| 优先级 | 步骤 | 状态 | 动作 | 验证 | 禁止范围 |",
            "|---|---:|---|---|---|---|",
        ]
    )
    for item in payload.get("automation_recovery_playbook") or []:
        lines.append(
            "| {priority} | {order} | {status} | {action} | {verify} | {forbidden} |".format(
                priority=md(item.get("priority")),
                order=md(item.get("order")),
                status=md(item.get("status")),
                action=md(item.get("action")),
                verify=md(item.get("verify")),
                forbidden=md(item.get("forbidden_scope")),
            )
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('automation_boundary_note', '')}"])
    return "\n".join(lines)


def write_automation_maturity_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("rows") or []
    playbook = payload.get("automation_recovery_playbook") or []
    compare = payload.get("old_new_compare") or {}
    ready_rows = [row for row in rows if row.get("status") == "ready"]
    blocked_rows = [row for row in rows if row.get("status") != "ready"]
    charts = [
        chart_from_items(
            "验收项状态",
            [("ready", len(ready_rows)), ("blocked", len(blocked_rows))],
            "#1F4E79",
        ),
        chart_from_items(
            "成熟度得分",
            [(row.get("title", ""), float(row.get("score") or 0) * 100) for row in rows],
            "#247A5A",
        ),
        chart_from_items(
            "P0阻塞",
            [("P0 blockers", summary.get("p0_blocker_count", 0)), ("Other gaps", max(0, len(blocked_rows) - int(summary.get("p0_blocker_count") or 0)))],
            "#C62828",
        ),
        chart_from_items(
            "报告系统能力",
            [
                ("database", score_for(rows, "local_database") * 100),
                ("compare", score_for(rows, "old_new_compare") * 100),
                ("visual", score_for(rows, "visual_reports_dashboard") * 100),
                ("models", score_for(rows, "open_source_models") * 100),
                ("entry", score_for(rows, "bet_recommendation_board") * 100),
            ],
            "#6A4C93",
        ),
        chart_from_items(
            "恢复优先级",
            [
                ("P0", sum(1 for item in playbook if item.get("priority") == "P0" and not item.get("ready"))),
                ("P1", sum(1 for item in playbook if item.get("priority") == "P1" and not item.get("ready"))),
                ("P2", sum(1 for item in playbook if item.get("priority") == "P2" and not item.get("ready"))),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Automation 成熟度验收矩阵",
        subtitle="面向每日自动报告的验收证据、缺口和下一步；只生成研究报告，不自动下注。",
        summary_rows=[
            ("automation_ready", str(bool(executive.get("automation_ready")))),
            ("status", str(executive.get("status", ""))),
            ("overall_score", pct(summary.get("average_score"))),
            ("required_ready", f"{summary.get('required_ready_count', 0)}/{summary.get('required_count', 0)}"),
            ("p0_blockers", str(summary.get("p0_blocker_count", 0))),
            ("primary_gap", str(executive.get("primary_gap", ""))),
            ("old_new_compare", f"{compare.get('status', '')}; score_delta={compare.get('score_delta', 0)}"),
        ],
        charts=charts,
        table_headers=["验收项", "状态", "得分", "下一步"],
        table_rows=[
            [
                str(row.get("title", "")),
                str(row.get("status", "")),
                pct(row.get("score")),
                str(row.get("next_action", "")),
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "人工复核队列",
                "headers": ["验收项", "缺口", "用户价值"],
                "rows": [
                    [str(row.get("title", "")), str(row.get("gap", "")), str(row.get("user_value", ""))]
                    for row in blocked_rows
                ],
            },
            {
                "title": "Automation 恢复 Playbook",
                "headers": ["优先级", "步骤", "状态", "动作", "验证"],
                "rows": [
                    [
                        str(item.get("priority", "")),
                        str(item.get("order", "")),
                        str(item.get("status", "")),
                        str(item.get("action", "")),
                        str(item.get("verify", "")),
                    ]
                    for item in playbook
                ],
            },
            {
                "title": "新旧成熟度变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["score_delta", str(compare.get("score_delta", 0))],
                    ["ready_delta", str(compare.get("ready_delta", 0))],
                    ["blocked_delta", str(compare.get("blocked_delta", 0))],
                    ["p0_blocker_delta", str(compare.get("p0_blocker_delta", 0))],
                ],
            }
        ],
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def database_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ready": False, "database": path.name, "run_count": 0, "automation_run_count": 0, "active_timeline_audit_count": 0}
    uri = f"file:{path.resolve()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        try:
            run_count = scalar_count(conn, "report_runs")
            automation_run_count = scalar_count(conn, "automation_runs")
            audit_count = scalar_count(conn, "active_timeline_audits")
        finally:
            conn.close()
    except sqlite3.Error:
        return {"ready": False, "database": path.name, "run_count": 0, "automation_run_count": 0, "active_timeline_audit_count": 0}
    return {
        "ready": run_count > 0,
        "database": path.name,
        "run_count": run_count,
        "automation_run_count": automation_run_count,
        "active_timeline_audit_count": audit_count,
    }


def scalar_count(conn: sqlite3.Connection, table: str) -> int:
    exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    if not exists:
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)


def downloads_entry_status() -> dict[str, Any]:
    entry = Path.home() / "Downloads" / "FIFA Report" / "TAB FIFA盘口研究系统.html"
    if not entry.exists():
        return {"ready": False, "file": entry.name, "artifact_link_count": 0, "recommendation_labels": {}}
    text = entry.read_text(encoding="utf-8", errors="ignore")
    labels = {
        label: label in text
        for label in ["时间", "板块", "盘口", "下注", "赔率", "金额", "分析一致性", "盘口价值", "EV", "概率赔率编辑", "置信度"]
    }
    return {
        "ready": "推荐下注板块" in text and "主动测试并自动补缺" in text,
        "file": entry.name,
        "artifact_link_count": len(re.findall(r"<a\\s+[^>]*href=", text)),
        "recommendation_labels": labels,
    }


def has_report_comparison(intelligence: dict[str, Any], report_index: dict[str, Any]) -> bool:
    comparison = intelligence.get("report_comparison") or {}
    if comparison:
        return True
    for run in report_index.get("runs") or []:
        if run.get("compare_summary"):
            return True
    return False


def compare_evidence(intelligence: dict[str, Any], report_index: dict[str, Any]) -> str:
    comparison = intelligence.get("report_comparison") or {}
    if comparison:
        return "added={added}；removed={removed}；changed={changed}；retained={retained}".format(
            added=comparison.get("added_count", 0),
            removed=comparison.get("removed_count", 0),
            changed=comparison.get("changed_count", 0),
            retained=comparison.get("retained_count", 0),
        )
    for run in report_index.get("runs") or []:
        compare = run.get("compare_summary") or {}
        if compare:
            return f"report_index compare_summary: changed={compare.get('changed_count', 0)}"
    return "缺少 report_comparison"


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def first_gap(rows: list[dict[str, Any]]) -> str:
    for item in rows:
        if item.get("status") != "ready":
            return str(item.get("title", ""))
    return "无"


def recommended_next_action(rows: list[dict[str, Any]]) -> str:
    for item in rows:
        if item.get("status") != "ready":
            return str(item.get("next_action", ""))
    return "保持自动生成并进入 scheduler evidence 验证。"


def score_for(rows: list[dict[str, Any]], requirement_id: str) -> float:
    for row in rows:
        if row.get("requirement_id") == requirement_id:
            return float(row.get("score") or 0)
    return 0.0


def pct(value: Any) -> str:
    try:
        return f"{float(value or 0) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")


def snapshot_id(generated_at: str) -> str:
    return "automation-maturity-" + re.sub(r"[^0-9A-Za-z]+", "-", str(generated_at)).strip("-")
