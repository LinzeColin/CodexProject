#!/usr/bin/env python3
"""Validate owner-authorized anchor confirmation blocker audit artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit import (  # noqa: E402
    ACCEPTANCE_ID,
    AUDIT_CONCLUSION,
    DECISION,
    EXPECTED_TRACK_COUNTS,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_AUDIT_DIAGNOSTIC_PATH,
    PRIVATE_AUDIT_QUEUE_PATH,
    PRIVATE_AUDIT_REPORT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_GO_NO_GO_PATH,
    SOURCE_MANIFEST_PATH,
    SOURCE_MATRIX_PATH,
    SOURCE_PRIVATE_CONFIRMATION_READY_QUEUE_PATH,
    SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_DIFFERENCE_REPORT_PATH,
    SOURCE_PRIVATE_REPORT_PATH,
    SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH,
    SOURCE_SUMMARY_PATH,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DOWNLOADS_MARKER = "/Users/" + "linzezhang/Downloads"
RAW_INBOX_MARKER = "KMFA" + "_MetaData"
PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    MATRIX_PATH,
    REPORT_PATH,
    GO_NO_GO_RECORD_PATH,
    TEST_RESULTS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    METADATA_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MATRIX_PATH,
]
PRIVATE_ARTIFACTS = [
    SOURCE_PRIVATE_DIFFERENCE_REPORT_PATH,
    SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH,
    SOURCE_PRIVATE_CONFIRMATION_READY_QUEUE_PATH,
    SOURCE_PRIVATE_REPORT_PATH,
    PRIVATE_AUDIT_DIAGNOSTIC_PATH,
    PRIVATE_AUDIT_QUEUE_PATH,
    PRIVATE_AUDIT_REPORT_PATH,
]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|business_value|field_header|processed_value_fingerprint|raw_candidate_fingerprint|raw_candidate_record_ref_hash)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL artifact: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, value: Any) -> None:
    if value is not True:
        raise ValidationError(f"{label}: expected true, got {value!r}")


def _require_false(label: str, value: Any) -> None:
    if value is not False:
        raise ValidationError(f"{label}: expected false, got {value!r}")


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


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False).returncode == 0


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
    forbidden = re.compile(
        r"\.codex_private_runtime|"
        + re.escape(RAW_DOWNLOADS_MARKER)
        + "|"
        + re.escape(RAW_INBOX_MARKER)
        + r"|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$",
        re.IGNORECASE,
    )
    hits = [path for path in tracked if forbidden.search(path)]
    if hits:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(hits[:20]))


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    for key in (
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "source_public_difference_report_summary_read_by_this_phase",
        "source_public_difference_report_manifest_read_by_this_phase",
        "source_public_difference_report_go_no_go_read_by_this_phase",
        "source_public_difference_report_matrix_read_by_this_phase",
        "source_private_difference_report_read_by_this_phase",
        "source_private_diagnostic_read_by_this_phase",
        "source_private_unresolved_queue_read_by_this_phase",
        "source_private_confirmation_ready_queue_read_by_this_phase",
        "source_private_report_read_by_this_phase",
        "private_audit_diagnostic_written_by_this_phase",
        "private_audit_queue_written_by_this_phase",
        "private_audit_report_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    for key in (
        "owner_authorized_anchor_confirmation_performed_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key != "public_safe_aggregate_only":
            _require_false(f"public_safety.{key}", value)


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.audit conclusion", summary.get("audit_conclusion"), AUDIT_CONCLUSION)
    _require_equal(
        "summary.source phase",
        summary.get("source_phase_id"),
        "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_OR_DIFFERENCE_REPORT",
    )
    _require_equal("summary.source manifest phase", summary.get("source_manifest_phase_id"), summary.get("source_phase_id"))
    _require_equal("summary.source go/no-go", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source difference report items", summary.get("source_difference_report_item_count"), 72)
    _require_equal("summary.source unresolved", summary.get("source_unresolved_difference_count"), 72)
    _require_equal("summary.source confirmations", summary.get("source_owner_authorized_anchor_confirmation_count"), 0)
    _require_equal("summary.source private unresolved rows", summary.get("source_private_unresolved_queue_item_count"), 72)
    _require_equal("summary.source private ready rows", summary.get("source_private_confirmation_ready_queue_item_count"), 0)
    _require_true("summary.audit performed", summary.get("owner_authorized_anchor_blocker_audit_performed"))
    _require_equal("summary.prior observation", summary.get("prior_owner_authorized_anchor_blocker_observation_count"), 0)
    _require_equal("summary.current observation", summary.get("owner_authorized_anchor_blocker_observation_count"), 1)
    _require_false("summary.threshold", summary.get("owner_authorized_anchor_blocked_audit_threshold_met"))
    _require_equal(
        "summary.goal status recommendation",
        summary.get("goal_status_recommendation"),
        "continue_to_owner_authorized_anchor_blocker_threshold_recheck",
    )
    _require_equal("summary.blockers", summary.get("owner_authorized_anchor_blocker_count"), 72)
    _require_equal("summary.confirmations", summary.get("owner_authorized_anchor_confirmation_count"), 0)
    _require_equal("summary.unresolved", summary.get("unresolved_difference_count"), 72)
    _require_equal("summary.missing owner anchors", summary.get("missing_owner_authorized_anchor_count"), 72)
    _require_equal("summary.missing processed fingerprints", summary.get("missing_processed_value_fingerprint_count"), 72)
    _require_equal("summary.missing raw anchors", summary.get("missing_raw_candidate_anchor_count"), 72)
    _require_equal("summary.track counts", summary.get("diagnostic_track_counts"), EXPECTED_TRACK_COUNTS)
    for key in (
        "anchor_confirmation_ready",
        "owner_authorized_anchor_confirmation_performed_by_this_phase",
        "raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "full_reconciliation_allowed",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    for key in (
        "private_audit_diagnostic_written",
        "private_audit_queue_written",
        "private_audit_report_written",
        "private_audit_diagnostic_gitignored",
        "private_audit_queue_gitignored",
        "private_audit_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _require_equal("summary.next required", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.next recommended", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.count", matrix.get("check_count"), 13)
    _require_equal("matrix.pass", matrix.get("check_pass_count"), 13)
    _require_equal("matrix.fail", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_difference_report_loaded",
        "source_go_no_go_preserved",
        "source_unresolved_differences_present",
        "owner_authorized_anchor_blockers_present",
        "blocker_audit_recorded",
        "threshold_not_met_on_first_observation",
        "anchor_confirmation_count_zero",
        "unresolved_difference_count_preserved",
        "diagnostic_track_counts_locked",
        "raw_inbox_untouched",
        "source_private_inputs_not_mutated",
        "private_outputs_ignored",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.observation", go_no_go.get("owner_authorized_anchor_blocker_observation_count"), 1)
    _require_false("go_no_go.threshold", go_no_go.get("owner_authorized_anchor_blocked_audit_threshold_met"))
    _require_equal("go_no_go.blockers", go_no_go.get("owner_authorized_anchor_blocker_count"), 72)
    _require_equal("go_no_go.confirmations", go_no_go.get("owner_authorized_anchor_confirmation_count"), 0)
    _require_equal("go_no_go.unresolved", go_no_go.get("unresolved_difference_count"), 72)
    _require_false("go_no_go.anchor ready", go_no_go.get("anchor_confirmation_ready"))
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_allowed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_allowed"))
    _require_equal("go_no_go.next required", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.next recommended", go_no_go.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_artifacts() -> None:
    for path in PRIVATE_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
    _read_json(SOURCE_SUMMARY_PATH)
    _read_json(SOURCE_MANIFEST_PATH)
    _read_json(SOURCE_GO_NO_GO_PATH)
    _read_json(SOURCE_MATRIX_PATH)
    source_report = _read_json(SOURCE_PRIVATE_DIFFERENCE_REPORT_PATH)
    source_unresolved = _read_jsonl(SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH)
    source_ready = _read_jsonl(SOURCE_PRIVATE_CONFIRMATION_READY_QUEUE_PATH)
    audit_diagnostic = _read_json(PRIVATE_AUDIT_DIAGNOSTIC_PATH)
    audit_rows = _read_jsonl(PRIVATE_AUDIT_QUEUE_PATH)
    _require_equal("source report unresolved", source_report.get("unresolved_difference_count"), 72)
    _require_equal("source unresolved rows", len(source_unresolved), 72)
    _require_equal("source ready rows", len(source_ready), 0)
    _require_equal("audit diagnostic observation", audit_diagnostic.get("owner_authorized_anchor_blocker_observation_count"), 1)
    _require_equal("audit rows", len(audit_rows), 72)
    _require_equal(
        "private target sets",
        {row.get("target_slot_id") for row in source_unresolved},
        {row.get("target_slot_id") for row in audit_rows},
    )
    _require_equal("private unresolved track counts", dict(Counter(row.get("diagnostic_track") for row in audit_rows)), EXPECTED_TRACK_COUNTS)
    for row in audit_rows:
        _require_false("audit anchor ready", row.get("anchor_confirmation_ready_after_audit"))
        _require_false("audit raw comparison ready", row.get("raw_to_processed_value_comparison_ready_after_audit"))
        _require_false("audit business consistency", row.get("business_value_consistency_verified_after_audit"))
        _require_false("audit threshold", row.get("threshold_met_after_this_phase"))
        _require_false("audit public", row.get("public_commit_allowed"))
    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in PRIVATE_ARTIFACTS:
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")


def validate(*, require_private_audit: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for metadata_path, source in (
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _require_equal(f"{metadata_path}.content", _read_json(metadata_path), source)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_audit:
        _check_private_artifacts()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-audit", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_audit=args.require_private_audit)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 owner-authorized anchor blocker audit artifacts validated "
        f"(blockers={summary['owner_authorized_anchor_blocker_count']}, "
        f"observation={summary['owner_authorized_anchor_blocker_observation_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
