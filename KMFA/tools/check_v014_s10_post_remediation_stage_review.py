#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 10 post-remediation review evidence."""

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

from KMFA.tools import v014_s10_post_remediation_stage_review as phase
from KMFA.tools.check_v013_s10_stage_review import validate_v013_s10_stage_review
from KMFA.tools.check_v014_s10_p3_post_remediation_restricted_export import (
    _load_public_payloads as load_p3_public_payloads,
    validate_payloads as validate_p3_payloads,
)
from KMFA.tools.check_v014_s10_stage_review import validate_v014_s10_stage_review


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "business_value",
    "amount_cents",
    "amount_yuan",
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
CSV_HEADERS = [
    "报告名称",
    "报告等级",
    "发布状态",
    "最终接受未决数",
    "非零差异数",
    "零差异数",
    "未完成比较数",
    "使用限制",
]


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
    rows = []
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
        for key in _walk_keys(json.loads(text)):
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


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "review_scope": phase.REVIEW_SCOPE,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "report_template_count": 2,
        "management_section_count": 11,
        "report_grade_record_count": 2,
        "report_export_record_count": 2,
        "html_restricted_preview_count": 2,
        "csv_restricted_appendix_count": 2,
        "excel_compatible_csv_download_count": 2,
        "browser_viewport_check_count": 4,
        "byte_exact_download_count": 2,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "committed_pdf_file_count": 0,
        "committed_excel_workbook_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "fixed_review_finding_count": 6,
        "open_review_finding_count": 0,
        "raw_source_file_count": 5,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending count leaked into summary", errors)
    _require(
        summary.get("phase_results") == {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"},
        "phase results mismatch",
        errors,
    )
    for key in ("raw_snapshot_exact_match", "raw_cross_phase_snapshot_exact_match"):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    for key in ("s11_p1_performed", "github_upload_performed", "app_reinstall_performed", "business_execution_performed"):
        _require(summary.get(key) is False, f"summary {key} must be false", errors)

    findings = manifest.get("review_findings", [])
    _require(len(findings) == 6, "review finding count mismatch", errors)
    _require(all(item.get("status") == "fixed" for item in findings), "review finding remains open", errors)
    for key in (
        "historical_review_dependency_validated",
        "historical_v013_review_dependency_validated",
        "historical_legacy_review_dependency_validated",
        "frozen_phase_semantics_validated",
        "cross_format_restriction_propagation_verified",
    ):
        _require(manifest.get(key) is True, f"manifest {key} must be true", errors)
    for key in (
        "historical_review_dynamic_state_is_authoritative",
        "stale_b_grade_or_pending_twelve_detected",
        "restricted_preview_mislabeled_as_formal_report",
    ):
        _require(manifest.get(key) is False, f"manifest {key} must be false", errors)
    boundaries = manifest.get("review_boundaries", {})
    _require(boundaries.get("stage10_review_performed") is True, "review boundary missing", errors)
    for key in (
        "s11_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence must be aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)
    _require(matrix.get("check_count") == 25, "matrix count mismatch", errors)
    _require(matrix.get("check_pass_count") == 25, "matrix pass count mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix contains failures", errors)
    _require(all(item.get("passed") is True for item in matrix.get("checks", [])), "matrix row failed", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("restricted_preview_exports_validated") is True, "restricted exports not validated", errors)
    for key in ("formal_report_allowed", "business_decision_basis_allowed", "github_upload_performed"):
        _require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)
    return manifest


def _validate_cross_format(errors: list[str]) -> None:
    for entry_id, html_path in phase.p3_phase.HTML_PATHS.items():
        text = html_path.read_text(encoding="utf-8")
        for token in (
            "D级（未放行）",
            "仅供内部复核",
            "关键现金数据缺失",
            "九项非零差异",
            "一项比较未完成",
            "PDF导出未执行",
        ):
            _require(token in text, f"HTML restriction missing: {entry_id}:{token}", errors)
        for token in ("B级", "完整可信报告", "正式报告已生成"):
            _require(token not in text, f"HTML stale/formal token found: {entry_id}:{token}", errors)

    for entry_id, csv_path in phase.p3_phase.CSV_PATHS.items():
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        _require(len(rows) == 2, f"CSV row count mismatch: {entry_id}", errors)
        if len(rows) == 2:
            _require(rows[0] == CSV_HEADERS, f"CSV headers mismatch: {entry_id}", errors)
            _require(rows[1][1:] == ["D级", "未放行", "3", "9", "2", "1", "仅供内部复核，不作为正式经营决策依据"], f"CSV restriction mismatch: {entry_id}", errors)


def _validate_dependencies(errors: list[str]) -> None:
    p1 = phase.p2_phase.validate_s10_p1_dependency()
    p2 = phase.p3_phase.validate_s10_p2_dependency()
    p3_errors: list[str] = []
    p3 = validate_p3_payloads(load_p3_public_payloads(p3_errors))
    _require(not p3_errors, f"S10-P3 public payload errors: {p3_errors}", errors)
    _require(p1.get("summary", {}).get("report_template_count") == 2, "S10-P1 frozen semantics failed", errors)
    _require(p2.get("summary", {}).get("current_report_grade") == "D", "S10-P2 frozen semantics failed", errors)
    _require(p3.get("summary", {}).get("report_export_record_count") == 2, "S10-P3 frozen semantics failed", errors)
    old = validate_v014_s10_stage_review()
    v013 = validate_v013_s10_stage_review()
    legacy = phase.validate_legacy_review()
    _require(old.get("stage_id") == "S10", "historical v0.1.4 review failed", errors)
    _require(v013.get("stage_id") == "S10", "historical v0.1.3 review failed", errors)
    _require(bool(legacy), "legacy Stage 10 review failed", errors)


def _validate_governance(errors: list[str]) -> None:
    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    statuses = _read_jsonl(phase.STAGE_STATUS_PATH)
    tasks = _read_jsonl(phase.TASK_STATUS_PATH)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in events) == 1, "development event missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in statuses) == 1, "stage status missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in tasks) == 1, "task status missing or duplicated", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    metadata_model_text = Path("KMFA/metadata/model_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "current_open_final_count == 3",
        "current_grade == D",
        "fixed_review_finding_count == 6",
        "open_review_finding_count == 0",
        "byte_exact_download_count == 2",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model registry record missing", errors)
    _require(phase.MODEL_REGISTRY_KEY in metadata_model_text, "metadata model registry record missing", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected = {
        "PARAM-KMFA-1705": "2;11;2;2;2;2;2;4;2;Q4;D;3;9;2;1;12;6;0;0;0;0;0;5;NO_GO",
        "PARAM-KMFA-1706": "true;true;true;true;true;true;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1707": "true;true;true;true;true;false;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected_value in expected.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{phase.PHASE_ID}"' in version_matrix, "VERSION_MATRIX current phase drift", errors)
    handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
    _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
    _require("S11-P1" in handoff, "HANDOFF next phase missing", errors)
    _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(bool(rows), f"browser audit empty: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"browser audit failure: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"browser audit file count mismatch: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_REVIEW_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p3_phase.PRIVATE_RAW_AFTER_PATH)
        current = phase.p3_phase._raw_snapshot("validate_v014_s10_post_remediation_stage_review")
        normalize = phase.p3_phase._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("无需生成最终差异报告", "不推断、不平均、不补零", "3 / 9 / 2 / 1"):
            _require(token in report, f"private review report missing token: {token}", errors)

    if not require_browser_evidence:
        return
    for path in (phase.PRIVATE_BROWSER_PATH, phase.PRIVATE_BASELINE_AUDIT_PATH, phase.PRIVATE_EXPORT_AUDIT_PATH):
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 1)
    _read_audit(phase.PRIVATE_EXPORT_AUDIT_PATH, errors, 2)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        checks = browser.get("checks", [])
        downloads = browser.get("download_checks", [])
        _require(browser.get("status") == "PASS", "browser verification status mismatch", errors)
        _require(len(checks) == 4 and all(item.get("status") == "PASS" for item in checks), "browser viewport checks failed", errors)
        _require(len(downloads) == 2 and all(item.get("byte_exact") is True for item in downloads), "browser downloads not byte-exact", errors)
    expected_widths = {
        "project_cost_special_report_desktop.png": 1440,
        "project_cost_special_report_mobile.png": 390,
        "business_overview_report_desktop.png": 1440,
        "business_overview_report_mobile.png": 390,
    }
    for name, width in expected_widths.items():
        path = phase.PRIVATE_SCREENSHOT_DIR / name
        _require(path.is_file(), f"browser screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s10_post_remediation_stage_review(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_cross_format(errors)
    _validate_dependencies(errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_phase_tests",
            "review_tests",
            "strict_validator",
            "browser_and_download",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation status mismatch: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate_v014_s10_post_remediation_stage_review(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: Stage 10 post-remediation review "
        f"phases=3 findings={summary['fixed_review_finding_count']}/0 "
        f"html={summary['html_restricted_preview_count']} "
        f"csv={summary['csv_restricted_appendix_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
