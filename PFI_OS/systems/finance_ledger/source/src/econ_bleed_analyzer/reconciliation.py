from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .reports import write_report_pdf


RECONCILIATION_SCHEMA_VERSION = "2026.06.05.1"


def build_reconciliation_checks(
    conn: sqlite3.Connection,
    *,
    output_dir: str | Path,
    handoff_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    generated_at = datetime.now().isoformat(timespec="seconds")
    output = Path(output_dir)
    checks: list[dict[str, Any]] = []

    def add(
        check_id: str,
        layer: str,
        status: str,
        expected: str,
        actual: str,
        formula: str,
        evidence_path: str,
        detail: str,
        next_action: str,
        evidence_classification: str = "FACT",
    ) -> None:
        checks.append(
            {
                "check_id": check_id,
                "layer": layer,
                "status": status,
                "evidence_classification": evidence_classification,
                "decision_grade": _decision_grade(status),
                "expected": expected,
                "actual": actual,
                "formula": formula,
                "evidence_path": evidence_path,
                "detail": detail,
                "next_action": next_action,
                "generated_at": generated_at,
                "schema_version": RECONCILIATION_SCHEMA_VERSION,
            }
        )

    source_count = _safe_count(conn, "source_archives")
    add(
        "source_archive_count",
        "source_to_ledger",
        "pass" if source_count >= 1 else "fail",
        ">= 1 archived source row",
        str(source_count),
        "count(source_archives)",
        "source_archives",
        "账单来源归档行数检查。",
        "如果为 fail，重新运行 weekly_update.py 并确认 --input 指向真实账单源文件。",
    )

    _add_source_file_checks(conn, add)
    _add_transaction_count_checks(conn, add)
    _add_expense_reconciliation_checks(conn, add)
    _add_pending_isolation_checks(conn, add)
    _add_data_trust_reconciliation_checks(conn, add)
    _add_handoff_checks(add, output, handoff_path)
    _add_report_file_checks(add, output)
    return checks


def write_reconciliation_outputs(checks: list[dict[str, Any]], output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    audit_dir = output / "audit"
    reports_dir = output / "reports"
    audit_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    csv_path = audit_dir / "reconciliation_checks.csv"
    json_path = audit_dir / "reconciliation_checks.json"
    md_path = reports_dir / "reconciliation_audit_report.md"
    pdf_path = reports_dir / "reconciliation_audit_report.pdf"

    fieldnames = list(checks[0].keys()) if checks else ["check_id", "status", "detail"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(checks)
    json_path.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown = reconciliation_report_markdown(checks)
    md_path.write_text(markdown, encoding="utf-8")
    write_report_pdf(markdown, pdf_path)
    _update_report_manifest(output, md_path, pdf_path)
    return {
        "reconciliation_checks_csv": csv_path,
        "reconciliation_checks_json": json_path,
        "reconciliation_audit_md": md_path,
        "reconciliation_audit_pdf": pdf_path,
    }


def reconciliation_report_markdown(checks: list[dict[str, Any]]) -> str:
    counts = {status: sum(1 for item in checks if item.get("status") == status) for status in ("pass", "warn", "fail")}
    lines = [
        "# Reconciliation Layer 自动对账报告",
        "",
        "本报告对比原始来源、清洗交易、生产分摊、月度汇总、Data Trust、HANDOFF.md 和真实文件状态。该层只做审计和决策降级，不改变生产金额、分类、复核或报告口径。",
        "",
        "## 审计总览",
        "",
        f"- 生成时间：`{datetime.now().isoformat(timespec='seconds')}`",
        f"- Schema：`{RECONCILIATION_SCHEMA_VERSION}`",
        f"- 通过：{counts['pass']}",
        f"- 警告：{counts['warn']}",
        f"- 失败：{counts['fail']}",
        "- 决策规则：任何 `fail` 都阻止把本次账本声明为完全可对账；`warn` 表示证据不足但不改变已有生产统计。",
        "",
        "## 对账公式与假设",
        "",
        "- 生产支出公式：`sum(production_expense_allocations.allocated_amount_cents) / 100`。",
        "- 月度汇总公式：`sum(summary_by_month.total_expense)`。",
        "- 容差：人民币金额对账容差为 `0.05` 元，用于处理分摊和格式化小数误差。",
        "- 复核隔离公式：`manual_review_queue` 生成的 pending key 不得出现在 `production_expense_allocations.review_key`。",
        "- Data Trust 对账公式：`count(data_trust_transactions where status='RECONCILED') = count(distinct production_expense_allocations.review_key)`。",
        "- 文件溯源公式：可校验来源文件的 `sha256(extracted_path)` 必须等于 `source_archives.member_sha256`。",
        "",
        "## 检查矩阵",
        "",
        "| 检查项 | 状态 | 证据等级 | 决策等级 | 实际结果 | 下一步 |",
        "|---|---:|---|---|---|---|",
    ]
    for item in checks:
        lines.append(
            "| {check_id} | {status} | {evidence_classification} | {decision_grade} | {actual} | {next_action} |".format(
                check_id=item.get("check_id", ""),
                status=item.get("status", ""),
                evidence_classification=item.get("evidence_classification", ""),
                decision_grade=item.get("decision_grade", ""),
                actual=str(item.get("actual", "")).replace("|", "/"),
                next_action=str(item.get("next_action", "")).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## 机器可读证据",
            "",
            "- CSV：`audit/reconciliation_checks.csv`",
            "- JSON：`audit/reconciliation_checks.json`",
            "- SQLite 表：`reconciliation_checks`",
            "- SQLite 视图：`v_reconciliation_checks`、`v_reconciliation_failures`、`v_reconciliation_summary`",
        ]
    )
    return "\n".join(lines) + "\n"


def _add_source_file_checks(conn: sqlite3.Connection, add: Any) -> None:
    columns = _columns(conn, "source_archives")
    if not {"extracted_path", "member_sha256"} <= columns:
        add(
            "source_hash_match",
            "source_to_file",
            "warn",
            "source_archives has extracted_path and member_sha256",
            f"columns={sorted(columns)}",
            "sha256(extracted_path) == member_sha256",
            "source_archives",
            "当前表结构缺少文件 hash 校验字段，只能保留来源行数检查。",
            "下次真实导入时使用 prepare_sources 生成完整 source_archives 字段。",
            "OBSERVATION",
        )
        return
    rows = conn.execute("select extracted_path, member_sha256 from source_archives").fetchall()
    missing: list[str] = []
    mismatched: list[str] = []
    checked = 0
    for extracted_path, expected_hash in rows:
        path_text = str(extracted_path or "")
        expected = str(expected_hash or "")
        if not path_text:
            continue
        path = Path(path_text)
        if not path.exists():
            missing.append(path_text)
            continue
        if expected:
            checked += 1
            if _sha256_file(path) != expected:
                mismatched.append(path_text)
    if missing or mismatched:
        status = "fail"
        actual = f"missing={len(missing)}, mismatched={len(mismatched)}, checked={checked}"
        detail = "来源文件缺失或 hash 不一致。"
        next_action = "恢复缺失源文件或重新导入原始账单，禁止把本轮输出声明为完全可追溯。"
    elif checked:
        status = "pass"
        actual = f"checked={checked}, missing=0, mismatched=0"
        detail = "来源文件存在且 hash 校验通过。"
        next_action = "保持 source_archives 与 data/finance_ledger/sources 只读归档。"
    else:
        status = "warn"
        actual = "no hash-checkable source rows"
        detail = "存在来源行，但没有可校验 hash。"
        next_action = "下次导入时保留 member_sha256。"
    add(
        "source_hash_match",
        "source_to_file",
        status,
        "all existing extracted_path hashes match member_sha256",
        actual,
        "sha256(extracted_path) == member_sha256",
        "source_archives",
        detail,
        next_action,
        "FACT" if status != "warn" else "OBSERVATION",
    )


def _add_transaction_count_checks(conn: sqlite3.Connection, add: Any) -> None:
    classified = _safe_count(conn, "classified_transactions_audit")
    data_trust = _safe_count(conn, "data_trust_transactions")
    status = "pass" if classified > 0 and classified == data_trust else "fail"
    add(
        "classified_vs_data_trust_count",
        "parsed_to_trust",
        status,
        "classified count equals data_trust count and count > 0",
        f"classified={classified}, data_trust={data_trust}",
        "count(classified_transactions_audit) == count(data_trust_transactions)",
        "classified_transactions_audit,data_trust_transactions",
        "清洗交易与逐笔可信度审计行数对账。",
        "如果失败，重新生成 reports.py 输出并检查 Data Trust 构建函数。",
    )


def _add_expense_reconciliation_checks(conn: sqlite3.Connection, add: Any) -> None:
    production_total = _safe_float(
        conn,
        "select coalesce(sum(cast(allocated_amount_cents as real)),0) / 100.0 from production_expense_allocations",
    )
    monthly_total = _safe_float(conn, "select coalesce(sum(cast(total_expense as real)),0) from summary_by_month")
    diff = abs(production_total - monthly_total)
    add(
        "production_vs_monthly_expense",
        "production_to_summary",
        "pass" if diff <= 0.05 and production_total > 0 else "fail",
        "absolute difference <= 0.05",
        f"production={production_total:.2f}, monthly={monthly_total:.2f}, diff={diff:.4f}",
        "abs(sum(production.allocated_amount_cents)/100 - sum(summary_by_month.total_expense)) <= 0.05",
        "production_expense_allocations,summary_by_month",
        "生产分摊与月度汇总金额对账。",
        "如果失败，暂停使用周期报告金额结论，检查分摊和汇总生成口径。",
    )


def _add_pending_isolation_checks(conn: sqlite3.Connection, add: Any) -> None:
    if not (_has_table(conn, "manual_review_queue") and _has_table(conn, "production_expense_allocations")):
        add(
            "pending_not_in_production",
            "review_to_production",
            "fail",
            "pending review rows are isolated from production rows",
            "required tables missing",
            "pending_keys ∩ production.review_key = empty",
            "manual_review_queue,production_expense_allocations",
            "复核队列或生产分摊表缺失。",
            "重新生成账本并确认 review/prod 表已写入。",
        )
        return
    pending_columns = _columns(conn, "manual_review_queue")
    required = {"order_id", "transaction_time", "counterparty", "amount_cents", "description"}
    if not required <= pending_columns or "review_key" not in _columns(conn, "production_expense_allocations"):
        add(
            "pending_not_in_production",
            "review_to_production",
            "warn",
            "pending review rows are isolated from production rows",
            f"manual_review_queue_columns={sorted(pending_columns)}",
            "pending_keys ∩ production.review_key = empty",
            "manual_review_queue,production_expense_allocations",
            "测试或旧库缺少完整复核 key 字段，无法执行严格隔离对账。",
            "真实账本应保留完整复核字段；fixture 可保持 warn。",
            "OBSERVATION",
        )
        return
    pending_keys = {
        row[0]
        for row in conn.execute(
            "select coalesce(order_id, transaction_time || '|' || counterparty || '|' || amount_cents || '|' || description) from manual_review_queue"
        )
    }
    production_keys = {row[0] for row in conn.execute("select review_key from production_expense_allocations")}
    overlap = pending_keys & production_keys
    add(
        "pending_not_in_production",
        "review_to_production",
        "pass" if not overlap else "fail",
        "0 overlapping keys",
        f"overlap={len(overlap)}, pending={len(pending_keys)}, production_keys={len(production_keys)}",
        "pending_keys ∩ production.review_key = empty",
        "manual_review_queue,production_expense_allocations",
        "大额/待复核交易与生产分摊隔离检查。",
        "如果失败，立即回滚对应复核回灌并重建账本。",
    )


def _add_data_trust_reconciliation_checks(conn: sqlite3.Connection, add: Any) -> None:
    if not (_has_table(conn, "data_trust_transactions") and _has_table(conn, "production_expense_allocations")):
        add(
            "data_trust_reconciled_matches_production",
            "trust_to_production",
            "fail",
            "RECONCILED data_trust rows equal distinct production review keys",
            "required tables missing",
            "count(data_trust where status='RECONCILED') == count(distinct production.review_key)",
            "data_trust_transactions,production_expense_allocations",
            "Data Trust 或生产分摊表缺失。",
            "重新生成 Data Trust Layer 和 master ledger。",
        )
        return
    production_columns = _columns(conn, "production_expense_allocations")
    data_trust_columns = _columns(conn, "data_trust_transactions")
    if "review_key" not in production_columns or "data_trust_status" not in data_trust_columns:
        add(
            "data_trust_reconciled_matches_production",
            "trust_to_production",
            "warn",
            "RECONCILED data_trust rows equal distinct production review keys",
            f"production_columns={sorted(production_columns)}, data_trust_columns={sorted(data_trust_columns)}",
            "count(data_trust where status='RECONCILED') == count(distinct production.review_key)",
            "data_trust_transactions,production_expense_allocations",
            "缺少严格对账字段，只能降级为结构观察。",
            "真实账本应保留 review_key 和 data_trust_status。",
            "OBSERVATION",
        )
        return
    reconciled = _safe_int(conn, "select count(*) from data_trust_transactions where data_trust_status = 'RECONCILED'")
    production_keys = _safe_int(conn, "select count(distinct review_key) from production_expense_allocations")
    add(
        "data_trust_reconciled_matches_production",
        "trust_to_production",
        "pass" if reconciled == production_keys and production_keys > 0 else "fail",
        "equal nonzero counts",
        f"reconciled={reconciled}, production_distinct_keys={production_keys}",
        "count(data_trust where status='RECONCILED') == count(distinct production.review_key)",
        "data_trust_transactions,production_expense_allocations",
        "可信度层已对齐生产分摊唯一交易 key。",
        "如果失败，检查 build_data_trust_transactions 的 production_keys 输入。",
    )


def _add_handoff_checks(add: Any, output_dir: Path, handoff_path: str | Path | None) -> None:
    path = Path(handoff_path) if handoff_path else Path("HANDOFF.md")
    exists = path.exists()
    content = path.read_text(encoding="utf-8", errors="ignore") if exists else ""
    add(
        "handoff_exists",
        "handoff_to_files",
        "pass" if exists else "warn",
        "HANDOFF.md exists",
        str(path if exists else "missing"),
        "Path(HANDOFF.md).exists()",
        str(path),
        "交接文件存在性检查。",
        "如果缺失，更新 HANDOFF.md 后再交接给下一轮。",
        "FACT" if exists else "OBSERVATION",
    )
    output_marker = str(output_dir)
    add(
        "handoff_mentions_output_dir",
        "handoff_to_files",
        "pass" if exists and output_marker in content else "warn",
        "HANDOFF.md mentions current output_dir",
        f"mentioned={exists and output_marker in content}",
        "output_dir string in HANDOFF.md",
        str(path),
        "交接文件与当前输出目录一致性检查。",
        "如果为 warn，在本轮结束更新 HANDOFF.md。",
        "FACT" if exists and output_marker in content else "OBSERVATION",
    )


def _add_report_file_checks(add: Any, output_dir: Path) -> None:
    required = [
        output_dir / "reports" / "data_trust_audit_report.pdf",
        output_dir / "audit" / "report_manifest.json",
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    add(
        "key_artifacts_exist",
        "report_to_files",
        "pass" if not missing else "fail",
        "required audit/report files exist and are non-empty",
        f"missing={len(missing)}",
        "exists(data_trust_pdf, report_manifest)",
        ",".join(str(path) for path in required),
        "关键审计产物存在性检查。",
        "如果失败，重新运行 weekly_update.py 并检查输出目录。",
    )


def _update_report_manifest(output_dir: Path, md_path: Path, pdf_path: Path) -> None:
    manifest_path = output_dir / "audit" / "report_manifest.json"
    if not manifest_path.exists():
        return
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    reports = payload.setdefault("reports", {})
    reports["reconciliation_audit_md"] = str(md_path)
    reports["reconciliation_audit_pdf"] = str(pdf_path)
    payload["last_reconciliation_update"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _decision_grade(status: str) -> str:
    if status == "pass":
        return "Actionable"
    if status == "fail":
        return "Reject"
    return "Watch"


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("select count(*) from sqlite_master where type in ('table','view') and name = ?", (table,)).fetchone()[0] > 0


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _has_table(conn, table):
        return set()
    return {row[1] for row in conn.execute(f'pragma table_info("{table}")')}


def _safe_count(conn: sqlite3.Connection, table: str) -> int:
    if not _has_table(conn, table):
        return 0
    return _safe_int(conn, f'select count(*) from "{table}"')


def _safe_int(conn: sqlite3.Connection, sql: str) -> int:
    try:
        value = conn.execute(sql).fetchone()[0]
    except sqlite3.Error:
        return 0
    return int(value or 0)


def _safe_float(conn: sqlite3.Connection, sql: str) -> float:
    try:
        value = conn.execute(sql).fetchone()[0]
    except sqlite3.Error:
        return 0.0
    return float(value or 0.0)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
