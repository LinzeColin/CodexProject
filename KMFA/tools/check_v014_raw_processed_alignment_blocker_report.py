from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_RAW_PROCESSED_ALIGNMENT_BLOCKER_REPORT"
TASK_ID = "KMFA-V014-RAW-PROCESSED-ALIGNMENT-BLOCKER-REPORT-20260706"
VERSION = "0.1.4-raw-processed-alignment-blocker-report"
ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"

SUMMARY_PATH = MACHINE_DIR / "raw_processed_alignment_blocker_summary.json"
MANIFEST_PATH = MACHINE_DIR / "raw_processed_alignment_blocker_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "raw_processed_alignment_blocker_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "raw_processed_alignment_blocker_report.md"
DIAGNOSTIC_PACKET_PATH = HUMAN_DIR / "chatgpt_agent_diagnostic_packet.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    REPORT_PATH,
    DIAGNOSTIC_PACKET_PATH,
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_raw_processed_alignment_blocker_summary.json",
    QUALITY_DIR / "v014_raw_processed_alignment_blocker_manifest.json",
    QUALITY_DIR / "v014_raw_processed_alignment_blocker_go_no_go_report.json",
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
    return json.loads(path.read_text(encoding="utf-8"))


def _require_equal(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{name}: expected {expected!r}, got {actual!r}")


def _require_false(name: str, value: Any) -> None:
    if value is not False:
        raise ValidationError(f"{name}: expected False, got {value!r}")


def _require_true(name: str, value: Any) -> None:
    if value is not True:
        raise ValidationError(f"{name}: expected True, got {value!r}")


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


def validate() -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.source_artifact_count", summary.get("source_artifact_count"), 10)
    _require_equal("summary.raw_value_fingerprint_count", summary.get("raw_value_fingerprint_count"), 871)
    _require_equal("summary.raw_unique_numeric_fingerprint_count", summary.get("raw_unique_numeric_fingerprint_count"), 330)
    _require_equal("summary.raw_root_file_count", summary.get("raw_root_file_count"), 5)
    _require_true("summary.raw_root_stat_unchanged_after_phase", summary.get("raw_root_stat_unchanged_after_phase"))
    _require_false("summary.raw_inbox_mutation_detected", summary.get("raw_inbox_mutation_detected"))
    _require_equal("summary.processed_target_slot_count", summary.get("processed_target_slot_count"), 149)
    _require_equal("summary.staged_processed_value_fingerprint_count", summary.get("staged_processed_value_fingerprint_count"), 0)
    _require_equal("summary.usable_processed_source_map_count", summary.get("usable_processed_source_map_count"), 0)
    _require_equal("summary.authorized_filled_item_count", summary.get("authorized_filled_item_count"), 36)
    _require_equal("summary.authorized_unfilled_item_count", summary.get("authorized_unfilled_item_count"), 113)
    _require_equal("summary.unresolved_gap_item_count", summary.get("unresolved_gap_item_count"), 113)
    _require_equal("summary.active_fill_record_keep_pending_count", summary.get("active_fill_record_keep_pending_count"), 113)
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.raw_processed_structural_key_intersection_count", summary.get("raw_processed_structural_key_intersection_count"), 0)
    _require_equal("summary.comparable_value_pair_count", summary.get("comparable_value_pair_count"), 0)
    _require_false("summary.business_value_consistency_verified", summary.get("business_value_consistency_verified"))
    _require_false("summary.raw_to_processed_value_comparison_performed", summary.get("raw_to_processed_value_comparison_performed"))
    _require_true(
        "summary.interim_report_generated_for_external_agent_diagnosis",
        summary.get("interim_report_generated_for_external_agent_diagnosis"),
    )
    _require_false("summary.final_discrepancy_report_required_now", summary.get("final_discrepancy_report_required_now"))
    _require_true(
        "summary.final_discrepancy_report_required_if_repeated_mismatch_after_authorized_map",
        summary.get("final_discrepancy_report_required_if_repeated_mismatch_after_authorized_map"),
    )

    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.comparable_value_pair_count", go_no_go.get("comparable_value_pair_count"), 0)
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app_reinstall_performed", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business_execution_performed", go_no_go.get("business_execution_performed"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)

    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    return manifest


def main() -> None:
    manifest = validate()
    print(
        "PASS: KMFA v0.1.4 raw/processed alignment blocker report validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"comparable_pairs={manifest['summary']['comparable_value_pair_count']})"
    )


if __name__ == "__main__":
    main()
