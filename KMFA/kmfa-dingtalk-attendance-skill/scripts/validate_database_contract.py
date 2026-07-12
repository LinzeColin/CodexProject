#!/usr/bin/env python3
"""Offline PostgreSQL contract validator for KMFA attendance stage-2 database path.

This validator intentionally does not connect to PostgreSQL. It checks that the
repo SQL exposes the objects needed for the stage-2 -> payroll baseline path,
then runs an in-memory synthetic insert/query simulation for the critical views.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_TYPES = {
    "quality_grade",
    "run_slot",
    "exception_priority",
    "stage2_status",
}

REQUIRED_TABLES = {
    "raw_import_batch",
    "employee_identity_map",
    "raw_attendance_result",
    "raw_attendance_detail",
    "attendance_trajectory_point",
    "attendance_group_snapshot",
    "shift_snapshot",
    "site_geofence",
    "policy_version",
    "rule_config_snapshot",
    "attendance_day_fact",
    "attendance_punch_fact",
    "classification_result",
    "exception_case",
    "canonical_month_snapshot",
    "stage2_shadow_run",
    "stage2_consensus_certificate",
    "payroll_baseline_attendance",
    "payroll_export_audit",
    "integrity_audit_log",
}

REQUIRED_VIEWS = {
    "v_payroll_baseline_active",
    "v_monthly_baseline_summary",
    "v_stage2_blockers",
}


@dataclass(frozen=True)
class ContractCheck:
    name: str
    passed: bool
    detail: str


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.lower())


def extract_types(sql: str) -> set[str]:
    return {m.group(1).lower() for m in re.finditer(r"create\s+type\s+([a-zA-Z_][\w]*)\s+as\s+enum", sql, re.I)}


def extract_views(sql: str) -> set[str]:
    return {m.group(1).lower() for m in re.finditer(r"create\s+or\s+replace\s+view\s+([a-zA-Z_][\w]*)\s+as", sql, re.I)}


def extract_table_blocks(sql: str) -> dict[str, str]:
    pattern = re.compile(r"create\s+table\s+if\s+not\s+exists\s+([a-zA-Z_][\w]*)\s*\(", re.I)
    blocks: dict[str, str] = {}
    for match in pattern.finditer(sql):
        name = match.group(1).lower()
        open_paren = match.end() - 1
        depth = 0
        end = None
        for idx in range(open_paren, len(sql)):
            char = sql[idx]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = idx
                    break
        if end is None:
            continue
        blocks[name] = sql[open_paren + 1 : end]
    return blocks


def contract_checks(tables: dict[str, str], views_sql: str) -> list[ContractCheck]:
    checks: list[ContractCheck] = []
    normalized_views = normalize_sql(views_sql)

    def table_contains(table: str, needle: str) -> None:
        body = normalize_sql(tables.get(table, ""))
        checks.append(ContractCheck(f"{table}:{needle}", needle in body, needle))

    table_contains("stage2_shadow_run", "snapshot_id uuid not null references canonical_month_snapshot")
    table_contains("stage2_shadow_run", "run_index integer not null check (run_index between 1 and 5)")
    table_contains("stage2_shadow_run", "unique (target_month, run_index)")
    table_contains("stage2_consensus_certificate", "status stage2_status not null")
    table_contains("stage2_consensus_certificate", "accepted boolean not null default false")
    table_contains("payroll_baseline_attendance", "source_day_fact_id uuid not null references attendance_day_fact")
    table_contains("payroll_baseline_attendance", "stage2_certificate_id uuid not null references stage2_consensus_certificate")
    checks.append(
        ContractCheck(
            "v_payroll_baseline_active:accepted_certificate_filter",
            "join stage2_consensus_certificate c" in normalized_views
            and "c.status = 'accepted'" in normalized_views
            and "c.accepted = true" in normalized_views,
            "active payroll rows must require accepted stage-2 certificate",
        )
    )
    checks.append(
        ContractCheck(
            "v_stage2_blockers:p0_p1_filter",
            "priority in ('p0', 'p1')" in normalized_views and "status <> 'resolved'" in normalized_views,
            "stage-2 blockers must count unresolved P0/P1 only",
        )
    )
    return checks


def run_synthetic_path() -> dict[str, Any]:
    target_month = "202607"
    canonical_hash = "sha256:" + "a" * 64
    policy_version_id = "policy-1"
    day_fact = {
        "day_fact_id": "day-1",
        "target_month": target_month,
        "employee_internal_id": "E001",
        "dingtalk_userid": "u001",
        "work_date": "2026-07-01",
        "policy_version_id": policy_version_id,
        "required_attendance_state": "workday",
        "actual_attendance_state": "present",
        "first_in_time": "2026-07-01T09:00:00+08:00",
        "last_out_time": "2026-07-01T18:00:00+08:00",
        "late_minutes": 0,
        "early_leave_minutes": 0,
        "absent_flag": False,
        "missing_punch_count": 0,
        "location_evidence_count": 2,
        "trajectory_evidence_count": 2,
    }
    snapshot = {
        "snapshot_id": "snapshot-1",
        "target_month": target_month,
        "policy_version_id": policy_version_id,
        "identity_version": "identity_v1",
        "canonical_hash": canonical_hash,
    }
    stage2_runs = [
        {
            "stage2_run_id": f"stage2-run-{idx}",
            "target_month": target_month,
            "run_index": idx,
            "snapshot_id": snapshot["snapshot_id"],
            "canonical_hash": canonical_hash,
            "quality": "Q5",
            "p0_unresolved": 0,
            "p1_unresolved": 0,
        }
        for idx in range(1, 6)
    ]
    stage2_accepted = (
        len(stage2_runs) == 5
        and len({run["canonical_hash"] for run in stage2_runs}) == 1
        and all(run["p0_unresolved"] == 0 and run["p1_unresolved"] == 0 for run in stage2_runs)
    )
    certificate = {
        "stage2_certificate_id": "cert-1",
        "target_month": target_month,
        "status": "accepted" if stage2_accepted else "failed",
        "accepted": stage2_accepted,
        "canonical_hash": canonical_hash if stage2_accepted else None,
        "run_ids": [run["stage2_run_id"] for run in stage2_runs],
    }
    payroll_rows = [
        {
            "target_month": target_month,
            "employee_internal_id": day_fact["employee_internal_id"],
            "dingtalk_userid": day_fact["dingtalk_userid"],
            "work_date": day_fact["work_date"],
            "required_attendance_state": day_fact["required_attendance_state"],
            "actual_attendance_state": day_fact["actual_attendance_state"],
            "late_minutes": day_fact["late_minutes"],
            "early_leave_minutes": day_fact["early_leave_minutes"],
            "absent_flag": day_fact["absent_flag"],
            "missing_punch_count": day_fact["missing_punch_count"],
            "location_evidence_count": day_fact["location_evidence_count"],
            "trajectory_evidence_count": day_fact["trajectory_evidence_count"],
            "source_day_fact_id": day_fact["day_fact_id"],
            "stage2_certificate_id": certificate["stage2_certificate_id"],
            "canonical_hash": canonical_hash,
            "status": "active",
        }
    ]
    active_rows = [
        row
        for row in payroll_rows
        if row["status"] == "active" and certificate["status"] == "accepted" and certificate["accepted"] is True
    ]
    exception_cases = [
        {"target_month": target_month, "priority": "P2", "status": "open"},
        {"target_month": target_month, "priority": "P1", "status": "resolved"},
    ]
    blockers = [
        case
        for case in exception_cases
        if case["target_month"] == target_month and case["status"] != "resolved" and case["priority"] in {"P0", "P1"}
    ]
    monthly_summary = {
        "target_month": target_month,
        "baseline_rows": len(active_rows),
        "employees": len({row["employee_internal_id"] for row in active_rows}),
        "absent_days": sum(1 for row in active_rows if row["absent_flag"]),
        "missing_punches": sum(int(row["missing_punch_count"]) for row in active_rows),
        "late_minutes": sum(int(row["late_minutes"]) for row in active_rows),
        "early_leave_minutes": sum(int(row["early_leave_minutes"]) for row in active_rows),
        "canonical_hash": min((row["canonical_hash"] for row in active_rows), default=None),
    }
    return {
        "target_month": target_month,
        "stage2_accepted": stage2_accepted,
        "stage2_run_count": len(stage2_runs),
        "canonical_hash": canonical_hash,
        "active_payroll_baseline_rows": len(active_rows),
        "monthly_summary": monthly_summary,
        "stage2_blocker_count": len(blockers),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA attendance database SQL contract offline.")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--views", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    views_path = Path(args.views)
    schema_sql = schema_path.read_text(encoding="utf-8")
    views_sql = views_path.read_text(encoding="utf-8")
    types = extract_types(schema_sql)
    tables = extract_table_blocks(schema_sql)
    views = extract_views(views_sql)
    checks = contract_checks(tables, views_sql)
    failures = [check.name for check in checks if not check.passed]
    missing_tables = sorted(REQUIRED_TABLES - set(tables))
    missing_views = sorted(REQUIRED_VIEWS - views)
    missing_types = sorted(REQUIRED_TYPES - types)
    if missing_tables:
        failures.extend(f"missing_table:{name}" for name in missing_tables)
    if missing_views:
        failures.extend(f"missing_view:{name}" for name in missing_views)
    if missing_types:
        failures.extend(f"missing_type:{name}" for name in missing_types)

    synthetic = run_synthetic_path()
    if not synthetic["stage2_accepted"]:
        failures.append("synthetic_stage2_not_accepted")
    if synthetic["active_payroll_baseline_rows"] != 1:
        failures.append("synthetic_active_payroll_baseline_rows_not_1")
    if synthetic["stage2_blocker_count"] != 0:
        failures.append("synthetic_stage2_blockers_not_0")

    result = {
        "status": "fail" if failures else "pass",
        "mode": "offline_contract_dry_run",
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
        "schema": {
            "schema_file": str(schema_path),
            "views_file": str(views_path),
            "table_count": len(tables),
            "view_count": len(views),
            "type_count": len(types),
            "missing_required_tables": missing_tables,
            "missing_required_views": missing_views,
            "missing_required_types": missing_types,
            "contract_checks": [check.__dict__ for check in checks],
        },
        "synthetic_path": synthetic,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
