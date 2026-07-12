#!/usr/bin/env python3
"""Validate the KMFA v0.1.4 one-time public-safe GitHub main upload."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_ONE_TIME_GITHUB_MAIN_UPLOAD/machine/"
    "one_time_github_main_upload_manifest.json"
)
ACCEPTANCE_PATH = Path(
    "KMFA/stage_artifacts/V014_ONE_TIME_GITHUB_MAIN_UPLOAD/machine/"
    "acceptance_matrix_public_safe.json"
)
PHASE_ID = "V014_ONE_TIME_GITHUB_MAIN_UPLOAD"
TASK_ID = "KMFA-V014-ONE-TIME-GITHUB-MAIN-UPLOAD-20260713"
ACCEPTANCE_ID = "ACC-V014-ONE-TIME-GITHUB-MAIN-UPLOAD"
VERSION = "0.1.4-one-time-github-main-upload"
FORMULA_ID = "FORM-KMFA-V014-ONE-TIME-GITHUB-MAIN-UPLOAD-001"
PARAMETER_IDS = ("PARAM-KMFA-1822", "PARAM-KMFA-1823", "PARAM-KMFA-1824")
MODEL_REGISTRY_KEY = "kmfa_v014_one_time_github_main_upload"
NEXT_PHASE = "V014_APP_REINSTALL_AND_PARITY"

REQUIRED_FINAL_VALIDATION_KEYS = (
    "integration_full_suite",
    "final_overall_review_strict_validator",
    "focused_upload_tests",
    "no_float_money_check",
    "no_omission_check",
    "project_governance_validate",
    "lean_governance_validate",
    "governance_sync_validate",
    "structured_parse_checks",
    "tracked_forbidden_suffix_scan",
    "raw_filename_leak_scan",
    "high_signal_secret_scan",
    "diff_check",
)
FORBIDDEN_TRACKED_SUFFIXES = (
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".db",
)
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "actual_package_sha256",
    "member_sha256:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "amount_cents:",
    "account_number:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----BEGIN",
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class ValidationError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} contains a non-object row")
            rows.append(value)
    return rows


def _git_output(args: list[str]) -> str:
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


def _git_is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _require_all_false(label: str, payload: Any) -> None:
    _require(isinstance(payload, dict) and payload, f"{label} must be a non-empty object")
    for key, value in payload.items():
        _require(value is False, f"{label}.{key} must be false")


def _require_existing_refs(label: str, refs: Any) -> None:
    _require(isinstance(refs, list) and refs, f"{label} must be a non-empty list")
    missing = [ref for ref in refs if not isinstance(ref, str) or not Path(ref).exists()]
    _require(not missing, f"{label} missing refs: {missing}")


def _validate_public_text(paths: list[Path]) -> None:
    for path in paths:
        _require(path.is_file(), f"missing public evidence: {path}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for token in FORBIDDEN_EVIDENCE_TEXT:
            _require(token.lower() not in lower, f"forbidden public text {token!r} in {path}")
        for pattern in SECRET_PATTERNS:
            _require(pattern.search(text) is None, f"secret-like text in {path}: {pattern.pattern}")


def _validate_git_identity(manifest: dict[str, Any]) -> None:
    _require(_git_output(["rev-parse", "--show-toplevel"]).endswith("/CodexProject/kmfa"), "git root drift")
    _require(_git_output(["branch", "--show-current"]) == "codex/kmfa", "branch drift")
    remote = _git_output(["remote", "get-url", "origin"])
    _require(
        remote in {
            "git@github.com:LinzeColin/CodexProject.git",
            "https://github.com/LinzeColin/CodexProject.git",
        },
        "origin remote drift",
    )
    integration = manifest["git_integration"]
    for key in ("final_review_commit", "origin_main_integration_base", "integration_commit"):
        value = integration.get(key)
        _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"{key} must be a full SHA")
        _require(_git_is_ancestor(value), f"{key} is not an ancestor of HEAD")
    _require(integration.get("merge_integration_used") is True, "merge integration flag must be true")
    _require(integration.get("force_push_required") is False, "force push must not be required")


def _validate_source_review(manifest: dict[str, Any]) -> None:
    source = manifest["source_review"]
    _require(source.get("final_overall_review_validated") is True, "final review validation flag mismatch")
    _require(source.get("current_stage_validator_pass_count") == 18, "Stage validator count mismatch")
    _require(source.get("open_review_finding_count") == 0, "open final-review finding remains")
    _require(source.get("github_main_upload_ready") is True, "final review did not authorize code upload")
    _require(source.get("github_upload_performed_before_this_phase") is False, "source review upload state mismatch")
    final_manifest = _read_json(Path(source["final_overall_review_manifest_ref"]))
    _require(final_manifest.get("phase_id") == "V014_FINAL_OVERALL_REVIEW", "final review phase mismatch")
    _require(final_manifest.get("decision") == "NO_GO", "final review decision drift")
    _require(final_manifest.get("go_no_go", {}).get("github_main_upload_ready") is True, "final review upload readiness drift")


def _validate_governance() -> None:
    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == VERSION, "VERSION drift")
    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{PHASE_ID}"' in version_matrix, "VERSION_MATRIX current phase drift")
    _require(f'next_phase: "{NEXT_PHASE}"' in version_matrix, "VERSION_MATRIX next phase drift")
    _require(f'{MODEL_REGISTRY_KEY}: "{VERSION}"' in version_matrix, "VERSION_MATRIX profile missing")

    for path in (
        Path("KMFA/docs/governance/development_events.jsonl"),
        Path("KMFA/metadata/stage_status.jsonl"),
        Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl"),
    ):
        rows = _read_jsonl(path)
        _require(sum(row.get("phase_id") == PHASE_ID for row in rows) == 1, f"governance row missing or duplicated: {path}")

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(FORMULA_ID in formula_text, "formula registry entry missing")
    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id in PARAMETER_IDS:
        row = rows.get(parameter_id)
        _require(row is not None, f"parameter registry row missing: {parameter_id}")
        _require(row.get("formula_id") == FORMULA_ID, f"parameter formula drift: {parameter_id}")
        _require(row.get("parameter_version") == VERSION, f"parameter version drift: {parameter_id}")
    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(f"{MODEL_REGISTRY_KEY}:" in text, f"model profile missing: {path}")
        _require(FORMULA_ID in text, f"model formula missing: {path}")
        for parameter_id in PARAMETER_IDS:
            _require(parameter_id in text, f"model parameter missing {parameter_id}: {path}")


def _validate_final_validation(manifest: dict[str, Any]) -> None:
    validation = manifest.get("validation_summary")
    _require(isinstance(validation, dict), "validation_summary must be an object")
    for key in REQUIRED_FINAL_VALIDATION_KEYS:
        _require(str(validation.get(key, "")).startswith("PASS"), f"final validation is not PASS: {key}")
    acceptance = _read_json(ACCEPTANCE_PATH)
    _require(acceptance.get("check_fail_count") == 0, "acceptance matrix contains failures")
    _require(acceptance.get("check_pending_count") == 0, "acceptance matrix contains pending checks")
    _require(acceptance.get("check_pass_count") == acceptance.get("check_count"), "acceptance matrix is incomplete")


def _validate_remote_parity(manifest: dict[str, Any]) -> None:
    head = _git_output(["rev-parse", "HEAD"])
    origin_main = _git_output(["rev-parse", "origin/main"])
    remote_line = _git_output(["ls-remote", "--heads", "origin", "refs/heads/main"])
    remote_main = remote_line.split()[0] if remote_line else ""
    _require(head == origin_main == remote_main, f"remote parity failed: HEAD={head} origin/main={origin_main} remote={remote_main}")
    _require(_git_output(["status", "--short"]) == "", "remote parity requires a clean worktree")
    _require(
        manifest["upload_closure"].get("upload_closure_commit") == "recorded_by_commit_containing_this_file",
        "upload closure commit marker mismatch",
    )


def validate_v014_one_time_github_main_upload(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_final_validation: bool = False,
    require_remote_parity: bool = False,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    expected = {
        "schema_version": "kmfa.v014.one_time_github_main_upload_manifest.v1",
        "record_type": "v014_one_time_github_main_upload_manifest",
        "project_id": "KMFA",
        "stage_id": "S01-S18",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": "uploaded_to_github_main_public_safe",
        "decision": "NO_GO",
        "target_repository": "LinzeColin/CodexProject",
        "target_ref": "refs/heads/main",
        "source_branch": "codex/kmfa",
        "next_phase": NEXT_PHASE,
        "legacy_owner_plaintext_policy_applies_to_this_upload": False,
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"{key}: expected {value!r}, got {manifest.get(key)!r}")

    upload = manifest.get("upload_closure", {})
    _require(upload.get("upload_closure_commit") == "recorded_by_commit_containing_this_file", "closure marker mismatch")
    _require(upload.get("push_count_authorized") == 1, "exactly one push must be authorized")
    _require(upload.get("github_upload_performed_by_this_phase") is True, "upload completion flag mismatch")
    _require(upload.get("force_push_allowed") is False, "force push must be false")
    _require(upload.get("post_push_remote_parity_required") is True, "post-push parity must be required")

    release = manifest.get("release_state", {})
    _require(release.get("current_data_quality_grade") == "Q4", "data quality grade drift")
    _require(release.get("current_report_grade") == "D", "report grade drift")
    _require(release.get("decision") == "NO_GO", "release decision drift")
    _require(release.get("difference_state") == "3-9-2-1", "difference state drift")
    for key in (
        "lineage_full_check_complete",
        "delivery_allowed",
        "official_report_release_allowed",
        "business_execution_allowed",
        "persistent_business_write_allowed",
    ):
        _require(release.get(key) is False, f"release_state.{key} must be false")

    _require(manifest.get("phase_boundaries", {}).get("app_reinstall_performed") is False, "App reinstall must remain false")
    _require_all_false("public_repo_safety", manifest.get("public_repo_safety"))
    _require_all_false("raw_data_boundary", manifest.get("raw_data_boundary"))
    _require_existing_refs("source_refs", manifest.get("source_refs"))
    _require_existing_refs("evidence_refs", manifest.get("evidence_refs"))
    _validate_git_identity(manifest)
    _validate_source_review(manifest)
    _validate_governance()

    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = [path for path in tracked if Path(path).suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES]
    _require(not forbidden, f"tracked forbidden binary files: {forbidden}")
    evidence_paths = [Path(ref) for ref in manifest["evidence_refs"] if Path(ref).suffix.lower() in {".json", ".md"}]
    _validate_public_text(evidence_paths)

    if require_final_validation or require_remote_parity:
        _validate_final_validation(manifest)
    if require_remote_parity:
        _validate_remote_parity(manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-final-validation", action="store_true")
    parser.add_argument("--require-remote-parity", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_one_time_github_main_upload(
            args.manifest,
            require_final_validation=args.require_final_validation,
            require_remote_parity=args.require_remote_parity,
        )
    except (ValidationError, ValueError, KeyError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    mode = "remote_parity" if args.require_remote_parity else "final" if args.require_final_validation else "structural"
    print(
        "PASS: KMFA v0.1.4 one-time GitHub main upload validated "
        f"(mode={mode}, phase={manifest['phase_id']}, status={manifest['status']}, "
        f"next={manifest['next_phase']}, decision={manifest['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
