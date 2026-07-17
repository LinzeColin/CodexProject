#!/usr/bin/env python3
"""Strict validator for KMFA v1.5 S03-P3 public repository safety."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import stat
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from KMFA.tools import build_v015_s03_p3_public_repository_safety as builder
from KMFA.tools import v015_s03_p3_public_repository_safety as safety


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE
MANIFEST_PATH = ARTIFACT_ROOT / builder.MANIFEST_RELATIVE
TASK_MATRIX_PATH = ARTIFACT_ROOT / builder.TASK_MATRIX_RELATIVE
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / builder.VALIDATION_RESULTS_RELATIVE
PROTECTION_PATH = ARTIFACT_ROOT / builder.PROTECTION_VERIFICATION_RELATIVE
DUAL_PLANE_PATH = ARTIFACT_ROOT / builder.DUAL_PLANE_RELATIVE
LEGACY_CENSUS_PATH = ARTIFACT_ROOT / builder.LEGACY_CENSUS_RELATIVE
METADATA_CLASSIFICATION_PATH = ARTIFACT_ROOT / builder.METADATA_CLASSIFICATION_RELATIVE
PRIVATE_RECEIPTS_PATH = PROJECT_ROOT / builder.PRIVATE_VALIDATION_RECEIPTS_RELATIVE

POST_VALIDATION_GOVERNANCE_REFS = frozenset(
    {
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/events.jsonl",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/metadata/stage_status.jsonl",
    }
)
POST_VALIDATION_ARTIFACT_REFS = frozenset(
    builder.ARTIFACT_REFS[key] for key in builder.VALIDATION_MUTABLE_KEYS
)
POST_VALIDATION_ALLOWED_REFS = POST_VALIDATION_GOVERNANCE_REFS | POST_VALIDATION_ARTIFACT_REFS
FINAL_EVENT_ID = "EVENT-KMFA-20260714-V015-S03-P3-PUBLIC-REPOSITORY-SAFETY-FINAL"
FINAL_DEVELOPMENT_EVENT_ID = "DEV-KMFA-20260714-V015-S03-P3-PUBLIC-REPOSITORY-SAFETY-FINAL"
FINAL_STATUS_RECORD_ID = "STATUS-KMFA-20260714-V015-S03-P3-PUBLIC-REPOSITORY-SAFETY-FINAL"
FINAL_ITERATION_ID = "ITER-20260714-KMFA-V015-S03-P3-PUBLIC-REPOSITORY-SAFETY"
FINAL_RECORD_STATUS = "completed_validated_local_only_s03p3_passed_s03_review_pending_public_repository_safety"
FINAL_DEVELOPMENT_SUMMARY = (
    "S03-P3 public repository safety passed one exact validation run; S03 remains "
    "IN_PROGRESS/PENDING at 100 percent and only S03 Stage review/fix is opened."
)
FINAL_EVIDENCE_REF = "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/"
FINAL_RESULT_COMMIT = "recorded_by_commit_containing_this_file"
FINAL_VERSION = "1.5.0-dev-s03p3"
FINAL_ASSURANCE_GENERATOR_VERSION = "manual-1.5.0-dev-s03p3"
FINAL_ASSURANCE_BINDING = "recorded_by_commit_containing_this_phase_evidence"
FINAL_ASSURANCE_ACTIVE_PARAMETER_COUNT = 1492
FINAL_ASSURANCE_ACTIVE_FORMULA_COUNT = 327
FINAL_ASSURANCE_EVIDENCE_REFS = frozenset(
    {
        FINAL_EVIDENCE_REF,
        "KMFA/tools/check_v015_s03_p3_public_repository_safety.py",
        "KMFA/tools/run_v015_s03_p3_validations.py",
        "KMFA/tests/test_v015_s03_p3_public_repository_safety_checker.py",
    }
)

_SENSITIVE_GOVERNANCE_KEY = re.compile(
    r"(?:^|_)(?:raw_path|exact_path|file_name|filename|customer|person_name|identity|"
    r"money|amount|credential|password|api_key|access_token|refresh_token|private_key|"
    r"private_hash|hmac_key|webhook)(?:_|$)",
    re.IGNORECASE,
)
_SENSITIVE_GOVERNANCE_VALUE = re.compile(
    r"(?:/Users/|/Volumes/|/home/|/tmp/|~[/\\]|[A-Za-z]:[/\\]|file://|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\bAKIA[0-9A-Z]{16}\b|\bgh[opusr]_[A-Za-z0-9_]{20,}\b)"
)


class CheckError(RuntimeError):
    """The phase contract is incomplete or unsafe."""


def _git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _public_bytes(path: Path) -> bytes:
    try:
        relative = path.relative_to(REPO_ROOT).as_posix()
        return safety.read_repository_file(relative)
    except (FileNotFoundError, OSError, ValueError, safety.SafetyError) as error:
        raise CheckError(f"unsafe or unreadable public repository file: {path}") from error


def _public_text(path: Path) -> str:
    try:
        return _public_bytes(path).decode("utf-8")
    except UnicodeDecodeError as error:
        raise CheckError(f"public repository file is not UTF-8: {path}") from error


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(_public_text(path))
    if not isinstance(value, dict):
        raise CheckError(f"{path.name} must contain an object")
    return value


def _read_json_rows(path: Path, *, private: bool = False) -> list[dict[str, Any]]:
    if private:
        payload = safety._read_regular_single_link(path, expected_mode=0o600)
        text = payload.decode("utf-8")
    else:
        text = _public_text(path)
    if path.suffix == ".json":
        value = json.loads(text)
        if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
            raise CheckError(f"{path.name} must contain object rows")
        return value
    rows = []
    for line in text.splitlines():
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise CheckError(f"{path.name} contains a non-object row")
            rows.append(row)
    return rows


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_public_text(path), newline="")))


def _top_level_yaml_scalars(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in _public_text(path).splitlines():
        if not line or line[0].isspace() or line.startswith("#") or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        raw = raw.strip()
        if not raw:
            continue
        if raw in {"true", "false"}:
            value: Any = raw == "true"
        elif raw == "null":
            value = None
        elif re.fullmatch(r"-?[0-9]+", raw):
            value = int(raw)
        elif raw.startswith('"') and raw.endswith('"'):
            value = json.loads(raw)
        else:
            value = raw
        values[key.strip()] = value
    return values


def _assurance_header_keys(path: Path) -> set[str]:
    """Return the exact mutable header key set before the legacy dimensions body."""
    keys: set[str] = set()
    for line in _public_text(path).splitlines():
        if not line or line[0].isspace() or line.startswith("#") or ":" not in line:
            continue
        key = line.split(":", 1)[0].strip()
        keys.add(key)
        if key == "dimensions":
            break
    return keys


def _assurance_s03p3_semantics(path: Path) -> tuple[int | None, int | None, set[str]]:
    """Read only the final mutable assurance values needed by the S03-P3 gate."""
    text = _public_text(path)
    parameter_match = re.search(r"^\s{4}total_active_parameters:\s*([0-9]+)\s*$", text, re.MULTILINE)
    formula_match = re.search(r"^\s{4}total_active_formulas:\s*([0-9]+)\s*$", text, re.MULTILINE)
    empirical_match = re.search(
        r"^\s{2}empirical_validation:\s*$\n(?P<body>.*?)(?=^\s{2}[A-Za-z0-9_]+:\s*$|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    evidence_refs: set[str] = set()
    if empirical_match:
        evidence_refs = set(
            re.findall(r'^\s{6}-\s+"([^"\r\n]+)"\s*$', empirical_match.group("body"), re.MULTILINE)
        )
    return (
        int(parameter_match.group(1)) if parameter_match else None,
        int(formula_match.group(1)) if formula_match else None,
        evidence_refs,
    )


def _sensitive_governance_findings(value: Any, *, location: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_location = f"{location}.{key_text}"
            if _SENSITIVE_GOVERNANCE_KEY.search(key_text):
                findings.append(child_location)
            findings.extend(_sensitive_governance_findings(child, location=child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_sensitive_governance_findings(child, location=f"{location}[{index}]"))
    elif isinstance(value, str) and _SENSITIVE_GOVERNANCE_VALUE.search(value):
        findings.append(location)
    return findings


def _validate_exact_governance_mapping(
    *, label: str, actual: Mapping[str, Any], expected: Mapping[str, Any]
) -> None:
    sensitive = _sensitive_governance_findings(actual)
    if sensitive:
        raise CheckError(f"final governance sensitive field/value: {label}.{sensitive[0]}")
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise CheckError(f"final governance record missing keys: {label}: {', '.join(missing)}")
    extra = sorted(set(actual) - set(expected))
    if extra:
        raise CheckError(f"final governance record extra keys: {label}: {', '.join(extra)}")
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            raise CheckError(f"final governance record drift: {label}.{key}")


def _validated_final_event_time(value: Any, *, label: str) -> str:
    text = str(value)
    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError as error:
        raise CheckError(f"final governance event time drift: {label}") from error
    if timestamp.tzinfo is None or timestamp.date().isoformat() != "2026-07-14":
        raise CheckError(f"final governance event time drift: {label}")
    if timestamp.utcoffset() is None or int(timestamp.utcoffset().total_seconds()) != 10 * 60 * 60:
        raise CheckError(f"final governance event timezone drift: {label}")
    return text


def _last_jsonl_row(path: Path) -> dict[str, Any]:
    rows = _read_json_rows(path)
    if not rows:
        raise CheckError(f"empty governance JSONL: {path.relative_to(REPO_ROOT)}")
    return rows[-1]


def _validate_phase_governance_shape() -> None:
    expected = {
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "decision": "CONTINUE_TO_S03_STAGE_REVIEW_ONLY",
        "s03_p3_acceptance_status": "PASSED",
        "s03_stage_review_entry_allowed": True,
        "s03_stage_review_started": False,
        "s03_stage_review_performed": False,
        "next_gate_id": "S03-STAGE-REVIEW",
        "reachable_history_clean": False,
        "history_rewrite_performed": False,
        "final_github_upload_allowed": False,
    }
    for path in (
        PROJECT_ROOT / "docs/governance/project.yaml",
        PROJECT_ROOT / "metadata/project/project.yaml",
        PROJECT_ROOT / "docs/governance/roadmap.yaml",
    ):
        values = _top_level_yaml_scalars(path)
        if values.get("current_phase_id", values.get("current_phase")) != builder.RUN_PHASE_ID:
            raise CheckError(f"final governance shape drift: {path.name}.current_phase")
        if values.get("current_task_id", values.get("current_task")) != builder.TASK_ID:
            raise CheckError(f"final governance shape drift: {path.name}.current_task")
        if values.get("current_acceptance_id", values.get("current_acceptance")) != builder.ACCEPTANCE_ID:
            raise CheckError(f"final governance shape drift: {path.name}.current_acceptance")
        for key, expected_value in expected.items():
            if values.get(key) != expected_value:
                raise CheckError(f"final governance shape drift: {path.name}.{key}")
        if path.name == "project.yaml":
            for key, expected_value in {
                "stage_phase_pass_count": 3,
                "stage_task_accepted_count": 9,
                "phase_task_accepted_count": 3,
            }.items():
                if values.get(key) != expected_value:
                    raise CheckError(f"final governance shape drift: {path}.{key}")


def _validate_final_governance(
    *, validation_run_id: str, receipt_head: str, subject_digest: str, receipt_count: int
) -> None:
    _validate_phase_governance_shape()
    shared = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S03",
        "phase_id": builder.RUN_PHASE_ID,
        "roadmap_phase_id": "S03-P3",
        "task_id": builder.TASK_ID,
        "acceptance_id": builder.ACCEPTANCE_ID,
        "run_mode": "IMPLEMENT",
        "work_kind": "PUBLIC_REPOSITORY_SAFETY",
        "fact_level": "EXTRACTED",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "final_validation_status": "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3,
        "stage_task_accepted_count": 9,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3,
        "decision": "CONTINUE_TO_S03_STAGE_REVIEW_ONLY",
        "s03_p3_started": True,
        "s03_p3_acceptance_status": "PASSED",
        "s03_stage_review_entry_allowed": True,
        "s03_stage_review_started": False,
        "s03_stage_review_performed": False,
        "s04_p1_entry_allowed": False,
        "product_implementation_allowed": False,
        "reachable_history_clean": False,
        "history_rewrite_performed": False,
        "final_github_upload_allowed": False,
        "github_upload_performed_by_current_run": False,
        "app_reinstall_performed_by_current_run": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "raw_business_content_read": False,
        "raw_business_interpretation_performed": False,
        "business_execution_performed": False,
        "raw_root_access_count_by_phase": 0,
        "protected_submission_class_count": 5,
        "committable_metadata_class_count": 6,
        "forbidden_public_detail_class_count": 4,
        "owner_plaintext_exception_effective": False,
        "current_submission_gate_pass": True,
        "public_reconstruction_success_count": 0,
        "validation_run_id": validation_run_id,
        "validation_head": receipt_head,
        "validation_subject_sha256": subject_digest,
        "validation_receipt_count": receipt_count,
        "validation_pass_count": receipt_count,
        "validation_failed_count": 0,
        "evidence_ref": FINAL_EVIDENCE_REF,
    }
    event_path = PROJECT_ROOT / "docs/governance/events.jsonl"
    development_path = PROJECT_ROOT / "docs/governance/development_events.jsonl"
    status_path = PROJECT_ROOT / "metadata/stage_status.jsonl"
    event = _last_jsonl_row(event_path)
    development = _last_jsonl_row(development_path)
    status = _last_jsonl_row(status_path)
    event_time = _validated_final_event_time(event.get("event_time"), label=event_path.name)
    if _validated_final_event_time(development.get("event_time"), label=development_path.name) != event_time:
        raise CheckError("final governance event time mismatch: development_events.jsonl")
    if _validated_final_event_time(status.get("event_time"), label=status_path.name) != event_time:
        raise CheckError("final governance event time mismatch: stage_status.jsonl")

    _validate_exact_governance_mapping(
        label=event_path.name,
        actual=event,
        expected={
            **shared,
            "event_id": FINAL_EVENT_ID,
            "event_type": "final_validation",
            "status": FINAL_RECORD_STATUS,
            "event_time": event_time,
        },
    )
    _validate_exact_governance_mapping(
        label=development_path.name,
        actual=development,
        expected={
            **shared,
            "event_id": FINAL_DEVELOPMENT_EVENT_ID,
            "iteration_id": FINAL_ITERATION_ID,
            "event_type": "final_validation",
            "status": FINAL_RECORD_STATUS,
            "summary": FINAL_DEVELOPMENT_SUMMARY,
            "event_time": event_time,
            "result_commit": FINAL_RESULT_COMMIT,
            "files_changed": list(builder.phase_changed_refs()),
        },
    )
    _validate_exact_governance_mapping(
        label=status_path.name,
        actual=status,
        expected={
            **shared,
            "schema_version": "kmfa.stage_status.v1",
            "status_record_id": FINAL_STATUS_RECORD_ID,
            "record_type": "phase_status",
            "status": FINAL_RECORD_STATUS,
            "event_time": event_time,
            "version": FINAL_VERSION,
            "updated_at": event_time,
        },
    )

    assurance_path = PROJECT_ROOT / "docs/governance/ASSURANCE_STATUS.yaml"
    assurance = _top_level_yaml_scalars(assurance_path)
    assurance_expected = {
        "project_id": "KMFA",
        "as_of_event_id": FINAL_DEVELOPMENT_EVENT_ID,
        "source_snapshot_hash": subject_digest,
        "source_base_commit": receipt_head,
        "source_tree_hash": subject_digest,
        "snapshot_event_time": event_time,
        "generator_version": FINAL_ASSURANCE_GENERATOR_VERSION,
        "final_commit_binding": FINAL_ASSURANCE_BINDING,
        "historical_pre_v2_atime_effect_unknown": True,
        "os_atime_observation_scope": "S03_P2_RAW_ROOT_AND_DIRECT_FILES_EACH_COPY_RUN",
    }
    _validate_exact_governance_mapping(
        label=assurance_path.name,
        actual=assurance,
        expected=assurance_expected,
    )
    assurance_header_keys = _assurance_header_keys(assurance_path)
    expected_header_keys = set(assurance_expected) | {"dimensions"}
    if assurance_header_keys != expected_header_keys:
        missing = sorted(expected_header_keys - assurance_header_keys)
        extra = sorted(assurance_header_keys - expected_header_keys)
        raise CheckError(
            "final assurance header schema drift: "
            f"missing={','.join(missing) or '-'} extra={','.join(extra) or '-'}"
        )
    active_parameters, active_formulas, evidence_refs = _assurance_s03p3_semantics(assurance_path)
    if active_parameters != FINAL_ASSURANCE_ACTIVE_PARAMETER_COUNT:
        raise CheckError("final assurance active parameter count drift")
    if active_formulas != FINAL_ASSURANCE_ACTIVE_FORMULA_COUNT:
        raise CheckError("final assurance active formula count drift")
    missing_refs = sorted(FINAL_ASSURANCE_EVIDENCE_REFS - evidence_refs)
    if missing_refs:
        raise CheckError("final assurance S03-P3 evidence refs missing: " + ", ".join(missing_refs))


def _regular_single_link(path: Path, *, private: bool = False) -> None:
    if private:
        try:
            safety._read_regular_single_link(path, expected_mode=0o600)
        except (FileNotFoundError, OSError, safety.SafetyError) as error:
            raise CheckError(f"unsafe private file type/link: {path}") from error
        return
    _public_bytes(path)


def _validate_protection_contract(protection: Mapping[str, Any]) -> None:
    if protection.get("owner_plaintext_exception_effective") is not False:
        raise CheckError("legacy owner plaintext exception remains active")
    if protection.get("current_submission_gate_pass") is not True:
        raise CheckError("current submission protection gate failed")
    repository_scans = protection.get("repository_scans")
    if not isinstance(repository_scans, Mapping):
        raise CheckError("repository scan contract missing")
    for scope in ("head", "index", "worktree"):
        row = repository_scans.get(scope)
        if not isinstance(row, Mapping) or row.get("pass") is not True or row.get("finding_count") != 0:
            raise CheckError(f"repository {scope} scan did not pass")


def _validate_legacy_census_contract(census: Mapping[str, Any]) -> None:
    for key in (
        "current_tree_absolute_local_path_count",
        "current_tree_absolute_local_path_file_count",
        "legacy_schema_review_finding_count",
        "legacy_schema_review_file_count",
    ):
        if census.get(key) != 0:
            raise CheckError(f"legacy current-tree census is not zero: {key}")
    if census.get("reachable_history_clean") is not False:
        raise CheckError("legacy census history claim drift")


def _validate_static_artifacts(*, final_expected: bool) -> dict[str, Any]:
    required = [
        MANIFEST_PATH, TASK_MATRIX_PATH, VALIDATION_RESULTS_PATH, PROTECTION_PATH,
        DUAL_PLANE_PATH, LEGACY_CENSUS_PATH, METADATA_CLASSIFICATION_PATH,
        PROJECT_ROOT / builder.PROTECTION_POLICY_RELATIVE,
        PROJECT_ROOT / builder.METADATA_POLICY_RELATIVE,
        PROJECT_ROOT / builder.REDACTION_AMENDMENT_RELATIVE,
    ]
    for path in required:
        try:
            _regular_single_link(path)
        except CheckError as error:
            raise CheckError(f"required artifact missing or unsafe: {path.relative_to(REPO_ROOT)}") from error
    manifest = _read_json(MANIFEST_PATH)
    expected_status = "PASSED" if final_expected else "PENDING_FINAL_VALIDATION"
    expected_decision = "CONTINUE_TO_S03_STAGE_REVIEW_ONLY" if final_expected else "REMAIN_IN_S03_P3"
    exact = {
        "run_phase_id": builder.RUN_PHASE_ID,
        "task_id": builder.TASK_ID,
        "acceptance_id": builder.ACCEPTANCE_ID,
        "run_id": builder.RUN_ID,
        "phase_base_commit": builder.PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": expected_status,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "decision": expected_decision,
        "s03_stage_review_entry_allowed": final_expected,
        "s03_stage_review_started": False,
        "s04_p1_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "raw_root_access_count_by_phase": 0,
        "protected_submission_class_count": 5,
        "committable_metadata_class_count": 6,
        "forbidden_public_detail_class_count": 4,
        "task_count": 3,
        "task_accepted_count": 3 if final_expected else 0,
        "validation_receipt_count": len(builder.EXPECTED_VALIDATION_RECEIPTS),
        "validation_run_id": None,
    }
    for key, expected in exact.items():
        if key == "validation_run_id" and final_expected:
            if not re.fullmatch(r"[0-9a-f]{32}", str(manifest.get(key))):
                raise CheckError("manifest.validation_run_id drift")
            continue
        if manifest.get(key) != expected:
            raise CheckError(f"manifest.{key} drift")
    if manifest.get("artifact_refs") != builder.ARTIFACT_REFS:
        raise CheckError("manifest artifact refs drift")
    history = manifest.get("history_boundary")
    if not isinstance(history, dict) or history.get("reachable_history_clean") is not False:
        raise CheckError("manifest must not claim reachable Git history is clean")
    if history.get("history_rewrite_performed") is not False:
        raise CheckError("manifest must not claim history rewrite")
    if history.get("final_github_upload_allowed_by_this_phase") is not False:
        raise CheckError("S03-P3 must not allow final GitHub upload")

    tasks = _read_json_rows(TASK_MATRIX_PATH)
    if [row.get("task_id") for row in tasks] != [task["task_id"] for task in builder.TASKS]:
        raise CheckError("task matrix IDs drift")
    for row in tasks:
        if row.get("acceptance_status") != expected_status:
            raise CheckError("task acceptance status drift")

    protection = _read_json(PROTECTION_PATH)
    _validate_protection_contract(protection)

    census = _read_json(LEGACY_CENSUS_PATH)
    _validate_legacy_census_contract(census)

    metadata_rows = _read_csv_rows(METADATA_CLASSIFICATION_PATH)
    expected_metadata_refs = sorted(
        ref for ref in manifest.get("phase_changed_refs", []) if ref.startswith("KMFA/metadata/")
    )
    if [row.get("metadata_ref") for row in metadata_rows] != expected_metadata_refs:
        raise CheckError("phase metadata classification coverage drift")
    for row in metadata_rows:
        if row.get("metadata_class") not in safety.COMMITTABLE_METADATA_CLASSES:
            raise CheckError("phase metadata class is outside the six-class contract")
        if row.get("structured_public_detail_finding_count") != "0" or row.get("secret_finding_count") != "0":
            raise CheckError("phase metadata classification contains a public-safety finding")
        if row.get("classification_policy") != "EXPLICIT_SIX_CLASS_FAIL_CLOSED":
            raise CheckError("phase metadata classification policy drift")
    expected_live_metadata_rows = builder._phase_metadata_rows(manifest.get("phase_changed_refs", []))
    if metadata_rows != expected_live_metadata_rows:
        raise CheckError("phase metadata classification is not an exact live rebuild")

    dual = _read_json(DUAL_PLANE_PATH)
    if dual.get("run_id") != builder.RUN_ID or dual.get("raw_root_access_count_by_phase") != 0:
        raise CheckError("dual-plane run/raw boundary drift")
    public = dual.get("public_projection_summary")
    if not isinstance(public, dict):
        raise CheckError("dual-plane public projection summary missing")
    if public.get("run_id") != builder.RUN_ID:
        raise CheckError("dual-plane shared run identity drift")
    if public.get("plaintext_or_raw_private_values_public") is not False:
        raise CheckError("dual-plane public artifact exposes plaintext/raw private values")
    if public.get("keyed_opaque_token_values_bound_in_public_projection") is not True:
        raise CheckError("dual-plane public artifact does not bind keyed opaque tokens")
    if public.get("opaque_token_count") != 5:
        raise CheckError("dual-plane public token aggregate drift")
    public_projection = dual.get("public_projection")
    if not isinstance(public_projection, dict):
        raise CheckError("tracked public projection missing")
    safety.validate_public_metadata_envelope(public_projection)
    if public_projection.get("run_id") != builder.RUN_ID:
        raise CheckError("tracked public projection run identity drift")
    verification = dual.get("verification", {})
    if verification.get("declared_attack_model_pass") is not True:
        raise CheckError("dual-plane declared attack model did not pass")
    if verification.get("information_theoretic_non_reconstruction_claimed") is not False:
        raise CheckError("dual-plane overclaims non-reconstruction")
    return manifest


def _validate_live_controls() -> None:
    ignore = safety.verify_gitignore_contract()
    if not ignore["pass"]:
        raise CheckError("live gitignore contract failed")
    for scope in ("head", "index", "worktree"):
        _, findings = safety.scan_repository(scope=scope)
        if findings:
            raise CheckError(f"live {scope} scan found {len(findings)} blocking findings")


def _validate_private_evidence(max_age_seconds: float) -> None:
    summary = safety.private_evidence_summary(
        PROJECT_ROOT / builder.PRIVATE_ROOT_RELATIVE,
        run_id=builder.RUN_ID,
    )
    if summary.get("private_evidence_gitignored") is not True or summary.get("private_evidence_tracked") is not False:
        raise CheckError("private dual-plane evidence boundary failed")
    receipt = PROJECT_ROOT / builder.PRIVATE_ROOT_RELATIVE / "synthetic_private_dual_plane_receipt.json"
    _regular_single_link(receipt, private=True)
    if max_age_seconds > 0 and time.time() - receipt.stat().st_mtime > max_age_seconds:
        raise CheckError("private dual-plane evidence is stale")
    public_projection = summary.pop("public_projection")
    verification = summary.pop("verification")
    tracked = _read_json(DUAL_PLANE_PATH)
    if tracked.get("same_run_evidence_summary") != summary:
        raise CheckError("tracked private-evidence aggregate does not bind live private evidence")
    if tracked.get("public_projection") != public_projection:
        raise CheckError("tracked public projection does not bind live private evidence")
    if tracked.get("public_projection_summary") != builder._public_projection_summary(public_projection):
        raise CheckError("tracked public projection summary does not bind live private evidence")
    if tracked.get("verification") != verification:
        raise CheckError("tracked dual-plane verification does not bind live private evidence")


def _validate_receipts(manifest: Mapping[str, Any], *, clean_head: str | None) -> str:
    _regular_single_link(PRIVATE_RECEIPTS_PATH, private=True)
    rows = _read_json_rows(PRIVATE_RECEIPTS_PATH, private=True)
    if len(rows) != len(builder.EXPECTED_VALIDATION_RECEIPTS):
        raise CheckError("validation receipt count drift")
    if [row.get("validation_id") for row in rows] != list(builder.EXPECTED_VALIDATION_RECEIPTS):
        raise CheckError("validation receipt order/IDs drift")
    run_ids = {row.get("run_id") for row in rows}
    subjects = {row.get("validation_subject_sha256") for row in rows}
    heads = {row.get("head_before") for row in rows} | {row.get("head_after") for row in rows}
    if len(run_ids) != 1 or not re.fullmatch(r"[0-9a-f]{32}", str(next(iter(run_ids)))):
        raise CheckError("validation receipts do not share one valid run ID")
    if len(subjects) != 1 or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(next(iter(subjects)))):
        raise CheckError("validation receipts do not share one valid subject")
    if len(heads) != 1 or not re.fullmatch(r"[0-9a-f]{40}", str(next(iter(heads)))):
        raise CheckError("validation receipts do not share one committed HEAD")
    receipt_head = str(next(iter(heads)))
    required_keys = {
        "schema_version", "run_id", "validation_id", "command", "result", "exit_code",
        "execution_sequence", "started_at", "ended_at", "duration_ms", "phase_base_commit",
        "head_before", "head_after", "validation_subject_sha256", "stdout_sha256", "stderr_sha256",
    }
    for sequence, (validation_id, command) in enumerate(builder.EXPECTED_VALIDATION_RECEIPTS.items(), start=1):
        row = rows[sequence - 1]
        if set(row) != required_keys:
            raise CheckError(f"validation receipt fields drifted: {validation_id}")
        if row.get("schema_version") != builder.VALIDATION_RECEIPT_SCHEMA_VERSION:
            raise CheckError(f"validation receipt schema drifted: {validation_id}")
        if row.get("execution_sequence") != sequence:
            raise CheckError(f"validation receipt sequence drifted: {validation_id}")
        if row.get("command") != command or row.get("result") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"validation receipt failed or drifted: {validation_id}")
        if row.get("phase_base_commit") != builder.PHASE_BASE_COMMIT:
            raise CheckError("validation receipt phase base drift")
        if not isinstance(row.get("duration_ms"), int) or row["duration_ms"] < 0:
            raise CheckError(f"validation receipt duration drifted: {validation_id}")
        try:
            started = datetime.fromisoformat(str(row.get("started_at")))
            ended = datetime.fromisoformat(str(row.get("ended_at")))
        except ValueError as error:
            raise CheckError(f"validation receipt timestamp drifted: {validation_id}") from error
        if started.tzinfo is None or ended.tzinfo is None or ended < started:
            raise CheckError(f"validation receipt time ordering drifted: {validation_id}")
        for digest_field in ("stdout_sha256", "stderr_sha256"):
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get(digest_field))):
                raise CheckError(f"validation receipt digest drifted: {validation_id}.{digest_field}")
    receipt_run_id = str(next(iter(run_ids)))
    if manifest.get("validation_run_id") != receipt_run_id:
        raise CheckError("manifest validation run ID does not bind receipts")
    if clean_head is not None:
        expected_receipt_head = _git(["rev-parse", f"{clean_head}^1"])
        if receipt_head != expected_receipt_head:
            raise CheckError("receipt HEAD must be the final commit's immediate first parent")
    expected_subject = builder.validation_subject_sha256(
        changed_refs=manifest.get("phase_changed_refs", []),
        git_ref=receipt_head,
    )
    if subjects != {expected_subject} or manifest.get("validation_subject_sha256") != expected_subject:
        raise CheckError("validation subject binding drift")
    return receipt_head


def _validate_clean_commit(manifest: Mapping[str, Any], receipt_head: str) -> None:
    if _git(["status", "--porcelain"]):
        raise CheckError("worktree must be clean for post-commit validation")
    head = _git(["rev-parse", "HEAD"])
    parent = _git(["rev-parse", f"{head}^1"])
    if receipt_head != parent:
        raise CheckError("final validation evidence must be a distinct second commit")
    if _git(["rev-list", "--count", f"{builder.PHASE_BASE_COMMIT}..{head}"]) != "2":
        raise CheckError("S03-P3 must close with exactly implementation and evidence commits")
    _git(["merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, head])
    phase_changed = set(
        _git(["diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..{head}", "--", "KMFA"]).splitlines()
    )
    recorded = set(manifest.get("phase_changed_refs", []))
    if phase_changed != recorded:
        raise CheckError("committed phase changed refs do not exactly match manifest")
    escaped = sorted(ref for ref in phase_changed if not builder._allowed_phase_ref(ref))
    if escaped:
        raise CheckError("committed phase diff escaped allowlist: " + ", ".join(escaped))
    post_changed = set(_git(["diff", "--name-only", f"{receipt_head}..{head}", "--", "KMFA"]).splitlines())
    if not post_changed:
        raise CheckError("final validation evidence commit is empty")
    if not post_changed <= POST_VALIDATION_ALLOWED_REFS:
        raise CheckError("post-validation commit changed non-mutable refs: " + ", ".join(sorted(post_changed - POST_VALIDATION_ALLOWED_REFS)))


def validate(
    *,
    skip_validation_receipts: bool,
    skip_exact_rebuild: bool,
    skip_clean_commit: bool,
    pre_receipt_final_governance: bool,
    max_private_evidence_age_seconds: float,
) -> None:
    final_expected = not skip_validation_receipts
    manifest = _validate_static_artifacts(final_expected=final_expected)
    _validate_live_controls()
    _validate_private_evidence(max_private_evidence_age_seconds)
    if not skip_exact_rebuild:
        builder.run(check=True, final_validation=final_expected)
    if pre_receipt_final_governance or final_expected:
        _validate_phase_governance_shape()
    receipt_head = None
    current_head = _git(["rev-parse", "HEAD"]) if not skip_clean_commit else None
    if not skip_validation_receipts:
        receipt_head = _validate_receipts(manifest, clean_head=current_head)
        _validate_final_governance(
            validation_run_id=str(manifest["validation_run_id"]),
            receipt_head=receipt_head,
            subject_digest=str(manifest["validation_subject_sha256"]),
            receipt_count=len(builder.EXPECTED_VALIDATION_RECEIPTS),
        )
    if not skip_clean_commit:
        if skip_validation_receipts or receipt_head is None:
            raise CheckError("clean commit validation requires final receipts")
        _validate_clean_commit(manifest, receipt_head)
    if pre_receipt_final_governance and not skip_validation_receipts:
        raise CheckError("pre-receipt mode cannot require final receipts")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-exact-rebuild", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--pre-receipt-final-governance", action="store_true")
    parser.add_argument("--private-evidence-only", action="store_true")
    parser.add_argument(
        "--max-private-evidence-age-seconds",
        type=float,
        default=0.0,
        help="optional same-run freshness gate; 0 keeps cryptographic/content validation reusable",
    )
    args = parser.parse_args(argv)
    try:
        if args.private_evidence_only:
            _validate_private_evidence(args.max_private_evidence_age_seconds)
        else:
            validate(
                skip_validation_receipts=args.skip_validation_receipts,
                skip_exact_rebuild=args.skip_exact_rebuild,
                skip_clean_commit=args.skip_clean_commit,
                pre_receipt_final_governance=args.pre_receipt_final_governance,
                max_private_evidence_age_seconds=args.max_private_evidence_age_seconds,
            )
    except (CheckError, builder.BuildError, safety.SafetyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: KMFA v1.5 S03-P3 public repository safety")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
