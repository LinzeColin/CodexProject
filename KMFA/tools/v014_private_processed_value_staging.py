#!/usr/bin/env python3
"""Generate KMFA v0.1.4 private processed value staging evidence.

This phase does not read the raw inbox and does not compare raw values with
processed values. It scans existing public-safe KMFA metadata for value-like
processed private-ref slots, writes the slot list to ignored private runtime,
and publishes only aggregate readiness evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_staging.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_staging_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_staging.v1"
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_STAGING"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-STAGING-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-STAGING"
STATUS = "completed_validated_local_only_no_go_processed_target_slots_staged_value_fingerprints_missing"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_STAGING")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_staging_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_staging_go_no_go_report.json"
STAGING_SUMMARY_PATH = MACHINE_DIR / "private_processed_value_staging_summary.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_staging_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_staging_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_staging_go_no_go_report.json")
METADATA_STAGING_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_staging_summary.json")

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_staging")
PRIVATE_STAGING_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_staging.json"
PRIVATE_MATERIALIZATION_REQUEST_PATH = PRIVATE_OUTPUT_DIR / "local_materialization_request.md"

RAW_DRY_RUN_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_RAW_VALUE_MATCHING_PRIVATE_DRY_RUN/machine/raw_value_matching_private_dry_run_manifest.json"
)
RAW_DRY_RUN_GO_NO_GO_PATH = Path(
    "KMFA/stage_artifacts/V014_RAW_VALUE_MATCHING_PRIVATE_DRY_RUN/machine/raw_value_matching_private_dry_run_go_no_go_report.json"
)

PROCESSED_SCAN_ROOTS = (
    Path("KMFA/metadata/lineage"),
    Path("KMFA/metadata/reports"),
    Path("KMFA/metadata/quality"),
)
PRIVATE_REF_RE = re.compile(r"\bprivate(?:_ref)?://[^\s\"',}\]]+")
VALUE_CONTEXT_RE = re.compile(
    r"(amount|balance|cash|cent|collection|cost|gross|invoice|margin|metric|price|profit|rate|ratio|revenue|tax|value)",
    re.IGNORECASE,
)
EXCLUDED_CONTEXT_RE = re.compile(
    r"(raw|source_file|source_header|header|filename|package|owner|decision|template|connector|credential|secret)",
    re.IGNORECASE,
)


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip()


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _iter_records(path: Path) -> Iterable[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return []
    if suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except Exception:
                continue
            if isinstance(value, dict):
                records.append(value)
        return records
    if suffix == ".csv":
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))
        except Exception:
            return []
    return []


def _walk_private_refs(value: Any, key_path: tuple[str, ...] = ()) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from _walk_private_refs(nested, (*key_path, str(key)))
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_private_refs(nested, (*key_path, "item"))
    elif isinstance(value, str):
        for match in PRIVATE_REF_RE.findall(value):
            yield ".".join(key_path), match


def _root_id(path: Path) -> str:
    parts = path.parts
    if "lineage" in parts:
        return "metadata_lineage"
    if "reports" in parts:
        return "metadata_reports"
    if "quality" in parts:
        return "metadata_quality"
    return "metadata_other"


def _is_processed_value_slot(path: Path, key_path: str, private_ref: str) -> bool:
    context = f"{path.as_posix()} {key_path} {private_ref}"
    if not VALUE_CONTEXT_RE.search(context):
        return False
    if EXCLUDED_CONTEXT_RE.search(key_path) or EXCLUDED_CONTEXT_RE.search(private_ref):
        return False
    return True


def _scan_processed_target_slots() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    files: list[Path] = []
    for root in PROCESSED_SCAN_ROOTS:
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.suffix.lower() in {".json", ".jsonl", ".csv"})

    private_ref_candidate_count = 0
    excluded_private_ref_count = 0
    records_scanned = 0
    slots_by_root: dict[str, int] = {}
    slots_by_context_group: dict[str, int] = {}
    slots: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for path in sorted(files):
        for record_index, record in enumerate(_iter_records(path), 1):
            records_scanned += 1
            record_hash = _hash_text(json.dumps(record, ensure_ascii=False, sort_keys=True))
            for key_path, private_ref in _walk_private_refs(record):
                private_ref_candidate_count += 1
                if not _is_processed_value_slot(path, key_path, private_ref):
                    excluded_private_ref_count += 1
                    continue
                dedupe_key = (path.as_posix(), key_path, private_ref)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                root_id = _root_id(path)
                context_group = key_path.split(".")[-1] if key_path else "value_private_ref"
                slots_by_root[root_id] = slots_by_root.get(root_id, 0) + 1
                slots_by_context_group[context_group] = slots_by_context_group.get(context_group, 0) + 1
                slot_index = len(slots) + 1
                slots.append(
                    {
                        "target_slot_id": f"PVSTG-{slot_index:05d}",
                        "source_artifact_ref_hash": _hash_text(path.as_posix()),
                        "source_root_id": root_id,
                        "record_ref_hash": record_hash,
                        "record_index": record_index,
                        "target_key_ref_hash": _hash_text(key_path),
                        "context_group": context_group,
                        "private_processed_ref": private_ref,
                        "private_processed_ref_hash": _hash_text(private_ref),
                        "value_fingerprint": None,
                        "value_materialized": False,
                    }
                )

    public_summary = {
        "processed_artifact_files_scanned": len(files),
        "processed_records_scanned": records_scanned,
        "private_ref_candidate_count": private_ref_candidate_count,
        "excluded_private_ref_count": excluded_private_ref_count,
        "processed_target_slot_count": len(slots),
        "approved_private_processed_target_slot_count": len(slots),
        "private_processed_value_fingerprint_count": 0,
        "processed_target_slots_staged": len(slots) > 0,
        "processed_value_materialization_complete": False,
        "target_slots_by_root": dict(sorted(slots_by_root.items())),
        "target_slots_by_context_group_count": len(slots_by_context_group),
        "target_slot_private_refs_committed_publicly": False,
        "processed_business_values_committed_publicly": False,
        "staging_status": (
            "processed_target_slots_staged_value_fingerprints_missing"
            if slots
            else "processed_target_slots_missing"
        ),
    }
    return public_summary, slots


def _go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "v014_private_processed_value_staging_go_no_go_report",
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": (
            "Processed private target slots are staged in ignored private runtime, but processed value fingerprints "
            "are not materialized, so raw-to-processed value comparison and business consistency cannot be claimed."
        ),
        "resolved_blocker_ids": [
            "PROCESSED_PRIVATE_TARGET_SLOTS_STAGED",
            "PUBLIC_SAFE_AGGREGATE_EVIDENCE_GENERATED",
            "RAW_INBOX_NOT_ACCESSED_BY_THIS_PHASE",
        ],
        "blocker_ids": [
            "PRIVATE_PROCESSED_VALUE_FINGERPRINTS_NOT_MATERIALIZED",
            "COMPARABLE_RAW_PROCESSED_VALUE_PAIRS_ZERO",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_BLOCKED_BY_VALUE_CONSISTENCY",
            "FORMAL_REPORT_RELEASE_BLOCKED_BY_LINEAGE",
            "GITHUB_UPLOAD_BLOCKED_BY_NO_GO",
            "APP_REINSTALL_BLOCKED_BY_NO_GO",
            "BUSINESS_EXECUTION_BLOCKED_BY_NO_GO",
        ],
        "processed_target_slots_staged": summary["processed_target_slots_staged"],
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "private_processed_value_fingerprint_count": 0,
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "raw_business_data_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "private_csv_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "archive_entry_names_committed": False,
        "sheet_names_committed": False,
        "field_or_header_plaintext_committed": False,
        "raw_or_processed_business_values_committed": False,
        "processed_private_ref_strings_committed": False,
        "credential_or_secret_committed": False,
        "private_staging_committed": False,
    }


def generate(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = _now(generated_at)
    raw_dry_run_manifest = _read_json(RAW_DRY_RUN_MANIFEST_PATH)
    raw_dry_run_go_no_go = _read_json(RAW_DRY_RUN_GO_NO_GO_PATH)
    summary, slots = _scan_processed_target_slots()
    go_no_go = _go_no_go(summary)

    private_staging = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_processed_value_staging_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_raw_dry_run_phase_id": raw_dry_run_manifest.get("phase_id"),
        "source_raw_value_fingerprint_count": raw_dry_run_manifest.get("value_matching_summary", {}).get(
            "raw_value_fingerprint_count", 0
        ),
        "processed_staging_summary": summary,
        "processed_target_slots": slots,
        "private_processed_value_fingerprint_count": 0,
        "value_materialization_complete": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    _write_json(PRIVATE_STAGING_PATH, private_staging)
    _write_text(
        PRIVATE_MATERIALIZATION_REQUEST_PATH,
        "\n".join(
            [
                "# KMFA private processed value materialization request",
                "",
                "- classification: private_runtime_do_not_commit",
                "- processed target slots staged: true",
                f"- processed target slot count: {summary['processed_target_slot_count']}",
                "- processed value fingerprints materialized: false",
                "- raw-to-processed comparison performed: false",
                "- next action: resolve staged processed private refs into private value fingerprints before comparison",
                "",
            ]
        ),
    )

    value_matching_readiness = {
        "raw_value_fingerprints_available_from_previous_phase": bool(
            raw_dry_run_manifest.get("value_matching_summary", {}).get("raw_value_fingerprints_generated")
        ),
        "raw_value_fingerprint_count_from_previous_phase": raw_dry_run_manifest.get("value_matching_summary", {}).get(
            "raw_value_fingerprint_count", 0
        ),
        "processed_target_slots_staged": summary["processed_target_slots_staged"],
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "private_processed_value_fingerprint_count": 0,
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "minimum_independent_validation_passes_required": 3,
        "independent_validation_passes_completed_by_this_phase": 1,
        "final_goal_closeout_difference_report_required_if_repeated": True,
    }

    manifest = {
        "record_type": "v014_private_processed_value_staging_manifest",
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "Private processed value staging",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": generated_at,
        "source_commit": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "raw_value_matching_private_dry_run_manifest": str(RAW_DRY_RUN_MANIFEST_PATH),
            "raw_value_matching_private_dry_run_go_no_go": str(RAW_DRY_RUN_GO_NO_GO_PATH),
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "private_processed_value_staging_only": True,
            "raw_dry_run_dependency_consumed": True,
            "processed_target_slot_scan_performed": True,
            "processed_target_slots_staged_private_runtime": True,
            "processed_value_materialization_performed": False,
            "raw_to_processed_value_comparison_performed": False,
            "processed_data_reconciliation_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_readonly_boundary": {
            "raw_inbox_read_performed_by_this_phase": False,
            "raw_inbox_list_performed_by_this_phase": False,
            "raw_inbox_stat_performed_by_this_phase": False,
            "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
            "raw_inbox_write_performed_by_this_phase": False,
            "raw_inbox_delete_performed_by_this_phase": False,
            "raw_inbox_move_performed_by_this_phase": False,
            "raw_inbox_rename_performed_by_this_phase": False,
            "raw_inbox_overwrite_performed_by_this_phase": False,
            "raw_inbox_copy_performed_by_this_phase": False,
            "raw_inbox_create_extra_files_inside_by_this_phase": False,
            "raw_inbox_normalize_performed_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
        },
        "processed_staging_summary": summary,
        "value_matching_readiness": value_matching_readiness,
        "go_no_go": go_no_go,
        "public_repo_safety": _public_safety(),
        "private_processed_staging_ref": str(PRIVATE_STAGING_PATH),
        "private_materialization_request_ref": str(PRIVATE_MATERIALIZATION_REQUEST_PATH),
        "prior_gap_status": raw_dry_run_go_no_go.get("decision_reason", "prior_raw_dry_run_no_go"),
        "evidence_refs": [
            str(REPORT_PATH),
            str(GO_NO_GO_RECORD_PATH),
            str(TEST_RESULTS_PATH),
            str(RISK_REGISTER_PATH),
            str(ROLLBACK_PATH),
            str(MANIFEST_PATH),
            str(GO_NO_GO_PATH),
            str(STAGING_SUMMARY_PATH),
            str(METADATA_MANIFEST_PATH),
            str(METADATA_GO_NO_GO_PATH),
            str(METADATA_STAGING_SUMMARY_PATH),
        ],
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_performed": False,
        "business_execution_performed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }

    for path, payload in (
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (STAGING_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_STAGING_SUMMARY_PATH, summary),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Private Processed Value Staging",
                "",
                f"- status: `{STATUS}`",
                "- phase_scope: `V014_PRIVATE_PROCESSED_VALUE_STAGING only`",
                f"- processed_target_slots_staged: `{str(summary['processed_target_slots_staged']).lower()}`",
                f"- processed_target_slot_count: `{summary['processed_target_slot_count']}`",
                "- private_processed_value_fingerprint_count: `0`",
                "- processed_value_materialization_complete: `false`",
                "- raw_to_processed_value_comparison_performed: `false`",
                "- business_value_consistency_verified: `false`",
                "- raw_inbox_access_by_this_phase: `false`",
                "- public_artifacts_include_processed_private_refs_or_business_values: `false`",
                f"- next_recommended_phase: `{NEXT_RECOMMENDED_PHASE}`",
                "",
            ]
        ),
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                "- decision: `NO_GO`",
                "- reason: `processed_target_slots_staged_but_private_processed_value_fingerprints_missing`",
                "- lineage_full_check_complete: `false`",
                "- formal_report_allowed: `false`",
                "- github_upload_allowed: `false`",
                "- app_reinstall_allowed: `false`",
                "- business_execution_allowed: `false`",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Private Processed Value Staging Test Results",
                "",
                "- status: `pending_final_validation`",
                "- generator: `pending_final_validation`",
                "- validator: `pending_final_validation`",
                "- focused_unit_test: `pending_final_validation`",
                "- governance_validator: `pending_final_validation`",
                "- raw_private_scan: `pending_final_validation`",
                "- secret_scan: `pending_final_validation`",
                "- diff_check: `pending_final_validation`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- risk: staged target slots are references only and do not contain processed value fingerprints.",
                "- control: keep decision `NO_GO` until private value fingerprints are materialized and compared.",
                "- risk: private staging could disclose internal refs if committed.",
                "- control: private staging stays under ignored `.codex_private_runtime` and validator checks it is untracked.",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove `KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_STAGING/`.",
                "- Remove `KMFA/metadata/quality/v014_private_processed_value_staging_*`.",
                "- Remove `KMFA/tools/v014_private_processed_value_staging.py` and validator/test files.",
                "- Remove ignored private runtime staging under `KMFA/.codex_private_runtime/v014_private_processed_value_staging/`.",
                "- Do not modify raw inbox.",
                "",
            ]
        ),
    )
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["processed_staging_summary"]
    print(
        "PASS: generated KMFA v0.1.4 private processed value staging "
        f"(target_slots={summary['processed_target_slot_count']}, "
        "value_fingerprints=0, business_consistency=False, decision=NO_GO)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
