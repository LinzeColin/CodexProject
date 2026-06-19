from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


DATA_TRUST_STATUSES = {
    "RAW_IMPORTED",
    "PARSED_CANDIDATE",
    "NEEDS_REVIEW",
    "USER_CONFIRMED",
    "RECONCILED",
    "ARCHIVED",
    "REJECTED",
}


@dataclass(frozen=True)
class DataTrustRecord:
    record_id: str
    source_group: str
    source_path: str
    source_type: str
    trust_status: str
    evidence_classification: str
    decision_grade: str
    issue: str
    next_action: str
    user_confirmation_required: bool
    observed_at: str
    content_hash: str

    def to_row(self) -> dict[str, object]:
        return asdict(self)


def build_data_trust_audit(
    *,
    source_db: str | Path = "data/source_registry.sqlite",
    content_db: str | Path = "data/policy_documents.sqlite",
    root: str | Path = ".",
    report_dir: str | Path = "reports",
    as_of: str | None = None,
    max_report_files: int = 80,
) -> dict[str, Any]:
    project_root = Path(root)
    generated_as_of = as_of or datetime.now().date().isoformat()
    observed_at = datetime.now().isoformat(timespec="seconds")
    records: list[DataTrustRecord] = []
    records.extend(_control_file_records(project_root, observed_at))
    records.extend(_config_file_records(project_root, observed_at))
    records.extend(_source_database_records(project_root / source_db, project_root, observed_at))
    records.extend(_content_database_records(project_root / content_db, project_root, observed_at))
    records.extend(_report_file_records(project_root / report_dir, project_root, observed_at, max_report_files=max_report_files))

    status_counts = Counter(record.trust_status for record in records)
    evidence_counts = Counter(record.evidence_classification for record in records)
    decision_counts = Counter(record.decision_grade for record in records)
    rejected_count = status_counts.get("REJECTED", 0)
    review_count = status_counts.get("NEEDS_REVIEW", 0)
    audit_status = "Blocked" if rejected_count else "Review" if review_count else "Pass"
    payload = {
        "schema": "PolicyDataTrustAuditV1",
        "system": "source-authority-registry",
        "as_of": generated_as_of,
        "run_id": _stable_hash("policyDataTrust", generated_as_of, str(project_root.resolve())),
        "generated_at": observed_at,
        "audit_status": audit_status,
        "record_count": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "review_count": int(review_count),
        "rejected_count": int(rejected_count),
        "assumptions": [
            "This audit is local and read-only except for writing its own audit bundle.",
            "It does not run policy crawlers, call search APIs, validate cookies, or refresh external platforms.",
            "Missing API keys, missing platform authorization, pending gaps, and failed runs are downgraded instead of silently promoted.",
            "Actionable means usable inside the policy evidence chain; it is not investment, trading, or execution approval.",
        ],
        "records": [record.to_row() for record in records],
    }
    return payload


def write_data_trust_audit(
    *,
    source_db: str | Path = "data/source_registry.sqlite",
    content_db: str | Path = "data/policy_documents.sqlite",
    root: str | Path = ".",
    report_dir: str | Path = "reports",
    output_dir: str | Path = "reports/system_audit",
    as_of: str | None = None,
) -> dict[str, Any]:
    audit = build_data_trust_audit(
        source_db=source_db,
        content_db=content_db,
        root=root,
        report_dir=report_dir,
        as_of=as_of,
    )
    target = Path(root) / output_dir
    target.mkdir(parents=True, exist_ok=True)
    stamp = str(audit["as_of"])
    stem = f"data_trust_audit_{stamp}"
    json_path = target / f"{stem}.json"
    csv_path = target / f"{stem}.csv"
    markdown_path = target / f"{stem}.md"
    pdf_path = target / f"{stem}.pdf"
    _write_json(json_path, audit)
    _write_csv(csv_path, audit["records"])
    markdown_path.write_text(_render_markdown(audit), encoding="utf-8")
    _write_pdf(pdf_path, audit)
    audit["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
    }
    _write_json(json_path, audit)
    return audit


def _control_file_records(root: Path, observed_at: str) -> list[DataTrustRecord]:
    return [
        _file_record(root / "AGENTS.md", root, "Project Control", "agent_instructions", observed_at, "项目级 AGENTS.md 存在。", "若缺失，使用上层/全局规则，并在交接中记录缺口。"),
        _file_record(root / "HANDOFF.md", root, "Project Control", "handoff", observed_at, "交接文件存在。", "每轮开始按 HANDOFF 与当前文件交叉核验。"),
        _file_record(root / "PLANS.md", root, "Project Control", "plan", observed_at, "项目级 PLANS.md 存在。", "若缺失，以 HANDOFF、README、CLI 和测试作为当前事实来源。"),
        _file_record(root / "CODEX_TASK_PACK.md", root, "Project Control", "task_pack", observed_at, "项目级 CODEX_TASK_PACK.md 存在。", "若缺失，避免假设任务包内容，按当前 Run Contract 小步推进。"),
        _file_record(root / "CODEX_PROMPTS.md", root, "Project Control", "prompt_registry", observed_at, "项目级 CODEX_PROMPTS.md 存在。", "若缺失，不引用不存在的 prompt 规则。"),
        _file_record(root / "README.md", root, "Project Control", "documentation", observed_at, "README 存在。", "保持数据可信度和证据边界同步到 README。"),
        _file_record(root / "pyproject.toml", root, "Project Control", "config", observed_at, "Python 项目配置存在。", "继续通过固定 CLI 和测试入口验证。"),
    ]


def _config_file_records(root: Path, observed_at: str) -> list[DataTrustRecord]:
    records: list[DataTrustRecord] = []
    for rel_path in [
        "config/seed_sources.json",
        "config/interpretation_sources.json",
        "config/platform_parsers.json",
        "rules/quality_gates.json",
        "scripts/run_policy_report.sh",
    ]:
        path = root / rel_path
        records.append(_file_record(path, root, "Policy Config", path.suffix.lstrip(".") or "file", observed_at, "关键配置或脚本存在。", "配置只作为候选能力证据；真实运行仍看 readiness 和质量门禁。"))
    return records


def _source_database_records(path: Path, root: Path, observed_at: str) -> list[DataTrustRecord]:
    records = [_database_file_record(path, root, "Source Registry DB", observed_at)]
    if not path.exists():
        return records
    conn = _connect_existing(path)
    try:
        records.extend(_source_rows(conn, root, path, observed_at))
    finally:
        conn.close()
    return records


def _content_database_records(path: Path, root: Path, observed_at: str) -> list[DataTrustRecord]:
    records = [_database_file_record(path, root, "Policy Content DB", observed_at)]
    if not path.exists():
        return records
    conn = _connect_existing(path)
    try:
        records.extend(_pipeline_run_rows(conn, root, path, observed_at))
        records.extend(_document_rows(conn, root, path, observed_at))
        records.extend(_analysis_rows(conn, root, path, observed_at))
        records.extend(_interpretation_rows(conn, root, path, observed_at))
        records.extend(_gap_rows(conn, root, path, observed_at))
        records.extend(_report_queue_rows(conn, root, path, observed_at))
    finally:
        conn.close()
    return records


def _source_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "sources"):
        return [_db_issue_record(root, db_path, "sources", "REJECTED", "sources 表缺失。", "先修复 source_registry.sqlite schema。", observed_at)]
    query = """
        SELECT
            s.source_id,
            s.name,
            s.review_status,
            s.status,
            s.crawl_enabled,
            COALESCE(a.final_score, a.system_score) AS effective_score,
            COALESCE(a.tier_final, a.tier_system) AS effective_tier
        FROM sources s
        LEFT JOIN authority_scores a ON a.source_id = s.source_id AND a.active = 1
        ORDER BY s.source_id
    """
    rows = _safe_query(conn, query)
    records: list[DataTrustRecord] = []
    for row in rows:
        review = str(row.get("review_status") or "")
        status = str(row.get("status") or "")
        trust = _source_trust_status(review, status)
        records.append(
            _row_record(
                root,
                db_path,
                "Source Authority",
                f"sources:{row.get('source_id')}",
                "sqlite_row",
                trust,
                "FACT",
                _decision_for_status(trust),
                f"政策来源 {row.get('name')} review={review} status={status} tier={row.get('effective_tier') or 'unknown'} score={row.get('effective_score') or 'missing'}。",
                "未人工确认或被拒绝的来源不得升级为高置信原始政策证据。",
                observed_at,
                user_confirmation_required=trust in {"NEEDS_REVIEW", "RAW_IMPORTED"},
            )
        )
    return records or [_db_issue_record(root, db_path, "sources", "NEEDS_REVIEW", "sources 表为空。", "导入或确认政策来源后再用于抓取。", observed_at)]


def _pipeline_run_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "pipeline_runs"):
        return [_db_issue_record(root, db_path, "pipeline_runs", "NEEDS_REVIEW", "pipeline_runs 表缺失。", "初始化 content DB 后再审计运行记录。", observed_at)]
    rows = _safe_query(
        conn,
        """
        SELECT run_id, status, mode, report_path, error_summary, completed_at
        FROM pipeline_runs
        ORDER BY started_at DESC
        LIMIT 120
        """,
    )
    records: list[DataTrustRecord] = []
    for row in rows:
        run_status = str(row.get("status") or "")
        trust = "RECONCILED" if run_status == "completed" else "REJECTED" if run_status == "failed" else "NEEDS_REVIEW"
        records.append(
            _row_record(
                root,
                db_path,
                "Pipeline Runs",
                f"pipeline_runs:{row.get('run_id')}",
                "sqlite_row",
                trust,
                "FACT",
                _decision_for_status(trust),
                f"运行 {row.get('run_id')} status={run_status} report={row.get('report_path') or 'none'} error={row.get('error_summary') or ''}",
                "失败或运行中记录必须进入复核，不得作为已完成政策证据。",
                observed_at,
                user_confirmation_required=trust != "RECONCILED",
            )
        )
    return records


def _document_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "documents"):
        return [_db_issue_record(root, db_path, "documents", "NEEDS_REVIEW", "documents 表缺失。", "运行抓取或初始化内容库。", observed_at)]
    rows = _safe_query(
        conn,
        """
        SELECT document_id, title, source_name, status, content_hash, snapshot_path, published_date
        FROM documents
        ORDER BY updated_at DESC
        LIMIT 200
        """,
    )
    records: list[DataTrustRecord] = []
    for row in rows:
        status = str(row.get("status") or "")
        if status == "failed":
            trust = "REJECTED"
        elif status == "analyzed":
            trust = "RECONCILED"
        elif status == "fetched":
            trust = "PARSED_CANDIDATE"
        else:
            trust = "RAW_IMPORTED"
        records.append(
            _row_record(
                root,
                db_path,
                "Policy Documents",
                f"documents:{row.get('document_id')}",
                "sqlite_row",
                trust,
                "FACT" if trust in {"RECONCILED", "REJECTED"} else "OBSERVATION",
                _decision_for_status(trust),
                f"政策文件《{row.get('title')}》source={row.get('source_name')} status={status} published={row.get('published_date') or 'unknown'}。",
                "discovered/fetched 文件只代表线索或候选，必须有原文、hash、分析和质量门禁才能提升。",
                observed_at,
                user_confirmation_required=trust in {"RAW_IMPORTED", "PARSED_CANDIDATE"},
            )
        )
    return records


def _analysis_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "analyses"):
        return []
    rows = _safe_query(
        conn,
        """
        SELECT analysis_id, document_id, analysis_mode, importance_score, created_at
        FROM analyses
        ORDER BY created_at DESC
        LIMIT 200
        """,
    )
    return [
        _row_record(
            root,
            db_path,
            "Policy Analyses",
            f"analyses:{row.get('analysis_id')}",
            "sqlite_row",
            "PARSED_CANDIDATE",
            "INFERENCE",
            "Watch",
            f"政策分析 document={row.get('document_id')} mode={row.get('analysis_mode')} importance={row.get('importance_score')}。",
            "自动分析是推断证据；必须结合原文、source log、外部参考和质量门禁。",
            observed_at,
        )
        for row in rows
    ]


def _interpretation_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "interpretation_items"):
        return []
    rows = _safe_query(
        conn,
        """
        SELECT item_id, platform, title, evidence_status, relevance_score, url
        FROM interpretation_items
        ORDER BY created_at DESC
        LIMIT 200
        """,
    )
    records: list[DataTrustRecord] = []
    for row in rows:
        evidence_status = str(row.get("evidence_status") or "")
        trust = _interpretation_trust_status(evidence_status)
        records.append(
            _row_record(
                root,
                db_path,
                "External Interpretation",
                f"interpretation_items:{row.get('item_id')}",
                "sqlite_row",
                trust,
                "OBSERVATION" if trust != "RECONCILED" else "FACT",
                _decision_for_status(trust),
                f"{row.get('platform')} 外部解读《{row.get('title')}》 evidence_status={evidence_status} relevance={row.get('relevance_score')}。",
                "外部解读只可作为辅助证据；授权缺失、CAPTCHA、登陆拦截和 landing 页不得提升为事实结论。",
                observed_at,
                user_confirmation_required=trust in {"NEEDS_REVIEW", "RAW_IMPORTED"},
            )
        )
    return records


def _gap_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "external_reference_gaps"):
        return []
    rows = _safe_query(
        conn,
        """
        SELECT gap_id, platform, gap_type, title, status, required_action
        FROM external_reference_gaps
        ORDER BY priority_score DESC, updated_at DESC
        LIMIT 200
        """,
    )
    records: list[DataTrustRecord] = []
    for row in rows:
        status = str(row.get("status") or "")
        trust = "NEEDS_REVIEW" if status == "pending" else "USER_CONFIRMED" if status == "resolved" else "ARCHIVED"
        records.append(
            _row_record(
                root,
                db_path,
                "Reference Gaps",
                f"external_reference_gaps:{row.get('gap_id')}",
                "sqlite_row",
                trust,
                "OBSERVATION",
                _decision_for_status(trust),
                f"{row.get('platform')} gap={row.get('gap_type')} status={status} title={row.get('title')}",
                str(row.get("required_action") or "补齐外部参考或保留缺口说明。"),
                observed_at,
                user_confirmation_required=status == "pending",
            )
        )
    return records


def _report_queue_rows(conn: sqlite3.Connection, root: Path, db_path: Path, observed_at: str) -> list[DataTrustRecord]:
    if not _table_exists(conn, "report_queue"):
        return []
    rows = _safe_query(
        conn,
        """
        SELECT document_id, analysis_mode, status, generated_report_path, updated_at
        FROM report_queue
        ORDER BY updated_at DESC
        LIMIT 120
        """,
    )
    records: list[DataTrustRecord] = []
    for row in rows:
        status = str(row.get("status") or "")
        trust = "RECONCILED" if status == "generated" else "ARCHIVED" if status == "skipped" else "PARSED_CANDIDATE"
        records.append(
            _row_record(
                root,
                db_path,
                "Report Queue",
                f"report_queue:{row.get('document_id')}:{row.get('analysis_mode')}",
                "sqlite_row",
                trust,
                "FACT" if trust == "RECONCILED" else "OBSERVATION",
                _decision_for_status(trust),
                f"报告队列 document={row.get('document_id')} status={status} report={row.get('generated_report_path') or 'none'}。",
                "pending 队列只代表待生产任务，不代表正式报告证据。",
                observed_at,
            )
        )
    return records


def _report_file_records(report_dir: Path, root: Path, observed_at: str, *, max_report_files: int) -> list[DataTrustRecord]:
    if not report_dir.exists():
        return [_path_record(root, report_dir, "Report Files", "directory", "NEEDS_REVIEW", "FACT", "Watch", "报告目录缺失。", "生成政策报告或确认报告路径。", observed_at)]
    files = [
        path
        for path in report_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".md", ".html", ".json", ".csv"}
    ]
    files = sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)[:max_report_files]
    records = []
    for path in files:
        trust = "RECONCILED" if path.suffix.lower() in {".pdf", ".md", ".html"} else "PARSED_CANDIDATE"
        records.append(_path_record(root, path, "Report Files", path.suffix.lstrip(".").lower(), trust, "FACT", _decision_for_status(trust), "报告或审计产物已索引。", "报告结论需引用原文、来源权威、外部参考和质量门禁。", observed_at))
    return records or [_path_record(root, report_dir, "Report Files", "directory", "NEEDS_REVIEW", "FACT", "Watch", "报告目录为空。", "运行报告生成或确认输出目录。", observed_at)]


def _database_file_record(path: Path, root: Path, group: str, observed_at: str) -> DataTrustRecord:
    if not path.exists():
        return _path_record(root, path, group, "sqlite", "NEEDS_REVIEW", "FACT", "Watch", "数据库文件缺失。", "初始化数据库或确认路径。", observed_at, user_confirmation_required=True)
    if path.stat().st_size <= 0:
        return _path_record(root, path, group, "sqlite", "NEEDS_REVIEW", "FACT", "Watch", "数据库文件为空。", "重新初始化或检查写入流程。", observed_at, user_confirmation_required=True)
    return _path_record(root, path, group, "sqlite", "RECONCILED", "FACT", "Actionable", "数据库文件存在且非空。", "继续按表级记录审计来源可信度。", observed_at)


def _file_record(path: Path, root: Path, group: str, source_type: str, observed_at: str, issue: str, next_action: str) -> DataTrustRecord:
    status = "RECONCILED" if path.exists() and path.stat().st_size > 0 else "NEEDS_REVIEW"
    return _path_record(root, path, group, source_type, status, "FACT", _decision_for_status(status), issue if status == "RECONCILED" else f"{path.name} 缺失或为空。", next_action, observed_at, user_confirmation_required=status == "NEEDS_REVIEW")


def _db_issue_record(root: Path, db_path: Path, table: str, status: str, issue: str, next_action: str, observed_at: str) -> DataTrustRecord:
    return _row_record(root, db_path, "Database Schema", f"schema:{table}", "sqlite_schema", status, "FACT", _decision_for_status(status), issue, next_action, observed_at, user_confirmation_required=status in {"NEEDS_REVIEW", "REJECTED"})


def _path_record(
    root: Path,
    path: Path,
    group: str,
    source_type: str,
    trust_status: str,
    evidence_classification: str,
    decision_grade: str,
    issue: str,
    next_action: str,
    observed_at: str,
    *,
    user_confirmation_required: bool = False,
) -> DataTrustRecord:
    source_path = _relative(path, root)
    content_hash = _file_hash(path) if path.exists() and path.is_file() else _stable_hash(str(path), trust_status, issue)
    return DataTrustRecord(
        record_id=_stable_hash("policyDataTrustRecord", source_path, trust_status, content_hash),
        source_group=group,
        source_path=source_path,
        source_type=source_type,
        trust_status=trust_status,
        evidence_classification=evidence_classification,
        decision_grade=decision_grade,
        issue=issue,
        next_action=next_action,
        user_confirmation_required=user_confirmation_required,
        observed_at=observed_at,
        content_hash=content_hash,
    )


def _row_record(
    root: Path,
    db_path: Path,
    group: str,
    key: str,
    source_type: str,
    trust_status: str,
    evidence_classification: str,
    decision_grade: str,
    issue: str,
    next_action: str,
    observed_at: str,
    *,
    user_confirmation_required: bool = False,
) -> DataTrustRecord:
    source_path = f"{_relative(db_path, root)}#{key}"
    content_hash = _stable_hash(source_path, trust_status, issue, next_action)
    return DataTrustRecord(
        record_id=_stable_hash("policyDataTrustRecord", source_path, content_hash),
        source_group=group,
        source_path=source_path,
        source_type=source_type,
        trust_status=trust_status,
        evidence_classification=evidence_classification,
        decision_grade=decision_grade,
        issue=issue,
        next_action=next_action,
        user_confirmation_required=user_confirmation_required,
        observed_at=observed_at,
        content_hash=content_hash,
    )


def _source_trust_status(review_status: str, status: str) -> str:
    if status == "rejected" or review_status == "rejected":
        return "REJECTED"
    if review_status == "user_confirmed" and status == "active":
        return "USER_CONFIRMED"
    if review_status == "needs_review":
        return "NEEDS_REVIEW"
    if review_status == "system_scored":
        return "PARSED_CANDIDATE"
    return "RAW_IMPORTED"


def _interpretation_trust_status(evidence_status: str) -> str:
    lowered = evidence_status.lower()
    if any(token in lowered for token in ["blocked", "captcha", "login", "auth", "failed", "error"]):
        return "NEEDS_REVIEW"
    if any(token in lowered for token in ["article", "excerpt", "parsed", "enriched"]):
        return "RECONCILED"
    if "landing" in lowered or "search" in lowered:
        return "RAW_IMPORTED"
    return "PARSED_CANDIDATE"


def _decision_for_status(status: str) -> str:
    if status == "REJECTED":
        return "Reject"
    if status in {"NEEDS_REVIEW", "PARSED_CANDIDATE", "RAW_IMPORTED"}:
        return "Watch"
    if status == "ARCHIVED":
        return "Observe"
    return "Actionable"


def _connect_existing(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?", (table,)).fetchone()
    return row is not None


def _safe_query(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    except sqlite3.Error:
        return []


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fieldnames = list(DataTrustRecord.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _render_markdown(audit: Mapping[str, Any]) -> str:
    lines = [
        f"# Policy Data Trust Audit {audit.get('as_of')}",
        "",
        f"- system: `{audit.get('system')}`",
        f"- run_id: `{audit.get('run_id')}`",
        f"- generated_at: `{audit.get('generated_at')}`",
        f"- audit_status: `{audit.get('audit_status')}`",
        f"- record_count: `{audit.get('record_count')}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in (audit.get("status_counts") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Key Review Items", ""])
    focus = [
        row
        for row in audit.get("records", [])
        if row.get("trust_status") in {"REJECTED", "NEEDS_REVIEW"}
    ][:30]
    if not focus:
        lines.append("- No rejected or review records.")
    for row in focus:
        lines.append(
            f"- `{row.get('trust_status')}` `{row.get('source_path')}`: {row.get('issue')} Next: {row.get('next_action')}"
        )
    lines.extend(["", "## Assumptions", ""])
    for item in audit.get("assumptions") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_pdf(path: Path, audit: Mapping[str, Any]) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("reportlab is required for PDF audit generation") from exc

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    base_font = "STSong-Light"
    styles.add(ParagraphStyle(name="PolicyTitle", parent=styles["Title"], fontName=base_font, fontSize=18, leading=24, textColor=colors.HexColor("#0a3f52"), wordWrap="CJK"))
    styles.add(ParagraphStyle(name="PolicyHeading", parent=styles["Heading2"], fontName=base_font, fontSize=13, leading=18, textColor=colors.HexColor("#0a3f52"), wordWrap="CJK"))
    styles.add(ParagraphStyle(name="PolicyBody", parent=styles["BodyText"], fontName=base_font, fontSize=9.2, leading=14, wordWrap="CJK"))
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    story: list[Any] = [
        Paragraph("政策系统数据可信度审计报告", styles["PolicyTitle"]),
        Paragraph(f"Run ID: {audit.get('run_id')}<br/>Generated: {audit.get('generated_at')}", styles["PolicyBody"]),
        Spacer(1, 8),
        Paragraph("一、审计摘要", styles["PolicyHeading"]),
    ]
    summary_rows = [
        ["指标", "结果"],
        ["系统", audit.get("system", "")],
        ["审计状态", audit.get("audit_status", "")],
        ["记录数", audit.get("record_count", 0)],
        ["需要复核", audit.get("review_count", 0)],
        ["拒绝/阻断", audit.get("rejected_count", 0)],
    ]
    story.append(_pdf_table(summary_rows, styles, colors))
    story.append(Spacer(1, 8))
    story.append(Paragraph("二、状态分布", styles["PolicyHeading"]))
    status_rows = [["状态", "数量"]] + [[key, value] for key, value in (audit.get("status_counts") or {}).items()]
    story.append(_pdf_table(status_rows, styles, colors))
    story.append(Spacer(1, 8))
    story.append(Paragraph("三、优先复核项目", styles["PolicyHeading"]))
    focus_rows = [["状态", "来源", "问题", "下一步"]]
    for row in [
        item for item in audit.get("records", []) if item.get("trust_status") in {"REJECTED", "NEEDS_REVIEW"}
    ][:12]:
        focus_rows.append([row.get("trust_status", ""), row.get("source_path", ""), row.get("issue", ""), row.get("next_action", "")])
    if len(focus_rows) == 1:
        focus_rows.append(["Pass", "全部", "无 REJECTED/NEEDS_REVIEW 项。", "继续按证据链生成报告。"])
    story.append(_pdf_table(focus_rows, styles, colors))
    story.append(Spacer(1, 8))
    story.append(Paragraph("四、边界和假设", styles["PolicyHeading"]))
    for item in audit.get("assumptions") or []:
        story.append(Paragraph(f"- {item}", styles["PolicyBody"]))
    doc.build(story)


def _pdf_table(rows: list[list[object]], styles: Mapping[str, Any], colors: Any) -> Any:
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    table_rows = [[Paragraph(str(cell), styles["PolicyBody"]) for cell in row] for row in rows]
    table = Table(table_rows, colWidths=[32 * mm, 120 * mm] if len(rows[0]) == 2 else [22 * mm, 40 * mm, 55 * mm, 45 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f0f3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0a3f52")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d4dc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
            ]
        )
    )
    return table


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _stable_hash(*values: object) -> str:
    payload = "|".join(str(value) for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
