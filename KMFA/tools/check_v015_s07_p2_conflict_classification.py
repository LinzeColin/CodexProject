#!/usr/bin/env python3
"""Strict pre-final/final checker for KMFA v1.5 S07-P2."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import build_v015_s07_p2_conflict_classification as builder
from KMFA.tools import v015_s07_p2_conflict_classification as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_BASE = "63af2eef72576be1c317cd0c435d38c6255ba574"
EXPECTED_VALIDATIONS = (
    (builder.EXPECTED_VALIDATION_NAMES[0], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s07_p2_conflict_classification"),
    (builder.EXPECTED_VALIDATION_NAMES[1], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s07_p2_conflict_classification_governance"),
    (builder.EXPECTED_VALIDATION_NAMES[2], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s07_p2_conflict_classification.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    (builder.EXPECTED_VALIDATION_NAMES[3], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s07_p2_conflict_classification.py --dependency-check"),
    (builder.EXPECTED_VALIDATION_NAMES[4], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    (builder.EXPECTED_VALIDATION_NAMES[5], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    (builder.EXPECTED_VALIDATION_NAMES[6], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    (builder.EXPECTED_VALIDATION_NAMES[7], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    (builder.EXPECTED_VALIDATION_NAMES[8], f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {PHASE_BASE} --enforce-sync"),
    (builder.EXPECTED_VALIDATION_NAMES[9], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    (builder.EXPECTED_VALIDATION_NAMES[10], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    (builder.EXPECTED_VALIDATION_NAMES[11], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s07_p2_conflict_classification.py --public-boundary-check"),
    (builder.EXPECTED_VALIDATION_NAMES[12], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s07_p2_conflict_classification.py --private-conflict-boundary-check"),
    (builder.EXPECTED_VALIDATION_NAMES[13], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s07_p2_conflict_classification.py --check"),
    (builder.EXPECTED_VALIDATION_NAMES[14], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m py_compile KMFA/tools/v015_s07_p2_conflict_classification.py KMFA/tools/build_v015_s07_p2_conflict_classification.py KMFA/tools/check_v015_s07_p2_conflict_classification.py KMFA/tools/run_v015_s07_p2_validations.py"),
    (builder.EXPECTED_VALIDATION_NAMES[15], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s07_p2_conflict_classification KMFA.tests.test_v015_s07_p2_conflict_classification_governance KMFA.tests.test_v015_roadmap_governance_sync"),
    (builder.EXPECTED_VALIDATION_NAMES[16], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s07_p2_conflict_classification.py --structured-public-diff-check"),
    (builder.EXPECTED_VALIDATION_NAMES[17], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s07_p1_zero_delta_validator"),
)


class CheckError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args], cwd=REPO_ROOT,
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    _require(all(isinstance(row, dict) for row in rows), f"JSONL object rows required: {path}")
    return rows


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _dependency() -> None:
    value = builder.dependency()
    _require(value["acceptance_status"] == "PASSED", "S07-P1 is not passed")
    _require(value["validation_receipt_count"] == 18, "S07-P1 receipt count drift")


def _private_conflict_boundary() -> None:
    value = kernel.validate_private_conflict_boundary()
    _require(value["private_queue_item_count"] == 147, "private queue count drift")
    _require(value["private_open_unconfirmed_item_count"] == 128, "private open count drift")
    _require(value["private_conflict_candidate_count"] == 6, "private conflict candidate count drift")
    _require(value["private_conflict_auto_selected_count"] == 0, "private conflict was auto-selected")
    _require(value["private_conflict_candidates_treated_as_resolved"] is False, "private conflicts treated as resolved")
    for key in (
        "private_value_count_public", "private_identity_count_public",
        "private_source_locator_count_public", "private_digest_count_public",
    ):
        _require(value[key] == 0, f"private detail entered public count: {key}")


def _public_boundary() -> None:
    value = kernel.public_projection()
    _require(value["conflict_class_count"] == 2, "conflict classes drift")
    _require(value["responsibility_layer_count"] == 5, "responsibility layers drift")
    _require(value["same_source_rerun_resolved_count"] == 1, "same-source rerun success proof missing")
    _require(value["same_source_persistent_system_error_count"] == 1, "persistent system-error proof missing")
    _require(value["cross_source_conflict_count"] == 1, "cross-source conflict proof missing")
    _require(value["automatic_source_selection_allowed"] is False, "automatic source selection enabled")
    _require(value["system_problem_assigned_to_user_count"] == 0, "system problem assigned to user")
    machine = json.dumps({
        "contract": _json(builder.CONTRACT_PATH),
        "manifest": _json(builder.MANIFEST_PATH),
        "matrix": _json(builder.TASK_MATRIX_PATH),
        "same": _json(builder.SAME_SOURCE_PATH),
        "cross": _json(builder.CROSS_SOURCE_PATH),
        "responsibility": _json(builder.RESPONSIBILITY_PATH),
    }, ensure_ascii=False)
    for forbidden in (
        "project_summaries", "source_locator", "fixture_digest", "source_golden_record_hash",
        "project_identity", "queue_digest",
    ):
        _require(f'"{forbidden}"' not in machine, f"public evidence contains private field: {forbidden}")


def _structured_public_diff() -> None:
    changed = _git("diff", "--name-only", PHASE_BASE, "--", "KMFA").splitlines()
    _require(not any(".codex_private_runtime" in path for path in changed), "private runtime entered tracked diff")
    for relative in changed:
        path = REPO_ROOT / relative
        if not path.is_file():
            continue
        try:
            if path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix.lower() == ".jsonl":
                _jsonl(path)
            elif path.suffix.lower() == ".csv":
                _csv(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise CheckError(f"structured parse failed: {relative}: {error}") from error
    fixture, queue, _ = kernel.s06p3.validate_private_outputs()
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for relative in changed
        if (path := REPO_ROOT / relative).is_file()
        and path.suffix.lower() in {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".py"}
    )
    sensitive = {
        str(row.get("project_identity") or "").strip() for row in fixture["project_summaries"]
    } | {
        str(row.get("source_locator") or "").strip() for row in queue["items"]
    }
    _require(not any(token and len(token) >= 8 and token in text for token in sensitive), "private identity or source locator leaked")
    _require(fixture["fixture_digest"] not in text and queue["queue_digest"] not in text, "private digest leaked")


def _scope() -> None:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", PHASE_BASE, "HEAD"], cwd=REPO_ROOT, check=False)
    _require(result.returncode == 0, "phase base is not an ancestor")


def _public_and_governance(pre_final: bool) -> dict[str, Any]:
    builder.check_outputs()
    manifest = _json(builder.MANIFEST_PATH)
    expected = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    _require(manifest["phase_acceptance_status"] == expected, "manifest acceptance mismatch")
    _require(manifest["validation_receipt_count"] == (0 if pre_final else len(EXPECTED_VALIDATIONS)), "receipt count mismatch")
    _require(manifest["task_accepted_count"] == (0 if pre_final else 3), "task acceptance mismatch")
    _require(manifest["stage_execution_percentage"] == 67, "S07 stage execution must be 67 percent")
    _require(manifest["stage_acceptance_status"] == "PENDING", "S07 stage must remain pending")
    _require(manifest["s07_p3_entry_allowed"] is (not pre_final), "S07-P3 entry mismatch")
    _require(manifest["s07_p3_started"] is False and manifest["s07_stage_review_started"] is False, "later S07 work started")
    governance = (
        Path("KMFA/docs/governance/project.yaml").read_text(encoding="utf-8")
        + Path("KMFA/metadata/project/project.yaml").read_text(encoding="utf-8")
    )
    for token in (
        'current_phase_id: "V015_S07_P2_CONFLICT_CLASSIFICATION"',
        'current_phase: "V015_S07_P2_CONFLICT_CLASSIFICATION"',
        f'phase_acceptance_status: "{expected}"',
        "stage_execution_percentage: 67",
        "active_formula_count: 342", "active_parameter_count: 1613",
        'current_parameter_range: "PARAM-KMFA-1990..1998"',
        's07_p1_acceptance_status: "PASSED"',
        "s07_p2_started: true", f's07_p2_acceptance_status: "{expected}"',
        f"s07_p3_entry_allowed: {str(not pre_final).lower()}", "s07_p3_started: false",
        "github_upload_performed: false", "app_reinstall_performed: false",
    ):
        _require(token in governance, f"governance token missing: {token}")
    return manifest


def _receipts_and_commit(manifest: dict[str, Any], skip_receipts: bool, skip_clean: bool) -> None:
    if not skip_receipts:
        receipts = builder.final_receipts()
        expected = dict(EXPECTED_VALIDATIONS)
        _require([row["name"] for row in receipts] == list(expected), "receipt identity drift")
        _require(all(row["command"] == expected[row["name"]] for row in receipts), "receipt command drift")
        head = receipts[0]["validation_head"]
        _require(manifest.get("validation_head") == head, "manifest validation head drift")
        _require(_git("rev-parse", "HEAD^") == head, "final evidence commit must immediately follow validation head")
        mutable = set(_git("diff", "--name-only", f"{head}..HEAD").splitlines())
        allowed = {
            str(builder.RECEIPTS_PATH), str(builder.MANIFEST_PATH), str(builder.TASK_MATRIX_PATH),
            str(builder.STATUS_PATH), str(builder.SAME_SOURCE_REPORT_PATH),
            str(builder.CROSS_SOURCE_REPORT_PATH), str(builder.RESPONSIBILITY_REPORT_PATH), str(builder.TEST_PATH),
            "KMFA/CHANGELOG.md", "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md", "KMFA/HANDOFF.md",
            "KMFA/docs/governance/ASSURANCE_STATUS.yaml", "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
            "KMFA/docs/governance/MODEL_SPEC.md", "KMFA/docs/governance/OWNER_STATUS.md",
            "KMFA/docs/governance/STATUS.md", "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
            "KMFA/docs/governance/VERSION_MATRIX.yaml", "KMFA/docs/governance/delivery_tasks.yaml",
            "KMFA/docs/governance/project.yaml", "KMFA/docs/governance/roadmap.yaml",
            "KMFA/metadata/project/project.yaml", "KMFA/docs/governance/development_events.jsonl",
            "KMFA/docs/governance/events.jsonl", "KMFA/metadata/stage_status.jsonl",
        }
        _require(not (mutable - allowed), "post-validation mutation outside allowlist: " + ", ".join(sorted(mutable - allowed)))
    if not skip_clean:
        _require(not _git("status", "--porcelain"), "final validation requires a clean commit")


def validate(
    *, pre_final: bool = False, skip_validation_receipts: bool = False,
    skip_clean_commit: bool = False, dependency_only: bool = False,
    private_only: bool = False, public_only: bool = False, structured_only: bool = False,
) -> None:
    if dependency_only:
        _dependency(); return
    if private_only:
        _private_conflict_boundary(); return
    if public_only:
        _public_boundary(); return
    if structured_only:
        _structured_public_diff(); return
    _scope()
    _dependency()
    _private_conflict_boundary()
    _public_boundary()
    _structured_public_diff()
    manifest = _public_and_governance(pre_final)
    _receipts_and_commit(manifest, skip_validation_receipts, skip_clean_commit)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check KMFA v1.5 S07-P2")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--private-conflict-boundary-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        validate(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
            dependency_only=args.dependency_check,
            private_only=args.private_conflict_boundary_check,
            public_only=args.public_boundary_check,
            structured_only=args.structured_public_diff_check,
        )
    except (
        CheckError, builder.BuildError, kernel.ConflictClassificationError,
        OSError, ValueError, KeyError, json.JSONDecodeError,
    ) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: KMFA v1.5 S07-P2 conflict classification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
