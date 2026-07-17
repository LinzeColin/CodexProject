#!/usr/bin/env python3
"""KMFA v1.5 S11-P1 deterministic public-safe quality rule engine.

The engine translates technical checks into four human-facing outcomes while
keeping rule identifiers and diagnostics inside ``professional_detail``.  It
uses integer basis points only.  A failed hard gate always wins over the
weighted score, so a high average can never hide a critical data problem.

This module evaluates caller-supplied aggregate counters.  It does not discover,
list, read, hash, copy, or mutate any raw-data path.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from typing import Any, Mapping


RUN_PHASE_ID = "V015_S11_P1_QUALITY_RULES"
ROADMAP_PHASE_ID = "S11-P1"
TASK_ID = "KMFA-V015-S11-P1-QUALITY-RULES-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S11-P1-QUALITY-RULES"
VERSION = "1.5.0-dev-s11p1"

CATALOG_SCHEMA = "kmfa.v015.s11p1.quality_rule_catalog.v1"
STATUS_SCHEMA = "kmfa.v015.s11p1.quality_status_model.v1"
SCORE_SCHEMA = "kmfa.v015.s11p1.quality_score_policy.v1"
RESULT_SCHEMA = "kmfa.v015.s11p1.quality_result.v1"

DIMENSIONS = (
    ("COMPLETENESS", "完整性"),
    ("UNIQUENESS", "唯一性"),
    ("RANGE", "范围"),
    ("FORMAT", "格式"),
    ("RELATION", "关系"),
    ("RECONCILIATION", "勾稽"),
    ("FRESHNESS", "新鲜度"),
    ("CONSISTENCY", "一致性"),
)

STATUS_CODES = ("PASSED", "REVIEW_REQUIRED", "NOT_USABLE", "OUTDATED")
STATUS_LABELS_ZH = ("已通过", "需确认", "不可使用", "已过期")
SEVERITIES = ("BLOCKING", "REVIEW", "NOTICE")
PROCESS_IMPACTS = ("BLOCK_RELEASE", "REQUIRE_CONFIRMATION", "MARK_OUTDATED", "CONTINUE")


class QualityRuleError(ValueError):
    """Fail-closed configuration or input error with a stable reason code."""

    def __init__(self, code: str, message_zh: str):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _rule(
    rule_id: str,
    dimension: str,
    name_zh: str,
    field: str,
    *,
    severity: str,
    process_impact: str,
    hard_gate: bool,
    failure_reason_zh: str,
    next_action_zh: str,
    operator: str = "eq",
    expected: int | None = 0,
    comparison_field: str | None = None,
) -> dict[str, Any]:
    evaluator: dict[str, Any] = {"operator": operator, "field": field}
    if operator == "eq":
        evaluator["expected"] = expected
    else:
        evaluator["comparison_field"] = comparison_field
    return {
        "rule_id": rule_id,
        "dimension": dimension,
        "name_zh": name_zh,
        "severity": severity,
        "process_impact": process_impact,
        "hard_gate": hard_gate,
        "weight_bps": 625,
        "evaluator": evaluator,
        "failure_reason_zh": failure_reason_zh,
        "next_action_zh": next_action_zh,
    }


def default_rule_catalog() -> dict[str, Any]:
    """Return the complete externalizable 16-rule catalog."""

    rules = [
        _rule("QR-COMPLETENESS-001", "COMPLETENESS", "必填字段齐全", "missing_required_field_count", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="存在缺失的必填字段。", next_action_zh="补齐缺失字段后重新检查。"),
        _rule("QR-COMPLETENESS-002", "COMPLETENESS", "应到表单齐全", "missing_expected_table_count", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="应到文件或工作表不完整。", next_action_zh="补交缺失文件或工作表后重新检查。"),
        _rule("QR-UNIQUENESS-001", "UNIQUENESS", "主键不重复", "duplicate_primary_key_count", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="发现重复主键，可能造成重复计算。", next_action_zh="确认并去除重复主键记录。"),
        _rule("QR-UNIQUENESS-002", "UNIQUENESS", "来源记录不重复", "duplicate_source_record_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="来源中有疑似重复记录。", next_action_zh="确认重复记录是否应保留。"),
        _rule("QR-RANGE-001", "RANGE", "数值在允许范围内", "out_of_range_value_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="存在超出允许范围的数值。", next_action_zh="核对异常数值及其业务依据。"),
        _rule("QR-RANGE-002", "RANGE", "枚举值已登记", "unregistered_enum_value_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="存在未登记的分类值。", next_action_zh="确认新分类或改正错误分类。"),
        _rule("QR-FORMAT-001", "FORMAT", "字段格式正确", "invalid_format_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="部分字段格式无法按既定规则识别。", next_action_zh="按提示修正日期、编号或文本格式。"),
        _rule("QR-FORMAT-002", "FORMAT", "字段类型正确", "type_mismatch_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="部分字段的数据类型不符合约定。", next_action_zh="修正字段类型或确认映射版本。"),
        _rule("QR-RELATION-001", "RELATION", "关联记录可追溯", "orphan_reference_count", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="存在找不到对应主体或主记录的孤立数据。", next_action_zh="补齐关联主记录或纠正关联编号。"),
        _rule("QR-RELATION-002", "RELATION", "主体与期间已绑定", "entity_period_binding_missing_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="部分记录缺少主体或期间归属。", next_action_zh="确认主体和期间后重新检查。"),
        _rule("QR-RECONCILIATION-001", "RECONCILIATION", "金额勾稽零差异", "reconciliation_delta_cents", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="金额勾稽存在分币差异。", next_action_zh="查明差异来源并重新勾稽。"),
        _rule("QR-RECONCILIATION-002", "RECONCILIATION", "记录已完成勾稽", "unreconciled_record_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="仍有记录未完成勾稽。", next_action_zh="完成未勾稽记录的核对。"),
        _rule("QR-FRESHNESS-001", "FRESHNESS", "来源仍在有效期内", "source_age_minutes", severity="NOTICE", process_impact="MARK_OUTDATED", hard_gate=False, failure_reason_zh="来源数据已超过允许更新时间。", next_action_zh="获取最新来源后重新检查。", operator="lte_field", expected=None, comparison_field="freshness_limit_minutes"),
        _rule("QR-FRESHNESS-002", "FRESHNESS", "数据期间一致", "period_mismatch_count", severity="REVIEW", process_impact="REQUIRE_CONFIRMATION", hard_gate=False, failure_reason_zh="存在期间不一致的记录。", next_action_zh="确认记录所属期间后重新检查。"),
        _rule("QR-CONSISTENCY-001", "CONSISTENCY", "同来源事实一致", "same_source_conflict_count", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="同一来源出现互相冲突的事实。", next_action_zh="解决同来源冲突后重新检查。"),
        _rule("QR-CONSISTENCY-002", "CONSISTENCY", "跨来源冲突已处理", "cross_source_unresolved_count", severity="BLOCKING", process_impact="BLOCK_RELEASE", hard_gate=True, failure_reason_zh="跨来源冲突尚未明确处理。", next_action_zh="由有权限人员确认采用或排除依据。"),
    ]
    return {
        "schema_version": CATALOG_SCHEMA,
        "version": VERSION,
        "dimensions": [{"code": code, "label_zh": label} for code, label in DIMENSIONS],
        "rules": rules,
    }


def default_status_model() -> dict[str, Any]:
    """Return four human-readable statuses; color is always supplemental."""

    return {
        "schema_version": STATUS_SCHEMA,
        "statuses": [
            {"technical_status": "PASSED", "label_zh": "已通过", "symbol": "✓", "color_token": "STATUS_SUCCESS", "summary_zh": "本次检查未发现阻塞问题。", "process_impact_zh": "可以继续质量流程。", "next_action_zh": "继续下一步。"},
            {"technical_status": "REVIEW_REQUIRED", "label_zh": "需确认", "symbol": "!", "color_token": "STATUS_WARNING", "summary_zh": "存在需要人工确认的问题。", "process_impact_zh": "确认前不进入正式发布。", "next_action_zh": "按问题提示逐项确认。"},
            {"technical_status": "NOT_USABLE", "label_zh": "不可使用", "symbol": "×", "color_token": "STATUS_DANGER", "summary_zh": "存在关键失败或过多未解决问题。", "process_impact_zh": "阻止正式发布和后续使用。", "next_action_zh": "先修复关键问题，再重新检查。"},
            {"technical_status": "OUTDATED", "label_zh": "已过期", "symbol": "⌛", "color_token": "STATUS_MUTED", "summary_zh": "来源数据已超过有效期。", "process_impact_zh": "更新前不进入正式发布。", "next_action_zh": "获取最新数据后重新检查。"},
        ],
        "technical_detail_location": "professional_detail",
        "color_is_only_information": False,
        "text_label_required": True,
        "symbol_required": True,
        "reason_required": True,
        "next_action_required": True,
    }


def default_score_policy() -> dict[str, Any]:
    """Return externalized integer thresholds and hard-gate precedence."""

    return {
        "schema_version": SCORE_SCHEMA,
        "score_scale_bps": 10000,
        "pass_min_bps": 9500,
        "not_usable_below_bps": 7500,
        "precedence": ["HARD_GATE_FAILURE", "OUTDATED", "LOW_SCORE", "REVIEW_REQUIRED", "PASSED"],
        "hard_gate_overrides_score": True,
        "integer_only": True,
        "formal_report_allowed_in_this_phase": False,
    }


def _positive_int(value: Any, code: str, message_zh: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise QualityRuleError(code, message_zh)
    return value


def _nonnegative_int(value: Any, code: str, message_zh: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QualityRuleError(code, message_zh)
    return value


def validate_configuration(
    catalog: Mapping[str, Any],
    status_model: Mapping[str, Any],
    score_policy: Mapping[str, Any],
) -> None:
    """Fail closed when rule, status, or score configuration is incomplete."""

    if catalog.get("schema_version") != CATALOG_SCHEMA:
        raise QualityRuleError("CATALOG_SCHEMA_INVALID", "质量规则库版本不受支持。")
    dimensions = catalog.get("dimensions")
    rules = catalog.get("rules")
    if not isinstance(dimensions, list) or not isinstance(rules, list):
        raise QualityRuleError("CATALOG_STRUCTURE_INVALID", "质量规则库结构不完整。")
    dimension_codes = [row.get("code") for row in dimensions if isinstance(row, Mapping)]
    if dimension_codes != [code for code, _ in DIMENSIONS]:
        raise QualityRuleError("DIMENSION_SET_INVALID", "质量维度必须完整且顺序固定。")
    if len(rules) != 16:
        raise QualityRuleError("RULE_COUNT_INVALID", "质量规则必须恰好覆盖 16 条。")
    ids = [row.get("rule_id") for row in rules if isinstance(row, Mapping)]
    if len(ids) != len(set(ids)) or any(not isinstance(value, str) or not value for value in ids):
        raise QualityRuleError("RULE_ID_INVALID", "质量规则编号必须完整且唯一。")
    counts = Counter(row.get("dimension") for row in rules if isinstance(row, Mapping))
    if counts != Counter({code: 2 for code, _ in DIMENSIONS}):
        raise QualityRuleError("DIMENSION_COVERAGE_INVALID", "每个质量维度必须恰好有两条规则。")
    total_weight = 0
    for rule in rules:
        if not isinstance(rule, Mapping):
            raise QualityRuleError("RULE_STRUCTURE_INVALID", "质量规则必须是结构化对象。")
        if rule.get("severity") not in SEVERITIES or rule.get("process_impact") not in PROCESS_IMPACTS:
            raise QualityRuleError("RULE_IMPACT_INVALID", "每条规则必须绑定有效严重度和流程影响。")
        if not isinstance(rule.get("hard_gate"), bool):
            raise QualityRuleError("HARD_GATE_FLAG_INVALID", "每条规则必须明确是否为关键门禁。")
        for key in ("name_zh", "failure_reason_zh", "next_action_zh"):
            if not isinstance(rule.get(key), str) or not rule[key].strip():
                raise QualityRuleError("RULE_HUMAN_TEXT_MISSING", "每条规则必须包含中文名称、原因和下一步。")
        total_weight += _positive_int(rule.get("weight_bps"), "RULE_WEIGHT_INVALID", "规则权重必须是正整数。")
        evaluator = rule.get("evaluator")
        if not isinstance(evaluator, Mapping) or evaluator.get("operator") not in {"eq", "lte_field"}:
            raise QualityRuleError("RULE_EVALUATOR_INVALID", "规则判断方式不受支持。")
        if not isinstance(evaluator.get("field"), str) or not evaluator["field"]:
            raise QualityRuleError("RULE_FIELD_INVALID", "规则必须绑定检查字段。")
        if evaluator["operator"] == "eq":
            _nonnegative_int(evaluator.get("expected"), "RULE_EXPECTED_INVALID", "相等规则目标值必须是非负整数。")
        elif not isinstance(evaluator.get("comparison_field"), str) or not evaluator["comparison_field"]:
            raise QualityRuleError("RULE_COMPARISON_FIELD_INVALID", "比较规则必须绑定阈值字段。")
    if total_weight != 10000:
        raise QualityRuleError("RULE_WEIGHT_TOTAL_INVALID", "规则总权重必须等于 10000 个基点。")

    if status_model.get("schema_version") != STATUS_SCHEMA:
        raise QualityRuleError("STATUS_SCHEMA_INVALID", "质量状态模型版本不受支持。")
    statuses = status_model.get("statuses")
    if not isinstance(statuses, list) or [row.get("technical_status") for row in statuses if isinstance(row, Mapping)] != list(STATUS_CODES):
        raise QualityRuleError("STATUS_SET_INVALID", "质量状态必须完整覆盖四种结果。")
    if [row.get("label_zh") for row in statuses] != list(STATUS_LABELS_ZH):
        raise QualityRuleError("STATUS_LABEL_INVALID", "质量状态必须使用约定的人类语言。")
    for status in statuses:
        for key in ("label_zh", "symbol", "color_token", "summary_zh", "process_impact_zh", "next_action_zh"):
            if not isinstance(status.get(key), str) or not status[key].strip():
                raise QualityRuleError("STATUS_HUMAN_TEXT_MISSING", "质量状态必须包含文字、符号、原因和下一步。")
    required_flags = ("text_label_required", "symbol_required", "reason_required", "next_action_required")
    if any(status_model.get(flag) is not True for flag in required_flags) or status_model.get("color_is_only_information") is not False:
        raise QualityRuleError("COLOR_ONLY_STATUS_REJECTED", "颜色不能作为状态的唯一信息。")
    if status_model.get("technical_detail_location") != "professional_detail":
        raise QualityRuleError("TECHNICAL_DETAIL_LOCATION_INVALID", "技术等级只能放在专业详情中。")

    if score_policy.get("schema_version") != SCORE_SCHEMA:
        raise QualityRuleError("SCORE_SCHEMA_INVALID", "质量评分策略版本不受支持。")
    scale = _positive_int(score_policy.get("score_scale_bps"), "SCORE_SCALE_INVALID", "评分满分必须是正整数。")
    pass_min = _positive_int(score_policy.get("pass_min_bps"), "PASS_THRESHOLD_INVALID", "通过阈值必须是正整数。")
    low = _positive_int(score_policy.get("not_usable_below_bps"), "LOW_THRESHOLD_INVALID", "不可用阈值必须是正整数。")
    if not 0 < low < pass_min <= scale or scale != total_weight:
        raise QualityRuleError("SCORE_THRESHOLD_ORDER_INVALID", "评分阈值顺序或满分不正确。")
    if score_policy.get("precedence") != ["HARD_GATE_FAILURE", "OUTDATED", "LOW_SCORE", "REVIEW_REQUIRED", "PASSED"]:
        raise QualityRuleError("SCORE_PRECEDENCE_INVALID", "质量结果优先级不正确。")
    if score_policy.get("hard_gate_overrides_score") is not True or score_policy.get("integer_only") is not True:
        raise QualityRuleError("SCORE_SAFETY_INVALID", "关键门禁必须优先且评分只能使用整数。")
    if score_policy.get("formal_report_allowed_in_this_phase") is not False:
        raise QualityRuleError("PREMATURE_REPORT_RELEASE", "本阶段不得开放正式报告。")


def _required_snapshot_fields(catalog: Mapping[str, Any]) -> set[str]:
    fields: set[str] = set()
    for rule in catalog["rules"]:
        evaluator = rule["evaluator"]
        fields.add(evaluator["field"])
        if evaluator["operator"] == "lte_field":
            fields.add(evaluator["comparison_field"])
    return fields


def validate_snapshot(snapshot: Mapping[str, Any], catalog: Mapping[str, Any]) -> None:
    if not isinstance(snapshot, Mapping):
        raise QualityRuleError("SNAPSHOT_INVALID", "质量检查输入必须是结构化对象。")
    missing = sorted(_required_snapshot_fields(catalog) - set(snapshot))
    if missing:
        raise QualityRuleError("SNAPSHOT_FIELD_MISSING", "质量检查输入缺少必要字段。")
    for field in _required_snapshot_fields(catalog):
        _nonnegative_int(snapshot[field], "SNAPSHOT_VALUE_INVALID", "质量检查计数必须是非负整数。")
    _positive_int(snapshot["freshness_limit_minutes"], "FRESHNESS_LIMIT_INVALID", "有效期阈值必须是正整数。")


def evaluate_quality(
    snapshot: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any] | None = None,
    status_model: Mapping[str, Any] | None = None,
    score_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate aggregate counters and return a human-first quality result."""

    catalog_value = copy.deepcopy(catalog if catalog is not None else default_rule_catalog())
    status_value = copy.deepcopy(status_model if status_model is not None else default_status_model())
    policy_value = copy.deepcopy(score_policy if score_policy is not None else default_score_policy())
    validate_configuration(catalog_value, status_value, policy_value)
    validate_snapshot(snapshot, catalog_value)

    rule_results: list[dict[str, Any]] = []
    score_bps = 0
    for rule in catalog_value["rules"]:
        evaluator = rule["evaluator"]
        actual = snapshot[evaluator["field"]]
        if evaluator["operator"] == "eq":
            expected = evaluator["expected"]
            passed = actual == expected
            comparison = f"{actual} == {expected}"
        else:
            limit = snapshot[evaluator["comparison_field"]]
            passed = actual <= limit
            comparison = f"{actual} <= {limit}"
        if passed:
            score_bps += rule["weight_bps"]
        rule_results.append({
            "rule_id": rule["rule_id"],
            "dimension": rule["dimension"],
            "severity": rule["severity"],
            "process_impact": rule["process_impact"],
            "hard_gate": rule["hard_gate"],
            "passed": passed,
            "weight_bps": rule["weight_bps"],
            "comparison": comparison,
            "failure_reason_zh": None if passed else rule["failure_reason_zh"],
            "next_action_zh": None if passed else rule["next_action_zh"],
        })

    failed = [row for row in rule_results if not row["passed"]]
    hard_failures = [row for row in failed if row["hard_gate"]]
    outdated = any(row["process_impact"] == "MARK_OUTDATED" for row in failed)
    if hard_failures:
        technical_status = "NOT_USABLE"
    elif outdated:
        technical_status = "OUTDATED"
    elif score_bps < policy_value["not_usable_below_bps"]:
        technical_status = "NOT_USABLE"
    elif failed or score_bps < policy_value["pass_min_bps"]:
        technical_status = "REVIEW_REQUIRED"
    else:
        technical_status = "PASSED"

    status = next(row for row in status_value["statuses"] if row["technical_status"] == technical_status)
    primary_failure = hard_failures[0] if hard_failures else (failed[0] if failed else None)
    display = {
        "label_zh": status["label_zh"],
        "symbol": status["symbol"],
        "summary_zh": status["summary_zh"],
        "reason_zh": primary_failure["failure_reason_zh"] if primary_failure else "全部质量规则均已通过。",
        "process_impact_zh": status["process_impact_zh"],
        "next_action_zh": primary_failure["next_action_zh"] if primary_failure else status["next_action_zh"],
        "color_token": status["color_token"],
        "color_is_supplemental": True,
    }
    result = {
        "schema_version": RESULT_SCHEMA,
        "display": display,
        "quality_flow_allowed": technical_status == "PASSED",
        "formal_report_allowed": False,
        "professional_detail": {
            "technical_status": technical_status,
            "score_bps": score_bps,
            "score_scale_bps": policy_value["score_scale_bps"],
            "passed_rule_count": len(rule_results) - len(failed),
            "failed_rule_count": len(failed),
            "hard_gate_failure_count": len(hard_failures),
            "outdated_rule_failure_count": sum(row["process_impact"] == "MARK_OUTDATED" for row in failed),
            "rule_results": rule_results,
            "catalog_fingerprint": _fingerprint(catalog_value),
            "status_model_fingerprint": _fingerprint(status_value),
            "score_policy_fingerprint": _fingerprint(policy_value),
        },
    }
    result["evaluation_fingerprint"] = _fingerprint(result)
    return result


def baseline_snapshot() -> dict[str, int]:
    return {
        "missing_required_field_count": 0,
        "missing_expected_table_count": 0,
        "duplicate_primary_key_count": 0,
        "duplicate_source_record_count": 0,
        "out_of_range_value_count": 0,
        "unregistered_enum_value_count": 0,
        "invalid_format_count": 0,
        "type_mismatch_count": 0,
        "orphan_reference_count": 0,
        "entity_period_binding_missing_count": 0,
        "reconciliation_delta_cents": 0,
        "unreconciled_record_count": 0,
        "source_age_minutes": 60,
        "freshness_limit_minutes": 1440,
        "period_mismatch_count": 0,
        "same_source_conflict_count": 0,
        "cross_source_unresolved_count": 0,
    }


def public_scenarios() -> dict[str, dict[str, int]]:
    """Return synthetic aggregate-only scenarios; no business values are present."""

    base = baseline_snapshot()
    scenarios = {"all_pass": dict(base)}
    critical = dict(base)
    critical["duplicate_primary_key_count"] = 1
    scenarios["high_score_critical_failure"] = critical
    review = dict(base)
    review["invalid_format_count"] = 1
    scenarios["review_required"] = review
    outdated = dict(base)
    outdated["source_age_minutes"] = 1441
    scenarios["outdated_source"] = outdated
    low = dict(base)
    for field in (
        "duplicate_source_record_count",
        "out_of_range_value_count",
        "invalid_format_count",
        "type_mismatch_count",
        "unreconciled_record_count",
    ):
        low[field] = 1
    scenarios["low_score_without_hard_gate"] = low
    return scenarios


def public_verification() -> dict[str, Any]:
    """Execute deterministic rule/status/score checks on public synthetic counters."""

    catalog = default_rule_catalog()
    statuses = default_status_model()
    policy = default_score_policy()
    validate_configuration(catalog, statuses, policy)
    results = {name: evaluate_quality(snapshot, catalog=catalog, status_model=statuses, score_policy=policy) for name, snapshot in public_scenarios().items()}
    checks: list[dict[str, Any]] = []

    def check(check_id: str, condition: bool) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL"})

    dimension_counts = Counter(rule["dimension"] for rule in catalog["rules"])
    check("RULE_COUNT_16", len(catalog["rules"]) == 16)
    check("DIMENSION_COUNT_8", len(catalog["dimensions"]) == 8)
    check("TWO_RULES_PER_DIMENSION", all(value == 2 for value in dimension_counts.values()))
    check("HARD_GATE_COUNT_7", sum(rule["hard_gate"] for rule in catalog["rules"]) == 7)
    check("WEIGHT_TOTAL_10000", sum(rule["weight_bps"] for rule in catalog["rules"]) == 10000)
    check("SEVERITY_BOUND", all(rule["severity"] in SEVERITIES for rule in catalog["rules"]))
    check("PROCESS_IMPACT_BOUND", all(rule["process_impact"] in PROCESS_IMPACTS for rule in catalog["rules"]))
    check("STATUS_COUNT_4", len(statuses["statuses"]) == 4)
    check("STATUS_LABELS_HUMAN", [row["label_zh"] for row in statuses["statuses"]] == list(STATUS_LABELS_ZH))
    check("COLOR_SUPPLEMENTAL_ONLY", statuses["color_is_only_information"] is False)
    check("TEXT_SYMBOL_REASON_ACTION_REQUIRED", all(statuses[key] is True for key in ("text_label_required", "symbol_required", "reason_required", "next_action_required")))
    check("TECHNICAL_DETAIL_NESTED", statuses["technical_detail_location"] == "professional_detail")
    check("THRESHOLDS_EXTERNALIZED", policy["pass_min_bps"] == 9500 and policy["not_usable_below_bps"] == 7500)
    check("HARD_GATE_PRECEDENCE", policy["precedence"][0] == "HARD_GATE_FAILURE" and policy["hard_gate_overrides_score"] is True)
    check("INTEGER_SCORE_ONLY", policy["integer_only"] is True)
    check("REPORT_CLOSED", policy["formal_report_allowed_in_this_phase"] is False)

    expected = {
        "all_pass": ("PASSED", "已通过", 10000, 0, True),
        "high_score_critical_failure": ("NOT_USABLE", "不可使用", 9375, 1, False),
        "review_required": ("REVIEW_REQUIRED", "需确认", 9375, 0, False),
        "outdated_source": ("OUTDATED", "已过期", 9375, 0, False),
        "low_score_without_hard_gate": ("NOT_USABLE", "不可使用", 6875, 0, False),
    }
    for name, (technical, label, score, hard_count, allowed) in expected.items():
        result = results[name]
        detail = result["professional_detail"]
        prefix = name.upper()
        check(prefix + "_TECHNICAL_STATUS", detail["technical_status"] == technical)
        check(prefix + "_HUMAN_LABEL", result["display"]["label_zh"] == label)
        check(prefix + "_SCORE", detail["score_bps"] == score)
        check(prefix + "_HARD_GATE_COUNT", detail["hard_gate_failure_count"] == hard_count)
        check(prefix + "_FLOW_GATE", result["quality_flow_allowed"] is allowed)
        check(prefix + "_REPORT_CLOSED", result["formal_report_allowed"] is False)
        check(prefix + "_NON_COLOR_INFORMATION", bool(result["display"]["symbol"] and result["display"]["reason_zh"] and result["display"]["next_action_zh"]))

    failed = sum(row["status"] != "PASS" for row in checks)
    return {
        "schema_version": "kmfa.v015.s11p1.quality_rule_verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
        "scenario_results": results,
        "rule_count": len(catalog["rules"]),
        "dimension_count": len(catalog["dimensions"]),
        "hard_gate_count": sum(rule["hard_gate"] for rule in catalog["rules"]),
        "status_count": len(statuses["statuses"]),
        "rule_weight_total_bps": sum(rule["weight_bps"] for rule in catalog["rules"]),
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "CATALOG_SCHEMA",
    "DIMENSIONS",
    "PROCESS_IMPACTS",
    "QualityRuleError",
    "RESULT_SCHEMA",
    "ROADMAP_PHASE_ID",
    "RUN_PHASE_ID",
    "SCORE_SCHEMA",
    "SEVERITIES",
    "STATUS_CODES",
    "STATUS_LABELS_ZH",
    "STATUS_SCHEMA",
    "TASK_ID",
    "VERSION",
    "baseline_snapshot",
    "default_rule_catalog",
    "default_score_policy",
    "default_status_model",
    "evaluate_quality",
    "public_scenarios",
    "public_verification",
    "validate_configuration",
    "validate_snapshot",
]
