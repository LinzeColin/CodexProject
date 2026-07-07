#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
FIX = ROOT / "tests" / "fixtures"


def run(cmd: list[str], env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if check and p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return p


def write_accepted_stage2(runtime: Path) -> Path:
    env = os.environ.copy()
    env.update({
        "KMFA_REPO_ROOT": str(ROOT.parent),
        "KMFA_PRIVATE_RUNTIME": str(runtime),
        "KMFA_RUN_SLOT": "evening",
        "KMFA_STAGE2_SOURCE_JSON": str(FIX / "minimal_snapshot_a.json"),
    })
    for day in range(1, 6):
        env["KMFA_TODAY_OVERRIDE"] = f"2026-08-{day:02d}"
        run([str(SCRIPT_DIR / "run_stage2_evening.sh")], env=env)
    return runtime / "stage2" / "202607"


def test_database_landing_bundle_materializes_accepted_stage2_without_db_mutation():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        stage2_root = write_accepted_stage2(runtime)
        out_dir = runtime / "db_landing" / "202607"
        p = run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_database_landing_bundle.py"),
            "--stage2-root",
            str(stage2_root),
            "--target-month",
            "202607",
            "--out-dir",
            str(out_dir),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["mode"] == "offline_db_landing_bundle"
        assert data["target_month"] == "202607"
        assert data["stage2_accepted"] is True
        assert data["stage2_run_count"] == 5
        assert data["payroll_baseline_rows"] == 1
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False
        for rel in [
            "db_landing_manifest.json",
            "load_order.json",
            "canonical_month_snapshot.json",
            "stage2_shadow_run.jsonl",
            "stage2_consensus_certificate.json",
            "attendance_day_fact.jsonl",
            "payroll_baseline_attendance.jsonl",
            "postgres_copy_manifest.sql",
        ]:
            assert (out_dir / rel).is_file(), f"missing {out_dir / rel}"
        load_order = json.loads((out_dir / "load_order.json").read_text(encoding="utf-8"))
        assert load_order["tables"] == [
            "policy_version",
            "canonical_month_snapshot",
            "stage2_shadow_run",
            "stage2_consensus_certificate",
            "attendance_day_fact",
            "payroll_baseline_attendance",
        ]
        assert (out_dir / "policy_version.json").is_file()
        payroll_lines = (out_dir / "payroll_baseline_attendance.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(payroll_lines) == 1
        payroll_row = json.loads(payroll_lines[0])
        assert payroll_row["employee_internal_id"] == "E001"
        assert payroll_row["dingtalk_userid"] == "u001"
        assert payroll_row["stage2_certificate_id"] == data["stage2_certificate_id"]


def test_postgres_landing_load_plan_is_generated_without_database_connection():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        stage2_root = write_accepted_stage2(runtime)
        out_dir = runtime / "db_landing" / "202607"
        run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_database_landing_bundle.py"),
            "--stage2-root",
            str(stage2_root),
            "--target-month",
            "202607",
            "--out-dir",
            str(out_dir),
        ])
        p = run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_postgres_landing_loader.py"),
            "--bundle-dir",
            str(out_dir),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["mode"] == "offline_postgres_load_plan"
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False
        assert data["tables"] == [
            "policy_version",
            "canonical_month_snapshot",
            "stage2_shadow_run",
            "stage2_consensus_certificate",
            "attendance_day_fact",
            "payroll_baseline_attendance",
        ]
        sql_path = out_dir / "postgres_load_plan.sql"
        manifest_path = out_dir / "postgres_load_plan_manifest.json"
        assert sql_path.is_file()
        assert manifest_path.is_file()
        sql = sql_path.read_text(encoding="utf-8")
        assert "\\set ON_ERROR_STOP on" in sql
        assert "BEGIN;" in sql
        assert "COMMIT;" in sql
        assert "INSERT INTO policy_version" in sql
        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql
        assert "psql" not in data


if __name__ == "__main__":
    test_database_landing_bundle_materializes_accepted_stage2_without_db_mutation()
    test_postgres_landing_load_plan_is_generated_without_database_connection()
    print("database landing bundle tests passed")
