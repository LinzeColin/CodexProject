#!/usr/bin/env python3
"""Generate an offline PostgreSQL load plan for a KMFA DB landing bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


TABLES = [
    "policy_version",
    "canonical_month_snapshot",
    "stage2_shadow_run",
    "stage2_consensus_certificate",
    "attendance_day_fact",
    "payroll_baseline_attendance",
]
SUPPORTED_TABLES = set(TABLES)

SINGLE_ROW_FILES = {
    "policy_version": "policy_version.json",
    "canonical_month_snapshot": "canonical_month_snapshot.json",
    "stage2_consensus_certificate": "stage2_consensus_certificate.json",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_table_rows(bundle_dir: Path, table: str) -> list[dict[str, Any]]:
    if table in SINGLE_ROW_FILES:
        data = load_json(bundle_dir / SINGLE_ROW_FILES[table])
        if not isinstance(data, dict):
            raise SystemExit(f"{SINGLE_ROW_FILES[table]} must contain a JSON object")
        return [data]
    path = bundle_dir / f"{table}.jsonl"
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise SystemExit(f"{path.name}:{line_no} must contain a JSON object")
            rows.append(row)
    return rows


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def temp_name(table: str) -> str:
    return "_kmfa_load_" + table


def json_array_uuid_expr(payload_key: str) -> str:
    return (
        "COALESCE(ARRAY("
        f"SELECT jsonb_array_elements_text(payload->'{payload_key}')::uuid"
        "), '{}'::uuid[])"
    )


def insert_sql(table: str) -> str:
    temp = temp_name(table)
    if table == "policy_version":
        return f"""INSERT INTO policy_version (
  policy_version_id, policy_code, policy_name, effective_from, effective_to, description
)
SELECT
  (payload->>'policy_version_id')::uuid,
  payload->>'policy_code',
  payload->>'policy_name',
  (payload->>'effective_from')::date,
  NULLIF(payload->>'effective_to', '')::date,
  payload->>'description'
FROM {temp}
ON CONFLICT (policy_code, effective_from) DO NOTHING;"""
    if table == "canonical_month_snapshot":
        return f"""INSERT INTO canonical_month_snapshot (
  snapshot_id, target_month, policy_version_id, identity_version, snapshot_json, canonical_hash
)
SELECT
  (payload->>'snapshot_id')::uuid,
  payload->>'target_month',
  (payload->>'policy_version_id')::uuid,
  payload->>'identity_version',
  payload->'snapshot_json',
  payload->>'canonical_hash'
FROM {temp}
ON CONFLICT (target_month, policy_version_id, identity_version, canonical_hash) DO NOTHING;"""
    if table == "stage2_shadow_run":
        return f"""INSERT INTO stage2_shadow_run (
  stage2_run_id, target_month, run_index, run_slot, snapshot_id, canonical_hash,
  quality, p0_unresolved, p1_unresolved, run_manifest
)
SELECT
  (payload->>'stage2_run_id')::uuid,
  payload->>'target_month',
  (payload->>'run_index')::integer,
  (payload->>'run_slot')::run_slot,
  (payload->>'snapshot_id')::uuid,
  payload->>'canonical_hash',
  (payload->>'quality')::quality_grade,
  (payload->>'p0_unresolved')::integer,
  (payload->>'p1_unresolved')::integer,
  payload->'run_manifest'
FROM {temp}
ON CONFLICT (target_month, run_index) DO NOTHING;"""
    if table == "stage2_consensus_certificate":
        return f"""INSERT INTO stage2_consensus_certificate (
  stage2_certificate_id, target_month, status, accepted, canonical_hash, run_ids, certificate_json
)
SELECT
  (payload->>'stage2_certificate_id')::uuid,
  payload->>'target_month',
  (payload->>'status')::stage2_status,
  (payload->>'accepted')::boolean,
  payload->>'canonical_hash',
  {json_array_uuid_expr("run_ids")},
  payload->'certificate_json'
FROM {temp}
ON CONFLICT (target_month, status, canonical_hash) DO NOTHING;"""
    if table == "attendance_day_fact":
        return f"""INSERT INTO attendance_day_fact (
  day_fact_id, target_month, employee_internal_id, dingtalk_userid, work_date,
  policy_version_id, required_attendance_state, actual_attendance_state,
  first_in_time, last_out_time, late_minutes, early_leave_minutes, absent_flag,
  missing_punch_count, location_evidence_count, trajectory_evidence_count,
  source_result_ids, source_detail_ids, derivation_hash
)
SELECT
  (payload->>'day_fact_id')::uuid,
  payload->>'target_month',
  payload->>'employee_internal_id',
  payload->>'dingtalk_userid',
  (payload->>'work_date')::date,
  (payload->>'policy_version_id')::uuid,
  payload->>'required_attendance_state',
  payload->>'actual_attendance_state',
  NULLIF(payload->>'first_in_time', '')::timestamptz,
  NULLIF(payload->>'last_out_time', '')::timestamptz,
  (payload->>'late_minutes')::integer,
  (payload->>'early_leave_minutes')::integer,
  (payload->>'absent_flag')::boolean,
  (payload->>'missing_punch_count')::integer,
  (payload->>'location_evidence_count')::integer,
  (payload->>'trajectory_evidence_count')::integer,
  {json_array_uuid_expr("source_result_ids")},
  {json_array_uuid_expr("source_detail_ids")},
  payload->>'derivation_hash'
FROM {temp}
ON CONFLICT (target_month, employee_internal_id, work_date, policy_version_id) DO NOTHING;"""
    if table == "payroll_baseline_attendance":
        return f"""INSERT INTO payroll_baseline_attendance (
  payroll_baseline_id, target_month, employee_internal_id, dingtalk_userid,
  work_date, required_attendance_state, actual_attendance_state, first_in_time,
  last_out_time, late_minutes, early_leave_minutes, absent_flag,
  missing_punch_count, location_result, location_evidence_count,
  trajectory_evidence_count, source_day_fact_id, stage2_certificate_id,
  canonical_hash, baseline_version, status
)
SELECT
  (payload->>'payroll_baseline_id')::uuid,
  payload->>'target_month',
  payload->>'employee_internal_id',
  payload->>'dingtalk_userid',
  (payload->>'work_date')::date,
  payload->>'required_attendance_state',
  payload->>'actual_attendance_state',
  NULLIF(payload->>'first_in_time', '')::timestamptz,
  NULLIF(payload->>'last_out_time', '')::timestamptz,
  (payload->>'late_minutes')::integer,
  (payload->>'early_leave_minutes')::integer,
  (payload->>'absent_flag')::boolean,
  (payload->>'missing_punch_count')::integer,
  payload->>'location_result',
  (payload->>'location_evidence_count')::integer,
  (payload->>'trajectory_evidence_count')::integer,
  (payload->>'source_day_fact_id')::uuid,
  (payload->>'stage2_certificate_id')::uuid,
  payload->>'canonical_hash',
  (payload->>'baseline_version')::integer,
  payload->>'status'
FROM {temp}
ON CONFLICT (target_month, employee_internal_id, work_date, baseline_version) DO NOTHING;"""
    raise SystemExit(f"unsupported table: {table}")


def write_payloads(bundle_dir: Path, payload_dir: Path, tables: list[str]) -> dict[str, dict[str, Any]]:
    payload_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict[str, Any]] = {}
    for table in tables:
        rows = load_table_rows(bundle_dir, table)
        if not rows:
            raise SystemExit(f"{table} has no rows")
        path = payload_dir / f"{table}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        result[table] = {"rows": len(rows), "path": str(path), "sha256": file_hash(path)}
    return result


def write_sql(path: Path, payload_info: dict[str, dict[str, Any]], tables: list[str]) -> None:
    lines = [
        "-- KMFA attendance PostgreSQL load plan generated offline.",
        "-- Review and run only against an explicitly approved PostgreSQL target.",
        "-- Required first: database/postgres_schema.sql and database/views_payroll_baseline.sql.",
        "\\set ON_ERROR_STOP on",
        "BEGIN;",
        "SET search_path TO kmfa_attendance, public;",
        "",
    ]
    for table in tables:
        temp = temp_name(table)
        payload_path = Path(str(payload_info[table]["path"])).resolve()
        lines.extend([
            f"CREATE TEMP TABLE {temp} (payload jsonb) ON COMMIT DROP;",
            f"\\copy {temp}(payload) FROM {sql_quote(str(payload_path))};",
            insert_sql(table),
            "",
        ])
    lines.append("COMMIT;")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a PostgreSQL load plan for a KMFA DB landing bundle.")
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    bundle_dir = Path(args.bundle_dir)
    out_dir = Path(args.out_dir) if args.out_dir else bundle_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_json(bundle_dir / "db_landing_manifest.json")
    if manifest.get("status") != "READY":
        raise SystemExit("db_landing_manifest status is not READY")
    if manifest.get("database_mutation_performed") is not False or manifest.get("postgres_connection_used") is not False:
        raise SystemExit("landing bundle must be offline before generating a load plan")
    load_order = load_json(bundle_dir / "load_order.json")
    tables = load_order.get("tables")
    if not isinstance(tables, list) or not tables:
        raise SystemExit("load_order.json must contain a non-empty tables list")
    if any(table not in SUPPORTED_TABLES for table in tables):
        raise SystemExit("load_order.json contains unsupported tables")
    if tables != [table for table in TABLES if table in tables]:
        raise SystemExit("load_order.json does not follow approved loader order")

    payload_info = write_payloads(bundle_dir, out_dir / "postgres_load_payloads", tables)
    sql_path = out_dir / "postgres_load_plan.sql"
    write_sql(sql_path, payload_info, tables)
    result = {
        "status": "READY",
        "mode": "offline_postgres_load_plan",
        "tables": tables,
        "bundle_dir": str(bundle_dir),
        "postgres_load_plan_sql": str(sql_path),
        "payloads": payload_info,
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }
    write_json(out_dir / "postgres_load_plan_manifest.json", result)
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
