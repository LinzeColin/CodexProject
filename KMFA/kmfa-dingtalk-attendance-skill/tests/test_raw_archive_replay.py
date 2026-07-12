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
        **(
            {"stage_id": "S19"}  # legacy_read_only fixture
            if run_id.startswith("s19_")  # legacy_read_only fixture
            else {"skill_id": "kmfa-dingtalk-attendance-skill"}
        ),
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


def write_seed_record_only_raw(month_dir: Path, *, run_id: str, work_date: str) -> None:
    month_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"type": "metadata", "run_plan": {"run_id": run_id, "run_type": "seed"}},
        {
            "type": "employee_attendance",
            "member": {"name": "员工甲", "userId": "u-secret-1"},
            "work_date": work_date,
            "record_list": [
                {"checkTypeDesc": "上班", "userCheckTime": f"{work_date} 08:31:00", "locationText": "private"},
                {"checkTypeDesc": "下班", "userCheckTime": f"{work_date} 18:31:00"},
            ],
        },
        {
            "type": "employee_attendance",
            "member": {"name": "员工乙", "userId": "u-secret-2"},
            "work_date": work_date,
            "record_list": [
                {"checkTypeDesc": "上班", "userCheckTime": f"{work_date} 08:29:00"},
                {"checkTypeDesc": "下班", "userCheckTime": f"{work_date} 18:34:00", "locationText": "private"},
            ],
        },
    ]
    raw_path = month_dir / f"{run_id}.raw.jsonl.gz"
    with gzip.open(raw_path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_seed_raw_with_empty_record_row(month_dir: Path, *, run_id: str, work_date: str) -> None:
    month_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"type": "metadata", "run_plan": {"run_id": run_id, "run_type": "seed"}},
        {
            "type": "employee_attendance",
            "member": {"name": "员工甲", "userId": "u-secret-1"},
            "work_date": work_date,
            "record_list": [],
        },
        {
            "type": "employee_attendance",
            "member": {"name": "员工乙", "userId": "u-secret-2"},
            "work_date": work_date,
            "record_list": [
                {"checkTypeDesc": "上班", "userCheckTime": f"{work_date} 08:29:00", "locationText": "private"},
                {"checkTypeDesc": "下班", "userCheckTime": f"{work_date} 18:34:00", "locationText": "private"},
            ],
        },
    ]
    raw_path = month_dir / f"{run_id}.raw.jsonl.gz"
    with gzip.open(raw_path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def test_raw_archive_month_replay_manifest_is_public_safe_and_stable():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260701_181500", work_date="2026-07-01")
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260702_181500", work_date="2026-07-02")
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


def test_raw_archive_month_replay_dual_reads_new_and_legacy_prefixes():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        write_archive_run(
            month_dir,
            run_id="dingtalk_attendance_evening_20260712_200000",
            work_date="2026-07-12",
        )
        write_archive_run(
            month_dir,
            run_id="s19_evening_20260711_200000",  # legacy_read_only
            work_date="2026-07-11",
        )
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "inspect_raw_archive_month.py"),
            "--archive-root",
            str(archive_root),
            "--target-month",
            "202607",
            "--print-json",
        ]

        result = json.loads(run(cmd).stdout)

        assert result["status"] == "pass"
        assert result["manifest_count"] == 2
        assert result["raw_file_count"] == 2


def test_raw_archive_month_replay_manifest_fails_on_manifest_count_mismatch():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260701_181500", work_date="2026-07-01", manifest_member_count=3)
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
        assert "manifest_count_mismatch:dingtalk_attendance_evening_20260701_181500:member_count" in data["failures"]
        assert data["checks"]["raw_counts_match_manifest"] is False
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False


def test_raw_archive_month_replay_can_index_seed_raw_separately_and_enforce_location_gate():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260701_181500", work_date="2026-07-01")
        write_seed_record_only_raw(month_dir, run_id="dingtalk_attendance_seed_20260702_000000", work_date="2026-07-02")

        base_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "inspect_raw_archive_month.py"),
            "--archive-root",
            str(archive_root),
            "--target-month",
            "202607",
            "--print-json",
        ]
        blocked = run(base_cmd, check=False)
        assert blocked.returncode == 1
        blocked_data = json.loads(blocked.stdout)
        assert "raw_without_manifest:dingtalk_attendance_seed_20260702_000000" in blocked_data["failures"]
        assert blocked_data["seed_raw_without_manifest_count"] == 1

        allowed = json.loads(run(base_cmd + ["--allow-seed-raw-without-manifest"]).stdout)
        assert allowed["status"] == "pass"
        assert allowed["raw_without_manifest_count"] == 1
        assert allowed["seed_raw_without_manifest_count"] == 1
        assert allowed["formal_raw_without_manifest_count"] == 0
        assert allowed["checks"]["raw_manifest_pairs_complete"] is True
        assert allowed["checks"]["seed_raw_without_manifest_indexed"] is True
        assert allowed["seed_raw_stats_totals"]["member_count"] == 2
        assert allowed["seed_raw_stats_totals"]["record_success_count"] == 2
        assert allowed["seed_location_coverage"]["punch_count"] == 4
        assert allowed["seed_location_coverage"]["punches_with_location_evidence"] == 2
        assert allowed["seed_replay_hash"].startswith("sha256:")
        payload = json.dumps(allowed, ensure_ascii=False)
        assert "员工甲" not in payload
        assert "u-secret" not in payload
        assert str(archive_root) not in payload

        location_blocked = run(base_cmd + ["--allow-seed-raw-without-manifest", "--min-location-coverage-ratio", "0.6"], check=False)
        assert location_blocked.returncode == 1
        location_data = json.loads(location_blocked.stdout)
        assert "location_coverage_below_threshold:0.5<0.6" in location_data["failures"]
        assert location_data["checks"]["location_coverage_threshold_met"] is False
        assert location_data["postgres_connection_used"] is False
        assert location_data["database_mutation_performed"] is False
        assert location_data["live_dws_performed"] is False


def test_raw_archive_replay_materializes_day_facts_with_raw_linkage_public_safe():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        out_dir = Path(td) / "private_runtime" / "raw_replay_day_fact" / "202607"
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260701_181500", work_date="2026-07-01")
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260702_181500", work_date="2026-07-02")
        write_seed_record_only_raw(month_dir, run_id="dingtalk_attendance_seed_20260703_000000", work_date="2026-07-03")

        p = run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_raw_replay_day_fact_bundle.py"),
            "--archive-root",
            str(archive_root),
            "--target-month",
            "202607",
            "--allow-seed-raw-without-manifest",
            "--min-location-coverage-ratio",
            "0.01",
            "--out-dir",
            str(out_dir),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["mode"] == "offline_raw_replay_day_fact_bundle"
        assert data["target_month"] == "202607"
        assert data["raw_replay_status"] == "pass"
        assert data["attendance_day_fact_rows"] == 6
        assert data["raw_detail_linkage_rows"] == 12
        assert data["checks"]["every_day_fact_links_to_raw_ids"] is True
        assert data["checks"]["canonical_hash_stable"] is True
        assert data["checks"]["public_safe_output"] is True
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False
        for rel in [
            "raw_replay_day_fact_manifest.json",
            "raw_replay_manifest.json",
            "attendance_day_fact.jsonl",
            "raw_detail_linkage.jsonl",
            "canonical_replay_snapshot.json",
            "canonical_replay_snapshot.sha256",
        ]:
            assert (out_dir / rel).is_file(), f"missing {out_dir / rel}"

        day_rows = [json.loads(line) for line in (out_dir / "attendance_day_fact.jsonl").read_text(encoding="utf-8").splitlines()]
        assert all(row["source_detail_ids"] for row in day_rows)
        assert all(row["employee_key_hash"].startswith("sha256:") for row in day_rows)
        assert len({row["derivation_hash"] for row in day_rows}) == 6
        payload = p.stdout + (out_dir / "raw_replay_day_fact_manifest.json").read_text(encoding="utf-8")
        private_payload = (out_dir / "attendance_day_fact.jsonl").read_text(encoding="utf-8") + (out_dir / "raw_detail_linkage.jsonl").read_text(encoding="utf-8")
        assert "员工甲" not in payload
        assert "员工乙" not in payload
        assert "u-secret" not in payload
        assert str(archive_root) not in payload
        assert "员工甲" not in private_payload
        assert "u-secret" not in private_payload


def test_raw_archive_replay_skips_empty_record_rows_without_unlinked_day_facts():
    with tempfile.TemporaryDirectory() as td:
        archive_root = Path(td) / "private_onedrive"
        month_dir = archive_root / "202607"
        out_dir = Path(td) / "private_runtime" / "raw_replay_day_fact" / "202607"
        write_archive_run(month_dir, run_id="dingtalk_attendance_evening_20260701_181500", work_date="2026-07-01")
        write_seed_raw_with_empty_record_row(month_dir, run_id="dingtalk_attendance_seed_20260702_000000", work_date="2026-07-02")

        p = run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_raw_replay_day_fact_bundle.py"),
            "--archive-root",
            str(archive_root),
            "--target-month",
            "202607",
            "--allow-seed-raw-without-manifest",
            "--min-location-coverage-ratio",
            "0.01",
            "--out-dir",
            str(out_dir),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["attendance_day_fact_rows"] == 3
        assert data["raw_employee_rows_without_punches"] == 1
        assert data["checks"]["every_day_fact_links_to_raw_ids"] is True
        assert "day_fact_without_raw_detail_link" not in data["failures"]


if __name__ == "__main__":
    test_raw_archive_month_replay_manifest_is_public_safe_and_stable()
    test_raw_archive_month_replay_manifest_fails_on_manifest_count_mismatch()
    test_raw_archive_month_replay_can_index_seed_raw_separately_and_enforce_location_gate()
    test_raw_archive_replay_materializes_day_facts_with_raw_linkage_public_safe()
    test_raw_archive_replay_skips_empty_record_rows_without_unlinked_day_facts()
    print("raw archive replay tests passed")
