#!/usr/bin/env python3
from __future__ import annotations

import json
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


def write_manifest(folder: Path, run_index: int, target_month="202607", quality="Q4", p0=0, p1=0):
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


if __name__ == "__main__":
    test_accepts_identical()
    test_rejects_divergent()
    print("stage2 consensus tests passed")
