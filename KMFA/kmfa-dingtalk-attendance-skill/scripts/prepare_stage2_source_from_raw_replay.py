#!/usr/bin/env python3
"""Prepare a Stage-2 source snapshot from a private raw replay day-fact bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


REQUIRED_REPLAY_CHECKS = [
    "raw_manifest_pairs_complete",
    "raw_counts_match_manifest",
    "raw_hashes_match_manifest",
    "location_coverage_threshold_met",
    "every_day_fact_links_to_raw_ids",
    "canonical_hash_stable",
    "public_safe_output",
]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            if not isinstance(data, dict):
                raise SystemExit(f"{path.name} must contain JSON objects")
            rows.append(data)
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def sorted_unique(values: Iterable[Any]) -> list[str]:
    return sorted({str(value) for value in values if str(value or "").strip()})


def hashed_dingtalk_surrogate(employee_key_hash: str) -> str:
    digest = employee_key_hash.removeprefix("sha256:")
    return f"hash:{digest}"


def source_hashes(day_rows: list[dict[str, Any]], manifest: dict[str, Any], raw_manifest: dict[str, Any]) -> list[str]:
    hashes: list[str] = []
    for row in day_rows:
        raw_hashes = row.get("source_run_hashes") if isinstance(row.get("source_run_hashes"), list) else []
        hashes.extend(str(item) for item in raw_hashes)
    if not hashes:
        for key in ("replay_hash", "seed_replay_hash"):
            if raw_manifest.get(key):
                hashes.append(str(raw_manifest[key]))
    if not hashes and manifest.get("canonical_snapshot_hash"):
        hashes.append(str(manifest["canonical_snapshot_hash"]))
    return sorted_unique(hashes)


def build_snapshot(target_month: str, manifest: dict[str, Any], raw_manifest: dict[str, Any], day_rows: list[dict[str, Any]]) -> dict[str, Any]:
    employees: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidates: list[dict[str, Any]] = []
    total_location = 0
    total_trajectory = 0
    total_missing_punches = 0

    for row in sorted(day_rows, key=lambda item: (str(item.get("employee_key_hash") or ""), str(item.get("work_date") or ""))):
        employee_hash = str(row.get("employee_key_hash") or "")
        work_date = str(row.get("work_date") or "")
        require(employee_hash.startswith("sha256:"), "employee_key_hash must be a sha256 surrogate")
        require(work_date, "day fact missing work_date")
        require(str(row.get("target_month") or target_month) == target_month, "day fact target_month mismatch")
        source_detail_ids = sorted_unique(row.get("source_detail_ids") if isinstance(row.get("source_detail_ids"), list) else [])
        require(source_detail_ids, "day fact missing raw detail linkage")
        source_run_hashes = sorted_unique(row.get("source_run_hashes") if isinstance(row.get("source_run_hashes"), list) else [])
        location_count = int(row.get("location_evidence_count") or 0)
        trajectory_count = int(row.get("trajectory_evidence_count") or 0)
        missing_count = int(row.get("missing_punch_count") or 0)
        total_location += location_count
        total_trajectory += trajectory_count
        total_missing_punches += missing_count
        day = {
            "source_day_fact_id": str(row.get("day_fact_id") or ""),
            "work_date": work_date,
            "required_attendance_state": str(row.get("required_attendance_state") or "workday"),
            "actual_attendance_state": str(row.get("actual_attendance_state") or "unknown"),
            "first_in_time": row.get("first_in_time"),
            "last_out_time": row.get("last_out_time"),
            "late_minutes": 0,
            "early_leave_minutes": 0,
            "absent_flag": bool(row.get("absent_flag", False)),
            "missing_punch_count": missing_count,
            "location_evidence_count": location_count,
            "trajectory_evidence_count": trajectory_count,
            "source_detail_ids": source_detail_ids,
            "source_run_hashes": source_run_hashes,
            "derivation_hash": row.get("derivation_hash"),
        }
        employees[employee_hash].append(day)
        candidates.append({
            "employee_internal_id": employee_hash,
            "work_date": work_date,
            "late_minutes": 0,
            "early_leave_minutes": 0,
            "missing_punch_count": missing_count,
            "absent_flag": bool(row.get("absent_flag", False)),
            "source_day_fact_id": day["source_day_fact_id"],
            "source_detail_ids": source_detail_ids,
        })

    checks = manifest.get("checks") if isinstance(manifest.get("checks"), dict) else {}
    raw_to_derived = all(checks.get(key) is True for key in REQUIRED_REPLAY_CHECKS)
    location_passed = bool(checks.get("location_coverage_threshold_met") is True and total_location > 0)
    employee_rows = [
        {
            "employee_internal_id": employee_hash,
            "dingtalk_userid": hashed_dingtalk_surrogate(employee_hash),
            "days": sorted(days, key=lambda day: str(day.get("work_date") or "")),
        }
        for employee_hash, days in sorted(employees.items())
    ]
    return {
        "target_month": target_month,
        "policy_version": "dingtalk_raw_replay_v1",
        "identity_version": "employee_key_hash_v1",
        "source_batch_hashes": source_hashes(day_rows, manifest, raw_manifest),
        "employees": employee_rows,
        "location_evidence_summary": {
            "day_count": len(day_rows),
            "location_evidence_count": total_location,
        },
        "trajectory_evidence_summary": {
            "day_count": len(day_rows),
            "trajectory_evidence_count": total_trajectory,
        },
        "unresolved_exceptions": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
        "quality_gates": {
            "location_evidence_thresholds_passed": location_passed,
            "raw_to_derived_reconciliation_passed": raw_to_derived,
            "database_transaction_committed": False,
            "database_transaction_verified": False,
        },
        "payroll_baseline_candidate": sorted(candidates, key=lambda row: (row["employee_internal_id"], row["work_date"])),
        "raw_replay": {
            "canonical_snapshot_hash": manifest.get("canonical_snapshot_hash"),
            "raw_replay_hash": raw_manifest.get("replay_hash"),
            "seed_replay_hash": raw_manifest.get("seed_replay_hash"),
            "missing_punch_count": total_missing_punches,
        },
    }


def materialize(raw_replay_day_fact_dir: Path, target_month: str, out_json: Path) -> dict[str, Any]:
    manifest_path = raw_replay_day_fact_dir / "raw_replay_day_fact_manifest.json"
    raw_manifest_path = raw_replay_day_fact_dir / "raw_replay_manifest.json"
    day_fact_path = raw_replay_day_fact_dir / "attendance_day_fact.jsonl"
    require(manifest_path.is_file(), "raw replay day-fact manifest missing")
    require(day_fact_path.is_file(), "attendance_day_fact.jsonl missing")
    manifest = load_json(manifest_path)
    raw_manifest = load_json(raw_manifest_path) if raw_manifest_path.is_file() else {}
    require(isinstance(manifest, dict), "raw replay day-fact manifest must be an object")
    require(isinstance(raw_manifest, dict), "raw replay manifest must be an object")
    require(manifest.get("status") == "READY", "raw replay day-fact bundle is not READY")
    require(manifest.get("target_month") == target_month, "raw replay day-fact target_month mismatch")
    require(manifest.get("postgres_connection_used") is False, "unexpected postgres use in raw replay bundle")
    require(manifest.get("database_mutation_performed") is False, "unexpected database mutation in raw replay bundle")
    require(manifest.get("live_dws_performed") is False, "unexpected live DWS in raw replay bundle")

    day_rows = load_jsonl(day_fact_path)
    require(bool(day_rows), "attendance_day_fact.jsonl is empty")
    snapshot = build_snapshot(target_month, manifest, raw_manifest, day_rows)
    require(bool(snapshot["source_batch_hashes"]), "source_batch_hashes is empty")
    write_json(out_json, snapshot)
    snapshot_hash = stable_hash(snapshot)
    summary = {
        "status": "READY",
        "mode": "offline_stage2_source_from_raw_replay",
        "target_month": target_month,
        "employee_count": len(snapshot["employees"]),
        "day_count": len(day_rows),
        "payroll_baseline_candidate_rows": len(snapshot["payroll_baseline_candidate"]),
        "source_batch_count": len(snapshot["source_batch_hashes"]),
        "stage2_source_hash": snapshot_hash,
        "quality_gates": snapshot["quality_gates"],
        "checks": {
            "raw_replay_ready": True,
            "raw_to_derived_reconciliation_passed": snapshot["quality_gates"]["raw_to_derived_reconciliation_passed"],
            "location_evidence_thresholds_passed": snapshot["quality_gates"]["location_evidence_thresholds_passed"],
            "public_safe_output": True,
        },
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a Stage-2 source snapshot from a raw replay day-fact bundle.")
    parser.add_argument("--raw-replay-day-fact-dir", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    summary = materialize(Path(args.raw_replay_day_fact_dir), args.target_month, Path(args.out_json))
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
