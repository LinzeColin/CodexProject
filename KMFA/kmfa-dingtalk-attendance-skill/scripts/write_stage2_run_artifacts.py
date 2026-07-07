#!/usr/bin/env python3
"""Write deterministic stage-2 run artifacts from an approved replay snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonicalize(source: Path, out_dir: Path) -> str:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "canonicalize_attendance_snapshot.py"),
            str(source),
            "--out",
            str(out_dir / "canonical_snapshot.json"),
            "--sha-out",
            str(out_dir / "canonical_snapshot.sha256"),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return (out_dir / "canonical_snapshot.sha256").read_text(encoding="utf-8").strip()


def evidence_counts(snapshot: dict[str, Any]) -> tuple[int, int]:
    location = 0
    trajectory = 0
    for employee in snapshot.get("employees", []):
        if not isinstance(employee, dict):
            continue
        for day in employee.get("days", []):
            if not isinstance(day, dict):
                continue
            location += int(day.get("location_evidence_count") or 0)
            trajectory += int(day.get("trajectory_evidence_count") or 0)
    return location, trajectory


def unresolved_exceptions(snapshot: dict[str, Any]) -> dict[str, int]:
    raw = snapshot.get("unresolved_exceptions")
    if not isinstance(raw, dict):
        raw = {}
    return {
        "P0": int(raw.get("P0") or 0),
        "P1": int(raw.get("P1") or 0),
        "P2": int(raw.get("P2") or 0),
        "P3": int(raw.get("P3") or 0),
    }


def quality_grade(location_count: int, trajectory_count: int, unresolved: dict[str, int]) -> str:
    if unresolved["P0"] or unresolved["P1"]:
        return "Q4"
    if location_count > 0 and trajectory_count > 0:
        return "Q5"
    return "Q4"


def quality_gates(snapshot: dict[str, Any], location_count: int) -> dict[str, bool]:
    source = snapshot.get("quality_gates") if isinstance(snapshot.get("quality_gates"), dict) else {}
    return {
        "location_evidence_thresholds_passed": bool(
            source.get("location_evidence_thresholds_passed")
            if "location_evidence_thresholds_passed" in source
            else location_count > 0
        ),
        "raw_to_derived_reconciliation_passed": bool(source.get("raw_to_derived_reconciliation_passed")),
        "database_transaction_committed": bool(source.get("database_transaction_committed")),
        "database_transaction_verified": bool(source.get("database_transaction_verified")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write one offline stage-2 run artifact set.")
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--run-index", required=True, type=int)
    parser.add_argument("--run-slot", default="evening", choices=["evening"])
    parser.add_argument("--database-transaction-marker", default="")
    args = parser.parse_args()

    if args.run_index < 1 or args.run_index > 5:
        raise SystemExit("run-index must be in 1..5")

    source = Path(args.source_json)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = load_json(source)
    if snapshot.get("target_month") != args.target_month:
        raise SystemExit(f"source target_month {snapshot.get('target_month')} does not match {args.target_month}")

    digest = canonicalize(source, out_dir)
    location_count, trajectory_count = evidence_counts(snapshot)
    unresolved = unresolved_exceptions(snapshot)
    grade = quality_grade(location_count, trajectory_count, unresolved)
    gates = quality_gates(snapshot, location_count)
    source_hash = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    marker = args.database_transaction_marker or f"offline-replay:{digest.removeprefix('sha256:')[:16]}"

    manifest = {
        "run_id": f"{args.target_month}-stage2-run-{args.run_index:02d}",
        "skill_name": "kmfa-dingtalk-attendance-skill",
        "run_slot": args.run_slot,
        "target_month": args.target_month,
        "stage2_run_index": args.run_index,
        "source_batches": snapshot.get("source_batch_hashes") or [source_hash],
        "raw_hashes": snapshot.get("source_batch_hashes") or [source_hash],
        "database_transaction_marker": marker,
        "canonical_snapshot_hash": digest,
        "quality_grade": grade,
        "unresolved_exceptions": unresolved,
        "quality_gates": gates,
        "stage2_status": "pending",
        "artifact_written_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "artifact_mode": "offline_replay",
    }
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(
        out_dir / "quality_report.json",
        {
            "target_month": args.target_month,
            "stage2_run_index": args.run_index,
            "quality_grade": grade,
            "location_evidence_count": location_count,
            "trajectory_evidence_count": trajectory_count,
            "canonical_snapshot_hash": digest,
            "quality_gates": gates,
        },
    )
    write_json(
        out_dir / "exception_report.json",
        {
            "target_month": args.target_month,
            "stage2_run_index": args.run_index,
            "unresolved_exceptions": unresolved,
        },
    )
    write_json(out_dir / "payroll_baseline_candidate.json", snapshot.get("payroll_baseline_candidate") or [])
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
