#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S01-P3 no-omission gate evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S01_NO_OMISSION_GATE/machine/s01_p3_no_omission_gate_manifest.json")
S01_P2_MANIFEST = Path("KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/machine/s01_p2_scope_freeze_manifest.json")
LEGACY_S01_P3_MANIFEST = Path("KMFA/stage_artifacts/S01_P3_no_omission_baseline/machine/s01_p3_manifest.json")
REQUIREMENTS = Path("KMFA/metadata/traceability/requirements.csv")
STAGE_STATUS = Path("KMFA/metadata/stage_status.jsonl")
NO_OMISSION_TOOL = Path("KMFA/tools/no_omission_check.py")
EXTERNAL_V013_ROADMAP = Path("/Users/linzezhang/Downloads/10_Codex_v0_1_3_Roadmap_STAGE_PHASE_TASK.md")
LOCAL_RAW_DATA_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
EVIDENCE_FILES = [
    Path("KMFA/stage_artifacts/V013_S01_NO_OMISSION_GATE/human/no_omission_gate_record.md"),
    Path("KMFA/stage_artifacts/V013_S01_NO_OMISSION_GATE/human/stage_status_replay_record.md"),
    Path("KMFA/stage_artifacts/V013_S01_NO_OMISSION_GATE/human/test_results.md"),
]
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value",
    "normalized_value",
    "source_header_text",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----BEGIN",
    "sk-",
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


def git_output(args: list[str]) -> str:
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


def run_no_omission_check() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(NO_OMISSION_TOOL)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"no_omission_check failed: {result.stdout.strip()} {result.stderr.strip()}".strip())
    match = re.search(
        r"requirements=(?P<requirements>\d+), P0=(?P<p0>\d+), P1=(?P<p1>\d+), "
        r"status_records=(?P<stage_status_records>\d+), tasks=(?P<task_records>\d+)",
        result.stdout,
    )
    if not match:
        raise ValidationError(f"no_omission_check output did not expose expected counts: {result.stdout.strip()}")
    parsed = {key: int(value) for key, value in match.groupdict().items()}
    parsed["result"] = "PASS"
    parsed["stdout"] = result.stdout.strip()
    return parsed


def count_requirements() -> dict[str, int]:
    if not REQUIREMENTS.exists():
        raise ValidationError(f"missing requirements matrix: {REQUIREMENTS}")
    with REQUIREMENTS.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "requirements": len(rows),
        "p0": sum(1 for row in rows if row.get("priority") == "P0"),
        "p1": sum(1 for row in rows if row.get("priority") == "P1"),
    }


def is_baseline_status_record(record: dict[str, Any]) -> bool:
    record_type = str(record.get("record_type") or "")
    phase_id = str(record.get("phase_id") or "")
    return not (record_type.startswith("v013_") or phase_id.startswith("V013_"))


def count_stage_status() -> dict[str, int]:
    if not STAGE_STATUS.exists():
        raise ValidationError(f"missing stage status registry: {STAGE_STATUS}")
    records: list[dict[str, Any]] = []
    task_ids: set[str] = set()
    for line_no, line in enumerate(STAGE_STATUS.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{STAGE_STATUS}:{line_no} must contain a JSON object")
        if not is_baseline_status_record(value):
            continue
        records.append(value)
        if value.get("record_type") == "task" and value.get("task_id"):
            task_ids.add(str(value["task_id"]))
    return {"stage_status_records": len(records), "task_records": len(task_ids)}


def validate_s01_p3_no_omission_gate(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s01_p2 = read_json(S01_P2_MANIFEST)
    legacy = read_json(LEGACY_S01_P3_MANIFEST)
    no_omission = run_no_omission_check()
    requirement_counts = count_requirements()
    stage_counts = count_stage_status()

    require(manifest.get("schema_version") == "kmfa.v013_s01_p3_no_omission_gate.v1", "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "manifest project_id mismatch")
    require(manifest.get("stage_phase") == "S01-P3", "manifest stage_phase must be S01-P3")
    require(manifest.get("task_id") == "KMFA-V013-S01-P3-NO-OMISSION-GATE-20260702", "task_id mismatch")
    require(manifest.get("phase_scope") == "no_omission_gate_replay_only", "phase_scope mismatch")
    require(manifest.get("governance_product_version") == "0.1.3-s01p3-no-omission-gate", "governance version mismatch")
    require(manifest.get("external_v013_roadmap_available") == EXTERNAL_V013_ROADMAP.exists(), "external roadmap availability mismatch")
    require(manifest.get("external_v013_roadmap_available") is False, "external roadmap must remain recorded unavailable")

    manifest_counts = manifest.get("no_omission", {})
    for key in ("requirements", "p0", "p1", "task_records"):
        require(manifest_counts.get(key) == no_omission.get(key), f"manifest no_omission {key} mismatch")
    require(manifest_counts.get("stage_status_records") == 549, "historical stage status snapshot mismatch")
    require(
        no_omission.get("stage_status_records", 0) >= manifest_counts.get("stage_status_records", 0),
        "current stage status registry regressed below the historical snapshot",
    )
    require(manifest_counts.get("result") == "PASS", "manifest no_omission result must be PASS")
    require(no_omission.get("requirements") == requirement_counts["requirements"] == 20, "requirements count mismatch")
    require(no_omission.get("p0") == requirement_counts["p0"] == 9, "P0 requirement count mismatch")
    require(no_omission.get("p1") == requirement_counts["p1"] == 8, "P1 requirement count mismatch")
    require(
        stage_counts["stage_status_records"] >= manifest_counts.get("stage_status_records", 0),
        "stage status record count regressed below the historical snapshot",
    )
    require(no_omission.get("task_records") == stage_counts["task_records"] == 162, "task record count mismatch")

    legacy_counts = legacy.get("no_omission", {})
    require(legacy_counts.get("requirements") == 20, "legacy S01-P3 requirements count mismatch")
    require(legacy_counts.get("p0") == 9, "legacy S01-P3 P0 count mismatch")
    require(legacy_counts.get("p1") == 8, "legacy S01-P3 P1 count mismatch")
    require(legacy_counts.get("task_records") == 162, "legacy S01-P3 task count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == str(LOCAL_RAW_DATA_DIR), "raw data directory mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "Codex must not modify raw data directory")
    require(raw_boundary.get("github_commit_allowed") is False, "raw data directory must not be committed")

    require(s01_p2.get("next_required_step", "").startswith("S01-P3"), "S01-P2 next step must authorize S01-P3 only")
    require(manifest.get("stage_review_scope_included") is False, "Stage review must not be included in S01-P3")
    require(manifest.get("github_upload_this_phase") is False, "GitHub upload must not be included in S01-P3")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_execution_allowed") is False, "business_execution_allowed must remain false")
    require(manifest.get("raw_business_data_committed") is False, "raw business data must not be committed")
    require(manifest.get("zip_committed") is False, "zip files must not be committed")
    require(manifest.get("excel_workbook_committed") is False, "Excel workbooks must not be committed")
    require(manifest.get("pdf_committed") is False, "PDF files must not be committed")
    require(manifest.get("private_csv_committed") is False, "private CSV files must not be committed")
    require(manifest.get("credentials_committed") is False, "credentials must not be committed")
    require(
        manifest.get("next_required_step") == "Stage 1 review; do not upload GitHub until review findings are fixed.",
        "next step mismatch",
    )

    for ref in manifest.get("source_evidence_refs", []):
        ref_path = Path(ref)
        require(ref_path.exists(), f"missing source evidence ref: {ref}")
    for evidence in EVIDENCE_FILES:
        require(evidence.exists(), f"missing human evidence: {evidence}")
        text = evidence.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_EVIDENCE_TEXT:
            require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_phase": manifest["stage_phase"],
        "phase_scope": manifest["phase_scope"],
        "governance_product_version": manifest["governance_product_version"],
        "no_omission": manifest_counts,
        "stage_review_scope_included": manifest["stage_review_scope_included"],
        "github_upload_this_phase": manifest["github_upload_this_phase"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S01-P3 no-omission gate evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_s01_p3_no_omission_gate(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S01-P3 no-omission gate validation failed")
        print(exc)
        return 1
    counts = result["no_omission"]
    print(
        "PASS: KMFA v0.1.3 S01-P3 no-omission gate remains local-only "
        f"(requirements={counts['requirements']}, P0={counts['p0']}, P1={counts['p1']}, "
        f"stage_status_records={counts['stage_status_records']}, task_records={counts['task_records']}, "
        f"stage_review={str(result['stage_review_scope_included']).lower()}, "
        f"github_upload={str(result['github_upload_this_phase']).lower()}, "
        f"delivery_allowed={str(result['delivery_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
