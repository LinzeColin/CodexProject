from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifact_compare import build_artifact_old_new_compare
from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .boards import BOARD_CONFIGS
from .partial_daily_research import (
    RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST,
    choose_partial_research_evidence,
    partial_from_research_only_manifest,
)
from .raw_refresh import looks_like_route_mismatch, normalize_partial_research_refresh
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


RAW_REFRESH_RECOVERY_JSON_LATEST = "raw_refresh_recovery_latest.json"
RAW_REFRESH_RECOVERY_MD_LATEST = "raw_refresh_recovery_latest.md"
RAW_REFRESH_RECOVERY_PDF_LATEST = "raw_refresh_recovery_latest.pdf"
MATCHES_REPAIR_VALIDATION_LATEST = "matches_repair_validation_latest.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_raw_refresh_recovery_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_raw_refresh_recovery(output_dir)
    json_path = output_dir / RAW_REFRESH_RECOVERY_JSON_LATEST
    md_path = output_dir / RAW_REFRESH_RECOVERY_MD_LATEST
    pdf_path = output_dir / RAW_REFRESH_RECOVERY_PDF_LATEST
    payload["old_new_compare"] = build_artifact_old_new_compare(json_path, payload, raw_refresh_compare_metrics())
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_raw_refresh_recovery_markdown(payload))
    pdf_summary = write_raw_refresh_recovery_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_raw_refresh_recovery(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    research_only_raw = load_json(output_dir / RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST)
    partial = choose_partial_research_evidence(
        normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {}),
        partial_from_research_only_manifest(research_only_raw),
    )
    if raw_health:
        raw_health = dict(raw_health)
        raw_health["partial_research_refresh"] = partial
    diagnostics = load_json(output_dir / "raw_refresh_diagnostics_latest.json")
    timeline = load_json(output_dir / "active_timeline_latest.json")
    backfill = load_json(output_dir / "active_backfill_latest.json")
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    live_discovery = load_json(output_dir / "live_board_discovery_latest.json")
    available_strategy = load_json(output_dir / "available_board_strategy_latest.json")
    matches_repair_validation = normalize_matches_repair_validation(
        load_json(output_dir / MATCHES_REPAIR_VALIDATION_LATEST)
    )
    raw_attempts = [item for item in diagnostics.get("attempts") or [] if isinstance(item, dict)]
    attempts = normalize_attempts(raw_attempts)
    all_attempts = normalize_attempts(raw_attempts, limit=None)
    board_failures = normalize_board_failures(diagnostics.get("board_failures") or [])
    staged_validation_errors = extract_staged_validation_errors(diagnostics)
    queue = normalize_backfill_queue(timeline.get("backfill_queue") or [])
    phase_rows = build_phase_rows(raw_health, diagnostics, timeline, backfill, readiness, live_discovery, available_strategy)
    target_rows = build_target_rows(raw_health)
    retry_plan = build_retry_plan(all_attempts, raw_health, live_discovery)
    board_recovery_matrix = build_board_recovery_matrix(
        raw_health=raw_health,
        attempts=all_attempts,
        board_failures=board_failures,
        staged_validation_errors=staged_validation_errors,
        live_discovery=live_discovery,
        partial=partial,
        matches_repair_validation=matches_repair_validation,
    )
    discovery_summary = live_discovery.get("summary") or {}
    strategy_summary = available_strategy.get("summary") or {}
    summary = {
        "raw_ready": bool(raw_health.get("ready")),
        "raw_status": raw_health.get("status", "missing"),
        "diagnostics_status": diagnostics.get("status", "missing"),
        "diagnostics_interrupted": diagnostics.get("status") == "interrupted",
        "ready_required_target_count": int(raw_health.get("ready_required_target_count") or 0),
        "required_target_count": int(raw_health.get("required_target_count") or 0),
        "attempt_count": len(all_attempts),
        "board_failure_count": len(board_failures),
        "continued_after_board_failure": bool(diagnostics.get("continued_after_board_failure")),
        "staged_batch_manifest_skipped": bool(diagnostics.get("staged_batch_manifest_skipped")),
        "access_denied_attempt_count": len([item for item in all_attempts if item.get("access_denied")]),
        "ai_controlled_access_rejected_attempt_count": len([item for item in all_attempts if item.get("ai_controlled_access_rejected") or item.get("access_policy_status") == "blocked_by_access_policy"]),
        "automated_public_raw_refresh_allowed": not access_policy_blocked(raw_health, diagnostics, all_attempts),
        "route_mismatch_attempt_count": len([item for item in all_attempts if item.get("route_mismatch")]),
        "headed_fallback_attempt_count": len([item for item in all_attempts if item.get("headed_fallback")]),
        "headless_access_denied_attempt_count": len(
            [item for item in all_attempts if item.get("access_denied") and not item.get("headed_fallback")]
        ),
        "backfill_queue_count": int((timeline.get("summary") or {}).get("backfill_queue_count") or 0),
        "blocked_queue_count": int(backfill.get("blocked_queue_count") or 0),
        "recovery_phase_count": len(phase_rows),
        "ready_phase_count": len([item for item in phase_rows if item["status"] == "ready"]),
        "next_retry_step_count": len(retry_plan),
        "live_discovery_status": (live_discovery.get("executive_status") or {}).get("status", "missing"),
        "live_discovery_ready": bool(discovery_summary.get("discovery_ready")),
        "live_discovery_quality_status": discovery_summary.get("quality_status", "missing"),
        "live_discovery_failed": bool(discovery_summary.get("discovery_failed")),
        "live_discovery_listed_expected_count": int(discovery_summary.get("listed_expected_count") or 0),
        "live_discovery_missing_expected_count": int(discovery_summary.get("missing_expected_count") or 0),
        "live_discovery_observed_world_cup_link_count": int(discovery_summary.get("observed_world_cup_link_count") or 0),
        "effective_board_scope_source": strategy_summary.get("board_scope_source", "missing"),
        "effective_board_scope_last_success_fallback_used": bool(strategy_summary.get("last_success_fallback_used")),
        "effective_board_scope_last_success_fresh_within_sla": bool(strategy_summary.get("last_success_fresh_within_sla")),
        "effective_board_scope_research_allowed_count": int(strategy_summary.get("research_allowed_board_count") or 0),
        "effective_board_scope_unavailable_count": int(strategy_summary.get("unavailable_board_count") or 0),
        "effective_board_scope_retry_count": int(strategy_summary.get("discovery_retry_board_count") or 0),
        "effective_board_scope_listed_expected_count": int(strategy_summary.get("listed_expected_count") or 0),
        "effective_board_scope_missing_expected_count": int(strategy_summary.get("missing_expected_count") or 0),
        "partial_refresh_status": partial.get("status", "not_attempted"),
        "partial_refresh_freshness_status": partial.get("freshness_status", "missing"),
        "partial_refresh_fresh_within_sla": bool(partial.get("fresh_within_sla")),
        "partial_evidence_source": partial.get("selected_evidence_source", "raw_refresh_health_latest.json"),
        "partial_refresh_age_hours": partial.get("age_hours"),
        "partial_refresh_sla_hours": partial.get("freshness_sla_hours"),
        "partial_refresh_successful_board_count": int(partial.get("successful_board_count") or 0),
        "partial_refresh_attempted_board_count": int(partial.get("attempted_board_count") or 0),
        "partial_refresh_failed_board_count": int(partial.get("failed_board_count") or 0),
        "research_only_raw_status": research_only_raw.get("status", "missing"),
        "research_only_raw_successful_board_count": int(research_only_raw.get("successful_board_count") or 0),
        "research_only_raw_failed_board_count": int(research_only_raw.get("failed_board_count") or 0),
        "research_only_raw_attempt_warning_count": int(research_only_raw.get("attempt_warning_count") or 0),
        "board_recovery_matrix_count": len(board_recovery_matrix),
        "board_recovery_research_only_ready_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "research_only_ready"]),
        "board_recovery_auto_retry_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "auto_retry_read_only"]),
        "board_recovery_match_repair_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "auto_retry_with_match_repair"]),
        "board_recovery_unavailable_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "mark_unavailable_review"]),
        "board_recovery_validation_fix_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "parser_or_validation_fix"]),
        "board_recovery_partial_coverage_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "partial_coverage_review"]),
        "board_recovery_access_policy_blocked_count": len([row for row in board_recovery_matrix if row.get("automation_action") == "access_policy_blocked"]),
        "board_recovery_staged_validation_error_count": len([row for row in board_recovery_matrix if row.get("staged_validation_error_count")]),
        "board_recovery_manual_review_count": len([row for row in board_recovery_matrix if row.get("requires_user_presence")]),
        "matches_repair_validation_status": matches_repair_validation.get("status", "missing"),
        "matches_repair_validation_passed": bool(matches_repair_validation.get("passed")),
        "matches_repair_validation_match_count": int(matches_repair_validation.get("match_count") or 0),
        "matches_repair_validation_market_count": int(matches_repair_validation.get("market_count") or 0),
        "matches_repair_validation_error_count": int(matches_repair_validation.get("error_count") or 0),
    }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "raw_refresh_recovery_dashboard",
        "purpose": "Raw Refresh 恢复 Dashboard：定位 TAB 公开盘口抓取失败、判断是否允许补跑、给出恢复顺序；只读抓取，不自动下注。",
        "executive_status": {
            "ready_to_backfill": bool(raw_health.get("ready")) and summary["backfill_queue_count"] > 0,
            "status": "ready" if raw_health.get("ready") else "blocked",
            "primary_blocker": primary_blocker(raw_health, diagnostics),
            "recommended_next_action": recommended_next_action(raw_health, diagnostics),
        },
        "summary": summary,
        "phase_rows": phase_rows,
        "target_rows": target_rows,
        "partial_research_refresh": build_partial_refresh_evidence(partial),
        "matches_repair_validation": matches_repair_validation,
        "board_recovery_matrix": board_recovery_matrix,
        "attempt_rows": attempts,
        "board_failure_rows": board_failures,
        "next_retry_plan": retry_plan,
        "backfill_queue_preview": queue,
        "backfill_guard": build_backfill_guard(raw_health, backfill, queue),
        "source_artifacts": {
            "raw_refresh_health": "raw_refresh_health_latest.json" if raw_health else "",
            "raw_refresh_diagnostics": "raw_refresh_diagnostics_latest.json" if diagnostics else "",
            "raw_refresh_research_only": RAW_REFRESH_RESEARCH_ONLY_JSON_LATEST if research_only_raw else "",
            "active_timeline": "active_timeline_latest.json" if timeline else "",
            "active_backfill": "active_backfill_latest.json" if backfill else "",
            "automation_readiness": "automation_readiness_latest.json" if readiness else "",
            "live_board_discovery": "live_board_discovery_latest.json" if live_discovery else "",
            "available_board_strategy": "available_board_strategy_latest.json" if available_strategy else "",
            "matches_repair_validation": MATCHES_REPAIR_VALIDATION_LATEST if matches_repair_validation else "",
        },
        "truthfulness_note": "公开盘口 raw 未就绪时，补跑必须保持 blocked_by_raw_refresh；不能用旧盘口生成可执行下注日报。",
        "access_policy_note": "TAB 拒绝 AI controlled access 时，系统不得使用 headed fallback、验证码绕过、指纹伪装或 stealth browser；只能使用官方/授权数据源、用户导出导入或已有 fresh partial raw 做 research-only。",
    }
    return sanitize_public_payload(payload)


def raw_refresh_compare_metrics() -> list[tuple[str, str]]:
    return [
        ("status", "executive_status.status"),
        ("ready_to_backfill", "executive_status.ready_to_backfill"),
        ("raw_ready", "summary.raw_ready"),
        ("ready_required_target_count", "summary.ready_required_target_count"),
        ("required_target_count", "summary.required_target_count"),
        ("board_failure_count", "summary.board_failure_count"),
        ("continued_after_board_failure", "summary.continued_after_board_failure"),
        ("access_denied_attempt_count", "summary.access_denied_attempt_count"),
        ("route_mismatch_attempt_count", "summary.route_mismatch_attempt_count"),
        ("backfill_queue_count", "summary.backfill_queue_count"),
        ("live_discovery_missing_expected_count", "summary.live_discovery_missing_expected_count"),
        ("effective_board_scope_source", "summary.effective_board_scope_source"),
        ("effective_board_scope_research_allowed_count", "summary.effective_board_scope_research_allowed_count"),
        ("effective_board_scope_unavailable_count", "summary.effective_board_scope_unavailable_count"),
        ("partial_refresh_successful_board_count", "summary.partial_refresh_successful_board_count"),
        ("partial_refresh_freshness_status", "summary.partial_refresh_freshness_status"),
        ("board_recovery_research_only_ready_count", "summary.board_recovery_research_only_ready_count"),
        ("board_recovery_match_repair_count", "summary.board_recovery_match_repair_count"),
        ("matches_repair_validation_status", "summary.matches_repair_validation_status"),
        ("board_recovery_partial_coverage_count", "summary.board_recovery_partial_coverage_count"),
    ]


def normalize_matches_repair_validation(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or summary.get("status") or "missing")
    error_count = int(payload.get("error_count") or summary.get("error_count") or 0)
    market_count = int(payload.get("market_count") or summary.get("market_count") or 0)
    match_count = int(payload.get("match_count") or summary.get("match_count") or 0)
    validated_matches = payload.get("validated_matches") or summary.get("validated_matches") or []
    if not isinstance(validated_matches, list):
        validated_matches = []
    passed = status in {"passed", "ready"} and error_count == 0 and match_count > 0 and market_count > 0
    return {
        "schema_version": int(payload.get("schema_version") or 1),
        "generated_at": payload.get("generated_at", ""),
        "source": payload.get("source", ""),
        "status": "passed" if passed else status,
        "passed": passed,
        "board_id": payload.get("board_id", "matches"),
        "refresh_id": payload.get("refresh_id", ""),
        "scope": payload.get("scope", ""),
        "trigger": payload.get("trigger", ""),
        "read_only_guard": payload.get("read_only_guard", ""),
        "match_count": match_count,
        "market_count": market_count,
        "error_count": error_count,
        "validated_matches": [str(item) for item in validated_matches[:8]],
        "evidence": short_text(payload.get("evidence", ""), 220),
    }


def build_phase_rows(
    raw_health: dict[str, Any],
    diagnostics: dict[str, Any],
    timeline: dict[str, Any],
    backfill: dict[str, Any],
    readiness: dict[str, Any],
    live_discovery: dict[str, Any],
    available_strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_ready = bool(raw_health.get("ready"))
    access_denied = any(item.get("access_denied") for item in (diagnostics.get("attempts") or []))
    route_mismatch = has_route_mismatch(raw_health, diagnostics)
    board_failure_count = len(diagnostics.get("board_failures") or [])
    continued_after_failure = bool(diagnostics.get("continued_after_board_failure"))
    timeline_summary = timeline.get("summary") or {}
    private_ready = bool((readiness.get("private_position_bootstrap") or {}).get("ready"))
    discovery_summary = live_discovery.get("summary") or {}
    strategy_summary = available_strategy.get("summary") or {}
    partial = raw_health.get("partial_research_refresh") or {}
    partial_success = int(partial.get("successful_board_count") or 0)
    partial_attempted = int(partial.get("attempted_board_count") or 0)
    return [
        phase(
            "diagnose_access",
            "诊断 AI controlled access 拒绝 / 板块错配 / stale raw",
            "ready" if diagnostics else "blocked",
            (
                f"attempts={len(diagnostics.get('attempts') or [])}；"
                f"board_failures={board_failure_count}；"
                f"continued_after_failure={continued_after_failure}；"
                f"access_denied={access_denied}；route_mismatch={route_mismatch}"
            ),
            "保留最近 raw_refresh_diagnostics_latest.json；若出现 ai_controlled_access_rejected，自动 raw 停止，不再 headed fallback。",
        ),
        phase(
            "live_board_discovery",
            "发现 TAB Soccer live board list",
            "ready" if discovery_summary.get("discovery_ready") else "blocked",
            (
                f"listed={discovery_summary.get('listed_expected_count', 0)}/"
                f"{discovery_summary.get('expected_board_count', 0)}；"
                f"missing={discovery_summary.get('missing_expected_count', 0)}；"
                f"quality={discovery_summary.get('quality_status', 'missing')}"
            ),
            "route mismatch 时先读取 live_board_discovery_latest.json，缺失板块进入 unavailable review queue。",
        ),
        phase(
            "effective_board_scope",
            "确认当前研究范围来源",
            "ready"
            if int(strategy_summary.get("research_allowed_board_count") or 0) > 0
            and (
                bool(strategy_summary.get("discovery_ready"))
                or (
                    bool(strategy_summary.get("last_success_fallback_used"))
                    and bool(strategy_summary.get("last_success_fresh_within_sla"))
                )
            )
            else "blocked",
            (
                f"scope={strategy_summary.get('board_scope_source', 'missing')}；"
                f"research={strategy_summary.get('research_allowed_board_count', 0)}/"
                f"{strategy_summary.get('expected_board_count', 0)}；"
                f"excluded={strategy_summary.get('unavailable_board_count', 0)}；"
                f"fallback={strategy_summary.get('last_success_fallback_used', False)}；"
                f"fallback_fresh={strategy_summary.get('last_success_fresh_within_sla', False)}"
            ),
            "当前 discovery 失败时，只允许使用 4 小时内 last-success 范围生成 research-only 诊断；不能解锁新增下注。",
        ),
        phase(
            "partial_research_refresh",
            "记录 partial raw freshness 研究证据",
            "ready" if partial_success > 0 and partial.get("fresh_within_sla") else "blocked",
            (
                f"status={partial.get('status', 'missing')}；freshness={partial.get('freshness_status', 'missing')}；"
                f"success={partial_success}/{partial_attempted}；age={partial.get('age_hours', 'n/a')}h"
            ),
            "只把成功板块用于研究诊断；全量 raw/private/preflight 未通过时，新增执行金额仍为 AUD 0。",
        ),
        phase(
            "headed_public_refresh",
            "公开 raw 自动刷新合规门禁",
            "ready" if raw_ready else "blocked",
            f"raw_ready={raw_ready}；targets={raw_health.get('ready_required_target_count', 0)}/{raw_health.get('required_target_count', 0)}",
            "TAB 拒绝 AI controlled access 时不再触发 headed fallback；改用官方/授权数据源或用户导出导入，成功前不触发补跑。",
        ),
        phase(
            "batch_validation",
            "验证 5 个 required board 同批次",
            "ready" if raw_ready and raw_health.get("refresh_batch_manifest_ready", True) else "blocked",
            f"batch_ready={raw_health.get('refresh_batch_ready')}；manifest_ready={raw_health.get('refresh_batch_manifest_ready')}",
            "确认 5 个 raw 都来自同一 refresh_id，并通过 batch manifest sha256 检查。",
        ),
        phase(
            "private_position",
            "更新当日私有持仓快照",
            "ready" if private_ready else "blocked",
            f"private_position_ready={private_ready}",
            "raw 恢复后启动只读持仓读取；用真实余额和已下注结果更新预算。",
        ),
        phase(
            "safe_backfill",
            "执行安全补跑队列",
            "ready" if raw_ready and int(timeline_summary.get("backfill_queue_count") or 0) > 0 else "blocked",
            f"queue={timeline_summary.get('backfill_queue_count', 0)}；last_backfill={backfill.get('status', 'not_run')}",
            "仅生成 run-scoped PDF，不发布 latest_commit；补齐每日 4 次分析和日报缺口。",
        ),
    ]


def build_target_rows(raw_health: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in raw_health.get("targets") or []:
        rows.append(
            {
                "board_id": item.get("board_id", ""),
                "name": item.get("name", ""),
                "status": item.get("status", ""),
                "raw_fresh": bool(item.get("raw_fresh")),
                "raw_valid": bool(item.get("raw_valid")),
                "driver_configured": bool(item.get("driver_configured")),
                "blocker_codes": item.get("blocker_codes", []),
                "raw_age_hours": item.get("raw_age_hours"),
            }
        )
    return rows


def build_partial_refresh_evidence(partial: dict[str, Any]) -> dict[str, Any]:
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
        "attempted_board_count": int(partial.get("attempted_board_count") or 0),
        "successful_board_count": int(partial.get("successful_board_count") or 0),
        "failed_board_count": int(partial.get("failed_board_count") or 0),
        "successful_board_names": [str(item.get("name") or item.get("board_id") or "") for item in successful],
        "failed_board_names": [str(item.get("name") or item.get("board_id") or "") for item in failed],
        "note": partial.get("note", "Partial raw 只允许研究诊断，不解锁下注执行。"),
    }


def build_board_recovery_matrix(
    *,
    raw_health: dict[str, Any],
    attempts: list[dict[str, Any]],
    board_failures: list[dict[str, Any]],
    staged_validation_errors: dict[str, list[str]],
    live_discovery: dict[str, Any],
    partial: dict[str, Any],
    matches_repair_validation: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    target_by_board = {str(item.get("board_id") or ""): item for item in raw_health.get("targets") or [] if isinstance(item, dict)}
    target_by_refresh = {refresh_alias(str(item.get("board_id") or "")): item for item in raw_health.get("targets") or [] if isinstance(item, dict)}
    attempts_by_refresh: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        attempts_by_refresh.setdefault(refresh_alias(str(attempt.get("board_id") or "")), []).append(attempt)
    failure_by_refresh = {refresh_alias(str(item.get("board_id") or "")): item for item in board_failures}
    discovery_by_refresh = {
        str(item.get("refresh_board_id") or ""): item
        for item in (live_discovery.get("expected_board_rows") or [])
        if isinstance(item, dict)
    }
    partial_success = {refresh_alias(str(item.get("board_id") or item.get("name") or "")) for item in partial.get("successful_boards") or []}
    partial_failed = {refresh_alias(str(item.get("board_id") or item.get("name") or "")) for item in partial.get("failed_boards") or []}
    rows: list[dict[str, Any]] = []
    for board in BOARD_CONFIGS:
        target = target_by_board.get(board.board_id) or target_by_refresh.get(board.refresh_board_id) or {}
        board_attempts = attempts_by_refresh.get(board.refresh_board_id, [])
        last_attempt = board_attempts[-1] if board_attempts else {}
        failure = failure_by_refresh.get(board.refresh_board_id) or {}
        validation_errors = staged_validation_errors.get(board.refresh_board_id, [])
        discovery = discovery_by_refresh.get(board.refresh_board_id) or {}
        repair_validation = matches_repair_validation if board.refresh_board_id == "matches" else {}
        partial_result = partial_result_for_board(board, partial_success, partial_failed)
        automation_action = board_recovery_action(board, target, last_attempt, failure, discovery, validation_errors, partial_result)
        rows.append(
            {
                "board_id": board.board_id,
                "refresh_board_id": board.refresh_board_id,
                "name": board.name,
                "priority": board.priority,
                "live_nav_status": discovery.get("live_nav_status", "unknown"),
                "matched_link_count": int(discovery.get("matched_link_count") or 0),
                "raw_status": target.get("status", "missing"),
                "raw_fresh": bool(target.get("raw_fresh")),
                "raw_valid": bool(target.get("raw_valid")),
                "raw_age_hours": target.get("raw_age_hours"),
                "attempt_count": len(board_attempts),
                "last_exit_code": last_attempt.get("exit_code", ""),
                "route_mismatch": bool(last_attempt.get("route_mismatch")) or looks_like_route_mismatch(failure.get("error") or ""),
                "access_denied": bool(last_attempt.get("access_denied")),
                "board_failure": bool(failure),
                "staged_validation_error_count": len(validation_errors),
                "staged_validation_errors": validation_errors[:3],
                "repair_validation_status": (repair_validation or {}).get("status", "missing"),
                "repair_validation_passed": bool((repair_validation or {}).get("passed")),
                "repair_validation_match_count": int((repair_validation or {}).get("match_count") or 0),
                "repair_validation_market_count": int((repair_validation or {}).get("market_count") or 0),
                "repair_validation_error_count": int((repair_validation or {}).get("error_count") or 0),
                "partial_result": partial_result,
                "blocker_codes": target.get("blocker_codes") or [],
                "automation_action": automation_action,
                "requires_user_presence": automation_action in {"manual_access_review", "private_profile_required", "access_policy_blocked"},
                "safe_to_retry_now": automation_action in {"auto_retry_read_only", "auto_retry_with_match_repair", "parser_or_validation_fix"},
                "success_gate": board_success_gate(board, automation_action),
                "next_action": board_next_action(board, automation_action),
                "evidence": board_recovery_evidence(target, last_attempt, failure, discovery, validation_errors, repair_validation),
            }
        )
    return rows


def refresh_alias(value: str) -> str:
    normalized = str(value or "").lower()
    aliases = {
        "world_cup_matches": "matches",
        "2026 world cup matches": "matches",
        "world_cup_futures": "futures",
        "2026 world cup futures": "futures",
        "world_cup_group_betting": "group_betting",
        "2026 world cup group betting": "group_betting",
        "world_cup_australia_markets": "australia_markets",
        "2026 world cup australia markets": "australia_markets",
        "world_cup_team_futures_multi": "team_futures_multi",
        "2026 world cup team futures multi": "team_futures_multi",
    }
    return aliases.get(normalized, normalized)


def partial_result_for_board(board: Any, partial_success: set[str], partial_failed: set[str]) -> str:
    key = board.refresh_board_id
    if key in partial_success:
        return "partial_success"
    if key in partial_failed:
        return "partial_failed"
    return "not_in_partial_batch"


def board_recovery_action(
    board: Any,
    target: dict[str, Any],
    last_attempt: dict[str, Any],
    failure: dict[str, Any],
    discovery: dict[str, Any],
    staged_validation_errors: list[str] | None = None,
    partial_result: str = "",
) -> str:
    if partial_result == "partial_failed":
        return "mark_unavailable_review"
    error_text = " ".join(str(value or "") for value in [failure.get("error"), last_attempt.get("error"), last_attempt.get("stderr_tail")])
    if looks_like_route_mismatch(error_text):
        return "mark_unavailable_review"
    if last_attempt.get("access_denied"):
        return "access_policy_blocked"
    if matches_repairable_attempt_errors(board, last_attempt):
        return "auto_retry_with_match_repair"
    if matches_repairable_staged_errors(board, staged_validation_errors or []):
        return "auto_retry_with_match_repair"
    if partial_coverage_staged_errors(board, staged_validation_errors or []):
        return "partial_coverage_review"
    if staged_validation_errors:
        return "parser_or_validation_fix"
    if partial_result == "partial_success":
        return "research_only_ready"
    if discovery.get("automation_decision") == "temporarily_unavailable_review" or discovery.get("live_nav_status") == "missing_from_live_nav":
        return "mark_unavailable_review"
    if failure or target.get("raw_valid") is False:
        return "parser_or_validation_fix"
    if target.get("raw_fresh") is False or target.get("status") in {"blocked", "missing"}:
        return "auto_retry_read_only"
    return "monitor"


def board_success_gate(board: Any, action: str) -> str:
    if action == "research_only_ready":
        return "research-only raw 保持 4小时内 fresh/valid；正式执行仍等待 5/5 raw、私有持仓和发布门禁。"
    if action == "mark_unavailable_review":
        return "TAB live nav 重新列出该板块，且 deep link resolves 到预期 competition。"
    if action == "parser_or_validation_fix":
        return "staged raw 通过该板块 parser/coverage validation，再进入同批次 raw gate。"
    if action == "partial_coverage_review":
        return "TAB 当前页面重新提供完整 required coverage；该板块通过 parser/coverage validation 后才进入全量 raw gate。"
    if action == "auto_retry_with_match_repair":
        return "Matches chunk 合并后，缺失/partial/error 单场由 --match 重抓修复，并通过 Result/Handicap/Goals/BTTS 覆盖验证。"
    if action == "access_policy_blocked":
        return "接入官方/授权数据源或用户导出导入快照；不得使用 headed fallback、验证码绕过、指纹伪装或 stealth browser。"
    if action == "manual_access_review":
        return "访问政策确认允许后，导入数据通过 freshness、coverage、same refresh_id batch 与 public safety gate。"
    if action == "auto_retry_read_only":
        return "raw fresh、raw valid、refresh_id 同批次且 5/5 required boards 通过。"
    return "持续保持 fresh/valid，并纳入下一轮全量门禁。"


def board_next_action(board: Any, action: str) -> str:
    if action == "research_only_ready":
        return "纳入 research-only 诊断；继续等待完整 raw gate，不生成新增执行下注。"
    if action == "mark_unavailable_review":
        return "保持 unavailable review queue；不使用旧盘口，不生成该板块当前执行建议。"
    if action == "parser_or_validation_fix":
        return f"复核 {board.parser_strategy} 的 marker/coverage 规则；只更新解析与验证，不放宽门禁。"
    if action == "partial_coverage_review":
        return "保持 research-only；下一轮只读刷新重新检查 TAB 是否补齐该板块完整球队/小组/市场，不用旧盘口补齐缺口。"
    if action == "auto_retry_with_match_repair":
        return "运行只读 Matches raw refresh；chunk 合并后自动用 --match 单场重抓缺失、partial 或 error 场次。"
    if action == "access_policy_blocked":
        return "停止自动公开 raw；保留 research-only 诊断，等待官方/授权 feed 或用户导出导入。"
    if action == "manual_access_review":
        return "不要使用 headed 自动访问；仅接受官方/授权数据源或用户导出导入。"
    if action == "auto_retry_read_only":
        return f"运行只读刷新 driver：scripts/refresh_tab_readonly.mjs --board {board.refresh_board_id}。"
    return "保持监控；下一轮 raw refresh 继续验证 freshness。"


def board_recovery_evidence(
    target: dict[str, Any],
    last_attempt: dict[str, Any],
    failure: dict[str, Any],
    discovery: dict[str, Any],
    staged_validation_errors: list[str] | None = None,
    repair_validation: dict[str, Any] | None = None,
) -> str:
    parts = [
        f"live={discovery.get('live_nav_status', 'unknown')}",
        f"raw={target.get('status', 'missing')}",
        f"fresh={bool(target.get('raw_fresh'))}",
        f"valid={bool(target.get('raw_valid'))}",
    ]
    if last_attempt:
        parts.append(f"last_exit={last_attempt.get('exit_code', '')}")
    if failure:
        parts.append(f"failure={short_text(failure.get('error', ''), 90)}")
    if staged_validation_errors:
        parts.append(f"staged_validation={short_text(staged_validation_errors[0], 120)}")
    chunk_quality_errors = last_attempt.get("chunk_quality_errors") or []
    if chunk_quality_errors:
        parts.append(f"chunk_quality={short_text(chunk_quality_errors[0], 120)}")
    if repair_validation:
        parts.append(
            "repair_validation="
            f"{repair_validation.get('status', 'missing')}/"
            f"{repair_validation.get('match_count', 0)} matches/"
            f"{repair_validation.get('market_count', 0)} markets/"
            f"errors {repair_validation.get('error_count', 0)}"
        )
    blockers = target.get("blocker_codes") or []
    if blockers:
        parts.append("blocker=" + ",".join(str(item) for item in blockers))
    return "；".join(parts)


def matches_repairable_attempt_errors(board: Any, attempt: dict[str, Any]) -> bool:
    if getattr(board, "refresh_board_id", "") != "matches":
        return False
    texts = []
    texts.extend(str(item or "") for item in attempt.get("chunk_quality_errors") or [])
    texts.extend(str(item or "") for item in attempt.get("repair_quality_errors") or [])
    texts.extend(str(value or "") for value in [attempt.get("error"), attempt.get("stderr_tail"), attempt.get("stdout_tail")])
    return matches_repairable_error_text(texts)


def matches_repairable_staged_errors(board: Any, errors: list[str]) -> bool:
    if getattr(board, "refresh_board_id", "") != "matches":
        return False
    return matches_repairable_error_text(errors)


def partial_coverage_staged_errors(board: Any, errors: list[str]) -> bool:
    if getattr(board, "refresh_board_id", "") not in {"futures", "group_betting"}:
        return False
    combined = " ".join(str(item or "").lower() for item in errors)
    if not combined:
        return False
    markers = [
        "expected 48 teams",
        "expected 48 complete futures rows",
        "missing futures teams",
        "expected 12 groups",
        "expected 12 complete group winner markets",
        "missing groups",
    ]
    return any(marker in combined for marker in markers)


def matches_repairable_error_text(errors: list[str]) -> bool:
    markers = [
        "result market coverage",
        "detail coverage",
        "full core coverage",
        "missing match",
        "partial",
        "market expansion errors",
        "market header expansion failed",
        "handicap",
        "chunk_quality",
    ]
    combined = " ".join(str(item or "").lower() for item in errors)
    return bool(combined) and any(marker in combined for marker in markers)


def extract_staged_validation_errors(diagnostics: dict[str, Any]) -> dict[str, list[str]]:
    error_text = str(diagnostics.get("error") or "")
    if not error_text:
        return {}
    rows: dict[str, list[str]] = {}
    for board in BOARD_CONFIGS:
        marker = f"{board.name} staged raw validation failed:"
        start = 0
        while True:
            index = error_text.find(marker, start)
            if index < 0:
                break
            content_start = index + len(marker)
            next_index = next_validation_marker_index(error_text, content_start)
            message = error_text[content_start:next_index].strip(" ;.")
            if message:
                rows.setdefault(board.refresh_board_id, []).append(message)
            start = next_index
    return rows


def next_validation_marker_index(text: str, start: int) -> int:
    candidates = [
        pos
        for board in BOARD_CONFIGS
        for marker in [f"; {board.name} staged raw validation failed:"]
        for pos in [text.find(marker, start)]
        if pos >= 0
    ]
    return min(candidates) if candidates else len(text)


def normalize_attempts(attempts: list[dict[str, Any]], limit: int | None = 8) -> list[dict[str, Any]]:
    rows = []
    selected = attempts if limit is None else attempts[-limit:]
    for item in selected:
        rows.append(
            {
                "board_id": item.get("board_id", ""),
                "attempt": int(item.get("attempt") or 0),
                "exit_code": item.get("exit_code", ""),
                "access_denied": bool(item.get("access_denied")),
                "route_mismatch": looks_like_route_mismatch(item.get("error") or item.get("stderr_tail") or ""),
                "headed_fallback": bool(item.get("headed_fallback")),
                "ai_controlled_access_rejected": bool(item.get("ai_controlled_access_rejected") or item.get("access_policy_status") == "blocked_by_access_policy"),
                "access_policy_status": item.get("access_policy_status", ""),
                "chunk_offset": item.get("chunk_offset", ""),
                "chunk_limit": item.get("chunk_limit", ""),
                "chunk_quality_errors": [short_text(error, 220) for error in (item.get("chunk_quality_errors") or [])],
                "repair_quality_errors": [short_text(error, 220) for error in (item.get("repair_quality_errors") or [])],
                "repair_match": item.get("repair_match", ""),
                "repair_success": bool(item.get("repair_success")),
                "error": short_text(item.get("error") or item.get("stderr_tail") or "", 220),
            }
        )
    return rows


def normalize_board_failures(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(failures, start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "rank": index,
                "board_id": item.get("board_id", ""),
                "output": item.get("output", ""),
                "error": short_text(item.get("error", ""), 240),
            }
        )
    return rows


def normalize_backfill_queue(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in queue[:7]:
        rows.append(
            {
                "rank": int(item.get("repair_rank") or len(rows) + 1),
                "report_date": item.get("report_date", ""),
                "display_date": item.get("display_date", ""),
                "priority_score": int(item.get("priority_score") or 0),
                "reason": item.get("reason", ""),
                "operation": item.get("operation", ""),
                "mode": item.get("mode", "safe_no_latest_publish"),
            }
        )
    return rows


def build_retry_plan(attempts: list[dict[str, Any]], raw_health: dict[str, Any], live_discovery: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    access_denied_attempts = [item for item in attempts if item.get("access_denied")]
    headed_attempts = [item for item in attempts if item.get("headed_fallback")]
    route_mismatch_attempts = [item for item in attempts if item.get("route_mismatch")]
    plan = []
    if has_route_mismatch(raw_health, {"attempts": attempts}):
        first = route_mismatch_attempts[0] if route_mismatch_attempts else {}
        discovery_summary = (live_discovery or {}).get("summary") or {}
        discovery_hint = ""
        if discovery_summary:
            discovery_hint = (
                f"；discovery listed={discovery_summary.get('listed_expected_count', 0)}/"
                f"{discovery_summary.get('expected_board_count', 0)}, missing={discovery_summary.get('missing_expected_count', 0)}"
            )
        plan.append(
            {
                "rank": 1,
                "scope": "2026 World Cup Australia Markets",
                "trigger": "live board route mismatch / board not listed",
                "operation": "重新发现 TAB Soccer live board list；若仍不在导航中，保持该板块 unavailable，不用旧盘口生成下注建议" + discovery_hint,
                "mode": "live_board_discovery_review",
                "chunk": str(first.get("chunk_offset", "")),
                "requires_user_presence": False,
                "success_gate": "board URL resolves to Australia Markets and 14 expected markets priced",
            }
        )
    elif access_denied_attempts:
        first = access_denied_attempts[0]
        plan.append(
            {
                "rank": 1,
                "scope": "2026 World Cup Matches",
                "trigger": "TAB Access Denied / AI controlled access rejected",
                "operation": "停止自动公开 raw；接入官方/授权 feed，或由用户导出后导入 raw 快照；已有 fresh partial raw 仅用于 research-only。",
                "mode": "access_policy_blocked",
                "chunk": f"{first.get('chunk_offset', '')}-{first.get('chunk_limit', '')}",
                "requires_user_presence": True,
                "success_gate": "导入数据通过 freshness、coverage、same refresh_id batch 与 public safety gate。",
            }
        )
    else:
        plan.append(
            {
                "rank": 1,
                "scope": "Required boards",
                "trigger": ", ".join(raw_health.get("blocker_codes") or []) or "raw_refresh_not_ready",
                "operation": "执行标准只读 raw refresh；若出现 Access Denied 立即 fail-closed，不做 headed fallback",
                "mode": "standard_read_only_refresh",
                "chunk": "",
                "requires_user_presence": False,
                "success_gate": "5/5 required raw fresh + valid + same refresh_id batch",
            }
        )
    plan.append(
        {
            "rank": len(plan) + 1,
            "scope": "Backfill queue",
            "trigger": "raw_refresh_ready=true",
            "operation": "解锁 safe_no_latest_publish 补跑，不推进 latest_commit",
            "mode": "safe_no_latest_publish",
            "chunk": "",
            "requires_user_presence": False,
            "success_gate": "补跑 run-scoped PDF 生成并写入 active_timeline_audits",
        }
    )
    return plan


def build_backfill_guard(raw_health: dict[str, Any], backfill: dict[str, Any], queue: list[dict[str, Any]]) -> dict[str, Any]:
    raw_ready = bool(raw_health.get("ready"))
    return {
        "allowed_now": raw_ready and bool(queue),
        "current_status": backfill.get("status", "not_run"),
        "requested_count": int(backfill.get("requested_count") or 0),
        "completed_count": int(backfill.get("completed_count") or 0),
        "blocked_queue_count": int(backfill.get("blocked_queue_count") or 0),
        "guard_reason": "raw_ready" if raw_ready else "raw_refresh_not_ready",
        "safe_backfill_mode": "safe_no_latest_publish",
        "fail_closed_rule": "raw 未就绪时不执行历史补跑，不发布 latest_commit。",
    }


def phase(phase_id: str, title: str, status: str, evidence: str, next_action: str) -> dict[str, Any]:
    return {
        "phase_id": phase_id,
        "title": title,
        "status": status,
        "score": 1.0 if status == "ready" else 0.0,
        "evidence": evidence,
        "next_action": next_action,
    }


def render_raw_refresh_recovery_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    partial = payload.get("partial_research_refresh") or {}
    repair_validation = payload.get("matches_repair_validation") or {}
    lines = [
        "# TAB FIFA Raw Refresh 恢复 Dashboard",
        "",
        "本报告聚焦公开盘口 raw 抓取恢复和安全补跑解锁。它只读公开盘口，不自动下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- diagnostics_status: `{summary.get('diagnostics_status', 'missing')}` / interrupted `{bool(summary.get('diagnostics_interrupted'))}`",
        f"- ready_to_backfill: `{bool(executive.get('ready_to_backfill'))}`",
        f"- raw targets: `{summary.get('ready_required_target_count', 0)}/{summary.get('required_target_count', 0)}`",
        f"- attempts: `{summary.get('attempt_count', 0)}`",
        f"- board failures: `{summary.get('board_failure_count', 0)}` / continued_after_failure `{bool(summary.get('continued_after_board_failure'))}`",
        f"- staged batch manifest skipped: `{bool(summary.get('staged_batch_manifest_skipped'))}`",
        f"- access denied attempts: `{summary.get('access_denied_attempt_count', 0)}`",
        f"- route mismatch attempts: `{summary.get('route_mismatch_attempt_count', 0)}`",
        f"- live discovery: `{summary.get('live_discovery_status', 'missing')}` / ready `{bool(summary.get('live_discovery_ready'))}` / quality `{summary.get('live_discovery_quality_status', 'missing')}` / listed `{summary.get('live_discovery_listed_expected_count', 0)}` / missing `{summary.get('live_discovery_missing_expected_count', 0)}`",
        f"- effective board scope: `{summary.get('effective_board_scope_source', 'missing')}` / research `{summary.get('effective_board_scope_research_allowed_count', 0)}` / unavailable `{summary.get('effective_board_scope_unavailable_count', 0)}` / fallback `{bool(summary.get('effective_board_scope_last_success_fallback_used'))}` / fresh `{bool(summary.get('effective_board_scope_last_success_fresh_within_sla'))}`",
        f"- partial refresh: `{partial.get('successful_board_count', 0)}/{partial.get('attempted_board_count', 0)}` / `{partial.get('freshness_status', 'missing')}` / age `{partial.get('age_hours', 'n/a')}`h / SLA `{partial.get('freshness_sla_hours', 'n/a')}`h",
        f"- board recovery matrix: `{summary.get('board_recovery_matrix_count', 0)}` / research_only_ready `{summary.get('board_recovery_research_only_ready_count', 0)}` / auto_retry `{summary.get('board_recovery_auto_retry_count', 0)}` / match_repair `{summary.get('board_recovery_match_repair_count', 0)}` / unavailable `{summary.get('board_recovery_unavailable_count', 0)}` / partial_coverage `{summary.get('board_recovery_partial_coverage_count', 0)}` / validation_fix `{summary.get('board_recovery_validation_fix_count', 0)}` / staged_validation `{summary.get('board_recovery_staged_validation_error_count', 0)}` / manual_review `{summary.get('board_recovery_manual_review_count', 0)}`",
        f"- Matches repair validation: `{summary.get('matches_repair_validation_status', 'missing')}` / passed `{bool(summary.get('matches_repair_validation_passed'))}` / matches `{summary.get('matches_repair_validation_match_count', 0)}` / markets `{summary.get('matches_repair_validation_market_count', 0)}` / errors `{summary.get('matches_repair_validation_error_count', 0)}`",
        f"- backfill queue: `{summary.get('backfill_queue_count', 0)}`",
        f"- primary_blocker: `{executive.get('primary_blocker', '')}`",
        f"- recommended_next_action: {executive.get('recommended_next_action', '')}",
        "",
        "## Visual Summary",
        "",
        "```mermaid",
        "pie showData",
        f"  \"ready phases\" : {summary.get('ready_phase_count', 0)}",
        f"  \"blocked phases\" : {max(0, summary.get('recovery_phase_count', 0) - summary.get('ready_phase_count', 0))}",
        "```",
        "",
        "## 恢复阶段",
        "",
        "| 阶段 | 状态 | 证据 | 下一步 |",
        "|---|---|---|---|",
    ]
    for item in payload.get("phase_rows") or []:
        lines.append(f"| {md(item.get('title'))} | {md(item.get('status'))} | {md(item.get('evidence'))} | {md(item.get('next_action'))} |")
    lines.extend(["", "## 目标板块状态", "", "| 板块 | 状态 | fresh | valid | driver | blocker |", "|---|---|---|---|---|---|"])
    for item in payload.get("target_rows") or []:
        lines.append(
            f"| {md(item.get('name'))} | {md(item.get('status'))} | {yes_no(item.get('raw_fresh'))} | {yes_no(item.get('raw_valid'))} | {yes_no(item.get('driver_configured'))} | {md(', '.join(item.get('blocker_codes') or []))} |"
        )
    lines.extend(
        [
            "",
            "## 板块级恢复矩阵",
            "",
            "| 优先级 | 板块 | live状态 | raw状态 | partial | attempts | staged错误 | 修复验证 | action | 是否可自动重试 | 成功门禁 | 下一步 |",
            "|---:|---|---|---|---|---:|---:|---|---|---|---|---|",
        ]
    )
    for item in payload.get("board_recovery_matrix") or []:
        lines.append(
            f"| {item.get('priority', '')} | {md(item.get('name'))} | {md(item.get('live_nav_status'))} | {md(item.get('raw_status'))} | {md(item.get('partial_result'))} | {item.get('attempt_count', 0)} | {item.get('staged_validation_error_count', 0)} | {md(item.get('repair_validation_status'))} | {md(item.get('automation_action'))} | {yes_no(item.get('safe_to_retry_now'))} | {md(item.get('success_gate'))} | {md(item.get('next_action'))} |"
        )
    if repair_validation:
        lines.extend(
            [
                "",
                "## Matches Repair Live Validation",
                "",
                "该证据只证明盘口展开修复在只读测试中可用，不解锁全量 raw 或新增下注金额。",
                "",
                "| 项目 | 值 |",
                "|---|---|",
                f"| status | {md(repair_validation.get('status'))} |",
                f"| passed | {yes_no(repair_validation.get('passed'))} |",
                f"| scope | {md(repair_validation.get('scope'))} |",
                f"| trigger | {md(repair_validation.get('trigger'))} |",
                f"| matches / markets / errors | {md(repair_validation.get('match_count'))} / {md(repair_validation.get('market_count'))} / {md(repair_validation.get('error_count'))} |",
                f"| validated matches | {md('、'.join(repair_validation.get('validated_matches') or []))} |",
                f"| guard | {md(repair_validation.get('read_only_guard'))} |",
            ]
        )
    lines.extend(
        [
            "",
            "## Partial Raw Freshness Evidence",
            "",
            "该部分只证明部分板块可用于研究诊断，不证明全量可执行下注日报。",
            "",
            "| 项目 | 值 |",
            "|---|---|",
            f"| status | {md(partial.get('status'))} |",
            f"| freshness_status | {md(partial.get('freshness_status'))} |",
            f"| fresh_within_sla | {yes_no(partial.get('fresh_within_sla'))} |",
            f"| age / SLA | {md(partial.get('age_hours'))}h / {md(partial.get('freshness_sla_hours'))}h |",
            f"| successful boards | {md('、'.join(partial.get('successful_board_names') or []))} |",
            f"| failed boards | {md('、'.join(partial.get('failed_board_names') or []))} |",
            f"| execution_allowed | {yes_no(partial.get('execution_allowed'))} |",
            f"| current_research_only_allowed | {yes_no(partial.get('current_research_only_allowed'))} |",
            f"| historical_research_evidence_available | {yes_no(partial.get('historical_research_evidence_available'))} |",
            f"| note | {md(partial.get('note'))} |",
        ]
    )
    lines.extend(["", "## 最近尝试", "", "| board | attempt | exit | access_denied | chunk | error |", "|---|---:|---|---|---|---|"])
    for item in payload.get("attempt_rows") or []:
        chunk = f"{item.get('chunk_offset')}-{item.get('chunk_limit')}"
        lines.append(f"| {md(item.get('board_id'))} | {item.get('attempt', 0)} | {md(item.get('exit_code'))} | {yes_no(item.get('access_denied'))} | {md(chunk)} | {md(item.get('error'))} |")
    lines.extend(["", "## 单板失败隔离", "", "| 顺序 | board | output | error |", "|---:|---|---|---|"])
    for item in payload.get("board_failure_rows") or []:
        lines.append(f"| {item.get('rank', '')} | {md(item.get('board_id'))} | {md(item.get('output'))} | {md(item.get('error'))} |")
    lines.extend(["", "## 下一次刷新计划", "", "| 顺序 | 范围 | 触发条件 | 操作 | 模式 | 成功门禁 |", "|---:|---|---|---|---|---|"])
    for item in payload.get("next_retry_plan") or []:
        lines.append(
            f"| {item.get('rank', '')} | {md(item.get('scope'))} | {md(item.get('trigger'))} | {md(item.get('operation'))} | {md(item.get('mode'))} | {md(item.get('success_gate'))} |"
        )
    lines.extend(["", "## 补跑队列预览", "", "| 顺序 | 日期 | 分数 | 原因 | 模式 |", "|---:|---|---:|---|---|"])
    for item in payload.get("backfill_queue_preview") or []:
        lines.append(f"| {item.get('rank', '')} | {md(item.get('display_date'))} | {item.get('priority_score', 0)} | {md(item.get('reason'))} | {md(item.get('mode'))} |")
    lines.extend(
        [
            "",
            "## old_new_compare / 新旧恢复变化",
            "",
            f"- compare_status: `{compare.get('status', '')}`",
            f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
            f"- changed_count: `{compare.get('changed_count', 0)}/{compare.get('metric_count', 0)}`",
            f"- summary: {md(compare.get('summary'))}",
            "",
            "| 指标 | 当前 | 上一版 | 变化 |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in compare.get("rows") or []:
        lines.append(f"| {md(row.get('metric'))} | {md(row.get('current'))} | {md(row.get('previous'))} | {md(row.get('delta'))} |")
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}"])
    return "\n".join(lines)


def write_raw_refresh_recovery_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    phase_rows = payload.get("phase_rows") or []
    target_rows = payload.get("target_rows") or []
    attempts = payload.get("attempt_rows") or []
    board_failures = payload.get("board_failure_rows") or []
    retry_plan = payload.get("next_retry_plan") or []
    queue = payload.get("backfill_queue_preview") or []
    compare = payload.get("old_new_compare") or {}
    partial = payload.get("partial_research_refresh") or {}
    board_matrix = payload.get("board_recovery_matrix") or []
    repair_validation = payload.get("matches_repair_validation") or {}
    charts = [
        chart_from_items("Raw targets", [("ready", summary.get("ready_required_target_count", 0)), ("blocked", max(0, summary.get("required_target_count", 0) - summary.get("ready_required_target_count", 0)))], "#1F4E79"),
        chart_from_items("Recovery phases", [(row.get("title", ""), float(row.get("score") or 0) * 100) for row in phase_rows], "#247A5A"),
        chart_from_items(
            "Refresh attempts",
            [
                ("route mismatch", summary.get("route_mismatch_attempt_count", 0)),
                ("access denied", summary.get("access_denied_attempt_count", 0)),
                (
                    "other",
                    max(
                        0,
                        summary.get("attempt_count", 0)
                        - summary.get("access_denied_attempt_count", 0)
                        - summary.get("route_mismatch_attempt_count", 0),
                    ),
                ),
            ],
            "#C62828",
        ),
        chart_from_items("Backfill queue", [(row.get("display_date", ""), float(row.get("priority_score") or 0)) for row in queue], "#6A4C93"),
        chart_from_items(
            "Partial raw freshness",
            [
                ("successful boards", partial.get("successful_board_count", 0)),
                ("failed boards", partial.get("failed_board_count", 0)),
                ("age hours", partial.get("age_hours") or 0),
                ("SLA hours", partial.get("freshness_sla_hours") or 0),
            ],
            "#0F766E",
        ),
        chart_from_items(
            "板块恢复动作",
            recovery_action_items(board_matrix),
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Raw Refresh 恢复 Dashboard",
        subtitle="公开盘口抓取恢复、补跑解锁和 fail-closed 状态；只读抓取，不自动下注。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("diagnostics status", f"{summary.get('diagnostics_status', 'missing')} / interrupted {yes_no(summary.get('diagnostics_interrupted'))}"),
            ("ready_to_backfill", str(bool(executive.get("ready_to_backfill")))),
            ("raw targets", f"{summary.get('ready_required_target_count', 0)}/{summary.get('required_target_count', 0)}"),
            ("attempts", str(summary.get("attempt_count", 0))),
            ("board failures", str(summary.get("board_failure_count", 0))),
            ("continued after failure", yes_no(summary.get("continued_after_board_failure"))),
            ("access denied attempts", str(summary.get("access_denied_attempt_count", 0))),
            ("route mismatch attempts", str(summary.get("route_mismatch_attempt_count", 0))),
            ("live discovery", f"{summary.get('live_discovery_status', 'missing')} / ready {yes_no(summary.get('live_discovery_ready'))} / quality {summary.get('live_discovery_quality_status', 'missing')} / listed {summary.get('live_discovery_listed_expected_count', 0)} / missing {summary.get('live_discovery_missing_expected_count', 0)}"),
            ("effective board scope", f"{summary.get('effective_board_scope_source', 'missing')} / research {summary.get('effective_board_scope_research_allowed_count', 0)} / unavailable {summary.get('effective_board_scope_unavailable_count', 0)} / fallback {yes_no(summary.get('effective_board_scope_last_success_fallback_used'))} / fresh {yes_no(summary.get('effective_board_scope_last_success_fresh_within_sla'))}"),
            ("partial refresh", f"{partial.get('successful_board_count', 0)}/{partial.get('attempted_board_count', 0)} / {partial.get('freshness_status', 'missing')}"),
            ("board recovery matrix", f"{summary.get('board_recovery_matrix_count', 0)} rows / research-only {summary.get('board_recovery_research_only_ready_count', 0)} / auto {summary.get('board_recovery_auto_retry_count', 0)} / match repair {summary.get('board_recovery_match_repair_count', 0)} / unavailable {summary.get('board_recovery_unavailable_count', 0)} / partial {summary.get('board_recovery_partial_coverage_count', 0)} / staged {summary.get('board_recovery_staged_validation_error_count', 0)}"),
            ("Matches repair validation", f"{summary.get('matches_repair_validation_status', 'missing')} / {summary.get('matches_repair_validation_match_count', 0)} matches / {summary.get('matches_repair_validation_market_count', 0)} markets / errors {summary.get('matches_repair_validation_error_count', 0)}"),
            ("legacy headed fallback attempts", str(summary.get("headed_fallback_attempt_count", 0))),
            ("backfill queue", str(summary.get("backfill_queue_count", 0))),
            ("primary blocker", str(executive.get("primary_blocker", ""))),
        ],
        charts=charts,
        table_headers=["阶段", "状态", "证据", "下一步"],
        table_rows=[
            [str(row.get("title", "")), str(row.get("status", "")), str(row.get("evidence", "")), str(row.get("next_action", ""))]
            for row in phase_rows
        ],
        extra_tables=[
            {
                "title": "板块级恢复矩阵",
                "headers": ["板块", "live", "raw", "partial", "staged错误", "修复验证", "action", "自动重试", "成功门禁"],
                "rows": [
                    [
                        str(row.get("name", "")),
                        str(row.get("live_nav_status", "")),
                        str(row.get("raw_status", "")),
                        str(row.get("partial_result", "")),
                        str(row.get("staged_validation_error_count", 0)),
                        str(row.get("repair_validation_status", "")),
                        str(row.get("automation_action", "")),
                        yes_no(row.get("safe_to_retry_now")),
                        str(row.get("success_gate", "")),
                    ]
                    for row in board_matrix
                ],
            },
            *(
                [
                    {
                        "title": "Matches Repair Live Validation",
                        "headers": ["项目", "值"],
                        "rows": [
                            ["status", str(repair_validation.get("status", "missing"))],
                            ["passed", yes_no(repair_validation.get("passed"))],
                            ["scope", str(repair_validation.get("scope", ""))],
                            ["trigger", str(repair_validation.get("trigger", ""))],
                            ["matches", str(repair_validation.get("match_count", 0))],
                            ["markets", str(repair_validation.get("market_count", 0))],
                            ["errors", str(repair_validation.get("error_count", 0))],
                            ["validated_matches", "；".join(repair_validation.get("validated_matches") or [])],
                            ["guard", str(repair_validation.get("read_only_guard", ""))],
                        ],
                    }
                ]
                if repair_validation
                else []
            ),
            {
                "title": "Partial Raw Freshness Evidence",
                "headers": ["项目", "值"],
                "rows": [
                    ["status", str(partial.get("status", ""))],
                    ["freshness_status", str(partial.get("freshness_status", ""))],
                    ["fresh_within_sla", yes_no(partial.get("fresh_within_sla"))],
                    ["age_hours", str(partial.get("age_hours", ""))],
                    ["freshness_sla_hours", str(partial.get("freshness_sla_hours", ""))],
                    ["successful_boards", "；".join(partial.get("successful_board_names") or [])],
                    ["failed_boards", "；".join(partial.get("failed_board_names") or [])],
                    ["execution_allowed", yes_no(partial.get("execution_allowed"))],
                    ["current_research_only_allowed", yes_no(partial.get("current_research_only_allowed"))],
                    ["historical_research_evidence_available", yes_no(partial.get("historical_research_evidence_available"))],
                ],
            },
            {
                "title": "目标板块状态",
                "headers": ["板块", "状态", "fresh", "valid", "blocker"],
                "rows": [
                    [
                        str(row.get("name", "")),
                        str(row.get("status", "")),
                        yes_no(row.get("raw_fresh")),
                        yes_no(row.get("raw_valid")),
                        ", ".join(row.get("blocker_codes") or []),
                    ]
                    for row in target_rows
                ],
            },
            {
                "title": "最近抓取尝试",
                "headers": ["board", "attempt", "exit", "access denied", "error"],
                "rows": [
                    [
                        str(row.get("board_id", "")),
                        str(row.get("attempt", "")),
                        str(row.get("exit_code", "")),
                        yes_no(row.get("access_denied")),
                        str(row.get("error", "")),
                    ]
                    for row in attempts
                ],
            },
            {
                "title": "单板失败隔离",
                "headers": ["顺序", "board", "output", "error"],
                "rows": [
                    [
                        str(row.get("rank", "")),
                        str(row.get("board_id", "")),
                        str(row.get("output", "")),
                        str(row.get("error", "")),
                    ]
                    for row in board_failures
                ],
            },
            {
                "title": "下一次刷新计划",
                "headers": ["顺序", "范围", "触发条件", "模式", "成功门禁"],
                "rows": [
                    [
                        str(row.get("rank", "")),
                        str(row.get("scope", "")),
                        str(row.get("trigger", "")),
                        str(row.get("mode", "")),
                        str(row.get("success_gate", "")),
                    ]
                    for row in retry_plan
                ],
            },
            {
                "title": "新旧恢复变化",
                "headers": ["指标", "当前", "上一版", "变化"],
                "rows": [
                    [str(row.get("metric", "")), str(row.get("current", "")), str(row.get("previous", "")), str(row.get("delta", ""))]
                    for row in (compare.get("rows") or [])
                ],
            },
        ],
    )


def recovery_action_items(board_matrix: list[dict[str, Any]]) -> list[tuple[str, float]]:
    counts: dict[str, int] = {}
    for row in board_matrix:
        action = str(row.get("automation_action") or "unknown")
        counts[action] = counts.get(action, 0) + 1
    return [(key, float(value)) for key, value in sorted(counts.items(), key=lambda item: item[0])]


def primary_blocker(raw_health: dict[str, Any], diagnostics: dict[str, Any]) -> str:
    if raw_health.get("ready") is True:
        return "无 raw 阻塞"
    if access_policy_blocked(raw_health, diagnostics, diagnostics.get("attempts") or []):
        return "TAB 拒绝 AI controlled access，公开 raw 自动刷新被合规门禁阻断"
    if has_route_mismatch(raw_health, diagnostics):
        return "TAB live 当前未列出 Australia Markets / deep link 路由到 Matches"
    if any(item.get("access_denied") for item in diagnostics.get("attempts") or []):
        return "TAB match detail 返回 Access Denied"
    codes = raw_health.get("blocker_codes") or []
    return ", ".join(codes) or "raw_refresh_not_ready"


def recommended_next_action(raw_health: dict[str, Any], diagnostics: dict[str, Any]) -> str:
    if raw_health.get("ready") is True:
        return "raw 已就绪，可以继续私有持仓快照和安全补跑。"
    if access_policy_blocked(raw_health, diagnostics, diagnostics.get("attempts") or []):
        return "停止自动公开 raw；不要 headed fallback/验证码绕过/指纹伪装。接入官方/授权数据源或用户导出导入；当前只保留 research-only 诊断。"
    if has_route_mismatch(raw_health, diagnostics):
        return "重新发现 TAB Soccer live board list；若 Australia Markets 仍缺失，保持该板块 unavailable，不用旧盘口生成下注建议。"
    if any(item.get("access_denied") for item in diagnostics.get("attempts") or []):
        return "TAB 返回 Access Denied；自动 raw 保持 fail-closed，等待官方/授权数据源或用户导出导入。"
    return raw_health.get("recommended_next_action") or "接入授权 raw 或导入用户导出快照后再重跑日报门禁。"


def access_policy_blocked(raw_health: dict[str, Any], diagnostics: dict[str, Any], attempts: list[dict[str, Any]]) -> bool:
    if "ai_controlled_access_rejected" in (raw_health.get("blocker_codes") or []):
        return True
    access_policy = raw_health.get("access_policy") if isinstance(raw_health.get("access_policy"), dict) else {}
    if access_policy.get("status") == "blocked_by_access_policy":
        return True
    if diagnostics.get("access_policy_status") == "blocked_by_access_policy":
        return True
    return any(
        item.get("ai_controlled_access_rejected") or item.get("access_policy_status") == "blocked_by_access_policy"
        for item in attempts
        if isinstance(item, dict)
    )


def has_route_mismatch(raw_health: dict[str, Any], diagnostics: dict[str, Any]) -> bool:
    if "route_mismatch" in (raw_health.get("blocker_codes") or []):
        return True
    if looks_like_route_mismatch(raw_health.get("refresh_error") or ""):
        return True
    for item in diagnostics.get("attempts") or []:
        if item.get("route_mismatch"):
            return True
        if looks_like_route_mismatch(item.get("error") or item.get("stderr_tail") or ""):
            return True
    return False


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def short_text(value: Any, limit: int) -> str:
    text = str(value or "").replace("\n", " ")
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def yes_no(value: Any) -> str:
    return "是" if bool(value) else "否"


def md(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")
