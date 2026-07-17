#!/usr/bin/env python3
"""Strict pre-final/final checker for KMFA v1.5 S06-P2."""

from __future__ import annotations

import argparse
import json
import stat
import subprocess
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import build_v015_s06_p2_golden_baseline_lock as builder
from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel
from KMFA.tools import v015_s06_p2_signoff_review as review


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_BASE = "fd32ecdc7b8144c8d80e4099918e3545d7dd3b16"
EXPECTED_VALIDATIONS = (
    (builder.EXPECTED_VALIDATION_NAMES[0], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_authorized_resolution"),
    (builder.EXPECTED_VALIDATION_NAMES[1], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_golden_baseline_lock"),
    (builder.EXPECTED_VALIDATION_NAMES[2], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_signoff_review"),
    (builder.EXPECTED_VALIDATION_NAMES[3], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. $HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B KMFA/tests/playwright_v015_s06_p2_signoff_review.py --self-host"),
    (builder.EXPECTED_VALIDATION_NAMES[4], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_golden_baseline_lock_governance"),
    (builder.EXPECTED_VALIDATION_NAMES[5], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    (builder.EXPECTED_VALIDATION_NAMES[6], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s06_p1_authoritative_source_registration.py --check"),
    (builder.EXPECTED_VALIDATION_NAMES[7], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    (builder.EXPECTED_VALIDATION_NAMES[8], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    (builder.EXPECTED_VALIDATION_NAMES[9], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    (builder.EXPECTED_VALIDATION_NAMES[10], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    (builder.EXPECTED_VALIDATION_NAMES[11], f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {PHASE_BASE} --enforce-sync"),
    (builder.EXPECTED_VALIDATION_NAMES[12], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    (builder.EXPECTED_VALIDATION_NAMES[13], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    (builder.EXPECTED_VALIDATION_NAMES[14], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py --raw-invariant-check"),
    (builder.EXPECTED_VALIDATION_NAMES[15], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py --private-boundary-check"),
    (builder.EXPECTED_VALIDATION_NAMES[16], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py --check"),
    (builder.EXPECTED_VALIDATION_NAMES[17], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m py_compile KMFA/tools/v015_s06_p2_golden_baseline_lock.py KMFA/tools/v015_s06_p2_authorized_resolution.py KMFA/tools/build_v015_s06_p2_golden_baseline_lock.py KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py KMFA/tools/run_v015_s06_p2_validations.py"),
    (builder.EXPECTED_VALIDATION_NAMES[18], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s06_p2_authorized_resolution KMFA.tests.test_v015_s06_p2_golden_baseline_lock KMFA.tests.test_v015_s06_p2_signoff_review KMFA.tests.test_v015_s06_p2_golden_baseline_lock_governance"),
    (builder.EXPECTED_VALIDATION_NAMES[19], "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s06_p2_golden_baseline_lock.py --structured-public-diff-check"),
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


def _private_boundary() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    required = (
        kernel.PRIVATE_PACKET_PATH, kernel.PRIVATE_SIGNOFF_TEMPLATE_PATH, kernel.PRIVATE_REVIEW_PATH,
        kernel.PRIVATE_AUTHORIZATION_PATH, kernel.PRIVATE_SIGNOFF_PATH, kernel.PRIVATE_VERSION_LEDGER_PATH,
    )
    _require(stat.S_IMODE(kernel.PRIVATE_OUTPUT_DIR.stat().st_mode) == 0o700, "private directory must be 0700")
    for path in required:
        _require(path.is_file(), f"private evidence missing: {path.name}")
        _require(stat.S_IMODE(path.stat().st_mode) == 0o600, f"private file must be 0600: {path.name}")
        ignored = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=REPO_ROOT, check=False)
        _require(ignored.returncode == 0, f"private file is not ignored: {path.name}")
    packet = _json(kernel.PRIVATE_PACKET_PATH)
    signoff = _json(kernel.PRIVATE_SIGNOFF_PATH)
    authorization = _json(kernel.PRIVATE_AUTHORIZATION_PATH)
    kernel.validate_candidate_packet(packet)
    kernel.validate_authorization_record(authorization)
    accepted = kernel.validate_signoff(signoff, packet)
    summaries = kernel.build_project_summaries(accepted)
    ledger = kernel._read_ledger()
    _require(len(packet["candidate_records"]) == 157, "candidate count mismatch")
    _require(len(accepted) == 92, "accepted field count mismatch")
    _require(sum(row["decision"] == "REJECT" for row in signoff["decision_rows"]) == 65, "rejected count mismatch")
    _require(len(summaries) == 8, "project summary count mismatch")
    _require(all(row["money_difference_cents"] == 0 for row in summaries), "non-zero project difference")
    _require(len(ledger) == 1 and ledger[0]["locked"] is True, "first golden version is not locked")
    _require(ledger[0]["project_count"] == 8 and ledger[0]["accepted_field_count"] == 92, "golden version aggregate mismatch")
    review.validate_draft(_json(kernel.PRIVATE_SIGNOFF_TEMPLATE_PATH), packet)
    return packet, signoff, ledger


def _raw_invariants() -> None:
    p1 = _json(kernel.P1_MANIFEST_PATH)
    before = kernel._raw_invariants(p1)
    after = kernel._raw_invariants(p1)
    _require(before == after, "raw invariant check drifted")
    _require(before == {
        "raw_root_stat_unchanged": True, "package_stat_unchanged": True,
        "raw_mutation_performed": False,
    }, "raw source invariant failed")


def _structured_public_diff(packet: dict[str, Any], signoff: dict[str, Any]) -> None:
    tracked = _git("diff", "--name-only", PHASE_BASE, "--", "KMFA")
    _require(".codex_private_runtime" not in tracked, "private runtime entered tracked diff")
    paths = [REPO_ROOT / line for line in tracked.splitlines() if line and (REPO_ROOT / line).is_file()]
    rendered = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in paths
        if path.suffix.lower() in {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".py"}
    )
    authorization = _json(kernel.PRIVATE_AUTHORIZATION_PATH)
    _require(authorization["user_message"] not in rendered, "private authorization text leaked to tracked diff")
    _require(signoff["confirmer"]["basis"] not in rendered, "private authorization binding leaked")
    private_tokens = {
        str(row.get("raw_text") or "").strip() for row in packet["candidate_records"]
        if len(str(row.get("raw_text") or "").strip()) >= 24
    }
    _require(not any(token in rendered for token in private_tokens), "private candidate text leaked to tracked diff")
    public = json.dumps({
        "contract": _json(builder.CONTRACT_PATH), "manifest": _json(builder.MANIFEST_PATH),
        "matrix": _json(builder.TASK_MATRIX_PATH),
    }, ensure_ascii=False)
    for forbidden in ("source_locator", "confirmer_identity", "user_message", "project_summaries", "canonical_value"):
        _require(f'"{forbidden}":' not in public, f"public machine evidence contains private field: {forbidden}")


def _public_and_governance(pre_final: bool) -> None:
    builder.check_outputs()
    projection = kernel.current_public_projection()
    _require(projection["phase_acceptance_status"] == "PENDING_FINAL_VALIDATION", "lock projection mismatch")
    _require(projection["accepted_field_count"] == 92, "projection accepted count mismatch")
    _require(projection["project_summary_count"] == 8, "projection summary count mismatch")
    _require(projection["golden_version_count"] == 1, "projection version count mismatch")
    manifest = _json(builder.MANIFEST_PATH)
    matrix = _json(builder.TASK_MATRIX_PATH)
    expected = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    _require(manifest["phase_acceptance_status"] == expected, "manifest acceptance mismatch")
    _require(manifest["task_accepted_count"] == (0 if pre_final else 3), "task acceptance mismatch")
    _require(manifest["validation_receipt_count"] == (0 if pre_final else 20), "receipt count mismatch")
    _require(manifest["s06_p3_entry_allowed"] is (not pre_final), "S06-P3 entry mismatch")
    _require(manifest["s06_p3_started"] is False, "S06-P3 must not start in S06-P2 run")
    _require(matrix["task_execution_complete_count"] == 3, "task execution count mismatch")
    _require(matrix["task_accepted_count"] == (0 if pre_final else 3), "task matrix acceptance mismatch")
    governance = (Path("KMFA/docs/governance/project.yaml").read_text(encoding="utf-8") +
                  Path("KMFA/metadata/project/project.yaml").read_text(encoding="utf-8") +
                  Path("KMFA/docs/governance/roadmap.yaml").read_text(encoding="utf-8"))
    for token in (
        f'phase_acceptance_status: "{expected}"', "s06_p2_accepted_field_count: 92",
        "s06_p2_rejected_candidate_count: 65", "s06_p2_project_summary_count: 8",
        "s06_p2_golden_version_count: 1", "s06_p2_human_signoff_valid: true",
        f"s06_p2_validation_receipt_count: {0 if pre_final else 20}",
        f"s06_p3_entry_allowed: {str(not pre_final).lower()}", "s06_p3_started: false",
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
    skip_clean_commit: bool = False, structured_public_diff_only: bool = False,
    raw_invariant_only: bool = False, private_boundary_only: bool = False,
) -> None:
    if raw_invariant_only:
        _raw_invariants()
        return
    packet, signoff, _ = _private_boundary()
    if private_boundary_only:
        return
    if structured_public_diff_only:
        _structured_public_diff(packet, signoff)
        return
    _raw_invariants()
    _structured_public_diff(packet, signoff)
    _public_and_governance(pre_final)
    _receipts_and_commit(skip_validation_receipts, skip_clean_commit)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check KMFA v1.5 S06-P2")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--raw-invariant-check", action="store_true")
    parser.add_argument("--private-boundary-check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        validate(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
            structured_public_diff_only=args.structured_public_diff_check,
            raw_invariant_only=args.raw_invariant_check,
            private_boundary_only=args.private_boundary_check,
        )
    except (CheckError, kernel.GoldenBaselineError, builder.BuildError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: KMFA v1.5 S06-P2 golden baseline lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
