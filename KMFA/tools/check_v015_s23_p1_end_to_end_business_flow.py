#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S23-P1."""

from __future__ import annotations

import argparse
import csv
import json
import struct
import subprocess
import sys
from pathlib import Path

from KMFA.tools import build_v015_s23_p1_end_to_end_business_flow as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s23_p1_end_to_end_business_flow.py','KMFA/tools/run_v015_s23_p1_end_to_end_business_flow.py','KMFA/tools/build_v015_s23_p1_end_to_end_business_flow.py','KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py','KMFA/tools/run_v015_s23_p1_browser_tests.py','KMFA/tools/run_v015_s23_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_core_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p1_end_to_end_business_flow",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p1_end_to_end_business_flow_runtime",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p1_end_to_end_business_flow_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p1_end_to_end_business_flow_governance",
    ),
    (
        "focused_browser_tests",
        "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s23_p1_browser_tests.py",
    ),
    (
        "report_workflow_regression",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p3_report_workflow",
    ),
    (
        "recalculation_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s20_p3_recalculation_publication",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s23_p1_end_to_end_business_flow.py",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S23_P1_PENDING_FINAL_VALIDATION",
    ),
    (
        "registry_integrity",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py --registry-only",
    ),
    (
        "xlsx_signature",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py --xlsx-only",
    ),
    (
        "cross_format_consistency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py --consistency-only",
    ),
    (
        "no_float_money",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    ),
    (
        "no_omission",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    ),
    (
        "taskpack_source",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py --taskpack-source-check",
    ),
    (
        "scope_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p1_end_to_end_business_flow.py --scope-boundary-check",
    ),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S23_P1_END_TO_END_BUSINESS_FLOW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s23_p1_end_to_end_business_flow",
    "KMFA/tools/build_v015_s23_p1_",
    "KMFA/tools/check_v015_s23_p1_",
    "KMFA/tools/run_v015_s23_p1_",
    "KMFA/tools/v015_s23_p1_",
    "KMFA/tools/v015_s21_p3_report_workflow.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (
    ".github/workflows/kmfa-dual-plane.yml",
    "KMFA/machine/",
    "KMFA/文档/",
)


class CheckError(RuntimeError):
    """S23-P1 validation failed."""


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _preserved(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _allowed(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PHASE_PREFIXES)


def _check_changed_paths() -> None:
    changed = set(_git("-c", "core.quotepath=false", "diff", "--name-only", builder.PHASE_BASE_COMMIT, "--").splitlines())
    changed.update(
        line
        for line in _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines()
        if line and not _preserved(line)
    )
    unexpected = sorted(path for path in changed if path and not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S23-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value["acceptance_status"] != "PASSED" or value["overall_accepted_phase_count"] != 64:
        raise CheckError("S22 总体复审依赖不是已通过的 64/72 状态")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    stages = _json(path).get("stages", []) if path.is_file() else []
    stage = next((row for row in stages if row.get("id") == "S23"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P1"), None)
    expected = [
        ("T01", "验证经营首页任务", "后端状态、页面和报告一致。", "仅 DOM 变化不得判通过。"),
        ("T02", "验证项目成本与差异处理", "权威项目零差异。", "任一分差异失败。"),
        ("T03", "验证报告与导出", "页面、HTML、PDF、Excel 一致。", "不一致阻塞。"),
    ]
    actual = [(row.get("id"), row.get("name"), row.get("acceptance"), row.get("stop")) for row in (phase or {}).get("tasks", [])]
    if actual != expected:
        raise CheckError("S23-P1 TaskPack source drift")


def _check_registry() -> None:
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [
        row for row in rows
        if row.get("parameter_id", "").startswith("PARAM-KMFA-")
        and 2986 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 3005
    ]
    if len(selected) != 20 or any(
        row["model_id"] != "MOD-KMFA-END-TO-END-ACCEPTANCE-001"
        or row["formula_id"] != "FORM-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-001"
        or row["status"] != "active"
        for row in selected
    ):
        raise CheckError("S23-P1 parameter registry mismatch")
    combined = "\n".join(
        (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            "docs/governance/model_registry.yaml",
            "metadata/model_registry.yaml",
            "docs/governance/formula_registry.yaml",
            "docs/governance/TRACEABILITY_MATRIX.csv",
            "docs/governance/VERSION_MATRIX.yaml",
        )
    )
    for token in (
        "MOD-KMFA-END-TO-END-ACCEPTANCE-001",
        "FORM-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-001",
        "PARAM-KMFA-2986",
        "PARAM-KMFA-3005",
        "REQ-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW",
    ):
        if token not in combined:
            raise CheckError(f"governance registry missing {token}")


def _check_xlsx() -> None:
    if not builder.DELIVERABLE_PATH.is_file() or builder.DELIVERABLE_PATH.stat().st_size < 5_000:
        raise CheckError("S23-P1 Excel deliverable missing")
    if builder.DELIVERABLE_PATH.read_bytes()[:2] != b"PK":
        raise CheckError("S23-P1 Excel deliverable is not an XLSX file")
    consistency = _json(builder.CONSISTENCY_PATH)
    if consistency.get("deliverable_sha256") != builder._sha256(builder.DELIVERABLE_PATH):
        raise CheckError("S23-P1 Excel deliverable hash mismatch")


def _check_consistency() -> None:
    value = _json(builder.CONSISTENCY_PATH)
    expected = {
        "status": "PASS",
        "format_count": 4,
        "numeric_value_count": 26,
        "difference_integer": 0,
        "project_difference_cents": 0,
        "xlsx_sheet_count": 3,
        "xlsx_formula_error_count": 0,
        "xlsx_visual_pass_count": 3,
    }
    mismatch = [key for key, expected_value in expected.items() if value.get(key) != expected_value]
    if mismatch or value.get("formats") != ["HTML", "PDF", "CSV", "XLSX"]:
        raise CheckError("cross-format consistency mismatch: " + ", ".join(mismatch or ["formats"]))


def _check_scope_boundary() -> None:
    value = _json(builder.MANIFEST_PATH)
    for key in ("raw_root_access_count", "raw_write_count", "external_network_request_count"):
        if value.get(key) != 0:
            raise CheckError(f"scope boundary counter is nonzero: {key}")
    if any(
        value.get(key) is not False
        for key in (
            "s23_p2_started", "s23_p3_started", "s23_stage_review_started",
            "s23_stage_review_performed", "github_upload_performed", "app_reinstall_performed",
        )
    ):
        raise CheckError("later phase or release boundary was crossed")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH, builder.SOURCE_CONTRACT_PATH, builder.PUBLIC_VERIFICATION_PATH,
        builder.TRACE_PATH, builder.CONSISTENCY_PATH, builder.BROWSER_PATH, builder.TASK_MATRIX_PATH,
        builder.COMPLETION_REPORT_PATH, builder.TEST_RESULTS_PATH, builder.USER_GUIDE_PATH,
        builder.RISKS_ROLLBACK_PATH, builder.DELIVERABLE_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CheckError("missing S23-P1 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S23-P1 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S23-P1 evidence")
    expected = {
        "run_phase_id": "V015_S23_P1_END_TO_END_BUSINESS_FLOW",
        "roadmap_phase_id": "S23-P1",
        "phase_task_count": 3,
        "overall_total_phase_count": 72,
        "stage_execution_percentage": 33,
        "stage_acceptance_status": "PENDING",
        "public_check_count": 47,
        "public_check_pass_count": 47,
        "public_check_failed_count": 0,
        "core_test_count": 5,
        "runtime_test_count": 3,
        "browser_flow_count": 11,
        "visual_evidence_count": 8,
        "publication_version_count": 1,
        "backend_view_count": 4,
        "homepage_authoritative_binding_count": 1,
        "authoritative_project_count": 4,
        "project_difference_cents": 0,
        "report_version_count": 2,
        "report_export_count": 2,
        "export_format_count": 4,
        "cross_format_numeric_value_count": 26,
        "cross_format_difference_integer": 0,
        "xlsx_sheet_count": 3,
        "xlsx_formula_error_count": 0,
        "xlsx_visual_pass_count": 3,
        "workflow_case_count": 2,
        "workflow_step_count_per_case": 5,
        "revision_source_difference_count": 1,
        "revision_unexplained_difference_count": 0,
        "refresh_persistence_pass_count": 1,
        "governance_model_count": 23,
        "active_formula_count": 405,
        "active_parameter_count": 2620,
        "current_parameter_range": "PARAM-KMFA-2986..3005",
        "s23_p1_started": True,
        "s23_p2_started": False,
        "s23_p3_started": False,
        "s23_stage_review_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    mismatch = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatch:
        raise CheckError("S23-P1 manifest mismatch: " + ", ".join(mismatch))
    expected_state = {
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": 20 if final else 0,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 65 if final else 64,
        "overall_phase_acceptance_percent": 90.3 if final else 88.9,
        "decision": "GO_TO_S23_P2_ONLY" if final else "REMAIN_IN_S23_P1_FINAL_VALIDATION",
        "next_gate_id": "S23-P2" if final else "S23-P1-FINAL-VALIDATION",
        "s23_p1_completed": final,
        "s23_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s23_p2_entry_allowed": final,
    }
    mismatch = [key for key, expected_value in expected_state.items() if manifest.get(key) != expected_value]
    if mismatch:
        raise CheckError("S23-P1 acceptance state mismatch: " + ", ".join(mismatch))
    verification = _json(builder.PUBLIC_VERIFICATION_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    browser = _json(builder.BROWSER_PATH)
    if (verification.get("status"), verification.get("check_count"), verification.get("pass_count"), verification.get("fail_count")) != ("PASS", 47, 47, 0):
        raise CheckError("public verification failed")
    if matrix.get("phase_task_count") != 3 or len(matrix.get("tasks", [])) != 3 or any(row.get("status") != "PASS" for row in matrix["tasks"]):
        raise CheckError("task acceptance matrix failed")
    if (browser.get("browser_flow_count"), browser.get("visual_evidence_count"), browser.get("external_network_request_count")) != (11, 8, 0):
        raise CheckError("browser acceptance contract failed")
    for index, path in enumerate(builder.SCREENSHOT_PATHS):
        if not path.is_file() or path.stat().st_size < 10_000:
            raise CheckError(f"missing browser visual: {path.relative_to(REPO_ROOT)}")
        data = path.read_bytes()[:24]
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise CheckError(f"invalid browser visual: {path.relative_to(REPO_ROOT)}")
        width, height = struct.unpack(">II", data[16:24])
        if index < 7 and (width < 1000 or height < 700):
            raise CheckError(f"desktop browser visual too small: {path.relative_to(REPO_ROOT)}")
        if index == 7 and (width != 390 or height < 800):
            raise CheckError("mobile browser visual dimensions mismatch")
    _check_consistency()
    _check_xlsx()
    _check_scope_boundary()
    if not skip_receipts:
        rows = builder.receipts()
        if final:
            if len(rows) != 20 or [row.get("name") for row in rows] != list(builder.EXPECTED_VALIDATION_NAMES):
                raise CheckError("formal validation receipts are incomplete")
            if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
                raise CheckError("formal validation receipt failed")
            if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")} or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
                raise CheckError("formal validation receipt binding mismatch")
        elif rows:
            raise CheckError("pending evidence must not contain formal receipts")


def check(*, require_final: bool | None = None, skip_receipts: bool = False) -> None:
    _check_dependency()
    _check_taskpack_source()
    _check_registry()
    _check_changed_paths()
    _check_artifacts(require_final=require_final, skip_receipts=skip_receipts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--require-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--scope-boundary-check", action="store_true")
    parser.add_argument("--registry-only", action="store_true")
    parser.add_argument("--xlsx-only", action="store_true")
    parser.add_argument("--consistency-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.scope_boundary_check:
            _check_scope_boundary()
        elif args.registry_only:
            _check_registry()
        elif args.xlsx_only:
            _check_xlsx()
        elif args.consistency_only:
            _check_consistency()
        else:
            check(
                require_final=True if args.require_final else (False if args.pre_final else None),
                skip_receipts=args.skip_validation_receipts,
            )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S23-P1 acceptance checker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
