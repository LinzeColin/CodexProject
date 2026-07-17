#!/usr/bin/env python3
"""Strict acceptance checker for KMFA v1.5 S22-P3 operations governance."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s22_p3_operations_governance as builder


REPO_ROOT = builder.REPO_ROOT
EXPECTED_VALIDATIONS = (
    (
        "phase_contract",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s22_p3_operations_governance.py','KMFA/tools/run_v015_s22_p3_operations_governance.py','KMFA/tools/build_v015_s22_p3_operations_governance.py','KMFA/tools/check_v015_s22_p3_operations_governance.py','KMFA/tools/run_v015_s22_p3_browser_tests.py','KMFA/tools/run_v015_s22_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_core_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p3_operations_governance",
    ),
    (
        "focused_runtime_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p3_operations_governance_runtime",
    ),
    (
        "focused_browser_tests",
        "KMFA_PRESERVE_TRACKED_SCREENSHOTS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_p3_browser_tests.py",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p3_operations_governance_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p3_operations_governance_governance",
    ),
    (
        "s22_p2_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p3_operations_governance.py --dependency-check",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s22_p3_operations_governance.py",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p3_operations_governance.py --pre-final --skip-validation-receipts",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S22_P3_PENDING_FINAL_VALIDATION",
    ),
    (
        "metadata_protocol",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py",
    ),
    (
        "project_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required",
    ),
    (
        "lean_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required",
    ),
    (
        "governance_sync",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p3_operations_governance.py --clean-governance-sync-check",
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
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p3_operations_governance.py --taskpack-source-check",
    ),
    (
        "operations_public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_p3_operations_governance.py --operations-public-boundary-check",
    ),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S22_P3_OPERATIONS_GOVERNANCE/",
    "KMFA/taskpack/v1_5/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s22_p3_operations_governance.py",
    "KMFA/tests/test_v015_s22_p3_operations_governance_runtime.py",
    "KMFA/tests/test_v015_s22_p3_operations_governance_browser.py",
    "KMFA/tests/test_v015_s22_p3_operations_governance_artifacts.py",
    "KMFA/tests/test_v015_s22_p3_operations_governance_governance.py",
    "KMFA/tools/build_v015_s22_p3_operations_governance.py",
    "KMFA/tools/check_v015_s22_p3_operations_governance.py",
    "KMFA/tools/run_v015_s22_p3_browser_tests.py",
    "KMFA/tools/run_v015_s22_p3_operations_governance.py",
    "KMFA/tools/run_v015_s22_p3_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s22_p3_operations_governance.py",
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
    """S22-P3 validation failed."""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _allowed(path: str) -> bool:
    return any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in ALLOWED_PHASE_PREFIXES
    )


def _preserved(path: str) -> bool:
    return any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in PRESERVED_UNTRACKED_PREFIXES
    )


def _check_scope() -> None:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    ).returncode:
        raise CheckError("S22-P3 base commit is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(
            line for line in _git(*args).splitlines() if line and not _preserved(line)
        )
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("unexpected S22-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if (
        value["acceptance_status"] != "PASSED"
        or value["overall_accepted_phase_count"] != 63
        or value["s22_p3_entry_allowed"] is not True
    ):
        raise CheckError("S22-P2 dependency is not the accepted 63/72 handoff")


def _check_taskpack_source() -> None:
    path = builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
    stages = _json(path).get("stages", []) if path.is_file() else []
    stage = next((row for row in stages if row.get("id") == "S22"), None)
    phase = next(
        (row for row in (stage or {}).get("phases", []) if row.get("id") == "P3"),
        None,
    )
    expected = [
        ("T01", "实现健康检查和可观测性", "关键服务无监控不得运行。"),
        ("T02", "实现备份恢复和灾难演练", "备份未验证不算可用。"),
        ("T03", "实现版本升级和迁移", "不可逆迁移需明确批准。"),
    ]
    actual = [
        (row.get("id"), row.get("name"), row.get("stop"))
        for row in (phase or {}).get("tasks", [])
    ]
    if actual != expected:
        raise CheckError("S22-P3 TaskPack source drift")


def _check_artifacts(*, require_final: bool | None, skip_receipts: bool) -> None:
    required = (
        builder.MANIFEST_PATH,
        builder.SOURCE_CONTRACT_PATH,
        builder.HEALTH_CONTRACT_PATH,
        builder.BACKUP_CONTRACT_PATH,
        builder.MIGRATION_CONTRACT_PATH,
        builder.BROWSER_PATH,
        builder.PUBLIC_CHECKS_PATH,
        builder.TASK_MATRIX_PATH,
        builder.IMPLEMENTATION_REPORT_PATH,
        builder.USER_GUIDE_PATH,
        builder.TEST_RESULTS_PATH,
        builder.RISKS_ROLLBACK_PATH,
    )
    missing = [
        str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()
    ]
    if missing:
        raise CheckError("missing S22-P3 evidence: " + ", ".join(missing))
    manifest = _json(builder.MANIFEST_PATH)
    final = manifest.get("phase_acceptance_status") == "PASSED"
    if require_final is True and not final:
        raise CheckError("S22-P3 final acceptance is required")
    if require_final is False and final:
        raise CheckError("pre-final checker requires pending S22-P3 evidence")
    expected_manifest = {
        "run_phase_id": "V015_S22_P3_OPERATIONS_GOVERNANCE",
        "roadmap_phase_id": "S22-P3",
        "phase_task_count": 3,
        "overall_total_phase_count": 72,
        "stage_execution_percentage": 100,
        "stage_acceptance_status": "PENDING",
        "public_check_count": 62,
        "public_check_pass_count": 62,
        "public_check_failed_count": 0,
        "core_test_count": 15,
        "runtime_test_count": 9,
        "browser_flow_count": 9,
        "visual_evidence_count": 7,
        "service_count": 6,
        "monitored_service_count": 6,
        "unmonitored_service_count": 0,
        "health_failure_detected_count": 1,
        "health_recovery_count": 1,
        "backup_dataset_type_count": 3,
        "verified_backup_count": 1,
        "restore_drill_count": 1,
        "restore_difference_count": 0,
        "restore_permission_difference_count": 0,
        "backup_tamper_accept_count": 0,
        "migration_surface_count": 4,
        "migration_change_count": 4,
        "migration_idempotent_noop_count": 1,
        "migration_failure_rollback_count": 1,
        "migration_rollback_difference_count": 0,
        "migration_permission_difference_count": 0,
        "irreversible_without_approval_accept_count": 0,
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "s22_p3_started": True,
        "s22_stage_review_started": False,
        "s22_stage_review_performed": False,
        "s23_entry_allowed": False,
        "s23_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    mismatch = [
        key for key, value in expected_manifest.items() if manifest.get(key) != value
    ]
    if mismatch:
        raise CheckError("S22-P3 manifest mismatch: " + ", ".join(mismatch))
    health = _json(builder.HEALTH_CONTRACT_PATH)
    backup = _json(builder.BACKUP_CONTRACT_PATH)
    migration = _json(builder.MIGRATION_CONTRACT_PATH)
    browser = _json(builder.BROWSER_PATH)
    checks = _json(builder.PUBLIC_CHECKS_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    if (
        health.get("service_count"),
        health.get("monitored_service_count"),
        health.get("unmonitored_service_count"),
        health.get("critical_unmonitored_production_accept_count"),
    ) != (6, 6, 0, 0):
        raise CheckError("health monitoring contract failed")
    if (
        backup.get("dataset_type_count"),
        backup.get("restore_difference_count"),
        backup.get("restore_permission_difference_count"),
        backup.get("backup_tamper_accept_count"),
        backup.get("unverified_restore_accept_count"),
    ) != (3, 0, 0, 0, 0):
        raise CheckError("backup recovery contract failed")
    if (
        migration.get("surface_count"),
        migration.get("idempotent_noop_count"),
        migration.get("rollback_difference_count"),
        migration.get("permission_difference_count"),
        migration.get("irreversible_without_approval_accept_count"),
    ) != (4, 1, 0, 0, 0):
        raise CheckError("migration contract failed")
    if (
        browser.get("browser_flow_count"),
        browser.get("visual_evidence_count"),
        browser.get("external_network_request_count"),
    ) != (9, 7, 0):
        raise CheckError("browser contract failed")
    if (
        checks.get("status"),
        checks.get("public_check_count"),
        checks.get("public_check_pass_count"),
        checks.get("public_check_failed_count"),
    ) != ("PASS", 62, 62, 0):
        raise CheckError("public checks failed")
    if (
        matrix.get("phase_task_count") != 3
        or len(matrix.get("tasks", [])) != 3
        or any(row.get("status") != "PASS" for row in matrix["tasks"])
    ):
        raise CheckError("task acceptance matrix failed")
    for path in builder.SCREENSHOT_PATHS:
        if not path.is_file() or path.stat().st_size < 10_000:
            raise CheckError(f"missing browser visual: {path.relative_to(REPO_ROOT)}")
    expected_state = {
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": 20 if final else 0,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 64 if final else 63,
        "overall_phase_acceptance_percent": 88.9 if final else 87.5,
        "decision": (
            "GO_TO_S22_STAGE_REVIEW_ONLY"
            if final
            else "REMAIN_IN_S22_P3_FINAL_VALIDATION"
        ),
        "next_gate_id": (
            "S22-STAGE-REVIEW" if final else "S22-P3-FINAL-VALIDATION"
        ),
        "s22_p3_completed": final,
        "s22_p3_acceptance_status": (
            "PASSED" if final else "PENDING_FINAL_VALIDATION"
        ),
        "s22_stage_review_entry_allowed": final,
    }
    mismatch = [
        key for key, value in expected_state.items() if manifest.get(key) != value
    ]
    if mismatch:
        raise CheckError("S22-P3 acceptance-state mismatch: " + ", ".join(mismatch))
    if not skip_receipts:
        rows = builder.receipts()
        if final:
            if len(rows) != 20 or [row.get("name") for row in rows] != list(
                builder.EXPECTED_VALIDATION_NAMES
            ):
                raise CheckError("formal validation receipts are incomplete")
            if any(
                row.get("status") != "PASS" or row.get("exit_code") != 0
                for row in rows
            ):
                raise CheckError("formal validation receipt failed")
            if (
                {row.get("validation_run_id") for row in rows}
                != {manifest.get("validation_run_id")}
                or {row.get("validation_head") for row in rows}
                != {manifest.get("validation_head")}
            ):
                raise CheckError("formal validation receipt binding mismatch")
        elif rows:
            raise CheckError("pending evidence must not contain formal receipts")


def _check_operations_public_boundary() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    for key in (
        "raw_root_access_count",
        "raw_write_count",
        "external_network_request_count",
        "restore_difference_count",
        "restore_permission_difference_count",
        "backup_tamper_accept_count",
        "migration_rollback_difference_count",
        "migration_permission_difference_count",
        "irreversible_without_approval_accept_count",
    ):
        if manifest.get(key) != 0:
            raise CheckError(f"operations boundary counter is nonzero: {key}")
    if (
        manifest.get("github_upload_performed") is not False
        or manifest.get("app_reinstall_performed") is not False
        or manifest.get("s22_stage_review_started") is not False
        or manifest.get("s23_started") is not False
    ):
        raise CheckError("later-phase or release boundary was crossed")
    source = _json(builder.SOURCE_CONTRACT_PATH)
    if (
        source.get("data_classification") != "PUBLIC_SYNTHETIC_ONLY"
        or "raw" not in source.get("excluded", [])
    ):
        raise CheckError("source boundary is not public-synthetic-only")
    paths = (
        builder.PROJECT_ROOT / "tools/v015_s22_p3_operations_governance.py",
        builder.PROJECT_ROOT / "tools/run_v015_s22_p3_operations_governance.py",
        builder.PROJECT_ROOT / "tools/build_v015_s22_p3_operations_governance.py",
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    urls = re.findall(r"https?://[^\s\"']+", text)
    if (
        "/Users/" in text
        or "KMFA_MetaData" in text
        or any(
            not url.startswith(
                ("http://{address}", "http://127.0.0.1", "http://localhost")
            )
            for url in urls
        )
    ):
        raise CheckError("S22-P3 phase contains a private path or external URL")


def _check_clean_governance_sync() -> None:
    manifest = _json(builder.MANIFEST_PATH)
    state = (
        "S22_P3_PASSED"
        if manifest.get("phase_acceptance_status") == "PASSED"
        else "S22_P3_PENDING_FINAL_VALIDATION"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "KMFA/tools/v015_roadmap_governance_sync.py",
            "--check",
            "--validation-state",
            state,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError(
            "governance sync mismatch\n" + (result.stdout + result.stderr)[-4000:]
        )


def run(
    *,
    require_final: bool | None = None,
    skip_validation_receipts: bool = False,
) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_artifacts(
        require_final=require_final,
        skip_receipts=skip_validation_receipts,
    )
    _check_operations_public_boundary()
    _check_clean_governance_sync()


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S22-P3 运维与治理")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--operations-public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--require-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.operations_public_boundary_check:
            _check_operations_public_boundary()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        else:
            required = (
                True
                if args.require_final
                else (False if args.pre_final else None)
            )
            run(
                require_final=required,
                skip_validation_receipts=args.skip_validation_receipts,
            )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        builder.BuildError,
        CheckError,
    ) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S22-P3 operations governance is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
