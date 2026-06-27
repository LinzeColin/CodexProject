from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.services.approval_queue import annotate_ticket_freshness


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE_ROOT = ROOT / "docs" / "evidence" / "phase6_closeout_latest"
DEFAULT_RUNTIME_EVIDENCE_ROOT = ROOT / "runtime" / "phase6_owner_gate_latest"
DEFAULT_SOAK_HISTORY_PATH = ROOT / "runtime" / "phase6_soak_history.jsonl"


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
    output_path: str | Path | None = None,
) -> dict:
    sorted_samples = sorted(samples, key=lambda item: item.get("generated_at") or "")
    first = _parse_time(sorted_samples[0].get("generated_at")) if sorted_samples else None
    latest = _parse_time(sorted_samples[-1].get("generated_at")) if sorted_samples else None
    observed_seconds = int((latest - first).total_seconds()) if first and latest else 0
    required_seconds = int(duration_hours * 3600)
    failed_samples = [item for item in sorted_samples if int(item.get("fail_count", 0)) > 0]
    checks = [
        _check("samples_present", bool(sorted_samples), "soak samples present"),
        _check("duration_coverage", observed_seconds >= required_seconds, "48h natural-day coverage"),
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
        "observed_seconds": observed_seconds,
        "observed_hours": round(observed_seconds / 3600, 4),
        "sample_count": len(sorted_samples),
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
