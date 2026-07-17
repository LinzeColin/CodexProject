#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S11-P2."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s11_p2_check_board_data_model as builder
from KMFA.tools import v015_s11_p2_check_board_data_model as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s11_p2_check_board_data_model.py','KMFA/tools/build_v015_s11_p2_check_board_data_model.py','KMFA/tools/check_v015_s11_p2_check_board_data_model.py','KMFA/tools/run_v015_s11_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s11_p2_check_board_data_model"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s11_p2_check_board_data_model_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s11_p2_check_board_data_model_governance"),
    ("legacy_source_check_board_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_source_check_board_runtime"),
    ("s11_p1_quality_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p2_check_board_data_model.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s11_p2_check_board_data_model.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p2_check_board_data_model.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S11_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p2_check_board_data_model.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p2_check_board_data_model.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p2_check_board_data_model.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/delivery_tasks.yaml",
    "KMFA/development_events.jsonl",
    "KMFA/events.jsonl",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/quality/",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S11_P2_CHECK_BOARD_DATA_MODEL/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s11_p2_check_board_data_model.py",
    "KMFA/tests/test_v015_s11_p2_check_board_data_model_artifacts.py",
    "KMFA/tests/test_v015_s11_p2_check_board_data_model_governance.py",
    "KMFA/tools/build_v015_s11_p2_check_board_data_model.py",
    "KMFA/tools/check_v015_s11_p2_check_board_data_model.py",
    "KMFA/tools/run_v015_s11_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s11_p2_check_board_data_model.py",
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
    pass


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise CheckError(f"JSONL object rows required: {path}")
    return rows


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S11-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S11-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("s11_p2_entry_allowed") is not True:
        raise CheckError("S11-P1 quality dependency is not accepted")
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S11-P1 validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S11-P1 validation head is not reachable")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads" / "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (source.get("source_package_sha256"), source.get("stage_count"), source.get("phase_count"), source.get("task_count")) != (builder.TASKPACK_SHA256, 24, 72, 216):
        raise CheckError("tracked TaskPack source manifest drift")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S11"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P2"), None)
    if (stage or {}).get("name") != "数据质量、完整性与数据源检查板" or (phase or {}).get("name") != "检查板数据模型":
        raise CheckError("S11-P2 source phase drift")
    tasks = (phase or {}).get("tasks", [])
    if [row.get("id") for row in tasks] != ["T01", "T02", "T03"]:
        raise CheckError("S11-P2 source task drift")
    if [row.get("stop") for row in tasks] != ["不得把所有文件堆在同一层。", "状态无解释则失败。", "前端不可直接把失败改为已就绪。"]:
        raise CheckError("S11-P2 source stop condition drift")


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
    paths.extend((builder.HIERARCHY_CONTRACT_PATH, builder.COLUMN_CONTRACT_PATH, builder.STATE_FLOW_CONTRACT_PATH))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for pattern in (r"/Users/", r"/Volumes/", r"/home/", r"file://", r"KMFA_MetaData", r"private://"):
        if re.search(pattern, text, re.IGNORECASE):
            raise CheckError(f"public S11-P2 evidence contains forbidden material: {pattern}")
    for path in paths:
        if path.suffix == ".json":
            _json(path)
        elif path.suffix == ".jsonl":
            _jsonl(path)
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                list(csv.reader(handle))


def _check_governance_sync_in_clean_worktree() -> None:
    with tempfile.TemporaryDirectory(prefix="kmfa-s11p2-governance-") as temp_dir:
        worktree = Path(temp_dir) / "repo"
        added = subprocess.run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if added.returncode:
            raise CheckError(added.stderr.strip() or "failed to create clean governance worktree")
        validation: subprocess.CompletedProcess[str] | None = None
        cleanup: subprocess.CompletedProcess[str] | None = None
        try:
            environment = dict(os.environ)
            environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
            validation = subprocess.run(
                ["python3", "-B", "scripts/validate_governance_sync.py", "--changed-only", "--base-ref", builder.PHASE_BASE_COMMIT, "--enforce-sync"],
                cwd=worktree,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            cleanup = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if cleanup.returncode:
            raise CheckError(cleanup.stderr.strip() or "failed to remove clean governance worktree")
        if validation is None or validation.returncode:
            output = "" if validation is None else validation.stdout + validation.stderr
            raise CheckError("clean governance sync failed\n" + output[-6000:])


def _check_evidence() -> None:
    source = _json(builder.SOURCE_CONTRACT_PATH)
    hierarchy = _json(builder.HIERARCHY_CONTRACT_PATH)
    columns = _json(builder.COLUMN_CONTRACT_PATH)
    state_flow = _json(builder.STATE_FLOW_CONTRACT_PATH)
    model = _json(builder.BOARD_MODEL_PATH)
    projections = _json(builder.PROJECTION_EXAMPLES_PATH)
    automatic = _json(builder.AUTOMATIC_FLOW_PATH)
    tasks = _json(builder.TASK_MATRIX_PATH)
    if source.get("roadmap_phase_id") != "S11-P2" or source.get("task_count") != 3:
        raise CheckError("source contract drift")
    hierarchy_codes = [row.get("code") for row in hierarchy.get("levels", [])]
    if hierarchy.get("level_count") != 6 or hierarchy_codes != [code for code, _ in kernel.HIERARCHY_LEVELS]:
        raise CheckError("six-level hierarchy contract drift")
    if columns.get("required_column_count") != 7 or columns.get("required_columns") != list(kernel.REQUIRED_COLUMNS):
        raise CheckError("required column contract drift")
    if state_flow.get("backend_fact_only") is not True or state_flow.get("frontend_status_mutation_allowed") is not False:
        raise CheckError("backend-only state contract drift")
    if (model.get("node_count"), model.get("leaf_count"), model.get("max_depth"), model.get("flat_leaf_at_root_count")) != (34, 6, 5, 0):
        raise CheckError("board hierarchy evidence drift")
    if projections.get("accounting") != {"total": 83, "passed": 83, "failed": 0}:
        raise CheckError("public check accounting drift")
    transition = automatic.get("transition", {})
    if transition.get("before_auto_selected") is not False or transition.get("after_auto_selected") is not True:
        raise CheckError("automatic status transition drift")
    if automatic.get("frontend_status_mutation_allowed") is not False or automatic.get("raw_source_mutation_performed") is not False:
        raise CheckError("automatic flow boundary drift")
    if tasks.get("task_count") != 3:
        raise CheckError("task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    expected = {
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S11-P2",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": acceptance,
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "phase_task_accepted_count": 0 if pre_final else 3,
        "overall_accepted_phase_count": 29 if pre_final else 30,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 1 if pre_final else 2,
        "stage_task_accepted_count": 3 if pre_final else 6,
        "decision": "REMAIN_IN_S11_P2_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S11_P3_ONLY",
        "hierarchy_level_count": 6,
        "board_node_count": 34,
        "board_leaf_count": 6,
        "board_max_depth": 5,
        "flat_leaf_at_root_count": 0,
        "required_column_count": 7,
        "view_operation_count": 4,
        "human_status_count": 4,
        "alert_type_count": 6,
        "public_check_accounting": {"total": 83, "passed": 83, "failed": 0},
        "missing_source_actionable_count": 1,
        "automatic_selected_leaf_count": 1,
        "backend_fact_only": True,
        "frontend_status_mutation_allowed": False,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "s11_p1_acceptance_status": "PASSED",
        "s11_p2_started": True,
        "s11_p2_acceptance_status": acceptance,
        "s11_p3_entry_allowed": not pre_final,
        "s11_p3_started": False,
        "s11_stage_review_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise CheckError("S11-P2 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S11_P2_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S11_P3_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "active_formula_count: 358",
            "active_parameter_count: 1769",
            'current_parameter_range: "PARAM-KMFA-2139..2154"',
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 67",
            f'decision: "{decision}"',
            's11_p1_acceptance_status: "PASSED"',
            "s11_p2_started: true",
            f's11_p2_acceptance_status: "{acceptance}"',
            f"s11_p3_entry_allowed: {str(not pre_final).lower()}",
            "s11_p3_started: false",
            "github_upload_performed: false",
            "app_reinstall_performed: false",
        ):
            if token not in text:
                raise CheckError(f"governance token missing from {relative}: {token}")
    registry_text = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    mirror_text = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
    formula_text = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    parameter_text = (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
    for text in (registry_text, mirror_text):
        if "kmfa_v015_s11_p2_check_board_data_model" not in text or "MOD-KMFA-QUALITY-GATE-001" not in text:
            raise CheckError("S11-P2 model registry entry missing")
    if "FORM-KMFA-V015-S11-P2-CHECK-BOARD-DATA-MODEL-001" not in formula_text:
        raise CheckError("S11-P2 formula registry entry missing")
    for number in range(2139, 2155):
        if f"PARAM-KMFA-{number}" not in parameter_text:
            raise CheckError(f"S11-P2 parameter missing: PARAM-KMFA-{number}")
    for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
        if kernel.RUN_PHASE_ID not in (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"):
            raise CheckError(f"human governance record missing: {relative}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    rows = _jsonl(builder.VALIDATION_RESULTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    if len(rows) != len(expected) or [row.get("name") for row in rows] != list(expected):
        raise CheckError("S11-P2 validation receipt count/order drift")
    runs = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    if len(runs) != 1 or None in runs or len(heads) != 1 or None in heads:
        raise CheckError("S11-P2 receipts do not share one head/run")
    for row in rows:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"S11-P2 validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"S11-P2 validation output digest invalid: {name}")
    head = next(iter(heads))
    run_id = next(iter(runs))
    if manifest.get("validation_head") != head or manifest.get("validation_run_id") != run_id or manifest.get("validation_receipt_count") != len(rows):
        raise CheckError("S11-P2 manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final S11-P2 evidence commit must be the immediate child of validation head")


def run(*, pre_final: bool, skip_validation_receipts: bool) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_public_boundary()
    _check_evidence()
    manifest = _check_manifest(pre_final=pre_final)
    _check_governance(pre_final=pre_final)
    builder.check_outputs()
    if not pre_final and not skip_validation_receipts:
        _check_receipts(manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        elif args.clean_governance_sync_check:
            _check_governance_sync_in_clean_worktree()
        else:
            run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S11-P2 strict receipt-bound checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
