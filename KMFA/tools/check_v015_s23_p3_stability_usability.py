#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S23-P3."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

from KMFA.tools import build_v015_s23_p3_stability_usability as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s23_p3_stability_usability.py','KMFA/tools/build_v015_s23_p3_stability_usability.py','KMFA/tools/check_v015_s23_p3_stability_usability.py','KMFA/tools/run_v015_s23_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_core_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p3_stability_usability"),
    ("focused_browser_tests", "KMFA_PRESERVE_TRACKED_S23P3_BROWSER=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s23_p3_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p3_stability_usability_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p3_stability_usability_governance"),
    ("s23_p2_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p3_stability_usability.py --dependency-check"),
    ("app_shell_print_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s15_p1_app_shell KMFA.tests.test_v015_s15_p1_app_shell_browser KMFA.tests.test_v015_s15_p2_identity_roles_runtime"),
    ("s23_p1_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p1_end_to_end_business_flow"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s23_p3_stability_usability.py"),
    ("pre_final_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p3_stability_usability.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S23_P3_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p3_stability_usability.py --taskpack-source-check"),
    ("scope_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p3_stability_usability.py --scope-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md", "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/stage_artifacts/V015_S23_P3_STABILITY_USABILITY/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py", "KMFA/tests/test_v015_s23_p3_stability_usability",
    "KMFA/tools/build_v015_s23_p3_", "KMFA/tools/check_v015_s23_p3_", "KMFA/tools/run_v015_s23_p3_",
    "KMFA/tools/v015_s23_p3_", "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/run_v015_s15_p1_app_shell.py", "KMFA/tools/run_v015_s17_p3_project_workflow.py",
    "KMFA/stage_artifacts/V015_S15_P1_APP_SHELL/exports/screenshots/kmfa_app_shell_mobile.png",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")


class CheckError(RuntimeError):
    """S23-P3 validation failed."""


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
    changed.update(line for line in _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines() if line and not _preserved(line))
    unexpected = sorted(path for path in changed if path and not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S23-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value["acceptance_status"] != "PASSED" or value["overall_accepted_phase_count"] != 66:
        raise CheckError("S23-P2 依赖不是已通过的 66/72 状态")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    stages = _json(path).get("stages", []) if path.is_file() else []
    stage = next((row for row in stages if row.get("id") == "S23"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P3"), None)
    expected = [
        ("T01", "执行多轮回归和浸泡测试", "结果幂等，无内存或队列泄露。", "静默错误数必须为 0。"),
        ("T02", "执行真实用户可用性测试", "关键任务完成率和效率达标。", "明显机械或 AI 堆叠则重做。"),
        ("T03", "执行可访问性和多尺寸测试", "关键页面达到约定标准。", "关键信息只靠颜色失败。"),
    ]
    actual = [(row.get("id"), row.get("name"), row.get("acceptance"), row.get("stop")) for row in (phase or {}).get("tasks", [])]
    if actual != expected:
        raise CheckError("S23-P3 TaskPack source drift")


def _check_registry() -> None:
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 3026 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 3045]
    if len(selected) != 20 or any(row["model_id"] != "MOD-KMFA-STABILITY-USABILITY-001" or row["formula_id"] != "FORM-KMFA-V015-S23-P3-STABILITY-USABILITY-001" or row["status"] != "active" for row in selected):
        raise CheckError("S23-P3 parameter registry mismatch")
    combined = "\n".join((builder.PROJECT_ROOT / relative).read_text(encoding="utf-8") for relative in ("docs/governance/model_registry.yaml", "metadata/model_registry.yaml", "docs/governance/formula_registry.yaml", "docs/governance/TRACEABILITY_MATRIX.csv", "docs/governance/VERSION_MATRIX.yaml"))
    for token in ("MOD-KMFA-STABILITY-USABILITY-001", "FORM-KMFA-V015-S23-P3-STABILITY-USABILITY-001", "PARAM-KMFA-3026", "PARAM-KMFA-3045", "REQ-KMFA-V015-S23-P3-STABILITY-USABILITY"):
        if token not in combined:
            raise CheckError(f"governance registry missing {token}")


def _check_scope_boundary() -> None:
    value = _json(builder.MANIFEST_PATH)
    for key in ("raw_root_access_count", "raw_write_count", "external_network_request_count", "stage_review_execution_count", "s24_execution_count", "silent_error_count", "idempotency_failure_count", "queue_leak_count", "accessibility_fail_count"):
        if value.get(key) != 0:
            raise CheckError(f"S23-P3 zero boundary failed: {key}")
    if any(value.get(key) is not False for key in ("s23_stage_review_started", "s24_started", "github_upload_performed", "app_reinstall_performed")):
        raise CheckError("later phase or release boundary was crossed")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH, builder.SOURCE_CONTRACT_PATH, builder.SOAK_REPORT_PATH,
        builder.BROWSER_ACCEPTANCE_PATH, builder.PUBLIC_VERIFICATION_PATH, builder.USABILITY_REPORT_PATH,
        builder.ACCESSIBILITY_REPORT_PATH, builder.TASK_MATRIX_PATH, builder.COMPLETION_REPORT_PATH,
        builder.STABILITY_REPORT_ZH_PATH, builder.USABILITY_REPORT_ZH_PATH,
        builder.ACCESSIBILITY_REPORT_ZH_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CheckError("missing S23-P3 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S23-P3 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S23-P3 evidence")
    expected = {
        "run_phase_id": "V015_S23_P3_STABILITY_USABILITY", "roadmap_phase_id": "S23-P3",
        "phase_task_count": 3, "overall_total_phase_count": 72, "stage_execution_percentage": 100,
        "stage_acceptance_status": "PENDING", "public_check_count": 60, "public_check_pass_count": 60,
        "public_check_failed_count": 0, "soak_cycle_count": 12, "repeated_import_count": 12,
        "repeated_recalculation_count": 12, "repeated_report_count": 12, "restart_count": 3,
        "refresh_count": 24, "idempotency_failure_count": 0, "silent_error_count": 0,
        "queue_leak_count": 0, "temporary_file_leak_count": 0, "thread_leak_count": 0,
        "memory_growth_budget_bytes": 8388608, "memory_growth_excess_count": 0,
        "soak_elapsed_budget_ms": 60000, "usability_task_count": 3,
        "completed_usability_task_count": 3, "usability_completion_rate_bps": 10000,
        "usability_total_budget_ms": 30000, "technical_document_dependency_count": 0,
        "technical_term_exposure_count": 0, "mechanical_ai_issue_count": 0,
        "accessibility_check_count": 34, "accessibility_fail_count": 0,
        "contrast_sample_count": 10, "contrast_fail_count": 0, "narrow_viewport_count": 2,
        "narrow_overflow_count": 0, "touch_target_fail_count": 0,
        "color_only_critical_info_count": 0, "browser_page_error_count": 0,
        "browser_external_network_request_count": 0, "screenshot_count": 7,
        "governance_model_count": 25, "active_formula_count": 407, "active_parameter_count": 2660,
        "current_parameter_range": "PARAM-KMFA-3026..3045", "s23_p3_started": True,
        "s23_stage_review_started": False, "s24_started": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
    }
    mismatch = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatch:
        raise CheckError("S23-P3 manifest mismatch: " + ", ".join(mismatch))
    if manifest["memory_growth_bytes"] > manifest["memory_growth_budget_bytes"] or manifest["soak_elapsed_ms"] > manifest["soak_elapsed_budget_ms"] or manifest["usability_total_elapsed_ms"] > manifest["usability_total_budget_ms"] or manifest["usability_max_interaction_count"] > 8:
        raise CheckError("S23-P3 stability or usability budget failed")
    state = {
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": 20 if final else 0,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 67 if final else 66,
        "overall_phase_acceptance_percent": 93.1 if final else 91.7,
        "decision": "GO_TO_S23_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S23_P3_FINAL_VALIDATION",
        "next_gate_id": "S23-STAGE-REVIEW" if final else "S23-P3-FINAL-VALIDATION",
        "s23_p3_completed": final, "s23_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s23_stage_review_entry_allowed": final, "s24_entry_allowed": False,
    }
    mismatch = [key for key, expected_value in state.items() if manifest.get(key) != expected_value]
    if mismatch:
        raise CheckError("S23-P3 acceptance state mismatch: " + ", ".join(mismatch))
    verification, soak = _json(builder.PUBLIC_VERIFICATION_PATH), _json(builder.SOAK_REPORT_PATH)
    browser, accessibility = _json(builder.BROWSER_ACCEPTANCE_PATH), _json(builder.ACCESSIBILITY_REPORT_PATH)
    if (verification.get("status"), verification.get("check_count"), verification.get("pass_count"), verification.get("fail_count")) != ("PASS", 60, 60, 0):
        raise CheckError("public verification failed")
    if soak.get("status") != "PASS" or browser.get("status") != "PASS" or accessibility.get("fail_count") != 0:
        raise CheckError("soak or browser evidence failed")
    matrix = _json(builder.TASK_MATRIX_PATH)
    if matrix.get("phase_task_count") != 3 or len(matrix.get("tasks", [])) != 3 or any(row.get("status") != "PASS" for row in matrix["tasks"]):
        raise CheckError("task acceptance matrix failed")
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
    _check_dependency(); _check_taskpack_source(); _check_registry(); _check_changed_paths()
    _check_artifacts(require_final=require_final, skip_receipts=skip_receipts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--scope-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check: _check_dependency()
        elif args.taskpack_source_check: _check_taskpack_source()
        elif args.scope_boundary_check: _check_scope_boundary()
        else: check(require_final=False if args.pre_final else True, skip_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, builder.BuildError, CheckError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S23-P3 strict checker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
