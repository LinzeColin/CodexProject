from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_REVIEW_INTAKE_PREP"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-REVIEW-INTAKE-PREP-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-owner-review-intake-prep"
ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep"
PRIVATE_GROUPED_REVIEW_PATH = PRIVATE_DIR / "private_grouped_owner_review_intake.json"
PRIVATE_RESPONSE_TEMPLATE_PATH = PRIVATE_DIR / "private_owner_review_response_template.json"
PRIVATE_CANDIDATE_CATALOG_PATH = PRIVATE_DIR / "private_candidate_catalog.json"
PRIVATE_COMPRESSED_QUESTION_LIST_PATH = PRIVATE_DIR / "private_grouped_question_list_zh.md"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_intake_prep_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_intake_prep_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_review_intake_prep_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_review_intake_prep_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    HUMAN_DIR / "test_results.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_intake_prep_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_intake_prep_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_intake_prep_go_no_go_report.json",
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
    forbidden_suffix = re.compile(r"\.(zip|xlsx|xlsm|xls|pdf|sqlite|db|key|pem|p12|pfx)$", re.IGNORECASE)
    hits = [path for path in tracked if forbidden_suffix.search(path) or ".codex_private_runtime" in path]
    if hits:
        raise ValidationError("forbidden tracked raw/private files: " + ", ".join(hits[:20]))


def _check_private_paths_ignored() -> None:
    for path in (
        PRIVATE_GROUPED_REVIEW_PATH,
        PRIVATE_RESPONSE_TEMPLATE_PATH,
        PRIVATE_CANDIDATE_CATALOG_PATH,
        PRIVATE_COMPRESSED_QUESTION_LIST_PATH,
    ):
        result = subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False)
        _require_equal(f"{path}.gitignored", result.returncode, 0)
        tracked = _git_output(["ls-files", path.as_posix()])
        _require_equal(f"{path}.tracked", tracked, "")


def _check_private_intake() -> None:
    grouped = _read_json(PRIVATE_GROUPED_REVIEW_PATH)
    response = _read_json(PRIVATE_RESPONSE_TEMPLATE_PATH)
    catalog = _read_json(PRIVATE_CANDIDATE_CATALOG_PATH)
    if not PRIVATE_COMPRESSED_QUESTION_LIST_PATH.exists():
        raise ValidationError(f"missing private grouped question list: {PRIVATE_COMPRESSED_QUESTION_LIST_PATH}")
    _require_equal("grouped.phase_id", grouped.get("phase_id"), PHASE_ID)
    _require_equal("response.phase_id", response.get("phase_id"), PHASE_ID)
    _require_equal("catalog.phase_id", catalog.get("phase_id"), PHASE_ID)
    _require_equal("grouped.review_group_count", grouped.get("review_group_count"), 22)
    _require_equal("grouped.response_template_row_count", grouped.get("response_template_row_count"), 113)
    _require_equal("response.response_row_count", response.get("response_row_count"), 113)
    _require_false("response.active_record", response.get("response_template_is_active_authorization_record"))
    _require_false("response.completion_template_overwritten", response.get("completion_template_overwritten"))
    _require_false("response.active_owner_authorized_fill_record_written", response.get("active_owner_authorized_fill_record_written"))
    if int(catalog.get("candidate_catalog_record_count", 0)) <= 0:
        raise ValidationError("private candidate catalog must contain review records")


def validate(*, require_private_intake: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_intake_prep_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_intake_prep_manifest.json")
    metadata_go_no_go = _read_json(
        QUALITY_DIR / "v014_processed_value_source_map_completion_owner_review_intake_prep_go_no_go_report.json"
    )

    _require_equal("metadata summary copy", metadata_summary, summary)
    _require_equal("metadata manifest copy", metadata_manifest, manifest)
    _require_equal("metadata go/no-go copy", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), "private_owner_review_intake_ready_owner_response_required")
    _require_equal("summary.source_candidate_draft_item_count", summary.get("source_candidate_draft_item_count"), 113)
    _require_equal("summary.review_group_count", summary.get("review_group_count"), 22)
    _require_equal("summary.response_template_row_count", summary.get("response_template_row_count"), 113)
    _require_true("summary.private_grouped_review_written", summary.get("private_grouped_review_written"))
    _require_true("summary.private_response_template_written", summary.get("private_response_template_written"))
    _require_true("summary.private_candidate_catalog_written", summary.get("private_candidate_catalog_written"))
    _require_true("summary.private_grouped_question_list_written", summary.get("private_grouped_question_list_written"))
    _require_true("summary.private_grouped_review_gitignored", summary.get("private_grouped_review_gitignored"))
    _require_true("summary.private_response_template_gitignored", summary.get("private_response_template_gitignored"))
    _require_true("summary.private_candidate_catalog_gitignored", summary.get("private_candidate_catalog_gitignored"))
    _require_true("summary.private_grouped_question_list_gitignored", summary.get("private_grouped_question_list_gitignored"))
    _require_false("summary.response_template_is_active_authorization_record", summary.get("response_template_is_active_authorization_record"))
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

    boundary = summary.get("raw_boundary", {})
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

    safety = summary.get("public_safety", {})
    _require_true("public_safety.public_safe_aggregate_only", safety.get("public_safe_aggregate_only"))
    for key in (
        "private_grouped_review_committed",
        "private_response_template_committed",
        "private_candidate_catalog_committed",
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
    if require_private_intake:
        _check_private_intake()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-intake", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_intake=args.require_private_intake)
    print(
        "PASS: KMFA v0.1.4 owner review intake prep validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"review_groups={manifest['summary']['review_group_count']}, "
        f"response_rows={manifest['summary']['response_template_row_count']})"
    )


if __name__ == "__main__":
    main()
