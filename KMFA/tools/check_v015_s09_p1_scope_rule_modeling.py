#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S09-P1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s09_p1_scope_rule_modeling as builder
from KMFA.tools import v015_s09_p1_scope_rule_modeling as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    ("python_compile", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s09_p1_scope_rule_modeling.py','KMFA/tools/build_v015_s09_p1_scope_rule_modeling.py','KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py','KMFA/tools/run_v015_s09_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p1_scope_rule_modeling"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p1_scope_rule_modeling_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p1_scope_rule_modeling_governance"),
    ("s08_stage_review_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_stage_review_contract KMFA.tests.test_v015_s08_stage_review"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s09_p1_scope_rule_modeling.py --check"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py --pre-final --skip-validation-receipts"),
    ("s08_stage_review_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py --dependency-check"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S09_P1_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.PHASE_BASE_COMMIT} --enforce-sync"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py --taskpack-source-check"),
    ("structured_public_diff", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py --structured-public-diff-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py --public-boundary-check"),
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
    "KMFA/metadata/protocol/v015_s09_p1_adjustment_event_protocol_public_safe.json",
    "KMFA/metadata/quality/v015_s09_p1_difference_dictionary_public_safe.json",
    "KMFA/metadata/quality/v015_s09_p1_ledger_view_policy_public_safe.json",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s09_p1_scope_rule_modeling.py",
    "KMFA/tests/test_v015_s09_p1_scope_rule_modeling_artifacts.py",
    "KMFA/tests/test_v015_s09_p1_scope_rule_modeling_governance.py",
    "KMFA/tools/build_v015_s09_p1_scope_rule_modeling.py",
    "KMFA/tools/check_v015_s09_p1_scope_rule_modeling.py",
    "KMFA/tools/run_v015_s09_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s09_p1_scope_rule_modeling.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)

FINAL_MUTABLE_PATHS = frozenset(
    {
        "KMFA/AGENTS.md",
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
        "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/human/implementation_report_zh.md",
        "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/s09_p1_scope_rule_modeling_manifest.json",
        "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/task_acceptance_matrix_public_safe.json",
        "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/validation_results.jsonl",
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


def _is_allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S09-P1 base commit is not an ancestor of HEAD")
    groups = [
        _git("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        _git("-c", "core.quotepath=false", "diff", "--name-only"),
        _git("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ]
    changed = [line for group in groups for line in group.splitlines() if line]
    unexpected = sorted({path for path in changed if not _is_allowed(path)})
    if unexpected:
        raise CheckError("unexpected S09-P1 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("s09_p1_entry_allowed") is not True:
        raise CheckError("S08 review dependency is not accepted")
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S08 review validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S08 review validation head is not reachable")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    expected = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != expected:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (source.get("source_package_sha256"), source.get("stage_count"), source.get("phase_count"), source.get("task_count")) != (expected, 24, 72, 216):
        raise CheckError("tracked TaskPack source manifest drift")


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
        if path.is_file() and path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.is_file() and path.suffix.lower() == ".jsonl":
            _jsonl(path)
        elif path.is_file() and path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                list(csv.reader(handle))


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
    paths.extend((builder.LEDGER_POLICY_PATH, builder.DIFFERENCE_DICTIONARY_PATH, builder.ADJUSTMENT_PROTOCOL_PATH))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for pattern in (r"/Users/", r"/Volumes/", r"/home/", r"file://", r"KMFA_MetaData", r"private://", r"\.(?:xlsx|xls|pdf|zip)(?:\b|\")"):
        if re.search(pattern, text, re.IGNORECASE):
            raise CheckError(f"public S09-P1 evidence contains forbidden material: {pattern}")
    for path in paths:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".jsonl":
            _jsonl(path)


def _check_evidence() -> None:
    policy = _json(builder.LEDGER_POLICY_PATH)
    dictionary = _json(builder.DIFFERENCE_DICTIONARY_PATH)
    protocol = _json(builder.ADJUSTMENT_PROTOCOL_PATH)
    boundary = _json(builder.BOUNDARY_CASES_PATH)
    differences = _json(builder.DIFFERENCE_CASES_PATH)
    adjustments = _json(builder.ADJUSTMENT_CASES_PATH)
    tasks = _json(builder.TASK_MATRIX_PATH)
    if policy.get("legal_ledger_count") != 1 or len(policy.get("views", [])) != 5:
        raise CheckError("one-ledger five-view policy drift")
    if boundary.get("positive_pass_count") != 5 or boundary.get("negative_pass_count") != 4:
        raise CheckError("view boundary cases drift")
    if len(dictionary.get("types", [])) != 8 or differences.get("registered_case_pass_count") != 8:
        raise CheckError("difference dictionary coverage drift")
    if differences.get("unknown_result", {}).get("state") != "UNKNOWN_REQUIRES_CONFIRMATION" or differences.get("incomplete_result", {}).get("state") != "EVIDENCE_INCOMPLETE_REQUIRES_CONFIRMATION":
        raise CheckError("unknown or incomplete difference does not fail closed")
    if differences.get("silent_offset_count") != 0 or differences.get("float_money_rejected") is not True:
        raise CheckError("money or silent-offset boundary drift")
    if protocol.get("append_only_required") is not True or protocol.get("direct_legal_ledger_mutation_allowed") is not False:
        raise CheckError("adjustment protocol mutability drift")
    if adjustments.get("event_count") != 5 or adjustments.get("event_roundtrip_exact") is not True:
        raise CheckError("adjustment event evidence drift")
    if adjustments.get("high_risk_unauthorized_rejected") is not True or adjustments.get("direct_ledger_mutation_rejected") is not True or adjustments.get("source_snapshot_unchanged") is not True:
        raise CheckError("high-risk approval or source immutability drift")
    if tasks.get("task_count") != 3:
        raise CheckError("S09-P1 task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    required = {
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S09-P1",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "phase_task_accepted_count": 0 if pre_final else 3,
        "overall_accepted_phase_count": 22 if pre_final else 23,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "decision": "REMAIN_IN_S09_P1_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S09_P2_ONLY",
        "s09_p1_started": True,
        "s09_p1_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s09_p2_entry_allowed": not pre_final,
        "s09_p2_started": False,
        "s09_p3_entry_allowed": False,
        "s09_stage_review_entry_allowed": False,
        "legal_ledger_count": 1,
        "derived_view_count": 5,
        "difference_type_count": 8,
        "silent_offset_count": 0,
        "unapproved_adjustment_effective_count": 0,
        "direct_ledger_mutation_rejected": True,
        "raw_root_access_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, expected in required.items() if manifest.get(key) != expected]
    if mismatches:
        raise CheckError("S09-P1 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S09_P1_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S09_P2_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "active_formula_count: 349",
            "active_parameter_count: 1669",
            'current_parameter_range: "PARAM-KMFA-2046..2054"',
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 33",
            f'decision: "{decision}"',
            "s09_p1_started: true",
            f's09_p1_acceptance_status: "{acceptance}"',
            f"s09_p2_entry_allowed: {str(not pre_final).lower()}",
            "s09_p2_started: false",
            "github_upload_performed: false",
            "app_reinstall_performed: false",
        ):
            if token not in text:
                raise CheckError(f"governance token missing from {relative}: {token}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    receipts = _jsonl(builder.VALIDATION_RESULTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    if len(receipts) != len(expected) or [row.get("name") for row in receipts] != list(expected):
        raise CheckError("S09-P1 validation receipt count/order drift")
    runs = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    if len(runs) != 1 or None in runs or len(heads) != 1 or None in heads:
        raise CheckError("S09-P1 validation receipts do not share one head/run")
    for row in receipts:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"S09-P1 validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"S09-P1 validation output digest invalid: {name}")
    head = next(iter(heads))
    run_id = next(iter(runs))
    if manifest.get("validation_head") != head or manifest.get("validation_run_id") != run_id or manifest.get("validation_receipt_count") != len(receipts):
        raise CheckError("S09-P1 manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final S09-P1 evidence commit must be the immediate child of validation head")
    mutable = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{head}..HEAD").splitlines())
    unexpected = sorted(mutable - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("post-validation mutation outside S09-P1 allowlist: " + ", ".join(unexpected))


def run(*, pre_final: bool, skip_validation_receipts: bool, skip_clean_commit: bool) -> None:
    mismatches = builder.check_outputs()
    if mismatches:
        raise CheckError("deterministic artifact drift: " + ", ".join(mismatches))
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
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
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
            print("PASS: S08 review dependency is exact and reachable")
            return 0
        if args.taskpack_source_check:
            _check_taskpack_source()
            print("PASS: v1.5 TaskPack source is exact")
            return 0
        if args.structured_public_diff_check:
            _check_structured_public_diff()
            print("PASS: S09-P1 structured public diff")
            return 0
        if args.public_boundary_check:
            _check_public_boundary()
            print("PASS: S09-P1 public boundary")
            return 0
        run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts, skip_clean_commit=args.skip_clean_commit)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: KMFA v1.5 S09-P1 Scope Rule Modeling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
