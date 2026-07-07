#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
FIX = ROOT / "tests" / "fixtures"


def run(cmd, check=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return p


def canonicalize(src: Path, out: Path):
    run([
        sys.executable,
        str(SCRIPT_DIR / "canonicalize_attendance_snapshot.py"),
        str(src),
        "--out", str(out / "canonical_snapshot.json"),
        "--sha-out", str(out / "canonical_snapshot.sha256"),
    ])


def write_manifest(
    folder: Path,
    run_index: int,
    target_month="202607",
    quality="Q4",
    p0=0,
    p1=0,
    quality_gates: dict | None = None,
):
    digest = (folder / "canonical_snapshot.sha256").read_text().strip()
    manifest = {
        "run_id": f"run_{run_index}",
        "skill_name": "kmfa-dingtalk-attendance-skill",
        "run_slot": "evening",
        "target_month": target_month,
        "stage2_run_index": run_index,
        "source_batches": ["batch"],
        "raw_hashes": ["sha256:rawbatch"],
        "database_transaction_marker": "txid:test",
        "canonical_snapshot_hash": digest,
        "quality_grade": quality,
        "unresolved_exceptions": {"P0": p0, "P1": p1, "P2": 0, "P3": 0},
        "quality_gates": quality_gates
        or {
            "location_evidence_thresholds_passed": True,
            "raw_to_derived_reconciliation_passed": True,
            "database_transaction_committed": True,
            "database_transaction_verified": True,
        },
        "stage2_status": "pending",
    }
    (folder / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def prepare_stage2(tmp: Path, divergent=False):
    stage2 = tmp / "stage2" / "202607"
    for i in range(1, 6):
        folder = stage2 / f"run_{i:02d}"
        folder.mkdir(parents=True)
        src = FIX / ("minimal_snapshot_c_diff.json" if divergent and i == 5 else "minimal_snapshot_a.json")
        canonicalize(src, folder)
        write_manifest(folder, i)
    return stage2


def test_accepts_identical():
    with tempfile.TemporaryDirectory() as td:
        stage2 = prepare_stage2(Path(td), divergent=False)
        p = run([sys.executable, str(SCRIPT_DIR / "stage2_consensus_gate.py"), "--stage2-root", str(stage2), "--target-month", "202607"])
        data = json.loads(p.stdout)
        assert data["accepted"] is True


def test_rejects_divergent():
    with tempfile.TemporaryDirectory() as td:
        stage2 = prepare_stage2(Path(td), divergent=True)
        p = run([sys.executable, str(SCRIPT_DIR / "stage2_consensus_gate.py"), "--stage2-root", str(stage2), "--target-month", "202607"], check=False)
        assert p.returncode == 2
        data = json.loads(p.stdout)
        assert data["accepted"] is False


def test_rejects_identical_hashes_without_required_quality_gates():
    with tempfile.TemporaryDirectory() as td:
        stage2 = Path(td) / "stage2" / "202607"
        for i in range(1, 6):
            folder = stage2 / f"run_{i:02d}"
            folder.mkdir(parents=True)
            canonicalize(FIX / "minimal_snapshot_a.json", folder)
            write_manifest(
                folder,
                i,
                quality_gates={
                    "location_evidence_thresholds_passed": True,
                    "raw_to_derived_reconciliation_passed": False,
                    "database_transaction_committed": False,
                    "database_transaction_verified": False,
                },
            )
        p = run([sys.executable, str(SCRIPT_DIR / "stage2_consensus_gate.py"), "--stage2-root", str(stage2), "--target-month", "202607"], check=False)
        assert p.returncode == 2
        data = json.loads(p.stdout)
        assert data["accepted"] is False
        assert "run_01:raw_to_derived_reconciliation_failed" in data["failures"]
        assert "run_01:database_transaction_not_committed" in data["failures"]
        assert "run_01:database_transaction_not_verified" in data["failures"]


def test_evening_replay_adapter_writes_five_run_artifacts_and_fails_without_database_commit():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        source = FIX / "minimal_snapshot_a.json"
        env = os.environ.copy()
        env.update({
            "KMFA_REPO_ROOT": str(ROOT.parent),
            "KMFA_PRIVATE_RUNTIME": str(runtime),
            "KMFA_RUN_SLOT": "evening",
            "KMFA_STAGE2_SOURCE_JSON": str(source),
        })
        for day in range(1, 6):
            env["KMFA_TODAY_OVERRIDE"] = f"2026-08-{day:02d}"
            p = subprocess.run(
                [str(SCRIPT_DIR / "run_stage2_evening.sh")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            expected_code = 2 if day == 5 else 0
            if p.returncode != expected_code:
                print(p.stdout)
                print(p.stderr, file=sys.stderr)
                raise SystemExit(p.returncode)
            run_dir = runtime / "stage2" / "202607" / f"run_{day:02d}"
            for rel in [
                "run_manifest.json",
                "canonical_snapshot.json",
                "canonical_snapshot.sha256",
                "quality_report.json",
                "exception_report.json",
                "payroll_baseline_candidate.json",
            ]:
                assert (run_dir / rel).is_file(), f"missing {run_dir / rel}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            assert manifest["quality_gates"]["database_transaction_committed"] is False
            assert manifest["quality_gates"]["database_transaction_verified"] is False
        cert = json.loads((runtime / "stage2" / "202607" / "stage2_consensus_certificate.json").read_text())
        assert cert["accepted"] is False
        assert cert["stage2_status"] == "failed"
        assert "run_01:database_transaction_not_committed" in cert["failures"]
        assert (runtime / "stage2" / "202607" / "stage2_divergence_report.md").is_file()


def test_stage2_accepted_rehearsal_requires_db_verified_source_and_materializes_landing_bundle():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        source = runtime / "source.db_verified.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        snapshot = json.loads((FIX / "minimal_snapshot_a.json").read_text(encoding="utf-8"))
        snapshot["quality_gates"] = {
            "location_evidence_thresholds_passed": True,
            "raw_to_derived_reconciliation_passed": True,
            "database_transaction_committed": True,
            "database_transaction_verified": True,
        }
        snapshot["database_transaction_marker"] = "postgres-nonprod:test-marker"
        snapshot["database_execution_proof"] = {
            "proof_hash": "sha256:execution",
            "state_verification_hash": "sha256:state",
            "state_counts_verified": True,
            "database_mutation_performed": True,
            "postgres_connection_used": True,
            "live_dws_performed": False,
        }
        source.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

        p = run([
            sys.executable,
            str(SCRIPT_DIR / "run_stage2_accepted_rehearsal.py"),
            "--source-json",
            str(source),
            "--target-month",
            "202607",
            "--out-root",
            str(runtime),
            "--print-json",
        ])
        data = json.loads(p.stdout)
        assert data["status"] == "READY"
        assert data["accepted"] is True
        assert data["stage2_run_count"] == 5
        assert data["db_landing_status"] == "READY"
        assert data["payroll_baseline_rows"] == 1
        assert data["postgres_load_plan_validation_status"] == "pass"
        assert data["postgres_connection_used"] is False
        assert data["database_mutation_performed"] is False
        assert "/private_runtime/" not in p.stdout
        assert str(runtime) not in p.stdout
        assert (runtime / "stage2" / "202607" / "stage2_consensus_certificate.json").is_file()
        assert (runtime / "db_landing" / "202607" / "payroll_baseline_attendance.jsonl").is_file()
        assert (runtime / "db_landing" / "202607" / "postgres_load_plan_manifest.json").is_file()


def test_stage2_accepted_rehearsal_rejects_unverified_database_source():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        source = runtime / "source.unverified.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        snapshot = json.loads((FIX / "minimal_snapshot_a.json").read_text(encoding="utf-8"))
        snapshot["quality_gates"] = {
            "location_evidence_thresholds_passed": True,
            "raw_to_derived_reconciliation_passed": True,
            "database_transaction_committed": True,
            "database_transaction_verified": True,
        }
        snapshot["database_transaction_marker"] = "postgres-nonprod:test-marker"
        source.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        p = run([
            sys.executable,
            str(SCRIPT_DIR / "run_stage2_accepted_rehearsal.py"),
            "--source-json",
            str(source),
            "--target-month",
            "202607",
            "--out-root",
            str(runtime),
            "--print-json",
        ], check=False)
        assert p.returncode != 0
        assert "database_execution_proof_state_counts_not_verified" in p.stderr


def test_evening_live_source_adapter_fails_closed_without_dws_authorization():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "private_runtime"
        env = os.environ.copy()
        env.update({
            "KMFA_REPO_ROOT": str(ROOT.parent),
            "KMFA_PRIVATE_RUNTIME": str(runtime),
            "KMFA_RUN_SLOT": "evening",
            "KMFA_TODAY_OVERRIDE": "2026-08-01",
            "KMFA_STAGE2_SOURCE_MODE": "dws_live",
            "KMFA_S19_ALLOW_DWS_COMMANDS": "0",
        })
        env.pop("KMFA_STAGE2_SOURCE_JSON", None)
        p = subprocess.run(
            [str(SCRIPT_DIR / "run_stage2_evening.sh")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        assert p.returncode == 2
        assert "STAGE2_ADAPTER_SOURCE_MISSING" in p.stderr
        run_dir = runtime / "stage2" / "202607" / "run_01"
        status_path = run_dir / "source_adapter_status.json"
        assert status_path.is_file()
        status = json.loads(status_path.read_text(encoding="utf-8"))
        assert status["status"] == "STAGE2_ADAPTER_SOURCE_MISSING"
        assert status["source_mode"] == "dws_live"
        assert status["live_dws_performed"] is False
        assert status["dws_commands_allowed"] is False
        assert not (run_dir / "run_manifest.json").exists()


if __name__ == "__main__":
    test_accepts_identical()
    test_rejects_divergent()
    test_rejects_identical_hashes_without_required_quality_gates()
    test_evening_replay_adapter_writes_five_run_artifacts_and_fails_without_database_commit()
    test_stage2_accepted_rehearsal_requires_db_verified_source_and_materializes_landing_bundle()
    test_stage2_accepted_rehearsal_rejects_unverified_database_source()
    test_evening_live_source_adapter_fails_closed_without_dws_authorization()
    print("stage2 consensus tests passed")
