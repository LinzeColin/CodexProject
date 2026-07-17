#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S08-P3."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s08_p3_matching_quality_confirmation as builder
from KMFA.tools import v015_s08_p3_matching_quality_confirmation as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    ("focused_kernel_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_p3_matching_quality_confirmation"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_p3_matching_quality_confirmation_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s08_p3_matching_quality_confirmation_governance"),
    ("pre_final_phase_checker", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p3_matching_quality_confirmation.py --pre-final --skip-validation-receipts"),
    ("s08_p2_dependency_check", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p3_matching_quality_confirmation.py --dependency-check"),
    ("legacy_matching_quality_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_entity_matching_quality KMFA.tests.test_v015_s08_p3_legacy_regression && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v014_s08_p3_entity_matching_quality.py"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S08_P3_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.PHASE_BASE_COMMIT} --enforce-sync"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("deterministic_evidence", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s08_p3_matching_quality_confirmation.py --check"),
    ("python_compile", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s08_p3_matching_quality_confirmation.py','KMFA/tools/build_v015_s08_p3_matching_quality_confirmation.py','KMFA/tools/check_v015_s08_p3_matching_quality_confirmation.py','KMFA/tools/run_v015_s08_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("structured_public_diff", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p3_matching_quality_confirmation.py --structured-public-diff-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s08_p3_matching_quality_confirmation.py --public-boundary-check"),
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
    "KMFA/metadata/quality/v015_s08_p3_matching_quality_confirmation_public_safe.json",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s08_p3_matching_quality_confirmation.py",
    "KMFA/tests/test_v015_s08_p3_matching_quality_confirmation_artifacts.py",
    "KMFA/tests/test_v015_s08_p3_matching_quality_confirmation_governance.py",
    "KMFA/tests/test_v015_s08_p3_legacy_regression.py",
    "KMFA/tools/build_v015_s08_p3_matching_quality_confirmation.py",
    "KMFA/tools/check_v015_s08_p3_matching_quality_confirmation.py",
    "KMFA/tools/run_v015_s08_p3_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s08_p3_matching_quality_confirmation.py",
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
        "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/human/implementation_report_zh.md",
        "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/machine/s08_p3_matching_quality_confirmation_manifest.json",
        "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/machine/task_acceptance_matrix_public_safe.json",
        "KMFA/stage_artifacts/V015_S08_P3_MATCHING_QUALITY_CONFIRMATION/machine/validation_results.jsonl",
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
        raise CheckError("S08-P3 base commit is not an ancestor of HEAD")
    committed = _git(
        "-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"
    ).splitlines()
    unstaged = _git("-c", "core.quotepath=false", "diff", "--name-only").splitlines()
    staged = _git("-c", "core.quotepath=false", "diff", "--cached", "--name-only").splitlines()
    untracked = _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard").splitlines()
    changed = committed + unstaged + staged + untracked
    unexpected = [path for path in changed if path and not _is_allowed(path)]
    if unexpected:
        raise CheckError("unexpected S08-P3 path(s): " + ", ".join(sorted(set(unexpected))))


def _check_dependency() -> None:
    value = builder.dependency()
    if value.get("acceptance_status") != "PASSED" or value.get("s08_p3_entry_allowed") is not True:
        raise CheckError("S08-P2 dependency is not accepted")
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S08-P2 validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S08-P2 validation head is not reachable")


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value] + [item for child in value.values() for item in _walk_keys(child)]
    if isinstance(value, list):
        return [item for child in value for item in _walk_keys(child)]
    return []


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
    paths.append(builder.CONTRACT_PATH)
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
            raise CheckError(f"public S08-P3 evidence contains forbidden material: {pattern}")
    forbidden_keys = {
        "raw_value",
        "plaintext_value",
        "source_path",
        "full_account_number",
        "bank_account_number",
        "fact_update",
    }
    for path in paths:
        if path.suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            leaked = forbidden_keys.intersection(_walk_keys(value))
            if leaked:
                raise CheckError(f"public S08-P3 evidence contains forbidden key(s): {sorted(leaked)}")
        elif path.suffix == ".jsonl":
            _read_jsonl(path)
    confirmation = _read_json(builder.CONFIRMATION_PATH)
    cards_text = json.dumps(confirmation.get("confirmation_cards"), ensure_ascii=False).lower()
    terms = [term for term in kernel.PLAIN_LANGUAGE_FORBIDDEN_TERMS if term.lower() in cards_text]
    if terms or confirmation.get("acceptance", {}).get("technical_term_occurrence_count") != 0:
        raise CheckError("confirmation UI exposes technical terms: " + ", ".join(terms))
    contract = _read_json(builder.CONTRACT_PATH)
    if (
        contract.get("raw_root_access_count") != 0
        or contract.get("private_business_values_published") is not False
        or contract.get("confirmation_source_mutation_performed") is not False
    ):
        raise CheckError("S08-P3 public contract crosses raw/private boundary")


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
            _read_jsonl(path)


def _check_evidence() -> None:
    policy = _read_json(builder.POLICY_PATH)["acceptance"]
    classification = _read_json(builder.CLASSIFICATION_PATH)["acceptance"]
    confirmation = _read_json(builder.CONFIRMATION_PATH)["acceptance"]
    events = _read_json(builder.EVENT_LEDGER_PATH)["acceptance"]
    recalculation = _read_json(builder.RECALCULATION_PATH)["acceptance"]
    tasks = _read_json(builder.TASK_MATRIX_PATH)
    if (
        policy.get("match_state_count") != 3
        or policy.get("auto_match_min_bps") != 8500
        or policy.get("candidate_review_min_bps") != 7000
        or policy.get("thresholds_externalized") is not True
        or policy.get("threshold_change_requires_regression") is not True
        or policy.get("silent_threshold_change_allowed") is not False
    ):
        raise CheckError("matching threshold policy evidence drift")
    if (
        classification.get("classification_case_count") != 4
        or classification.get("automatic_state_count") != 1
        or classification.get("candidate_state_count") != 1
        or classification.get("manual_state_count") != 2
        or classification.get("hard_conflict_manual_override_count") != 1
        or classification.get("reasoned_case_count") != 4
        or classification.get("regression_case_count") != 5
        or classification.get("regression_pass_count") != 5
        or classification.get("regression_fail_count") != 0
        or classification.get("regression_required_enforced") is not True
    ):
        raise CheckError("matching classification or regression evidence drift")
    if (
        confirmation.get("confirmation_card_count") != 2
        or confirmation.get("side_by_side_column_count_per_card") != 2
        or confirmation.get("display_field_count_per_candidate") != 6
        or confirmation.get("required_explanation_section_count") != 4
        or confirmation.get("decision_option_count") != 3
        or confirmation.get("technical_term_occurrence_count") != 0
        or confirmation.get("source_mutation_performed") is not False
        or confirmation.get("fact_table_mutation_performed") is not False
    ):
        raise CheckError("confirmation-flow acceptance evidence drift")
    if (
        events.get("control_event_count") != 4
        or events.get("decision_recorded_event_count") != 2
        or events.get("reversal_event_count") != 1
        or events.get("rollback_event_count") != 1
        or events.get("append_only_event_count") != 4
        or events.get("persistence_roundtrip_event_count") != 4
        or events.get("persistence_roundtrip_exact") is not True
        or events.get("direct_fact_mutation_rejected") is not True
        or events.get("source_snapshot_unchanged") is not True
        or events.get("fact_snapshot_unchanged") is not True
    ):
        raise CheckError("decision-event acceptance evidence drift")
    if (
        recalculation.get("recalculation_receipt_count") != 4
        or recalculation.get("recalculation_pass_count") != 4
        or recalculation.get("trigger_event_binding_count") != 4
        or recalculation.get("affected_node_count_per_receipt") != [3]
        or recalculation.get("raw_source_mutation_count") != 0
        or recalculation.get("fact_table_mutation_count") != 0
    ):
        raise CheckError("affected-chain recalculation evidence drift")
    if tasks.get("task_execution_complete_count") != 3 or len(tasks.get("tasks", [])) != 3:
        raise CheckError("S08-P3 task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _read_json(builder.MANIFEST_PATH)
    required = {
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "task_accepted_count": 0 if pre_final else 3,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "decision": "REMAIN_IN_S08_P3_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S08_STAGE_REVIEW_ONLY",
        "s08_p1_acceptance_status": "PASSED",
        "s08_p2_acceptance_status": "PASSED",
        "s08_p3_entry_allowed": False,
        "s08_p3_started": True,
        "s08_p3_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s08_stage_review_entry_allowed": not pre_final,
        "s08_stage_review_started": False,
        "s08_stage_review_performed": False,
        "overall_accepted_phase_count": 21 if pre_final else 22,
        "match_state_count": 3,
        "auto_match_min_bps": 8500,
        "candidate_review_min_bps": 7000,
        "thresholds_externalized": True,
        "threshold_change_requires_regression": True,
        "classification_case_count": 4,
        "policy_regression_case_count": 5,
        "policy_regression_fail_count": 0,
        "confirmation_card_count": 2,
        "confirmation_technical_term_occurrence_count": 0,
        "control_event_count": 4,
        "reversal_event_count": 1,
        "rollback_event_count": 1,
        "recalculation_receipt_count": 4,
        "direct_fact_mutation_rejected": True,
        "source_snapshot_unchanged": True,
        "fact_snapshot_unchanged": True,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "fact_table_mutation_performed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches:
        raise CheckError("S08-P3 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S08_P3_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S08_STAGE_REVIEW_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        required = (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            "active_formula_count: 347",
            "active_parameter_count: 1654",
            'current_parameter_range: "PARAM-KMFA-2030..2039"',
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 100",
            f'decision: "{decision}"',
            "s08_p3_started: true",
            f's08_p3_acceptance_status: "{acceptance}"',
            f"s08_stage_review_entry_allowed: {str(not pre_final).lower()}",
            "s08_stage_review_started: false",
            "product_implementation_allowed: false",
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
        raise CheckError("S08-P3 validation receipt count/order drift")
    runs = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    if len(runs) != 1 or None in runs or len(heads) != 1 or None in heads:
        raise CheckError("S08-P3 validation receipts do not share one head/run")
    for row in receipts:
        name = str(row.get("name"))
        if row.get("command") != expected[name] or row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"S08-P3 validation receipt failed/drifted: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or "")):
            raise CheckError(f"S08-P3 validation output digest invalid: {name}")
    head = next(iter(heads))
    run_id = next(iter(runs))
    if (
        manifest.get("validation_head") != head
        or manifest.get("validation_run_id") != run_id
        or manifest.get("validation_receipt_count") != len(receipts)
    ):
        raise CheckError("S08-P3 manifest validation binding drift")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final S08-P3 evidence commit must be the immediate child of validation head")
    mutable = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{head}..HEAD").splitlines())
    unexpected = sorted(mutable - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("post-validation mutation outside S08-P3 allowlist: " + ", ".join(unexpected))


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
            print("PASS: S08-P2 dependency is exact and reachable")
            return 0
        if args.structured_public_diff_check:
            _check_structured_public_diff()
            print("PASS: S08-P3 structured public diff")
            return 0
        if args.public_boundary_check:
            _check_public_boundary()
            print("PASS: S08-P3 public boundary")
            return 0
        run(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError, builder.BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: KMFA v1.5 S08-P3 Matching Quality and Confirmation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
