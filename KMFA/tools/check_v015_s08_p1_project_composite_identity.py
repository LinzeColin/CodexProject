#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S08-P1."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s08_p1_project_composite_identity as builder
from KMFA.tools import v015_s08_p1_project_composite_identity as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_p1_project_composite_identity"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_p1_project_composite_identity_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_p1_project_composite_identity_governance"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p1_project_composite_identity.py --pre-final --skip-validation-receipts"),
    ("s07_review_dependency_check", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p1_project_composite_identity.py --dependency-check"),
    ("legacy_project_identity_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_project_composite_key && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v014_s08_p1_project_composite_key.py"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S08_P1_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.PHASE_BASE_COMMIT} --enforce-sync"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s08_p1_project_composite_identity.py --check"),
    ("python_compile", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s08_p1_project_composite_identity.py','KMFA/tools/build_v015_s08_p1_project_composite_identity.py','KMFA/tools/check_v015_s08_p1_project_composite_identity.py','KMFA/tools/run_v015_s08_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("structured_public_diff", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p1_project_composite_identity.py --structured-public-diff-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p1_project_composite_identity.py --public-boundary-check"),
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
    "KMFA/metadata/quality/v015_s08_p1_project_composite_identity_public_safe.json",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s08_p1_project_composite_identity.py",
    "KMFA/tests/test_v015_s08_p1_project_composite_identity_artifacts.py",
    "KMFA/tests/test_v015_s08_p1_project_composite_identity_governance.py",
    "KMFA/tools/build_v015_s08_p1_project_composite_identity.py",
    "KMFA/tools/check_v015_s08_p1_project_composite_identity.py",
    "KMFA/tools/run_v015_s08_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s08_p1_project_composite_identity.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)

FINAL_MUTABLE_PATHS = frozenset(
    {
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/README.md",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/VERSION_MATRIX.yaml",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/events.jsonl",
        "KMFA/docs/governance/project.yaml",
        "KMFA/docs/governance/roadmap.yaml",
        "KMFA/metadata/project/project.yaml",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/human/implementation_report_zh.md",
        "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/s08_p1_project_composite_identity_manifest.json",
        "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/task_acceptance_matrix_public_safe.json",
        "KMFA/stage_artifacts/V015_S08_P1_PROJECT_COMPOSITE_IDENTITY/machine/validation_results.jsonl",
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


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise CheckError(f"JSONL object rows required: {path}")
    return rows


def _is_allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    ).returncode:
        raise CheckError("S08-P1 base commit is not an ancestor of HEAD")
    changed = _git(
        "-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"
    ).splitlines()
    unexpected = [path for path in changed if path and not _is_allowed(path)]
    if unexpected:
        raise CheckError("unexpected S08-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("stage_acceptance_status") != "PASSED":
        raise CheckError("S07 review dependency is not accepted")
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S07 review validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S07 review validation head is not reachable")


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
    paths.append(builder.CONTRACT_PATH)
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden_patterns = (
        r"/Users/",
        r"/Volumes/",
        r"/home/",
        r"file://",
        r"KMFA_MetaData",
        r"private://",
        r"\.(?:xlsx|xls|pdf|zip)(?:\b|\")",
    )
    for pattern in forbidden_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise CheckError(f"public S08-P1 evidence contains forbidden material: {pattern}")
    for path in paths:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".jsonl":
            _read_jsonl(path)
    contract = _read_json(builder.CONTRACT_PATH)
    if contract.get("raw_root_access_count") != 0 or contract.get("private_business_values_published") is not False:
        raise CheckError("S08-P1 public contract crosses the raw/private boundary")


def _check_structured_public_diff() -> None:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "diff", "--name-only", builder.PHASE_BASE_COMMIT, "--", "KMFA"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise CheckError("structured diff path scan failed")
    for relative in (line.strip() for line in result.stdout.splitlines() if line.strip()):
        path = REPO_ROOT / relative
        if not path.is_file():
            continue
        if path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".jsonl":
            _read_jsonl(path)


def _check_evidence() -> None:
    model = _read_json(builder.MATCHING_MODEL_PATH)
    names = _read_json(builder.NAME_FIXTURES_PATH)
    auxiliary = _read_json(builder.AUXILIARY_CASES_PATH)
    tasks = _read_json(builder.TASK_MATRIX_PATH)
    if model.get("component_weights_bps") != kernel.COMPONENT_WEIGHTS_BPS:
        raise CheckError("S08-P1 component weights drift")
    if model.get("configured_weight_total_bps") != 10000:
        raise CheckError("S08-P1 component weight total drift")
    missing = model.get("missing_contract_case", {})
    if (
        missing.get("available_weight_bps") != 8000
        or missing.get("renormalized_similarity_bps") != 10000
        or missing.get("auto_merge_allowed") is not True
    ):
        raise CheckError("missing-contract renormalization acceptance drift")
    low = model.get("low_coverage_case", {})
    if low.get("renormalized_similarity_bps") != 10000 or low.get("auto_merge_allowed") is not False:
        raise CheckError("low-coverage fail-closed acceptance drift")
    if (
        names.get("fixture_count") != 6
        or names.get("raw_name_preserved_count") != 6
        or names.get("irreversible_overwrite_count") != 0
    ):
        raise CheckError("name normalization evidence drift")
    if any(
        row.get("raw_name_preserved") is not True
        or row.get("irreversible_overwrite_performed") is not False
        or row.get("transformation_count") != len(row.get("transformations", []))
        for row in names.get("fixtures", [])
    ):
        raise CheckError("name normalization explanation/preservation drift")
    if (
        auxiliary.get("amount_evidence_auxiliary_only") is not True
        or auxiliary.get("amount_alone_decided_match") is not False
        or auxiliary.get("manual_confirmation_count") != 3
        or any(row.get("auto_merge_allowed") is not False for row in auxiliary.get("cases", {}).values())
    ):
        raise CheckError("time/amount auxiliary boundary drift")
    if tasks.get("task_execution_complete_count") != 3 or len(tasks.get("tasks", [])) != 3:
        raise CheckError("S08-P1 task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _read_json(builder.MANIFEST_PATH)
    required = {
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "counted_as_taskpack_phase": True,
        "counted_as_taskpack_task_count": 3,
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "task_accepted_count": 0 if pre_final else 3,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "REMAIN_IN_S08_P1_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S08_P2_ONLY",
        "s08_p1_started": True,
        "s08_p1_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s08_p2_entry_allowed": not pre_final,
        "s08_p2_started": False,
        "s08_p3_entry_allowed": False,
        "s08_stage_review_entry_allowed": False,
        "overall_accepted_phase_count": 19 if pre_final else 20,
        "overall_taskpack_phase_count": 72,
        "component_count": 8,
        "configured_weight_total_bps": 10000,
        "missing_contract_renormalized_similarity_bps": 10000,
        "missing_contract_auto_merge_allowed": True,
        "low_coverage_auto_merge_allowed": False,
        "amount_evidence_auxiliary_only": True,
        "amount_alone_decided_match": False,
        "hard_conflict_auto_merge_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches:
        raise CheckError("S08-P1 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    status = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S08_P1_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S08_P2_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        required = (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "active_formula_count: 345",
            "active_parameter_count: 1636",
            'current_parameter_range: "PARAM-KMFA-2014..2021"',
            f'phase_acceptance_status: "{status}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 33",
            f'decision: "{decision}"',
            "s08_p1_started: true",
            f's08_p1_acceptance_status: "{status}"',
            f"s08_p2_entry_allowed: {str(not pre_final).lower()}",
            "s08_p2_started: false",
            f"product_implementation_allowed: {str(not pre_final).lower()}",
            "github_upload_performed: false",
            "app_reinstall_performed: false",
        )
        for token in required:
            if token not in text:
                raise CheckError(f"governance token missing from {relative}: {token}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    receipts = _read_jsonl(builder.VALIDATION_RESULTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    if len(receipts) != len(expected) or [row.get("name") for row in receipts] != list(expected):
        raise CheckError("S08-P1 validation receipt count/order drift")
    run_ids = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    if len(run_ids) != 1 or None in run_ids or len(heads) != 1 or None in heads:
        raise CheckError("S08-P1 validation receipts do not share one head/run")
    for row in receipts:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"S08-P1 validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"S08-P1 validation output digest invalid: {name}")
    head = next(iter(heads))
    run_id = next(iter(run_ids))
    if (
        manifest.get("validation_head") != head
        or manifest.get("validation_run_id") != run_id
        or manifest.get("validation_receipt_count") != len(receipts)
    ):
        raise CheckError("S08-P1 manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final S08-P1 evidence commit must be the immediate child of validation head")
    mutable = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{head}..HEAD").splitlines())
    unexpected = sorted(mutable - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("post-validation mutation outside S08-P1 allowlist: " + ", ".join(unexpected))


def run(*, pre_final: bool, skip_validation_receipts: bool, skip_clean_commit: bool) -> None:
    mismatches = builder.check_outputs()
    if mismatches:
        raise CheckError("deterministic artifact drift: " + ", ".join(mismatches))
    _check_scope()
    _check_dependency()
    _check_public_boundary()
    _check_structured_public_diff()
    _check_evidence()
    manifest = _check_manifest(pre_final=pre_final)
    _check_governance(pre_final=pre_final)
    if not skip_validation_receipts:
        if pre_final:
            raise CheckError("pre-final mode cannot require final receipts")
        _check_receipts(manifest)
    if not skip_clean_commit and _git("status", "--porcelain"):
        raise CheckError("worktree must be clean")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
            print("PASS: S07 review dependency is exact and reachable")
            return 0
        if args.structured_public_diff_check:
            _check_structured_public_diff()
            print("PASS: S08-P1 structured public diff")
            return 0
        if args.public_boundary_check:
            _check_public_boundary()
            print("PASS: S08-P1 public boundary")
            return 0
        run(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: KMFA v1.5 S08-P1 Project Composite Identity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
