from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_INPUT_KIT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-INPUT-KIT-20260706"
VERSION = "0.1.4-processed-value-source-map-completion-input-kit"
ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_input_kit/owner_authorized_processed_value_source_map_completion_template.json"
)

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_input_kit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_input_kit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_input_kit_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_input_kit_report.md",
    HUMAN_DIR / "owner_agent_completion_packet.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_processed_value_source_map_completion_input_kit_summary.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_input_kit_manifest.json",
    QUALITY_DIR / "v014_processed_value_source_map_completion_input_kit_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(r"raw_hash|metadata_hash|sheet_name|cell_ref|row_index|zip_member", re.IGNORECASE),
]

ALLOWED_ACTION_CODES = [
    "supply_authorized_processed_value_fingerprint",
    "map_existing_metadata_hash_sibling",
    "keep_pending",
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


def _check_private_template() -> None:
    template = _read_json(PRIVATE_TEMPLATE_PATH)
    _require_equal("private_template.phase_id", template.get("phase_id"), PHASE_ID)
    _require_equal("private_template.task_id", template.get("task_id"), TASK_ID)
    _require_equal("private_template.completion_item_count", template.get("completion_item_count"), 113)
    items = template.get("completion_items")
    if not isinstance(items, list):
        raise ValidationError("private template completion_items must be a list")
    _require_equal("private_template.completion_items len", len(items), 113)
    target_ids = [item.get("target_slot_id") for item in items if isinstance(item, dict)]
    _require_equal("private_template.unique_target_slot_count", len(set(target_ids)), 113)
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("private template item must be an object")
        _require_equal("item.allowed_action_codes", item.get("allowed_action_codes"), ALLOWED_ACTION_CODES)
        _require_equal(
            "item.selected_action_code",
            item.get("selected_action_code"),
            "PENDING_OWNER_OR_AUTHORIZED_DELEGATE_INPUT",
        )
    result = subprocess.run(["git", "check-ignore", "-q", PRIVATE_TEMPLATE_PATH.as_posix()], check=False)
    _require_equal("private_template.gitignored", result.returncode, 0)


def validate(*, require_private_template: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.source_blocker_decision", summary.get("source_blocker_decision"), "NO_GO")
    _require_equal("summary.source_blocker_comparable_value_pair_count", summary.get("source_blocker_comparable_value_pair_count"), 0)
    _require_equal("summary.source_worklist_item_count", summary.get("source_worklist_item_count"), 113)
    _require_equal("summary.active_fill_record_item_count", summary.get("active_fill_record_item_count"), 113)
    _require_equal("summary.active_keep_pending_item_count", summary.get("active_keep_pending_item_count"), 113)
    _require_true("summary.private_completion_template_written", summary.get("private_completion_template_written"))
    _require_true("summary.private_completion_template_gitignored", summary.get("private_completion_template_gitignored"))
    _require_equal("summary.private_completion_template_item_count", summary.get("private_completion_template_item_count"), 113)
    _require_equal(
        "summary.private_completion_template_unique_target_slot_count",
        summary.get("private_completion_template_unique_target_slot_count"),
        113,
    )
    _require_true("summary.completion_ready_for_owner_or_agent_fill", summary.get("completion_ready_for_owner_or_agent_fill"))
    _require_false("summary.authorized_completion_record_supplied", summary.get("authorized_completion_record_supplied"))
    _require_equal("summary.authorized_processed_value_fingerprint_count", summary.get("authorized_processed_value_fingerprint_count"), 0)
    _require_equal("summary.metadata_digest_sibling_mapping_count", summary.get("metadata_digest_sibling_mapping_count"), 0)
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.comparable_value_pair_count", summary.get("comparable_value_pair_count"), 0)
    _require_false("summary.business_value_consistency_verified", summary.get("business_value_consistency_verified"))
    _require_false("summary.raw_to_processed_value_comparison_performed", summary.get("raw_to_processed_value_comparison_performed"))
    _require_false("summary.github_upload_performed", summary.get("github_upload_performed"))
    _require_false("summary.app_reinstall_performed", summary.get("app_reinstall_performed"))
    _require_false("summary.business_execution_performed", summary.get("business_execution_performed"))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.private_completion_template_item_count", go_no_go.get("private_completion_template_item_count"), 113)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)

    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_template:
        _check_private_template()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-template", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_template=args.require_private_template)
    print(
        "PASS: KMFA v0.1.4 processed value source-map completion input kit validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"template_items={manifest['summary']['private_completion_template_item_count']})"
    )


if __name__ == "__main__":
    main()
