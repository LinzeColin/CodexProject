#!/usr/bin/env python3
"""Validate KMFA v1.4 S01-P3 no-omission baseline evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/machine/"
    "s01_p3_no_omission_baseline_manifest.json"
)
S01P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/machine/"
    "s01_p2_public_baseline_sync_manifest.json"
)
ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
LEGACY_REQUIREMENTS_PATH = Path("KMFA/metadata/traceability/requirements.csv")
V14_REQUIREMENTS_PATH = Path("KMFA/metadata/traceability/v1_4_no_omission_requirements.csv")
V14_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")
LEGACY_NO_OMISSION_TOOL = Path("KMFA/tools/no_omission_check.py")
IMPLEMENTATION_PHASE_RE = re.compile(r"^S\d{2}P[123]$")
IMPLEMENTATION_TASK_RE = re.compile(r"^S\d{2}P[123]T\d{2}$")
EVIDENCE_FILES = [
    Path("KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/human/s01_p3_completion_record.md"),
    Path("KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/human/risk_register.md"),
    Path("KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/human/rollback_plan.md"),
    Path("KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/human/test_results.md"),
    MANIFEST_PATH,
    V14_REQUIREMENTS_PATH,
    V14_STATUS_PATH,
]
REQUIRED_LEGACY_COLUMNS = {
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
FORBIDDEN_EXTENSIONS = {
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".db",
}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_path",
    "member_name",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def split_values(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").replace(",", ";").split(";") if item.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValidationError(f"missing CSV file: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_LEGACY_COLUMNS - columns)
        if missing:
            raise ValidationError(f"{path} missing columns: {', '.join(missing)}")
        return list(reader)


def run_legacy_no_omission() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(LEGACY_NO_OMISSION_TOOL)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(
            f"legacy no_omission_check failed: {result.stdout.strip()} {result.stderr.strip()}".strip()
        )
    match = re.search(
        r"requirements=(?P<requirements>\d+), P0=(?P<p0>\d+), P1=(?P<p1>\d+), "
        r"status_records=(?P<stage_status_records>\d+), tasks=(?P<task_records>\d+)",
        result.stdout,
    )
    if not match:
        raise ValidationError(f"legacy no_omission output missing counts: {result.stdout.strip()}")
    parsed = {key: int(value) for key, value in match.groupdict().items()}
    parsed["stdout"] = result.stdout.strip()
    return parsed


def load_v14_status() -> tuple[list[dict[str, Any]], set[str], set[str], set[str]]:
    if not V14_STATUS_PATH.exists():
        raise ValidationError(f"missing v1.4 stage status registry: {V14_STATUS_PATH}")
    records: list[dict[str, Any]] = []
    stage_ids: set[str] = set()
    phase_ids: set[str] = set()
    task_ids: set[str] = set()
    for line_no, line in enumerate(V14_STATUS_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{V14_STATUS_PATH}:{line_no} must contain a JSON object")
        if value.get("schema_version") != "kmfa.v014_stage_phase_task_status.v1":
            raise ValidationError(f"{V14_STATUS_PATH}:{line_no} schema mismatch")
        if value.get("project_id") != "KMFA" or value.get("version") != "0.1.4":
            raise ValidationError(f"{V14_STATUS_PATH}:{line_no} project/version mismatch")
        if value.get("raw_data_committed") is not False:
            raise ValidationError(f"{V14_STATUS_PATH}:{line_no} raw_data_committed must be false")
        records.append(value)
        if value.get("record_type") == "stage":
            stage_ids.add(str(value.get("stage_id")))
        elif value.get("record_type") == "phase":
            phase_id = str(value.get("phase_id"))
            if IMPLEMENTATION_PHASE_RE.fullmatch(phase_id):
                phase_ids.add(phase_id)
        elif value.get("record_type") == "task":
            task_id = str(value.get("task_id"))
            if IMPLEMENTATION_TASK_RE.fullmatch(task_id):
                task_ids.add(task_id)

    if len(stage_ids) != 18:
        raise ValidationError(f"expected 18 v1.4 stages, found {len(stage_ids)}")
    if len(phase_ids) != 54:
        raise ValidationError(f"expected 54 v1.4 phases, found {len(phase_ids)}")
    if len(task_ids) != 162:
        raise ValidationError(f"expected 162 v1.4 tasks, found {len(task_ids)}")
    if len(stage_ids) + len(phase_ids) + len(task_ids) != 234:
        raise ValidationError("expected 234 unique v1.4 implementation ids")

    phases_by_stage: dict[str, set[str]] = defaultdict(set)
    tasks_by_phase: dict[str, set[str]] = defaultdict(set)
    for record in records:
        if record.get("record_type") == "phase":
            phase_id = str(record["phase_id"])
            if IMPLEMENTATION_PHASE_RE.fullmatch(phase_id):
                phases_by_stage[str(record["stage_id"])].add(phase_id)
        elif record.get("record_type") == "task":
            phase_id = str(record["phase_id"])
            task_id = str(record["task_id"])
            if IMPLEMENTATION_PHASE_RE.fullmatch(phase_id) and IMPLEMENTATION_TASK_RE.fullmatch(task_id):
                tasks_by_phase[phase_id].add(task_id)
    for stage in stage_ids:
        if len(phases_by_stage[stage]) != 3:
            raise ValidationError(f"{stage} must have 3 phases")
    for phase in phase_ids:
        if len(tasks_by_phase[phase]) != 3:
            raise ValidationError(f"{phase} must have 3 tasks")

    required_current = {"S01P3T01", "S01P3T02", "S01P3T03"}
    if not required_current.issubset(task_ids):
        raise ValidationError("missing v1.4 S01-P3 task ids")
    return records, stage_ids, phase_ids, task_ids


def check_requirements(rows: list[dict[str, str]], stage_ids: set[str], task_ids: set[str]) -> Counter[str]:
    if not rows:
        raise ValidationError("requirements matrix has no rows")
    seen: set[str] = set()
    for row in rows:
        req_id = row["requirement_id"].strip()
        if not req_id:
            raise ValidationError("blank requirement_id")
        if req_id in seen:
            raise ValidationError(f"duplicate requirement_id: {req_id}")
        seen.add(req_id)
        priority = row["priority"].strip()
        if priority not in {"P0", "P1", "P2"}:
            raise ValidationError(f"{req_id}: invalid priority {priority!r}")
        if priority in {"P0", "P1"}:
            for field in (
                "theme",
                "requirement",
                "covered_stages",
                "task_ids",
                "acceptance_gate",
                "test_or_evidence",
                "evidence_ref",
                "status",
                "source_file",
            ):
                if not str(row.get(field, "")).strip():
                    raise ValidationError(f"{req_id}: missing {field}")
            missing_stages = [stage for stage in split_values(row["covered_stages"]) if stage not in stage_ids]
            if missing_stages:
                raise ValidationError(f"{req_id}: unknown covered stages: {', '.join(missing_stages)}")
            missing_tasks = [task for task in split_values(row["task_ids"]) if task not in task_ids]
            if missing_tasks:
                raise ValidationError(f"{req_id}: unknown task ids: {', '.join(missing_tasks[:10])}")
    return Counter(row["priority"].strip() for row in rows)


def check_evidence_public_safe() -> None:
    for path in EVIDENCE_FILES:
        if not path.exists():
            raise ValidationError(f"missing evidence file: {path}")
        if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
            raise ValidationError(f"forbidden evidence extension: {path}")
        if path.suffix.lower() not in {".md", ".json", ".jsonl", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in text:
                raise ValidationError(f"forbidden evidence text {forbidden!r} in {path}")


def validate_v014_s01_p3_no_omission_baseline(
    manifest_path: Path = MANIFEST_PATH,
    *,
    run_legacy_check: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s01p2 = read_json(S01P2_MANIFEST_PATH)
    records, v14_stage_ids, v14_phase_ids, v14_task_ids = load_v14_status()
    legacy_rows = read_csv(LEGACY_REQUIREMENTS_PATH)
    v14_rows = read_csv(V14_REQUIREMENTS_PATH)
    legacy_counts = Counter(row["priority"].strip() for row in legacy_rows)
    v14_counts = check_requirements(v14_rows, v14_stage_ids, v14_task_ids)

    if run_legacy_check:
        legacy_result = run_legacy_no_omission()
        require(legacy_result.get("requirements") == 20, "legacy no-omission requirements count mismatch")
        require(legacy_result.get("p0") == 9, "legacy no-omission P0 count mismatch")
        require(legacy_result.get("p1") == 8, "legacy no-omission P1 count mismatch")
        require(legacy_result.get("task_records") == 162, "legacy no-omission task count mismatch")

    require(manifest.get("schema_version") == "kmfa.v014_s01_p3_no_omission_baseline.v1", "schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.4", "version mismatch")
    require(manifest.get("stage_phase") == "S01-P3", "stage_phase must be S01-P3")
    require(
        manifest.get("task_id") == "KMFA-V014-S01-P3-NO-OMISSION-BASELINE-20260703",
        "task_id mismatch",
    )
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred",
        "status mismatch",
    )

    dependency = manifest.get("dependency", {})
    require(dependency.get("required_phase") == "S01-P2", "dependency must be S01-P2")
    require(dependency.get("dependency_manifest") == str(S01P2_MANIFEST_PATH), "dependency manifest mismatch")
    require(s01p2.get("phase_scope", {}).get("next_phase") == "S01-P3", "S01-P2 must point to S01-P3")

    scope = manifest.get("phase_scope", {})
    require(scope.get("current_phase_only") is True, "current_phase_only must be true")
    require(scope.get("stage_review_performed") is False, "Stage 1 review must not be performed")
    require(scope.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(scope.get("s02_started") is False, "S02 must not be started")
    require(scope.get("next_phase") == "S01_STAGE_REVIEW", "next phase must be Stage 1 review")
    require(scope.get("next_phase_started") is False, "next phase must not be started")

    baseline = manifest.get("no_omission_baseline", {})
    require(baseline.get("legacy_requirements") == len(legacy_rows) == 20, "legacy requirements count mismatch")
    require(baseline.get("legacy_p0") == legacy_counts.get("P0") == 9, "legacy P0 count mismatch")
    require(baseline.get("legacy_p1") == legacy_counts.get("P1") == 8, "legacy P1 count mismatch")
    require(baseline.get("v14_overlay_requirements") == len(v14_rows) == 5, "v1.4 overlay count mismatch")
    require(baseline.get("v14_overlay_p0") == v14_counts.get("P0") == 3, "v1.4 overlay P0 count mismatch")
    require(baseline.get("v14_overlay_p1") == v14_counts.get("P1") == 2, "v1.4 overlay P1 count mismatch")
    require(baseline.get("v14_stages") == 18, "v1.4 stage count mismatch")
    require(baseline.get("v14_phases") == 54, "v1.4 phase count mismatch")
    require(baseline.get("v14_tasks") == 162, "v1.4 task count mismatch")
    require(baseline.get("v14_stage_phase_task_status") == str(V14_STATUS_PATH), "v1.4 status path mismatch")
    require(baseline.get("v14_overlay_requirements_matrix") == str(V14_REQUIREMENTS_PATH), "v1.4 requirements path mismatch")
    require(baseline.get("roadmap_source") == str(ROADMAP_PATH), "roadmap source mismatch")
    html_gate = baseline.get("v14_html_human_flow_audit", {})
    require(html_gate.get("pass") == 54 and html_gate.get("warn") == 0 and html_gate.get("fail") == 0, "HTML gate must be 54/0/0")

    require(ROADMAP_PATH.exists(), "missing v1.4 roadmap")
    require(TASKPACK_PATH.exists(), "missing v1.4 taskpack")

    raw_boundary = manifest.get("raw_data_boundary", {})
    for key in (
        "raw_inbox_read_by_this_phase",
        "raw_inbox_listed_by_this_phase",
        "raw_inbox_modified_by_this_phase",
        "raw_payload_extracted_from_delivery_zip",
        "raw_filenames_committed",
        "raw_hashes_committed",
        "field_or_header_plaintext_committed",
        "business_values_committed",
    ):
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false")

    release_state = manifest.get("release_state", {})
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release_state.get(key) is False, f"release_state.{key} must be false")
    require(release_state.get("current_go_no_go") == "NO_GO", "current Go/No-Go must remain NO_GO")

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing manifest evidence ref: {ref}")
    check_evidence_public_safe()

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "schema_version": manifest["schema_version"],
        "version": manifest["version"],
        "stage_phase": manifest["stage_phase"],
        "task_id": manifest["task_id"],
        "status": manifest["status"],
        "legacy_requirements": len(legacy_rows),
        "legacy_p0": legacy_counts.get("P0", 0),
        "legacy_p1": legacy_counts.get("P1", 0),
        "v14_overlay_requirements": len(v14_rows),
        "v14_overlay_p0": v14_counts.get("P0", 0),
        "v14_overlay_p1": v14_counts.get("P1", 0),
        "v14_stage_status_records": len(v14_stage_ids) + len(v14_phase_ids) + len(v14_task_ids),
        "v14_stages": baseline["v14_stages"],
        "v14_phases": baseline["v14_phases"],
        "v14_tasks": baseline["v14_tasks"],
        "phase_scope": scope,
        "raw_data_boundary": raw_boundary,
        "release_state": release_state,
        "next_recommended_phase": manifest["next_recommended_phase"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 S01-P3 no-omission baseline evidence.")
    parser.add_argument("--skip-legacy-no-omission", action="store_true")
    args = parser.parse_args()
    result = validate_v014_s01_p3_no_omission_baseline(run_legacy_check=not args.skip_legacy_no_omission)
    print(
        "PASS: KMFA v1.4 S01-P3 no-omission baseline validated "
        f"(legacy_requirements={result['legacy_requirements']}, "
        f"v14_overlay={result['v14_overlay_requirements']}, "
        f"stages={result['v14_stages']}, phases={result['v14_phases']}, "
        f"tasks={result['v14_tasks']}, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
