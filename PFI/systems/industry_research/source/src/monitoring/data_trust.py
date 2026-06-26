from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from src.config import ROOT
from src.reporting.paths import REPORTS_HOME
from src.reporting.renderer import _markdown_to_story, _register_font


VALID_DATA_TRUST_STATUSES = {
    "RAW_IMPORTED",
    "PARSED_CANDIDATE",
    "NEEDS_REVIEW",
    "USER_CONFIRMED",
    "RECONCILED",
    "ARCHIVED",
    "REJECTED",
}

SYSTEM_AUDIT_DIRNAME = "system_audit"


@dataclass(frozen=True)
class DataTrustRecord:
    record_id: str
    source_type: str
    source_name: str
    source_path: str
    data_trust_status: str
    evidence_classification: str
    decision_grade: str
    freshness: str
    row_count: int
    required_fields_present: bool
    source_url_count: int
    fetch_time_min: str
    fetch_time_max: str
    sha256: str
    issues: str
    next_action: str


def build_data_trust_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    reports_home: Path | str = REPORTS_HOME,
) -> dict[str, Any]:
    project_root = Path(root)
    records = build_data_trust_records(as_of, root=project_root, reports_home=Path(reports_home))
    status_counts = Counter(record.data_trust_status for record in records)
    evidence_counts = Counter(record.evidence_classification for record in records)
    decision_counts = Counter(record.decision_grade for record in records)
    blocked_count = status_counts.get("REJECTED", 0)
    review_count = status_counts.get("NEEDS_REVIEW", 0)
    audit_status = "Blocked" if blocked_count else "Review" if review_count else "Pass"
    payload = {
        "schema": "AIResearchDataTrustV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": _now(),
        "audit_status": audit_status,
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "record_count": len(records),
        "assumptions": [
            "This audit is read-only and does not refresh market data, OpenD, moomoo, Alipay, policy bridge, or ResearchBus.",
            "NEEDS_REVIEW means the artifact can inform research only after manual review or stronger source confirmation.",
            "RECONCILED means the artifact has the expected local companion evidence for this audit; it is not a trading approval.",
        ],
        "records": [asdict(record) for record in records],
    }
    return payload


def build_data_trust_records(
    as_of: str,
    *,
    root: Path | str = ROOT,
    reports_home: Path | str = REPORTS_HOME,
) -> list[DataTrustRecord]:
    project_root = Path(root)
    report_root = Path(reports_home)
    records: list[DataTrustRecord] = []
    records.extend(_source_log_records(as_of, project_root, report_root))
    records.extend(_csv_records(as_of, project_root))
    records.extend(_json_records(as_of, project_root))
    return sorted(records, key=lambda row: (row.data_trust_status, row.source_type, row.source_name, row.source_path))


def write_data_trust_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    reports_home: Path | str = REPORTS_HOME,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    audit = build_data_trust_audit(as_of, root=project_root, reports_home=Path(reports_home))
    target_dir = Path(output_dir) if output_dir else project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"data_trust_audit_{as_of}"
    json_path = target_dir / f"{stem}.json"
    csv_path = target_dir / f"{stem}.csv"
    markdown_path = target_dir / f"{stem}.md"
    pdf_path = target_dir / f"{stem}.pdf"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_records_csv(csv_path, audit["records"])
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


def _source_log_records(as_of: str, root: Path, reports_home: Path) -> list[DataTrustRecord]:
    records = []
    for path in sorted((root / "data" / "report_artifacts").glob("**/_source_logs/*.json")):
        payload = _load_json(path, {})
        sources = payload.get("sources") if isinstance(payload, dict) else []
        report_name = str(payload.get("report_name") or path.name.replace("_sources.json", "")) if isinstance(payload, dict) else path.stem
        required_ok = True
        issues: list[str] = []
        fetch_times: list[str] = []
        source_urls = 0
        if not isinstance(sources, list) or not sources:
            required_ok = False
            issues.append("source log has no sources")
        else:
            for index, source in enumerate(sources, start=1):
                if not isinstance(source, dict):
                    required_ok = False
                    issues.append(f"source[{index}] is not an object")
                    continue
                for field in ["source_name", "source_url", "fetch_time", "data_version"]:
                    if not str(source.get(field, "")).strip():
                        required_ok = False
                        issues.append(f"source[{index}] missing {field}")
                if str(source.get("source_url", "")).strip():
                    source_urls += 1
                if str(source.get("fetch_time", "")).strip():
                    fetch_times.append(str(source.get("fetch_time")))
        markdown_path = path.parent.parent / "_markdown" / f"{report_name}.md"
        pdf_report = _pdf_path_for_report(report_name, reports_home)
        if not markdown_path.exists():
            issues.append("matching markdown report is missing")
        if not pdf_report.exists():
            issues.append("matching PDF report is missing")
        if required_ok and markdown_path.exists() and pdf_report.exists():
            status = "RECONCILED"
            decision = "Actionable"
            next_action = "可作为报告来源链证据；仍需结合质量闸门和账户/行情门禁。"
        elif required_ok:
            status = "PARSED_CANDIDATE"
            decision = "Watch"
            next_action = "补齐 markdown/PDF 伴随证据后再进入正式报告证据链。"
        else:
            status = "NEEDS_REVIEW"
            decision = "Watch"
            next_action = "修复 source log 必填字段，缺失时不得提升结论等级。"
        records.append(
            _record(
                as_of,
                source_type="report_source_log",
                source_name=report_name,
                source_path=path,
                status=status,
                evidence="FACT",
                decision=decision,
                row_count=len(sources) if isinstance(sources, list) else 0,
                required_ok=required_ok,
                source_url_count=source_urls,
                fetch_times=fetch_times,
                issues=issues,
                next_action=next_action,
            )
        )
    return records


def _csv_records(as_of: str, root: Path) -> list[DataTrustRecord]:
    paths = [
        *sorted((root / "data" / "sample").glob("*.csv")),
        *sorted((root / "data" / "private" / "alipay").glob("*.csv")),
    ]
    records = []
    for path in paths:
        rows = _read_csv(path)
        required = _required_fields_for_csv(path.name)
        required_ok = bool(rows) and all(field in rows[0] for field in required)
        issues = [] if rows else ["csv has no rows"]
        if rows and not required_ok:
            issues.append("missing required fields: " + ", ".join(field for field in required if field not in rows[0]))
        status, decision, next_action = _classify_csv(path, rows, required_ok)
        records.append(
            _record(
                as_of,
                source_type="csv_artifact",
                source_name=path.name,
                source_path=path,
                status=status,
                evidence="FACT" if status in {"USER_CONFIRMED", "RECONCILED"} else "OBSERVATION",
                decision=decision,
                row_count=len(rows),
                required_ok=required_ok,
                source_url_count=sum(1 for row in rows if str(row.get("source_url", "")).strip()),
                fetch_times=_row_times(rows),
                issues=issues,
                next_action=next_action,
            )
        )
    return records


def _json_records(as_of: str, root: Path) -> list[DataTrustRecord]:
    patterns = [
        "data/report_artifacts/automation_logs/automation_health_*.json",
        "data/report_artifacts/policy_bridge/status/*.json",
        "data/report_artifacts/research_bus_bridge/*.json",
        "data/report_artifacts/pfi_os_bridge/*.json",
        "data/report_artifacts/**/_pfi_os/validation_summary_*.json",
    ]
    records = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path in seen:
                continue
            seen.add(path)
            payload = _load_json(path, {})
            status, decision, next_action, issues, count = _classify_json(path, payload)
            records.append(
                _record(
                    as_of,
                    source_type="json_artifact",
                    source_name=path.name,
                    source_path=path,
                    status=status,
                    evidence="FACT" if status in {"RECONCILED", "USER_CONFIRMED"} else "OBSERVATION",
                    decision=decision,
                    row_count=count,
                    required_ok=not issues,
                    source_url_count=_json_source_url_count(payload),
                    fetch_times=_json_times(payload),
                    issues=issues,
                    next_action=next_action,
                )
            )
    return records


def _classify_csv(path: Path, rows: list[dict[str, str]], required_ok: bool) -> tuple[str, str, str]:
    name = path.name
    statuses = {str(row.get("status", "")).strip().lower() for row in rows}
    if not required_ok:
        return "NEEDS_REVIEW", "Watch", "补齐必需字段或重新导入后再进入证据链。"
    if name == "daily_update_log.csv":
        if "confirmed" in statuses:
            return "USER_CONFIRMED", "Actionable", "可作为账户更新事实；仍需逐项检查候选行。"
        return "NEEDS_REVIEW", "Watch", "等待用户确认截图/视频/导出文件后再提升状态。"
    if name in {"import_log.csv", "trade_ledger.csv"}:
        return "USER_CONFIRMED", "Actionable", "官方导出或确认流水可用于账户事实核对。"
    if name.startswith("raw_transactions_"):
        return "RAW_IMPORTED", "Observe", "保留为原始导入证据，不直接用于行动结论。"
    if name == "current_positions.csv":
        if statuses <= {"confirmed", "user_confirmed"}:
            return "USER_CONFIRMED", "Actionable", "当前持仓已确认，可用于持仓事实层。"
        return "NEEDS_REVIEW", "Watch", "当前持仓含视频可见或延续口径，进入人工复核。"
    if "pending" in name or "candidate" in name:
        if rows:
            return "NEEDS_REVIEW", "Watch", "候选或待确认数据不能直接进入正式行动口径。"
        return "RECONCILED", "Observe", "当前没有待确认候选。"
    if name == "watchlist_snapshot.csv":
        if any(str(row.get("source_name", "")).startswith("OpenD") for row in rows):
            return "PARSED_CANDIDATE", "Watch", "行情快照可用于研究，但仍需结合 automation health 覆盖率。"
        return "NEEDS_REVIEW", "Watch", "行情主要依赖 fallback，正式行动前需要核对 OpenD/数据源覆盖。"
    if path.parts[-2] == "sample":
        return "PARSED_CANDIDATE", "Observe", "样例或本地快照可用于复现，不单独提升交易研究结论。"
    return "PARSED_CANDIDATE", "Observe", "已解析，可作为候选证据。"


def _classify_json(path: Path, payload: Any) -> tuple[str, str, str, list[str], int]:
    issues: list[str] = []
    if not isinstance(payload, dict):
        return "NEEDS_REVIEW", "Watch", "JSON 结构异常，需要人工检查。", ["json root is not an object"], 0
    name = path.name
    if name.startswith("automation_health_"):
        if "1900-01-01" in name:
            return "ARCHIVED", "Observe", "历史占位健康检查已归档，不作为当前运行阻断。", issues, _json_count(payload)
        status = str(payload.get("status", "")).lower()
        if status == "pass":
            return "RECONCILED", "Actionable", "自动化健康检查通过，可作为运行环境事实。", issues, _json_count(payload)
        if status == "fail":
            return "REJECTED", "Reject", "自动化健康失败，相关报告或建议必须降级。", ["automation health failed"], _json_count(payload)
        return "NEEDS_REVIEW", "Watch", "自动化健康为 warn，需要先处理覆盖率、报告缺失或账户更新问题。", ["automation health warning"], _json_count(payload)
    if "policy_bridge_status_" in name:
        refresh = payload.get("refresh") if isinstance(payload.get("refresh"), dict) else {}
        refresh_status = str(refresh.get("status", "")).lower()
        if refresh_status in {"failed", "error", "timeout"}:
            return "REJECTED", "Reject", "政策桥接失败，不得提高政策催化结论等级。", ["policy bridge refresh failed"], _json_count(payload)
        if refresh_status in {"cached_refreshed", "cached"}:
            return "PARSED_CANDIDATE", "Watch", "政策桥接使用缓存，正式结论前需核验原文和报告路径。", ["policy bridge uses cache"], _json_count(payload)
        return "RECONCILED", "Actionable", "政策桥接状态可作为来源事实。", issues, _json_count(payload)
    if name == "PFIOSResults.json":
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        weak = [
            row
            for row in results
            if str(row.get("research_status", "")).lower() in {"needsmoreevidence", "dataqualityreview", "donotuse"}
            or str(row.get("status", "")).lower() in {"review", "block", "blocked"}
        ]
        if weak:
            return "NEEDS_REVIEW", "Watch", "PFIOS 结果含 Review/NeedsMoreEvidence，报告只能降级使用。", [f"weak pfi_os rows={len(weak)}"], len(results)
        return "RECONCILED", "Actionable", "PFIOS 结果无明显弱证据状态。", issues, len(results)
    if name.endswith("FromBus.json"):
        count = _research_bus_payload_count(payload)
        if "HoldingUpdateCandidates" in name and count > 0:
            return "NEEDS_REVIEW", "Watch", "ResearchBus 有持仓更新候选，必须人工复核。", [f"pending candidates={count}"], count
        if count == 0:
            return "RECONCILED", "Observe", "ResearchBus 对应队列为空，无需行动。", issues, 0
        return "PARSED_CANDIDATE", "Watch", "ResearchBus 同步数据已落地，需按来源系统口径核验。", issues, count
    if name.startswith("validation_summary_"):
        status_counts = payload.get("status_counts") if isinstance(payload.get("status_counts"), dict) else {}
        weak = sum(int(status_counts.get(key, 0) or 0) for key in ["NeedsMoreEvidence", "DataQualityReview", "DoNotUse", "Blocked", "Review"])
        total = sum(int(value or 0) for value in status_counts.values()) if status_counts else _json_count(payload)
        if weak:
            return "NEEDS_REVIEW", "Watch", "验证摘要含弱证据或阻塞状态，需要降级使用。", [f"weak validation rows={weak}"], total
        return "RECONCILED", "Actionable", "验证摘要无弱证据状态。", issues, total
    return "PARSED_CANDIDATE", "Observe", "JSON 已归档，可作为候选证据。", issues, _json_count(payload)


def _record(
    as_of: str,
    *,
    source_type: str,
    source_name: str,
    source_path: Path,
    status: str,
    evidence: str,
    decision: str,
    row_count: int,
    required_ok: bool,
    source_url_count: int,
    fetch_times: Iterable[str],
    issues: list[str],
    next_action: str,
) -> DataTrustRecord:
    if status not in VALID_DATA_TRUST_STATUSES:
        raise ValueError(f"Invalid data trust status: {status}")
    clean_times = sorted(t for t in fetch_times if str(t).strip())
    return DataTrustRecord(
        record_id=_stable_id(source_type, str(source_path), status),
        source_type=source_type,
        source_name=source_name,
        source_path=str(source_path),
        data_trust_status=status,
        evidence_classification=evidence,
        decision_grade=decision,
        freshness=_freshness(as_of, clean_times),
        row_count=int(row_count),
        required_fields_present=bool(required_ok),
        source_url_count=int(source_url_count),
        fetch_time_min=clean_times[0] if clean_times else "",
        fetch_time_max=clean_times[-1] if clean_times else "",
        sha256=_sha256(source_path),
        issues="; ".join(dict.fromkeys(issue for issue in issues if issue)),
        next_action=next_action,
    )


def _required_fields_for_csv(name: str) -> list[str]:
    if name == "watchlist_snapshot.csv":
        return ["date", "symbol", "close", "source_name", "source_url"]
    if name == "watchlist_moomoo.csv":
        return ["symbol", "name", "exchange", "asset_class"]
    if name == "current_positions.csv":
        return ["date", "name", "amount", "status"]
    if name == "daily_update_log.csv":
        return ["date", "status", "source_type", "source_path"]
    if name == "import_log.csv":
        return ["source_path", "total_rows", "raw_output_path"]
    if name.startswith("video_position_candidates"):
        return ["date", "name", "amount", "status"]
    if name.startswith("video_trade_candidates"):
        return ["trade_date", "name", "status", "source_path"]
    if name == "pending_orders.csv":
        return ["trade_date", "name", "status"]
    if name == "trade_ledger.csv":
        return ["trade_date", "name", "status"]
    return []


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _row_times(rows: list[dict[str, str]]) -> list[str]:
    fields = ["fetch_time", "updated_at", "date", "trade_date", "imported_at", "source_end_time"]
    times = []
    for row in rows:
        for field in fields:
            value = str(row.get(field, "")).strip()
            if value:
                times.append(value)
                break
    return times


def _json_times(payload: Any) -> list[str]:
    times: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"generated_at", "exported_at", "updated_at", "created_at", "fetch_time", "as_of", "date", "started_at", "completed_at"}:
                    if str(item).strip():
                        times.append(str(item))
                if isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(value, list):
            for item in value[:100]:
                visit(item)

    visit(payload)
    return times


def _json_source_url_count(payload: Any) -> int:
    count = 0

    def visit(value: Any) -> None:
        nonlocal count
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "source_url" and str(item).strip():
                    count += 1
                elif isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return count


def _json_count(payload: Any) -> int:
    if isinstance(payload, dict):
        for key in ["checks", "results", "holdings", "portfolio_transactions", "validation_tasks", "independent_validation_runs"]:
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
        return len(payload)
    if isinstance(payload, list):
        return len(payload)
    return 0


def _research_bus_payload_count(payload: dict[str, Any]) -> int:
    for key, value in payload.items():
        if isinstance(value, list):
            return len(value)
    return 0


def _pdf_path_for_report(report_name: str, reports_home: Path) -> Path:
    report_date = _date_from_report_name(report_name)
    monday = report_date.fromordinal(report_date.toordinal() - report_date.weekday())
    sunday = monday.fromordinal(monday.toordinal() + 6)
    week_of_month = (monday.day - 1) // 7 + 1
    return reports_home / f"{monday.month}月第{week_of_month}周 {monday:%d%m}-{sunday:%d%m}" / f"{report_name}.pdf"


def _date_from_report_name(name: str) -> date:
    path = Path(name)
    stem = path.stem if path.suffix.lower() in {".pdf", ".md", ".json", ".docx", ".doc", ".txt"} else str(name)
    match = re.search(r"_(\d{2})(\d{2})(\d{4})$", stem)
    if not match:
        match = re.search(r"(?:^|\s)(\d{2})(\d{2})(\d{4})_", stem)
    if match:
        day, month, year = match.groups()
        return date(int(year), int(month), int(day))
    iso_match = re.search(r"_(\d{4})-(\d{2})-(\d{2})$", stem)
    if iso_match:
        year, month, day = iso_match.groups()
        return date(int(year), int(month), int(day))
    return date.today()


def _freshness(as_of: str, times: list[str]) -> str:
    if not times:
        return "Missing"
    dates = [_parse_date(value) for value in times]
    dates = [value for value in dates if value is not None]
    if not dates:
        return "Unknown"
    latest = max(dates)
    target = date.fromisoformat(as_of)
    age = (target - latest).days
    if age <= 1:
        return "Fresh"
    if age <= 7:
        return "Delayed"
    return "Stale"


def _parse_date(value: str) -> date | None:
    text = str(value).strip()
    if not text:
        return None
    if len(text) >= 10:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            pass
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return date.fromisoformat("-".join(match.groups()))
    match = re.search(r"(\d{2})(\d{2})(\d{4})", text)
    if match:
        day, month, year = match.groups()
        return date(int(year), int(month), int(day))
    return None


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"dataTrust_{digest}"


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _write_records_csv(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def _audit_markdown(audit: dict[str, Any]) -> str:
    records = list(audit["records"])
    watch_rows = [row for row in records if row["data_trust_status"] in {"NEEDS_REVIEW", "REJECTED"}][:30]
    sample_rows = records[:30]
    lines = [
        f"# AI-Research-System Data Trust Audit {audit['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {audit['system']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Records: {audit['record_count']}",
        "",
        "## Status Definitions",
        "- RAW_IMPORTED: 原始导入证据，只能保留追溯，不直接支撑行动结论。",
        "- PARSED_CANDIDATE: 已解析候选证据，可以辅助研究，但还不能提高结论等级。",
        "- NEEDS_REVIEW: 需要人工复核或更强来源确认，正式结论必须降级。",
        "- USER_CONFIRMED: 用户确认或官方导出来源，可作为账户/持仓事实。",
        "- RECONCILED: 已具备本审计要求的伴随证据，可进入报告证据链。",
        "- ARCHIVED: 已归档历史证据，不参与当前行动判断。",
        "- REJECTED: 失败、冲突或不可用证据，必须阻断对应结论。",
        "",
        "## Status Summary",
        _markdown_table([{"status": key, "count": value} for key, value in audit["status_counts"].items()], ["status", "count"]),
        "",
        "## Decision Summary",
        _markdown_table([{"decision": key, "count": value} for key, value in audit["decision_counts"].items()], ["decision", "count"]),
        "",
        "## Review Queue",
        _markdown_table(watch_rows, ["source_type", "source_name", "data_trust_status", "freshness", "row_count", "issues", "next_action"]),
        "",
        "## Sample Records",
        _markdown_table(sample_rows, ["source_type", "source_name", "data_trust_status", "evidence_classification", "decision_grade", "freshness", "row_count"]),
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


def _write_pdf(path: Path, markdown: str) -> None:
    _register_font()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=path.stem,
    )
    doc.build(_markdown_to_story(markdown))
