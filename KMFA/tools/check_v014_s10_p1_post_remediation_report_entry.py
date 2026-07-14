#!/usr/bin/env python3
"""Validate the KMFA v0.1.4 S10-P1 post-remediation report entry."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s10_p1_post_remediation_report_entry as phase
from KMFA.tools.check_v014_s09_post_remediation_stage_review import (
    validate_v014_s09_post_remediation_stage_review,
)
from KMFA.tools.check_v014_s10_p1_report_templates import (
    validate_v014_s10_p1_report_templates,
)
from KMFA.tools.report_templates import FORBIDDEN_VISIBLE_TEXT_RE


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
    re.compile(r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"),
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
    entries_document = payloads.get("entries", {})
    go_no_go = payloads.get("go_no_go", {})

    _require(manifest.get("schema_version") == "kmfa.v014.s10_p1.post_remediation_report_entry_manifest.v1", "manifest schema mismatch", errors)
    _require(manifest.get("stage_id") == "S10", "stage id mismatch", errors)
    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase id mismatch", errors)
    _require(manifest.get("roadmap_phase_id") == "S10-P1", "roadmap phase mismatch", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task id mismatch", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance id mismatch", errors)
    _require(manifest.get("status") == phase.STATUS, "status mismatch", errors)
    _require(manifest.get("decision") == "NO_GO", "decision mismatch", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(entries_document.get("report_entries") == manifest.get("report_entries"), "entry artifact drift", errors)

    expected_summary = {
        "report_template_count": 2,
        "management_section_count": 11,
        "project_cost_section_count": 4,
        "business_overview_section_count": 7,
        "cost_category_count": 9,
        "human_readable_reconciliation_count": 12,
        "queue_closed_or_excluded_count": 69,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "forced_zero_materialization_count": 0,
        "missing_cash_value_materialized_as_zero_count": 0,
        "authority_system_overwrite_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "formal_report_count": 0,
        "export_artifact_count": 0,
        "raw_source_file_count": 5,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    for key in ("raw_snapshot_exact_match", "raw_cross_phase_snapshot_exact_match"):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)

    entries = manifest.get("report_entries", [])
    _require(len(entries) == 2, "report entry count mismatch", errors)
    expected_entries = (
        ("project_cost_special_report", "项目成本专题报告", ["经营摘要", "项目毛利", "成本结构", "风险事项"]),
        ("business_overview_report", "经营总览报告", ["经营总览", "收入", "开票", "回款", "现金", "项目", "税务"]),
    )
    for entry, (entry_id, title, sections) in zip(entries, expected_entries):
        _require(entry.get("entry_id") == entry_id, f"entry id mismatch: {entry_id}", errors)
        _require(entry.get("visible_title") == title, f"entry title mismatch: {entry_id}", errors)
        _require(entry.get("visible_sections") == sections, f"entry sections mismatch: {entry_id}", errors)
        visible_text = json.dumps(
            {
                "title": entry.get("visible_title"),
                "sections": entry.get("visible_sections"),
                "summary": entry.get("visible_management_summary"),
                "status": entry.get("visible_trust_status"),
            },
            ensure_ascii=False,
        )
        _require(FORBIDDEN_VISIBLE_TEXT_RE.search(visible_text) is None, f"technical title leaked: {entry_id}", errors)
        for token in ("Q4", "D", "NO_GO", "未放行"):
            _require(token in visible_text, f"visible trust token missing: {entry_id}:{token}", errors)
        for key in (
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "business_values_included",
            "internal_technical_title_visible",
            "missing_value_rendered_as_zero",
            "authority_value_overwrite_allowed",
        ):
            _require(entry.get(key) is False, f"entry boundary must be false: {entry_id}:{key}", errors)

    trust = manifest.get("trust_entry", {})
    _require(trust.get("current_data_quality_grade") == "Q4", "trust Q4 mismatch", errors)
    _require(trust.get("current_report_grade") == "D", "trust D mismatch", errors)
    _require(trust.get("decision") == "NO_GO", "trust decision mismatch", errors)
    _require(trust.get("inherited_from_stage9_post_remediation_review") is True, "trust inheritance missing", errors)
    _require(trust.get("grade_calculation_performed_by_this_phase") is False, "S10-P2 calculation leaked", errors)
    _require(trust.get("grade_override_allowed") is False, "grade override must be false", errors)

    release = manifest.get("release_gate", {})
    for key in (
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "delivery_allowed",
        "report_runtime_performed",
        "report_export_performed",
    ):
        _require(release.get(key) is False, f"release gate {key} must be false", errors)

    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries.get("s10_p1_performed") is True, "S10-P1 must be true", errors)
    for key in (
        "s10_p2_performed",
        "s10_p3_performed",
        "stage10_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)

    raw = manifest.get("raw_boundary", {})
    _require(raw.get("raw_read_authorized") is True, "raw authorization missing", errors)
    _require(raw.get("raw_snapshot_validation_performed") is True, "raw snapshot validation missing", errors)
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
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety flag changed", errors)
    dependencies = manifest.get("dependencies", {})
    _require(dependencies.get("stage9_post_remediation_review_validated") is True, "Stage 9 dependency missing", errors)
    _require(dependencies.get("historical_s10_p1_structure_validated") is True, "S10-P1 structure missing", errors)
    _require(dependencies.get("historical_dynamic_state_reused") is False, "historical dynamic state reused", errors)
    _require(dependencies.get("current_stage9_state_authoritative") is True, "current Stage 9 state not authoritative", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go mismatch", errors)
    _require(go_no_go.get("formal_report_allowed") is False, "go/no-go formal report must be false", errors)
    _require(go_no_go.get("github_upload_performed") is False, "go/no-go upload must be false", errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def _load_public_payloads(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.ENTRIES_PATH,
        phase.GO_NO_GO_PATH,
        phase.COMPLETION_PATH,
        phase.MANAGEMENT_PREVIEW_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_ENTRIES_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)
    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    entries = _read_json(phase.ENTRIES_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(entries == _read_json(phase.METADATA_ENTRIES_PATH), "entries mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    preview = phase.MANAGEMENT_PREVIEW_PATH.read_text(encoding="utf-8")
    _require(FORBIDDEN_VISIBLE_TEXT_RE.search(preview) is None, "technical title leaked into management preview", errors)
    return {"summary": summary, "manifest": manifest, "entries": entries, "go_no_go": go_no_go}


def _validate_dependencies(manifest: dict[str, Any], errors: list[str]) -> None:
    s09 = validate_v014_s09_post_remediation_stage_review(require_private_evidence=False)
    historical = validate_v014_s10_p1_report_templates()
    for key in (
        "cost_category_count",
        "human_readable_reconciliation_count",
        "queue_closed_or_excluded_count",
        "open_final_difference_accepted_count",
        "nonzero_delta_reconciliation_count",
        "zero_delta_reconciliation_count",
        "incomplete_reconciliation_count",
        "forced_zero_materialization_count",
        "authority_system_overwrite_allowed_count",
        "current_data_quality_grade",
        "current_report_grade",
        "release_permission",
    ):
        _require(manifest["summary"].get(key) == s09.get(key), f"Stage 9 dependency drift: {key}", errors)
    _require(historical.get("template_count") == 2, "historical template count drift", errors)
    _require(historical.get("section_count") == 11, "historical section count drift", errors)


def _validate_governance(errors: list[str]) -> None:
    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    stage_rows = _read_jsonl(phase.STAGE_STATUS_PATH)
    task_rows = _read_jsonl(phase.TASK_STATUS_PATH)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in events) == 1, "development event missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in stage_rows) == 1, "stage status missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in task_rows) == 1, "task status missing or duplicated", errors)
    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    parameter_path = Path("KMFA/docs/governance/parameter_registry.csv")
    with parameter_path.open(encoding="utf-8", newline="") as handle:
        parameter_rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    _require("missing_cash_zero_count == 0" in formula_text, "formula missing cash-zero control drift", errors)
    _require("grade_calculation_performed == false" in formula_text, "formula grade boundary drift", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model record missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in parameter_rows, f"parameter record missing: {parameter_id}", errors)
    expected_values = {
        "PARAM-KMFA-1696": "2;11;4;7;9;12;69;3;9;2;1;0;0;0;5;Q4;D;NO_GO",
        "PARAM-KMFA-1697": "true;true;true;true;true;true;true;false;false;false;false;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1698": "true;true;true;true;true;true;false;false;false;false;false;false;false;false;false;false;false",
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
    _require("S10-P2" in handoff, "HANDOFF next phase drift", errors)


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
    prior = _read_json(phase.s09_phase.PRIVATE_RAW_AFTER_PATH)
    current = phase._raw_snapshot("validate_v014_s10_p1_post_remediation_report_entry")
    normalize = phase._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
    _require(normalize(after) == normalize(current), "raw current mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count mismatch", errors)


def validate_v014_s10_p1_post_remediation_report_entry(
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
        manifest = validate_v014_s10_p1_post_remediation_report_entry(
            require_private_evidence=args.require_private_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S10-P1 post-remediation report entry "
        f"templates={summary['report_template_count']} sections={summary['management_section_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open_final={summary['open_final_difference_accepted_count']} decision={manifest['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
