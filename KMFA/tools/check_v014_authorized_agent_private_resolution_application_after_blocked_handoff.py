#!/usr/bin/env python3
"""Validate the v0.1.4 authorized-agent private-resolution phase."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import v014_authorized_agent_private_resolution_application_after_blocked_handoff as phase  # noqa: E402


class ValidationError(RuntimeError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _snapshot_core(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_count": snapshot.get("file_count"),
        "total_bytes": snapshot.get("total_bytes"),
        "extension_counts": snapshot.get("extension_counts"),
        "records_sha256": snapshot.get("records_sha256"),
        "records": snapshot.get("records"),
    }


def _public_text() -> str:
    paths = [
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.GO_NO_GO_PATH,
        phase.MATRIX_PATH,
        phase.REPORT_PATH,
        phase.GO_NO_GO_RECORD_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        phase.METADATA_MATRIX_PATH,
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def validate(*, require_private_resolution: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    public_paths = [
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.GO_NO_GO_PATH,
        phase.MATRIX_PATH,
        phase.REPORT_PATH,
        phase.GO_NO_GO_RECORD_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        phase.METADATA_MATRIX_PATH,
    ]
    for path in public_paths:
        _require(path.exists(), f"missing public artifact: {path}", errors)
    if errors:
        raise ValidationError("; ".join(errors))

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary metadata mirror mismatch", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest metadata mirror mismatch", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go metadata mirror mismatch", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix metadata mirror mismatch", errors)

    _require(summary.get("phase_id") == phase.PHASE_ID, "phase_id mismatch", errors)
    _require(summary.get("task_id") == phase.TASK_ID, "task_id mismatch", errors)
    _require(summary.get("status") == phase.STATUS, "status mismatch", errors)
    _require(summary.get("decision") == "NO_GO", "decision must remain NO_GO", errors)
    _require(summary.get("source_resolution_item_count") == 48, "source item count must be 48", errors)
    _require(summary.get("resolved_structural_item_count") == 8, "resolved structural count must be 8", errors)
    _require(summary.get("resolved_formula_mapping_count") == 4, "formula mapping count must be 4", errors)
    _require(summary.get("resolved_non_numeric_mapping_count") == 4, "taxonomy mapping count must be 4", errors)
    _require(summary.get("unresolved_business_value_item_count") == 40, "unresolved value count must be 40", errors)
    _require(summary.get("unresolved_difference_count") == 72, "unresolved difference count must be 72", errors)
    _require(summary.get("raw_snapshot_exact_match") is True, "raw snapshots must match exactly", errors)
    _require(summary.get("raw_inbox_mutated_by_this_phase") is False, "raw inbox mutation must be false", errors)
    _require(summary.get("raw_to_processed_value_comparison_complete") is False, "comparison must remain incomplete", errors)
    _require(summary.get("processed_consistency_verified") is False, "processed consistency must not be claimed", errors)
    _require(summary.get("business_value_consistency_verified") is False, "business consistency must not be claimed", errors)
    _require(summary.get("raw_business_data_committed") is False, "raw data must not be committed", errors)
    _require(summary.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    _require(summary.get("app_reinstall_performed") is False, "app reinstall must be false", errors)
    _require(summary.get("business_execution_performed") is False, "business execution must be false", errors)
    _require(matrix.get("check_count") == 14, "matrix check count must be 14", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix must have zero failures", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go report must be NO_GO", errors)
    _require(go_no_go.get("blocking_item_count") == 40, "go/no-go blocker count must be 40", errors)

    public_text = _public_text()
    forbidden_public_fragments = (
        "normalized_value_hash",
        "raw_value_hash",
        "private_processed_ref",
        "archive_member_name",
        "sheet_name",
        "cell_address",
        "context_text",
        "numeric_value_fingerprint",
        "private_authority_baseline_raw_match_do_not_commit",
    )
    for fragment in forbidden_public_fragments:
        _require(fragment not in public_text, f"private fragment leaked to public artifacts: {fragment}", errors)

    if require_private_resolution:
        private_paths = [
            phase.PRIVATE_RAW_BEFORE_PATH,
            phase.PRIVATE_RAW_AFTER_PATH,
            phase.PRIVATE_DIAGNOSTIC_PATH,
            phase.PRIVATE_RESOLUTION_RECORDS_PATH,
            phase.PRIVATE_UNRESOLVED_QUEUE_PATH,
            phase.PRIVATE_DIFFERENCE_REPORT_PATH,
            phase.PRIVATE_AUTHORITY_MATCH_PATH,
        ]
        for path in private_paths:
            _require(path.exists(), f"missing private artifact: {path}", errors)
            _require(_git_ignored(path), f"private artifact is not gitignored: {path}", errors)
        if not errors:
            before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
            after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
            diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
            records = _read_jsonl(phase.PRIVATE_RESOLUTION_RECORDS_PATH)
            unresolved = _read_jsonl(phase.PRIVATE_UNRESOLVED_QUEUE_PATH)
            source_queue_hash = _sha256_bytes(phase.SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH.read_bytes())
            _require(_snapshot_core(before) == _snapshot_core(after), "private raw snapshots differ", errors)
            _require(diagnostic.get("raw_snapshot_exact_match") is True, "private diagnostic raw match false", errors)
            _require(diagnostic.get("source_queue_unchanged") is True, "source queue changed during phase", errors)
            _require(diagnostic.get("source_queue_sha256_before") == source_queue_hash, "source queue before hash mismatch", errors)
            _require(diagnostic.get("source_queue_sha256_after") == source_queue_hash, "source queue after hash mismatch", errors)
            _require(len(records) == 48, "private resolution record count must be 48", errors)
            _require(len(unresolved) == 40, "private unresolved record count must be 40", errors)
            resolved = [row for row in records if row.get("resolution_applied") is True]
            _require(len(resolved) == 8, "private resolved record count must be 8", errors)
            _require(
                all(row.get("business_value_materialized") is False for row in resolved),
                "structural mappings must not materialize business values",
                errors,
            )
            _require(
                all(row.get("public_commit_allowed") is False for row in records),
                "private records must prohibit public commit",
                errors,
            )
            _require(
                all(row.get("resolution_applied") is False for row in unresolved),
                "unresolved queue contains resolved row",
                errors,
            )

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-resolution", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_resolution=args.require_private_resolution)
    summary = manifest["summary"]
    print(
        "authorized-agent private resolution validation: PASS "
        f"resolved={summary['resolved_structural_item_count']} "
        f"unresolved={summary['unresolved_business_value_item_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
