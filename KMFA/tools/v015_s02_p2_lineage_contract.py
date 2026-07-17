#!/usr/bin/env python3
"""Deterministic, public-safe S02-P2 data-to-report lineage contract.

This module defines planning-time schema and coverage only.  It never reads the
KMFA raw root, never materializes business values, and never claims that actual
field/metric/report lineage exists.  Callers may pass the public TaskPack member
09 CSV text directly; no Downloads path is a runtime dependency.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union


SCHEMA_VERSION = "kmfa.v015.s02_p2.data_report_lineage_contract.v1"
RECORD_TYPE = "data_report_lineage_contract"
CONTRACT_VERSION = "1.0.0"
DEFAULT_GENERATED_AT = "2026-07-13T00:00:00+10:00"


class LineageContractError(ValueError):
    """Raised when a planning contract violates a fail-closed invariant."""


TOP_LEVEL_PATH_FIELDS: Tuple[str, ...] = (
    "record_type",
    "schema_version",
    "lineage_record_id",
    "lineage_path_id",
    "project_id",
    "business_line_ids",
    "requirement_ids",
    "value_id",
    "value_class",
    "criticality",
    "source",
    "extraction",
    "mapping",
    "fact",
    "derivation",
    "quality",
    "human_review",
    "report_target",
    "publication_gate",
    "control_event_ids",
    "lineage_status",
    "evidence_refs",
    "created_at",
    "supersedes_lineage_record_id",
    "public_safe_projection",
)

VERSION_REQUIRED_FIELDS: Tuple[str, ...] = (
    "source_version",
    "extractor_version",
    "mapping_rule_version",
    "fact_version",
    "fact_schema_version",
    "derived_version",
    "formula_version",
    "parameter_set_version",
    "validation_rule_version",
    "report_version",
    "template_version",
)

AMOUNT_SEMANTICS_REQUIRED_FIELDS: Tuple[str, ...] = (
    "currency",
    "unit",
    "tax_inclusive_status",
    "tax_rate",
    "legal_entity_id",
    "business_period",
    "source_date",
    "effective_date",
)

LOCATOR_KINDS: Tuple[str, ...] = (
    "TABULAR_CELL",
    "PAGED_TABLE_CELL",
    "PAGED_REGION",
    "STRUCTURED_FIELD",
)

REPORT_TARGET_KINDS: Tuple[str, ...] = (
    "PAGE_FIELD",
    "API_FIELD",
    "METADATA_FIELD",
    "REPORT_CELL",
    "CHART_DATUM",
    "EXPORT_CELL",
)

HARD_GATES: Tuple[str, ...] = (
    "raw_file_registered_and_intact",
    "file_hash_available",
    "parse_success",
    "required_fields_available",
    "unit_known",
    "legal_entity_known",
    "period_known",
    "relationship_complete",
    "critical_reconciliation_passed",
    "zero_delta_passed_for_authoritative_fields",
    "freshness_acceptable_or_disclosed",
    "open_conflicts_resolved_or_explicitly_degraded",
)

_PRIMARY_EDGES: Tuple[Tuple[str, str], ...] = (
    ("L0", "L1"),
    ("L1", "L2"),
    ("L2", "L3"),
    ("L3", "L4"),
    ("L4", "L5"),
    ("L5", "L6"),
)
_CONTROL_EDGES: Tuple[Tuple[str, str], ...] = (
    ("L7", "L3"),
    ("L7", "L4"),
    ("L7", "L5"),
    ("L7", "L6"),
)


def _build_edge_contract() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, (source, target) in enumerate(_PRIMARY_EDGES + _CONTROL_EDGES, start=1):
        rows.append(
            {
                "edge_id": "EDGE-%02d-%s-%s" % (index, source, target),
                "from_layer": source,
                "to_layer": target,
                "edge_kind": "PRIMARY" if index <= len(_PRIMARY_EDGES) else "CONTROL",
                "version_append_required": True,
                "raw_mutation_allowed": False,
            }
        )
    return rows


NESTED_REQUIRED_FIELDS: Dict[str, Tuple[str, ...]] = {
    "source": (
        "import_run_id",
        "source_id",
        "source_system_code",
        "source_package_ref",
        "source_version",
        "file_hash",
        "file_size_bytes",
        "file_format",
        "storage_ref",
        "received_at",
        "container_member_ref",
        "locator",
    ),
    "source.locator": (
        "locator_kind",
        "worksheet_ref",
        "page_number",
        "table_ref",
        "row_start",
        "row_end",
        "column_start",
        "column_end",
        "cell_ref",
        "region_ref",
        "field_path",
    ),
    "extraction": (
        "extraction_record_id",
        "extraction_run_id",
        "extractor_id",
        "extractor_version",
        "extraction_status",
        "parse_status",
        "raw_text_private_ref",
        "raw_display_value_private_ref",
        "raw_formula_private_ref",
        "raw_text_hash",
        "raw_display_value_hash",
        "raw_formula_hash",
    ),
    "mapping": (
        "mapping_rule_id",
        "mapping_rule_version",
        "canonical_field_id",
        "rule_chain",
        "normalization_rule_id",
        "normalization_rule_version",
        "unit_conversion_rule_id",
        "unit_conversion_rule_version",
    ),
    "fact": (
        "staging_record_id",
        "fact_record_id",
        "fact_version",
        "fact_schema_version",
        "legal_entity_id",
        "business_period",
        "source_date",
        "effective_date",
        "currency",
        "unit",
        "tax_inclusive_status",
        "tax_rate",
        "fact_status",
    ),
    "derivation": (
        "derived_metric_id",
        "derived_version",
        "formula_id",
        "formula_version",
        "parameter_set_id",
        "parameter_set_version",
        "calculation_run_id",
        "input_lineage_record_ids",
        "amount_representation",
        "rounding_rule_id",
        "rounding_rule_version",
        "output_value_private_ref",
        "output_value_hash",
    ),
    "quality": (
        "quality_result_id",
        "validation_rule_id",
        "validation_rule_version",
        "hard_gate_results",
        "zero_delta_cents",
        "same_source_consistency_status",
        "cross_source_conflict_status",
        "freshness_status",
        "confidence_status",
        "confidence_score_bps",
        "confidence_model_id",
        "confidence_model_version",
        "confidence_threshold_parameter_ref",
        "hard_conflict_codes",
        "silent_error_count",
        "discrepancy_ids",
        "evidence_refs",
    ),
    "human_review": ("required", "reason_codes", "status", "control_event_ids"),
    "report_target": (
        "report_id",
        "report_version",
        "template_id",
        "template_version",
        "report_section_id",
        "report_slot_id",
        "target_kind",
        "target_locator",
    ),
    "publication_gate": (
        "requested_release_scope",
        "lineage_complete",
        "hard_gates_passed",
        "zero_delta_passed",
        "same_source_consistent",
        "cross_source_conflicts_closed_or_disclosed",
        "freshness_acceptable_or_disclosed",
        "human_approval_complete",
        "page_api_metadata_export_consistent",
        "raw_fingerprint_unchanged",
        "publication_status",
        "release_permission",
        "block_reason_ids",
    ),
    "public_safe_projection": (
        "private_lineage_record_token",
        "lineage_complete",
        "contains_raw_value",
        "contains_plaintext_filename",
        "contains_inferable_hash_locator_combination",
    ),
}


DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV = """来源系统,业务板块,文件包/数据包,公司主体,银行/系统账户,账户/报表/工作表,建议频率,初始状态,影响功能/报告,下一步
红圈,经营数据,经营汇总,主体待配置,,经营报表/工作表待映射,周,部分可用,经营首页、项目,需提供真实导出模板
红圈,合同数据,合同及付款节点,主体待配置,,合同报表/工作表待映射,事件/周,部分可用,项目、回款、税务,需提供真实导出模板
红圈,回款数据,回款计划与实际,主体待配置,,回款报表/工作表待映射,日/周,部分可用,回款、资金,需提供真实导出模板
红圈,财务数据,项目收入与成本,主体待配置,,财务报表/工作表待映射,周/月,部分可用,项目、报告,需提供真实导出模板
金蝶,总账,科目余额表,主体待配置,,账套/报表待映射,周/月,部分可用,财务资金、报告,确认金蝶版本和模板
金蝶,凭证,凭证明细,主体待配置,,账套/报表待映射,周/月,部分可用,项目、税务、报告,确认金蝶版本和模板
金蝶,往来,应收应付,主体待配置,,账套/报表待映射,周,部分可用,回款、资金,确认金蝶版本和模板
金蝶,财务报表,利润表/现金流/资产负债,主体待配置,,账套/报表待映射,月,部分可用,经营报告,确认金蝶版本和模板
WPS,客户资料,客户与账期,主体待配置,,文件/工作表待映射,周/月,部分可用,项目、回款,读取现有样本
WPS,应收账龄,账龄与明细,主体待配置,,文件/工作表待映射,周,部分可用,回款、报告,读取现有样本
WPS,发票,开票与税务台账,主体待配置,,文件/工作表待映射,周,部分可用,税务、报告,读取现有样本
WPS,项目状态,开工/完工/结算状态,主体待配置,,文件/工作表待映射,周,部分可用,项目、报告,读取现有样本
银行,流水,交易流水,主体待配置,银行/账户待配置,流水文件,日/周,部分可用,资金、回款、项目,建立主体-银行-账户目录
银行,余额,账户日余额,主体待配置,银行/账户待配置,余额文件,日,部分可用,资金、经营首页,建立主体-银行-账户目录
银行,回单,收付款回单,主体待配置,银行/账户待配置,回单文件,日/周,部分可用,项目、回款、资金,确认导出格式
税务/数电票,销项,销项发票,主体待配置,,发票数据,周/月,部分可用,税务、项目,确认导出字段
税务/数电票,进项,进项发票,主体待配置,,发票数据,周/月,部分可用,税务、项目,确认导出字段
合同资料,主合同,主合同与补充协议,主体待配置,,合同文件/台账,事件,部分可用,项目、回款、税务,优先结构化台账
合同资料,变更结算,签证/变更/结算确认,主体待配置,,文件/台账,事件/周,部分可用,项目、报告,后续合同扫描独立立项
政策证据,研发,研发项目/人员/费用,主体待配置,,证据台账,月/季,部分可用,税务与政策,只做证据准备度
政策证据,知识产权,知识产权清单,主体待配置,,证据台账,月/季,部分可用,税务与政策,只做证据准备度
"""

_SOURCE_SYSTEM_CODES: Dict[str, str] = {
    "红圈": "REDCIRCLE",
    "金蝶": "KINGDEE",
    "WPS": "WPS",
    "银行": "BANK",
    "税务/数电票": "TAX_EINVOICE",
    "合同资料": "CONTRACT_DOCS",
    "政策证据": "POLICY_EVIDENCE",
}

_SOURCE_BUSINESS_LINES: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("红圈", "经营数据"): ("BL-02", "BL-04", "BL-08", "BL-09"),
    ("红圈", "合同数据"): ("BL-01", "BL-03", "BL-06", "BL-08"),
    ("红圈", "回款数据"): ("BL-03", "BL-05"),
    ("红圈", "财务数据"): ("BL-01", "BL-02"),
    ("金蝶", "总账"): ("BL-02", "BL-05", "BL-06"),
    ("金蝶", "凭证"): ("BL-01", "BL-02", "BL-06", "BL-07"),
    ("金蝶", "往来"): ("BL-03", "BL-05", "BL-07"),
    ("金蝶", "财务报表"): ("BL-02", "BL-05"),
    ("WPS", "客户资料"): ("BL-03", "BL-09"),
    ("WPS", "应收账龄"): ("BL-03", "BL-09"),
    ("WPS", "发票"): ("BL-06",),
    ("WPS", "项目状态"): ("BL-08",),
    ("银行", "流水"): ("BL-01", "BL-03", "BL-05"),
    ("银行", "余额"): ("BL-02", "BL-05"),
    ("银行", "回单"): ("BL-01", "BL-03", "BL-05", "BL-07"),
    ("税务/数电票", "销项"): ("BL-01", "BL-06"),
    ("税务/数电票", "进项"): ("BL-01", "BL-06", "BL-07"),
    ("合同资料", "主合同"): ("BL-01", "BL-03", "BL-06", "BL-08", "BL-09"),
    ("合同资料", "变更结算"): ("BL-01", "BL-08"),
    ("政策证据", "研发"): ("BL-06",),
    ("政策证据", "知识产权"): ("BL-06",),
}

_CANONICAL_SOURCE_KEYS: Tuple[Tuple[str, str], ...] = tuple(_SOURCE_BUSINESS_LINES.keys())
_SOURCE_HEADERS: Tuple[str, ...] = (
    "来源系统",
    "业务板块",
    "文件包/数据包",
    "公司主体",
    "银行/系统账户",
    "账户/报表/工作表",
    "建议频率",
    "初始状态",
    "影响功能/报告",
    "下一步",
)

_BUSINESS_LINE_PRIORITIES: Dict[str, str] = {
    "BL-01": "P0",
    "BL-02": "P1",
    "BL-03": "P1",
    "BL-04": "P1",
    "BL-05": "P1",
    "BL-06": "P1",
    "BL-07": "P1",
    "BL-08": "P1",
    "BL-09": "P2",
    "BL-10": "P2",
}

_SOURCE_ROW_FIELDS: Tuple[str, ...] = (
    "source_domain_row_id",
    "source_system_code",
    "source_system_name",
    "business_segment",
    "source_package_class",
    "entity_scope",
    "account_scope",
    "report_or_worksheet_scope",
    "expected_frequency",
    "template_initial_status",
    "impact_surfaces",
    "next_step",
    "business_line_ids",
    "lineage_kind",
    "allowed_locator_kinds",
    "human_review_required",
    "private_lineage_required",
    "publication_default",
    "source_row_hash",
    "source_ref",
)


def _source_row_hash(row: Mapping[str, Any]) -> str:
    payload = {key: row[key] for key in _SOURCE_ROW_FIELDS if key != "source_row_hash"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def parse_source_domain_csv(csv_input: Union[str, bytes]) -> List[Dict[str, Any]]:
    """Parse public TaskPack member 09 CSV content into canonical coverage rows."""

    if isinstance(csv_input, bytes):
        text = csv_input.decode("utf-8-sig")
    elif isinstance(csv_input, str):
        text = csv_input.lstrip("\ufeff")
    else:
        raise LineageContractError("source-domain CSV input must be str or bytes")

    reader = csv.DictReader(io.StringIO(text))
    if tuple(reader.fieldnames or ()) != _SOURCE_HEADERS:
        raise LineageContractError("source-domain CSV headers do not match public member 09")

    raw_by_key: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row_number, raw in enumerate(reader, start=2):
        normalized = {key: (raw.get(key) or "").strip() for key in _SOURCE_HEADERS}
        key = (normalized["来源系统"], normalized["业务板块"])
        if key in raw_by_key:
            raise LineageContractError("duplicate source-domain key at CSV row %d: %r" % (row_number, key))
        if key not in _SOURCE_BUSINESS_LINES:
            raise LineageContractError("unknown source-domain key at CSV row %d: %r" % (row_number, key))
        raw_by_key[key] = normalized

    if set(raw_by_key) != set(_CANONICAL_SOURCE_KEYS):
        missing = sorted(set(_CANONICAL_SOURCE_KEYS) - set(raw_by_key))
        extra = sorted(set(raw_by_key) - set(_CANONICAL_SOURCE_KEYS))
        raise LineageContractError("source-domain coverage mismatch: missing=%r extra=%r" % (missing, extra))

    rows: List[Dict[str, Any]] = []
    for index, key in enumerate(_CANONICAL_SOURCE_KEYS, start=1):
        raw = raw_by_key[key]
        system_name, segment = key
        system_code = _SOURCE_SYSTEM_CODES[system_name]
        lineage_kind = "DOCUMENT_EVIDENCE" if system_code in {"CONTRACT_DOCS", "POLICY_EVIDENCE"} else "DATA_VALUE"
        row: Dict[str, Any] = {
            "source_domain_row_id": "SRC-DOM-%03d" % index,
            "source_system_code": system_code,
            "source_system_name": system_name,
            "business_segment": segment,
            "source_package_class": raw["文件包/数据包"],
            "entity_scope": raw["公司主体"],
            "account_scope": raw["银行/系统账户"],
            "report_or_worksheet_scope": raw["账户/报表/工作表"],
            "expected_frequency": raw["建议频率"],
            "template_initial_status": raw["初始状态"],
            "impact_surfaces": [part for part in raw["影响功能/报告"].split("、") if part],
            "next_step": raw["下一步"],
            "business_line_ids": list(_SOURCE_BUSINESS_LINES[key]),
            "lineage_kind": lineage_kind,
            "allowed_locator_kinds": list(LOCATOR_KINDS),
            "human_review_required": True,
            "private_lineage_required": True,
            "publication_default": "BLOCKED",
            "source_ref": "SOURCE_PACKAGE_TOKEN::09_KMFA_数据源检查矩阵模板_v2_0.csv#row-%03d" % index,
        }
        row["source_row_hash"] = _source_row_hash(row)
        rows.append(row)
    return rows


def _build_business_line_profiles(source_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    profiles: List[Dict[str, Any]] = []
    for business_line_id, priority in _BUSINESS_LINE_PRIORITIES.items():
        source_ids = [
            str(row["source_domain_row_id"])
            for row in source_rows
            if business_line_id in row.get("business_line_ids", [])
        ]
        profiles.append(
            {
                "business_line_id": business_line_id,
                "priority": priority,
                "lineage_mode": "CONTROL_EVIDENCE_ONLY" if business_line_id == "BL-10" else "DATA_OR_DOCUMENT_LINEAGE",
                "source_domain_row_ids": source_ids,
                "publication_default": "BLOCKED",
                "product_implementation_allowed": False,
            }
        )
    return profiles


def _path_record_schema() -> Dict[str, Any]:
    return {
        "top_level_required_fields": list(TOP_LEVEL_PATH_FIELDS),
        "nested_required_fields": {key: list(value) for key, value in NESTED_REQUIRED_FIELDS.items()},
        "version_required_fields": list(VERSION_REQUIRED_FIELDS),
        "amount_semantics_required_fields": list(AMOUNT_SEMANTICS_REQUIRED_FIELDS),
        "amount_representation_allowed": ["INTEGER_CENTS", "DECIMAL_STRING"],
        "binary_float_allowed": False,
        "amount_tolerance_cents": 0,
        "unknown_parameter_policy": "BLOCK",
        "implicit_rounding_allowed": False,
        "legacy_version_ref_policy": "BLOCK_UNLESS_UNIQUELY_RESOLVED_TO_CANONICAL_ID_AND_SEMVER",
    }


def _identity_contract() -> Dict[str, Any]:
    return {
        "import_run_id_pattern": r"^IMP-[0-9]{8}-[0-9]{6}-[a-z0-9-]{3,40}-[a-f0-9]{8}$",
        "source_id_pattern": r"^SRC-[a-z0-9-]{3,40}-[a-f0-9]{8}$",
        "file_hash_pattern": r"^sha256:[a-f0-9]{64}$",
        "stable_versioned_id_pattern": r"^[A-Z][A-Z0-9-]{2,127}$",
        "semantic_version_pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$",
        "canonical_formula_binding": "formula_id@formula_version",
        "canonical_rule_binding": "rule_id@rule_version",
        "legacy_only_binding_publication_allowed": False,
    }


def _publication_contract() -> Dict[str, Any]:
    return {
        "publication_default": "BLOCKED",
        "amount_tolerance_cents": 0,
        "silent_error_count_required": 0,
        "internal_use_requires": [
            "critical_hard_gates_passed",
            "open_differences_explicitly_disclosed",
            "source_freshness_acceptable_or_disclosed",
            "lineage_path_complete",
        ],
        "external_use_requires": [
            "internal_use_requirements_passed",
            "manual_approval_complete",
            "no_open_critical_difference",
            "all_required_sources_ready",
            "page_api_metadata_export_consistent",
        ],
        "stop_when_any": [
            "missing_source_or_locator",
            "missing_rule_formula_parameter_or_report_version",
            "lineage_graph_disconnected_or_cyclic",
            "binary_float_in_amount_path",
            "implicit_rounding_or_nonzero_authoritative_delta",
            "hard_gate_missing_or_failed",
            "same_source_inconsistency_not_rerun",
            "cross_source_auto_selection",
            "required_human_review_missing",
            "page_api_metadata_export_mismatch",
            "raw_fingerprint_changed",
            "public_sensitive_or_inferable_private_content",
        ],
    }


def _public_private_plane_contract() -> Dict[str, Any]:
    return {
        "public_artifact_mode": "SCHEMA_COUNTS_AND_OPAQUE_REFS_ONLY",
        "private_runtime_required_for_actual_lineage": True,
        "public_actual_raw_values_allowed": False,
        "public_plaintext_filenames_allowed": False,
        "public_inferable_hash_locator_combination_allowed": False,
        "raw_access_performed_by_module": False,
        "raw_root_dependency_allowed": False,
    }


def _lineage_record_accounting() -> Dict[str, Any]:
    return {
        "field": {"protocol_header_count": 1, "actual_lineage_record_count": 0},
        "metric": {"protocol_header_count": 1, "actual_lineage_record_count": 0},
        "report": {"protocol_header_count": 1, "actual_lineage_record_count": 0},
        "total_actual_lineage_record_count": 0,
        "protocol_headers_count_as_actual": False,
    }


PAYLOAD_FIELDS: Tuple[str, ...] = (
    "schema_version",
    "record_type",
    "project_id",
    "target_release",
    "roadmap_phase_id",
    "task_id",
    "contract_version",
    "status",
    "generated_at",
    "actual_lineage_record_count",
    "lineage_full_check_complete",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "product_implementation_allowed",
    "github_upload_allowed",
    "app_reinstall_allowed",
    "identity_contract",
    "path_record_schema",
    "locator_kinds",
    "report_target_kinds",
    "hard_gates",
    "layer_edge_contract",
    "source_domain_coverage",
    "business_line_profiles",
    "lineage_record_accounting",
    "publication_contract",
    "public_private_plane_contract",
    "source_refs",
)


def build_lineage_contract_payload(
    source_domain_rows: Optional[Sequence[Mapping[str, Any]]] = None,
    generated_at: str = DEFAULT_GENERATED_AT,
) -> Dict[str, Any]:
    """Build the deterministic S02-P2 T02 planning contract."""

    if source_domain_rows is None:
        rows = parse_source_domain_csv(DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV)
    else:
        rows = [copy.deepcopy(dict(row)) for row in source_domain_rows]

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "roadmap_phase_id": "S02-P2",
        "task_id": "S02P2T02",
        "contract_version": CONTRACT_VERSION,
        "status": "PLANNING_CONTRACT_ONLY",
        "generated_at": generated_at,
        "actual_lineage_record_count": 0,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "product_implementation_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "identity_contract": _identity_contract(),
        "path_record_schema": _path_record_schema(),
        "locator_kinds": list(LOCATOR_KINDS),
        "report_target_kinds": list(REPORT_TARGET_KINDS),
        "hard_gates": list(HARD_GATES),
        "layer_edge_contract": _build_edge_contract(),
        "source_domain_coverage": rows,
        "business_line_profiles": _build_business_line_profiles(rows),
        "lineage_record_accounting": _lineage_record_accounting(),
        "publication_contract": _publication_contract(),
        "public_private_plane_contract": _public_private_plane_contract(),
        "source_refs": [
            "SOURCE_PACKAGE_TOKEN::06_KMFA_数据治理准确性与只读协议_v2_0.md",
            "SOURCE_PACKAGE_TOKEN::07_KMFA_界面交互全量重构规范_v2_0.md",
            "SOURCE_PACKAGE_TOKEN::08_KMFA_模型公式函数参数主注册表_v2_0.yaml",
            "SOURCE_PACKAGE_TOKEN::09_KMFA_数据源检查矩阵模板_v2_0.csv",
            "SOURCE_PACKAGE_TOKEN::10_KMFA_质量门禁与测试证据规范_v2_0.md",
            "SOURCE_PACKAGE_TOKEN::13_KMFA_阶段一与阶段二五环节信息继承清单_v2_0.md",
            "KMFA/metadata/protocol/metadata_protocol.yaml",
            "KMFA/metadata/lineage/field_lineage.jsonl",
            "KMFA/metadata/lineage/metric_lineage.jsonl",
            "KMFA/metadata/lineage/report_lineage.jsonl",
        ],
    }


def count_actual_lineage_records(rows: Iterable[Mapping[str, Any]]) -> int:
    """Count real lineage rows while explicitly excluding protocol headers."""

    count = 0
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise LineageContractError("lineage row %d must be an object" % index)
        record_type = row.get("record_type")
        if not isinstance(record_type, str) or not record_type:
            raise LineageContractError("lineage row %d has no record_type" % index)
        if record_type != "protocol_header":
            count += 1
    return count


def _require_exact_value(label: str, actual: Any, expected: Any) -> None:
    if type(actual) is not type(expected) or actual != expected:  # bool must not pass as int
        raise LineageContractError("%s: expected %r, got %r" % (label, expected, actual))


def _validate_source_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        raise LineageContractError("source_domain_coverage must be a list")
    if len(rows) != 21:
        raise LineageContractError("source_domain_coverage must contain exactly 21 rows")

    expected_ids = ["SRC-DOM-%03d" % index for index in range(1, 22)]
    keys: List[Tuple[str, str]] = []
    system_codes: List[str] = []
    covered_business_lines: set = set()
    validated: List[Dict[str, Any]] = []
    for index, value in enumerate(rows, start=1):
        if not isinstance(value, dict):
            raise LineageContractError("source-domain row %d must be an object" % index)
        if set(value) != set(_SOURCE_ROW_FIELDS):
            raise LineageContractError("source-domain row %d fields differ from contract" % index)
        row = value
        _require_exact_value("source-domain row id", row["source_domain_row_id"], expected_ids[index - 1])
        key = (row["source_system_name"], row["business_segment"])
        if key != _CANONICAL_SOURCE_KEYS[index - 1]:
            raise LineageContractError("source-domain row %d is not in canonical member 09 order" % index)
        expected_code = _SOURCE_SYSTEM_CODES.get(str(row["source_system_name"]))
        _require_exact_value("source-domain system code", row["source_system_code"], expected_code)
        if row["business_line_ids"] != list(_SOURCE_BUSINESS_LINES[key]):
            raise LineageContractError("source-domain row %d business-line mapping differs" % index)
        if "BL-10" in row["business_line_ids"]:
            raise LineageContractError("BL-10 is control/evidence only and cannot be forged as a source-domain row")
        if row["allowed_locator_kinds"] != list(LOCATOR_KINDS):
            raise LineageContractError("source-domain row %d locator kinds differ" % index)
        _require_exact_value("source-domain human review", row["human_review_required"], True)
        _require_exact_value("source-domain private lineage", row["private_lineage_required"], True)
        _require_exact_value("source-domain publication default", row["publication_default"], "BLOCKED")
        _require_exact_value("source-domain row hash", row["source_row_hash"], _source_row_hash(row))
        keys.append(key)
        system_codes.append(row["source_system_code"])
        covered_business_lines.update(row["business_line_ids"])
        validated.append(row)

    if len(set(keys)) != 21:
        raise LineageContractError("source-domain keys must be unique")
    distribution = Counter(system_codes)
    expected_distribution = Counter(
        {"REDCIRCLE": 4, "KINGDEE": 4, "WPS": 4, "BANK": 3, "TAX_EINVOICE": 2, "CONTRACT_DOCS": 2, "POLICY_EVIDENCE": 2}
    )
    if distribution != expected_distribution:
        raise LineageContractError("source-system distribution differs from public member 09")
    if covered_business_lines != {"BL-%02d" % index for index in range(1, 10)}:
        raise LineageContractError("source-domain rows must cover BL-01..BL-09 exactly")
    return validated


def validate_lineage_contract_payload(payload: Mapping[str, Any]) -> Dict[str, int]:
    """Fail-closed validation for the S02-P2 T02 planning payload."""

    if not isinstance(payload, Mapping):
        raise LineageContractError("lineage contract payload must be an object")
    if set(payload) != set(PAYLOAD_FIELDS):
        missing = sorted(set(PAYLOAD_FIELDS) - set(payload))
        extra = sorted(set(payload) - set(PAYLOAD_FIELDS))
        raise LineageContractError("payload fields differ: missing=%r extra=%r" % (missing, extra))

    fixed_values = {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "roadmap_phase_id": "S02-P2",
        "task_id": "S02P2T02",
        "contract_version": CONTRACT_VERSION,
        "status": "PLANNING_CONTRACT_ONLY",
        "actual_lineage_record_count": 0,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "product_implementation_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
    }
    for key, expected in fixed_values.items():
        _require_exact_value(key, payload.get(key), expected)
    if not isinstance(payload.get("generated_at"), str) or not payload["generated_at"]:
        raise LineageContractError("generated_at must be a non-empty deterministic string")

    _require_exact_value("identity_contract", payload["identity_contract"], _identity_contract())
    _require_exact_value("path_record_schema", payload["path_record_schema"], _path_record_schema())
    _require_exact_value("locator_kinds", payload["locator_kinds"], list(LOCATOR_KINDS))
    _require_exact_value("report_target_kinds", payload["report_target_kinds"], list(REPORT_TARGET_KINDS))
    _require_exact_value("hard_gates", payload["hard_gates"], list(HARD_GATES))
    _require_exact_value("layer_edge_contract", payload["layer_edge_contract"], _build_edge_contract())
    _require_exact_value("publication_contract", payload["publication_contract"], _publication_contract())
    _require_exact_value(
        "public_private_plane_contract", payload["public_private_plane_contract"], _public_private_plane_contract()
    )
    _require_exact_value("lineage_record_accounting", payload["lineage_record_accounting"], _lineage_record_accounting())

    source_rows = _validate_source_rows(payload["source_domain_coverage"])
    _require_exact_value(
        "business_line_profiles",
        payload["business_line_profiles"],
        _build_business_line_profiles(source_rows),
    )
    if not isinstance(payload["source_refs"], list) or len(payload["source_refs"]) < 6:
        raise LineageContractError("source_refs must contain the public contract authorities")

    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in ("/Users/", "KMFA_MetaData"):
        if forbidden in encoded:
            raise LineageContractError("public planning payload contains forbidden local/raw dependency: %s" % forbidden)

    return {
        "edge_count": len(payload["layer_edge_contract"]),
        "top_level_path_field_count": len(payload["path_record_schema"]["top_level_required_fields"]),
        "locator_kind_count": len(payload["locator_kinds"]),
        "report_target_kind_count": len(payload["report_target_kinds"]),
        "hard_gate_count": len(payload["hard_gates"]),
        "source_domain_row_count": len(source_rows),
        "source_system_count": len({row["source_system_code"] for row in source_rows}),
        "business_line_profile_count": len(payload["business_line_profiles"]),
        "actual_lineage_record_count": payload["actual_lineage_record_count"],
    }


__all__ = [
    "AMOUNT_SEMANTICS_REQUIRED_FIELDS",
    "CONTRACT_VERSION",
    "DEFAULT_PUBLIC_SOURCE_TEMPLATE_CSV",
    "HARD_GATES",
    "LOCATOR_KINDS",
    "LineageContractError",
    "REPORT_TARGET_KINDS",
    "SCHEMA_VERSION",
    "TOP_LEVEL_PATH_FIELDS",
    "VERSION_REQUIRED_FIELDS",
    "build_lineage_contract_payload",
    "count_actual_lineage_records",
    "parse_source_domain_csv",
    "validate_lineage_contract_payload",
]
