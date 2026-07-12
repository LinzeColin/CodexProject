#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_database_contract.py"


def run_database_dry_run() -> dict:
    p = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--schema",
            str(ROOT / "database" / "postgres_schema.sql"),
            "--views",
            str(ROOT / "database" / "views_payroll_baseline.sql"),
            "--print-json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return json.loads(p.stdout)


def test_database_contract_dry_run_accepts_synthetic_stage2_payroll_path():
    data = run_database_dry_run()
    assert data["status"] == "pass"
    assert data["mode"] == "offline_contract_dry_run"
    assert data["postgres_connection_used"] is False
    assert data["live_dws_performed"] is False
    assert data["database_mutation_performed"] is False
    assert data["schema"]["missing_required_tables"] == []
    assert data["schema"]["missing_required_views"] == []
    assert data["schema"]["missing_required_types"] == []
    assert data["synthetic_path"]["stage2_accepted"] is True
    assert data["synthetic_path"]["stage2_run_count"] == 5
    assert data["synthetic_path"]["active_payroll_baseline_rows"] == 1
    assert data["synthetic_path"]["monthly_summary"]["baseline_rows"] == 1
    assert data["synthetic_path"]["stage2_blocker_count"] == 0


if __name__ == "__main__":
    test_database_contract_dry_run_accepts_synthetic_stage2_payroll_path()
    print("database dry-run tests passed")
