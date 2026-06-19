from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import PROJECT_ROOT, REPORT_ROOT_DIR
from pfi_os.integrations.research_bus import RESEARCH_BUS_DB_PATH
from pfi_os.integrations.research_bus_audit import run_research_bus_interop_audit
from pfi_os.storage import atomic_write_json, atomic_write_text
from pfi_os.system.data_trust import build_data_trust_audit


@dataclass(frozen=True)
class PFIOSIntegrationAuditItem:
    layer: str
    status: str
    summary: str
    evidence: dict[str, Any]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_pfi_os_integration_audit(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    db_path: Path | str = RESEARCH_BUS_DB_PATH,
    ai_research_root: Path | str | None = None,
    data_trust_payload: dict[str, Any] | None = None,
    research_bus_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser()
    reports = Path(report_root).expanduser()
    bus_db = Path(db_path).expanduser()
    audit_date = as_of or datetime.now().date().isoformat()
    items = [
        _data_trust_item(data_trust_payload or build_data_trust_audit(as_of=audit_date, project_root=root, report_root=reports)),
        _entity_registry_item(root),
        _workflow_inputs_item(bus_db),
        _report_evidence_item(reports),
        _research_bus_item(research_bus_payload or _run_research_bus_audit(bus_db, ai_research_root)),
        _no_live_trading_item(root),
    ]
    status_counts = Counter(item.status for item in items)
    overall_status = "Fail" if status_counts.get("Fail") else "Review" if status_counts.get("Review") else "Pass"
    return {
        "schema": "PFIOSIntegrationAuditV1",
        "system": "PFIOS",
        "as_of": audit_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": overall_status,
        "summary": {
            "pass": int(status_counts.get("Pass", 0)),
            "review": int(status_counts.get("Review", 0)),
            "fail": int(status_counts.get("Fail", 0)),
            "item_count": len(items),
        },
        "items": [item.to_dict() for item in items],
        "assumptions": [
            "The integration audit is read-only unless write_pfi_os_integration_audit is called.",
            "It does not refresh market data, open Streamlit, start Moomoo OpenD, or mutate holdings.",
            "Pass means local evidence chains are connected; it does not approve live trading or real orders.",
        ],
    }


def write_pfi_os_integration_audit(
    *,
    as_of: str | None = None,
    project_root: Path | str = PROJECT_ROOT,
    report_root: Path | str = REPORT_ROOT_DIR,
    db_path: Path | str = RESEARCH_BUS_DB_PATH,
    ai_research_root: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    payload = build_pfi_os_integration_audit(
        as_of=as_of,
        project_root=project_root,
        report_root=report_root,
        db_path=db_path,
        ai_research_root=ai_research_root,
    )
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / "data" / "systemAudit"
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload["as_of"]))
    json_path = target / f"PFIOSIntegrationAudit_{stamp}.json"
    markdown_path = target / f"PFIOSIntegrationAudit_{stamp}.md"
    payload["outputs"] = {"json": str(json_path), "markdown": str(markdown_path)}
    atomic_write_text(markdown_path, _integration_audit_markdown(payload))
    atomic_write_json(json_path, payload)
    return payload


def _data_trust_item(payload: dict[str, Any]) -> PFIOSIntegrationAuditItem:
    status = str(payload.get("audit_status") or "")
    mapped = "Pass" if status == "Pass" else "Fail" if status == "Blocked" else "Review"
    return PFIOSIntegrationAuditItem(
        layer="DataTrust",
        status=mapped,
        summary=f"Data Trust status={status or 'Missing'}; records={payload.get('record_count', 0)}.",
        evidence={
            "audit_status": status or "Missing",
            "record_count": int(payload.get("record_count", 0) or 0),
            "review_count": int(payload.get("review_count", 0) or 0),
            "rejected_count": int(payload.get("rejected_count", 0) or 0),
        },
        next_action="处理 REJECTED 和 NEEDS_REVIEW 记录后再升级研究状态。" if mapped != "Pass" else "继续保持只读审计和证据链记录。",
    )


def _entity_registry_item(root: Path) -> PFIOSIntegrationAuditItem:
    entity_dir = root / "data" / "entityRegistry"
    json_path = entity_dir / "EntityRegistry.json"
    csv_path = entity_dir / "EntityRegistry.csv"
    markdown_path = entity_dir / "EntityRegistry.md"
    missing = [str(path.relative_to(root)) for path in [json_path, csv_path, markdown_path] if not path.exists()]
    if missing:
        return PFIOSIntegrationAuditItem(
            layer="EntityRegistry",
            status="Review",
            summary="Entity Registry artifacts are incomplete.",
            evidence={"missing": missing},
            next_action="运行 write_entity_registry() 生成 JSON/CSV/Markdown 派生产物。",
        )
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return PFIOSIntegrationAuditItem(
            layer="EntityRegistry",
            status="Fail",
            summary="Entity Registry JSON is unreadable.",
            evidence={"json_path": str(json_path), "error": str(exc)},
            next_action="修复 EntityRegistry.json 后再运行集成审计。",
        )
    schema_ok = payload.get("schema") == "PFIOSEntityRegistryV1"
    status = "Pass" if schema_ok else "Review"
    return PFIOSIntegrationAuditItem(
        layer="EntityRegistry",
        status=status,
        summary=f"Entity Registry schema={payload.get('schema', 'Missing')}; records={payload.get('record_count', 0)}.",
        evidence={
            "json": str(json_path),
            "csv": str(csv_path),
            "markdown": str(markdown_path),
            "schema": payload.get("schema", ""),
            "record_count": int(payload.get("record_count", 0) or 0),
            "status_counts": payload.get("status_counts", {}),
        },
        next_action="确认 ProxyMapped 和 MissingSymbol 的报告口径。" if status == "Pass" else "重新生成 Entity Registry。",
    )


def _workflow_inputs_item(db_path: Path) -> PFIOSIntegrationAuditItem:
    if not db_path.exists():
        return PFIOSIntegrationAuditItem(
            layer="WorkflowInputs",
            status="Review",
            summary="ResearchBus database is missing, so workflow inputs cannot be inspected.",
            evidence={"db_path": str(db_path)},
            next_action="先运行 ResearchBus 同步或提交一条聊天输入。",
        )
    try:
        counts = _workflow_input_counts_readonly(db_path)
    except Exception as exc:
        return PFIOSIntegrationAuditItem(
            layer="WorkflowInputs",
            status="Review",
            summary="Workflow input view could not be opened.",
            evidence={"db_path": str(db_path), "error": str(exc)},
            next_action="修复或重新初始化 ResearchBus SQLite 后再复核工作流输入。",
        )
    if counts["input_count"] == 0:
        return PFIOSIntegrationAuditItem(
            layer="WorkflowInputs",
            status="Review",
            summary="No workflow inputs have been recorded.",
            evidence={"db_path": str(db_path), "input_count": 0},
            next_action="通过 submit-chat、dropbox 或 API request 记录一次可追溯输入。",
        )
    return PFIOSIntegrationAuditItem(
        layer="WorkflowInputs",
        status="Pass",
        summary=f"Workflow inputs are queryable; rows={counts['input_count']}.",
        evidence={
            "db_path": str(db_path),
            "input_count": counts["input_count"],
            "status_counts": counts["status_counts"],
            "input_type_counts": counts["input_type_counts"],
        },
        next_action="新报告应引用 workflow_input_id 或明确标注 ManualOrLocalOnly。",
    )


def _report_evidence_item(report_root: Path) -> PFIOSIntegrationAuditItem:
    metadata_files = sorted(report_root.glob("**/*RunMetadata*.json"))
    if not metadata_files:
        return PFIOSIntegrationAuditItem(
            layer="ReportEvidence",
            status="Review",
            summary="No RunMetadata JSON files were found.",
            evidence={"report_root": str(report_root), "metadata_count": 0},
            next_action="生成一份新的回测 Word 报告，使 RunMetadata 包含 report_evidence。",
        )
    evidence_count = 0
    unreadable: list[str] = []
    for path in metadata_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            unreadable.append(str(path))
            continue
        evidence = payload.get("report_evidence") if isinstance(payload, dict) else None
        if isinstance(evidence, dict) and evidence.get("schema") == "PFIOSReportEvidenceV1":
            evidence_count += 1
    if unreadable:
        return PFIOSIntegrationAuditItem(
            layer="ReportEvidence",
            status="Fail",
            summary="Some RunMetadata files are unreadable.",
            evidence={"unreadable": unreadable[:10], "metadata_count": len(metadata_files)},
            next_action="修复损坏 RunMetadata JSON。",
        )
    status = "Pass" if evidence_count else "Review"
    return PFIOSIntegrationAuditItem(
        layer="ReportEvidence",
        status=status,
        summary=f"RunMetadata files={len(metadata_files)}; report_evidence={evidence_count}.",
        evidence={"report_root": str(report_root), "metadata_count": len(metadata_files), "report_evidence_count": evidence_count},
        next_action="旧报告可保留；新报告必须包含 PFIOSReportEvidenceV1。" if status == "Pass" else "重新导出报告以写入 report_evidence。",
    )


def _research_bus_item(payload: dict[str, Any]) -> PFIOSIntegrationAuditItem:
    raw_status = str(payload.get("status") or "")
    readonly_blocked = _research_bus_readonly_blocked(payload)
    status = "Pass" if raw_status == "Pass" else "Review" if payload.get("error") or readonly_blocked else "Fail" if raw_status == "Fail" else "Review"
    summary = payload.get("summary", {})
    return PFIOSIntegrationAuditItem(
        layer="ResearchBusInterop",
        status=status,
        summary=f"ResearchBus interoperability status={raw_status or 'Missing'}.",
        evidence={"status": raw_status, "summary": summary},
        next_action="处理 ResearchBus 互通审计 Warn/Fail 项。" if status != "Pass" else "继续保持跨系统同步审计。",
    )


def _workflow_input_counts_readonly(db_path: Path) -> dict[str, Any]:
    uri = f"file:{db_path}?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as conn:
        table_names = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        if "bus_chat_inputs" not in table_names or "bus_api_requests" not in table_names:
            return {"input_count": 0, "status_counts": {}, "input_type_counts": {}}
        chat_rows = conn.execute("SELECT status, COUNT(*) FROM bus_chat_inputs GROUP BY status").fetchall()
        request_rows = conn.execute(
            """
            SELECT status, COUNT(*)
            FROM bus_api_requests
            WHERE request_id NOT IN (
                SELECT linked_request_id FROM bus_chat_inputs WHERE linked_request_id != ''
            )
            GROUP BY status
            """
        ).fetchall()
    chat_count = sum(int(count) for _, count in chat_rows)
    request_count = sum(int(count) for _, count in request_rows)
    status_counts: dict[str, int] = {}
    for status, count in [*chat_rows, *request_rows]:
        key = str(status or "Unknown")
        status_counts[key] = status_counts.get(key, 0) + int(count)
    return {
        "input_count": chat_count + request_count,
        "status_counts": status_counts,
        "input_type_counts": {"chat": chat_count, "api_request": request_count},
    }


def _research_bus_readonly_blocked(payload: dict[str, Any]) -> bool:
    if "unable to open database file" in str(payload.get("error", "")):
        return True
    for item in payload.get("items", []):
        if "unable to open database file" in str(item.get("evidence", "")):
            return True
    return False


def _no_live_trading_item(root: Path) -> PFIOSIntegrationAuditItem:
    policy_text = "\n".join(_read_text(path) for path in [root / "AGENTS.md", root / "README.md", root / "docs" / "RiskAndLimits.md"])
    has_boundary = any(term in policy_text for term in ["禁止接入实盘", "禁止真实下单", "No live trading", "must not place real orders"])
    suspicious = _suspicious_live_trading_terms(root)
    if suspicious:
        return PFIOSIntegrationAuditItem(
            layer="NoLiveTradingBoundary",
            status="Fail",
            summary="Suspicious live-trading terms were found in source code.",
            evidence={"matches": suspicious[:20]},
            next_action="逐项确认并移除真实下单路径或改为只读研究模拟。",
        )
    return PFIOSIntegrationAuditItem(
        layer="NoLiveTradingBoundary",
        status="Pass" if has_boundary else "Review",
        summary="No live order code was found; policy boundary is documented." if has_boundary else "No live order code was found, but policy boundary text is incomplete.",
        evidence={"policy_boundary_documented": has_boundary},
        next_action="保持研究-only 边界。" if has_boundary else "补充 README/AGENTS 中的禁止实盘交易边界。",
    )


def _run_research_bus_audit(db_path: Path, ai_research_root: Path | str | None) -> dict[str, Any]:
    try:
        return run_research_bus_interop_audit(db_path, ai_research_root=ai_research_root, output_path=None)
    except Exception as exc:
        return {"status": "Review", "summary": {"warn": 1}, "error": str(exc)}


def _suspicious_live_trading_terms(root: Path) -> list[str]:
    source_root = root / "src"
    if not source_root.exists():
        return []
    suspicious_terms = ["place_order(", "submit_order(", "send_order(", "live_trading=True", "real_order=True"]
    matches: list[str] = []
    for path in source_root.rglob("*.py"):
        if path.name == "integration_audit.py":
            continue
        text = _read_text(path)
        for term in suspicious_terms:
            if term in text:
                matches.append(f"{path.relative_to(root)}::{term}")
    return matches


def _integration_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# PFIOS Integration Audit",
        "",
        f"- Status: `{payload.get('status', '')}`",
        f"- As Of: `{payload.get('as_of', '')}`",
        f"- Generated At: `{payload.get('generated_at', '')}`",
        "",
        "| Layer | Status | Summary | Next Action |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload.get("items", []):
        lines.append(
            "| {layer} | {status} | {summary} | {next_action} |".format(
                layer=_markdown_cell(item.get("layer", "")),
                status=_markdown_cell(item.get("status", "")),
                summary=_markdown_cell(item.get("summary", "")),
                next_action=_markdown_cell(item.get("next_action", "")),
            )
        )
    return "\n".join(lines) + "\n"


def _date_stamp(as_of: str) -> str:
    try:
        return datetime.fromisoformat(as_of).strftime("%d%m%Y")
    except ValueError:
        return datetime.now().strftime("%d%m%Y")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()
