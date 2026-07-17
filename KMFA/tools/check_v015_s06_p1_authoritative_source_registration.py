#!/usr/bin/env python3
"""Strict validator for KMFA v1.5 S06-P1."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import build_v015_s06_p1_authoritative_source_registration as builder
from KMFA.tools import v015_s06_p1_authoritative_source_registration as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_BASE = "c409795a477a4dc0816752a26077b440ca684ccf"
FORMULA_ID = "FORM-KMFA-V015-S06-P1-AUTHORITATIVE-SOURCE-REGISTRATION-001"
PARAMETER_IDS = tuple(f"PARAM-KMFA-{value}" for value in range(1948, 1957))
EXPECTED_VALIDATIONS = (
    ("python_compile", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s06_p1_authoritative_source_registration.py','KMFA/tools/build_v015_s06_p1_authoritative_source_registration.py','KMFA/tools/check_v015_s06_p1_authoritative_source_registration.py','KMFA/tools/run_v015_s06_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\""),
    ("phase_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p1_authoritative_source_registration"),
    ("phase_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p1_authoritative_source_registration_governance"),
    ("private_scan_replay", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. $HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B KMFA/tools/v015_s06_p1_authoritative_source_registration.py --private-scan"),
    ("builder_exact_rebuild", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s06_p1_authoritative_source_registration.py --check"),
    ("phase_checker_pre_final", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p1_authoritative_source_registration.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    ("s05_review_contract_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s05_stage_review_contract"),
    ("s05_review_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s05_stage_review"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {PHASE_BASE} --enforce-sync"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("structured_public_diff", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p1_authoritative_source_registration.py --structured-public-diff-check"),
    ("s05_p3_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s05_p3_field_standardization"),
    ("s05_review_builder_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s05_stage_review.py --check"),
    ("git_diff_check", f"git diff --check {PHASE_BASE}..HEAD"),
)
FINAL_MUTABLE_PATHS = frozenset({
    "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md", "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md", "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml", "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl", "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/project.yaml", "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
    str(builder.MANIFEST_PATH), str(builder.TASK_MATRIX_PATH), str(builder.RECEIPTS_PATH),
    str(builder.COMPLETION_PATH), str(builder.TEST_RESULTS_PATH),
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
})
PUBLIC_PHASE_FILES = (
    builder.SOURCE_REGISTER_PATH, builder.FIELD_COVERAGE_PATH, builder.TEMPLATE_STRATEGY_PATH,
    builder.MANIFEST_PATH, builder.TASK_MATRIX_PATH, builder.COMPLETION_PATH,
    builder.TEST_RESULTS_PATH, builder.OPEN_RISKS_PATH, builder.ROLLBACK_PATH,
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
    if not path.exists():
        return []
    values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(value, dict) for value in values):
        raise CheckError(f"JSONL objects required: {path}")
    return values


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def _private_current() -> dict[str, Any]:
    path = kernel.PRIVATE_MANIFEST_PATH
    _require(path.exists(), "private S06-P1 manifest is missing")
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "private manifest must be mode 0600")
    _require(stat.S_IMODE(path.parent.stat().st_mode) == 0o700, "private directory must be mode 0700")
    ignored = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=REPO_ROOT, check=False)
    _require(ignored.returncode == 0, "private manifest must be Git-ignored")
    _require(str(path) not in set(_git("ls-files").splitlines()), "private manifest must not be tracked")
    private = kernel.read_private_payload(path)
    raw_root = Path(private["private_raw_root"])
    package = Path(private["private_package_path"])
    _require(raw_root.is_dir() and package.is_file(), "current raw root or authority package is unavailable")
    _require(kernel._stat_snapshot(raw_root) == private["raw_root_after"], "raw root stat drifted after private scan")
    _require(kernel._stat_snapshot(package) == private["package_after"], "authority package stat drifted after private scan")
    return private


def _validate_public_artifacts(private: dict[str, Any]) -> None:
    builder.check_outputs()
    projection = kernel.public_projection(private)
    _require(_json(builder.SOURCE_REGISTER_PATH) == projection["registration"], "source register projection mismatch")
    _require(_json(builder.FIELD_COVERAGE_PATH) == projection["coverage"], "field coverage projection mismatch")
    _require(_json(builder.TEMPLATE_STRATEGY_PATH) == projection["template"], "template projection mismatch")
    manifest = _json(builder.MANIFEST_PATH)
    expected = {
        "authority_source_count": 9,
        "authority_pdf_count": 8,
        "authority_workbook_count": 1,
        "source_readable_hashed_count": 9,
        "field_family_count": 6,
        "covered_field_family_count": 6,
        "private_field_candidate_count": 157,
        "contract_total_locator_collision_count": 0,
        "supporting_pdf_promoted_candidate_count": 0,
        "margin_header_gross_profit_candidate_count": 0,
        "workbook_summary_candidate_count": 0,
        "observed_template_class_count": 6,
        "template_strategy_covered_count": 6,
        "unknown_template_source_count": 0,
        "quarantined_component_count": 1,
        "textless_page_count": 1,
        "formula_cell_count": 89,
        "cached_formula_display_count": 89,
        "workbook_embedded_media_count": 6,
        "ocr_final_fact_count": 0,
        "golden_value_confirmed_count": 0,
        "public_raw_name_count": 0,
        "public_raw_hash_count": 0,
        "public_raw_text_count": 0,
        "public_raw_value_count": 0,
        "public_sheet_name_count": 0,
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"manifest {key} mismatch")
    _require(manifest.get("formula_and_display_values_separated") is True, "formula/display separation missing")
    _require(manifest.get("candidate_semantic_quality_passed") is True, "candidate semantic quality gate failed")
    _require(manifest.get("s05_stage_review_dependency_validated") is True, "S05 review dependency missing")
    _require(manifest.get("raw_root_stat_unchanged") is True, "raw root stat invariant failed")
    _require(manifest.get("package_stat_unchanged") is True, "package stat invariant failed")
    _require(manifest.get("package_hash_unchanged") is True, "package hash invariant failed")
    for key in (
        "raw_write_performed", "raw_delete_performed", "raw_move_performed", "raw_rename_performed",
        "raw_overwrite_performed", "raw_mutation_performed", "s06_p2_started",
        "s06_p3_entry_allowed", "s06_stage_review_entry_allowed", "formal_report_generated",
        "github_upload_performed", "app_reinstall_performed", "business_execution_performed",
    ):
        _require(manifest.get(key) is False, f"boundary {key} must be false")
    task_matrix = _json(builder.TASK_MATRIX_PATH)
    _require(task_matrix.get("task_count") == 3, "task matrix count mismatch")
    _require(task_matrix.get("task_execution_complete_count") == 3, "task execution count mismatch")


def _public_safety(private: dict[str, Any]) -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_PHASE_FILES if path.exists())
    for token in ("/Users/", "/Volumes/", "file://", "KMFA_MetaData", ".codex_private_runtime"):
        _require(token not in combined, f"private path token leaked into public evidence: {token}")
    _require(not re.search(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", combined, re.I), "private SHA-256 leaked into public evidence")
    sensitive: set[str] = {
        private.get("private_package_name", ""), private.get("private_package_sha256", ""),
        private.get("private_package_path", ""), private.get("private_raw_root", ""),
    }
    for source in private["source_records"]:
        sensitive.update({
            str(source.get("private_member_name", "")), str(source.get("private_member_sha256", "")),
        })
        inspection = source["inspection"]
        for sheet in inspection.get("sheets", []):
            sensitive.add(str(sheet.get("private_sheet_name", "")))
        for candidate in inspection.get("field_candidates", []):
            raw_text = str(candidate.get("raw_text", ""))
            if len(raw_text) >= 12:
                sensitive.add(raw_text)
    for value in sensitive:
        if value and len(value) >= 4:
            _require(value not in combined, "private source-derived value leaked into public evidence")


def _governance(pre_final: bool) -> None:
    expected_acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    expected_validation = "PENDING" if pre_final else "PASS"
    expected_decision = "REMAIN_IN_S06_P1" if pre_final else "CONTINUE_TO_S06_P2_ONLY"
    common_tokens = (
        'phase_execution_status: "EXECUTION_COMPLETE"',
        f'phase_acceptance_status: "{expected_acceptance}"',
        f'evidence_validation_status: "{expected_validation}"',
        'stage_lifecycle_status: "IN_PROGRESS"', 'stage_acceptance_status: "PENDING"',
        'stage_execution_percentage: 33', f'decision: "{expected_decision}"',
        's06_p1_started: true', f's06_p1_acceptance_status: "{expected_acceptance}"',
        f's06_p2_entry_allowed: {str(not pre_final).lower()}', 's06_p2_started: false',
        's06_p1_authority_source_count: 9', 's06_p1_private_candidate_count: 157',
        's06_p1_template_class_count: 6', 's06_p1_raw_mutation_performed: false',
        f'next_gate_id: "{"S06-P1-FINAL-VALIDATION" if pre_final else "S06-P2"}"',
    )
    project_specific = (
        'current_stage_id: "S06"', f'current_phase_id: "{kernel.RUN_PHASE_ID}"',
        f'current_task_id: "{kernel.TASK_ID}"', f'current_acceptance_id: "{kernel.ACCEPTANCE_ID}"',
    )
    mirror_specific = (
        'current_stage: "S06"', f'current_phase: "{kernel.RUN_PHASE_ID}"',
        f'current_task: "{kernel.TASK_ID}"', f'current_acceptance: "{kernel.ACCEPTANCE_ID}"',
    )
    for path, specific in (
        (Path("KMFA/docs/governance/project.yaml"), project_specific),
        (Path("KMFA/metadata/project/project.yaml"), mirror_specific),
    ):
        text = path.read_text(encoding="utf-8")
        for token in common_tokens + specific:
            _require(token in text, f"governance token missing from {path}: {token}")
    formula = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    params = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
    models = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    metadata_models = Path("KMFA/metadata/model_registry.yaml").read_text(encoding="utf-8")
    _require(formula.count(FORMULA_ID) >= 1, "S06-P1 formula missing")
    for parameter_id in PARAMETER_IDS:
        _require(params.count(parameter_id + ",") == 1, f"parameter missing or duplicated: {parameter_id}")
    _require("kmfa_v015_s06_p1_authoritative_source_registration:" in models, "governance model block missing")
    _require("kmfa_v015_s06_p1_authoritative_source_registration:" in metadata_models, "metadata model block missing")
    for path in (
        "KMFA/HANDOFF.md", "KMFA/开发记录.md", "KMFA/功能清单.md", "KMFA/模型参数文件.md",
    ):
        _require("v1.5 S06-P1" in Path(path).read_text(encoding="utf-8"), f"S06-P1 entry missing: {path}")


def _receipts_and_commit(skip_validation_receipts: bool, skip_clean_commit: bool) -> None:
    if skip_validation_receipts:
        return
    manifest = _json(builder.MANIFEST_PATH)
    receipts = _jsonl(builder.RECEIPTS_PATH)
    expected = dict(EXPECTED_VALIDATIONS)
    _require(len(receipts) == len(expected), "exactly twenty final validation receipts are required")
    _require([row.get("name") for row in receipts] == list(expected), "validation receipt order/identity drifted")
    for row in receipts:
        name = str(row.get("name"))
        _require(row.get("command") == expected[name], f"validation command drifted: {name}")
        _require(row.get("status") == "PASS" and row.get("exit_code") == 0, f"validation failed: {name}")
        _require(bool(re.fullmatch(r"sha256:[0-9a-f]{64}", str(row.get("output_sha256") or ""))), f"invalid output digest: {name}")
    run_ids = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    _require(len(run_ids) == len(heads) == 1, "receipt run/head identity is mixed")
    run_id, validation_head = next(iter(run_ids)), next(iter(heads))
    _require(manifest.get("validation_run_id") == run_id, "manifest validation run mismatch")
    _require(manifest.get("validation_head") == validation_head, "manifest validation head mismatch")
    _require(manifest.get("validation_receipt_count") == 20, "manifest receipt count mismatch")
    if skip_clean_commit:
        return
    _require(not _git("status", "--porcelain"), "final checker requires a clean worktree")
    head = _git("rev-parse", "HEAD")
    parent = _git("rev-parse", "HEAD^")
    _require(parent == validation_head, "final evidence commit must be immediate child of validation HEAD")
    changed = set(_git("diff", "--name-only", validation_head, head).splitlines())
    unexpected = sorted(changed - FINAL_MUTABLE_PATHS)
    _require(not unexpected, "unexpected post-validation paths: " + ", ".join(unexpected))


def _structured_public_diff(private: dict[str, Any]) -> None:
    changed = _git("diff", "--name-only", PHASE_BASE)
    _require("KMFA/tools/v015_s06_p1_authoritative_source_registration.py" in changed, "phase implementation missing from diff")
    _public_safety(private)


def validate(
    *, pre_final: bool = False, skip_validation_receipts: bool = False,
    skip_clean_commit: bool = False, structured_public_diff_only: bool = False,
) -> None:
    private = _private_current()
    if structured_public_diff_only:
        _structured_public_diff(private)
        return
    _validate_public_artifacts(private)
    _public_safety(private)
    _governance(pre_final)
    manifest = _json(builder.MANIFEST_PATH)
    expected_acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    _require(manifest.get("phase_acceptance_status") == expected_acceptance, "manifest phase acceptance mismatch")
    _require(manifest.get("task_accepted_count") == (0 if pre_final else 3), "manifest task acceptance mismatch")
    _require(manifest.get("s06_p2_entry_allowed") is (not pre_final), "manifest next entry mismatch")
    _receipts_and_commit(skip_validation_receipts, skip_clean_commit)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check KMFA v1.5 S06-P1")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        validate(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
            structured_public_diff_only=args.structured_public_diff_check,
        )
    except (CheckError, kernel.RegistrationError, builder.BuildError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: KMFA v1.5 S06-P1 authoritative source registration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
