#!/usr/bin/env python3
"""KMFA v1.5 S13 整体复审的严格回执绑定检查器。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s13_stage_review as builder
from KMFA.tools import v015_s13_stage_review_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s13_stage_review_contract.py','KMFA/tools/build_v015_s13_stage_review.py','KMFA/tools/check_v015_s13_stage_review.py','KMFA/tools/run_v015_s13_stage_review_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    ("focused_contract_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s13_stage_review_contract"),
    ("focused_review_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s13_stage_review"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s13_stage_review_governance"),
    ("s13_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s13_p1_indicator_registry.py --check"),
    ("s13_p2_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s13_p2_business_health_model.py --check"),
    ("s13_p3_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s13_p3_action_priority.py --check"),
    ("s13_p1_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s13_p1_indicator_registry"),
    ("s13_p2_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s13_p2_business_health_model"),
    ("s13_p3_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s13_p3_action_priority"),
    ("integrated_review_consistency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s13_stage_review.py --integrated-review-check"),
    ("builder_exact_rebuild", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s13_stage_review.py --check"),
    ("stage_checker_pre_final", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s13_stage_review.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S13_STAGE_REVIEW_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s13_stage_review.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"from KMFA.tools.build_v015_s13_stage_review import source_contract; assert source_contract()['source_integrity_status'] == 'PASS'\""),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s13_stage_review.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.REVIEW_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S13_STAGE_REVIEW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s13_stage_review.py",
    "KMFA/tests/test_v015_s13_stage_review_contract.py",
    "KMFA/tests/test_v015_s13_stage_review_governance.py",
    "KMFA/tools/build_v015_s13_stage_review.py",
    "KMFA/tools/check_v015_s13_stage_review.py",
    "KMFA/tools/run_v015_s13_stage_review_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s13_stage_review_contract.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")
FINAL_MUTABLE_PATHS = frozenset(
    {
        "KMFA/AGENTS.md",
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/README.md",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/events.jsonl",
        "KMFA/docs/governance/project.yaml",
        "KMFA/docs/governance/roadmap.yaml",
        "KMFA/metadata/project/project.yaml",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/stage_artifacts/V015_S13_STAGE_REVIEW/human/stage13_review_report_zh.md",
        "KMFA/stage_artifacts/V015_S13_STAGE_REVIEW/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S13_STAGE_REVIEW/machine/s13_stage_review_manifest.json",
        "KMFA/stage_artifacts/V015_S13_STAGE_REVIEW/machine/validation_results.jsonl",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    }
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


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PREFIXES)


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.REVIEW_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S13 review base is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.REVIEW_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(row for row in _git(*args).splitlines() if row and not _preserved(row))
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("out-of-scope path: " + ", ".join(unexpected))


def _check_public_boundary() -> None:
    forbidden = (
        "/Users/linzezhang/Downloads/KMFA_MetaData",
        "private_raw_source_index",
        "应收账龄表2025_private_copy",
        "生产项目状态表_private_copy",
    )
    roots = [builder.OUTPUT_ROOT, builder.PROJECT_ROOT / "tools/v015_s13_stage_review_contract.py"]
    for root in roots:
        paths = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="ignore")
            matches = [token for token in forbidden if token in text]
            if matches:
                raise CheckError(f"private/raw token in public review output: {path}: {matches}")


def _check_clean_governance_sync() -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(".github/workflows/kmfa-dual-plane.yml\nKMFA/machine/\nKMFA/文档/\n")
        exclude_path = handle.name
    try:
        env = dict(os.environ)
        env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.excludesFile", "GIT_CONFIG_VALUE_0": exclude_path, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."})
        result = subprocess.run(
            ["python3", "-B", "scripts/validate_governance_sync.py", "--changed-only", "--base-ref", builder.REVIEW_BASE_COMMIT, "--enforce-sync"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise CheckError((result.stdout + result.stderr).strip())
    finally:
        Path(exclude_path).unlink(missing_ok=True)


def _check_predecessors() -> None:
    evidence = _json(builder.MACHINE_ROOT / "phase_evidence_public_safe.json")
    expected = {
        "phase_count": 3,
        "phase_passed_count": 3,
        "task_count": 9,
        "task_accepted_count": 9,
        "predecessor_public_check_count": 254,
        "predecessor_receipt_count": 60,
    }
    if evidence.get("accounting") != expected:
        raise CheckError("predecessor accounting drift")
    if any(
        row.get("acceptance_status") != "PASSED"
        or row.get("validation_receipt_count") != 20
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("manifest_sha256") or ""))
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("receipts_sha256") or ""))
        for row in evidence["phases"]
    ):
        raise CheckError("predecessor acceptance binding drift")


def _check_review_evidence() -> None:
    contracts = _json(builder.MACHINE_ROOT / "cross_phase_contracts_public_safe.json")
    if contracts.get("accounting") != {"total": 36, "passed": 36, "failed": 0, "blocking_failed": 0}:
        raise CheckError("cross-phase contract accounting drift")
    verification = _json(builder.MACHINE_ROOT / "cross_phase_verification_public_safe.json")
    if verification.get("accounting") != {"total": 72, "passed": 72, "failed": 0}:
        raise CheckError("live review verification drift")
    integrated = _json(builder.MACHINE_ROOT / "integrated_review_public_safe.json")
    summary = contract.validate_integrated_review(integrated)
    if summary != {"dimension_count": 6, "candidate_count": 6, "focus_item_count": 5, "source_binding_count": 7, "explanation_count": 6, "explanation_mismatch_count": 0}:
        raise CheckError("integrated review invariant drift")
    findings = _csv(builder.MACHINE_ROOT / "stage13_review_findings_public_safe.csv")
    if [row.get("finding_id") for row in findings] != ["S13REV-F001", "S13REV-F002", "S13REV-F003", "S13REV-F004"]:
        raise CheckError("review finding identity drift")
    if any(row.get("status") != "FIXED_VALIDATED" or row.get("blocks_stage_acceptance") != "false" for row in findings):
        raise CheckError("review finding closure drift")
    risks = _csv(builder.MACHINE_ROOT / "open_risk_register_public_safe.csv")
    if len(risks) != 6 or any(row.get("status") != "ROUTED_RESIDUAL" or row.get("plan_complete") != "true" or row.get("blocks_s13_stage_acceptance") != "false" for row in risks):
        raise CheckError("risk route drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    required = {
        "run_phase_id": builder.RUN_PHASE_ID,
        "task_id": builder.TASK_ID,
        "acceptance_id": builder.ACCEPTANCE_ID,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "review_execution_status": "EXECUTION_COMPLETE" if pre_final else "COMPLETED",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "stage_lifecycle_status": "IN_PROGRESS" if pre_final else "COMPLETED",
        "stage_acceptance_status": "PENDING" if pre_final else "PASSED",
        "decision": "REMAIN_IN_S13_STAGE_REVIEW" if pre_final else "GO_TO_S14_P1_ONLY",
        "s13_stage_review_started": True,
        "s13_stage_review_performed": not pre_final,
        "s13_stage_review_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s14_entry_allowed": not pre_final,
        "s14_p1_entry_allowed": not pre_final,
        "s14_p1_started": False,
        "overall_accepted_phase_count": 37,
        "overall_taskpack_phase_count": 72,
        "source_binding_count": 7,
        "generated_action_candidate_count": 6,
        "focus_item_count": 5,
        "automatic_execution_count": 0,
        "recommendation_fact_write_count": 0,
        "automatic_parameter_change_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, expected in required.items() if manifest.get(key) != expected]
    if mismatches:
        raise CheckError("manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    status = "PENDING" if pre_final else "PASSED"
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    lifecycle = "IN_PROGRESS" if pre_final else "COMPLETED"
    decision = "REMAIN_IN_S13_STAGE_REVIEW" if pre_final else "GO_TO_S14_P1_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        tokens = (
            builder.RUN_PHASE_ID,
            builder.TASK_ID,
            builder.ACCEPTANCE_ID,
            "active_formula_count: 368",
            "active_parameter_count: 1916",
            'current_parameter_range: "PARAM-KMFA-2290..2301"',
            f'stage_lifecycle_status: "{lifecycle}"',
            f'stage_acceptance_status: "{status}"',
            f'decision: "{decision}"',
            "s13_stage_review_started: true",
            f"s13_stage_review_performed: {str(not pre_final).lower()}",
            f's13_stage_review_acceptance_status: "{acceptance}"',
            f"s14_p1_entry_allowed: {str(not pre_final).lower()}",
            "s14_p1_started: false",
            "github_upload_performed: false",
            "app_reinstall_performed: false",
        )
        for token in tokens:
            if token not in text:
                raise CheckError(f"governance token missing from {relative}: {token}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    receipts = _jsonl(builder.VALIDATION_RESULTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    if len(receipts) != len(expected) or [row.get("name") for row in receipts] != list(expected):
        raise CheckError("validation receipt count/order drift")
    run_ids = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    if len(run_ids) != 1 or None in run_ids or len(heads) != 1 or None in heads:
        raise CheckError("validation receipts do not share one head/run")
    for row in receipts:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"validation output digest invalid: {name}")
    head, run_id = next(iter(heads)), next(iter(run_ids))
    if manifest.get("validation_head") != head or manifest.get("validation_run_id") != run_id or manifest.get("validation_receipt_count") != len(receipts):
        raise CheckError("manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final evidence commit must directly follow validation_head")
    mutable = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{head}..HEAD").splitlines())
    unexpected = sorted(mutable - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("post-validation mutation outside allowlist: " + ", ".join(unexpected))


def run(*, pre_final: bool, skip_validation_receipts: bool, skip_clean_commit: bool) -> None:
    mismatches = builder.check_outputs()
    if mismatches:
        raise CheckError("deterministic artifact drift: " + ", ".join(mismatches))
    _check_scope()
    _check_public_boundary()
    _check_predecessors()
    _check_review_evidence()
    manifest = _check_manifest(pre_final=pre_final)
    _check_governance(pre_final=pre_final)
    if not skip_validation_receipts:
        if pre_final:
            raise CheckError("pre-final mode cannot require final receipts")
        _check_receipts(manifest)
    if not skip_clean_commit and _git("status", "--porcelain", "--untracked-files=no"):
        raise CheckError("tracked worktree must be clean")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--integrated-review-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.public_boundary_check:
            _check_public_boundary()
        elif args.integrated_review_check:
            _check_review_evidence()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        else:
            run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts, skip_clean_commit=args.skip_clean_commit)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S13 整体复审严格检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
