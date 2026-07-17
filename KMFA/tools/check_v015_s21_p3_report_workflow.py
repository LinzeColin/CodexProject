#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S21-P3 report workflow."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s21_p3_report_workflow as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s21_p3_report_workflow.py','KMFA/tools/run_v015_s21_p3_report_workflow.py','KMFA/tools/build_v015_s21_p3_report_workflow.py','KMFA/tools/check_v015_s21_p3_report_workflow.py','KMFA/tools/run_v015_s21_p3_browser_tests.py','KMFA/tools/run_v015_s21_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_unit_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p3_report_workflow"),
    ("focused_runtime_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p3_report_workflow_runtime"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s21_p3_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p3_report_workflow_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p3_report_workflow_governance"),
    ("s21_p2_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p3_report_workflow.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s21_p3_report_workflow.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p3_report_workflow.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S21_P3_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p3_report_workflow.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p3_report_workflow.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s21_p3_report_workflow.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/stage_artifacts/V015_S21_P3_REPORT_WORKFLOW/",
    "KMFA/taskpack/v1_5/", "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s21_p3_report_workflow.py", "KMFA/tests/test_v015_s21_p3_report_workflow_runtime.py",
    "KMFA/tests/test_v015_s21_p3_report_workflow_browser.py", "KMFA/tests/test_v015_s21_p3_report_workflow_artifacts.py",
    "KMFA/tests/test_v015_s21_p3_report_workflow_governance.py", "KMFA/tools/build_v015_s21_p3_report_workflow.py",
    "KMFA/tools/check_v015_s21_p3_report_workflow.py", "KMFA/tools/run_v015_s21_p3_browser_tests.py",
    "KMFA/tools/run_v015_s21_p3_report_workflow.py", "KMFA/tools/run_v015_s21_p3_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py", "KMFA/tools/v015_s21_p3_report_workflow.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")


class CheckError(RuntimeError):
    """S21-P3 validation failed."""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S21-P3 base commit is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(line for line in _git(*args).splitlines() if line and not _preserved(line))
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S21-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value["acceptance_status"] != "PASSED" or value["overall_accepted_phase_count"] != 60:
        raise CheckError("S21-P2 dependency is not the accepted 60/72 handoff")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    if not path.is_file():
        raise CheckError("tracked v1.5 roadmap is missing")
    stages = _json(path).get("stages", [])
    stage = next((row for row in stages if row.get("id") == "S21"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P3"), None)
    expected = [
        ("T01", "实现预览、复核、批准和发布", "未通过质量门禁不得发布。"),
        ("T02", "实现报告比较与修订", "不能解释的变化阻塞。"),
        ("T03", "实现报告中心", "敏感报告不得公开链接。"),
    ]
    actual = [(row.get("id"), row.get("name"), row.get("stop")) for row in (phase or {}).get("tasks", [])]
    if actual != expected:
        raise CheckError("S21-P3 TaskPack source drift")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH, builder.SOURCE_CONTRACT_PATH, builder.QUALITY_GATE_PATH,
        builder.WORKFLOW_PATH, builder.COMPARISON_PATH, builder.REPORT_CENTER_PATH,
        builder.BROWSER_PATH, builder.PUBLIC_CHECKS_PATH, builder.TASK_MATRIX_PATH,
        builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH,
        builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CheckError("missing S21-P3 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S21-P3 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S21-P3 evidence")
    expected_manifest = {
        "run_phase_id": "V015_S21_P3_REPORT_WORKFLOW", "roadmap_phase_id": "S21-P3",
        "workflow_action_count": 5, "workflow_event_count": 5, "quality_gate_check_count": 15,
        "unexplained_difference_count": 0, "report_center_filter_count": 6,
        "authenticated_download_format_count": 3, "public_check_count": 53,
        "public_check_failed_count": 0, "browser_flow_count": 8,
        "visual_evidence_count": 6, "history_overwrite_count": 0,
        "raw_root_access_count": 0, "raw_write_count": 0,
        "external_network_request_count": 0, "internal_approval_count": 1,
        "internal_publication_count": 1, "external_publication_count": 0,
        "public_share_link_count": 0, "cross_company_access_success_count": 0,
        "s21_p3_started": True, "s21_stage_review_started": False,
        "s22_entry_allowed": False, "s22_p1_started": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "data_classification": "PUBLIC_SYNTHETIC_ONLY",
    }
    mismatch = [key for key, value in expected_manifest.items() if manifest.get(key) != value]
    if mismatch:
        raise CheckError("S21-P3 manifest mismatch: " + ", ".join(mismatch))
    quality, workflow = _json(builder.QUALITY_GATE_PATH), _json(builder.WORKFLOW_PATH)
    comparison, center = _json(builder.COMPARISON_PATH), _json(builder.REPORT_CENTER_PATH)
    checks, browser, matrix = _json(builder.PUBLIC_CHECKS_PATH), _json(builder.BROWSER_PATH), _json(builder.TASK_MATRIX_PATH)
    if (quality.get("status"), quality.get("check_count"), quality.get("failed_count")) != ("PASS", 15, 0):
        raise CheckError("quality gate contract failed")
    if (workflow.get("published_case_state"), workflow.get("event_count"), workflow.get("external_publication_count")) != ("PUBLISHED_INTERNAL", 5, 0):
        raise CheckError("workflow contract failed")
    if comparison.get("difference_count", 0) < 1 or comparison.get("unexplained_difference_count") != 0 or comparison.get("publication_allowed") is not True:
        raise CheckError("revision comparison contract failed")
    if (center.get("filter_count"), center.get("tax_download_format_count"), center.get("public_link_count")) != (6, 0, 0):
        raise CheckError("report center contract failed")
    if (checks.get("status"), checks.get("public_check_count"), checks.get("public_check_failed_count")) != ("PASS", 53, 0):
        raise CheckError("public checks failed")
    if (browser.get("browser_flow_count"), browser.get("visual_evidence_count")) != (8, 6):
        raise CheckError("browser contract failed")
    if matrix.get("phase_task_count") != 3 or len(matrix.get("tasks", [])) != 3 or any(row.get("status") != "PASS" for row in matrix["tasks"]):
        raise CheckError("task acceptance matrix failed")
    for path in builder.SCREENSHOT_PATHS:
        if not path.is_file() or path.stat().st_size < 10_000:
            raise CheckError(f"missing browser visual: {path.relative_to(REPO_ROOT)}")
    if final:
        expected_final = {
            "evidence_validation_status": "PASS", "validation_receipt_count": 20,
            "phase_task_accepted_count": 3, "overall_accepted_phase_count": 61,
            "decision": "GO_TO_S21_STAGE_REVIEW_ONLY", "next_gate_id": "S21-STAGE-REVIEW",
            "s21_p3_completed": True, "s21_p3_acceptance_status": "PASSED",
            "s21_stage_review_entry_allowed": True,
        }
    else:
        expected_final = {
            "evidence_validation_status": "PENDING", "validation_receipt_count": 0,
            "phase_task_accepted_count": 0, "overall_accepted_phase_count": 60,
            "decision": "REMAIN_IN_S21_P3_FINAL_VALIDATION", "next_gate_id": "S21-P3-FINAL-VALIDATION",
            "s21_p3_completed": False, "s21_p3_acceptance_status": "PENDING_FINAL_VALIDATION",
            "s21_stage_review_entry_allowed": False,
        }
    mismatch = [key for key, value in expected_final.items() if manifest.get(key) != value]
    if mismatch:
        raise CheckError("S21-P3 acceptance-state mismatch: " + ", ".join(mismatch))
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


def _check_public_boundary() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    zeros = (
        "raw_root_access_count", "raw_write_count", "external_network_request_count",
        "external_publication_count", "public_share_link_count", "cross_company_access_success_count",
    )
    if any(manifest.get(key) != 0 for key in zeros):
        raise CheckError("public boundary counters are not zero")
    if manifest.get("github_upload_performed") is not False or manifest.get("app_reinstall_performed") is not False:
        raise CheckError("release boundary was crossed")
    source = _json(builder.SOURCE_CONTRACT_PATH)
    if source.get("data_classification") != "PUBLIC_SYNTHETIC_ONLY" or "raw" not in source.get("excluded", []):
        raise CheckError("source boundary is not public-synthetic-only")
    runtime = (builder.PROJECT_ROOT / "tools/v015_s21_p3_report_workflow.py").read_text(encoding="utf-8")
    if "/Users/" in runtime or "KMFA_MetaData" in runtime or re.search(r"https?://", runtime):
        raise CheckError("S21-P3 kernel contains raw path or external URL")


def _check_clean_governance_sync() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    state = "S21_P3_PASSED" if manifest.get("phase_acceptance_status") == "PASSED" else "S21_P3_PENDING_FINAL_VALIDATION"
    result = subprocess.run(
        [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check", "--validation-state", state],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise CheckError("governance sync mismatch\n" + (result.stdout + result.stderr)[-4000:])


def run(*, require_final: bool | None = None, skip_validation_receipts: bool = False) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts(require_final=require_final, skip_receipts=skip_validation_receipts)
    _check_public_boundary()
    _check_clean_governance_sync()


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S21-P3 报告工作流")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        else:
            run(require_final=False if args.pre_final else None, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S21-P3 report workflow is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
