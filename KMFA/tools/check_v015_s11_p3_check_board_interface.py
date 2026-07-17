#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S11-P3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s11_p3_check_board_interface as builder
from KMFA.tools import v015_s11_p3_check_board_interface as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s11_p3_check_board_interface.py','KMFA/tools/build_v015_s11_p3_check_board_interface.py','KMFA/tools/check_v015_s11_p3_check_board_interface.py','KMFA/tools/run_v015_s11_p3_validations.py','KMFA/tools/run_v015_s11_p3_browser_tests.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s11_p3_check_board_interface"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s11_p3_check_board_interface_artifacts"),
    ("focused_browser_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s11_p3_browser_tests.py"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s11_p3_check_board_interface_governance"),
    ("s11_p2_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p3_check_board_interface.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s11_p3_check_board_interface.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p3_check_board_interface.py --pre-final --skip-validation-receipts"),
    ("legacy_board_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_source_check_board_runtime"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S11_P3_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p3_check_board_interface.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p3_check_board_interface.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s11_p3_check_board_interface.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.PHASE_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PHASE_PREFIXES = (
    "KMFA/.impeccable/",
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/DESIGN.md",
    "KMFA/HANDOFF.md",
    "KMFA/PRODUCT.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/quality/",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S11_P3_CHECK_BOARD_INTERFACE/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s11_p3_check_board_interface.py",
    "KMFA/tests/test_v015_s11_p3_check_board_interface_artifacts.py",
    "KMFA/tests/test_v015_s11_p3_check_board_interface_browser.py",
    "KMFA/tests/test_v015_s11_p3_check_board_interface_governance.py",
    "KMFA/tools/build_v015_s11_p3_check_board_interface.py",
    "KMFA/tools/check_v015_s11_p3_check_board_interface.py",
    "KMFA/tools/run_v015_s11_p3_browser_tests.py",
    "KMFA/tools/run_v015_s11_p3_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s11_p3_check_board_interface.py",
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
        raise CheckError("S11-P3 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S11-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("s11_p3_entry_allowed") is not True:
        raise CheckError("S11-P2 data-model dependency is not accepted")
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S11-P2 validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S11-P2 validation head is not reachable")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads" / "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (source.get("source_package_sha256"), source.get("stage_count"), source.get("phase_count"), source.get("task_count")) != (builder.TASKPACK_SHA256, 24, 72, 216):
        raise CheckError("tracked TaskPack source manifest drift")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S11"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P3"), None)
    if (stage or {}).get("name") != "数据质量、完整性与数据源检查板" or (phase or {}).get("name") != "检查板界面":
        raise CheckError("S11-P3 source phase drift")
    tasks = (phase or {}).get("tasks", [])
    if [row.get("id") for row in tasks] != ["T01", "T02", "T03"]:
        raise CheckError("S11-P3 source task drift")
    if [row.get("stop") for row in tasks] != ["颜色影响阅读时失败。", "没有明确下一步不得通过。", "返回丢失上下文则失败。"]:
        raise CheckError("S11-P3 source stop condition drift")


def _check_screenshot() -> None:
    data = builder.SCREENSHOT_PATH.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 10_000:
        raise CheckError("S11-P3 visual screenshot is missing or invalid")
    width, height = struct.unpack(">II", data[16:24])
    if width < 1400 or height < 900:
        raise CheckError("S11-P3 visual screenshot dimensions are too small")


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".html", ".csv"}]
    paths.extend((builder.INTERFACE_CONTRACT_PATH, builder.ACTION_CONTRACT_PATH, builder.ACCESSIBILITY_CONTRACT_PATH))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for pattern in (r"/Users/", r"/Volumes/", r"/home/", r"file://", r"KMFA_MetaData", r"private://"):
        if re.search(pattern, text, re.IGNORECASE):
            raise CheckError(f"public S11-P3 evidence contains forbidden material: {pattern}")
    for path in paths:
        if path.suffix == ".json":
            _json(path)
        elif path.suffix == ".jsonl":
            _jsonl(path)
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                list(csv.reader(handle))
    _check_screenshot()


def _check_governance_sync_in_clean_worktree() -> None:
    with tempfile.TemporaryDirectory(prefix="kmfa-s11p3-governance-") as temp_dir:
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
    interface = _json(builder.INTERFACE_CONTRACT_PATH)
    action = _json(builder.ACTION_CONTRACT_PATH)
    accessibility = _json(builder.ACCESSIBILITY_CONTRACT_PATH)
    interaction = _json(builder.INTERACTION_EVIDENCE_PATH)
    visual = _json(builder.VISUAL_EVIDENCE_PATH)
    flows = _json(builder.ACTION_FLOW_EVIDENCE_PATH)
    browser = _json(builder.BROWSER_CONTRACT_PATH)
    tasks = _json(builder.TASK_MATRIX_PATH)
    if source.get("roadmap_phase_id") != "S11-P3" or source.get("task_count") != 3:
        raise CheckError("source contract drift")
    if (interface.get("row_count"), interface.get("leaf_count"), len(interface.get("matrix_columns_zh", []))) != (34, 6, 6):
        raise CheckError("interface matrix contract drift")
    if interface.get("business_blue_primary") is not True or interface.get("large_yellow_surface_count") != 0:
        raise CheckError("visual direction contract drift")
    if interface.get("internal_field_names_visible_by_default") is not False or interface.get("frontend_status_mutation_allowed") is not False:
        raise CheckError("human-readable or status-write boundary drift")
    if {row.get("kind") for row in action.get("action_kinds", [])} != set(kernel.ACTION_KINDS):
        raise CheckError("action flow kind drift")
    if len(action.get("context_fields", [])) != 8 or action.get("frontend_status_write_count") != 0:
        raise CheckError("context preservation contract drift")
    if action.get("real_upload_or_sync_performed") is not False:
        raise CheckError("real upload or sync must remain closed")
    if accessibility.get("target") != "WCAG_2_1_AA" or accessibility.get("focus_restored_after_return") is not True:
        raise CheckError("accessibility contract drift")
    if interaction.get("accounting") != {"total": 65, "passed": 65, "failed": 0}:
        raise CheckError("public check accounting drift")
    visual_contract = visual.get("visual_contract", {})
    if visual_contract.get("contrast_all_pass") is not True or len(visual_contract.get("contrast_pairs", [])) != 7:
        raise CheckError("contrast evidence drift")
    if any(not flow.get("context_exact") or not flow.get("backend_state_unchanged") for flow in flows.get("flows", {}).values()):
        raise CheckError("action return evidence drift")
    if browser.get("network_request_count_expected") != 0 or browser.get("console_error_count_expected") != 0:
        raise CheckError("browser acceptance boundary drift")
    if tasks.get("task_count") != 3:
        raise CheckError("task matrix drift")
    _check_screenshot()


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    expected = {
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S11-P3",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": acceptance,
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "phase_task_accepted_count": 0 if pre_final else 3,
        "overall_accepted_phase_count": 30 if pre_final else 31,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 2 if pre_final else 3,
        "stage_task_accepted_count": 6 if pre_final else 9,
        "decision": "REMAIN_IN_S11_P3_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S11_STAGE_REVIEW_ONLY",
        "interface_row_count": 34,
        "interface_leaf_count": 6,
        "matrix_column_count": 6,
        "filter_control_count": 4,
        "action_kind_count": 4,
        "context_preservation_field_count": 8,
        "visual_contrast_pair_count": 7,
        "visual_contrast_all_pass": True,
        "large_yellow_surface_count": 0,
        "large_status_color_surface_count": 0,
        "public_check_accounting": {"total": 65, "passed": 65, "failed": 0},
        "frontend_status_mutation_allowed": False,
        "frontend_status_write_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "s11_p1_acceptance_status": "PASSED",
        "s11_p2_acceptance_status": "PASSED",
        "s11_p3_started": True,
        "s11_p3_acceptance_status": acceptance,
        "s11_stage_review_entry_allowed": not pre_final,
        "s11_stage_review_started": False,
        "s12_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise CheckError("S11-P3 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S11_P3_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S11_STAGE_REVIEW_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "active_formula_count: 359",
            "active_parameter_count: 1787",
            'current_parameter_range: "PARAM-KMFA-2155..2172"',
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 100",
            f'decision: "{decision}"',
            's11_p1_acceptance_status: "PASSED"',
            's11_p2_acceptance_status: "PASSED"',
            "s11_p3_started: true",
            f's11_p3_acceptance_status: "{acceptance}"',
            f"s11_stage_review_entry_allowed: {str(not pre_final).lower()}",
            "s11_stage_review_started: false",
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
        if "kmfa_v015_s11_p3_check_board_interface" not in text or "MOD-KMFA-QUALITY-GATE-001" not in text:
            raise CheckError("S11-P3 model registry entry missing")
    if "FORM-KMFA-V015-S11-P3-CHECK-BOARD-INTERFACE-001" not in formula_text:
        raise CheckError("S11-P3 formula registry entry missing")
    for number in range(2155, 2173):
        if f"PARAM-KMFA-{number}" not in parameter_text:
            raise CheckError(f"S11-P3 parameter missing: PARAM-KMFA-{number}")
    for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
        if kernel.RUN_PHASE_ID not in (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"):
            raise CheckError(f"human governance record missing: {relative}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    rows = _jsonl(builder.VALIDATION_RESULTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    if len(rows) != len(expected) or [row.get("name") for row in rows] != list(expected):
        raise CheckError("S11-P3 validation receipt count/order drift")
    runs = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    if len(runs) != 1 or None in runs or len(heads) != 1 or None in heads:
        raise CheckError("S11-P3 receipts do not share one head/run")
    for row in rows:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"S11-P3 validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"S11-P3 validation output digest invalid: {name}")
    head = next(iter(heads))
    run_id = next(iter(runs))
    if manifest.get("validation_head") != head or manifest.get("validation_run_id") != run_id or manifest.get("validation_receipt_count") != len(rows):
        raise CheckError("S11-P3 manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final S11-P3 evidence commit must be the immediate child of validation head")


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
    print("PASS: S11-P3 strict receipt-bound checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
