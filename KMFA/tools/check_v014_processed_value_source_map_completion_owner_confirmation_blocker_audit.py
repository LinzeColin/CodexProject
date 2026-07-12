from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-CONFIRMATION-BLOCKER-AUDIT-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-owner-confirmation-blocker-audit"
BLOCKER = "owner_or_authorized_delegate_confirmation_code_not_supplied"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_decision_option_or_fills_response_template"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_blocker_audit/private_owner_confirmation_blocker_diagnostic.json"
)

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_blocker_audit_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"',
        re.IGNORECASE,
    ),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _require_equal(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{name}: expected {expected!r}, got {actual!r}")


def _require_true(name: str, value: Any) -> None:
    if value is not True:
        raise ValidationError(f"{name}: expected True, got {value!r}")


def _require_false(name: str, value: Any) -> None:
    if value is not False:
        raise ValidationError(f"{name}: expected False, got {value!r}")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=PROJECT_ROOT.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _check_public_artifacts() -> None:
    for path in PUBLIC_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                raise ValidationError(f"forbidden public marker {pattern.pattern!r} in {path}")


def _check_no_raw_private_files_tracked() -> None:
    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_suffix = re.compile(r"\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$", re.IGNORECASE)
    hits = [path for path in tracked if forbidden_suffix.search(path) or ".codex_private_runtime" in path]
    if hits:
        raise ValidationError("forbidden tracked raw/private files: " + ", ".join(hits[:20]))


def _check_raw_boundary(boundary: dict[str, Any]) -> None:
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", boundary.get("raw_data_root_readonly_policy_active"))
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_overwrite_performed_by_this_phase",
        "raw_inbox_copy_performed_by_this_phase",
        "raw_inbox_normalize_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", boundary.get(key))


def _check_public_safety(safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", safety.get("public_safe_aggregate_only"))
    for key in (
        "private_confirmation_record_committed",
        "private_diagnostic_committed",
        "raw_file_committed",
        "raw_filename_committed",
        "raw_archive_member_name_committed",
        "field_header_plaintext_committed",
        "row_value_committed",
        "business_value_committed",
        "credential_or_secret_committed",
    ):
        _require_false(f"public_safety.{key}", safety.get(key))


def _check_private_diagnostic(summary: dict[str, Any]) -> None:
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("private_diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private_diagnostic.task_id", diagnostic.get("task_id"), TASK_ID)
    _require_false("private_diagnostic.confirmation_record_found", diagnostic.get("confirmation_record_found"))
    _require_equal("private_diagnostic.source_response_row_count", diagnostic.get("source_response_row_count"), 113)
    _require_equal("private_diagnostic.source_pending_owner_decision_count", diagnostic.get("source_pending_owner_decision_count"), 113)
    _require_equal("private_diagnostic.decision_option_count", diagnostic.get("decision_option_count"), 3)
    _require_equal(
        "private_diagnostic.confirmation_count_matches_summary",
        diagnostic.get("confirmation_record_found"),
        summary.get("confirmation_record_found"),
    )
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    result = subprocess.run(
        ["git", "check-ignore", "-q", PRIVATE_DIAGNOSTIC_PATH.as_posix()],
        cwd=PROJECT_ROOT.parent,
        check=False,
    )
    _require_equal("private_diagnostic.gitignored", result.returncode, 0)
    _require_equal("private_diagnostic.tracked", _git_output(["ls-files", PRIVATE_DIAGNOSTIC_PATH.as_posix()]), "")


def validate(*, require_private_diagnostic: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_summary.json"
    )
    metadata_manifest = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_manifest.json"
    )
    metadata_go_no_go = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_confirmation_blocker_audit_go_no_go_report.json"
    )

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.blocker_condition", summary.get("blocker_condition"), BLOCKER)
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), BLOCKER)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_response_row_count", summary.get("source_response_row_count"), 113)
    _require_equal("summary.source_pending_owner_decision_count", summary.get("source_pending_owner_decision_count"), 113)
    _require_equal("summary.decision_option_count", summary.get("decision_option_count"), 3)
    _require_false("summary.confirmation_record_found", summary.get("confirmation_record_found"))
    _require_true("summary.private_diagnostic_written", summary.get("private_diagnostic_written"))
    _require_true("summary.private_diagnostic_gitignored", summary.get("private_diagnostic_gitignored"))
    _require_false("summary.owner_confirmation_supplied", summary.get("owner_confirmation_supplied"))

    for key in (
        "active_owner_authorized_fill_record_ready",
        "active_owner_authorized_fill_record_written",
        "completion_template_overwritten",
        "authorized_completion_record_supplied",
        "source_map_completion_reapplication_ready",
        "source_map_completion_reapplication_performed",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.diagnostic_conclusion", go_no_go.get("diagnostic_conclusion"), BLOCKER)
    _require_false("go_no_go.confirmation_record_found", go_no_go.get("confirmation_record_found"))
    _require_false("go_no_go.owner_confirmation_supplied", go_no_go.get("owner_confirmation_supplied"))
    _require_equal("go_no_go.source_pending_owner_decision_count", go_no_go.get("source_pending_owner_decision_count"), 113)
    _require_false("go_no_go.active_owner_authorized_fill_record_ready", go_no_go.get("active_owner_authorized_fill_record_ready"))
    _require_false("go_no_go.source_map_completion_reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
    _require_false("go_no_go.raw_to_processed_value_comparison_performed", go_no_go.get("raw_to_processed_value_comparison_performed"))
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app_reinstall_performed", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business_execution_performed", go_no_go.get("business_execution_performed"))
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)

    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_diagnostic:
        _check_private_diagnostic(summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_diagnostic=args.require_private_diagnostic)
    print(
        "PASS: KMFA v0.1.4 owner confirmation blocker audit validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"confirmation_found={manifest['summary']['confirmation_record_found']}, "
        f"pending={manifest['summary']['source_pending_owner_decision_count']})"
    )


if __name__ == "__main__":
    main()
