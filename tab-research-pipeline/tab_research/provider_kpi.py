from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .provider_alternate_plan import PROVIDER_ALTERNATE_PLAN_JSON_LATEST, build_provider_alternate_plan
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


PROVIDER_KPI_JSON_LATEST = "provider_kpi_latest.json"
PROVIDER_KPI_MD_LATEST = "provider_kpi_latest.md"
PROVIDER_KPI_PDF_LATEST = "provider_kpi_latest.pdf"
ODDS_PROVIDER_BLOCKED_LATEST = "odds_provider_blocked_latest.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")


def write_provider_kpi_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_provider_kpi(output_dir)
    json_path = output_dir / PROVIDER_KPI_JSON_LATEST
    md_path = output_dir / PROVIDER_KPI_MD_LATEST
    pdf_path = output_dir / PROVIDER_KPI_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_provider_kpi_markdown(payload))
    pdf_summary = write_provider_kpi_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_provider_kpi(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    coverage = load_json(output_dir / "odds_provider_coverage_latest.json")
    manifest = load_json(output_dir / "odds_provider_raw_latest.json")
    blocked_attempt = load_json(output_dir / ODDS_PROVIDER_BLOCKED_LATEST)
    target = first_matches_target(coverage)
    request_usage = coverage.get("request_usage") or manifest.get("request_usage") or {}
    alternate_plan = load_json(output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST) or build_provider_alternate_plan(output_dir)
    event_count = int(target.get("event_count") or 0)
    market_coverage = target.get("market_coverage") or {}
    rows = build_kpi_rows(coverage, target, request_usage, alternate_plan)
    summary = summarize_rows(rows)
    credit = credit_summary(request_usage)
    refresh_id = coverage.get("refresh_id") or manifest.get("refresh_id") or ""
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "mode": "provider_kpi",
        "executive_status": {
            "status": "ready" if summary["required_ready_count"] == summary["required_count"] else "in_progress",
            "overall_score": summary["average_score"],
            "overall_progress_pct": summary["average_score"],
            "primary_gap": first_gap(rows),
            "recommended_next_action": recommended_next_action(rows, alternate_plan),
        },
        "scope": coverage.get("scope") or manifest.get("scope") or "matches",
        "refresh_id": refresh_id,
        "provider_analysis_ready": bool(target.get("provider_analysis_ready")),
        "formal_publish_allowed": bool(coverage.get("formal_publish_allowed")),
        "full_automation_allowed": bool(coverage.get("full_automation_allowed")),
        "current_executable_new_stake_aud": 0,
        "summary": {
            **summary,
            "event_count": event_count,
            "covered_market_family_count": covered_focus_market_family_count(market_coverage),
            "request_usage": request_usage,
            "credit": credit,
            "alternate_plan": alternate_plan_summary(alternate_plan),
        },
        "market_coverage": market_coverage_rows(event_count, market_coverage),
        "kpi_rows": rows,
        "manual_review_queue": [row for row in rows if row["status"] != "ready"],
        "alternate_plan": compact_alternate_plan(alternate_plan),
        "last_blocked_attempt": compact_blocked_attempt(blocked_attempt, current_refresh_id=refresh_id),
        "source_artifacts": {
            "odds_provider_coverage": "odds_provider_coverage_latest.json" if coverage else "",
            "odds_provider_blocked": ODDS_PROVIDER_BLOCKED_LATEST if blocked_attempt else "",
            "odds_provider_raw": "odds_provider_raw_latest.json" if manifest else "",
            "provider_alternate_plan": PROVIDER_ALTERNATE_PLAN_JSON_LATEST if alternate_plan else "",
        },
        "truthfulness_note": "Provider KPI 只证明授权数据源覆盖度和平台就绪度；不自动下注，也不把未覆盖盘口伪装为可执行建议。",
        "automation_boundary_note": "未通过 formal publish 和人工 TAB final verification 前，新增可执行下注金额保持 AUD 0。",
    }
    return sanitize_public_payload(payload)


def build_kpi_rows(
    coverage: dict[str, Any],
    target: dict[str, Any],
    request_usage: dict[str, Any],
    alternate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    event_count = int(target.get("event_count") or 0)
    market_coverage = target.get("market_coverage") or {}
    request_kinds = request_usage.get("request_kind_counts") or {}
    return [
        kpi_row(
            "authorized_provider_raw",
            "授权 provider raw",
            "ready" if target.get("provider_analysis_ready") else "blocked",
            1.0 if target.get("provider_analysis_ready") else 0.0,
            f"provider_analysis_ready={bool(target.get('provider_analysis_ready'))}",
            "The Odds API / TAB-labeled payload 已进入 staging。",
            "先恢复 provider live refresh。",
        ),
        market_row("result_coverage", "Result 覆盖", event_count, market_coverage.get("Result"), required_ratio=0.90),
        market_row("handicap_coverage", "Handicap 覆盖", event_count, market_coverage.get("Handicap"), required_ratio=0.50, partial_ok=True),
        market_row("total_ou_coverage", "Total Score O/U 覆盖", event_count, market_coverage.get("Total Goals Over/Under"), required_ratio=0.70),
        market_row("team_total_ou_coverage", "Team Total Score O/U 覆盖", event_count, market_coverage.get("Team Total Goals Over/Under"), required_ratio=0.50),
        kpi_row(
            "alternate_market_probe",
            "Alternate markets 探测",
            "ready" if int(request_kinds.get("event_markets") or 0) > 0 else "planned",
            1.0 if int(request_kinds.get("event_markets") or 0) > 0 else 0.35,
            f"event_market_probe_count={int(request_kinds.get('event_markets') or 0)}",
            "已用 /events/{eventId}/markets 探测单场可用 market keys。",
            "用 --event-market-probe-limit 小样本探测，再按可用 markets 拉 event odds。",
        ),
        kpi_row(
            "alternate_probe_plan",
            "Alternate markets 补齐计划",
            alternate_plan_kpi_status(alternate_plan),
            alternate_plan_kpi_score(alternate_plan),
            alternate_plan_evidence(alternate_plan),
            "已生成 credit-aware 下一批 probe 队列、停止条件和推荐命令。",
            alternate_plan_next_action(alternate_plan),
        ),
        kpi_row(
            "provider_credit_budget",
            "Provider credit 预算",
            credit_status(request_usage),
            credit_score(request_usage),
            credit_evidence(request_usage),
            "剩余额度支持继续小样本探测。",
            "把 probe limit 控制在小样本，优先推荐候选场次。",
        ),
        kpi_row(
            "formal_publish_gate",
            "正式 raw 发布门禁",
            "ready" if coverage.get("formal_publish_allowed") else "blocked",
            1.0 if coverage.get("formal_publish_allowed") else 0.0,
            f"formal_publish_allowed={bool(coverage.get('formal_publish_allowed'))}",
            "已通过 TAB 人工最终校验，可发布当前 scope raw。",
            "对推荐候选做 TAB 人工最终校验 hash。",
        ),
        kpi_row(
            "full_automation_gate",
            "完整 automation 门禁",
            "ready" if coverage.get("full_automation_allowed") else "blocked",
            1.0 if coverage.get("full_automation_allowed") else 0.0,
            f"full_automation_allowed={bool(coverage.get('full_automation_allowed'))}",
            "完整日报 gate 通过。",
            "补齐 raw、持仓、正式日报、CLV 数据闭环。",
        ),
    ]


def alternate_plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    credit = plan.get("credit_policy") or {}
    decision = plan.get("operational_decision") or {}
    return {
        "status": plan.get("status", "missing"),
        "probe_queue_count": plan.get("probe_queue_count", 0),
        "recommended_batch_size": credit.get("recommended_batch_size", 0),
        "estimated_next_batch_credit_floor": credit.get("estimated_next_batch_credit_floor"),
        "estimated_next_batch_credit_ceiling": credit.get("estimated_next_batch_credit_ceiling"),
        "fallback_queue_count": plan.get("fallback_queue_count", 0),
        "recommended_next_action": plan.get("recommended_next_action", ""),
        "recommended_command": plan.get("recommended_command", ""),
        "operational_decision_status": decision.get("status", ""),
        "operational_decision_title": decision.get("title", ""),
        "operational_primary_action": decision.get("primary_action", ""),
    }


def compact_alternate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    summary = alternate_plan_summary(plan)
    return {
        **summary,
        "operational_decision": plan.get("operational_decision") or {},
        "market_family_gaps": plan.get("market_family_gaps", []),
        "next_probe_queue_preview": (plan.get("next_probe_queue") or [])[:5],
        "fallback_queue_preview": (plan.get("fallback_queue") or [])[:5],
        "stop_conditions": plan.get("stop_conditions", []),
    }


def compact_blocked_attempt(payload: dict[str, Any], *, current_refresh_id: str = "") -> dict[str, Any]:
    if not payload:
        return {}
    blocked_refresh_id = str(payload.get("refresh_id", ""))
    is_current = bool(current_refresh_id and blocked_refresh_id == current_refresh_id)
    return {
        "provider": payload.get("provider", ""),
        "refresh_id": blocked_refresh_id,
        "blocker_code": payload.get("blocker_code", ""),
        "is_current_refresh_blocker": is_current,
        "stale_history_only": bool(current_refresh_id and blocked_refresh_id and not is_current),
        "last_good_coverage_preserved": bool(payload.get("last_good_coverage_preserved")),
        "next_safe_action": payload.get("next_safe_action", ""),
    }


def alternate_plan_kpi_status(plan: dict[str, Any]) -> str:
    status = str(plan.get("status") or "missing")
    if status == "ready":
        return "ready"
    if status == "in_progress":
        return "partial"
    if status == "fallback_required":
        return "blocked"
    if status == "missing":
        return "planned"
    return "blocked"


def alternate_plan_kpi_score(plan: dict[str, Any]) -> float:
    status = alternate_plan_kpi_status(plan)
    return {"ready": 1.0, "partial": 0.65, "planned": 0.35, "blocked": 0.0}.get(status, 0.0)


def alternate_plan_evidence(plan: dict[str, Any]) -> str:
    summary = alternate_plan_summary(plan)
    fallback = summary.get("fallback_queue_count")
    return (
        f"status={summary.get('status')} / queue={summary.get('probe_queue_count')} / "
        f"fallback={fallback} / "
        f"batch={summary.get('recommended_batch_size')} / "
        f"credit={summary.get('estimated_next_batch_credit_floor')}-{summary.get('estimated_next_batch_credit_ceiling')}"
    )


def alternate_plan_next_action(plan: dict[str, Any]) -> str:
    status = str(plan.get("status") or "")
    if status == "fallback_required":
        return str(
            plan.get("recommended_next_action")
            or "The Odds API 队列已耗尽；剩余盘口转 OpticOdds 官方访问或 TAB 人工最终校验。"
        )
    if status == "blocked":
        return str(plan.get("recommended_next_action") or "暂停 provider probe；检查 credit、endpoint 或人工校验路径。")
    return "按计划小批量 probe，不要全量扫 68 场；Team Total 连续 0 覆盖则切换 provider 或人工校验。"


def market_row(row_id: str, name: str, event_count: int, count_value: Any, *, required_ratio: float, partial_ok: bool = False) -> dict[str, Any]:
    count = int(count_value or 0)
    ratio = (count / event_count) if event_count else 0.0
    if ratio >= required_ratio:
        status = "ready"
        score = 1.0
        next_action = f"{name} 已达到可用覆盖阈值；后续只做监控或候选场次人工复核。"
    elif count > 0 and partial_ok:
        status = "partial"
        score = 0.55
        next_action = f"继续探测 event markets / alternate markets 补齐 {name}。"
    elif count > 0:
        status = "partial"
        score = min(0.75, max(0.25, ratio / required_ratio))
        next_action = f"继续探测 event markets / alternate markets 补齐 {name}。"
    else:
        status = "blocked"
        score = 0.0
        next_action = f"切换授权 provider 或人工校验补齐 {name}。"
    return kpi_row(
        row_id,
        name,
        status,
        score,
        f"{count}/{event_count} ({pct(ratio)})",
        f"{name} 已达到可用覆盖阈值。",
        next_action,
        coverage_ratio=ratio,
        covered_count=count,
        total_count=event_count,
    )


def kpi_row(
    row_id: str,
    name: str,
    status: str,
    score: float,
    evidence: str,
    ready_definition: str,
    next_action: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": row_id,
        "name": name,
        "status": status,
        "ready": status == "ready",
        "score": round(float(score), 4),
        "severity": severity_for_status(status),
        "evidence": evidence,
        "ready_definition": ready_definition,
        "next_action": next_action,
        **extra,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = rows
    ready_count = len([row for row in required if row["status"] == "ready"])
    partial_count = len([row for row in required if row["status"] == "partial"])
    blocked_count = len([row for row in required if row["status"] == "blocked"])
    score = sum(float(row.get("score") or 0) for row in required) / len(required) if required else 0.0
    return {
        "required_count": len(required),
        "required_ready_count": ready_count,
        "partial_count": partial_count,
        "blocked_count": blocked_count,
        "average_score": round(score, 4),
    }


def market_coverage_rows(event_count: int, coverage: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for market in ["Result", "Handicap", "Total Goals Over/Under", "Team Total Goals Over/Under"]:
        count = int(coverage.get(market) or 0)
        rows.append(
            {
                "market": market,
                "covered_count": count,
                "event_count": event_count,
                "coverage_ratio": round(count / event_count, 4) if event_count else 0.0,
            }
        )
    return rows


def covered_focus_market_family_count(coverage: dict[str, Any]) -> int:
    focus = ["Result", "Handicap", "Total Goals Over/Under", "Team Total Goals Over/Under"]
    return len([market for market in focus if int(coverage.get(market) or 0) > 0])


def credit_summary(request_usage: dict[str, Any]) -> dict[str, Any]:
    used = to_int(request_usage.get("reported_requests_used_max"))
    remaining = to_int(request_usage.get("reported_requests_remaining_min"))
    last = to_int(request_usage.get("reported_last_request_cost"))
    monthly_limit = used + remaining if used is not None and remaining is not None else None
    return {
        "reported_used": used,
        "reported_remaining": remaining,
        "reported_last_request_cost": last,
        "inferred_monthly_limit": monthly_limit,
        "remaining_ratio": round(remaining / monthly_limit, 4) if remaining is not None and monthly_limit else None,
    }


def credit_status(request_usage: dict[str, Any]) -> str:
    ratio = credit_summary(request_usage).get("remaining_ratio")
    if ratio is None:
        return "watch"
    if ratio >= 0.50:
        return "ready"
    if ratio >= 0.20:
        return "partial"
    return "blocked"


def credit_score(request_usage: dict[str, Any]) -> float:
    status = credit_status(request_usage)
    return {"ready": 1.0, "partial": 0.5, "watch": 0.35, "blocked": 0.0}.get(status, 0.0)


def credit_evidence(request_usage: dict[str, Any]) -> str:
    credit = credit_summary(request_usage)
    return (
        f"used={credit.get('reported_used')} / remaining={credit.get('reported_remaining')} / "
        f"last={credit.get('reported_last_request_cost')} / inferred_limit={credit.get('inferred_monthly_limit')}"
    )


def first_matches_target(coverage: dict[str, Any]) -> dict[str, Any]:
    for row in coverage.get("targets") or []:
        if row.get("board_id") == "world_cup_matches":
            return row
    targets = coverage.get("targets") or []
    return targets[0] if targets else {}


def first_gap(rows: list[dict[str, Any]]) -> str:
    for status in ("blocked", "partial", "planned", "watch"):
        for row in rows:
            if row.get("status") == status:
                return f"{row.get('name')}: {row.get('evidence')}"
    return "全部 provider KPI 已达到 ready。"


def recommended_next_action(rows: list[dict[str, Any]], alternate_plan: dict[str, Any] | None = None) -> str:
    plan_action = str((alternate_plan or {}).get("recommended_next_action") or "")
    if plan_action and any(
        family.get("status") == "fallback_required"
        for family in (alternate_plan or {}).get("market_family_gaps") or []
        if isinstance(family, dict)
    ):
        return plan_action
    for status in ("blocked", "partial", "planned", "watch"):
        for row in rows:
            if row.get("status") == status:
                return str(row.get("next_action") or "")
    return "进入 TAB 人工最终校验和日报门禁复核。"


def severity_for_status(status: str) -> str:
    return {"ready": "low", "partial": "medium", "planned": "medium", "watch": "medium", "blocked": "high"}.get(status, "medium")


def render_provider_kpi_markdown(payload: dict[str, Any]) -> str:
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    lines = [
        "# Provider KPI",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{executive.get('status', '')}`",
        f"- overall_score: `{pct(executive.get('overall_score'))}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- provider_analysis_ready: `{bool(payload.get('provider_analysis_ready'))}`",
        f"- formal_publish_allowed: `{bool(payload.get('formal_publish_allowed'))}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        f"- primary_gap: {md(executive.get('primary_gap'))}",
        f"- next_action: {md(executive.get('recommended_next_action'))}",
        "",
        "## Summary",
        "",
        f"- required_ready: `{summary.get('required_ready_count', 0)}/{summary.get('required_count', 0)}`",
        f"- event_count: `{summary.get('event_count', 0)}`",
        f"- covered_market_family_count: `{summary.get('covered_market_family_count', 0)}`",
        "",
        "## Market Coverage",
        "",
        "| Market | Covered | Coverage |",
        "|---|---:|---:|",
    ]
    for row in payload.get("market_coverage") or []:
        lines.append(
            f"| {md(row.get('market'))} | {row.get('covered_count', 0)}/{row.get('event_count', 0)} | {pct(row.get('coverage_ratio'))} |"
        )
    lines.extend(["", "## KPI Rows", "", "| KPI | Status | Score | Evidence | Next Action |", "|---|---|---:|---|---|"])
    for row in payload.get("kpi_rows") or []:
        lines.append(
            f"| {md(row.get('name'))} | `{row.get('status', '')}` | {pct(row.get('score'))} | {md(row.get('evidence'))} | {md(row.get('next_action'))} |"
        )
    blocked = payload.get("last_blocked_attempt") or {}
    if blocked:
        blocked_heading = "Last Blocked Provider Attempt"
        if blocked.get("stale_history_only"):
            blocked_heading += " (History Only)"
        lines.extend(
            [
                "",
                f"## {blocked_heading}",
                "",
                f"- provider: `{blocked.get('provider', '')}`",
                f"- blocker_code: `{blocked.get('blocker_code', '')}`",
                f"- is_current_refresh_blocker: `{bool(blocked.get('is_current_refresh_blocker'))}`",
                f"- last_good_coverage_preserved: `{bool(blocked.get('last_good_coverage_preserved'))}`",
                f"- next_safe_action: {md(blocked.get('next_safe_action'))}",
            ]
        )
    plan = payload.get("alternate_plan") or {}
    lines.extend(
        [
            "",
            "## Alternate Plan",
            "",
            f"- status: `{plan.get('status', '')}`",
            f"- probe_queue_count: `{plan.get('probe_queue_count', 0)}`",
            f"- recommended_batch_size: `{plan.get('recommended_batch_size', 0)}`",
            f"- estimated_next_batch_credit: `{plan.get('estimated_next_batch_credit_floor')}-{plan.get('estimated_next_batch_credit_ceiling')}`",
            "",
            "```bash",
            str(plan.get("recommended_command") or ""),
            "```",
        ]
    )
    lines.extend(["", f"Truthfulness: {payload.get('truthfulness_note', '')}"])
    return "\n".join(lines) + "\n"


def write_provider_kpi_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    executive = payload.get("executive_status") or {}
    summary = payload.get("summary") or {}
    credit = summary.get("credit") or {}
    plan = payload.get("alternate_plan") or {}
    table_rows = [
        [
            str(row.get("name", "")),
            str(row.get("status", "")),
            pct(row.get("score")),
            str(row.get("evidence", "")),
            str(row.get("next_action", "")),
        ]
        for row in payload.get("kpi_rows") or []
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Provider KPI",
        subtitle="授权 provider 覆盖、credit、alternate markets 和正式发布门禁状态；不自动下注。",
        summary_rows=[
            ("Status", str(executive.get("status", ""))),
            ("Progress", pct(executive.get("overall_score"))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Events", str(summary.get("event_count", 0))),
            ("Credit Remaining", str(credit.get("reported_remaining"))),
            ("Probe Queue", str(plan.get("probe_queue_count", 0))),
            ("Probe Batch", str(plan.get("recommended_batch_size", 0))),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Market Coverage",
                [(row.get("market", ""), float(row.get("coverage_ratio") or 0) * 100) for row in payload.get("market_coverage") or []],
                "#1D4ED8",
            ),
            chart_from_items(
                "KPI Score",
                [(row.get("name", ""), float(row.get("score") or 0) * 100) for row in payload.get("kpi_rows") or []],
                "#0F7B4F",
            ),
        ],
        table_headers=["KPI", "Status", "Score", "Evidence", "Next Action"],
        table_rows=table_rows,
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "待校准"


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
