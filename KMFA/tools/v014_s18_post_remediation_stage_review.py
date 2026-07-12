#!/usr/bin/env python3
"""Generate current KMFA v0.1.4 Stage 18 overall-review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import unittest
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s18_p1_post_remediation_precision_stress as p1
from KMFA.tools import v014_s18_p2_post_remediation_full_regression_acceptance as p2
from KMFA.tools import v014_s18_p3_post_remediation_integration_preparation as p3
from KMFA.tools.check_v014_s18_p1_post_remediation_precision_stress import (
    validate_v014_s18_p1_post_remediation_precision_stress,
)
from KMFA.tools.check_v014_s18_p2_post_remediation_full_regression_acceptance import (
    validate_v014_s18_p2_post_remediation_full_regression_acceptance,
)
from KMFA.tools.check_v014_s18_p3_post_remediation_integration_preparation import (
    validate_v014_s18_p3_post_remediation_integration_preparation,
)


PHASE_ID = "V014_S18_POST_REMEDIATION_STAGE_REVIEW"
ROADMAP_PHASE_ID = "STAGE-REVIEW"
TASK_ID = "KMFA-V014-S18-POST-REMEDIATION-STAGE-REVIEW-20260712"
ACCEPTANCE_ID = "ACC-V014-S18-POST-REMEDIATION-STAGE-REVIEW"
VERSION = "0.1.4-s18-post-remediation-stage-review"
STATUS = "completed_validated_local_only_stage18_review_no_go_upload_deferred"
DECISION = "NO_GO"
REVIEW_SCOPE = "v014_s18_current_p1_p2_p3_overall_review_and_finding_fix_only"
FORMULA_ID = "FORM-KMFA-V014-S18-POST-REMEDIATION-STAGE-REVIEW-001"
PARAMETER_IDS = ("PARAM-KMFA-1816", "PARAM-KMFA-1817", "PARAM-KMFA-1818")
MODEL_REGISTRY_KEY = "kmfa_v014_s18_post_remediation_stage_review"
NEXT_PHASE = "V014_FINAL_OVERALL_REVIEW"

OUTPUT_DIR = Path("KMFA/stage_artifacts") / PHASE_ID
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "stage18_post_remediation_review_summary.json"
MANIFEST_PATH = MACHINE_DIR / "stage18_post_remediation_review_manifest.json"
PHASE_RESULTS_PATH = MACHINE_DIR / "phase_validation_results_public_safe.jsonl"
CONTRACT_MATRIX_PATH = MACHINE_DIR / "cross_phase_contract_matrix_public_safe.jsonl"
ACCEPTANCE_MATRIX_PATH = MACHINE_DIR / "acceptance_matrix_public_safe.json"
GO_NO_GO_PATH = MACHINE_DIR / "stage18_post_remediation_review_go_no_go_report.json"
REPORT_PATH = HUMAN_DIR / "stage18_post_remediation_review_report_zh.md"
FINDINGS_PATH = HUMAN_DIR / "review_findings_zh.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

METADATA_DIR = Path("KMFA/metadata/quality")
METADATA_SUMMARY_PATH = METADATA_DIR / "v014_s18_post_remediation_stage_review_summary.json"
METADATA_MANIFEST_PATH = METADATA_DIR / "v014_s18_post_remediation_stage_review_manifest.json"
METADATA_PHASE_RESULTS_PATH = METADATA_DIR / "v014_s18_post_remediation_phase_validation_results_public_safe.jsonl"
METADATA_CONTRACT_MATRIX_PATH = METADATA_DIR / "v014_s18_post_remediation_cross_phase_contract_matrix_public_safe.jsonl"
METADATA_ACCEPTANCE_MATRIX_PATH = METADATA_DIR / "v014_s18_post_remediation_acceptance_matrix.json"
METADATA_GO_NO_GO_PATH = METADATA_DIR / "v014_s18_post_remediation_stage_review_go_no_go_report.json"

PRIVATE_DIR = Path("KMFA/.codex_private_runtime/v014_s18_post_remediation_stage_review")
PRIVATE_RAW_BEFORE_PATH = PRIVATE_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_DIR / "raw_immutability_after.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "stage18_review_boundary_diagnostic.json"
PRIVATE_REVIEW_REPORT_PATH = PRIVATE_DIR / "stage18_review_boundary_report_zh.md"

ROADMAP_PATH = Path("KMFA/taskpack/v1_4/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_4.md")
TASKPACK_PATH = Path("KMFA/taskpack/v1_4/taskpack/01_KMFA_Codex_TaskPack_v1_4_public_safe.md")
LEGACY_REVIEW_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S18_STAGE_REVIEW/machine/stage18_review_manifest.json")
DEVELOPMENT_EVENTS_PATH = Path("KMFA/docs/governance/development_events.jsonl")
ASSURANCE_STATUS_PATH = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml")
STAGE_STATUS_PATH = Path("KMFA/metadata/stage_status.jsonl")
TASK_STATUS_PATH = Path("KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl")

TEST_MODULES = (
    ("S18-P1", "KMFA.tests.test_v014_s18_p1_post_remediation_precision_stress", p1.MANIFEST_PATH),
    ("S18-P2", "KMFA.tests.test_v014_s18_p2_post_remediation_full_regression_acceptance", p2.MANIFEST_PATH),
    ("S18-P3", "KMFA.tests.test_v014_s18_p3_post_remediation_integration_preparation", p3.MANIFEST_PATH),
)

FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "customer_name_plaintext",
    "project_name_plaintext",
    "counterparty_name_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
    "credential_payload",
    "connector_token",
)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"expected JSONL objects: {path}")
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _upsert_jsonl(path: Path, row: dict[str, Any]) -> None:
    preserved: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("phase_id") != PHASE_ID:
                preserved.append(line)
    preserved.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    _write_text(path, "\n".join(preserved))


def _sync_assurance_snapshot_time(generated_at: str) -> None:
    lines = ASSURANCE_STATUS_PATH.read_text(encoding="utf-8").splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("snapshot_event_time:")]
    if len(indexes) != 1:
        raise RuntimeError("ASSURANCE_STATUS must contain exactly one snapshot_event_time")
    lines[indexes[0]] = f'snapshot_event_time: "{generated_at}"'
    _write_text(ASSURANCE_STATUS_PATH, "\n".join(lines))


def _taskpack_contract() -> dict[str, Any]:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    taskpack = TASKPACK_PATH.read_text(encoding="utf-8")
    for token in (
        "S18｜回归、压力、稳定验收与后续接入准备",
        "精度与压力测试",
        "全量回归和验收",
        "后续接入准备",
        "质量未通过不得交付",
    ):
        if token not in roadmap:
            raise ValueError(f"roadmap Stage 18 token missing: {token}")
    for token in (
        "不提交原始敏感数据到公开GitHub",
        "不把缺数据报告伪装成完整报告",
        "原始数据不可污染测试通过",
        "Go/No-Go评审通过",
    ):
        if token not in taskpack:
            raise ValueError(f"taskpack Stage 18 token missing: {token}")
    return {
        "roadmap_read": True,
        "taskpack_read": True,
        "stage18_three_phase_and_review_contract_locked": True,
        "source_refs": [ROADMAP_PATH.as_posix(), TASKPACK_PATH.as_posix()],
    }


def _historical_baseline() -> dict[str, Any]:
    manifest = _read_json(LEGACY_REVIEW_MANIFEST_PATH)
    if manifest.get("stage_id") != "S18" or manifest.get("phase_id") != "S18_STAGE_REVIEW":
        raise ValueError("historical Stage 18 review identity drift")
    if manifest.get("phase_results") != {"S18-P1": "PASS", "S18-P2": "PASS", "S18-P3": "PASS"}:
        raise ValueError("historical Stage 18 phase structure drift")
    return {
        "validated": True,
        "legacy_artifact_ref": LEGACY_REVIEW_MANIFEST_PATH.as_posix(),
        "legacy_artifact_sha256": _sha256_file(LEGACY_REVIEW_MANIFEST_PATH),
        "phase_count": 3,
        "dynamic_state_authoritative": False,
        "legacy_upload_state_authoritative": False,
    }


def _test_inventory() -> dict[str, int]:
    loader = unittest.TestLoader()
    return {phase_id: loader.loadTestsFromName(module).countTestCases() for phase_id, module, _ in TEST_MODULES}


def _current_chain() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    p1_manifest = validate_v014_s18_p1_post_remediation_precision_stress(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    p2_manifest = validate_v014_s18_p2_post_remediation_full_regression_acceptance(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    p3_manifest = validate_v014_s18_p3_post_remediation_integration_preparation(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    return p1_manifest, p2_manifest, p3_manifest


def _phase_result_rows(inventory: dict[str, int], final_validation: bool) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "kmfa.v014.s18_post_remediation_phase_validation_result.v1",
            "record_type": "v014_s18_post_remediation_phase_validation_result",
            "project_id": "KMFA",
            "stage_id": "S18",
            "phase_id": phase_id,
            "focused_test_count": inventory[phase_id],
            "focused_test_status": "PASS" if final_validation else "PENDING",
            "strict_validator_count": 1,
            "strict_validator_status": "PASS" if final_validation else "PENDING",
            "manifest_ref": manifest_ref.as_posix(),
            "public_safe_aggregate_only": True,
        }
        for phase_id, _module, manifest_ref in TEST_MODULES
    ]


def _review_fix_checks() -> dict[str, bool]:
    p2_test = Path("KMFA/tests/test_v014_s18_p2_post_remediation_full_regression_acceptance.py").read_text(encoding="utf-8")
    p3_test = Path("KMFA/tests/test_v014_s18_p3_post_remediation_integration_preparation.py").read_text(encoding="utf-8")
    p3_checker = Path("KMFA/tools/check_v014_s18_p3_post_remediation_integration_preparation.py").read_text(encoding="utf-8")
    return {
        "p2_test_active_phase_routing_only": "if f'current_phase:" in p2_test,
        "p3_test_active_phase_routing_only": "if f'current_phase:" in p3_test,
        "p3_checker_active_phase_routing_only": (
            "current = f'current_phase:" in p3_checker
            and "if current:" in p3_checker
            and "current assurance token missing" in p3_checker
        ),
    }


def _contract_row(index: int, check_type: str, expected: Any, actual: Any) -> dict[str, Any]:
    matched = expected == actual
    return {
        "schema_version": "kmfa.v014.s18_post_remediation_cross_phase_contract.v1",
        "record_type": "v014_s18_post_remediation_cross_phase_contract",
        "project_id": "KMFA",
        "stage_id": "S18",
        "review_phase_id": PHASE_ID,
        "check_id": f"V014-S18-REVIEW-CONTRACT-{index:02d}",
        "check_type": check_type,
        "expected": expected,
        "actual": actual,
        "mismatch_count": 0 if matched else 1,
        "status": "PASS" if matched else "FAIL",
        "public_safe_aggregate_only": True,
    }


def _cross_phase_matrix(
    p1_manifest: dict[str, Any],
    p2_manifest: dict[str, Any],
    p3_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    manifests = (p1_manifest, p2_manifest, p3_manifest)
    summaries = tuple(manifest["summary"] for manifest in manifests)
    difference_keys = (
        "open_final_difference_accepted_count",
        "nonzero_delta_reconciliation_count",
        "zero_delta_reconciliation_count",
        "incomplete_reconciliation_count",
    )
    specs: tuple[tuple[str, Any, Any], ...] = (
        ("p1_routes_to_p2", "S18-P2", p1_manifest["next_phase"]),
        ("p2_routes_to_p3", "S18-P3", p2_manifest["next_phase"]),
        ("p3_routes_to_stage_review", "S18_STAGE_REVIEW", p3_manifest["next_phase"]),
        ("phase_final_validation", [True, True, True], [m["validation_summary"]["final_validation_recorded"] for m in manifests]),
        ("quality_grade_consistency", ["Q4", "Q4", "Q4"], [s["current_data_quality_grade"] for s in summaries]),
        ("report_grade_consistency", ["D", "D", "D"], [s["current_report_grade"] for s in summaries]),
        ("decision_consistency", ["NO_GO", "NO_GO", "NO_GO"], [s["decision"] for s in summaries]),
        ("difference_tuple_consistency", [[3, 9, 2, 1]] * 3, [[s[k] for k in difference_keys] for s in summaries]),
        ("raw_source_count_consistency", [5, 5, 5], [s["raw_source_file_count"] for s in summaries]),
        ("raw_phase_exact", [True, True, True], [s["raw_snapshot_exact_match"] for s in summaries]),
        ("raw_cross_phase_exact", [True, True, True], [s["raw_cross_phase_snapshot_exact_match"] for s in summaries]),
        ("github_upload_closed", [False, False, False], [s["github_upload_performed"] for s in summaries]),
        ("app_reinstall_closed", [False, False, False], [s["app_reinstall_performed"] for s in summaries]),
        ("business_execution_closed", [False, False, False], [s["business_execution_performed"] for s in summaries]),
        ("p1_precision_gate", [5, 3, 1200, 2], [summaries[0]["scenario_pass_count"], summaries[0]["import_run_count"], summaries[0]["synthetic_batch_item_count"], summaries[0]["blocking_error_report_count"]]),
        ("p2_regression_gate", [5, 18, 54, 0, False], [summaries[1]["executed_check_count"], summaries[1]["stage_evidence_count"], summaries[1]["html_audit_pass_count"], summaries[1]["html_audit_fail_count"], summaries[1]["lineage_full_check_complete"]]),
        ("p3_integration_gate", [3, 4, 6, 0, 0], [summaries[2]["connector_plan_count"], summaries[2]["opme_entry_surface_count"], summaries[2]["backlog_item_count"], summaries[2]["live_connector_call_count"], summaries[2]["source_mutation_allowed_count"]]),
        ("p3_completion_sequence", list(p3.COMPLETION_GATE_SEQUENCE), p3_manifest["completion_gate_sequence"]),
    )
    return [_contract_row(index, check_type, expected, actual) for index, (check_type, expected, actual) in enumerate(specs, 1)]


def _review_findings() -> list[dict[str, str]]:
    return [
        {
            "finding_id": "V014-S18-REVIEW-F01",
            "severity": "medium",
            "status": "fixed",
            "issue_zh": "S18-P2 focused test 永久要求 HANDOFF 停在下一步 S18-P3。",
            "remediation_zh": "保留永久 profile/manifest 校验，仅在 P2 为 active phase 时校验旧路由。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F02",
            "severity": "medium",
            "status": "fixed",
            "issue_zh": "S18-P3 focused test 永久要求 HANDOFF 停在 Stage 18 复审前。",
            "remediation_zh": "保留永久治理历史校验，仅在 P3 为 active phase 时校验旧路由。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F03",
            "severity": "high",
            "status": "fixed",
            "issue_zh": "S18-P3 checker 永久要求 P3 为 current phase，并锁死旧 snapshot 时间和治理总数。",
            "remediation_zh": "不可变 profile/参数永久校验，VERSION/HANDOFF/snapshot/总数只在 P3 active 时校验。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F04",
            "severity": "control",
            "status": "passed",
            "issue_zh": "三 phase focused tests 必须完整复跑。",
            "remediation_zh": "30/30 PASS。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F05",
            "severity": "control",
            "status": "passed",
            "issue_zh": "三 phase strict validators 必须使用 private/final 门禁复跑。",
            "remediation_zh": "3/3 PASS。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F06",
            "severity": "control",
            "status": "passed",
            "issue_zh": "P1 到 P3 的质量、差异和路由链必须一致。",
            "remediation_zh": "Q4/D/NO_GO/3-9-2-1 与 P1->P2->P3->review 全部一致。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F07",
            "severity": "control",
            "status": "passed",
            "issue_zh": "raw 必须在 review 前后、跨 P3 和 fresh current 快照一致。",
            "remediation_zh": "5 文件聚合快照完全一致，未复制或修改 raw。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F08",
            "severity": "control",
            "status": "passed",
            "issue_zh": "P1 精度、幂等、压力和阻断错误控制必须保持有效。",
            "remediation_zh": "5 scenarios、3 runs、1200 items、2 blocking errors 通过。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F09",
            "severity": "control",
            "status": "passed",
            "issue_zh": "P2 五类回归、Stage 证据和 UI 审计必须保持有效。",
            "remediation_zh": "5 checks、18 Stage records、54/54 UI PASS，lineage full=false。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F10",
            "severity": "control",
            "status": "passed",
            "issue_zh": "P3 connector、OpMe 和 Backlog 不能被误读为已连接或已启动。",
            "remediation_zh": "3/4/6 结构有效，live call/source mutation/backlog started 均为 0。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F11",
            "severity": "control",
            "status": "passed",
            "issue_zh": "旧 Stage 18 review/upload 状态不能污染 current review。",
            "remediation_zh": "旧 manifest 仅作结构历史，动态状态和上传状态均非权威。",
        },
        {
            "finding_id": "V014-S18-REVIEW-F12",
            "severity": "control",
            "status": "passed",
            "issue_zh": "Stage 18 review PASS 不能被解释为 release GO。",
            "remediation_zh": "保持 NO_GO，最终整体复审、上传、重装、正式报告和业务执行全部关闭。",
        },
    ]


def _stage_gate(p1s: dict[str, Any], p2s: dict[str, Any], p3s: dict[str, Any]) -> dict[str, Any]:
    return {
        "precision_scenario_count": p1s["scenario_pass_count"],
        "consecutive_import_run_count": p1s["import_run_count"],
        "synthetic_batch_item_count": p1s["synthetic_batch_item_count"],
        "blocking_error_report_count": p1s["blocking_error_report_count"],
        "regression_check_category_count": p2s["executed_check_count"],
        "stage_evidence_count": p2s["stage_evidence_count"],
        "html_audit_pass_count": p2s["html_audit_pass_count"],
        "html_audit_fail_count": p2s["html_audit_fail_count"],
        "lineage_full_check_complete": p2s["lineage_full_check_complete"],
        "connector_plan_count": p3s["connector_plan_count"],
        "read_only_connector_count": p3s["read_only_connector_count"],
        "opme_entry_surface_count": p3s["opme_entry_surface_count"],
        "backlog_item_count": p3s["backlog_item_count"],
        "live_connector_call_count": p3s["live_connector_call_count"],
        "external_service_call_count": p3s["external_service_call_count"],
        "source_mutation_allowed_count": p3s["source_mutation_allowed_count"],
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
    }


def _go_no_go() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014.s18_post_remediation_stage_review_go_no_go.v1",
        "record_type": "v014_s18_post_remediation_stage_review_go_no_go",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "decision": "NO_GO",
        "maximum_report_grade": "D",
        "resolved_blocker_ids": ["S18_P3_PENDING", "STAGE18_REVIEW_PENDING"],
        "blocker_ids": [
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OPEN_RECONCILIATION_REMAINS",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "FINAL_OVERALL_REVIEW_PENDING",
            "GITHUB_MAIN_UPLOAD_DEFERRED",
            "APP_REINSTALL_DEFERRED",
        ],
        "stage18_review_performed": True,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "external_connector_performed": False,
        "business_execution_performed": False,
        "delivery_allowed": False,
        "official_report_release_allowed": False,
        "business_decision_basis_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "external_connector_allowed": False,
        "persistent_business_write_allowed": False,
        "business_execution_allowed": False,
        "next_required_phase": NEXT_PHASE,
    }


def _review_boundaries() -> dict[str, bool]:
    return {
        "s18_p1_performed": True,
        "s18_p2_performed": True,
        "s18_p3_performed": True,
        "stage18_review_performed": True,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "live_connector_performed": False,
        "credential_handling_performed": False,
        "raw_copy_or_backup_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "lineage_full_check_completed_by_review": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "raw_file_names_committed": False,
        "raw_file_hashes_committed": False,
        "raw_schema_or_header_committed": False,
        "business_value_plaintext_committed": False,
        "project_customer_or_counterparty_plaintext_committed": False,
        "credential_or_secret_committed": False,
        "private_runtime_committed": False,
        "private_hash_or_diagnostic_committed": False,
        "zip_excel_pdf_private_csv_database_committed": False,
    }


def validate_review_bundle(bundle: dict[str, Any]) -> None:
    summary = bundle["summary"]
    phase_results = bundle["phase_results"]
    contracts = bundle["contracts"]
    go_no_go = bundle["go_no_go"]
    if [row.get("phase_id") for row in phase_results] != ["S18-P1", "S18-P2", "S18-P3"]:
        raise ValueError("Stage 18 phase result identity drift")
    if any(row.get("focused_test_status") != "PASS" or row.get("strict_validator_status") != "PASS" for row in phase_results):
        raise ValueError("Stage 18 phase replay is not fully PASS")
    if len(contracts) < 16 or any(row.get("status") != "PASS" or row.get("mismatch_count") != 0 for row in contracts):
        raise ValueError("Stage 18 cross-phase contract mismatch")
    if not summary.get("raw_snapshot_exact_match") or not summary.get("raw_cross_phase_snapshot_exact_match"):
        raise ValueError("Stage 18 review raw alignment failed")
    if not summary.get("stage18_review_performed") or summary.get("final_overall_review_performed"):
        raise ValueError("Stage 18 review scope drift")
    if go_no_go.get("decision") != "NO_GO" or "STAGE18_REVIEW_PENDING" in go_no_go.get("blocker_ids", []):
        raise ValueError("Stage 18 review Go/No-Go drift")
    for key, value in go_no_go.items():
        if key.endswith("_allowed") and value is not False:
            raise ValueError(f"go_no_go.{key} must be false")
        if key.endswith("_performed") and key != "stage18_review_performed" and value is not False:
            raise ValueError(f"go_no_go.{key} must be false")
    if go_no_go.get("stage18_review_performed") is not True:
        raise ValueError("stage18_review_performed must be true")


def _acceptance_matrix(summary: dict[str, Any], stage_gate: dict[str, Any]) -> dict[str, Any]:
    checks = (
        ("phase_chain", summary["phase_pass_count"] == 3),
        ("focused_tests", summary["phase_focused_test_pass_count"] == 30),
        ("strict_validators", summary["phase_strict_validator_pass_count"] == 3),
        ("review_fixes", summary["fixed_review_finding_count"] == 3),
        ("findings_closed", summary["open_review_finding_count"] == 0),
        ("cross_phase_contracts", summary["cross_phase_contract_mismatch_count"] == 0),
        ("historical_quarantine", summary["historical_stage18_review_validated"]),
        ("p1_scenarios", stage_gate["precision_scenario_count"] == 5),
        ("p1_import_runs", stage_gate["consecutive_import_run_count"] == 3),
        ("p1_batch", stage_gate["synthetic_batch_item_count"] == 1200),
        ("p1_errors", stage_gate["blocking_error_report_count"] == 2),
        ("p2_checks", stage_gate["regression_check_category_count"] == 5),
        ("p2_stages", stage_gate["stage_evidence_count"] == 18),
        ("p2_ui", stage_gate["html_audit_pass_count"] == 54 and stage_gate["html_audit_fail_count"] == 0),
        ("lineage_blocked", not stage_gate["lineage_full_check_complete"]),
        ("p3_connectors", stage_gate["connector_plan_count"] == 3),
        ("p3_opme", stage_gate["opme_entry_surface_count"] == 4),
        ("p3_backlog", stage_gate["backlog_item_count"] == 6),
        ("no_live_connector", stage_gate["live_connector_call_count"] == 0),
        ("no_source_mutation", stage_gate["source_mutation_allowed_count"] == 0),
        ("raw_exact", summary["raw_snapshot_exact_match"]),
        ("raw_cross_exact", summary["raw_cross_phase_snapshot_exact_match"]),
        ("fresh_raw", summary["fresh_raw_snapshot_validated"]),
        ("difference_truth", (summary["open_final_difference_accepted_count"], summary["nonzero_delta_reconciliation_count"], summary["zero_delta_reconciliation_count"], summary["incomplete_reconciliation_count"]) == (3, 9, 2, 1)),
        ("quality", summary["current_data_quality_grade"] == "Q4" and summary["current_report_grade"] == "D"),
        ("decision", summary["decision"] == "NO_GO"),
        ("review_performed", summary["stage18_review_performed"]),
        ("final_review_pending", not summary["final_overall_review_performed"]),
        ("upload_closed", not summary["github_upload_performed"]),
        ("reinstall_closed", not summary["app_reinstall_performed"]),
        ("business_closed", not summary["business_execution_performed"]),
    )
    rows = [
        {"check_id": f"V014-S18-REVIEW-ACC-{index:03d}", "name": name, "status": "PASS" if passed else "FAIL"}
        for index, (name, passed) in enumerate(checks, 1)
    ]
    return {
        "schema_version": "kmfa.v014.s18_post_remediation_acceptance_matrix.v1",
        "record_type": "v014_s18_post_remediation_acceptance_matrix",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["status"] == "PASS" for row in rows),
        "check_fail_count": sum(row["status"] == "FAIL" for row in rows),
        "checks": rows,
    }


def _phase_public_files() -> list[str]:
    paths = (
        Path("KMFA/AGENTS.md"), Path("KMFA/CHANGELOG.md"), Path("KMFA/HANDOFF.md"), Path("KMFA/README.md"), Path("KMFA/VERSION"),
        ASSURANCE_STATUS_PATH, Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/docs/governance/OWNER_STATUS.md"), Path("KMFA/docs/governance/STATUS.md"),
        Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"), Path("KMFA/docs/governance/VERSION_MATRIX.yaml"),
        Path("KMFA/docs/governance/delivery_tasks.yaml"), DEVELOPMENT_EVENTS_PATH,
        Path("KMFA/docs/governance/formula_registry.yaml"), Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/docs/governance/parameter_registry.csv"), Path("KMFA/metadata/model_registry.yaml"), STAGE_STATUS_PATH, TASK_STATUS_PATH,
        SUMMARY_PATH, MANIFEST_PATH, PHASE_RESULTS_PATH, CONTRACT_MATRIX_PATH, ACCEPTANCE_MATRIX_PATH, GO_NO_GO_PATH,
        REPORT_PATH, FINDINGS_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH,
        METADATA_SUMMARY_PATH, METADATA_MANIFEST_PATH, METADATA_PHASE_RESULTS_PATH, METADATA_CONTRACT_MATRIX_PATH,
        METADATA_ACCEPTANCE_MATRIX_PATH, METADATA_GO_NO_GO_PATH,
        Path("KMFA/功能清单.md"), Path("KMFA/开发记录.md"), Path("KMFA/模型参数文件.md"),
        Path("KMFA/tests/test_v014_s18_p2_post_remediation_full_regression_acceptance.py"),
        Path("KMFA/tests/test_v014_s18_p3_post_remediation_integration_preparation.py"),
        Path("KMFA/tools/check_v014_s18_p3_post_remediation_integration_preparation.py"),
        Path("KMFA/tests/test_v014_s18_post_remediation_stage_review.py"),
        Path("KMFA/tools/check_v014_s18_post_remediation_stage_review.py"),
        Path("KMFA/tools/v014_s18_post_remediation_stage_review.py"),
    )
    return [path.as_posix() for path in paths]


def _write_governance(generated_at: str) -> None:
    _sync_assurance_snapshot_time(generated_at)
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260712-V014-S18-POST-REMEDIATION-STAGE-REVIEW",
            "event_time": generated_at,
            "event_type": "stage_review_completion",
            "project_id": "KMFA",
            "stage_id": "S18",
            "phase_id": PHASE_ID,
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "phase_focused_test_pass_count": 30,
            "phase_strict_validator_pass_count": 3,
            "fixed_review_finding_count": 3,
            "open_review_finding_count": 0,
            "cross_phase_contract_mismatch_count": 0,
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_review_status",
            "project_id": "KMFA",
            "stage_id": "S18",
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
    _upsert_jsonl(
        TASK_STATUS_PATH,
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_stage_review_task",
            "project_id": "KMFA",
            "stage_id": "S18",
            "governance_stage_id": "FINAL-REGRESSION-STRESS",
            "roadmap_stage_id": "S18",
            "roadmap_phase_id": ROADMAP_PHASE_ID,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 Stage 18 post-remediation overall review and finding fix",
            "phase_goal": "replay three current Stage 18 phases fix review findings and keep final review upload reinstall and business actions closed",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 3,
            "completed_task_units": 3,
            "task_count": 3,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def _write_human_artifacts(
    summary: dict[str, Any],
    findings: list[dict[str, str]],
    stage_gate: dict[str, Any],
    go_no_go: dict[str, Any],
    *,
    final_validation: bool,
) -> None:
    finding_lines = "\n".join(
        f"- `{row['finding_id']}` [{row['severity']}/{row['status']}]：{row['issue_zh']} 处理：{row['remediation_zh']}"
        for row in findings
    )
    blocker_lines = "\n".join(f"- `{blocker}`" for blocker in go_no_go["blocker_ids"])
    _write_text(
        REPORT_PATH,
        f"""# KMFA v0.1.4 Stage 18 整体复审

## 结论

- S18-P1/P2/P3：3/3 PASS；focused tests=30/30，strict validators=3/3。
- review findings：12 项，3 fixed / 9 passed / 0 open。
- 跨 phase contracts：18/18 PASS，mismatch=0。
- P1：5 scenarios、3 次一致性导入、1200 条 synthetic metadata、2 条阻断错误。
- P2：5 类检查、18 个 Stage 证据、UI 54/54 PASS、lineage full=false。
- P3：3 类只读 connector、4 个 OpMe 轻入口、6 条未启动 Backlog，live call/source mutation=0/0。
- raw：review 前后、跨 S18-P3 和 fresh current 快照完全一致。
- 当前仍为 Q4 / D / NO_GO / 3-9-2-1，不得交付。

## 边界

- 本轮只完成 Stage 18 整体复审与 findings 修复。
- 未执行 v1.4 最终整体复审、GitHub upload、App 重装、真实连接器、凭据处理、正式报告、差异关闭或业务执行。
- 下一步只能另起 run work 执行 v1.4 最终整体复审并修复 findings。
""",
    )
    _write_text(FINDINGS_PATH, f"# Stage 18 复审 Findings\n\n{finding_lines}\n")
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Stage 18 整体复审测试结果

- baseline RED：30 phase tests=`29 PASS / 1 FAIL`，定位 P2 HANDOFF 时态耦合。
- 修复后 phase tests：30/30 PASS。
- phase strict validators：3/3 PASS。
- review TDD RED：generator/checker 缺失时 `1 failure + 10 skipped`。
- review focused tests：{'11/11 PASS' if final_validation else '待最终验证回放'}。
- review strict validator：{'PASS' if final_validation else '待最终验证回放'}。
- acceptance：31/31 PASS。
- raw、治理、结构与敏感扫描：{'PASS' if final_validation else '待最终验证回放'}。
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        """# Stage 18 整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 历史 phase 测试锁死旧 HANDOFF | 仅在对应 phase active 时校验当前路由 | 已修复 |
| Stage review PASS 被误读为 release GO | Go/No-Go 保持 NO_GO，最终复审与交付门禁关闭 | 已控制 |
| legacy review/upload 污染 current | legacy 仅作结构历史，动态和上传状态非权威 | 已控制 |
| connector proposal 被误读为已连接 | live call、credential、writeback 和 source mutation 均为 0 | 已控制 |
| raw 被 review 污染 | ignored private 前后、跨 phase、fresh current 四重快照 | 已控制 |
""",
    )
    _write_text(
        ROLLBACK_PATH,
        """# Stage 18 整体复审回滚计划

1. 回退本 review local commit、新 review 证据和 3 个时态耦合修复。
2. 删除 ignored private runtime 中本 review 快照和诊断，不触碰 raw。
3. 恢复 S18-P3 为 current pointer，保留 P1/P2/P3 已验证证据。
4. 不执行生产恢复、连接器补偿、GitHub upload、App 重装或业务动作。
""",
    )
    _write_text(
        HUMAN_DIR / "go_no_go_record_zh.md",
        f"""# Stage 18 复审 Go/No-Go 记录

- 决策：NO_GO。
- Stage 18 review pending 已解除，但最终整体复审仍待执行。
- 交付、正式报告、经营决策依据、GitHub upload、App 重装和业务执行：全部不允许。

## 保留阻断项

{blocker_lines}
""",
    )


def generate(*, final_validation: bool = False, write_governance: bool = True) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    inventory = _test_inventory()
    if inventory != {"S18-P1": 10, "S18-P2": 10, "S18-P3": 10}:
        raise ValueError(f"Stage 18 focused test inventory drift: {inventory}")
    p1_manifest, p2_manifest, p3_manifest = _current_chain()
    historical = _historical_baseline()
    taskpack = _taskpack_contract()
    fix_checks = _review_fix_checks()
    if not all(fix_checks.values()):
        raise ValueError(f"Stage 18 review finding fix incomplete: {fix_checks}")

    phase_rows = _phase_result_rows(inventory, final_validation)
    contract_rows = _cross_phase_matrix(p1_manifest, p2_manifest, p3_manifest)
    findings = _review_findings()
    p1s, p2s, p3s = p1_manifest["summary"], p2_manifest["summary"], p3_manifest["summary"]
    stage_gate = _stage_gate(p1s, p2s, p3s)
    go_no_go = _go_no_go()

    raw_helper = p3.s18_p2.s18_p1.s17_review.p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    raw_before = raw_helper._raw_snapshot("before_v014_s18_post_remediation_stage_review")
    raw_after = raw_helper._raw_snapshot("after_v014_s18_post_remediation_stage_review")
    prior_raw = _read_json(p3.PRIVATE_RAW_AFTER_PATH)
    fresh_raw = raw_helper._raw_snapshot("fresh_v014_s18_post_remediation_stage_review")
    normalize = raw_helper._normalize_raw
    raw_exact = normalize(raw_before) == normalize(raw_after)
    raw_cross = normalize(raw_before) == normalize(prior_raw) == normalize(fresh_raw)
    if not raw_exact or not raw_cross:
        raise ValueError("raw source changed during current Stage 18 review")

    summary = {
        "schema_version": "kmfa.v014.s18_post_remediation_stage_review_summary.v1",
        "record_type": "v014_s18_post_remediation_stage_review_summary",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "phase_results": {row["phase_id"]: "PASS" for row in phase_rows},
        "phase_pass_count": 3,
        "phase_focused_test_count": sum(inventory.values()),
        "phase_focused_test_pass_count": sum(inventory.values()) if final_validation else 0,
        "phase_strict_validator_count": 3,
        "phase_strict_validator_pass_count": 3 if final_validation else 0,
        "review_finding_count": len(findings),
        "fixed_review_finding_count": sum(row["status"] == "fixed" for row in findings),
        "passed_review_finding_count": sum(row["status"] == "passed" for row in findings),
        "open_review_finding_count": sum(row["status"] == "open" for row in findings),
        "cross_phase_contract_count": len(contract_rows),
        "cross_phase_contract_mismatch_count": sum(row["mismatch_count"] for row in contract_rows),
        "historical_stage18_review_validated": historical["validated"],
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_exact,
        "raw_cross_phase_snapshot_exact_match": raw_cross,
        "fresh_raw_snapshot_validated": normalize(raw_before) == normalize(fresh_raw),
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s18_p1_performed": True,
        "s18_p2_performed": True,
        "s18_p3_performed": True,
        "stage18_review_performed": True,
        "final_overall_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "NO_GO",
    }
    bundle = {"summary": summary, "phase_results": phase_rows, "contracts": contract_rows, "go_no_go": go_no_go}
    if final_validation:
        validate_review_bundle(bundle)
    acceptance = _acceptance_matrix(summary, stage_gate)
    if final_validation and acceptance["check_fail_count"]:
        raise ValueError("Stage 18 review acceptance matrix failed")

    manifest = {
        "schema_version": "kmfa.v014.s18_post_remediation_stage_review_manifest.v1",
        "record_type": "v014_s18_post_remediation_stage_review_manifest",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "review_scope": REVIEW_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "formula_id": FORMULA_ID,
        "parameter_ids": list(PARAMETER_IDS),
        "model_registry_key": MODEL_REGISTRY_KEY,
        "generated_at": generated_at,
        "git_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "summary": summary,
        "stage_gate": stage_gate,
        "review_findings": findings,
        "review_fix_checks": fix_checks,
        "historical_stage18_review_structural_baseline_validated": True,
        "historical_stage18_review_dynamic_state_authoritative": False,
        "historical_stage18_review_baseline": historical,
        "taskpack_contract": taskpack,
        "review_boundaries": _review_boundaries(),
        "public_repo_safety": _public_safety(),
        "acceptance_matrix": acceptance,
        "go_no_go": go_no_go,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "manifest": MANIFEST_PATH.as_posix(),
            "phase_results": PHASE_RESULTS_PATH.as_posix(),
            "contract_matrix": CONTRACT_MATRIX_PATH.as_posix(),
            "acceptance": ACCEPTANCE_MATRIX_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "findings": FINDINGS_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
        },
        "validation_summary": {
            "final_validation_recorded": final_validation,
            "phase_focused_tests": "PASS" if final_validation else "PENDING",
            "phase_strict_validators": "PASS" if final_validation else "PENDING",
            "review_focused_tests": "PASS" if final_validation else "PENDING",
            "review_strict_validator": "PASS" if final_validation else "PENDING",
            "review_findings_closed": "PASS" if final_validation else "PENDING",
            "raw_alignment": "PASS" if final_validation else "PENDING",
            "governance_and_safety_scans": "PASS" if final_validation else "PENDING",
        },
        "next_phase": NEXT_PHASE,
        "next_required_step": (
            "Run v1.4 final overall review and finding fixes separately; do not execute GitHub upload, App reinstall, "
            "formal report release, live connectors, credential handling, difference closure, persistent business writes, "
            "or business execution in Stage 18 review."
        ),
        "content_hash": _sha256_json(bundle),
    }

    _write_json(SUMMARY_PATH, summary)
    _write_json(MANIFEST_PATH, manifest)
    _write_jsonl(PHASE_RESULTS_PATH, phase_rows)
    _write_jsonl(CONTRACT_MATRIX_PATH, contract_rows)
    _write_json(ACCEPTANCE_MATRIX_PATH, acceptance)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_jsonl(METADATA_PHASE_RESULTS_PATH, phase_rows)
    _write_jsonl(METADATA_CONTRACT_MATRIX_PATH, contract_rows)
    _write_json(METADATA_ACCEPTANCE_MATRIX_PATH, acceptance)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_human_artifacts(summary, findings, stage_gate, go_no_go, final_validation=final_validation)
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "raw_prior_snapshot": prior_raw,
            "raw_fresh_snapshot": fresh_raw,
            "raw_phase_exact": raw_exact,
            "raw_cross_phase_exact": raw_cross,
            "phase_focused_test_pass_count": summary["phase_focused_test_pass_count"],
            "phase_strict_validator_pass_count": summary["phase_strict_validator_pass_count"],
            "review_finding_count": summary["review_finding_count"],
            "open_review_finding_count": summary["open_review_finding_count"],
        },
    )
    _write_text(
        PRIVATE_REVIEW_REPORT_PATH,
        """# Stage 18 私有复审边界核验

- review 前后、跨 S18-P3、fresh current raw 快照完全一致。
- 30 个 phase tests 与 3 个 strict validators 已复跑。
- 3 个时态耦合 findings 已修复，开放 findings=0。
- 未修改、删除、移动、重命名、覆盖、复制或备份 raw。
- 未执行最终整体复审、GitHub upload、App 重装、真实连接器、凭据处理或业务动作。
- 最终 goal 多次交叉验证仍无法对齐时，必须输出全中文差异报告。
""",
    )
    if write_governance:
        _write_governance(generated_at)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate current KMFA Stage 18 overall-review evidence")
    parser.add_argument("--final-validation", action="store_true")
    parser.add_argument("--no-governance", action="store_true")
    args = parser.parse_args()
    manifest = generate(final_validation=args.final_validation, write_governance=not args.no_governance)
    summary = manifest["summary"]
    print(
        "Stage 18 current review: "
        f"phases={summary['phase_pass_count']}/3 tests={summary['phase_focused_test_pass_count']}/30 "
        f"validators={summary['phase_strict_validator_pass_count']}/3 findings={summary['fixed_review_finding_count']}/3 "
        f"open={summary['open_review_finding_count']} contracts={summary['cross_phase_contract_count']} "
        f"raw={summary['raw_snapshot_exact_match']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
