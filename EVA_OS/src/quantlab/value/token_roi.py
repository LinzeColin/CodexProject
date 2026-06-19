from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from quantlab.config import PROJECT_ROOT, REPORT_ROOT_DIR
from quantlab.reports.catalog import collect_report_artifacts
from quantlab.storage import atomic_write_json, atomic_write_text, locked_json_update, read_json_state
from quantlab.system.eva_identity import MASTER_SYSTEM_ID

MANUAL_TOKEN_ROI_PATH = PROJECT_ROOT / "data" / "value" / "TokenROIManualEntries.json"


TOKEN_ROI_COLUMNS = [
    "roi_id",
    "record_type",
    "subsystem",
    "artifact_type",
    "title",
    "source_path",
    "run_date",
    "task_goal",
    "file_modified_at",
    "size_kb",
    "value_contribution",
    "evidence_level",
    "decision_level",
    "review_status",
    "token_estimate",
    "ai_cost",
    "human_time_cost",
    "revenue_generated",
    "cost_saved",
    "loss_avoided",
    "asset_reuse_value",
    "roi_score",
    "value_status",
    "time_saved_hours",
    "reuse_count",
    "evidence_link",
    "notes",
    "next_action",
]

TOKEN_ROI_FINANCIAL_FIELDS = [
    "ai_cost",
    "human_time_cost",
    "revenue_generated",
    "cost_saved",
    "loss_avoided",
    "asset_reuse_value",
]


def build_token_roi_ledger(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    manual_entry_path: Path | str | None = None,
    artifact_limit: int = 300,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    ledger_date = as_of or datetime.now().date().isoformat()
    manual_path = Path(manual_entry_path).expanduser() if manual_entry_path else root / "data" / "value" / "TokenROIManualEntries.json"
    manual_entries = load_manual_token_roi_entries(manual_path)
    records = (
        _collect_system_audit_records(root)
        + _collect_command_center_records(root)
        + _collect_report_decision_records(root)
        + _collect_validation_queue_records(root)
        + _collect_report_records(reports)
        + manual_entries
    )
    unique_records = _deduplicate_records(records)
    unique_records.sort(key=lambda row: str(row.get("file_modified_at", "")), reverse=True)
    limited = unique_records[: max(1, int(artifact_limit))]
    summary = _summary(limited)
    payload = {
        "schema": "EVATokenROILedgerV1",
        "system": MASTER_SYSTEM_ID,
        "subsystem": "Token ROI Ledger",
        "as_of": ledger_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "report_root": str(reports),
        "record_count": len(limited),
        "summary": summary,
        "formula": "Token ROI = (revenue_generated + cost_saved + loss_avoided + asset_reuse_value - ai_cost - human_time_cost) / (ai_cost + human_time_cost)",
        "assumptions": [
            "This ledger records reusable value evidence; it does not fabricate financial gains.",
            "Financial fields stay 0.00 and roi_score stays null until the user supplies measured revenue, cost saved, loss avoided, asset reuse value, AI cost, or human time cost.",
            "Manual value entries are counted as Quantified only when review_status is Reviewed and at least one real financial field is supplied.",
            "System audit, readiness, validation queue, report, metadata, data-quality, and cross-validation files are FACT evidence that the output exists and can be reviewed.",
            "value_contribution is an INFERENCE used for prioritization, not proof of cash profit.",
            "Research-only boundary remains active: no live trading, no real orders, no payments, no betting execution.",
        ],
        "manual_value_entry_path": _relative_path(manual_path, root),
        "records": limited,
    }
    payload["runtime_summary"] = build_token_roi_runtime_summary(payload)
    return payload


def build_token_roi_runtime_summary(payload: dict[str, Any]) -> dict[str, Any]:
    records = [record for record in payload.get("records", []) if isinstance(record, dict)]
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    totals = summary.get("financial_totals", {}) if isinstance(summary.get("financial_totals"), dict) else {}
    quantified = [record for record in records if record.get("value_status") == "Quantified"]
    manual = [record for record in records if record.get("record_type") == "ManualValueEvidence"]
    artifact = [record for record in records if record.get("record_type") == "ArtifactEvidence"]
    pending_manual = [record for record in manual if record.get("review_status") == "PendingReview"]
    rejected_manual = [record for record in manual if record.get("review_status") == "Rejected"]
    pending_with_amounts = [record for record in pending_manual if _has_financial_input(record)]
    quantified_without_evidence = [
        record for record in quantified if not str(record.get("evidence_link") or record.get("source_path") or "").strip()
    ]
    cost_total = _money(totals.get("ai_cost", 0.0)) + _money(totals.get("human_time_cost", 0.0))
    benefit_total = (
        _money(totals.get("revenue_generated", 0.0))
        + _money(totals.get("cost_saved", 0.0))
        + _money(totals.get("loss_avoided", 0.0))
        + _money(totals.get("asset_reuse_value", 0.0))
    )
    aggregate_roi_score = round((benefit_total - cost_total) / cost_total, 4) if cost_total > 0 else None
    gates = [
        _token_roi_gate(
            "LedgerSchema",
            "Pass" if payload.get("schema") == "EVATokenROILedgerV1" else "Blocked",
            f"schema={payload.get('schema', '')}",
        ),
        _token_roi_gate("RecordsPresent", "Pass" if records else "Review", f"records={len(records)}"),
        _token_roi_gate(
            "QuantifiedValuePresent",
            "Pass" if quantified else "Review",
            f"quantified={len(quantified)}; unquantified={max(0, len(records) - len(quantified))}",
        ),
        _token_roi_gate(
            "PendingValueReview",
            "Review" if pending_manual else "Pass",
            f"pending_manual={len(pending_manual)}; pending_with_amounts={len(pending_with_amounts)}",
        ),
        _token_roi_gate(
            "QuantifiedEvidenceLinks",
            "Review" if quantified_without_evidence else "Pass",
            f"quantified_without_evidence={len(quantified_without_evidence)}",
        ),
        _token_roi_gate(
            "FormulaReady",
            "Review" if quantified and cost_total <= 0 else "Pass",
            f"benefit_total={benefit_total:.2f}; cost_total={cost_total:.2f}; aggregate_roi_score={aggregate_roi_score}",
        ),
        _token_roi_gate(
            "ResearchOnlyBoundary",
            "Pass",
            "does not trade, pay, place orders, or infer financial value without reviewed evidence",
        ),
    ]
    token_estimate_total = sum(_non_negative_int(record.get("token_estimate", 0)) for record in manual)
    time_saved_hours_total = round(sum(_non_negative_float(record.get("time_saved_hours", 0.0)) for record in quantified), 2)
    reuse_count_total = sum(_non_negative_int(record.get("reuse_count", 0)) for record in quantified)
    return {
        "schema": "EVATokenROIRuntimeSummaryV1",
        "ledger_schema": str(payload.get("schema", "")),
        "as_of": str(payload.get("as_of", "")),
        "generated_at": str(payload.get("generated_at", "")),
        "status": _token_roi_status(gates),
        "record_count": len(records),
        "artifact_record_count": len(artifact),
        "manual_record_count": len(manual),
        "quantified_records": len(quantified),
        "unquantified_records": max(0, len(records) - len(quantified)),
        "pending_manual_records": len(pending_manual),
        "pending_financial_hypothesis_count": len(pending_with_amounts),
        "rejected_manual_records": len(rejected_manual),
        "quantified_without_evidence_count": len(quantified_without_evidence),
        "financial_totals": {
            "benefit_total": round(benefit_total, 2),
            "cost_total": round(cost_total, 2),
            "net_value": round(benefit_total - cost_total, 2),
            "aggregate_roi_score": aggregate_roi_score,
            "revenue_generated": _money(totals.get("revenue_generated", 0.0)),
            "cost_saved": _money(totals.get("cost_saved", 0.0)),
            "loss_avoided": _money(totals.get("loss_avoided", 0.0)),
            "asset_reuse_value": _money(totals.get("asset_reuse_value", 0.0)),
            "ai_cost": _money(totals.get("ai_cost", 0.0)),
            "human_time_cost": _money(totals.get("human_time_cost", 0.0)),
        },
        "manual_input_totals": {
            "token_estimate_total": token_estimate_total,
            "time_saved_hours_total": time_saved_hours_total,
            "reuse_count_total": reuse_count_total,
        },
        "top_value_contributions": list(summary.get("value_contribution_counts", []))[:8],
        "top_artifact_types": list(summary.get("artifact_type_counts", []))[:8],
        "evidence_gate": gates,
        "token_policy": (
            "Compact Token ROI runtime summary for UI and agent handoff; it does not include full records and "
            "does not rescan report artifacts beyond the ledger build."
        ),
        "safety_boundary": (
            "Research-only value accounting. No live trading, no real orders, no payments, no bank transfers, "
            "and no fabricated revenue, savings, avoided loss, or ROI."
        ),
    }


def create_manual_token_roi_entry(
    *,
    run_date: str,
    task_goal: str,
    title: str = "",
    subsystem: str = "EVA_OS",
    value_contribution: str = "Decision Support",
    evidence_link: str = "",
    output_path: str = "",
    token_estimate: int = 0,
    ai_cost: float = 0.0,
    human_time_cost: float = 0.0,
    revenue_generated: float = 0.0,
    cost_saved: float = 0.0,
    loss_avoided: float = 0.0,
    asset_reuse_value: float = 0.0,
    time_saved_hours: float = 0.0,
    reuse_count: int = 0,
    review_status: str = "PendingReview",
    notes: str = "",
) -> dict[str, Any]:
    clean_title = title.strip() or task_goal.strip()
    clean_run_date = run_date.strip() or datetime.now().date().isoformat()
    clean_goal = task_goal.strip()
    if not clean_goal:
        raise ValueError("task_goal is required for a manual Token ROI entry.")
    status = _clean_review_status(review_status)
    financial_values = {
        "ai_cost": _money(ai_cost),
        "human_time_cost": _money(human_time_cost),
        "revenue_generated": _money(revenue_generated),
        "cost_saved": _money(cost_saved),
        "loss_avoided": _money(loss_avoided),
        "asset_reuse_value": _money(asset_reuse_value),
    }
    cost_base = financial_values["ai_cost"] + financial_values["human_time_cost"]
    benefit = financial_values["revenue_generated"] + financial_values["cost_saved"] + financial_values["loss_avoided"] + financial_values["asset_reuse_value"]
    roi_score = round((benefit - cost_base) / cost_base, 4) if cost_base > 0 else None
    has_financial_input = any(value > 0 for value in financial_values.values())
    value_status = "Quantified" if status == "Reviewed" and has_financial_input else "PendingReview"
    source_path = output_path.strip() or evidence_link.strip()
    created_at = datetime.now().isoformat(timespec="seconds")
    payload = {
        "roi_id": _stable_id("manual", clean_run_date, clean_goal, clean_title, created_at),
        "record_type": "ManualValueEvidence",
        "subsystem": subsystem.strip() or "EVA_OS",
        "artifact_type": "Manual Value Evidence",
        "title": clean_title,
        "source_path": source_path,
        "run_date": clean_run_date,
        "task_goal": clean_goal,
        "file_modified_at": created_at,
        "size_kb": 0.0,
        "value_contribution": value_contribution.strip() or "Decision Support",
        "evidence_level": "FACT" if evidence_link.strip() or output_path.strip() else "OBSERVATION",
        "decision_level": "Observe",
        "review_status": status,
        "token_estimate": max(0, int(token_estimate or 0)),
        **financial_values,
        "roi_score": roi_score if value_status == "Quantified" else None,
        "value_status": value_status,
        "time_saved_hours": round(float(time_saved_hours or 0.0), 2),
        "reuse_count": max(0, int(reuse_count or 0)),
        "evidence_link": evidence_link.strip(),
        "notes": notes.strip(),
        "created_at": created_at,
        "next_action": _manual_next_action(value_status),
    }
    return payload


def append_manual_token_roi_entry(entry: dict[str, Any], path: Path | str = MANUAL_TOKEN_ROI_PATH) -> Path:
    clean_entry = _normalize_manual_entry(entry)

    def append_entry(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [_normalize_manual_entry(item) for item in payload if isinstance(item, dict)]
        rows.append(clean_entry)
        return rows

    return locked_json_update(path, [], append_entry, expected_type=list)


def load_manual_token_roi_entries(path: Path | str = MANUAL_TOKEN_ROI_PATH) -> list[dict[str, Any]]:
    payload = read_json_state(path, [], expected_type=list, fail_closed=True)
    return [_normalize_manual_entry(item) for item in payload if isinstance(item, dict)]


def write_token_roi_ledger(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    manual_entry_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    artifact_limit: int = 300,
) -> dict[str, Any]:
    payload = build_token_roi_ledger(
        as_of=as_of,
        project_root=project_root,
        report_root=report_root,
        manual_entry_path=manual_entry_path,
        artifact_limit=artifact_limit,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "value"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"EVATokenROILedger_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "EVATokenROILedger_latest.json"
    latest_csv = target / "EVATokenROILedger_latest.csv"
    latest_markdown = target / "EVATokenROILedger_latest.md"
    latest_pdf = target / "EVATokenROILedger_latest.pdf"
    runtime_summary_json = target / f"EVATokenROIRuntimeSummary_{stamp}.json"
    latest_runtime_summary_json = target / "EVATokenROIRuntimeSummary_latest.json"
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
    payload["runtime_summary"] = build_token_roi_runtime_summary(payload)
    payload["runtime_summary"]["outputs"] = {
        "runtime_summary_json": str(runtime_summary_json),
        "latest_runtime_summary_json": str(latest_runtime_summary_json),
        "ledger_json": str(json_path),
        "latest_ledger_json": str(latest_json),
    }
    markdown = token_roi_ledger_markdown(payload)
    csv_text = _csv_text(payload.get("records", []))
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_token_roi_pdf(pdf_path, payload)
    _write_token_roi_pdf(latest_pdf, payload)
    atomic_write_json(runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(latest_runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    return payload


def token_roi_ledger_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"# EVA_OS Token ROI Ledger {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- System: `{payload.get('system', '')}`",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        f"- Runtime Status: `{runtime.get('status', '')}`",
        f"- Record Count: `{payload.get('record_count', 0)}`",
        f"- Quantified Records: `{summary.get('quantified_records', 0)}`",
        f"- Unquantified Records: `{summary.get('unquantified_records', 0)}`",
        f"- Formula: `{payload.get('formula', '')}`",
        f"- Token Policy: {runtime.get('token_policy', '')}",
        "",
        "## Runtime Evidence Gate",
        _markdown_table(runtime.get("evidence_gate", []), ["gate", "status", "evidence"]),
        "",
        "## Value Contribution",
        _markdown_table(summary.get("value_contribution_counts", []), ["value_contribution", "count"]),
        "",
        "## Artifact Types",
        _markdown_table(summary.get("artifact_type_counts", []), ["artifact_type", "count"]),
        "",
        "## Records",
        _markdown_table(payload.get("records", [])[:80], ["artifact_type", "title", "value_contribution", "value_status", "source_path", "next_action"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _collect_system_audit_records(root: Path) -> list[dict[str, Any]]:
    audit_dir = root / "data" / "systemAudit"
    if not audit_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(audit_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.name.startswith("."):
            continue
        rows.append(_record_from_path(path, root, artifact_type=_system_audit_type(path), subsystem="EVA_OS Foundation"))
    return rows


def _collect_command_center_records(root: Path) -> list[dict[str, Any]]:
    command_dir = root / "data" / "commandCenter"
    if not command_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(command_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.name.startswith("."):
            continue
        rows.append(_record_from_path(path, root, artifact_type="Executive Command Center", subsystem="EVA_OS Foundation"))
    return rows


def _collect_report_decision_records(root: Path) -> list[dict[str, Any]]:
    decision_dir = root / "data" / "reportDecision"
    if not decision_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(decision_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.name.startswith("."):
            continue
        rows.append(_record_from_path(path, root, artifact_type="Report Decision Support Index", subsystem="QuantLab"))
    return rows


def _collect_validation_queue_records(root: Path) -> list[dict[str, Any]]:
    queue_dir = root / "data" / "validationQueue"
    if not queue_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.name.startswith(".") or path.name.endswith(".lock"):
            continue
        rows.append(_record_from_path(path, root, artifact_type=_validation_queue_type(path), subsystem="QuantLab"))
    return rows


def _collect_report_records(report_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in collect_report_artifacts(report_root):
        rows.append(
            _record_from_path(
                Path(artifact.path),
                report_root,
                artifact_type=str(artifact.artifact_type),
                subsystem="QuantLab",
                source_path=str(Path(artifact.path)),
                title=artifact.name,
            )
        )
    return rows


def _record_from_path(
    path: Path,
    base: Path,
    *,
    artifact_type: str,
    subsystem: str,
    source_path: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    stat = path.stat()
    file_modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    normalized_source = source_path or _relative_path(path, base)
    value_contribution = _value_contribution(artifact_type, path.name)
    cost_base = 0.0
    return {
        "roi_id": _stable_id(str(path), str(stat.st_mtime_ns), str(stat.st_size)),
        "record_type": "ArtifactEvidence",
        "subsystem": subsystem,
        "artifact_type": artifact_type,
        "title": title or path.stem,
        "source_path": normalized_source,
        "run_date": file_modified_at[:10],
        "task_goal": "Review reusable EVA_OS evidence artifact.",
        "file_modified_at": file_modified_at,
        "size_kb": round(stat.st_size / 1024, 2),
        "value_contribution": value_contribution,
        "evidence_level": "FACT",
        "decision_level": "Observe",
        "review_status": "Recorded",
        "token_estimate": 0,
        "ai_cost": 0.0,
        "human_time_cost": 0.0,
        "revenue_generated": 0.0,
        "cost_saved": 0.0,
        "loss_avoided": 0.0,
        "asset_reuse_value": 0.0,
        "roi_score": None if cost_base == 0 else 0.0,
        "value_status": "Unquantified",
        "time_saved_hours": 0.0,
        "reuse_count": 0,
        "evidence_link": "",
        "notes": "",
        "next_action": _next_action(value_contribution),
    }


def _system_audit_type(path: Path) -> str:
    name = path.name
    if "DailyReadiness" in name:
        return "Daily Readiness"
    if "DataTrust" in name:
        return "Data Trust Audit"
    if "IntegrationAudit" in name:
        return "Integration Audit"
    return "System Audit"


def _validation_queue_type(path: Path) -> str:
    name = path.name
    if "ValidationTaskPriorityPlan" in name:
        return "Validation Task Priority Plan"
    if "ValidationTaskExecution" in name or "CrossValidation" in name:
        return "Validation Task Execution"
    if "ValidationTasks" in name:
        return "Validation Task Queue"
    return "Validation Queue Artifact"


def _value_contribution(artifact_type: str, name: str) -> str:
    text = f"{artifact_type} {name}".lower()
    if "data trust" in text or "data quality" in text or "cross validation" in text:
        return "Data Credibility"
    if "integration" in text or "readiness" in text or "system audit" in text or "command center" in text:
        return "System Reliability"
    if "runmetadata" in text or "metadata" in text:
        return "Traceability"
    if "word report" in text or "backtest" in text or "experiment research" in text:
        return "Decision Support"
    if "experiment" in text or "walk forward" in text or "validation" in text:
        return "Validation Efficiency"
    return "Reusable Asset"


def _next_action(value_contribution: str) -> str:
    if value_contribution == "Data Credibility":
        return "Use as evidence only after checking freshness, source, and limitations."
    if value_contribution == "System Reliability":
        return "Keep this gate green before relying on downstream research outputs."
    if value_contribution == "Traceability":
        return "Link this metadata to the related report and decision record."
    if value_contribution == "Decision Support":
        return "Review risk gates and missing evidence before using as decision support."
    if value_contribution == "Validation Efficiency":
        return "Compare against out-of-sample and walk-forward evidence before promotion."
    return "Decide whether this artifact should become a reusable asset or be archived."


def _manual_next_action(value_status: str) -> str:
    if value_status == "Quantified":
        return "Use this reviewed value entry in Token ROI summaries and keep its evidence link current."
    return "Review the evidence, confirm real cost or benefit, then mark review_status as Reviewed."


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


def _money(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        amount = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0
    if amount < 0:
        return 0.0
    return round(amount, 2)


def _non_negative_float(value: Any) -> float:
    try:
        amount = float(value or 0.0)
    except (TypeError, ValueError):
        amount = 0.0
    return round(max(0.0, amount), 2)


def _non_negative_int(value: Any) -> int:
    try:
        amount = int(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return max(0, amount)


def _normalize_manual_entry(entry: dict[str, Any]) -> dict[str, Any]:
    run_date = str(entry.get("run_date") or datetime.now().date().isoformat()).strip()
    task_goal = str(entry.get("task_goal") or entry.get("title") or "Manual Token ROI evidence").strip()
    title = str(entry.get("title") or task_goal).strip()
    review_status = _clean_review_status(entry.get("review_status", "PendingReview"))
    financial_values = {
        "ai_cost": _money(entry.get("ai_cost", 0.0)),
        "human_time_cost": _money(entry.get("human_time_cost", 0.0)),
        "revenue_generated": _money(entry.get("revenue_generated", 0.0)),
        "cost_saved": _money(entry.get("cost_saved", 0.0)),
        "loss_avoided": _money(entry.get("loss_avoided", 0.0)),
        "asset_reuse_value": _money(entry.get("asset_reuse_value", 0.0)),
    }
    benefit = (
        financial_values["revenue_generated"]
        + financial_values["cost_saved"]
        + financial_values["loss_avoided"]
        + financial_values["asset_reuse_value"]
    )
    cost_base = financial_values["ai_cost"] + financial_values["human_time_cost"]
    has_financial_input = any(value > 0 for value in financial_values.values())
    value_status = "Quantified" if review_status == "Reviewed" and has_financial_input else "PendingReview"
    roi_score = round((benefit - cost_base) / cost_base, 4) if value_status == "Quantified" and cost_base > 0 else None
    created_at = str(entry.get("created_at") or entry.get("file_modified_at") or datetime.now().isoformat(timespec="seconds"))
    source_path = str(entry.get("source_path") or entry.get("output_path") or entry.get("evidence_link") or "").strip()
    evidence_link = str(entry.get("evidence_link") or "").strip()
    output = {
        "roi_id": str(entry.get("roi_id") or _stable_id("manual", run_date, task_goal, title, created_at)),
        "record_type": "ManualValueEvidence",
        "subsystem": str(entry.get("subsystem") or "EVA_OS").strip() or "EVA_OS",
        "artifact_type": "Manual Value Evidence",
        "title": title,
        "source_path": source_path,
        "run_date": run_date,
        "task_goal": task_goal,
        "file_modified_at": created_at,
        "size_kb": 0.0,
        "value_contribution": str(entry.get("value_contribution") or "Decision Support").strip() or "Decision Support",
        "evidence_level": "FACT" if source_path or evidence_link else "OBSERVATION",
        "decision_level": "Observe",
        "review_status": review_status,
        "token_estimate": _non_negative_int(entry.get("token_estimate", 0)),
        **financial_values,
        "roi_score": roi_score,
        "value_status": value_status,
        "time_saved_hours": _non_negative_float(entry.get("time_saved_hours", 0.0)),
        "reuse_count": _non_negative_int(entry.get("reuse_count", 0)),
        "evidence_link": evidence_link,
        "notes": str(entry.get("notes") or "").strip(),
        "created_at": created_at,
        "next_action": _manual_next_action(value_status),
    }
    return output


def _deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        key = str(record.get("source_path") or record.get("roi_id") or "")
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    quantified = [row for row in records if row.get("value_status") == "Quantified"]
    return {
        "total_records": len(records),
        "quantified_records": len(quantified),
        "unquantified_records": len(records) - len(quantified),
        "artifact_type_counts": _count_rows(records, "artifact_type"),
        "value_contribution_counts": _count_rows(records, "value_contribution"),
        "financial_totals": {
            "ai_cost": _sum_float(quantified, "ai_cost"),
            "human_time_cost": _sum_float(quantified, "human_time_cost"),
            "revenue_generated": _sum_float(quantified, "revenue_generated"),
            "cost_saved": _sum_float(quantified, "cost_saved"),
            "loss_avoided": _sum_float(quantified, "loss_avoided"),
            "asset_reuse_value": _sum_float(quantified, "asset_reuse_value"),
        },
    }


def _count_rows(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key, "") or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return [{"value_contribution" if key == "value_contribution" else "artifact_type": value, "count": count} for value, count in sorted(counts.items())]


def _sum_float(records: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    for record in records:
        try:
            total += float(record.get(key, 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
    return round(total, 2)


def _has_financial_input(record: dict[str, Any]) -> bool:
    return any(_money(record.get(field, 0.0)) > 0 for field in TOKEN_ROI_FINANCIAL_FIELDS)


def _token_roi_gate(gate: str, status: str, evidence: str) -> dict[str, str]:
    clean_status = status if status in {"Pass", "Review", "Blocked"} else "Review"
    return {"gate": gate, "status": clean_status, "evidence": evidence}


def _token_roi_status(gates: list[dict[str, str]]) -> str:
    statuses = {str(gate.get("status", "")) for gate in gates}
    if "Blocked" in statuses:
        return "Blocked"
    if "Review" in statuses:
        return "NeedsReview"
    return "Pass"


def _csv_text(records: list[dict[str, Any]]) -> str:
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=TOKEN_ROI_COLUMNS, extrasaction="ignore")
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


def _write_token_roi_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"EVA_OS Token ROI Ledger {payload.get('as_of', '')}",
        f"Generated At: {payload.get('generated_at', '')}",
        f"System: {payload.get('system', '')}",
        f"Runtime Status: {runtime.get('status', '')}",
        f"Record Count: {payload.get('record_count', 0)}",
        f"Quantified Records: {summary.get('quantified_records', 0)}",
        f"Unquantified Records: {summary.get('unquantified_records', 0)}",
        f"Benefit Total: {runtime.get('financial_totals', {}).get('benefit_total', 0.0)}",
        f"Cost Total: {runtime.get('financial_totals', {}).get('cost_total', 0.0)}",
        "",
        "Formula:",
        str(payload.get("formula", "")),
        "",
        "Runtime Evidence Gate:",
    ]
    for gate in runtime.get("evidence_gate", [])[:8]:
        lines.append(f"- {gate.get('gate')}: {gate.get('status')} | {gate.get('evidence')}")
    lines.extend([
        "",
        "Top Records:",
    ])
    for row in payload.get("records", [])[:28]:
        lines.append(f"- {row.get('artifact_type')}: {row.get('title')} | {row.get('value_contribution')} | {row.get('value_status')}")
    lines.extend(["", "Assumptions:"])
    for item in payload.get("assumptions", [])[:8]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Research-only. No live trading. No real orders.")
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


def _relative_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"tokenRoi_{digest}"


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
