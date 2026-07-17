#!/usr/bin/env python3
"""Strict checker for KMFA v1.5 S04-P1 data-catalog evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s04_p1_data_catalog as builder
from KMFA.tools import v015_s04_p1_data_catalog as catalog


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_BASE_COMMIT = "a717483360f4eea01dd9c9b94cf318285a5a6d12"

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s04_p1_data_catalog.py','KMFA/tools/build_v015_s04_p1_data_catalog.py','KMFA/tools/check_v015_s04_p1_data_catalog.py','KMFA/tools/run_v015_s04_p1_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "data_catalog_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s04_p1_data_catalog",
    ),
    (
        "data_catalog_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s04_p1_data_catalog_governance",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "source_lineage_regression_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_v014_s02_p1_metadata_protocol KMFA.tests.test_v015_s02_p2_lineage_contract",
    ),
    (
        "builder_exact_rebuild",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s04_p1_data_catalog.py --check",
    ),
    (
        "phase_checker_pre_final",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s04_p1_data_catalog.py --pre-final --skip-validation-receipts --skip-clean-commit",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state PENDING_FINAL_VALIDATION",
    ),
    (
        "metadata_protocol",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py",
    ),
    (
        "project_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required",
    ),
    (
        "lean_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required",
    ),
    (
        "no_float_money",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    ),
    (
        "no_omission",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    ),
    ("git_diff_check", f"git diff --check {PHASE_BASE_COMMIT}..HEAD"),
)

ALLOWED_PHASE_PREFIXES = (
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/metadata/catalog/",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S04_P1_DATA_CATALOG/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s04_p1_data_catalog.py",
    "KMFA/tests/test_v015_s04_p1_data_catalog_governance.py",
    "KMFA/tests/test_v015_s04_p1_validation_runner.py",
    "KMFA/tools/build_v015_s04_p1_data_catalog.py",
    "KMFA/tools/check_v015_s04_p1_data_catalog.py",
    "KMFA/tools/run_v015_s04_p1_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s04_p1_data_catalog.py",
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
        "KMFA/docs/governance/events.jsonl",
        "KMFA/docs/governance/project.yaml",
        "KMFA/docs/governance/roadmap.yaml",
        "KMFA/metadata/project/project.yaml",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/stage_artifacts/V015_S04_P1_DATA_CATALOG/human/completion_record_zh.md",
        "KMFA/stage_artifacts/V015_S04_P1_DATA_CATALOG/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S04_P1_DATA_CATALOG/machine/s04_p1_data_catalog_manifest.json",
        "KMFA/stage_artifacts/V015_S04_P1_DATA_CATALOG/machine/validation_results.jsonl",
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


def _is_allowed_phase_path(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"invalid JSON: {path.relative_to(REPO_ROOT)}") from error
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path.relative_to(REPO_ROOT)}")
    return value


def _read_receipts() -> list[dict[str, Any]]:
    try:
        lines = builder.VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError("invalid validation_results.jsonl") from error
    if not all(isinstance(row, dict) for row in rows):
        raise CheckError("validation receipts must be JSON objects")
    return rows


def _check_public_artifacts() -> None:
    paths = list((builder.PROJECT_ROOT / "metadata/catalog").glob("v015_s04_p1_*.json"))
    paths.extend(
        path
        for path in builder.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path != builder.VALIDATION_RESULTS_PATH
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    if re.search(r"(?:/Users/|/Volumes/|/home/|file://)", combined):
        raise CheckError("public artifact contains an absolute local path")
    if re.search(r"sha256:[a-f0-9]{64}", combined):
        raise CheckError("public artifact contains a private-style digest value")
    if any(token in combined for token in (".xlsx", ".xls", ".zip")):
        raise CheckError("public artifact contains a source filename-like token")


def _check_scope() -> None:
    try:
        _git("merge-base", "--is-ancestor", PHASE_BASE_COMMIT, "HEAD")
    except CheckError as error:
        raise CheckError("phase base is not an ancestor of HEAD") from error
    changed = [
        line
        for line in _git(
            "-c", "core.quotepath=false", "diff", "--name-only", f"{PHASE_BASE_COMMIT}..HEAD"
        ).splitlines()
        if line
    ]
    unexpected = [path for path in changed if not _is_allowed_phase_path(path)]
    if unexpected:
        raise CheckError("unexpected phase path(s): " + ", ".join(unexpected))


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _read_json(builder.MANIFEST_PATH)
    expected_status = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    expected_decision = "REMAIN_IN_S04_P1" if pre_final else "CONTINUE_TO_S04_P2_ONLY"
    required = {
        "phase_id": catalog.RUN_PHASE_ID,
        "task_id": catalog.TASK_ID,
        "acceptance_id": catalog.ACCEPTANCE_ID,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": expected_status,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "catalog_record_count": 21,
        "source_system_count": 7,
        "catalog_hierarchy_level_count": 9,
        "source_status_count": 5,
        "required_import_field_count": 6,
        "raw_root_access_count": 0,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "decision": expected_decision,
        "s04_p2_entry_allowed": not pre_final,
        "s04_p2_started": False,
        "s04_p3_entry_allowed": False,
        "s04_stage_review_entry_allowed": False,
    }
    mismatched = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatched:
        raise CheckError("manifest mismatch: " + ", ".join(mismatched))
    return manifest


def _check_receipts(manifest: dict[str, Any]) -> None:
    receipts = _read_receipts()
    expected = dict(EXPECTED_VALIDATIONS)
    if len(receipts) != len(expected):
        raise CheckError(f"validation receipt count mismatch: {len(receipts)} != {len(expected)}")
    if [row.get("name") for row in receipts] != list(expected):
        raise CheckError("validation receipt names/order mismatch")
    run_ids = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    if len(run_ids) != 1 or None in run_ids or len(heads) != 1 or None in heads:
        raise CheckError("validation receipts must share one run id and head")
    for row in receipts:
        name = str(row.get("name"))
        if row.get("command") != expected[name]:
            raise CheckError(f"validation command mismatch: {name}")
        if row.get("status") != "PASS" or row.get("exit_code") != 0:
            raise CheckError(f"validation did not pass: {name}")
        digest = str(row.get("output_sha256") or "")
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
            raise CheckError(f"invalid output digest: {name}")
        if not row.get("started_at") or not row.get("ended_at"):
            raise CheckError(f"validation timestamps missing: {name}")
    validation_head = next(iter(heads))
    validation_run_id = next(iter(run_ids))
    if manifest.get("validation_head") != validation_head:
        raise CheckError("manifest validation_head mismatch")
    if manifest.get("validation_run_id") != validation_run_id:
        raise CheckError("manifest validation_run_id mismatch")
    if manifest.get("validation_receipt_count") != len(receipts):
        raise CheckError("manifest receipt count mismatch")
    if _git("rev-parse", "HEAD^") != validation_head:
        raise CheckError("final evidence commit must be the immediate child of validation_head")
    mutable = set(
        _git(
            "-c", "core.quotepath=false", "diff", "--name-only", f"{validation_head}..HEAD"
        ).splitlines()
    )
    unexpected = sorted(mutable - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("post-validation mutation outside final allowlist: " + ", ".join(unexpected))


def run(*, pre_final: bool, skip_validation_receipts: bool, skip_clean_commit: bool) -> None:
    mismatches = builder.check_outputs()
    if mismatches:
        raise CheckError("deterministic artifact drift: " + ", ".join(mismatches))
    _check_public_artifacts()
    _check_scope()
    manifest = _check_manifest(pre_final=pre_final)
    if not skip_validation_receipts:
        if pre_final:
            raise CheckError("pre-final mode cannot require final validation receipts")
        _check_receipts(manifest)
    if not skip_clean_commit and _git("status", "--porcelain"):
        raise CheckError("worktree must be clean")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-clean-commit", action="store_true")
    args = parser.parse_args()
    try:
        run(
            pre_final=args.pre_final,
            skip_validation_receipts=args.skip_validation_receipts,
            skip_clean_commit=args.skip_clean_commit,
        )
    except (OSError, ValueError, CheckError, catalog.DataCatalogError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: KMFA v1.5 S04-P1 data catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
