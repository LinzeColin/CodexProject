from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "evidence_decision_matrix.v1"

MATRIX_FIELDS = [
    "evidence_id",
    "layer",
    "subject_type",
    "subject_id",
    "subject_name",
    "evidence_classification",
    "decision_grade",
    "status",
    "risk_level",
    "conclusion",
    "source_table",
    "evidence_path",
    "next_action",
    "generated_at",
    "schema_version",
]

SUMMARY_FIELDS = [
    "layer",
    "evidence_classification",
    "decision_grade",
    "status",
    "count",
    "schema_version",
    "generated_at",
]


def build_evidence_decision_layer(
    *,
    data_trust_rows: list[dict[str, Any]] | None = None,
    reconciliation_rows: list[dict[str, Any]] | None = None,
    manual_review_rows: list[dict[str, Any]] | None = None,
    entity_rows: list[dict[str, Any]] | None = None,
    alias_rows: list[dict[str, Any]] | None = None,
    control_plan_rows: list[dict[str, Any]] | None = None,
    source_platform_rows: list[dict[str, Any]] | None = None,
    report_rows: list[dict[str, Any]] | None = None,
    question_answer_rows: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    generated_at = datetime.now().isoformat(timespec="seconds")
    matrix: list[dict[str, Any]] = []
    for row in data_trust_rows or []:
        matrix.append(_data_trust_evidence_row(row, generated_at))
    for row in reconciliation_rows or []:
        matrix.append(_reconciliation_evidence_row(row, generated_at))
    for row in manual_review_rows or []:
        matrix.append(_manual_review_evidence_row(row, generated_at))
    for row in entity_rows or []:
        matrix.append(_entity_evidence_row(row, generated_at))
    for row in alias_rows or []:
        matrix.append(_alias_evidence_row(row, generated_at))
    for row in control_plan_rows or []:
        matrix.append(_control_action_evidence_row(row, generated_at))
    for row in source_platform_rows or []:
        matrix.append(_source_platform_evidence_row(row, generated_at))
    for row in report_rows or []:
        matrix.append(_report_evidence_row(row, generated_at))
    for row in question_answer_rows or []:
        matrix.append(_question_answer_evidence_row(row, generated_at))
    matrix = [row for row in matrix if row.get("subject_id") or row.get("subject_name")]
    return {
        "evidence_decision_matrix": matrix,
        "evidence_decision_summary": summarize_evidence_decision(matrix),
    }


def summarize_evidence_decision(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    generated_at = datetime.now().isoformat(timespec="seconds")
    buckets = Counter(
        (
            str(row.get("layer", "")),
            str(row.get("evidence_classification", "")),
            str(row.get("decision_grade", "")),
            str(row.get("status", "")),
        )
        for row in rows
    )
    return [
        {
            "layer": layer,
            "evidence_classification": evidence,
            "decision_grade": decision,
            "status": status,
            "count": count,
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
        }
        for (layer, evidence, decision, status), count in sorted(buckets.items())
    ]


def report_rows_from_manifest(output_dir: str | Path) -> list[dict[str, Any]]:
    manifest_path = Path(output_dir) / "audit" / "report_manifest.json"
    if not manifest_path.exists():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            {
                "report_key": "report_manifest",
                "report_path": str(manifest_path),
                "status": "invalid_json",
                "next_action": "修复 report_manifest.json 后重跑 weekly_update.py。",
            }
        ]
    reports = payload.get("reports", {}) if isinstance(payload, dict) else {}
    rows: list[dict[str, Any]] = []
    if isinstance(reports, dict):
        for key, value in sorted(reports.items()):
            path = Path(str(value))
            rows.append(
                {
                    "report_key": key,
                    "report_path": str(value),
                    "status": "exists" if path.exists() else "missing",
                    "next_action": "保持报告登记。" if path.exists() else "重建报告并检查 report_manifest 输出。",
                }
            )
    return rows


def question_answer_rows_from_audit(output_dir: str | Path) -> list[dict[str, Any]]:
    qa_path = Path(output_dir) / "audit" / "question_answer_index.json"
    if not qa_path.exists():
        return []
    try:
        payload = json.loads(qa_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            {
                "question": "question_answer_index",
                "answer_policy": "invalid_json",
                "sources": [str(qa_path)],
                "next_action": "修复 question_answer_index.json 后重建输出。",
            }
        ]
    return payload if isinstance(payload, list) else []


def evidence_decision_report_markdown(layer: dict[str, list[dict[str, Any]]]) -> str:
    matrix = layer.get("evidence_decision_matrix", [])
    summary = layer.get("evidence_decision_summary", [])
    run_id = hashlib.sha256(f"{len(matrix)}-{datetime.now().isoformat()}".encode("utf-8")).hexdigest()[:16]
    generated_at = datetime.now().isoformat(timespec="seconds")
    decision_counts = Counter(str(row.get("decision_grade", "")) for row in matrix)
    evidence_counts = Counter(str(row.get("evidence_classification", "")) for row in matrix)
    watch_rows = [
        row
        for row in matrix
        if str(row.get("decision_grade", "")) in {"Watch", "Reject"} or str(row.get("risk_level", "")) in {"P0", "P1"}
    ][:40]
    lines = [
        "# Evidence Decision Matrix 证据分层与决策等级矩阵报告",
        "",
        f"- run_id：`{run_id}`",
        f"- generated_at：`{generated_at}`",
        f"- schema_version：`{SCHEMA_VERSION}`",
        "- source_log：`audit/source_log.jsonl`",
        "- run_manifest：`audit/run_manifest.json`",
        "",
        "口径：本报告把 Data Trust、Reconciliation、Manual Review、Entity Registry、Alias Map、控制动作、来源平台、报告登记和查询模板统一为只读矩阵；不改变生产金额、分类、复核或周期报告口径。",
        "",
        "## 状态口径",
        "",
        "| 字段 | 含义 |",
        "|---|---|",
        "| evidence_classification | `FACT` 可由文件/表直接验证；`INFERENCE` 来自规则推断；`OBSERVATION` 表示需观察或人工复核；`OPINION` 当前不作为机器事实。 |",
        "| decision_grade | `Actionable` 可作为只读下游输入；`Watch` 需要复核或观察；`Observe` 仅作背景；`Reject` 不得用于结论。 |",
        "| risk_level | `P0/P1` 优先复核；`P2/P3` 可排队处理或仅保留观察。 |",
        "| next_action | 下一个可执行动作；所有金额、回款、成本和复核动作仍以原始表和复核文件为准。 |",
        "",
        "## 执行摘要",
        "",
        f"- 矩阵行数：{len(matrix)}",
        f"- FACT：{evidence_counts.get('FACT', 0)}；INFERENCE：{evidence_counts.get('INFERENCE', 0)}；OBSERVATION：{evidence_counts.get('OBSERVATION', 0)}；OPINION：{evidence_counts.get('OPINION', 0)}",
        f"- Actionable：{decision_counts.get('Actionable', 0)}；Watch：{decision_counts.get('Watch', 0)}；Observe：{decision_counts.get('Observe', 0)}；Reject：{decision_counts.get('Reject', 0)}",
        "",
        "## 分层摘要",
        "",
        "| 层 | 证据等级 | 决策等级 | 状态 | 数量 |",
        "|---|---|---|---|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row.get('layer', '')} | {row.get('evidence_classification', '')} | {row.get('decision_grade', '')} | {row.get('status', '')} | {row.get('count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## 优先复核 / 拒绝项",
            "",
            "| 层 | 对象 | 证据等级 | 决策等级 | 风险 | 状态 | 下一步 |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    if not watch_rows:
        lines.append("| 无 |  | FACT | Actionable | P3 | pass | 继续周更和校验。 |")
    for row in watch_rows:
        lines.append(
            f"| {row.get('layer', '')} | {_safe_text(row.get('subject_name') or row.get('subject_id'), 30)} | "
            f"{row.get('evidence_classification', '')} | {row.get('decision_grade', '')} | {row.get('risk_level', '')} | "
            f"{_safe_text(row.get('status', ''), 18)} | {_safe_text(row.get('next_action', ''), 42)} |"
        )
    lines.extend(
        [
            "",
            "## 机器可读产物",
            "",
            "- CSV：`audit/evidence_decision_matrix.csv`、`audit/evidence_decision_summary.csv`",
            "- JSON：`audit/evidence_decision_matrix.json`、`audit/evidence_decision_summary.json`",
            "- SQLite 表：`evidence_decision_matrix`、`evidence_decision_summary`",
            "- SQLite 视图：`v_evidence_decision_matrix`、`v_evidence_decision_actionable`、`v_evidence_decision_watchlist`、`v_evidence_decision_summary`",
            "",
            "## 验证方式",
            "",
            "```bash",
            "python3 scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_evidence_decision_outputs(layer: dict[str, list[dict[str, Any]]], output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    audit_dir = output / "audit"
    data_dir = output / "data"
    reports_dir = output / "reports"
    audit_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    matrix = layer.get("evidence_decision_matrix", [])
    summary = layer.get("evidence_decision_summary", [])
    paths = {
        "evidence_decision_matrix_csv": audit_dir / "evidence_decision_matrix.csv",
        "evidence_decision_matrix_json": audit_dir / "evidence_decision_matrix.json",
        "evidence_decision_summary_csv": audit_dir / "evidence_decision_summary.csv",
        "evidence_decision_summary_json": audit_dir / "evidence_decision_summary.json",
        "evidence_decision_matrix_data_csv": data_dir / "evidence_decision_matrix.csv",
        "evidence_decision_summary_data_csv": data_dir / "evidence_decision_summary.csv",
        "evidence_decision_matrix_report_md": reports_dir / "evidence_decision_matrix_report.md",
    }
    _write_csv(paths["evidence_decision_matrix_csv"], matrix, MATRIX_FIELDS)
    _write_csv(paths["evidence_decision_matrix_data_csv"], matrix, MATRIX_FIELDS)
    _write_json(paths["evidence_decision_matrix_json"], matrix)
    _write_csv(paths["evidence_decision_summary_csv"], summary, SUMMARY_FIELDS)
    _write_csv(paths["evidence_decision_summary_data_csv"], summary, SUMMARY_FIELDS)
    _write_json(paths["evidence_decision_summary_json"], summary)
    paths["evidence_decision_matrix_report_md"].write_text(evidence_decision_report_markdown(layer), encoding="utf-8")
    return paths


def update_evidence_decision_report_manifest(output_dir: str | Path, md_path: str | Path, pdf_path: str | Path) -> None:
    manifest_path = Path(output_dir) / "audit" / "report_manifest.json"
    if not manifest_path.exists():
        return
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    reports = payload.setdefault("reports", {})
    reports["evidence_decision_matrix_report_md"] = str(md_path)
    reports["evidence_decision_matrix_report_pdf"] = str(pdf_path)
    payload["last_evidence_decision_update"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _data_trust_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    status = str(row.get("data_trust_status", ""))
    return _matrix_row(
        "DataTrust",
        "transaction",
        str(row.get("transaction_key") or row.get("review_key") or row.get("order_id") or ""),
        str(row.get("counterparty") or row.get("description") or ""),
        str(row.get("evidence_classification") or _default_evidence_for_status(status)),
        str(row.get("decision_grade") or _default_decision_for_status(status)),
        status,
        "P1" if status == "NEEDS_REVIEW" else "P2" if status in {"PARSED_CANDIDATE", "USER_CONFIRMED"} else "P3",
        str(row.get("status_reason") or row.get("ledger_effect") or ""),
        "data_trust_transactions",
        str(row.get("source_file") or "data/data_trust_transactions.csv"),
        _next_action_for_decision(str(row.get("decision_grade") or ""), "按 Data Trust 状态下游降级读取。"),
        generated_at,
    )


def _reconciliation_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    status = str(row.get("status", ""))
    return _matrix_row(
        "Reconciliation",
        "check",
        str(row.get("check_id", "")),
        str(row.get("layer") or row.get("check_id") or ""),
        str(row.get("evidence_classification") or "FACT"),
        str(row.get("decision_grade") or _decision_from_reconciliation_status(status)),
        status,
        "P0" if status == "fail" else "P1" if status == "warn" else "P3",
        str(row.get("detail") or row.get("actual") or ""),
        "reconciliation_checks",
        str(row.get("evidence_path") or "audit/reconciliation_checks.csv"),
        str(row.get("next_action") or ""),
        generated_at,
    )


def _manual_review_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return _matrix_row(
        "ManualReview",
        "review_item",
        str(row.get("review_key", "")),
        str(row.get("counterparty") or row.get("description") or row.get("review_key") or ""),
        str(row.get("evidence_classification") or "OBSERVATION"),
        str(row.get("decision_grade") or "Watch"),
        str(row.get("queue_status", "")),
        str(row.get("priority") or "P2"),
        str(row.get("priority_reason") or row.get("candidate_reason") or ""),
        str(row.get("source_table") or "manual_review_queue_audit"),
        "audit/manual_review_queue_audit.csv",
        str(row.get("next_action") or ""),
        generated_at,
    )


def _entity_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    review_required = str(row.get("review_required", "")).lower() in {"true", "1", "yes", "是"}
    return _matrix_row(
        "EntityRegistry",
        str(row.get("entity_type") or "entity"),
        str(row.get("entity_id", "")),
        str(row.get("canonical_name") or row.get("display_name") or ""),
        str(row.get("evidence_classification") or "FACT"),
        str(row.get("decision_grade") or ("Watch" if review_required else "Actionable")),
        str(row.get("entity_status") or ("REVIEW_REQUIRED" if review_required else "ACTIVE")),
        "P1" if review_required else "P3",
        str(row.get("review_reason") or f"transaction_count={row.get('transaction_count', '')}"),
        "entity_registry",
        "audit/entity_registry.csv",
        "人工确认实体后再合并或映射。" if review_required else "可作为实体标准名只读使用。",
        generated_at,
    )


def _alias_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    collision = str(row.get("collision_status", "")) == "collision"
    return _matrix_row(
        "AliasMap",
        str(row.get("entity_type") or "alias"),
        str(row.get("alias_id", "")),
        str(row.get("alias_value") or row.get("canonical_name") or ""),
        str(row.get("evidence_classification") or "INFERENCE"),
        str(row.get("decision_grade") or ("Watch" if collision else "Actionable")),
        str(row.get("collision_status") or "unique"),
        "P1" if collision else "P3",
        f"alias_normalized={row.get('alias_normalized', '')}; canonical={row.get('canonical_entity_id', '')}",
        "alias_map",
        "audit/alias_map.csv",
        "人工确认同名实体是否应合并。" if collision else "保持当前别名映射。",
        generated_at,
    )


def _control_action_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    priority = str(row.get("priority") or "P2")
    review_needed = str(row.get("review_needed", "")).strip() in {"是", "yes", "true", "1"}
    return _matrix_row(
        "ControlAction",
        "control_plan",
        str(row.get("focus_area") or row.get("priority") or ""),
        str(row.get("focus_area") or row.get("recommended_action") or ""),
        "INFERENCE",
        "Watch" if priority in {"P0", "P1"} or review_needed else "Observe",
        priority,
        priority or "P2",
        str(row.get("trigger_metric") or row.get("current_pct") or ""),
        "spending_control_plan",
        "data/spending_control_plan.csv",
        str(row.get("recommended_action") or ""),
        generated_at,
    )


def _source_platform_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    pending = _int(row.get("pending_review_count"))
    platform = str(row.get("platform") or row.get("source_platform") or "unknown")
    return _matrix_row(
        "SourcePlatform",
        "source_platform",
        platform,
        platform,
        "FACT",
        "Watch" if pending > 0 else "Actionable",
        "ACTIVE_WITH_PENDING_REVIEW" if pending > 0 else "ACTIVE",
        "P1" if pending > 0 else "P3",
        f"transaction_count={row.get('transaction_count', '')}; production_expense={row.get('production_expense', '')}; pending_review_count={pending}",
        "source_platform_summary",
        "data/source_platform_summary.csv",
        "先处理待复核交易。" if pending > 0 else "保持来源平台导入。",
        generated_at,
    )


def _report_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    status = str(row.get("status") or "")
    report_key = str(row.get("report_key") or row.get("report_path") or "")
    return _matrix_row(
        "ReportLayer",
        "report_artifact",
        report_key,
        Path(str(row.get("report_path") or report_key)).name,
        "FACT",
        "Actionable" if status == "exists" else "Reject",
        status or "unknown",
        "P3" if status == "exists" else "P0",
        str(row.get("report_path") or ""),
        "report_manifest",
        str(row.get("report_path") or "audit/report_manifest.json"),
        str(row.get("next_action") or ""),
        generated_at,
    )


def _question_answer_evidence_row(row: dict[str, Any], generated_at: str) -> dict[str, Any]:
    question = str(row.get("question") or row.get("id") or "question_answer")
    sources = row.get("sources", [])
    source_text = "|".join(str(item) for item in sources) if isinstance(sources, list) else str(sources)
    return _matrix_row(
        "QuestionAnswer",
        "fixed_question",
        _stable_id("question", question),
        question,
        "INFERENCE",
        "Observe",
        "template_registered",
        "P3",
        str(row.get("answer_policy") or ""),
        "question_answer_index",
        source_text or "audit/question_answer_index.json",
        str(row.get("next_action") or "只读检索证据后回答；不得编造缺失证据。"),
        generated_at,
    )


def _matrix_row(
    layer: str,
    subject_type: str,
    subject_id: str,
    subject_name: str,
    evidence: str,
    decision: str,
    status: str,
    risk_level: str,
    conclusion: str,
    source_table: str,
    evidence_path: str,
    next_action: str,
    generated_at: str,
) -> dict[str, Any]:
    normalized = {
        "layer": layer,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "evidence_classification": _normalize_evidence(evidence),
        "decision_grade": _normalize_decision(decision),
        "status": status,
        "risk_level": risk_level or "P3",
        "conclusion": conclusion,
        "source_table": source_table,
        "evidence_path": evidence_path,
        "next_action": next_action,
        "generated_at": generated_at,
        "schema_version": SCHEMA_VERSION,
    }
    normalized["evidence_id"] = _stable_id(layer, source_table, subject_type, subject_id, status)
    return {field: normalized.get(field, "") for field in MATRIX_FIELDS}


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fieldnames} for row in rows])


def _write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _normalize_evidence(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"FACT", "INFERENCE", "OPINION", "OBSERVATION"}:
        return normalized
    return "OBSERVATION"


def _normalize_decision(value: str) -> str:
    normalized = str(value or "").strip()
    if normalized in {"Actionable", "Watch", "Observe", "Reject"}:
        return normalized
    lowered = normalized.lower()
    if lowered in {"pass", "passed", "ok"}:
        return "Actionable"
    if lowered in {"fail", "failed", "reject"}:
        return "Reject"
    if lowered in {"warn", "review"}:
        return "Watch"
    return "Observe"


def _default_evidence_for_status(status: str) -> str:
    if status in {"RAW_IMPORTED", "ARCHIVED", "USER_CONFIRMED", "RECONCILED", "REJECTED"}:
        return "FACT"
    if status == "NEEDS_REVIEW":
        return "OBSERVATION"
    return "INFERENCE"


def _default_decision_for_status(status: str) -> str:
    if status == "RECONCILED":
        return "Actionable"
    if status in {"REJECTED"}:
        return "Reject"
    if status in {"NEEDS_REVIEW", "USER_CONFIRMED"}:
        return "Watch"
    return "Observe"


def _decision_from_reconciliation_status(status: str) -> str:
    if status == "pass":
        return "Actionable"
    if status == "fail":
        return "Reject"
    return "Watch"


def _next_action_for_decision(decision: str, fallback: str) -> str:
    if decision == "Reject":
        return "不得用于下游结论；先修正来源或复核文件。"
    if decision == "Watch":
        return "进入人工复核或观察队列。"
    return fallback


def _stable_id(*parts: Any) -> str:
    text = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _safe_text(value: Any, limit: int) -> str:
    text = str(value or "").replace("|", "/").replace("\n", " ").strip()
    return text[:limit]


def _int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
