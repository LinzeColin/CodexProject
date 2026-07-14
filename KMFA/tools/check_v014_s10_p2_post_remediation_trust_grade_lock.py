#!/usr/bin/env python3
"""Validate the KMFA v0.1.4 S10-P2 post-remediation trust grade lock."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s10_p2_post_remediation_trust_grade_lock as phase
from KMFA.tools.check_v014_s10_p2_report_trust_grade import (
    validate_v014_s10_p2_report_trust_grade,
)


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "business_value",
    "row_value",
    "cell_value",
    "sheet_name",
    "member_name",
    "original_filename",
    "file_hash",
    "field_key",
    "field_label",
    "source_header_text",
    "project_name_plaintext",
    "customer_name_plaintext",
    "authoritative_value_cents",
    "system_value_cents",
}
RAW_ROOT_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)
VISIBLE_TECHNICAL_TOKENS = (
    "validator",
    "manifest",
    "metadata",
    "source_ref",
    "private_ref",
    "schema",
    "phase",
    "stage",
    "S10-P2",
)
REQUIRED_HARD_BLOCKS = (
    "zero_delta_failed",
    "unresolved_critical_difference",
    "incomplete_reconciliation",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "full_business_value_consistency_not_verified",
)
VERSION_FIELDS = (
    "report_record_version",
    "report_entry_version",
    "template_version",
    "formula_version",
    "mapping_version",
    "field_mapping_version",
    "grade_policy_version",
    "release_gate_version",
)


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} must contain objects")
            rows.append(value)
    return rows


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local Downloads path leaked in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        for key in _walk_keys(value):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key!r} in {path}", errors)


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", path.as_posix()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def validate_payloads(payloads: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    summary = payloads.get("summary", {})
    manifest = payloads.get("manifest", {})
    rules_document = payloads.get("rules", {})
    records_document = payloads.get("records", {})
    go_no_go = payloads.get("go_no_go", {})

    _require(
        manifest.get("schema_version") == "kmfa.v014.s10_p2.post_remediation_trust_grade_manifest.v1",
        "manifest schema mismatch",
        errors,
    )
    _require(manifest.get("stage_id") == "S10", "stage id mismatch", errors)
    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase id mismatch", errors)
    _require(manifest.get("roadmap_phase_id") == "S10-P2", "roadmap phase mismatch", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task id mismatch", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance id mismatch", errors)
    _require(manifest.get("status") == phase.STATUS, "status mismatch", errors)
    _require(manifest.get("decision") == "NO_GO", "decision mismatch", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("grade_rules") == rules_document, "rules artifact drift", errors)
    _require(
        manifest.get("grade_records") == records_document.get("report_grade_records"),
        "record artifact drift",
        errors,
    )

    expected_summary = {
        "report_template_count": 2,
        "report_grade_record_count": 2,
        "grade_distribution": {"D": 2},
        "current_data_quality_grade": "Q4",
        "maximum_report_grade_before_hard_blocks": "B",
        "current_report_grade": "D",
        "grade_recalculation_performed_by_this_phase": True,
        "automatic_grade_promotion_performed": False,
        "record_version_binding_count": 2,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "full_trusted_report_allowed_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "export_artifact_count": 0,
        "raw_source_file_count": 5,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    for key in ("raw_snapshot_exact_match", "raw_cross_phase_snapshot_exact_match"):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    expected_block_counts = {block: 2 for block in REQUIRED_HARD_BLOCKS}
    _require(summary.get("hard_block_counts") == expected_block_counts, "hard block counts mismatch", errors)

    rules = manifest.get("grade_rules", {})
    _require(
        rules.get("driver_dimensions") == ["data_quality", "difference_status", "human_confirmation", "timeliness"],
        "grade dimensions mismatch",
        errors,
    )
    report_grades = rules.get("report_grades", [])
    _require([row.get("grade") for row in report_grades] == ["A", "B", "C", "D"], "grade order mismatch", errors)
    if len(report_grades) == 4:
        _require(report_grades[0].get("minimum_quality_grade") == "Q5", "A minimum quality mismatch", errors)
        _require(report_grades[0].get("zero_delta_required") is True, "A zero-delta rule mismatch", errors)
        _require(report_grades[1].get("minimum_quality_grade") == "Q4", "B minimum quality mismatch", errors)
        _require(report_grades[1].get("limitations_required") is True, "B limitation rule mismatch", errors)
        _require(report_grades[2].get("preview_only") is True, "C preview rule mismatch", errors)
        _require(report_grades[3].get("release_permission") == "blocked_decision_use", "D release rule mismatch", errors)

    inputs = manifest.get("grade_inputs", {})
    expected_inputs = {
        "data_quality_grade": "Q4",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "incomplete_reconciliation_count": 1,
        "zero_delta_passed": False,
        "human_confirmation_status": "partial_not_release_sufficient",
        "timeliness_status": "current_no_stale_signal",
        "stale_input_detected": False,
        "lineage_full_check_complete": False,
        "full_business_value_consistency_verified": False,
    }
    for key, expected in expected_inputs.items():
        _require(inputs.get(key) == expected, f"grade input {key} mismatch", errors)

    bindings = manifest.get("version_binding_requirements", {})
    expected_bindings = {
        "report_record_version": phase.REPORT_RECORD_VERSION,
        "formula_version": phase.FORMULA_VERSION,
        "mapping_version": phase.MAPPING_VERSION,
        "field_mapping_version": phase.FIELD_MAPPING_VERSION,
        "grade_policy_version": phase.GRADE_POLICY_VERSION,
        "release_gate_version": phase.RELEASE_GATE_VERSION,
        "record_version_binding_count": 2,
    }
    for key, expected in expected_bindings.items():
        _require(bindings.get(key) == expected, f"version binding {key} mismatch", errors)
    for key in VERSION_FIELDS:
        _require(bool(bindings.get(key)), f"version binding missing: {key}", errors)

    records = manifest.get("grade_records", [])
    _require(len(records) == 2, "grade record count mismatch", errors)
    _require(len({record.get("report_entry_id") for record in records}) == 2, "grade record entry ids not unique", errors)
    for record in records:
        _require(record.get("computed_report_grade") == "D", "record grade must be D", errors)
        _require(record.get("maximum_report_grade_before_hard_blocks") == "B", "record ceiling must be B", errors)
        _require(record.get("release_permission") == "blocked_decision_use", "record release permission mismatch", errors)
        _require(record.get("hard_blocks") == list(REQUIRED_HARD_BLOCKS), "record hard blocks mismatch", errors)
        for key in VERSION_FIELDS:
            _require(record.get(key) == bindings.get(key), f"record version drift: {key}", errors)
        for key in (
            "complete_trusted_report_display_allowed",
            "full_trusted_report_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "s10_p3_export_allowed",
        ):
            _require(record.get(key) is False, f"record gate {key} must be false", errors)
        safety = record.get("public_repo_safety", {})
        _require(safety.get("aggregate_only") is True, "record must be aggregate-only", errors)
        _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "record safety drift", errors)

    explanation_text = json.dumps(manifest.get("management_explanation", {}), ensure_ascii=False)
    for token in VISIBLE_TECHNICAL_TOKENS:
        _require(token not in explanation_text, f"technical token visible to management: {token}", errors)
    for token in ("D级", "未放行", "关键现金数据缺失", "九项非零差异", "一项比较未完成"):
        _require(token in explanation_text, f"management explanation missing: {token}", errors)

    release = manifest.get("release_gate", {})
    for key in (
        "complete_trusted_report_display_allowed",
        "full_trusted_report_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "delivery_allowed",
        "s10_p3_export_allowed",
    ):
        _require(release.get(key) is False, f"release gate {key} must be false", errors)

    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries.get("s10_p1_performed") is True, "S10-P1 dependency boundary missing", errors)
    _require(boundaries.get("s10_p2_performed") is True, "S10-P2 must be true", errors)
    for key in (
        "s10_p3_performed",
        "stage10_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)

    raw = manifest.get("raw_boundary", {})
    _require(raw.get("raw_read_authorized") is True, "raw authorization missing", errors)
    _require(raw.get("raw_snapshot_validation_performed") is True, "raw validation missing", errors)
    for key in (
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
        "raw_mutation_performed",
    ):
        _require(raw.get(key) is False, f"raw boundary {key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence must be aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)

    dependencies = manifest.get("dependencies", {})
    _require(dependencies.get("s10_p1_post_remediation_entry_validated") is True, "current S10-P1 dependency missing", errors)
    _require(dependencies.get("historical_s10_p2_rule_framework_validated") is True, "historical framework missing", errors)
    _require(dependencies.get("historical_dynamic_state_reused") is False, "historical dynamic state reused", errors)
    _require(dependencies.get("current_s10_p1_state_authoritative") is True, "current S10-P1 not authoritative", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("current_report_grade") == "D", "go/no-go grade mismatch", errors)
    _require(go_no_go.get("blocking_reason_codes") == list(REQUIRED_HARD_BLOCKS), "go/no-go blockers mismatch", errors)
    _require(go_no_go.get("formal_report_allowed") is False, "go/no-go formal report must be false", errors)
    _require(go_no_go.get("s10_p3_export_allowed") is False, "go/no-go S10-P3 export must be false", errors)
    _require(go_no_go.get("github_upload_performed") is False, "go/no-go upload must be false", errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def _load_public_payloads(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.RULES_PATH,
        phase.RECORDS_PATH,
        phase.GO_NO_GO_PATH,
        phase.COMPLETION_PATH,
        phase.MANAGEMENT_EXPLANATION_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_RULES_PATH,
        phase.METADATA_RECORDS_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)
    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    rules = _read_json(phase.RULES_PATH)
    records = _read_json(phase.RECORDS_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(rules == _read_json(phase.METADATA_RULES_PATH), "rules mirror drift", errors)
    _require(records == _read_json(phase.METADATA_RECORDS_PATH), "records mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    management = phase.MANAGEMENT_EXPLANATION_PATH.read_text(encoding="utf-8")
    for token in VISIBLE_TECHNICAL_TOKENS:
        _require(token not in management, f"technical token leaked into management explanation: {token}", errors)
    return {"summary": summary, "manifest": manifest, "rules": rules, "records": records, "go_no_go": go_no_go}


def _validate_dependencies(manifest: dict[str, Any], errors: list[str]) -> None:
    current = phase.validate_s10_p1_dependency()
    validate_v014_s10_p2_report_trust_grade()
    historical = _read_json(phase.HISTORICAL_S10_P2_MANIFEST_PATH)
    expected_from_current = {
        "report_template_count": "report_template_count",
        "open_final_difference_accepted_count": "open_final_difference_accepted_count",
        "nonzero_delta_reconciliation_count": "nonzero_delta_reconciliation_count",
        "zero_delta_reconciliation_count": "zero_delta_reconciliation_count",
        "incomplete_reconciliation_count": "incomplete_reconciliation_count",
        "raw_source_file_count": "raw_source_file_count",
    }
    for local_key, source_key in expected_from_current.items():
        _require(
            manifest.get("summary", {}).get(local_key) == current.get("summary", {}).get(source_key),
            f"current S10-P1 dependency drift: {local_key}",
            errors,
        )
    policy = historical.get("report_trust_grade_policy", {})
    _require(policy.get("allowed_report_grades") == ["A", "B", "C", "D"], "historical grade framework drift", errors)
    _require(
        policy.get("grade_driver_dimensions") == ["data_quality", "difference_status", "human_confirmation", "timeliness"],
        "historical grade dimensions drift",
        errors,
    )
    _require(
        manifest.get("version_binding_requirements", {}).get("template_version") == policy.get("template_version"),
        "historical template version drift",
        errors,
    )


def _validate_governance(errors: list[str]) -> None:
    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    stage_rows = _read_jsonl(phase.STAGE_STATUS_PATH)
    task_rows = _read_jsonl(phase.TASK_STATUS_PATH)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in events) == 1, "development event missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in stage_rows) == 1, "stage status missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in task_rows) == 1, "task status missing or duplicated", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    metadata_model_text = Path("KMFA/metadata/model_registry.yaml").read_text(encoding="utf-8")
    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameter_rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in ("Q4", "maximum_grade_before_hard_blocks = B", "hard_blocks > 0 => final_grade = D"):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model registry record missing", errors)
    _require(phase.MODEL_REGISTRY_KEY in metadata_model_text, "metadata model registry record missing", errors)
    expected_values = {
        "PARAM-KMFA-1699": "2;Q4;B;D;3;9;2;1;12;0;0;0;5;NO_GO",
        "PARAM-KMFA-1700": "true;false;false;partial_not_release_sufficient;current_no_stale_signal;false;false;false;NO_GO",
        "PARAM-KMFA-1701": "true;true;false;false;false;false;false;true;false;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected in expected_values.items():
        row = parameter_rows.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)

    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{phase.PHASE_ID}"' in version_matrix, "VERSION_MATRIX current phase drift", errors)
    handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
    _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
    _require("S10-P3" in handoff, "HANDOFF next phase drift", errors)


def _validate_private_evidence(errors: list[str]) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_VALIDATION_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if any(not path.is_file() for path in private_paths):
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.p1_phase.PRIVATE_RAW_AFTER_PATH)
    current = phase._raw_snapshot("validate_v014_s10_p2_post_remediation_trust_grade_lock")
    normalize = phase._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
    _require(normalize(after) == normalize(current), "raw current mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count mismatch", errors)


def validate_v014_s10_p2_post_remediation_trust_grade_lock(
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    payloads = _load_public_payloads(errors)
    try:
        manifest = validate_payloads(payloads)
    except ValidationError as exc:
        errors.append(str(exc))
        manifest = payloads.get("manifest", {})
    _validate_dependencies(manifest, errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private_evidence(errors)
    if require_final_evidence:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in ("focused_tests", "strict_validator", "governance_and_safety_scans"):
            _require(validation.get(key) == "PASS", f"final validation status mismatch: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate_v014_s10_p2_post_remediation_trust_grade_lock(
            require_private_evidence=args.require_private_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S10-P2 post-remediation trust grade lock "
        f"records={summary['report_grade_record_count']} quality={summary['current_data_quality_grade']} "
        f"ceiling={summary['maximum_report_grade_before_hard_blocks']} grade={summary['current_report_grade']} "
        f"hard_blocks={summary['hard_block_count']} decision={manifest['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
