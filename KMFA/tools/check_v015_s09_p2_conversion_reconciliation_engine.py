#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S09-P2."""

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

from KMFA.tools import build_v015_s09_p2_conversion_reconciliation_engine as builder
from KMFA.tools import v015_s09_p2_conversion_reconciliation_engine as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s09_p2_conversion_reconciliation_engine.py','KMFA/tools/build_v015_s09_p2_conversion_reconciliation_engine.py','KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py','KMFA/tools/run_v015_s09_p2_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_kernel_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p2_conversion_reconciliation_engine",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p2_conversion_reconciliation_engine_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p2_conversion_reconciliation_engine_governance",
    ),
    (
        "s09_p1_dependency_regression",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p1_scope_rule_modeling KMFA.tests.test_v015_s09_p1_scope_rule_modeling_artifacts",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s09_p2_conversion_reconciliation_engine.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py --pre-final --skip-validation-receipts",
    ),
    (
        "s09_p1_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py --dependency-check",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S09_P2_PENDING_FINAL_VALIDATION",
    ),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
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
        f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.PHASE_BASE_COMMIT} --enforce-sync",
    ),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    (
        "taskpack_source",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py --taskpack-source-check",
    ),
    (
        "structured_public_diff",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py --structured-public-diff-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py --public-boundary-check",
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
    "KMFA/metadata/protocol/v015_s09_p2_rerun_confirmation_protocol_public_safe.json",
    "KMFA/metadata/quality/v015_s09_p2_conversion_policy_public_safe.json",
    "KMFA/metadata/quality/v015_s09_p2_project_financial_reconciliation_public_safe.json",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s09_p2_conversion_reconciliation_engine.py",
    "KMFA/tests/test_v015_s09_p2_conversion_reconciliation_engine_artifacts.py",
    "KMFA/tests/test_v015_s09_p2_conversion_reconciliation_engine_governance.py",
    "KMFA/tools/build_v015_s09_p2_conversion_reconciliation_engine.py",
    "KMFA/tools/check_v015_s09_p2_conversion_reconciliation_engine.py",
    "KMFA/tools/run_v015_s09_p2_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s09_p2_conversion_reconciliation_engine.py",
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
        "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/human/implementation_report_zh.md",
        "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/s09_p2_conversion_reconciliation_manifest.json",
        "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/task_acceptance_matrix_public_safe.json",
        "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/validation_results.jsonl",
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
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False
    ).returncode:
        raise CheckError("S09-P2 base commit is not an ancestor of HEAD")
    groups = [
        _git("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        _git("-c", "core.quotepath=false", "diff", "--name-only"),
        _git("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ]
    changed = [line for group in groups for line in group.splitlines() if line]
    unexpected = sorted({path for path in changed if not _is_allowed(path)})
    if unexpected:
        raise CheckError("unexpected S09-P2 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S09-P1 validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S09-P1 validation head is not reachable")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    expected = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != expected:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (
        source.get("source_package_sha256"),
        source.get("stage_count"),
        source.get("phase_count"),
        source.get("task_count"),
    ) != (expected, 24, 72, 216):
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
    paths.extend((builder.CONVERSION_POLICY_PATH, builder.RECONCILIATION_POLICY_PATH, builder.RERUN_PROTOCOL_PATH))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for pattern in (
        r"/Users/",
        r"/Volumes/",
        r"/home/",
        r"file://",
        r"KMFA_MetaData",
        r"private://",
        r"\.(?:xlsx|xls|pdf|zip)(?:\b|\")",
    ):
        if re.search(pattern, text, re.IGNORECASE):
            raise CheckError(f"public S09-P2 evidence contains forbidden material: {pattern}")
    for path in paths:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".jsonl":
            _jsonl(path)


def _check_evidence() -> None:
    policy = _json(builder.CONVERSION_POLICY_PATH)
    reconciliation_policy = _json(builder.RECONCILIATION_POLICY_PATH)
    rerun_protocol = _json(builder.RERUN_PROTOCOL_PATH)
    conversion = _json(builder.CONVERSION_CASES_PATH)
    reconciliation = _json(builder.RECONCILIATION_CASES_PATH)
    rerun = _json(builder.RERUN_CASES_PATH)
    tasks = _json(builder.TASK_MATRIX_PATH)
    if len(policy.get("rules", [])) != 2 or policy.get("input_output_conservation_required") is not True:
        raise CheckError("conversion policy coverage drift")
    conservation = conversion.get("balanced_conversion", {}).get("conservation", {})
    if conservation.get("residual_cents") != 0 or conservation.get("conservation_passed") is not True:
        raise CheckError("conversion conservation drift")
    if conversion.get("imbalance_blocked") is not True or conversion.get("float_money_rejected") is not True:
        raise CheckError("conversion negative gates drift")
    if conversion.get("unapproved_effective_count") != 0 or conversion.get("source_snapshot_unchanged") is not True:
        raise CheckError("adjustment or source immutability drift")
    if reconciliation_policy.get("opposite_difference_netting_allowed") is not False:
        raise CheckError("reconciliation netting policy drift")
    if reconciliation.get("opposite_delta_values") != [-1000, 1000]:
        raise CheckError("opposite differences are not both retained")
    if reconciliation.get("silent_offset_count") != 0 or reconciliation.get("every_difference_has_source_and_impact") is not True:
        raise CheckError("difference source/impact or silent-offset drift")
    missing = reconciliation.get("missing_source_case", {})
    if missing.get("status") != "REQUIRES_CONFIRMATION" or missing.get("complete_chain") is not False:
        raise CheckError("missing source does not fail closed")
    if rerun_protocol.get("automatic_cross_source_winner_allowed") is not False:
        raise CheckError("cross-source automatic winner policy drift")
    if rerun.get("same_source_resolved_case", {}).get("status") != "RERUN_RESOLVED":
        raise CheckError("same-source rerun resolution drift")
    if rerun.get("same_source_persistent_case", {}).get("status") != "SYSTEM_ERROR_BLOCKED":
        raise CheckError("persistent same-source mismatch is not blocked")
    if rerun.get("cross_source_confirmation_case", {}).get("status") != "PENDING_HUMAN_CONFIRMATION":
        raise CheckError("cross-source conflict is not pending human confirmation")
    if rerun.get("cross_source_automatic_winner") is not None or rerun.get("source_snapshot_unchanged") is not True:
        raise CheckError("rerun winner or source immutability drift")
    if tasks.get("task_count") != 3:
        raise CheckError("S09-P2 task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    required = {
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "phase_task_accepted_count": 0 if pre_final else 3,
        "overall_accepted_phase_count": 23 if pre_final else 24,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "decision": "REMAIN_IN_S09_P2_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S09_P3_ONLY",
        "s09_p1_acceptance_status": "PASSED",
        "s09_p2_started": True,
        "s09_p2_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s09_p3_entry_allowed": not pre_final,
        "s09_p3_started": False,
        "s09_stage_review_entry_allowed": False,
        "conservation_residual_cents": 0,
        "conservation_passed": True,
        "imbalance_blocked": True,
        "reconciliation_required_source_count": 4,
        "reconciliation_difference_count": 2,
        "opposite_differences_retained_separately": True,
        "every_difference_has_source_and_impact": True,
        "silent_offset_count": 0,
        "same_source_rerun_resolved": True,
        "persistent_same_source_blocked": True,
        "cross_source_status": "PENDING_HUMAN_CONFIRMATION",
        "cross_source_automatic_winner": None,
        "chain_state_consistent": True,
        "source_snapshot_unchanged": True,
        "raw_source_mutation_performed": False,
        "raw_root_access_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, expected in required.items() if manifest.get(key) != expected]
    if mismatches:
        raise CheckError("S09-P2 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S09_P2_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S09_P3_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 67",
            f'decision: "{decision}"',
            "s09_p2_started: true",
            f's09_p2_acceptance_status: "{acceptance}"',
            f"s09_p3_entry_allowed: {str(not pre_final).lower()}",
            "s09_p3_started: false",
            "s09_stage_review_entry_allowed: false",
            "active_formula_count: 350",
            "active_parameter_count: 1679",
            'current_parameter_range: "PARAM-KMFA-2055..2064"',
        ):
            if token not in text:
                raise CheckError(f"governance token missing in {relative}: {token}")
    surfaces = {
        "metadata/model_registry.yaml": "kmfa_v015_s09_p2_conversion_reconciliation_engine",
        "docs/governance/model_registry.yaml": "kmfa_v015_s09_p2_conversion_reconciliation_engine",
        "docs/governance/formula_registry.yaml": "FORM-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-001",
        "docs/governance/parameter_registry.csv": "PARAM-KMFA-2064",
        "docs/governance/TRACEABILITY_MATRIX.csv": "REQ-KMFA-V015-S09-P2-CONVERSION-RECONCILIATION-ENGINE",
        "功能清单.md": "FEAT-KMFA-283",
    }
    for relative, token in surfaces.items():
        if token not in (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"):
            raise CheckError(f"registry token missing in {relative}: {token}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    rows = _jsonl(builder.VALIDATION_RESULTS_PATH)
    if len(rows) != len(EXPECTED_VALIDATIONS):
        raise CheckError("validation receipt count mismatch")
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    if len(run_ids) != 1 or len(heads) != 1:
        raise CheckError("validation receipts do not bind one run and head")
    for row, (name, command) in zip(rows, EXPECTED_VALIDATIONS):
        if (
            row.get("name") != name
            or row.get("command") != command
            or row.get("status") != "PASS"
            or row.get("exit_code") != 0
        ):
            raise CheckError(f"validation receipt mismatch: {name}")
    run_id = next(iter(run_ids))
    head = next(iter(heads))
    if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
        raise CheckError("manifest validation binding mismatch")
    if manifest.get("validation_receipt_count") != len(rows) or manifest.get("validation_pass_count") != len(rows):
        raise CheckError("manifest receipt counts mismatch")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final evidence commit must be the immediate child of the validated implementation head")
    final_changed = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{head}..HEAD").splitlines())
    unexpected = sorted(final_changed - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("final evidence commit changed immutable implementation paths: " + ", ".join(unexpected))


def run(*, pre_final: bool, skip_validation_receipts: bool) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_structured_public_diff()
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
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.structured_public_diff_check:
            _check_structured_public_diff()
        elif args.public_boundary_check:
            _check_public_boundary()
        else:
            run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S09-P2 strict checker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
