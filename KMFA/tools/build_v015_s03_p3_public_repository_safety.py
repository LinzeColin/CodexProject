#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S03-P3."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from KMFA.tools import v015_s03_p3_public_repository_safety as safety


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PHASE_BASE_COMMIT = safety.PHASE_BASE_COMMIT
RUN_PHASE_ID = safety.RUN_PHASE_ID
TASK_ID = safety.TASK_ID
ACCEPTANCE_ID = safety.ACCEPTANCE_ID
RUN_ID = hashlib.sha256((RUN_PHASE_ID + "|2026-07-14").encode()).hexdigest()[:32]
ABSOLUTE_TEXT_PATTERN = re.compile(
    r"(?:/Users/|/Volumes/|/home/|/tmp/|~[/\\]|(?<![A-Za-z0-9_])[A-Za-z]:[/\\]|file://)",
    re.IGNORECASE,
)

PRIVATE_ROOT_RELATIVE = Path(".codex_private_runtime/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY")
PRIVATE_VALIDATION_RECEIPTS_RELATIVE = PRIVATE_ROOT_RELATIVE / "private_validation_receipts.jsonl"
VALIDATION_RECEIPT_SCHEMA_VERSION = "kmfa.v015.s03_p3.validation_receipt.v1"

OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY")
MANIFEST_RELATIVE = Path("machine/s03_p3_public_repository_safety_manifest.json")
TASK_MATRIX_RELATIVE = Path("machine/task_acceptance_matrix_public_safe.json")
EVIDENCE_SLOTS_RELATIVE = Path("machine/task_evidence_slot_matrix_public_safe.jsonl")
RECEIPT_TEMPLATE_RELATIVE = Path("machine/validation_receipts_template.jsonl")
VALIDATION_RESULTS_RELATIVE = Path("machine/validation_results.jsonl")
PROTECTION_VERIFICATION_RELATIVE = Path("machine/repository_protection_verification_public_safe.json")
FIELD_AUDIT_RELATIVE = Path("machine/committable_metadata_field_audit_public_safe.csv")
METADATA_CLASSIFICATION_RELATIVE = Path("machine/phase_metadata_classification_public_safe.csv")
DUAL_PLANE_RELATIVE = Path("machine/dual_plane_verification_public_safe.json")
LEGACY_CENSUS_RELATIVE = Path("machine/legacy_exposure_census_public_safe.json")
COMPLETION_RELATIVE = Path("human/completion_record_zh.md")
DUAL_PLANE_REPORT_RELATIVE = Path("human/dual_plane_validation_report_zh.md")
TEST_RESULTS_RELATIVE = Path("human/test_results_zh.md")
ROLLBACK_RELATIVE = Path("human/rollback_plan_zh.md")
OPEN_RISKS_RELATIVE = Path("human/open_risks_zh.md")
PROTECTION_POLICY_RELATIVE = Path(
    "metadata/protocol/v015_s03_p3_public_repository_protection_policy_public_safe.json"
)
METADATA_POLICY_RELATIVE = Path(
    "metadata/protocol/v015_s03_p3_committable_metadata_policy_public_safe.json"
)
REDACTION_AMENDMENT_RELATIVE = Path(
    "metadata/protocol/v015_s03_p3_legacy_public_metadata_redaction_amendment.json"
)


def _artifact_ref(relative: Path) -> str:
    return f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{relative.as_posix()}"


ARTIFACT_REFS = {
    "manifest": _artifact_ref(MANIFEST_RELATIVE),
    "task_matrix": _artifact_ref(TASK_MATRIX_RELATIVE),
    "evidence_slots": _artifact_ref(EVIDENCE_SLOTS_RELATIVE),
    "receipt_template": _artifact_ref(RECEIPT_TEMPLATE_RELATIVE),
    "validation_results": _artifact_ref(VALIDATION_RESULTS_RELATIVE),
    "protection_verification": _artifact_ref(PROTECTION_VERIFICATION_RELATIVE),
    "field_audit": _artifact_ref(FIELD_AUDIT_RELATIVE),
    "metadata_classification": _artifact_ref(METADATA_CLASSIFICATION_RELATIVE),
    "dual_plane": _artifact_ref(DUAL_PLANE_RELATIVE),
    "legacy_census": _artifact_ref(LEGACY_CENSUS_RELATIVE),
    "completion": _artifact_ref(COMPLETION_RELATIVE),
    "dual_plane_report": _artifact_ref(DUAL_PLANE_REPORT_RELATIVE),
    "test_results": _artifact_ref(TEST_RESULTS_RELATIVE),
    "rollback": _artifact_ref(ROLLBACK_RELATIVE),
    "open_risks": _artifact_ref(OPEN_RISKS_RELATIVE),
    "protection_policy": f"KMFA/{PROTECTION_POLICY_RELATIVE.as_posix()}",
    "metadata_policy": f"KMFA/{METADATA_POLICY_RELATIVE.as_posix()}",
    "redaction_amendment": f"KMFA/{REDACTION_AMENDMENT_RELATIVE.as_posix()}",
}

TASKS = (
    {
        "task_id": "S03P3T01",
        "name": "完善 gitignore 与秘密扫描",
        "acceptance": "敏感测试样本全部被 ignore 与统一 scanner 阻止。",
        "result": "TASK_ACCEPTED",
    },
    {
        "task_id": "S03P3T02",
        "name": "定义可提交 metadata",
        "acceptance": "仅六类 public-safe metadata；未知字段和四类敏感明细默认拒绝。",
        "result": "TASK_ACCEPTED",
    },
    {
        "task_id": "S03P3T03",
        "name": "验证私有与公开双平面",
        "acceptance": "同 run private/public 可精确投影，声明攻击模型下无明文、key 或裸 hash 泄漏。",
        "result": "TASK_ACCEPTED",
    },
)
EVIDENCE_SLOTS = (
    "manifest.json", "commands.txt", "test_results.json", "human_summary.md",
    "changed_files.txt", "screenshots/", "logs/", "exports/", "rollback.md", "open_risks.md",
)
EVIDENCE_SLOT_ARTIFACTS = {
    "manifest.json": "manifest",
    "test_results.json": "validation_results",
    "human_summary.md": "completion",
    "rollback.md": "rollback",
    "open_risks.md": "open_risks",
}
EVIDENCE_SLOT_NA_RATIONALES = {
    "commands.txt": "exact commands are schema-bound in validation receipt template/results",
    "changed_files.txt": "exact changed refs are schema-bound in the phase manifest",
    "screenshots/": "CLI governance Phase; visual UI evidence is not applicable",
    "logs/": "command output remains private; public receipts expose digests only",
    "exports/": "this Phase produces no business or data export",
}

EXPECTED_VALIDATION_RECEIPTS = {
    "python_compile": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; "
        "[ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in "
        "('KMFA/tools/v015_s03_p3_public_repository_safety.py',"
        "'KMFA/tools/build_v015_s03_p3_public_repository_safety.py',"
        "'KMFA/tools/check_v015_s03_p3_public_repository_safety.py',"
        "'KMFA/tools/run_v015_s03_p3_validations.py')]\""
    ),
    "public_repository_safety_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p3_public_repository_safety"
    ),
    "phase_governance_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p3_public_repository_safety_governance"
    ),
    "phase_checker_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p3_public_repository_safety_checker"
    ),
    "validation_runner_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_p3_validation_runner"
    ),
    "legacy_access_policy_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_access_security_policy"
    ),
    "dws_public_metadata_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_dws_output_manifest_backup"
    ),
    "roadmap_governance_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_roadmap_governance_sync"
    ),
    "baseline_adapter_regression_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_a0_file_register "
        "KMFA.tests.test_a0_golden_fixture "
        "KMFA.tests.test_finance_file_adapter "
        "KMFA.tests.test_project_composite_key "
        "KMFA.tests.test_project_cost_fact_layer "
        "KMFA.tests.test_redcircle_postponement_policy "
        "KMFA.tests.test_s05_p2_completion_gate "
        "KMFA.tests.test_s05_p3_authority_baseline_lock "
        "KMFA.tests.test_v013_s05_p1_a0_file_registration "
        "KMFA.tests.test_v014_s03_p1_file_registration "
        "KMFA.tests.test_v014_s05_p1_a0_file_registration "
        "KMFA.tests.test_v014_s05_p3_authority_baseline_lock "
        "KMFA.tests.test_v014_s07_p1_finance_file_adapter "
        "KMFA.tests.test_v014_s07_p2_wps_file_adapter "
        "KMFA.tests.test_v015_s01_p2_implementation_spec_gap_inventory "
        "KMFA.tests.test_wps_file_adapter"
    ),
    "report_quality_regression_tests": (
        "PYTHONDONTWRITEBYTECODE=1 KMFA_VALIDATION_READ_ONLY=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_cross_table_review "
        "KMFA.tests.test_customer_business_analysis "
        "KMFA.tests.test_entity_matching_quality "
        "KMFA.tests.test_performance_fact_fields "
        "KMFA.tests.test_performance_review_list "
        "KMFA.tests.test_performance_salary_boundary "
        "KMFA.tests.test_project_margin_cash_margin "
        "KMFA.tests.test_project_scope_reconciliation "
        "KMFA.tests.test_project_status_lifecycle "
        "KMFA.tests.test_subcontract_procurement_aggregation "
        "KMFA.tests.test_v013_s06_p3_validation_evidence_replay "
        "KMFA.tests.test_v014_final_overall_review "
        "KMFA.tests.test_v014_s06_p3_validation_evidence "
        "KMFA.tests.test_v014_s15_p1_post_remediation_performance_fact_fields "
        "KMFA.tests.test_validation_evidence_output"
    ),
    "automation_identity_safety_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_automation_schedule_contract "
        "KMFA.tests.test_daily_routine_check "
        "KMFA.tests.test_dingtalk_attendance"
    ),
    "public_skill_package_validators": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import runpy; "
        "targets=('KMFA/daily_routine_check_skill/tools/validate_skill_package.py',"
        "'KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py'); "
        "[(_ for _ in ()).throw(SystemExit(f'{target} failed')) if "
        "runpy.run_path(target, run_name='__validation__')['main']() else None for target in targets]\""
    ),
    "dingtalk_skill_identity_regression_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import runpy; "
        "targets=('KMFA/kmfa-dingtalk-attendance-skill/tests/test_raw_archive_replay.py',"
        "'KMFA/kmfa-dingtalk-attendance-skill/tests/test_stage2_source_from_raw_replay.py'); "
        "[runpy.run_path(target, run_name='__main__') for target in targets]\""
    ),
    "monthly_report_public_metadata_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest discover "
        "-s KMFA/mgmt-monthly-report-skill/tests -p 'test_*.py'"
    ),
    "builder_exact_rebuild": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_p3_public_repository_safety.py --check"
    ),
    "phase_checker": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_p3_public_repository_safety.py "
        "--skip-validation-receipts --skip-clean-commit --pre-receipt-final-governance"
    ),
    "project_governance": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/validate_project_governance.py --project KMFA --mode required"
    ),
    "lean_governance": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/lean_governance.py validate --project KMFA --mode required"
    ),
    "governance_sync": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        f"scripts/validate_governance_sync.py --changed-only --base-ref {PHASE_BASE_COMMIT} --enforce-sync"
    ),
    "no_float_money": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    "no_omission": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    "git_diff_check": f"git diff --check {PHASE_BASE_COMMIT}..HEAD",
}

VALIDATION_MUTABLE_KEYS = frozenset(
    {"manifest", "task_matrix", "validation_results", "protection_verification", "dual_plane", "legacy_census", "completion", "dual_plane_report", "test_results", "open_risks"}
)

ALLOWED_PHASE_PREFIXES = (
    "KMFA/.gitignore",
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/docs/governance/",
    "KMFA/daily_routine_check_skill/",
    "KMFA/kmfa-dingtalk-attendance-skill/",
    "KMFA/metadata/",
    "KMFA/mgmt-monthly-report-skill/",
    "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/",
    "KMFA/tests/",
    "KMFA/tools/",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
)

ALLOWED_LEGACY_STAGE_EVIDENCE_REFS = frozenset(
    {
        "KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine/mismatch_report.csv",
        "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/machine/s09_p1_manifest.json",
        "KMFA/stage_artifacts/S09_P2_margin_cash_margin/machine/s09_p2_manifest.json",
        "KMFA/stage_artifacts/S13_P3_cross_table_review/machine/s13_p3_manifest.json",
        "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/machine/s16_p1_manifest.json",
        "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/machine/s16_p2_manifest.json",
        "KMFA/stage_artifacts/S16_P3_customer_business_analysis/machine/s16_p3_manifest.json",
        "KMFA/stage_artifacts/V013_S06_P3_VALIDATION_EVIDENCE_REPLAY/machine/mismatch_report.csv",
        "KMFA/stage_artifacts/V014_FINAL_OVERALL_REVIEW/machine/final_overall_review_manifest.json",
        "KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/human/authority_baseline_lock_report.md",
        "KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/human/risk_register.md",
        "KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/human/rollback_plan.md",
        "KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/human/test_results.md",
        "KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/machine/authority_baseline_lock_manifest.json",
        "KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE/machine/mismatch_report.csv",
        "KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/human/finance_file_adapter_report.md",
        "KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/human/risk_register.md",
        "KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/human/test_results.md",
        "KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/machine/finance_file_adapter_manifest.json",
        "KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/machine/finance_readonly_field_report.jsonl",
        "KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/human/test_results.md",
        "KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/human/wps_file_adapter_report.md",
        "KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/machine/wps_conversion_guidance.jsonl",
        "KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/machine/wps_file_adapter_manifest.json",
        "KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/machine/wps_readonly_field_report.jsonl",
        "KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/human/redcircle_postponement_report.md",
        "KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/human/test_results.md",
        "KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/machine/redcircle_postponement_manifest.json",
        "KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/machine/redcircle_reserved_export_templates.jsonl",
        "KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_manifest.json",
        "KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_summary.json",
    }
)

PHASE_METADATA_CLASS_PREFIXES = (
    ("KMFA/metadata/protocol/", "rule"),
    ("KMFA/metadata/security/", "rule"),
    ("KMFA/metadata/traceability/", "schema"),
    ("KMFA/metadata/project/", "status"),
    ("KMFA/metadata/model_registry.yaml", "status"),
    ("KMFA/metadata/stage_status.jsonl", "status"),
    ("KMFA/metadata/automation/", "deidentified_manifest"),
    ("KMFA/metadata/baseline/", "deidentified_manifest"),
    ("KMFA/metadata/imports/", "deidentified_manifest"),
    ("KMFA/metadata/lineage/", "deidentified_manifest"),
    ("KMFA/metadata/mgmt-monthly-report-skill/", "aggregate_evidence"),
    ("KMFA/metadata/quality/", "deidentified_manifest"),
    ("KMFA/metadata/reports/", "aggregate_evidence"),
    ("KMFA/metadata/schema_maps/", "deidentified_manifest"),
    ("KMFA/metadata/dws_outputs_backup/", "aggregate_evidence"),
    ("KMFA/metadata/daily_routine_check/", "deidentified_manifest"),
    ("KMFA/metadata/dingtalk_attendance/", "deidentified_manifest"),
)


class BuildError(RuntimeError):
    """The current repository or public evidence cannot be built safely."""


def _read_public_ref(path: str) -> bytes:
    try:
        return safety.read_repository_file(path)
    except (OSError, safety.SafetyError) as error:
        raise BuildError(f"unsafe or unreadable public repository file: {path}") from error


def _public_ref_exists(path: str) -> bool:
    try:
        return safety.repository_file_exists(path)
    except (OSError, safety.SafetyError) as error:
        raise BuildError(f"unsafe public repository path: {path}") from error


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join((json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n").encode() for row in rows)


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _git(args: Sequence[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise BuildError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def _git_paths(args: Sequence[str]) -> tuple[str, ...]:
    """Return Git path output without C quoting or newline ambiguity."""
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise BuildError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or f"git {' '.join(args)} failed"
        )
    return tuple(
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    )


def phase_changed_refs() -> tuple[str, ...]:
    changed = set(_git_paths(["diff", "--name-only", "-z", f"{PHASE_BASE_COMMIT}..HEAD", "--", "KMFA"]))
    changed.update(_git_paths(["diff", "--name-only", "-z", "--", "KMFA"]))
    changed.update(_git_paths(["diff", "--cached", "--name-only", "-z", "--", "KMFA"]))
    changed.update(_git_paths(["ls-files", "--others", "--exclude-standard", "-z", "--", "KMFA"]))
    return tuple(sorted(path for path in changed if path))


def _allowed_phase_ref(path: str) -> bool:
    return path in ALLOWED_LEGACY_STAGE_EVIDENCE_REFS or any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in ALLOWED_PHASE_PREFIXES
    )


def _blob_at_ref(path: str, git_ref: str | None) -> bytes:
    if git_ref is None:
        if not _public_ref_exists(path):
            raise BuildError(f"validation subject path missing: {path}")
        return _read_public_ref(path)
    result = subprocess.run(
        ["git", "show", f"{git_ref}:{path}"], cwd=REPO_ROOT, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise BuildError(f"validation subject path missing at {git_ref}: {path}")
    return result.stdout


def validation_subject_refs(changed_refs: Sequence[str] | None = None) -> tuple[str, ...]:
    refs = tuple(phase_changed_refs() if changed_refs is None else changed_refs)
    mutable = {ARTIFACT_REFS[key] for key in VALIDATION_MUTABLE_KEYS}
    mutable.update(
        {
            "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
            "KMFA/docs/governance/events.jsonl",
            "KMFA/docs/governance/development_events.jsonl",
            "KMFA/metadata/stage_status.jsonl",
        }
    )
    return tuple(sorted(ref for ref in refs if ref not in mutable))


def _validation_entry_at_ref(path: str, git_ref: str | None) -> tuple[str, bytes]:
    """Bind either the exact blob or an authenticated deletion tombstone."""
    if git_ref is None:
        if _public_ref_exists(path):
            return "PRESENT", _read_public_ref(path)
        diff_args = [
            "diff", "--no-renames", "--name-only", "--diff-filter=D", "-z",
            PHASE_BASE_COMMIT, "--", path,
        ]
    else:
        result = subprocess.run(
            ["git", "show", f"{git_ref}:{path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return "PRESENT", result.stdout
        diff_args = [
            "diff", "--no-renames", "--name-only", "--diff-filter=D", "-z",
            f"{PHASE_BASE_COMMIT}..{git_ref}", "--", path,
        ]
    deleted = set(_git_paths(diff_args))
    if path in deleted:
        _blob_at_ref(path, PHASE_BASE_COMMIT)
        return "DELETED", b""
    raise BuildError(f"validation subject path missing without a bound deletion: {path}")


def validation_subject_sha256(
    project_root: Path = PROJECT_ROOT,
    *,
    changed_refs: Sequence[str] | None = None,
    git_ref: str | None = None,
) -> str:
    del project_root
    digest = hashlib.sha256()
    for ref in validation_subject_refs(changed_refs):
        state, payload = _validation_entry_at_ref(ref, git_ref)
        digest.update(ref.encode() + b"\0" + state.encode() + b"\0")
        if state == "PRESENT":
            digest.update(hashlib.sha256(payload).digest())
    return "sha256:" + digest.hexdigest()


def _private_receipt_rows() -> list[dict[str, Any]]:
    path = PROJECT_ROOT / PRIVATE_VALIDATION_RECEIPTS_RELATIVE
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows.append(
                {
                    key: row.get(key)
                    for key in (
                        "schema_version", "run_id", "validation_id", "command", "result", "exit_code",
                        "execution_sequence", "phase_base_commit", "head_before", "head_after",
                        "validation_subject_sha256", "stdout_sha256", "stderr_sha256", "duration_ms",
                    )
                    if key in row
                }
            )
    return rows


def _field_audit_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for category in safety.COMMITTABLE_METADATA_CLASSES:
        rows.append(
            {
                "classification": "ALLOW",
                "category": category,
                "public_contract": "strict_schema_or_tracked_public_artifact_binding",
                "unknown_field_policy": "DENY",
                "raw_private_hash_allowed": "false",
            }
        )
    for category in safety.FORBIDDEN_PUBLIC_DETAIL_CLASSES:
        rows.append(
            {
                "classification": "DENY",
                "category": category,
                "public_contract": "private_plane_or_opaque_non_derived_ref_only",
                "unknown_field_policy": "DENY",
                "raw_private_hash_allowed": "false",
            }
        )
    return rows


def _phase_metadata_class(path: str) -> str:
    for prefix, metadata_class in PHASE_METADATA_CLASS_PREFIXES:
        if path == prefix or (prefix.endswith("/") and path.startswith(prefix)):
            if metadata_class not in safety.COMMITTABLE_METADATA_CLASSES:
                raise BuildError(f"invalid phase metadata class policy: {metadata_class}")
            return metadata_class
    raise BuildError(f"phase metadata ref has no explicit six-class policy: {path}")


def _phase_metadata_rows(changed_refs: Sequence[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    deleted_refs: set[str] | None = None
    for ref in sorted(path for path in changed_refs if path.startswith("KMFA/metadata/")):
        path = REPO_ROOT / ref
        exists = _public_ref_exists(ref)
        if exists:
            payload = _read_public_ref(ref)
            ref_state = "PRESENT"
        else:
            if deleted_refs is None:
                deleted_refs = set(
                    _git_paths(
                        [
                            "diff", "--no-renames", "--name-only", "--diff-filter=D", "-z",
                            PHASE_BASE_COMMIT, "--", "KMFA/metadata",
                        ]
                    )
                )
        if not exists and deleted_refs is not None and ref in deleted_refs:
            payload = _blob_at_ref(ref, PHASE_BASE_COMMIT)
            ref_state = "DELETED_PROTECTED_METADATA"
        elif not exists:
            raise BuildError(f"phase metadata ref missing from worktree: {ref}")
        structured_findings = safety.audit_public_metadata_bytes(ref, payload)
        if structured_findings:
            categories = sorted({finding.category for finding in structured_findings})
            raise BuildError(
                f"phase metadata public-detail audit failed: {ref}: {','.join(categories)}"
            )
        secret_findings = safety.scan_payload_for_secrets(ref, payload)
        if secret_findings:
            raise BuildError(f"phase metadata secret audit failed: {ref}")
        rows.append(
            {
                "metadata_ref": ref,
                "metadata_class": _phase_metadata_class(ref),
                "format": path.suffix.lower().lstrip(".") or "none",
                "ref_state": ref_state,
                "structured_public_detail_finding_count": "0",
                "secret_finding_count": "0",
                "classification_policy": "EXPLICIT_SIX_CLASS_FAIL_CLOSED",
            }
        )
    return rows


def _audit_changed_stage_evidence(changed_refs: Sequence[str]) -> None:
    """Apply the metadata detail contract to every changed legacy evidence record."""
    current_output_prefix = f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/"
    for ref in sorted(changed_refs):
        if not ref.startswith("KMFA/stage_artifacts/") or ref.startswith(current_output_prefix):
            continue
        if not _public_ref_exists(ref):
            continue
        payload = _read_public_ref(ref)
        if ABSOLUTE_TEXT_PATTERN.search(payload.decode("utf-8", errors="replace")):
            raise BuildError(f"changed stage evidence contains an absolute local path: {ref}")
        findings = safety.audit_public_metadata_bytes(ref, payload)
        if findings:
            categories = sorted({finding.category for finding in findings})
            raise BuildError(
                f"changed stage evidence public-detail audit failed: {ref}: {','.join(categories)}"
            )


_STRUCTURED_PUBLIC_SUFFIXES = frozenset(
    {".csv", ".json", ".jsonl", ".md", ".sql", ".toml", ".txt", ".yaml", ".yml"}
)


def _finding_delta_signature(finding: safety.Finding) -> tuple[str, str]:
    detail = re.sub(r"\$\[(?:line|row):[0-9]+\]", "$[]", finding.detail)
    return finding.category, detail


def _audit_changed_public_structured_files(changed_refs: Sequence[str]) -> None:
    """Block new structured leakage anywhere in the Phase-owned public diff.

    Historical governance ledgers retain a narrow count/signature delta allowance;
    every other changed or new structured file must be finding-free.
    """
    for ref in sorted(changed_refs):
        if Path(ref).suffix.casefold() not in _STRUCTURED_PUBLIC_SUFFIXES:
            continue
        if not _public_ref_exists(ref):
            continue
        payload = _read_public_ref(ref)
        if safety.scan_payload_for_secrets(ref, payload):
            raise BuildError(f"changed structured public file contains secret material: {ref}")
        current = safety.audit_public_metadata_bytes(ref, payload)
        if not current:
            continue
        delta_allowed = ref.startswith("KMFA/docs/governance/") or Path(ref).suffix.casefold() in {
            ".md", ".sql", ".txt"
        }
        if not delta_allowed:
            categories = sorted({finding.category for finding in current})
            raise BuildError(
                f"changed structured public file failed detail audit: {ref}: {','.join(categories)}"
            )
        baseline_result = subprocess.run(
            ["git", "show", f"{PHASE_BASE_COMMIT}:{ref}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if baseline_result.returncode != 0:
            raise BuildError(f"new public text/governance file is not public-safe: {ref}")
        baseline = safety.audit_public_metadata_bytes(ref, baseline_result.stdout)
        current_counts = collections.Counter(_finding_delta_signature(item) for item in current)
        baseline_counts = collections.Counter(_finding_delta_signature(item) for item in baseline)
        if current_counts - baseline_counts:
            raise BuildError(f"governance structured leakage increased from Phase base: {ref}")


def _legacy_census() -> dict[str, Any]:
    absolute_path_files: set[str] = set()
    absolute_path_count = 0
    structured_findings = 0
    structured_files: set[str] = set()
    public_candidates = _git_paths(
        [
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "KMFA/metadata",
        ]
    )
    for relative in public_candidates:
        if not relative.startswith("KMFA/metadata/") or not _public_ref_exists(relative):
            continue
        payload = _read_public_ref(relative)
        text = payload.decode("utf-8", errors="replace")
        matches = ABSOLUTE_TEXT_PATTERN.findall(text)
        if matches:
            absolute_path_count += len(matches)
            absolute_path_files.add(relative)
        findings = safety.audit_public_metadata_bytes(relative, payload)
        for finding in findings:
            if finding.category != "absolute_local_path":
                structured_findings += 1
                structured_files.add(relative)
    return {
        "schema_version": "kmfa.v015.s03_p3.legacy_exposure_census.public_safe.v1",
        "run_id": RUN_ID,
        "current_tree_absolute_local_path_count": absolute_path_count,
        "current_tree_absolute_local_path_file_count": len(absolute_path_files),
        "legacy_schema_review_finding_count": structured_findings,
        "legacy_schema_review_file_count": len(structured_files),
        "finding_values_public": False,
        "current_submission_policy_enforced": True,
        "reachable_history_clean": False,
        "history_rewrite_performed": False,
        "final_github_upload_allowed_by_this_phase": False,
        "history_remediation_required_before_final_upload": True,
    }


def _protection_policy() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s03_p3.public_repository_protection_policy.v1",
        "policy_version": safety.POLICY_VERSION,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": "S03-P3",
        "protected_submission_classes": list(safety.PROTECTED_SUBMISSION_CLASSES),
        "enforcement_scopes": ["HEAD", "index", "worktree", "git_add_force_fixture"],
        "owner_plaintext_exception_effective": False,
        "unknown_sensitive_path_default": "DENY",
        "github_server_side_enforcement_claimed": False,
        "final_upload_requires_separate_history_and_remote_gate": True,
    }


def _metadata_policy() -> dict[str, Any]:
    return {
        "schema_version": safety.METADATA_CONTRACT_VERSION,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": "S03-P3",
        "public_envelope_schema_version": safety.PUBLIC_ENVELOPE_VERSION,
        "allowed_metadata_classes": list(safety.COMMITTABLE_METADATA_CLASSES),
        "forbidden_public_detail_classes": list(safety.FORBIDDEN_PUBLIC_DETAIL_CLASSES),
        "unknown_fields_allowed": False,
        "absolute_local_paths_allowed": False,
        "raw_private_content_hash_allowed": False,
        "tracked_public_artifact_hash_allowed": True,
        "opaque_ref_must_not_be_unkeyed_sensitive_digest": True,
    }


def _redaction_amendment(census: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s03_p3.legacy_public_metadata_redaction_amendment.v1",
        "phase_id": "S03-P3",
        "amendment_scope": "current_tree_producer_and_public_projection_only",
        "legacy_owner_plaintext_exception_effective": False,
        "absolute_path_migration": {
            "raw_root": "PRIMARY_RAW_ROOT plus null public path plus private registry ref",
            "worktree": "repo://KMFA",
            "local_runtime": "local-resource://PRIVATE_RUNTIME",
        },
        "sensitive_identifier_migration": "versioned opaque non-derived public refs",
        "unkeyed_low_entropy_hash_publication_allowed": False,
        "current_tree_absolute_local_path_count_after_migration": census["current_tree_absolute_local_path_count"],
        "reachable_history_clean": False,
        "history_rewrite_performed": False,
        "history_remediation_owner_decision_required": True,
    }


def _public_projection_summary(public_projection: Mapping[str, Any]) -> dict[str, Any]:
    """Return the deterministic public audit surface, never private-derived tokens."""
    safety.validate_public_metadata_envelope(public_projection)
    return {
        "schema_version": safety.PUBLIC_PROJECTION_VERSION,
        "envelope_schema_version": public_projection["schema_version"],
        "record_type": public_projection["record_type"],
        "run_id": public_projection["run_id"],
        "subject_class": public_projection["subject_class"],
        "status": public_projection["status"],
        "aggregate_counts": public_projection["aggregate_counts"],
        "public_flags": public_projection["public_flags"],
        "policy_ref_count": len(public_projection["policy_refs"]),
        "evidence_ref_count": len(public_projection["evidence_refs"]),
        "public_artifact_digest_count": len(public_projection["public_artifact_digests"]),
        "opaque_token_count": len(public_projection["opaque_tokens"]),
        "plaintext_or_raw_private_values_public": False,
        "keyed_opaque_token_values_bound_in_public_projection": True,
    }


def expected_outputs(*, final_validation: bool | None = None) -> dict[Path, bytes]:
    changed_refs = phase_changed_refs()
    escaped = [ref for ref in changed_refs if not _allowed_phase_ref(ref)]
    if escaped:
        raise BuildError("phase diff escaped allowlist: " + ", ".join(escaped))
    _audit_changed_public_structured_files(changed_refs)
    _audit_changed_stage_evidence(changed_refs)
    ignore = safety.verify_gitignore_contract()
    scans = {}
    for scope in ("head", "index", "worktree"):
        scanned, findings = safety.scan_repository(scope=scope)
        scans[scope] = {"scanned_file_count": scanned, "finding_count": len(findings), "pass": not findings}
        if findings:
            raise BuildError(f"{scope} repository scan found {len(findings)} blocking findings")
    if not ignore["pass"]:
        raise BuildError("gitignore contract failed")

    private_summary = safety.private_evidence_summary(PROJECT_ROOT / PRIVATE_ROOT_RELATIVE, run_id=RUN_ID)
    public_projection = private_summary.pop("public_projection")
    verification = private_summary.pop("verification")
    dual_plane = {
        "schema_version": safety.PUBLIC_PROJECTION_VERSION,
        "run_id": RUN_ID,
        "same_run_evidence_summary": private_summary,
        "public_projection": public_projection,
        "public_projection_summary": _public_projection_summary(public_projection),
        "verification": verification,
        "raw_root_access_count_by_phase": 0,
    }
    census = _legacy_census()
    metadata_rows = _phase_metadata_rows(changed_refs)
    receipts = _private_receipt_rows()
    if final_validation is None:
        final_validation = bool(receipts) and len(receipts) == len(EXPECTED_VALIDATION_RECEIPTS) and all(
            row.get("result") == "PASS" for row in receipts
        )
    validated_receipts = receipts if final_validation else []
    validation_status = "PASS" if final_validation else "PENDING_FINAL_VALIDATION"
    decision = "CONTINUE_TO_S03_STAGE_REVIEW_ONLY" if final_validation else "REMAIN_IN_S03_P3"
    subject_refs = validation_subject_refs(changed_refs)
    subject_digest = validation_subject_sha256(changed_refs=changed_refs)

    protection = {
        "schema_version": "kmfa.v015.s03_p3.repository_protection_verification.v1",
        "run_id": RUN_ID,
        "gitignore": ignore,
        "repository_scans": scans,
        "owner_plaintext_exception_effective": False,
        "current_tree_absolute_local_path_count": census["current_tree_absolute_local_path_count"],
        "current_submission_gate_pass": (
            all(row["pass"] for row in scans.values())
            and ignore["pass"]
            and census["current_tree_absolute_local_path_count"] == 0
            and census["legacy_schema_review_finding_count"] == 0
        ),
        "reachable_history_clean": False,
        "history_gate_deferred_to_final_upload": True,
    }
    task_matrix = []
    for task in TASKS:
        task_matrix.append(
            {
                **task,
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED" if final_validation else "PENDING_FINAL_VALIDATION",
                "evidence_validation_status": validation_status,
            }
        )
    slots = []
    for task in TASKS:
        for slot in EVIDENCE_SLOTS:
            artifact_key = EVIDENCE_SLOT_ARTIFACTS.get(slot)
            if artifact_key is not None:
                status = "PRESENT"
                rationale = "bound to an existing public-safe phase artifact"
                artifact_ref = ARTIFACT_REFS[artifact_key]
            else:
                status = "N/A_WITH_RATIONALE"
                rationale = EVIDENCE_SLOT_NA_RATIONALES[slot]
                artifact_ref = None
            slots.append(
                {
                    "task_id": task["task_id"],
                    "slot": slot,
                    "status": status,
                    "public_safe": True,
                    "rationale": rationale,
                    "artifact_ref": artifact_ref,
                }
            )
    receipt_template = [
        {
            "schema_version": VALIDATION_RECEIPT_SCHEMA_VERSION,
            "run_id": None,
            "validation_id": validation_id,
            "command": command,
            "result": "PENDING",
            "phase_base_commit": PHASE_BASE_COMMIT,
        }
        for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items()
    ]
    # A running or failed private receipt set is not public evidence. Keep the
    # committed pending projection deterministic until one complete run passes.
    validation_rows = validated_receipts or receipt_template
    manifest = {
        "schema_version": "kmfa.v015.s03_p3.public_repository_safety_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S03",
        "phase_id": "S03-P3",
        "run_phase_id": RUN_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "run_id": RUN_ID,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final_validation else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": validation_status,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "decision": decision,
        "s03_stage_review_entry_allowed": bool(final_validation),
        "s03_stage_review_started": False,
        "s04_p1_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "raw_root_access_count_by_phase": 0,
        "protected_submission_class_count": len(safety.PROTECTED_SUBMISSION_CLASSES),
        "committable_metadata_class_count": len(safety.COMMITTABLE_METADATA_CLASSES),
        "forbidden_public_detail_class_count": len(safety.FORBIDDEN_PUBLIC_DETAIL_CLASSES),
        "task_count": 3,
        "task_accepted_count": 3 if final_validation else 0,
        "validation_receipt_count": len(EXPECTED_VALIDATION_RECEIPTS),
        "validation_pass_count": len(validated_receipts),
        "validation_run_id": validated_receipts[0].get("run_id") if validated_receipts else None,
        "validation_subject_refs": list(subject_refs),
        "validation_subject_sha256": subject_digest,
        "phase_changed_refs": list(changed_refs),
        "artifact_refs": ARTIFACT_REFS,
        "history_boundary": {
            "current_submission_policy_enforced": True,
            "reachable_history_clean": False,
            "history_rewrite_performed": False,
            "final_github_upload_allowed_by_this_phase": False,
        },
    }

    field_rows = _field_audit_rows()
    protection_policy = _protection_policy()
    metadata_policy = _metadata_policy()
    amendment = _redaction_amendment(census)
    outputs: dict[Path, bytes] = {
        PROJECT_ROOT / PROTECTION_POLICY_RELATIVE: _json_bytes(protection_policy),
        PROJECT_ROOT / METADATA_POLICY_RELATIVE: _json_bytes(metadata_policy),
        PROJECT_ROOT / REDACTION_AMENDMENT_RELATIVE: _json_bytes(amendment),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / MANIFEST_RELATIVE: _json_bytes(manifest),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / TASK_MATRIX_RELATIVE: _json_bytes(task_matrix),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / EVIDENCE_SLOTS_RELATIVE: _jsonl_bytes(slots),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / RECEIPT_TEMPLATE_RELATIVE: _jsonl_bytes(receipt_template),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / VALIDATION_RESULTS_RELATIVE: _jsonl_bytes(validation_rows),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / PROTECTION_VERIFICATION_RELATIVE: _json_bytes(protection),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / FIELD_AUDIT_RELATIVE: _csv_bytes(
            field_rows,
            ("classification", "category", "public_contract", "unknown_field_policy", "raw_private_hash_allowed"),
        ),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / METADATA_CLASSIFICATION_RELATIVE: _csv_bytes(
            metadata_rows,
            (
                "metadata_ref",
                "metadata_class",
                "format",
                "ref_state",
                "structured_public_detail_finding_count",
                "secret_finding_count",
                "classification_policy",
            ),
        ),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / DUAL_PLANE_RELATIVE: _json_bytes(dual_plane),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / LEGACY_CENSUS_RELATIVE: _json_bytes(census),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / COMPLETION_RELATIVE: (
            "# KMFA v1.5 S03-P3 完成记录\n\n"
            f"- Phase execution：100%\n- Phase acceptance：{'PASSED' if final_validation else 'PENDING_FINAL_VALIDATION'}\n"
            f"- 决策：`{decision}`\n- 3 个 Roadmap Task 已实现；Stage S03 仍为 `IN_PROGRESS / PENDING`。\n"
            "- 本 Run 未进入 Stage review、S04、GitHub upload 或 App reinstall。\n"
        ).encode(),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / DUAL_PLANE_REPORT_RELATIVE: (
            "# 私有/公开双平面验证\n\n"
            "同一 run ID 的合成 private receipt 与 tracked public projection 可精确重建并逐字段绑定；"
            "公开 projection 仅发布 keyed HMAC opaque token、aggregate/count/status 和严格 public refs，"
            "不发布 plaintext/raw private value。\n"
            "声明攻击语料中的明文、大小写、hex、base64、裸 SHA-256、private record 和 key 均未泄漏。\n"
            "不可还原结论仅适用于声明攻击模型下的 public-only 观察，不是信息论证明；真实 raw access count 为 0。\n"
        ).encode(),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / TEST_RESULTS_RELATIVE: (
            "# 测试结果\n\n"
            f"- receipt：{len(validated_receipts)}/{len(EXPECTED_VALIDATION_RECEIPTS)} PASS\n"
            f"- evidence validation：{validation_status}\n"
        ).encode(),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / ROLLBACK_RELATIVE: (
            "# 回滚计划\n\n仅回滚 S03-P3 tracked diff；不得恢复 owner 明文旁路，不得触碰 raw 或改写 Git 历史。\n"
        ).encode(),
        PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / OPEN_RISKS_RELATIVE: (
            "# 开放风险\n\n"
            "1. reachable Git 历史仍含 legacy 本机路径、文件名或低熵 hash；本 Phase 未获授权改写历史，最终 upload 必须保持阻断。\n"
            "2. 本 Phase 只证明本地 fail-closed gate；未声称 GitHub server-side enforcement。\n"
            "3. 双平面不可反推结论限定于已声明攻击模型，不是信息论证明。\n"
        ).encode(),
    }
    for path, payload in outputs.items():
        relative = path.relative_to(REPO_ROOT).as_posix()
        if ABSOLUTE_TEXT_PATTERN.search(payload.decode("utf-8", errors="replace")):
            raise BuildError(f"generated public evidence contains an absolute local path: {relative}")
        findings = safety.audit_public_metadata_bytes(relative, payload)
        if findings:
            categories = sorted({finding.category for finding in findings})
            raise BuildError(
                f"generated public evidence audit failed: {relative}: {','.join(categories)}"
            )
    return outputs


def run(*, check: bool, final_validation: bool | None = None) -> None:
    outputs = expected_outputs(final_validation=final_validation)
    drift = []
    for path, payload in outputs.items():
        if check:
            relative = path.relative_to(REPO_ROOT).as_posix()
            if not _public_ref_exists(relative) or _read_public_ref(relative) != payload:
                drift.append(relative)
        else:
            relative = path.relative_to(REPO_ROOT).as_posix()
            safety.write_repository_file(relative, payload)
    if drift:
        raise BuildError("S03-P3 evidence drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--pending", action="store_true", help="force pending receipt projection")
    args = parser.parse_args()
    try:
        run(check=args.check, final_validation=False if args.pending else None)
    except (BuildError, safety.SafetyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS" if args.check else "UPDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
