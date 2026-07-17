#!/usr/bin/env python3
"""严格检查 KMFA v1.5 S22 整体复审及正式验收绑定。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s22_stage_review as builder
from KMFA.tools import v015_s22_stage_review_contract as contract


REPO_ROOT = builder.REPO_ROOT
TASKPACK_PATH = Path("/Users/linzezhang/Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip")
EXPECTED_VALIDATIONS = (
    ("phase_contract", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_s22_stage_review_contract.py"),
    ("focused_contract_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_stage_review_contract"),
    ("focused_review_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_stage_review"),
    ("focused_browser_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_stage_review_browser_tests.py"),
    ("focused_artifact_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_stage_review_artifacts"),
    ("focused_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_stage_review_governance"),
    ("s22_p1_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_s22_p1_notifications.py"),
    ("s22_p2_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_s22_p2_security_audit.py"),
    ("s22_p3_dependency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_s22_p3_operations_governance.py"),
    ("s22_p1_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p1_notifications"),
    ("s22_p2_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit"),
    ("s22_p3_kernel_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p3_operations_governance"),
    ("s22_p1_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p1_notifications_runtime"),
    ("s22_p2_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p2_security_audit_runtime"),
    ("s22_p3_runtime_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s22_p3_operations_governance_runtime"),
    ("s22_p1_browser_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_p1_browser_tests.py"),
    ("s22_p2_browser_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_p2_browser_tests.py"),
    ("s22_p3_browser_regression", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/run_v015_s22_p3_browser_tests.py"),
    ("integrated_review_consistency", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_stage_review.py --integrated-review-check"),
    ("builder_exact_rebuild", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s22_stage_review.py --check"),
    ("stage_checker_pre_final", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_stage_review.py --pre-final --skip-validation-receipts --skip-clean-commit"),
    ("roadmap_governance_tests", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync"),
    ("roadmap_sync_pending", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S22_STAGE_REVIEW_PENDING_FINAL_VALIDATION"),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    ("project_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required"),
    ("lean_governance", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required"),
    ("governance_sync", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_stage_review.py --clean-governance-sync-check"),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    ("taskpack_source", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_stage_review.py --taskpack-source-check"),
    ("public_boundary", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s22_stage_review.py --public-boundary-check"),
    ("git_diff_check", f"git diff --check {builder.REVIEW_BASE_COMMIT}..HEAD"),
)
if tuple(name for name, _ in EXPECTED_VALIDATIONS) != builder.EXPECTED_VALIDATION_NAMES:
    raise RuntimeError("builder/checker validation name drift")

PRESERVED_UNTRACKED_PREFIXES = (".github/workflows/kmfa-dual-plane.yml", "KMFA/machine/", "KMFA/文档/")
ALLOWED_PREFIXES = (
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/stage_artifacts/V015_S22_STAGE_REVIEW/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s22_stage_review.py", "KMFA/tests/test_v015_s22_stage_review_artifacts.py",
    "KMFA/tests/test_v015_s22_stage_review_browser.py", "KMFA/tests/test_v015_s22_stage_review_contract.py",
    "KMFA/tests/test_v015_s22_stage_review_governance.py",
    "KMFA/tests/test_v015_s22_p2_security_audit_runtime.py",
    "KMFA/tools/build_v015_s22_stage_review.py", "KMFA/tools/check_v015_s22_stage_review.py",
    "KMFA/tools/run_v015_s22_p1_notifications.py", "KMFA/tools/run_v015_s22_p2_security_audit.py",
    "KMFA/tools/run_v015_s22_p3_operations_governance.py", "KMFA/tools/run_v015_s22_stage_review_browser_tests.py",
    "KMFA/tools/run_v015_s22_stage_review_validations.py", "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s22_p3_operations_governance.py", "KMFA/tools/v015_s22_stage_review_contract.py",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
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


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _preserved(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in PRESERVED_UNTRACKED_PREFIXES)


def _allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", builder.REVIEW_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S22 review base is not an ancestor of HEAD")
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
    if hashlib.sha256(TASKPACK_PATH.read_bytes()).hexdigest() != builder.TASKPACK_SHA256:
        raise CheckError("TaskPack source SHA-256 mismatch")
    source = builder.source_contract()
    if source.get("stage_id") != "S22" or source.get("phase_ids") != ["S22-P1", "S22-P2", "S22-P3"] or source.get("source_integrity_status") != "PASS":
        raise CheckError("tracked S22 source contract drift")


def _check_public_boundary() -> None:
    forbidden = ("/Users/linzezhang/Downloads/KMFA_MetaData", "private_raw_source_index", "应收账龄表2025_private_copy", "生产项目状态表_private_copy")
    roots = (builder.OUTPUT_ROOT, REPO_ROOT / "KMFA/tools/v015_s22_stage_review_contract.py")
    for root in roots:
        paths = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
        for path in paths:
            if path.suffix.casefold() == ".png":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            matches = [token for token in forbidden if token in text]
            if matches:
                raise CheckError(f"private/raw token in public output: {path}: {matches}")


def _png_dimensions(path: Path) -> tuple[int, int]:
    body = path.read_bytes()
    if len(body) < 24 or body[:8] != b"\x89PNG\r\n\x1a\n":
        raise CheckError(f"invalid PNG: {path}")
    return struct.unpack(">II", body[16:24])


def _check_evidence(*, require_receipts: bool) -> None:
    state = "PASSED" if require_receipts else "PENDING"
    manifest = _json(builder.MANIFEST_PATH)
    if require_receipts and manifest.get("stage_acceptance_status") != "PASSED":
        raise CheckError("S22 stage review is not passed")
    if not require_receipts and manifest.get("stage_acceptance_status") not in {"PENDING", "PASSED"}:
        raise CheckError("S22 stage review pending manifest is invalid")
    phase = _json(builder.PHASE_EVIDENCE_PATH)
    integrated = _json(builder.INTEGRATED_REVIEW_PATH)
    verification = _json(builder.CROSS_PHASE_VERIFICATION_PATH)
    audit = _json(builder.TECHNICAL_AUDIT_PATH)
    findings = _csv(builder.FINDINGS_PATH)
    risks = _csv(builder.RISKS_PATH)
    if phase.get("accounting") != {
        "phase_count": 3, "phase_passed_count": 3, "task_count": 9, "task_accepted_count": 9,
        "predecessor_public_check_count": 187, "predecessor_receipt_count": 60,
    }:
        raise CheckError("predecessor phase evidence drift")
    if integrated.get("integration_binding_count") != 48 or integrated.get("integration_binding_failed_count") != 0 or not integrated.get("stage_acceptance_ready"):
        raise CheckError("integrated review failed")
    if verification.get("public_check_count") != 48 or verification.get("public_check_failed_count") != 0:
        raise CheckError("cross-phase verification drift")
    if audit.get("total_score") != 20 or audit.get("open_issue_count") != 0:
        raise CheckError("technical audit drift")
    if len(findings) != 4 or any(row.get("status") != "FIXED_VALIDATED" or row.get("blocks_stage_acceptance") != "false" for row in findings):
        raise CheckError("review findings not closed")
    if risks:
        raise CheckError("open risk register is not empty")
    for path in builder.SCREENSHOT_PATHS:
        width, height = _png_dimensions(path)
        if width < 390 or height < 500:
            raise CheckError(f"screenshot too small: {path}")
    if state == "PENDING" and manifest.get("s23_entry_allowed"):
        raise CheckError("S23 opened before formal validation")
    if manifest.get("s23_p1_started") or manifest.get("github_upload_performed") or manifest.get("app_reinstall_performed"):
        raise CheckError("out-of-scope lifecycle action recorded")
    if require_receipts:
        rows = _jsonl(builder.VALIDATION_RESULTS_PATH)
        if len(rows) != builder.EXPECTED_VALIDATION_COUNT or [row.get("name") for row in rows] != list(builder.EXPECTED_VALIDATION_NAMES):
            raise CheckError("formal validation receipt count or order drift")
        if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
            raise CheckError("formal validation receipt failed")
        if {row.get("validation_run_id") for row in rows} != {manifest.get("validation_run_id")} or {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
            raise CheckError("formal validation binding drift")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _check_clean_commit() -> None:
    dirty = []
    for line in _git("-c", "core.quotepath=false", "status", "--porcelain").splitlines():
        path = line[3:].split(" -> ")[-1]
        if not _preserved(path):
            dirty.append(line)
    if dirty:
        raise CheckError("tracked acceptance commit is not clean: " + " | ".join(dirty))


def _check_clean_governance_sync() -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(".github/workflows/kmfa-dual-plane.yml\nKMFA/machine/\nKMFA/文档/\n")
        exclude_path = handle.name
    try:
        env = dict(os.environ)
        env.update({
            "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.excludesFile", "GIT_CONFIG_VALUE_0": exclude_path,
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".",
        })
        result = subprocess.run(
            [sys.executable, "-B", "scripts/validate_governance_sync.py", "--changed-only", "--base-ref", builder.REVIEW_BASE_COMMIT, "--enforce-sync"],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise CheckError(result.stdout.strip() or result.stderr.strip() or "governance sync failed")
    finally:
        Path(exclude_path).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--integrated-review-check", action="store_true")
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    parser.add_argument("--clean-governance-sync-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.taskpack_source_check:
            _check_taskpack_source()
        elif args.public_boundary_check:
            _check_public_boundary()
        elif args.clean_governance_sync_check:
            _check_clean_governance_sync()
        elif args.integrated_review_check:
            payload = contract.integrated_review()
            if not payload["stage_acceptance_ready"] or payload["integration_binding_failed_count"]:
                raise CheckError("integrated review failed")
        else:
            _check_scope()
            _check_taskpack_source()
            _check_public_boundary()
            _check_evidence(require_receipts=not args.skip_validation_receipts and not args.pre_final)
            if not args.skip_clean_commit and not args.pre_final:
                _check_clean_commit()
        print(json.dumps({"status": "PASS", "run_phase_id": contract.RUN_PHASE_ID}, ensure_ascii=False))
        return 0
    except (CheckError, contract.StageReviewError, builder.BuildError, OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
