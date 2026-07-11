#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S14-P3 policy-evidence outputs."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any, Iterator

from KMFA.tools import v014_s14_p3_post_remediation_policy_evidence_plan as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".csv", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "raw_sha256",
    "raw_root_private",
    "member_name_private",
    "member_sha256",
    "sheet_name_private",
    "matched_terms_private",
    "preview_rows_private",
    "probe_fingerprint",
    "classification_fingerprint",
    "field_plaintext",
    "header_plaintext",
    "business_amount",
    "tax_rate_value",
    "invoice_number",
    "tax_declaration_number",
    "project_name",
    "customer_name",
    "original_filename",
}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} contains a non-object row")
            rows.append(value)
    return rows


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _walk_floats(value: Any) -> Iterator[float]:
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_floats(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_floats(item)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(result.stderr.strip())
    return result.stdout.strip()


def _git_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path)], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return bool(_git_output(["ls-files", "--", str(path)]))


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require("/Users/linzezhang/Downloads" not in text, f"local raw path leaked: {path}", errors)
    _require("KMFA_MetaData" not in text, f"raw root token leaked: {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token: {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        _require(not list(_walk_floats(value)), f"float found: {path}", errors)
        for key in _walk_keys(value):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key}: {path}", errors)


def _public_artifact_paths() -> tuple[Path, ...]:
    return (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.DIRECTORIES_PATH,
        phase.GAPS_PATH,
        phase.RISKS_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_DIRECTORIES_PATH,
        phase.METADATA_GAPS_PATH,
        phase.METADATA_RISKS_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_artifact_paths():
        _check_public_file(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}

    manifest = _read_json(phase.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    expected_identity = {
        "project_id": "KMFA",
        "stage_id": "S14",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S14-P3",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
    }
    for key, expected in expected_identity.items():
        _require(manifest.get(key) == expected, f"manifest {key} mismatch", errors)
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    expected_summary = {
        "s14_p2_post_remediation_dependency_validated": True,
        "policy_program_count": 5,
        "evidence_directory_definition_count": 5,
        "required_evidence_category_total_count": 23,
        "unique_public_source_ref_count": 4,
        "program_source_association_count": 12,
        "unique_structure_candidate_count": 20,
        "program_structure_candidate_association_count": 60,
        "authoritative_evidence_bound_program_count": 0,
        "evidence_complete_program_count": 0,
        "evidence_gap_count": 5,
        "risk_tip_count": 5,
        "formal_policy_qualification_conclusion_count": 0,
        "policy_score_count": 0,
        "policy_application_submission_count": 0,
        "subsidy_application_count": 0,
        "identified_business_item_count": 0,
        "public_business_amount_count": 0,
        "raw_source_file_count": 5,
        "private_xlsx_container_count": 48,
        "private_parseable_xlsx_count": 25,
        "private_unparseable_xlsx_count": 23,
        "private_parseable_sheet_count": 4198,
        "private_policy_lexical_candidate_sheet_count_by_program": {
            "small_tech_company": 0,
            "high_tech_enterprise": 1,
            "specialized_refined_innovative": 0,
            "little_giant": 0,
            "r_and_d_expense": 3830,
        },
        "private_unique_policy_lexical_candidate_sheet_count": 3830,
        "private_multi_program_candidate_sheet_count": 1,
        "private_lexical_candidate_covered_program_count": 2,
        "private_probe_roundtrip_mismatch_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "browser_status": "PASS",
        "browser_viewport_check_count": 2,
        "program_interaction_check_count": 10,
        "dependency_link_http_check_count": 4,
        "dependency_navigation_check_count": 4,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "stage14_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    expected_programs = {row["program_id"]: row for row in phase.PROGRAM_SPECS}
    directories = manifest.get("policy_evidence_directories", [])
    _require(len(directories) == 5, "directory count mismatch", errors)
    _require({row.get("program_id") for row in directories} == set(expected_programs), "directory ids mismatch", errors)
    _require(sum(row.get("required_evidence_category_count", 0) for row in directories) == 23, "category total mismatch", errors)
    for row in directories:
        spec = expected_programs.get(row.get("program_id"), {})
        _require(row.get("visible_name") == spec.get("visible_name"), "directory visible name mismatch", errors)
        _require(
            row.get("required_evidence_categories") == list(spec.get("required_evidence_categories", ())),
            f"directory categories mismatch: {row.get('program_id')}",
            errors,
        )
        _require(row.get("directory_definition_registered") is True, "directory not registered", errors)
        _require(row.get("directory_status") == "definition_registered_authoritative_evidence_unbound", "directory status mismatch", errors)
        for key in (
            "authoritative_evidence_bound",
            "evidence_complete",
            "formal_policy_qualification_conclusion_allowed",
            "policy_score_allowed",
            "policy_application_submission_allowed",
            "subsidy_application_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "contains_business_amounts",
            "contains_field_or_header_plaintext",
        ):
            _require(row.get(key) is False, f"directory {key} mismatch", errors)

    gaps = manifest.get("policy_evidence_gaps", [])
    _require(len(gaps) == 5, "gap count mismatch", errors)
    _require({row.get("program_id") for row in gaps} == set(expected_programs), "gap ids mismatch", errors)
    for row in gaps:
        _require(row.get("gap_status") == "authoritative_evidence_not_bound", "gap status mismatch", errors)
        _require(row.get("evidence_gap_only") is True, "non-gap output found", errors)
        for key in (
            "authoritative_evidence_bound",
            "evidence_complete",
            "formal_policy_qualification_conclusion_allowed",
            "policy_score_allowed",
            "policy_application_submission_allowed",
            "subsidy_application_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "contains_business_amounts",
        ):
            _require(row.get(key) is False, f"gap {key} mismatch", errors)

    risks = manifest.get("policy_risk_tips", [])
    _require(len(risks) == 5, "risk count mismatch", errors)
    _require({row.get("program_id") for row in risks} == set(expected_programs), "risk ids mismatch", errors)
    for row in risks:
        _require(row.get("risk_tip_only") is True, "formal conclusion found in risk output", errors)
        _require(
            row.get("required_control") == "manual_authoritative_policy_evidence_review_before_any_conclusion",
            "risk control mismatch",
            errors,
        )
        for key in (
            "formal_policy_qualification_conclusion_allowed",
            "policy_application_submission_allowed",
            "subsidy_application_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            _require(row.get(key) is False, f"risk {key} mismatch", errors)

    quarantine = manifest.get("historical_quarantine", {})
    for key in (
        "legacy_manifest_validated_as_historical_fixture",
        "legacy_pending_twelve_quarantined",
        "legacy_five_gap_statuses_quarantined",
        "legacy_five_risk_statuses_quarantined",
    ):
        _require(quarantine.get(key) is True, f"historical quarantine missing: {key}", errors)
    _require(quarantine.get("legacy_s14_p3_dynamic_state_is_authoritative") is False, "legacy state authoritative", errors)
    _require(quarantine.get("current_authoritative_evidence_bound_program_count") == 0, "current binding invented", errors)
    _require(quarantine.get("current_formal_policy_qualification_conclusion_count") == 0, "current conclusion invented", errors)

    matrix = manifest.get("acceptance_matrix", {})
    _require(matrix.get("fail_count") == 0, "acceptance matrix failed", errors)
    _require(matrix.get("pass_count") == 12, "acceptance matrix pass count mismatch", errors)
    expected_mirrors = (
        (phase.SUMMARY_PATH, summary),
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.DIRECTORIES_PATH, {"schema_version": "kmfa.v014.s14_p3_directories.v1", "directories": directories}),
        (phase.METADATA_DIRECTORIES_PATH, {"schema_version": "kmfa.v014.s14_p3_directories.v1", "directories": directories}),
        (phase.GAPS_PATH, {"schema_version": "kmfa.v014.s14_p3_gaps.v1", "gaps": gaps}),
        (phase.METADATA_GAPS_PATH, {"schema_version": "kmfa.v014.s14_p3_gaps.v1", "gaps": gaps}),
        (phase.RISKS_PATH, {"schema_version": "kmfa.v014.s14_p3_risks.v1", "risks": risks}),
        (phase.METADATA_RISKS_PATH, {"schema_version": "kmfa.v014.s14_p3_risks.v1", "risks": risks}),
        (phase.MATRIX_PATH, matrix),
        (phase.METADATA_MATRIX_PATH, matrix),
    )
    for path, expected in expected_mirrors:
        _require(_read_json(path) == expected, f"public mirror drift: {path}", errors)
    _require(_read_json(phase.METADATA_GO_NO_GO_PATH) == _read_json(phase.GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    return manifest


def _validate_dependency(errors: list[str]) -> None:
    try:
        dependency = phase._load_dependency()
    except Exception as exc:
        errors.append(f"current S14-P2 dependency failed: {exc}")
        return
    summary = dependency.get("summary", {})
    _require(dependency.get("next_phase") == "S14-P3", "S14-P2 routing drift", errors)
    _require(summary.get("source_lane_count") == 3, "S14-P2 lane drift", errors)
    _require(summary.get("identified_business_item_count") == 0, "S14-P2 business item drift", errors)
    _require(summary.get("current_report_grade") == "D", "S14-P2 grade drift", errors)
    _require(summary.get("decision") == "NO_GO", "S14-P2 decision drift", errors)


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "政策证据工作台",
        "科小",
        "高新",
        "专精特新",
        "小巨人",
        "研发费用",
        "证据缺口",
        "风险",
        "Q4 / D",
        "NO_GO",
        "5 / 5",
        "2 / 5",
        "0 / 5",
        "正式资格结论",
        "不得据此输出政策资格、评分、申报或补贴申请结论",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    _require(text.count("data-program-button=") == 5, "HTML program button count mismatch", errors)
    _require(text.count("data-program-panel=") == 5, "HTML program panel count mismatch", errors)
    _require(text.count("data-dependency-link=") == 8, "HTML dependency link count mismatch", errors)
    _require("table{min-width:0;table-layout:fixed}" in text, "mobile table layout guard missing", errors)
    _require("word-break:break-word" in text, "mobile table wrapping guard missing", errors)
    _require("Stage 14 三个 phase 均已完成" in text, "current Stage 14 status missing", errors)
    _require("本 phase 仅完成 S14-P3" not in text, "stale S14-P3 status remains", errors)
    for link_id, (href, _) in phase.DEPENDENCY_LINKS.items():
        _require(href in text, f"HTML href missing: {link_id}", errors)
        _require((phase.HTML_PATH.parent / href).resolve().is_file(), f"HTML target missing: {link_id}", errors)
    _require("gradient(" not in text, "gradient found", errors)
    _require("pending_reconciliation_count" not in text, "legacy pending leaked", errors)
    _require("资格结论允许" not in text and "申报允许" not in text, "policy permission leaked", errors)


def _validate_boundaries(manifest: dict[str, Any], errors: list[str]) -> None:
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate mismatch", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary mismatch", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety mismatch", errors)
    boundaries = manifest.get("phase_boundaries", {})
    for key in (
        "s14_p1_post_remediation_validated",
        "s14_p2_post_remediation_validated",
        "s14_p3_performed",
    ):
        _require(boundaries.get(key) is True, f"required boundary missing: {key}", errors)
    for key, value in boundaries.items():
        if key not in {
            "s14_p1_post_remediation_validated",
            "s14_p2_post_remediation_validated",
            "s14_p3_performed",
        }:
            _require(value is False, f"review or operation boundary opened: {key}", errors)


def _phase_is_current(version_matrix: str) -> bool:
    return f'current_phase: "{phase.PHASE_ID}"' in version_matrix


def _validate_governance(errors: list[str]) -> None:
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("evidence_gap_count") == 5, "event gap count mismatch", errors)
        _require(events[0].get("risk_tip_count") == 5, "event risk count mismatch", errors)
        _require(events[0].get("formal_policy_qualification_conclusion_count") == 0, "event conclusion mismatch", errors)
        _require(events[0].get("identified_business_item_count") == 0, "event business item mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "event upload mismatch", errors)
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
        _require(statuses[0].get("decision") == "NO_GO", "stage decision mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)
        _require(tasks[0].get("task_count") == 3, "task count mismatch", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "policy_program_count == 5",
        "evidence_directory_definition_count == 5",
        "required_evidence_category_total_count == 23",
        "authoritative_evidence_bound_program_count == 0",
        "evidence_complete_program_count == 0",
        "evidence_gap_count == 5",
        "risk_tip_count == 5",
        "formal_policy_qualification_conclusion_count == 0",
        "private_probe_roundtrip_mismatch_count == 0",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)

    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"formula ref missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"parameter ref missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    manifest = _read_json(phase.MANIFEST_PATH)
    browser = manifest.get("browser_review", {})
    audit = str(browser.get("current_pass_count"))
    expected = {
        "PARAM-KMFA-1758": (
            "5;5;23;4;12;20;60;0;0;5;5;0;0;0;0;0;0;5;48;25;23;4198;0;1;0;0;3830;3830;1;2;0;"
            "3;9;2;1;Q4;D;NO_GO"
        ),
        "PARAM-KMFA-1759": f"6;54;54;0;0;1;{audit};{audit};0;0;2;10;4;4;0;0",
        "PARAM-KMFA-1760": (
            "true;true;true;true;true;true;true;true;true;false;false;false;false;false;false;false;"
            "false;false;false;false;false;false;NO_GO"
        ),
        "PARAM-KMFA-1761": (
            "directory_definitions_registered_authoritative_evidence_unbound;5;5;0;0;0;0;0;"
            "false;false;false;false;D;NO_GO"
        ),
    }
    for parameter_id, expected_value in expected.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    if _phase_is_current(version_matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 Stage 14 整体复审" in handoff, "HANDOFF review routing missing", errors)
        _require("不得执行 S15" in handoff, "HANDOFF later-stage boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S14-P3" in agents and "Stage 14 整体复审" in agents, "AGENTS scope drift", errors)

    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability and phase.ACCEPTANCE_ID in traceability, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S14-P3 修补后政策证据"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count mismatch: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count mismatch: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"audit failure: {path}", errors)
    _require(sum(row.get("status") == "WARN" for row in rows) == 0, f"audit warning: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PROBE_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p2.PRIVATE_RAW_AFTER_PATH)
        helper = phase.p2.p1.s13_review.p1.s12_review.p1.s11_project
        current = helper._raw_snapshot("validate_v014_s14_p3_post_remediation_policy_evidence_plan")
        normalize = helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S14-P2 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        probe = _read_json(phase.PRIVATE_PROBE_PATH)
        expected_probe = {
            "raw_file_count": 5,
            "private_xlsx_container_count": 48,
            "private_parseable_xlsx_count": 25,
            "private_unparseable_xlsx_count": 23,
            "private_parseable_sheet_count": 4198,
            "private_policy_lexical_candidate_sheet_count_by_program": {
                "small_tech_company": 0,
                "high_tech_enterprise": 1,
                "specialized_refined_innovative": 0,
                "little_giant": 0,
                "r_and_d_expense": 3830,
            },
            "private_unique_policy_lexical_candidate_sheet_count": 3830,
            "private_multi_program_candidate_sheet_count": 1,
            "private_lexical_candidate_covered_program_count": 2,
            "private_probe_roundtrip_mismatch_count": 0,
            "authoritative_evidence_bound_program_count": 0,
            "evidence_complete_program_count": 0,
        }
        for key, expected in expected_probe.items():
            _require(probe.get(key) == expected, f"private probe {key} mismatch", errors)
        _require(len(probe.get("candidate_sheets_private", [])) == 3830, "private candidate record count mismatch", errors)
        report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
        for token in (
            "唯一候选 / 跨目录候选 / 覆盖目录：3830 / 1 / 2",
            "二次探针指纹不一致：0",
            "权威证据绑定 / 证据完整目录：0 / 0",
            "全中文最终差异报告",
        ):
            _require(token in report, f"private report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_ignored(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    if phase.MANIFEST_PATH.is_file():
        current_rows = _read_json(phase.MANIFEST_PATH).get("browser_review", {}).get("current_control_row_count", -1)
        _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 1, current_rows)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_counts = {
            "viewport_checks": 2,
            "program_interaction_checks": 10,
            "dependency_link_http_checks": 4,
            "dependency_navigation_checks": 4,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} mismatch", errors)
        for key in (
            "program_interaction_checks",
            "dependency_link_http_checks",
            "dependency_navigation_checks",
        ):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("marker_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"policy_evidence_{mode}.png"
        _require(path.is_file(), f"screenshot missing: {path}", errors)
        _require(_git_ignored(path), f"screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s14_p3_post_remediation_policy_evidence_plan(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependency(errors)
    _validate_html(errors)
    if manifest:
        _validate_boundaries(manifest, errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_candidate_probe",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation {key} mismatch", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s14_p3_post_remediation_policy_evidence_plan(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S14-P3 strict validation PASS: "
        f"directories={summary['evidence_directory_definition_count']} "
        f"lexical={summary['private_unique_policy_lexical_candidate_sheet_count']} "
        f"bound={summary['authoritative_evidence_bound_program_count']} "
        f"conclusions={summary['formal_policy_qualification_conclusion_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
