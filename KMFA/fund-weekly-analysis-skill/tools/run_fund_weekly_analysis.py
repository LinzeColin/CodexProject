#!/usr/bin/env python3
"""KMFA fund weekly analysis deterministic runner shell.

This runner does the non-LLM deterministic parts: input scan, hash manifest,
private run directory creation, and safety checks. OCR/vision extraction and Excel
creation are performed by the Codex agent under SKILL.md using the manifests and
sheet spec. The runner deliberately does not invent data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

DISALLOWED_PRODUCTION_MARKERS = ("sample", "demo", "fake", "synthetic", "模拟", "测试数据")
PRIVATE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".xls", ".csv", ".pdf", ".doc", ".docx", ".zip"}
TEMPLATE_NAME = "资金与税费管理母版_真实数据预览_v2.xlsx"


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


def iso_from_timestamp(timestamp: float) -> str:
    return dt.datetime.fromtimestamp(timestamp).isoformat()


def summarize_tree(path: Path, limit: int = 5000) -> dict:
    file_count = 0
    latest_mtime: float | None = None
    for p in path.rglob("*"):
        if not p.is_file() or p.name.startswith("."):
            continue
        file_count += 1
        latest_mtime = max(latest_mtime or p.stat().st_mtime, p.stat().st_mtime)
        if file_count >= limit:
            break
    return {
        "file_count_limited": file_count,
        "file_count_limit": limit,
        "latest_file_mtime_iso": iso_from_timestamp(latest_mtime) if latest_mtime else None,
    }


def source_candidates_for(input_dir: Path) -> list[dict]:
    group_name = input_dir.name
    one_drive_root = input_dir.parent.parent if input_dir.parent.name == "DWS_Outputs" else input_dir.parent
    candidates = [
        ("dws_outputs_zip", one_drive_root / "DWS_Outputs.zip"),
        ("dws_archive_group", one_drive_root / "DWS_Archive" / group_name),
    ]
    result = []
    for kind, path in candidates:
        item = {
            "kind": kind,
            "path": str(path),
            "exists": path.exists(),
            "inspected": False,
            "note": "private source candidate; not used unless explicitly materialized into the configured input folder",
        }
        if path.exists():
            stat = path.stat()
            item.update({
                "size_bytes": stat.st_size,
                "mtime_iso": iso_from_timestamp(stat.st_mtime),
            })
            if path.is_dir():
                item.update(summarize_tree(path))
                item["inspected"] = True
            else:
                item["file_count_limited"] = None
                item["file_count_limit"] = None
                item["latest_file_mtime_iso"] = item["mtime_iso"]
        result.append(item)
    return result


def source_summary(files: list[dict]) -> dict:
    kinds = Counter(item["kind"] for item in files)
    suffixes = Counter(item["suffix"] or "<none>" for item in files)
    latest = max((item["mtime_iso"] for item in files), default=None)
    return {
        "kind_counts": dict(sorted(kinds.items())),
        "suffix_counts": dict(sorted(suffixes.items())),
        "latest_file_mtime_iso": latest,
        "real_file_count": len(files),
    }


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
        "status": "INDEXED_PENDING_EXTRACTION",
        "generation_mode": "no_hallucination_index_only",
        "file_count": len(files),
        "files": files,
        "source_summary": source_summary(files),
        "data_quality_issues": [{
            "issue_type": "PENDING_OCR_OR_REVIEW",
            "severity": "blocking_for_management_conclusion",
            "observed_at": now.isoformat(),
            "action": "Evidence was indexed from real files, but no financial amount is promoted until OCR/table extraction and review pass.",
        }],
    }
    return manifest


def evidence_rows(manifest: dict) -> list[dict]:
    rows = []
    for i, item in enumerate(manifest["files"], 1):
        if item["kind"] in {"screenshot", "archive", "document_evidence", "tabular_finance_source"}:
            rows.append({
                "evidence_id": f"FW{manifest['run_id']}-{i:05d}",
                "relative_path": item["relative_path"],
                "kind": item["kind"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "review_status": "indexed_only_pending_extraction",
            })
    return rows


def write_evidence_index_stub(manifest: dict, run_dir: Path) -> list[dict]:
    path = run_dir / "evidence_index.csv"
    rows = evidence_rows(manifest)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["evidence_id", "relative_path", "kind", "sha256", "size_bytes", "review_status"])
        w.writeheader()
        w.writerows(rows)
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict] | None = None) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def write_no_hallucination_outputs(manifest: dict, run_dir: Path) -> None:
    evidence = write_evidence_index_stub(manifest, run_dir)
    skill_root = Path(__file__).resolve().parents[1]
    template = skill_root / "templates" / TEMPLATE_NAME
    workbook_path = run_dir / f"资金与税费管理母版_{manifest['run_id']}.xlsx"
    shutil.copyfile(template, workbook_path)

    write_csv(run_dir / "fund_ledger.csv", [
        "ledger_id",
        "date",
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "inflow",
        "outflow",
        "ending_balance",
        "source_evidence_id",
        "extraction_status",
    ])
    write_csv(run_dir / "net_flow_ledger.csv", [
        "date",
        "external_inflow",
        "external_outflow",
        "internal_transfer_in",
        "internal_transfer_out",
        "internal_transfer_net",
        "unclassified_net",
        "review_status",
    ])
    write_csv(run_dir / "company_bank_matrix.csv", [
        "company",
        "bank",
        "account_alias",
        "liquidity_tier",
        "ending_balance",
        "evidence_count",
        "review_status",
    ])
    write_csv(run_dir / "tax_loan_risk.csv", [
        "risk_id",
        "risk_type",
        "due_date",
        "amount",
        "source_evidence_id",
        "review_status",
    ])
    write_csv(
        run_dir / "exception_tasks.csv",
        ["task_id", "evidence_id", "task_type", "severity", "reason", "relative_path", "review_status"],
        [
            {
                "task_id": f"EX-{manifest['run_id']}-{index:05d}",
                "evidence_id": row["evidence_id"],
                "task_type": "PENDING_OCR_OR_REVIEW",
                "severity": "blocking_for_financial_fact",
                "reason": "Real source evidence indexed; financial facts require OCR/table extraction and review before use.",
                "relative_path": row["relative_path"],
                "review_status": "pending",
            }
            for index, row in enumerate(evidence, 1)
        ],
    )

    cross_review = {
        "run_id": manifest["run_id"],
        "management_conclusion_allowed": False,
        "generated_financial_amount_count": 0,
        "excel_workbook_generated": True,
        "workbook": workbook_path.name,
        "source_file_count": manifest["file_count"],
        "evidence_count": len(evidence),
        "status": manifest["status"],
        "reason": "No amount was generated or inferred before OCR/table extraction and review gates.",
    }
    (run_dir / "cross_review.json").write_text(json.dumps(cross_review, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "audit_log.json").write_text(
        json.dumps([
            {
                "event": "real_sources_indexed",
                "run_id": manifest["run_id"],
                "file_count": manifest["file_count"],
            },
            {
                "event": "no_hallucination_outputs_written",
                "generated_financial_amount_count": 0,
                "management_conclusion_allowed": False,
            },
        ], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "data_quality_issues.json").write_text(
        json.dumps(manifest["data_quality_issues"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_source_missing_artifacts(input_dir: Path, run_dir: Path, timezone: str) -> None:
    now = dt.datetime.now(ZoneInfo(timezone)).isoformat()
    candidates = source_candidates_for(input_dir)
    issue = {
        "issue_type": "SOURCE_MISSING",
        "severity": "blocking",
        "path": str(input_dir),
        "observed_at": now,
        "action": "Create or refresh the DWS_Outputs/付款请示群 source, or run an explicit materialization step from a verified private source candidate; do not invent data.",
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
        "source_candidates": candidates,
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
    write_no_hallucination_outputs(manifest, run_dir)
    (run_dir / "run_summary.md").write_text(
        f"# Fund weekly analysis run {run_id}\n\n"
        f"Status: INDEXED_PENDING_EXTRACTION\n\n"
        f"Indexed {manifest['file_count']} real source files and generated a native editable Excel workbook from the current mother template.\n\n"
        "No financial amount, management conclusion, or forecast was generated from unreviewed OCR/table extraction. "
        "Next step: perform OCR/table extraction, internal-transfer netting, cross-review, then promote reviewed facts only.\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "status": manifest["status"], "file_count": manifest["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
