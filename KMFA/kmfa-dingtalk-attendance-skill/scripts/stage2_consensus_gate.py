#!/usr/bin/env python3
"""Validate five-run stage-2 exact consensus for a target month.

Expected folder layout:
  stage2/YYYYMM/run_01/run_manifest.json
  stage2/YYYYMM/run_01/canonical_snapshot.sha256
  ... run_05/...
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunCheck:
    run_index: int
    folder: str
    present: bool
    hash: str | None
    quality_grade: str | None
    p0: int | None
    p1: int | None
    stage2_status: str | None
    failures: list[str]


QUALITY_ORDER = {"Q0": 0, "Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "Q5": 5}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def check_run(root: Path, run_index: int, min_quality: str) -> RunCheck:
    folder = root / f"run_{run_index:02d}"
    failures: list[str] = []
    sha_path = folder / "canonical_snapshot.sha256"
    manifest_path = folder / "run_manifest.json"
    if not folder.is_dir():
        return RunCheck(run_index, str(folder), False, None, None, None, None, None, ["run_folder_missing"])
    digest = None
    if sha_path.is_file():
        digest = sha_path.read_text(encoding="utf-8").strip()
    else:
        failures.append("canonical_snapshot_sha_missing")
    manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
    else:
        failures.append("run_manifest_missing")
    grade = manifest.get("quality_grade")
    if grade not in QUALITY_ORDER:
        failures.append("quality_grade_missing_or_invalid")
    elif QUALITY_ORDER[grade] < QUALITY_ORDER[min_quality]:
        failures.append(f"quality_below_{min_quality}:{grade}")
    unresolved = manifest.get("unresolved_exceptions", {}) if isinstance(manifest.get("unresolved_exceptions"), dict) else {}
    p0 = int(unresolved.get("P0", 999))
    p1 = int(unresolved.get("P1", 999))
    if p0 != 0:
        failures.append(f"P0_unresolved:{p0}")
    if p1 != 0:
        failures.append(f"P1_unresolved:{p1}")
    stage2_status = manifest.get("stage2_status")
    return RunCheck(run_index, str(folder), True, digest, grade, p0, p1, stage2_status, failures)


def write_hash_matrix(path: Path, checks: list[RunCheck]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["run_index", "present", "hash", "quality_grade", "P0", "P1", "failures"])
        writer.writeheader()
        for c in checks:
            writer.writerow({
                "run_index": c.run_index,
                "present": c.present,
                "hash": c.hash or "",
                "quality_grade": c.quality_grade or "",
                "P0": c.p0 if c.p0 is not None else "",
                "P1": c.p1 if c.p1 is not None else "",
                "failures": ";".join(c.failures),
            })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage2-root", required=True, help="Path to private_runtime/stage2/YYYYMM")
    parser.add_argument("--target-month", required=True)
    parser.add_argument("--min-quality", default="Q4", choices=sorted(QUALITY_ORDER))
    args = parser.parse_args()
    root = Path(args.stage2_root)
    root.mkdir(parents=True, exist_ok=True)
    checks = [check_run(root, i, args.min_quality) for i in range(1, 6)]
    all_hashes = [c.hash for c in checks if c.hash]
    exact_hash_match = len(all_hashes) == 5 and len(set(all_hashes)) == 1
    failures = []
    for c in checks:
        failures.extend([f"run_{c.run_index:02d}:{f}" for f in c.failures])
    if not exact_hash_match:
        failures.append("five_run_hash_consensus_failed")
    accepted = not failures and exact_hash_match
    certificate = {
        "target_month": args.target_month,
        "stage2_status": "accepted" if accepted else "failed",
        "accepted": accepted,
        "canonical_snapshot_hash": all_hashes[0] if exact_hash_match else None,
        "run_checks": [asdict(c) for c in checks],
        "failures": failures,
    }
    cert_json = root / "stage2_consensus_certificate.json"
    cert_md = root / "stage2_consensus_certificate.md"
    matrix = root / "stage2_hash_matrix.csv"
    divergence = root / "stage2_divergence_report.md"
    cert_json.write_text(json.dumps(certificate, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_hash_matrix(matrix, checks)
    md = [f"# Stage-2 Consensus Certificate - {args.target_month}", "", f"status: {'ACCEPTED' if accepted else 'FAILED'}", ""]
    md.append(f"canonical_snapshot_hash: {certificate['canonical_snapshot_hash'] or 'N/A'}")
    md.append("")
    md.append("| Run | Present | Hash | Quality | P0 | P1 | Failures |")
    md.append("|---:|---:|---|---|---:|---:|---|")
    for c in checks:
        md.append(f"| {c.run_index} | {str(c.present).lower()} | {c.hash or ''} | {c.quality_grade or ''} | {c.p0 if c.p0 is not None else ''} | {c.p1 if c.p1 is not None else ''} | {'; '.join(c.failures)} |")
    cert_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    if not accepted:
        divergence.write_text("# Stage-2 Divergence Report\n\n" + "\n".join(f"- {x}" for x in failures) + "\n", encoding="utf-8")
    print(json.dumps(certificate, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
