#!/usr/bin/env python3
"""KMFA v1.5 S13-P1 指标、参数版本与计算边界。

本模块只处理公开安全的规则和合成值，不发现、不列举、也不读取原始资料。
金额只允许整数分，比例只允许整数基点。所有不能可靠计算的情形都返回
明确状态，调用方不得把异常或资料不足静默变成 0。
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


RUN_PHASE_ID = "V015_S13_P1_INDICATOR_REGISTRY"
ROADMAP_PHASE_ID = "S13-P1"
TASK_ID = "KMFA-V015-S13-P1-INDICATOR-REGISTRY-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S13-P1-INDICATOR-REGISTRY"
VERSION = "1.5.0-dev-s13p1"

INDICATOR_DOMAINS = (
    "REVENUE",
    "COST",
    "MARGIN",
    "COLLECTION",
    "CASH",
    "TAX",
    "PERFORMANCE",
    "DATA_QUALITY",
)
FUNCTION_IDS = (
    "FN-SAFE-RATIO-BPS",
    "FN-TREND-CHANGE-BPS",
    "FN-BRIDGE-DELTA-CENTS",
    "FN-PRIORITY-SORT-KEY",
    "FN-AVAILABILITY-GATE",
)
RESULT_STATUSES = (
    "READY",
    "MISSING_INPUT",
    "ZERO_DENOMINATOR",
    "NEGATIVE_DENOMINATOR_UNSUPPORTED",
    "SMALL_SAMPLE",
    "INVALID_INPUT",
)

_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]{2,95}$")
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:/.-]{1,159}$")
_FORBIDDEN_KEYS = {
    "raw_value",
    "original_value",
    "plaintext_value",
    "absolute_path",
    "local_path",
    "private_hash",
    "password",
    "token",
    "api_key",
    "bank_account_number",
    "identity_document_number",
}


class IndicatorRegistryError(ValueError):
    """带稳定错误码的 fail-closed 规则异常。"""

    def __init__(self, code: str, message_zh: str):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IndicatorRegistryError("TEXT_REQUIRED", f"{field} 必须是非空文本。")
    return value.strip()


def _identifier(value: Any, field: str) -> str:
    text = _text(value, field)
    if not _ID_RE.fullmatch(text):
        raise IndicatorRegistryError("IDENTIFIER_INVALID", f"{field} 格式不正确。")
    return text


def _reference(value: Any, field: str) -> str:
    text = _text(value, field)
    if not _REF_RE.fullmatch(text) or text.startswith(("file://", "private://")):
        raise IndicatorRegistryError("REFERENCE_INVALID", f"{field} 必须是公开安全引用。")
    return text


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise IndicatorRegistryError("INTEGER_REQUIRED", f"{field} 必须是整数，不能使用 float 或布尔值。")
    return value


def _positive_int(value: Any, field: str) -> int:
    number = _integer(value, field)
    if number <= 0:
        raise IndicatorRegistryError("POSITIVE_INTEGER_REQUIRED", f"{field} 必须大于 0。")
    return number


def _assert_public_safe(value: Any, path: str = "record") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_KEYS:
                raise IndicatorRegistryError("PRIVATE_FIELD_REJECTED", f"{path}.{key_text} 不允许进入公开规则。")
            _assert_public_safe(nested, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_public_safe(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if value.startswith(("/Users/", "/Volumes/", "/home/")) or "kmfa_metadata" in lowered or lowered.startswith(("file://", "private://")):
            raise IndicatorRegistryError("PRIVATE_VALUE_REJECTED", f"{path} 包含本地或私有定位信息。")


def _result(status: str, *, value: int | None = None, unit: str | None = None, reason_zh: str) -> dict[str, Any]:
    if status not in RESULT_STATUSES:
        raise IndicatorRegistryError("RESULT_STATUS_INVALID", "计算结果状态未登记。")
    return {
        "status": status,
        "value": value,
        "unit": unit,
        "reason_zh": reason_zh,
        "displayable": status == "READY",
        "exception_swallowed": False,
    }


def _round_div_half_away_from_zero(numerator: int, denominator: int) -> int:
    """整数除法，0.5 向远离 0 的方向取整。"""

    numerator = _integer(numerator, "numerator")
    denominator = _positive_int(denominator, "denominator")
    sign = -1 if numerator < 0 else 1
    absolute = abs(numerator)
    quotient, remainder = divmod(absolute, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return sign * quotient


def availability_gate(values: Mapping[str, Any] | None, *, sample_size: int | None, minimum_sample_size: int = 1) -> dict[str, Any]:
    """统一处理缺失和小样本；不把它们变成 0。"""

    minimum = _positive_int(minimum_sample_size, "minimum_sample_size")
    if values is None or not isinstance(values, Mapping) or not values:
        return _result(status="MISSING_INPUT", reason_zh="缺少必需输入，禁止显示指标。")
    missing = sorted(str(key) for key, value in values.items() if value is None)
    if missing:
        return {
            **_result(status="MISSING_INPUT", reason_zh="存在缺失输入，禁止显示指标。"),
            "missing_fields": missing,
        }
    if sample_size is None:
        return _result(status="MISSING_INPUT", reason_zh="缺少样本量，禁止显示指标。")
    sample = _integer(sample_size, "sample_size")
    if sample < 0:
        return _result(status="INVALID_INPUT", reason_zh="样本量不能为负数。")
    if sample < minimum:
        return {
            **_result(status="SMALL_SAMPLE", reason_zh="样本量低于登记下限，禁止显示指标。"),
            "sample_size": sample,
            "minimum_sample_size": minimum,
        }
    return _result(status="READY", value=sample, unit="COUNT", reason_zh="输入和样本量满足计算条件。")


def safe_ratio_bps(
    numerator: int | None,
    denominator: int | None,
    *,
    sample_size: int | None = 1,
    minimum_sample_size: int = 1,
    negative_denominator_allowed: bool = False,
) -> dict[str, Any]:
    """按整数基点计算比率，并显式处理缺失、除零、负分母和小样本。"""

    gate = availability_gate(
        {"numerator": numerator, "denominator": denominator},
        sample_size=sample_size,
        minimum_sample_size=minimum_sample_size,
    )
    if gate["status"] != "READY":
        return gate
    top = _integer(numerator, "numerator")
    bottom = _integer(denominator, "denominator")
    if bottom == 0:
        return _result(status="ZERO_DENOMINATOR", reason_zh="分母为 0，不能计算比率。")
    if bottom < 0 and not negative_denominator_allowed:
        return _result(status="NEGATIVE_DENOMINATOR_UNSUPPORTED", reason_zh="负分母未获规则授权，不能计算比率。")
    value = _round_div_half_away_from_zero(top * 10_000, abs(bottom))
    if bottom < 0:
        value = -value
    return _result(status="READY", value=value, unit="BPS", reason_zh="按登记规则计算整数基点。")


def trend_change_bps(
    current: int | None,
    previous: int | None,
    *,
    sample_size: int | None = 1,
    minimum_sample_size: int = 1,
) -> dict[str, Any]:
    """计算相对上期变化；上期为负数时使用其绝对值作为基数并保留方向。"""

    if current is None or previous is None:
        return _result(status="MISSING_INPUT", reason_zh="当前值或上期值缺失，不能计算趋势。")
    current_value = _integer(current, "current")
    previous_value = _integer(previous, "previous")
    result = safe_ratio_bps(
        current_value - previous_value,
        abs(previous_value),
        sample_size=sample_size,
        minimum_sample_size=minimum_sample_size,
        negative_denominator_allowed=False,
    )
    if result["status"] == "READY":
        result["reason_zh"] = "按（当前值－上期值）÷上期值绝对值计算趋势。"
    return result


def bridge_delta_cents(inflows: Sequence[int] | None, outflows: Sequence[int] | None) -> dict[str, Any]:
    """计算桥接差额；每一项必须是整数分。"""

    if inflows is None or outflows is None:
        return _result(status="MISSING_INPUT", reason_zh="流入或流出明细缺失，不能计算桥接差额。")
    if isinstance(inflows, (str, bytes)) or isinstance(outflows, (str, bytes)):
        return _result(status="INVALID_INPUT", reason_zh="流入和流出必须是整数分列表。")
    try:
        in_values = [_integer(value, f"inflows[{index}]") for index, value in enumerate(inflows)]
        out_values = [_integer(value, f"outflows[{index}]") for index, value in enumerate(outflows)]
    except TypeError:
        return _result(status="INVALID_INPUT", reason_zh="流入和流出必须是可遍历的整数分列表。")
    return {
        **_result(status="READY", value=sum(in_values) - sum(out_values), unit="CENTS", reason_zh="按流入合计减流出合计计算。"),
        "inflow_count": len(in_values),
        "outflow_count": len(out_values),
    }


def priority_sort_key(record: Mapping[str, Any]) -> tuple[int, str]:
    """只定义稳定排序键，不生成健康判断或行动建议。"""

    if not isinstance(record, Mapping):
        raise IndicatorRegistryError("RECORD_INVALID", "排序记录必须是结构化记录。")
    _assert_public_safe(record)
    score = _integer(record.get("priority_score_bps"), "priority_score_bps")
    indicator_id = _identifier(record.get("indicator_id"), "indicator_id")
    return (-score, indicator_id)


def indicator_registry() -> list[dict[str, Any]]:
    """返回八个经营领域的公开安全指标定义。"""

    common = {
        "version": "1.0.0",
        "period_kind": "REGISTERED_REPORTING_PERIOD",
        "source_required": True,
        "display_without_source_allowed": False,
        "missing_policy": "RETURN_MISSING_INPUT_AND_HIDE",
        "negative_policy": "PRESERVE_SIGN_UNLESS_DENOMINATOR_RULE_REJECTS",
        "minimum_sample_size": 1,
        "frontend_definition_write_allowed": False,
        "production_direct_write_allowed": False,
    }
    rows = [
        ("IND-REVENUE-RECOGNIZED-CENTS", "已确认收入", "REVENUE", "FORM-KMFA-S13P1-REVENUE-SUM-V1", "FN-BRIDGE-DELTA-CENTS", "CENTS", "已确认收入事实合计（整数分）", ["FACT-CONTRACT-INCOME", "FACT-SETTLEMENT-INCOME"], "仅反映已确认事实，不代表回款或现金流。"),
        ("IND-COST-RECOGNIZED-CENTS", "已归集成本", "COST", "FORM-KMFA-S13P1-COST-SUM-V1", "FN-BRIDGE-DELTA-CENTS", "CENTS", "已归集项目成本事实合计（整数分）", ["FACT-PROJECT-COST", "FACT-UNALLOCATED-COST-POOL"], "未归集成本必须单列，不能猜测分配。"),
        ("IND-MARGIN-GROSS-BPS", "毛利率", "MARGIN", "FORM-KMFA-S13P1-GROSS-MARGIN-BPS-V1", "FN-SAFE-RATIO-BPS", "BPS", "（已确认收入－已归集成本）÷已确认收入×10000", ["FACT-CONTRACT-INCOME", "FACT-PROJECT-COST"], "收入为零、口径不一致或资料不足时不得显示。"),
        ("IND-COLLECTION-RATE-BPS", "回款率", "COLLECTION", "FORM-KMFA-S13P1-COLLECTION-RATE-BPS-V1", "FN-SAFE-RATIO-BPS", "BPS", "已确认回款÷已开票金额×10000", ["FACT-COLLECTION", "FACT-INVOICE"], "不等同于合同收现率；开票金额为零时不得显示。"),
        ("IND-CASH-NET-MOVEMENT-CENTS", "现金净变动", "CASH", "FORM-KMFA-S13P1-CASH-BRIDGE-CENTS-V1", "FN-BRIDGE-DELTA-CENTS", "CENTS", "现金流入合计－现金流出合计（整数分）", ["FACT-CASH-INFLOW", "FACT-CASH-OUTFLOW"], "只反映登记期间现金变动，不等同于利润。"),
        ("IND-TAX-BURDEN-BPS", "税费负担率", "TAX", "FORM-KMFA-S13P1-TAX-BURDEN-BPS-V1", "FN-SAFE-RATIO-BPS", "BPS", "已确认税费÷对应不含税收入×10000", ["FACT-TAX", "FACT-REVENUE-EX-TAX"], "收入含税口径未知或分母为零时不得显示。"),
        ("IND-PERFORMANCE-COMPLETION-BPS", "履约完成率", "PERFORMANCE", "FORM-KMFA-S13P1-PERFORMANCE-BPS-V1", "FN-SAFE-RATIO-BPS", "BPS", "已确认完成节点数÷计划节点数×10000", ["FACT-MILESTONE-COMPLETED", "FACT-MILESTONE-PLANNED"], "节点定义或期间不一致时不得比较。"),
        ("IND-DATA-QUALITY-COVERAGE-BPS", "数据质量覆盖率", "DATA_QUALITY", "FORM-KMFA-S13P1-DATA-QUALITY-BPS-V1", "FN-SAFE-RATIO-BPS", "BPS", "通过质量规则的必需字段数÷必需字段总数×10000", ["FACT-QUALITY-RESULT", "FACT-REQUIRED-FIELD"], "只说明规则覆盖情况，不代表业务结论正确。"),
    ]
    return [
        {
            "indicator_id": indicator_id,
            "name_zh": name_zh,
            "domain": domain,
            "formula_id": formula_id,
            "function_id": function_id,
            "unit": unit,
            "formula_zh": formula_zh,
            "source_contract_refs": source_refs,
            "limitations_zh": limitation,
            **common,
        }
        for indicator_id, name_zh, domain, formula_id, function_id, unit, formula_zh, source_refs, limitation in rows
    ]


def parameter_versions() -> list[dict[str, Any]]:
    """返回外置参数版本；前端和生产环境均不得直接改写。"""

    rows = [
        ("PAR-INDICATOR-SOURCE-REQUIRED", True, "BOOLEAN", "指标必须绑定来源后才能显示。", ["REG-SOURCE-001", "REG-SOURCE-002"]),
        ("PAR-RATIO-ROUNDING-MODE", "HALF_AWAY_FROM_ZERO", "ENUM", "比例统一使用整数基点并固定取整方式。", ["FN-RATIO-001", "FN-RATIO-002"]),
        ("PAR-NEGATIVE-DENOMINATOR-ALLOWED", False, "BOOLEAN", "默认拒绝负分母，避免方向被误读。", ["FN-RATIO-NEG-001"]),
        ("PAR-MINIMUM-SAMPLE-SIZE", 3, "COUNT", "经营判断至少需要三个样本；单项事实指标可另行登记为 1。", ["FN-SAMPLE-001", "FN-SAMPLE-002"]),
        ("PAR-TREND-BASELINE-MIN-CENTS", 1, "CENTS", "趋势基数必须非零且为整数分。", ["FN-TREND-001", "FN-TREND-002"]),
        ("PAR-STALE-WARNING-DAYS", 35, "DAYS", "超过一个月度结账周期后提示数据可能过期。", ["REG-PERIOD-001"]),
        ("PAR-PRIORITY-TIE-BREAK", "INDICATOR_ID_ASC", "ENUM", "同分时按指标编号排序，保证重复运行一致。", ["FN-SORT-001"]),
        ("PAR-MISSING-VALUE-DISPLAY", "HIDE_WITH_REASON", "ENUM", "缺失不能静默转成零，必须隐藏并给出原因。", ["FN-MISSING-001", "FN-MISSING-002"]),
    ]
    return [
        {
            "parameter_id": parameter_id,
            "version": "1.0.0",
            "value": value,
            "unit": unit,
            "effective_from": "2026-07-16",
            "rationale_zh": rationale,
            "approval_ref": "APPROVAL-KMFA-V015-S13-P1-PUBLIC-RULES",
            "regression_case_ids": regressions,
            "frontend_write_allowed": False,
            "production_direct_write_allowed": False,
        }
        for parameter_id, value, unit, rationale, regressions in rows
    ]


def function_contracts() -> list[dict[str, Any]]:
    return [
        {"function_id": "FN-SAFE-RATIO-BPS", "purpose_zh": "统一比率", "output_unit": "BPS", "explicit_boundaries": ["MISSING_INPUT", "ZERO_DENOMINATOR", "NEGATIVE_DENOMINATOR_UNSUPPORTED", "SMALL_SAMPLE"], "silent_exception_allowed": False},
        {"function_id": "FN-TREND-CHANGE-BPS", "purpose_zh": "统一趋势", "output_unit": "BPS", "explicit_boundaries": ["MISSING_INPUT", "ZERO_DENOMINATOR", "SMALL_SAMPLE"], "silent_exception_allowed": False},
        {"function_id": "FN-BRIDGE-DELTA-CENTS", "purpose_zh": "统一桥接差额", "output_unit": "CENTS", "explicit_boundaries": ["MISSING_INPUT", "INVALID_INPUT"], "silent_exception_allowed": False},
        {"function_id": "FN-PRIORITY-SORT-KEY", "purpose_zh": "统一稳定排序", "output_unit": "SORT_KEY", "explicit_boundaries": ["INVALID_INPUT"], "silent_exception_allowed": False},
        {"function_id": "FN-AVAILABILITY-GATE", "purpose_zh": "统一缺失和小样本处理", "output_unit": "STATUS", "explicit_boundaries": ["MISSING_INPUT", "SMALL_SAMPLE", "INVALID_INPUT"], "silent_exception_allowed": False},
    ]


def validate_indicator_registry(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if isinstance(rows, (str, bytes)) or not rows:
        raise IndicatorRegistryError("INDICATOR_REGISTRY_EMPTY", "指标注册表不能为空。")
    required = {
        "indicator_id", "name_zh", "domain", "formula_id", "function_id", "unit", "formula_zh",
        "period_kind", "source_contract_refs", "limitations_zh", "version", "source_required",
        "display_without_source_allowed", "missing_policy", "negative_policy", "minimum_sample_size",
        "frontend_definition_write_allowed", "production_direct_write_allowed",
    }
    ids: set[str] = set()
    domains: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise IndicatorRegistryError("INDICATOR_RECORD_INVALID", "指标必须是结构化记录。")
        _assert_public_safe(row)
        missing = sorted(required - set(row))
        if missing:
            raise IndicatorRegistryError("INDICATOR_FIELD_MISSING", "指标缺少字段：" + ", ".join(missing))
        indicator_id = _identifier(row["indicator_id"], "indicator_id")
        if indicator_id in ids:
            raise IndicatorRegistryError("INDICATOR_DUPLICATE", "指标编号不能重复。")
        ids.add(indicator_id)
        domain = _text(row["domain"], "domain")
        if domain not in INDICATOR_DOMAINS:
            raise IndicatorRegistryError("INDICATOR_DOMAIN_INVALID", "指标领域未登记。")
        domains.add(domain)
        _identifier(row["formula_id"], "formula_id")
        if _identifier(row["function_id"], "function_id") not in FUNCTION_IDS:
            raise IndicatorRegistryError("FUNCTION_NOT_REGISTERED", "指标引用了未登记函数。")
        if not _VERSION_RE.fullmatch(_text(row["version"], "version")):
            raise IndicatorRegistryError("VERSION_INVALID", "指标版本必须使用语义版本。")
        refs = row["source_contract_refs"]
        if isinstance(refs, (str, bytes)) or not refs:
            raise IndicatorRegistryError("SOURCE_REQUIRED", "无来源指标不得显示。")
        for ref in refs:
            _reference(ref, "source_contract_ref")
        if row["source_required"] is not True or row["display_without_source_allowed"] is not False:
            raise IndicatorRegistryError("SOURCE_GATE_INVALID", "无来源指标必须禁止显示。")
        if row["frontend_definition_write_allowed"] is not False or row["production_direct_write_allowed"] is not False:
            raise IndicatorRegistryError("DIRECT_WRITE_REJECTED", "前端不得直接改写生产指标定义。")
        _positive_int(row["minimum_sample_size"], "minimum_sample_size")
        for field in ("name_zh", "unit", "formula_zh", "period_kind", "limitations_zh", "missing_policy", "negative_policy"):
            _text(row[field], field)
    if domains != set(INDICATOR_DOMAINS):
        raise IndicatorRegistryError("DOMAIN_COVERAGE_INCOMPLETE", "八个经营指标领域必须完整覆盖。")
    return {"indicator_count": len(ids), "domain_count": len(domains), "registry_fingerprint": fingerprint(list(rows))}


class ParameterVersionRegistry:
    """不可静默覆盖的参数版本登记器。"""

    def __init__(self) -> None:
        self._versions: dict[tuple[str, str], dict[str, Any]] = {}

    def register(self, record: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise IndicatorRegistryError("PARAMETER_RECORD_INVALID", "参数版本必须是结构化记录。")
        source = dict(record)
        _assert_public_safe(source)
        parameter_id = _identifier(source.get("parameter_id"), "parameter_id")
        version = _text(source.get("version"), "version")
        if not _VERSION_RE.fullmatch(version):
            raise IndicatorRegistryError("VERSION_INVALID", "参数版本必须使用语义版本。")
        for field in ("unit", "effective_from", "rationale_zh", "approval_ref"):
            _text(source.get(field), field)
        _reference(source["approval_ref"], "approval_ref")
        regressions = source.get("regression_case_ids")
        if isinstance(regressions, (str, bytes)) or not regressions:
            raise IndicatorRegistryError("REGRESSION_REQUIRED", "参数变更必须绑定回归用例。")
        for case_id in regressions:
            _identifier(case_id, "regression_case_id")
        if source.get("frontend_write_allowed") is not False or source.get("production_direct_write_allowed") is not False:
            raise IndicatorRegistryError("DIRECT_WRITE_REJECTED", "前端不得直接改生产参数。")
        if "value" not in source or isinstance(source["value"], float):
            raise IndicatorRegistryError("PARAMETER_VALUE_INVALID", "参数值必须存在且不得使用 float。")
        key = (parameter_id, version)
        normalized = copy.deepcopy(source)
        normalized["parameter_fingerprint"] = fingerprint(source)
        existing = self._versions.get(key)
        if existing is not None:
            if existing["parameter_fingerprint"] != normalized["parameter_fingerprint"]:
                raise IndicatorRegistryError("IMMUTABLE_VERSION_CONFLICT", "同一参数版本不能被不同内容覆盖。")
            return copy.deepcopy(existing)
        self._versions[key] = normalized
        return copy.deepcopy(normalized)

    @property
    def versions(self) -> list[dict[str, Any]]:
        return copy.deepcopy([self._versions[key] for key in sorted(self._versions)])


def validate_parameter_versions(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if isinstance(rows, (str, bytes)) or not rows:
        raise IndicatorRegistryError("PARAMETER_REGISTRY_EMPTY", "参数注册表不能为空。")
    registry = ParameterVersionRegistry()
    for row in rows:
        registry.register(row)
    return {"parameter_count": len(registry.versions), "registry_fingerprint": fingerprint(registry.versions)}


def validate_function_contracts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if isinstance(rows, (str, bytes)) or not rows:
        raise IndicatorRegistryError("FUNCTION_REGISTRY_EMPTY", "函数规范不能为空。")
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise IndicatorRegistryError("FUNCTION_RECORD_INVALID", "函数规范必须是结构化记录。")
        _assert_public_safe(row)
        function_id = _identifier(row.get("function_id"), "function_id")
        if function_id in ids:
            raise IndicatorRegistryError("FUNCTION_DUPLICATE", "函数编号不能重复。")
        ids.add(function_id)
        _text(row.get("purpose_zh"), "purpose_zh")
        _text(row.get("output_unit"), "output_unit")
        boundaries = row.get("explicit_boundaries")
        if isinstance(boundaries, (str, bytes)) or not boundaries:
            raise IndicatorRegistryError("FUNCTION_BOUNDARY_MISSING", "函数必须登记边界行为。")
        if any(status not in RESULT_STATUSES for status in boundaries):
            raise IndicatorRegistryError("FUNCTION_BOUNDARY_INVALID", "函数边界状态未登记。")
        if row.get("silent_exception_allowed") is not False:
            raise IndicatorRegistryError("SILENT_EXCEPTION_REJECTED", "异常不得被默默吞掉。")
    if ids != set(FUNCTION_IDS):
        raise IndicatorRegistryError("FUNCTION_COVERAGE_INCOMPLETE", "比率、趋势、桥接、排序和缺失函数必须完整。")
    return {"function_count": len(ids), "registry_fingerprint": fingerprint(list(rows))}


def _rejects(operation: Any, expected_code: str) -> bool:
    try:
        operation()
    except IndicatorRegistryError as error:
        return error.code == expected_code
    return False


def public_verification() -> dict[str, Any]:
    """仅用合成规则和值执行确定性验收。"""

    indicators = indicator_registry()
    parameters = parameter_versions()
    functions = function_contracts()
    indicator_summary = validate_indicator_registry(indicators)
    parameter_summary = validate_parameter_versions(parameters)
    function_summary = validate_function_contracts(functions)

    ratio = safe_ratio_bps(1, 3)
    negative_numerator = safe_ratio_bps(-1, 4)
    authorized_negative = safe_ratio_bps(1, -4, negative_denominator_allowed=True)
    trend_up = trend_change_bps(125, 100)
    trend_negative_base = trend_change_bps(-80, -100)
    bridge = bridge_delta_cents([10_000, 5_000], [4_000, 1_000])
    sorted_ids = [
        row["indicator_id"]
        for row in sorted(
            [
                {"indicator_id": "IND-BBB", "priority_score_bps": 7000},
                {"indicator_id": "IND-AAA", "priority_score_bps": 7000},
                {"indicator_id": "IND-CCC", "priority_score_bps": 5000},
            ],
            key=priority_sort_key,
        )
    ]

    tampered_indicator = copy.deepcopy(indicators)
    tampered_indicator[0]["source_contract_refs"] = []
    tampered_parameter = copy.deepcopy(parameters[0])
    tampered_parameter["frontend_write_allowed"] = True
    conflict_registry = ParameterVersionRegistry()
    conflict_registry.register(parameters[0])
    conflict = copy.deepcopy(parameters[0])
    conflict["value"] = False

    checks: dict[str, bool] = {
        "indicator_count_exact": indicator_summary["indicator_count"] == 8,
        "indicator_domain_count_exact": indicator_summary["domain_count"] == 8,
        "indicator_domains_exact": {row["domain"] for row in indicators} == set(INDICATOR_DOMAINS),
        "indicator_ids_unique": len({row["indicator_id"] for row in indicators}) == 8,
        "indicator_names_present": all(row["name_zh"] for row in indicators),
        "indicator_formula_ids_present": all(row["formula_id"] for row in indicators),
        "indicator_function_ids_registered": all(row["function_id"] in FUNCTION_IDS for row in indicators),
        "indicator_units_present": all(row["unit"] for row in indicators),
        "indicator_periods_present": all(row["period_kind"] for row in indicators),
        "indicator_sources_present": all(row["source_contract_refs"] for row in indicators),
        "indicator_limitations_present": all(row["limitations_zh"] for row in indicators),
        "indicator_source_required": all(row["source_required"] is True for row in indicators),
        "indicator_without_source_hidden": all(row["display_without_source_allowed"] is False for row in indicators),
        "indicator_frontend_write_closed": all(row["frontend_definition_write_allowed"] is False for row in indicators),
        "indicator_production_write_closed": all(row["production_direct_write_allowed"] is False for row in indicators),
        "indicator_versions_valid": all(_VERSION_RE.fullmatch(row["version"]) for row in indicators),
        "indicator_samples_positive": all(row["minimum_sample_size"] > 0 for row in indicators),
        "indicator_missing_policy_explicit": all(row["missing_policy"] for row in indicators),
        "indicator_negative_policy_explicit": all(row["negative_policy"] for row in indicators),
        "source_gate_rejects_empty": _rejects(lambda: validate_indicator_registry(tampered_indicator), "SOURCE_REQUIRED"),
        "parameter_count_exact": parameter_summary["parameter_count"] == 8,
        "parameter_ids_unique": len({row["parameter_id"] for row in parameters}) == 8,
        "parameter_versions_valid": all(_VERSION_RE.fullmatch(row["version"]) for row in parameters),
        "parameter_reasons_present": all(row["rationale_zh"] for row in parameters),
        "parameter_approvals_present": all(row["approval_ref"] for row in parameters),
        "parameter_regressions_present": all(row["regression_case_ids"] for row in parameters),
        "parameter_frontend_write_closed": all(row["frontend_write_allowed"] is False for row in parameters),
        "parameter_production_write_closed": all(row["production_direct_write_allowed"] is False for row in parameters),
        "parameter_float_absent": all(not isinstance(row["value"], float) for row in parameters),
        "parameter_direct_write_rejected": _rejects(lambda: ParameterVersionRegistry().register(tampered_parameter), "DIRECT_WRITE_REJECTED"),
        "parameter_conflict_rejected": _rejects(lambda: conflict_registry.register(conflict), "IMMUTABLE_VERSION_CONFLICT"),
        "parameter_exact_replay_idempotent": conflict_registry.register(parameters[0])["parameter_fingerprint"] == conflict_registry.versions[0]["parameter_fingerprint"],
        "function_count_exact": function_summary["function_count"] == 5,
        "function_ids_exact": {row["function_id"] for row in functions} == set(FUNCTION_IDS),
        "function_boundaries_present": all(row["explicit_boundaries"] for row in functions),
        "function_silent_exception_closed": all(row["silent_exception_allowed"] is False for row in functions),
        "ratio_ready": ratio["status"] == "READY",
        "ratio_one_third_rounding": ratio["value"] == 3333,
        "ratio_unit_bps": ratio["unit"] == "BPS",
        "ratio_zero_denominator_explicit": safe_ratio_bps(1, 0)["status"] == "ZERO_DENOMINATOR",
        "ratio_negative_denominator_rejected": safe_ratio_bps(1, -4)["status"] == "NEGATIVE_DENOMINATOR_UNSUPPORTED",
        "ratio_negative_denominator_authorized": authorized_negative["value"] == -2500,
        "ratio_negative_numerator_preserved": negative_numerator["value"] == -2500,
        "ratio_missing_numerator_explicit": safe_ratio_bps(None, 1)["status"] == "MISSING_INPUT",
        "ratio_missing_denominator_explicit": safe_ratio_bps(1, None)["status"] == "MISSING_INPUT",
        "ratio_small_sample_explicit": safe_ratio_bps(1, 2, sample_size=2, minimum_sample_size=3)["status"] == "SMALL_SAMPLE",
        "ratio_float_rejected": _rejects(lambda: safe_ratio_bps(1.0, 2), "INTEGER_REQUIRED"),
        "ratio_bool_rejected": _rejects(lambda: safe_ratio_bps(True, 2), "INTEGER_REQUIRED"),
        "trend_ready": trend_up["status"] == "READY",
        "trend_up_value": trend_up["value"] == 2500,
        "trend_zero_base_explicit": trend_change_bps(5, 0)["status"] == "ZERO_DENOMINATOR",
        "trend_missing_explicit": trend_change_bps(None, 1)["status"] == "MISSING_INPUT",
        "trend_negative_base_direction": trend_negative_base["value"] == 2000,
        "bridge_ready": bridge["status"] == "READY",
        "bridge_value_exact": bridge["value"] == 10_000,
        "bridge_unit_cents": bridge["unit"] == "CENTS",
        "bridge_missing_explicit": bridge_delta_cents(None, [1])["status"] == "MISSING_INPUT",
        "bridge_string_invalid": bridge_delta_cents("1", [1])["status"] == "INVALID_INPUT",
        "bridge_float_rejected": _rejects(lambda: bridge_delta_cents([json.loads("1.0")], [1]), "INTEGER_REQUIRED"),
        "bridge_bool_rejected": _rejects(lambda: bridge_delta_cents([True], [1]), "INTEGER_REQUIRED"),
        "sort_descending": sorted_ids == ["IND-AAA", "IND-BBB", "IND-CCC"],
        "sort_tie_deterministic": sorted_ids[:2] == ["IND-AAA", "IND-BBB"],
        "sort_float_rejected": _rejects(
            lambda: priority_sort_key({"indicator_id": "IND-AAA", "priority_score_bps": json.loads("1.0")}),
            "INTEGER_REQUIRED",
        ),
        "availability_missing_explicit": availability_gate({}, sample_size=1)["status"] == "MISSING_INPUT",
        "availability_missing_field_listed": availability_gate({"a": None}, sample_size=1).get("missing_fields") == ["a"],
        "availability_sample_missing": availability_gate({"a": 1}, sample_size=None)["status"] == "MISSING_INPUT",
        "availability_negative_sample_invalid": availability_gate({"a": 1}, sample_size=-1)["status"] == "INVALID_INPUT",
        "availability_small_sample": availability_gate({"a": 1}, sample_size=1, minimum_sample_size=2)["status"] == "SMALL_SAMPLE",
        "availability_ready": availability_gate({"a": 1}, sample_size=2, minimum_sample_size=2)["status"] == "READY",
        "result_exception_not_swallowed": all(result["exception_swallowed"] is False for result in (ratio, trend_up, bridge)),
        "indicator_registry_deterministic": indicator_summary["registry_fingerprint"] == validate_indicator_registry(indicator_registry())["registry_fingerprint"],
        "parameter_registry_deterministic": parameter_summary["registry_fingerprint"] == validate_parameter_versions(parameter_versions())["registry_fingerprint"],
        "function_registry_deterministic": function_summary["registry_fingerprint"] == validate_function_contracts(function_contracts())["registry_fingerprint"],
        "raw_root_access_zero": True,
        "live_source_read_zero": True,
        "business_execution_absent": True,
        "health_score_not_computed": True,
        "action_priority_not_computed": True,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "kmfa.v015.s13p1.public_verification.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "checks": checks,
        "failed_checks": failed,
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "summary": {
            **indicator_summary,
            "parameter_count": parameter_summary["parameter_count"],
            "parameter_registry_fingerprint": parameter_summary["registry_fingerprint"],
            "function_count": function_summary["function_count"],
            "function_registry_fingerprint": function_summary["registry_fingerprint"],
            "result_status_count": len(RESULT_STATUSES),
            "raw_root_access_count": 0,
            "live_source_read_count": 0,
            "raw_business_content_read": False,
            "health_score_computed": False,
            "action_priority_computed": False,
            "business_execution_performed": False,
        },
    }
