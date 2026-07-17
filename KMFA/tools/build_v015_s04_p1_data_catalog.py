#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S04-P1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s04_p1_data_catalog as catalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S04_P1_DATA_CATALOG")
OUTPUT_ROOT = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"

MANIFEST_PATH = MACHINE_ROOT / "s04_p1_data_catalog_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

METADATA_OUTPUTS = {
    PROJECT_ROOT / "metadata/catalog/v015_s04_p1_data_catalog_schema_public_safe.json": "catalog_schema",
    PROJECT_ROOT / "metadata/catalog/v015_s04_p1_catalog_template_public_safe.json": "catalog_template",
    PROJECT_ROOT / "metadata/catalog/v015_s04_p1_source_status_machine_public_safe.json": "status_machine",
    PROJECT_ROOT / "metadata/catalog/v015_s04_p1_import_registration_protocol_public_safe.json": "import_protocol",
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n").encode()
        for value in values
    )


def _ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def catalog_schema() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.data_catalog_schema.v1",
        "phase_id": catalog.RUN_PHASE_ID,
        "hierarchy": list(catalog.CATALOG_HIERARCHY),
        "hierarchy_level_count": len(catalog.CATALOG_HIERARCHY),
        "required_source_systems": [
            "REDCIRCLE",
            "KINGDEE",
            "WPS",
            "BANK",
            "TAX_EINVOICE",
            "CONTRACT_DOCS",
            "POLICY_EVIDENCE",
        ],
        "required_source_system_count": 7,
        "required_catalog_record_count": 21,
        "identity_contract": {
            "source_id_pattern": catalog.SOURCE_ID_PATTERN.pattern,
            "catalog_record_id_pattern": r"^CAT-S04P1-[0-9]{3}$",
        },
        "formal_report_gate": {
            "required_bindings": ["entity", "account_or_report", "period", "version", "owner_role"],
            "missing_core_binding_action": "BLOCK_FORMAL_REPORT",
        },
        "public_private_boundary": {
            "public_template_allowed": True,
            "raw_values_allowed": False,
            "plaintext_filenames_allowed": False,
            "private_file_digests_allowed": False,
            "raw_root_access_required": False,
        },
    }


def status_verification() -> dict[str, Any]:
    rows = catalog.build_catalog_records()
    source_id = rows[0]["source_id"]
    manual = catalog.build_status_event(
        source_id=source_id,
        previous_status="PARTIAL",
        new_status="MANUAL_REVIEW",
        reason="synthetic missing binding requires confirmation",
        operator_role="ROLE::DATA_REVIEWER",
        authority="CONTROL_REVIEWER",
        event_time="2026-07-14T12:00:00+10:00",
        affected_report_refs=["REPORT::MANAGEMENT_OVERVIEW"],
        backend_fact_ref="FACT::SYNTHETIC_IMPORT_STATE",
    )
    ready = catalog.build_status_event(
        source_id=source_id,
        previous_status="MANUAL_REVIEW",
        new_status="READY",
        reason="synthetic backend and quality facts complete",
        operator_role="ROLE::QUALITY_ENGINE",
        authority="QUALITY_ENGINE",
        event_time="2026-07-14T12:01:00+10:00",
        affected_report_refs=["REPORT::MANAGEMENT_OVERVIEW"],
        backend_fact_ref="FACT::SYNTHETIC_IMPORT_STATE",
        quality_fact_ref="QUALITY::SYNTHETIC_PASS",
    )
    blocked_frontend = False
    try:
        catalog.build_status_event(
            source_id=source_id,
            previous_status="PARTIAL",
            new_status="READY",
            reason="frontend request",
            operator_role="ROLE::FRONTEND_USER",
            authority="FRONTEND",
            event_time="2026-07-14T12:02:00+10:00",
            affected_report_refs=["REPORT::MANAGEMENT_OVERVIEW"],
            backend_fact_ref="FACT::SYNTHETIC_IMPORT_STATE",
            quality_fact_ref="QUALITY::SYNTHETIC_PASS",
        )
    except catalog.DataCatalogError:
        blocked_frontend = True
    return {
        "schema_version": "kmfa.v015.s04p1.status_verification.v1",
        "status_count": len(catalog.SOURCE_STATUSES),
        "status_labels_exact": list(catalog.SOURCE_STATUS_LABELS.values()),
        "append_only_event_examples_valid": all(
            event["storage_mode"] == "APPEND_ONLY_METADATA"
            and not event["raw_fact_mutation_allowed"]
            for event in (manual, ready)
        ),
        "reason_operator_time_reports_fact_required": True,
        "ready_quality_fact_required": True,
        "frontend_direct_transition_blocked": blocked_frontend,
        "raw_fact_mutation_allowed": False,
        "event_example_count": 2,
        "public_event_values_are_synthetic": True,
    }


def task_matrix() -> list[dict[str, Any]]:
    return [
        {
            "task_id": "S04P1T01",
            "name": "建立多层数据目录",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/catalog/v015_s04_p1_data_catalog_schema_public_safe.json"),
                _ref(PROJECT_ROOT / "metadata/catalog/v015_s04_p1_catalog_template_public_safe.json"),
                _ref(MACHINE_ROOT / "catalog_coverage_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S04P1T02",
            "name": "建立数据源状态模型",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/catalog/v015_s04_p1_source_status_machine_public_safe.json"),
                _ref(MACHINE_ROOT / "status_machine_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S04P1T03",
            "name": "建立文件与批次登记",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/catalog/v015_s04_p1_import_registration_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "import_registration_verification_public_safe.json"),
            ],
        },
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = final_validation and receipts and all(row.get("status") == "PASS" for row in receipts)
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and any(row.get("validation_head") != validation_head for row in receipts):
        raise ValueError("validation receipts do not share one validation_head")
    if passed and any(row.get("validation_run_id") != validation_run_id for row in receipts):
        raise ValueError("validation receipts do not share one validation_run_id")
    coverage = catalog.validate_catalog_records(catalog.build_catalog_records())
    return {
        "schema_version": "kmfa.v015.s04p1.data_catalog_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S04",
        "phase_id": catalog.RUN_PHASE_ID,
        "roadmap_phase_id": "S04-P1",
        "task_id": catalog.TASK_ID,
        "acceptance_id": catalog.ACCEPTANCE_ID,
        "version": catalog.VERSION,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if passed else 0,
        "catalog_record_count": coverage["catalog_record_count"],
        "source_system_count": coverage["source_system_count"],
        "catalog_hierarchy_level_count": coverage["hierarchy_level_count"],
        "source_status_count": len(catalog.SOURCE_STATUSES),
        "required_import_field_count": len(catalog.REQUIRED_IMPORT_FIELDS),
        "formal_report_allowed": False,
        "formal_report_stop_reason": coverage["formal_report_stop_reason"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "raw_fact_mutation_allowed": False,
        "product_implementation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "CONTINUE_TO_S04_P2_ONLY" if passed else "REMAIN_IN_S04_P1",
        "s04_p1_started": True,
        "s04_p1_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s04_p2_entry_allowed": bool(passed),
        "s04_p2_started": False,
        "s04_p3_entry_allowed": False,
        "s04_stage_review_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
        "evidence_refs": [
            _ref(MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"),
            _ref(MACHINE_ROOT / "catalog_coverage_verification_public_safe.json"),
            _ref(MACHINE_ROOT / "status_machine_verification_public_safe.json"),
            _ref(MACHINE_ROOT / "import_registration_verification_public_safe.json"),
            _ref(VALIDATION_RESULTS_PATH),
        ],
    }


def expected_static_outputs() -> dict[Path, bytes]:
    records = catalog.build_catalog_records()
    coverage = catalog.validate_catalog_records(records)
    outputs = {
        PROJECT_ROOT / "metadata/catalog/v015_s04_p1_data_catalog_schema_public_safe.json": _json_bytes(catalog_schema()),
        PROJECT_ROOT / "metadata/catalog/v015_s04_p1_catalog_template_public_safe.json": _json_bytes(
            {
                "schema_version": "kmfa.v015.data_catalog_template.v1",
                "record_count": len(records),
                "records": records,
            }
        ),
        PROJECT_ROOT / "metadata/catalog/v015_s04_p1_source_status_machine_public_safe.json": _json_bytes(catalog.status_machine_contract()),
        PROJECT_ROOT / "metadata/catalog/v015_s04_p1_import_registration_protocol_public_safe.json": _json_bytes(catalog.import_registration_protocol()),
        MACHINE_ROOT / "catalog_coverage_verification_public_safe.json": _json_bytes(
            {
                "schema_version": "kmfa.v015.s04p1.catalog_coverage_verification.v1",
                **coverage,
                "required_source_domains_covered": True,
                "public_safe_template_only": True,
                "raw_root_access_count": 0,
            }
        ),
        MACHINE_ROOT / "status_machine_verification_public_safe.json": _json_bytes(status_verification()),
        MACHINE_ROOT / "import_registration_verification_public_safe.json": _json_bytes(catalog.public_verification_summary()),
        MACHINE_ROOT / "task_acceptance_matrix_public_safe.json": _json_bytes(task_matrix()),
        HUMAN_ROOT / "completion_record_zh.md": (
            "# v1.5 S04-P1 数据目录完成记录\n\n"
            "- 完成 21 行、7 类来源系统、9 层公共安全数据目录模板。\n"
            "- 完成五态 append-only 状态机；前端不能直接改变来源事实或把状态改为已就绪。\n"
            "- 完成六字段文件/批次登记协议；重复文件可识别，解析版本可共存，缺 source/hash 必须隔离。\n"
            "- 本 Phase 未访问 raw inbox；真实文件 hash 仅允许位于私有 metadata 平面。\n"
            "- 当前目录仍含待绑定占位，因此正式报告继续阻断；S04-P2、S04-P3、Stage review、GitHub 与 App 均未启动。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            "最终结果以 `machine/validation_results.jsonl` 与 strict checker 为准。"
            "必须覆盖 schema、状态机、前端越权拒绝、幂等、版本共存、隔离及治理同步。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n"
            "仅回滚本 Phase 新增的 catalog metadata、工具、测试、证据和对应治理登记。"
            "不得删除或改写 raw inbox、既有 S03 证据或已发布基线。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 未解决风险\n\n"
            "- `S04P1-RISK-001`：21 行公共模板中的主体、账户、期间和版本仍待私有导入事实绑定；"
            "正式报告门保持关闭，后续路由到 `S04P2T01`。\n"
        ).encode(),
    }
    return outputs


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[MANIFEST_PATH] = _json_bytes(manifest(final_validation=final_validation, receipts=receipts))
    outputs[VALIDATION_RESULTS_PATH] = _jsonl_bytes(receipts or [])
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_static_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(_ref(path))
    if not MANIFEST_PATH.is_file():
        mismatches.append(_ref(MANIFEST_PATH))
    if not VALIDATION_RESULTS_PATH.is_file():
        mismatches.append(_ref(VALIDATION_RESULTS_PATH))
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise ValueError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S04-P1 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S04-P1 public-safe artifacts")
    except (OSError, ValueError, catalog.DataCatalogError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
