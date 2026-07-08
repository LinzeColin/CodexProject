#!/usr/bin/env python3
"""Install reviewed OCR owner decision corrections into private runtime.

Dry-run is the default. The tool writes only the private owner decision
manifest, and only after the owner-reviewed draft has complete required fields
and the operator passes an explicit acknowledgement flag.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path


DECISION_SCOPE = "ocr_fact_candidate_owner_worklist_validation_only"
SOURCE_ARTIFACT = "ocr_fact_candidate_owner_worklist.csv"
PRIVATE_DECISION_PREFIX = Path(
    "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions"
)


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def default_run_dir(repo_root: Path, run_id: str) -> Path:
    return repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id


def default_draft_path(repo_root: Path, run_id: str) -> Path:
    return default_run_dir(repo_root, run_id) / "ocr_fact_owner_decision_correction_draft.json"


def candidate_template_path(repo_root: Path, run_id: str) -> Path:
    return default_run_dir(repo_root, run_id) / "ocr_fact_candidate_owner_decision_template.json"


def default_output_relative_path(run_id: str) -> str:
    return str(PRIVATE_DECISION_PREFIX / f"{run_id}.json")


def safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("output_decision_manifest_relative_path must be a safe relative path")
    return path


def load_draft(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("draft_missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("draft_invalid_json") from exc
    if not isinstance(payload, dict):
        raise ValueError("draft_invalid_schema")
    return payload


def load_csv_draft(path: Path, run_id: str) -> dict:
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError as exc:
        raise ValueError("draft_missing") from exc
    except csv.Error as exc:
        raise ValueError("draft_invalid_csv") from exc
    if not rows:
        raise ValueError("draft_has_no_owner_decisions")
    decisions: list[dict] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"draft_invalid_schema:csv_row[{index}]")
        decisions.append({
            "fact_candidate_id": str(row.get("fact_candidate_id", "")),
            "candidate_metric": str(row.get("candidate_metric", "")),
            "owner_authorization_decision": str(row.get("owner_authorization_decision", "")),
            "owner_corrected_company": str(row.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(row.get("owner_corrected_bank", "")),
            "required_owner_fields": str(row.get("required_owner_fields", "")),
            "owner_note": str(row.get("owner_note", "")),
        })
    return {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "draft_status": "owner_decision_csv_intake",
        "generated_from": path.name,
        "source_artifact": SOURCE_ARTIFACT,
        "output_decision_manifest_relative_path": default_output_relative_path(run_id),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "owner_decisions": decisions,
    }


def resolve_default_draft_path(repo_root: Path, run_id: str) -> Path:
    correction_path = default_draft_path(repo_root, run_id)
    template_path = candidate_template_path(repo_root, run_id)
    try:
        correction_draft = load_draft(correction_path)
    except ValueError:
        return template_path if template_path.exists() else correction_path
    if not correction_draft.get("owner_decisions") and template_path.exists():
        return template_path
    return correction_path


def required_fields_from(decision: dict) -> list[str]:
    raw = str(decision.get("required_owner_fields", ""))
    return [field.strip() for field in raw.split(",") if field.strip()]


def validate_draft(draft: dict, run_id: str) -> tuple[dict, list[dict]]:
    required = {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "source_artifact": SOURCE_ARTIFACT,
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    for key, expected in required.items():
        if draft.get(key) != expected:
            raise ValueError(f"draft_invalid_schema:{key}")
    output_relative_path = draft.get("output_decision_manifest_relative_path")
    if output_relative_path != default_output_relative_path(run_id):
        raise ValueError("draft_invalid_schema:output_decision_manifest_relative_path")
    output_path = safe_relative_path(str(output_relative_path))
    if output_path.parent != PRIVATE_DECISION_PREFIX:
        raise ValueError("draft_invalid_schema:output_decision_manifest_relative_path")

    raw_decisions = draft.get("owner_decisions")
    if not isinstance(raw_decisions, list) or not raw_decisions:
        raise ValueError("draft_has_no_owner_decisions")

    seen_ids: set[str] = set()
    decisions: list[dict] = []
    missing_values: list[str] = []
    not_approved: list[str] = []
    for index, decision in enumerate(raw_decisions, 1):
        if not isinstance(decision, dict):
            raise ValueError(f"draft_invalid_schema:owner_decisions[{index}]")
        fact_candidate_id = str(decision.get("fact_candidate_id", ""))
        candidate_metric = str(decision.get("candidate_metric", ""))
        if not fact_candidate_id or not candidate_metric:
            raise ValueError(f"draft_invalid_schema:owner_decisions[{index}]")
        if fact_candidate_id in seen_ids:
            raise ValueError(f"draft_invalid_schema:duplicate_fact_candidate_id:{fact_candidate_id}")
        seen_ids.add(fact_candidate_id)
        owner_decision = str(decision.get("owner_authorization_decision", ""))
        if owner_decision != "approve_for_review_authorization":
            not_approved.append(fact_candidate_id)
        required_owner_fields = required_fields_from(decision)
        if not required_owner_fields and draft.get("draft_status") == "owner_decision_correction_manifest_draft":
            raise ValueError(f"draft_invalid_schema:required_owner_fields:{fact_candidate_id}")
        for field in required_owner_fields:
            if not str(decision.get(field, "")).strip() and field not in missing_values:
                missing_values.append(field)
        decisions.append({
            "fact_candidate_id": fact_candidate_id,
            "candidate_metric": candidate_metric,
            "owner_authorization_decision": owner_decision,
            "owner_corrected_company": str(decision.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(decision.get("owner_corrected_bank", "")),
            "owner_note": str(decision.get("owner_note", "")),
        })
    return (
        {
            "output_relative_path": str(output_path),
            "missing_owner_values": missing_values,
            "not_approved_fact_candidate_ids": not_approved,
        },
        decisions,
    )


def build_manifest(run_id: str, decisions: list[dict]) -> dict:
    return {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "source_artifact": SOURCE_ARTIFACT,
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "owner_decisions": decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--draft-path", default="")
    parser.add_argument("--draft-csv-path", default="")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--acknowledge-owner-reviewed-values", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if args.draft_path and args.draft_csv_path:
        emit({
            "status": "INVALID_ARGUMENTS",
            "run_id": args.run_id,
            "reason": "choose only one of --draft-path or --draft-csv-path",
            "apply_performed": False,
            "financial_fact_promotion_allowed": False,
            "fund_ledger_write_allowed": False,
            "management_conclusion_allowed": False,
        })
        return 2
    draft_format = "csv" if args.draft_csv_path else "json"
    draft_path = (
        Path(args.draft_csv_path or args.draft_path).expanduser().resolve()
        if args.draft_path or args.draft_csv_path
        else resolve_default_draft_path(repo_root, args.run_id)
    )
    try:
        draft = load_csv_draft(draft_path, args.run_id) if args.draft_csv_path else load_draft(draft_path)
        validation, decisions = validate_draft(draft, args.run_id)
    except ValueError as exc:
        reason = str(exc)
        status = "DRAFT_MISSING" if reason == "draft_missing" else "INVALID_DRAFT_SCHEMA"
        emit({
            "status": status,
            "run_id": args.run_id,
            "draft_path": str(draft_path),
            "draft_format": draft_format,
            "reason": reason,
            "apply_performed": False,
            "financial_fact_promotion_allowed": False,
            "fund_ledger_write_allowed": False,
            "management_conclusion_allowed": False,
        })
        return 2

    base_payload = {
        "run_id": args.run_id,
        "draft_path": str(draft_path),
        "draft_format": draft_format,
        "output_decision_manifest_relative_path": validation["output_relative_path"],
        "output_decision_manifest_path": str(repo_root / validation["output_relative_path"]),
        "owner_decision_count": len(decisions),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    if validation["missing_owner_values"]:
        emit({
            **base_payload,
            "status": "BLOCKED_OWNER_VALUES_MISSING",
            "missing_owner_values": validation["missing_owner_values"],
            "apply_performed": False,
        })
        return 3
    if validation["not_approved_fact_candidate_ids"]:
        emit({
            **base_payload,
            "status": "BLOCKED_OWNER_DECISION_NOT_APPROVED",
            "not_approved_fact_candidate_ids": validation["not_approved_fact_candidate_ids"],
            "apply_performed": False,
        })
        return 3
    if args.apply and not args.acknowledge_owner_reviewed_values:
        emit({
            **base_payload,
            "status": "ACK_REQUIRED",
            "apply_performed": False,
        })
        return 2

    output_path = repo_root / validation["output_relative_path"]
    if not args.apply:
        emit({
            **base_payload,
            "status": "READY_DRY_RUN",
            "apply_performed": False,
        })
        return 0
    if output_path.exists():
        emit({
            **base_payload,
            "status": "TARGET_EXISTS",
            "apply_performed": False,
        })
        return 4

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_manifest(args.run_id, decisions), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    emit({
        **base_payload,
        "status": "APPLIED",
        "apply_performed": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
