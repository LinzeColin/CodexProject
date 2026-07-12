#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner-authorized fill record draft evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_private_processed_value_source_map_owner_authorized_fill_record_draft import (  # noqa: E402
    ACTIVE_FILL_RECORD_CANDIDATE_PATHS,
    GO_NO_GO_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_PREVIEW_PATH,
    METADATA_SUMMARY_PATH,
    PHASE_ID,
    PREVIEW_PATH,
    PREVIEW_SCHEMA_VERSION,
    PRIVATE_DRAFT_PATH,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    SCHEMA_VERSION,
    STATUS,
    SUMMARY_PATH,
    SUMMARY_SCHEMA_VERSION,
    TASK_ID,
)


FORBIDDEN_PUBLIC_KEYS = {
    "private_processed_ref",
    "raw_value",
    "normalized_value",
    "processed_value",
    "business_value",
    "source_header_text",
    "cell_value",
    "row_value",
    "plaintext_content",
    "raw_file_bytes",
    "raw_filename",
    "zip_member_name",
    "sheet_name",
    "bank_account_number",
    "password",
    "token",
    "api_key",
    "private_key",
    "fill_items",
    "target_slot_id",
}
FORBIDDEN_PUBLIC_TEXT = (
    "KMFA_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
    "private://",
    "private_ref://",
    "raw path",
    "raw filename",
    "sheet name",
    "cell value",
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)
FORBIDDEN_TRACKED_SUFFIXES = (
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".sqlite-shm",
    ".sqlite-wal",
    ".db",
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_check_ignore(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_forbidden_public_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_public_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_public_keys(child, errors, f"{path}[{index}]")


def check_public_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    for pattern in SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _validate_summary(summary: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "private_intake_request_item_count": 113,
        "source_unresolved_gap_item_count": 113,
        "source_unresolved_unique_private_ref_count": 101,
        "draft_fill_item_count": 113,
        "draft_unique_target_slot_count": 113,
        "draft_keep_pending_item_count": 113,
        "draft_supply_authorized_fingerprint_item_count": 0,
        "draft_map_existing_metadata_hash_sibling_item_count": 0,
        "draft_private_runtime_written": True,
        "draft_is_active_record": False,
        "owner_authorized_fill_record_supplied": False,
        "active_authorized_fill_record_created": False,
        "fill_application_performed": False,
        "source_map_records_applied_count": 0,
        "new_authorized_fingerprint_count": 0,
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "candidate_active_fill_record_path_count": 2,
        "existing_active_fill_record_path_count": 0,
        "active_authorized_fill_record_found": False,
    }
    require(summary.get("schema_version") == SUMMARY_SCHEMA_VERSION, "summary schema mismatch", errors)
    require(summary.get("phase_id") == PHASE_ID, "summary phase mismatch", errors)
    require(summary.get("task_id") == TASK_ID, "summary task mismatch", errors)
    require(
        summary.get("next_required_input") == "owner_or_authorized_delegate_activation_of_draft_fill_record",
        "summary next required input mismatch",
        errors,
    )
    for key, expected_value in expected.items():
        require(summary.get(key) == expected_value, f"summary {key} mismatch: {summary.get(key)!r}", errors)


def _validate_go_no_go(go_no_go: dict[str, Any], errors: list[str]) -> None:
    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go_no_go schema mismatch", errors)
    require(go_no_go.get("phase_id") == PHASE_ID, "go_no_go phase mismatch", errors)
    require(go_no_go.get("task_id") == TASK_ID, "go_no_go task mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go_no_go decision mismatch", errors)
    for key in (
        "draft_is_active_record",
        "owner_authorized_fill_record_supplied",
        "active_authorized_fill_record_created",
        "fill_application_performed",
        "source_map_gap_resolution_complete",
        "processed_value_materialization_replay_allowed",
        "raw_to_processed_value_comparison_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)
    require(go_no_go.get("draft_prepared") is True, "go_no_go draft_prepared must be true", errors)
    require(go_no_go.get("source_map_records_applied_count") == 0, "go_no_go applied count mismatch", errors)
    require(go_no_go.get("new_authorized_fingerprint_count") == 0, "go_no_go fingerprint count mismatch", errors)


def _validate_private_draft(*, require_private_draft: bool, errors: list[str]) -> None:
    require(".codex_private_runtime/" in PRIVATE_DRAFT_PATH.as_posix(), "private draft path mismatch", errors)
    require(git_check_ignore(PRIVATE_DRAFT_PATH), "private draft must be git-ignored", errors)
    require(not git_output(["ls-files", str(PRIVATE_DRAFT_PATH)]), "private draft must not be tracked", errors)
    for path in ACTIVE_FILL_RECORD_CANDIDATE_PATHS:
        require(git_check_ignore(path), f"active record candidate must be git-ignored: {path}", errors)
    # A later authorized-application phase may create an active record. The
    # draft evidence proves its own non-activation through the frozen summary
    # and draft payload; current filesystem absence is not a historical fact.
    if not require_private_draft:
        return
    require(PRIVATE_DRAFT_PATH.exists(), f"private draft must exist: {PRIVATE_DRAFT_PATH}", errors)
    if not PRIVATE_DRAFT_PATH.exists():
        return
    draft = read_json(PRIVATE_DRAFT_PATH)
    require(draft.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private draft schema mismatch", errors)
    require(
        draft.get("classification") == "private_owner_authorized_fill_record_draft_do_not_commit",
        "private draft classification mismatch",
        errors,
    )
    require(draft.get("draft_is_active_record") is False, "private draft must not be active", errors)
    template = draft.get("proposed_active_record_template", {})
    require(isinstance(template, dict), "private draft template must be object", errors)
    fill_items = template.get("fill_items", [])
    require(isinstance(fill_items, list), "private draft fill_items must be list", errors)
    require(len(fill_items) == 113, "private draft fill item count mismatch", errors)
    require(len({item.get("target_slot_id") for item in fill_items if isinstance(item, dict)}) == 113, "private draft target ids must be unique", errors)
    require(all(isinstance(item, dict) and item.get("action_code") == "keep_pending" for item in fill_items), "private draft action codes must all be keep_pending", errors)
    draft_text = json.dumps(draft, ensure_ascii=False, sort_keys=True)
    for forbidden in ("private_processed_ref", '"raw_value"', '"normalized_value"', '"business_value"', "KMFA_MetaData"):
        require(forbidden not in draft_text, f"private draft should not copy forbidden source detail: {forbidden}", errors)


def _check_tracked_sensitive_suffixes(errors: list[str]) -> None:
    tracked = git_output(["ls-files", "KMFA"])
    for filename in tracked.splitlines():
        lower = filename.lower()
        if lower.endswith(FORBIDDEN_TRACKED_SUFFIXES):
            errors.append(f"forbidden tracked raw/private suffix in KMFA: {filename}")


def validate_v014_owner_authorized_fill_record_draft(*, require_private_draft: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(MANIFEST_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    summary = read_json(SUMMARY_PATH)
    preview = read_json(PREVIEW_PATH)

    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        SUMMARY_PATH,
        PREVIEW_PATH,
        REPORT_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_PREVIEW_PATH,
    ):
        check_public_text(path, errors)
    for payload in (manifest, go_no_go, summary, preview):
        walk_forbidden_public_keys(payload, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "manifest phase mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "manifest task mismatch", errors)
    require(manifest.get("status") == STATUS, "manifest status mismatch", errors)
    require(preview.get("schema_version") == PREVIEW_SCHEMA_VERSION, "preview schema mismatch", errors)
    require(preview.get("draft_is_active_record") is False, "preview draft active flag mismatch", errors)
    require(preview.get("draft_fill_item_count") == 113, "preview draft count mismatch", errors)

    _validate_summary(summary, errors)
    _validate_go_no_go(go_no_go, errors)
    _validate_private_draft(require_private_draft=require_private_draft, errors=errors)
    _check_tracked_sensitive_suffixes(errors)

    raw_boundary = manifest.get("raw_readonly_boundary", {})
    require(raw_boundary.get("raw_inbox_read_performed_by_this_phase") is False, "raw inbox read flag mismatch", errors)
    require(raw_boundary.get("raw_inbox_mutation_performed_by_this_phase") is False, "raw inbox mutation flag mismatch", errors)
    require(raw_boundary.get("final_discrepancy_report_required_if_repeated_cross_validation_diverges") is True, "difference report duty missing", errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-draft", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_owner_authorized_fill_record_draft(require_private_draft=args.require_private_draft)
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    summary = manifest["owner_authorized_fill_record_draft_summary"]
    print(
        json.dumps(
            {
                "ok": True,
                "phase_id": manifest["phase_id"],
                "status": manifest["status"],
                "draft_fill_item_count": summary["draft_fill_item_count"],
                "active_authorized_fill_record_created": summary["active_authorized_fill_record_created"],
                "go_no_go": manifest["go_no_go"]["decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
