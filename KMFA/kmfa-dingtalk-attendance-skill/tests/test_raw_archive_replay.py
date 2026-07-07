#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
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


def write_archive_run(month_dir: Path, *, run_id: str, work_date: str, manifest_member_count: int | None = None) -> None:
    month_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "type": "metadata",
            "run_plan": {"run_id": run_id, "run_type": "evening"},
            "stats": {"member_count": 2, "record_success_count": 2, "summary_success_count": 2},
        },
        {
            "type": "employee_attendance",
            "member": {"name": "员工甲", "userId": "u-secret-1"},
            "work_date": work_date,
            "record": {
                "final": {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "result": {
                            "recordList": [
                                {
                                    "checkTypeDesc": "上班",
                                    "userCheckTime": f"{work_date} 08:31:00",
                                    "userLatitude": 30.1234567,
                                    "userLongitude": 114.1234567,
                                    "userAddress": "private address",
                                    "baseAddress": "private base",
                                },
                                {"checkTypeDesc": "下班", "userCheckTime": f"{work_date} 18:31:00"},
                            ]
                        },
                    },
                }
            },
            "summary": {"final": {"returncode": 0, "payload": {"success": True, "result": {"items": []}}}},
            "derived": {"record_success": True, "summary_success": True, "record_has_full_day": True, "record_count": 2},
        },
        {
            "type": "employee_attendance",
            "member": {"name": "员工乙", "userId": "u-secret-2"},
            "work_date": work_date,
            "record": {
                "final": {
                    "returncode": 0,
                    "payload": {
                        "success": True,
                        "result": {
                            "recordList": [
                                {"checkTypeDesc": "上班", "userCheckTime": f"{work_date} 08:29:00"},
                                {
                                    "checkTypeDesc": "下班",
                                    "userCheckTime": f"{work_date} 18:34:00",
                                    "latitude": 30.7654321,
                                    "longitude": 114.7654321,
                                },
                            ]
                        },
                    },
                }
            },
            "summary": {"final": {"returncode": 0, "payload": {"success": True, "result": {"items": []}}}},
            "derived": {"record_success": True, "summary_success": True, "record_has_full_day": True, "record_count": 2},
        },
    ]
    raw_path = month_dir / f"{run_id}.raw.jsonl.gz"
    with gzip.open(raw_path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    manifest = {
        "run_id": run_id,
        "backend": "dws",
        "raw_jsonl_gz": str(raw_path),
        "raw_jsonl_gz_sha256": digest,
        "stats": {
            "member_count": manifest_member_count if manifest_member_count is not None else 2,
            "record_success_count": 2,
            "summary_success_count": 2,
        },
    }
    (month_dir / f"{run_id}.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def test_raw_archive_month_replay_manifest_is_public_safe_and_stable():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        write_archive_run(month_dir, run_id="s19_evening_20260701_181500", work_date="2026-07-01")
        write_archive_run(month_dir, run_id="s19_evening_20260702_181500", work_date="2026-07-02")
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "inspect_raw_archive_month.py"),
            "--archive-root",
            str(archive_root),
            "--target-month",
            "202607",
            "--print-json",
        ]
        first = json.loads(run(cmd).stdout)
        second = json.loads(run(cmd).stdout)
        assert first == second
        assert first["status"] == "pass"
        assert first["mode"] == "private_raw_archive_month_replay_inspection"
        assert first["target_month"] == "202607"
        assert first["archive_root_included"] is False
        assert first["raw_file_count"] == 2
        assert first["manifest_count"] == 2
        assert first["raw_without_manifest_count"] == 0
        assert first["manifest_without_raw_count"] == 0
        assert first["employee_attendance_row_count"] == 4
        assert first["manifest_stats_totals"]["member_count"] == 4
        assert first["raw_stats_totals"]["member_count"] == 4
        assert first["checks"]["raw_counts_match_manifest"] is True
        assert first["checks"]["raw_hashes_match_manifest"] is True
        assert first["checks"]["replay_hash_stable"] is True
        assert first["location_coverage"]["punch_count"] == 8
        assert first["location_coverage"]["punches_with_location_evidence"] == 4
        assert first["location_coverage"]["ratio"] == 0.5
        assert first["postgres_connection_used"] is False
        assert first["database_mutation_performed"] is False
        assert first["live_dws_performed"] is False
        payload = json.dumps(first, ensure_ascii=False)
        assert "员工甲" not in payload
        assert "员工乙" not in payload
        assert "u-secret" not in payload
        assert str(archive_root) not in payload


def test_raw_archive_month_replay_manifest_fails_on_manifest_count_mismatch():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        write_archive_run(month_dir, run_id="s19_evening_20260701_181500", work_date="2026-07-01", manifest_member_count=3)
        p = run([
            sys.executable,
            str(SCRIPT_DIR / "inspect_raw_archive_month.py"),
            "--archive-root",
            str(archive_root),
            "--target-month",
            "202607",
            "--print-json",
        ], check=False)
        assert p.returncode == 1
        data = json.loads(p.stdout)
        assert data["status"] == "fail"
        assert "manifest_count_mismatch:s19_evening_20260701_181500:member_count" in data["failures"]
        assert data["checks"]["raw_counts_match_manifest"] is False
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False


if __name__ == "__main__":
    test_raw_archive_month_replay_manifest_is_public_safe_and_stable()
    test_raw_archive_month_replay_manifest_fails_on_manifest_count_mismatch()
    print("raw archive replay tests passed")
