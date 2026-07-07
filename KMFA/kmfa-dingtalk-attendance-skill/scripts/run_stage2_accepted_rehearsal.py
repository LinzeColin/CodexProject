#!/usr/bin/env python3
"""Run an offline five-run Stage-2 accepted rehearsal from a DB-verified source."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"json_object_required:{path.name}")
    return data


def run_json(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        if proc.stdout:
            print(proc.stdout, file=sys.stderr, end="")
        raise SystemExit(proc.returncode)
    return json.loads(proc.stdout)


def run_quiet(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        if proc.stdout:
            print(proc.stdout, file=sys.stderr, end="")
        raise SystemExit(proc.returncode)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require_db_verified_source(source: dict[str, Any], target_month: str) -> None:
    if source.get("target_month") != target_month:
        raise SystemExit("source_target_month_mismatch")
    gates = source.get("quality_gates") if isinstance(source.get("quality_gates"), dict) else {}
    required = [
        "location_evidence_thresholds_passed",
        "raw_to_derived_reconciliation_passed",
        "database_transaction_committed",
        "database_transaction_verified",
    ]
    for key in required:
        if gates.get(key) is not True:
            raise SystemExit(f"source_quality_gate_not_true:{key}")
    marker = str(source.get("database_transaction_marker") or "").strip()
    if not marker.startswith("postgres-nonprod:"):
        raise SystemExit("database_transaction_marker_missing_or_invalid")
    proof = source.get("database_execution_proof") if isinstance(source.get("database_execution_proof"), dict) else {}
    if proof.get("state_counts_verified") is not True:
        raise SystemExit("database_execution_proof_state_counts_not_verified")
    if not proof.get("proof_hash") or not proof.get("state_verification_hash"):
        raise SystemExit("database_execution_proof_hash_missing")
    if proof.get("live_dws_performed") is not False:
        raise SystemExit("database_execution_proof_live_dws_not_false")


def run_rehearsal(source_json: Path, target_month: str, out_root: Path) -> dict[str, Any]:
    source = load_json(source_json)
    require_db_verified_source(source, target_month)
    stage2_root = out_root / "stage2" / target_month
    db_landing_dir = out_root / "db_landing" / target_month
    stage2_root.mkdir(parents=True, exist_ok=True)
    db_landing_dir.mkdir(parents=True, exist_ok=True)

    for run_index in range(1, 6):
        run_dir = stage2_root / f"run_{run_index:02d}"
        run_quiet([
            sys.executable,
            str(SCRIPT_DIR / "write_stage2_run_artifacts.py"),
            "--source-json",
            str(source_json),
            "--out-dir",
            str(run_dir),
            "--target-month",
            target_month,
            "--run-index",
            str(run_index),
        ])

    certificate = run_json([
        sys.executable,
        str(SCRIPT_DIR / "stage2_consensus_gate.py"),
        "--stage2-root",
        str(stage2_root),
        "--target-month",
        target_month,
        "--min-quality",
        "Q4",
    ])
    if certificate.get("accepted") is not True:
        raise SystemExit("stage2_consensus_not_accepted")

    db_landing = run_json([
        sys.executable,
        str(SCRIPT_DIR / "prepare_database_landing_bundle.py"),
        "--stage2-root",
        str(stage2_root),
        "--target-month",
        target_month,
        "--out-dir",
        str(db_landing_dir),
        "--print-json",
    ])
    load_plan = run_json([
        sys.executable,
        str(SCRIPT_DIR / "prepare_postgres_landing_loader.py"),
        "--bundle-dir",
        str(db_landing_dir),
        "--print-json",
    ])
    validation = run_json([
        sys.executable,
        str(SCRIPT_DIR / "validate_postgres_load_plan.py"),
        "--schema",
        str(SKILL_DIR / "database" / "postgres_schema.sql"),
        "--bundle-dir",
        str(db_landing_dir),
        "--print-json",
    ])

    return {
        "status": "READY",
        "mode": "offline_stage2_accepted_rehearsal",
        "target_month": target_month,
        "source_hash": sha256_file(source_json),
        "accepted": True,
        "stage2_run_count": 5,
        "canonical_snapshot_hash": certificate.get("canonical_snapshot_hash"),
        "db_landing_status": db_landing.get("status"),
        "stage2_certificate_id": db_landing.get("stage2_certificate_id"),
        "attendance_day_fact_rows": db_landing.get("attendance_day_fact_rows"),
        "payroll_baseline_rows": db_landing.get("payroll_baseline_rows"),
        "postgres_load_plan_status": load_plan.get("status"),
        "postgres_load_plan_validation_status": validation.get("status"),
        "postgres_load_plan_tables": validation.get("tables_checked"),
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a private offline Stage-2 accepted rehearsal from a DB-verified source.")
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    result = run_rehearsal(Path(args.source_json), args.target_month, Path(args.out_root))
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
