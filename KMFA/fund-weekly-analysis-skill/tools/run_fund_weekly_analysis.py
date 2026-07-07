#!/usr/bin/env python3
"""KMFA fund weekly analysis deterministic runner shell.

This runner does the non-LLM deterministic parts: input scan, hash manifest,
private run directory creation, and safety checks. OCR/vision extraction and Excel
creation are performed by the Codex agent under SKILL.md using the manifests and
sheet spec. The runner deliberately does not invent data.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

DISALLOWED_PRODUCTION_MARKERS = ("sample", "demo", "fake", "synthetic", "模拟", "测试数据")
PRIVATE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".xls", ".csv", ".pdf", ".doc", ".docx", ".zip"}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            yield p


def classify_file(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "screenshot"
    if suffix in {".xlsx", ".xls", ".csv"}:
        return "tabular_finance_source"
    if suffix == ".zip":
        return "archive"
    if suffix in {".pdf", ".doc", ".docx"}:
        return "document_evidence"
    return "other"


def build_manifest(input_dir: Path, run_dir: Path, timezone: str) -> dict:
    files = []
    for p in sorted(iter_files(input_dir)):
        rel = str(p.relative_to(input_dir))
        files.append({
            "relative_path": rel,
            "suffix": p.suffix.lower(),
            "kind": classify_file(p),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "mtime_iso": dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            "public_safe_to_commit": False if p.suffix.lower() in PRIVATE_EXTENSIONS else False,
        })
    now = dt.datetime.now(ZoneInfo(timezone))
    manifest = {
        "project_id": "KMFA",
        "skill_name": "fund-weekly-analysis-skill",
        "run_id": run_dir.name,
        "timezone": timezone,
        "input_dir": str(input_dir),
        "generated_at": now.isoformat(),
        "file_count": len(files),
        "files": files,
    }
    return manifest


def write_evidence_index_stub(manifest: dict, run_dir: Path) -> None:
    path = run_dir / "evidence_index.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["evidence_id", "relative_path", "kind", "sha256", "size_bytes", "review_status"])
        w.writeheader()
        for i, item in enumerate(manifest["files"], 1):
            if item["kind"] in {"screenshot", "archive", "document_evidence", "tabular_finance_source"}:
                w.writerow({
                    "evidence_id": f"FW{manifest['run_id']}-{i:05d}",
                    "relative_path": item["relative_path"],
                    "kind": item["kind"],
                    "sha256": item["sha256"],
                    "size_bytes": item["size_bytes"],
                    "review_status": "indexed_only_pending_extraction",
                })


def write_source_missing_artifacts(input_dir: Path, run_dir: Path, timezone: str) -> None:
    now = dt.datetime.now(ZoneInfo(timezone)).isoformat()
    issue = {
        "issue_type": "SOURCE_MISSING",
        "severity": "blocking",
        "path": str(input_dir),
        "observed_at": now,
        "action": "Create or refresh the DWS_Outputs/付款请示群 source before extraction; do not invent data.",
    }
    manifest = {
        "project_id": "KMFA",
        "skill_name": "fund-weekly-analysis-skill",
        "run_id": run_dir.name,
        "timezone": timezone,
        "input_dir": str(input_dir),
        "generated_at": now,
        "status": "SOURCE_MISSING",
        "file_count": 0,
        "files": [],
        "data_quality_issues": [issue],
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "data_quality_issues.json").write_text(json.dumps([issue], ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "evidence_index.csv").write_text(
        "evidence_id,relative_path,kind,sha256,size_bytes,review_status\n",
        encoding="utf-8-sig",
    )
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {run_dir.name}\n\n"
        f"Status: SOURCE_MISSING\n\n"
        f"Missing input directory: `{input_dir}`\n\n"
        "No extraction, financial conclusion, or Excel production was performed. This is a fail-closed run.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群")
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--timezone", default="Australia/Sydney")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    timezone = ZoneInfo(args.timezone)
    input_dir = Path(args.input_dir).expanduser().resolve()
    run_id = args.run_id or dt.datetime.now(timezone).strftime("%Y%m%dT%H%M%S%z")
    run_dir = repo_root / "KMFA" / "metadata" / "fund_weekly_analysis" / "private_runtime" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        write_source_missing_artifacts(input_dir, run_dir, args.timezone)
        print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": "SOURCE_MISSING"}, ensure_ascii=False))
        return 2

    manifest = build_manifest(input_dir, run_dir, args.timezone)
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_evidence_index_stub(manifest, run_dir)
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {run_id}\n\nIndexed {manifest['file_count']} files. Next step: Codex agent reads SKILL.md and performs extraction, cross-validation, and Excel generation without simulated data.\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "file_count": manifest["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
