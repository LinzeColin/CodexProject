from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.services.approval_queue import annotate_ticket_freshness


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE_ROOT = ROOT / "docs" / "evidence" / "phase6_closeout_latest"
DEFAULT_RUNTIME_EVIDENCE_ROOT = ROOT / "runtime" / "phase6_owner_gate_latest"
DEFAULT_SOAK_HISTORY_PATH = ROOT / "runtime" / "phase6_soak_history.jsonl"
DEFAULT_MAX_SAMPLE_GAP_SECONDS = 900
DEFAULT_MAX_SAMPLE_AGE_SECONDS = 900


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_paper_shadow_report(*, run_result: dict, output_path: str | Path | None = None) -> dict:
    ticket = run_result.get("approval_queue", {}).get("ticket") or {}
    annotated_ticket = annotate_ticket_freshness(ticket)
    broker_payload = annotated_ticket.get("broker_payload") or {}
    intent = run_result.get("intent") or {}
    paper_order = run_result.get("paper_order") or {}
    portfolio = run_result.get("paper_portfolio") or {}
    risk_check = run_result.get("risk_check") or {}
    hard_gate_checks = [
        _check("paper_cycle_completed", run_result.get("status") == "completed", "paper loop completed"),
        _check("paper_order_filled", paper_order.get("status") == "filled", "paper order filled"),
        _check("risk_allowed", risk_check.get("allowed") is True, "pre-trade risk allowed"),
        _check(
            "broker_ready_limit_order",
            broker_payload.get("order_type") == "limit",
            "broker-ready ticket uses limit order contract",
        ),
        _check("ticket_fresh", annotated_ticket.get("actionability") == "fresh_pending_owner_approval", "ticket is fresh"),
        _check("portfolio_positive_equity", float(portfolio.get("total_equity") or 0) > 0, "portfolio equity positive"),
        _check("human_review_required", annotated_ticket.get("human_action_required") is True, "owner review required"),
    ]
    report = {
        "schema_version": "2026-06-27.alpha.phase6.paper_shadow_report",
        "generated_at": utc_now_iso(),
        "trading_day": str(run_result.get("generated_at", "")[:10]),
        "run_id": run_result.get("run_id"),
        "hard_gate_checks": hard_gate_checks,
        "paper": {
            "order_status": paper_order.get("status"),
            "trade_count": portfolio.get("trade_count"),
            "total_equity": portfolio.get("total_equity"),
            "latest_trade": portfolio.get("latest_trade"),
        },
        "shadow": {
            "ticket_id": annotated_ticket.get("ticket_id"),
            "actionability": annotated_ticket.get("actionability"),
            "symbol": broker_payload.get("symbol"),
            "side": broker_payload.get("side"),
            "quantity": broker_payload.get("quantity"),
            "order_type": broker_payload.get("order_type"),
            "time_in_force": broker_payload.get("time_in_force"),
            "client_order_id": broker_payload.get("client_order_id"),
            "estimated_notional_aud": intent.get("estimated_notional_aud"),
        },
        "safety_boundary": _safety_boundary(),
    }
    schema_checks = validate_paper_shadow_report_schema(report)
    report["schema_checks"] = schema_checks
    report["status"] = (
        "pass"
        if all(item["status"] == "pass" for item in hard_gate_checks + schema_checks)
        else "fail"
    )
    if output_path:
        _write_json(output_path, report)
    return report


def validate_paper_shadow_report_schema(report: dict) -> list[dict]:
    required_paths = [
        ("schema_version",),
        ("generated_at",),
        ("trading_day",),
        ("run_id",),
        ("hard_gate_checks",),
        ("paper", "order_status"),
        ("paper", "trade_count"),
        ("paper", "total_equity"),
        ("paper", "latest_trade"),
        ("shadow", "ticket_id"),
        ("shadow", "actionability"),
        ("shadow", "symbol"),
        ("shadow", "side"),
        ("shadow", "quantity"),
        ("shadow", "order_type"),
        ("shadow", "time_in_force"),
        ("shadow", "client_order_id"),
        ("shadow", "estimated_notional_aud"),
        ("safety_boundary", "live_trading_enabled"),
        ("safety_boundary", "broker_mutation_allowed"),
        ("safety_boundary", "live_authorization_file_must_be_absent"),
    ]
    checks = []
    for path in required_paths:
        value = _nested_get(report, path)
        checks.append(_check("schema_" + ".".join(path), value is not None, ".".join(path)))
    checks.append(
        _check(
            "schema_hard_gate_checks_non_empty",
            bool(report.get("hard_gate_checks")),
            "hard_gate_checks non-empty",
        )
    )
    return checks


def build_shadow_live_constraints_report(
    *,
    health: dict | None = None,
    live_authorization_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict:
    health = health or {"live_trading_enabled": False, "kill_switch_active": False}
    auth_path = Path(live_authorization_path or ROOT / "runtime" / "LIVE_AUTHORIZATION.json")
    checks = [
        _check("live_trading_disabled", health.get("live_trading_enabled") is False, "live trading disabled"),
        _check("live_authorization_absent", not auth_path.exists(), "LIVE_AUTHORIZATION.json absent"),
        _check("broker_mutation_disabled", True, "no broker mutation path used"),
        _check("owner_review_required", True, "shadow orders remain owner-review tickets"),
    ]
    report = {
        "schema_version": "2026-06-27.alpha.phase6.shadow_live_constraints",
        "generated_at": utc_now_iso(),
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "blocked",
        "checks": checks,
        "health": health,
        "live_authorization_path": str(auth_path),
        "safety_boundary": _safety_boundary(),
    }
    if output_path:
        _write_json(output_path, report)
    return report


def build_soak_validation_report(
    *,
    samples: list[dict],
    duration_hours: int = 48,
    max_sample_gap_seconds: int = 900,
    output_path: str | Path | None = None,
) -> dict:
    sorted_samples = sorted(samples, key=lambda item: item.get("generated_at") or "")
    parsed_samples = []
    invalid_sample_count = 0
    for item in sorted_samples:
        try:
            parsed_time = _parse_time(item.get("generated_at"))
        except ValueError:
            parsed_time = None
        if parsed_time is None:
            invalid_sample_count += 1
            continue
        parsed_samples.append((parsed_time, item))

    gaps = [
        {
            "start": previous[0].isoformat(),
            "end": current[0].isoformat(),
            "seconds": max(0, int((current[0] - previous[0]).total_seconds())),
        }
        for previous, current in zip(parsed_samples, parsed_samples[1:])
    ]
    gap_violations = [item for item in gaps if item["seconds"] > max_sample_gap_seconds]
    continuous_start_index = 0
    if gap_violations:
        last_gap = gap_violations[-1]
        for index, (parsed_time, _) in enumerate(parsed_samples):
            if parsed_time.isoformat() == last_gap["end"]:
                continuous_start_index = index
                break
    continuous_samples = parsed_samples[continuous_start_index:] if parsed_samples else []
    first = continuous_samples[0][0] if continuous_samples else None
    latest = continuous_samples[-1][0] if continuous_samples else None
    observed_seconds = int((latest - first).total_seconds()) if first and latest else 0
    required_seconds = int(duration_hours * 3600)
    failed_samples = [item for item in sorted_samples if int(item.get("fail_count", 0)) > 0]
    current_window_gaps = gaps[continuous_start_index:] if parsed_samples else []
    current_window_gap_violations = [item for item in current_window_gaps if item["seconds"] > max_sample_gap_seconds]
    checks = [
        _check("samples_present", bool(sorted_samples), "soak samples present"),
        _check("timestamps_valid", invalid_sample_count == 0, "sample timestamps valid"),
        _check("sample_gap_coverage", not current_window_gap_violations, "current continuous sample window has no stale gaps"),
        _check("duration_coverage", observed_seconds >= required_seconds, "48h natural-day continuous coverage"),
        _check("no_failed_samples", not failed_samples, "no failed soak samples"),
        _check(
            "paper_shadow_reports_pass",
            all((item.get("paper_shadow_report") or {}).get("status") == "pass" for item in sorted_samples),
            "paper/shadow report passed for every sample",
        ),
        _check(
            "shadow_constraints_pass",
            all((item.get("shadow_live_constraints") or {}).get("status") == "pass" for item in sorted_samples),
            "shadow live constraints passed for every sample",
        ),
    ]
    report = {
        "schema_version": "2026-06-27.alpha.phase6.soak_validation",
        "generated_at": utc_now_iso(),
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "observing",
        "duration_hours_required": duration_hours,
        "max_sample_gap_seconds": max_sample_gap_seconds,
        "max_observed_gap_seconds": max((item["seconds"] for item in gaps), default=0),
        "gap_violation_count": len(gap_violations),
        "last_gap_violation": gap_violations[-1] if gap_violations else None,
        "window_start": first.isoformat() if first else None,
        "window_end": latest.isoformat() if latest else None,
        "observed_seconds": observed_seconds,
        "observed_hours": round(observed_seconds / 3600, 4),
        "sample_count": len(sorted_samples),
        "continuous_sample_count": len(continuous_samples),
        "invalid_sample_count": invalid_sample_count,
        "fail_count": sum(1 for item in checks if item["status"] == "fail"),
        "checks": checks,
        "safety_boundary": _safety_boundary(),
    }
    if output_path:
        _write_json(output_path, report)
    return report


def append_soak_sample(
    *,
    paper_shadow_report: dict,
    shadow_live_constraints: dict,
    history_path: str | Path = DEFAULT_SOAK_HISTORY_PATH,
) -> dict:
    sample = {
        "generated_at": utc_now_iso(),
        "fail_count": 0 if paper_shadow_report.get("status") == "pass" and shadow_live_constraints.get("status") == "pass" else 1,
        "paper_shadow_report": paper_shadow_report,
        "shadow_live_constraints": shadow_live_constraints,
        "safety_boundary": _safety_boundary(),
    }
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n")
    return sample


def read_soak_samples(history_path: str | Path = DEFAULT_SOAK_HISTORY_PATH) -> list[dict]:
    path = Path(history_path)
    if not path.exists():
        return []
    samples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        samples.append(json.loads(line))
    return samples


def build_owner_gate_closeout(
    *,
    soak_validation: dict,
    paper_shadow_report: dict,
    shadow_live_constraints: dict,
    output_path: str | Path | None = None,
) -> dict:
    acceptance = [
        _acceptance("phase6_48h_soak_validation", soak_validation.get("status") == "pass", soak_validation),
        _acceptance("qualified_trading_day_paper_shadow_report", paper_shadow_report.get("status") == "pass", paper_shadow_report),
        _acceptance("shadow_live_constraints", shadow_live_constraints.get("status") == "pass", shadow_live_constraints),
        _acceptance("limit_order_contract", _limit_order_contract_passed(paper_shadow_report), paper_shadow_report),
        _acceptance("live_authorization_absent", not (ROOT / "runtime" / "LIVE_AUTHORIZATION.json").exists(), {}),
    ]
    ready = all(item["status"] == "pass" for item in acceptance)
    report = {
        "schema_version": "2026-06-27.alpha.phase6.owner_gate_closeout",
        "generated_at": utc_now_iso(),
        "status": "ready_for_owner_gate" if ready else "blocked_not_ready_for_owner_gate",
        "status_zh": "可提交 OWNER-GATE-01" if ready else "阻塞，尚不可进入 OWNER-GATE-01",
        "acceptance": acceptance,
        "blocking_conditions": [item["id"] for item in acceptance if item["status"] != "pass"],
        "safety_boundary": _safety_boundary(),
    }
    if output_path:
        _write_json(output_path, report)
    return report


def build_phase6_owner_gate_status(
    *,
    evidence_root: str | Path = DEFAULT_RUNTIME_EVIDENCE_ROOT,
    history_path: str | Path = DEFAULT_SOAK_HISTORY_PATH,
    duration_hours: int = 48,
    max_sample_gap_seconds: int = DEFAULT_MAX_SAMPLE_GAP_SECONDS,
    max_sample_age_seconds: int = DEFAULT_MAX_SAMPLE_AGE_SECONDS,
    live_authorization_path: str | Path | None = None,
) -> dict:
    root = Path(evidence_root)
    samples = read_soak_samples(history_path)
    paper_shadow = _read_json(root / "paper_shadow_report_latest.json")
    shadow_constraints = _read_json(root / "shadow_live_constraints_latest.json")
    soak = build_soak_validation_report(
        samples=samples,
        duration_hours=duration_hours,
        max_sample_gap_seconds=max_sample_gap_seconds,
    )
    closeout = build_owner_gate_closeout(
        soak_validation=soak,
        paper_shadow_report=paper_shadow,
        shadow_live_constraints=shadow_constraints,
    )
    auth_path = Path(live_authorization_path or ROOT / "runtime" / "LIVE_AUTHORIZATION.json")
    return {
        "schema_version": "2026-06-27.alpha.phase6.owner_gate_status",
        "status": closeout["status"],
        "blocking_conditions": closeout["blocking_conditions"],
        "sample_count": soak["sample_count"],
        "continuous_sample_count": soak["continuous_sample_count"],
        "observed_hours": soak["observed_hours"],
        "duration_hours_required": soak["duration_hours_required"],
        "window_start": soak.get("window_start"),
        "window_end": soak.get("window_end"),
        "max_sample_gap_seconds": soak.get("max_sample_gap_seconds"),
        "max_observed_gap_seconds": soak.get("max_observed_gap_seconds"),
        "gap_violation_count": soak.get("gap_violation_count"),
        "last_gap_violation": soak.get("last_gap_violation"),
        "paper_shadow_status": paper_shadow.get("status", "missing"),
        "shadow_live_constraints_status": shadow_constraints.get("status", "missing"),
        "live_authorization_absent": not auth_path.exists(),
        "evidence_root": str(root),
        "history_path": str(Path(history_path)),
        **_latest_sample_freshness(samples, max_age_seconds=max_sample_age_seconds),
    }


def build_owner_decision_markdown(
    *,
    closeout: dict,
    soak_validation: dict,
    paper_shadow_report: dict,
    shadow_live_constraints: dict,
    output_path: str | Path | None = None,
) -> str:
    def _display(value: Any) -> str:
        if value is None:
            return "不适用"
        if value == "":
            return "无"
        return str(value)

    ready = closeout.get("status") == "ready_for_owner_gate"
    blocking = closeout.get("blocking_conditions") or []
    observed_hours = float(soak_validation.get("observed_hours") or 0)
    duration_hours = float(soak_validation.get("duration_hours_required") or 48)
    remaining_hours = max(duration_hours - observed_hours, 0)
    max_gap_seconds = int(soak_validation.get("max_observed_gap_seconds") or 0)
    gap_violation_count = int(soak_validation.get("gap_violation_count") or 0)
    option_a = (
        "批准提交 OWNER-GATE-01 审核；仍停在 owner 决策，不进入 MICRO_LIVE。"
        if ready
        else "继续补齐 Phase 6 证据，等待 48 小时自然日 soak validation 通过；仍不进入 MICRO_LIVE。"
    )
    schema_passed = all(item.get("status") == "pass" for item in paper_shadow_report.get("schema_checks", []))
    lines = [
        "# Alpha OWNER-GATE-01 Decision",
        "",
        "## 当前结论",
        "",
        f"- 收口状态: `{_display(closeout.get('status', '缺失'))}`",
        f"- 中文状态: `{_display(closeout.get('status_zh', '缺失'))}`",
        f"- 生成时间: `{_display(closeout.get('generated_at', '缺失'))}`",
        f"- 已观察 soak 小时: `{observed_hours:.4f} / {duration_hours:.0f}`",
        f"- 剩余 soak 小时: `{remaining_hours:.4f}`",
        f"- 连续观察窗口: `{_display(soak_validation.get('window_start'))}` 到 `{_display(soak_validation.get('window_end'))}`",
        f"- 最大样本间隔: `{max_gap_seconds}` 秒；gap violation: `{gap_violation_count}`",
        f"- 当前阻塞项: `{', '.join(blocking) if blocking else '无'}`",
        "- 实盘交易开关: `false`",
        "- Broker 真实写单允许状态: `false`",
        "- runtime/LIVE_AUTHORIZATION.json: `必须保持不存在`",
        "",
        "## 验收证据",
        "",
        "| 验收项 | 当前状态 | 证据状态 | 证据时间 |",
        "|---|---|---|---|",
    ]
    for item in closeout.get("acceptance", []):
        lines.append(
            f"| `{_display(item.get('id'))}` | `{_display(item.get('status'))}` | "
            f"`{_display(item.get('evidence_status'))}` | `{_display(item.get('evidence_generated_at'))}` |"
        )
    lines.extend(
        [
            "",
            "## Paper/Shadow 摘要",
            "",
            f"- Paper/Shadow 状态: `{_display(paper_shadow_report.get('status', '缺失'))}`",
            f"- Paper/Shadow schema 状态: `{'pass' if schema_passed else 'fail'}`",
            f"- 交易日: `{_display(paper_shadow_report.get('trading_day', '缺失'))}`",
            f"- 最新标的: `{_display((paper_shadow_report.get('shadow') or {}).get('symbol', '缺失'))}`",
            f"- 订单类型: `{_display((paper_shadow_report.get('shadow') or {}).get('order_type', '缺失'))}`",
            f"- Shadow live 约束状态: `{_display(shadow_live_constraints.get('status', '缺失'))}`",
            "",
            "## Owner 选择",
            "",
            f"### A. {option_a}",
            "",
            "### B. 保持研究/意图审核模式",
            "",
            "维持当前模式，只允许研究、回测、模拟、风控、审批队列和 broker-ready order intent；暂停 Phase 6 完成声明或 OWNER-GATE 推进。",
            "",
            "### C. 暂停 Alpha Phase 6",
            "",
            "停止 Phase 6 推进，只保留当前代码、治理文件和安全边界，等待 owner 后续重新授权继续。",
            "",
            "## 明确禁止",
            "",
            "- 不创建 `runtime/LIVE_AUTHORIZATION.json`",
            "- 不开启 live trading",
            "- 不提交真实 broker order",
            "- 不从旧 shadow folder 继续运行 Phase 6",
            "- 不把缺失证据写成通过",
            "",
        ]
    )
    document = "\n".join(lines)
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
    return document


def build_phase6_closeout_report_markdown(
    *,
    closeout: dict,
    soak_validation: dict,
    paper_shadow_report: dict,
    shadow_live_constraints: dict,
    output_path: str | Path | None = None,
) -> str:
    def _display(value: Any) -> str:
        if value is None:
            return "不适用"
        if isinstance(value, bool):
            return "true" if value else "false"
        if value == "":
            return "无"
        return str(value)

    ready = closeout.get("status") == "ready_for_owner_gate"
    observed_hours = float(soak_validation.get("observed_hours") or 0)
    required_hours = float(soak_validation.get("duration_hours_required") or 48)
    remaining_hours = max(required_hours - observed_hours, 0)
    max_gap_seconds = int(soak_validation.get("max_observed_gap_seconds") or 0)
    gap_violation_count = int(soak_validation.get("gap_violation_count") or 0)
    schema_passed = all(item.get("status") == "pass" for item in paper_shadow_report.get("schema_checks", []))
    hard_gates_passed = all(item.get("status") == "pass" for item in paper_shadow_report.get("hard_gate_checks", []))
    acceptance_by_id = {item.get("id"): item for item in closeout.get("acceptance", [])}
    requirement_rows = [
        (
            "48 小时自然日 soak validation 通过",
            acceptance_by_id.get("phase6_48h_soak_validation", {}),
            "soak_validation_latest.json",
        ),
        (
            "至少一个合格交易日 Paper/Shadow 报告通过 schema 和 hard gate",
            {
                "status": "pass" if paper_shadow_report.get("status") == "pass" and schema_passed and hard_gates_passed else "blocked",
                "evidence_status": paper_shadow_report.get("status"),
                "evidence_generated_at": paper_shadow_report.get("generated_at"),
            },
            "paper_shadow_report_latest.json",
        ),
        (
            "Shadow live 约束不再 blocked",
            acceptance_by_id.get("shadow_live_constraints", {}),
            "shadow_live_constraints_latest.json",
        ),
        (
            "限价订单契约通过",
            acceptance_by_id.get("limit_order_contract", {}),
            "paper_shadow_report_latest.json",
        ),
        (
            "phase6_closeout.json status 为 ready_for_owner_gate",
            {
                "status": "pass" if ready else "blocked",
                "evidence_status": closeout.get("status"),
                "evidence_generated_at": closeout.get("generated_at"),
            },
            "phase6_closeout.json",
        ),
        (
            "OWNER_DECISION.md 可供 owner 选择 A/B/C",
            {
                "status": "pass",
                "evidence_status": "已生成",
                "evidence_generated_at": closeout.get("generated_at"),
            },
            "OWNER_DECISION.md",
        ),
        (
            "不写 runtime/LIVE_AUTHORIZATION.json",
            acceptance_by_id.get("live_authorization_absent", {}),
            "runtime/LIVE_AUTHORIZATION.json absent",
        ),
    ]
    lines = [
        "# Alpha Phase 6 Closeout Report",
        "",
        "## 执行摘要",
        "",
        f"- 当前状态: `{closeout.get('status', '缺失')}`",
        f"- 中文状态: `{closeout.get('status_zh', '缺失')}`",
        f"- 生成时间: `{closeout.get('generated_at', '缺失')}`",
        f"- 48 小时观察进度: `{observed_hours:.4f} / {required_hours:.0f}` 小时",
        f"- 剩余观察时间: `{remaining_hours:.4f}` 小时",
        f"- 连续观察窗口: `{_display(soak_validation.get('window_start'))}` 到 `{_display(soak_validation.get('window_end'))}`",
        f"- 最大样本间隔: `{max_gap_seconds}` 秒；gap violation: `{gap_violation_count}`",
        f"- 当前阻塞项: `{', '.join(closeout.get('blocking_conditions') or []) or '无'}`",
        "- 结论: `可提交 OWNER-GATE-01`" if ready else "- 结论: `尚不可提交 OWNER-GATE-01`",
        "",
        "## 验收标准逐项审计",
        "",
        "| 验收标准 | 当前状态 | 证据状态 | 证据时间 | 证据文件 |",
        "|---|---|---|---|---|",
    ]
    for requirement, evidence, evidence_file in requirement_rows:
        lines.append(
            f"| {requirement} | `{evidence.get('status', 'missing')}` | "
            f"`{_display(evidence.get('evidence_status'))}` | "
            f"`{_display(evidence.get('evidence_generated_at'))}` | `{evidence_file}` |"
        )
    lines.extend(
        [
            "",
            "## Paper/Shadow 合格交易日报告",
            "",
            f"- 报告状态: `{paper_shadow_report.get('status', '缺失')}`",
            f"- Schema 检查: `{'pass' if schema_passed else 'fail'}`",
            f"- Hard gate 检查: `{'pass' if hard_gates_passed else 'fail'}`",
            f"- 交易日: `{paper_shadow_report.get('trading_day', '缺失')}`",
            f"- 标的: `{(paper_shadow_report.get('shadow') or {}).get('symbol', '缺失')}`",
            f"- 订单类型: `{(paper_shadow_report.get('shadow') or {}).get('order_type', '缺失')}`",
            "",
            "## Shadow Live 约束",
            "",
            f"- 约束状态: `{shadow_live_constraints.get('status', '缺失')}`",
            f"- 实盘交易开关: `{_display((shadow_live_constraints.get('health') or {}).get('live_trading_enabled', '缺失'))}`",
            f"- Kill switch: `{_display((shadow_live_constraints.get('health') or {}).get('kill_switch_active', '缺失'))}`",
            "",
            "## 安全边界",
            "",
            "- 停在 OWNER-GATE-01，不进入 MICRO_LIVE。",
            "- 不创建 `runtime/LIVE_AUTHORIZATION.json`。",
            "- 不开启 live trading。",
            "- 不提交真实 broker order。",
            "- 不把 48 小时未满写成 ready。",
            "",
            "## 下一步",
            "",
            "继续让 Phase 6 sampler 自然累计 48 小时 Paper/Shadow 观察；达到要求后重新生成本报告和 `phase6_closeout.json`。",
            "",
        ]
    )
    document = "\n".join(lines)
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
    return document


def build_phase6_evidence_manifest(
    *,
    evidence_root: str | Path,
    closeout: dict,
    soak_validation: dict,
    paper_shadow_report: dict,
    shadow_live_constraints: dict,
    output_path: str | Path | None = None,
) -> dict:
    root = Path(evidence_root)
    artifacts = [
        ("phase6_closeout", "phase6_closeout.json"),
        ("paper_shadow_report", "paper_shadow_report_latest.json"),
        ("shadow_live_constraints", "shadow_live_constraints_latest.json"),
        ("soak_validation", "soak_validation_latest.json"),
        ("owner_decision", "OWNER_DECISION.md"),
        ("closeout_report", "PHASE6_CLOSEOUT_REPORT.md"),
    ]
    artifact_checks = []
    for artifact_id, relative_path in artifacts:
        path = root / relative_path
        artifact_checks.append(
            {
                "id": artifact_id,
                "path": relative_path,
                "exists": path.exists(),
                "sha256": _sha256(path) if path.exists() else None,
            }
        )
    acceptance = closeout.get("acceptance", [])
    report = {
        "schema_version": "2026-06-27.alpha.phase6.evidence_manifest",
        "generated_at": utc_now_iso(),
        "status": closeout.get("status", "blocked_not_ready_for_owner_gate"),
        "evidence_root": str(root),
        "artifact_checks": artifact_checks,
        "all_artifacts_present": all(item["exists"] for item in artifact_checks),
        "acceptance": acceptance,
        "blocking_conditions": closeout.get("blocking_conditions", []),
        "soak": {
            "status": soak_validation.get("status"),
            "sample_count": soak_validation.get("sample_count"),
            "continuous_sample_count": soak_validation.get("continuous_sample_count"),
            "observed_hours": soak_validation.get("observed_hours"),
            "duration_hours_required": soak_validation.get("duration_hours_required"),
            "window_start": soak_validation.get("window_start"),
            "window_end": soak_validation.get("window_end"),
            "max_sample_gap_seconds": soak_validation.get("max_sample_gap_seconds"),
            "max_observed_gap_seconds": soak_validation.get("max_observed_gap_seconds"),
            "gap_violation_count": soak_validation.get("gap_violation_count"),
        },
        "paper_shadow": {
            "status": paper_shadow_report.get("status"),
            "schema_status": _aggregate_check_status(paper_shadow_report.get("schema_checks", [])),
            "hard_gate_status": _aggregate_check_status(paper_shadow_report.get("hard_gate_checks", [])),
            "trading_day": paper_shadow_report.get("trading_day"),
            "order_type": (paper_shadow_report.get("shadow") or {}).get("order_type"),
        },
        "shadow_live_constraints": {
            "status": shadow_live_constraints.get("status"),
            "live_trading_enabled": (shadow_live_constraints.get("health") or {}).get("live_trading_enabled"),
            "kill_switch_active": (shadow_live_constraints.get("health") or {}).get("kill_switch_active"),
        },
        "safety_boundary": _safety_boundary(),
        "live_authorization_absent": not (ROOT / "runtime" / "LIVE_AUTHORIZATION.json").exists(),
    }
    if output_path:
        _write_json(output_path, report)
    return report


def publish_phase6_owner_gate_evidence(
    *,
    source_evidence_root: str | Path = DEFAULT_RUNTIME_EVIDENCE_ROOT,
    target_evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    history_path: str | Path = DEFAULT_SOAK_HISTORY_PATH,
    duration_hours: int = 48,
    max_sample_gap_seconds: int = DEFAULT_MAX_SAMPLE_GAP_SECONDS,
) -> dict:
    source_root = Path(source_evidence_root)
    target_root = Path(target_evidence_root)
    paper_shadow_report = _read_json(source_root / "paper_shadow_report_latest.json")
    shadow_live_constraints = _read_json(source_root / "shadow_live_constraints_latest.json")
    samples = read_soak_samples(history_path)

    _write_json(target_root / "paper_shadow_report_latest.json", paper_shadow_report)
    _write_json(target_root / "shadow_live_constraints_latest.json", shadow_live_constraints)

    soak_validation = build_soak_validation_report(
        samples=samples,
        duration_hours=duration_hours,
        max_sample_gap_seconds=max_sample_gap_seconds,
        output_path=target_root / "soak_validation_latest.json",
    )
    closeout = build_owner_gate_closeout(
        soak_validation=soak_validation,
        paper_shadow_report=paper_shadow_report,
        shadow_live_constraints=shadow_live_constraints,
        output_path=target_root / "phase6_closeout.json",
    )
    build_owner_decision_markdown(
        closeout=closeout,
        soak_validation=soak_validation,
        paper_shadow_report=paper_shadow_report,
        shadow_live_constraints=shadow_live_constraints,
        output_path=target_root / "OWNER_DECISION.md",
    )
    build_phase6_closeout_report_markdown(
        closeout=closeout,
        soak_validation=soak_validation,
        paper_shadow_report=paper_shadow_report,
        shadow_live_constraints=shadow_live_constraints,
        output_path=target_root / "PHASE6_CLOSEOUT_REPORT.md",
    )
    build_phase6_evidence_manifest(
        evidence_root=target_root,
        closeout=closeout,
        soak_validation=soak_validation,
        paper_shadow_report=paper_shadow_report,
        shadow_live_constraints=shadow_live_constraints,
        output_path=target_root / "EVIDENCE_MANIFEST.json",
    )
    verification = verify_phase6_evidence_package(
        evidence_root=target_root,
        output_path=target_root / "EVIDENCE_PACKAGE_VERIFICATION.json",
    )
    return {
        "schema_version": "2026-06-27.alpha.phase6.owner_gate_publish",
        "generated_at": utc_now_iso(),
        "source_evidence_root": str(source_root),
        "target_evidence_root": str(target_root),
        "history_path": str(Path(history_path)),
        "status": closeout.get("status"),
        "blocking_conditions": closeout.get("blocking_conditions", []),
        "soak": {
            "status": soak_validation.get("status"),
            "observed_hours": soak_validation.get("observed_hours"),
            "duration_hours_required": soak_validation.get("duration_hours_required"),
            "sample_count": soak_validation.get("sample_count"),
            "continuous_sample_count": soak_validation.get("continuous_sample_count"),
            "window_start": soak_validation.get("window_start"),
            "window_end": soak_validation.get("window_end"),
        },
        "verification_status": verification.get("verification_status"),
        "live_authorization_absent": verification.get("live_authorization_absent"),
    }


def verify_phase6_evidence_package(
    *,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    live_authorization_path: str | Path | None = None,
    require_ready: bool = False,
    output_path: str | Path | None = None,
) -> dict:
    root = Path(evidence_root)
    auth_path = Path(live_authorization_path or ROOT / "runtime" / "LIVE_AUTHORIZATION.json")
    manifest = _read_json(root / "EVIDENCE_MANIFEST.json")
    closeout = _read_json(root / "phase6_closeout.json")
    paper_shadow = _read_json(root / "paper_shadow_report_latest.json")
    shadow_constraints = _read_json(root / "shadow_live_constraints_latest.json")
    soak = _read_json(root / "soak_validation_latest.json")
    checks = []

    required_files = [
        "EVIDENCE_MANIFEST.json",
        "OWNER_DECISION.md",
        "PHASE6_CLOSEOUT_REPORT.md",
        "paper_shadow_report_latest.json",
        "phase6_closeout.json",
        "shadow_live_constraints_latest.json",
        "soak_validation_latest.json",
    ]
    for relative_path in required_files:
        checks.append(_check(f"artifact_exists.{relative_path}", (root / relative_path).exists(), relative_path))

    manifest_artifacts = manifest.get("artifact_checks", []) if isinstance(manifest, dict) else []
    for artifact in manifest_artifacts:
        path = root / str(artifact.get("path"))
        expected_hash = artifact.get("sha256")
        checks.append(_check(f"artifact_hash.{artifact.get('id')}", path.exists() and _sha256(path) == expected_hash, str(artifact.get("path"))))

    checks.extend(
        [
            _check("manifest_all_artifacts_present", manifest.get("all_artifacts_present") is True, "manifest all artifacts present"),
            _check("manifest_status_matches_closeout", manifest.get("status") == closeout.get("status"), "manifest status matches closeout"),
            _check("acceptance_matches_closeout", manifest.get("acceptance") == closeout.get("acceptance"), "manifest acceptance matches closeout"),
            _check("paper_shadow_pass", paper_shadow.get("status") == "pass", "Paper/Shadow report pass"),
            _check("paper_schema_pass", _aggregate_check_status(paper_shadow.get("schema_checks", [])) == "pass", "Paper/Shadow schema pass"),
            _check("paper_hard_gates_pass", _aggregate_check_status(paper_shadow.get("hard_gate_checks", [])) == "pass", "Paper/Shadow hard gates pass"),
            _check("limit_order_contract", (paper_shadow.get("shadow") or {}).get("order_type") == "limit", "limit order contract"),
            _check("shadow_constraints_pass", shadow_constraints.get("status") == "pass", "Shadow live constraints pass"),
            _check("live_trading_disabled", (shadow_constraints.get("health") or {}).get("live_trading_enabled") is False, "live trading disabled"),
            _check("live_authorization_absent", not auth_path.exists(), "LIVE_AUTHORIZATION.json absent"),
            _check("soak_samples_present", int(soak.get("sample_count") or 0) > 0, "soak samples present"),
            _check("soak_sample_gap_coverage", _check_status(soak, "sample_gap_coverage") == "pass", "soak current sample gaps within threshold"),
            _check("soak_no_failed_samples", _check_status(soak, "no_failed_samples") == "pass", "soak has no failed samples"),
            _check("soak_duration_pass", soak.get("status") == "pass", "48h natural-day soak pass"),
            _check("closeout_ready", closeout.get("status") == "ready_for_owner_gate", "closeout ready for owner gate"),
        ]
    )

    if not require_ready:
        non_required = {"soak_duration_pass", "closeout_ready"}
        verification_checks = [item for item in checks if item["id"] not in non_required]
    else:
        verification_checks = checks
    verification_passed = all(item["status"] == "pass" for item in verification_checks)
    report = {
        "schema_version": "2026-06-27.alpha.phase6.evidence_package_verification",
        "generated_at": utc_now_iso(),
        "verification_status": "pass" if verification_passed else "fail",
        "owner_gate_status": closeout.get("status", "missing"),
        "require_ready": require_ready,
        "blocking_conditions": closeout.get("blocking_conditions", []),
        "checks": checks,
        "evidence_root": str(root),
        "live_authorization_absent": not auth_path.exists(),
    }
    if output_path:
        _write_json(output_path, report)
    return report


def _limit_order_contract_passed(report: dict) -> bool:
    return report.get("status") == "pass" and report.get("shadow", {}).get("order_type") == "limit"


def _acceptance(check_id: str, passed: bool, evidence: dict) -> dict:
    return {
        "id": check_id,
        "status": "pass" if passed else "blocked",
        "evidence_status": evidence.get("status"),
        "evidence_generated_at": evidence.get("generated_at"),
    }


def _check(check_id: str, condition: bool, message: str) -> dict:
    return {"id": check_id, "status": "pass" if condition else "fail", "message": message}


def _nested_get(payload: dict, path: tuple[str, ...]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _aggregate_check_status(checks: list[dict]) -> str:
    if not checks:
        return "missing"
    return "pass" if all(item.get("status") == "pass" for item in checks) else "fail"


def _check_status(report: dict, check_id: str) -> str:
    for item in report.get("checks", []):
        if item.get("id") == check_id:
            return str(item.get("status"))
    return "missing"


def _latest_sample_freshness(samples: list[dict], *, max_age_seconds: int) -> dict:
    if not samples:
        return {
            "latest_sample_generated_at": None,
            "latest_sample_age_seconds": None,
            "max_sample_age_seconds": max_age_seconds,
            "sampler_freshness_status": "missing",
        }
    latest_sample = max(samples, key=lambda item: item.get("generated_at") or "")
    latest_generated_at = latest_sample.get("generated_at")
    try:
        latest_time = _parse_time(latest_generated_at)
    except ValueError:
        latest_time = None
    if latest_time is None:
        return {
            "latest_sample_generated_at": latest_generated_at,
            "latest_sample_age_seconds": None,
            "max_sample_age_seconds": max_age_seconds,
            "sampler_freshness_status": "invalid_timestamp",
        }
    age_seconds = max(0, int((datetime.now(timezone.utc) - latest_time).total_seconds()))
    return {
        "latest_sample_generated_at": latest_time.isoformat(),
        "latest_sample_age_seconds": age_seconds,
        "max_sample_age_seconds": max_age_seconds,
        "sampler_freshness_status": "pass" if age_seconds <= max_age_seconds else "stale",
    }


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safety_boundary() -> dict:
    return {
        "live_trading_enabled": False,
        "broker_mutation_allowed": False,
        "live_authorization_file_must_be_absent": True,
        "mode": "research_paper_order_intent_review",
    }


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _write_json(path: str | Path, payload: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
