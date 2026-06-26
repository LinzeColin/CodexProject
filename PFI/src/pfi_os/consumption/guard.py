from __future__ import annotations

import csv
import hashlib
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json, atomic_write_text, locked_json_update, read_json_state
from pfi_os.system.pfi_identity import MASTER_SYSTEM_ID

CONSUMPTION_EVENT_PATH = PROJECT_ROOT / "data" / "consumption" / "ConsumptionGuardEvents.json"

CONSUMPTION_EVENT_TYPES = (
    "Essential",
    "Discretionary",
    "Impulse",
    "Subscription",
    "InvestmentRelated",
    "Social",
    "Debt",
    "Health",
    "Other",
)
CONSUMPTION_CATEGORIES = (
    "Food",
    "Transport",
    "Housing",
    "Utilities",
    "Subscription",
    "Shopping",
    "Entertainment",
    "Education",
    "Health",
    "InvestmentRelated",
    "Debt",
    "Other",
)
CONSUMPTION_COLUMNS = [
    "event_id",
    "event_date",
    "event_type",
    "category",
    "amount",
    "currency",
    "merchant",
    "payment_method",
    "planned",
    "recurring",
    "necessity_score",
    "impulse_score",
    "regret_score",
    "risk_score",
    "risk_level",
    "evidence_link",
    "evidence_path",
    "evidence_status",
    "review_status",
    "notes",
    "created_at",
    "updated_at",
    "next_action",
]


def create_consumption_event(
    *,
    event_date: str,
    event_type: str,
    category: str,
    amount: float,
    currency: str = "AUD",
    merchant: str = "",
    payment_method: str = "",
    planned: bool = False,
    recurring: bool = False,
    necessity_score: float = 0.0,
    impulse_score: float = 0.0,
    regret_score: float = 0.0,
    evidence_link: str = "",
    evidence_path: str = "",
    review_status: str = "PendingReview",
    notes: str = "",
) -> dict[str, Any]:
    clean_date = _clean_date(event_date)
    clean_event_type = _clean_choice(event_type, CONSUMPTION_EVENT_TYPES, "Other")
    clean_category = _clean_choice(category, CONSUMPTION_CATEGORIES, "Other")
    clean_amount = _money(amount)
    if clean_amount <= 0:
        raise ValueError("amount must be greater than 0 for a consumption event.")
    created_at = datetime.now().isoformat(timespec="seconds")
    raw = {
        "event_id": _stable_id("consumption", clean_date, clean_event_type, clean_category, str(clean_amount), created_at),
        "event_date": clean_date,
        "event_type": clean_event_type,
        "category": clean_category,
        "amount": clean_amount,
        "currency": (currency or "AUD").strip().upper()[:8],
        "merchant": merchant.strip(),
        "payment_method": payment_method.strip(),
        "planned": bool(planned),
        "recurring": bool(recurring),
        "necessity_score": necessity_score,
        "impulse_score": impulse_score,
        "regret_score": regret_score,
        "evidence_link": evidence_link.strip(),
        "evidence_path": evidence_path.strip(),
        "review_status": _clean_review_status(review_status),
        "notes": notes.strip(),
        "created_at": created_at,
        "updated_at": created_at,
    }
    return _normalize_event(raw)


def append_consumption_event(event: dict[str, Any], path: Path | str = CONSUMPTION_EVENT_PATH) -> Path:
    clean_event = _normalize_event(event)

    def append_event(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [_normalize_event(item) for item in payload if isinstance(item, dict)]
        rows.append(clean_event)
        return rows

    return locked_json_update(path, [], append_event, expected_type=list)


def load_consumption_events(path: Path | str = CONSUMPTION_EVENT_PATH) -> list[dict[str, Any]]:
    payload = read_json_state(path, [], expected_type=list, fail_closed=True)
    return [_normalize_event(item) for item in payload if isinstance(item, dict)]


def build_consumption_guard(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    event_path: Path | str | None = None,
    events: list[dict[str, Any]] | None = None,
    lookback_days: int = 30,
    monthly_investable_budget: float = 0.0,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    audit_date = _clean_date(as_of or date.today().isoformat())
    if events is None:
        path = Path(event_path).expanduser() if event_path else root / "data" / "consumption" / "ConsumptionGuardEvents.json"
        loaded_events = load_consumption_events(path)
        event_source = str(path)
    else:
        loaded_events = [_normalize_event(item) for item in events if isinstance(item, dict)]
        event_source = "operational_store:private_reviewed_inputs/consumption_guard"
    summary = _summary(
        loaded_events,
        as_of=audit_date,
        lookback_days=max(1, int(lookback_days)),
        monthly_investable_budget=_money(monthly_investable_budget),
    )
    payload = {
        "schema": "PFIOSConsumptionGuardV1",
        "system": MASTER_SYSTEM_ID,
        "subsystem": "Consumption Guard",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "event_path": event_source,
        "lookback_days": max(1, int(lookback_days)),
        "monthly_investable_budget": _money(monthly_investable_budget),
        "guard_status": summary["guard_status"],
        "summary": summary,
        "action_queue": _action_queue(summary),
        "category_totals": _category_totals(loaded_events, as_of=audit_date, lookback_days=max(1, int(lookback_days))),
        "events": sorted(loaded_events, key=lambda row: (row.get("event_date", ""), row.get("created_at", "")), reverse=True),
        "assumptions": [
            "Only Reviewed events with evidence_link or evidence_path are counted in spend, impulse, fixed-cost, and pressure summaries.",
            "PendingReview, Rejected, or missing-evidence events stay in the ledger but do not affect guard metrics.",
            "monthly_investable_budget is a user-supplied planning value; it is not read from bank, payroll, Alipay, tax, or brokerage systems.",
            "Risk scores are behavior-review aids, not medical, legal, financial, investment, or payment advice.",
            "No payment, transfer, bank action, investment order, or external account action is executed.",
        ],
    }
    payload["runtime_summary"] = build_consumption_runtime_summary(payload)
    return payload


def build_consumption_runtime_summary(payload: dict[str, Any]) -> dict[str, Any]:
    events = [event for event in payload.get("events", []) if isinstance(event, dict)]
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    counted = [event for event in events if _is_counted(event)]
    pending = [event for event in events if event.get("review_status") == "PendingReview"]
    reviewed_missing_evidence = [
        event for event in events if event.get("review_status") == "Reviewed" and event.get("evidence_status") != "Pass"
    ]
    rejected = [event for event in events if event.get("review_status") == "Rejected"]
    high_risk = [event for event in counted if event.get("risk_level") == "HighImpulse" or event.get("event_type") == "Impulse"]
    budget = float(summary.get("monthly_investable_budget", payload.get("monthly_investable_budget", 0.0)) or 0.0)
    pressure = summary.get("investable_cashflow_pressure")
    blocked_behavior = int(summary.get("high_risk_event_count", 0) or 0) >= 3
    blocked_pressure = isinstance(pressure, (int, float)) and float(pressure) > 1.0
    gates = [
        _consumption_gate(
            "GuardSchema",
            "Pass" if payload.get("schema") == "PFIOSConsumptionGuardV1" else "Blocked",
            f"schema={payload.get('schema', '')}",
        ),
        _consumption_gate(
            "ConsumptionEvidence",
            "Pass" if events else "Blocked",
            f"event_count={len(events)}",
        ),
        _consumption_gate(
            "EvidenceCompleteness",
            "Review" if reviewed_missing_evidence else "Pass",
            f"reviewed_missing_evidence={len(reviewed_missing_evidence)}",
        ),
        _consumption_gate(
            "ManualReview",
            "Review" if pending else "Pass",
            f"pending_review={len(pending)}; rejected={len(rejected)}",
        ),
        _consumption_gate(
            "ImpulseRisk",
            "Blocked" if blocked_behavior else ("Review" if high_risk else "Pass"),
            f"high_risk_event_count={summary.get('high_risk_event_count', 0)}; impulse_spend={summary.get('impulse_spend', 0.0)}",
        ),
        _consumption_gate(
            "InvestableBudget",
            "Review" if budget <= 0 else "Pass",
            f"monthly_investable_budget={budget}",
        ),
        _consumption_gate(
            "InvestableCashflowPressure",
            "Blocked" if blocked_pressure else ("Review" if isinstance(pressure, (int, float)) and float(pressure) > 0.6 else "Pass"),
            f"pressure={pressure}",
        ),
        _consumption_gate(
            "NoExternalExecution",
            "Pass",
            "does not connect Alipay, banks, payroll, tax, payment, broker, or trading systems",
        ),
    ]
    return {
        "schema": "PFIOSConsumptionGuardRuntimeSummaryV1",
        "guard_schema": str(payload.get("schema", "")),
        "as_of": str(payload.get("as_of", "")),
        "generated_at": str(payload.get("generated_at", "")),
        "status": _consumption_runtime_status(gates),
        "guard_status": str(payload.get("guard_status", "")),
        "event_count": len(events),
        "counted_records": len(counted),
        "pending_review_records": len(pending),
        "reviewed_missing_evidence_records": len(reviewed_missing_evidence),
        "rejected_records": len(rejected),
        "lookback_days": int(payload.get("lookback_days", 0) or 0),
        "lookback_start": str(summary.get("lookback_start", "")),
        "lookback_end": str(summary.get("lookback_end", "")),
        "counted_spend": float(summary.get("counted_spend", 0.0) or 0.0),
        "essential_spend": float(summary.get("essential_spend", 0.0) or 0.0),
        "discretionary_spend": float(summary.get("discretionary_spend", 0.0) or 0.0),
        "impulse_spend": float(summary.get("impulse_spend", 0.0) or 0.0),
        "fixed_cost": float(summary.get("fixed_cost", 0.0) or 0.0),
        "high_risk_event_count": int(summary.get("high_risk_event_count", 0) or 0),
        "average_risk_score": float(summary.get("average_risk_score", 0.0) or 0.0),
        "monthly_investable_budget": budget,
        "investable_cashflow_pressure": pressure,
        "category_count": len(payload.get("category_totals", []) if isinstance(payload.get("category_totals"), list) else []),
        "evidence_gate": gates,
        "top_actions": list(payload.get("action_queue", []))[:5],
        "top_risk_events": [_compact_consumption_event(event) for event in sorted(counted, key=lambda row: float(row.get("risk_score", 0.0) or 0.0), reverse=True)[:5]],
        "token_policy": (
            "Compact Consumption Guard runtime summary for UI and agent handoff; it does not include full events and "
            "does not connect external financial or payment systems."
        ),
        "safety_boundary": (
            "Local consumption evidence review only. No Alipay login, no bank login, no payroll or tax access, "
            "no payment, no transfer, no refund, no account freeze, no broker action, and no real-money execution."
        ),
    }


def write_consumption_guard(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    event_path: Path | str | None = None,
    events: list[dict[str, Any]] | None = None,
    output_dir: Path | str | None = None,
    lookback_days: int = 30,
    monthly_investable_budget: float = 0.0,
) -> dict[str, Any]:
    payload = build_consumption_guard(
        as_of=as_of,
        project_root=project_root,
        event_path=event_path,
        events=events,
        lookback_days=lookback_days,
        monthly_investable_budget=monthly_investable_budget,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "consumption"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"ConsumptionGuard_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "ConsumptionGuard_latest.json"
    latest_csv = target / "ConsumptionGuard_latest.csv"
    latest_markdown = target / "ConsumptionGuard_latest.md"
    latest_pdf = target / "ConsumptionGuard_latest.pdf"
    runtime_summary_json = target / f"ConsumptionGuardRuntimeSummary_{stamp}.json"
    latest_runtime_summary_json = target / "ConsumptionGuardRuntimeSummary_latest.json"
    payload["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
        "latest_json": str(latest_json),
        "latest_csv": str(latest_csv),
        "latest_markdown": str(latest_markdown),
        "latest_pdf": str(latest_pdf),
        "runtime_summary_json": str(runtime_summary_json),
        "latest_runtime_summary_json": str(latest_runtime_summary_json),
    }
    payload["runtime_summary"] = build_consumption_runtime_summary(payload)
    payload["runtime_summary"]["outputs"] = {
        "runtime_summary_json": str(runtime_summary_json),
        "latest_runtime_summary_json": str(latest_runtime_summary_json),
        "guard_json": str(json_path),
        "latest_guard_json": str(latest_json),
    }
    markdown = consumption_guard_markdown(payload)
    csv_text = _csv_text(payload.get("events", []))
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_consumption_pdf(pdf_path, payload)
    _write_consumption_pdf(latest_pdf, payload)
    atomic_write_json(runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(latest_runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    return payload


def consumption_guard_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"# PFI_OS Consumption Guard {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- System: `{payload.get('system', '')}`",
        f"- Status: `{payload.get('guard_status', '')}`",
        f"- Runtime Status: `{runtime.get('status', '')}`",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        f"- Counted Spend: `{summary.get('counted_spend', 0.0)}`",
        f"- Impulse Spend: `{summary.get('impulse_spend', 0.0)}`",
        f"- Fixed Cost: `{summary.get('fixed_cost', 0.0)}`",
        f"- Investable Cashflow Pressure: `{summary.get('investable_cashflow_pressure', None)}`",
        f"- Token Policy: {runtime.get('token_policy', '')}",
        "",
        "## Runtime Evidence Gate",
        _markdown_table(runtime.get("evidence_gate", []), ["gate", "status", "evidence"]),
        "",
        "## Action Queue",
        _markdown_table(payload.get("action_queue", []), ["priority", "status", "action", "source"]),
        "",
        "## Category Totals",
        _markdown_table(payload.get("category_totals", []), ["category", "amount", "high_risk_amount", "count"]),
        "",
        "## Events",
        _markdown_table(payload.get("events", [])[:80], ["event_date", "event_type", "category", "amount", "risk_level", "review_status", "evidence_status", "merchant"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _summary(events: list[dict[str, Any]], *, as_of: str, lookback_days: int, monthly_investable_budget: float) -> dict[str, Any]:
    end = _parse_date(as_of) or date.today()
    start = end - timedelta(days=lookback_days - 1)
    counted = [event for event in events if _is_counted(event)]
    pending = [event for event in events if event.get("review_status") == "PendingReview"]
    reviewed_missing_evidence = [
        event for event in events if event.get("review_status") == "Reviewed" and event.get("evidence_status") != "Pass"
    ]
    window = [event for event in counted if start <= (_parse_date(str(event.get("event_date", ""))) or date.min) <= end]
    counted_spend = _sum_amount(window)
    impulse_events = [event for event in window if event.get("risk_level") == "HighImpulse" or event.get("event_type") == "Impulse"]
    impulse_spend = _sum_amount(impulse_events)
    fixed_cost = _sum_amount([event for event in window if event.get("recurring") or event.get("event_type") == "Subscription"])
    discretionary_spend = _sum_amount([event for event in window if event.get("event_type") in {"Discretionary", "Impulse", "Social", "Entertainment"} or event.get("category") in {"Shopping", "Entertainment"}])
    pressure = round(discretionary_spend / monthly_investable_budget, 4) if monthly_investable_budget > 0 else None
    high_risk_count = len(impulse_events)
    average_risk_score = round(sum(float(event.get("risk_score", 0.0) or 0.0) for event in window) / len(window), 2) if window else 0.0
    return {
        "total_records": len(events),
        "counted_records": len(counted),
        "pending_review_records": len(pending),
        "reviewed_missing_evidence_records": len(reviewed_missing_evidence),
        "lookback_start": start.isoformat(),
        "lookback_end": end.isoformat(),
        "counted_spend": counted_spend,
        "essential_spend": _sum_amount([event for event in window if event.get("event_type") == "Essential"]),
        "discretionary_spend": discretionary_spend,
        "impulse_spend": impulse_spend,
        "fixed_cost": fixed_cost,
        "high_risk_event_count": high_risk_count,
        "average_risk_score": average_risk_score,
        "monthly_investable_budget": monthly_investable_budget,
        "investable_cashflow_pressure": pressure,
        "guard_status": _guard_status(events, pending, reviewed_missing_evidence, high_risk_count, pressure),
    }


def _guard_status(
    events: list[dict[str, Any]],
    pending: list[dict[str, Any]],
    reviewed_missing_evidence: list[dict[str, Any]],
    high_risk_count: int,
    pressure: float | None,
) -> str:
    if not events:
        return "MissingConsumptionEvidence"
    if reviewed_missing_evidence:
        return "NeedsEvidence"
    if high_risk_count >= 3 or (pressure is not None and pressure > 1.0):
        return "StopBleeding"
    if high_risk_count > 0 or (pressure is not None and pressure > 0.6):
        return "Watch"
    if pending:
        return "StableWithPendingReview"
    return "Stable"


def _action_queue(summary: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if int(summary.get("total_records", 0) or 0) <= 0:
        rows.append(_action("P0", "录入至少一条消费事件，并附上账单、截图、导出 CSV 或可复核说明。", "Consumption Evidence"))
    if int(summary.get("reviewed_missing_evidence_records", 0) or 0) > 0:
        rows.append(_action("P0", "已复核消费事件缺少证据；补充 evidence_link 或 evidence_path，否则不要计入守卫指标。", "Evidence Gate"))
    if int(summary.get("pending_review_records", 0) or 0) > 0:
        rows.append(_action("P1", "复核 PendingReview 消费事件，确认金额、类别、冲动分和证据后再升级为 Reviewed。", "Manual Review"))
    if int(summary.get("high_risk_event_count", 0) or 0) > 0:
        rows.append(_action("P1", "存在高冲动消费事件；复盘触发场景并设置下一次消费前冷静检查。", "Impulse Risk"))
    pressure = summary.get("investable_cashflow_pressure")
    if isinstance(pressure, (int, float)) and pressure > 0.6:
        rows.append(_action("P1" if pressure <= 1.0 else "P0", f"可投资现金流压力为 {pressure:.2%}；优先削减非必要和重复订阅支出。", "Investable Cashflow"))
    if float(summary.get("fixed_cost", 0.0) or 0.0) > 0:
        rows.append(_action("P2", "复核周期性支出，确认是否仍有必要，避免固定成本吞噬投资现金流。", "Fixed Cost"))
    if not rows:
        rows.append(_action("P2", "继续每周登记消费证据，保持支出、冲动风险和可投资现金流压力可见。", "Consumption Guard"))
    return rows


def _action(priority: str, action: str, source: str) -> dict[str, str]:
    return {"priority": priority, "status": "Open", "action": action, "source": source}


def _consumption_gate(gate: str, status: str, evidence: str) -> dict[str, str]:
    clean_status = status if status in {"Pass", "Review", "Blocked"} else "Review"
    return {"gate": gate, "status": clean_status, "evidence": evidence}


def _consumption_runtime_status(gates: list[dict[str, str]]) -> str:
    statuses = {str(gate.get("status", "")) for gate in gates}
    if "Blocked" in statuses:
        return "Blocked"
    if "Review" in statuses:
        return "NeedsReview"
    return "Pass"


def _compact_consumption_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(event.get("event_id", "")),
        "event_date": str(event.get("event_date", "")),
        "event_type": str(event.get("event_type", "")),
        "category": str(event.get("category", "")),
        "amount": float(event.get("amount", 0.0) or 0.0),
        "risk_score": float(event.get("risk_score", 0.0) or 0.0),
        "risk_level": str(event.get("risk_level", "")),
        "review_status": str(event.get("review_status", "")),
        "evidence_status": str(event.get("evidence_status", "")),
        "next_action": str(event.get("next_action", ""))[:180],
    }


def _category_totals(events: list[dict[str, Any]], *, as_of: str, lookback_days: int) -> list[dict[str, Any]]:
    end = _parse_date(as_of) or date.today()
    start = end - timedelta(days=lookback_days - 1)
    totals: dict[str, dict[str, float | int]] = {}
    for event in events:
        if not _is_counted(event):
            continue
        event_day = _parse_date(str(event.get("event_date", ""))) or date.min
        if not start <= event_day <= end:
            continue
        category = str(event.get("category", "Other") or "Other")
        bucket = totals.setdefault(category, {"amount": 0.0, "high_risk_amount": 0.0, "count": 0})
        amount = float(event.get("amount", 0.0) or 0.0)
        bucket["amount"] = float(bucket["amount"]) + amount
        bucket["count"] = int(bucket["count"]) + 1
        if event.get("risk_level") == "HighImpulse":
            bucket["high_risk_amount"] = float(bucket["high_risk_amount"]) + amount
    return [
        {
            "category": category,
            "amount": round(float(values["amount"]), 2),
            "high_risk_amount": round(float(values["high_risk_amount"]), 2),
            "count": int(values["count"]),
        }
        for category, values in sorted(totals.items(), key=lambda item: (-float(item[1]["amount"]), item[0]))
    ]


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    event_date = _clean_date(str(event.get("event_date") or date.today().isoformat()))
    event_type = _clean_choice(str(event.get("event_type") or "Other"), CONSUMPTION_EVENT_TYPES, "Other")
    category = _clean_choice(str(event.get("category") or "Other"), CONSUMPTION_CATEGORIES, "Other")
    amount = _money(event.get("amount", 0.0))
    planned = bool(event.get("planned", False))
    recurring = bool(event.get("recurring", False))
    necessity_score = _score(event.get("necessity_score", 0.0))
    impulse_score = _score(event.get("impulse_score", 0.0))
    regret_score = _score(event.get("regret_score", 0.0))
    risk_score = _risk_score(necessity_score, impulse_score, regret_score, planned)
    risk_level = _risk_level(risk_score, event_type)
    evidence_link = str(event.get("evidence_link") or "").strip()
    evidence_path = str(event.get("evidence_path") or "").strip()
    evidence_status = "Pass" if evidence_link or evidence_path else "Missing"
    review_status = _clean_review_status(event.get("review_status", "PendingReview"))
    created_at = str(event.get("created_at") or datetime.now().isoformat(timespec="seconds"))
    return {
        "event_id": str(event.get("event_id") or _stable_id("consumption", event_date, event_type, category, str(amount), created_at)),
        "event_date": event_date,
        "event_type": event_type,
        "category": category,
        "amount": amount,
        "currency": str(event.get("currency") or "AUD").strip().upper()[:8],
        "merchant": str(event.get("merchant") or "").strip(),
        "payment_method": str(event.get("payment_method") or "").strip(),
        "planned": planned,
        "recurring": recurring,
        "necessity_score": necessity_score,
        "impulse_score": impulse_score,
        "regret_score": regret_score,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "evidence_link": evidence_link,
        "evidence_path": evidence_path,
        "evidence_status": evidence_status,
        "review_status": review_status,
        "notes": str(event.get("notes") or "").strip(),
        "created_at": created_at,
        "updated_at": str(event.get("updated_at") or created_at),
        "next_action": _next_action(review_status, evidence_status, risk_level),
    }


def _risk_score(necessity_score: float, impulse_score: float, regret_score: float, planned: bool) -> float:
    planning_penalty = 0.0 if planned else 10.0
    score = impulse_score * 0.45 + regret_score * 0.25 + (100.0 - necessity_score) * 0.20 + planning_penalty
    return round(max(0.0, min(100.0, score)), 2)


def _risk_level(risk_score: float, event_type: str) -> str:
    if event_type == "Impulse" or risk_score >= 70:
        return "HighImpulse"
    if risk_score >= 40:
        return "Watch"
    return "Controlled"


def _next_action(review_status: str, evidence_status: str, risk_level: str) -> str:
    if review_status == "Rejected":
        return "Keep archived; do not count this event."
    if evidence_status != "Pass":
        return "Attach bill, receipt, screenshot, CSV export, or reviewable note before counting."
    if review_status != "Reviewed":
        return "Review amount, category, impulse score, and evidence before counting."
    if risk_level == "HighImpulse":
        return "Review trigger, cooling-off rule, and whether this category should be capped."
    if risk_level == "Watch":
        return "Monitor repeated pattern and compare against investable cashflow budget."
    return "Counted as controlled consumption evidence."


def _is_counted(event: dict[str, Any]) -> bool:
    return event.get("review_status") == "Reviewed" and event.get("evidence_status") == "Pass"


def _sum_amount(events: list[dict[str, Any]]) -> float:
    return round(sum(float(event.get("amount", 0.0) or 0.0) for event in events), 2)


def _clean_date(value: str) -> str:
    parsed = _parse_date(value)
    if parsed is None:
        raise ValueError(f"Invalid date: {value}")
    return parsed.isoformat()


def _parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def _clean_choice(value: str, choices: tuple[str, ...], default: str) -> str:
    raw = str(value or "").strip()
    return raw if raw in choices else default


def _clean_review_status(value: Any) -> str:
    raw = str(value or "").strip()
    if raw in {"PendingReview", "Reviewed", "Rejected"}:
        return raw
    aliases = {
        "pending": "PendingReview",
        "pendingreview": "PendingReview",
        "待复核": "PendingReview",
        "reviewed": "Reviewed",
        "approved": "Reviewed",
        "已复核": "Reviewed",
        "rejected": "Rejected",
        "拒绝": "Rejected",
    }
    return aliases.get(raw.lower(), "PendingReview")


def _score(value: Any) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        number = 0.0
    return round(max(0.0, min(100.0, number)), 2)


def _money(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        amount = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, amount), 2)


def _csv_text(records: list[dict[str, Any]]) -> str:
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=CONSUMPTION_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow(record)
    return handle.getvalue()


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |\n"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _write_consumption_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"PFI_OS Consumption Guard {payload.get('as_of', '')}",
        f"Generated At: {payload.get('generated_at', '')}",
        f"Status: {payload.get('guard_status', '')}",
        f"Runtime Status: {runtime.get('status', '')}",
        f"Counted Spend: {summary.get('counted_spend', 0.0)}",
        f"Impulse Spend: {summary.get('impulse_spend', 0.0)}",
        f"Fixed Cost: {summary.get('fixed_cost', 0.0)}",
        f"Investable Cashflow Pressure: {summary.get('investable_cashflow_pressure', None)}",
        f"Token Policy: {runtime.get('token_policy', '')}",
        "",
        "Runtime Evidence Gate:",
    ]
    for row in runtime.get("evidence_gate", [])[:8]:
        lines.append(f"- {row.get('gate')}: {row.get('status')} | {row.get('evidence')}")
    lines.extend([
        "",
        "Action Queue:",
    ])
    for row in payload.get("action_queue", [])[:12]:
        lines.append(f"- {row.get('priority')}: {row.get('action')}")
    lines.extend(["", "Assumptions:"])
    for item in payload.get("assumptions", [])[:6]:
        lines.append(f"- {item}")
    content = ["BT", "/F1 10 Tf", "56 760 Td", "12 TL"]
    for line in lines[:58]:
        content.append(f"({_pdf_escape(_pdf_ascii(line))}) Tj")
        content.append("T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    _write_pdf_objects(path, objects)


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(content)


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"consumption_{digest}"


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _cell(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text[:160]
