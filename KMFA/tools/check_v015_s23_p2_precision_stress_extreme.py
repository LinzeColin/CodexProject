#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S23-P2."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

from KMFA.tools import build_v015_s23_p2_precision_stress_extreme as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s23_p2_precision_stress_extreme.py','KMFA/tools/build_v015_s23_p2_precision_stress_extreme.py','KMFA/tools/check_v015_s23_p2_precision_stress_extreme.py','KMFA/tools/run_v015_s23_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_core_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p2_precision_stress_extreme"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p2_precision_stress_extreme_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s23_p2_precision_stress_extreme_governance"),
    ("s23_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p2_precision_stress_extreme.py --dependency-check"),
    ("import_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s20_p1_data_update"),
    ("report_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s21_p2_report_generation"),
    ("security_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s23_p2_precision_stress_extreme.py"),
    ("pre_final_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p2_precision_stress_extreme.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S23_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p2_precision_stress_extreme.py --taskpack-source-check"),
    ("scope_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s23_p2_precision_stress_extreme.py --scope-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md", "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/stage_artifacts/V015_S23_P2_PRECISION_STRESS_EXTREME/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py", "KMFA/tests/test_v015_s23_p2_precision_stress_extreme",
    "KMFA/tools/build_v015_s23_p2_", "KMFA/tools/check_v015_s23_p2_", "KMFA/tools/run_v015_s23_p2_",
    "KMFA/tools/v015_s23_p2_", "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")


class CheckError(RuntimeError):
    """S23-P2 validation failed."""


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
        raise CheckError("unexpected S23-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value["acceptance_status"] != "PASSED" or value["overall_accepted_phase_count"] != 65:
        raise CheckError("S23-P1 依赖不是已通过的 65/72 状态")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    stages = _json(path).get("stages", []) if path.is_file() else []
    stage = next((row for row in stages if row.get("id") == "S23"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P2"), None)
    expected = [
        ("T01", "执行金额精密测试", "0 分误差。", "任何 float 路径失败。"),
        ("T02", "执行规模与并发测试", "达到约定响应和资源门槛。", "数据错误优先于性能。"),
        ("T03", "执行极限和恶意输入测试", "系统安全失败且可恢复。", "数据污染为高危失败。"),
    ]
    actual = [(row.get("id"), row.get("name"), row.get("acceptance"), row.get("stop")) for row in (phase or {}).get("tasks", [])]
    if actual != expected:
        raise CheckError("S23-P2 TaskPack source drift")


def _check_registry() -> None:
    with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("parameter_id", "").startswith("PARAM-KMFA-") and 3006 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 3025]
    if len(selected) != 20 or any(row["model_id"] != "MOD-KMFA-PRECISION-STRESS-001" or row["formula_id"] != "FORM-KMFA-V015-S23-P2-PRECISION-STRESS-EXTREME-001" or row["status"] != "active" for row in selected):
        raise CheckError("S23-P2 parameter registry mismatch")
    combined = "\n".join((builder.PROJECT_ROOT / relative).read_text(encoding="utf-8") for relative in ("docs/governance/model_registry.yaml", "metadata/model_registry.yaml", "docs/governance/formula_registry.yaml", "docs/governance/TRACEABILITY_MATRIX.csv", "docs/governance/VERSION_MATRIX.yaml"))
    for token in ("MOD-KMFA-PRECISION-STRESS-001", "FORM-KMFA-V015-S23-P2-PRECISION-STRESS-EXTREME-001", "PARAM-KMFA-3006", "PARAM-KMFA-3025", "REQ-KMFA-V015-S23-P2-PRECISION-STRESS-EXTREME"):
        if token not in combined:
            raise CheckError(f"governance registry missing {token}")


def _check_scope_boundary() -> None:
    value = _json(builder.MANIFEST_PATH)
    for key in ("raw_root_access_count", "raw_write_count", "external_network_request_count", "data_error_count", "data_pollution_count", "float_money_accept_count"):
        if value.get(key) != 0:
            raise CheckError(f"S23-P2 zero boundary failed: {key}")
    if any(value.get(key) is not False for key in ("s23_p3_started", "s23_stage_review_started", "github_upload_performed", "app_reinstall_performed")):
        raise CheckError("later phase or release boundary was crossed")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH, builder.SOURCE_CONTRACT_PATH, builder.PUBLIC_VERIFICATION_PATH,
        builder.PRECISION_REPORT_PATH, builder.PERFORMANCE_REPORT_PATH, builder.EXTREME_REPORT_PATH,
        builder.TASK_MATRIX_PATH, builder.COMPLETION_REPORT_PATH, builder.PRECISION_REPORT_ZH_PATH,
        builder.PERFORMANCE_REPORT_ZH_PATH, builder.EXTREME_REPORT_ZH_PATH,
        builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CheckError("missing S23-P2 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S23-P2 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S23-P2 evidence")
    expected = {
        "run_phase_id": "V015_S23_P2_PRECISION_STRESS_EXTREME", "roadmap_phase_id": "S23-P2",
        "phase_task_count": 3, "overall_total_phase_count": 72, "stage_execution_percentage": 67,
        "stage_acceptance_status": "PENDING", "public_check_count": 49, "public_check_pass_count": 49,
        "public_check_failed_count": 0, "precision_case_count": 20000,
        "maximum_absolute_cents": 9000000000000000, "rounding_difference_count": 0,
        "cross_sheet_difference_cents": 0, "float_money_accept_count": 0,
        "synthetic_file_count": 128, "worksheet_count": 64, "project_count": 20000,
        "account_count": 5000, "concurrent_import_count": 128, "concurrent_report_count": 128,
        "concurrency_worker_count": 8, "data_error_count": 0, "total_elapsed_budget_ms": 30000,
        "import_p95_budget_ms": 3000, "peak_memory_budget_bytes": 268435456,
        "attack_case_count": 9, "rejected_attack_count": 9, "fault_injection_count": 1,
        "successful_recovery_count": 1, "data_pollution_count": 0,
        "governance_model_count": 24, "active_formula_count": 406, "active_parameter_count": 2640,
        "current_parameter_range": "PARAM-KMFA-3006..3025", "s23_p2_started": True,
        "s23_p3_started": False, "s23_stage_review_started": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
    }
    mismatch = [key for key, expected_value in expected.items() if manifest.get(key) != expected_value]
    if mismatch:
        raise CheckError("S23-P2 manifest mismatch: " + ", ".join(mismatch))
    state = {
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": 20 if final else 0,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 66 if final else 65,
        "overall_phase_acceptance_percent": 91.7 if final else 90.3,
        "decision": "GO_TO_S23_P3_ONLY" if final else "REMAIN_IN_S23_P2_FINAL_VALIDATION",
        "next_gate_id": "S23-P3" if final else "S23-P2-FINAL-VALIDATION",
        "s23_p2_completed": final, "s23_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s23_p3_entry_allowed": final,
    }
    mismatch = [key for key, expected_value in state.items() if manifest.get(key) != expected_value]
    if mismatch:
        raise CheckError("S23-P2 acceptance state mismatch: " + ", ".join(mismatch))
    verification = _json(builder.PUBLIC_VERIFICATION_PATH)
    precision, performance, extreme = _json(builder.PRECISION_REPORT_PATH), _json(builder.PERFORMANCE_REPORT_PATH), _json(builder.EXTREME_REPORT_PATH)
    if (verification.get("status"), verification.get("check_count"), verification.get("pass_count"), verification.get("fail_count")) != ("PASS", 49, 49, 0):
        raise CheckError("public verification failed")
    if precision.get("difference_cents") != 0 or performance.get("data_error_count") != 0 or extreme.get("data_pollution_count") != 0:
        raise CheckError("precision correctness or pollution gate failed")
    if performance.get("total_elapsed_ms", 10**9) > performance.get("total_elapsed_budget_ms", 0) or performance.get("import_p95_ms", 10**9) > performance.get("import_p95_budget_ms", 0) or performance.get("peak_memory_bytes", 10**12) > performance.get("peak_memory_budget_bytes", 0):
        raise CheckError("performance budget failed")
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
    print("PASS: S23-P2 strict checker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
