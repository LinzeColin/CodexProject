from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from .alipay import expand_input_paths, load_transactions
from .classifier import classify_transactions, load_rules
from .data_trust import build_data_trust_sources
from .evidence_decision import (
    build_evidence_decision_layer,
    question_answer_rows_from_audit,
    report_rows_from_manifest,
    update_evidence_decision_report_manifest,
    write_evidence_decision_outputs,
)
from .reconciliation import build_reconciliation_checks, write_reconciliation_outputs
from .reports import generate_outputs, load_tag_config, write_report_pdf
from .review import load_review_decisions


LEDGER_SCHEMA_VERSION = "2026.06.05.1"


@dataclass(frozen=True)
class PreparedSources:
    input_paths: list[Path]
    source_archives: list[dict[str, object]]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_range_name(name: str, fallback: str) -> str:
    match = re.search(r"\((\d{8}-\d{8})\)", name)
    if match:
        return match.group(1)
    return fallback


def _zip_bill_members(zip_path: Path) -> list[tuple[str, bytes, str]]:
    members: list[tuple[str, bytes, str]] = []
    with ZipFile(zip_path) as z:
        for info in z.infolist():
            filename = info.filename
            if info.is_dir() or filename.startswith("__MACOSX/") or "/._" in filename or filename.endswith(".DS_Store"):
                continue
            suffix = Path(filename).suffix.casefold()
            if suffix not in {".csv", ".xlsx"}:
                continue
            members.append((filename, z.read(info), suffix))
    return members


def extract_zip_sources(zip_path: str | Path, source_root: str | Path) -> list[dict[str, object]]:
    source = Path(zip_path).expanduser().resolve()
    archive_hash = sha256_file(source)
    target_dir = Path(source_root) / f"{source.stem}_{archive_hash[:12]}"
    target_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for index, (member_name, payload, suffix) in enumerate(_zip_bill_members(source), start=1):
        member_hash = hashlib.sha256(payload).hexdigest()
        range_name = _safe_range_name(member_name, f"file_{index:02d}")
        target = target_dir / f"bill_{range_name}_{member_hash[:12]}{suffix}"
        if not target.exists() or target.read_bytes() != payload:
            target.write_bytes(payload)
        rows.append(
            {
                "source_type": "zip_member",
                "bill_period": range_name,
                "archive_path": str(source),
                "archive_sha256": archive_hash,
                "member_name": member_name,
                "member_sha256": member_hash,
                "extracted_path": str(target),
                "size_bytes": len(payload),
            }
        )
    return rows


def prepare_sources(inputs: list[str | Path], source_root: str | Path) -> PreparedSources:
    prepared_paths: list[Path] = []
    archives: list[dict[str, object]] = []
    for raw in inputs:
        path = Path(raw).expanduser()
        if path.suffix.casefold() == ".zip":
            extracted = extract_zip_sources(path, source_root)
            archives.extend(extracted)
            prepared_paths.extend(Path(item["extracted_path"]) for item in extracted)
        else:
            paths = expand_input_paths([path])
            prepared_paths.extend(paths)
            for source in paths:
                archives.append(
                    {
                        "source_type": "csv",
                        "bill_period": _safe_range_name(source.name, ""),
                        "archive_path": "",
                        "archive_sha256": "",
                        "member_name": source.name,
                        "member_sha256": sha256_file(source),
                        "extracted_path": str(source.resolve()),
                        "size_bytes": source.stat().st_size,
                    }
                )
    unique = sorted({path.resolve() for path in prepared_paths})
    if not unique:
        raise FileNotFoundError("未找到可导入的 CSV/XLSX 账单文件。")
    return PreparedSources(input_paths=unique, source_archives=archives)


def _write_rows(conn: sqlite3.Connection, table_name: str, rows: list[dict[str, object]]) -> None:
    conn.execute(f'drop table if exists "{table_name}"')
    if not rows:
        conn.execute(f'create table "{table_name}" (empty text)')
        return
    columns = list(rows[0].keys())
    column_sql = ", ".join(f'"{col}" text' for col in columns)
    conn.execute(f'create table "{table_name}" ({column_sql})')
    placeholders = ", ".join("?" for _ in columns)
    insert_columns = ", ".join(f'"{col}"' for col in columns)
    conn.executemany(
        f'insert into "{table_name}" ({insert_columns}) values ({placeholders})',
        [[json.dumps(row.get(col), ensure_ascii=False) if isinstance(row.get(col), (dict, list)) else row.get(col) for col in columns] for row in rows],
    )


def _install_views(conn: sqlite3.Connection) -> None:
    views = {
        "v_production_transactions": "select * from production_expense_allocations",
        "v_classified_transactions_audit": "select * from classified_transactions_audit",
        "v_pending_large_review": "select * from manual_review_queue",
        "v_review_status_summary": "select * from manual_review_status_summary",
        "v_review_decision_candidates": "select * from manual_review_decision_candidates",
        "v_review_decision_candidate_groups": "select * from manual_review_decision_candidate_groups",
        "v_manual_review_queue_audit": "select * from manual_review_queue_audit",
        "v_manual_review_queue_blockers": "select * from manual_review_queue_audit where priority in ('P0','P1') and queue_status in ('PENDING_REVIEW','INVALID_DECISION')",
        "v_manual_review_queue_summary": "select * from manual_review_queue_audit_summary",
        "v_category_summary": "select * from summary_by_category",
        "v_risk_summary": "select * from summary_by_risk_tag",
        "v_control_plan": "select * from spending_control_plan",
        "v_budget_pressure_radar": "select * from budget_pressure_radar",
        "v_source_platform_summary": "select * from source_platform_summary",
        "v_data_trust_transactions": "select * from data_trust_transactions",
        "v_data_trust_sources": "select * from data_trust_sources",
        "v_data_trust_summary": """
            select data_trust_status, count(*) as count
            from data_trust_transactions
            group by data_trust_status
        """,
        "v_reconciliation_checks": "select * from reconciliation_checks",
        "v_reconciliation_failures": "select * from reconciliation_checks where status = 'fail'",
        "v_reconciliation_summary": """
            select status, count(*) as count
            from reconciliation_checks
            group by status
        """,
        "v_entity_registry": "select * from entity_registry",
        "v_alias_map": "select * from alias_map",
        "v_entity_registry_summary": "select * from entity_registry_summary",
        "v_entity_alias_conflicts": "select * from alias_map where collision_status = 'collision'",
        "v_evidence_decision_matrix": "select * from evidence_decision_matrix",
        "v_evidence_decision_actionable": "select * from evidence_decision_matrix where decision_grade = 'Actionable'",
        "v_evidence_decision_watchlist": "select * from evidence_decision_matrix where decision_grade in ('Watch','Reject') or risk_level in ('P0','P1')",
        "v_evidence_decision_summary": "select * from evidence_decision_summary",
        "v_tag_library": "select * from tag_library",
        "v_tag_filter_presets": "select * from tag_filter_presets",
        "v_cashflow_weekly": "select * from summary_by_week",
        "v_cashflow_monthly": "select * from summary_by_month",
        "v_cashflow_quarterly": "select * from summary_by_quarter",
        "v_cashflow_half_year": "select * from summary_by_half",
        "v_cashflow_yearly": "select * from summary_by_year",
        "v_fact_expense_allocations": """
            select
                date,
                substr(date, 1, 7) as month,
                substr(date, 1, 4) as year,
                source_platform,
                transaction_time,
                counterparty,
                description,
                cast(original_amount as real) as original_amount,
                cast(allocated_amount as real) as allocated_amount,
                cast(allocated_amount_cents as integer) as allocated_amount_cents,
                main_category,
                sub_category,
                risk_tags,
                review_confirmed,
                review_decision,
                review_key
            from production_expense_allocations
        """,
        "v_fact_transactions_audit": """
            select
                date,
                substr(date, 1, 7) as month,
                substr(date, 1, 4) as year,
                source_platform,
                transaction_time,
                cast(hour as integer) as hour,
                transaction_type,
                counterparty,
                description,
                direction,
                cast(amount as real) as amount,
                cast(amount_cents as integer) as amount_cents,
                payment_method,
                status,
                order_id,
                source_file,
                primary_bucket,
                main_category,
                sub_category,
                cash_flow_type,
                risk_tags,
                needs_review,
                mechanism,
                risk_level,
                rule_name,
                is_real_consumption,
                is_risk_spending,
                is_optimizable_spending,
                is_social_spending,
                is_financial_spending,
                is_business_personal_mixed,
                is_account_transfer,
                is_late_night,
                is_huabei_or_credit
            from classified_transactions_audit
        """,
        "v_fact_pending_large_review": """
            select
                date,
                substr(date, 1, 7) as month,
                substr(date, 1, 4) as year,
                source_platform,
                transaction_time,
                counterparty,
                description,
                cast(amount as real) as amount,
                cast(amount_cents as integer) as amount_cents,
                main_category,
                sub_category,
                risk_tags,
                order_id,
                rule_name,
                classification_reason
            from manual_review_queue
        """,
        "v_mart_daily_cashflow": """
            with dates as (
                select date from classified_transactions_audit
                union
                select date from production_expense_allocations
                union
                select date from manual_review_queue
            ),
            expense as (
                select date, sum(cast(allocated_amount_cents as real)) / 100.0 as total_expense
                from production_expense_allocations
                group by date
            ),
            income as (
                select date, sum(cast(amount as real)) as total_income
                from classified_transactions_audit
                where cash_flow_type = 'income'
                group by date
            ),
            transfer as (
                select date, sum(cast(amount as real)) as total_transfer
                from classified_transactions_audit
                where cash_flow_type = 'transfer'
                group by date
            ),
            pending as (
                select date, sum(cast(amount as real)) as pending_review
                from manual_review_queue
                group by date
            )
            select
                dates.date,
                substr(dates.date, 1, 7) as month,
                substr(dates.date, 1, 4) as year,
                coalesce(expense.total_expense, 0) as total_expense,
                coalesce(income.total_income, 0) as total_income,
                coalesce(income.total_income, 0) - coalesce(expense.total_expense, 0) as net_cash_flow,
                coalesce(transfer.total_transfer, 0) as total_transfer,
                coalesce(pending.pending_review, 0) as pending_review
            from dates
            left join expense on expense.date = dates.date
            left join income on income.date = dates.date
            left join transfer on transfer.date = dates.date
            left join pending on pending.date = dates.date
        """,
        "v_mart_counterparty_monthly": """
            select
                substr(date, 1, 7) as month,
                counterparty,
                main_category,
                sub_category,
                count(*) as allocation_count,
                sum(cast(allocated_amount_cents as real)) / 100.0 as total_expense
            from production_expense_allocations
            group by substr(date, 1, 7), counterparty, main_category, sub_category
        """,
        "v_mart_risk_monthly": """
            select
                substr(date, 1, 7) as month,
                risk_tags,
                count(*) as allocation_count,
                sum(cast(allocated_amount_cents as real)) / 100.0 as total_expense
            from production_expense_allocations
            group by substr(date, 1, 7), risk_tags
        """,
    }
    for name in views:
        conn.execute(f'drop view if exists "{name}"')
    for name, sql in views.items():
        conn.execute(f'create view "{name}" as {sql}')


def _has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    return bool(conn.execute("select 1 from sqlite_master where type='table' and name = ?", (table_name,)).fetchone())


def _read_rows(conn: sqlite3.Connection, table_name: str) -> list[dict[str, object]]:
    if not _has_table(conn, table_name):
        return []
    cursor = conn.execute(f'select * from "{table_name}"')
    columns = [item[0] for item in cursor.description or []]
    if columns == ["empty"]:
        return []
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def install_master_ledger(
    report_sqlite: str | Path,
    ledger_db: str | Path,
    *,
    source_archives: list[dict[str, object]],
    transaction_count: int,
    date_start: str,
    date_end: str,
    output_dir: str | Path,
) -> Path:
    target = Path(ledger_db)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report_sqlite, target)
    metadata = [
        {"key": "schema_version", "value": LEDGER_SCHEMA_VERSION},
        {"key": "generated_at", "value": datetime.now().isoformat(timespec="seconds")},
        {"key": "transaction_count", "value": transaction_count},
        {"key": "date_start", "value": date_start},
        {"key": "date_end", "value": date_end},
        {"key": "analysis_output_dir", "value": str(Path(output_dir))},
        {"key": "access_policy", "value": "read_only_for_downstream_systems"},
    ]
    with sqlite3.connect(target) as conn:
        _write_rows(conn, "ledger_metadata", metadata)
        _write_rows(conn, "source_archives", source_archives)
        _write_rows(conn, "data_trust_sources", build_data_trust_sources(source_archives))
        reconciliation_checks = build_reconciliation_checks(
            conn,
            output_dir=output_dir,
            handoff_path=Path(__file__).resolve().parents[2] / "HANDOFF.md",
        )
        _write_rows(conn, "reconciliation_checks", reconciliation_checks)
        evidence_decision_layer = build_evidence_decision_layer(
            data_trust_rows=_read_rows(conn, "data_trust_transactions"),
            reconciliation_rows=reconciliation_checks,
            manual_review_rows=_read_rows(conn, "manual_review_queue_audit"),
            entity_rows=_read_rows(conn, "entity_registry"),
            alias_rows=_read_rows(conn, "alias_map"),
            control_plan_rows=_read_rows(conn, "spending_control_plan"),
            source_platform_rows=_read_rows(conn, "source_platform_summary"),
            report_rows=report_rows_from_manifest(output_dir),
            question_answer_rows=question_answer_rows_from_audit(output_dir),
        )
        _write_rows(conn, "evidence_decision_matrix", evidence_decision_layer["evidence_decision_matrix"])
        _write_rows(conn, "evidence_decision_summary", evidence_decision_layer["evidence_decision_summary"])
        _install_views(conn)
        write_reconciliation_outputs(reconciliation_checks, output_dir)
        evidence_paths = write_evidence_decision_outputs(evidence_decision_layer, output_dir)
        evidence_md = evidence_paths["evidence_decision_matrix_report_md"]
        evidence_pdf = evidence_md.with_suffix(".pdf")
        write_report_pdf(evidence_md.read_text(encoding="utf-8"), evidence_pdf)
        update_evidence_decision_report_manifest(output_dir, evidence_md, evidence_pdf)
        conn.execute("pragma user_version = 20260605")
        conn.commit()
    return target


def build_master_ledger(
    *,
    inputs: list[str | Path],
    ledger_db: str | Path = "data/finance_ledger/finance_ledger.sqlite",
    output_dir: str | Path = "outputs/finance_ledger_latest",
    source_root: str | Path = "data/finance_ledger/sources",
    rules_path: str | Path = "configs/classification_rules.json",
    review_decisions_path: str | Path | None = None,
    tag_library_path: str | Path | None = None,
) -> dict[str, Path | int | str]:
    prepared = prepare_sources(inputs, source_root)
    transactions = load_transactions(prepared.input_paths)
    if not transactions:
        raise ValueError("未读取到交易记录。")
    rules = load_rules(rules_path)
    classified = classify_transactions(transactions, rules)
    review_decisions = load_review_decisions(review_decisions_path)
    tag_library_rows, tag_filter_preset_rows = load_tag_config(tag_library_path)
    outputs = generate_outputs(
        classified,
        output_dir,
        review_decisions=review_decisions,
        tag_library_rows=tag_library_rows,
        tag_filter_preset_rows=tag_filter_preset_rows,
    )
    dates = [row.date for row in classified]
    ledger_path = install_master_ledger(
        outputs["sqlite"],
        ledger_db,
        source_archives=prepared.source_archives,
        transaction_count=len(transactions),
        date_start=min(dates),
        date_end=max(dates),
        output_dir=output_dir,
    )
    return {
        "ledger_db": ledger_path,
        "output_dir": Path(output_dir),
        "source_count": len(prepared.input_paths),
        "transaction_count": len(transactions),
        "date_start": min(dates),
        "date_end": max(dates),
    }
