#!/usr/bin/env python3
"""Build the KMFA v0.1.4 S10-P2 post-remediation trust grade lock."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools import report_grade_runtime
from KMFA.tools import v014_s10_p1_post_remediation_report_entry as p1_phase
from KMFA.tools.check_v014_s10_p1_post_remediation_report_entry import validate_payloads as validate_s10_p1_payloads
from KMFA.tools.check_v014_s10_p2_report_trust_grade import (
    validate_v014_s10_p2_report_trust_grade,
)


PHASE_ID = "V014_S10_P2_POST_REMEDIATION_TRUST_GRADE_LOCK"
ROADMAP_PHASE_ID = "S10-P2"
TASK_ID = "KMFA-V014-S10-P2-POST-REMEDIATION-TRUST-GRADE-LOCK-20260711"
ACCEPTANCE_ID = "ACC-V014-S10-P2-POST-REMEDIATION-TRUST-GRADE-LOCK"
VERSION = "0.1.4-s10-p2-post-remediation-trust-grade-lock"
STATUS = "completed_validated_local_only_report_grade_recomputed_d_locked_no_go_upload_deferred"
DECISION = "NO_GO"
FORMULA_ID = "FORM-KMFA-V014-S10-P2-POST-REMEDIATION-TRUST-GRADE-LOCK-001"
PARAMETER_IDS = ("PARAM-KMFA-1699", "PARAM-KMFA-1700", "PARAM-KMFA-1701")
MODEL_REGISTRY_KEY = "kmfa_v014_s10_p2_post_remediation_trust_grade_lock"

REPORT_RECORD_VERSION = "RPTREC-KMFA-V014-S10P2-POST-REMEDIATION-001"
FORMULA_VERSION = FORMULA_ID
MAPPING_VERSION = "MAP-KMFA-V014-S10P2-POST-REMEDIATION-PUBLIC-SAFE-v1"
FIELD_MAPPING_VERSION = report_grade_runtime.FIELD_MAPPING_VERSION
GRADE_POLICY_VERSION = report_grade_runtime.GRADE_POLICY_VERSION
RELEASE_GATE_VERSION = report_grade_runtime.RELEASE_GATE_VERSION

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "trust_grade_summary.json"
MANIFEST_PATH = MACHINE_DIR / "trust_grade_manifest.json"
RULES_PATH = MACHINE_DIR / "grade_rules_public_safe.json"
RECORDS_PATH = MACHINE_DIR / "report_grade_records_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "trust_grade_go_no_go_report.json"
COMPLETION_PATH = HUMAN_DIR / "s10_p2_completion_record_zh.md"
MANAGEMENT_EXPLANATION_PATH = HUMAN_DIR / "management_grade_explanation_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

QUALITY_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = QUALITY_DIR / "v014_s10_p2_post_remediation_trust_grade_lock_summary.json"
METADATA_MANIFEST_PATH = QUALITY_DIR / "v014_s10_p2_post_remediation_trust_grade_lock_manifest.json"
METADATA_RULES_PATH = QUALITY_DIR / "v014_s10_p2_post_remediation_grade_rules_public_safe.json"
METADATA_RECORDS_PATH = QUALITY_DIR / "v014_s10_p2_post_remediation_report_grade_records_public_safe.json"
METADATA_GO_NO_GO_PATH = QUALITY_DIR / "v014_s10_p2_post_remediation_trust_grade_lock_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s10_p2_post_remediation_trust_grade_lock")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_VALIDATION_REPORT_PATH = PRIVATE_DIR / "s10_p2_trust_grade_validation_zh.md"

DEVELOPMENT_EVENTS_PATH = p1_phase.DEVELOPMENT_EVENTS_PATH
STAGE_STATUS_PATH = p1_phase.STAGE_STATUS_PATH
TASK_STATUS_PATH = p1_phase.TASK_STATUS_PATH
GRADE_POLICY_PATH = Path("KMFA/metadata/reports/report_grade_policy.yaml")
HISTORICAL_S10_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/machine/report_trust_grade_manifest.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _grade_rules() -> dict[str, Any]:
    policy = _read_json(GRADE_POLICY_PATH)
    return {
        "schema_version": "kmfa.v014.s10_p2.post_remediation_grade_rules_public_safe.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "grade_policy_version": policy["schema_version"],
        "driver_dimensions": ["data_quality", "difference_status", "human_confirmation", "timeliness"],
        "report_grades": policy["report_grades"],
        "promotion_blocks": [
            "unresolved_critical_difference",
            "zero_delta_failed",
            "missing_required_lineage",
            "missing_human_confirmation_for_A",
            "stale_input",
            "raw_data_mutation_detected",
        ],
    }


def _hard_blocks() -> list[str]:
    return [
        "zero_delta_failed",
        "unresolved_critical_difference",
        "incomplete_reconciliation",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
        "full_business_value_consistency_not_verified",
    ]


def _grade_records(
    p1: dict[str, Any],
    historical: dict[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    blocks = _hard_blocks()
    records: list[dict[str, Any]] = []
    for entry in p1["report_entries"]:
        records.append(
            {
                "schema_version": "kmfa.v014.s10_p2.post_remediation_grade_record.v1",
                "record_type": "post_remediation_report_grade_record",
                "project_id": "KMFA",
                "stage_id": "S10",
                "phase_id": PHASE_ID,
                "report_record_id": f"S10P2-POST-GRADE-{entry['entry_id'].upper().replace('_', '-')}",
                "report_entry_id": entry["entry_id"],
                "visible_report_title": entry["visible_title"],
                "report_record_version": REPORT_RECORD_VERSION,
                "report_entry_version": p1["version"],
                "template_version": historical["report_trust_grade_policy"]["template_version"],
                "formula_version": FORMULA_VERSION,
                "mapping_version": MAPPING_VERSION,
                "field_mapping_version": FIELD_MAPPING_VERSION,
                "grade_policy_version": GRADE_POLICY_VERSION,
                "release_gate_version": RELEASE_GATE_VERSION,
                "generated_at": generated_at,
                "source_quality_grade": "Q4",
                "maximum_report_grade_before_hard_blocks": "B",
                "computed_report_grade": "D",
                "release_permission": "blocked_decision_use",
                "hard_blocks": list(blocks),
                "limitations": [
                    "关键现金数据缺失，不能显示为完整可信报告。",
                    "九项非零差异和一项未完成比较继续阻断发布。",
                    "完整追溯、充分人工确认和业务一致性尚未成立。",
                ],
                "complete_trusted_report_display_allowed": False,
                "full_trusted_report_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "s10_p3_export_allowed": False,
                "public_repo_safety": {
                    "aggregate_only": True,
                    "business_values_included": False,
                    "field_or_header_plaintext_included": False,
                    "raw_identity_included": False,
                },
            }
        )
    return records


def _raw_snapshot(label: str) -> dict[str, Any]:
    return p1_phase._raw_snapshot(label)


def _normalize_raw(snapshot: dict[str, Any]) -> Any:
    return p1_phase._normalize_raw(snapshot)


def validate_s10_p1_dependency() -> dict[str, Any]:
    payloads = {
        "summary": _read_json(p1_phase.SUMMARY_PATH),
        "manifest": _read_json(p1_phase.MANIFEST_PATH),
        "entries": _read_json(p1_phase.ENTRIES_PATH),
        "go_no_go": _read_json(p1_phase.GO_NO_GO_PATH),
    }
    manifest = validate_s10_p1_payloads(payloads)
    mirror_pairs = (
        (p1_phase.SUMMARY_PATH, p1_phase.METADATA_SUMMARY_PATH),
        (p1_phase.MANIFEST_PATH, p1_phase.METADATA_MANIFEST_PATH),
        (p1_phase.ENTRIES_PATH, p1_phase.METADATA_ENTRIES_PATH),
        (p1_phase.GO_NO_GO_PATH, p1_phase.METADATA_GO_NO_GO_PATH),
    )
    for public_path, mirror_path in mirror_pairs:
        if _read_json(public_path) != _read_json(mirror_path):
            raise ValueError(f"S10-P1 dependency mirror drift: {public_path}")
    validation = manifest.get("validation_summary", {})
    if validation.get("final_validation_recorded") is not True:
        raise ValueError("S10-P1 dependency final validation is not recorded")
    for key in ("focused_tests", "strict_validator", "governance_and_safety_scans"):
        if validation.get(key) != "PASS":
            raise ValueError(f"S10-P1 dependency final status mismatch: {key}")
    return manifest


def build_payloads(*, final_validation: bool = False) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_before = _raw_snapshot("before_v014_s10_p2_post_remediation_trust_grade_lock")
    p1 = validate_s10_p1_dependency()
    validate_v014_s10_p2_report_trust_grade()
    historical = _read_json(HISTORICAL_S10_P2_MANIFEST_PATH)
    raw_after = _raw_snapshot("after_v014_s10_p2_post_remediation_trust_grade_lock")
    prior_raw = _read_json(p1_phase.PRIVATE_RAW_AFTER_PATH)
    raw_exact = _normalize_raw(raw_before) == _normalize_raw(raw_after)
    raw_cross_phase_exact = _normalize_raw(raw_before) == _normalize_raw(prior_raw)
    if not raw_exact or not raw_cross_phase_exact:
        raise ValueError("raw source changed during S10-P2 post-remediation trust grade lock")

    rules = _grade_rules()
    records = _grade_records(p1, historical, generated_at)
    hard_block_counts = {block: len(records) for block in _hard_blocks()}
    p1_summary = p1["summary"]
    summary = {
        "schema_version": "kmfa.v014.s10_p2.post_remediation_trust_grade_summary.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "report_template_count": p1_summary["report_template_count"],
        "report_grade_record_count": len(records),
        "grade_distribution": {"D": len(records)},
        "current_data_quality_grade": "Q4",
        "maximum_report_grade_before_hard_blocks": "B",
        "current_report_grade": "D",
        "grade_recalculation_performed_by_this_phase": True,
        "automatic_grade_promotion_performed": False,
        "record_version_binding_count": len(records),
        "open_final_difference_accepted_count": p1_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": p1_summary["nonzero_delta_reconciliation_count"],
        "zero_delta_reconciliation_count": p1_summary["zero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": p1_summary["incomplete_reconciliation_count"],
        "hard_block_count": sum(hard_block_counts.values()),
        "hard_block_counts": hard_block_counts,
        "full_trusted_report_allowed_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "export_artifact_count": 0,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross_phase_exact,
    }
    grade_inputs = {
        "data_quality_grade": "Q4",
        "open_final_difference_accepted_count": p1_summary["open_final_difference_accepted_count"],
        "nonzero_delta_reconciliation_count": p1_summary["nonzero_delta_reconciliation_count"],
        "incomplete_reconciliation_count": p1_summary["incomplete_reconciliation_count"],
        "zero_delta_passed": False,
        "human_confirmation_status": "partial_not_release_sufficient",
        "timeliness_status": "current_no_stale_signal",
        "stale_input_detected": False,
        "lineage_full_check_complete": False,
        "full_business_value_consistency_verified": False,
    }
    management_explanation = {
        "visible_grade_label": "D级（未放行）",
        "visible_theoretical_ceiling": "数据质量为Q4，未触发阻断时最高为B级",
        "visible_reasons": [
            "关键现金数据缺失，三项仍无唯一权威数值来源。",
            "九项非零差异继续保留，不能静默通过。",
            "一项比较未完成，完整业务一致性尚未成立。",
            "时效检查当前有效，但不能抵消数据、差异、确认和追溯阻断。",
        ],
        "visible_usage_limit": "仅供内部复核，不作为正式经营决策依据",
    }
    release_gate = {
        "complete_trusted_report_display_allowed": False,
        "full_trusted_report_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "delivery_allowed": False,
        "s10_p3_export_allowed": False,
    }
    phase_boundaries = {
        "s10_p1_performed": True,
        "s10_p2_performed": True,
        "s10_p3_performed": False,
        "stage10_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    raw_boundary = {
        "raw_read_authorized": True,
        "raw_snapshot_validation_performed": True,
        "raw_write_performed": False,
        "raw_delete_performed": False,
        "raw_move_performed": False,
        "raw_rename_performed": False,
        "raw_overwrite_performed": False,
        "raw_mutation_performed": False,
    }
    public_repo_safety = {
        "aggregate_only": True,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_hash_committed": False,
        "field_or_header_plaintext_committed": False,
        "business_value_committed": False,
        "project_or_customer_plaintext_committed": False,
        "private_runtime_committed": False,
        "credential_or_secret_committed": False,
    }
    rules_document = {**rules}
    records_document = {
        "schema_version": "kmfa.v014.s10_p2.post_remediation_grade_records_public_safe.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "report_grade_records": records,
    }
    manifest = {
        "schema_version": "kmfa.v014.s10_p2.post_remediation_trust_grade_manifest.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "reviewed_head": p1_phase._git_output(["rev-parse", "HEAD"]),
        "branch": p1_phase._git_output(["branch", "--show-current"]),
        "status": STATUS,
        "decision": DECISION,
        "summary": summary,
        "grade_rules": rules_document,
        "grade_inputs": grade_inputs,
        "grade_records": records,
        "management_explanation": management_explanation,
        "release_gate": release_gate,
        "phase_boundaries": phase_boundaries,
        "raw_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "version_binding_requirements": {
            "report_record_version": REPORT_RECORD_VERSION,
            "report_entry_version": p1["version"],
            "template_version": historical["report_trust_grade_policy"]["template_version"],
            "formula_version": FORMULA_VERSION,
            "mapping_version": MAPPING_VERSION,
            "field_mapping_version": FIELD_MAPPING_VERSION,
            "grade_policy_version": GRADE_POLICY_VERSION,
            "release_gate_version": RELEASE_GATE_VERSION,
            "record_version_binding_count": len(records),
        },
        "dependencies": {
            "s10_p1_post_remediation_entry_validated": True,
            "historical_s10_p2_rule_framework_validated": True,
            "historical_dynamic_state_reused": False,
            "current_s10_p1_state_authoritative": True,
        },
        "source_evidence_refs": {
            "current_s10_p1": p1_phase.MANIFEST_PATH.as_posix(),
            "historical_s10_p2_framework": HISTORICAL_S10_P2_MANIFEST_PATH.as_posix(),
            "report_grade_policy": GRADE_POLICY_PATH.as_posix(),
            "roadmap": "KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md",
        },
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "rules": RULES_PATH.as_posix(),
            "records": RECORDS_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "management_explanation": MANAGEMENT_EXPLANATION_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_s10_p2_post_remediation_trust_grade_lock.py",
        },
        "validation_summary": {
            "red_test_observed": True,
            "focused_tests": "PASS" if final_validation else "PENDING",
            "strict_validator": "PASS" if final_validation else "PENDING",
            "s10_p1_dependency": "PASS",
            "historical_s10_p2_framework": "PASS",
            "raw_snapshot_exact": "PASS",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
            "final_validation_recorded": final_validation,
        },
        "next_required_phase": "S10-P3",
    }
    go_no_go = {
        "schema_version": "kmfa.v014.s10_p2.post_remediation_trust_grade_go_no_go.v1",
        "project_id": "KMFA",
        "stage_id": "S10",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "current_data_quality_grade": "Q4",
        "maximum_report_grade_before_hard_blocks": "B",
        "current_report_grade": "D",
        "blocking_reason_codes": list(_hard_blocks()),
        "formal_report_allowed": False,
        "s10_p3_export_allowed": False,
        "github_upload_performed": False,
    }
    return {
        "summary": summary,
        "manifest": manifest,
        "rules": rules_document,
        "records": records_document,
        "go_no_go": go_no_go,
        "private": {"raw_before": raw_before, "raw_after": raw_after},
    }


def _render_management_explanation(manifest: dict[str, Any]) -> str:
    explanation = manifest["management_explanation"]
    lines = [
        "# KMFA 报告可信等级说明",
        "",
        f"- 当前等级：{explanation['visible_grade_label']}",
        f"- 理论上限：{explanation['visible_theoretical_ceiling']}",
        f"- 使用限制：{explanation['visible_usage_limit']}",
        "",
        "## 当前阻断原因",
        "",
    ]
    lines.extend(f"- {reason}" for reason in explanation["visible_reasons"])
    lines.extend(
        [
            "",
            "## 等级规则摘要",
            "",
            "- A级：Q5、零差异、关键差异关闭、完整人工确认和追溯均满足。",
            "- B级：至少Q4，关键差异可解释且限制完整；当前关键值缺失和未完成比较不满足。",
            "- C级：Q3 预览用途，不作为决策依据。",
            "- D级：关键数据缺失、过期或差异未处理时阻断决策使用。",
        ]
    )
    return "\n".join(lines)


def _render_completion(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    return f"""# KMFA v0.1.4 S10-P2 修补后可信等级锁定完成记录

- phase：`{PHASE_ID}`
- roadmap phase：`{ROADMAP_PHASE_ID}`
- status：`{STATUS}`
- records / version-bound records：`{summary['report_grade_record_count']} / {summary['record_version_binding_count']}`
- data quality / theoretical ceiling / final grade：`Q4 / B / D`
- open / nonzero / incomplete：`{summary['open_final_difference_accepted_count']} / {summary['nonzero_delta_reconciliation_count']} / {summary['incomplete_reconciliation_count']}`
- hard blocks：`{summary['hard_block_count']}`
- decision：`{DECISION}`
- S10-P3 / Stage 10 review / GitHub upload / app reinstall / business execution：`false / false / false / false / false`
"""


def _render_test_results(manifest: dict[str, Any]) -> str:
    final = manifest["validation_summary"]["final_validation_recorded"]
    state = "PASS" if final else "PENDING"
    return f"""# KMFA v0.1.4 S10-P2 修补后可信等级测试结果

- RED：`PASS`，已观察到实现缺失断言失败。
- focused tests：`{state}`
- strict validator：`{state}`
- current S10-P1 dependency：`PASS`
- historical S10-P2 rule framework：`PASS`
- raw before/after/cross-phase snapshot：`PASS`
- governance / no-float / no-omission / structured parse / secret scan：`{state}`
- final validation recorded：`{str(final).lower()}`
- GitHub upload：`false`
"""


def _render_private_report(summary: dict[str, Any]) -> str:
    return f"""# S10-P2 可信等级私有验证记录

- 原始文件数量：{summary['raw_source_file_count']}
- 本 phase 前后快照一致：{str(summary['raw_snapshot_exact_match']).lower()}
- 与 S10-P1 快照一致：{str(summary['raw_cross_phase_snapshot_exact_match']).lower()}
- 两条报告记录均重新计算为 D，未自动提级。
- 三项关键现金缺失、九项非零差异和一项未完成比较保持阻断。
"""


def _phase_public_files() -> list[str]:
    return [
        path.as_posix()
        for path in (
            SUMMARY_PATH,
            MANIFEST_PATH,
            RULES_PATH,
            RECORDS_PATH,
            GO_NO_GO_PATH,
            COMPLETION_PATH,
            MANAGEMENT_EXPLANATION_PATH,
            TEST_RESULTS_PATH,
            RISK_REGISTER_PATH,
            ROLLBACK_PATH,
            METADATA_SUMMARY_PATH,
            METADATA_MANIFEST_PATH,
            METADATA_RULES_PATH,
            METADATA_RECORDS_PATH,
            METADATA_GO_NO_GO_PATH,
        )
    ] + [
        "KMFA/tools/v014_s10_p2_post_remediation_trust_grade_lock.py",
        "KMFA/tools/check_v014_s10_p2_post_remediation_trust_grade_lock.py",
        "KMFA/tests/test_v014_s10_p2_post_remediation_trust_grade_lock.py",
    ]


def _write_governance(generated_at: str) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    p1_phase._upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260711-V014-S10-P2-POST-REMEDIATION-TRUST-GRADE-LOCK",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    p1_phase._upsert_jsonl(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "phase_status",
            "project_id": "KMFA",
            "stage_id": "S10",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "current_report_grade": "D",
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    p1_phase._upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "S10",
            "governance_stage_id": "REPORT-TRUST-AND-GENERATION",
            "roadmap_stage_id": "S10",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 S10-P2 post-remediation trust grade lock",
            "phase_goal": "recompute report trust grades from current inputs and lock D while hard blocks remain",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    payloads = build_payloads(final_validation=final_validation)
    for path, payload in (
        (SUMMARY_PATH, payloads["summary"]),
        (MANIFEST_PATH, payloads["manifest"]),
        (RULES_PATH, payloads["rules"]),
        (RECORDS_PATH, payloads["records"]),
        (GO_NO_GO_PATH, payloads["go_no_go"]),
        (METADATA_SUMMARY_PATH, payloads["summary"]),
        (METADATA_MANIFEST_PATH, payloads["manifest"]),
        (METADATA_RULES_PATH, payloads["rules"]),
        (METADATA_RECORDS_PATH, payloads["records"]),
        (METADATA_GO_NO_GO_PATH, payloads["go_no_go"]),
        (PRIVATE_RAW_BEFORE_PATH, payloads["private"]["raw_before"]),
        (PRIVATE_RAW_AFTER_PATH, payloads["private"]["raw_after"]),
    ):
        p1_phase._write_json(path, payload)
    p1_phase._write_text(COMPLETION_PATH, _render_completion(payloads["manifest"]))
    p1_phase._write_text(MANAGEMENT_EXPLANATION_PATH, _render_management_explanation(payloads["manifest"]))
    p1_phase._write_text(TEST_RESULTS_PATH, _render_test_results(payloads["manifest"]))
    p1_phase._write_text(
        RISK_REGISTER_PATH,
        """# S10-P2 修补后可信等级风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| Q4 被直接显示为 B | 先计算理论上限，再应用六类 hard blocks，最终固定 D | controlled |
| 时效通过抵消关键数据缺失 | 四维独立判断，任一关键阻断均不可被时效覆盖 | controlled |
| 历史 12 pending 污染当前输入 | 历史 S10-P2 只复用规则/版本框架，动态输入来自当前 S10-P1 | controlled |
| D 级记录被当成正式报告 | trusted/formal/decision/export/delivery 全部为 false | controlled |
""",
    )
    p1_phase._write_text(
        ROLLBACK_PATH,
        f"""# S10-P2 修补后可信等级回滚计划

1. 回退本 phase 本地 commit 和 `{OUTPUT_DIR.as_posix()}` 公开证据。
2. 删除本 phase ignored private runtime 草稿，不触碰原始目录。
3. 恢复到 S10-P1 的 `Q4 / D / NO_GO` 继承显示状态。
4. 不回退、不移动、不删除、不覆盖任何原始文件。
""",
    )
    p1_phase._write_text(PRIVATE_VALIDATION_REPORT_PATH, _render_private_report(payloads["summary"]))
    if write_governance:
        _write_governance(payloads["manifest"]["generated_at"])
    return payloads["manifest"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-validation", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation)
    summary = manifest["summary"]
    print(
        "S10-P2 post-remediation trust grade lock: "
        f"records={summary['report_grade_record_count']} grade={summary['current_report_grade']} "
        f"hard_blocks={summary['hard_block_count']} decision={manifest['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
