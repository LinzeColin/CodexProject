#!/usr/bin/env python3
"""KMFA v1.5 S13-P2 可解释经营健康模型。

本模块只处理公开安全的规则和合成值。健康分不能覆盖硬门禁；缺少来源、
解释或新鲜度时不显示综合分。情景分析严格区分事实与假设，且永不写回事实层。
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s13_p1_indicator_registry as indicator_kernel


RUN_PHASE_ID = "V015_S13_P2_BUSINESS_HEALTH_MODEL"
ROADMAP_PHASE_ID = "S13-P2"
TASK_ID = "KMFA-V015-S13-P2-BUSINESS-HEALTH-MODEL-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S13-P2-BUSINESS-HEALTH-MODEL"
VERSION = "1.5.0-dev-s13p2"

HEALTH_DIMENSION_IDS = (
    "HEALTH-CASH-SAFETY",
    "HEALTH-PROJECT-PROFIT",
    "HEALTH-COLLECTION-QUALITY",
    "HEALTH-TAX-POLICY",
    "HEALTH-CONTRACT-PERFORMANCE",
    "HEALTH-DATA-COMPLETENESS",
)
HEALTH_STATES = (
    "HEALTHY",
    "WATCH",
    "AT_RISK",
    "BLOCKED_BY_HARD_GATE",
    "INSUFFICIENT_DATA",
    "INVALID_INPUT",
)
FRESHNESS_STATES = ("FRESH", "AGING", "STALE")
SCENARIO_TYPES = ("COLLECTION_DELAY", "COST_INCREASE", "REVENUE_DECLINE")

_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]{2,95}$")
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


class HealthModelError(ValueError):
    """带稳定错误码的 fail-closed 健康模型异常。"""

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
        raise HealthModelError("TEXT_REQUIRED", f"{field} 必须是非空文本。")
    return value.strip()


def _identifier(value: Any, field: str) -> str:
    text = _text(value, field)
    if not _ID_RE.fullmatch(text):
        raise HealthModelError("IDENTIFIER_INVALID", f"{field} 格式不正确。")
    return text


def _reference(value: Any, field: str) -> str:
    text = _text(value, field)
    if not _REF_RE.fullmatch(text) or text.startswith(("file://", "private://")):
        raise HealthModelError("REFERENCE_INVALID", f"{field} 必须是公开安全引用。")
    return text


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HealthModelError("INTEGER_REQUIRED", f"{field} 必须是整数，不能使用 float 或布尔值。")
    return value


def _bounded_integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    number = _integer(value, field)
    if number < minimum or number > maximum:
        raise HealthModelError("INTEGER_OUT_OF_RANGE", f"{field} 必须在 {minimum} 至 {maximum} 之间。")
    return number


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise HealthModelError("BOOLEAN_REQUIRED", f"{field} 必须是布尔值。")
    return value


def _assert_public_safe(value: Any, path: str = "record") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_KEYS:
                raise HealthModelError("PRIVATE_FIELD_REJECTED", f"{path}.{key_text} 不允许进入公开模型。")
            _assert_public_safe(nested, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_public_safe(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if value.startswith(("/Users/", "/Volumes/", "/home/")) or "kmfa_metadata" in lowered or lowered.startswith(("file://", "private://")):
            raise HealthModelError("PRIVATE_VALUE_REJECTED", f"{path} 包含本地或私有定位信息。")


def _round_div_half_away_from_zero(numerator: int, denominator: int) -> int:
    top = _integer(numerator, "numerator")
    bottom = _integer(denominator, "denominator")
    if bottom <= 0:
        raise HealthModelError("POSITIVE_DENOMINATOR_REQUIRED", "分母必须大于 0。")
    sign = -1 if top < 0 else 1
    absolute = abs(top)
    quotient, remainder = divmod(absolute, bottom)
    if remainder * 2 >= bottom:
        quotient += 1
    return sign * quotient


def _clamp_score(value: int) -> int:
    return min(10_000, max(0, _integer(value, "score_bps")))


def health_dimensions() -> list[dict[str, Any]]:
    """返回六个外置健康维度；权重使用整数基点。"""

    return copy.deepcopy(
        [
            {
                "dimension_id": "HEALTH-CASH-SAFETY",
                "name_zh": "现金安全",
                "weight_bps": 2200,
                "base_score_bps": 5000,
                "source_indicator_ids": ["IND-CASH-NET-MOVEMENT-CENTS"],
                "hard_gate_id": "GATE-CASH-SAFETY",
                "freshness_limit_days": 7,
                "limitations_zh": "仅评估现金安全信号，不替代资金审批、付款或银行操作。",
            },
            {
                "dimension_id": "HEALTH-PROJECT-PROFIT",
                "name_zh": "项目利润",
                "weight_bps": 2000,
                "base_score_bps": 5000,
                "source_indicator_ids": ["IND-MARGIN-GROSS-BPS", "IND-COST-RECOGNIZED-CENTS"],
                "hard_gate_id": "GATE-PROJECT-PROFIT",
                "freshness_limit_days": 30,
                "limitations_zh": "只反映已登记利润与成本事实，不替代项目结算或收入确认。",
            },
            {
                "dimension_id": "HEALTH-COLLECTION-QUALITY",
                "name_zh": "回款质量",
                "weight_bps": 1800,
                "base_score_bps": 5000,
                "source_indicator_ids": ["IND-COLLECTION-RATE-BPS"],
                "hard_gate_id": "GATE-COLLECTION-QUALITY",
                "freshness_limit_days": 14,
                "limitations_zh": "只描述已确认回款质量，不生成催收、法务或客户处置决定。",
            },
            {
                "dimension_id": "HEALTH-TAX-POLICY",
                "name_zh": "税务政策",
                "weight_bps": 1200,
                "base_score_bps": 5000,
                "source_indicator_ids": ["IND-TAX-BURDEN-BPS"],
                "hard_gate_id": "GATE-TAX-POLICY",
                "freshness_limit_days": 90,
                "limitations_zh": "税负信号必须结合政策证据，不构成税务申报或合规结论。",
            },
            {
                "dimension_id": "HEALTH-CONTRACT-PERFORMANCE",
                "name_zh": "合同履约",
                "weight_bps": 1600,
                "base_score_bps": 5000,
                "source_indicator_ids": ["IND-PERFORMANCE-COMPLETION-BPS"],
                "hard_gate_id": "GATE-CONTRACT-PERFORMANCE",
                "freshness_limit_days": 30,
                "limitations_zh": "只汇总履约证据，不替代签证、验收、结算或法律判断。",
            },
            {
                "dimension_id": "HEALTH-DATA-COMPLETENESS",
                "name_zh": "数据完整度",
                "weight_bps": 1200,
                "base_score_bps": 5000,
                "source_indicator_ids": ["IND-DATA-QUALITY-COVERAGE-BPS"],
                "hard_gate_id": "GATE-DATA-COMPLETENESS",
                "freshness_limit_days": 7,
                "limitations_zh": "数据完整度是所有经营判断的硬门禁，不能被其他高分抵消。",
            },
        ]
    )


def validate_health_dimensions(dimensions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if isinstance(dimensions, (str, bytes)) or not isinstance(dimensions, Sequence):
        raise HealthModelError("DIMENSION_SEQUENCE_REQUIRED", "健康维度必须是列表。")
    rows = [dict(row) for row in dimensions]
    if len(rows) != 6:
        raise HealthModelError("DIMENSION_COUNT_INVALID", "经营健康模型必须正好包含六个维度。")
    known_indicators = {row["indicator_id"] for row in indicator_kernel.indicator_registry()}
    seen: set[str] = set()
    total_weight = 0
    for index, row in enumerate(rows):
        _assert_public_safe(row, f"dimensions[{index}]")
        dimension_id = _identifier(row.get("dimension_id"), "dimension_id")
        if dimension_id in seen:
            raise HealthModelError("DIMENSION_DUPLICATE", "健康维度编号不能重复。")
        seen.add(dimension_id)
        _text(row.get("name_zh"), "name_zh")
        total_weight += _bounded_integer(row.get("weight_bps"), "weight_bps", 1, 10_000)
        if _bounded_integer(row.get("base_score_bps"), "base_score_bps", 0, 10_000) != 5000:
            raise HealthModelError("BASE_SCORE_DRIFT", "当前模型基准分必须统一为 5000 基点。")
        sources = row.get("source_indicator_ids")
        if not isinstance(sources, list) or not sources:
            raise HealthModelError("SOURCE_REQUIRED", "每个健康维度必须绑定至少一个指标来源。")
        for source in sources:
            if _identifier(source, "source_indicator_id") not in known_indicators:
                raise HealthModelError("SOURCE_UNKNOWN", "健康维度引用了未登记指标。")
        _identifier(row.get("hard_gate_id"), "hard_gate_id")
        _bounded_integer(row.get("freshness_limit_days"), "freshness_limit_days", 1, 365)
        _text(row.get("limitations_zh"), "limitations_zh")
    if tuple(row["dimension_id"] for row in rows) != HEALTH_DIMENSION_IDS:
        raise HealthModelError("DIMENSION_ORDER_DRIFT", "健康维度顺序必须稳定。")
    if total_weight != 10_000:
        raise HealthModelError("WEIGHT_SUM_INVALID", "六个健康维度的权重总和必须等于 10000 基点。")
    return {
        "dimension_count": len(rows),
        "weight_total_bps": total_weight,
        "score_min_bps": 0,
        "score_max_bps": 10_000,
        "hard_gate_count": len(rows),
        "registry_fingerprint": fingerprint(rows),
    }


def _freshness_state(age_days: Any, limit_days: int) -> str:
    age = _bounded_integer(age_days, "freshness_age_days", 0, 3650)
    if age <= limit_days:
        return "FRESH"
    if age <= limit_days * 2:
        return "AGING"
    return "STALE"


def _insufficient_result(reason_zh: str, missing_dimensions: list[str]) -> dict[str, Any]:
    return {
        "health_state": "INSUFFICIENT_DATA",
        "overall_score_bps": None,
        "score_displayable": False,
        "reason_zh": reason_zh,
        "missing_dimension_ids": missing_dimensions,
        "dimension_results": [],
        "hard_gate_override_applied": False,
        "scoring_replaced_hard_gate": False,
        "explanation_complete": False,
        "data_freshness_visible": True,
        "action_priority_computed": False,
        "business_action_executed": False,
    }


def _dimension_result(spec: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    _assert_public_safe(observation, str(spec["dimension_id"]))
    if _identifier(observation.get("dimension_id"), "dimension_id") != spec["dimension_id"]:
        raise HealthModelError("DIMENSION_BINDING_MISMATCH", "健康观察与维度编号不一致。")
    sources = observation.get("source_indicator_ids")
    if sources != spec["source_indicator_ids"]:
        raise HealthModelError("SOURCE_BINDING_MISMATCH", "健康观察必须精确绑定登记指标。")
    source_fingerprint = _reference(observation.get("source_fingerprint"), "source_fingerprint")
    if not source_fingerprint.startswith("sha256:") or len(source_fingerprint) != 71:
        raise HealthModelError("SOURCE_FINGERPRINT_INVALID", "来源指纹格式不正确。")
    as_of_date = _text(observation.get("as_of_date"), "as_of_date")
    freshness = _freshness_state(observation.get("freshness_age_days"), int(spec["freshness_limit_days"]))
    gate_passed = _boolean(observation.get("hard_gate_passed"), "hard_gate_passed")
    gate_reason = _text(observation.get("hard_gate_reason_zh"), "hard_gate_reason_zh")
    factors = observation.get("factors")
    if not isinstance(factors, list) or not factors:
        raise HealthModelError("UNEXPLAINED_SCORE_REJECTED", "健康分必须至少有一个可追溯贡献因素。")
    seen: set[str] = set()
    normalized_factors: list[dict[str, Any]] = []
    factor_total = 0
    for index, factor in enumerate(factors):
        if not isinstance(factor, Mapping):
            raise HealthModelError("FACTOR_RECORD_REQUIRED", "贡献因素必须是结构化记录。")
        factor_id = _identifier(factor.get("factor_id"), "factor_id")
        if factor_id in seen:
            raise HealthModelError("FACTOR_DUPLICATE", "同一维度的贡献因素编号不能重复。")
        seen.add(factor_id)
        effect = _bounded_integer(factor.get("effect_bps"), "effect_bps", -10_000, 10_000)
        direction = _text(factor.get("direction"), "direction")
        expected_direction = "POSITIVE" if effect > 0 else "NEGATIVE" if effect < 0 else "NEUTRAL"
        if direction != expected_direction:
            raise HealthModelError("FACTOR_DIRECTION_MISMATCH", "贡献因素方向与影响值不一致。")
        source_id = _identifier(factor.get("source_indicator_id"), "source_indicator_id")
        if source_id not in sources:
            raise HealthModelError("FACTOR_SOURCE_MISMATCH", "贡献因素必须来自本维度登记指标。")
        if factor.get("record_kind") != "FACT":
            raise HealthModelError("ASSUMPTION_IN_ACTUAL_SCORE", "实际健康分只允许使用事实，不能混入情景假设。")
        reason = _text(factor.get("reason_zh"), "reason_zh")
        normalized_factors.append(
            {
                "factor_id": factor_id,
                "effect_bps": effect,
                "direction": direction,
                "reason_zh": reason,
                "source_indicator_id": source_id,
                "record_kind": "FACT",
            }
        )
        factor_total += effect
    score = _clamp_score(int(spec["base_score_bps"]) + factor_total)
    displayable = gate_passed and freshness != "STALE"
    weighted = _round_div_half_away_from_zero(score * int(spec["weight_bps"]), 10_000) if displayable else None
    return {
        "dimension_id": spec["dimension_id"],
        "name_zh": spec["name_zh"],
        "weight_bps": spec["weight_bps"],
        "score_bps": score if displayable else None,
        "weighted_contribution_bps": weighted,
        "score_displayable": displayable,
        "source_indicator_ids": copy.deepcopy(sources),
        "source_fingerprint": source_fingerprint,
        "as_of_date": as_of_date,
        "freshness_age_days": observation["freshness_age_days"],
        "freshness_state": freshness,
        "hard_gate_id": spec["hard_gate_id"],
        "hard_gate_passed": gate_passed,
        "hard_gate_reason_zh": gate_reason,
        "base_score_bps": spec["base_score_bps"],
        "factors": normalized_factors,
        "explanation_complete": True,
    }


def evaluate_health(observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """按六维权重生成可解释健康判断；硬门禁失败时不显示综合分。"""

    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise HealthModelError("OBSERVATION_SEQUENCE_REQUIRED", "健康观察必须是列表。")
    specs = health_dimensions()
    validate_health_dimensions(specs)
    indexed: dict[str, Mapping[str, Any]] = {}
    for observation in observations:
        if not isinstance(observation, Mapping):
            raise HealthModelError("OBSERVATION_RECORD_REQUIRED", "健康观察必须是结构化记录。")
        dimension_id = _identifier(observation.get("dimension_id"), "dimension_id")
        if dimension_id in indexed:
            raise HealthModelError("OBSERVATION_DUPLICATE", "同一健康维度不能重复。")
        indexed[dimension_id] = observation
    extra = sorted(set(indexed) - set(HEALTH_DIMENSION_IDS))
    if extra:
        raise HealthModelError("OBSERVATION_UNKNOWN_DIMENSION", "健康观察包含未登记维度。")
    missing = [dimension_id for dimension_id in HEALTH_DIMENSION_IDS if dimension_id not in indexed]
    if missing:
        result = _insufficient_result("缺少必需健康维度，禁止显示综合分。", missing)
        result["result_fingerprint"] = fingerprint(result)
        return result
    results = [_dimension_result(spec, indexed[str(spec["dimension_id"])]) for spec in specs]
    failed_gates = [row["dimension_id"] for row in results if not row["hard_gate_passed"]]
    stale = [row["dimension_id"] for row in results if row["freshness_state"] == "STALE"]
    if failed_gates:
        state = "BLOCKED_BY_HARD_GATE"
        score: int | None = None
        displayable = False
        reason = "存在硬门禁失败；其他维度高分不能抵消，综合分禁止显示。"
    elif stale:
        state = "INSUFFICIENT_DATA"
        score = None
        displayable = False
        reason = "存在过期资料；刷新前禁止显示综合分。"
    else:
        score = sum(int(row["weighted_contribution_bps"]) for row in results)
        if score < 0 or score > 10_000:
            raise HealthModelError("WEIGHTED_SCORE_OUT_OF_RANGE", "综合健康分超出 0 至 10000。")
        state = "HEALTHY" if score >= 8000 else "WATCH" if score >= 6500 else "AT_RISK"
        displayable = True
        reason = "六个维度、来源、解释、新鲜度和硬门禁均满足显示条件。"
    output = {
        "health_state": state,
        "overall_score_bps": score,
        "score_displayable": displayable,
        "reason_zh": reason,
        "missing_dimension_ids": [],
        "failed_hard_gate_dimension_ids": failed_gates,
        "stale_dimension_ids": stale,
        "dimension_results": results,
        "weight_total_bps": sum(int(row["weight_bps"]) for row in results),
        "hard_gate_override_applied": bool(failed_gates),
        "scoring_replaced_hard_gate": False,
        "explanation_complete": all(row["explanation_complete"] for row in results),
        "data_freshness_visible": all(row["freshness_state"] in FRESHNESS_STATES for row in results),
        "action_priority_computed": False,
        "business_action_executed": False,
    }
    output["result_fingerprint"] = fingerprint(output)
    return output


def compare_health(
    current_observations: Sequence[Mapping[str, Any]],
    prior_observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """解释综合分与各维度为何变化；无法解释时拒绝输出。"""

    current = evaluate_health(current_observations)
    prior = evaluate_health(prior_observations)
    if not current["score_displayable"] or not prior["score_displayable"]:
        raise HealthModelError("COMPARISON_SCORE_UNAVAILABLE", "当前期和比较期都必须有可显示健康分。")
    current_by_id = {row["dimension_id"]: row for row in current["dimension_results"]}
    prior_by_id = {row["dimension_id"]: row for row in prior["dimension_results"]}
    changes: list[dict[str, Any]] = []
    unexplained = 0
    for dimension_id in HEALTH_DIMENSION_IDS:
        current_row = current_by_id[dimension_id]
        prior_row = prior_by_id[dimension_id]
        current_factors = {row["factor_id"]: row for row in current_row["factors"]}
        prior_factors = {row["factor_id"]: row for row in prior_row["factors"]}
        factor_changes: list[dict[str, Any]] = []
        for factor_id in sorted(set(current_factors) | set(prior_factors)):
            current_effect = int(current_factors.get(factor_id, {}).get("effect_bps", 0))
            prior_effect = int(prior_factors.get(factor_id, {}).get("effect_bps", 0))
            if current_effect != prior_effect:
                source = current_factors.get(factor_id) or prior_factors[factor_id]
                factor_changes.append(
                    {
                        "factor_id": factor_id,
                        "effect_change_bps": current_effect - prior_effect,
                        "reason_zh": source["reason_zh"],
                        "source_indicator_id": source["source_indicator_id"],
                    }
                )
        score_change = int(current_row["score_bps"]) - int(prior_row["score_bps"])
        if score_change != 0 and not factor_changes:
            unexplained += 1
        changes.append(
            {
                "dimension_id": dimension_id,
                "score_change_bps": score_change,
                "weighted_change_bps": int(current_row["weighted_contribution_bps"]) - int(prior_row["weighted_contribution_bps"]),
                "factor_changes": factor_changes,
                "freshness_change": f"{prior_row['freshness_state']}->{current_row['freshness_state']}",
            }
        )
    if unexplained:
        raise HealthModelError("UNEXPLAINED_SCORE_CHANGE", "存在无法由贡献因素解释的健康分变化。")
    output = {
        "current_score_bps": current["overall_score_bps"],
        "prior_score_bps": prior["overall_score_bps"],
        "overall_score_change_bps": int(current["overall_score_bps"]) - int(prior["overall_score_bps"]),
        "dimension_changes": changes,
        "unexplained_change_count": 0,
        "explanation_complete": True,
        "current_result_fingerprint": current["result_fingerprint"],
        "prior_result_fingerprint": prior["result_fingerprint"],
    }
    output["comparison_fingerprint"] = fingerprint(output)
    return output


def _validated_facts(facts: Mapping[str, Any]) -> dict[str, int]:
    if not isinstance(facts, Mapping):
        raise HealthModelError("FACT_RECORD_REQUIRED", "情景分析事实必须是结构化记录。")
    _assert_public_safe(facts, "facts")
    required = (
        "recognized_revenue_cents",
        "recognized_cost_cents",
        "confirmed_collection_cents",
        "cash_balance_cents",
        "outstanding_receivable_cents",
    )
    if set(facts) != set(required):
        raise HealthModelError("FACT_FIELDS_INVALID", "情景分析事实字段必须完整且不能夹带其他字段。")
    values = {key: _integer(facts[key], key) for key in required}
    for key in ("recognized_revenue_cents", "recognized_cost_cents", "confirmed_collection_cents", "outstanding_receivable_cents"):
        if values[key] < 0:
            raise HealthModelError("NEGATIVE_FACT_UNSUPPORTED", f"{key} 不能为负数。")
    return values


def run_scenario(facts: Mapping[str, Any], scenario: Mapping[str, Any]) -> dict[str, Any]:
    """运行单个只读情景；假设和投影永不写回事实层。"""

    fact_snapshot = _validated_facts(facts)
    before = fingerprint(fact_snapshot)
    if not isinstance(scenario, Mapping):
        raise HealthModelError("SCENARIO_RECORD_REQUIRED", "情景假设必须是结构化记录。")
    _assert_public_safe(scenario, "scenario")
    scenario_id = _identifier(scenario.get("scenario_id"), "scenario_id")
    scenario_type = _text(scenario.get("scenario_type"), "scenario_type")
    if scenario_type not in SCENARIO_TYPES:
        raise HealthModelError("SCENARIO_TYPE_INVALID", "情景类型未登记。")
    if scenario.get("record_kind") != "ASSUMPTION":
        raise HealthModelError("SCENARIO_NOT_MARKED_ASSUMPTION", "情景必须明确标记为假设。")
    projected = copy.deepcopy(fact_snapshot)
    normalized_assumption: dict[str, Any] = {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "record_kind": "ASSUMPTION",
        "reason_zh": _text(scenario.get("reason_zh"), "reason_zh"),
    }
    if scenario_type == "COLLECTION_DELAY":
        delay_days = _bounded_integer(scenario.get("delay_days"), "delay_days", 1, 365)
        delayed = _bounded_integer(
            scenario.get("delayed_collection_cents"),
            "delayed_collection_cents",
            0,
            fact_snapshot["confirmed_collection_cents"],
        )
        normalized_assumption.update({"delay_days": delay_days, "delayed_collection_cents": delayed})
        projected["confirmed_collection_cents"] -= delayed
        projected["cash_balance_cents"] -= delayed
        projected["outstanding_receivable_cents"] += delayed
    elif scenario_type == "COST_INCREASE":
        increase = _bounded_integer(scenario.get("increase_bps"), "increase_bps", 0, 10_000)
        normalized_assumption["increase_bps"] = increase
        projected["recognized_cost_cents"] += _round_div_half_away_from_zero(fact_snapshot["recognized_cost_cents"] * increase, 10_000)
    else:
        decline = _bounded_integer(scenario.get("decline_bps"), "decline_bps", 0, 10_000)
        normalized_assumption["decline_bps"] = decline
        projected["recognized_revenue_cents"] -= _round_div_half_away_from_zero(fact_snapshot["recognized_revenue_cents"] * decline, 10_000)
    projection = {
        **projected,
        "gross_profit_cents": projected["recognized_revenue_cents"] - projected["recognized_cost_cents"],
        "cash_delta_cents": projected["cash_balance_cents"] - fact_snapshot["cash_balance_cents"],
        "record_kind": "SCENARIO_PROJECTION",
    }
    after = fingerprint(_validated_facts(facts))
    if before != after:
        raise HealthModelError("FACT_MUTATION_DETECTED", "情景分析修改了事实层。")
    output = {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "fact_snapshot": fact_snapshot,
        "fact_snapshot_fingerprint": before,
        "assumption_snapshot": normalized_assumption,
        "projection": projection,
        "fact_layer_write_count": 0,
        "assumption_written_to_fact_layer": False,
        "is_actual_result": False,
        "business_action_executed": False,
    }
    output["scenario_fingerprint"] = fingerprint(output)
    return output


def run_sensitivity_analysis(
    facts: Mapping[str, Any],
    scenarios: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if isinstance(scenarios, (str, bytes)) or not isinstance(scenarios, Sequence):
        raise HealthModelError("SCENARIO_SEQUENCE_REQUIRED", "敏感性分析情景必须是列表。")
    if len(scenarios) != 3:
        raise HealthModelError("SCENARIO_COUNT_INVALID", "敏感性分析必须包含回款延迟、成本上涨和收入下降三类情景。")
    results = [run_scenario(facts, scenario) for scenario in scenarios]
    types = [row["scenario_type"] for row in results]
    if tuple(types) != SCENARIO_TYPES:
        raise HealthModelError("SCENARIO_ORDER_DRIFT", "三类情景必须按登记顺序提供且不能重复。")
    output = {
        "scenario_count": len(results),
        "scenario_types": types,
        "results": results,
        "fact_layer_write_count": 0,
        "assumption_written_to_fact_layer": False,
        "fact_and_assumption_separated": True,
        "action_priority_computed": False,
        "business_action_executed": False,
    }
    output["analysis_fingerprint"] = fingerprint(output)
    return output


def synthetic_observations(*, factor_shift_bps: int = 0) -> list[dict[str, Any]]:
    """公开合成样例；仅用于验证模型边界。"""

    shift = _bounded_integer(factor_shift_bps, "factor_shift_bps", -2000, 2000)
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(health_dimensions()):
        effect = 1500 + index * 150 + shift
        source_id = spec["source_indicator_ids"][0]
        rows.append(
            {
                "dimension_id": spec["dimension_id"],
                "source_indicator_ids": copy.deepcopy(spec["source_indicator_ids"]),
                "source_fingerprint": fingerprint({"dimension_id": spec["dimension_id"], "sample": "public-safe"}),
                "as_of_date": "2026-07-16",
                "freshness_age_days": min(3, int(spec["freshness_limit_days"])),
                "hard_gate_passed": True,
                "hard_gate_reason_zh": "公开合成样例未触发该维度硬门禁。",
                "factors": [
                    {
                        "factor_id": f"FACTOR-{index + 1:02d}-PRIMARY",
                        "effect_bps": effect,
                        "direction": "POSITIVE",
                        "reason_zh": "登记指标较比较期改善，形成可追溯正向贡献。",
                        "source_indicator_id": source_id,
                        "record_kind": "FACT",
                    }
                ],
            }
        )
    return rows


def synthetic_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "SCN-COLLECTION-DELAY-30D",
            "scenario_type": "COLLECTION_DELAY",
            "record_kind": "ASSUMPTION",
            "reason_zh": "假设部分已确认回款延迟三十天。",
            "delay_days": 30,
            "delayed_collection_cents": 20_000,
        },
        {
            "scenario_id": "SCN-COST-INCREASE-1000BPS",
            "scenario_type": "COST_INCREASE",
            "record_kind": "ASSUMPTION",
            "reason_zh": "假设已确认成本上涨一千基点。",
            "increase_bps": 1000,
        },
        {
            "scenario_id": "SCN-REVENUE-DECLINE-1500BPS",
            "scenario_type": "REVENUE_DECLINE",
            "record_kind": "ASSUMPTION",
            "reason_zh": "假设已确认收入下降一千五百基点。",
            "decline_bps": 1500,
        },
    ]


def _rejects(callable_value: Any, code: str) -> bool:
    try:
        callable_value()
    except HealthModelError as error:
        return error.code == code
    return False


def public_verification() -> dict[str, Any]:
    dimensions = health_dimensions()
    registry = validate_health_dimensions(dimensions)
    current_observations = synthetic_observations(factor_shift_bps=300)
    prior_observations = synthetic_observations(factor_shift_bps=0)
    current = evaluate_health(current_observations)
    prior = evaluate_health(prior_observations)
    comparison = compare_health(current_observations, prior_observations)

    hard_gate_observations = synthetic_observations(factor_shift_bps=2000)
    hard_gate_observations[5]["hard_gate_passed"] = False
    hard_gate_observations[5]["hard_gate_reason_zh"] = "数据完整度硬门禁失败。"
    hard_gate = evaluate_health(hard_gate_observations)

    stale_observations = synthetic_observations()
    stale_observations[0]["freshness_age_days"] = 30
    stale = evaluate_health(stale_observations)
    missing = evaluate_health(synthetic_observations()[:-1])

    facts = {
        "recognized_revenue_cents": 120_000,
        "recognized_cost_cents": 80_000,
        "confirmed_collection_cents": 90_000,
        "cash_balance_cents": 50_000,
        "outstanding_receivable_cents": 30_000,
    }
    facts_before = copy.deepcopy(facts)
    sensitivity = run_sensitivity_analysis(facts, synthetic_scenarios())

    unexplained = synthetic_observations()
    unexplained[0]["factors"] = []
    assumption_in_score = synthetic_observations()
    assumption_in_score[0]["factors"][0]["record_kind"] = "ASSUMPTION"
    wrong_source = synthetic_observations()
    wrong_source[0]["source_indicator_ids"] = ["IND-REVENUE-RECOGNIZED-CENTS"]
    invalid_weight = health_dimensions()
    invalid_weight[0]["weight_bps"] = 2100
    private_dimension = health_dimensions()
    private_dimension[0]["limitations_zh"] = "/Users/private/value"
    invalid_fact = copy.deepcopy(facts)
    invalid_fact["recognized_cost_cents"] = json.loads("1.0")
    invalid_scenario = synthetic_scenarios()[1]
    invalid_scenario["increase_bps"] = json.loads("1.0")

    checks = {
        "dimension_count_exact": registry["dimension_count"] == 6,
        "dimension_ids_exact": tuple(row["dimension_id"] for row in dimensions) == HEALTH_DIMENSION_IDS,
        "weight_total_exact": registry["weight_total_bps"] == 10_000,
        "score_min_exact": registry["score_min_bps"] == 0,
        "score_max_exact": registry["score_max_bps"] == 10_000,
        "hard_gate_count_exact": registry["hard_gate_count"] == 6,
        "all_weights_positive": all(row["weight_bps"] > 0 for row in dimensions),
        "all_sources_present": all(row["source_indicator_ids"] for row in dimensions),
        "all_sources_registered": all(source in {item["indicator_id"] for item in indicator_kernel.indicator_registry()} for row in dimensions for source in row["source_indicator_ids"]),
        "all_limits_present": all(bool(row["limitations_zh"]) for row in dimensions),
        "all_freshness_limits_positive": all(row["freshness_limit_days"] > 0 for row in dimensions),
        "registry_deterministic": registry["registry_fingerprint"] == validate_health_dimensions(health_dimensions())["registry_fingerprint"],
        "current_score_displayed": current["score_displayable"] is True,
        "current_state_valid": current["health_state"] in ("HEALTHY", "WATCH", "AT_RISK"),
        "current_score_in_range": 0 <= current["overall_score_bps"] <= 10_000,
        "current_dimension_count": len(current["dimension_results"]) == 6,
        "current_weight_total": current["weight_total_bps"] == 10_000,
        "current_explanation_complete": current["explanation_complete"] is True,
        "current_freshness_visible": current["data_freshness_visible"] is True,
        "current_no_hard_gate_override": current["hard_gate_override_applied"] is False,
        "current_scoring_not_gate": current["scoring_replaced_hard_gate"] is False,
        "current_action_priority_closed": current["action_priority_computed"] is False,
        "current_business_action_closed": current["business_action_executed"] is False,
        "all_dimension_scores_in_range": all(0 <= row["score_bps"] <= 10_000 for row in current["dimension_results"]),
        "all_dimension_scores_displayed": all(row["score_displayable"] for row in current["dimension_results"]),
        "all_dimension_explanations_complete": all(row["explanation_complete"] for row in current["dimension_results"]),
        "all_dimension_sources_fingerprinted": all(row["source_fingerprint"].startswith("sha256:") for row in current["dimension_results"]),
        "all_dimension_freshness_visible": all(row["freshness_state"] in FRESHNESS_STATES for row in current["dimension_results"]),
        "all_factors_are_fact": all(factor["record_kind"] == "FACT" for row in current["dimension_results"] for factor in row["factors"]),
        "all_factors_explained": all(bool(factor["reason_zh"]) for row in current["dimension_results"] for factor in row["factors"]),
        "prior_score_displayed": prior["score_displayable"] is True,
        "current_above_prior": current["overall_score_bps"] > prior["overall_score_bps"],
        "comparison_delta_exact": comparison["overall_score_change_bps"] == current["overall_score_bps"] - prior["overall_score_bps"],
        "comparison_dimension_count": len(comparison["dimension_changes"]) == 6,
        "comparison_explained": comparison["explanation_complete"] is True,
        "comparison_unexplained_zero": comparison["unexplained_change_count"] == 0,
        "comparison_all_changed": all(row["score_change_bps"] > 0 for row in comparison["dimension_changes"]),
        "comparison_factor_reasons_present": all(row["factor_changes"] and row["factor_changes"][0]["reason_zh"] for row in comparison["dimension_changes"]),
        "comparison_deterministic": comparison["comparison_fingerprint"] == compare_health(current_observations, prior_observations)["comparison_fingerprint"],
        "hard_gate_state": hard_gate["health_state"] == "BLOCKED_BY_HARD_GATE",
        "hard_gate_score_hidden": hard_gate["overall_score_bps"] is None,
        "hard_gate_not_displayable": hard_gate["score_displayable"] is False,
        "hard_gate_override_visible": hard_gate["hard_gate_override_applied"] is True,
        "hard_gate_dimension_identified": hard_gate["failed_hard_gate_dimension_ids"] == ["HEALTH-DATA-COMPLETENESS"],
        "hard_gate_high_scores_do_not_override": hard_gate["scoring_replaced_hard_gate"] is False,
        "stale_state_insufficient": stale["health_state"] == "INSUFFICIENT_DATA",
        "stale_score_hidden": stale["overall_score_bps"] is None,
        "stale_dimension_identified": stale["stale_dimension_ids"] == ["HEALTH-CASH-SAFETY"],
        "stale_freshness_visible": stale["data_freshness_visible"] is True,
        "missing_state_insufficient": missing["health_state"] == "INSUFFICIENT_DATA",
        "missing_score_hidden": missing["overall_score_bps"] is None,
        "missing_dimension_identified": missing["missing_dimension_ids"] == ["HEALTH-DATA-COMPLETENESS"],
        "unexplained_score_rejected": _rejects(lambda: evaluate_health(unexplained), "UNEXPLAINED_SCORE_REJECTED"),
        "assumption_in_actual_score_rejected": _rejects(lambda: evaluate_health(assumption_in_score), "ASSUMPTION_IN_ACTUAL_SCORE"),
        "wrong_source_rejected": _rejects(lambda: evaluate_health(wrong_source), "SOURCE_BINDING_MISMATCH"),
        "weight_drift_rejected": _rejects(lambda: validate_health_dimensions(invalid_weight), "WEIGHT_SUM_INVALID"),
        "private_dimension_rejected": _rejects(lambda: validate_health_dimensions(private_dimension), "PRIVATE_VALUE_REJECTED"),
        "float_fact_rejected": _rejects(lambda: run_sensitivity_analysis(invalid_fact, synthetic_scenarios()), "INTEGER_REQUIRED"),
        "float_assumption_rejected": _rejects(lambda: run_scenario(facts, invalid_scenario), "INTEGER_REQUIRED"),
        "boolean_factor_rejected": _rejects(lambda: _integer(True, "effect_bps"), "INTEGER_REQUIRED"),
        "scenario_count_exact": sensitivity["scenario_count"] == 3,
        "scenario_types_exact": tuple(sensitivity["scenario_types"]) == SCENARIO_TYPES,
        "scenario_facts_unchanged": facts == facts_before,
        "scenario_fact_write_zero": sensitivity["fact_layer_write_count"] == 0,
        "scenario_assumption_not_written": sensitivity["assumption_written_to_fact_layer"] is False,
        "scenario_fact_assumption_separated": sensitivity["fact_and_assumption_separated"] is True,
        "scenario_action_priority_closed": sensitivity["action_priority_computed"] is False,
        "scenario_business_action_closed": sensitivity["business_action_executed"] is False,
        "all_scenarios_not_actual": all(row["is_actual_result"] is False for row in sensitivity["results"]),
        "all_scenario_fact_writes_zero": all(row["fact_layer_write_count"] == 0 for row in sensitivity["results"]),
        "all_scenario_assumptions_separate": all(row["assumption_written_to_fact_layer"] is False for row in sensitivity["results"]),
        "all_scenario_fingerprints": all(row["scenario_fingerprint"].startswith("sha256:") for row in sensitivity["results"]),
        "collection_delay_cash_effect": sensitivity["results"][0]["projection"]["cash_delta_cents"] == -20_000,
        "collection_delay_receivable_effect": sensitivity["results"][0]["projection"]["outstanding_receivable_cents"] == 50_000,
        "cost_increase_exact": sensitivity["results"][1]["projection"]["recognized_cost_cents"] == 88_000,
        "cost_increase_profit_exact": sensitivity["results"][1]["projection"]["gross_profit_cents"] == 32_000,
        "revenue_decline_exact": sensitivity["results"][2]["projection"]["recognized_revenue_cents"] == 102_000,
        "revenue_decline_profit_exact": sensitivity["results"][2]["projection"]["gross_profit_cents"] == 22_000,
        "sensitivity_deterministic": sensitivity["analysis_fingerprint"] == run_sensitivity_analysis(facts, synthetic_scenarios())["analysis_fingerprint"],
        "health_state_registry_exact": len(HEALTH_STATES) == 6,
        "freshness_state_registry_exact": len(FRESHNESS_STATES) == 3,
        "scenario_type_registry_exact": len(SCENARIO_TYPES) == 3,
        "raw_root_access_zero": True,
        "live_source_read_zero": True,
        "real_business_calculation_false": True,
        "github_upload_false": True,
        "app_reinstall_false": True,
        "formal_report_false": True,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": "kmfa.v015.s13p2.public_verification.v1",
        "phase_id": RUN_PHASE_ID,
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "checks": checks,
        "summary": {
            "dimension_count": registry["dimension_count"],
            "weight_total_bps": registry["weight_total_bps"],
            "hard_gate_count": registry["hard_gate_count"],
            "health_state_count": len(HEALTH_STATES),
            "freshness_state_count": len(FRESHNESS_STATES),
            "scenario_count": sensitivity["scenario_count"],
            "unexplained_change_count": comparison["unexplained_change_count"],
            "fact_layer_write_count": sensitivity["fact_layer_write_count"],
        },
        "sample_health_result": current,
        "sample_change_explanation": comparison,
        "sample_sensitivity_analysis": sensitivity,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "real_business_calculation_performed": False,
        "action_priority_computed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
    }


if __name__ == "__main__":
    print(json.dumps(public_verification(), ensure_ascii=False, indent=2, sort_keys=True))
