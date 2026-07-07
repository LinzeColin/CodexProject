#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from test_stage2_source_from_raw_replay import write_raw_replay_day_fact_bundle


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"


def run(cmd: list[str], env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if check and p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return p


def test_preconsensus_database_proof_promotes_stage2_database_gates_without_payroll_acceptance():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        raw_bundle = runtime / "raw_replay_day_fact" / "202607"
        source = runtime / "stage2_source" / "202607" / "source_snapshot.json"
        db_bundle = runtime / "db_landing_preconsensus" / "202607"
        verified_source = runtime / "stage2_source" / "202607" / "source_snapshot.db_verified.json"
        write_raw_replay_day_fact_bundle(raw_bundle)

        run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_stage2_source_from_raw_replay.py"),
            "--raw-replay-day-fact-dir",
            str(raw_bundle),
            "--target-month",
            "202607",
            "--out-json",
            str(source),
        ])
        before = json.loads(source.read_text(encoding="utf-8"))
        assert before["quality_gates"]["database_transaction_committed"] is False
        assert before["quality_gates"]["database_transaction_verified"] is False

        bundle_result = run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_preconsensus_postgres_landing_bundle.py"),
            "--source-json",
            str(source),
            "--target-month",
            "202607",
            "--out-dir",
            str(db_bundle),
            "--print-json",
        ])
        bundle_data = json.loads(bundle_result.stdout)
        assert bundle_data["status"] == "READY"
        assert bundle_data["mode"] == "offline_preconsensus_db_landing_bundle"
        assert bundle_data["stage2_accepted"] is False
        assert bundle_data["payroll_baseline_rows"] == 0
        assert bundle_data["attendance_day_fact_rows"] == 2
        assert bundle_data["postgres_connection_used"] is False
        assert bundle_data["database_mutation_performed"] is False
        assert json.loads((db_bundle / "load_order.json").read_text(encoding="utf-8"))["tables"] == [
            "policy_version",
            "canonical_month_snapshot",
            "attendance_day_fact",
        ]
        assert not (db_bundle / "payroll_baseline_attendance.jsonl").exists()

        run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_postgres_landing_loader.py"),
            "--bundle-dir",
            str(db_bundle),
        ])
        validation = run([
            sys.executable,
            str(SCRIPT_DIR / "validate_postgres_load_plan.py"),
            "--schema",
            str(ROOT / "database" / "postgres_schema.sql"),
            "--bundle-dir",
            str(db_bundle),
            "--print-json",
        ])
        validation_data = json.loads(validation.stdout)
        assert validation_data["status"] == "pass"
        assert validation_data["tables_checked"] == [
            "policy_version",
            "canonical_month_snapshot",
            "attendance_day_fact",
        ]

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
        proof = run(
            [
                sys.executable,
                str(SCRIPT_DIR / "execute_postgres_load_plan.py"),
                "--schema",
                str(ROOT / "database" / "postgres_schema.sql"),
                "--views",
                str(ROOT / "database" / "views_payroll_baseline.sql"),
                "--bundle-dir",
                str(db_bundle),
                "--execute",
                "--acknowledge-nonprod-mutation",
                "--psql-bin",
                str(fake_psql),
                "--print-json",
            ],
            env=env,
        )
        proof_path = runtime / "db_landing_preconsensus" / "202607" / "postgres_execution_proof.json"
        proof_path.write_text(proof.stdout, encoding="utf-8")
        proof_data = json.loads(proof.stdout)
        assert proof_data["status"] == "pass"
        assert proof_data["database_mutation_performed"] is True
        assert "postgresql://localhost" not in proof.stdout
        assert str(db_bundle) not in proof.stdout
        assert str(ROOT) not in proof.stdout

        missing_state_proof = run(
            [
                sys.executable,
                str(SCRIPT_DIR / "apply_stage2_database_proof.py"),
                "--source-json",
                str(source),
                "--bundle-dir",
                str(db_bundle),
                "--execution-proof-json",
                str(proof_path),
                "--out-json",
                str(verified_source),
                "--print-json",
            ],
            check=False,
        )
        assert missing_state_proof.returncode != 0
        assert "state verification proof" in missing_state_proof.stderr

        verify_psql = Path(td) / "verify_psql.sh"
        verify_log = Path(td) / "verify_psql_args.txt"
        verify_psql.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$@\" > \"$KMFA_FAKE_PSQL_LOG\"\n"
            "printf '%s\\n' '{\"policy_version\":1,\"canonical_month_snapshot\":1,\"attendance_day_fact\":2}'\n",
            encoding="utf-8",
        )
        verify_psql.chmod(0o755)
        state_verification = run(
            [
                sys.executable,
                str(SCRIPT_DIR / "verify_postgres_landing_state.py"),
                "--bundle-dir",
                str(db_bundle),
                "--psql-bin",
                str(verify_psql),
                "--acknowledge-nonprod-read",
                "--print-json",
            ],
            env=env,
        )
        state_verification_path = db_bundle / "postgres_state_verification.json"
        state_verification_path.write_text(state_verification.stdout, encoding="utf-8")
        state_data = json.loads(state_verification.stdout)
        assert state_data["status"] == "pass"
        assert state_data["expected_counts"] == {
            "policy_version": 1,
            "canonical_month_snapshot": 1,
            "attendance_day_fact": 2,
        }
        assert state_data["observed_counts"] == state_data["expected_counts"]
        assert state_data["database_mutation_performed"] is False
        assert "postgresql://localhost" not in state_verification.stdout
        assert str(db_bundle) not in state_verification.stdout
        assert str(ROOT) not in state_verification.stdout

        apply_result = run([
            sys.executable,
            str(SCRIPT_DIR / "apply_stage2_database_proof.py"),
            "--source-json",
            str(source),
            "--bundle-dir",
            str(db_bundle),
            "--execution-proof-json",
            str(proof_path),
            "--state-verification-json",
            str(state_verification_path),
            "--out-json",
            str(verified_source),
            "--print-json",
        ])
        applied = json.loads(apply_result.stdout)
        assert applied["status"] == "READY"
        assert applied["database_transaction_marker"].startswith("postgres-nonprod:")
        assert applied["postgres_connection_used"] is False
        assert applied["database_mutation_performed"] is False
        verified = json.loads(verified_source.read_text(encoding="utf-8"))
        assert verified["quality_gates"]["database_transaction_committed"] is True
        assert verified["quality_gates"]["database_transaction_verified"] is True
        assert verified["database_transaction_marker"] == applied["database_transaction_marker"]

        run_dir = runtime / "stage2" / "202607" / "run_01"
        run([
            sys.executable,
            str(SCRIPT_DIR / "write_stage2_run_artifacts.py"),
            "--source-json",
            str(verified_source),
            "--out-dir",
            str(run_dir),
            "--target-month",
            "202607",
            "--run-index",
            "1",
        ])
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest["quality_gates"]["database_transaction_committed"] is True
        assert manifest["quality_gates"]["database_transaction_verified"] is True
        assert manifest["database_transaction_marker"] == applied["database_transaction_marker"]
        assert "postgresql://localhost" not in apply_result.stdout
        assert str(db_bundle) not in apply_result.stdout


if __name__ == "__main__":
    test_preconsensus_database_proof_promotes_stage2_database_gates_without_payroll_acceptance()
    print("preconsensus database proof tests passed")
