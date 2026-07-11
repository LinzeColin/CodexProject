#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S16-P1 subcontract/procurement evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s16_p1_post_remediation_subcontract_procurement as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "sheet_name_private",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "invoice_number",
    "supplier_name_plaintext",
    "project_name_plaintext",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "member_name_private",
    "sheet_name_private",
    "matched_terms_private",
    "preview_rows_private",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "invoice_number",
    "supplier_name_plaintext",
    "project_name_plaintext",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
)


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"non-object JSONL row: {path}")
            rows.append(value)
    return rows


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _git_ignored(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _walk(value: Any, key: str = "") -> list[tuple[str, Any]]:
    rows = [(key, value)]
    if isinstance(value, dict):
        for child_key, child in value.items():
            rows.extend(_walk(child, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_walk(child, key))
    return rows


def _public_paths() -> tuple[Path, ...]:
    return (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.SOURCE_LANES_PATH,
        phase.MATCHING_CONTRACT_PATH,
        phase.UNALLOCATED_CONTRACT_PATH,
        phase.DETECTION_RULES_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.HTML_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_SOURCE_LANES_PATH,
        phase.METADATA_MATCHING_CONTRACT_PATH,
        phase.METADATA_UNALLOCATED_CONTRACT_PATH,
        phase.METADATA_DETECTION_RULES_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _scan_public(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"public evidence missing: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    data = path.read_bytes()
    _require(b"\x00" not in data, f"binary public evidence: {path}", errors)
    if b"\x00" in data:
        return
    text = data.decode("utf-8")
    for token in FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public text in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix == ".json":
        payload = json.loads(text)
        for key, value in _walk(payload):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
            if isinstance(value, float):
                errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "stage15_post_remediation_review_dependency_validated": True,
        "source_lane_count": 5,
        "private_candidate_covered_lane_count": 5,
        "private_candidate_sheet_count_by_lane": {
            "invoice": 672,
            "payment_application": 391,
            "procurement_order": 296,
            "project_attribution": 5,
            "subcontract_contract": 283,
        },
        "raw_source_file_count": 5,
        "private_xlsx_container_count": 48,
        "private_parseable_xlsx_count": 25,
        "private_unparseable_xlsx_count": 23,
        "private_parseable_sheet_count": 4198,
        "private_unique_candidate_sheet_count": 1335,
        "private_candidate_lane_association_count": 1647,
        "private_multi_lane_candidate_sheet_count": 274,
        "private_probe_roundtrip_mismatch_count": 0,
        "processed_candidate_sheet_count": 1335,
        "processed_candidate_lane_association_count": 1647,
        "processed_private_structure_alignment_exact": True,
        "project_matching_contract_count": 1,
        "project_matching_component_count": 6,
        "authoritative_row_binding_count": 0,
        "authoritative_value_binding_count": 0,
        "materialized_transaction_record_count": 0,
        "project_match_record_count": 0,
        "unallocated_cost_pool_item_count": 0,
        "detection_rule_count": 4,
        "anomaly_candidate_count": 0,
        "duplicate_payment_candidate_count": 0,
        "payment_without_contract_candidate_count": 0,
        "cross_project_cost_candidate_count": 0,
        "public_business_value_count": 0,
        "workbench_html_count": 1,
        "browser_status": "PASS",
        "baseline_html_control_row_count": 54,
        "baseline_html_pass_count": 54,
        "current_html_control_row_count": 13,
        "current_html_pass_count": 13,
        "browser_viewport_check_count": 2,
        "lane_interaction_check_count": 10,
        "rule_interaction_check_count": 8,
        "dependency_link_http_check_count": 4,
        "dependency_navigation_check_count": 4,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s16_p1_performed": True,
        "s16_p2_performed": False,
        "s16_p3_performed": False,
        "stage16_review_performed": False,
        "procurement_execution_performed": False,
        "payment_approval_performed": False,
        "payment_execution_performed": False,
        "bank_operation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "business_execution_performed": False,
    }


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _scan_public(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    lanes_document = _read_json(phase.SOURCE_LANES_PATH)
    matching = _read_json(phase.MATCHING_CONTRACT_PATH)
    pool = _read_json(phase.UNALLOCATED_CONTRACT_PATH)
    rules_document = _read_json(phase.DETECTION_RULES_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)

    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase identity drift", errors)
    _require(manifest.get("roadmap_phase_id") == "S16-P1", "roadmap phase drift", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task drift", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance drift", errors)
    _require(manifest.get("version") == phase.VERSION, "version drift", errors)
    _require(manifest.get("status") == phase.STATUS, "status drift", errors)
    _require(manifest.get("decision") == "NO_GO", "decision drift", errors)
    _require(manifest.get("formula_id") == phase.FORMULA_ID, "formula drift", errors)
    _require(manifest.get("parameter_ids") == list(phase.PARAMETER_IDS), "parameter drift", errors)
    _require(manifest.get("model_registry_key") == phase.MODEL_REGISTRY_KEY, "model drift", errors)
    _require(manifest.get("summary") == summary, "summary mirror drift", errors)
    _require(manifest.get("source_lanes") == lanes_document.get("source_lanes"), "lane mirror drift", errors)
    _require(manifest.get("project_matching_contract") == matching, "matching mirror drift", errors)
    _require(manifest.get("unallocated_cost_pool_contract") == pool, "pool mirror drift", errors)
    _require(manifest.get("detection_rules") == rules_document.get("rules"), "rule mirror drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "matrix mirror drift", errors)
    _require(manifest.get("go_no_go") == go_no_go, "go/no-go mirror drift", errors)
    for key, expected in _expected_summary().items():
        _require(summary.get(key) == expected, f"summary {key} drift", errors)

    lanes = manifest.get("source_lanes", [])
    _require(len(lanes) == 5, "source lane count drift", errors)
    _require({row.get("lane_id") for row in lanes} == set(phase.LANE_IDS), "source lane identities drift", errors)
    expected_counts = summary.get("private_candidate_sheet_count_by_lane", {})
    for row in lanes:
        lane_id = row.get("lane_id")
        _require(row.get("candidate_sheet_count") == expected_counts.get(lane_id), f"lane count drift: {lane_id}", errors)
        _require(row.get("authoritative_row_binding_count") == 0, f"lane row binding drift: {lane_id}", errors)
        _require(row.get("materialized_transaction_record_count") == 0, f"lane transaction drift: {lane_id}", errors)
        _require(row.get("manual_review_required") is True, f"lane review drift: {lane_id}", errors)

    _require(matching.get("component_count") == 6, "matching component count drift", errors)
    _require(matching.get("candidate_materialization_allowed") is False, "matching materialization opened", errors)
    _require(matching.get("project_match_record_count") == 0, "project matches materialized", errors)
    _require(pool.get("materialized_pool_item_count") == 0, "pool items materialized", errors)
    _require(pool.get("forced_zero_amount_allowed") is False, "forced-zero policy opened", errors)
    rules = rules_document.get("rules", [])
    _require(len(rules) == 4, "rule count drift", errors)
    _require({row.get("rule_id") for row in rules} == {row["rule_id"] for row in phase.DETECTION_SPECS}, "rule ids drift", errors)
    _require(all(row.get("materialized_candidate_count") == 0 for row in rules), "anomaly candidate materialized", errors)
    _require(all(row.get("manual_review_required") is True for row in rules), "rule review boundary drift", errors)

    _require(manifest.get("stage15_post_remediation_review_dependency_validated") is True, "dependency flag drift", errors)
    _require(manifest.get("historical_s16_p1_fixture_validated") is True, "legacy fixture not validated", errors)
    _require(manifest.get("historical_s16_p1_dynamic_state_is_authoritative") is False, "legacy state active", errors)
    _require(manifest.get("historical_five_project_matches_quarantined") is True, "legacy matches not quarantined", errors)
    _require(manifest.get("historical_two_unallocated_items_quarantined") is True, "legacy pool not quarantined", errors)
    _require(manifest.get("historical_four_anomaly_candidates_quarantined") is True, "legacy anomalies not quarantined", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("raw_boundary") == phase._raw_boundary(), "raw boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(matrix.get("check_count") == 13 and matrix.get("check_pass_count") == 13, "acceptance matrix failed", errors)
    _require(matrix.get("check_fail_count") == 0, "acceptance failures detected", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            if key == "structure_candidate_review_allowed":
                _require(value is True, "structure review unexpectedly blocked", errors)
            else:
                _require(value is False, f"go/no-go boundary opened: {key}", errors)
    _require(manifest.get("next_phase") == "S16-P2", "next phase drift", errors)

    for path, expected in (
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_SOURCE_LANES_PATH, lanes_document),
        (phase.METADATA_MATCHING_CONTRACT_PATH, matching),
        (phase.METADATA_UNALLOCATED_CONTRACT_PATH, pool),
        (phase.METADATA_DETECTION_RULES_PATH, rules_document),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    try:
        current = phase._load_dependency()
        legacy = phase._load_legacy_fixture()
        contract = phase._load_contract()
    except Exception as exc:
        errors.append(f"dependency validation failed: {exc}")
        return
    _require(current["summary"]["stage15_review_performed"] is True, "Stage 15 review dependency drift", errors)
    _require(current["summary"]["s16_p1_performed"] is False, "Stage 15 dependency already includes S16-P1", errors)
    _require(legacy["summary"]["project_match_count"] == 5, "legacy matches fixture drift", errors)
    _require(legacy["summary"]["unallocated_cost_pool_count"] == 2, "legacy pool fixture drift", errors)
    _require(legacy["summary"]["anomaly_candidate_count"] == 4, "legacy anomaly fixture drift", errors)
    _require(contract.get("five_current_structure_lanes_locked") is True, "taskpack contract drift", errors)


def _validate_html(errors: list[str]) -> None:
    path = phase.HTML_PATH
    _require(path.is_file(), "workbench HTML missing", errors)
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for token in (
        "外协采购归集工作台",
        "Q4 / D",
        "NO_GO",
        "Stage 16 三个 phase 与整体复审均已完成",
        "S17 仅可在下一 run work",
        "table{min-width:0;table-layout:fixed}",
        "word-break:break-word",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    _require(text.count("data-lane-button=") == 5, "lane button count drift", errors)
    _require(text.count("data-lane-panel=") == 5, "lane panel count drift", errors)
    _require(text.count("data-rule-button=") == 4, "rule button count drift", errors)
    _require(text.count("data-rule-panel=") == 4, "rule panel count drift", errors)
    _require(text.count("data-dependency-link=") == 4, "dependency link count drift", errors)
    _require(text.count("data-stage-link=") == 2, "stage link count drift", errors)
    for link_id, target, _marker in phase.DEPENDENCY_SPECS:
        href = phase._relative_href(target)
        _require(f'data-dependency-link="{link_id}" href="{href}"' in text, f"dependency href drift: {link_id}", errors)
        _require((path.parent / href).resolve() == target.resolve(), f"dependency target drift: {link_id}", errors)
        _require(target.is_file(), f"dependency target missing: {link_id}", errors)
    for link_id, target in (
        ("project-lifecycle", Path("KMFA/stage_artifacts/V014_S16_P2_POST_REMEDIATION_PROJECT_STATUS_LIFECYCLE/exports/html/project_status_lifecycle_workbench.html")),
        ("customer-analysis", Path("KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/exports/html/customer_business_analysis_workbench.html")),
    ):
        matches = re.findall(rf'data-stage-link="{link_id}" href="([^"]+)"', text)
        _require(len(matches) == 1, f"stage href drift: {link_id}", errors)
        if matches:
            _require((path.parent / matches[0]).resolve() == target.resolve(), f"stage target drift: {link_id}", errors)
            _require(target.is_file(), f"stage target missing: {link_id}", errors)


def _expected_parameters(manifest: dict[str, Any]) -> dict[str, str]:
    summary = manifest["summary"]
    return {
        "PARAM-KMFA-1780": "5;5;5;48;25;23;4198;1335;1647;274;0;283;296;391;672;5",
        "PARAM-KMFA-1781": "1;6;0;0;0;0;0;4;0;0;0;0;0;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1782": (
            f"6;54;54;0;0;1;{summary['current_html_control_row_count']};{summary['current_html_pass_count']};0;0;"
            "2;10;8;4;4;0;0;5;true;true;true;true;true;false;false;false;false;false;false;false;false;false;false;false;false;Q4;D;NO_GO"
        ),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == phase.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == phase.STATUS, f"governance status drift: {path}", errors)
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    if events:
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list drift", errors)
        _require(events[0].get("project_match_record_count") == 0, "event project match drift", errors)
        _require(events[0].get("anomaly_candidate_count") == 0, "event anomaly drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "source_lane_count == 5",
        "private_candidate_covered_lane_count == 5",
        "private_probe_roundtrip_mismatch_count == 0",
        "processed_private_structure_alignment_exact == true",
        "authoritative_row_binding_count == 0",
        "project_match_record_count == 0",
        "detection_rule_count == 4",
        "anomaly_candidate_count == 0",
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
    for parameter_id, expected in _expected_parameters(manifest).items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    current = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S16-P2" in handoff, "HANDOFF S16-P2 route missing", errors)
        _require("不得执行 S16-P3" in handoff, "HANDOFF later phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S16-P1" in agents and "S16-P2" in agents, "AGENTS scope drift", errors)
    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    if current:
        _require(f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance, "assurance time drift", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S16-P1 外协采购归集"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, expected_files: int, expected_rows: int, errors: list[str]) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count drift: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count drift: {path}", errors)
    _require(all(row.get("status") == "PASS" for row in rows), f"audit non-pass row: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(manifest: dict[str, Any], errors: list[str], require_browser: bool) -> None:
    paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PROBE_PATH,
        phase.PRIVATE_DIFFERENCE_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s15_review.PRIVATE_RAW_AFTER_PATH)
        raw_helper = phase.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
        current = raw_helper._raw_snapshot("validate_v014_s16_p1_post_remediation_subcontract_procurement")
        normalize = raw_helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-Stage15 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        probe = _read_json(phase.PRIVATE_PROBE_PATH)
        for key, expected in _expected_summary().items():
            if key.startswith("private_") or key in {
                "raw_source_file_count",
                "authoritative_row_binding_count",
                "authoritative_value_binding_count",
                "materialized_transaction_record_count",
            }:
                _require(probe.get(key) == expected, f"private probe {key} drift", errors)
        candidates = probe.get("candidate_sheets_private", [])
        _require(len(candidates) == 1335, "private candidate row count drift", errors)
        identities = {
            (row.get("raw_index"), row.get("member_index"), row.get("sheet_index"), tuple(row.get("matched_lanes", [])))
            for row in candidates
        }
        _require(len(identities) == 1335, "private candidate identities not unique", errors)
        _require(all(row.get("authoritative_row_binding_proven") is False for row in candidates), "private row binding invented", errors)
        _require(all(row.get("transaction_materialization_allowed") is False for row in candidates), "private transaction materialization opened", errors)
        counts = {
            lane_id: sum(lane_id in row.get("matched_lanes", []) for row in candidates)
            for lane_id in phase.LANE_IDS
        }
        _require(counts == manifest["summary"]["private_candidate_sheet_count_by_lane"], "private/public lane count mismatch", errors)
        report = phase.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("processed/private 结构计数：exact match", "raw review 前后、跨 Stage 15 review 和当前快照：exact match", "全中文最终差异报告"):
            _require(token in report, f"private difference report token missing: {token}", errors)
    if not require_browser:
        return
    for path, files, rows in (
        (phase.PRIVATE_BASELINE_AUDIT_PATH, 6, 54),
        (phase.PRIVATE_CURRENT_AUDIT_PATH, 1, 13),
    ):
        _require(_git_ignored(path), f"audit not ignored: {path}", errors)
        _require(not _git_tracked(path), f"audit tracked: {path}", errors)
        _read_audit(path, files, rows, errors)
    _require(phase.PRIVATE_BROWSER_PATH.is_file(), "browser evidence missing", errors)
    _require(_git_ignored(phase.PRIVATE_BROWSER_PATH), "browser evidence not ignored", errors)
    _require(not _git_tracked(phase.PRIVATE_BROWSER_PATH), "browser evidence tracked", errors)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status drift", errors)
        for key, count in (
            ("viewport_checks", 2),
            ("lane_interaction_checks", 10),
            ("rule_interaction_checks", 8),
            ("dependency_link_http_checks", 4),
            ("dependency_navigation_checks", 4),
        ):
            _require(len(browser.get(key, [])) == count, f"browser {key} count drift", errors)
        for key in ("lane_interaction_checks", "rule_interaction_checks", "dependency_link_http_checks", "dependency_navigation_checks"):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("marker_visible") is True
                and row.get("quality_boundary_visible") is True
                and row.get("phase_complete_visible") is True
                and row.get("next_run_boundary_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"subcontract_procurement_{mode}.png"
        _require(path.is_file(), f"screenshot missing: {path}", errors)
        _require(_git_ignored(path), f"screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width drift: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s16_p1_post_remediation_subcontract_procurement(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependencies(errors)
    _validate_html(errors)
    if manifest:
        _validate_governance(manifest, errors)
    if require_private_evidence and manifest:
        _validate_private(manifest, errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_alignment",
            "processed_private_structure_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation {key} drift", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s16_p1_post_remediation_subcontract_procurement(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S16-P1 strict validation PASS: "
        f"lanes={summary['source_lane_count']} candidates={summary['private_unique_candidate_sheet_count']} "
        f"matches={summary['project_match_record_count']} anomalies={summary['anomaly_candidate_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
