from __future__ import annotations

import csv
import hashlib
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json, atomic_write_text, locked_json_update, read_json_state
from pfi_os.system.pfi_identity import MASTER_SYSTEM_ID

POLICY_ENTRY_PATH = PROJECT_ROOT / "data" / "policy" / "PolicyOpportunityEntries.json"

POLICY_SOURCE_TYPES = ("Official", "Regulator", "Government", "Exchange", "Research", "News", "Manual")
POLICY_LEVELS = ("National", "State", "City", "Agency", "Industry", "Company", "Unknown")
POLICY_OPPORTUNITY_TYPES = ("Subsidy", "RegulatoryChange", "Procurement", "Tax", "IndustrySupport", "RiskWarning", "Compliance", "Other")
POLICY_COLUMNS = [
    "policy_id",
    "published_date",
    "title",
    "jurisdiction",
    "policy_level",
    "source_name",
    "source_type",
    "source_url",
    "evidence_path",
    "evidence_status",
    "review_status",
    "opportunity_type",
    "sectors",
    "affected_entities",
    "impact_summary",
    "required_action",
    "authority_score",
    "relevance_score",
    "urgency_score",
    "feasibility_score",
    "impact_score",
    "opportunity_status",
    "notes",
    "created_at",
    "updated_at",
    "next_action",
]


def create_policy_opportunity(
    *,
    published_date: str,
    title: str,
    source_name: str,
    source_type: str,
    source_url: str = "",
    evidence_path: str = "",
    jurisdiction: str = "",
    policy_level: str = "Unknown",
    opportunity_type: str = "Other",
    sectors: str | list[str] = "",
    affected_entities: str | list[str] = "",
    impact_summary: str = "",
    required_action: str = "",
    authority_score: float = 0.0,
    relevance_score: float = 0.0,
    urgency_score: float = 0.0,
    feasibility_score: float = 0.0,
    review_status: str = "PendingReview",
    notes: str = "",
) -> dict[str, Any]:
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("title is required for a policy opportunity.")
    clean_source = source_name.strip()
    if not clean_source:
        raise ValueError("source_name is required for a policy opportunity.")
    clean_date = _clean_date(published_date)
    clean_source_type = _clean_choice(source_type, POLICY_SOURCE_TYPES, "Manual")
    clean_policy_level = _clean_choice(policy_level, POLICY_LEVELS, "Unknown")
    clean_opportunity_type = _clean_choice(opportunity_type, POLICY_OPPORTUNITY_TYPES, "Other")
    created_at = datetime.now().isoformat(timespec="seconds")
    raw = {
        "policy_id": _stable_id("policy", clean_date, clean_title, clean_source, created_at),
        "published_date": clean_date,
        "title": clean_title,
        "jurisdiction": jurisdiction.strip() or "Unknown",
        "policy_level": clean_policy_level,
        "source_name": clean_source,
        "source_type": clean_source_type,
        "source_url": source_url.strip(),
        "evidence_path": evidence_path.strip(),
        "review_status": _clean_review_status(review_status),
        "opportunity_type": clean_opportunity_type,
        "sectors": _join_items(sectors),
        "affected_entities": _join_items(affected_entities),
        "impact_summary": impact_summary.strip(),
        "required_action": required_action.strip(),
        "authority_score": authority_score,
        "relevance_score": relevance_score,
        "urgency_score": urgency_score,
        "feasibility_score": feasibility_score,
        "notes": notes.strip(),
        "created_at": created_at,
        "updated_at": created_at,
    }
    return _normalize_opportunity(raw)


def append_policy_opportunity(entry: dict[str, Any], path: Path | str = POLICY_ENTRY_PATH) -> Path:
    clean_entry = _normalize_opportunity(entry)

    def append_entry(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [_normalize_opportunity(item) for item in payload if isinstance(item, dict)]
        rows.append(clean_entry)
        return rows

    return locked_json_update(path, [], append_entry, expected_type=list)


def load_policy_opportunities(path: Path | str = POLICY_ENTRY_PATH) -> list[dict[str, Any]]:
    payload = read_json_state(path, [], expected_type=list, fail_closed=True)
    return [_normalize_opportunity(item) for item in payload if isinstance(item, dict)]


def build_policy_radar(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    entry_path: Path | str | None = None,
    opportunities: list[dict[str, Any]] | None = None,
    opportunity_limit: int = 300,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    audit_date = _clean_date(as_of or date.today().isoformat())
    if opportunities is None:
        path = Path(entry_path).expanduser() if entry_path else root / "data" / "policy" / "PolicyOpportunityEntries.json"
        entries = load_policy_opportunities(path)
        entry_source = str(path)
    else:
        entries = [_normalize_opportunity(item) for item in opportunities if isinstance(item, dict)]
        entry_source = "operational_store:private_reviewed_inputs/policy_radar"
    entries.sort(key=lambda row: (float(row.get("impact_score", 0.0) or 0.0), str(row.get("published_date", ""))), reverse=True)
    limited = entries[: max(1, int(opportunity_limit))]
    summary = _summary(limited)
    payload = {
        "schema": "PFIOSPolicyIntelligenceRadarV1",
        "system": MASTER_SYSTEM_ID,
        "subsystem": "Policy Intelligence Radar",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "entry_path": entry_source,
        "opportunity_count": len(limited),
        "policy_status": summary["policy_status"],
        "summary": summary,
        "action_queue": _action_queue(summary, limited),
        "sector_exposure": _sector_exposure(limited),
        "opportunities": limited,
        "assumptions": [
            "This radar stores manually reviewed policy opportunities; it does not claim real-time policy coverage.",
            "Only Reviewed opportunities with Official/Regulator/Government/Exchange source type and source evidence are Actionable.",
            "Research, News, or Manual sources can support Watch or Observe status, but not Actionable policy decisions.",
            "Scores are prioritization aids, not proof of subsidy availability, regulatory approval, investment return, or compliance advice.",
            "No trading, payment, application submission, legal filing, or government-portal action is executed.",
        ],
    }
    payload["runtime_summary"] = build_policy_runtime_summary(payload)
    return payload


def build_policy_runtime_summary(payload: dict[str, Any]) -> dict[str, Any]:
    opportunities = [row for row in payload.get("opportunities", []) if isinstance(row, dict)]
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    authoritative_sources = [row for row in opportunities if row.get("source_type") in {"Official", "Regulator", "Government", "Exchange"}]
    needs_authority = [row for row in opportunities if row.get("evidence_status") == "NeedsAuthorityReview"]
    missing_evidence = [row for row in opportunities if row.get("evidence_status") == "Missing"]
    reviewed_missing_evidence = [
        row for row in opportunities if row.get("review_status") == "Reviewed" and row.get("evidence_status") != "Pass"
    ]
    pending = [row for row in opportunities if row.get("review_status") == "PendingReview"]
    rejected = [row for row in opportunities if row.get("review_status") == "Rejected"]
    actionable = [row for row in opportunities if row.get("opportunity_status") == "Actionable"]
    broken_actionable = [
        row
        for row in actionable
        if row.get("review_status") != "Reviewed"
        or row.get("evidence_status") != "Pass"
        or row.get("source_type") not in {"Official", "Regulator", "Government", "Exchange"}
    ]
    gates = [
        _policy_gate(
            "CommandSchema",
            "Pass" if payload.get("schema") == "PFIOSPolicyIntelligenceRadarV1" else "Blocked",
            f"schema={payload.get('schema', '')}",
        ),
        _policy_gate(
            "PolicyEvidence",
            "Pass" if opportunities else "Blocked",
            f"opportunity_count={len(opportunities)}",
        ),
        _policy_gate(
            "SourceAuthority",
            "Review" if needs_authority else "Pass",
            f"authoritative_sources={len(authoritative_sources)}; needs_authority_review={len(needs_authority)}",
        ),
        _policy_gate(
            "EvidenceCompleteness",
            "Review" if missing_evidence or reviewed_missing_evidence else "Pass",
            f"missing_evidence={len(missing_evidence)}; reviewed_missing_evidence={len(reviewed_missing_evidence)}",
        ),
        _policy_gate(
            "ManualReview",
            "Review" if pending else "Pass",
            f"pending_review={len(pending)}; rejected={len(rejected)}",
        ),
        _policy_gate(
            "ActionableQuality",
            "Blocked" if broken_actionable else "Pass",
            f"actionable={len(actionable)}; broken_actionable={len(broken_actionable)}",
        ),
        _policy_gate(
            "NoExternalExecution",
            "Pass",
            "does not log in to government portals, submit applications, pay fees, file legal documents, or trade",
        ),
    ]
    return {
        "schema": "PFIOSPolicyIntelligenceRuntimeSummaryV1",
        "command_schema": str(payload.get("schema", "")),
        "as_of": str(payload.get("as_of", "")),
        "generated_at": str(payload.get("generated_at", "")),
        "status": _policy_runtime_status(gates),
        "policy_status": str(payload.get("policy_status", "")),
        "opportunity_count": len(opportunities),
        "actionable_count": int(summary.get("actionable_count", 0) or 0),
        "watch_count": int(summary.get("watch_count", 0) or 0),
        "observe_count": int(summary.get("observe_count", 0) or 0),
        "missing_evidence_count": int(summary.get("missing_evidence_count", 0) or 0),
        "pending_review_count": int(summary.get("pending_review_count", 0) or 0),
        "authoritative_source_records": len(authoritative_sources),
        "needs_authority_review_records": len(needs_authority),
        "reviewed_missing_evidence_records": len(reviewed_missing_evidence),
        "rejected_records": len(rejected),
        "max_impact_score": float(summary.get("max_impact_score", 0.0) or 0.0),
        "evidence_gate": gates,
        "top_actions": list(payload.get("action_queue", []))[:5],
        "top_opportunities": [_compact_policy_opportunity(row) for row in opportunities[:5]],
        "token_policy": (
            "Compact Policy Intelligence runtime summary for UI and agent handoff; it does not include full opportunities "
            "and does not read live policy feeds."
        ),
        "safety_boundary": (
            "Local policy evidence review only. No government-portal login, no application submission, no payment, "
            "no legal, tax, compliance, subsidy, or investment conclusion, and no trading execution."
        ),
    }


def write_policy_radar(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    entry_path: Path | str | None = None,
    opportunities: list[dict[str, Any]] | None = None,
    output_dir: Path | str | None = None,
    opportunity_limit: int = 300,
) -> dict[str, Any]:
    payload = build_policy_radar(
        as_of=as_of,
        project_root=project_root,
        entry_path=entry_path,
        opportunities=opportunities,
        opportunity_limit=opportunity_limit,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "policy"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"PolicyIntelligenceRadar_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "PolicyIntelligenceRadar_latest.json"
    latest_csv = target / "PolicyIntelligenceRadar_latest.csv"
    latest_markdown = target / "PolicyIntelligenceRadar_latest.md"
    latest_pdf = target / "PolicyIntelligenceRadar_latest.pdf"
    runtime_summary_json = target / f"PolicyIntelligenceRuntimeSummary_{stamp}.json"
    latest_runtime_summary_json = target / "PolicyIntelligenceRuntimeSummary_latest.json"
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
    payload["runtime_summary"] = build_policy_runtime_summary(payload)
    payload["runtime_summary"]["outputs"] = {
        "runtime_summary_json": str(runtime_summary_json),
        "latest_runtime_summary_json": str(latest_runtime_summary_json),
        "radar_json": str(json_path),
        "latest_radar_json": str(latest_json),
    }
    markdown = policy_radar_markdown(payload)
    csv_text = _csv_text(payload.get("opportunities", []))
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_policy_pdf(pdf_path, payload)
    _write_policy_pdf(latest_pdf, payload)
    atomic_write_json(runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(latest_runtime_summary_json, payload["runtime_summary"])
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    return payload


def policy_radar_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"# PFI_OS Policy Intelligence Radar {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- System: `{payload.get('system', '')}`",
        f"- Status: `{payload.get('policy_status', '')}`",
        f"- Runtime Status: `{runtime.get('status', '')}`",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        f"- Opportunities: `{payload.get('opportunity_count', 0)}`",
        f"- Actionable: `{summary.get('actionable_count', 0)}`",
        f"- Watch: `{summary.get('watch_count', 0)}`",
        f"- Missing Evidence: `{summary.get('missing_evidence_count', 0)}`",
        f"- Token Policy: {runtime.get('token_policy', '')}",
        "",
        "## Runtime Evidence Gate",
        _markdown_table(runtime.get("evidence_gate", []), ["gate", "status", "evidence"]),
        "",
        "## Action Queue",
        _markdown_table(payload.get("action_queue", []), ["priority", "status", "action", "source"]),
        "",
        "## Sector Exposure",
        _markdown_table(payload.get("sector_exposure", []), ["sector", "count", "max_impact_score"]),
        "",
        "## Opportunities",
        _markdown_table(payload.get("opportunities", [])[:80], ["published_date", "title", "source_type", "evidence_status", "review_status", "impact_score", "opportunity_status", "required_action"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _normalize_opportunity(entry: dict[str, Any]) -> dict[str, Any]:
    published_date = _clean_date(str(entry.get("published_date") or date.today().isoformat()))
    title = str(entry.get("title") or "Untitled policy opportunity").strip()
    source_name = str(entry.get("source_name") or "Unknown").strip()
    source_type = _clean_choice(str(entry.get("source_type") or "Manual"), POLICY_SOURCE_TYPES, "Manual")
    source_url = str(entry.get("source_url") or "").strip()
    evidence_path = str(entry.get("evidence_path") or "").strip()
    review_status = _clean_review_status(entry.get("review_status", "PendingReview"))
    evidence_status = _evidence_status(source_type, source_url, evidence_path)
    scores = {
        "authority_score": _score(entry.get("authority_score", 0.0)),
        "relevance_score": _score(entry.get("relevance_score", 0.0)),
        "urgency_score": _score(entry.get("urgency_score", 0.0)),
        "feasibility_score": _score(entry.get("feasibility_score", 0.0)),
    }
    impact_score = round(
        scores["authority_score"] * 0.30
        + scores["relevance_score"] * 0.30
        + scores["urgency_score"] * 0.20
        + scores["feasibility_score"] * 0.20,
        2,
    )
    opportunity_status = _opportunity_status(review_status, evidence_status, source_type, impact_score)
    created_at = str(entry.get("created_at") or datetime.now().isoformat(timespec="seconds"))
    normalized = {
        "policy_id": str(entry.get("policy_id") or _stable_id("policy", published_date, title, source_name, created_at)),
        "published_date": published_date,
        "title": title,
        "jurisdiction": str(entry.get("jurisdiction") or "Unknown").strip() or "Unknown",
        "policy_level": _clean_choice(str(entry.get("policy_level") or "Unknown"), POLICY_LEVELS, "Unknown"),
        "source_name": source_name,
        "source_type": source_type,
        "source_url": source_url,
        "evidence_path": evidence_path,
        "evidence_status": evidence_status,
        "review_status": review_status,
        "opportunity_type": _clean_choice(str(entry.get("opportunity_type") or "Other"), POLICY_OPPORTUNITY_TYPES, "Other"),
        "sectors": _join_items(entry.get("sectors", "")),
        "affected_entities": _join_items(entry.get("affected_entities", "")),
        "impact_summary": str(entry.get("impact_summary") or "").strip(),
        "required_action": str(entry.get("required_action") or "").strip(),
        **scores,
        "impact_score": impact_score,
        "opportunity_status": opportunity_status,
        "notes": str(entry.get("notes") or "").strip(),
        "created_at": created_at,
        "updated_at": str(entry.get("updated_at") or created_at),
        "next_action": _next_action(opportunity_status, evidence_status, review_status),
    }
    return normalized


def _summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    actionable = [row for row in entries if row.get("opportunity_status") == "Actionable"]
    watch = [row for row in entries if row.get("opportunity_status") == "Watch"]
    observe = [row for row in entries if row.get("opportunity_status") == "Observe"]
    missing = [row for row in entries if row.get("evidence_status") != "Pass"]
    pending = [row for row in entries if row.get("review_status") == "PendingReview"]
    return {
        "total_records": len(entries),
        "actionable_count": len(actionable),
        "watch_count": len(watch),
        "observe_count": len(observe),
        "missing_evidence_count": len(missing),
        "pending_review_count": len(pending),
        "max_impact_score": max([float(row.get("impact_score", 0.0) or 0.0) for row in entries], default=0.0),
        "policy_status": _policy_status(entries, actionable, missing, pending),
    }


def _policy_status(
    entries: list[dict[str, Any]],
    actionable: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    pending: list[dict[str, Any]],
) -> str:
    if not entries:
        return "MissingPolicyEvidence"
    if actionable:
        return "Actionable"
    if missing:
        return "NeedsEvidence"
    if pending:
        return "NeedsReview"
    return "Observe"


def _action_queue(summary: dict[str, Any], entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if int(summary.get("total_records", 0) or 0) <= 0:
        rows.append(_action("P0", "录入至少一条政策机会，并附上官方、监管或政府来源证据。", "Policy Evidence"))
    if int(summary.get("missing_evidence_count", 0) or 0) > 0:
        rows.append(_action("P0", "补齐缺失 source_url 或 evidence_path 的政策机会；缺证据前不得进入行动清单。", "Evidence Gate"))
    if int(summary.get("pending_review_count", 0) or 0) > 0:
        rows.append(_action("P1", "复核 PendingReview 政策机会，确认来源权威、影响行业、行动要求和限制条件。", "Manual Review"))
    top = [row for row in entries if row.get("opportunity_status") == "Actionable"][:3]
    for row in top:
        rows.append(_action("P1", f"复核政策机会：{row.get('title')}；下一步：{row.get('required_action') or row.get('next_action')}", "Policy Opportunity"))
    if not rows:
        rows.append(_action("P2", "继续维护政策机会台账；定期同步政府政策系统产物并复核来源权威。", "Policy Intelligence Radar"))
    return rows


def _action(priority: str, action: str, source: str) -> dict[str, str]:
    return {"priority": priority, "status": "Open", "action": action, "source": source}


def _policy_gate(gate: str, status: str, evidence: str) -> dict[str, str]:
    clean_status = status if status in {"Pass", "Review", "Blocked"} else "Review"
    return {"gate": gate, "status": clean_status, "evidence": evidence}


def _policy_runtime_status(gates: list[dict[str, str]]) -> str:
    statuses = {str(gate.get("status", "")) for gate in gates}
    if "Blocked" in statuses:
        return "Blocked"
    if "Review" in statuses:
        return "NeedsReview"
    return "Pass"


def _compact_policy_opportunity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_id": str(row.get("policy_id", "")),
        "published_date": str(row.get("published_date", "")),
        "title": str(row.get("title", ""))[:120],
        "source_type": str(row.get("source_type", "")),
        "evidence_status": str(row.get("evidence_status", "")),
        "review_status": str(row.get("review_status", "")),
        "impact_score": float(row.get("impact_score", 0.0) or 0.0),
        "opportunity_status": str(row.get("opportunity_status", "")),
        "next_action": str(row.get("next_action", ""))[:180],
    }


def _sector_exposure(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sectors: dict[str, dict[str, Any]] = {}
    for row in entries:
        for sector in _split_items(str(row.get("sectors", ""))):
            bucket = sectors.setdefault(sector, {"count": 0, "max_impact_score": 0.0})
            bucket["count"] += 1
            bucket["max_impact_score"] = max(float(bucket["max_impact_score"]), float(row.get("impact_score", 0.0) or 0.0))
    return [
        {"sector": sector, "count": values["count"], "max_impact_score": round(float(values["max_impact_score"]), 2)}
        for sector, values in sorted(sectors.items(), key=lambda item: (-item[1]["max_impact_score"], item[0]))
    ]


def _opportunity_status(review_status: str, evidence_status: str, source_type: str, impact_score: float) -> str:
    if review_status == "Rejected":
        return "Rejected"
    if review_status != "Reviewed":
        return "PendingReview"
    if evidence_status != "Pass":
        return "NeedsEvidence"
    if source_type in {"Official", "Regulator", "Government", "Exchange"} and impact_score >= 70:
        return "Actionable"
    if impact_score >= 50:
        return "Watch"
    return "Observe"


def _evidence_status(source_type: str, source_url: str, evidence_path: str) -> str:
    if not source_url.strip() and not evidence_path.strip():
        return "Missing"
    if source_type in {"Official", "Regulator", "Government", "Exchange"}:
        return "Pass"
    return "NeedsAuthorityReview"


def _next_action(opportunity_status: str, evidence_status: str, review_status: str) -> str:
    if opportunity_status == "Actionable":
        return "Add to manual opportunity review queue; verify eligibility, deadline, and constraints before any external action."
    if evidence_status == "Missing":
        return "Attach official source URL, PDF, policy page, or registry evidence."
    if evidence_status == "NeedsAuthorityReview":
        return "Trace this item back to an official, regulator, government, or exchange source before promotion."
    if review_status != "Reviewed":
        return "Review source authority, affected sectors, impact score, and required action."
    return "Keep as observed policy context; do not promote until impact or relevance increases."


def _clean_date(value: str) -> str:
    try:
        return datetime.fromisoformat(str(value)[:10]).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid date: {value}") from exc


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


def _join_items(value: str | list[str] | Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return ", ".join(_split_items(str(value or "")))


def _split_items(value: str) -> list[str]:
    normalized = value.replace("，", ",").replace(";", ",").replace("；", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _csv_text(records: list[dict[str, Any]]) -> str:
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=POLICY_COLUMNS, extrasaction="ignore")
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


def _write_policy_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary", {})
    runtime = payload.get("runtime_summary", {})
    lines = [
        f"PFI_OS Policy Intelligence Radar {payload.get('as_of', '')}",
        f"Generated At: {payload.get('generated_at', '')}",
        f"Status: {payload.get('policy_status', '')}",
        f"Runtime Status: {runtime.get('status', '')}",
        f"Opportunities: {payload.get('opportunity_count', 0)}",
        f"Actionable: {summary.get('actionable_count', 0)}",
        f"Missing Evidence: {summary.get('missing_evidence_count', 0)}",
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
    lines.extend(["", "Top Opportunities:"])
    for row in payload.get("opportunities", [])[:12]:
        lines.append(f"- {row.get('title')} | {row.get('opportunity_status')} | score={row.get('impact_score')}")
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
    return f"policy_{digest}"


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
