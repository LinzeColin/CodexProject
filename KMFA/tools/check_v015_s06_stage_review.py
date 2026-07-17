#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S06 Stage Review."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s06_stage_review as builder


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VALIDATIONS = (
    ("python_compile", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s06_stage_review_contract.py','KMFA/tools/build_v015_s06_stage_review.py','KMFA/tools/check_v015_s06_stage_review.py','KMFA/tools/run_v015_s06_stage_review_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("stage_binding_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_stage_review_contract"),
    ("stage_review_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_stage_review"),
    ("stage_review_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_stage_review_governance"),
    ("s06_p1_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p1_authoritative_source_registration"),
    ("s06_p2_resolution_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_authorized_resolution"),
    ("s06_p2_golden_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_golden_baseline_lock"),
    ("s06_p3_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p3_baseline_coverage_boundary"),
    ("s06_p3_governance_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p3_baseline_coverage_boundary_governance"),
    ("builder_exact_rebuild", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s06_stage_review.py --check"),
    ("stage_checker_pre_final", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_stage_review.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.REVIEW_BASE_COMMIT} --enforce-sync"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("structured_public_diff", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_stage_review.py --structured-public-diff-check"),
    ("git_diff_check", f"git diff --check {builder.REVIEW_BASE_COMMIT}..HEAD"),
)

ALLOWED_REVIEW_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/",
    "KMFA/metadata/quality/v015_s06_p3_baseline_coverage_boundary_public_safe.json",
    "KMFA/stage_artifacts/V015_S06_P3_BASELINE_COVERAGE_BOUNDARY/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py", "KMFA/tests/test_v015_s06_stage_review.py",
    "KMFA/tests/test_v015_s06_stage_review_contract.py", "KMFA/tests/test_v015_s06_stage_review_governance.py",
    "KMFA/tests/test_v015_s06_p3_baseline_coverage_boundary.py",
    "KMFA/tests/test_v015_s06_p3_baseline_coverage_boundary_governance.py",
    "KMFA/tools/build_v015_s06_stage_review.py", "KMFA/tools/check_v015_s06_stage_review.py",
    "KMFA/tools/run_v015_s06_stage_review_validations.py", "KMFA/tools/v015_s06_stage_review_contract.py",
    "KMFA/tools/build_v015_s06_p3_baseline_coverage_boundary.py",
    "KMFA/tools/v015_s06_p3_baseline_coverage_boundary.py",
    "KMFA/tools/v015_roadmap_governance_sync.py", "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)

FINAL_MUTABLE_PATHS = frozenset({
    "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md", "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md", "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml", "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl", "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/project.yaml", "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/human/stage6_review_report_zh.md",
    "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/human/test_results_zh.md",
    "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/machine/s06_stage_review_manifest.json",
    "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/machine/validation_results.jsonl",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
})


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _is_allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_REVIEW_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.REVIEW_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("review base is not an ancestor of HEAD")
    changed = _git("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.REVIEW_BASE_COMMIT}..HEAD").splitlines()
    unexpected = [path for path in changed if path and not _is_allowed(path)]
    if unexpected:
        raise CheckError("unexpected review path(s): " + ", ".join(unexpected))


def _check_public_safe() -> None:
    texts = "\n".join(path.read_text(encoding="utf-8") for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file() and path != builder.VALIDATION_RESULTS_PATH)
    if re.search(r"(?:/Users/|/Volumes/|/home/|file://|KMFA_MetaData)", texts):
        raise CheckError("review evidence contains private path/root material")
    if re.search(r"sha256:[a-f0-9]{64}", texts):
        raise CheckError("review evidence contains private-style source digest")
    if any(token in texts for token in (".xlsx", ".xls")):
        raise CheckError("review evidence contains source filename extension")


def _check_structured_public_diff() -> None:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "diff", "--name-only", builder.REVIEW_BASE_COMMIT, "--", "KMFA"],
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
        try:
            if path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix.lower() == ".jsonl":
                _read_jsonl(path)
            elif path.suffix.lower() == ".csv":
                _read_csv(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise CheckError(f"structured parse failed: {relative}: {error}") from error


def _check_predecessors() -> None:
    evidence = _read_json(builder.MACHINE_ROOT / "phase_evidence_public_safe.json")
    expected = {"phase_count": 3, "phase_passed_count": 3, "task_count": 9, "task_accepted_count": 9, "predecessor_receipt_count": 58}
    if evidence.get("accounting") != expected:
        raise CheckError("predecessor accounting drift")
    for row in evidence["phases"]:
        if row.get("acceptance_status") != "PASSED" or not re.fullmatch(r"[0-9a-f]{40}", str(row.get("validation_head") or "")):
            raise CheckError("predecessor identity/status drift")
        if subprocess.run(["git", "merge-base", "--is-ancestor", row["validation_head"], "HEAD"], cwd=REPO_ROOT, check=False).returncode:
            raise CheckError("predecessor validation head is not reachable")


def _check_review_evidence() -> None:
    contracts = _read_json(builder.MACHINE_ROOT / "cross_phase_contracts_public_safe.json")
    if contracts.get("accounting") != {"total": 20, "passed": 20, "failed": 0, "blocking_failed": 0}:
        raise CheckError("cross-Phase contract accounting drift")
    if [row.get("contract_id") for row in contracts["contracts"]] != [f"S06REV-C{i:02d}" for i in range(1, 21)] or any(row.get("status") != "PASS" for row in contracts["contracts"]):
        raise CheckError("cross-Phase contract identity/status drift")
    binding = _read_json(builder.MACHINE_ROOT / "cross_phase_binding_verification_public_safe.json")
    if binding.get("accounting") != {"total": 12, "passed": 12, "failed": 0}:
        raise CheckError("executable binding accounting drift")
    if binding.get("golden_fixture_money_difference_cents") != 0 or binding.get("empirical_coverage_complete") is not False:
        raise CheckError("golden fixture or empirical coverage boundary drift")
    if any(binding.get(key) is not False for key in ("downstream_cross_period_claim_allowed", "tax_normalization_allowed", "open_items_may_be_treated_as_resolved")):
        raise CheckError("downstream boundary gate drift")
    findings = _read_csv(builder.MACHINE_ROOT / "stage6_review_findings_public_safe.csv")
    if [row.get("finding_id") for row in findings] != ["S06REV-F001", "S06REV-F002"] or any(row.get("status") != "FIXED_VALIDATED" or row.get("blocks_stage_acceptance") != "false" for row in findings):
        raise CheckError("review finding closure drift")
    risks = _read_csv(builder.MACHINE_ROOT / "open_risk_register_public_safe.csv")
    if len(risks) != 5 or any(row.get("status") != "ROUTED_RESIDUAL" or row.get("plan_complete") != "true" or row.get("blocks_s06_stage_acceptance") != "false" for row in risks):
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
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "stage_lifecycle_status": "IN_PROGRESS" if pre_final else "COMPLETED",
        "stage_acceptance_status": "PENDING" if pre_final else "PASSED",
        "decision": "REMAIN_IN_S06_STAGE_REVIEW" if pre_final else "GO_TO_S07_P1_ONLY",
        "s06_stage_review_started": True,
        "s06_stage_review_performed": not pre_final,
        "s06_stage_review_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s07_p1_entry_allowed": not pre_final,
        "s07_p1_started": False,
        "s07_p2_plus_entry_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches:
        raise CheckError("manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    status = "PENDING" if pre_final else "PASSED"
    lifecycle = "IN_PROGRESS" if pre_final else "COMPLETED"
    decision = "REMAIN_IN_S06_STAGE_REVIEW" if pre_final else "GO_TO_S07_P1_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            builder.RUN_PHASE_ID, builder.TASK_ID, builder.ACCEPTANCE_ID,
            "active_formula_count: 340", "active_parameter_count: 1595",
            'current_parameter_range: "PARAM-KMFA-1975..1980"',
            f'stage_lifecycle_status: "{lifecycle}"', f'stage_acceptance_status: "{status}"',
            f'decision: "{decision}"', "s06_stage_review_started: true",
            f"s06_stage_review_performed: {str(not pre_final).lower()}",
            f"s07_p1_entry_allowed: {str(not pre_final).lower()}", "s07_p1_started: false",
            "github_upload_performed: false", "app_reinstall_performed: false",
        ):
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
    head = next(iter(heads))
    run_id = next(iter(run_ids))
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
    _check_public_safe()
    _check_structured_public_diff()
    _check_predecessors()
    _check_review_evidence()
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
    parser.add_argument("--structured-public-diff-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.structured_public_diff_check:
            _check_structured_public_diff()
            print("PASS: S06 Stage Review structured public diff")
            return 0
        run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts, skip_clean_commit=args.skip_clean_commit)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: KMFA v1.5 S06 Stage Review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
