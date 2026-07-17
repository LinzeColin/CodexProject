#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S16 整体复审及正式验收绑定。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s16_stage_review as builder
from KMFA.tools import v015_s16_stage_review_contract as contract


REPO_ROOT = builder.REPO_ROOT
TASKPACK_PATH = Path(
    "/Users/linzezhang/Downloads/"
    "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)

EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_s16_stage_review_contract.py"),
    ("focused_contract_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_stage_review_contract"),
    ("focused_review_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_stage_review"),
    ("focused_browser_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_stage_review_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_stage_review_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_stage_review_governance"),
    ("s16_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_p1_homepage.py --check"),
    ("s16_p2_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_p2_drilldown_explanation.py --check"),
    ("s16_p3_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_p3_homepage_usability.py --check"),
    ("s16_p1_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p1_homepage"),
    ("s16_p2_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p2_drilldown_explanation"),
    ("s16_p3_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p3_homepage_usability"),
    ("s16_p1_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p1_homepage_runtime"),
    ("s16_p2_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p2_drilldown_explanation_runtime"),
    ("s16_p3_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s16_p3_homepage_usability_runtime"),
    ("s16_p1_browser_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p1_browser_tests.py"),
    ("s16_p2_browser_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p2_browser_tests.py"),
    ("s16_p3_browser_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s16_p3_browser_tests.py"),
    ("integrated_review_consistency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_stage_review.py --integrated-review-check"),
    ("builder_exact_rebuild", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s16_stage_review.py --check"),
    ("stage_checker_pre_final", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_stage_review.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S16_STAGE_REVIEW_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_stage_review.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_stage_review.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s16_stage_review.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.REVIEW_BASE_COMMIT}..HEAD"),
)

if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

ALLOWED_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S16_P1_HOMEPAGE_FIRST_SCREEN/",
    "KMFA/stage_artifacts/V015_S16_P2_DRILLDOWN_EXPLANATION/",
    "KMFA/stage_artifacts/V015_S16_P3_HOMEPAGE_USABILITY_ACCEPTANCE/",
    "KMFA/stage_artifacts/V015_S16_STAGE_REVIEW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s16_stage_review.py",
    "KMFA/tests/test_v015_s16_stage_review_artifacts.py",
    "KMFA/tests/test_v015_s16_stage_review_browser.py",
    "KMFA/tests/test_v015_s16_stage_review_contract.py",
    "KMFA/tests/test_v015_s16_stage_review_governance.py",
    "KMFA/tools/build_v015_s16_stage_review.py",
    "KMFA/tools/check_v015_s16_stage_review.py",
    "KMFA/tools/run_v015_s16_p3_homepage_usability.py",
    "KMFA/tools/run_v015_s16_stage_review_browser_tests.py",
    "KMFA/tools/run_v015_s16_stage_review_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s16_stage_review_contract.py",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)
PRESERVED_UNTRACKED_PREFIXES = (
    ".github/workflows/kmfa-dual-plane.yml",
    "KMFA/machine/",
    "KMFA/文档/",
)
FINAL_MUTABLE_PATHS = frozenset(
    {
        "KMFA/AGENTS.md",
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/README.md",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/events.jsonl",
        "KMFA/docs/governance/project.yaml",
        "KMFA/docs/governance/roadmap.yaml",
        "KMFA/metadata/project/project.yaml",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/stage_artifacts/V015_S16_STAGE_REVIEW/human/stage16_review_report_zh.md",
        "KMFA/stage_artifacts/V015_S16_STAGE_REVIEW/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S16_STAGE_REVIEW/machine/s16_stage_review_manifest.json",
        "KMFA/stage_artifacts/V015_S16_STAGE_REVIEW/machine/validation_results.jsonl",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    }
)


class CheckError(RuntimeError):
    pass


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _preserved(path: str) -> bool:
    return any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in PRESERVED_UNTRACKED_PREFIXES
    )


def _allowed(path: str) -> bool:
    return any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in ALLOWED_PREFIXES
    )


def _check_scope() -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.REVIEW_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode:
        raise CheckError("S16 review base is not an ancestor of HEAD")
    changed: set[str] = set()
    for args in (
        ("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.REVIEW_BASE_COMMIT}..HEAD"),
        ("-c", "core.quotepath=false", "diff", "--name-only"),
        ("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        ("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ):
        changed.update(row for row in _git(*args).splitlines() if row and not _preserved(row))
    unexpected = sorted(path for path in changed if not _allowed(path))
    if unexpected:
        raise CheckError("out-of-scope path: " + ", ".join(unexpected))


def _check_taskpack_source() -> None:
    if not TASKPACK_PATH.is_file():
        raise CheckError("TaskPack source ZIP is unavailable")
    digest = hashlib.sha256(TASKPACK_PATH.read_bytes()).hexdigest()
    if digest != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack source SHA-256 mismatch")
    source = builder.source_contract()
    if (
        source.get("stage_id") != "S16"
        or source.get("phase_ids") != ["S16-P1", "S16-P2", "S16-P3"]
        or source.get("source_integrity_status") != "PASS"
    ):
        raise CheckError("tracked S16 source contract drift")


def _check_public_boundary() -> None:
    forbidden = (
        "/Users/linzezhang/Downloads/KMFA_MetaData",
        "private_raw_source_index",
        "应收账龄表2025_private_copy",
        "生产项目状态表_private_copy",
    )
    roots = (builder.OUTPUT_ROOT, builder.PROJECT_ROOT / "tools/v015_s16_stage_review_contract.py")
    for root in roots:
        paths = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
        for path in paths:
            if path.suffix.casefold() == ".png":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            matches = [token for token in forbidden if token in text]
            if matches:
                raise CheckError(f"private/raw token in public output: {path}: {matches}")


def _check_clean_governance_sync() -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(".github/workflows/kmfa-dual-plane.yml\nKMFA/machine/\nKMFA/文档/\n")
        exclude_path = handle.name
    try:
        env = dict(os.environ)
        env.update(
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.excludesFile",
                "GIT_CONFIG_VALUE_0": exclude_path,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": ".",
            }
        )
        result = subprocess.run(
            [
                "python3",
                "-B",
                "scripts/validate_governance_sync.py",
                "--changed-only",
                "--base-ref",
                builder.REVIEW_BASE_COMMIT,
                "--enforce-sync",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise CheckError((result.stdout + result.stderr).strip())
    finally:
        Path(exclude_path).unlink(missing_ok=True)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        raise CheckError(f"invalid PNG: {path.name}")
    return struct.unpack(">II", data[16:24])


def _check_integrated_review() -> None:
    evidence = _json(builder.PHASE_EVIDENCE_PATH)
    if evidence.get("accounting") != {
        "phase_count": 3,
        "phase_passed_count": 3,
        "task_count": 9,
        "task_accepted_count": 9,
        "predecessor_public_check_count": 183,
        "predecessor_receipt_count": 60,
    }:
        raise CheckError("predecessor accounting drift")
    cross = _json(builder.CROSS_PHASE_CONTRACTS_PATH)
    if cross.get("accounting") != {
        "total": 45,
        "passed": 45,
        "failed": 0,
        "blocking_failed": 0,
    }:
        raise CheckError("cross-phase accounting drift")
    verification = _json(builder.CROSS_PHASE_VERIFICATION_PATH)
    if verification.get("accounting") != {"total": 240, "passed": 240, "failed": 0}:
        raise CheckError("public verification accounting drift")
    summary = contract.validate_integrated_review(_json(builder.INTEGRATED_REVIEW_PATH))
    if summary["technical_audit_score"] != 19 or summary["open_review_finding_count"] != 0:
        raise CheckError("integrated review closure drift")
    findings = _csv(builder.FINDINGS_PATH)
    if [row.get("finding_id") for row in findings] != [
        "S16REV-F001",
        "S16REV-F002",
        "S16REV-F003",
    ] or any(row.get("status") != "FIXED_VALIDATED" for row in findings):
        raise CheckError("review finding closure drift")
    expected_screenshots = (
        (builder.DESKTOP_SCREENSHOT_PATH, 1440, 1000),
        (builder.DRILLDOWN_SCREENSHOT_PATH, 1440, 1000),
        (builder.FAULT_SCREENSHOT_PATH, 1440, 1000),
        (builder.TABLET_SCREENSHOT_PATH, 820, 1180),
        (builder.MOBILE_SCREENSHOT_PATH, 390, 844),
    )
    for path, width, minimum_height in expected_screenshots:
        actual_width, actual_height = _png_dimensions(path)
        if actual_width != width or actual_height < minimum_height:
            raise CheckError(f"browser screenshot size drift: {path.name}")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    value = _json(builder.MANIFEST_PATH)
    required = {
        "run_phase_id": builder.RUN_PHASE_ID,
        "counted_as_taskpack_phase": False,
        "counted_as_taskpack_task": False,
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "stage_lifecycle_status": "IN_PROGRESS" if pre_final else "COMPLETED",
        "stage_acceptance_status": "PENDING" if pre_final else "PASSED",
        "decision": "REMAIN_IN_S16_STAGE_REVIEW" if pre_final else "GO_TO_S17_P1_ONLY",
        "overall_accepted_phase_count": 46,
        "overall_taskpack_phase_count": 72,
        "s16_stage_review_started": True,
        "s16_stage_review_performed": not pre_final,
        "s17_entry_allowed": not pre_final,
        "s17_p1_entry_allowed": not pre_final,
        "s17_p1_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    for key, expected in required.items():
        if value.get(key) != expected:
            raise CheckError(f"manifest drift: {key}={value.get(key)!r}, expected {expected!r}")
    return value


def _check_receipts(manifest: dict[str, Any]) -> None:
    rows = [
        json.loads(line)
        for line in builder.VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != builder.EXPECTED_VALIDATION_COUNT:
        raise CheckError("formal validation receipt count drift")
    if [row.get("name") for row in rows] != list(builder.EXPECTED_VALIDATION_NAMES):
        raise CheckError("formal validation receipt order drift")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise CheckError("formal validation receipt failure")
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    if run_ids != {manifest.get("validation_run_id")} or heads != {manifest.get("validation_head")}:
        raise CheckError("formal validation receipt binding drift")
    validation_head = str(manifest["validation_head"])
    if _git("rev-list", "--count", f"{validation_head}..HEAD") != "1":
        raise CheckError("final acceptance commit must immediately follow validation head")
    final_changed = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{validation_head}..HEAD").splitlines())
    unexpected = sorted(final_changed - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("unexpected post-validation path: " + ", ".join(unexpected))


def run_checks(
    *,
    pre_final: bool,
    skip_validation_receipts: bool,
    skip_clean_commit: bool,
) -> None:
    _check_scope()
    _check_taskpack_source()
    _check_public_boundary()
    _check_integrated_review()
    mismatches = builder.check_outputs()
    if mismatches:
        raise CheckError("deterministic output drift: " + ", ".join(mismatches))
    manifest = _check_manifest(pre_final=pre_final)
    if not skip_validation_receipts and not pre_final:
        _check_receipts(manifest)
    if not skip_clean_commit and _git("status", "--porcelain", "--untracked-files=no"):
        raise CheckError("tracked worktree is not clean")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 KMFA v1.5 S16 整体复审")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--integrated-review-check", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.integrated_review_check:
            _check_integrated_review()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        else:
            run_checks(
                pre_final=args.pre_final,
                skip_validation_receipts=args.skip_validation_receipts,
                skip_clean_commit=args.skip_clean_commit,
            )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S16 整体复审检查")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
