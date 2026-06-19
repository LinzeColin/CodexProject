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
from src.reporting.paths import REPORTS_HOME


@dataclass(frozen=True)
class ReconciliationCheck:
    check_id: str
    domain: str
    check_name: str
    status: str
    severity: str
    evidence_classification: str
    decision_grade: str
    observed: str
    expected: str
    source_paths: str
    issue: str
    next_action: str


def build_reconciliation_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    reports_home: Path | str = REPORTS_HOME,
) -> dict[str, Any]:
    project_root = Path(root)
    report_root = Path(reports_home)
    data_trust_path = project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME / f"data_trust_audit_{as_of}.json"
    checks: list[ReconciliationCheck] = []
    data_trust = _load_json(data_trust_path, {})

    checks.extend(_data_trust_checks(project_root, data_trust_path, data_trust))
    checks.extend(_source_log_checks(project_root, report_root, data_trust))
    checks.extend(_bridge_checks(project_root))
    checks.extend(_automation_health_checks(project_root, as_of))
    checks.extend(_handoff_checks(project_root, as_of))

    status_counts = Counter(check.status for check in checks)
    severity_counts = Counter(check.severity for check in checks)
    audit_status = "Blocked" if status_counts.get("fail", 0) else "Review" if status_counts.get("warn", 0) else "Pass"
    return {
        "schema": "AIResearchReconciliationV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": _now(),
        "audit_status": audit_status,
        "check_count": len(checks),
        "status_counts": dict(sorted(status_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "assumptions": [
            "This audit is read-only and compares local artifacts only.",
            "A fail means the corresponding evidence chain cannot support executable trading actions.",
            "A warn means the artifact can support observation only until stronger evidence is available.",
        ],
        "checks": [asdict(check) for check in checks],
    }


def write_reconciliation_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    reports_home: Path | str = REPORTS_HOME,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    audit = build_reconciliation_audit(as_of, root=project_root, reports_home=reports_home)
    target_dir = Path(output_dir) if output_dir else project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"reconciliation_audit_{as_of}"
    json_path = target_dir / f"{stem}.json"
    csv_path = target_dir / f"{stem}.csv"
    markdown_path = target_dir / f"{stem}.md"
    pdf_path = target_dir / f"{stem}.pdf"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_checks_csv(csv_path, audit["checks"])
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


def _data_trust_checks(root: Path, data_trust_path: Path, data_trust: Any) -> list[ReconciliationCheck]:
    checks: list[ReconciliationCheck] = []
    if not data_trust_path.exists():
        return [
            _check(
                "data_trust_artifact_exists",
                "data_trust",
                "fail",
                "P0",
                "FACT",
                "Reject",
                "missing",
                str(data_trust_path),
                [data_trust_path],
                "Data Trust audit is missing.",
                "先运行 `python3 -m src.cli data-trust-audit --date YYYY-MM-DD`。",
            )
        ]
    checks.append(
        _check(
            "data_trust_artifact_exists",
            "data_trust",
            "pass",
            "P2",
            "FACT",
            "Actionable",
            "exists",
            str(data_trust_path),
            [data_trust_path],
            "",
            "继续检查 Data Trust 内部一致性。",
        )
    )
    if not isinstance(data_trust, dict):
        checks.append(
            _check(
                "data_trust_json_parse",
                "data_trust",
                "fail",
                "P0",
                "FACT",
                "Reject",
                type(data_trust).__name__,
                "JSON object",
                [data_trust_path],
                "Data Trust JSON root is invalid.",
                "重新生成 Data Trust 审计。",
            )
        )
        return checks
    records = data_trust.get("records") if isinstance(data_trust.get("records"), list) else []
    record_count = int(data_trust.get("record_count") or 0)
    checks.append(
        _boolean_check(
            "data_trust_record_count",
            "data_trust",
            len(records) == record_count,
            "P0",
            "FACT",
            "Actionable",
            f"records={len(records)}",
            f"record_count={record_count}",
            [data_trust_path],
            "Data Trust record_count does not match records length.",
            "重新生成 Data Trust 审计，避免下游按错误行数判断。",
        )
    )
    expected_counts = Counter(str(row.get("data_trust_status", "")) for row in records)
    observed_counts = data_trust.get("status_counts") if isinstance(data_trust.get("status_counts"), dict) else {}
    checks.append(
        _boolean_check(
            "data_trust_status_counts",
            "data_trust",
            dict(sorted(expected_counts.items())) == observed_counts,
            "P0",
            "FACT",
            "Actionable",
            str(observed_counts),
            str(dict(sorted(expected_counts.items()))),
            [data_trust_path],
            "Data Trust status_counts does not match record statuses.",
            "重新生成 Data Trust 审计或修复 status_counts。",
        )
    )
    outputs = data_trust.get("outputs") if isinstance(data_trust.get("outputs"), dict) else {}
    output_paths = [Path(str(path)) for path in outputs.values() if str(path).strip()]
    missing_outputs = [str(path) for path in output_paths if not path.exists()]
    checks.append(
        _boolean_check(
            "data_trust_outputs_exist",
            "data_trust",
            not missing_outputs and len(output_paths) >= 4,
            "P1",
            "FACT",
            "Actionable",
            f"missing={missing_outputs}",
            "json/csv/markdown/pdf exist",
            output_paths or [data_trust_path],
            "Data Trust output bundle is incomplete.",
            "重新运行 Data Trust 审计，补齐 JSON/CSV/Markdown/PDF。",
        )
    )
    csv_path = Path(str(outputs.get("csv", ""))) if outputs.get("csv") else data_trust_path.with_suffix(".csv")
    csv_rows = _csv_row_count(csv_path)
    checks.append(
        _boolean_check(
            "data_trust_csv_rows",
            "data_trust",
            csv_rows == len(records),
            "P1",
            "FACT",
            "Actionable",
            f"csv_rows={csv_rows}",
            f"records={len(records)}",
            [csv_path, data_trust_path],
            "Data Trust CSV row count differs from JSON records.",
            "重新生成 Data Trust 审计，保证机器读取一致。",
        )
    )
    rejected = [row for row in records if row.get("data_trust_status") == "REJECTED"]
    checks.append(
        _boolean_check(
            "data_trust_active_rejected",
            "data_trust",
            not rejected,
            "P0",
            "FACT",
            "Reject" if rejected else "Actionable",
            f"rejected={len(rejected)}",
            "rejected=0",
            [Path(str(row.get("source_path", ""))) for row in rejected] or [data_trust_path],
            "Data Trust contains active REJECTED evidence.",
            "先处理 REJECTED 文件；处理前相关报告只能作为观察，不能支撑可执行动作。",
        )
    )
    review = [row for row in records if row.get("data_trust_status") == "NEEDS_REVIEW"]
    checks.append(
        _check(
            "data_trust_review_queue",
            "data_trust",
            "warn" if review else "pass",
            "P1" if review else "P2",
            "OBSERVATION" if review else "FACT",
            "Watch" if review else "Actionable",
            f"needs_review={len(review)}",
            "needs_review=0",
            [data_trust_path],
            "Data Trust contains evidence that needs manual review." if review else "",
            "进入 Manual Review Queue 层处理候选、弱验证、fallback 和账户确认问题。" if review else "无需额外复核队列。",
        )
    )
    stale_hashes = _data_trust_hash_mismatches(records)
    checks.append(
        _boolean_check(
            "data_trust_source_hashes",
            "data_trust",
            not stale_hashes,
            "P1",
            "FACT",
            "Watch" if stale_hashes else "Actionable",
            f"mismatch={len(stale_hashes)}",
            "mismatch=0",
            [Path(item["source_path"]) for item in stale_hashes[:20]] or [data_trust_path],
            "Some source files changed after Data Trust audit.",
            "重新生成 Data Trust 和 Reconciliation 审计，避免依据过期 hash。",
        )
    )
    return checks


def _source_log_checks(root: Path, reports_home: Path, data_trust: Any) -> list[ReconciliationCheck]:
    source_logs = sorted((root / "data" / "report_artifacts").glob("**/_source_logs/*.json"))
    data_records = data_trust.get("records", []) if isinstance(data_trust, dict) else []
    report_source_records = [row for row in data_records if row.get("source_type") == "report_source_log"]
    checks = [
        _boolean_check(
            "source_log_record_coverage",
            "report_chain",
            len(source_logs) == len(report_source_records),
            "P1",
            "FACT",
            "Actionable",
            f"source_logs={len(source_logs)}; data_trust_source_logs={len(report_source_records)}",
            "counts equal",
            [root / "data" / "report_artifacts"],
            "Data Trust source-log coverage does not match real source logs.",
            "重新生成 Data Trust，确保 source log 全部进入审计。",
        )
    ]
    missing_markdown: list[Path] = []
    missing_pdf: list[Path] = []
    invalid_source_logs: list[Path] = []
    for path in source_logs:
        payload = _load_json(path, {})
        if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list) or not payload.get("sources"):
            invalid_source_logs.append(path)
        report_name = str(payload.get("report_name") or path.name.replace("_sources.json", "")) if isinstance(payload, dict) else path.stem
        markdown = path.parent.parent / "_markdown" / f"{report_name}.md"
        pdf = _pdf_path_for_report(report_name, reports_home)
        if not markdown.exists():
            missing_markdown.append(markdown)
        if not pdf.exists():
            missing_pdf.append(pdf)
    checks.append(
        _boolean_check(
            "source_logs_are_valid",
            "report_chain",
            not invalid_source_logs,
            "P1",
            "FACT",
            "Watch" if invalid_source_logs else "Actionable",
            f"invalid={len(invalid_source_logs)}",
            "invalid=0",
            invalid_source_logs or source_logs[:5],
            "Some source logs are empty or malformed.",
            "修复 source log 必填字段；正式报告不得依赖缺字段来源。",
        )
    )
    checks.append(
        _boolean_check(
            "source_log_markdown_pairing",
            "report_chain",
            not missing_markdown,
            "P1",
            "FACT",
            "Actionable",
            f"missing_markdown={len(missing_markdown)}",
            "missing_markdown=0",
            missing_markdown or source_logs[:5],
            "Some source logs do not have matching Markdown artifacts.",
            "补齐内部 Markdown，保证 PDF 可追溯到源文稿。",
        )
    )
    checks.append(
        _boolean_check(
            "source_log_pdf_pairing",
            "report_chain",
            not missing_pdf,
            "P1",
            "FACT",
            "Actionable",
            f"missing_pdf={len(missing_pdf)}",
            "missing_pdf=0",
            missing_pdf or source_logs[:5],
            "Some source logs do not have matching formal PDFs.",
            "补齐正式 PDF；PDF 缺失时不能作为正式交付证据。",
        )
    )
    return checks


def _bridge_checks(root: Path) -> list[ReconciliationCheck]:
    checks: list[ReconciliationCheck] = []
    bridge_dir = root / "data" / "report_artifacts" / "research_bus_bridge"
    expected_bridge_files = [
        "ConsumerBehaviorStateFromBus.json",
        "HoldingSymbolMappingsFromBus.json",
        "HoldingUpdateCandidatesFromBus.json",
        "HoldingsMasterFromBus.json",
        "IndependentValidationRunsFromBus.json",
        "PortfolioTransactionsFromBus.json",
        "PFIOSResultsFromBus.json",
        "ValidationTasksFromBus.json",
    ]
    missing = [bridge_dir / name for name in expected_bridge_files if not (bridge_dir / name).exists()]
    checks.append(
        _boolean_check(
            "research_bus_bridge_files",
            "research_bus",
            not missing,
            "P1",
            "FACT",
            "Actionable",
            f"missing={len(missing)}",
            "missing=0",
            missing or [bridge_dir],
            "ResearchBus bridge export set is incomplete.",
            "运行 `python3 -m src.cli research-bus-sync --json` 后再使用跨系统数据。",
        )
    )
    invalid_schema = []
    for path in sorted(bridge_dir.glob("*.json")):
        payload = _load_json(path, {})
        if isinstance(payload, dict) and payload.get("schema") and payload.get("schema") != "ResearchBusV1":
            invalid_schema.append(path)
    checks.append(
        _boolean_check(
            "research_bus_bridge_schema",
            "research_bus",
            not invalid_schema,
            "P1",
            "FACT",
            "Actionable",
            f"invalid_schema={len(invalid_schema)}",
            "schema=ResearchBusV1",
            invalid_schema or [bridge_dir],
            "ResearchBus bridge schema mismatch.",
            "同步 PFIOS ResearchBus schema 后重新拉取。",
        )
    )
    pfi_os_path = root / "data" / "report_artifacts" / "pfi_os_bridge" / "PFIOSResults.json"
    pfi_os = _load_json(pfi_os_path, {})
    results = pfi_os.get("results") if isinstance(pfi_os, dict) and isinstance(pfi_os.get("results"), list) else []
    weak = [
        row
        for row in results
        if str(row.get("research_status", "")).lower() in {"needsmoreevidence", "dataqualityreview", "donotuse"}
        or str(row.get("status", "")).lower() in {"review", "blocked", "block"}
    ]
    checks.append(
        _check(
            "pfi_os_bridge_research_gate",
            "pfi_os_bridge",
            "warn" if weak else "pass",
            "P1" if weak else "P2",
            "OBSERVATION" if weak else "FACT",
            "Watch" if weak else "Actionable",
            f"weak_rows={len(weak)}; total={len(results)}",
            "weak_rows=0",
            [pfi_os_path],
            "PFIOS bridge contains Review/NeedsMoreEvidence rows." if weak else "",
            "报告中读取这些结果时必须降级为观察或待验证。" if weak else "PFIOS bridge 当前无弱证据状态。",
        )
    )
    policy_status_dir = root / "data" / "report_artifacts" / "policy_bridge" / "status"
    policy_event_dir = root / "data" / "report_artifacts" / "policy_bridge" / "events"
    policy_issues = []
    for status_path in sorted(policy_status_dir.glob("policy_bridge_status_*.json")):
        payload = _load_json(status_path, {})
        date_suffix = status_path.stem.replace("policy_bridge_status_", "")
        if isinstance(payload, dict) and int(payload.get("matched_event_count") or 0) > 0:
            event_path = policy_event_dir / f"policy_events_{date_suffix}.csv"
            if not event_path.exists():
                policy_issues.append(event_path)
    checks.append(
        _boolean_check(
            "policy_bridge_status_event_pairing",
            "policy_bridge",
            not policy_issues,
            "P1",
            "FACT",
            "Watch" if policy_issues else "Actionable",
            f"missing_event_files={len(policy_issues)}",
            "missing_event_files=0",
            policy_issues or [policy_status_dir],
            "Policy bridge status references matched events without event CSV.",
            "补齐 policy events CSV；缺失时政策催化只能作为背景。",
        )
    )
    return checks


def _automation_health_checks(root: Path, as_of: str) -> list[ReconciliationCheck]:
    logs = sorted((root / "data" / "report_artifacts" / "automation_logs").glob(f"automation_health_{as_of}*.json"))
    if not logs:
        return [
            _check(
                "automation_health_current_date",
                "automation",
                "warn",
                "P1",
                "OBSERVATION",
                "Watch",
                "missing",
                f"automation_health_{as_of}*.json",
                [root / "data" / "report_artifacts" / "automation_logs"],
                "No automation health file for audit date.",
                "运行 automation-health 或在报告中标记运行健康未知。",
            )
        ]
    failed = []
    warned = []
    for path in logs:
        payload = _load_json(path, {})
        status = str(payload.get("status", "")).lower() if isinstance(payload, dict) else ""
        if status == "fail":
            failed.append(path)
        elif status == "warn":
            warned.append(path)
    if failed:
        status = "fail"
        issue = "Current-date automation health has failures."
        next_action = "先处理失败健康检查，处理前相关报告不能支撑可执行交易动作。"
        paths = failed
        decision = "Reject"
    elif warned:
        status = "warn"
        issue = "Current-date automation health has warnings."
        next_action = "将相关结论降级为观察，优先处理行情覆盖、账户更新或报告缺口。"
        paths = warned
        decision = "Watch"
    else:
        status = "pass"
        issue = ""
        next_action = "自动化健康检查当前无 fail/warn。"
        paths = logs
        decision = "Actionable"
    return [
        _check(
            "automation_health_current_date",
            "automation",
            status,
            "P0" if failed else "P1" if warned else "P2",
            "FACT" if status == "pass" else "OBSERVATION",
            decision,
            f"fail={len(failed)}; warn={len(warned)}; files={len(logs)}",
            "fail=0; warn=0",
            paths,
            issue,
            next_action,
        )
    ]


def _handoff_checks(root: Path, as_of: str) -> list[ReconciliationCheck]:
    handoff = root / "HANDOFF.md"
    readme = root / "README.md"
    agents = root / "AGENTS.md"
    checks = [
        _boolean_check(
            "handoff_exists",
            "workflow",
            handoff.exists(),
            "P1",
            "FACT",
            "Actionable",
            "exists" if handoff.exists() else "missing",
            "exists",
            [handoff],
            "HANDOFF.md is missing.",
            "补齐 HANDOFF，降低跨 Run 上下文成本。",
        )
    ]
    handoff_text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""
    checks.append(
        _boolean_check(
            "handoff_mentions_data_trust",
            "workflow",
            f"data_trust_audit_{as_of}" in handoff_text and "Data Trust Layer v1" in handoff_text,
            "P2",
            "FACT",
            "Observe",
            "mentioned" if f"data_trust_audit_{as_of}" in handoff_text else "not mentioned",
            f"data_trust_audit_{as_of}",
            [handoff],
            "HANDOFF does not mention latest Data Trust audit.",
            "更新 HANDOFF，确保新聊天能恢复最新数据可信度状态。",
        )
    )
    readme_text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    checks.append(
        _boolean_check(
            "readme_mentions_data_trust_command",
            "workflow",
            "data-trust-audit" in readme_text,
            "P2",
            "FACT",
            "Observe",
            "present" if "data-trust-audit" in readme_text else "missing",
            "data-trust-audit command documented",
            [readme],
            "README does not document Data Trust command.",
            "更新 README 的固定入口说明。",
        )
    )
    checks.append(
        _check(
            "agents_exists",
            "workflow",
            "pass" if agents.exists() else "warn",
            "P2",
            "FACT",
            "Observe",
            "exists" if agents.exists() else "missing",
            "exists",
            [agents],
            "AGENTS.md is not present yet." if not agents.exists() else "",
            "留到 Codex Workflow Layer v1 补齐项目级 AGENTS.md。" if not agents.exists() else "无需处理。",
        )
    )
    return checks


def _data_trust_hash_mismatches(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mismatches = []
    for row in records:
        path = Path(str(row.get("source_path", "")))
        expected = str(row.get("sha256", ""))
        if not path.exists() or not expected:
            continue
        if _sha256(path) != expected:
            mismatches.append(row)
    return mismatches


def _pdf_path_for_report(report_name: str, reports_home: Path) -> Path:
    from src.reporting.paths import report_dir_for_name

    return report_dir_for_name(report_name).joinpath(f"{report_name}.pdf") if reports_home == REPORTS_HOME else _fallback_pdf_path(report_name, reports_home)


def _fallback_pdf_path(report_name: str, reports_home: Path) -> Path:
    from src.reporting.paths import _date_from_report_name

    day = _date_from_report_name(report_name)
    monday = day.fromordinal(day.toordinal() - day.weekday())
    sunday = monday.fromordinal(monday.toordinal() + 6)
    week_of_month = (monday.day - 1) // 7 + 1
    return reports_home / f"{monday.month}月第{week_of_month}周 {monday:%d%m}-{sunday:%d%m}" / f"{report_name}.pdf"


def _boolean_check(
    check_name: str,
    domain: str,
    passed: bool,
    severity: str,
    evidence: str,
    decision: str,
    observed: str,
    expected: str,
    paths: list[Path],
    issue: str,
    next_action: str,
) -> ReconciliationCheck:
    return _check(
        check_name,
        domain,
        "pass" if passed else "fail",
        severity,
        evidence,
        decision if passed else ("Reject" if severity == "P0" else "Watch"),
        observed,
        expected,
        paths,
        "" if passed else issue,
        "无需处理。" if passed else next_action,
    )


def _check(
    check_name: str,
    domain: str,
    status: str,
    severity: str,
    evidence: str,
    decision: str,
    observed: str,
    expected: str,
    paths: list[Path],
    issue: str,
    next_action: str,
) -> ReconciliationCheck:
    return ReconciliationCheck(
        check_id=_stable_id(domain, check_name, observed, expected),
        domain=domain,
        check_name=check_name,
        status=status,
        severity=severity,
        evidence_classification=evidence,
        decision_grade=decision,
        observed=observed,
        expected=expected,
        source_paths="; ".join(str(path) for path in paths if str(path)),
        issue=issue,
        next_action=next_action,
    )


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _csv_row_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    except Exception:
        return -1


def _write_checks_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _audit_markdown(audit: dict[str, Any]) -> str:
    checks = list(audit["checks"])
    problem_rows = [row for row in checks if row["status"] in {"fail", "warn"}]
    lines = [
        f"# AI-Research-System Reconciliation Audit {audit['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {audit['system']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Checks: {audit['check_count']}",
        "",
        "## Status Summary",
        _markdown_table([{"status": key, "count": value} for key, value in audit["status_counts"].items()], ["status", "count"]),
        "",
        "## Severity Summary",
        _markdown_table([{"severity": key, "count": value} for key, value in audit["severity_counts"].items()], ["severity", "count"]),
        "",
        "## Problems",
        _markdown_table(problem_rows, ["domain", "check_name", "status", "severity", "observed", "expected", "issue", "next_action"]),
        "",
        "## All Checks",
        _markdown_table(checks, ["domain", "check_name", "status", "severity", "decision_grade", "observed", "expected"]),
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
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"reconciliation_{digest}"


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
