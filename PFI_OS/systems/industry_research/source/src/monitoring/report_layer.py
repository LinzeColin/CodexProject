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
class ReportLayerGateRow:
    gate_id: str
    gate_name: str
    status: str
    evidence_classification: str
    decision_grade: str
    priority: str
    issue: str
    next_action: str
    source_paths: str


def build_report_layer_audit(as_of: str, *, root: Path | str = ROOT) -> dict[str, Any]:
    project_root = Path(root)
    audit_dir = project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    matrix_path = audit_dir / f"evidence_decision_matrix_{as_of}.json"
    matrix = _load_json(matrix_path, {})
    rows = _gate_rows_from_matrix(matrix, matrix_path)
    status_counts = Counter(row.status for row in rows)
    evidence_counts = Counter(row.evidence_classification for row in rows)
    decision_counts = Counter(row.decision_grade for row in rows)
    priority_counts = Counter(row.priority for row in rows)
    blockers = [row for row in rows if row.priority == "P0" or row.decision_grade == "Reject" or row.status == "Blocked"]
    review_rows = [row for row in rows if row.status == "Review" or row.decision_grade in {"Watch", "Observe"}]
    audit_status = "Blocked" if blockers else "Review" if review_rows else "Pass"
    conclusion_ceiling = _conclusion_ceiling(matrix, rows)
    return {
        "schema": "AIResearchReportLayerAuditV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "run_id": _stable_id("reportLayer", as_of, str(matrix_path), str(matrix.get("generated_at", ""))),
        "generated_at": _now(),
        "audit_status": audit_status,
        "conclusion_ceiling": conclusion_ceiling,
        "quality_gate_issues": report_layer_quality_issues_from_payload(matrix),
        "row_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "inputs": {
            "evidence_decision_matrix": str(matrix_path),
            "matrix_schema": str(matrix.get("schema", "")) if isinstance(matrix, dict) else "",
            "matrix_audit_status": str(matrix.get("audit_status", "")) if isinstance(matrix, dict) else "",
            "matrix_row_count": int(matrix.get("row_count", 0) or 0) if isinstance(matrix, dict) else 0,
        },
        "assumptions": [
            "This audit is read-only and only composes existing local system audit artifacts.",
            "It does not refresh OpenD, moomoo, Alipay, policy bridge, PFIOS, ResearchBus, or historical reports.",
            "Reject/P0 rows block executable trading support and cap formal reports at research-only status.",
            "Watch/OBSERVATION rows may remain in reports only as clearly labeled evidence gaps or observations.",
        ],
        "required_report_language": {
            "blocked": "当前报告仅可作为研究复盘和证据缺口清单，不能作为交易执行依据。",
            "review": "当前结论需要更多证据或人工复核后才能提高置信等级。",
            "pass": "当前审计层未发现系统级阻断；仍需单份报告质量门禁通过。",
        },
        "rows": [asdict(row) for row in rows],
    }


def write_report_layer_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    audit = build_report_layer_audit(as_of, root=project_root)
    target_dir = Path(output_dir) if output_dir else project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"report_layer_audit_{as_of}"
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


def report_layer_quality_issues(as_of: str, *, root: Path | str = ROOT) -> list[str]:
    project_root = Path(root)
    audit_dir = project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    report_layer_path = audit_dir / f"report_layer_audit_{as_of}.json"
    report_layer = _load_json(report_layer_path, {})
    if isinstance(report_layer, dict) and report_layer.get("schema") == "AIResearchReportLayerAuditV1":
        issues = report_layer.get("quality_gate_issues")
        return [str(item) for item in issues if str(item).strip()] if isinstance(issues, list) else []
    matrix_path = audit_dir / f"evidence_decision_matrix_{as_of}.json"
    matrix = _load_json(matrix_path, {})
    if isinstance(matrix, dict) and matrix.get("schema") == "AIResearchEvidenceDecisionMatrixV1":
        return report_layer_quality_issues_from_payload(matrix)
    return []


def report_layer_quality_issues_from_payload(payload: dict[str, Any]) -> list[str]:
    if not isinstance(payload, dict) or payload.get("schema") != "AIResearchEvidenceDecisionMatrixV1":
        return ["Report Layer gate blocked: evidence decision matrix is missing or unreadable."]
    issues: list[str] = []
    blocker_count = int(payload.get("blocker_count", 0) or 0)
    watch_count = int(payload.get("watch_count", 0) or 0)
    decision_counts = payload.get("decision_counts") if isinstance(payload.get("decision_counts"), dict) else {}
    evidence_counts = payload.get("evidence_counts") if isinstance(payload.get("evidence_counts"), dict) else {}
    priority_counts = payload.get("priority_counts") if isinstance(payload.get("priority_counts"), dict) else {}
    reject_count = int(decision_counts.get("Reject", 0) or 0)
    p0_count = int(priority_counts.get("P0", 0) or 0)
    observation_count = int(evidence_counts.get("OBSERVATION", 0) or 0)
    opinion_count = int(evidence_counts.get("OPINION", 0) or 0)
    if blocker_count or reject_count or p0_count:
        issues.append(
            "Report Layer gate blocked: "
            f"P0={p0_count}, Reject={reject_count}, blocker_count={blocker_count}. "
            "Formal report conclusions must be downgraded to research-only until blockers are resolved."
        )
    if watch_count or observation_count or opinion_count:
        issues.append(
            "Report Layer gate review: "
            f"Watch/weak rows={watch_count}, OBSERVATION={observation_count}, OPINION={opinion_count}. "
            "Weak evidence must be labeled as observation or evidence gap, not executable support."
        )
    return issues


def _gate_rows_from_matrix(matrix: dict[str, Any], matrix_path: Path) -> list[ReportLayerGateRow]:
    if not isinstance(matrix, dict) or matrix.get("schema") != "AIResearchEvidenceDecisionMatrixV1":
        return [
            _row(
                "Evidence Decision Matrix",
                "Blocked",
                "FACT",
                "Reject",
                "P0",
                "Evidence Decision Matrix is missing or unreadable.",
                "先运行 evidence-decision-audit，再运行 report-layer-audit。",
                [matrix_path],
            )
        ]
    issues = report_layer_quality_issues_from_payload(matrix)
    rows = [
        _row(
            "Evidence Decision Matrix",
            "Pass" if matrix.get("audit_status") == "Pass" else "Blocked" if matrix.get("audit_status") == "Blocked" else "Review",
            "FACT",
            "Reject" if matrix.get("audit_status") == "Blocked" else "Watch" if matrix.get("audit_status") == "Review" else "Actionable",
            "P0" if matrix.get("audit_status") == "Blocked" else "P1" if matrix.get("audit_status") == "Review" else "P2",
            f"Evidence matrix status is {matrix.get('audit_status')} with {matrix.get('row_count', 0)} rows.",
            "先处理 P0/Reject，再把 Watch/OBSERVATION 明确写成证据缺口。",
            [matrix_path],
        )
    ]
    for issue in issues:
        priority = "P0" if "blocked" in issue.lower() else "P1"
        rows.append(
            _row(
                "Report Conclusion Ceiling",
                "Blocked" if priority == "P0" else "Review",
                "FACT",
                "Reject" if priority == "P0" else "Watch",
                priority,
                issue,
                "质量门禁必须保留该降级原因；生成正式报告前不得提升为可执行交易支持。",
                [matrix_path],
            )
        )
    user_count = int(matrix.get("user_confirmation_required_count", 0) or 0)
    if user_count:
        rows.append(
            _row(
                "User Confirmation Required",
                "Review",
                "FACT",
                "Watch",
                "P1",
                f"{user_count} rows require user confirmation.",
                "把账户、持仓、视频/OCR 或待确认订单相关结论降级为人工复核项。",
                [matrix_path],
            )
        )
    return rows


def _conclusion_ceiling(matrix: dict[str, Any], rows: list[ReportLayerGateRow]) -> str:
    if not isinstance(matrix, dict) or matrix.get("schema") != "AIResearchEvidenceDecisionMatrixV1":
        return "NoFormalResearchUse"
    if any(row.priority == "P0" or row.decision_grade == "Reject" for row in rows):
        return "ResearchOnlyBlocked"
    if any(row.status == "Review" or row.decision_grade == "Watch" for row in rows):
        return "ObservationOnly"
    return "EvidenceChainReady"


def _row(
    gate_name: str,
    status: str,
    evidence: str,
    decision: str,
    priority: str,
    issue: str,
    next_action: str,
    source_paths: list[Any],
) -> ReportLayerGateRow:
    clean_paths = "; ".join(dict.fromkeys(str(path) for path in source_paths if str(path).strip()))
    return ReportLayerGateRow(
        gate_id=_stable_id("reportLayerGate", gate_name, status, issue, clean_paths),
        gate_name=gate_name,
        status=status,
        evidence_classification=evidence,
        decision_grade=decision,
        priority=priority,
        issue=issue,
        next_action=next_action,
        source_paths=clean_paths,
    )


def _audit_markdown(audit: dict[str, Any]) -> str:
    rows = list(audit["rows"])
    non_pass = [row for row in rows if row["status"] != "Pass"]
    lines = [
        f"# AI-Research-System Report Layer Audit {audit['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {audit['system']}",
        f"- Run ID: {audit['run_id']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Conclusion Ceiling: {audit['conclusion_ceiling']}",
        "",
        "## Inputs",
        _markdown_table([audit["inputs"]], ["evidence_decision_matrix", "matrix_schema", "matrix_audit_status", "matrix_row_count"]),
        "",
        "## Quality Gate Issues",
        "\n".join(f"- {issue}" for issue in audit["quality_gate_issues"]) if audit["quality_gate_issues"] else "暂无",
        "",
        "## Non-Pass Gates",
        _markdown_table(non_pass, ["priority", "gate_name", "status", "decision_grade", "issue", "next_action"]),
        "",
        "## All Gates",
        _markdown_table(rows, ["priority", "gate_name", "status", "evidence_classification", "decision_grade", "issue"]),
        "",
        "## Required Report Language",
        _markdown_table(
            [{"status": key, "language": value} for key, value in audit["required_report_language"].items()],
            ["status", "language"],
        ),
        "",
        "## Assumptions",
        *[f"- {item}" for item in audit["assumptions"]],
    ]
    return "\n".join(lines)


def _write_rows_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


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


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"reportLayer_{digest}"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
