from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.storage import atomic_write_json, atomic_write_text

MASTER_SYSTEM_ID = "PFI_OS"


REPORT_DECISION_COLUMNS = [
    "decision_id",
    "date_folder",
    "run",
    "strategy_id",
    "symbol",
    "market",
    "report_readiness",
    "evidence_score",
    "research_status",
    "risk_gate_status",
    "decision_quality_status",
    "decision_quality_score",
    "data_quality_status",
    "cross_validation_status",
    "missing_evidence_count",
    "critical_missing_evidence",
    "total_return",
    "annualized_return",
    "sharpe",
    "max_drawdown",
    "trade_count",
    "cost_ratio",
    "metadata_path",
    "linked_report_path",
    "next_action",
]


def build_report_decision_support_index(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    max_records: int = 500,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    records = _collect_records(reports)
    records.sort(key=lambda row: str(row.get("metadata_modified_at", "")), reverse=True)
    limited = records[: max(1, int(max_records))]
    return {
        "schema": "PFIOSReportDecisionSupportIndexV1",
        "system": MASTER_SYSTEM_ID,
        "subsystem": "Report Decision Support Index",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "report_root": str(reports),
        "record_count": len(limited),
        "summary": _summary(limited),
        "records": limited,
        "assumptions": [
            "This index is read-only and does not modify existing Word reports or RunMetadata files.",
            "ContinueResearch requires traceable report evidence, a linked Word report, data quality, cross-source validation, risk gates, and decision-quality evidence.",
            "NeedsMoreEvidence means the report may still be useful for research review, but should not be treated as trade-ready evidence.",
            "DoNotUse means at least one decision, risk, or evidence gate explicitly rejects the report for decision support.",
            "No live trading, no real orders, and no financial advice are produced by this index.",
        ],
    }


def write_report_decision_support_index(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    output_dir: Path | str | None = None,
    max_records: int = 500,
) -> dict[str, Any]:
    payload = build_report_decision_support_index(
        as_of=as_of,
        project_root=project_root,
        report_root=report_root,
        max_records=max_records,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "reportDecision"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    stem = f"ReportDecisionSupportIndex_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    latest_json = target / "ReportDecisionSupportIndex_latest.json"
    latest_csv = target / "ReportDecisionSupportIndex_latest.csv"
    latest_markdown = target / "ReportDecisionSupportIndex_latest.md"
    latest_pdf = target / "ReportDecisionSupportIndex_latest.pdf"
    payload["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
        "latest_json": str(latest_json),
        "latest_csv": str(latest_csv),
        "latest_markdown": str(latest_markdown),
        "latest_pdf": str(latest_pdf),
    }
    csv_text = _csv_text(payload.get("records", []))
    markdown = report_decision_support_markdown(payload)
    atomic_write_text(csv_path, csv_text)
    atomic_write_text(latest_csv, csv_text)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(latest_markdown, markdown)
    _write_report_decision_pdf(pdf_path, payload)
    _write_report_decision_pdf(latest_pdf, payload)
    atomic_write_json(json_path, payload)
    atomic_write_json(latest_json, payload)
    return payload


def report_decision_support_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        f"# Report Decision Support Index {payload.get('as_of', '')}",
        "",
        "## Summary",
        f"- System: `{payload.get('system', '')}`",
        f"- Record Count: `{payload.get('record_count', 0)}`",
        f"- ContinueResearch: `{summary.get('continue_research_count', 0)}`",
        f"- NeedsMoreEvidence: `{summary.get('needs_more_evidence_count', 0)}`",
        f"- WatchOnly: `{summary.get('watch_only_count', 0)}`",
        f"- DoNotUse: `{summary.get('do_not_use_count', 0)}`",
        f"- Average Evidence Score: `{summary.get('average_evidence_score', 0)}`",
        "",
        "## Readiness Counts",
        _markdown_table(summary.get("readiness_counts", []), ["report_readiness", "count"]),
        "",
        "## Top Missing Evidence",
        _markdown_table(summary.get("missing_evidence_counts", []), ["missing_evidence", "count"]),
        "",
        "## Records",
        _markdown_table(
            payload.get("records", [])[:80],
            [
                "date_folder",
                "run",
                "strategy_id",
                "report_readiness",
                "evidence_score",
                "critical_missing_evidence",
                "next_action",
            ],
        ),
        "",
        "## Assumptions",
        *[f"- {item}" for item in payload.get("assumptions", [])],
    ]
    return "\n".join(lines) + "\n"


def _collect_records(report_root: Path) -> list[dict[str, Any]]:
    if not report_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for metadata_path in sorted(report_root.glob("**/RunMetadata*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        records.append(_record_from_metadata(metadata_path, report_root))
    return records


def _record_from_metadata(metadata_path: Path, report_root: Path) -> dict[str, Any]:
    stat = metadata_path.stat()
    base = {
        "decision_id": _stable_id(str(metadata_path), str(stat.st_mtime_ns), str(stat.st_size)),
        "date_folder": _date_folder(metadata_path, report_root),
        "run": metadata_path.stem,
        "metadata_path": str(metadata_path),
        "metadata_modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            **base,
            "strategy_id": "",
            "report_readiness": "DoNotUse",
            "evidence_score": 0,
            "research_status": "UnreadableMetadata",
            "risk_gate_status": "Missing",
            "decision_quality_status": "Missing",
            "decision_quality_score": 0,
            "data_quality_status": "Missing",
            "cross_validation_status": "Missing",
            "missing_evidence_count": 1,
            "critical_missing_evidence": "RunMetadata JSON unreadable",
            "total_return": 0.0,
            "annualized_return": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "trade_count": 0,
            "cost_ratio": 0.0,
            "linked_report_path": "",
            "next_action": f"修复不可读取的 RunMetadata：{exc}",
        }
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
    risk_gate = payload.get("risk_gate", {}) if isinstance(payload, dict) else {}
    decision_quality = payload.get("decision_quality", {}) if isinstance(payload, dict) else {}
    report_evidence = payload.get("report_evidence", {}) if isinstance(payload, dict) else {}
    strategy = metadata.get("strategy", {}) if isinstance(metadata, dict) else {}
    backtest = metadata.get("backtest", {}) if isinstance(metadata, dict) else {}
    entity = metadata.get("entity", {}) if isinstance(metadata, dict) else {}
    linked_report = _linked_report_path(metadata_path)
    missing = _missing_evidence(report_evidence, risk_gate, decision_quality, linked_report)
    statuses = _status_values(report_evidence, risk_gate, decision_quality)
    readiness = _report_readiness(statuses, missing, linked_report)
    cost_total = _safe_float(metrics.get("cost_total"))
    ending_equity = _safe_float(metrics.get("ending_equity"))
    cost_ratio = cost_total / ending_equity if ending_equity else 0.0
    return {
        **base,
        "strategy_id": str(strategy.get("strategy_id", "")),
        "symbol": str(backtest.get("symbol") or entity.get("canonical_symbol") or ""),
        "market": str(backtest.get("market") or entity.get("market") or ""),
        "report_readiness": readiness,
        "evidence_score": _evidence_score(report_evidence, risk_gate, decision_quality, linked_report, missing),
        "research_status": _research_status(statuses, readiness),
        "risk_gate_status": str(risk_gate.get("status") or "Missing"),
        "decision_quality_status": str(decision_quality.get("status") or "Missing"),
        "decision_quality_score": int(_safe_float(decision_quality.get("score"))),
        "data_quality_status": str(report_evidence.get("data_quality_status") or "Missing"),
        "cross_validation_status": str(report_evidence.get("cross_validation_status") or "Missing"),
        "missing_evidence_count": len(missing),
        "critical_missing_evidence": "; ".join(missing[:8]),
        "total_return": _safe_float(metrics.get("total_return")),
        "annualized_return": _safe_float(metrics.get("annualized_return")),
        "sharpe": _safe_float(metrics.get("sharpe")),
        "max_drawdown": _safe_float(metrics.get("max_drawdown")),
        "trade_count": int(_safe_float(metrics.get("trade_count"))),
        "cost_ratio": round(cost_ratio, 6),
        "linked_report_path": str(linked_report) if linked_report else "",
        "next_action": _next_action(readiness, missing),
    }


def _linked_report_path(metadata_path: Path) -> Path | None:
    parent = metadata_path.parent
    if not parent.exists():
        return None
    docx_files = [path for path in parent.glob("*.docx") if path.is_file() and path.stat().st_size > 0]
    if not docx_files:
        return None
    tokens = set(re.findall(r"\d{8,14}", metadata_path.name))
    if tokens:
        token_matches = [path for path in docx_files if any(token in path.name for token in tokens)]
        if token_matches:
            return max(token_matches, key=lambda path: path.stat().st_mtime)
    return max(docx_files, key=lambda path: path.stat().st_mtime)


def _missing_evidence(
    report_evidence: dict[str, Any],
    risk_gate: dict[str, Any],
    decision_quality: dict[str, Any],
    linked_report: Path | None,
) -> list[str]:
    missing: list[str] = []
    if report_evidence.get("schema") != "PFIOSReportEvidenceV1":
        missing.append("PFIOSReportEvidenceV1")
        if not report_evidence.get("data_quality_status"):
            missing.append("数据质量状态")
        if not report_evidence.get("cross_validation_status"):
            missing.append("多源交叉校验状态")
    missing.extend(str(item) for item in report_evidence.get("missing_evidence", []) or [])
    missing.extend(str(item) for item in risk_gate.get("missing_evidence", []) or [])
    missing.extend(str(item) for item in decision_quality.get("missing_evidence", []) or [])
    if not risk_gate.get("status"):
        missing.append("风险闸门状态")
    if not decision_quality.get("status"):
        missing.append("决策质量状态")
    if linked_report is None:
        missing.append("Word 报告文件")
    return _dedupe(missing)


def _status_values(report_evidence: dict[str, Any], risk_gate: dict[str, Any], decision_quality: dict[str, Any]) -> set[str]:
    return {
        str(value)
        for value in [
            report_evidence.get("evidence_status"),
            report_evidence.get("risk_gate_status"),
            report_evidence.get("decision_quality_status"),
            risk_gate.get("status"),
            decision_quality.get("status"),
        ]
        if value
    }


def _report_readiness(statuses: set[str], missing: list[str], linked_report: Path | None) -> str:
    if "DoNotUse" in statuses:
        return "DoNotUse"
    if linked_report is None or missing:
        return "NeedsMoreEvidence"
    if "NeedsMoreEvidence" in statuses:
        return "NeedsMoreEvidence"
    if "WatchOnly" in statuses:
        return "WatchOnly"
    if "ContinueResearch" in statuses:
        return "ContinueResearch"
    return "NeedsMoreEvidence"


def _research_status(statuses: set[str], readiness: str) -> str:
    for status in ["DoNotUse", "NeedsMoreEvidence", "WatchOnly", "ContinueResearch"]:
        if status in statuses:
            return status
    return readiness


def _evidence_score(
    report_evidence: dict[str, Any],
    risk_gate: dict[str, Any],
    decision_quality: dict[str, Any],
    linked_report: Path | None,
    missing: list[str],
) -> int:
    score = 0
    if report_evidence.get("schema") == "PFIOSReportEvidenceV1":
        score += 20
    if linked_report is not None:
        score += 10
    if str(report_evidence.get("data_quality_status")) in {"Pass", "Info"}:
        score += 20
    elif report_evidence.get("data_quality_status"):
        score += 8
    if str(report_evidence.get("cross_validation_status")) in {"Pass", "Info"}:
        score += 20
    elif report_evidence.get("cross_validation_status"):
        score += 8
    if risk_gate.get("status"):
        score += 15
    if decision_quality.get("status"):
        score += 15
    score -= min(30, len(missing) * 3)
    return max(0, min(100, int(score)))


def _next_action(readiness: str, missing: list[str]) -> str:
    if readiness == "ContinueResearch":
        return "继续研究；进入交易前参考前仍需复核最新数据、成本和风险闸门。"
    if readiness == "WatchOnly":
        return "保留观察；先复核回撤、成本、样本外和失效环境。"
    if readiness == "DoNotUse":
        return "暂停使用该报告作为研究依据，先修复拒绝项或重新生成报告。"
    if missing:
        return "补齐缺失证据：" + "；".join(missing[:5])
    return "补充报告证据后再升级研究状态。"


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    readiness_counts = _count_rows(records, "report_readiness")
    missing_counts: dict[str, int] = {}
    for row in records:
        for item in str(row.get("critical_missing_evidence", "")).split(";"):
            normalized = item.strip()
            if normalized:
                missing_counts[normalized] = missing_counts.get(normalized, 0) + 1
    scores = [int(_safe_float(row.get("evidence_score"))) for row in records]
    return {
        "total_records": len(records),
        "continue_research_count": _status_count(records, "ContinueResearch"),
        "needs_more_evidence_count": _status_count(records, "NeedsMoreEvidence"),
        "watch_only_count": _status_count(records, "WatchOnly"),
        "do_not_use_count": _status_count(records, "DoNotUse"),
        "average_evidence_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "readiness_counts": readiness_counts,
        "missing_evidence_counts": [
            {"missing_evidence": key, "count": value}
            for key, value in sorted(missing_counts.items(), key=lambda item: (-item[1], item[0]))[:20]
        ],
    }


def _status_count(records: list[dict[str, Any]], status: str) -> int:
    return sum(1 for row in records if row.get("report_readiness") == status)


def _count_rows(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key, "") or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return [{key: value, "count": count} for value, count in sorted(counts.items())]


def _csv_text(records: list[dict[str, Any]]) -> str:
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=REPORT_DECISION_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow(record)
    return handle.getvalue()


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _write_report_decision_pdf(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary", {})
    lines = [
        f"Report Decision Support Index {payload.get('as_of', '')}",
        f"System: {payload.get('system', '')}",
        f"Record Count: {payload.get('record_count', 0)}",
        f"ContinueResearch: {summary.get('continue_research_count', 0)}",
        f"NeedsMoreEvidence: {summary.get('needs_more_evidence_count', 0)}",
        f"WatchOnly: {summary.get('watch_only_count', 0)}",
        f"DoNotUse: {summary.get('do_not_use_count', 0)}",
        f"Average Evidence Score: {summary.get('average_evidence_score', 0)}",
        "",
        "Top Missing Evidence:",
    ]
    for row in summary.get("missing_evidence_counts", [])[:12]:
        lines.append(f"- {row.get('missing_evidence')}: {row.get('count')}")
    lines.extend(["", "Top Records:"])
    for row in payload.get("records", [])[:20]:
        lines.append(
            f"- {row.get('date_folder')} {row.get('run')} | {row.get('report_readiness')} | score={row.get('evidence_score')} | {row.get('next_action')}"
        )
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


def _date_folder(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return ""
    return relative.parts[0] if relative.parts else ""


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"reportDecision_{digest}"


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _pdf_ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
