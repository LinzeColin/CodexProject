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


def test_postgres_load_plan_static_validator_checks_schema_and_conflicts():
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
        run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_postgres_landing_loader.py"),
            "--bundle-dir",
            str(out_dir),
        ])
        p = run([
            sys.executable,
            str(SCRIPT_DIR / "validate_postgres_load_plan.py"),
            "--schema",
            str(ROOT / "database" / "postgres_schema.sql"),
            "--bundle-dir",
            str(out_dir),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "pass"
        assert data["mode"] == "offline_postgres_load_plan_static_validation"
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert data["live_dws_performed"] is False
        assert data["failures"] == []
        assert data["tables_checked"] == [
            "policy_version",
            "canonical_month_snapshot",
            "stage2_shadow_run",
            "stage2_consensus_certificate",
            "attendance_day_fact",
            "payroll_baseline_attendance",
        ]
        assert data["checks"]["conflict_targets_backed_by_schema"] is True

        bad_sql = out_dir / "postgres_load_plan_bad.sql"
        sql = (out_dir / "postgres_load_plan.sql").read_text(encoding="utf-8")
        bad_sql.write_text(sql.replace("ON CONFLICT (target_month, run_index)", "ON CONFLICT (target_month)", 1), encoding="utf-8")
        bad = run([
            sys.executable,
            str(SCRIPT_DIR / "validate_postgres_load_plan.py"),
            "--schema",
            str(ROOT / "database" / "postgres_schema.sql"),
            "--bundle-dir",
            str(out_dir),
            "--sql",
            str(bad_sql),
            "--print-json",
        ], check=False)
        assert bad.returncode == 1
        bad_data = json.loads(bad.stdout)
        assert "conflict_target_not_backed_by_schema:stage2_shadow_run:target_month" in bad_data["failures"]


def test_postgres_load_plan_execution_guard_requires_nonproduction_approval():
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
        run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_postgres_landing_loader.py"),
            "--bundle-dir",
            str(out_dir),
        ])
        guard_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "execute_postgres_load_plan.py"),
            "--schema",
            str(ROOT / "database" / "postgres_schema.sql"),
            "--views",
            str(ROOT / "database" / "views_payroll_baseline.sql"),
            "--bundle-dir",
            str(out_dir),
            "--print-json",
        ]
        dry = run(guard_cmd)
        dry_data = json.loads(dry.stdout)
        assert dry_data["status"] == "pass"
        assert dry_data["mode"] == "postgres_load_plan_execution_guard"
        assert dry_data["execute_requested"] is False
        assert dry_data["psql_invoked"] is False
        assert dry_data["postgres_connection_used"] is False
        assert dry_data["database_mutation_performed"] is False
        assert dry_data["live_dws_performed"] is False
        assert dry_data["checks"]["static_validation_passed"] is True

        blocked = run(
            guard_cmd
            + [
                "--execute",
                "--acknowledge-nonprod-mutation",
                "--database-url",
                "postgresql://localhost/kmfa_attendance_local",
                "--target-env",
                "local",
            ],
            check=False,
        )
        assert blocked.returncode == 1
        blocked_data = json.loads(blocked.stdout)
        assert "nonprod_execution_not_allowed" in blocked_data["failures"]
        assert blocked_data["psql_invoked"] is False
        assert blocked_data["database_mutation_performed"] is False

        prod_env = os.environ.copy()
        prod_env["KMFA_ALLOW_NONPROD_POSTGRES_EXECUTION"] = "1"
        prod = run(
            guard_cmd
            + [
                "--execute",
                "--acknowledge-nonprod-mutation",
                "--database-url",
                "postgresql://db.prod.example/kmfa_attendance_prod",
                "--target-env",
                "production",
            ],
            env=prod_env,
            check=False,
        )
        assert prod.returncode == 1
        prod_data = json.loads(prod.stdout)
        assert "target_env_not_nonproduction:production" in prod_data["failures"]
        assert prod_data["psql_invoked"] is False

        fake_psql = Path(td) / "fake_psql.sh"
        fake_log = Path(td) / "fake_psql_args.txt"
        fake_psql.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$KMFA_FAKE_PSQL_LOG\"\n", encoding="utf-8")
        fake_psql.chmod(0o755)
        env = os.environ.copy()
        env.update({
            "KMFA_ALLOW_NONPROD_POSTGRES_EXECUTION": "1",
            "KMFA_ATTENDANCE_POSTGRES_DSN": "postgresql://localhost/kmfa_attendance_local",
            "KMFA_POSTGRES_TARGET_ENV": "local",
            "KMFA_FAKE_PSQL_LOG": str(fake_log),
        })
        executed = run(
            guard_cmd
            + [
                "--execute",
                "--acknowledge-nonprod-mutation",
                "--psql-bin",
                str(fake_psql),
            ],
            env=env,
        )
        executed_data = json.loads(executed.stdout)
        assert executed_data["status"] == "pass"
        assert executed_data["psql_invoked"] is True
        assert executed_data["postgres_connection_used"] is True
        assert executed_data["database_mutation_attempted"] is True
        assert executed_data["database_mutation_performed"] is True
        assert executed_data["live_dws_performed"] is False
        fake_args = fake_log.read_text(encoding="utf-8")
        assert "postgresql://localhost/kmfa_attendance_local" in fake_args
        assert str(ROOT / "database" / "postgres_schema.sql") in fake_args
        assert str(ROOT / "database" / "views_payroll_baseline.sql") in fake_args
        assert str(out_dir / "postgres_load_plan.sql") in fake_args


if __name__ == "__main__":
    test_database_landing_bundle_materializes_accepted_stage2_without_db_mutation()
    test_postgres_landing_load_plan_is_generated_without_database_connection()
    test_postgres_load_plan_static_validator_checks_schema_and_conflicts()
    test_postgres_load_plan_execution_guard_requires_nonproduction_approval()
    print("database landing bundle tests passed")
