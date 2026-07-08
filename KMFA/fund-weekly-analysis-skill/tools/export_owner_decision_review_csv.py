#!/usr/bin/env python3
"""Export a small no-write owner decision review CSV from OCR owner worklist rows."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


DEFAULT_OUTPUT_NAME = "ocr_fact_candidate_owner_decision_review_batch.csv"
WORKLIST_NAME = "ocr_fact_candidate_owner_worklist.csv"

OUTPUT_FIELDS = [
    "review_batch_row_id",
    "owner_worklist_id",
    "ocr_fact_evidence_review_queue_id",
    "fact_candidate_id",
    "candidate_metric",
    "source_evidence_id",
    "source_ocr_text_relative_path",
    "business_date",
    "amount",
    "currency",
    "company",
    "bank",
    "account_alias",
    "proposed_amount_role",
    "proposed_liquidity_tier",
    "proposed_flow_type",
    "owner_authorization_decision",
    "owner_corrected_company",
    "owner_corrected_bank",
    "required_owner_fields",
    "owner_note",
    "fund_ledger_write_allowed",
    "financial_fact_promoted",
    "management_conclusion_allowed",
    "recommended_owner_action",
]


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def run_dir(repo_root: Path, run_id: str) -> Path:
    return repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id


def safe_output_name(name: str) -> str:
    path = Path(name)
    if path.name != name or path.is_absolute() or name in {"", ".", ".."}:
        raise ValueError("output_name_must_be_a_plain_filename")
    if path.suffix.lower() != ".csv":
        raise ValueError("output_name_must_end_with_csv")
    return name


def parse_metrics(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def read_worklist(path: Path) -> list[dict]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError as exc:
        raise ValueError("owner_worklist_missing") from exc


def required_owner_fields(row: dict) -> str:
    missing = []
    if not str(row.get("company", "")).strip():
        missing.append("owner_corrected_company")
    if not str(row.get("bank", "")).strip():
        missing.append("owner_corrected_bank")
    return ",".join(missing)


def select_rows(rows: list[dict], metrics: list[str], limit_per_metric: int) -> list[dict]:
    if not metrics:
        selected = rows
        return selected if limit_per_metric <= 0 else selected[:limit_per_metric]
    selected: list[dict] = []
    for metric in metrics:
        metric_rows = [row for row in rows if row.get("candidate_metric") == metric]
        selected.extend(metric_rows if limit_per_metric <= 0 else metric_rows[:limit_per_metric])
    return selected


def build_review_rows(run_id: str, selected_rows: list[dict]) -> list[dict]:
    output_rows: list[dict] = []
    for row in selected_rows:
        output_rows.append({
            "review_batch_row_id": f"OCROWNERREVIEWCSV-{run_id}-{len(output_rows) + 1:05d}",
            "owner_worklist_id": row.get("owner_worklist_id", ""),
            "ocr_fact_evidence_review_queue_id": row.get("ocr_fact_evidence_review_queue_id", ""),
            "fact_candidate_id": row.get("fact_candidate_id", ""),
            "candidate_metric": row.get("candidate_metric", ""),
            "source_evidence_id": row.get("source_evidence_id", ""),
            "source_ocr_text_relative_path": row.get("source_ocr_text_relative_path", ""),
            "business_date": row.get("business_date", ""),
            "amount": row.get("amount", ""),
            "currency": row.get("currency", ""),
            "company": row.get("company", ""),
            "bank": row.get("bank", ""),
            "account_alias": row.get("account_alias", ""),
            "proposed_amount_role": row.get("proposed_amount_role", ""),
            "proposed_liquidity_tier": row.get("proposed_liquidity_tier", ""),
            "proposed_flow_type": row.get("proposed_flow_type", ""),
            "owner_authorization_decision": "pending_owner_review",
            "owner_corrected_company": "",
            "owner_corrected_bank": "",
            "required_owner_fields": required_owner_fields(row),
            "owner_note": "",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_owner_action": (
                "Fill owner_authorization_decision and required owner fields, then run "
                "install_owner_decision_manifest.py --draft-csv-path as a dry-run first."
            ),
        })
    return output_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--metrics", default="")
    parser.add_argument("--limit-per-metric", type=int, default=5)
    parser.add_argument("--output-name", default=DEFAULT_OUTPUT_NAME)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    try:
        output_name = safe_output_name(args.output_name)
        rows = read_worklist(run_dir(repo_root, args.run_id) / WORKLIST_NAME)
    except ValueError as exc:
        emit({
            "status": "BLOCKED_REVIEW_CSV_EXPORT",
            "run_id": args.run_id,
            "reason": str(exc),
            "apply_performed": False,
            "fund_ledger_write_allowed": False,
            "financial_fact_promoted": False,
            "management_conclusion_allowed": False,
        })
        return 2

    metrics = parse_metrics(args.metrics)
    selected = select_rows(rows, metrics, args.limit_per_metric)
    review_rows = build_review_rows(args.run_id, selected)
    output_relative_path = (
        Path("KMFA/metadata/fund_weekly_analysis/private_runtime/runs")
        / args.run_id
        / output_name
    )
    output_path = repo_root / output_relative_path
    write_csv(output_path, review_rows)
    emit({
        "status": "READY_REVIEW_CSV",
        "run_id": args.run_id,
        "source_worklist_relative_path": str(
            Path("KMFA/metadata/fund_weekly_analysis/private_runtime/runs") / args.run_id / WORKLIST_NAME
        ),
        "output_relative_path": str(output_relative_path),
        "metrics": metrics,
        "limit_per_metric": args.limit_per_metric,
        "source_count": len(rows),
        "selected_count": len(review_rows),
        "apply_performed": False,
        "fund_ledger_write_allowed": False,
        "financial_fact_promoted": False,
        "management_conclusion_allowed": False,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
