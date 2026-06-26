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


VALID_EVIDENCE_CLASSES = {"FACT", "INFERENCE", "OPINION", "OBSERVATION"}
VALID_DECISION_GRADES = {"Actionable", "Watch", "Observe", "Reject"}


@dataclass(frozen=True)
class EvidenceDecisionRow:
    matrix_id: str
    source_layer: str
    source_domain: str
    item_name: str
    item_status: str
    entity_id: str
    evidence_classification: str
    decision_grade: str
    data_quality_status: str
    priority: str
    user_confirmation_required: bool
    blocker_scope: str
    issue: str
    next_action: str
    source_paths: str
    source_record_id: str


def build_evidence_decision_matrix(
    as_of: str,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    project_root = Path(root)
    audit_dir = project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    rows: list[EvidenceDecisionRow] = []
    rows.extend(_rows_from_data_trust(audit_dir / f"data_trust_audit_{as_of}.json"))
    rows.extend(_rows_from_reconciliation(audit_dir / f"reconciliation_audit_{as_of}.json"))
    rows.extend(_rows_from_manual_review(audit_dir / f"manual_review_queue_{as_of}.json"))
    rows.extend(_rows_from_entity_registry(audit_dir / f"entity_registry_{as_of}.json"))

    for source_layer, file_name in [
        ("DataTrust", f"data_trust_audit_{as_of}.json"),
        ("Reconciliation", f"reconciliation_audit_{as_of}.json"),
        ("ManualReview", f"manual_review_queue_{as_of}.json"),
        ("EntityRegistry", f"entity_registry_{as_of}.json"),
    ]:
        path = audit_dir / file_name
        if not path.exists():
            rows.append(
                _row(
                    source_layer=source_layer,
                    source_domain="system_audit",
                    item_name=file_name,
                    item_status="missing",
                    evidence="FACT",
                    decision="Reject",
                    data_quality_status="missing",
                    priority="P0",
                    issue=f"{source_layer} audit artifact is missing.",
                    next_action=f"先生成 {file_name} 后再重跑 evidence-decision-audit。",
                    source_paths=[path],
                )
            )

    normalized_rows = sorted(_dedupe_rows(rows), key=lambda row: (_priority_rank(row.priority), row.source_layer, row.source_domain, row.item_name))
    validation_issues = _classification_issues(normalized_rows)
    evidence_counts = Counter(row.evidence_classification for row in normalized_rows)
    decision_counts = Counter(row.decision_grade for row in normalized_rows)
    priority_counts = Counter(row.priority for row in normalized_rows)
    layer_counts = Counter(row.source_layer for row in normalized_rows)
    blocker_rows = [row for row in normalized_rows if row.priority == "P0" or row.decision_grade == "Reject"]
    watch_rows = [row for row in normalized_rows if row.decision_grade == "Watch" or row.evidence_classification in {"OBSERVATION", "OPINION"}]
    audit_status = "Blocked" if blocker_rows or validation_issues else "Review" if watch_rows else "Pass"
    return {
        "schema": "AIResearchEvidenceDecisionMatrixV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": _now(),
        "audit_status": audit_status,
        "row_count": len(normalized_rows),
        "source_layer_counts": dict(sorted(layer_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "blocker_count": len(blocker_rows),
        "watch_count": len(watch_rows),
        "user_confirmation_required_count": sum(1 for row in normalized_rows if row.user_confirmation_required),
        "validation_issues": validation_issues,
        "assumptions": [
            "This matrix is read-only and composes existing local audit artifacts; it does not refresh OpenD, moomoo, Alipay, policy bridge, PFIOS, or ResearchBus.",
            "Actionable means the source row is structurally usable inside the research evidence chain; it is not trading approval.",
            "Reject or P0 rows fail closed and block executable trading support until resolved or explicitly downgraded with stronger evidence.",
            "Watch and OBSERVATION rows can support research context only; they require stronger source evidence before becoming decision support.",
        ],
        "rows": [asdict(row) for row in normalized_rows],
    }


def write_evidence_decision_matrix(
    as_of: str,
    *,
    root: Path | str = ROOT,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    audit = build_evidence_decision_matrix(as_of, root=project_root)
    target_dir = Path(output_dir) if output_dir else project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"evidence_decision_matrix_{as_of}"
    json_path = target_dir / f"{stem}.json"
    csv_path = target_dir / f"{stem}.csv"
    markdown_path = target_dir / f"{stem}.md"
    pdf_path = target_dir / f"{stem}.pdf"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_rows_csv(csv_path, audit["rows"])
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


def _rows_from_data_trust(path: Path) -> list[EvidenceDecisionRow]:
    payload = _load_json(path, {})
    records = payload.get("records") if isinstance(payload, dict) else []
    rows = []
    for record in records if isinstance(records, list) else []:
        status = str(record.get("data_trust_status", ""))
        decision = _clean_decision(record.get("decision_grade"))
        priority = "P0" if status == "REJECTED" or decision == "Reject" else "P1" if status == "NEEDS_REVIEW" or decision == "Watch" else "P2"
        text = " ".join(str(record.get(key, "")) for key in ["source_type", "source_name", "source_path", "issues", "next_action"])
        rows.append(
            _row(
                source_layer="DataTrust",
                source_domain=str(record.get("source_type", "")),
                item_name=str(record.get("source_name", "")),
                item_status=status,
                evidence=_clean_evidence(record.get("evidence_classification")),
                decision=decision,
                data_quality_status=status,
                priority=priority,
                issue=str(record.get("issues", "")),
                next_action=str(record.get("next_action", "")),
                source_paths=[record.get("source_path", ""), path],
                source_record_id=str(record.get("record_id", "")),
                user_confirmation_required=_requires_user_confirmation(text),
            )
        )
    return rows


def _rows_from_reconciliation(path: Path) -> list[EvidenceDecisionRow]:
    payload = _load_json(path, {})
    checks = payload.get("checks") if isinstance(payload, dict) else []
    rows = []
    for check in checks if isinstance(checks, list) else []:
        status = str(check.get("status", ""))
        severity = str(check.get("severity", "P2"))
        decision = _clean_decision(check.get("decision_grade"))
        priority = "P0" if status == "fail" and severity == "P0" else "P1" if severity in {"P0", "P1"} or status == "fail" else "P2"
        rows.append(
            _row(
                source_layer="Reconciliation",
                source_domain=str(check.get("domain", "")),
                item_name=str(check.get("check_name", "")),
                item_status=status,
                evidence=_clean_evidence(check.get("evidence_classification")),
                decision=decision,
                data_quality_status=status,
                priority=priority,
                issue=str(check.get("issue", "")),
                next_action=str(check.get("next_action", "")),
                source_paths=[*_split_paths(check.get("source_paths")), path],
                source_record_id=str(check.get("check_id", "")),
            )
        )
    return rows


def _rows_from_manual_review(path: Path) -> list[EvidenceDecisionRow]:
    payload = _load_json(path, {})
    items = payload.get("items") if isinstance(payload, dict) else []
    rows = []
    for item in items if isinstance(items, list) else []:
        rows.append(
            _row(
                source_layer="ManualReview",
                source_domain=str(item.get("source_domain", "")),
                item_name=str(item.get("item_name", "")),
                item_status=f"{item.get('queue_status', '')}:{item.get('item_status', '')}".strip(":"),
                evidence=_clean_evidence(item.get("evidence_classification")),
                decision=_clean_decision(item.get("decision_grade")),
                data_quality_status=str(item.get("item_status", "")),
                priority=str(item.get("priority", "P2")),
                issue=str(item.get("issue", "")),
                next_action=str(item.get("next_action", "")),
                source_paths=[*_split_paths(item.get("source_paths")), path],
                source_record_id=str(item.get("review_id", "")),
                user_confirmation_required=bool(item.get("user_confirmation_required", False)),
                blocker_scope=str(item.get("blocker_scope", "")),
            )
        )
    return rows


def _rows_from_entity_registry(path: Path) -> list[EvidenceDecisionRow]:
    payload = _load_json(path, {})
    entities = payload.get("entities") if isinstance(payload, dict) else []
    conflicts = payload.get("conflicts") if isinstance(payload, dict) else []
    rows = []
    for entity in entities if isinstance(entities, list) else []:
        issue = str(entity.get("issues", ""))
        decision = _clean_decision(entity.get("decision_grade"))
        priority = "P1" if issue or decision in {"Watch", "Reject"} else "P2"
        rows.append(
            _row(
                source_layer="EntityRegistry",
                source_domain=str(entity.get("entity_type", "")),
                item_name=str(entity.get("canonical_name", "")),
                item_status="Registered" if not issue else "Review",
                entity_id=str(entity.get("entity_id", "")),
                evidence=_clean_evidence(entity.get("evidence_classification")),
                decision=decision,
                data_quality_status="AliasConflict" if "conflict" in issue.lower() else "Registered",
                priority=priority,
                issue=issue,
                next_action="保留实体映射；若存在别名冲突则进入 Alias Map hardening。",
                source_paths=[*_split_paths(entity.get("source_paths")), path],
                source_record_id=str(entity.get("entity_id", "")),
            )
        )
    for conflict in conflicts if isinstance(conflicts, list) else []:
        rows.append(
            _row(
                source_layer="AliasMap",
                source_domain="alias_conflict",
                item_name=str(conflict.get("alias") or conflict.get("normalized_alias") or "alias_conflict"),
                item_status="Conflict",
                entity_id=str(conflict.get("entity_id", "")),
                evidence="FACT",
                decision="Watch",
                data_quality_status="AliasConflict",
                priority="P1",
                issue=f"Alias conflict: {conflict.get('normalized_alias', '')}",
                next_action="明确该别名应合并、拆分还是保留多市场口径后重跑 Entity Registry。",
                source_paths=[conflict.get("source_path", ""), path],
                source_record_id=str(conflict.get("alias_id", "")),
            )
        )
    return rows


def _row(
    *,
    source_layer: str,
    source_domain: str,
    item_name: str,
    item_status: str,
    evidence: str,
    decision: str,
    data_quality_status: str,
    priority: str,
    issue: str,
    next_action: str,
    source_paths: list[Any],
    source_record_id: str = "",
    entity_id: str = "",
    user_confirmation_required: bool | None = None,
    blocker_scope: str = "",
) -> EvidenceDecisionRow:
    clean_paths = "; ".join(dict.fromkeys(str(path) for path in source_paths if str(path).strip()))
    evidence_value = _clean_evidence(evidence)
    decision_value = _clean_decision(decision)
    confirmation_required = _requires_user_confirmation(" ".join([source_layer, source_domain, item_name, clean_paths, issue, next_action])) if user_confirmation_required is None else bool(user_confirmation_required)
    return EvidenceDecisionRow(
        matrix_id=_stable_id("evidenceDecision", source_layer, source_domain, item_name, clean_paths, source_record_id),
        source_layer=source_layer,
        source_domain=source_domain,
        item_name=item_name,
        item_status=item_status,
        entity_id=entity_id,
        evidence_classification=evidence_value,
        decision_grade=decision_value,
        data_quality_status=data_quality_status,
        priority=priority if priority in {"P0", "P1", "P2"} else "P2",
        user_confirmation_required=confirmation_required,
        blocker_scope=blocker_scope or _blocker_scope(priority, decision_value, source_layer, source_domain, item_name, issue),
        issue=issue,
        next_action=next_action,
        source_paths=clean_paths,
        source_record_id=source_record_id,
    )


def _dedupe_rows(rows: list[EvidenceDecisionRow]) -> list[EvidenceDecisionRow]:
    deduped: dict[str, EvidenceDecisionRow] = {}
    for row in rows:
        existing = deduped.get(row.matrix_id)
        if existing is None or _priority_rank(row.priority) < _priority_rank(existing.priority):
            deduped[row.matrix_id] = row
    return list(deduped.values())


def _classification_issues(rows: list[EvidenceDecisionRow]) -> list[str]:
    issues = []
    invalid_evidence = sorted({row.evidence_classification for row in rows if row.evidence_classification not in VALID_EVIDENCE_CLASSES})
    invalid_decision = sorted({row.decision_grade for row in rows if row.decision_grade not in VALID_DECISION_GRADES})
    if invalid_evidence:
        issues.append("Invalid evidence classification values: " + ", ".join(invalid_evidence))
    if invalid_decision:
        issues.append("Invalid decision grade values: " + ", ".join(invalid_decision))
    return issues


def _clean_evidence(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in VALID_EVIDENCE_CLASSES else "OBSERVATION"


def _clean_decision(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in VALID_DECISION_GRADES else "Observe"


def _requires_user_confirmation(text: str) -> bool:
    lowered = str(text or "").lower()
    keywords = ["alipay", "支付宝", "current_positions", "pending_orders", "video", "持仓", "待确认", "账户", "screenrecording"]
    return any(keyword in lowered for keyword in keywords)


def _blocker_scope(priority: str, decision: str, layer: str, domain: str, item_name: str, issue: str) -> str:
    text = " ".join([layer, domain, item_name, issue]).lower()
    if priority == "P0" or decision == "Reject":
        return "Blocks executable trading support; reports remain research-only until resolved."
    if "alias" in text or "entity" in text:
        return "Entity mapping requires review before cross-system aggregation."
    if "source_log" in text or "pdf" in text or "markdown" in text:
        return "Formal report evidence chain is incomplete until companion files are fixed."
    if "pfi_os" in text:
        return "PFIOS validation evidence must remain observation or further validation."
    if _requires_user_confirmation(text):
        return "Account or holding evidence requires user confirmation before use."
    return "Research observation only unless stronger evidence is available."


def _priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2}.get(priority, 9)


def _split_paths(value: Any) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_rows_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _audit_markdown(audit: dict[str, Any]) -> str:
    rows = list(audit["rows"])
    blockers = [row for row in rows if row["priority"] == "P0" or row["decision_grade"] == "Reject"]
    review_rows = [row for row in rows if row["priority"] == "P1"][:80]
    user_rows = [row for row in rows if row["user_confirmation_required"]][:60]
    lines = [
        f"# AI-Research-System Evidence Decision Matrix {audit['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {audit['system']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Rows: {audit['row_count']}",
        f"- Blockers: {audit['blocker_count']}",
        f"- Watch Rows: {audit['watch_count']}",
        f"- User Confirmation Required: {audit['user_confirmation_required_count']}",
        "",
        "## Source Layer Summary",
        _markdown_table([{"source_layer": key, "count": value} for key, value in audit["source_layer_counts"].items()], ["source_layer", "count"]),
        "",
        "## Evidence Summary",
        _markdown_table([{"evidence_classification": key, "count": value} for key, value in audit["evidence_counts"].items()], ["evidence_classification", "count"]),
        "",
        "## Decision Summary",
        _markdown_table([{"decision_grade": key, "count": value} for key, value in audit["decision_counts"].items()], ["decision_grade", "count"]),
        "",
        "## P0 / Reject Blockers",
        _markdown_table(blockers, ["priority", "source_layer", "source_domain", "item_name", "decision_grade", "issue", "next_action"]),
        "",
        "## User Confirmation Required",
        _markdown_table(user_rows, ["priority", "source_layer", "source_domain", "item_name", "decision_grade", "issue", "next_action"]),
        "",
        "## P1 Review Sample",
        _markdown_table(review_rows, ["priority", "source_layer", "source_domain", "item_name", "evidence_classification", "decision_grade", "issue"]),
        "",
        "## Validation Issues",
        "\n".join(f"- {item}" for item in audit["validation_issues"]) if audit["validation_issues"] else "暂无",
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


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"evidenceDecision_{digest}"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
