#!/usr/bin/env python3
"""KMFA no-omission baseline check.

This check is intentionally local and deterministic. It verifies that the
imported TaskPack requirements bind P0/P1 items to Stage/Phase/Task status,
acceptance gates, tests, and evidence references without requiring raw content
inspection.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "metadata" / "traceability" / "requirements.csv"
STAGE_STATUS = ROOT / "metadata" / "stage_status.jsonl"
BASELINE_V12 = ROOT / "taskpack" / "v1_2"
OWNER_AUTHORIZED_PLAINTEXT_UPLOAD_MANIFEST = (
    ROOT / "metadata" / "security" / "owner_authorized_plaintext_upload_manifest.jsonl"
)

REQUIRED_REQUIREMENT_COLUMNS = {
    "requirement_id",
    "priority",
    "theme",
    "requirement",
    "covered_stages",
    "task_ids",
    "acceptance_gate",
    "test_or_evidence",
    "evidence_ref",
    "status",
    "source_file",
}

REQUIRED_STATUS_FIELDS = {"record_type", "status", "updated_at", "fact_level"}
EXPECTED_COUNTS = {"P0": 9, "P1": 8}
PUBLIC_REPO_FORBIDDEN_SUFFIXES = {
    ".zip",
    ".xls",
    ".xlsx",
    ".pdf",
    ".mov",
    ".mp4",
    ".m4v",
    ".sqlite",
    ".db",
    ".sqlite-shm",
    ".sqlite-wal",
}
OWNER_AUTHORIZED_UPLOAD_RECORD_TYPE = "owner_authorized_plaintext_upload_file"
PUBLIC_SYNTHETIC_REPORT_EXPORTS = {
    "stage_artifacts/V015_S17_P3_PROJECT_WORKFLOW/exports/pdf/kmfa_project_cost_report.pdf": "PDF",
    "stage_artifacts/V015_S17_P3_PROJECT_WORKFLOW/exports/xlsx/kmfa_project_cost_report.xlsx": "XLSX",
}
TRACKED_PUBLIC_SYNTHETIC_REPORT_EXPORTS = {
    "stage_artifacts/V015_S21_P2_REPORT_GENERATION/exports/pdf/kmfa_management_report.pdf",
}

REQUIRED_V12_BASELINE_FILES = [
    "01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "00_总索引与补漏复核/KMFA_补漏复核报告_v1_2.md",
    "00_总索引与补漏复核/KMFA_全量信息承接矩阵_v1_2.csv",
    "20_HTML_UIUX_报告预览/00_HTML总入口_KMFA_v1_2.html",
    "20_HTML_UIUX_报告预览/HTML文件索引_v1_2.csv",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_系统首页预览_v4_blue.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_经营分析报告预览_v3_blue.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_数据源检查板_v0_5_blue.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Resolution_Workbench_v0_4.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Ring5_Final_Task_Control_Board.html",
    "20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_阶段三任务控制台预览_v1_0.html",
    "21_前序生成包归档_可追溯/前序生成压缩包_SHA256_v1_2.csv",
    "source_manifests/用户原始上传数据_SHA256_v1_2.csv",
    "source_manifests/前序散件_SHA256_v1_2.csv",
    "92_工具与代码/check_required_html.py",
    "92_工具与代码/check_v1_2_no_omission.py",
    "machine/source_package_manifest.json",
    "machine/repo_baseline_sha256.csv",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def split_values(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").replace(",", ";").split(";") if item.strip()]


def is_ignored_untracked_private_runtime(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    if ".codex_private_runtime" not in parts and "private_runtime" not in parts:
        return False
    repo_root = ROOT.parent
    repo_rel = path.relative_to(repo_root).as_posix()
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", repo_rel],
        cwd=repo_root,
        check=False,
    ).returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", repo_rel],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    return ignored and not tracked


def is_verified_ignored_public_synthetic_report(path: Path) -> bool:
    """Allow only the two local, ignored exports proven by the S17-P3 manifest.

    This does not permit either file to enter Git. Any other PDF/XLSX, a tracked
    copy, a changed path, or a report without zero-difference public-synthetic
    evidence remains forbidden.
    """
    rel = path.relative_to(ROOT).as_posix()
    format_name = PUBLIC_SYNTHETIC_REPORT_EXPORTS.get(rel)
    if format_name is None:
        return False
    repo_root = ROOT.parent
    repo_rel = f"KMFA/{rel}"
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", repo_rel], cwd=repo_root, check=False
    ).returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", repo_rel],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    if not ignored or tracked:
        return False
    machine = ROOT / "stage_artifacts/V015_S17_P3_PROJECT_WORKFLOW/machine"
    try:
        manifest = json.loads((machine / "s17_p3_project_workflow_manifest.json").read_text(encoding="utf-8"))
        report = json.loads((machine / "project_report_contract_public_safe.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    expected_path = f"KMFA/{rel}"
    if (
        manifest.get("data_classification") != "PUBLIC_SYNTHETIC"
        or manifest.get("raw_root_access_count") != 0
        or manifest.get("source_data_write_count") != 0
        or manifest.get("formal_business_report") is not False
        or report.get("formats", {}).get(format_name) != expected_path
        or report.get("page_golden_difference_cents") != 0
        or report.get("category_page_difference_cents") != 0
        or report.get("money_tolerance_cents") != 0
    ):
        return False
    if format_name == "PDF":
        return path.read_bytes()[:5] == b"%PDF-" and path.stat().st_size > 10_000
    return path.read_bytes()[:2] == b"PK" and path.stat().st_size > 5_000


def is_verified_tracked_public_synthetic_report(path: Path) -> bool:
    """Allow the exact S21-P2 PDF only when its public-safe evidence agrees.

    The path may be untracked before the implementation commit and tracked
    afterwards. No other PDF gains an exception from this check.
    """
    rel = path.relative_to(ROOT).as_posix()
    if rel not in TRACKED_PUBLIC_SYNTHETIC_REPORT_EXPORTS:
        return False
    machine = ROOT / "stage_artifacts/V015_S21_P2_REPORT_GENERATION/machine"
    try:
        manifest = json.loads((machine / "s21_p2_report_generation_manifest.json").read_text(encoding="utf-8"))
        source = json.loads((machine / "source_contract_public_safe.json").read_text(encoding="utf-8"))
        consistency = json.loads((machine / "cross_format_consistency_public_safe.json").read_text(encoding="utf-8"))
        pdf_contract = json.loads((machine / "pdf_contract_public_safe.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if (
        manifest.get("data_classification") != "PUBLIC_SYNTHETIC_ONLY"
        or manifest.get("raw_root_access_count") != 0
        or manifest.get("raw_write_count") != 0
        or manifest.get("formal_business_report") is not False
        or manifest.get("approval_or_publication_count") != 0
        or manifest.get("github_upload_performed") is not False
        or manifest.get("app_reinstall_performed") is not False
        or manifest.get("exact_numeric_value_count") != 21
        or manifest.get("cross_format_difference_integer") != 0
        or source.get("data_classification") != "PUBLIC_SYNTHETIC_ONLY"
        or source.get("dependency") != "V015_S21_P1_REPORT_MODEL:PASSED"
        or consistency.get("status") != "PASS"
        or consistency.get("numeric_value_count") != 21
        or consistency.get("pdf_value_count") != 21
        or consistency.get("difference_integer") != 0
        or pdf_contract.get("page_count", 0) < pdf_contract.get("minimum_page_count", 2)
        or pdf_contract.get("page_number_present") is not True
        or pdf_contract.get("repeating_header_present") is not True
        or pdf_contract.get("source_section_present") is not True
        or pdf_contract.get("professional_appendix_present") is not True
    ):
        return False
    return path.read_bytes()[:5] == b"%PDF-" and path.stat().st_size > 10_000


def load_requirements() -> list[dict[str, str]]:
    if not REQUIREMENTS.exists():
        fail(f"missing requirements matrix: {REQUIREMENTS.relative_to(ROOT)}")
    with REQUIREMENTS.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_REQUIREMENT_COLUMNS - columns)
        if missing:
            fail("requirements.csv missing columns: " + ", ".join(missing))
        rows = list(reader)
    if not rows:
        fail("requirements.csv has no rows")
    return rows


def is_baseline_status_record(record: dict[str, object]) -> bool:
    record_type = str(record.get("record_type") or "")
    phase_id = str(record.get("phase_id") or "")
    return not (record_type.startswith("v013_") or phase_id.startswith("V013_"))


def load_status_records() -> tuple[set[str], set[str], set[str], list[dict[str, object]]]:
    if not STAGE_STATUS.exists():
        fail(f"missing stage status registry: {STAGE_STATUS.relative_to(ROOT)}")
    records: list[dict[str, object]] = []
    for line_no, line in enumerate(STAGE_STATUS.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSONL at stage_status.jsonl:{line_no}: {exc}")
        missing = sorted(REQUIRED_STATUS_FIELDS - set(record))
        if missing:
            fail(f"stage_status.jsonl:{line_no} missing fields: {', '.join(missing)}")
        records.append(record)
    if not records:
        fail("stage_status.jsonl has no records")
    baseline_records = [record for record in records if is_baseline_status_record(record)]

    roadmap_stage_ids: set[str] = set()
    governance_stage_ids: set[str] = set()
    stage_ids: set[str] = set()
    phase_ids: set[str] = set()
    task_ids: set[str] = set()
    for record in baseline_records:
        if record.get("record_type") == "stage":
            if record.get("roadmap_stage_id"):
                roadmap_stage_ids.add(str(record["roadmap_stage_id"]))
                stage_ids.add(str(record["roadmap_stage_id"]))
            if record.get("governance_stage_id"):
                governance_stage_ids.add(str(record["governance_stage_id"]))
                stage_ids.add(str(record["governance_stage_id"]))
        elif record.get("record_type") == "phase" and record.get("phase_id"):
            phase_ids.add(str(record["phase_id"]))
        elif record.get("record_type") == "task" and record.get("task_id"):
            task_ids.add(str(record["task_id"]))

    if len(roadmap_stage_ids) != 18:
        fail(f"expected 18 roadmap stage ids, found {len(roadmap_stage_ids)}")
    if len(governance_stage_ids) != 18:
        fail(f"expected 18 governance stage ids, found {len(governance_stage_ids)}")
    if len(phase_ids) != 54:
        fail(f"expected 54 phase records, found {len(phase_ids)}")
    if len(task_ids) != 162:
        fail(f"expected 162 task records, found {len(task_ids)}")
    return stage_ids, phase_ids, task_ids, baseline_records


def check_requirements(rows: list[dict[str, str]], stage_ids: set[str], task_ids: set[str]) -> None:
    ids = [row["requirement_id"].strip() for row in rows]
    duplicates = [req_id for req_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        fail("duplicate requirement_id values: " + ", ".join(sorted(duplicates)))

    priority_counts = Counter(row["priority"].strip() for row in rows)
    for priority, expected in EXPECTED_COUNTS.items():
        actual = priority_counts.get(priority, 0)
        if actual != expected:
            fail(f"expected {expected} {priority} requirements, found {actual}")

    for row in rows:
        req_id = row["requirement_id"].strip()
        priority = row["priority"].strip()
        if priority not in {"P0", "P1", "P2"}:
            fail(f"{req_id}: invalid priority {priority!r}")
        if priority not in {"P0", "P1"}:
            continue

        for field in ("theme", "requirement", "covered_stages", "task_ids", "acceptance_gate", "test_or_evidence", "evidence_ref", "status"):
            if not str(row.get(field, "")).strip():
                fail(f"{req_id}: missing {field}")

        covered_stages = split_values(row["covered_stages"])
        missing_stages = [stage_id for stage_id in covered_stages if stage_id not in stage_ids]
        if missing_stages:
            fail(f"{req_id}: covered stages missing from stage registry: {', '.join(missing_stages)}")

        bound_tasks = split_values(row["task_ids"])
        missing_tasks = [task_id for task_id in bound_tasks if task_id not in task_ids]
        if missing_tasks:
            fail(f"{req_id}: task bindings missing from stage registry: {', '.join(missing_tasks[:10])}")

        if len(bound_tasks) < len(covered_stages):
            fail(f"{req_id}: fewer task bindings than covered stages")


def check_no_raw_sensitive_files() -> None:
    validate_owner_plaintext_exception_is_disabled()
    matches = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        repo_rel = f"KMFA/{rel}"
        if "90_用户原始上传数据_仅本地私有_禁止提交GitHub/" in rel:
            if is_ignored_untracked_private_runtime(path):
                continue
            matches.append(rel)
            continue
        if path.suffix.lower() in PUBLIC_REPO_FORBIDDEN_SUFFIXES:
            if is_ignored_untracked_private_runtime(path):
                continue
            if is_verified_ignored_public_synthetic_report(path):
                continue
            if is_verified_tracked_public_synthetic_report(path):
                continue
            matches.append(rel)
    if matches:
        fail("forbidden raw/sensitive file-like artifacts under KMFA: " + ", ".join(matches[:20]))


def validate_owner_plaintext_exception_is_disabled() -> None:
    if not OWNER_AUTHORIZED_PLAINTEXT_UPLOAD_MANIFEST.exists():
        fail("missing legacy owner plaintext policy tombstone")

    policy_rows = 0
    for line_number, line in enumerate(
        OWNER_AUTHORIZED_PLAINTEXT_UPLOAD_MANIFEST.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") == OWNER_AUTHORIZED_UPLOAD_RECORD_TYPE:
            fail(
                f"legacy owner plaintext upload record {line_number} is forbidden by v1.5 strict policy"
            )
        if record.get("record_type") != "owner_authorized_plaintext_upload_policy":
            continue
        policy_rows += 1
        if record.get("allowed") is not False:
            fail(f"legacy owner plaintext policy {line_number} must set allowed=false")
        if record.get("legacy_policy_effective") is not False:
            fail(f"legacy owner plaintext policy {line_number} must set legacy_policy_effective=false")
        if record.get("current_authorization_status") != "superseded_v1.5_strict_public_safe_only":
            fail(f"legacy owner plaintext policy {line_number} has an invalid supersession status")
    if policy_rows != 1:
        fail(f"expected exactly one disabled legacy owner plaintext policy row, found {policy_rows}")


def check_v12_baseline() -> None:
    if not BASELINE_V12.is_dir():
        fail("missing v1.2 full task-pack baseline: taskpack/v1_2")

    missing = [rel for rel in REQUIRED_V12_BASELINE_FILES if not (BASELINE_V12 / rel).is_file()]
    if missing:
        fail("v1.2 baseline missing files: " + ", ".join(missing[:20]))

    html_files = list((BASELINE_V12 / "20_HTML_UIUX_报告预览").rglob("*.html"))
    core_html_files = list((BASELINE_V12 / "20_HTML_UIUX_报告预览" / "01_核心HTML验收样板").glob("*.html"))
    if len(html_files) < 45:
        fail(f"v1.2 baseline expected at least 45 HTML files, found {len(html_files)}")
    if len(core_html_files) < 7:
        fail(f"v1.2 baseline expected at least 7 core HTML files, found {len(core_html_files)}")

    private_manifest = (BASELINE_V12 / "source_manifests" / "用户原始上传数据_SHA256_v1_2.csv").read_text(
        encoding="utf-8-sig"
    )
    if "禁止提交公开GitHub" not in private_manifest:
        fail("private source manifest does not preserve the public GitHub prohibition")


def main() -> int:
    rows = load_requirements()
    stage_ids, _phase_ids, task_ids, records = load_status_records()
    check_requirements(rows, stage_ids, task_ids)
    check_v12_baseline()
    check_no_raw_sensitive_files()
    priority_counts = Counter(row["priority"].strip() for row in rows)
    print(
        "PASS: KMFA no omission check passed "
        f"(requirements={len(rows)}, P0={priority_counts.get('P0', 0)}, "
        f"P1={priority_counts.get('P1', 0)}, status_records={len(records)}, tasks={len(task_ids)}, "
        "v1.2_html=45+)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
