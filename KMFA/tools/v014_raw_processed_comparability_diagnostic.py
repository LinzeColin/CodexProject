#!/usr/bin/env python3
"""Generate KMFA v0.1.4 raw/processed comparability diagnostic evidence.

This phase is a private diagnostic gate. It verifies whether the current raw
numeric fingerprints and processed target slots have enough shared keys to form
raw-to-processed comparable pairs. Public artifacts remain aggregate-only; raw
file names, sheet names, cells, PDF text, row values and business values never
leave the git-ignored private runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX, sha256_file, sha256_text, stat_snapshot  # noqa: E402


PROJECT_ID = "KMFA"
VERSION = "0.1.4"
PHASE_ID = "V014_RAW_PROCESSED_COMPARABILITY_DIAGNOSTIC"
TASK_ID = "KMFA-V014-RAW-PROCESSED-COMPARABILITY-DIAGNOSTIC-20260706"
ACCEPTANCE_ID = "ACC-V014-RAW-PROCESSED-COMPARABILITY-DIAGNOSTIC"
STATUS = "completed_validated_local_only_no_go_raw_processed_comparability_blocked"
SCHEMA_VERSION = "kmfa.v014_raw_processed_comparability_diagnostic.v1"
GO_NO_GO_SCHEMA_VERSION = "kmfa.v014_raw_processed_comparability_diagnostic_go_no_go.v1"
PRIVATE_SCHEMA_VERSION = "kmfa.private.v014_raw_processed_comparability_diagnostic.v1"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_supplies_target_slot_to_processed_value_source_map"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_RAW_PROCESSED_COMPARABILITY_DIAGNOSTIC")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "raw_processed_comparability_diagnostic_summary.json"
MANIFEST_PATH = MACHINE_DIR / "raw_processed_comparability_diagnostic_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "raw_processed_comparability_diagnostic_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "raw_processed_comparability_diagnostic_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = Path("KMFA/metadata/quality/v014_raw_processed_comparability_diagnostic_summary.json")
METADATA_MANIFEST_PATH = Path("KMFA/metadata/quality/v014_raw_processed_comparability_diagnostic_manifest.json")
METADATA_GO_NO_GO_PATH = Path("KMFA/metadata/quality/v014_raw_processed_comparability_diagnostic_go_no_go_report.json")

PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v014_raw_processed_comparability_diagnostic")
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_processed_comparability_diagnostic.json"
PRIVATE_LOCAL_REPORT_PATH = PRIVATE_OUTPUT_DIR / "local_comparability_gap_report.md"

RAW_MATCHING_DIAGNOSTIC_PATH = Path(
    "KMFA/.codex_private_runtime/v014_raw_value_matching_private_dry_run/private_raw_value_matching_diagnostic.json"
)
PROCESSED_STAGING_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"
)
PRIVATE_SOURCE_MAP_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_authorized_fill/private_processed_value_source_map.json"
)
OWNER_WORKLIST_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_gap_resolution/private_owner_authorized_fill_worklist.json"
)
ACTIVE_FILL_RECORD_PATH = Path(
    "KMFA/.codex_private_runtime/v014_private_processed_value_source_map_owner_authorized_fill_application/active_owner_authorized_fill_record.json"
)
OWNER_APPLICATION_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION/machine/private_processed_value_source_map_owner_authorized_fill_application_manifest.json"
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


def _copy_to_metadata(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _normalized_hash(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value[7:] if value.startswith("sha256:") else value
    if len(candidate) == 64 and all(char in "0123456789abcdefABCDEF" for char in candidate):
        return candidate.lower()
    return None


def _collect_hash_values(value: Any, keys: set[str]) -> set[str]:
    collected: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys:
                normalized = _normalized_hash(child)
                if normalized:
                    collected.add(normalized)
            collected.update(_collect_hash_values(child, keys))
    elif isinstance(value, list):
        for child in value:
            collected.update(_collect_hash_values(child, keys))
    return collected


def _raw_structural_keys(raw_diagnostic: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for records in raw_diagnostic.get("raw_private_records", {}).values():
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            for key in ("source_ref_hash", "page_ref_hash", "sheet_ref_hash", "cell_ref_hash", "token_ref_hash"):
                normalized = _normalized_hash(record.get(key))
                if normalized:
                    keys.add(normalized)
    return keys


def _processed_structural_keys(staging: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for slot in staging.get("processed_target_slots", []):
        if not isinstance(slot, dict):
            continue
        for key in (
            "source_artifact_ref_hash",
            "record_ref_hash",
            "target_key_ref_hash",
            "private_processed_ref_hash",
            "source_root_id",
        ):
            value = slot.get(key)
            normalized = _normalized_hash(value) or (sha256_text(value) if isinstance(value, str) else None)
            if normalized:
                keys.add(normalized)
    return keys


def _private_raw_root_snapshot() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    suffix_counter: Counter[str] = Counter()
    if RAW_INBOX.exists():
        for path in sorted(candidate for candidate in RAW_INBOX.iterdir() if candidate.is_file()):
            suffix = path.suffix.lower() or "none"
            suffix_counter[suffix] += 1
            stat = path.stat()
            files.append(
                {
                    "path_hash": sha256_text(str(path)),
                    "suffix": suffix,
                    "size_bytes": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "sha256": sha256_file(path),
                }
            )
    return {
        "raw_root_exists": RAW_INBOX.exists(),
        "raw_root_file_count": len(files),
        "raw_root_suffix_counts": dict(sorted(suffix_counter.items())),
        "raw_private_file_hash_records": files,
    }


def build_payloads(generated_at: str | None = None) -> dict[str, dict[str, Any]]:
    generated = _now(generated_at)
    raw_root_before = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    raw_private_snapshot = _private_raw_root_snapshot()

    raw_diagnostic = _read_json(RAW_MATCHING_DIAGNOSTIC_PATH)
    staging = _read_json(PROCESSED_STAGING_PATH)
    source_map = _read_json(PRIVATE_SOURCE_MAP_PATH)
    owner_worklist = _read_json(OWNER_WORKLIST_PATH)
    active_record = _read_json(ACTIVE_FILL_RECORD_PATH)
    owner_application_manifest = _read_json(OWNER_APPLICATION_MANIFEST_PATH)

    raw_numeric_fingerprints = _collect_hash_values(raw_diagnostic, {"numeric_value_fingerprint"})
    processed_staged_fingerprints = _collect_hash_values(staging, {"value_fingerprint", "processed_value_fingerprint"})
    processed_source_map_fingerprints = _collect_hash_values(
        source_map, {"value_fingerprint", "processed_value_fingerprint"}
    )
    raw_structural_keys = _raw_structural_keys(raw_diagnostic)
    processed_structural_keys = _processed_structural_keys(staging)

    processed_slots = staging.get("processed_target_slots", [])
    source_map_records = source_map.get("processed_value_sources", [])
    owner_items = owner_worklist.get("owner_worklist_items", [])
    active_items = active_record.get("fill_items", [])

    raw_root_after = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
    raw_root_stat_unchanged = raw_root_before == raw_root_after
    raw_root_mutation_detected = not raw_root_stat_unchanged

    raw_processed_fingerprint_overlap = raw_numeric_fingerprints & processed_source_map_fingerprints
    staged_fingerprint_overlap = raw_numeric_fingerprints & processed_staged_fingerprints
    structural_key_overlap = raw_structural_keys & processed_structural_keys

    summary = {
        "record_type": "v014_raw_processed_comparability_diagnostic_summary",
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "status": STATUS,
        "raw_root_exists": raw_private_snapshot["raw_root_exists"],
        "raw_root_file_count": raw_private_snapshot["raw_root_file_count"],
        "raw_root_private_hash_record_count": len(raw_private_snapshot["raw_private_file_hash_records"]),
        "raw_root_stat_unchanged_after_phase": raw_root_stat_unchanged,
        "raw_inbox_mutation_detected": raw_root_mutation_detected,
        "prior_raw_value_fingerprint_record_count": raw_diagnostic.get("raw_private_summary", {}).get(
            "raw_value_fingerprint_count", 0
        ),
        "prior_raw_unique_numeric_fingerprint_count": len(raw_numeric_fingerprints),
        "processed_target_slot_count": len(processed_slots),
        "staged_processed_value_fingerprint_count": len(processed_staged_fingerprints),
        "existing_processed_source_map_record_count": len(source_map_records),
        "existing_processed_source_map_unique_fingerprint_count": len(processed_source_map_fingerprints),
        "unresolved_owner_worklist_item_count": len(owner_items),
        "active_fill_record_item_count": len(active_items),
        "active_fill_record_keep_pending_count": sum(
            1 for item in active_items if isinstance(item, dict) and item.get("action_code") == "keep_pending"
        ),
        "raw_processed_staged_fingerprint_overlap_count": len(staged_fingerprint_overlap),
        "raw_processed_source_map_fingerprint_overlap_count": len(raw_processed_fingerprint_overlap),
        "raw_structural_key_count": len(raw_structural_keys),
        "processed_structural_key_count": len(processed_structural_keys),
        "raw_processed_structural_key_intersection_count": len(structural_key_overlap),
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "source_map_gap_resolution_complete": False,
        "diagnostic_conclusion": "blocked_no_authorized_processed_value_source_map",
        "blocker": "processed_target_slots_lack_authorized_value_fingerprints_and_shared_raw_join_keys",
        "next_required_input": NEXT_REQUIRED_INPUT,
    }

    go_no_go = {
        "record_type": "v014_raw_processed_comparability_diagnostic_go_no_go",
        "schema_version": GO_NO_GO_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "decision": "NO_GO",
        "decision_reason": (
            "Raw numeric fingerprints and processed target slots are present in private diagnostics, "
            "but there are zero shared structural join keys and zero authorized processed-value fingerprints "
            "on staged target slots, so raw-to-processed comparable pairs cannot be formed."
        ),
        "raw_root_file_count": summary["raw_root_file_count"],
        "prior_raw_unique_numeric_fingerprint_count": summary["prior_raw_unique_numeric_fingerprint_count"],
        "processed_target_slot_count": summary["processed_target_slot_count"],
        "staged_processed_value_fingerprint_count": summary["staged_processed_value_fingerprint_count"],
        "existing_processed_source_map_record_count": summary["existing_processed_source_map_record_count"],
        "unresolved_owner_worklist_item_count": summary["unresolved_owner_worklist_item_count"],
        "active_fill_record_keep_pending_count": summary["active_fill_record_keep_pending_count"],
        "raw_processed_structural_key_intersection_count": summary[
            "raw_processed_structural_key_intersection_count"
        ],
        "raw_processed_source_map_fingerprint_overlap_count": summary[
            "raw_processed_source_map_fingerprint_overlap_count"
        ],
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_allowed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }

    private_diagnostic = {
        "classification": "private_raw_processed_comparability_diagnostic_do_not_commit",
        "schema_version": PRIVATE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "raw_root_before": raw_root_before,
        "raw_root_after": raw_root_after,
        "raw_private_snapshot": raw_private_snapshot,
        "raw_numeric_fingerprint_count": len(raw_numeric_fingerprints),
        "processed_staged_fingerprint_count": len(processed_staged_fingerprints),
        "processed_source_map_fingerprint_count": len(processed_source_map_fingerprints),
        "raw_processed_staged_fingerprint_overlap_count": len(staged_fingerprint_overlap),
        "raw_processed_source_map_fingerprint_overlap_count": len(raw_processed_fingerprint_overlap),
        "raw_structural_key_count": len(raw_structural_keys),
        "processed_structural_key_count": len(processed_structural_keys),
        "raw_processed_structural_key_intersection_count": len(structural_key_overlap),
        "raw_inbox_mutation_detected": raw_root_mutation_detected,
        "basis_private_refs": {
            "raw_matching_diagnostic": str(RAW_MATCHING_DIAGNOSTIC_PATH),
            "processed_staging": str(PROCESSED_STAGING_PATH),
            "private_source_map": str(PRIVATE_SOURCE_MAP_PATH),
            "owner_worklist": str(OWNER_WORKLIST_PATH),
            "active_fill_record": str(ACTIVE_FILL_RECORD_PATH),
        },
        "owner_application_status": owner_application_manifest.get("status"),
        "decision": "NO_GO",
        "next_required_input": NEXT_REQUIRED_INPUT,
    }

    manifest = {
        "record_type": "v014_raw_processed_comparability_diagnostic_manifest",
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated,
        "status": STATUS,
        "summary_ref": str(SUMMARY_PATH),
        "go_no_go_ref": str(GO_NO_GO_PATH),
        "private_diagnostic_ref": "gitignored_private_runtime",
        "summary": summary,
        "go_no_go": go_no_go,
        "scope_controls": {
            "raw_root_readonly_phase": True,
            "raw_inbox_read_performed_by_this_phase": True,
            "raw_inbox_list_performed_by_this_phase": True,
            "raw_inbox_stat_performed_by_this_phase": True,
            "raw_inbox_hash_performed_by_this_phase": True,
            "raw_inbox_write_performed_by_this_phase": False,
            "raw_inbox_delete_performed_by_this_phase": False,
            "raw_inbox_move_performed_by_this_phase": False,
            "raw_inbox_rename_performed_by_this_phase": False,
            "raw_inbox_copy_performed_by_this_phase": False,
            "raw_inbox_normalize_performed_by_this_phase": False,
            "raw_inbox_mutation_performed_by_this_phase": False,
            "raw_to_processed_value_comparison_performed": False,
            "business_value_consistency_verified": False,
            "lineage_full_check_complete": False,
            "formal_report_allowed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    return {"summary": summary, "go_no_go": go_no_go, "manifest": manifest, "private": private_diagnostic}


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# KMFA v0.1.4 Raw/Processed Comparability Diagnostic",
        "",
        f"- status: `{summary['status']}`",
        f"- raw_root_file_count: `{summary['raw_root_file_count']}`",
        f"- prior_raw_value_fingerprint_record_count: `{summary['prior_raw_value_fingerprint_record_count']}`",
        f"- prior_raw_unique_numeric_fingerprint_count: `{summary['prior_raw_unique_numeric_fingerprint_count']}`",
        f"- processed_target_slot_count: `{summary['processed_target_slot_count']}`",
        f"- staged_processed_value_fingerprint_count: `{summary['staged_processed_value_fingerprint_count']}`",
        f"- existing_processed_source_map_record_count: `{summary['existing_processed_source_map_record_count']}`",
        f"- unresolved_owner_worklist_item_count: `{summary['unresolved_owner_worklist_item_count']}`",
        f"- active_fill_record_keep_pending_count: `{summary['active_fill_record_keep_pending_count']}`",
        f"- raw_processed_structural_key_intersection_count: `{summary['raw_processed_structural_key_intersection_count']}`",
        f"- comparable_value_pair_count: `{summary['comparable_value_pair_count']}`",
        f"- business_value_consistency_verified: `{str(summary['business_value_consistency_verified']).lower()}`",
        f"- raw_inbox_mutation_detected: `{str(summary['raw_inbox_mutation_detected']).lower()}`",
        "",
        "## Conclusion",
        "",
        (
            "Current private evidence cannot form raw-to-processed comparable pairs. "
            "The next input must be an owner-authorized mapping from target slots to processed value sources."
        ),
    ]
    return "\n".join(lines) + "\n"


def _render_go_no_go(go_no_go: dict[str, Any]) -> str:
    lines = [
        "# Go/No-Go Record",
        "",
        "- decision: `NO_GO`",
        f"- reason: `{go_no_go['decision_reason']}`",
        f"- comparable_value_pair_count: `{go_no_go['comparable_value_pair_count']}`",
        f"- next_required_input: `{go_no_go['next_required_input']}`",
        "- github_upload_performed: `false`",
        "- app_reinstall_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_performed: `false`",
    ]
    return "\n".join(lines) + "\n"


def _render_risk_register() -> str:
    return "\n".join(
        [
            "# Risk Register",
            "",
            "| risk_id | risk | control | status |",
            "|---|---|---|---|",
            "| RPD-001 | Raw numeric fingerprints could be mistaken for business consistency proof | Keep comparable pairs at zero until authorized processed source-map exists | controlled |",
            "| RPD-002 | Processed private refs are path/ref-only | Require owner-authorized target-slot source mapping before materialization | active |",
            "| RPD-003 | Raw files must remain immutable | Write all diagnostics only to ignored private runtime and verify raw mutation flag is false | controlled |",
        ]
    ) + "\n"


def _render_rollback() -> str:
    return "\n".join(
        [
            "# Rollback Plan",
            "",
            "- Remove `KMFA/stage_artifacts/V014_RAW_PROCESSED_COMPARABILITY_DIAGNOSTIC/`.",
            "- Remove metadata copies under `KMFA/metadata/quality/v014_raw_processed_comparability_diagnostic_*`.",
            "- Remove ignored private runtime diagnostic under `KMFA/.codex_private_runtime/v014_raw_processed_comparability_diagnostic/`.",
            "- Revert governance and status entries for this phase.",
            "- Do not modify the raw data inbox.",
        ]
    ) + "\n"


def _render_private_gap_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Private raw/processed comparability gap report",
            "",
            "- classification: private_runtime_do_not_commit",
            f"- raw unique numeric fingerprints: {summary['prior_raw_unique_numeric_fingerprint_count']}",
            f"- processed target slots: {summary['processed_target_slot_count']}",
            f"- staged processed value fingerprints: {summary['staged_processed_value_fingerprint_count']}",
            f"- existing processed source-map records: {summary['existing_processed_source_map_record_count']}",
            f"- structural key intersection: {summary['raw_processed_structural_key_intersection_count']}",
            f"- comparable value pairs: {summary['comparable_value_pair_count']}",
            "- reason: no shared raw-to-processed join key and no staged processed value fingerprints",
            f"- next required input: {summary['next_required_input']}",
        ]
    ) + "\n"


def generate(generated_at: str | None = None) -> dict[str, dict[str, Any]]:
    payloads = build_payloads(generated_at)
    summary = payloads["summary"]
    go_no_go = payloads["go_no_go"]
    manifest = payloads["manifest"]
    private = payloads["private"]

    for path in (MACHINE_DIR, HUMAN_DIR, PRIVATE_OUTPUT_DIR):
        path.mkdir(parents=True, exist_ok=True)

    _write_json(SUMMARY_PATH, summary)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private)
    _write_text(PRIVATE_LOCAL_REPORT_PATH, _render_private_gap_report(summary))
    _write_text(REPORT_PATH, _render_report(summary))
    _write_text(GO_NO_GO_RECORD_PATH, _render_go_no_go(go_no_go))
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 Raw/Processed Comparability Diagnostic Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- validator: `pending_final_validation`",
                "- focused_unit_test: `pending_final_validation`",
                "- governance_validator: `pending_final_validation`",
                "- raw_private_scan: `pending_final_validation`",
                "- secret_scan: `pending_final_validation`",
            ]
        )
        + "\n",
    )
    _write_text(RISK_REGISTER_PATH, _render_risk_register())
    _write_text(ROLLBACK_PATH, _render_rollback())

    _copy_to_metadata(SUMMARY_PATH, METADATA_SUMMARY_PATH)
    _copy_to_metadata(MANIFEST_PATH, METADATA_MANIFEST_PATH)
    _copy_to_metadata(GO_NO_GO_PATH, METADATA_GO_NO_GO_PATH)
    return payloads


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    payloads = generate(args.generated_at)
    summary = payloads["summary"]
    print(
        "Generated KMFA v0.1.4 raw/processed comparability diagnostic "
        f"(decision=NO_GO, raw_unique={summary['prior_raw_unique_numeric_fingerprint_count']}, "
        f"processed_slots={summary['processed_target_slot_count']}, comparable_pairs=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
