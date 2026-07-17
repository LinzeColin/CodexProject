#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S10 整体复审及其回执绑定。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s10_stage_review as builder


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VALIDATIONS = (
    ("python_compile", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s10_stage_review_contract.py','KMFA/tools/build_v015_s10_stage_review.py','KMFA/tools/check_v015_s10_stage_review.py','KMFA/tools/run_v015_s10_stage_review_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("stage_contract_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s10_stage_review_contract"),
    ("stage_review_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s10_stage_review"),
    ("stage_review_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s10_stage_review_governance"),
    ("s10_predecessor_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s10_p1_general_import KMFA.tests.test_v015_s10_p1_general_import_artifacts KMFA.tests.test_v015_s10_p2_source_adapters KMFA.tests.test_v015_s10_p2_source_adapters_artifacts KMFA.tests.test_v015_s10_p3_automatic_ingestion_reserve KMFA.tests.test_v015_s10_p3_automatic_ingestion_reserve_artifacts"),
    ("s10_p1_builder", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s10_p1_general_import.py --check"),
    ("s10_p2_builder", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s10_p2_source_adapters.py --check"),
    ("s10_p3_builder", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s10_p3_automatic_ingestion_reserve.py --check"),
    ("s09_stage_review_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s09_stage_review.py --check"),
    ("builder_exact_rebuild", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s10_stage_review.py --check"),
    ("stage_checker_pre_final", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s10_stage_review.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S10_STAGE_REVIEW_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", f"GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.excludesFile GIT_CONFIG_VALUE_0=/tmp/kmfa_s10review_unrelated.exclude PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.REVIEW_BASE_COMMIT} --enforce-sync"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"from KMFA.tools.build_v015_s10_stage_review import source_contract; assert source_contract()['source_integrity_status'] == 'PASS'\""),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s10_stage_review.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.REVIEW_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md", "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/", "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s10_stage_review.py", "KMFA/tests/test_v015_s10_stage_review_contract.py",
    "KMFA/tests/test_v015_s10_stage_review_governance.py", "KMFA/tools/build_v015_s10_stage_review.py",
    "KMFA/tools/check_v015_s10_stage_review.py", "KMFA/tools/run_v015_s10_stage_review_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py", "KMFA/tools/v015_s10_stage_review_contract.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)

FINAL_MUTABLE_PATHS = frozenset(
    {
        "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml", "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/OWNER_STATUS.md", "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/delivery_tasks.yaml", "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/events.jsonl", "KMFA/docs/governance/project.yaml", "KMFA/docs/governance/roadmap.yaml",
        "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
        "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/s10_stage_review_manifest.json",
        "KMFA/stage_artifacts/V015_S10_STAGE_REVIEW/machine/validation_results.jsonl",
        "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
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
        raise CheckError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise CheckError(f"expected JSON object rows: {path}")
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _check_scope() -> None:
    changed = _git("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.REVIEW_BASE_COMMIT}..HEAD").splitlines()
    unexpected = [path for path in changed if not any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES)]
    if unexpected:
        raise CheckError("out-of-scope tracked change: " + ", ".join(unexpected))


def _check_public_boundary() -> None:
    forbidden = (
        "/Users/linzezhang/Downloads/KMFA_MetaData", "private_raw_source_index",
        "应收账龄表2025_private_copy", "生产项目状态表_private_copy",
    )
    roots = [builder.OUTPUT_ROOT, builder.PROJECT_ROOT / "tools/v015_s10_stage_review_contract.py"]
    for root in roots:
        paths = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="ignore")
            matches = [token for token in forbidden if token in text]
            if matches:
                raise CheckError(f"private/raw token in public review output: {path}: {matches}")


def _check_predecessors() -> None:
    evidence = _read_json(builder.MACHINE_ROOT / "phase_evidence_public_safe.json")
    expected = {"phase_count": 3, "phase_passed_count": 3, "task_count": 9, "task_accepted_count": 9, "predecessor_receipt_count": 57}
    if evidence.get("accounting") != expected:
        raise CheckError("predecessor accounting drift")
    if any(row.get("acceptance_status") != "PASSED" or row.get("validation_receipt_count") != 19 for row in evidence["phases"]):
        raise CheckError("predecessor acceptance drift")


def _check_review_evidence() -> None:
    contracts = _read_json(builder.MACHINE_ROOT / "cross_phase_contracts_public_safe.json")
    if contracts.get("accounting") != {"total": 24, "passed": 24, "failed": 0, "blocking_failed": 0}:
        raise CheckError("cross-phase contract accounting drift")
    verification = _read_json(builder.MACHINE_ROOT / "cross_phase_verification_public_safe.json")
    if verification.get("accounting") != {"total": 36, "passed": 36, "failed": 0}:
        raise CheckError("live cross-part verification drift")
    findings = _read_csv(builder.MACHINE_ROOT / "stage10_review_findings_public_safe.csv")
    if [row.get("finding_id") for row in findings] != ["S10REV-F001", "S10REV-F002", "S10REV-F003"]:
        raise CheckError("review finding identity drift")
    if any(row.get("status") != "FIXED_VALIDATED" or row.get("blocks_stage_acceptance") != "false" for row in findings):
        raise CheckError("review finding closure drift")
    risks = _read_csv(builder.MACHINE_ROOT / "open_risk_register_public_safe.csv")
    if len(risks) != 5 or any(row.get("status") != "ROUTED_RESIDUAL" or row.get("plan_complete") != "true" or row.get("blocks_s10_stage_acceptance") != "false" for row in risks):
        raise CheckError("risk route drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _read_json(builder.MANIFEST_PATH)
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
        "decision": "REMAIN_IN_S10_STAGE_REVIEW" if pre_final else "GO_TO_S11_P1_ONLY",
        "s10_stage_review_started": True,
        "s10_stage_review_performed": not pre_final,
        "s10_stage_review_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s11_entry_allowed": not pre_final,
        "s11_p1_entry_allowed": not pre_final,
        "s11_p1_started": False,
        "overall_accepted_phase_count": 28,
        "overall_taskpack_phase_count": 72,
        "automatic_connector_enabled_count": 0,
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
    lifecycle = "IN_PROGRESS" if pre_final else "COMPLETED"
    decision = "REMAIN_IN_S10_STAGE_REVIEW" if pre_final else "GO_TO_S11_P1_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        tokens = (
            builder.RUN_PHASE_ID, builder.TASK_ID, builder.ACCEPTANCE_ID,
            "active_formula_count: 356", "active_parameter_count: 1740",
            'current_parameter_range: "PARAM-KMFA-2119..2125"',
            f'stage_lifecycle_status: "{lifecycle}"', f'stage_acceptance_status: "{status}"',
            f'decision: "{decision}"', "s10_stage_review_started: true",
            f"s10_stage_review_performed: {str(not pre_final).lower()}",
            f"s11_p1_entry_allowed: {str(not pre_final).lower()}", "s11_p1_started: false",
            "github_upload_performed: false", "app_reinstall_performed: false",
        )
        for token in tokens:
            if token not in text:
                raise CheckError(f"governance token missing from {relative}: {token}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    receipts = _read_jsonl(builder.VALIDATION_RESULTS_PATH)
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
        raise CheckError("final evidence commit must be the immediate child of validation_head")
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
    args = parser.parse_args()
    try:
        if args.public_boundary_check:
            _check_public_boundary()
        else:
            run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts, skip_clean_commit=args.skip_clean_commit)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S10 整体复审严格检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
