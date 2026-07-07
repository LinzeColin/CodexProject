#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return p


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_raw_replay_day_fact_bundle(folder: Path) -> None:
    folder.mkdir(parents=True)
    raw_hash = "sha256:" + "1" * 64
    day_rows = [
        {
            "day_fact_id": "day-001",
            "target_month": "202607",
            "employee_key_hash": "sha256:" + "a" * 64,
            "work_date": "2026-07-01",
            "required_attendance_state": "workday",
            "actual_attendance_state": "present",
            "first_in_time": "2026-07-01 08:31:00",
            "last_out_time": "2026-07-01 18:31:00",
            "missing_punch_count": 0,
            "location_evidence_count": 1,
            "trajectory_evidence_count": 1,
            "source_detail_ids": ["detail-001-a", "detail-001-b"],
            "source_run_hashes": [raw_hash],
            "derivation_hash": "sha256:" + "2" * 64,
        },
        {
            "day_fact_id": "day-002",
            "target_month": "202607",
            "employee_key_hash": "sha256:" + "a" * 64,
            "work_date": "2026-07-02",
            "required_attendance_state": "workday",
            "actual_attendance_state": "incomplete",
            "first_in_time": "2026-07-02 08:35:00",
            "last_out_time": "2026-07-02 08:35:00",
            "missing_punch_count": 1,
            "location_evidence_count": 1,
            "trajectory_evidence_count": 1,
            "source_detail_ids": ["detail-002-a"],
            "source_run_hashes": [raw_hash],
            "derivation_hash": "sha256:" + "3" * 64,
        },
    ]
    write_jsonl(folder / "attendance_day_fact.jsonl", day_rows)
    write_json(
        folder / "raw_replay_day_fact_manifest.json",
        {
            "status": "READY",
            "mode": "offline_raw_replay_day_fact_bundle",
            "target_month": "202607",
            "canonical_snapshot_hash": "sha256:" + "4" * 64,
            "checks": {
                "raw_manifest_pairs_complete": True,
                "raw_counts_match_manifest": True,
                "raw_hashes_match_manifest": True,
                "location_coverage_threshold_met": True,
                "every_day_fact_links_to_raw_ids": True,
                "canonical_hash_stable": True,
                "public_safe_output": True,
            },
            "postgres_connection_used": False,
            "database_mutation_performed": False,
            "live_dws_performed": False,
        },
    )
    write_json(
        folder / "raw_replay_manifest.json",
        {
            "status": "pass",
            "target_month": "202607",
            "replay_hash": "sha256:" + "5" * 64,
            "seed_replay_hash": "sha256:" + "6" * 64,
        },
    )


def test_raw_replay_day_fact_bundle_becomes_stage2_source_snapshot_public_safe():
    with tempfile.TemporaryDirectory() as td:
        raw_bundle = Path(td) / "private_runtime" / "raw_replay_day_fact" / "202607"
        source = Path(td) / "private_runtime" / "stage2_source" / "202607" / "source_snapshot.json"
        write_raw_replay_day_fact_bundle(raw_bundle)

        p = run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_stage2_source_from_raw_replay.py"),
            "--raw-replay-day-fact-dir",
            str(raw_bundle),
            "--target-month",
            "202607",
            "--out-json",
            str(source),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["mode"] == "offline_stage2_source_from_raw_replay"
        assert data["target_month"] == "202607"
        assert data["employee_count"] == 1
        assert data["day_count"] == 2
        assert data["payroll_baseline_candidate_rows"] == 2
        assert data["quality_gates"]["raw_to_derived_reconciliation_passed"] is True
        assert data["quality_gates"]["location_evidence_thresholds_passed"] is True
        assert data["quality_gates"]["database_transaction_committed"] is False
        assert data["quality_gates"]["database_transaction_verified"] is False
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False
        assert source.is_file()

        snapshot = json.loads(source.read_text(encoding="utf-8"))
        assert snapshot["target_month"] == "202607"
        assert snapshot["policy_version"] == "dingtalk_raw_replay_v1"
        assert snapshot["identity_version"] == "employee_key_hash_v1"
        assert snapshot["source_batch_hashes"] == ["sha256:" + "1" * 64]
        assert snapshot["unresolved_exceptions"]["P0"] == 0
        assert snapshot["unresolved_exceptions"]["P1"] == 0
        assert snapshot["employees"][0]["employee_internal_id"].startswith("sha256:")
        assert snapshot["employees"][0]["dingtalk_userid"].startswith("hash:")
        assert snapshot["employees"][0]["days"][0]["source_detail_ids"] == ["detail-001-a", "detail-001-b"]
        assert snapshot["payroll_baseline_candidate"][1]["missing_punch_count"] == 1

        public_payload = p.stdout + source.read_text(encoding="utf-8")
        assert "员工甲" not in public_payload
        assert "u-secret" not in public_payload
        assert str(raw_bundle) not in public_payload

        run_dir = Path(td) / "private_runtime" / "stage2" / "202607" / "run_01"
        run([
            sys.executable,
            str(SCRIPT_DIR / "write_stage2_run_artifacts.py"),
            "--source-json",
            str(source),
            "--out-dir",
            str(run_dir),
            "--target-month",
            "202607",
            "--run-index",
            "1",
        ])
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest["quality_grade"] == "Q5"
        assert manifest["quality_gates"]["raw_to_derived_reconciliation_passed"] is True
        assert manifest["quality_gates"]["database_transaction_committed"] is False


def test_resolve_stage2_source_can_use_raw_replay_day_fact_bundle_without_live_dws():
    with tempfile.TemporaryDirectory() as td:
        raw_bundle = Path(td) / "private_runtime" / "raw_replay_day_fact" / "202607"
        run_dir = Path(td) / "private_runtime" / "stage2" / "202607" / "run_01"
        write_raw_replay_day_fact_bundle(raw_bundle)

        p = run([
            sys.executable,
            str(SCRIPT_DIR / "resolve_stage2_source.py"),
            "--target-month",
            "202607",
            "--run-index",
            "1",
            "--run-dir",
            str(run_dir),
            "--repo-root",
            str(ROOT.parent),
            "--source-mode",
            "raw_replay_day_fact",
            "--raw-replay-day-fact-dir",
            str(raw_bundle),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["source_mode"] == "raw_replay_day_fact"
        assert data["source_json"] == str(run_dir / "stage2_source_snapshot.json")
        assert data["live_dws_performed"] is False
        assert data["database_mutation_performed"] is False
        source = run_dir / "stage2_source_snapshot.json"
        assert source.is_file()
        payload = p.stdout + source.read_text(encoding="utf-8")
        assert "员工甲" not in payload
        assert "u-secret" not in payload
        assert str(raw_bundle) not in p.stdout


if __name__ == "__main__":
    test_raw_replay_day_fact_bundle_becomes_stage2_source_snapshot_public_safe()
    test_resolve_stage2_source_can_use_raw_replay_day_fact_bundle_without_live_dws()
    print("stage2 source-from-raw-replay tests passed")
