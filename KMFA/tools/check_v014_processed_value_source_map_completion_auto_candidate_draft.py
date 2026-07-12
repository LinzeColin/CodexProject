from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_AUTO_CANDIDATE_DRAFT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-AUTO-CANDIDATE-DRAFT-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-auto-candidate-draft"
ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_auto_candidate_draft"
PRIVATE_RAW_INDEX_PATH = PRIVATE_DIR / "private_raw_source_index.json"
PRIVATE_CANDIDATE_DRAFT_PATH = PRIVATE_DIR / "auto_candidate_completion_template_draft.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "auto_match_diagnostic.json"
PRIVATE_QUESTION_LIST_PATH = PRIVATE_DIR / "unmatched_question_list_zh.md"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_auto_candidate_draft_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_auto_candidate_draft_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_auto_candidate_draft_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_auto_candidate_draft_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    HUMAN_DIR / "test_results.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_auto_candidate_draft_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_auto_candidate_draft_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_auto_candidate_draft_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal)"',
        re.IGNORECASE,
    ),
    re.compile(r'"(header_candidate_rows|row_text_values|context_text)"', re.IGNORECASE),
    re.compile(r"account_number|invoice_number|tax_identifier", re.IGNORECASE),
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
    forbidden_suffix = re.compile(r"\.(zip|xlsx|xlsm|xls|pdf|sqlite|db|key|pem|p12|pfx)$", re.IGNORECASE)
    hits = [path for path in tracked if forbidden_suffix.search(path) or ".codex_private_runtime" in path]
    if hits:
        raise ValidationError("forbidden tracked raw/private files: " + ", ".join(hits[:20]))


def _check_private_paths_ignored() -> None:
    for path in (PRIVATE_RAW_INDEX_PATH, PRIVATE_CANDIDATE_DRAFT_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_QUESTION_LIST_PATH):
        result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
        _require_equal(f"{path}.gitignored", result.returncode, 0)
        tracked = _git_output(["ls-files", path.as_posix()])
        _require_equal(f"{path}.tracked", tracked, "")


def _check_private_draft() -> None:
    raw_index = _read_json(PRIVATE_RAW_INDEX_PATH)
    draft = _read_json(PRIVATE_CANDIDATE_DRAFT_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    if not PRIVATE_QUESTION_LIST_PATH.exists():
        raise ValidationError(f"missing private question list: {PRIVATE_QUESTION_LIST_PATH}")
    _require_equal("raw_index.phase_id", raw_index.get("phase_id"), PHASE_ID)
    _require_equal("draft.phase_id", draft.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_true("draft.draft_only_not_active_owner_authorization", draft.get("draft_only_not_active_owner_authorization"))
    _require_false("draft.completion_template_overwritten", draft.get("completion_template_overwritten"))
    _require_false("draft.active_owner_authorized_fill_record_written", draft.get("active_owner_authorized_fill_record_written"))
    _require_equal("draft.candidate_draft_item_count", draft.get("candidate_draft_item_count"), 113)
    candidate_items = draft.get("candidate_completion_items")
    if not isinstance(candidate_items, list) or len(candidate_items) != 113:
        raise ValidationError("private candidate_completion_items must contain 113 items")
    _require_equal("diagnostic.unresolved_item_count", diagnostic.get("unresolved_item_count"), 113 - draft.get("candidate_status_counts", {}).get("auto_unique_candidate_requires_owner_confirmation", 0))
    raw_before = raw_index.get("raw_root_before")
    raw_after = raw_index.get("raw_root_after")
    _require_equal("private_raw_index.raw_root_stat_unchanged", raw_before, raw_after)
    if int(diagnostic.get("raw_numeric_candidate_count", 0)) <= 0:
        raise ValidationError("private diagnostic raw numeric candidate count must be > 0")


def validate(*, require_private_draft: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_auto_candidate_draft_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_auto_candidate_draft_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_auto_candidate_draft_go_no_go_report.json")

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), "private_candidate_draft_ready_owner_review_required")
    _require_equal("summary.completion_template_item_count", summary.get("completion_template_item_count"), 113)
    _require_equal("summary.candidate_draft_item_count", summary.get("candidate_draft_item_count"), 113)
    _require_equal("summary.owner_review_required_item_count", summary.get("owner_review_required_item_count"), 113)
    _require_true("summary.private_raw_index_written", summary.get("private_raw_index_written"))
    _require_true("summary.private_candidate_draft_written", summary.get("private_candidate_draft_written"))
    _require_true("summary.private_match_diagnostic_written", summary.get("private_match_diagnostic_written"))
    _require_true("summary.private_question_list_written", summary.get("private_question_list_written"))
    _require_true("summary.private_raw_index_gitignored", summary.get("private_raw_index_gitignored"))
    _require_true("summary.private_candidate_draft_gitignored", summary.get("private_candidate_draft_gitignored"))
    _require_true("summary.private_match_diagnostic_gitignored", summary.get("private_match_diagnostic_gitignored"))
    _require_true("summary.private_question_list_gitignored", summary.get("private_question_list_gitignored"))
    _require_false("summary.completion_template_overwritten", summary.get("completion_template_overwritten"))
    _require_false("summary.active_owner_authorized_fill_record_written", summary.get("active_owner_authorized_fill_record_written"))
    _require_false("summary.authorized_completion_record_supplied", summary.get("authorized_completion_record_supplied"))
    _require_false("summary.source_map_completion_reapplication_ready", summary.get("source_map_completion_reapplication_ready"))
    _require_false("summary.source_map_completion_reapplication_performed", summary.get("source_map_completion_reapplication_performed"))
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_false("summary.raw_to_processed_value_comparison_performed", summary.get("raw_to_processed_value_comparison_performed"))
    _require_false("summary.business_value_consistency_verified", summary.get("business_value_consistency_verified"))
    _require_false("summary.github_upload_performed", summary.get("github_upload_performed"))
    _require_false("summary.app_reinstall_performed", summary.get("app_reinstall_performed"))
    _require_false("summary.business_execution_performed", summary.get("business_execution_performed"))

    raw_summary = summary.get("raw_private_extraction_summary", {})
    _require_true("raw_summary.raw_root_exists", raw_summary.get("raw_root_exists"))
    if int(raw_summary.get("raw_root_file_count", 0)) <= 0:
        raise ValidationError("raw root file count must be > 0")
    if int(raw_summary.get("raw_numeric_candidate_count", 0)) <= 0:
        raise ValidationError("raw numeric candidate count must be > 0")
    _require_true(
        "raw_summary.raw_root_stat_unchanged_after_auto_candidate_draft",
        raw_summary.get("raw_root_stat_unchanged_after_auto_candidate_draft"),
    )
    boundary = summary.get("raw_boundary", {})
    for key in (
        "user_authorized_raw_data_read_for_this_phase",
        "raw_data_root_readonly_policy_active",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_root_stat_unchanged_after_auto_candidate_draft",
    ):
        _require_true(f"raw_boundary.{key}", boundary.get(key))
    for key in (
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
    safety = summary.get("public_safety", {})
    for key in (
        "public_safe_aggregate_only",
    ):
        _require_true(f"public_safety.{key}", safety.get(key))
    for key in (
        "private_raw_index_committed",
        "private_candidate_draft_committed",
        "private_match_diagnostic_committed",
        "private_question_list_committed",
        "raw_file_committed",
        "raw_filename_committed",
        "raw_archive_member_name_committed",
        "field_header_plaintext_committed",
        "row_value_committed",
        "business_value_committed",
        "credential_or_secret_committed",
    ):
        _require_false(f"public_safety.{key}", safety.get(key))

    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_false("go_no_go.source_map_completion_reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
    _require_false("go_no_go.raw_to_processed_value_comparison_performed", go_no_go.get("raw_to_processed_value_comparison_performed"))
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)

    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    _check_private_paths_ignored()
    if require_private_draft:
        _check_private_draft()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-draft", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_draft=args.require_private_draft)
    print(
        "PASS: KMFA v0.1.4 processed value source-map auto candidate draft validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"candidate_items={manifest['summary']['candidate_draft_item_count']}, "
        f"unresolved_questions={manifest['summary']['unresolved_question_item_count']})"
    )


if __name__ == "__main__":
    main()
