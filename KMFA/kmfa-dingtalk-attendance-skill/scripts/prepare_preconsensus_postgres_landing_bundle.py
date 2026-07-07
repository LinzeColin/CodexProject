#!/usr/bin/env python3
"""Prepare a pre-consensus PostgreSQL landing bundle from a Stage-2 source."""
from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Iterable


NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "kmfa-dingtalk-attendance-skill/database-landing")
TABLES = ["policy_version", "canonical_month_snapshot", "attendance_day_fact"]


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


def first_day_of_month(target_month: str) -> str:
    return f"{target_month[:4]}-{target_month[4:]}-01"


def uuid_array_from_refs(*, target_month: str, day_fact_id: str, refs: list[Any], prefix: str) -> list[str]:
    return [stable_uuid(prefix, target_month, day_fact_id, str(ref)) for ref in refs if str(ref or "").strip()]


def build_day_rows(snapshot: dict[str, Any], target_month: str, policy_version_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
            source_day_fact_id = str(day.get("source_day_fact_id") or "")
            day_fact_id = stable_uuid("attendance_day_fact", target_month, employee_id, work_date, policy_version_id)
            source_detail_refs = day.get("source_detail_ids") if isinstance(day.get("source_detail_ids"), list) else []
            source_run_refs = day.get("source_run_hashes") if isinstance(day.get("source_run_hashes"), list) else []
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
                "late_minutes": int(day.get("late_minutes") or 0),
                "early_leave_minutes": int(day.get("early_leave_minutes") or 0),
                "absent_flag": bool(day.get("absent_flag", False)),
                "missing_punch_count": int(day.get("missing_punch_count") or 0),
                "location_evidence_count": int(day.get("location_evidence_count") or 0),
                "trajectory_evidence_count": int(day.get("trajectory_evidence_count") or 0),
                "source_result_ids": uuid_array_from_refs(
                    target_month=target_month,
                    day_fact_id=source_day_fact_id or day_fact_id,
                    refs=source_run_refs,
                    prefix="source_result_ref",
                ),
                "source_detail_ids": uuid_array_from_refs(
                    target_month=target_month,
                    day_fact_id=source_day_fact_id or day_fact_id,
                    refs=source_detail_refs,
                    prefix="source_detail_ref",
                ),
            }
            rows.append({
                "day_fact_id": day_fact_id,
                **base,
                "derivation_hash": stable_hash(base),
            })
    return sorted(rows, key=lambda row: (row["employee_internal_id"], row["work_date"]))


def materialize(source_json: Path, target_month: str, out_dir: Path) -> dict[str, Any]:
    snapshot = load_json(source_json)
    require(isinstance(snapshot, dict), "source snapshot must be a JSON object")
    require(snapshot.get("target_month") == target_month, "source target_month mismatch")
    gates = snapshot.get("quality_gates") if isinstance(snapshot.get("quality_gates"), dict) else {}
    require(gates.get("raw_to_derived_reconciliation_passed") is True, "raw_to_derived_reconciliation gate must be true")
    require(gates.get("location_evidence_thresholds_passed") is True, "location_evidence_threshold gate must be true")

    out_dir.mkdir(parents=True, exist_ok=True)
    source_snapshot_hash = stable_hash(snapshot)
    policy_code = str(snapshot.get("policy_version") or "policy_v1")
    policy_version_id = stable_uuid("policy_version", policy_code)
    snapshot_id = stable_uuid("canonical_month_snapshot", target_month, source_snapshot_hash)
    policy_version = {
        "policy_version_id": policy_version_id,
        "policy_code": policy_code,
        "policy_name": f"KMFA attendance policy {policy_code}",
        "effective_from": first_day_of_month(target_month),
        "effective_to": None,
        "description": "Pre-consensus Stage-2 source landing bundle. Does not include payroll baseline acceptance.",
    }
    canonical_snapshot = {
        "snapshot_id": snapshot_id,
        "target_month": target_month,
        "policy_version_id": policy_version_id,
        "identity_version": snapshot.get("identity_version") or "identity_v1",
        "snapshot_json": snapshot,
        "canonical_hash": source_snapshot_hash,
    }
    day_rows = build_day_rows(snapshot, target_month, policy_version_id)
    require(day_rows, "no attendance_day_fact rows materialized")
    write_json(out_dir / "policy_version.json", policy_version)
    write_json(out_dir / "canonical_month_snapshot.json", canonical_snapshot)
    write_jsonl(out_dir / "attendance_day_fact.jsonl", day_rows)
    write_json(out_dir / "load_order.json", {"tables": TABLES})
    manifest = {
        "status": "READY",
        "mode": "offline_preconsensus_db_landing_bundle",
        "target_month": target_month,
        "stage2_accepted": False,
        "source_snapshot_hash": source_snapshot_hash,
        "policy_version_id": policy_version_id,
        "snapshot_id": snapshot_id,
        "attendance_day_fact_rows": len(day_rows),
        "payroll_baseline_rows": 0,
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
        "load_order": TABLES,
    }
    write_json(out_dir / "db_landing_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a pre-consensus DB landing bundle from Stage-2 source JSON.")
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    result = materialize(Path(args.source_json), args.target_month, Path(args.out_dir))
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
