from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_READINESS_RECHECK"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-READINESS-RECHECK-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-readiness-recheck"
ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_readiness_recheck/private_readiness_recheck_diagnostic.json"
)

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_readiness_recheck_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_readiness_recheck_report.md",
    HUMAN_DIR / "owner_agent_readiness_recheck_packet.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_readiness_recheck_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_readiness_recheck_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_readiness_recheck_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(r"raw_hash|metadata_hash|sheet_name|cell_ref|row_index|zip_member", re.IGNORECASE),
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


def _check_public_artifacts() -> None:
    for path in PUBLIC_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                raise ValidationError(f"forbidden public marker {pattern.pattern!r} in {path}")


def _check_no_raw_private_files_tracked() -> None:
    repo_root = PROJECT_ROOT.parent
    tracked = subprocess.check_output(["git", "ls-files", "KMFA"], cwd=repo_root, text=True).splitlines()
    forbidden_suffix = re.compile(r"\.(zip|xlsx|xls|pdf|sqlite|db|key|pem|p12|pfx)$", re.IGNORECASE)
    hits = [path for path in tracked if forbidden_suffix.search(path) or ".codex_private_runtime" in path]
    if hits:
        raise ValidationError("forbidden tracked raw/private files: " + ", ".join(hits[:20]))


def _check_private_diagnostic() -> None:
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("private_diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private_diagnostic.task_id", diagnostic.get("task_id"), TASK_ID)
    counts = diagnostic.get("counts", {})
    _require_equal("private_diagnostic.template_item_count", counts.get("template_item_count"), 113)
    _require_equal("private_diagnostic.pending_selected_action_count", counts.get("pending_selected_action_count"), 113)
    _require_equal("private_diagnostic.valid_completion_item_count", counts.get("valid_completion_item_count"), 0)
    _require_false("private_diagnostic.reapplication_ready", diagnostic.get("reapplication_ready"))
    result = subprocess.run(["git", "check-ignore", "-q", PRIVATE_DIAGNOSTIC_PATH.as_posix()], check=False)
    _require_equal("private_diagnostic.gitignored", result.returncode, 0)


def validate(*, require_private_diagnostic: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.source_application_decision", summary.get("source_application_decision"), "NO_GO")
    _require_equal("summary.source_application_valid_completion_item_count", summary.get("source_application_valid_completion_item_count"), 0)
    _require_true("summary.private_template_gitignored", summary.get("private_template_gitignored"))
    _require_true("summary.private_diagnostic_written", summary.get("private_diagnostic_written"))
    _require_true("summary.private_diagnostic_gitignored", summary.get("private_diagnostic_gitignored"))
    _require_equal("summary.completion_template_item_count", summary.get("completion_template_item_count"), 113)
    _require_equal("summary.completion_template_unique_target_slot_count", summary.get("completion_template_unique_target_slot_count"), 113)
    _require_equal("summary.pending_selected_action_count", summary.get("pending_selected_action_count"), 113)
    _require_equal("summary.valid_completion_item_count", summary.get("valid_completion_item_count"), 0)
    _require_equal("summary.invalid_or_pending_completion_item_count", summary.get("invalid_or_pending_completion_item_count"), 113)
    _require_false("summary.authorized_completion_record_supplied", summary.get("authorized_completion_record_supplied"))
    _require_equal("summary.authorized_processed_value_fingerprint_count", summary.get("authorized_processed_value_fingerprint_count"), 0)
    _require_false("summary.source_map_completion_reapplication_ready", summary.get("source_map_completion_reapplication_ready"))
    _require_false("summary.source_map_completion_reapplication_performed", summary.get("source_map_completion_reapplication_performed"))
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.comparable_value_pair_count", summary.get("comparable_value_pair_count"), 0)
    _require_false("summary.business_value_consistency_verified", summary.get("business_value_consistency_verified"))
    _require_false("summary.raw_to_processed_value_comparison_performed", summary.get("raw_to_processed_value_comparison_performed"))
    _require_false("summary.github_upload_performed", summary.get("github_upload_performed"))
    _require_false("summary.app_reinstall_performed", summary.get("app_reinstall_performed"))
    _require_false("summary.business_execution_performed", summary.get("business_execution_performed"))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.pending_selected_action_count", go_no_go.get("pending_selected_action_count"), 113)
    _require_false("go_no_go.source_map_completion_reapplication_ready", go_no_go.get("source_map_completion_reapplication_ready"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)

    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_diagnostic:
        _check_private_diagnostic()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_diagnostic=args.require_private_diagnostic)
    print(
        "PASS: KMFA v0.1.4 processed value source-map completion readiness recheck validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid_items={manifest['summary']['valid_completion_item_count']}, "
        f"reapplication_ready={manifest['summary']['source_map_completion_reapplication_ready']})"
    )


if __name__ == "__main__":
    main()
