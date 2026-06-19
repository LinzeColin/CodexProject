from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.data import provider_status_rows
from pfi_os.reports.catalog import artifact_counts, latest_report_artifact, report_artifacts_frame
from pfi_os.storage import atomic_write_json, atomic_write_text
from pfi_os.system.data_trust import build_data_trust_audit
from pfi_os.system.health import HealthCheck, collect_health_checks
from pfi_os.system.integration_audit import build_pfi_os_integration_audit


def build_daily_readiness(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    data_trust_payload: dict[str, Any] | None = None,
    integration_payload: dict[str, Any] | None = None,
    health_checks: list[HealthCheck] | list[dict[str, Any]] | None = None,
    provider_rows: list[dict[str, Any]] | None = None,
    report_counts: dict[str, int] | None = None,
    latest_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    data_trust = data_trust_payload or build_data_trust_audit(as_of=audit_date, project_root=root, report_root=reports)
    integration = integration_payload or build_pfi_os_integration_audit(
        as_of=audit_date,
        project_root=root,
        report_root=reports,
    )
    checks = [_health_row(item) for item in (health_checks if health_checks is not None else collect_health_checks(root, reports))]
    providers = provider_rows if provider_rows is not None else provider_status_rows()
    counts = report_counts if report_counts is not None else artifact_counts()
    latest = latest_report
    if latest is None:
        artifacts = report_artifacts_frame()
        latest = latest_report_artifact(artifacts) or {}

    gate_rows = _gate_rows(data_trust, integration, counts, latest)
    health_summary = _count_statuses(checks)
    provider_summary = _provider_summary(providers)
    action_items = _action_items(gate_rows, provider_summary, checks, latest)
    readiness_status = _readiness_status(gate_rows)
    return {
        "schema": "PFIOSDailyReadinessV1",
        "system": "PFIOS",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "readiness_status": readiness_status,
        "project_root": str(root),
        "report_root": str(reports),
        "core_gates": gate_rows,
        "health_summary": health_summary,
        "provider_summary": provider_summary,
        "provider_rows": providers,
        "report_counts": counts,
        "latest_report": latest,
        "action_items": action_items,
        "assumptions": [
            "This readiness check is read-only.",
            "It does not refresh market data, start Moomoo OpenD, open Streamlit, mutate holdings, or place orders.",
            "Provider API keys and OpenD are real-data readiness notes, not proof that a specific research conclusion is valid.",
            "InsufficientData validation records must not be treated as successful out-of-sample evidence.",
        ],
    }


def write_daily_readiness(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    payload = build_daily_readiness(as_of=as_of, project_root=project_root, report_root=report_root)
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "systemAudit"
    target.mkdir(parents=True, exist_ok=True)
    stem = f"PFIOSDailyReadiness_{_date_stamp(str(payload['as_of']))}"
    json_path = target / f"{stem}.json"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    payload["outputs"] = {"json": str(json_path), "markdown": str(markdown_path), "pdf": str(pdf_path)}
    atomic_write_text(markdown_path, daily_readiness_markdown(payload))
    _write_daily_readiness_pdf(pdf_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def daily_readiness_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# PFIOS Daily Readiness {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- Readiness Status: `{payload.get('readiness_status', '')}`",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        f"- Project Root: `{payload.get('project_root', '')}`",
        f"- Report Root: `{payload.get('report_root', '')}`",
        "",
        "## Core Gates",
        _markdown_table(payload.get("core_gates", []), ["gate", "status", "evidence", "next_action"]),
        "",
        "## Provider Summary",
        _markdown_table([payload.get("provider_summary", {})], ["ready", "needs_config", "needs_package", "needs_opend", "other"]),
        "",
        "## Latest Report",
        _markdown_table([payload.get("latest_report", {})], ["path", "artifact_type", "modified_at"]),
        "",
        "## Action Items",
        *[f"- {item}" for item in payload.get("action_items", [])],
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _gate_rows(data_trust: dict[str, Any], integration: dict[str, Any], counts: dict[str, int], latest_report: dict[str, Any]) -> list[dict[str, str]]:
    layers = {str(item.get("layer", "")): str(item.get("status", "")) for item in integration.get("items", [])}
    return [
        {
            "gate": "DataTrust",
            "status": "Pass" if data_trust.get("audit_status") == "Pass" and not data_trust.get("review_count") and not data_trust.get("rejected_count") else "Review",
            "evidence": f"audit_status={data_trust.get('audit_status')}; review={data_trust.get('review_count')}; rejected={data_trust.get('rejected_count')}",
            "next_action": "Keep evidence audit clean before using research outputs.",
        },
        {
            "gate": "IntegrationAudit",
            "status": str(integration.get("status", "Review")),
            "evidence": f"summary={integration.get('summary', {})}",
            "next_action": "Run scripts/auditPFIIntegration.sh --no-write if not Pass.",
        },
        {
            "gate": "NoLiveTradingBoundary",
            "status": layers.get("NoLiveTradingBoundary", "Review"),
            "evidence": "No live order path must remain enforced.",
            "next_action": "Remove or fail closed any real-order code path.",
        },
        {
            "gate": "ReportEvidence",
            "status": layers.get("ReportEvidence", "Review"),
            "evidence": f"run_metadata={counts.get('Run Metadata', 0)}; report_evidence_layer={layers.get('ReportEvidence', '')}",
            "next_action": "Generate a report with RunMetadata before using results.",
        },
        {
            "gate": "LatestWordReport",
            "status": "Pass" if latest_report.get("path") else "Review",
            "evidence": str(latest_report.get("path", "")),
            "next_action": "Generate at least one Word report for the current research session.",
        },
    ]


def _readiness_status(gates: list[dict[str, str]]) -> str:
    statuses = {row["status"] for row in gates}
    if "Fail" in statuses or "Blocked" in statuses:
        return "Blocked"
    if any(status != "Pass" for status in statuses):
        return "NeedsReview"
    return "ReadyForResearch"


def _action_items(gates: list[dict[str, str]], provider_summary: dict[str, int], health_rows: list[dict[str, str]], latest_report: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for gate in gates:
        if gate["status"] != "Pass":
            items.append(f"{gate['gate']}: {gate['next_action']}")
    if provider_summary.get("needs_opend", 0):
        items.append("If using Moomoo real data, start Moomoo OpenD first; this system remains quote/research-only.")
    if provider_summary.get("needs_config", 0):
        items.append("Configure provider API keys only for the data sources you actually use; do not store keys in source code.")
    review_health = [row for row in health_rows if row.get("status") == "Review"]
    if review_health:
        items.append(f"Review {len(review_health)} local setup checks, mainly launchers or local scripts.")
    if latest_report.get("path"):
        items.append("Open the latest report from Report Center and check data quality, cross-source validation, and risk gates before using it.")
    if not items:
        items.append("Ready for research workflow. Keep conclusions evidence-based and research-only.")
    return items


def _provider_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"ready": 0, "needs_config": 0, "needs_package": 0, "needs_opend": 0, "other": 0}
    for row in rows:
        status = str(row.get("status", ""))
        if status == "Ready":
            counts["ready"] += 1
        elif status == "NeedsConfig":
            counts["needs_config"] += 1
        elif status == "NeedsPackage":
            counts["needs_package"] += 1
        elif status == "NeedsOpenD":
            counts["needs_opend"] += 1
        else:
            counts["other"] += 1
    return counts


def _count_statuses(rows: list[dict[str, str]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status", "Unknown"))
        result[status] = result.get(status, 0) + 1
    return result


def _health_row(item: HealthCheck | dict[str, Any]) -> dict[str, str]:
    if isinstance(item, dict):
        return {key: str(value) for key, value in item.items()}
    return {
        "item_cn": item.item_cn,
        "item_en": item.item_en,
        "status": item.status,
        "detail_cn": item.detail_cn,
        "detail_en": item.detail_en,
    }


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "None"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        values = [str(row.get(column, "")).replace("\n", " ").replace("|", "/") for column in columns]
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *body])


def _write_daily_readiness_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"PFIOS Daily Readiness {payload.get('as_of', '')}",
        f"Generated At: {payload.get('generated_at', '')}",
        f"Readiness Status: {payload.get('readiness_status', '')}",
        f"Health Summary: {payload.get('health_summary', {})}",
        f"Provider Summary: {payload.get('provider_summary', {})}",
        "",
        "Core Gates:",
    ]
    for row in payload.get("core_gates", []):
        lines.append(f"- {row.get('gate')}: {row.get('status')} | {row.get('evidence')}")
    lines.extend(["", "Top Actions:"])
    for item in payload.get("action_items", [])[:8]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Research-only. No live trading. No real orders.")
    content = ["BT", "/F1 11 Tf", "72 760 Td", "13 TL"]
    for line in lines[:54]:
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


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")
