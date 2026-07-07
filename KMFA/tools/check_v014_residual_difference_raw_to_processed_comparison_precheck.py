#!/usr/bin/env python3
"""Validate KMFA v0.1.4 residual-difference comparison precheck artifacts."""

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

from KMFA.tools.v014_residual_difference_raw_to_processed_comparison_precheck import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    DIAGNOSTIC_CONCLUSION,
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
    PRIVATE_BLOCKER_RECORDS_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_PRECHECK_PATH,
    PRIVATE_READY_RECORDS_PATH,
    PRIVATE_REPORT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
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
    PRIVATE_PRECHECK_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_READY_RECORDS_PATH,
    PRIVATE_BLOCKER_RECORDS_PATH,
    PRIVATE_REPORT_PATH,
]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|authorization_item_id|source_final_threshold_item_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|business_value|field_header|processed_value_fingerprint|raw_candidate_fingerprint|raw_candidate_record_ref_hash)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
FORBIDDEN_PRIVATE_RAW_KEYS = {
    "raw_file_name",
    "archive_member_name",
    "sheet_name",
    "cell_address",
    "raw_value",
    "normalized_decimal",
    "context_text",
    "business_value",
    "field_header",
}


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


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, inner in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(inner))
    elif isinstance(value, list):
        for inner in value:
            keys.update(_walk_keys(inner))
    return keys


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
        "source_public_materialization_summary_read_by_this_phase",
        "source_public_materialization_go_no_go_read_by_this_phase",
        "source_public_materialization_matrix_read_by_this_phase",
        "source_private_materialization_diagnostic_read_by_this_phase",
        "source_private_materialization_result_read_by_this_phase",
        "source_private_materialized_records_read_by_this_phase",
        "source_private_raw_comparison_input_read_by_this_phase",
        "private_precheck_written_by_this_phase",
        "private_precheck_ready_records_written_by_this_phase",
        "private_precheck_blocker_records_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    _require_false(
        "raw_boundary.raw_to_processed_value_comparison_performed_by_this_phase",
        raw_boundary.get("raw_to_processed_value_comparison_performed_by_this_phase"),
    )


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
    _require_equal("summary.diagnostic", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source materialized", summary.get("source_private_materialized_record_count"), 72)
    _require_equal("summary.source raw input", summary.get("source_raw_comparison_input_record_count"), 72)
    _require_true("summary.precheck performed", summary.get("raw_to_processed_value_comparison_precheck_performed_by_this_phase"))
    _require_false("summary.precheck passed", summary.get("raw_to_processed_value_comparison_precheck_passed"))
    _require_equal("summary.ready count", summary.get("comparison_ready_record_count"), 0)
    _require_equal("summary.blocker count", summary.get("comparison_blocker_record_count"), 72)
    _require_equal("summary.missing anchor count", summary.get("missing_private_comparison_anchor_count"), 72)
    _require_equal("summary.track counts", summary.get("diagnostic_track_counts"), EXPECTED_TRACK_COUNTS)
    for key in (
        "raw_to_processed_value_comparison_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "full_reconciliation_allowed",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    for key in (
        "private_precheck_written",
        "private_precheck_gitignored",
        "private_ready_records_written",
        "private_ready_records_gitignored",
        "private_blocker_records_written",
        "private_blocker_records_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _require_equal("summary.next recommended", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _require_equal("summary.next required", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check count", matrix.get("precheck_check_count"), 7)
    _require_equal("matrix.pass count", matrix.get("precheck_pass_count"), 5)
    _require_equal("matrix.fail count", matrix.get("precheck_fail_count"), 2)
    _require_equal("matrix.ready count", matrix.get("comparison_ready_record_count"), 0)
    _require_equal("matrix.blocker count", matrix.get("comparison_blocker_record_count"), 72)
    _require_equal("matrix.missing anchor count", matrix.get("missing_private_comparison_anchor_count"), 72)
    _require_false("matrix.raw comparison ready", matrix.get("raw_to_processed_value_comparison_ready"))
    _require_false("matrix.raw comparison", matrix.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("matrix.business consistency", matrix.get("business_value_consistency_verified"))
    _require_equal("go_no_go.next required", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.ready count", go_no_go.get("comparison_ready_record_count"), 0)
    _require_equal("go_no_go.blocker count", go_no_go.get("comparison_blocker_record_count"), 72)
    _require_false("go_no_go.raw comparison ready", go_no_go.get("raw_to_processed_value_comparison_ready"))
    _require_false("go_no_go.raw comparison performed", go_no_go.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go_report", manifest.get("go_no_go_report"), go_no_go)


def _check_private_precheck(summary: dict[str, Any]) -> None:
    for path in PRIVATE_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        tracked = _git_output(["ls-files", "--", path.as_posix()])
        if tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    precheck = _read_json(PRIVATE_PRECHECK_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    ready = _read_jsonl(PRIVATE_READY_RECORDS_PATH)
    blockers = _read_jsonl(PRIVATE_BLOCKER_RECORDS_PATH)
    for payload_name, payload in (("precheck", precheck), ("diagnostic", diagnostic)):
        _require_equal(f"{payload_name}.phase_id", payload.get("phase_id"), PHASE_ID)
        _require_equal(f"{payload_name}.task_id", payload.get("task_id"), TASK_ID)
        forbidden_keys = _walk_keys(payload) & FORBIDDEN_PRIVATE_RAW_KEYS
        if forbidden_keys:
            raise ValidationError(f"{payload_name} contains forbidden raw keys: {sorted(forbidden_keys)}")
    _require_equal("private ready records length", len(ready), 0)
    _require_equal("private blocker records length", len(blockers), 72)
    _require_equal("precheck.ready count", precheck.get("comparison_ready_record_count"), 0)
    _require_equal("precheck.blocker count", precheck.get("comparison_blocker_record_count"), 72)
    _require_equal("diagnostic.blocker count", diagnostic.get("comparison_blocker_record_count"), 72)
    _require_false("precheck passed", precheck.get("raw_to_processed_value_comparison_precheck_passed"))
    _require_false("raw comparison ready", precheck.get("raw_to_processed_value_comparison_ready"))
    _require_false("raw comparison performed", precheck.get("raw_to_processed_value_comparison_performed"))
    _require_false("business consistency", precheck.get("business_value_consistency_verified"))
    track_counts = dict(Counter(row.get("diagnostic_track") for row in blockers))
    _require_equal("private blocker track counts", track_counts, EXPECTED_TRACK_COUNTS)
    for row in blockers:
        _require_equal("blocker status", row.get("comparison_precheck_status"), "missing_private_comparison_anchor")
        _require_false("blocker raw comparison ready", row.get("raw_to_processed_value_comparison_ready"))
        _require_false("blocker raw comparison performed", row.get("raw_to_processed_value_comparison_performed"))
        _require_false("blocker full reconciliation", row.get("full_reconciliation_allowed"))
        _require_false("blocker business consistency", row.get("business_value_consistency_verified"))
        _require_false("blocker public commit", row.get("public_commit_allowed"))
    _require_equal("summary blocker count", summary.get("comparison_blocker_record_count"), len(blockers))
    _require_equal("summary ready count", summary.get("comparison_ready_record_count"), len(ready))


def validate(*, require_private_precheck: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _require_equal("metadata summary", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata matrix", _read_json(METADATA_MATRIX_PATH), matrix)
    _check_summary(summary, matrix, go_no_go, manifest)
    if require_private_precheck:
        _check_private_precheck(summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-precheck", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_precheck=args.require_private_precheck)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 residual-difference raw comparison precheck artifacts validated "
        f"(ready_records={summary['comparison_ready_record_count']}, "
        f"blockers={summary['comparison_blocker_record_count']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
