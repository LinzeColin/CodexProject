from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_copy, atomic_write_json, atomic_write_text
from .raw_refresh import normalize_partial_research_refresh
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


PARTIAL_DAILY_RESEARCH_JSON_LATEST = "partial_daily_research_latest.json"
PARTIAL_DAILY_RESEARCH_MD_LATEST = "partial_daily_research_latest.md"
PARTIAL_DAILY_RESEARCH_PDF_LATEST = "partial_daily_research_latest.pdf"
RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST = "raw_refresh_research_only_latest.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_partial_daily_research_bundle(output_dir: Path, report_date: str | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_partial_daily_research(output_dir, report_date=report_date)
    latest_json = output_dir / PARTIAL_DAILY_RESEARCH_JSON_LATEST
    latest_md = output_dir / PARTIAL_DAILY_RESEARCH_MD_LATEST
    latest_pdf = output_dir / PARTIAL_DAILY_RESEARCH_PDF_LATEST
    dated_json = output_dir / str(payload["dated_artifacts"]["json"])
    dated_md = output_dir / str(payload["dated_artifacts"]["markdown"])
    dated_pdf = output_dir / str(payload["dated_artifacts"]["pdf"])

    atomic_write_json(latest_json, payload)
    atomic_write_text(latest_md, render_partial_daily_research_markdown(payload))
    pdf_summary = write_partial_daily_research_pdf(payload, latest_pdf)
    atomic_copy(latest_json, dated_json)
    atomic_copy(latest_md, dated_md)
    atomic_copy(latest_pdf, dated_pdf)

    payload["artifacts"] = {
        "json": latest_json.name,
        "markdown": latest_md.name,
        "pdf": latest_pdf.name,
        "dated_json": dated_json.name,
        "dated_markdown": dated_md.name,
        "dated_pdf": dated_pdf.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(latest_json, payload)
    atomic_write_json(dated_json, payload)
    return payload


def build_partial_daily_research(output_dir: Path, report_date: str | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    now = datetime.now(REPORT_TZ)
    report_date = report_date or now.strftime("%d%m%Y")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    diagnostics = load_json(output_dir / "raw_refresh_diagnostics_latest.json")
    research_only_raw = load_json(output_dir / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST)
    live_discovery = load_json(output_dir / "live_board_discovery_latest.json")
    strategy = load_json(output_dir / "available_board_strategy_latest.json")
    raw_recovery = load_json(output_dir / "raw_refresh_recovery_latest.json")
    recommendation_ops = load_json(output_dir / "recommendation_operations_latest.json")
    raw_health_partial = normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {})
    research_only_partial = partial_from_research_only_manifest(research_only_raw)
    partial = choose_partial_research_evidence(raw_health_partial, research_only_partial)
    strategy_summary = strategy.get("summary") or {}
    strategy_exec = strategy.get("executive_status") or {}
    live_summary = live_discovery.get("summary") or {}
    recovery_summary = raw_recovery.get("summary") or {}
    ready = partial_daily_research_ready(partial, strategy_summary, live_summary)
    successful_names = [
        str(item.get("name") or item.get("board_id") or "")
        for item in partial.get("successful_boards") or []
    ]
    failed_names = [
        str(item.get("name") or item.get("board_id") or "")
        for item in partial.get("failed_boards") or []
    ]
    board_rows = build_board_rows(strategy.get("board_scope_rows") or [], partial)
    unavailable_names = [row["name"] for row in board_rows if row["board_scope"] == "unavailable_excluded"]
    payload = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "report_date": report_date,
        "report_type": "partial_daily_research",
        "mode": "research_only_no_execution",
        "title": f"{report_date} TAB FIFA盘口研究诊断日报",
        "purpose": "当 TAB 部分板块当前不可见时，仍生成每日研究诊断报告；不自动下注、不点击赔率、不使用旧盘口补齐缺失板块。",
        "executive_status": {
            "status": "ready_research_only" if ready else "blocked",
            "partial_daily_report_ready": ready,
            "automation_value": "可作为每日 automation 的研究诊断产物；不是可执行下注日报。",
            "execution_allowed": False,
            "current_executable_new_stake_aud": 0,
            "recommended_next_action": next_action(ready, unavailable_names),
        },
        "summary": {
            "partial_successful_board_count": int(partial.get("successful_board_count") or 0),
            "partial_attempted_board_count": int(partial.get("attempted_board_count") or 0),
            "partial_failed_board_count": int(partial.get("failed_board_count") or 0),
            "partial_freshness_status": partial.get("freshness_status", "missing"),
            "partial_fresh_within_sla": bool(partial.get("fresh_within_sla")),
            "partial_age_hours": partial.get("age_hours"),
            "partial_sla_hours": partial.get("freshness_sla_hours"),
            "partial_evidence_source": partial.get("selected_evidence_source", "raw_refresh_health_latest.json"),
            "research_only_raw_status": research_only_raw.get("status", "missing"),
            "research_only_raw_successful_board_count": int(research_only_raw.get("successful_board_count") or 0),
            "research_only_raw_failed_board_count": int(research_only_raw.get("failed_board_count") or 0),
            "research_only_raw_fresh_within_sla": bool(research_only_partial.get("fresh_within_sla")),
            "research_allowed_board_count": int(strategy_summary.get("research_allowed_board_count") or 0),
            "unavailable_board_count": int(strategy_summary.get("unavailable_board_count") or 0),
            "discovery_retry_board_count": int(strategy_summary.get("discovery_retry_board_count") or 0),
            "board_scope_source": strategy_summary.get("board_scope_source", "missing"),
            "board_scope_last_success_fallback_used": bool(strategy_summary.get("last_success_fallback_used")),
            "board_scope_last_success_fresh_within_sla": bool(strategy_summary.get("last_success_fresh_within_sla")),
            "board_scope_last_success_age_hours": strategy_summary.get("last_success_age_hours"),
            "current_discovery_quality_status": strategy_summary.get("current_discovery_quality_status", live_summary.get("quality_status", "missing")),
            "live_discovery_ready": bool(live_summary.get("discovery_ready")),
            "route_mismatch_active": bool(strategy_summary.get("route_mismatch_active") or live_summary.get("route_mismatch_active")),
            "raw_refresh_ready": bool(raw_health.get("ready")),
            "raw_diagnostics_status": diagnostics.get("status", "missing"),
            "recovery_auto_retry_count": int(recovery_summary.get("board_recovery_auto_retry_count") or 0),
            "recovery_unavailable_count": int(recovery_summary.get("board_recovery_unavailable_count") or 0),
            "recommendation_candidate_count": int((recommendation_ops.get("summary") or {}).get("candidate_count") or 0),
            "recommendation_executable_new_stake_aud": 0,
            "current_executable_new_stake_aud": 0,
        },
        "successful_board_names": successful_names,
        "failed_board_names": failed_names,
        "unavailable_board_names": unavailable_names,
        "board_rows": board_rows,
        "operation_policy": {
            "report_publish": "允许发布 research-only 诊断日报，前提是 partial raw fresh 且缺失板块有 live discovery/unavailable 证据。",
            "missing_board_policy": "缺失板块只能写 No Bet / unavailable review，不使用旧盘口补齐。",
            "stake_policy": "公开 raw、私有持仓、正式 preflight 未全量通过前，新增执行金额固定 AUD 0。",
            "automation_policy": "该产物可由每日 automation 定时生成；但它不能创建投注单，也不能替代人工复核。",
        },
        "source_artifacts": {
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "raw_refresh_diagnostics": "raw_refresh_diagnostics_latest.json" if diagnostics else "",
            "raw_refresh_research_only": RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST if research_only_raw else "",
            "live_board_discovery": "live_board_discovery_latest.json" if live_discovery else "",
            "available_board_strategy": "available_board_strategy_latest.json" if strategy else "",
            "raw_refresh_recovery": "raw_refresh_recovery_latest.json" if raw_recovery else "",
            "recommendation_operations": "recommendation_operations_latest.json" if recommendation_ops else "",
        },
        "dated_artifacts": {
            "json": f"{report_date}_partial_daily_research.json",
            "markdown": f"{report_date}_partial_daily_research.md",
            "pdf": f"{report_date}_partial_daily_research.pdf",
        },
        "truthfulness_note": "本报告只证明当前可研究范围和缺失板块状态；不证明完整自动化已达成。",
    }
    return sanitize_public_payload(payload)


def partial_from_research_only_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not manifest:
        return {}
    successful = [item for item in manifest.get("successful_boards") or [] if isinstance(item, dict)]
    failed = [item for item in manifest.get("failed_boards") or [] if isinstance(item, dict)]
    partial = {
        "status": "partial_ready" if successful and failed else "all_attempted_ready" if successful else "blocked",
        "research_only_allowed": bool(successful),
        "generated_at": manifest.get("generated_at", ""),
        "freshness_sla_hours": 4.0,
        "attempted_board_count": int(manifest.get("required_target_count") or len(successful) + len(failed)),
        "successful_board_count": int(manifest.get("successful_board_count") or len(successful)),
        "failed_board_count": int(manifest.get("failed_board_count") or len(failed)),
        "successful_boards": [
            {
                "refresh_board_id": item.get("refresh_board_id", ""),
                "board_id": item.get("board_id", ""),
                "name": item.get("name", ""),
                "raw_snapshot": item.get("raw_snapshot", ""),
                "research_only_raw_snapshot": item.get("research_only_raw_snapshot", ""),
            }
            for item in successful
        ],
        "failed_boards": [
            {
                "refresh_board_id": item.get("refresh_board_id", ""),
                "board_id": item.get("board_id", ""),
                "name": item.get("name", ""),
                "raw_snapshot": item.get("raw_snapshot", ""),
            }
            for item in failed
        ],
        "refresh_id": manifest.get("refresh_id", ""),
        "diagnostics_status": "research_only_staged_raw_sidecar",
        "note": "来自 raw_refresh_research_only_latest.json；只用于当日研究诊断，不允许下注执行。",
    }
    normalized = normalize_partial_research_refresh(partial)
    normalized["selected_evidence_source"] = RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST
    return normalized


def choose_partial_research_evidence(raw_health_partial: dict[str, Any], research_only_partial: dict[str, Any]) -> dict[str, Any]:
    raw_health_partial = dict(raw_health_partial or {})
    raw_health_partial.setdefault("selected_evidence_source", "raw_refresh_health_latest.json")
    if not research_only_partial:
        return raw_health_partial
    research_success = int(research_only_partial.get("successful_board_count") or 0)
    raw_success = int(raw_health_partial.get("successful_board_count") or 0)
    if research_only_partial.get("current_research_only_allowed") and (
        not raw_health_partial.get("current_research_only_allowed") or research_success >= raw_success
    ):
        return research_only_partial
    return raw_health_partial


def partial_daily_research_status(output_dir: Path) -> dict[str, Any]:
    payload = load_json(Path(output_dir) / PARTIAL_DAILY_RESEARCH_JSON_LATEST)
    return partial_daily_research_status_from_payload(payload)


def partial_daily_research_status_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return {
            "ready": False,
            "status": "missing",
            "report_date": "",
            "generated_at": "",
            "execution_allowed": False,
            "current_executable_new_stake_aud": 0,
            "partial_successful_board_count": 0,
            "partial_attempted_board_count": 0,
            "unavailable_board_count": 0,
            "freshness_status": "missing",
            "fresh_within_sla": False,
            "partial_evidence_source": "",
            "pdf": "",
            "dated_pdf": "",
            "recommended_next_action": "先生成 partial daily research 诊断日报。",
        }
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    artifacts = payload.get("artifacts") or {}
    return {
        "ready": bool(executive.get("partial_daily_report_ready")),
        "status": executive.get("status", "missing"),
        "report_date": payload.get("report_date", ""),
        "generated_at": payload.get("generated_at", ""),
        "execution_allowed": bool(executive.get("execution_allowed")),
        "current_executable_new_stake_aud": int(executive.get("current_executable_new_stake_aud") or 0),
        "partial_successful_board_count": int(summary.get("partial_successful_board_count") or 0),
        "partial_attempted_board_count": int(summary.get("partial_attempted_board_count") or 0),
        "unavailable_board_count": int(summary.get("unavailable_board_count") or 0),
        "board_scope_source": summary.get("board_scope_source", ""),
        "board_scope_last_success_fallback_used": bool(summary.get("board_scope_last_success_fallback_used")),
        "board_scope_last_success_fresh_within_sla": bool(summary.get("board_scope_last_success_fresh_within_sla")),
        "freshness_status": summary.get("partial_freshness_status", "missing"),
        "fresh_within_sla": bool(summary.get("partial_fresh_within_sla")),
        "partial_evidence_source": summary.get("partial_evidence_source", ""),
        "age_hours": summary.get("partial_age_hours"),
        "pdf": artifacts.get("pdf", ""),
        "dated_pdf": artifacts.get("dated_pdf", ""),
        "recommended_next_action": executive.get("recommended_next_action", ""),
    }


def partial_daily_research_ready(partial: dict[str, Any], strategy_summary: dict[str, Any], live_summary: dict[str, Any]) -> bool:
    research_scope_ready = int(strategy_summary.get("research_allowed_board_count") or 0) > 0 and bool(
        strategy_summary.get("research_diagnostic_allowed")
    )
    return bool(
        partial.get("current_research_only_allowed")
        and partial.get("fresh_within_sla")
        and int(partial.get("successful_board_count") or 0) > 0
        and research_scope_ready
        and int(strategy_summary.get("discovery_retry_board_count") or 0) == 0
    )


def build_board_rows(strategy_rows: list[dict[str, Any]], partial: dict[str, Any]) -> list[dict[str, Any]]:
    successful = {
        str(item.get("name") or item.get("board_id") or "")
        for item in partial.get("successful_boards") or []
        if isinstance(item, dict)
    }
    rows = []
    for item in strategy_rows:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        scope = str(item.get("board_scope") or "")
        has_fresh_partial = name in successful
        rows.append(
            {
                "board_id": item.get("board_id", ""),
                "name": name,
                "priority": item.get("priority", ""),
                "live_nav_status": item.get("live_nav_status", ""),
                "board_scope": scope,
                "partial_raw_fresh": has_fresh_partial,
                "research_action": research_action(scope, has_fresh_partial),
                "betting_action": "No Bet / 不下注",
                "stake_aud": 0,
                "reason": item.get("reason", ""),
                "next_action": item.get("next_action", ""),
            }
        )
    return rows


def research_action(scope: str, fresh: bool) -> str:
    if scope == "research_diagnostic_allowed" and fresh:
        return "纳入当日研究诊断"
    if scope == "research_diagnostic_allowed":
        return "等待 fresh raw 后纳入研究诊断"
    if scope == "discovery_retry_required":
        return "重试 discovery，暂不纳入"
    return "unavailable review，写入缺失说明"


def next_action(ready: bool, unavailable_names: list[str]) -> str:
    if ready and unavailable_names:
        return "每日 automation 可生成 research-only PDF；继续只读发现缺失板块，直到可恢复完整正式日报。"
    if ready:
        return "research-only PDF 可生成；下一步补齐正式 raw/private/preflight 门禁。"
    return "partial research 证据不足；先刷新公开 raw 与 live board discovery。"


def render_partial_daily_research_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    lines = [
        f"# {payload.get('title', 'TAB FIFA盘口研究诊断日报')}",
        "",
        "本报告是每日 automation 的研究诊断产物；不自动下注、不点击赔率、不加入投注单。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- partial_daily_report_ready: `{bool(executive.get('partial_daily_report_ready'))}`",
        f"- successful boards: `{summary.get('partial_successful_board_count', 0)}/{summary.get('partial_attempted_board_count', 0)}`",
        f"- unavailable boards: `{summary.get('unavailable_board_count', 0)}`",
        f"- board scope source: `{summary.get('board_scope_source', 'missing')}` / fallback `{bool(summary.get('board_scope_last_success_fallback_used'))}` / fresh `{bool(summary.get('board_scope_last_success_fresh_within_sla'))}` / current discovery `{summary.get('current_discovery_quality_status', 'missing')}`",
        f"- partial freshness: `{summary.get('partial_freshness_status', '')}` / age `{summary.get('partial_age_hours', 'n/a')}`h",
        f"- partial evidence source: `{summary.get('partial_evidence_source', '')}`",
        f"- research-only staged raw: `{summary.get('research_only_raw_status', 'missing')}` / success `{summary.get('research_only_raw_successful_board_count', 0)}`",
        f"- raw diagnostics: `{summary.get('raw_diagnostics_status', '')}`",
        f"- current_executable_new_stake_aud: `AUD {summary.get('current_executable_new_stake_aud', 0)}`",
        f"- 下一步: {md(executive.get('recommended_next_action'))}",
        "",
        "## Board Research Scope",
        "",
        "| 板块 | Live nav | 范围 | Fresh raw | 研究动作 | 下注动作 | 金额 | 原因 |",
        "|---|---|---|---:|---|---|---:|---|",
    ]
    for row in payload.get("board_rows") or []:
        lines.append(
            "| {name} | {live} | {scope} | {fresh} | {research} | {betting} | {stake} | {reason} |".format(
                name=md(row.get("name")),
                live=md(row.get("live_nav_status")),
                scope=md(row.get("board_scope")),
                fresh="是" if row.get("partial_raw_fresh") else "否",
                research=md(row.get("research_action")),
                betting=md(row.get("betting_action")),
                stake=md(row.get("stake_aud")),
                reason=md(row.get("reason")),
            )
        )
    lines.extend(["", "## Operation Policy", ""])
    for key, value in (payload.get("operation_policy") or {}).items():
        lines.append(f"- **{md(key)}**: {md(value)}")
    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for key, value in (payload.get("source_artifacts") or {}).items():
        lines.append(f"- {md(key)}: `{md(value)}`")
    return "\n".join(lines)


def write_partial_daily_research_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("board_rows") or []
    charts = [
        chart_from_items(
            "Partial raw boards",
            [
                ("success", summary.get("partial_successful_board_count", 0)),
                ("failed", summary.get("partial_failed_board_count", 0)),
                ("attempted", summary.get("partial_attempted_board_count", 0)),
            ],
            "#1F4E79",
        ),
        chart_from_items(
            "Report scope",
            [
                ("research", summary.get("research_allowed_board_count", 0)),
                ("unavailable", summary.get("unavailable_board_count", 0)),
                ("retry", summary.get("discovery_retry_board_count", 0)),
            ],
            "#247A5A",
        ),
        chart_from_items(
            "Execution gate",
            [
                ("raw ready", 1 if summary.get("raw_refresh_ready") else 0),
                ("route mismatch", 1 if summary.get("route_mismatch_active") else 0),
                ("new stake", summary.get("current_executable_new_stake_aud") or 0),
            ],
            "#A56710",
        ),
        chart_from_items(
            "Recovery",
            [
                ("auto retry", summary.get("recovery_auto_retry_count", 0)),
                ("unavailable", summary.get("recovery_unavailable_count", 0)),
            ],
            "#6A4C93",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title=str(payload.get("title") or "TAB FIFA盘口研究诊断日报"),
        subtitle="Research-only daily report for partial TAB board availability. No auto betting, no odds clicks, no wagering slip mutation.",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("partial ready", str(bool(executive.get("partial_daily_report_ready")))),
            ("successful boards", f"{summary.get('partial_successful_board_count', 0)}/{summary.get('partial_attempted_board_count', 0)}"),
            ("unavailable boards", str(summary.get("unavailable_board_count", 0))),
            ("board scope source", f"{summary.get('board_scope_source', 'missing')} / fallback {summary.get('board_scope_last_success_fallback_used')} / fresh {summary.get('board_scope_last_success_fresh_within_sla')}"),
            ("current discovery", str(summary.get("current_discovery_quality_status", "missing"))),
            ("freshness", str(summary.get("partial_freshness_status", ""))),
            ("evidence source", str(summary.get("partial_evidence_source", ""))),
            ("research-only staged raw", f"{summary.get('research_only_raw_status', 'missing')} / {summary.get('research_only_raw_successful_board_count', 0)}"),
            ("raw diagnostics", str(summary.get("raw_diagnostics_status", ""))),
            ("new executable stake", f"AUD {summary.get('current_executable_new_stake_aud', 0)}"),
            ("next action", str(executive.get("recommended_next_action", ""))),
        ],
        charts=charts,
        table_headers=["板块", "live", "范围", "fresh", "研究动作", "下注动作"],
        table_rows=[
            [
                str(row.get("name", "")),
                str(row.get("live_nav_status", "")),
                str(row.get("board_scope", "")),
                "是" if row.get("partial_raw_fresh") else "否",
                str(row.get("research_action", "")),
                str(row.get("betting_action", "")),
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "Operation Policy",
                "headers": ["策略", "内容"],
                "rows": [[key, str(value)] for key, value in (payload.get("operation_policy") or {}).items()],
            },
            {
                "title": "Source Artifacts",
                "headers": ["Artifact", "File"],
                "rows": [[key, str(value)] for key, value in (payload.get("source_artifacts") or {}).items()],
            },
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


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
