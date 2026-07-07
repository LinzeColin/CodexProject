#!/usr/bin/env python3
"""Prepare an offline PostgreSQL landing bundle from accepted stage-2 artifacts.

The bundle is written to the caller-provided private runtime folder. It does not
connect to PostgreSQL, mutate a database, read live DWS, or write SQLite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable


NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "kmfa-dingtalk-attendance-skill/database-landing")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def stable_uuid(*parts: Any) -> str:
    return str(uuid.uuid5(NAMESPACE, ":".join(str(part) for part in parts)))


def stable_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def load_accepted_certificate(stage2_root: Path, target_month: str) -> dict[str, Any]:
    cert_path = stage2_root / "stage2_consensus_certificate.json"
    require(cert_path.is_file(), f"stage2 certificate missing: {cert_path}")
    cert = load_json(cert_path)
    require(isinstance(cert, dict), "stage2 certificate must be a JSON object")
    require(cert.get("target_month") == target_month, "stage2 certificate target_month mismatch")
    require(cert.get("accepted") is True and cert.get("stage2_status") == "accepted", "stage2 certificate is not accepted")
    require(bool(cert.get("canonical_snapshot_hash")), "accepted certificate missing canonical_snapshot_hash")
    return cert


def load_stage2_runs(stage2_root: Path, target_month: str, canonical_hash: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    snapshot: dict[str, Any] | None = None
    snapshot_id = stable_uuid("canonical_month_snapshot", target_month, canonical_hash)
    for run_index in range(1, 6):
        run_dir = stage2_root / f"run_{run_index:02d}"
        manifest_path = run_dir / "run_manifest.json"
        snapshot_path = run_dir / "canonical_snapshot.json"
        require(manifest_path.is_file(), f"run manifest missing: {manifest_path}")
        require(snapshot_path.is_file(), f"canonical snapshot missing: {snapshot_path}")
        manifest = load_json(manifest_path)
        current_snapshot = load_json(snapshot_path)
        require(isinstance(manifest, dict), f"run manifest must be object: {manifest_path}")
        require(isinstance(current_snapshot, dict), f"canonical snapshot must be object: {snapshot_path}")
        require(manifest.get("target_month") == target_month, f"run_{run_index:02d} target_month mismatch")
        require(manifest.get("stage2_run_index") == run_index, f"run_{run_index:02d} run_index mismatch")
        require(manifest.get("canonical_snapshot_hash") == canonical_hash, f"run_{run_index:02d} canonical hash mismatch")
        unresolved = manifest.get("unresolved_exceptions", {}) if isinstance(manifest.get("unresolved_exceptions"), dict) else {}
        rows.append({
            "stage2_run_id": stable_uuid("stage2_shadow_run", target_month, run_index, canonical_hash),
            "target_month": target_month,
            "run_index": run_index,
            "run_slot": manifest.get("run_slot") or "evening",
            "snapshot_id": snapshot_id,
            "canonical_hash": canonical_hash,
            "quality": manifest.get("quality_grade"),
            "p0_unresolved": int(unresolved.get("P0") or 0),
            "p1_unresolved": int(unresolved.get("P1") or 0),
            "run_manifest": manifest,
        })
        if snapshot is None:
            snapshot = current_snapshot
    require(snapshot is not None, "no canonical snapshot loaded")
    return rows, snapshot


def candidate_index(snapshot: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in snapshot.get("payroll_baseline_candidate") or []:
        if isinstance(row, dict):
            employee = str(row.get("employee_internal_id") or "")
            work_date = str(row.get("work_date") or "")
            if employee and work_date:
                index[(employee, work_date)] = row
    return index


def build_day_and_payroll_rows(
    snapshot: dict[str, Any],
    target_month: str,
    canonical_hash: str,
    stage2_certificate_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    policy_version = str(snapshot.get("policy_version") or "policy_v1")
    policy_version_id = stable_uuid("policy_version", policy_version)
    candidates = candidate_index(snapshot)
    day_rows: list[dict[str, Any]] = []
    payroll_rows: list[dict[str, Any]] = []
    for employee in snapshot.get("employees") or []:
        if not isinstance(employee, dict):
            continue
        employee_id = str(employee.get("employee_internal_id") or "")
        dingtalk_userid = str(employee.get("dingtalk_userid") or "")
        if not employee_id or not dingtalk_userid:
            continue
        for day in employee.get("days") or []:
            if not isinstance(day, dict):
                continue
            work_date = str(day.get("work_date") or "")
            if not work_date:
                continue
            candidate = candidates.get((employee_id, work_date), {})
            day_fact_id = stable_uuid("attendance_day_fact", target_month, employee_id, work_date, policy_version_id)
            base = {
                "target_month": target_month,
                "employee_internal_id": employee_id,
                "dingtalk_userid": dingtalk_userid,
                "work_date": work_date,
                "policy_version_id": policy_version_id,
                "required_attendance_state": str(day.get("required_attendance_state") or "workday"),
                "actual_attendance_state": str(day.get("actual_attendance_state") or "unknown"),
                "first_in_time": day.get("first_in_time"),
                "last_out_time": day.get("last_out_time"),
                "late_minutes": int(candidate.get("late_minutes", day.get("late_minutes", 0)) or 0),
                "early_leave_minutes": int(candidate.get("early_leave_minutes", day.get("early_leave_minutes", 0)) or 0),
                "absent_flag": bool(day.get("absent_flag", False)),
                "missing_punch_count": int(day.get("missing_punch_count", 0) or 0),
                "location_evidence_count": int(day.get("location_evidence_count", 0) or 0),
                "trajectory_evidence_count": int(day.get("trajectory_evidence_count", 0) or 0),
            }
            day_row = {
                "day_fact_id": day_fact_id,
                **base,
                "source_result_ids": [],
                "source_detail_ids": [],
                "derivation_hash": stable_hash(base),
            }
            day_rows.append(day_row)
            payroll_rows.append({
                "payroll_baseline_id": stable_uuid("payroll_baseline_attendance", target_month, employee_id, work_date, canonical_hash),
                **base,
                "location_result": day.get("location_result"),
                "source_day_fact_id": day_fact_id,
                "stage2_certificate_id": stage2_certificate_id,
                "canonical_hash": canonical_hash,
                "baseline_version": 1,
                "status": "active",
            })
    return day_rows, payroll_rows


def first_day_of_month(target_month: str) -> str:
    return f"{target_month[:4]}-{target_month[4:]}-01"


def write_copy_manifest(path: Path, tables: list[str]) -> None:
    lines = [
        "-- Offline load manifest for KMFA attendance database landing.",
        "-- Run database/postgres_schema.sql and database/views_payroll_baseline.sql first.",
        "-- Execute only against an explicitly approved PostgreSQL target.",
        "SET search_path TO kmfa_attendance, public;",
        "",
    ]
    for table in tables:
        source = f"{table}.json" if table in {"canonical_month_snapshot", "stage2_consensus_certificate"} else f"{table}.jsonl"
        lines.append(f"-- Load {source} into {table} with your approved JSONB/COPY loader.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare offline DB landing bundle from accepted KMFA stage-2 artifacts.")
    parser.add_argument("--stage2-root", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    stage2_root = Path(args.stage2_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cert = load_accepted_certificate(stage2_root, args.target_month)
    canonical_hash = str(cert["canonical_snapshot_hash"])
    stage2_runs, snapshot = load_stage2_runs(stage2_root, args.target_month, canonical_hash)
    snapshot_id = stable_uuid("canonical_month_snapshot", args.target_month, canonical_hash)
    policy_code = str(snapshot.get("policy_version") or "policy_v1")
    policy_version_id = stable_uuid("policy_version", policy_code)
    stage2_certificate_id = stable_uuid("stage2_consensus_certificate", args.target_month, canonical_hash)
    day_rows, payroll_rows = build_day_and_payroll_rows(snapshot, args.target_month, canonical_hash, stage2_certificate_id)
    require(day_rows, "no attendance_day_fact rows materialized")
    require(payroll_rows, "no payroll_baseline_attendance rows materialized")

    canonical_snapshot_row = {
        "snapshot_id": snapshot_id,
        "target_month": args.target_month,
        "policy_version_id": policy_version_id,
        "identity_version": snapshot.get("identity_version") or "identity_v1",
        "snapshot_json": snapshot,
        "canonical_hash": canonical_hash,
    }
    policy_version_row = {
        "policy_version_id": policy_version_id,
        "policy_code": policy_code,
        "policy_name": f"KMFA attendance policy {policy_code}",
        "effective_from": first_day_of_month(args.target_month),
        "effective_to": None,
        "description": "Materialized from accepted KMFA DingTalk attendance stage-2 landing bundle.",
    }
    certificate_row = {
        "stage2_certificate_id": stage2_certificate_id,
        "target_month": args.target_month,
        "status": "accepted",
        "accepted": True,
        "canonical_hash": canonical_hash,
        "run_ids": [row["stage2_run_id"] for row in stage2_runs],
        "certificate_json": cert,
    }
    tables = [
        "policy_version",
        "canonical_month_snapshot",
        "stage2_shadow_run",
        "stage2_consensus_certificate",
        "attendance_day_fact",
        "payroll_baseline_attendance",
    ]
    write_json(out_dir / "policy_version.json", policy_version_row)
    write_json(out_dir / "canonical_month_snapshot.json", canonical_snapshot_row)
    write_jsonl(out_dir / "stage2_shadow_run.jsonl", stage2_runs)
    write_json(out_dir / "stage2_consensus_certificate.json", certificate_row)
    write_jsonl(out_dir / "attendance_day_fact.jsonl", day_rows)
    write_jsonl(out_dir / "payroll_baseline_attendance.jsonl", payroll_rows)
    write_json(out_dir / "load_order.json", {"tables": tables})
    write_copy_manifest(out_dir / "postgres_copy_manifest.sql", tables)

    manifest = {
        "status": "READY",
        "mode": "offline_db_landing_bundle",
        "target_month": args.target_month,
        "stage2_accepted": True,
        "stage2_run_count": len(stage2_runs),
        "stage2_certificate_id": stage2_certificate_id,
        "policy_version_id": policy_version_id,
        "canonical_snapshot_hash": canonical_hash,
        "attendance_day_fact_rows": len(day_rows),
        "payroll_baseline_rows": len(payroll_rows),
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
        "private_output_dir": str(out_dir),
        "load_order": tables,
    }
    write_json(out_dir / "db_landing_manifest.json", manifest)
    if args.print_json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
