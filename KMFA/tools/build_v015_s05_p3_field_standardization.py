#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S05-P3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import v015_s05_p3_field_standardization as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S05_P3_FIELD_STANDARDIZATION"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
FIELD_DICTIONARY_PATH = PROJECT_ROOT / "metadata/schema_maps/v015_s05_p3_standard_field_dictionary_public_safe.json"
ALIAS_REGISTRY_PATH = PROJECT_ROOT / "metadata/schema_maps/v015_s05_p3_alias_mapping_registry_public_safe.json"
SEMANTIC_CONTRACT_PATH = PROJECT_ROOT / "metadata/quality/v015_s05_p3_value_semantics_public_safe.json"
DICTIONARY_VERIFICATION_PATH = MACHINE_ROOT / "field_dictionary_verification_public_safe.json"
ALIAS_VERIFICATION_PATH = MACHINE_ROOT / "alias_mapping_verification_public_safe.json"
SEMANTIC_VERIFICATION_PATH = MACHINE_ROOT / "value_semantics_verification_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
MANIFEST_PATH = MACHINE_ROOT / "s05_p3_field_standardization_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")


def _ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def field_dictionary_contract() -> dict[str, Any]:
    fields = kernel.validate_field_dictionary()
    return {
        "schema_version": "kmfa.v015.s05p3.field_dictionary.v1",
        "dictionary_version": kernel.DICTIONARY_VERSION,
        "field_count": len(fields),
        "critical_field_count": sum(field.critical for field in fields),
        "domain_count": len(kernel.DOMAINS),
        "domains": list(kernel.DOMAINS),
        "required_definition_attributes": [
            "definition_zh", "data_type", "unit", "source_classes", "required_when",
        ],
        "fields": [field.to_public_dict() for field in fields],
        "raw_root_access_count": 0,
    }


def alias_mapping_contract() -> dict[str, Any]:
    registry = kernel.AliasRegistry()
    return {
        "schema_version": "kmfa.v015.s05p3.alias_mapping_registry.v1",
        "mapping_version": kernel.MAPPING_VERSION,
        "confidence_basis": "CURATED_RULE_CONFIDENCE_NOT_MODEL_PROBABILITY",
        "auto_map_minimum_bps": 9900,
        "manual_confirmation_minimum_bps": 8000,
        "rule_count": len(registry.rules),
        "confidence_band_count": 3,
        "alias_types": sorted(kernel.ALIAS_TYPES),
        "rules": [rule.to_public_dict() for rule in registry.rules],
        "low_confidence_auto_map_allowed": False,
        "unregistered_alias_auto_map_allowed": False,
        "raw_root_access_count": 0,
    }


def value_semantic_contract() -> dict[str, Any]:
    semantics = kernel.semantic_contract()
    return {
        "schema_version": "kmfa.v015.s05p3.value_semantics.v1",
        "special_semantic_count": len(semantics),
        "normal_semantic": kernel.ValueSemantic.PRESENT.value,
        "special_semantics": semantics,
        "blank_to_zero_allowed": False,
        "ambiguous_value_derivation_allowed": False,
        "raw_root_access_count": 0,
    }


def field_dictionary_verification() -> dict[str, Any]:
    fields = kernel.validate_field_dictionary()
    checks = {
        "all_domains_present": {field.domain for field in fields} == set(kernel.DOMAINS),
        "all_required_attributes_present": all(
            field.definition_zh and field.data_type and field.unit and field.source_classes and field.required_when
            for field in fields
        ),
        "all_amounts_are_integer_cents": all(
            field.data_type != "INTEGER_CENTS"
            or (field.unit == "CNY_CENT" and field.storage_format == "SIGNED_INTEGER_CENTS")
            for field in fields
        ),
        "all_dates_are_iso": all(
            field.data_type != "ISO_DATE" or field.storage_format == "YYYY-MM-DD"
            for field in fields
        ),
        "all_critical_fields_defined": all(not field.critical or field.definition_zh for field in fields),
    }
    return {
        "schema_version": "kmfa.v015.s05p3.field_dictionary_verification.v1",
        "case_count": len(fields) + len(checks),
        "pass_count": len(fields) + sum(checks.values()),
        "definition_count": len(fields),
        "critical_field_count": sum(field.critical for field in fields),
        "checks": checks,
        "raw_root_access_count": 0,
    }


def alias_mapping_verification() -> dict[str, Any]:
    registry = kernel.AliasRegistry()
    decisions = {
        "canonical": registry.resolve("项目名称").to_public_dict(),
        "abbreviation": registry.resolve("项目号", template_class="PROJECT_REGISTER").to_public_dict(),
        "historical": registry.resolve("客商名称", template_class="CUSTOMER_MASTER").to_public_dict(),
        "typo": registry.resolve("合同編号", template_class="CONTRACT_REGISTER").to_public_dict(),
        "template_variant": registry.resolve("含税金额", template_class="CONTRACT_REGISTER").to_public_dict(),
        "ambiguous_without_template": registry.resolve("金额").to_public_dict(),
        "contract_amount": registry.resolve("金额", template_class="CONTRACT_REGISTER").to_public_dict(),
        "cost_amount": registry.resolve("金额", template_class="COST_REGISTER").to_public_dict(),
        "invoice_amount": registry.resolve("金额", template_class="INVOICE_REGISTER").to_public_dict(),
        "collection_amount": registry.resolve("金额", template_class="COLLECTION_REGISTER").to_public_dict(),
        "unregistered": registry.resolve("未登记示例字段").to_public_dict(),
        "wrong_version": registry.resolve("项目名称", version="0.9.0").to_public_dict(),
    }
    expected = {
        "canonical": "AUTO_MAPPED",
        "abbreviation": "AUTO_MAPPED",
        "historical": "MANUAL_CONFIRMATION",
        "typo": "MANUAL_CONFIRMATION",
        "template_variant": "MANUAL_CONFIRMATION",
        "ambiguous_without_template": "AMBIGUOUS",
        "contract_amount": "AUTO_MAPPED",
        "cost_amount": "AUTO_MAPPED",
        "invoice_amount": "AUTO_MAPPED",
        "collection_amount": "AUTO_MAPPED",
        "unregistered": "UNREGISTERED",
        "wrong_version": "UNREGISTERED",
    }
    pass_count = sum(decisions[name]["status"] == status for name, status in expected.items())
    return {
        "schema_version": "kmfa.v015.s05p3.alias_mapping_verification.v1",
        "case_count": len(expected),
        "pass_count": pass_count,
        "expected_statuses": expected,
        "decisions": decisions,
        "low_confidence_auto_map_count": 0,
        "raw_root_access_count": 0,
    }


def value_semantics_verification() -> dict[str, Any]:
    cases = [
        ("observed_zero_integer", "cost_amount_cents", 0, False, "ZERO"),
        ("observed_zero_text", "cost_amount_cents", "0", False, "ZERO"),
        ("blank_none", "cost_amount_cents", None, False, "BLANK"),
        ("blank_whitespace", "cost_amount_cents", "   ", False, "BLANK"),
        ("dash", "cost_amount_cents", "-", False, "DASH"),
        ("source_unknown", "cost_amount_cents", "未知", False, "UNKNOWN_VALUE"),
        ("not_applicable", "cost_amount_cents", "不适用", False, "NOT_APPLICABLE"),
        ("explicit_parse_failure", "project_name", "示例项目", True, "PARSE_FAILED"),
        ("fractional_cents", "cost_amount_cents", "10.5", False, "PARSE_FAILED"),
        ("float_rejected", "cost_amount_cents", 1.0, False, "PARSE_FAILED"),
        ("valid_date", "invoice_date", "2026-07-15", False, "PRESENT"),
        ("invalid_date", "invoice_date", "2026-02-30", False, "PARSE_FAILED"),
    ]
    results = []
    for name, field_id, value, parse_failed, expected in cases:
        classified = kernel.classify_value(field_id, value, parse_failed=parse_failed)
        results.append({
            "case": name,
            "expected_semantic": expected,
            "passed": classified.semantic.value == expected,
            "result": classified.to_public_dict(),
        })
    return {
        "schema_version": "kmfa.v015.s05p3.value_semantics_verification.v1",
        "case_count": len(results),
        "pass_count": sum(row["passed"] for row in results),
        "cases": results,
        "blank_to_zero_count": sum(
            row["result"]["semantic"] == "ZERO" and row["case"].startswith("blank") for row in results
        ),
        "raw_root_access_count": 0,
    }


def task_matrix(*, accepted: bool) -> list[dict[str, Any]]:
    status = "PASSED" if accepted else "PENDING_FINAL_VALIDATION"
    return [
        {
            "task_id": "S05P3T01",
            "name": "建立标准字段字典",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [_ref(FIELD_DICTIONARY_PATH), _ref(DICTIONARY_VERIFICATION_PATH)],
        },
        {
            "task_id": "S05P3T02",
            "name": "建立别名与映射规则",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [_ref(ALIAS_REGISTRY_PATH), _ref(ALIAS_VERIFICATION_PATH)],
        },
        {
            "task_id": "S05P3T03",
            "name": "建立空值和异常值语义",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": status,
            "evidence_refs": [_ref(SEMANTIC_CONTRACT_PATH), _ref(SEMANTIC_VERIFICATION_PATH)],
        },
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and (
        {row.get("validation_head") for row in receipts} != {validation_head}
        or {row.get("validation_run_id") for row in receipts} != {validation_run_id}
    ):
        raise ValueError("validation receipts do not share one validation head and run")
    dictionary = field_dictionary_verification()
    aliases = alias_mapping_verification()
    semantics = value_semantics_verification()
    status = "PASSED" if passed else "PENDING_FINAL_VALIDATION"
    return {
        "schema_version": "kmfa.v015.s05p3.field_standardization_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S05",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S05-P3",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": status,
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_count": 3,
        "stage_phase_pass_count": 3 if passed else 2,
        "stage_task_count": 9,
        "stage_task_accepted_count": 9 if passed else 6,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if passed else 0,
        "field_domain_count": len(kernel.DOMAINS),
        "field_definition_count": dictionary["definition_count"],
        "critical_field_count": dictionary["critical_field_count"],
        "field_definition_case_count": dictionary["case_count"],
        "field_definition_pass_count": dictionary["pass_count"],
        "alias_rule_count": len(kernel.ALIAS_RULES),
        "mapping_case_count": aliases["case_count"],
        "mapping_case_pass_count": aliases["pass_count"],
        "confidence_band_count": 3,
        "low_confidence_auto_map_allowed": False,
        "alias_collision_silent_resolution_allowed": False,
        "special_value_semantic_count": len(kernel.SPECIAL_VALUE_SEMANTICS),
        "value_semantic_case_count": semantics["case_count"],
        "value_semantic_case_pass_count": semantics["pass_count"],
        "blank_to_zero_allowed": False,
        "ambiguous_value_derivation_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "CONTINUE_TO_S05_STAGE_REVIEW_ONLY" if passed else "REMAIN_IN_S05_P3",
        "s04_stage_review_acceptance_status": "PASSED",
        "s05_p1_acceptance_status": "PASSED",
        "s05_p2_acceptance_status": "PASSED",
        "s05_p3_started": True,
        "s05_p3_acceptance_status": status,
        "s05_stage_review_entry_allowed": passed,
        "s05_stage_review_started": False,
        "s05_stage_review_performed": False,
        "s06_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
    }


def expected_static_outputs() -> dict[Path, bytes]:
    return {
        FIELD_DICTIONARY_PATH: _json_bytes(field_dictionary_contract()),
        ALIAS_REGISTRY_PATH: _json_bytes(alias_mapping_contract()),
        SEMANTIC_CONTRACT_PATH: _json_bytes(value_semantic_contract()),
        DICTIONARY_VERIFICATION_PATH: _json_bytes(field_dictionary_verification()),
        ALIAS_VERIFICATION_PATH: _json_bytes(alias_mapping_verification()),
        SEMANTIC_VERIFICATION_PATH: _json_bytes(value_semantics_verification()),
        HUMAN_ROOT / "completion_record_zh.md": (
            "# v1.5 S05-P3 字段标准化完成记录\n\n"
            "- 24 个 public-safe 标准字段覆盖项目、客户、合同、成本、发票、回款、账户、政策八个域；每项均登记中文定义、类型、单位、来源、必填条件与存储/展示格式。\n"
            "- 36 条别名规则绑定版本与 curated confidence；低置信、错别字、历史名和歧义模板必须人工确认，未登记字段进入质量队列。\n"
            "- 0、空白、横线、未知、不适用、解析失败分别建模；仅观测零保持零，空白绝不静默转零。\n"
            "- 本 Phase raw access=0；未启动 Stage review、S06、GitHub、App、正式报告或业务执行。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n最终结果以 `machine/validation_results.jsonl` 与 strict checker 为准；"
            "覆盖字段 schema、八域完整性、金额/日期格式、别名版本与置信度、模板歧义、碰撞、六类特殊值语义及旧字段标准化回归。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n仅回滚 S05-P3 新增内核、public-safe metadata、测试、evidence 与治理登记；"
            "不得触碰 raw、S05-P1/P2 evidence、Stage review、remote 或 installed App。\n"
        ).encode("utf-8"),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 未解决风险\n\n"
            "- `S05P3-RISK-001`：规则置信度是可审计的人工规则等级，不是统计模型概率；真实模板启用前仍需 owner 审核。\n"
            "- `S05P3-RISK-002`：本 Run 只使用通用 public-safe 别名；真实私有表头映射须在忽略目录内验证且不得进入公开证据。\n"
            "- `S05P3-RISK-003`：Stage 5 尚未独立复审，S06 入口保持关闭。\n"
        ).encode("utf-8"),
    }


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[TASK_MATRIX_PATH] = _json_bytes(task_matrix(accepted=bool(final_validation and receipts)))
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
    for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH, TASK_MATRIX_PATH):
        if not path.is_file():
            mismatches.append(_ref(path))
    if MANIFEST_PATH.is_file() and VALIDATION_RESULTS_PATH.is_file() and TASK_MATRIX_PATH.is_file():
        try:
            current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            receipts = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
            final = current.get("phase_acceptance_status") == "PASSED"
            if MANIFEST_PATH.read_bytes() != _json_bytes(manifest(final_validation=final, receipts=receipts)):
                mismatches.append(_ref(MANIFEST_PATH))
            if TASK_MATRIX_PATH.read_bytes() != _json_bytes(task_matrix(accepted=final)):
                mismatches.append(_ref(TASK_MATRIX_PATH))
            if final != bool(receipts):
                mismatches.append(_ref(VALIDATION_RESULTS_PATH))
        except (OSError, ValueError, json.JSONDecodeError):
            mismatches.extend([_ref(MANIFEST_PATH), _ref(VALIDATION_RESULTS_PATH), _ref(TASK_MATRIX_PATH)])
    return sorted(set(mismatches))


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
            print("PASS: S05-P3 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S05-P3 public-safe artifacts")
    except (OSError, ValueError, json.JSONDecodeError, kernel.FieldContractError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
