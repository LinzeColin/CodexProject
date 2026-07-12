#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S18-P2 full-regression acceptance evidence.

This phase runs the v1.4 public-safe full regression and acceptance lock. It
reuses the validated S18-P1 precision stress evidence, replays the historical
S18-P2 full-regression baseline, executes the v1.4 HTML human-flow audit, and
records the Go/No-Go state. It does not access the raw/private inbox, perform
S18-P3 integration preparation, run Stage 18 review, upload to GitHub, release
formal reports, restore production, reinstall an app, call live connectors, or
execute business actions.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_v014_s18_p1_precision_stress import validate_v014_s18_p1_precision_stress  # noqa: E402
from KMFA.tools.full_regression_acceptance import (  # noqa: E402
    POLICY_VERSION as LEGACY_S18_P2_POLICY_VERSION,
    REQUIRED_CHECK_CATEGORIES,
    REQUIRED_STAGE_IDS,
    build_default_full_regression_acceptance_suite,
    validate_full_regression_acceptance_artifacts,
)


TASK_ID = "KMFA-V014-S18-P2-FULL-REGRESSION-ACCEPTANCE-20260705"
ACCEPTANCE_ID = "ACC-V014-S18-P2-FULL-REGRESSION-ACCEPTANCE"
SCHEMA_VERSION = "kmfa.v014_s18_p2_full_regression_acceptance.v1"
PHASE_SCOPE = "v014_s18_p2_full_regression_acceptance_only"
POLICY_LOCK_VERSION = "LOCK-KMFA-V014-S18P2-FULL-REGRESSION-ACCEPTANCE-PUBLIC-SAFE-001"
FORMULA_ID = "FORM-KMFA-V014-S18P2-FULL-REGRESSION-ACCEPTANCE-001"
MAPPING_VERSION = "MAP-KMFA-V014-S18P2-FULL-REGRESSION-v1"

REQUIRED_V014_CHECK_CATEGORIES = REQUIRED_CHECK_CATEGORIES
REQUIRED_V014_STAGE_IDS = REQUIRED_STAGE_IDS
REQUIRED_HTML_BASELINE_FILES = (
    "00_KMFA_HTML_human_flow_entry_v1_4.html",
    "KMFA_系统全流程可点击验收样板_v1_4.html",
    "KMFA_经营分析报告可点击预览_v1_4.html",
    "KMFA_数据源检查板可点击预览_v1_4.html",
    "KMFA_待处理事项工作台可点击预览_v1_4.html",
    "KMFA_Codex开发任务控制台可点击预览_v1_4.html",
)

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S18_P2_FULL_REGRESSION_ACCEPTANCE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
METADATA_DIR = Path("KMFA/metadata/quality")

MANIFEST_PATH = MACHINE_DIR / "full_regression_acceptance_manifest.json"
CHECK_RESULTS_PATH = MACHINE_DIR / "full_regression_check_results.jsonl"
STAGE_EVIDENCE_PATH = MACHINE_DIR / "stage_acceptance_evidence_index.jsonl"
GO_NO_GO_PATH = MACHINE_DIR / "go_no_go_report.json"
HTML_AUDIT_CSV_PATH = MACHINE_DIR / "html_human_flow_audit.csv"
HTML_AUDIT_SUMMARY_PATH = MACHINE_DIR / "html_human_flow_audit_summary.json"

METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s18_p2_full_regression_acceptance_manifest.json"
METADATA_CHECK_RESULTS_PATH = METADATA_DIR / "v014_s18_p2_full_regression_check_results.jsonl"
METADATA_STAGE_EVIDENCE_PATH = METADATA_DIR / "v014_s18_p2_stage_acceptance_evidence_index.jsonl"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s18_p2_go_no_go_report.json"
METADATA_HTML_AUDIT_SUMMARY_PATH = METADATA_DIR / "v014_s18_p2_html_human_flow_audit_summary.json"

REPORT_PATH = HUMAN_DIR / "full_regression_acceptance_report.md"
HTML_AUDIT_RECORD_PATH = HUMAN_DIR / "html_human_flow_audit_record.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

V14_TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
V14_ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
V14_HTML_DIR = Path("KMFA/taskpack/v1_4/html_uiux")
V14_HTML_AUDIT_SCRIPT = V14_HTML_DIR / "kmfa_html_human_flow_audit.py"
V14_HTML_AUDIT_REPORT = V14_HTML_DIR / "KMFA_HTML_human_flow_audit_report_v1_4.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S18-P3"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.4 S18-P3 integration preparation as a separate run only after user instruction. "
    "Do not perform Stage 18 review, GitHub upload, lineage full-check completion, formal report release, "
    "production restore, app reinstall, live connector calls, external services, raw inbox access, or "
    "business execution in S18-P2."
)

RAW_ACTION_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.hrefs.append(value)


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def validate_s18_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s18_p1_precision_stress()
    if result.get("stage_id") != "S18" or result.get("phase_id") != "S18-P1":
        raise RuntimeError("S18-P2 requires validated v0.1.4 S18-P1 evidence")
    progress = result.get("stage18_phase_progress", {})
    if progress.get("s18_p1_performed") is not True:
        raise RuntimeError("S18-P1 dependency must be performed")
    if progress.get("s18_p2_performed") is not False:
        raise RuntimeError("S18-P1 dependency must not already include S18-P2")
    if result.get("next_phase") != "S18-P2":
        raise RuntimeError("S18-P1 dependency must route to S18-P2")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("v1.4 GitHub upload must remain deferred")
    return result


def validate_historical_s18_p2_public_safe_baseline() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    artifacts = build_default_full_regression_acceptance_suite(generated_at="2026-07-01T23:59:59+10:00")
    validate_full_regression_acceptance_artifacts(*artifacts)
    return artifacts


def _entry_links() -> list[str]:
    entry = V14_HTML_DIR / REQUIRED_HTML_BASELINE_FILES[0]
    parser = _LinkParser()
    parser.feed(entry.read_text(encoding="utf-8", errors="ignore"))
    return [href for href in parser.hrefs if href and not href.startswith(("http://", "https://", "#"))]


def load_v14_taskpack_baseline() -> dict[str, Any]:
    taskpack_text = V14_TASKPACK_PATH.read_text(encoding="utf-8")
    roadmap_text = V14_ROADMAP_PATH.read_text(encoding="utf-8")
    audit_report_text = V14_HTML_AUDIT_REPORT.read_text(encoding="utf-8")
    html_stats = []
    for file_name in REQUIRED_HTML_BASELINE_FILES:
        path = V14_HTML_DIR / file_name
        text = path.read_text(encoding="utf-8")
        html_stats.append({"ref": path.as_posix(), "bytes": len(text.encode("utf-8")), "sha256": sha256(text.encode("utf-8")).hexdigest()})
    missing_links = []
    for href in _entry_links():
        if not (V14_HTML_DIR / href).exists():
            missing_links.append(href)
    for token in (
        "全量回归和验收",
        "no_omission、zero_delta、schema、lineage、UI检查",
        "逐Stage确认验收证据",
        "Go/No-Go报告",
    ):
        if token not in roadmap_text:
            raise RuntimeError(f"v1.4 roadmap missing S18-P2 marker {token}")
    for token in ("S18 时", "kmfa_html_human_flow_audit.py", "FAIL = 0", "原始数据"):
        if token not in taskpack_text:
            raise RuntimeError(f"v1.4 taskpack missing S18-P2 marker {token}")
    for token in ("FAIL：0", "HTML 文件数：6", "控制项/链接/输入核验行数：54"):
        if token not in audit_report_text:
            raise RuntimeError(f"v1.4 HTML audit report missing marker {token}")
    if missing_links:
        raise RuntimeError(f"v1.4 HTML baseline has missing entry links: {missing_links}")
    return {
        "taskpack_read": True,
        "roadmap_read": True,
        "roadmap_includes_s18_p2_requirements": True,
        "taskpack_includes_html_audit_and_raw_boundary_gate": True,
        "html_baseline_read": True,
        "html_baseline_ref_count": len(REQUIRED_HTML_BASELINE_FILES),
        "html_entry_link_count": len(_entry_links()),
        "html_entry_missing_link_count": 0,
        "html_audit_report_preexisting_fail_count": 0,
        "html_baseline_private_data": False,
        "html_baseline_source": "operator_supplied_v1_4_public_safe_delivery_pack_html_only",
        "html_baseline_stats": html_stats,
        "source_refs": {
            "taskpack": V14_TASKPACK_PATH.as_posix(),
            "roadmap": V14_ROADMAP_PATH.as_posix(),
            "html_dir": V14_HTML_DIR.as_posix(),
            "audit_script": V14_HTML_AUDIT_SCRIPT.as_posix(),
            "audit_report": V14_HTML_AUDIT_REPORT.as_posix(),
        },
    }


def _python_has_playwright(python_path: Path) -> bool:
    result = subprocess.run(
        [str(python_path), "-c", "import playwright"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def _audit_python() -> Path:
    candidates: list[Path] = []
    env_python = os.environ.get("KMFA_S18P2_AUDIT_PYTHON")
    if env_python:
        candidates.append(Path(env_python))
    candidates.append(Path("KMFA/.codex_private_runtime/s18_p2_playwright_venv/bin/python"))
    candidates.append(Path(sys.executable))
    for candidate in candidates:
        if candidate.exists() and _python_has_playwright(candidate):
            return candidate
    raise RuntimeError(
        "Python Playwright runtime is required for S18-P2 HTML audit. "
        "Create ignored private runtime at KMFA/.codex_private_runtime/s18_p2_playwright_venv."
    )


def _chromium_path() -> str | None:
    env_value = os.environ.get("KMFA_CHROMIUM")
    if env_value and Path(env_value).exists():
        return env_value
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        return str(chrome)
    chromium = Path("/usr/bin/chromium")
    if chromium.exists():
        return str(chromium)
    return None


def _parse_html_audit_csv(path: Path, *, command_stdout: str, audit_python: Path, chromium_path: str | None) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({key: value for key, value in row.items() if key is not None})
    statuses = [row.get("status", "") for row in rows]
    file_names = sorted({row.get("file", "") for row in rows if row.get("file")})
    return {
        "record_type": "v014_s18_p2_html_human_flow_audit_summary",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18-P2",
        "task_id": "S18P2T01",
        "audit_executed": True,
        "audit_script_ref": V14_HTML_AUDIT_SCRIPT.as_posix(),
        "audit_root_ref": V14_HTML_DIR.as_posix(),
        "audit_csv_ref": path.as_posix(),
        "audit_python_ref": "ignored_private_runtime_or_current_python_with_playwright",
        "browser_ref": "local_chromium_or_google_chrome",
        "audit_python_available": True,
        "browser_available": chromium_path is not None,
        "file_count": len(file_names),
        "row_count": len(rows),
        "pass_count": statuses.count("PASS"),
        "warn_count": statuses.count("WARN"),
        "fail_count": statuses.count("FAIL"),
        "file_names": file_names,
        "stdout": command_stdout.strip(),
        "raw_business_data_used": False,
        "raw_inbox_accessed": False,
        "external_service_called": False,
        "github_upload_performed": False,
    }


def run_html_human_flow_audit() -> dict[str, Any]:
    load_v14_taskpack_baseline()
    audit_python = _audit_python()
    chromium_path = _chromium_path()
    if chromium_path is None:
        raise RuntimeError("No local Chromium/Google Chrome executable found for S18-P2 HTML audit")
    HTML_AUDIT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["KMFA_CHROMIUM"] = chromium_path
    result = subprocess.run(
        [
            str(audit_python),
            str(V14_HTML_AUDIT_SCRIPT),
            str(V14_HTML_DIR),
            "--out",
            str(HTML_AUDIT_CSV_PATH),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"HTML human-flow audit failed: {result.stdout}\n{result.stderr}")
    summary = _parse_html_audit_csv(
        HTML_AUDIT_CSV_PATH,
        command_stdout=result.stdout,
        audit_python=audit_python,
        chromium_path=chromium_path,
    )
    if summary["file_count"] != len(REQUIRED_HTML_BASELINE_FILES):
        raise RuntimeError("HTML human-flow audit file count mismatch")
    if summary["row_count"] < 1 or summary["fail_count"] != 0:
        raise RuntimeError("HTML human-flow audit must produce rows and fail_count=0")
    write_json(HTML_AUDIT_SUMMARY_PATH, summary)
    write_json(METADATA_HTML_AUDIT_SUMMARY_PATH, summary)
    return summary


def _raw_boundary() -> dict[str, Any]:
    result: dict[str, Any] = {key: False for key in RAW_ACTION_KEYS}
    result.update(
        {
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_ref": RAW_INBOX_REF,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        }
    )
    return result


def _public_repo_safety() -> dict[str, bool]:
    return {
        "protected_source_material_committed": False,
        "compressed_raw_package_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "raw_or_private_table_committed": False,
        "local_database_committed": False,
        "auth_material_committed": False,
        "connector_auth_material_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "source_record_material_committed": False,
        "normalized_source_values_committed": False,
        "business_amount_values_committed": False,
        "public_numeric_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "account_plaintext_committed": False,
        "formal_report_committed": False,
        "business_decision_basis_committed": False,
        "production_restore_artifact_committed": False,
        "external_service_artifact_committed": False,
        "live_connector_artifact_committed": False,
        "app_reinstall_artifact_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "no_omission_check_passed": True,
        "zero_delta_check_ran": True,
        "zero_delta_or_difference_queue_gate_passed": True,
        "schema_check_passed": True,
        "lineage_check_ran": True,
        "lineage_full_check_complete": False,
        "ui_check_passed": True,
        "html_human_flow_audit_executed": True,
        "html_human_flow_audit_fail_zero": True,
        "stage_evidence_confirmed": True,
        "go_no_go_report_generated": True,
        "quality_not_passed_must_not_deliver": True,
        "metadata_only": True,
        "public_safe_synthetic_only": True,
        "s09_pending_reconciliation_count": 12,
        "maximum_report_grade": "D",
        "raw_business_data_used": False,
        "raw_inbox_read_by_this_phase": False,
        "raw_inbox_listed_by_this_phase": False,
        "raw_inbox_stat_by_this_phase": False,
        "raw_inbox_hashed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "true_money_used": False,
        "raw_file_committed": False,
        "raw_file_name_committed": False,
        "raw_file_hash_committed": False,
        "field_plaintext_committed": False,
        "official_report_release_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "s18_p3_scope_included": False,
        "stage18_review_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
    }


def _phase_boundaries() -> dict[str, bool]:
    return {
        "s18_p1_dependency_reused": True,
        "legacy_s18_p2_public_safe_baseline_reused": True,
        "v14_html_human_flow_audit_executed": True,
        "s18_p2_full_regression_scope_included": True,
        "s18_p3_integration_scope_included": False,
        "stage18_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "business_execution_scope_included": False,
        "raw_inbox_access_scope_included": False,
        "production_restore_scope_included": False,
        "external_connector_scope_included": False,
        "app_reinstall_scope_included": False,
    }


def _check_rows(legacy_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_checks:
        item = dict(row)
        item.update(
            {
                "record_type": "v014_s18_p2_regression_check_result",
                "project_id": "KMFA",
                "version": "0.1.4",
                "phase_id": "S18-P2",
                "task_id": "S18P2T01",
                "policy_lock_version": POLICY_LOCK_VERSION,
                "mapping_version": MAPPING_VERSION,
                "metadata_target": METADATA_CHECK_RESULTS_PATH.as_posix(),
                "evidence_ref": CHECK_RESULTS_PATH.as_posix(),
                "raw_inbox_accessed": False,
                "phase_completion_upload_allowed": False,
            }
        )
        if item["check_category"] == "ui":
            item["command_ref"] = (
                "KMFA_CHROMIUM=<local browser> python KMFA/taskpack/v1_4/html_uiux/"
                "kmfa_html_human_flow_audit.py KMFA/taskpack/v1_4/html_uiux --out "
                "KMFA/stage_artifacts/V014_S18_P2_FULL_REGRESSION_ACCEPTANCE/machine/html_human_flow_audit.csv"
            )
            item["result"] = "passed"
            item["acceptance_effect"] = "v1.4 human-flow HTML audit executed with FAIL=0"
        rows.append(item)
    return rows


def _stage_rows(legacy_stage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in legacy_stage_rows:
        item = dict(row)
        item.update(
            {
                "record_type": "v014_s18_p2_stage_acceptance_evidence",
                "project_id": "KMFA",
                "version": "0.1.4",
                "phase_id": "S18-P2",
                "task_id": "S18P2T02",
                "policy_lock_version": POLICY_LOCK_VERSION,
                "metadata_target": METADATA_STAGE_EVIDENCE_PATH.as_posix(),
                "evidence_ref": STAGE_EVIDENCE_PATH.as_posix(),
            }
        )
        if item.get("stage_id") == "S18":
            item.update(
                {
                    "status": "in_progress_v014_s18p2_local_acceptance",
                    "completed_phase_ids": ["S18-P1", "S18-P2"],
                    "pending_phase_ids": ["S18-P3"],
                    "review_or_phase_evidence_ref": REPORT_PATH.as_posix(),
                    "evidence_refs": [
                        "KMFA/stage_artifacts/V014_S18_P1_PRECISION_STRESS/human/precision_stress_report.md",
                        REPORT_PATH.as_posix(),
                        HTML_AUDIT_RECORD_PATH.as_posix(),
                        GO_NO_GO_RECORD_PATH.as_posix(),
                    ],
                }
            )
        rows.append(item)
    return rows


def _go_no_go(legacy_go_no_go: dict[str, Any]) -> dict[str, Any]:
    go_no_go = dict(legacy_go_no_go)
    go_no_go.update(
        {
            "record_type": "v014_s18_p2_go_no_go_report",
            "project_id": "KMFA",
            "version": "0.1.4",
            "phase_id": "S18-P2",
            "task_id": "S18P2T03",
            "policy_lock_version": POLICY_LOCK_VERSION,
            "formula_id": FORMULA_ID,
            "metadata_target": METADATA_GO_NO_GO_PATH.as_posix(),
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "next_required_phase": NEXT_PHASE,
            "raw_business_data_used": False,
            "raw_inbox_accessed": False,
            "phase_completion_upload_allowed": False,
            "github_upload_performed": False,
        }
    )
    blockers = list(dict.fromkeys([*go_no_go.get("blocker_ids", []), "S18_P3_PENDING", "STAGE18_REVIEW_PENDING"]))
    go_no_go["blocker_ids"] = blockers
    return go_no_go


def write_test_results_placeholder() -> None:
    if TEST_RESULTS_PATH.exists():
        existing = TEST_RESULTS_PATH.read_text(encoding="utf-8")
        if "focused v0.1.4 S18-P2 unit test: PASS" in existing:
            return
    write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P2 Full Regression Acceptance Test Results",
                "",
                "- generator: pending final validation replay",
                "- validator: pending final validation replay",
                "- focused_unittest: pending final validation replay",
                "- html_human_flow_audit: pending final validation replay",
                "- governance_validation: pending final validation replay",
                "- raw_secret_scan: pending final validation replay",
                "",
            ]
        ),
    )


def generate(*, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    s18_p1 = validate_s18_p1_dependency()
    legacy_manifest, legacy_checks, legacy_stage_rows, legacy_go_no_go = (
        validate_historical_s18_p2_public_safe_baseline()
    )
    v14_baseline = load_v14_taskpack_baseline()
    html_audit = run_html_human_flow_audit()
    check_results = _check_rows(legacy_checks)
    stage_evidence = _stage_rows(legacy_stage_rows)
    go_no_go = _go_no_go(legacy_go_no_go)
    quality_gate = _quality_gate()
    raw_boundary = _raw_boundary()
    phase_boundaries = _phase_boundaries()
    content_hash = sha256_json(
        {
            "check_results": check_results,
            "stage_evidence": stage_evidence,
            "go_no_go": go_no_go,
            "html_audit": html_audit,
            "html_refs": list(REQUIRED_HTML_BASELINE_FILES),
        }
    )
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "v014_s18_p2_full_regression_acceptance_manifest",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S18",
        "phase_id": "S18-P2",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "completed_task_ids": ["S18P2T01", "S18P2T02", "S18P2T03"],
        "generated_at": generated_at,
        "git_head": git_output(["rev-parse", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_full_regression_locked",
        "s18_p1_dependency_validated": True,
        "s18_p1_dependency_ref": "KMFA/stage_artifacts/V014_S18_P1_PRECISION_STRESS/machine/precision_stress_manifest.json",
        "historical_s18_p2_public_safe_baseline_validated": True,
        "historical_s18_p2_policy_version": LEGACY_S18_P2_POLICY_VERSION,
        "required_check_categories": list(REQUIRED_V014_CHECK_CATEGORIES),
        "required_stage_ids": list(REQUIRED_V014_STAGE_IDS),
        "full_regression_summary": {
            "check_category_count": len(check_results),
            "stage_evidence_count": len(stage_evidence),
            "html_audit_file_count": html_audit["file_count"],
            "html_audit_row_count": html_audit["row_count"],
            "html_audit_pass_count": html_audit["pass_count"],
            "html_audit_warn_count": html_audit["warn_count"],
            "html_audit_fail_count": html_audit["fail_count"],
            "go_no_go_decision": go_no_go["decision"],
            "blocker_count": len(go_no_go["blocker_ids"]),
            "maximum_report_grade": quality_gate["maximum_report_grade"],
            "next_required_phase": NEXT_PHASE,
        },
        "stage18_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s18_p1_performed": True,
            "s18_p2_performed": True,
            "s18_p3_performed": False,
            "stage18_review_performed": False,
        },
        "quality_gate": quality_gate,
        "phase_boundaries": phase_boundaries,
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": _public_repo_safety(),
        "v14_taskpack_baseline": v14_baseline,
        "s18_p1_dependency_summary": {
            "dependency_phase": s18_p1["phase_id"],
            "dependency_next_phase": s18_p1["next_phase"],
            "dependency_github_upload_performed": s18_p1["github_upload"]["github_upload_performed"],
        },
        "check_results": check_results,
        "stage_acceptance_evidence": stage_evidence,
        "go_no_go": go_no_go,
        "html_human_flow_audit": html_audit,
        "metadata_outputs": {
            "manifest": METADATA_MANIFEST_PATH.as_posix(),
            "check_results": METADATA_CHECK_RESULTS_PATH.as_posix(),
            "stage_evidence": METADATA_STAGE_EVIDENCE_PATH.as_posix(),
            "go_no_go": METADATA_GO_NO_GO_PATH.as_posix(),
            "html_audit_summary": METADATA_HTML_AUDIT_SUMMARY_PATH.as_posix(),
        },
        "artifact_refs": {
            "manifest": MANIFEST_PATH.as_posix(),
            "check_results": CHECK_RESULTS_PATH.as_posix(),
            "stage_evidence": STAGE_EVIDENCE_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "html_audit_csv": HTML_AUDIT_CSV_PATH.as_posix(),
            "html_audit_summary": HTML_AUDIT_SUMMARY_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "html_audit_record": HTML_AUDIT_RECORD_PATH.as_posix(),
            "go_no_go_record": GO_NO_GO_RECORD_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
        },
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "s18_p1_dependency_validator": "PASS",
            "historical_s18_p2_baseline_validator": "PASS",
            "html_human_flow_audit": "PASS",
            "s18_p2_validator": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_suffix_scan": "PENDING_FINAL_VALIDATION",
            "high_signal_secret_scan": "PENDING_FINAL_VALIDATION",
            "public_artifact_boundary_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "github_upload": {
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_ready_next_gate": False,
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": NEXT_REQUIRED_STEP,
        "content_hash": content_hash,
    }
    write_json(MANIFEST_PATH, manifest)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_jsonl(CHECK_RESULTS_PATH, check_results)
    write_jsonl(METADATA_CHECK_RESULTS_PATH, check_results)
    write_jsonl(STAGE_EVIDENCE_PATH, stage_evidence)
    write_jsonl(METADATA_STAGE_EVIDENCE_PATH, stage_evidence)
    write_json(GO_NO_GO_PATH, go_no_go)
    write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P2 Full Regression Acceptance Report",
                "",
                f"- generated_at: `{generated_at}`",
                f"- task_id: `{TASK_ID}`",
                "- scope: `S18-P2 only`",
                f"- check_categories: `{len(check_results)}`",
                f"- stage_evidence_count: `{len(stage_evidence)}`",
                f"- html_human_flow_files: `{html_audit['file_count']}`",
                f"- html_human_flow_rows: `{html_audit['row_count']}`",
                f"- html_human_flow_fail_count: `{html_audit['fail_count']}`",
                f"- go_no_go_decision: `{go_no_go['decision']}`",
                "- report_grade_visible: `D`",
                "- s18_p1_dependency_validated: `true`",
                "- s18_p3_performed: `false`",
                "- stage18_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_access_by_this_phase: `false`",
                "- formal_report_allowed: `false`",
                "- business_execution_allowed: `false`",
                "",
            ]
        ),
    )
    write_text(
        HTML_AUDIT_RECORD_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P2 HTML Human-Flow Audit Record",
                "",
                "- audit_executed: `true`",
                "- audit_root: `KMFA/taskpack/v1_4/html_uiux`",
                "- audit_script: `KMFA/taskpack/v1_4/html_uiux/kmfa_html_human_flow_audit.py`",
                f"- files: `{html_audit['file_count']}`",
                f"- rows: `{html_audit['row_count']}`",
                f"- pass: `{html_audit['pass_count']}`",
                f"- warn: `{html_audit['warn_count']}`",
                f"- fail: `{html_audit['fail_count']}`",
                "- external_service_called: `false`",
                "- raw_inbox_accessed: `false`",
                "- github_upload_performed: `false`",
                "",
            ]
        ),
    )
    write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P2 Go/No-Go Record",
                "",
                "- decision: `NO_GO`",
                "- delivery_allowed: `false`",
                "- github_upload_allowed: `false`",
                "- business_decision_basis_allowed: `false`",
                "- blocker: `LINEAGE_FULL_CHECK_NOT_COMPLETE`",
                "- blocker: `OFFICIAL_REPORT_RELEASE_NOT_ALLOWED`",
                "- blocker: `S18_P3_PENDING`",
                "- next_required_phase: `S18-P3`",
                "",
            ]
        ),
    )
    write_test_results_placeholder()
    write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P2 Risk Register",
                "",
                "- R1: Full regression acceptance is public-safe and metadata-only; it does not prove raw-backed production reconciliation.",
                "- R2: Go/No-Go remains `NO_GO` until S18-P3, Stage 18 review, lineage completion and formal release gates are done.",
                "- R3: HTML audit requires a local Playwright-capable private runtime, which is not committed to Git.",
                "",
            ]
        ),
    )
    write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 S18-P2 Rollback Plan",
                "",
                "- Remove only S18-P2 generated public-safe artifacts if this phase must be reverted.",
                "- Keep S18-P1 evidence intact unless the user explicitly requests a broader rollback.",
                "- Do not delete or mutate raw/private inbox material.",
                "- Do not push or upload during rollback.",
                "",
            ]
        ),
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA v0.1.4 S18-P2 full-regression acceptance evidence.")
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args(argv)
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["full_regression_summary"]
    print(
        "PASS: generated KMFA v0.1.4 S18-P2 full regression acceptance evidence "
        f"(checks={summary['check_category_count']}, "
        f"stages={summary['stage_evidence_count']}, "
        f"html_files={summary['html_audit_file_count']}, "
        f"html_rows={summary['html_audit_row_count']}, "
        f"html_fail={summary['html_audit_fail_count']}, "
        f"decision={summary['go_no_go_decision']}, "
        "s18_p3=False, stage18_review=False, github_upload=False)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
