#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S12-P2."""

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

from KMFA.tools import build_v015_s12_p2_core_calculations as builder
from KMFA.tools import v015_s12_p2_core_calculations as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s12_p2_core_calculations.py','KMFA/tools/build_v015_s12_p2_core_calculations.py','KMFA/tools/check_v015_s12_p2_core_calculations.py','KMFA/tools/run_v015_s12_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s12_p2_core_calculations"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s12_p2_core_calculations_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s12_p2_core_calculations_governance"),
    ("legacy_margin_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_project_margin_cash_margin"),
    ("amount_precision_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s05_p1_amount_precision"),
    ("s12_p1_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s12_p1_project_cost_facts"),
    ("s12_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s12_p2_core_calculations.py --dependency-check"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s12_p2_core_calculations.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s12_p2_core_calculations.py --pre-final --skip-validation-receipts"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S12_P2_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s12_p2_core_calculations.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s12_p2_core_calculations.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s12_p2_core_calculations.py --public-boundary-check"),
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
    "KMFA/metadata/lineage/v015_s12_p2_",
    "KMFA/metadata/quality/v015_s12_p2_",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S12_P2_CORE_CALCULATIONS/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s12_p2_core_calculations.py",
    "KMFA/tests/test_v015_s12_p2_core_calculations_artifacts.py",
    "KMFA/tests/test_v015_s12_p2_core_calculations_governance.py",
    "KMFA/tools/build_v015_s12_p2_core_calculations.py",
    "KMFA/tools/check_v015_s12_p2_core_calculations.py",
    "KMFA/tools/run_v015_s12_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s12_p2_core_calculations.py",
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
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) or path.startswith(prefix) for prefix in ALLOWED_PHASE_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S12-P2 base commit is not an ancestor of HEAD")
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
        raise CheckError("unexpected S12-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("validation_receipt_count") != 21:
        raise CheckError("S12-P1 dependency is not accepted")
    if value.get("s12_p2_entry_allowed") is not True or value.get("s12_p2_started") is not False:
        raise CheckError("S12-P1 did not open exactly S12-P2")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (source.get("source_package_sha256"), source.get("stage_count"), source.get("phase_count"), source.get("task_count")) != (builder.TASKPACK_SHA256, 24, 72, 216):
        raise CheckError("tracked TaskPack source manifest drift")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S12"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P2"), None)
    if (stage or {}).get("name") != "项目成本事实层与计算引擎" or (phase or {}).get("name") != "核心计算":
        raise CheckError("S12-P2 source phase drift")
    tasks = (phase or {}).get("tasks", [])
    if [row.get("id") for row in tasks] != ["T01", "T02", "T03"]:
        raise CheckError("S12-P2 source task drift")
    if [row.get("stop") for row in tasks] != ["任一分差异失败。", "账户或主体不明则降级。", "缺数据不得生成确定性结论。"]:
        raise CheckError("S12-P2 source stop condition drift")


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
    paths.extend((builder.MARGIN_CONTRACT_PATH, builder.CASH_CONTRACT_PATH, builder.RISK_POLICY_PATH))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for pattern in (r"/Users/", r"/Volumes/", r"/home/", r"file://", r"KMFA_MetaData", r"private://"):
        if re.search(pattern, text, re.IGNORECASE):
            raise CheckError(f"public S12-P2 evidence contains forbidden material: {pattern}")
    for forbidden in ("raw_value", "original_value", "plaintext_value", "private_hash", "bank_account_number", "identity_document_number"):
        if forbidden in text:
            raise CheckError(f"public S12-P2 evidence contains forbidden field: {forbidden}")
    for path in paths:
        if path.suffix == ".json":
            _json(path)
        elif path.suffix == ".jsonl":
            _jsonl(path)
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                list(csv.reader(handle))


def _check_governance_sync_in_clean_worktree() -> None:
    with tempfile.TemporaryDirectory(prefix="kmfa-s12p2-governance-") as temp_dir:
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
    margin_contract = _json(builder.MARGIN_CONTRACT_PATH)
    cash_contract = _json(builder.CASH_CONTRACT_PATH)
    risk_policy = _json(builder.RISK_POLICY_PATH)
    verification = _json(builder.VERIFICATION_PATH)
    margin = _json(builder.MARGIN_BASELINE_PATH)
    cash = _json(builder.CASH_CHAIN_PATH)
    risk = _json(builder.RISK_RULE_PATH)
    tasks = _json(builder.TASK_MATRIX_PATH)
    if source.get("roadmap_phase_id") != "S12-P2" or source.get("task_count") != 3:
        raise CheckError("source contract drift")
    if set(margin_contract.get("views", {})) != set(kernel.MARGIN_VIEWS) or margin_contract.get("money_tolerance_cents") != 0:
        raise CheckError("margin basis contract drift")
    if margin.get("comparison") != {
        "schema_version": "kmfa.v015.s12p2.margin_golden_comparison.v1",
        "money_tolerance_cents": 0,
        "differences_cents": {"contract": 0, "management": 0, "settlement": 0},
        "zero_difference_pass": True,
    }:
        raise CheckError("margin golden comparison drift")
    if cash_contract.get("uncollected_invoice_counted_as_cash") is not False or cash_contract.get("ordinary_receivable_counted_as_cash") is not False:
        raise CheckError("cash source contract drift")
    if cash.get("confirmed_case", {}).get("uncollected_amount_counted_as_cash_cents") != 0:
        raise CheckError("uncollected amount entered cash income")
    if cash.get("unresolved_account_case", {}).get("calculation_status") != kernel.DEGRADED or cash.get("unresolved_account_case", {}).get("business_decision_allowed") is not False:
        raise CheckError("unresolved account degradation drift")
    if risk_policy.get("thresholds_external_and_adjustable") is not True or risk_policy.get("missing_data_deterministic_conclusion_allowed") is not False:
        raise CheckError("risk policy gate drift")
    if risk.get("default_policy_case", {}).get("conclusion") != kernel.DETERMINATE_ALERT:
        raise CheckError("default risk result drift")
    if risk.get("adjusted_policy_case", {}).get("conclusion") != kernel.DETERMINATE_CLEAR:
        raise CheckError("adjusted risk result drift")
    if risk.get("missing_data_case", {}).get("conclusion") != kernel.INSUFFICIENT_DATA or risk.get("missing_data_case", {}).get("deterministic_conclusion_allowed") is not False:
        raise CheckError("missing data risk gate drift")
    if verification.get("accounting") != {"total": 48, "passed": 48, "failed": 0} or verification.get("failed_checks") != []:
        raise CheckError("core calculation verification accounting drift")
    if tasks.get("task_count") != 3:
        raise CheckError("task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    expected = {
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S12-P2",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": acceptance,
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 1 if pre_final else 2,
        "stage_task_accepted_count": 3 if pre_final else 6,
        "phase_task_accepted_count": 0 if pre_final else 3,
        "overall_accepted_phase_count": 32 if pre_final else 33,
        "decision": "REMAIN_IN_S12_P2_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S12_P3_ONLY",
        "margin_view_count": 3,
        "margin_golden_difference_cents": 0,
        "margin_money_tolerance_cents": 0,
        "contract_gross_profit_cents": 30000,
        "settlement_gross_profit_cents": 20000,
        "management_gross_profit_cents": 15000,
        "cash_gross_profit_cents": 20000,
        "capital_occupied_cents": 10000,
        "uncollected_amount_counted_as_cash_cents": 0,
        "degraded_cash_case_count": 1,
        "risk_policy_threshold_count": 4,
        "default_risk_trigger_count": 4,
        "relaxed_risk_trigger_count": 0,
        "insufficient_data_case_count": 1,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "s12_p1_acceptance_status": "PASSED",
        "s12_p2_started": True,
        "s12_p2_acceptance_status": acceptance,
        "s12_p3_entry_allowed": not pre_final,
        "s12_p3_started": False,
        "s12_stage_review_entry_allowed": False,
        "core_calculation_implemented": True,
        "real_business_calculation_performed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise CheckError("S12-P2 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S12_P2_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S12_P3_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "active_formula_count: 362",
            "active_parameter_count: 1826",
            'current_parameter_range: "PARAM-KMFA-2196..2211"',
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 67",
            f'decision: "{decision}"',
            's12_p1_acceptance_status: "PASSED"',
            "s12_p2_started: true",
            f's12_p2_acceptance_status: "{acceptance}"',
            f"s12_p3_entry_allowed: {str(not pre_final).lower()}",
            "s12_p3_started: false",
            "s12_stage_review_entry_allowed: false",
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
        if "kmfa_v015_s12_p2_core_calculations" not in text or "MOD-KMFA-COST-001" not in text:
            raise CheckError("S12-P2 model registry entry missing")
    if "FORM-KMFA-V015-S12-P2-CORE-CALCULATIONS-001" not in formula_text:
        raise CheckError("S12-P2 formula registry entry missing")
    for number in range(2196, 2212):
        if f"PARAM-KMFA-{number}" not in parameter_text:
            raise CheckError(f"S12-P2 parameter missing: PARAM-KMFA-{number}")
    for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
        if kernel.RUN_PHASE_ID not in (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"):
            raise CheckError(f"human governance record missing: {relative}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    rows = _jsonl(builder.VALIDATION_RESULTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    if len(rows) != len(expected) or [row.get("name") for row in rows] != list(expected):
        raise CheckError("S12-P2 validation receipt count/order drift")
    runs = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    if len(runs) != 1 or None in runs or len(heads) != 1 or None in heads:
        raise CheckError("S12-P2 receipts do not share one head/run")
    for row in rows:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"S12-P2 validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"S12-P2 validation output digest invalid: {name}")
    head = next(iter(heads))
    run_id = next(iter(runs))
    if manifest.get("validation_head") != head or manifest.get("validation_run_id") != run_id or manifest.get("validation_receipt_count") != len(rows):
        raise CheckError("S12-P2 manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final S12-P2 evidence commit must be the immediate child of validation head")


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
    print("PASS: S12-P2 strict receipt-bound checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
