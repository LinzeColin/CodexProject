#!/usr/bin/env python3
"""Generate KMFA v0.1.4 authorized private processed source-map fill evidence.

This phase consumes the previous ignored fill request and project metadata that
already carries authorized hash siblings. It does not read the raw inbox and it
does not compare raw values with processed values. The private source map stays
in ignored runtime; public artifacts contain aggregate status only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_authorized_fill.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_private_processed_value_source_map_authorized_fill_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map_authorized_fill.v1"
PRIVATE_SOURCE_MAP_SCHEMA_VERSION = "kmfa.private.v014_private_processed_value_source_map.v1"
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL"
TASK_ID = "KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-AUTHORIZED-FILL-20260705"
ACCEPTANCE_ID = "ACC-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-AUTHORIZED-FILL"
STATUS = "completed_validated_local_only_no_go_partial_authorized_processed_value_source_map_fill"
NEXT_RECOMMENDED_PHASE = "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "private_processed_value_source_map_authorized_fill_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "private_processed_value_source_map_authorized_fill_go_no_go_report.json"
SUMMARY_PATH = MACHINE_DIR / "private_processed_value_source_map_authorized_fill_summary.json"
REPORT_PATH = HUMAN_DIR / "private_processed_value_source_map_authorized_fill_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_authorized_fill_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_authorized_fill_go_no_go_report.json")
METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_private_processed_value_source_map_authorized_fill_summary.json")

CAPTURE_PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_capture")
FILL_REQUEST_PATH = CAPTURE_PRIVATE_DIR / "private_processed_value_source_map_fill_request.json"
CAPTURE_DIAGNOSTIC_PATH = CAPTURE_PRIVATE_DIR / "private_processed_value_source_map_capture.json"
CAPTURE_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE/machine/private_processed_value_source_map_capture_manifest.json"
)

METADATA_ROOT = Path("KMFA/metadata")
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_private_processed_value_source_map_authorized_fill")
PRIVATE_AUTHORIZED_FILL_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map_authorized_fill.json"
PRIVATE_SOURCE_MAP_PATH = PRIVATE_OUTPUT_DIR / "private_processed_value_source_map.json"
MATERIALIZATION_SOURCE_MAP_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_source_map.json"
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


def _current_git_commit() -> str:
    return _git_output(["rev-parse", "HEAD"])


def stable_source_commit(
    *,
    manifest_path: Path = MANIFEST_PATH,
    fallback_git_commit: Callable[[], str] = _current_git_commit,
) -> str:
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        source_commit = existing.get("source_commit") if isinstance(existing, dict) else None
        if isinstance(source_commit, str) and GIT_COMMIT_RE.fullmatch(source_commit):
            return source_commit
    return fallback_git_commit()


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


def _iter_json_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_json_objects(child)


def _load_jsonl_objects(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        value = json.loads(stripped)
        if isinstance(value, dict):
            yield value


def _load_metadata_hash_siblings() -> tuple[dict[str, str], dict[str, Any]]:
    ref_to_fingerprint: dict[str, str] = {}
    source_file_counter: Counter[str] = Counter()
    pair_counter: Counter[str] = Counter()

    for path in sorted(METADATA_ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in {".json", ".jsonl"}:
            continue
        try:
            objects = list(_load_jsonl_objects(path)) if path.suffix == ".jsonl" else list(_iter_json_objects(_read_json(path)))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            continue
        for record in objects:
            for key, ref in record.items():
                if not (isinstance(key, str) and key.endswith("_private_ref") and isinstance(ref, str)):
                    continue
                stem = key[: -len("_private_ref")]
                hash_key = f"{stem}_hash"
                fingerprint = record.get(hash_key)
                if not (isinstance(fingerprint, str) and fingerprint.startswith("sha256:")):
                    continue
                ref_to_fingerprint.setdefault(ref, fingerprint)
                source_file_counter[path.as_posix()] += 1
                pair_counter[f"{key}->{hash_key}"] += 1

    private_metadata_summary = {
        "metadata_files_with_authorized_hash_siblings": dict(sorted(source_file_counter.items())),
        "metadata_hash_sibling_pairs": dict(sorted(pair_counter.items())),
        "authorized_hash_sibling_unique_ref_count": len(ref_to_fingerprint),
        "authorized_hash_sibling_item_count": sum(source_file_counter.values()),
    }
    return ref_to_fingerprint, private_metadata_summary


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_create_extra_files_inside_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "raw_business_data_committed": False,
        "source_document_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "private_csv_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "field_or_header_plaintext_committed": False,
        "sheet_names_committed": False,
        "archive_entry_names_committed": False,
        "raw_or_processed_business_values_committed": False,
        "processed_private_ref_strings_committed": False,
        "processed_private_value_strings_committed": False,
        "private_authorized_fill_committed": False,
        "private_source_map_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_authorized_fill(
    *,
    fill_request: dict[str, Any],
    capture_diagnostic: dict[str, Any],
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    ref_to_fingerprint, private_metadata_summary = _load_metadata_hash_siblings()
    request_items = fill_request.get("fill_request_items", [])
    if not isinstance(request_items, list):
        raise ValueError("fill_request_items must be a list")

    source_records: list[dict[str, str]] = []
    filled_items: list[dict[str, str]] = []
    unfilled_items: list[dict[str, str]] = []
    requested_refs: list[str] = []
    filled_refs: set[str] = set()
    unfilled_refs: set[str] = set()

    for item in request_items:
        if not isinstance(item, dict):
            continue
        target_slot_id = item.get("target_slot_id")
        private_ref = item.get("private_processed_ref")
        private_ref_hash = item.get("private_processed_ref_hash")
        if not (isinstance(target_slot_id, str) and isinstance(private_ref, str)):
            continue
        requested_refs.append(private_ref)
        fingerprint = ref_to_fingerprint.get(private_ref)
        if fingerprint:
            filled_refs.add(private_ref)
            source_records.append(
                {
                    "target_slot_id": target_slot_id,
                    "processed_value_fingerprint": fingerprint,
                    "fill_status": "filled_from_existing_metadata_hash_sibling",
                }
            )
            filled_items.append(
                {
                    "target_slot_id": target_slot_id,
                    "private_processed_ref": private_ref,
                    "private_processed_ref_hash": str(private_ref_hash),
                    "processed_value_fingerprint": fingerprint,
                    "fill_status": "filled_from_existing_metadata_hash_sibling",
                }
            )
        else:
            unfilled_refs.add(private_ref)
            unfilled_items.append(
                {
                    "target_slot_id": target_slot_id,
                    "private_processed_ref": private_ref,
                    "private_processed_ref_hash": str(private_ref_hash),
                    "fill_status": "authorized_metadata_hash_sibling_not_found",
                }
            )

    unique_ref_count = len(set(requested_refs))
    filled_count = len(filled_items)
    unfilled_count = len(unfilled_items)
    summary = {
        "fill_request_item_count": len(request_items),
        "unique_private_ref_count": unique_ref_count,
        "duplicate_private_ref_item_count": len(requested_refs) - unique_ref_count,
        "authorized_filled_item_count": filled_count,
        "authorized_unfilled_item_count": unfilled_count,
        "authorized_filled_unique_ref_count": len(filled_refs),
        "authorized_unfilled_unique_ref_count": len(unfilled_refs),
        "metadata_hash_sibling_source_file_count": len(private_metadata_summary["metadata_files_with_authorized_hash_siblings"]),
        "metadata_hash_sibling_record_count": private_metadata_summary["authorized_hash_sibling_item_count"],
        "source_map_records_written_count": len(source_records),
        "source_map_authorized_fill_complete": unfilled_count == 0 and filled_count == len(request_items),
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "source_map_authorized_fill_status": (
            "complete"
            if unfilled_count == 0 and filled_count == len(request_items)
            else "partial_authorized_fill_remaining_source_map_gaps"
        ),
    }
    private_authorized_fill = {
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "classification": "private_processed_value_source_map_authorized_fill_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_fill_request_phase_id": fill_request.get("phase_id"),
        "source_capture_phase_id": capture_diagnostic.get("phase_id"),
        "source_map_schema_version": PRIVATE_SOURCE_MAP_SCHEMA_VERSION,
        "authorized_fill_summary": summary,
        "private_metadata_summary": private_metadata_summary,
        "filled_items": filled_items,
        "unfilled_items": unfilled_items,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
    }
    private_source_map = {
        "schema_version": PRIVATE_SOURCE_MAP_SCHEMA_VERSION,
        "classification": "private_processed_value_source_map_do_not_commit",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_map_records_written_count": len(source_records),
        "source_map_authorized_fill_complete": summary["source_map_authorized_fill_complete"],
        "public_commit_policy": "do_not_commit_private_source_map_or_values",
        "processed_value_sources": sorted(source_records, key=lambda record: record["target_slot_id"]),
    }
    return summary, private_authorized_fill, private_source_map


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_authorized_fill_go_no_go_report",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "decision": "NO_GO",
        "decision_reason": "authorized fill found only partial processed value fingerprints; remaining slots block materialization and value consistency",
        "fill_request_item_count": summary["fill_request_item_count"],
        "authorized_filled_item_count": summary["authorized_filled_item_count"],
        "authorized_unfilled_item_count": summary["authorized_unfilled_item_count"],
        "source_map_records_written_count": summary["source_map_records_written_count"],
        "source_map_authorized_fill_complete": summary["source_map_authorized_fill_complete"],
        "processed_value_materialization_replay_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "resolved_blocker_ids": [
            "AUTHORIZED_METADATA_HASH_SIBLING_PARTIAL_FILL_RECORDED",
            "RAW_INBOX_MUTATION_NOT_PERFORMED_BY_THIS_PHASE",
        ],
        "blocker_ids": [
            "AUTHORIZED_PROCESSED_VALUE_SOURCE_MAP_INCOMPLETE",
            "PROCESSED_VALUE_MATERIALIZATION_REPLAY_NOT_PERFORMED",
            "RAW_TO_PROCESSED_VALUE_COMPARISON_NOT_PERFORMED",
            "BUSINESS_VALUE_CONSISTENCY_NOT_VERIFIED",
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "FORMAL_REPORT_BLOCKED",
            "GITHUB_UPLOAD_DEFERRED",
            "APP_REINSTALL_BLOCKED",
            "BUSINESS_EXECUTION_BLOCKED",
        ],
    }


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = _now(generated_at)
    fill_request = _read_json(FILL_REQUEST_PATH)
    capture_diagnostic = _read_json(CAPTURE_DIAGNOSTIC_PATH)
    capture_manifest = _read_json(CAPTURE_MANIFEST_PATH)
    summary, private_authorized_fill, private_source_map = _build_authorized_fill(
        fill_request=fill_request,
        capture_diagnostic=capture_diagnostic,
        generated_at=timestamp,
    )
    go_no_go = _build_go_no_go(summary)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_private_processed_value_source_map_authorized_fill_manifest",
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "phase_name": "KMFA v0.1.4 authorized private processed value source-map fill",
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "status": STATUS,
        "generated_at": timestamp,
        "source_commit": stable_source_commit(),
        "branch": _git_output(["branch", "--show-current"]),
        "dependencies": {
            "private_processed_value_source_map_capture_manifest": CAPTURE_MANIFEST_PATH.as_posix(),
            "private_fill_request_runtime": "private_runtime_previous_phase",
            "private_capture_diagnostic_runtime": "private_runtime_previous_phase",
            "source_capture_status": capture_manifest.get("status"),
            "metadata_hash_sibling_scan_root": "project_metadata_only",
        },
        "phase_scope_controls": {
            "current_phase_only": True,
            "authorized_private_processed_value_source_map_fill_only": True,
            "previous_fill_request_consumed": True,
            "previous_capture_diagnostic_consumed": True,
            "project_metadata_hash_sibling_scan_performed": True,
            "private_authorized_fill_diagnostic_written": True,
            "private_source_map_write_performed": True,
            "private_source_map_staged_for_future_materialization": True,
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
        "raw_readonly_boundary": _raw_boundary(),
        "authorized_fill_summary": summary,
        "value_matching_readiness": {
            "fill_request_item_count": summary["fill_request_item_count"],
            "private_processed_value_fingerprint_count": summary["authorized_filled_item_count"],
            "source_map_authorized_fill_complete": summary["source_map_authorized_fill_complete"],
            "source_map_authorized_unfilled_count": summary["authorized_unfilled_item_count"],
            "processed_value_materialization_replay_performed": False,
            "raw_to_processed_value_comparison_performed": False,
            "comparable_value_pair_count": 0,
            "business_value_consistency_verified": False,
            "minimum_independent_validation_passes_required": 2,
            "independent_validation_passes_completed_by_this_phase": 0,
            "final_goal_closeout_difference_report_required_if_repeated": True,
        },
        "public_repo_safety": _public_safety(),
        "private_authorized_fill_ref": "private_runtime_only_not_committed",
        "private_source_map_ref": "private_runtime_only_not_committed",
        "go_no_go": go_no_go,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_SUMMARY_PATH.as_posix(),
        ],
        "github_upload_performed": False,
        "formal_report_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }

    _write_json(PRIVATE_AUTHORIZED_FILL_PATH, private_authorized_fill)
    _write_json(PRIVATE_SOURCE_MAP_PATH, private_source_map)
    _write_json(MATERIALIZATION_SOURCE_MAP_PATH, private_source_map)
    for path, payload in (
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_SUMMARY_PATH, summary),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Authorized Private Processed Source-Map Fill",
                "",
                f"- phase_scope: `{PHASE_ID} only`",
                f"- fill_request_item_count: `{summary['fill_request_item_count']}`",
                f"- unique_private_ref_count: `{summary['unique_private_ref_count']}`",
                f"- duplicate_private_ref_item_count: `{summary['duplicate_private_ref_item_count']}`",
                f"- authorized_filled_item_count: `{summary['authorized_filled_item_count']}`",
                f"- authorized_unfilled_item_count: `{summary['authorized_unfilled_item_count']}`",
                f"- source_map_records_written_count: `{summary['source_map_records_written_count']}`",
                f"- source_map_authorized_fill_complete: `{str(summary['source_map_authorized_fill_complete']).lower()}`",
                "- processed_value_materialization_replay_performed: `false`",
                "- raw_to_processed_value_comparison_performed: `false`",
                "- business_value_consistency_verified: `false`",
                "- go_no_go: `NO_GO`",
                "",
                "Public evidence is aggregate-only. The partially filled source map stays in ignored private runtime.",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                "- decision: `NO_GO`",
                "- reason: authorized fill is partial; remaining source-map gaps block materialization and value consistency.",
                "- processed_value_materialization_replay_performed: `false`",
                "- formal_report_allowed: `false`",
                "- github_upload_allowed: `false`",
                "- app_reinstall_allowed: `false`",
                "- business_execution_allowed: `false`",
                f"- next_recommended_phase: `{NEXT_RECOMMENDED_PHASE}`",
            ]
        )
        + "\n",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- R1: Partial source-map fill cannot prove processed business value consistency; mitigation is `NO_GO` until all slots are filled and replayed.",
                "- R2: Private source-map files could disclose internal refs if committed; mitigation is ignored runtime and validator Git-boundary checks.",
                "- R3: Staged source map could be mistaken for completed materialization; mitigation is explicit materialization=false gates.",
            ]
        )
        + "\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove current phase public evidence directory.",
                "- Remove current phase metadata quality copies.",
                "- Remove current phase tool, validator and focused test.",
                "- Remove ignored private runtime authorized-fill diagnostic and source map.",
                "- Revert governance entries for this phase.",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- status: `PENDING`",
                "- validator: `pending`",
                "- focused_unittest: `pending`",
                "- governance_validators: `pending`",
                "- public_safe_scan: `pending`",
                "- raw_inbox_mutation: `false`",
            ]
        )
        + "\n",
    )
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["authorized_fill_summary"]
    print(
        "Generated KMFA v0.1.4 authorized private processed source-map fill evidence "
        f"(filled={summary['authorized_filled_item_count']}, "
        f"unfilled={summary['authorized_unfilled_item_count']}, "
        "business_consistency=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
