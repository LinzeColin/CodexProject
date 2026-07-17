#!/usr/bin/env python3
"""Strict receipt-bound checker for KMFA v1.5 S09-P3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import build_v015_s09_p3_human_readable_audit as builder
from KMFA.tools import v015_s09_p3_human_readable_audit as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VALIDATIONS = (
    (
        "python_compile",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('KMFA/tools/v015_s09_p3_human_readable_audit.py','KMFA/tools/build_v015_s09_p3_human_readable_audit.py','KMFA/tools/check_v015_s09_p3_human_readable_audit.py','KMFA/tools/run_v015_s09_p3_validations.py','KMFA/tools/v015_roadmap_governance_sync.py')]\"",
    ),
    (
        "focused_kernel_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p3_human_readable_audit",
    ),
    (
        "focused_artifact_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p3_human_readable_audit_artifacts",
    ),
    (
        "focused_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p3_human_readable_audit_governance",
    ),
    (
        "s09_predecessor_regression",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_s09_p1_scope_rule_modeling KMFA.tests.test_v015_s09_p1_scope_rule_modeling_artifacts KMFA.tests.test_v015_s09_p2_conversion_reconciliation_engine KMFA.tests.test_v015_s09_p2_conversion_reconciliation_engine_artifacts",
    ),
    (
        "deterministic_evidence",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/build_v015_s09_p3_human_readable_audit.py --check",
    ),
    (
        "pre_final_phase_checker",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p3_human_readable_audit.py --pre-final --skip-validation-receipts",
    ),
    (
        "s09_p2_dependency",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p3_human_readable_audit.py --dependency-check",
    ),
    (
        "roadmap_governance_tests",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest KMFA.tests.test_v015_roadmap_governance_sync",
    ),
    (
        "roadmap_sync_pending",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/v015_roadmap_governance_sync.py --check --validation-state S09_P3_PENDING_FINAL_VALIDATION",
    ),
    ("metadata_protocol", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/metadata_protocol_check.py"),
    (
        "project_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_project_governance.py --project KMFA --mode required",
    ),
    (
        "lean_governance",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/lean_governance.py validate --project KMFA --mode required",
    ),
    (
        "governance_sync",
        f"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B scripts/validate_governance_sync.py --changed-only --base-ref {builder.PHASE_BASE_COMMIT} --enforce-sync",
    ),
    ("no_float_money", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py"),
    ("no_omission", "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py"),
    (
        "taskpack_source",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p3_human_readable_audit.py --taskpack-source-check",
    ),
    (
        "business_display_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p3_human_readable_audit.py --business-display-boundary-check",
    ),
    (
        "public_boundary",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_v015_s09_p3_human_readable_audit.py --public-boundary-check",
    ),
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
    "KMFA/metadata/protocol/v015_s09_p3_difference_closure_protocol_public_safe.json",
    "KMFA/metadata/protocol/v015_s09_p3_human_rule_manual_public_safe.json",
    "KMFA/metadata/quality/v015_s09_p3_report_difference_display_spec_public_safe.json",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s09_p3_human_readable_audit.py",
    "KMFA/tests/test_v015_s09_p3_human_readable_audit_artifacts.py",
    "KMFA/tests/test_v015_s09_p3_human_readable_audit_governance.py",
    "KMFA/tools/build_v015_s09_p3_human_readable_audit.py",
    "KMFA/tools/check_v015_s09_p3_human_readable_audit.py",
    "KMFA/tools/run_v015_s09_p3_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s09_p3_human_readable_audit.py",
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
        "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/human/implementation_report_zh.md",
        "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/human/test_results_zh.md",
        "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/s09_p3_human_readable_audit_manifest.json",
        "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/task_acceptance_matrix_public_safe.json",
        "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/validation_results.jsonl",
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


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise CheckError(f"JSONL object rows required: {path}")
    return rows


def _is_allowed(path: str) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_PHASE_PREFIXES)


def _check_scope() -> None:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT, check=False
    ).returncode:
        raise CheckError("S09-P3 base commit is not an ancestor of HEAD")
    groups = [
        _git("-c", "core.quotepath=false", "diff", "--name-only", f"{builder.PHASE_BASE_COMMIT}..HEAD"),
        _git("-c", "core.quotepath=false", "diff", "--name-only"),
        _git("-c", "core.quotepath=false", "diff", "--cached", "--name-only"),
        _git("-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"),
    ]
    changed = [line for group in groups for line in group.splitlines() if line]
    unexpected = sorted({path for path in changed if not _is_allowed(path)})
    if unexpected:
        raise CheckError("unexpected S09-P3 path(s): " + ", ".join(unexpected))


def _check_dependency() -> None:
    value = builder.dependency()
    head = str(value.get("validation_head") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise CheckError("S09-P2 validation head is invalid")
    if subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False).returncode:
        raise CheckError("S09-P2 validation head is not reachable")


def _check_taskpack_source() -> None:
    package = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
    expected = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != expected:
        raise CheckError("TaskPack package missing or SHA-256 drifted")
    source = _json(builder.PROJECT_ROOT / "taskpack/v1_5/source_manifest.json")
    if (
        source.get("source_package_sha256"),
        source.get("stage_count"),
        source.get("phase_count"),
        source.get("task_count"),
    ) != (expected, 24, 72, 216):
        raise CheckError("tracked TaskPack source manifest drift")
    roadmap = _json(builder.PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json")
    stage = next((row for row in roadmap.get("stages", []) if row.get("id") == "S09"), None)
    phase = next((row for row in (stage or {}).get("phases", []) if row.get("id") == "P3"), None)
    if not phase or [row.get("name") for row in phase.get("tasks", [])] != [
        "编写人类可读规则手册",
        "设计报告差异摘要",
        "验证差异闭环",
    ]:
        raise CheckError("tracked S09-P3 TaskPack contract drift")


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
            _jsonl(path)
        elif path.is_file() and path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                list(csv.reader(handle))


def _check_business_display_boundary() -> None:
    report = _json(builder.REPORT_SAMPLE_PATH)
    items = report.get("items", [])
    if report.get("included_difference_count") != 1 or report.get("excluded_non_decision_difference_count") != 1:
        raise CheckError("management difference filtering drift")
    if report.get("technical_term_occurrence_count") != 0 or report.get("debug_field_count") != 0:
        raise CheckError("technical or debug content reached management summary")
    for item in items:
        if set(item) != set(kernel.REPORT_ITEM_FIELDS):
            raise CheckError("management summary field whitelist drift")
        title = str(item.get("title_zh", ""))
        if not title.startswith("经营提醒：") or re.search(r"[A-Z_]{3,}", title):
            raise CheckError("management report title exposes internal mechanism")
        rendered = "\n".join(str(value) for value in item.values()).lower()
        if any(term.lower() in rendered for term in kernel.FORBIDDEN_REPORT_TERMS):
            raise CheckError("management summary contains forbidden internal term")
    human = (builder.HUMAN_ROOT / "report_sample_zh.md").read_text(encoding="utf-8")
    for token in ("difference_ref", "difference_type_code", "schema_version", "debug_payload", "SYN-DIFF"):
        if token in human:
            raise CheckError(f"human report sample exposes internal field: {token}")


def _check_public_boundary() -> None:
    paths = [path for path in builder.OUTPUT_ROOT.rglob("*") if path.is_file()]
    paths.extend((builder.RULE_MANUAL_PATH, builder.REPORT_DISPLAY_SPEC_PATH, builder.CLOSURE_PROTOCOL_PATH))
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
            raise CheckError(f"public S09-P3 evidence contains forbidden material: {pattern}")
    for path in paths:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".jsonl":
            _jsonl(path)


def _check_evidence() -> None:
    manual = _json(builder.RULE_MANUAL_PATH)
    review = _json(builder.RULE_REVIEW_PATH)
    spec = _json(builder.REPORT_DISPLAY_SPEC_PATH)
    report = _json(builder.REPORT_SAMPLE_PATH)
    protocol = _json(builder.CLOSURE_PROTOCOL_PATH)
    closure = _json(builder.CLOSURE_E2E_PATH)
    tasks = _json(builder.TASK_MATRIX_PATH)
    if len(manual.get("audiences", [])) != 2 or len(manual.get("rules", [])) != 10:
        raise CheckError("human rule manual coverage drift")
    if (
        review.get("transformation_rule_count"),
        review.get("difference_rule_count"),
        review.get("unexplained_rule_count"),
        review.get("owner_summary_missing_count"),
        review.get("review_status"),
    ) != (2, 8, 0, 0, "PASS"):
        raise CheckError("rule manual review drift")
    if review.get("external_human_signoff_claimed") is not False:
        raise CheckError("unsupported external signoff claim")
    if spec.get("decision_relevant_only") is not True or spec.get("debug_information_allowed") is not False:
        raise CheckError("report display policy drift")
    if (
        report.get("input_difference_count"),
        report.get("included_difference_count"),
        report.get("excluded_non_decision_difference_count"),
        report.get("technical_term_occurrence_count"),
        report.get("debug_field_count"),
    ) != (2, 1, 1, 0, 0):
        raise CheckError("management difference sample drift")
    if protocol.get("ordered_steps") != list(kernel.CLOSURE_STEPS):
        raise CheckError("closure protocol order drift")
    if any(
        protocol.get(field) is not True
        for field in (
            "feedback_required_for_every_step",
            "append_only_history_required",
            "status_refresh_persistence_required",
            "historical_query_required",
            "missing_feedback_fails",
            "out_of_order_step_fails",
        )
    ):
        raise CheckError("closure protocol gate drift")
    required_closure = {
        "required_step_count": 6,
        "event_count": 6,
        "feedback_count": 6,
        "closure_complete": True,
        "refresh_state_persisted": True,
        "history_queryable": True,
        "missing_feedback_rejected": True,
        "out_of_order_rejected": True,
        "report_version_advanced": True,
        "source_or_fact_mutation_performed": False,
        "raw_root_access_count": 0,
    }
    mismatch = [key for key, expected in required_closure.items() if closure.get(key) != expected]
    if mismatch:
        raise CheckError("closure evidence drift: " + ", ".join(mismatch))
    if tasks.get("task_count") != 3:
        raise CheckError("S09-P3 task matrix drift")


def _check_manifest(*, pre_final: bool) -> dict[str, Any]:
    manifest = _json(builder.MANIFEST_PATH)
    required = {
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "evidence_validation_status": "PENDING" if pre_final else "PASS",
        "phase_task_accepted_count": 0 if pre_final else 3,
        "overall_accepted_phase_count": 24 if pre_final else 25,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 2 if pre_final else 3,
        "stage_task_accepted_count": 6 if pre_final else 9,
        "decision": "REMAIN_IN_S09_P3_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S09_STAGE_REVIEW_ONLY",
        "s09_p1_acceptance_status": "PASSED",
        "s09_p2_acceptance_status": "PASSED",
        "s09_p3_started": True,
        "s09_p3_acceptance_status": "PENDING_FINAL_VALIDATION" if pre_final else "PASSED",
        "s09_stage_review_entry_allowed": not pre_final,
        "s09_stage_review_started": False,
        "s09_stage_review_performed": False,
        "s10_entry_allowed": False,
        "s10_p1_entry_allowed": False,
        "manual_audience_count": 2,
        "transformation_rule_count": 2,
        "difference_rule_count": 8,
        "human_rule_count": 10,
        "unexplained_rule_count": 0,
        "owner_summary_missing_count": 0,
        "finance_review_status": "PASS",
        "owner_summary_status": "PASS",
        "external_human_signoff_claimed": False,
        "report_input_difference_count": 2,
        "report_included_difference_count": 1,
        "report_excluded_non_decision_difference_count": 1,
        "report_technical_term_occurrence_count": 0,
        "report_debug_field_count": 0,
        "closure_required_step_count": 6,
        "closure_event_count": 6,
        "closure_feedback_count": 6,
        "closure_complete": True,
        "refresh_state_persisted": True,
        "history_queryable": True,
        "missing_feedback_rejected": True,
        "out_of_order_rejected": True,
        "report_version_advanced": True,
        "source_or_fact_mutation_performed": False,
        "raw_root_access_count": 0,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    mismatches = [key for key, expected in required.items() if manifest.get(key) != expected]
    if mismatches:
        raise CheckError("S09-P3 manifest mismatch: " + ", ".join(mismatches))
    return manifest


def _check_governance(*, pre_final: bool) -> None:
    acceptance = "PENDING_FINAL_VALIDATION" if pre_final else "PASSED"
    decision = "REMAIN_IN_S09_P3_FINAL_VALIDATION" if pre_final else "CONTINUE_TO_S09_STAGE_REVIEW_ONLY"
    for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
        text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            kernel.RUN_PHASE_ID,
            kernel.TASK_ID,
            kernel.ACCEPTANCE_ID,
            f'phase_acceptance_status: "{acceptance}"',
            'stage_lifecycle_status: "IN_PROGRESS"',
            'stage_acceptance_status: "PENDING"',
            "stage_execution_percentage: 100",
            f'decision: "{decision}"',
            's09_p1_acceptance_status: "PASSED"',
            's09_p2_acceptance_status: "PASSED"',
            "s09_p3_started: true",
            f's09_p3_acceptance_status: "{acceptance}"',
            f"s09_stage_review_entry_allowed: {str(not pre_final).lower()}",
            "s09_stage_review_started: false",
            "s09_stage_review_performed: false",
            "s10_p1_entry_allowed: false",
            "active_formula_count: 351",
            "active_parameter_count: 1689",
            'current_parameter_range: "PARAM-KMFA-2065..2074"',
        ):
            if token not in text:
                raise CheckError(f"governance token missing in {relative}: {token}")
    surfaces = {
        "metadata/model_registry.yaml": "kmfa_v015_s09_p3_human_readable_audit",
        "docs/governance/model_registry.yaml": "kmfa_v015_s09_p3_human_readable_audit",
        "docs/governance/formula_registry.yaml": "FORM-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT-001",
        "docs/governance/parameter_registry.csv": "PARAM-KMFA-2074",
        "docs/governance/TRACEABILITY_MATRIX.csv": "REQ-KMFA-V015-S09-P3-HUMAN-READABLE-AUDIT",
        "功能清单.md": "FEAT-KMFA-286",
    }
    for relative, token in surfaces.items():
        if token not in (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"):
            raise CheckError(f"registry token missing in {relative}: {token}")


def _check_receipts(manifest: dict[str, Any]) -> None:
    rows = _jsonl(builder.VALIDATION_RESULTS_PATH)
    if len(rows) != len(EXPECTED_VALIDATIONS):
        raise CheckError("validation receipt count mismatch")
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    if len(run_ids) != 1 or len(heads) != 1:
        raise CheckError("validation receipts do not bind one run and head")
    for row, (name, command) in zip(rows, EXPECTED_VALIDATIONS):
        if (
            row.get("name") != name
            or row.get("command") != command
            or row.get("status") != "PASS"
            or row.get("exit_code") != 0
        ):
            raise CheckError(f"validation receipt mismatch: {name}")
    run_id = next(iter(run_ids))
    head = next(iter(heads))
    if manifest.get("validation_run_id") != run_id or manifest.get("validation_head") != head:
        raise CheckError("manifest validation binding mismatch")
    if manifest.get("validation_receipt_count") != len(rows) or manifest.get("validation_pass_count") != len(rows):
        raise CheckError("manifest receipt counts mismatch")
    if _git("rev-parse", "HEAD^") != head:
        raise CheckError("final evidence commit must be the immediate child of the validated implementation head")
    final_changed = set(_git("-c", "core.quotepath=false", "diff", "--name-only", f"{head}..HEAD").splitlines())
    unexpected = sorted(final_changed - FINAL_MUTABLE_PATHS)
    if unexpected:
        raise CheckError("final evidence commit changed immutable implementation paths: " + ", ".join(unexpected))


def run(*, pre_final: bool, skip_validation_receipts: bool) -> None:
    _check_scope()
    _check_dependency()
    _check_taskpack_source()
    _check_structured_public_diff()
    _check_business_display_boundary()
    _check_public_boundary()
    _check_evidence()
    manifest = _check_manifest(pre_final=pre_final)
    _check_governance(pre_final=pre_final)
    builder.check_outputs()
    if not pre_final and not skip_validation_receipts:
        _check_receipts(manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-final", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--dependency-check", action="store_true")
    parser.add_argument("--taskpack-source-check", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--business-display-boundary-check", action="store_true")
    parser.add_argument("--public-boundary-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.dependency_check:
            _check_dependency()
        elif args.taskpack_source_check:
            _check_taskpack_source()
        elif args.structured_public_diff_check:
            _check_structured_public_diff()
        elif args.business_display_boundary_check:
            _check_business_display_boundary()
        elif args.public_boundary_check:
            _check_public_boundary()
        else:
            run(pre_final=args.pre_final, skip_validation_receipts=args.skip_validation_receipts)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CheckError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S09-P3 strict checker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
