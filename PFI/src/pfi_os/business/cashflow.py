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

CASHFLOW_ENTRY_PATH = PROJECT_ROOT / "data" / "cashflow" / "CompanyCashFlowEntries.json"

CASHFLOW_DIRECTIONS = ("Inflow", "Outflow", "BalanceSnapshot", "Receivable", "Payable")
CASHFLOW_CATEGORIES = (
    "SalesRevenue",
    "ServiceRevenue",
    "OwnerCapital",
    "Tax",
    "Salary",
    "Vendor",
    "Software",
    "Marketing",
    "Rent",
    "Compliance",
    "Debt",
    "Other",
)
CASHFLOW_COLUMNS = [
    "entry_id",
    "entry_date",
    "direction",
    "category",
    "amount",
    "currency",
    "account",
    "counterparty",
    "description",
    "evidence_link",
    "evidence_path",
    "evidence_status",
    "review_status",
    "recurring",
    "notes",
    "created_at",
    "updated_at",
    "decision_level",
    "next_action",
]


def create_cashflow_entry(
    *,
    entry_date: str,
    direction: str,
    category: str,
    amount: float,
    currency: str = "AUD",
    account: str = "",
    counterparty: str = "",
    description: str = "",
    evidence_link: str = "",
    evidence_path: str = "",
    review_status: str = "PendingReview",
    recurring: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    clean_date = _clean_date(entry_date)
    clean_direction = _clean_direction(direction)
    clean_category = _clean_category(category)
    clean_amount = _money(amount)
    if clean_amount <= 0:
        raise ValueError("amount must be greater than 0 for a cashflow entry.")
    status = _clean_review_status(review_status)
    created_at = datetime.now().isoformat(timespec="seconds")
    entry = {
        "entry_id": _stable_id("cashflow", clean_date, clean_direction, clean_category, str(clean_amount), created_at),
        "entry_date": clean_date,
        "direction": clean_direction,
        "category": clean_category,
        "amount": clean_amount,
        "currency": (currency or "AUD").strip().upper()[:8],
        "account": account.strip(),
        "counterparty": counterparty.strip(),
        "description": description.strip(),
        "evidence_link": evidence_link.strip(),
        "evidence_path": evidence_path.strip(),
        "evidence_status": _evidence_status(evidence_link, evidence_path),
        "review_status": status,
        "recurring": bool(recurring),
        "notes": notes.strip(),
        "created_at": created_at,
        "updated_at": created_at,
        "decision_level": "Observe",
        "next_action": _entry_next_action(status, _evidence_status(evidence_link, evidence_path)),
    }
    return entry


def append_cashflow_entry(entry: dict[str, Any], path: Path | str = CASHFLOW_ENTRY_PATH) -> Path:
    clean_entry = _normalize_entry(entry)

    def append_entry(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [_normalize_entry(item) for item in payload if isinstance(item, dict)]
        rows.append(clean_entry)
        return rows

    return locked_json_update(path, [], append_entry, expected_type=list)


def load_cashflow_entries(path: Path | str = CASHFLOW_ENTRY_PATH) -> list[dict[str, Any]]:
    payload = read_json_state(path, [], expected_type=list, fail_closed=True)
    return [_normalize_entry(item) for item in payload if isinstance(item, dict)]


def build_cashflow_command(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    entry_path: Path | str | None = None,
    entries: list[dict[str, Any]] | None = None,
    lookback_days: int = 30,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    audit_date = _clean_date(as_of or date.today().isoformat())
    if entries is None:
        path = Path(entry_path).expanduser() if entry_path else root / "data" / "cashflow" / "CompanyCashFlowEntries.json"
        loaded_entries = load_cashflow_entries(path)
        entry_source = str(path)
    else:
        loaded_entries = [_normalize_entry(item) for item in entries if isinstance(item, dict)]
        entry_source = "operational_store:private_reviewed_inputs/company_cashflow"
    summary = _summary(loaded_entries, as_of=audit_date, lookback_days=max(1, int(lookback_days)))
    payload = {
        "schema": "PFIOSCompanyCashFlowCommandV1",
        "system": MASTER_SYSTEM_ID,
        "subsystem": "Company CashFlow Command",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "entry_path": entry_source,
        "lookback_days": max(1, int(lookback_days)),
        "cashflow_status": summary["cashflow_status"],
        "summary": summary,
        "action_queue": _action_queue(summary),
        "category_totals": _category_totals(loaded_entries, as_of=audit_date, lookback_days=max(1, int(lookback_days))),
        "entries": sorted(loaded_entries, key=lambda row: (row.get("entry_date", ""), row.get("created_at", "")), reverse=True),
        "assumptions": [
            "Only entries with review_status=Reviewed and evidence_status=Pass are counted in cashflow totals.",
            "PendingReview entries are stored for review but do not affect balance, runway, inflow, outflow, receivable, or payable totals.",
            "BalanceSnapshot records are user-supplied evidence, not a bank API connection.",
            "This subsystem does not connect to bank accounts, payment providers, payroll, tax systems, or live trading.",
            "No payments, transfers, orders, or external account actions are executed.",
        ],
    }
    payload["runtime_summary"] = build_cashflow_runtime_summary(payload)
    return payload


def build_cashflow_runtime_summary(payload: dict[str, Any]) -> dict[str, Any]:
    entries = [entry for entry in payload.get("entries", []) if isinstance(entry, dict)]
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    counted = [entry for entry in entries if _is_counted(entry)]
    pending = [entry for entry in entries if entry.get("review_status") == "PendingReview"]
    reviewed_missing_evidence = [
        entry for entry in entries if entry.get("review_status") == "Reviewed" and entry.get("evidence_status") != "Pass"
    ]
    rejected = [entry for entry in entries if entry.get("review_status") == "Rejected"]
    stale_balance = _balance_is_stale(summary, str(payload.get("as_of", "")))
    critical_runway = _is_critical_runway(summary)
    negative_net = float(summary.get("net_cashflow", 0.0) or 0.0) < 0
    gates = [
        _cashflow_gate(
            "CommandSchema",
            "Pass" if payload.get("schema") == "PFIOSCompanyCashFlowCommandV1" else "Blocked",
            f"schema={payload.get('schema', '')}",
        ),
        _cashflow_gate(
            "BalanceSnapshot",
            "Pass" if summary.get("latest_balance") is not None else "Blocked",
            f"latest_balance={summary.get('latest_balance')}",
        ),
        _cashflow_gate(
            "EvidenceCompleteness",
            "Review" if reviewed_missing_evidence else "Pass",
            f"reviewed_missing_evidence={len(reviewed_missing_evidence)}",
        ),
        _cashflow_gate(
            "ManualReview",
            "Review" if pending else "Pass",
            f"pending_review={len(pending)}; rejected={len(rejected)}",
        ),
        _cashflow_gate(
            "Runway",
            "Blocked" if critical_runway else ("Review" if summary.get("runway_days") is None or _is_watch_runway(summary) else "Pass"),
            f"runway_days={summary.get('runway_days')}; daily_burn={summary.get('daily_burn')}",
        ),
        _cashflow_gate(
            "NetCashflow",
            "Review" if negative_net else "Pass",
            f"net_cashflow={summary.get('net_cashflow', 0.0)}",
        ),
        _cashflow_gate(
            "BalanceFreshness",
            "Review" if stale_balance else "Pass",
            f"lookback_end={summary.get('lookback_end', '')}; latest_balance_date={summary.get('latest_balance_date')}",
        ),
        _cashflow_gate(
            "NoExternalExecution",
            "Pass",
            "does not connect banks, payment providers, payroll, tax, accounting, broker, or trading systems",
        ),
    ]
    return {
        "schema": "PFIOSCompanyCashFlowRuntimeSummaryV1",
        "command_schema": str(payload.get("schema", "")),
        "as_of": str(payload.get("as_of", "")),
        "generated_at": str(payload.get("generated_at", "")),
        "status": _cashflow_runtime_status(gates),
        "cashflow_status": str(payload.get("cashflow_status", "")),
        "entry_count": len(entries),
        "counted_records": len(counted),
        "pending_review_records": len(pending),
        "reviewed_missing_evidence_records": len(reviewed_missing_evidence),
        "rejected_records": len(rejected),
        "lookback_days": int(payload.get("lookback_days", 0) or 0),
        "latest_balance": summary.get("latest_balance"),
        "latest_balance_date": summary.get("latest_balance_date"),
        "inflow": float(summary.get("inflow", 0.0) or 0.0),
        "outflow": float(summary.get("outflow", 0.0) or 0.0),
        "net_cashflow": float(summary.get("net_cashflow", 0.0) or 0.0),
        "receivable": float(summary.get("receivable", 0.0) or 0.0),
        "payable": float(summary.get("payable", 0.0) or 0.0),
        "daily_burn": float(summary.get("daily_burn", 0.0) or 0.0),
        "runway_days": summary.get("runway_days"),
        "evidence_gate": gates,
        "top_actions": list(payload.get("action_queue", []))[:5],
        "token_policy": (
            "Compact Company CashFlow runtime summary for UI and agent handoff; it does not include full entries and "
            "does not connect external financial systems."
        ),
        "safety_boundary": (
            "Local evidence review only. No bank login, no payment, no transfer, no payroll or tax filing, "
            "no accounting-system mutation, no broker action, and no real-money execution."
        ),
    }


def write_cashflow_command(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    entry_path: Path | str | None = None,
    entries: list[dict[str, Any]] | None = None,
    output_dir: Path | str | None = None,
    lookback_days: int = 30,
) -> dict[str, Any]:
    payload = build_cashflow_command(
        as_of=as_of,
        project_root=project_root,
        entry_path=entry_path,
        entries=entries,
        lookback_days=lookback_days,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "cashflow"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"CompanyCashFlowCommand_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "CompanyCashFlowCommand_latest.json"
    latest_csv = target / "CompanyCashFlowCommand_latest.csv"
    latest_markdown = target / "CompanyCashFlowCommand_latest.md"
    latest_pdf = target / "CompanyCashFlowCommand_latest.pdf"
    runtime_summary_json = target / f"CompanyCashFlowRuntimeSummary_{stamp}.json"
    latest_runtime_summary_json = target / "CompanyCashFlowRuntimeSummary_latest.json"
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
    payload["runtime_summary"] = build_cashflow_runtime_summary(payload)
    payload["runtime_summary"]["outputs"] = {
        "runtime_summary_json": str(runtime_summary_json),
        "latest_runtime_summary_json": str(latest_runtime_summary_json),
        "command_json": str(json_path),
        "latest_command_json": str(latest_json),
    }
    markdown = cashflow_command_markdown(payload)
    csv_text = _csv_text(payload.get("entries", []))
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_cashflow_pdf(pdf_path, payload)
    _write_cashflow_pdf(latest_pdf, payload)
    atomic_write_json(runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(latest_runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    return payload


def cashflow_command_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"# PFI_OS Company CashFlow Command {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- System: `{payload.get('system', '')}`",
        f"- Status: `{payload.get('cashflow_status', '')}`",
        f"- Runtime Status: `{runtime.get('status', '')}`",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        f"- Counted Balance: `{summary.get('latest_balance', None)}`",
        f"- Net Cashflow: `{summary.get('net_cashflow', 0.0)}`",
        f"- Runway Days: `{summary.get('runway_days', None)}`",
        f"- Token Policy: {runtime.get('token_policy', '')}",
        "",
        "## Runtime Evidence Gate",
        _markdown_table(runtime.get("evidence_gate", []), ["gate", "status", "evidence"]),
        "",
        "## Action Queue",
        _markdown_table(payload.get("action_queue", []), ["priority", "status", "action", "source"]),
        "",
        "## Category Totals",
        _markdown_table(payload.get("category_totals", []), ["category", "inflow", "outflow", "net"]),
        "",
        "## Entries",
        _markdown_table(payload.get("entries", [])[:80], ["entry_date", "direction", "category", "amount", "review_status", "evidence_status", "description"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _summary(entries: list[dict[str, Any]], *, as_of: str, lookback_days: int) -> dict[str, Any]:
    end = _parse_date(as_of) or date.today()
    start = end - timedelta(days=lookback_days - 1)
    counted = [entry for entry in entries if _is_counted(entry)]
    pending = [entry for entry in entries if entry.get("review_status") == "PendingReview"]
    reviewed_missing_evidence = [
        entry for entry in entries if entry.get("review_status") == "Reviewed" and entry.get("evidence_status") != "Pass"
    ]
    window = [entry for entry in counted if start <= (_parse_date(str(entry.get("entry_date", ""))) or date.min) <= end]
    inflow = _sum_direction(window, "Inflow")
    outflow = _sum_direction(window, "Outflow")
    receivable = _sum_direction(counted, "Receivable")
    payable = _sum_direction(counted, "Payable")
    latest_balance = _latest_balance(counted, end)
    daily_burn = outflow / lookback_days if outflow > 0 else 0.0
    runway_days = round(latest_balance / daily_burn, 1) if latest_balance is not None and daily_burn > 0 else None
    latest_balance_date = _latest_balance_date(counted, end)
    net_cashflow = round(inflow - outflow, 2)
    return {
        "total_records": len(entries),
        "counted_records": len(counted),
        "pending_review_records": len(pending),
        "reviewed_missing_evidence_records": len(reviewed_missing_evidence),
        "lookback_start": start.isoformat(),
        "lookback_end": end.isoformat(),
        "latest_balance": latest_balance,
        "latest_balance_date": latest_balance_date,
        "inflow": inflow,
        "outflow": outflow,
        "net_cashflow": net_cashflow,
        "receivable": receivable,
        "payable": payable,
        "daily_burn": round(daily_burn, 2),
        "runway_days": runway_days,
        "cashflow_status": _cashflow_status(latest_balance, runway_days, net_cashflow, pending, reviewed_missing_evidence),
    }


def _cashflow_status(
    latest_balance: float | None,
    runway_days: float | None,
    net_cashflow: float,
    pending: list[dict[str, Any]],
    reviewed_missing_evidence: list[dict[str, Any]],
) -> str:
    if latest_balance is None:
        return "MissingBalance"
    if reviewed_missing_evidence:
        return "NeedsEvidence"
    if runway_days is not None and runway_days < 14:
        return "Critical"
    if runway_days is not None and runway_days < 30:
        return "Watch"
    if net_cashflow < 0:
        return "NeedsReview"
    if pending:
        return "StableWithPendingReview"
    return "Stable"


def _cashflow_gate(gate: str, status: str, evidence: str) -> dict[str, str]:
    clean_status = status if status in {"Pass", "Review", "Blocked"} else "Review"
    return {"gate": gate, "status": clean_status, "evidence": evidence}


def _cashflow_runtime_status(gates: list[dict[str, str]]) -> str:
    statuses = {str(gate.get("status", "")) for gate in gates}
    if "Blocked" in statuses:
        return "Blocked"
    if "Review" in statuses:
        return "NeedsReview"
    return "Pass"


def _is_critical_runway(summary: dict[str, Any]) -> bool:
    runway = summary.get("runway_days")
    return isinstance(runway, (int, float)) and runway < 14


def _is_watch_runway(summary: dict[str, Any]) -> bool:
    runway = summary.get("runway_days")
    return isinstance(runway, (int, float)) and runway < 30


def _balance_is_stale(summary: dict[str, Any], as_of: str) -> bool:
    balance_date = _parse_date(str(summary.get("latest_balance_date") or ""))
    audit_date = _parse_date(as_of)
    if balance_date is None or audit_date is None:
        return summary.get("latest_balance") is not None
    return (audit_date - balance_date).days > 7


def _action_queue(summary: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if summary.get("latest_balance") is None:
        rows.append(_action("P0", "录入并复核最新公司现金余额 BalanceSnapshot，附上可复核证据。", "BalanceSnapshot"))
    if int(summary.get("reviewed_missing_evidence_records", 0) or 0) > 0:
        rows.append(_action("P0", "已复核现金流记录缺少证据；补充 evidence_link 或 evidence_path，否则不要计入现金流。", "Evidence Gate"))
    if int(summary.get("pending_review_records", 0) or 0) > 0:
        rows.append(_action("P1", "复核 PendingReview 现金流记录，确认金额、分类和证据后再升级为 Reviewed。", "Manual Review"))
    runway = summary.get("runway_days")
    if isinstance(runway, (int, float)) and runway < 30:
        rows.append(_action("P0" if runway < 14 else "P1", f"现金 runway 约 {runway:.1f} 天；优先检查固定支出、应收款和应付款。", "Runway"))
    if float(summary.get("net_cashflow", 0.0) or 0.0) < 0:
        rows.append(_action("P1", "近 30 天净现金流为负；按类别检查收入缺口或成本压力。", "Net Cashflow"))
    if not rows:
        rows.append(_action("P2", "继续每周录入 BalanceSnapshot、收入、支出、应收和应付款，保持证据闭环。", "Company CashFlow Command"))
    return rows


def _action(priority: str, action: str, source: str) -> dict[str, str]:
    return {"priority": priority, "status": "Open", "action": action, "source": source}


def _category_totals(entries: list[dict[str, Any]], *, as_of: str, lookback_days: int) -> list[dict[str, Any]]:
    end = _parse_date(as_of) or date.today()
    start = end - timedelta(days=lookback_days - 1)
    totals: dict[str, dict[str, float]] = {}
    for entry in entries:
        if not _is_counted(entry):
            continue
        entry_day = _parse_date(str(entry.get("entry_date", ""))) or date.min
        if not start <= entry_day <= end:
            continue
        direction = str(entry.get("direction", ""))
        if direction not in {"Inflow", "Outflow"}:
            continue
        category = str(entry.get("category", "Other") or "Other")
        row = totals.setdefault(category, {"inflow": 0.0, "outflow": 0.0})
        row["inflow" if direction == "Inflow" else "outflow"] += float(entry.get("amount", 0.0) or 0.0)
    return [
        {"category": category, "inflow": round(values["inflow"], 2), "outflow": round(values["outflow"], 2), "net": round(values["inflow"] - values["outflow"], 2)}
        for category, values in sorted(totals.items())
    ]


def _normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    entry_date = _clean_date(str(entry.get("entry_date") or date.today().isoformat()))
    direction = _clean_direction(str(entry.get("direction") or "Outflow"))
    category = _clean_category(str(entry.get("category") or "Other"))
    amount = _money(entry.get("amount", 0.0))
    created_at = str(entry.get("created_at") or datetime.now().isoformat(timespec="seconds"))
    evidence_link = str(entry.get("evidence_link") or "").strip()
    evidence_path = str(entry.get("evidence_path") or "").strip()
    evidence_status = _evidence_status(evidence_link, evidence_path)
    review_status = _clean_review_status(entry.get("review_status", "PendingReview"))
    return {
        "entry_id": str(entry.get("entry_id") or _stable_id("cashflow", entry_date, direction, category, str(amount), created_at)),
        "entry_date": entry_date,
        "direction": direction,
        "category": category,
        "amount": amount,
        "currency": str(entry.get("currency") or "AUD").strip().upper()[:8],
        "account": str(entry.get("account") or "").strip(),
        "counterparty": str(entry.get("counterparty") or "").strip(),
        "description": str(entry.get("description") or "").strip(),
        "evidence_link": evidence_link,
        "evidence_path": evidence_path,
        "evidence_status": evidence_status,
        "review_status": review_status,
        "recurring": bool(entry.get("recurring", False)),
        "notes": str(entry.get("notes") or "").strip(),
        "created_at": created_at,
        "updated_at": str(entry.get("updated_at") or created_at),
        "decision_level": "Observe",
        "next_action": _entry_next_action(review_status, evidence_status),
    }


def _is_counted(entry: dict[str, Any]) -> bool:
    return entry.get("review_status") == "Reviewed" and entry.get("evidence_status") == "Pass"


def _latest_balance(entries: list[dict[str, Any]], as_of: date) -> float | None:
    snapshots = [
        entry
        for entry in entries
        if entry.get("direction") == "BalanceSnapshot" and (_parse_date(str(entry.get("entry_date", ""))) or date.max) <= as_of
    ]
    if not snapshots:
        return None
    latest = max(snapshots, key=lambda row: (str(row.get("entry_date", "")), str(row.get("created_at", ""))))
    return float(latest.get("amount", 0.0) or 0.0)


def _latest_balance_date(entries: list[dict[str, Any]], as_of: date) -> str | None:
    snapshots = [
        entry
        for entry in entries
        if entry.get("direction") == "BalanceSnapshot" and (_parse_date(str(entry.get("entry_date", ""))) or date.max) <= as_of
    ]
    if not snapshots:
        return None
    latest = max(snapshots, key=lambda row: (str(row.get("entry_date", "")), str(row.get("created_at", ""))))
    return str(latest.get("entry_date", "")) or None


def _sum_direction(entries: list[dict[str, Any]], direction: str) -> float:
    return round(sum(float(entry.get("amount", 0.0) or 0.0) for entry in entries if entry.get("direction") == direction), 2)


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


def _clean_direction(value: str) -> str:
    raw = str(value or "").strip()
    aliases = {
        "收入": "Inflow",
        "支出": "Outflow",
        "余额": "BalanceSnapshot",
        "应收": "Receivable",
        "应付": "Payable",
    }
    raw = aliases.get(raw, raw)
    if raw not in CASHFLOW_DIRECTIONS:
        raise ValueError(f"Unsupported cashflow direction: {value}")
    return raw


def _clean_category(value: str) -> str:
    raw = str(value or "Other").strip().replace(" ", "")
    return raw or "Other"


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


def _evidence_status(evidence_link: str, evidence_path: str) -> str:
    return "Pass" if evidence_link.strip() or evidence_path.strip() else "Missing"


def _entry_next_action(review_status: str, evidence_status: str) -> str:
    if review_status == "Rejected":
        return "Keep archived; do not count this cashflow entry."
    if evidence_status != "Pass":
        return "Attach invoice, receipt, bank screenshot, ledger link, or other reviewable evidence."
    if review_status != "Reviewed":
        return "Review amount, direction, category, date, and evidence before counting."
    return "Counted in Company CashFlow Command summaries."


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
    writer = csv.DictWriter(handle, fieldnames=CASHFLOW_COLUMNS, extrasaction="ignore")
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


def _write_cashflow_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"PFI_OS Company CashFlow Command {payload.get('as_of', '')}",
        f"Generated At: {payload.get('generated_at', '')}",
        f"Status: {payload.get('cashflow_status', '')}",
        f"Runtime Status: {runtime.get('status', '')}",
        f"Latest Balance: {summary.get('latest_balance', None)}",
        f"Latest Balance Date: {summary.get('latest_balance_date', None)}",
        f"Inflow: {summary.get('inflow', 0.0)}",
        f"Outflow: {summary.get('outflow', 0.0)}",
        f"Net Cashflow: {summary.get('net_cashflow', 0.0)}",
        f"Runway Days: {summary.get('runway_days', None)}",
        "",
        "Runtime Evidence Gate:",
    ]
    for gate in runtime.get("evidence_gate", [])[:8]:
        lines.append(f"- {gate.get('gate')}: {gate.get('status')} | {gate.get('evidence')}")
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
    return f"cashflow_{digest}"


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
