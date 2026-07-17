#!/usr/bin/env python3
"""Strict pre-final/final checker for KMFA v1.5 S06-P3."""

from __future__ import annotations

import argparse
import json
import stat
import subprocess
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import build_v015_s06_p3_baseline_coverage_boundary as builder
from KMFA.tools import v015_s06_p2_golden_baseline_lock as p2
from KMFA.tools import v015_s06_p3_baseline_coverage_boundary as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_BASE = "4227449c0b13c2ffcb6bcdaca9be52d6a34cc45a"
EXPECTED_VALIDATIONS = (
    (builder.EXPECTED_VALIDATION_NAMES[0], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p3_baseline_coverage_boundary"),
    (builder.EXPECTED_VALIDATION_NAMES[1], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p3_baseline_coverage_boundary_governance"),
    (builder.EXPECTED_VALIDATION_NAMES[2], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    (builder.EXPECTED_VALIDATION_NAMES[3], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py --dependency-check"),
    (builder.EXPECTED_VALIDATION_NAMES[4], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    (builder.EXPECTED_VALIDATION_NAMES[5], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    (builder.EXPECTED_VALIDATION_NAMES[6], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    (builder.EXPECTED_VALIDATION_NAMES[7], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    (builder.EXPECTED_VALIDATION_NAMES[8], f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {PHASE_BASE} --enforce-sync"),
    (builder.EXPECTED_VALIDATION_NAMES[9], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    (builder.EXPECTED_VALIDATION_NAMES[10], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    (builder.EXPECTED_VALIDATION_NAMES[11], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py --public-boundary-check"),
    (builder.EXPECTED_VALIDATION_NAMES[12], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py --private-boundary-check"),
    (builder.EXPECTED_VALIDATION_NAMES[13], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s06_p3_baseline_coverage_boundary.py --check"),
    (builder.EXPECTED_VALIDATION_NAMES[14], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m py_compile KMFA/tools/v015_s06_p3_baseline_coverage_boundary.py KMFA/tools/build_v015_s06_p3_baseline_coverage_boundary.py KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py KMFA/tools/run_v015_s06_p3_validations.py"),
    (builder.EXPECTED_VALIDATION_NAMES[15], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p3_baseline_coverage_boundary KMFA.tests.test_v015_s06_p3_baseline_coverage_boundary_governance KMFA.tests.test_v015_roadmap_governance_sync"),
    (builder.EXPECTED_VALIDATION_NAMES[16], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py --structured-public-diff-check"),
    (builder.EXPECTED_VALIDATION_NAMES[17], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p3_baseline_coverage_boundary.py --raw-invariant-check"),
)


class CheckError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _dependency() -> None:
    dependency = builder._dependency()
    _require(dependency["acceptance_status"] == "PASSED", "S06-P2 acceptance mismatch")
    _require(dependency["receipt_count"] == 20, "S06-P2 receipt count mismatch")


def _private_boundary() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    fixture, queue, coverage = kernel.validate_private_outputs()
    for path in (
        kernel.PRIVATE_FIXTURE_PATH, kernel.PRIVATE_QUEUE_PATH,
        kernel.PRIVATE_COVERAGE_PATH, kernel.PRIVATE_SUMMARY_PATH,
    ):
        _require(stat.S_IMODE(path.stat().st_mode) == 0o600, f"private mode mismatch: {path.name}")
        ignored = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=REPO_ROOT, check=False)
        _require(ignored.returncode == 0, f"private file is not ignored: {path.name}")
    _require(fixture["project_count"] == 8 and fixture["money_difference_cents"] == 0, "fixture aggregate mismatch")
    _require(queue["item_count"] == 147, "open queue count mismatch")
    _require(queue["impact_present_count"] == queue["resolution_path_present_count"] == 147, "queue routing incomplete")
    _require(coverage["covered_scenario_count"] == 4 and coverage["missing_scenario_count"] == 1, "coverage mismatch")
    _require(coverage["future_samples"][0]["scenario"] == "CROSS_PERIOD", "future sample routing mismatch")
    return fixture, queue, coverage


def _raw_invariant() -> None:
    p1 = _json(p2.P1_MANIFEST_PATH)
    before = p2._raw_invariants(p1)
    after = p2._raw_invariants(p1)
    _require(before == after, "raw invariant drifted")
    _require(before == {
        "raw_root_stat_unchanged": True,
        "package_stat_unchanged": True,
        "raw_mutation_performed": False,
    }, "raw invariant failed")


def _public_boundary() -> None:
    projection = kernel.current_public_projection()
    _require(projection["public_project_identity_count"] == 0, "public identity leak counter")
    _require(projection["public_money_value_count"] == 0, "public money leak counter")
    _require(projection["public_source_locator_count"] == 0, "public locator leak counter")
    _require(projection["public_private_fixture_hash_count"] == 0, "public private-hash leak counter")
    public = json.dumps({
        "contract": _json(builder.CONTRACT_PATH),
        "manifest": _json(builder.MANIFEST_PATH),
        "matrix": _json(builder.TASK_MATRIX_PATH),
    }, ensure_ascii=False)
    for forbidden in ("project_summaries", "source_golden_record_hash", "fixture_digest", "source_locator"):
        _require(f'"{forbidden}"' not in public, f"public machine evidence contains private field: {forbidden}")


def _structured_public_diff() -> None:
    fixture, queue, _ = _private_boundary()
    tracked = _git("diff", "--name-only", PHASE_BASE, "--", "KMFA")
    _require(".codex_private_runtime" not in tracked, "private runtime entered tracked diff")
    paths = [REPO_ROOT / line for line in tracked.splitlines() if line and (REPO_ROOT / line).is_file()]
    rendered = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in paths
        if path.suffix.lower() in {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".py"}
    )
    sensitive_tokens = {
        str(row.get("project_identity") or "").strip() for row in fixture["project_summaries"]
    } | {
        str(row.get("source_locator") or "").strip() for row in queue["items"]
    }
    sensitive_tokens = {token for token in sensitive_tokens if len(token) >= 8}
    _require(not any(token in rendered for token in sensitive_tokens), "private project or locator leaked")
    _require(fixture["fixture_digest"] not in rendered, "private fixture digest leaked")


def _public_and_governance(pre_final: bool) -> None:
    builder.check_outputs()
    manifest = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    expected = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    _require(manifest["phase_acceptance_status"] == expected, "manifest acceptance mismatch")
    _require(manifest["validation_receipt_count"] == (0 if pre_final else 18), "receipt count mismatch")
    _require(manifest["task_accepted_count"] == (0 if pre_final else 3), "task acceptance mismatch")
    _require(manifest["stage_execution_percentage"] == 100, "stage execution mismatch")
    _require(manifest["stage_acceptance_status"] == "PENDING", "stage acceptance must remain pending")
    _require(manifest["s06_stage_review_entry_allowed"] is (not pre_final), "stage review entry mismatch")
    _require(manifest["s06_stage_review_started"] is False, "stage review must not start")
    _require(matrix["task_execution_complete_count"] == 3, "task execution mismatch")
    _require(matrix["task_accepted_count"] == (0 if pre_final else 3), "matrix acceptance mismatch")
    governance = Path("KMFA/docs/governance/project.yaml").read_text(encoding="utf-8") + Path(
        "KMFA/metadata/project/project.yaml"
    ).read_text(encoding="utf-8")
    for token in (
        'current_phase_id: "V015_S06_P3_BASELINE_COVERAGE_BOUNDARY"',
        f'phase_acceptance_status: "{expected}"',
        "active_formula_count: 339", "active_parameter_count: 1589",
        "s06_p3_started: true", f's06_p3_acceptance_status: "{expected}"',
        f"s06_stage_review_entry_allowed: {str(not pre_final).lower()}",
        "s06_stage_review_started: false", "github_upload_performed: false",
        "app_reinstall_performed: false",
    ):
        _require(token in governance, f"governance token missing: {token}")


def _receipts_and_commit(skip_validation_receipts: bool, skip_clean_commit: bool) -> None:
    if not skip_validation_receipts:
        receipts = builder._final_receipts()
        _require(len(receipts) == len(EXPECTED_VALIDATIONS), "final receipt set missing")
        _require([row["name"] for row in receipts] == [name for name, _ in EXPECTED_VALIDATIONS], "receipt names drifted")
        _require([row["command"] for row in receipts] == [command for _, command in EXPECTED_VALIDATIONS], "receipt commands drifted")
    if not skip_clean_commit:
        _require(not _git("status", "--porcelain"), "final validation requires a clean commit")


def validate(
    *, pre_final: bool = False, skip_validation_receipts: bool = False,
    skip_clean_commit: bool = False, dependency_only: bool = False,
    private_only: bool = False, public_only: bool = False,
    structured_only: bool = False, raw_only: bool = False,
) -> None:
    if dependency_only:
        _dependency(); return
    if private_only:
        _private_boundary(); return
    if public_only:
        _public_boundary(); return
    if structured_only:
        _structured_public_diff(); return
    if raw_only:
        _raw_invariant(); return
    _dependency()
    _private_boundary()
    _raw_invariant()
    _public_boundary()
    _structured_public_diff()
    _public_and_governance(pre_final)
    _receipts_and_commit(skip_validation_receipts, skip_clean_commit)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check KMFA v1.5 S06-P3")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--private-boundary-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--raw-invariant-check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        validate(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
            dependency_only=args.dependency_check,
            private_only=args.private_boundary_check,
            public_only=args.public_boundary_check,
            structured_only=args.structured_public_diff_check,
            raw_only=args.raw_invariant_check,
        )
    except (CheckError, kernel.BoundaryError, p2.GoldenBaselineError, builder.BuildError,
            OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: KMFA v1.5 S06-P3 baseline coverage boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
