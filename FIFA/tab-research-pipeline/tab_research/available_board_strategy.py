from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .boards import BOARD_CONFIGS
from .io import atomic_write_json, atomic_write_text
from .partial_daily_research import (
    RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST,
    choose_partial_research_evidence,
    partial_from_research_only_manifest,
)
from .raw_refresh import normalize_partial_research_refresh
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


AVAILABLE_BOARD_STRATEGY_JSON_LATEST = "available_board_strategy_latest.json"
AVAILABLE_BOARD_STRATEGY_MD_LATEST = "available_board_strategy_latest.md"
AVAILABLE_BOARD_STRATEGY_PDF_LATEST = "available_board_strategy_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_available_board_strategy_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_available_board_strategy(output_dir, db_path)
    json_path = output_dir / AVAILABLE_BOARD_STRATEGY_JSON_LATEST
    md_path = output_dir / AVAILABLE_BOARD_STRATEGY_MD_LATEST
    pdf_path = output_dir / AVAILABLE_BOARD_STRATEGY_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_available_board_strategy_markdown(payload))
    pdf_summary = write_available_board_strategy_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_available_board_strategy(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_available_board_strategy(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    live_discovery = load_json(output_dir / "live_board_discovery_latest.json")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    research_only_raw = load_json(output_dir / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST)
    partial = choose_partial_research_evidence(
        normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {}),
        partial_from_research_only_manifest(research_only_raw),
    )
    if raw_health:
        raw_health = dict(raw_health)
        raw_health["partial_research_refresh"] = partial
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    active_timeline = load_json(output_dir / "active_timeline_report_latest.json") or load_json(output_dir / "active_timeline_latest.json")
    previous = latest_available_board_strategy(db_path)
    latest_success = latest_available_board_strategy(db_path, usable_only=True)

    current_rows = build_board_scope_rows(live_discovery)
    current_discovery_summary = live_discovery.get("summary") or {}
    current_discovery_ready = bool(current_discovery_summary.get("discovery_ready", bool(live_discovery)))
    now = datetime.now(REPORT_TZ)
    fallback = build_last_success_fallback(latest_success, generated_at=now)
    fallback_used = bool(not current_discovery_ready and fallback.get("usable"))
    rows = build_fallback_rows(current_rows, fallback) if fallback_used else current_rows
    rows = apply_partial_raw_scope(rows, partial)
    partial_scope_success_count = len([row for row in rows if row.get("partial_raw_evidence") == "success"])
    partial_scope_failure_count = len([row for row in rows if row.get("partial_raw_evidence") == "failure"])
    board_scope_source = "last_success_fallback" if fallback_used else "current_discovery"
    if partial_scope_success_count and not fallback_used:
        board_scope_source = "current_discovery+partial_raw_success"
    elif partial_scope_success_count and fallback_used:
        board_scope_source = "last_success_fallback+partial_raw_success"
    listed_rows = [row for row in rows if row["board_scope"] == "research_diagnostic_allowed"]
    missing_rows = [row for row in rows if row["board_scope"] == "unavailable_excluded"]
    retry_rows = [row for row in rows if row["board_scope"] == "discovery_retry_required"]
    raw_ready = raw_health.get("ready") is True
    formal_ready = readiness.get("formal_report_publish_ready") is True
    full_live_ready = bool(rows) and not missing_rows and not retry_rows
    research_allowed = bool(listed_rows)
    executable_allowed = full_live_ready and raw_ready and formal_ready
    status = strategy_status(rows, listed_rows, missing_rows, retry_rows, raw_ready, formal_ready)
    generated_at = now.isoformat()
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "strategy_id": strategy_id(generated_at),
        "mode": "available_board_strategy_dashboard",
        "purpose": "根据 TAB live board discovery 判断当前哪些 FIFA 板块可进入研究诊断，哪些必须排除；只生成报告，不自动下注。",
        "executive_status": {
            "status": status,
            "decision": strategy_decision(status),
            "current_action": current_action(status, executable_allowed),
            "executable_report_allowed": executable_allowed,
            "research_diagnostic_allowed": research_allowed,
            "recommended_next_action": recommended_next_action(status, missing_rows, retry_rows, raw_ready, formal_ready),
        },
        "summary": {
            "expected_board_count": len(rows),
            "research_allowed_board_count": len(listed_rows),
            "unavailable_board_count": len(missing_rows),
            "discovery_retry_board_count": len(retry_rows),
            "discovery_ready": current_discovery_ready,
            "current_discovery_quality_status": current_discovery_summary.get("quality_status", "missing"),
            "board_scope_source": board_scope_source,
            "last_success_fallback_used": fallback_used,
            "last_success_fallback_status": fallback.get("status", "not_available"),
            "last_success_generated_at": fallback.get("generated_at", ""),
            "last_success_age_hours": fallback.get("age_hours"),
            "last_success_fresh_within_sla": bool(fallback.get("fresh_within_sla")),
            "last_success_sla_hours": fallback.get("sla_hours"),
            "listed_expected_count": len(listed_rows),
            "missing_expected_count": len(missing_rows),
            "route_mismatch_active": route_mismatch_active(live_discovery, raw_health),
            "raw_refresh_ready": raw_ready,
            "partial_refresh_status": partial.get("status", "not_attempted"),
            "partial_refresh_freshness_status": partial.get("freshness_status", "missing"),
            "partial_refresh_fresh_within_sla": bool(partial.get("fresh_within_sla")),
            "partial_refresh_current_research_allowed": bool(partial.get("current_research_only_allowed")),
            "partial_evidence_source": partial.get("selected_evidence_source", "raw_refresh_health_latest.json"),
            "partial_refresh_age_hours": partial.get("age_hours"),
            "partial_refresh_sla_hours": partial.get("freshness_sla_hours"),
            "partial_refresh_successful_board_count": int(partial.get("successful_board_count") or 0),
            "partial_refresh_attempted_board_count": int(partial.get("attempted_board_count") or 0),
            "research_only_raw_status": research_only_raw.get("status", "missing"),
            "research_only_raw_successful_board_count": int(research_only_raw.get("successful_board_count") or 0),
            "research_only_raw_failed_board_count": int(research_only_raw.get("failed_board_count") or 0),
            "research_only_raw_attempt_warning_count": int(research_only_raw.get("attempt_warning_count") or 0),
            "partial_raw_scope_success_count": partial_scope_success_count,
            "partial_raw_scope_failure_count": partial_scope_failure_count,
            "formal_report_publish_ready": formal_ready,
            "research_diagnostic_allowed": research_allowed,
            "executable_report_allowed": executable_allowed,
            "current_executable_new_stake_aud": 0 if not executable_allowed else None,
            "active_timeline_status": (active_timeline.get("executive_status") or {}).get("status", active_timeline.get("status", "missing")),
        },
        "board_scope_rows": rows,
        "current_discovery_board_scope_rows": current_rows,
        "last_success_fallback": public_fallback_summary(fallback),
        "available_research_boards": [row for row in rows if row["board_scope"] == "research_diagnostic_allowed"],
        "excluded_boards": [row for row in rows if row["board_scope"] == "unavailable_excluded"],
        "discovery_retry_boards": [row for row in rows if row["board_scope"] == "discovery_retry_required"],
        "old_new_compare": build_old_new_compare(previous, status, rows),
        "operation_policy": {
            "betting_operation": "不自动下注；不点击赔率；不加入 Bet Slip。",
            "when_partial_boards_available": "只允许 live listed 或 4小时SLA内 research-only raw 已通过 staged gate 的板块进入研究诊断，不允许发布当前可执行新增下注日报。",
            "last_success_fallback_policy": "当前 discovery 被 Access Denied 阻断时，4小时内 last-success 只可用于研究范围延续；不能解锁新增下注执行金额。",
            "partial_raw_freshness_policy": "partial raw fresh 只证明部分板块有 4 小时内研究证据；它不能替代 5/5 required raw、私有持仓和日报发布门禁。",
            "stake_policy": "live/raw/private/preflight 任一门禁未通过时，新增执行金额保持 AUD 0；旧报告买入项只能作为研究候选复核。",
            "time_effect_note": "后续胜负会影响余额与预算；但当前 live scope 不完整时，不能为了提高资金利用率而使用缺失板块的旧盘口。",
        },
        "partial_raw_freshness": build_partial_raw_freshness(partial),
        "source_artifacts": {
            "live_board_discovery": "live_board_discovery_latest.json" if live_discovery else "",
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "raw_refresh_research_only": RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST if research_only_raw else "",
            "automation_readiness": "automation_readiness_latest.json" if readiness else "",
            "active_timeline": "active_timeline_report_latest.json" if active_timeline else "",
        },
        "truthfulness_note": "该策略解决“部分板块可见”的报告范围问题；它不是下注执行指令，也不会绕过正式日报门禁。",
    }
    return sanitize_public_payload(payload)


def build_board_scope_rows(live_discovery: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        str(row.get("board_id") or ""): row
        for row in live_discovery.get("expected_board_rows") or []
        if isinstance(row, dict)
    }
    rows = []
    for board in BOARD_CONFIGS:
        source = by_id.get(board.board_id) or {}
        live_status = str(source.get("live_nav_status") or "discovery_missing")
        decision = str(source.get("automation_decision") or "")
        listed = live_status == "listed"
        retry_required = live_status == "discovery_blocked" or decision == "discovery_retry_required"
        scope = "research_diagnostic_allowed" if listed else "discovery_retry_required" if retry_required else "unavailable_excluded"
        rows.append(
            {
                "board_id": board.board_id,
                "name": board.name,
                "priority": board.priority,
                "live_nav_status": live_status,
                "matched_link_count": int(source.get("matched_link_count") or 0),
                "board_scope": scope,
                "report_usage": report_usage(scope),
                "executable_usage": executable_usage(scope),
                "amount_policy": "仅研究诊断；完整门禁通过前不新增执行金额" if listed else "新增执行金额 AUD 0，直到完整门禁恢复",
                "reason": board_reason(board.name, scope, live_status),
                "next_action": next_action_for_scope(scope),
                "scope_source": "current_discovery",
            }
        )
    return rows


def apply_partial_raw_scope(rows: list[dict[str, Any]], partial: dict[str, Any]) -> list[dict[str, Any]]:
    if not partial.get("current_research_only_allowed"):
        return rows
    success_ids = {
        str(item.get("board_id") or "")
        for item in (partial.get("successful_boards") or [])
        if isinstance(item, dict) and item.get("board_id")
    }
    failed_ids = {
        str(item.get("board_id") or "")
        for item in (partial.get("failed_boards") or [])
        if isinstance(item, dict) and item.get("board_id")
    }
    if not success_ids and not failed_ids:
        return rows
    updated = []
    for row in rows:
        item = dict(row)
        board_id = str(item.get("board_id") or "")
        if board_id in success_ids:
            item["board_scope"] = "research_diagnostic_allowed"
            item["report_usage"] = (
                "4小时SLA内 research-only raw 已通过 staged gate，可进入研究诊断；"
                "仍不能发布当前可执行下注日报。"
            )
            item["executable_usage"] = "不可执行；正式 raw/private/preflight 门禁未全部通过。"
            item["amount_policy"] = "research-only raw 仅支持研究诊断；新增执行金额 AUD 0"
            item["reason"] = (
                f"{item.get('name', '').replace('2026 World Cup ', '')} 已在 partial raw 中成功抓取并通过验证；"
                "当前只允许 No-execution 研究使用。"
            )
            item["next_action"] = "使用 research-only raw 进入研究诊断；继续修复正式 raw 门禁"
            item["scope_source"] = "partial_raw_success"
            item["partial_raw_evidence"] = "success"
        elif board_id in failed_ids:
            item["board_scope"] = "unavailable_excluded"
            item["report_usage"] = "partial raw 本轮未能取得该板块；只能写 No Bet / unavailable review。"
            item["executable_usage"] = "不可执行，不纳入金额分配。"
            item["amount_policy"] = "新增执行金额 AUD 0，直到 live/deep link/raw 重新恢复"
            item["reason"] = (
                f"{item.get('name', '').replace('2026 World Cup ', '')} 在 partial raw 本轮失败；"
                "不得使用旧盘口补齐。"
            )
            item["next_action"] = "保留 unavailable review queue；等待 TAB 重新列出或 deep link 恢复"
            item["scope_source"] = "partial_raw_failure"
            item["partial_raw_evidence"] = "failure"
        updated.append(item)
    return updated


def build_last_success_fallback(previous: dict[str, Any] | None, generated_at: datetime, sla_hours: float = 4.0) -> dict[str, Any]:
    if not previous:
        return {
            "status": "not_available",
            "usable": False,
            "generated_at": "",
            "age_hours": None,
            "fresh_within_sla": False,
            "sla_hours": sla_hours,
            "research_allowed_board_count": 0,
            "payload": {},
            "note": "没有可用的上一份成功板块范围快照。",
        }
    previous_generated_at = parse_datetime(previous.get("generated_at"))
    payload = previous.get("payload") if isinstance(previous.get("payload"), dict) else {}
    previous_rows = payload.get("board_scope_rows") or []
    research_count = len([row for row in previous_rows if isinstance(row, dict) and row.get("board_scope") == "research_diagnostic_allowed"])
    if previous_generated_at is None:
        return {
            "status": "timestamp_unparseable",
            "usable": False,
            "generated_at": str(previous.get("generated_at") or ""),
            "age_hours": None,
            "fresh_within_sla": False,
            "sla_hours": sla_hours,
            "research_allowed_board_count": research_count,
            "payload": {},
            "note": "上一份成功板块范围缺少可验证时间戳，不能用于 fallback。",
        }
    age_hours = max(0.0, (generated_at - previous_generated_at).total_seconds() / 3600)
    fresh = age_hours <= sla_hours
    usable = bool(fresh and research_count > 0)
    return {
        "status": "fresh_last_success" if usable else "stale_or_empty_last_success",
        "usable": usable,
        "generated_at": str(previous.get("generated_at") or ""),
        "age_hours": round(age_hours, 2),
        "fresh_within_sla": fresh,
        "sla_hours": sla_hours,
        "research_allowed_board_count": research_count,
        "source_strategy_id": str(previous.get("strategy_id") or ""),
        "payload": payload if usable else {},
        "note": (
            "当前 discovery 被阻断时，使用仍在4小时SLA内的上一份成功范围做研究-only 延续。"
            if usable
            else "上一份成功范围不可用或已超过4小时SLA。"
        ),
    }


def build_fallback_rows(current_rows: list[dict[str, Any]], fallback: dict[str, Any]) -> list[dict[str, Any]]:
    previous_payload = fallback.get("payload") if isinstance(fallback.get("payload"), dict) else {}
    previous_rows = previous_payload.get("board_scope_rows") or []
    previous_by_id = {str(row.get("board_id") or ""): row for row in previous_rows if isinstance(row, dict)}
    rows = []
    for current in current_rows:
        previous = dict(previous_by_id.get(str(current.get("board_id") or ""), current))
        previous["scope_source"] = "last_success_fallback"
        previous["current_discovery_live_nav_status"] = current.get("live_nav_status", "")
        previous["current_discovery_scope"] = current.get("board_scope", "")
        previous["fallback_generated_at"] = fallback.get("generated_at", "")
        previous["fallback_age_hours"] = fallback.get("age_hours")
        previous["report_usage"] = (
            f"{previous.get('report_usage', '')} 当前 discovery 被阻断，本行沿用4小时内 last-success 研究范围；不解锁执行金额。"
        ).strip()
        previous["executable_usage"] = "不可执行；当前 discovery/raw/private 门禁未全部通过。"
        previous["amount_policy"] = "last-success 仅研究延续；新增执行金额 AUD 0"
        previous["reason"] = (
            f"{previous.get('reason', '')} 当前 headless discovery 状态为 {current.get('live_nav_status', '')}，"
            f"使用 {fallback.get('generated_at', '')} 的成功范围作为研究-only fallback。"
        ).strip()
        rows.append(previous)
    return rows


def public_fallback_summary(fallback: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in fallback.items() if key != "payload"}


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=REPORT_TZ)
    return parsed.astimezone(REPORT_TZ)


def strategy_status(
    rows: list[dict[str, Any]],
    listed_rows: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
    retry_rows: list[dict[str, Any]],
    raw_ready: bool,
    formal_ready: bool,
) -> str:
    if retry_rows:
        return "blocked"
    if not rows or not listed_rows:
        return "blocked"
    if not missing_rows and raw_ready and formal_ready:
        return "full_scope_ready"
    return "research_only"


def strategy_decision(status: str) -> str:
    if status == "full_scope_ready":
        return "live scope 完整且日报门禁通过，可进入人工复核后的可执行下注日报。"
    if status == "research_only":
        return "部分板块可研究，但当前不允许发布新增下注执行结论。"
    return "live board discovery 证据不足或质量门禁失败，暂停当前研究范围扩张。"


def current_action(status: str, executable_allowed: bool) -> str:
    if executable_allowed:
        return "按正式日报执行清单人工复核"
    if status == "research_only":
        return "只看可用板块研究诊断；新增执行金额 AUD 0"
    return "先重新发现 TAB live board list"


def recommended_next_action(
    status: str,
    missing_rows: list[dict[str, Any]],
    retry_rows: list[dict[str, Any]],
    raw_ready: bool,
    formal_ready: bool,
) -> str:
    if status == "full_scope_ready":
        return "接入授权 raw 或导入用户导出快照后重跑正式日报，并核对私有持仓与预算。"
    if retry_rows:
        return "当前 discovery 质量门禁失败；TAB 拒绝 AI controlled access 时不切换 headed 自动访问，只等待授权数据源或用户导出导入，质量通过后再判断板块是否缺失。"
    if missing_rows:
        names = "、".join(row["name"].replace("2026 World Cup ", "") for row in missing_rows[:3])
        return f"当前排除缺失板块：{names}；先继续 discovery/raw 恢复，不发布新增下注。"
    if not raw_ready:
        return "live scope 无缺口但 raw refresh 未就绪；先接入授权 raw 或导入用户导出快照。"
    if not formal_ready:
        return "live/raw 已可用但正式日报门禁未通过；先补私有持仓与日报门禁。"
    return "保持只读检测，并等待下一次日报。"


def report_usage(scope: str) -> str:
    if scope == "research_diagnostic_allowed":
        return "可进入研究诊断和候选池，但仍受公开盘口、私有持仓、日报发布门禁约束。"
    if scope == "discovery_retry_required":
        return "Discovery 质量门禁失败；不能判断该板块是否真实缺失，需重试只读发现。"
    return "从当前研究范围和执行建议中排除；不得使用旧盘口替代。"


def executable_usage(scope: str) -> str:
    if scope == "research_diagnostic_allowed":
        return "仅当 5/5 目标板块、公开盘口、私有持仓、发布门禁全部通过后才可执行。"
    if scope == "discovery_retry_required":
        return "不可执行；先修复 discovery 质量门禁，不纳入金额分配。"
    return "不可执行，不纳入金额分配。"


def board_reason(name: str, scope: str, live_status: str) -> str:
    short_name = name.replace("2026 World Cup ", "")
    if scope == "research_diagnostic_allowed":
        return f"{short_name} 当前在 TAB live 导航中可见，可继续只读抓取和研究诊断。"
    if scope == "discovery_retry_required":
        return f"{short_name} 当前 discovery 状态为 {live_status}，不能判断是否下架；需重试只读发现。"
    return f"{short_name} 当前状态为 {live_status}，不能用旧盘口生成当前下注建议。"


def next_action_for_scope(scope: str) -> str:
    if scope == "research_diagnostic_allowed":
        return "进入只读 raw refresh / 研究诊断"
    if scope == "discovery_retry_required":
        return "等待授权数据源或用户导出导入；不使用 headed fallback"
    return "保留 unavailable review queue；等待 TAB 重新列出或重新发现"


def route_mismatch_active(live_discovery: dict[str, Any], raw_health: dict[str, Any]) -> bool:
    summary = live_discovery.get("summary") or {}
    if summary.get("route_mismatch_active"):
        return True
    return "route_mismatch" in (raw_health.get("blocker_codes") or [])


def build_partial_raw_freshness(partial: dict[str, Any]) -> dict[str, Any]:
    successful = partial.get("successful_boards") or []
    failed = partial.get("failed_boards") or []
    return {
        "status": partial.get("status", "not_attempted"),
        "freshness_status": partial.get("freshness_status", "missing"),
        "fresh_within_sla": bool(partial.get("fresh_within_sla")),
        "freshness_sla_hours": partial.get("freshness_sla_hours"),
        "generated_at": partial.get("generated_at", ""),
        "age_hours": partial.get("age_hours"),
        "research_only_allowed": bool(partial.get("research_only_allowed")),
        "current_research_only_allowed": bool(partial.get("current_research_only_allowed")),
        "historical_research_evidence_available": bool(partial.get("historical_research_evidence_available")),
        "execution_allowed": False,
        "successful_board_count": int(partial.get("successful_board_count") or 0),
        "attempted_board_count": int(partial.get("attempted_board_count") or 0),
        "successful_board_names": [str(item.get("name") or item.get("board_id") or "") for item in successful],
        "failed_board_names": [str(item.get("name") or item.get("board_id") or "") for item in failed],
        "note": "Partial raw 只允许研究诊断，不解锁新增下注执行金额。",
    }


def build_old_new_compare(previous: dict[str, Any] | None, status: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    current_listed = sorted(row["name"] for row in rows if row["board_scope"] == "research_diagnostic_allowed")
    current_missing = sorted(row["name"] for row in rows if row["board_scope"] == "unavailable_excluded")
    if not previous:
        return {
            "status": "no_previous_snapshot",
            "previous_generated_at": "",
            "current_status": status,
            "listed_count_delta": len(current_listed),
            "missing_count_delta": len(current_missing),
            "newly_listed": current_listed,
            "newly_missing": current_missing,
            "summary": "首次生成可用板块策略快照，后续日报会与该快照对比。",
        }
    previous_payload = previous.get("payload") or {}
    previous_rows = previous_payload.get("board_scope_rows") or []
    previous_listed = sorted(row.get("name", "") for row in previous_rows if row.get("board_scope") == "research_diagnostic_allowed")
    previous_missing = sorted(row.get("name", "") for row in previous_rows if row.get("board_scope") == "unavailable_excluded")
    previous_status = str(previous.get("status") or (previous_payload.get("executive_status") or {}).get("status") or "")
    newly_listed = sorted(set(current_listed) - set(previous_listed))
    newly_missing = sorted(set(current_missing) - set(previous_missing))
    return {
        "status": "compared_with_previous_snapshot",
        "previous_generated_at": previous.get("generated_at", ""),
        "previous_status": previous_status,
        "current_status": status,
        "status_changed": previous_status != status,
        "listed_count_delta": len(current_listed) - len(previous_listed),
        "missing_count_delta": len(current_missing) - len(previous_missing),
        "newly_listed": newly_listed,
        "newly_missing": newly_missing,
        "summary": compare_summary(previous_status, status, newly_listed, newly_missing),
    }


def compare_summary(previous_status: str, status: str, newly_listed: list[str], newly_missing: list[str]) -> str:
    changes = []
    if previous_status != status:
        changes.append(f"状态从 {previous_status or 'unknown'} 变为 {status}")
    if newly_listed:
        changes.append("新增可研究：" + "、".join(name.replace("2026 World Cup ", "") for name in newly_listed[:3]))
    if newly_missing:
        changes.append("新增缺失：" + "、".join(name.replace("2026 World Cup ", "") for name in newly_missing[:3]))
    return "；".join(changes) if changes else "与上一版策略范围一致。"


def persist_available_board_strategy(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO available_board_strategy_snapshots(
                    strategy_id, generated_at, status, listed_expected_count, missing_expected_count,
                    route_mismatch_active, executable_report_allowed, research_diagnostic_allowed, payload_json
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(public_payload.get("strategy_id") or ""),
                    str(public_payload.get("generated_at") or ""),
                    str(executive.get("status") or ""),
                    int(summary.get("listed_expected_count") or 0),
                    int(summary.get("missing_expected_count") or 0),
                    1 if summary.get("route_mismatch_active") else 0,
                    1 if executive.get("executable_report_allowed") else 0,
                    1 if executive.get("research_diagnostic_allowed") else 0,
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {
            "status": "stored",
            "database": Path(db_path).name,
            "table": "available_board_strategy_snapshots",
            "strategy_id": str(public_payload.get("strategy_id") or ""),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "database": Path(db_path).name,
            "table": "available_board_strategy_snapshots",
            "error": str(exc).splitlines()[0][:180],
        }


def latest_available_board_strategy(db_path: Path, usable_only: bool = False) -> dict[str, Any] | None:
    if not Path(db_path).exists():
        return None
    try:
        with connect_report_db(db_path) as conn:
            where = "WHERE research_diagnostic_allowed = 1 AND listed_expected_count > 0" if usable_only else ""
            row = conn.execute(
                f"""
                SELECT strategy_id, generated_at, status, listed_expected_count, missing_expected_count,
                       route_mismatch_active, executable_report_allowed, research_diagnostic_allowed, payload_json
                FROM available_board_strategy_snapshots
                {where}
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except Exception:
        return None
    if not row:
        return None
    payload = {}
    try:
        payload = json.loads(row["payload_json"] or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "strategy_id": row["strategy_id"],
        "generated_at": row["generated_at"],
        "status": row["status"],
        "listed_expected_count": row["listed_expected_count"],
        "missing_expected_count": row["missing_expected_count"],
        "route_mismatch_active": bool(row["route_mismatch_active"]),
        "executable_report_allowed": bool(row["executable_report_allowed"]),
        "research_diagnostic_allowed": bool(row["research_diagnostic_allowed"]),
        "payload": payload if isinstance(payload, dict) else {},
    }


def render_available_board_strategy_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    partial = payload.get("partial_raw_freshness") or {}
    fallback = payload.get("last_success_fallback") or {}
    lines = [
        "# TAB FIFA 可用板块策略 Dashboard",
        "",
        "本报告把 TAB live discovery 结果转换为报告范围和下注研究策略；只读，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- 当前动作: {md(executive.get('current_action'))}",
        f"- 可研究板块: `{summary.get('research_allowed_board_count', 0)}/{summary.get('expected_board_count', 0)}`",
        f"- scope source: `{summary.get('board_scope_source', 'current_discovery')}`",
        f"- last-success fallback: `{fallback.get('status', 'not_available')}` / used `{bool(fallback.get('usable'))}` / age `{fallback.get('age_hours', 'n/a')}`h",
        f"- partial raw freshness: `{partial.get('successful_board_count', 0)}/{partial.get('attempted_board_count', 0)}` / `{partial.get('freshness_status', 'missing')}` / age `{partial.get('age_hours', 'n/a')}`h",
        f"- 排除板块: `{summary.get('unavailable_board_count', 0)}`",
        f"- executable_report_allowed: `{bool(executive.get('executable_report_allowed'))}`",
        f"- research_diagnostic_allowed: `{bool(executive.get('research_diagnostic_allowed'))}`",
        f"- 当前新增执行金额: `AUD {summary.get('current_executable_new_stake_aud', 0)}`",
        f"- 下一步: {md(executive.get('recommended_next_action'))}",
        "",
        "## old_new_compare / 新旧范围对比",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- listed_count_delta: `{compare.get('listed_count_delta', 0)}`",
        f"- missing_count_delta: `{compare.get('missing_count_delta', 0)}`",
        f"- summary: {md(compare.get('summary'))}",
        "",
        "## Board Scope Matrix",
        "",
        "| 板块 | Live nav | 报告范围 | 可执行用途 | 金额策略 | 原因 | 下一步 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("board_scope_rows") or []:
        lines.append(
            "| {name} | {live} | {scope} | {usage} | {amount} | {reason} | {next_action} |".format(
                name=md(row.get("name")),
                live=md(row.get("live_nav_status")),
                scope=md(row.get("board_scope")),
                usage=md(row.get("executable_usage")),
                amount=md(row.get("amount_policy")),
                reason=md(row.get("reason")),
                next_action=md(row.get("next_action")),
            )
        )
    policy = payload.get("operation_policy") or {}
    lines.extend(
        [
            "",
            "## Last-success Fallback",
            "",
            "| 状态 | 使用 | 生成时间 | Age h | SLA h | 可研究板块 | 说明 |",
            "|---|---:|---|---:|---:|---:|---|",
            "| {status} | {usable} | {generated_at} | {age} | {sla} | {research_count} | {note} |".format(
                status=md(fallback.get("status")),
                usable="是" if fallback.get("usable") else "否",
                generated_at=md(fallback.get("generated_at")),
                age=md(fallback.get("age_hours")),
                sla=md(fallback.get("sla_hours")),
                research_count=md(fallback.get("research_allowed_board_count")),
                note=md(fallback.get("note")),
            ),
            "",
            "## Operation Policy",
            "",
            f"- {md(policy.get('betting_operation'))}",
            f"- {md(policy.get('when_partial_boards_available'))}",
            f"- {md(policy.get('last_success_fallback_policy'))}",
            f"- {md(policy.get('partial_raw_freshness_policy'))}",
            f"- {md(policy.get('stake_policy'))}",
            f"- {md(policy.get('time_effect_note'))}",
            "",
            "```mermaid",
            "pie showData",
            '  "可研究板块" : {research}',
            '  "排除板块" : {excluded}',
            "```",
        ]
    )
    markdown = "\n".join(lines)
    return markdown.format(
        research=int(summary.get("research_allowed_board_count") or 0),
        excluded=int(summary.get("unavailable_board_count") or 0),
    )


def write_available_board_strategy_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    partial = payload.get("partial_raw_freshness") or {}
    fallback = payload.get("last_success_fallback") or {}
    rows = payload.get("board_scope_rows") or []
    charts = [
        chart_from_items(
            "Board scope coverage",
            [
                ("research allowed", summary.get("research_allowed_board_count", 0)),
                ("excluded", summary.get("unavailable_board_count", 0)),
            ],
            "#1F4E79",
        ),
        chart_from_items(
            "Report decision",
            [
                ("executable allowed", 1 if executive.get("executable_report_allowed") else 0),
                ("research only", 1 if executive.get("research_diagnostic_allowed") and not executive.get("executable_report_allowed") else 0),
                ("blocked", 1 if not executive.get("research_diagnostic_allowed") else 0),
            ],
            "#C62828",
        ),
        chart_from_items(
            "Old-new count delta",
            [
                ("listed delta", compare.get("listed_count_delta", 0)),
                ("missing delta", compare.get("missing_count_delta", 0)),
            ],
            "#247A5A",
        ),
        chart_from_items(
            "Gate state",
            [
                ("raw ready", 1 if summary.get("raw_refresh_ready") else 0),
                ("formal ready", 1 if summary.get("formal_report_publish_ready") else 0),
                ("route mismatch", 1 if summary.get("route_mismatch_active") else 0),
            ],
            "#A56710",
        ),
        chart_from_items(
            "Partial raw freshness",
            [
                ("success", partial.get("successful_board_count", 0)),
                ("attempted", partial.get("attempted_board_count", 0)),
                ("age h", partial.get("age_hours") or 0),
                ("SLA h", partial.get("freshness_sla_hours") or 0),
            ],
            "#0F766E",
        ),
        chart_from_items(
            "Last-success fallback",
            [
                ("used", 1 if summary.get("last_success_fallback_used") else 0),
                ("research boards", fallback.get("research_allowed_board_count", 0)),
                ("age h", fallback.get("age_hours") or 0),
                ("SLA h", fallback.get("sla_hours") or 0),
            ],
            "#6A4C93",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 可用板块策略 Dashboard",
        subtitle="将 live board discovery 转换为报告范围、执行边界和新旧范围对比；只读，不自动下注。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("current action", str(executive.get("current_action", ""))),
            ("research boards", f"{summary.get('research_allowed_board_count', 0)}/{summary.get('expected_board_count', 0)}"),
            ("scope source", str(summary.get("board_scope_source", ""))),
            ("last-success fallback", f"{fallback.get('status', 'not_available')} / used={bool(fallback.get('usable'))}"),
            ("partial raw", f"{partial.get('successful_board_count', 0)}/{partial.get('attempted_board_count', 0)} / {partial.get('freshness_status', 'missing')}"),
            ("excluded boards", str(summary.get("unavailable_board_count", 0))),
            ("executable allowed", str(bool(executive.get("executable_report_allowed")))),
            ("new executable stake", f"AUD {summary.get('current_executable_new_stake_aud', 0)}"),
            ("old-new compare", str(compare.get("summary", ""))),
        ],
        charts=charts,
        table_headers=["板块", "live nav", "范围", "金额策略", "下一步"],
        table_rows=[
            [
                str(row.get("name", "")),
                str(row.get("live_nav_status", "")),
                str(row.get("board_scope", "")),
                str(row.get("amount_policy", "")),
                str(row.get("next_action", "")),
            ]
            for row in rows
        ],
        extra_tables=[
            {
                "title": "Last-success Fallback",
                "headers": ["字段", "值"],
                "rows": [
                    ["status", str(fallback.get("status", ""))],
                    ["usable", yes_no(fallback.get("usable"))],
                    ["generated_at", str(fallback.get("generated_at", ""))],
                    ["age_hours", str(fallback.get("age_hours", ""))],
                    ["sla_hours", str(fallback.get("sla_hours", ""))],
                    ["research_allowed_board_count", str(fallback.get("research_allowed_board_count", ""))],
                    ["note", str(fallback.get("note", ""))],
                ],
            },
            {
                "title": "Partial Raw Freshness",
                "headers": ["字段", "值"],
                "rows": [
                    ["status", str(partial.get("status", ""))],
                    ["freshness_status", str(partial.get("freshness_status", ""))],
                    ["fresh_within_sla", yes_no(partial.get("fresh_within_sla"))],
                    ["age_hours", str(partial.get("age_hours", ""))],
                    ["freshness_sla_hours", str(partial.get("freshness_sla_hours", ""))],
                    ["successful_boards", "；".join(partial.get("successful_board_names") or [])],
                    ["failed_boards", "；".join(partial.get("failed_board_names") or [])],
                    ["execution_allowed", yes_no(partial.get("execution_allowed"))],
                ],
            },
            {
                "title": "Old-New Compare",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous", str(compare.get("previous_generated_at", ""))],
                    ["current_status", str(compare.get("current_status", ""))],
                    ["listed_delta", str(compare.get("listed_count_delta", 0))],
                    ["missing_delta", str(compare.get("missing_count_delta", 0))],
                    ["summary", str(compare.get("summary", ""))],
                ],
            },
            {
                "title": "Operation Policy",
                "headers": ["策略", "内容"],
                "rows": [[key, str(value)] for key, value in (payload.get("operation_policy") or {}).items()],
            },
        ],
    )


def strategy_id(generated_at: str) -> str:
    safe = generated_at.replace(":", "").replace("-", "").replace("+", "_").replace(".", "_")
    return f"available_board_strategy_{safe}"


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


def yes_no(value: Any) -> str:
    return "是" if bool(value) else "否"
