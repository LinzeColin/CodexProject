from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import ROOT
from src.monitoring.data_trust import SYSTEM_AUDIT_DIRNAME, _write_pdf


@dataclass(frozen=True)
class ManualReviewItem:
    review_id: str
    queue_status: str
    priority: str
    source_layer: str
    source_domain: str
    item_name: str
    item_status: str
    evidence_classification: str
    decision_grade: str
    user_confirmation_required: bool
    blocker_scope: str
    issue: str
    next_action: str
    owner: str
    source_paths: str
    dedupe_key: str


def build_manual_review_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    project_root = Path(root)
    audit_dir = project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    data_trust_path = audit_dir / f"data_trust_audit_{as_of}.json"
    reconciliation_path = audit_dir / f"reconciliation_audit_{as_of}.json"
    data_trust = _load_json(data_trust_path, {})
    reconciliation = _load_json(reconciliation_path, {})

    items = []
    items.extend(_items_from_data_trust(data_trust, data_trust_path))
    items.extend(_items_from_reconciliation(reconciliation, reconciliation_path))
    if not data_trust_path.exists():
        items.append(
            _item(
                source_layer="DataTrust",
                source_domain="data_trust",
                item_name="data_trust_audit_missing",
                item_status="missing",
                priority="P0",
                evidence="FACT",
                decision="Reject",
                issue="Data Trust audit is missing.",
                next_action="先运行 `python3 -m src.cli data-trust-audit --date YYYY-MM-DD`。",
                source_paths=[data_trust_path],
            )
        )
    if not reconciliation_path.exists():
        items.append(
            _item(
                source_layer="Reconciliation",
                source_domain="reconciliation",
                item_name="reconciliation_audit_missing",
                item_status="missing",
                priority="P0",
                evidence="FACT",
                decision="Reject",
                issue="Reconciliation audit is missing.",
                next_action="先运行 `python3 -m src.cli reconciliation-audit --date YYYY-MM-DD`。",
                source_paths=[reconciliation_path],
            )
        )

    items = sorted(_dedupe_items(items), key=lambda row: (_priority_rank(row.priority), row.source_layer, row.source_domain, row.item_name))
    priority_counts = Counter(item.priority for item in items)
    owner_counts = Counter(item.owner for item in items)
    decision_counts = Counter(item.decision_grade for item in items)
    open_blockers = [item for item in items if item.priority == "P0" or item.decision_grade == "Reject"]
    audit_status = "Blocked" if open_blockers else "Review" if items else "Pass"
    return {
        "schema": "AIResearchManualReviewQueueV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": _now(),
        "audit_status": audit_status,
        "item_count": len(items),
        "priority_counts": dict(sorted(priority_counts.items())),
        "owner_counts": dict(sorted(owner_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "assumptions": [
            "This queue is generated from Data Trust and Reconciliation audits only; it does not refresh external data.",
            "P0 items block executable trading support until resolved or explicitly downgraded with evidence.",
            "User-confirmation items require the user to confirm account, holding, or video-derived evidence before use.",
        ],
        "items": [asdict(item) for item in items],
    }


def write_manual_review_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    audit = build_manual_review_audit(as_of, root=project_root)
    target_dir = Path(output_dir) if output_dir else project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"manual_review_queue_{as_of}"
    json_path = target_dir / f"{stem}.json"
    csv_path = target_dir / f"{stem}.csv"
    markdown_path = target_dir / f"{stem}.md"
    pdf_path = target_dir / f"{stem}.pdf"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_items_csv(csv_path, audit["items"])
    markdown = _audit_markdown(audit)
    markdown_path.write_text(markdown, encoding="utf-8")
    _write_pdf(pdf_path, markdown)
    audit["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
    }
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def _items_from_data_trust(data_trust: Any, data_trust_path: Path) -> list[ManualReviewItem]:
    if not isinstance(data_trust, dict):
        return []
    records = data_trust.get("records") if isinstance(data_trust.get("records"), list) else []
    items: list[ManualReviewItem] = []
    for row in records:
        status = str(row.get("data_trust_status", ""))
        decision = str(row.get("decision_grade", ""))
        if status not in {"NEEDS_REVIEW", "REJECTED"} and decision not in {"Watch", "Reject"}:
            continue
        priority = "P0" if status == "REJECTED" or decision == "Reject" else "P1"
        issue = str(row.get("issues") or _data_trust_issue(status))
        next_action = str(row.get("next_action") or "人工复核后再进入报告证据链。")
        path = Path(str(row.get("source_path", "")))
        items.append(
            _item(
                source_layer="DataTrust",
                source_domain=str(row.get("source_type", "")),
                item_name=str(row.get("source_name", "")),
                item_status=status,
                priority=priority,
                evidence=str(row.get("evidence_classification", "OBSERVATION")),
                decision=decision or ("Reject" if priority == "P0" else "Watch"),
                issue=issue,
                next_action=next_action,
                source_paths=[path, data_trust_path],
            )
        )
    return items


def _items_from_reconciliation(reconciliation: Any, reconciliation_path: Path) -> list[ManualReviewItem]:
    if not isinstance(reconciliation, dict):
        return []
    checks = reconciliation.get("checks") if isinstance(reconciliation.get("checks"), list) else []
    items: list[ManualReviewItem] = []
    for row in checks:
        status = str(row.get("status", ""))
        if status not in {"fail", "warn"}:
            continue
        severity = str(row.get("severity", "P2"))
        priority = "P0" if status == "fail" and severity == "P0" else "P1" if severity in {"P0", "P1"} else "P2"
        paths = [Path(part.strip()) for part in str(row.get("source_paths", "")).split(";") if part.strip()]
        paths.append(reconciliation_path)
        items.append(
            _item(
                source_layer="Reconciliation",
                source_domain=str(row.get("domain", "")),
                item_name=str(row.get("check_name", "")),
                item_status=status,
                priority=priority,
                evidence=str(row.get("evidence_classification", "OBSERVATION")),
                decision=str(row.get("decision_grade") or ("Reject" if status == "fail" else "Watch")),
                issue=str(row.get("issue") or "Reconciliation check needs review."),
                next_action=str(row.get("next_action") or "处理对账问题后重跑审计。"),
                source_paths=paths,
            )
        )
    return items


def _item(
    *,
    source_layer: str,
    source_domain: str,
    item_name: str,
    item_status: str,
    priority: str,
    evidence: str,
    decision: str,
    issue: str,
    next_action: str,
    source_paths: list[Path],
) -> ManualReviewItem:
    clean_paths = [str(path) for path in source_paths if str(path)]
    text = " ".join([source_layer, source_domain, item_name, item_status, issue, next_action, " ".join(clean_paths)]).lower()
    requires_user = _requires_user_confirmation(text)
    owner = "User" if requires_user else "System"
    blocker_scope = _blocker_scope(priority, decision, source_domain, item_name, text)
    dedupe_key = _dedupe_key(source_layer, source_domain, item_name, clean_paths)
    return ManualReviewItem(
        review_id=_stable_id("manualReview", dedupe_key, priority, item_status),
        queue_status="Open",
        priority=priority,
        source_layer=source_layer,
        source_domain=source_domain,
        item_name=item_name,
        item_status=item_status,
        evidence_classification=evidence,
        decision_grade=decision,
        user_confirmation_required=requires_user,
        blocker_scope=blocker_scope,
        issue=issue,
        next_action=next_action,
        owner=owner,
        source_paths="; ".join(dict.fromkeys(clean_paths)),
        dedupe_key=dedupe_key,
    )


def _dedupe_items(items: list[ManualReviewItem]) -> list[ManualReviewItem]:
    best: dict[str, ManualReviewItem] = {}
    for item in items:
        existing = best.get(item.dedupe_key)
        if existing is None or _priority_rank(item.priority) < _priority_rank(existing.priority):
            best[item.dedupe_key] = item
    return list(best.values())


def _data_trust_issue(status: str) -> str:
    if status == "REJECTED":
        return "Evidence is rejected and blocks executable use."
    if status == "NEEDS_REVIEW":
        return "Evidence needs manual review before use."
    return "Evidence requires review."


def _requires_user_confirmation(text: str) -> bool:
    keywords = [
        "alipay",
        "支付宝",
        "current_positions",
        "pending_orders",
        "video",
        "持仓",
        "待确认",
        "账户",
        "screenrecording",
    ]
    return any(keyword in text for keyword in keywords)


def _blocker_scope(priority: str, decision: str, domain: str, item_name: str, text: str) -> str:
    if priority == "P0" or decision == "Reject":
        return "Blocks executable trading support; reports may be read only as research context."
    if "pfi_os" in text:
        return "PFIOS evidence must be downgraded to observation or further validation."
    if "policy" in text:
        return "Policy catalyst evidence must remain background until original-source chain is verified."
    if "source_log" in text or "pdf" in text or "markdown" in text:
        return "Formal report evidence chain is incomplete until companion files are fixed."
    if "automation" in text:
        return "Automation health warning must be disclosed before using report outputs."
    if _requires_user_confirmation(text):
        return "Account or holding evidence requires user confirmation before use."
    return "Observation only until reviewed."


def _priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2}.get(priority, 9)


def _dedupe_key(source_layer: str, source_domain: str, item_name: str, paths: list[str]) -> str:
    material = "|".join([source_layer, source_domain, item_name, *paths])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"manualReview_{digest}"


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_items_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _audit_markdown(audit: dict[str, Any]) -> str:
    items = list(audit["items"])
    p0 = [row for row in items if row["priority"] == "P0"]
    p1 = [row for row in items if row["priority"] == "P1"]
    user_items = [row for row in items if row["user_confirmation_required"]]
    lines = [
        f"# AI-Research-System Manual Review Queue {audit['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {audit['system']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Items: {audit['item_count']}",
        "",
        "## Priority Summary",
        _markdown_table([{"priority": key, "count": value} for key, value in audit["priority_counts"].items()], ["priority", "count"]),
        "",
        "## Owner Summary",
        _markdown_table([{"owner": key, "count": value} for key, value in audit["owner_counts"].items()], ["owner", "count"]),
        "",
        "## P0 Blockers",
        _markdown_table(p0, ["priority", "source_layer", "source_domain", "item_name", "issue", "blocker_scope", "next_action"]),
        "",
        "## User Confirmation Required",
        _markdown_table(user_items, ["priority", "source_layer", "item_name", "issue", "next_action", "source_paths"]),
        "",
        "## P1 Review Queue",
        _markdown_table(p1, ["priority", "source_layer", "source_domain", "item_name", "issue", "next_action"]),
        "",
        "## All Open Items",
        _markdown_table(items, ["priority", "owner", "source_layer", "source_domain", "item_name", "item_status", "decision_grade"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in audit["assumptions"]],
    ]
    return "\n".join(lines)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "暂无数据"
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_clean_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, divider, *body])


def _clean_cell(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("|", "/").strip()
    return text[:220] + "..." if len(text) > 220 else text


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
